"""Build the stand FE model from geometry + brackets: nodes, sub-elements, joint springs.

Every member gets its own nodes; members never share a node.  Members meet only
through bracket springs (6-DOF, zero length, at the joint point `at`, rigid arms
to each member's node) and compression-only bearing springs (at the end face of
the bearing member, along its axis).
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from . import fem
from .geometry import AXES, Geometry, Joint, Member, face_vector

DOF_NAMES = ["ux", "uy", "uz", "rx", "ry", "rz"]


class ModelError(RuntimeError):
    """Inconsistent input (e.g. a joint member with no bracket and no bearing)."""


@dataclass
class BracketSpring:
    joint: str
    index: int              # entry index in the joint's bracket list
    copy: int               # 0..count-1
    type: str
    a: int
    b: int
    face: str
    note: str
    na: int
    nb: int
    X: np.ndarray
    EA_L: float             # min over a, b
    EI_L: float             # min over a, b (weak axis)
    legs: list = field(default_factory=list)   # filled by joints.prepare()

    @property
    def label(self) -> str:
        c = f".{self.copy}" if self.copy else ""
        return f"{self.joint}#{self.index}{c}"

    def spring(self, model: "StandModel", kt_f: float, kr_f: float) -> fem.Spring:
        Ks = fem.iso_spring_K(kt_f * self.EA_L, kr_f * self.EI_L)
        return fem.Spring(self.na, self.nb, self.X, model.x[self.na], model.x[self.nb], Ks,
                          {"bracket": self})


@dataclass
class BearingSpring:
    joint: str
    end_of: int
    bears_on: int
    n_end: int              # end node of end_of (side b)
    n_on: int               # node on bears_on (side a)
    n: np.ndarray           # outward axis of end_of at that end (closing direction)
    k: float

    def spring(self, model: "StandModel") -> fem.Spring:
        X = model.x[self.n_end]
        return fem.Spring(self.n_on, self.n_end, X, model.x[self.n_on], X,
                          fem.axial_spring_K(self.k, self.n), {"bearing": self})

    @property
    def label(self) -> str:
        return f"{self.joint}:M{self.end_of}->M{self.bears_on}"


@dataclass
class GroundContact:
    node: int
    member: int
    trib: float             # tributary length along the member (m)
    P: np.ndarray           # contact point (beam underside)
    r: np.ndarray           # P - x[node]

    def T(self) -> np.ndarray:
        """3x6: displacement of the contact point from the node's 6 DOFs (u + theta x r)."""
        rx = np.array([[0, -self.r[2], self.r[1]], [self.r[2], 0, -self.r[0]], [-self.r[1], self.r[0], 0]])
        return np.hstack([np.eye(3), -rx])


@dataclass
class PointLoad:
    node: int
    F: np.ndarray           # N, global
    at: np.ndarray          # point of application (moment transferred to node)
    what: str


@dataclass
class StandModel:
    geo: Geometry
    mode: str                                   # "3d" | "2d"
    members: dict[int, Member]                  # members in this model
    sections: dict[int, fem.Section]
    x: np.ndarray                               # node coords (n, 3)
    node_member: list[int]
    node_s: list[float]
    member_nodes: dict[int, list[int]]
    elements: list[fem.FrameElement]
    member_elements: dict[int, list[int]]
    joint_node: dict[tuple[str, int], int]
    brackets: list[BracketSpring]
    bearings: list[BearingSpring]
    joints: list[Joint]                         # joints as used (2D: filtered)
    thrust_node: int
    thrust_point: np.ndarray                    # point where stand loads act (2D: projected)
    load_scale: float                           # 1.0 (3D) or 0.5 (2D: half of every stand load)
    base_elements: list[int]
    base_nodes: list[int]
    fixed: list[int]                            # 3-2-1 restraint DOFs
    fixed_plane: list[int]                      # 2D: out-of-plane DOFs (all nodes)
    restraint_desc: list[str]
    lumped: list[PointLoad] = field(default_factory=list)   # 2D: half cross-member weights
    notes: list[str] = field(default_factory=list)
    stubs: dict[int, Member] = field(default_factory=dict)    # 2D joint stubs (no elements)
    E: float = 0.0
    G: float = 0.0
    ground: list = field(default_factory=list)    # ground mode: GroundContact per base node
    thrust_patches: list = field(default_factory=list)   # [(member, s0, s1)]: plate spreads stand loads
    thrust_patch_nodes: list = field(default_factory=list)

    @property
    def ground_mode(self) -> bool:
        return bool(self.ground)

    def geom(self, mid: int) -> Member:
        return self.members[mid] if mid in self.members else self.stubs[mid]

    @property
    def n_nodes(self) -> int:
        return len(self.x)

    @property
    def n_dof(self) -> int:
        return fem.DOF * self.n_nodes

    @property
    def all_fixed(self) -> list[int]:
        return sorted(set(self.fixed) | set(self.fixed_plane))

    def dof_label(self, d: int) -> str:
        n, k = divmod(d, fem.DOF)
        return f"node {n} (M{self.node_member[n]} s={self.node_s[n] * 1e3:.0f} mm) {DOF_NAMES[k]}"


# --------------------------------------------------------------------------- sections
def member_section(m: Member, p) -> tuple[fem.Section, np.ndarray]:
    sp = getattr(p.si, f"section_{m.profile}")
    if abs(sp.I_strong - sp.I_weak) > 1e-12:
        if m.depth_along is None:
            raise ModelError(f"{m.name}: {m.profile} member needs strong_axis_depth_along")
        y_hint = AXES[m.depth_along] if isinstance(m.depth_along, str) else np.asarray(m.depth_along, float)
        # local y = depth direction: v-deflection along the depth -> strong (Iz)
        sec = fem.Section(sp.A, Iy=sp.I_weak, Iz=sp.I_strong, J=sp.J, cy=sp.c_strong, cz=sp.c_weak,
                          w=sp.weight)
    else:
        y_hint = fem.default_y_hint(m.e)
        sec = fem.Section(sp.A, Iy=sp.I_weak, Iz=sp.I_strong, J=sp.J, cy=sp.c_strong, cz=sp.c_weak,
                          w=sp.weight)
    R = fem.rotation(m.e, y_hint)
    return sec, R


# --------------------------------------------------------------------------- validation
def validate_joints(geo: Geometry, snap_tol: float) -> list[str]:
    errors = []
    for j in geo.joints:
        used = {b.a for b in j.brackets if b.type != "none"} | {b.b for b in j.brackets if b.type != "none"}
        used |= {x.end_of for x in j.bearing} | {x.bears_on for x in j.bearing}
        for mid in j.members:
            if mid not in geo.members:
                errors.append(f"{j.id}: member M{mid} not in geometry")
                continue
            s, d = geo.members[mid].project(j.at)
            if d > snap_tol:
                errors.append(f"{j.id}: M{mid} centreline is {d * 1e3:.1f} mm from the joint (> snap tol)")
            if mid not in used:
                errors.append(f"{j.id}: M{mid} has no bracket and no bearing (modelling error)")
        for b in j.brackets:
            for mid in (b.a, b.b):
                if mid not in j.members:
                    errors.append(f"{j.id}: bracket {b.a}-{b.b} references M{mid} not in the joint's members")
            if b.type not in ("triangle", "plate_t5", "plate_other", "none"):
                errors.append(f"{j.id}: unknown bracket type {b.type!r}")
        for x in j.bearing:
            for mid in (x.end_of, x.bears_on):
                if mid not in j.members:
                    errors.append(f"{j.id}: bearing references M{mid} not in the joint's members")
    return errors


def _components(member_ids, links) -> list[set[int]]:
    adj = defaultdict(set)
    for a, b in links:
        adj[a].add(b)
        adj[b].add(a)
    seen, comps = set(), []
    for m in member_ids:
        if m in seen:
            continue
        comp, stack = set(), [m]
        while stack:
            k = stack.pop()
            if k in comp:
                continue
            comp.add(k)
            stack.extend(adj[k] - comp)
        seen |= comp
        comps.append(comp)
    return comps


# --------------------------------------------------------------------------- build
def build(geo: Geometry, p, mode: str = "3d") -> StandModel:
    si = p.si
    errors = validate_joints(geo, si.springs.snap_tol)
    if errors:
        raise ModelError("input errors:\n  " + "\n  ".join(errors))
    notes: list[str] = []

    # ---- member / joint selection (2D: front frame only, cross members removed)
    joints = geo.joints
    members = dict(geo.members)
    removed: dict[int, Member] = {}
    stubs: dict[tuple[str, int], float] = {}     # 2D: (joint, cross member) -> station on it
    stub_members: dict[int, Member] = {}
    if mode == "2d":
        yf, tol = si.model.front_frame_y, si.model.front_frame_tol
        keep = {i for i, m in members.items() if abs(m.p0[1] - yf) < tol and abs(m.p1[1] - yf) < tol}
        removed = {i: m for i, m in members.items() if i not in keep}

        def flat(v):
            w = v.copy()
            w[1] = yf
            return w
        # flatten onto the plane so in-plane forces have no out-of-plane lever arms
        members = {i: Member(m.id, flat(m.p0), flat(m.p1), m.profile, m.depth_along)
                   for i, m in members.items() if i in keep}
        # A removed cross member that brackets two or more front members together at one
        # joint is kept there as a zero-length stub node: in 3D the load between those
        # front members passes through its end (e.g. the M21/M32 splice through M26).
        for j in geo.joints:
            for c in j.members:
                if c in keep:
                    continue
                partners = {o for b in j.brackets if c in (b.a, b.b) and b.type != "none"
                            for o in (b.a, b.b) if o != c and o in keep}
                if len(partners) >= 2:
                    stubs[(j.id, c)] = geo.members[c].project(j.at)[0]
                    stub_members[c] = geo.members[c]
        if stubs:
            notes.append("2D: cross members kept as joint stubs (load path between front members): "
                         + ", ".join(f"M{c}@{jid}" for jid, c in sorted(stubs)))

        def alive(jid, mid):
            return mid in keep or (jid, mid) in stubs
        new = []
        for j in geo.joints:
            br = [b for b in j.brackets if alive(j.id, b.a) and alive(j.id, b.b)]
            be = [x for x in j.bearing if x.end_of in keep and alive(j.id, x.bears_on)]
            ms = [mm for mm in j.members if alive(j.id, mm)]
            if br or be:
                new.append(Joint(j.id, flat(j.at), ms, be, br))
        joints = new

    links = [(b.a, b.b) for j in joints for b in j.brackets if b.type != "none"]
    links += [(x.end_of, x.bears_on) for j in joints for x in j.bearing]
    comps = _components(sorted(set(members) | set(stub_members)), links)
    if mode == "3d":
        if len(comps) > 1:
            raise ModelError(f"frame is disconnected into {len(comps)} parts: "
                             + "; ".join(",".join(f"M{i}" for i in sorted(c)) for c in comps))
        # bracket-only connectivity (bearing OFF run)
        bcomps = _components(sorted(members), [(b.a, b.b) for j in joints for b in j.brackets
                                               if b.type != "none"])
        if len(bcomps) > 1:
            raise ModelError("frame is disconnected when bearing is OFF: "
                             + "; ".join(",".join(f"M{i}" for i in sorted(c)) for c in bcomps))

    # ---- load application point
    thrust_point = geo.thrust_point.copy()
    load_scale = 1.0
    thrust_member = geo.thrust_member
    if mode == "2d":
        load_scale = 0.5
        thrust_point[1] = si.model.front_frame_y
        if thrust_member not in members:
            # carried to the front frame member bracketed to the thrust member, at the front joint
            cand = []
            for j in geo.joints:
                if thrust_member in j.members:
                    for b in j.brackets:
                        other = b.b if b.a == thrust_member else b.a if b.b == thrust_member else None
                        if other in members:
                            cand.append((j, other))
            if not cand:
                raise ModelError("2D: thrust member does not connect to the front frame")
            j, other = cand[0]
            notes.append(f"2D: thrust/rocket loads (x0.5) moved from M{thrust_member} to "
                         f"M{other} at {j.id}")
            thrust_member = other
            thrust_point = members[other].point(members[other].project(thrust_point)[0])
        main = next(c for c in comps if thrust_member in c)
        dropped = sorted(set(members) - main)
        for key in [k for k in stubs if k[1] not in main]:
            stubs.pop(key)
        if dropped:
            notes.append("2D: dropped members disconnected from the loaded frame once cross "
                         "members are removed: " + ", ".join(f"M{i}" for i in dropped))
            for i in dropped:
                removed[i] = members.pop(i)
            def alive2(jid, mid):
                return mid in members or (jid, mid) in stubs
            joints = [Joint(j.id, j.at, [m for m in j.members if alive2(j.id, m)],
                            [x for x in j.bearing if x.end_of in members and alive2(j.id, x.bears_on)],
                            [b for b in j.brackets if alive2(j.id, b.a) and alive2(j.id, b.b)])
                      for j in joints]
            joints = [j for j in joints if j.brackets or j.bearing]

    # ---- stations along each member
    ground_mode = si.base.mode == "ground"
    if ground_mode and mode != "3d":
        raise ModelError("base.mode = ground is 3D only")
    merge = si.model.station_merge
    stations: dict[int, list[float]] = {i: [0.0, m.L] for i, m in members.items()}
    for j in joints:
        for mid in j.members:
            if mid in members:
                stations[mid].append(members[mid].project(j.at)[0])
    stub_members = {c: m for c, m in stub_members.items() if any(k[1] == c for k in stubs)}
    stations[thrust_member].append(members[thrust_member].project(thrust_point)[0])
    for (pm, s0, s1) in geo.thrust_patches:
        if pm in members:
            stations[pm] += [s0, s1, 0.5 * (s0 + s1)]

    x, node_member, node_s = [], [], []
    member_nodes, member_elements, elements, sections = {}, {}, [], {}
    for mid in sorted(members):
        m = members[mid]
        merged: list[float] = []
        for s in sorted(stations[mid]):
            if merged and s - merged[-1] <= merge:
                if s == m.L:
                    merged[-1] = m.L          # keep the exact end
                continue
            merged.append(s)
        fine = [merged[0]]
        for s0, s1 in zip(merged[:-1], merged[1:]):
            msub = (si.ground.spacing if ground_mode and mid in geo.base_members else si.model.max_subelement)
            n = max(1, int(np.ceil((s1 - s0) / msub - 1e-9)))
            fine += list(np.linspace(s0, s1, n + 1)[1:])
        sec, R = member_section(m, p)
        sections[mid] = sec
        ids = []
        for s in fine:
            ids.append(len(x))
            x.append(m.point(s))
            node_member.append(mid)
            node_s.append(float(s))
        member_nodes[mid] = ids
        member_elements[mid] = []
        for n1, n2 in zip(ids[:-1], ids[1:]):
            member_elements[mid].append(len(elements))
            elements.append(fem.FrameElement(n1, n2, R, float(node_s[n2] - node_s[n1]), sec, mid))
    stub_node = {}
    for (jid, c), s_c in sorted(stubs.items()):
        sec_c, _ = member_section(stub_members[c], p)
        sections[c] = sec_c
        pt = stub_members[c].point(s_c)
        pt[1] = si.model.front_frame_y
        stub_node[(jid, c)] = len(x)
        x.append(pt)
        node_member.append(c)
        node_s.append(float(s_c))
    x = np.array(x)
    geo_of = {**members, **stub_members}

    def nearest_node(mid: int, s: float) -> int:
        ids = member_nodes[mid]
        return ids[int(np.argmin([abs(node_s[i] - s) for i in ids]))]

    joint_node = dict(stub_node)
    for j in joints:
        for mid in j.members:
            if mid in members:
                joint_node[(j.id, mid)] = nearest_node(mid, members[mid].project(j.at)[0])
    thrust_node = nearest_node(thrust_member, members[thrust_member].project(thrust_point)[0])

    E, G = si.material.E, si.material.G

    def EA_L(mid):
        return E * sections[mid].A / geo_of[mid].L

    def EI_L(mid):
        return E * min(sections[mid].Iy, sections[mid].Iz) / geo_of[mid].L

    brackets = []
    for j in joints:
        for k, b in enumerate(j.brackets):
            if b.type == "none":
                continue
            for c in range(b.count):
                brackets.append(BracketSpring(
                    j.id, k, c, b.type, b.a, b.b, b.face, b.note,
                    joint_node[(j.id, b.a)], joint_node[(j.id, b.b)], j.at.copy(),
                    min(EA_L(b.a), EA_L(b.b)), min(EI_L(b.a), EI_L(b.b))))

    bearings = []
    for j in joints:
        for be in j.bearing:
            m = members[be.end_of]
            s, _ = m.project(j.at)
            at_end_1 = s > m.L / 2
            n_end = member_nodes[be.end_of][-1 if at_end_1 else 0]
            nvec = m.e if at_end_1 else -m.e
            n_on = joint_node[(j.id, be.bears_on)]
            bearings.append(BearingSpring(j.id, be.end_of, be.bears_on, n_end, n_on, nvec,
                                          si.springs.k_bearing_factor * EA_L(be.end_of)))

    # ---- 2D: lump half of each removed cross member's weight onto the front frame
    lumped = []
    if mode == "2d" and si.loads.self_weight:
        for rid, rm in removed.items():
            if abs(rm.p1[1] - rm.p0[1]) < si.model.front_frame_tol:
                continue            # side-frame member (back frame = other half; dropped front: lost)
            targets = sorted({nearest_node(mid, members[mid].project(j.at)[0])
                              for j in geo.joints if rid in j.members
                              for mid in j.members if mid in members})
            if targets:
                W = 0.5 * rm.L * sections_weight(rm, p)
                for t in targets:
                    lumped.append(PointLoad(t, np.array([0, 0, -W / len(targets)]), x[t].copy(),
                                            f"half weight M{rid}"))
        dropped_front = [i for i, rm in removed.items()
                         if abs(rm.p0[1] - si.model.front_frame_y) < si.model.front_frame_tol]
        if dropped_front:
            notes.append("2D: self-weight of dropped front members not included")

    # ---- base members and restraint
    base_members = [i for i in geo.base_members if i in members]
    base_elements = [e for i in base_members for e in member_elements[i]]
    base_nodes = sorted({n for i in base_members for n in member_nodes[i]})
    # restrain only at joint nodes (never a cantilever tip, which would swing the frame)
    base_joint_nodes = sorted({n for (jid, mid), n in joint_node.items() if mid in base_members})
    if base_nodes:
        fixed, fixed_plane, desc = choose_restraint(x, base_joint_nodes or base_nodes, mode,
                                                    node_member, node_s)
    else:                       # test models: caller supplies supports
        fixed, fixed_plane, desc = [], [], []
    if mode == "2d":
        for n in range(len(x)):
            fixed_plane += [6 * n + 1, 6 * n + 3, 6 * n + 5]       # uy, rx, rz
    ground = []
    if ground_mode:
        # the ground carries the stand: no 3-2-1 restraint; one contact spring per base node,
        # at the beam underside (half depth below the centreline)
        fixed, desc = [], ["none: base on compression-only ground springs"]
        z_c = min(x[n][2] for n in base_nodes)
        for mid in base_members:
            ns = member_nodes[mid]
            ss = [node_s[n] for n in ns]
            half = sections[mid].cz            # half the vertical depth (weak-axis fibre) of a flat base beam
            for k, n in enumerate(ns):
                lo = ss[k] - (ss[k] - ss[k - 1]) / 2 if k > 0 else ss[k]
                hi = ss[k] + (ss[k + 1] - ss[k]) / 2 if k < len(ns) - 1 else ss[k]
                P = np.array([x[n][0], x[n][1], z_c - half])
                ground.append(GroundContact(n, mid, hi - lo, P, P - np.asarray(x[n])))
        notes.append(f"ground mode: {len(ground)} contact springs on {len(base_members)} base members, "
                     f"no 3-2-1 restraint")

    return StandModel(geo, mode, members, sections, x, node_member, node_s, member_nodes, elements,
                      member_elements, joint_node, brackets, bearings, joints, thrust_node,
                      thrust_point, load_scale, base_elements, base_nodes, fixed, fixed_plane, desc, lumped,
                      notes, stub_members, E, G, ground,
                      [t for t in geo.thrust_patches if t[0] in members],
                      [nearest_node(t[0], 0.5 * (t[1] + t[2])) for t in geo.thrust_patches if t[0] in members])


def sections_weight(m: Member, p) -> float:
    return getattr(p.si, f"section_{m.profile}").weight


def choose_restraint(x, base_nodes, mode, node_member, node_s):
    """Statically determinate 3-2-1 (3D) or 2-1 (2D) restraint on base nodes spread far apart."""
    P = x[base_nodes]
    c = P.mean(axis=0)
    A = base_nodes[int(np.argmax(np.linalg.norm(P - c, axis=1)))]
    B = base_nodes[int(np.argmax(np.linalg.norm(P - x[A], axis=1)))]
    ab = (x[B] - x[A]) / np.linalg.norm(x[B] - x[A])
    d = [np.linalg.norm(np.cross(x[n] - x[A], ab)) for n in base_nodes]
    C = base_nodes[int(np.argmax(d))]

    def tag(n):
        return f"M{node_member[n]}@{node_s[n] * 1e3:.0f}mm"

    if mode == "2d":
        fixed = [6 * A + 0, 6 * A + 2, 6 * B + 2]
        desc = [f"{tag(A)}: ux uz", f"{tag(B)}: uz"]
        return fixed, [], desc
    if max(d) < 1e-3:
        raise ModelError("base nodes are collinear; cannot place a 3-2-1 restraint")
    along = int(np.argmax(np.abs(ab)))
    two = [k for k in range(3) if k != along]
    normal = np.cross(ab, x[C] - x[A])
    one = int(np.argmax(np.abs(normal)))
    fixed = [6 * A + 0, 6 * A + 1, 6 * A + 2] + [6 * B + k for k in two] + [6 * C + one]
    desc = [f"{tag(A)}: ux uy uz", f"{tag(B)}: " + " ".join(DOF_NAMES[k] for k in two),
            f"{tag(C)}: {DOF_NAMES[one]}"]
    return fixed, [], desc


def relative_to_base(model: "StandModel", u: np.ndarray) -> np.ndarray:
    """u minus the least-squares rigid-body motion of the base nodes (ground-relative motion)."""
    Rb = rigid_body_modes(model.x)
    if model.mode == "2d":
        Rb = Rb[:, [0, 2, 4]]                   # in-plane: ux, uz, ry
    rows = np.r_[[6 * n + k for n in model.base_nodes for k in range(3)]]
    c, *_ = np.linalg.lstsq(Rb[rows], u[rows], rcond=None)
    return u - Rb @ c


def rigid_body_modes(x: np.ndarray) -> np.ndarray:
    """(6n, 6) rigid-body displacement modes about the origin."""
    n = len(x)
    Rb = np.zeros((6 * n, 6))
    for i, p in enumerate(x):
        Rb[6 * i:6 * i + 3, :3] = np.eye(3)
        Rb[6 * i:6 * i + 3, 3:] = -fem.skew(p)
        Rb[6 * i + 3:6 * i + 6, 3:] = np.eye(3)
    return Rb


# --------------------------------------------------------------------------- load cases
_CASE_RE = re.compile(r"([+-])([xy])")


def parse_case(name: str) -> tuple[float, float]:
    if name == "none":
        return 0.0, 0.0
    parts = _CASE_RE.findall(name)
    if not parts or "".join(s + a for s, a in parts) != name:
        raise ValueError(f"cannot parse load case {name!r} (use none, +x, -y, +x+y, ...)")
    sx = sy = 0.0
    for s, a in parts:
        v = 1.0 if s == "+" else -1.0
        if a == "x":
            sx = v
        else:
            sy = v
    return sx, sy
