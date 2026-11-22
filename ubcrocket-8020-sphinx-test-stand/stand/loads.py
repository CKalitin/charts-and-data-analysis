"""Load cases: thrust, rocket weight, misalignment, self-weight, sandbag base line load.

The base is not fixed. The resultant (force + moment) of every applied load is
cancelled by a line load on the base members,

    q(p) = [cx - w*dy,  cy + w*dx,  a + bx*dx + by*dy]      (N/m, d = p - centroid)

i.e. uniform horizontal + vertical parts for the forces, a linear vertical part for
the overturning moments and a "torsional" horizontal part for the yaw moment.
Six unknowns, six equations, solved exactly; the 3-2-1 restraint then only removes
rigid-body motion and its reactions must vanish.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import fem
from .model import StandModel, parse_case


@dataclass
class CaseLoads:
    name: str
    F: np.ndarray                         # global nodal load vector (applied + base), N / N·m
    elem_q: dict[int, tuple[np.ndarray, np.ndarray]]   # element -> (q1, q2) global N/m
    feq_local: dict[int, np.ndarray]      # element -> consistent nodal loads (local)
    point: list                           # (node, F, at, what)
    applied_resultant: np.ndarray         # [F; M about base centroid] of applied loads (no base)
    base_resultant: np.ndarray
    base_theta: np.ndarray                # [cx, cy, a, bx, by, w]
    base_centroid: np.ndarray
    base_q_range: tuple[float, float]     # min/max vertical base q (N/m, +up)
    base_length: float
    summary: dict = field(default_factory=dict)


def _segment_resultant(p1, p2, q1, q2, c) -> np.ndarray:
    """[F; M about c] of a load varying linearly q1 -> q2 along segment p1 -> p2 (Simpson: exact)."""
    L = np.linalg.norm(p2 - p1)
    pm, qm = 0.5 * (p1 + p2), 0.5 * (q1 + q2)
    F = L * qm
    M = L / 6 * (np.cross(p1 - c, q1) + 4 * np.cross(pm - c, qm) + np.cross(p2 - c, q2))
    return np.r_[F, M]


def _point_resultant(F, at, c) -> np.ndarray:
    return np.r_[F, np.cross(at - c, F)]


def base_q(theta, p, c) -> np.ndarray:
    dx, dy = p[0] - c[0], p[1] - c[1]
    cx, cy, a, bx, by, w = theta
    return np.array([cx - w * dy, cy + w * dx, a + bx * dx + by * dy])


@dataclass
class Bags:
    """Sandbags sized by rigid-body statics (ground mode)."""
    stations: list[tuple[int, float, float]]      # (member, centre s, length) SI
    kg_each: float
    kg_needed: float                              # before rounding
    gov: str                                      # what sized them
    hull: np.ndarray                              # footprint polygon (plan, CCW), m
    z0: float                                     # ground level
    checks: list[dict] = field(default_factory=list)   # per case: worst edge, FS achieved

    @property
    def total_kg(self) -> float:
        return self.kg_each * len(self.stations)

    def points(self, model: StandModel) -> np.ndarray:
        return np.array([model.members[mid].point(s) for mid, s, _ in self.stations])


def _applied(model: StandModel, p, case: str):
    """Point loads + element loads of the applied (non-base) loads, and their resultant
    split into destabilising (thrust, misalignment) and gravity parts, about c."""
    si = p.si
    sc = model.load_scale
    T = si.loads.thrust * si.loads.DF
    sx, sy = parse_case(case)
    if model.mode == "2d" and sy:
        raise ValueError(f"2D mode has no out-of-plane case ({case})")
    tp = model.thrust_point
    dest = [(model.thrust_node, np.array([0, 0, sc * T]), tp, f"thrust {T:.0f} N x{sc:g}")]
    grav = [(model.thrust_node, np.array([0, 0, -sc * si.loads.rocket_weight]), tp, "rocket weight")]
    if sx or sy:
        Fh = sc * T * np.array([sx * si.loads.misalign_x, sy * si.loads.misalign_y, 0.0])
        dest.append((model.thrust_node, Fh, tp, f"misalignment {case}"))
    for pl in model.lumped:
        grav.append((pl.node, pl.F, pl.at, pl.what))
    elem_q: dict[int, list[np.ndarray]] = {}
    if si.loads.self_weight:
        for k, e in enumerate(model.elements):
            q = np.array([0, 0, -e.sec.w])
            elem_q[k] = [q.copy(), q.copy()]
    X = model.x
    base = model.base_elements
    Ls = np.array([model.elements[k].L for k in base])
    mids = np.array([0.5 * (X[model.elements[k].n1] + X[model.elements[k].n2]) for k in base])
    c = (Ls[:, None] * mids).sum(0) / Ls.sum()
    R_dest, R_grav = np.zeros(6), np.zeros(6)
    for (_, F, at, _) in dest:
        R_dest += _point_resultant(F, at, c)
    for (_, F, at, _) in grav:
        R_grav += _point_resultant(F, at, c)
    for k, (q1, q2) in elem_q.items():
        e = model.elements[k]
        R_grav += _segment_resultant(X[e.n1], X[e.n2], q1, q2, c)
    point = spread_on_patches(model, dest + grav, elem_q)
    return point, elem_q, R_dest, R_grav, c, Ls


def spread_on_patches(model: StandModel, point: list, elem_q: dict) -> list:
    """Rigid load plate: loads acting at the thrust node are shared equally between the
    plate's bearing patches (uniform line load over each patch); other point loads stay."""
    if not model.thrust_patches:
        return point
    keep = [pt for pt in point if pt[0] != model.thrust_node]
    moved = [pt for pt in point if pt[0] == model.thrust_node]
    share = 1.0 / len(model.thrust_patches)
    for (_, F, _, _) in moved:
        for mid, s0, s1 in model.thrust_patches:
            Lp = s1 - s0
            for k in model.member_elements[mid]:
                e = model.elements[k]
                a, b = model.node_s[e.n1], model.node_s[e.n2]
                ov = max(0.0, min(b, s1) - max(a, s0))
                if ov <= 0:
                    continue
                q = share * F / Lp * ov / e.L          # exact total per element, smeared over it
                cur = elem_q.setdefault(k, [np.zeros(3), np.zeros(3)])
                cur[0] = cur[0] + q
                cur[1] = cur[1] + q
    return keep


def footprint(model: StandModel) -> tuple[np.ndarray, float]:
    """Plan convex hull (CCW) of the base member ends, and ground level (beam undersides)."""
    from scipy.spatial import ConvexHull
    pts = np.array([q[:2] for mid in model.geo.base_members if mid in model.members
                    for q in (model.members[mid].p0, model.members[mid].p1)])
    h = ConvexHull(pts)
    z0 = min(c.P[2] for c in model.ground) if model.ground else float(model.x[model.base_nodes][:, 2].min())
    return pts[h.vertices], z0


def edge_moment(R: np.ndarray, c: np.ndarray, A: np.ndarray, t: np.ndarray) -> float:
    """Moment of resultant R = [F; M about c] about the line through A along t (+ = tips over it
    when t runs CCW round the footprint)."""
    return float((R[3:] + np.cross(c - A, R[:3])) @ t)


def size_sandbags(model: StandModel, p, cases: list[str]) -> Bags:
    """Equal bag mass per station so that, as a rigid body on its footprint, the stand has
    FS_tip against tipping over every footprint edge and against lift, in every case:
        W * sum_k d_k,e  >=  FS * M_dest,e - M_grav,e        (per edge e)
        n * W            >=  FS * F_up - W_frame             (lift)
    d_k,e = inward distance of bag k from edge e (plan)."""
    si = p.si
    sb = si.sandbags
    stations = [(int(m), float(s) * 1e-3, float(L) * 1e-3) for m, s, L in sb.stations]
    for mid, s, L in stations:
        if mid not in model.members or not (0 <= s - L / 2 and s + L / 2 <= model.members[mid].L + 1e-9):
            raise ValueError(f"sandbag station M{mid} @ {s * 1e3:.0f} mm (length {L * 1e3:.0f}) is off its member")
    hull, z0 = footprint(model)
    bp = np.array([model.members[mid].point(s) for mid, s, _ in stations])
    FS = sb.FS_tip
    need, gov, checks = 0.0, "", []
    for case in cases:
        _, _, Rd, Rg, c, _ = _applied(model, p, case)
        worst = None
        for i in range(len(hull)):
            A2, B2 = hull[i], hull[(i + 1) % len(hull)]
            A = np.r_[A2, z0]
            t = np.r_[(B2 - A2) / np.linalg.norm(B2 - A2), 0.0]
            Md, Mg = edge_moment(Rd, c, A, t), -edge_moment(Rg, c, A, t)    # Mg > 0 stabilises
            rel = bp[:, :2] - A2
            d = t[0] * rel[:, 1] - t[1] * rel[:, 0]                        # inward distance
            if Md <= 0:
                continue
            w = (FS * Md - Mg) / d.sum() if d.sum() > 0 else np.inf
            if worst is None or w > worst[0]:
                worst = (w, i, Md, Mg, d.sum())
            if w > need:
                need, gov = w, f"tipping over footprint edge {i} ({A2[0]*1e3:.0f},{A2[1]*1e3:.0f})->" \
                               f"({B2[0]*1e3:.0f},{B2[1]*1e3:.0f}) mm, case {case}"
        w_lift = (FS * Rd[2] + Rg[2]) / len(stations)                       # Rg[2] < 0 (weight)
        if w_lift > need:
            need, gov = w_lift, f"lift, case {case}"
        checks.append({"case": case, "edge": worst[1] if worst else None, "M_over": worst[2] if worst else 0.0,
                       "M_frame": worst[3] if worst else 0.0, "sum_d": worst[4] if worst else 0.0,
                       "F_up": Rd[2], "W_frame": -Rg[2]})
    g = si.model.g
    kg = max(need, 0.0) / g
    kg_r = float(np.ceil(kg / sb.round_to - 1e-9) * sb.round_to) if sb.round_to > 0 else kg
    bags = Bags(stations, kg_r, kg, gov, hull, z0, checks)
    for ch in bags.checks:                         # FS actually achieved with the rounded bags
        W = kg_r * g
        ch["FS_tip"] = ((W * ch["sum_d"] + ch["M_frame"]) / ch["M_over"]) if ch["M_over"] > 0 else np.inf
        ch["FS_lift"] = (W * len(stations) + ch["W_frame"]) / ch["F_up"] if ch["F_up"] > 0 else np.inf
    return bags


def build_case(model: StandModel, p, case: str, bags: Bags | None = None) -> CaseLoads:
    if model.ground_mode:
        return _build_ground_case(model, p, case, bags)
    return _build_line_case(model, p, case)


def _build_ground_case(model: StandModel, p, case: str, bags: Bags) -> CaseLoads:
    """Applied loads + sandbags; the ground springs supply the rest (no assumed base load)."""
    si = p.si
    point, elem_q, Rd, Rg, c, Ls = _applied(model, p, case)
    X = model.x
    W = bags.kg_each * si.model.g
    R_bags = np.zeros(6)
    for mid, s, L in bags.stations:          # uniform line load over the bag, element by element
        a, b = s - L / 2, s + L / 2
        q = np.array([0, 0, -W / L])
        for k in model.member_elements[mid]:
            e = model.elements[k]
            s1, s2 = model.node_s[e.n1], model.node_s[e.n2]
            ov = max(0.0, min(b, s2) - max(a, s1))
            if ov <= 0:
                continue
            qe = q * ov / e.L                 # exact total force, smeared over the element
            cur = elem_q.setdefault(k, [np.zeros(3), np.zeros(3)])
            cur[0] = cur[0] + qe
            cur[1] = cur[1] + qe
            R_bags += _segment_resultant(X[e.n1], X[e.n2], qe, qe, c)
    F = np.zeros(model.n_dof)
    for (n, Fp, at, _) in point:
        F[6 * n:6 * n + 3] += Fp
        F[6 * n + 3:6 * n + 6] += np.cross(at - X[n], Fp)
    feq_local = {}
    for k, (q1, q2) in elem_q.items():
        e = model.elements[k]
        fl = fem.linear_load_feq(e.L, e.R @ q1, e.R @ q2)
        feq_local[k] = fl
        F[e.dofs] += fem.big_T(e.R).T @ fl
    g = si.model.g
    R_app = Rd + Rg
    summary = {
        "thrust_factored_N": model.load_scale * si.loads.thrust * si.loads.DF,
        "Fz_applied_N": R_app[2], "sandbag_net_kg": R_app[2] / g, "sandbag_uniform_kg": np.nan,
        "F_horizontal_N": float(np.hypot(R_app[0], R_app[1])),
        "M_overturn_Nm": float(np.hypot(R_app[3], R_app[4])), "M_yaw_Nm": float(R_app[5]),
        "bags_kg_each": bags.kg_each, "bags_total_kg": bags.total_kg, "bags_gov": bags.gov,
    }
    return CaseLoads(case, F, {k: (v[0], v[1]) for k, v in elem_q.items()}, feq_local, point,
                     R_app, R_bags, np.zeros(6), c, (0.0, 0.0), float(Ls.sum()), summary)


def _build_line_case(model: StandModel, p, case: str) -> CaseLoads:
    si = p.si
    sc = model.load_scale
    T = si.loads.thrust * si.loads.DF
    sx, sy = parse_case(case)
    if model.mode == "2d" and sy:
        raise ValueError(f"2D mode has no out-of-plane case ({case})")
    tp = model.thrust_point
    point = [
        (model.thrust_node, np.array([0, 0, sc * T]), tp, f"thrust {T:.0f} N x{sc:g}"),
        (model.thrust_node, np.array([0, 0, -sc * si.loads.rocket_weight]), tp, "rocket weight"),
    ]
    if sx or sy:
        Fh = sc * T * np.array([sx * si.loads.misalign_x, sy * si.loads.misalign_y, 0.0])
        point.append((model.thrust_node, Fh, tp, f"misalignment {case}"))
    for pl in model.lumped:
        point.append((pl.node, pl.F, pl.at, pl.what))

    elem_q: dict[int, list[np.ndarray]] = {}
    if si.loads.self_weight:
        for k, e in enumerate(model.elements):
            q = np.array([0, 0, -e.sec.w])
            elem_q[k] = [q.copy(), q.copy()]
    point = spread_on_patches(model, point, elem_q)

    # ---- resultant of applied loads about the base centroid
    X = model.x
    base = model.base_elements
    Ls = np.array([model.elements[k].L for k in base])
    mids = np.array([0.5 * (X[model.elements[k].n1] + X[model.elements[k].n2]) for k in base])
    c = (Ls[:, None] * mids).sum(0) / Ls.sum()
    R_app = np.zeros(6)
    for (_, F, at, _) in point:
        R_app += _point_resultant(F, at, c)
    for k, (q1, q2) in elem_q.items():
        e = model.elements[k]
        R_app += _segment_resultant(X[e.n1], X[e.n2], q1, q2, c)

    # ---- solve the base line load
    A = np.zeros((6, 6))
    for j in range(6):
        th = np.zeros(6)
        th[j] = 1.0
        for k in base:
            e = model.elements[k]
            p1, p2 = X[e.n1], X[e.n2]
            A[:, j] += _segment_resultant(p1, p2, base_q(th, p1, c), base_q(th, p2, c), c)
    theta, *_ = np.linalg.lstsq(A, -R_app, rcond=None)
    R_base = A @ theta
    resid = np.abs(R_base + R_app).max()
    if resid > 1e-6 * max(1.0, np.abs(R_app).max()):
        raise RuntimeError(f"base line load cannot balance applied loads (residual {resid:.3g})")
    qz = []
    for k in base:
        e = model.elements[k]
        q1, q2 = base_q(theta, X[e.n1], c), base_q(theta, X[e.n2], c)
        qz += [q1[2], q2[2]]
        cur = elem_q.setdefault(k, [np.zeros(3), np.zeros(3)])
        cur[0] = cur[0] + q1
        cur[1] = cur[1] + q2

    # ---- nodal vector
    F = np.zeros(model.n_dof)
    for (n, Fp, at, _) in point:
        F[6 * n:6 * n + 3] += Fp
        F[6 * n + 3:6 * n + 6] += np.cross(at - X[n], Fp)
    feq_local = {}
    for k, (q1, q2) in elem_q.items():
        e = model.elements[k]
        fl = fem.linear_load_feq(e.L, e.R @ q1, e.R @ q2)
        feq_local[k] = fl
        F[e.dofs] += fem.big_T(e.R).T @ fl

    g = si.model.g
    uplift = R_app[2]
    summary = {
        "thrust_factored_N": sc * T,
        "Fz_applied_N": uplift,
        "sandbag_net_kg": uplift / g,
        # uniform bags on every base member must cover the most-downward demand
        "sandbag_uniform_kg": max(0.0, -min(qz)) * Ls.sum() / g,
        "F_horizontal_N": float(np.hypot(R_app[0], R_app[1])),
        "M_overturn_Nm": float(np.hypot(R_app[3], R_app[4])),
        "M_yaw_Nm": float(R_app[5]),
    }
    return CaseLoads(case, F, {k: (v[0], v[1]) for k, v in elem_q.items()}, feq_local, point,
                     R_app, R_base, theta, c, (min(qz), max(qz)), float(Ls.sum()), summary)


def nodal_resultant(F: np.ndarray, x: np.ndarray, about: np.ndarray) -> np.ndarray:
    """[F; M] about a point of a nodal load vector (forces + moments)."""
    f = F.reshape(-1, 6)
    return np.r_[f[:, :3].sum(0), (np.cross(x - about, f[:, :3]) + f[:, 3:]).sum(0)]
