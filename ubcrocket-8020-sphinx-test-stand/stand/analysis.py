"""Runs: k_theta (P / R) x bearing (ON / OFF) x load case, plus the k_theta sweep.

Each solve -> member checks, joint checks, equilibrium + restraint audit, frame
buckling factor.  The design value of every item is the worst over all VALID
solves; a run-P solve is invalid ("mechanism") when any node moves more than
checks.mechanism_disp, and run R is then used for that case.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from . import fem, joints, loads, members
from .model import StandModel, relative_to_base


@dataclass(frozen=True)
class RunSpec:
    name: str           # "P" | "R" | "k=0.01"
    k_theta: float      # factor on EI/L
    bearing: bool

    @property
    def label(self) -> str:
        return f"{self.name}-b{'ON' if self.bearing else 'OFF'}"


@dataclass
class Solve:
    run: RunSpec
    case: str
    u: np.ndarray                         # raw solution (3-2-1 frame)
    ur: np.ndarray                        # relative to the base rigid fit (report/plot this)
    loads: loads.CaseLoads
    active: tuple[bool, ...]
    bearing_iters: int
    bearing_forces: np.ndarray            # compression +, N
    internal: dict[int, np.ndarray]
    axial: np.ndarray                     # per element, tension +
    bracket_W: list[np.ndarray]
    member_rows: dict[int, dict]
    joint_rows: list[dict]
    max_disp: float
    max_disp_node: int
    thrust_disp: np.ndarray
    thrust_tilt_deg: float
    eq_residual: float                    # |applied + base + reactions| / thrust
    restraint_rel: float                  # max |3-2-1 restraint reaction| / thrust
    plane_rel: float                      # 2D: max |out-of-plane constraint reaction| / thrust
    lam: float = np.nan
    phi: np.ndarray | None = None
    valid: bool = True
    note: str = ""

    @property
    def key(self) -> str:
        return f"{self.run.label}/{self.case}"


@dataclass
class Study:
    model: StandModel
    solves: list[Solve]
    sweep: list[Solve]
    sweep_case: str
    sweep_bearing: bool
    mechanism_cases: list[str]
    eig_checks: list[dict]
    caps: joints.Caps
    timings: dict = field(default_factory=dict)


class Engine:
    def __init__(self, model: StandModel, p):
        self.m, self.p = model, p
        self.si = p.si
        self.caps = joints.capacities(p)
        joints.prepare(model, p)
        self.K_frame = fem.assemble(model.n_nodes, model.elements, [], model.E, model.G)
        self.bear_springs = [b.spring(model) for b in model.bearings]
        self.K_bear = [s.k_global() for s in self.bear_springs]
        self.segs = {mid: members.braced_segments(model, mid, p) for mid in model.members}
        self.case_loads: dict[str, loads.CaseLoads] = {}
        self._kbr: dict[float, tuple[np.ndarray, list[fem.Spring]]] = {}

    # ---------------------------------------------------------------- assembly
    def bracket_K(self, kr_f: float):
        if kr_f not in self._kbr:
            springs = [b.spring(self.m, self.si.springs.k_t_factor, kr_f) for b in self.m.brackets]
            K = np.zeros_like(self.K_frame)
            for s in springs:
                d = s.dofs
                K[np.ix_(d, d)] += s.k_global()
            self._kbr[kr_f] = (K, springs)
        return self._kbr[kr_f]

    def K_for(self, kr_f: float, active) -> np.ndarray:
        K = self.K_frame + self.bracket_K(kr_f)[0]
        for on, s, kb in zip(active, self.bear_springs, self.K_bear):
            if on:
                d = s.dofs
                K[np.ix_(d, d)] += kb
        return K

    def loads_for(self, case: str) -> loads.CaseLoads:
        if case not in self.case_loads:
            self.case_loads[case] = loads.build_case(self.m, self.p, case)
        return self.case_loads[case]

    # ---------------------------------------------------------------- solve
    def solve(self, run: RunSpec, case: str, cache: dict) -> Solve:
        m = self.m
        L = self.loads_for(case)
        nb = len(m.bearings)
        active = tuple([run.bearing] * nb)
        seen = []
        it = 0
        while True:
            it += 1
            key = (run.k_theta, active)
            if key not in cache:
                cache[key] = fem.Solver(self.K_for(run.k_theta, active), m.all_fixed)
            S = cache[key]
            u = S.solve(L.F)
            if not run.bearing:
                break
            gaps = np.array([(s.rel(u)[:3] @ b.n) for s, b in zip(self.bear_springs, m.bearings)])
            # rel = motion of end_of (b side) relative to bears_on at X; closing if > 0
            new = tuple(bool(g > 0) for g in gaps)
            if new == active:
                break
            if new in seen or it > 60:
                break                       # cycling: keep the last solved (consistent) set
            seen.append(active)
            active = new
        bearing_forces = np.array([
            (s.Ks[:3, :3] @ s.rel(u)[:3]) @ b.n if on else 0.0
            for s, b, on in zip(self.bear_springs, m.bearings, active)])
        return self._post(run, case, u, L, active, it, bearing_forces, S)

    def _post(self, run, case, u, L, active, it, bearing_forces, S) -> Solve:
        m, si = self.m, self.si
        E, G = m.E, m.G
        internal, axial = {}, np.zeros(len(m.elements))
        for k, e in enumerate(m.elements):
            f = fem.element_end_forces(e, u, E, G, L.feq_local.get(k))
            q1, q2 = L.elem_q.get(k, (np.zeros(3), np.zeros(3)))
            internal[k] = fem.internal_forces(e, f, e.R @ q1, e.R @ q2)
            axial[k] = 0.5 * (internal[k][0, 1] + internal[k][-1, 1])
        springs = self.bracket_K(run.k_theta)[1]
        Wb = [s.wrench_on_b(u) for s in springs]

        member_rows = {mid: members.check_member(m, mid, internal, self.segs[mid], self.p)
                       for mid in m.members}
        joint_rows = []
        for i, (br, W) in enumerate(zip(m.brackets, Wb)):
            desc, rows, nopt = joints.check_bracket(br, W, self.caps)
            for r in rows:
                r.update(spring=i, joint=br.joint, bracket=br.index, copy=br.copy, type=br.type,
                         option=desc, n_options=nopt, a=br.a, b=br.b, note=br.note)
                joint_rows.append(r)

        ur = relative_to_base(m, u)               # deformation relative to the ground
        disp = np.linalg.norm(ur.reshape(-1, 6)[:, :3], axis=1)
        i_max = int(np.argmax(disp))
        ut = ur[6 * m.thrust_node:6 * m.thrust_node + 6]
        tilt = np.degrees(np.hypot(ut[3], ut[4]))
        # equilibrium audit: applied + base (in F) + reactions must vanish
        R = np.zeros(m.n_dof)
        R[S.fixed] = S.reactions(u, L.F)
        T = L.summary["thrust_factored_N"]
        res = loads.nodal_resultant(L.F + R, m.x, L.base_centroid)
        eq = float(np.abs(res).max() / T)
        restraint = np.zeros(m.n_dof)
        restraint[m.fixed] = R[m.fixed]
        rel = float(np.abs(restraint).max() / T)
        plane = float(np.abs(R[m.fixed_plane]).max() / T) if m.fixed_plane else 0.0
        return Solve(run, case, u, ur, L, active, it, bearing_forces, internal, axial, Wb, member_rows,
                     joint_rows, float(disp[i_max]), i_max, ut[:3].copy(), float(tilt), eq, rel, plane)

    # ---------------------------------------------------------------- stability
    def buckling(self, s: Solve, cache) -> None:
        m = self.m
        S = cache[(s.run.k_theta, s.active)]
        Kg = fem.assemble_kg(m.n_nodes, m.elements, s.axial)
        f = S.free
        lam, phi = fem.buckling_lambda(S.Kff, Kg[np.ix_(f, f)])
        s.lam = float(lam)
        if phi is not None:
            full = np.zeros(m.n_dof)
            full[f] = phi
            s.phi = full

    def eig_check(self, run: RunSpec, cache) -> dict:
        m = self.m
        active = tuple([run.bearing] * len(m.bearings))
        key = (run.k_theta, active)
        if key not in cache:
            cache[key] = fem.Solver(self.K_for(run.k_theta, active), m.all_fixed)
        S = cache[key]
        vals, vecs = fem.lowest_modes(S.Kff, k=6)
        tol = self.si.checks.mech_eig_rel_tol
        v = np.zeros(m.n_dof)
        v[S.free] = vecs[:, 0]
        top = np.argsort(-np.abs(v))[:6]
        return {"run": run.label, "lowest": vals.tolist(), "mechanism": bool(vals[0] < tol),
                "mode_dofs": [(m.dof_label(int(d)), float(v[d])) for d in top]}


def default_runs(p) -> list[RunSpec]:
    s = p.si.springs
    return [RunSpec("P", s.k_theta_pinned, True), RunSpec("P", s.k_theta_pinned, False),
            RunSpec("R", s.k_theta_rigid, True), RunSpec("R", s.k_theta_rigid, False)]


def item_U(s: Solve) -> dict[str, float]:
    """Utilisation (1/SF) of every item in a solve, keyed by item id."""
    out = {f"M{mid}": 1.0 / r["SF"] if r["SF"] > 0 else np.inf for mid, r in s.member_rows.items()}
    for r in s.joint_rows:
        if np.isfinite(r["U"]):
            k = f"{r['joint']}#{r['bracket']}.{r['copy']}:{r['leg']}"
            out[k] = max(out.get(k, 0.0), r["U"])
    return out


def run_study(model: StandModel, p, cases: list[str] | None = None, log=print) -> Study:
    t0 = time.time()
    eng = Engine(model, p)
    si = p.si
    cases = cases or list(si.loads.cases)
    if model.mode == "2d":
        skipped = [c for c in cases if loads.parse_case(c)[1] != 0]
        if skipped:
            log(f"2D: skipping out-of-plane cases {', '.join(skipped)}")
        cases = [c for c in cases if loads.parse_case(c)[1] == 0]
    cache: dict = {}
    eig = [eng.eig_check(r, cache) for r in default_runs(p)]
    for e in eig:
        if e["mechanism"] and e["run"].startswith("R"):
            dofs = "\n    ".join(f"{d}: {v:+.3f}" for d, v in e["mode_dofs"])
            raise RuntimeError(f"mechanism in run {e['run']} (lowest eig ratio {e['lowest'][0]:.2e}); "
                               f"mode dominated by:\n    {dofs}")
    t1 = time.time()
    solves = []
    for run in default_runs(p):
        for c in cases:
            solves.append(eng.solve(run, c, cache))
    lim = si.checks.mechanism_disp
    mech_cases = sorted({s.case for s in solves if s.run.name == "P" and s.max_disp > lim},
                        key=cases.index)
    for s in solves:
        if s.run.name == "P" and s.case in mech_cases:
            s.valid = False
            s.note = "mechanism - pinned result invalid; joints carry moment"
    t2 = time.time()
    for s in solves:
        eng.buckling(s, cache)
    t3 = time.time()

    # ---- k_theta sweep on the governing case (worst item over valid solves)
    worst = None
    for s in solves:
        if not s.valid:
            continue
        for k, u in item_U(s).items():
            if worst is None or u > worst[0]:
                worst = (u, s)
    gov = worst[1]
    sweep = []
    d_rigid = next(s.max_disp for s in solves
                   if s.run.name == "R" and s.case == gov.case and s.run.bearing == gov.run.bearing)
    d_lim = max(lim, si.checks.sweep_mech_ratio * d_rigid)
    for f in si.springs.k_theta_sweep:
        run = RunSpec(f"k={f:g}", f, gov.run.bearing)
        s = eng.solve(run, gov.case, cache)
        s.valid = s.max_disp <= d_lim or f >= si.springs.k_theta_rigid
        if not s.valid:
            s.note = f"mechanism-dominated: max displacement {s.max_disp * 1e3:.3g} mm > {d_lim * 1e3:.3g} mm"
        eng.buckling(s, cache)
        sweep.append(s)
    t4 = time.time()
    return Study(model, solves, sweep, gov.case, gov.run.bearing, mech_cases, eig, eng.caps,
                 {"eig": t1 - t0, "solve": t2 - t1, "buckling": t3 - t2, "sweep": t4 - t3,
                  "total": t4 - t0})
