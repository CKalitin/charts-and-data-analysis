"""Validation suite (brief section 9) + solver unit checks.

Run with `python -m stand test` (or `pytest`).
"""
from __future__ import annotations


import numpy as np
import pytest

from stand import analysis, burrard, fem, geometry, joints, loads, members, model, params
from stand.geometry import Bearing, BracketSpec, Geometry, Joint, Member

E, G = 68.9e9, 26.5e9


@pytest.fixture(scope="module")
def p():
    return params.load(params.PROJECT_DIR / "params.yaml")


def sec_1010(p):
    s = p.si.section_1010
    return fem.Section(s.A, s.I_weak, s.I_strong, s.J, s.c_strong, s.c_weak, s.weight)


def line_model(p0, p1, n, sec, kind="frame"):
    """Straight member p0 -> p1 split into n elements; returns (x, elements)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    x = np.array([p0 + (p1 - p0) * t for t in np.linspace(0, 1, n + 1)])
    ax = p1 - p0
    R = fem.rotation(ax, fem.default_y_hint(ax))
    L = np.linalg.norm(ax) / n
    return x, [fem.FrameElement(i, i + 1, R, L, sec, kind=kind) for i in range(n)]


# --------------------------------------------------------------------------- 1. cantilever
@pytest.mark.parametrize("direction", [(1, 0, 0), (0, 0, 1), (1, 2, -0.5)])
def test_cantilever_tip_load(p, direction):
    sec = sec_1010(p)
    Lt, P = 1.2, 150.0
    d = np.asarray(direction, float) / np.linalg.norm(direction)
    x, els = line_model([0, 0, 0], Lt * d, 8, sec)
    K = fem.assemble(len(x), els, [], E, G)
    load_dir = np.cross(d, [0, 1, 0]) if abs(d[1]) < 0.9 else np.cross(d, [1, 0, 0])
    load_dir /= np.linalg.norm(load_dir)
    F = np.zeros(K.shape[0])
    F[-6:-3] = P * load_dir
    S = fem.Solver(K, range(6))
    u = S.solve(F)
    delta = u[-6:-3] @ load_dir
    assert delta == pytest.approx(P * Lt**3 / (3 * E * sec.Iz), rel=1e-9)
    f = fem.element_end_forces(els[0], u, E, G, None)
    r = fem.internal_forces(els[0], f, np.zeros(3), np.zeros(3))
    assert np.hypot(r[0, 5], r[0, 6]) == pytest.approx(P * Lt, rel=1e-9)


def test_distributed_load_simply_supported(p):
    """UDL w on a simply supported beam: midspan M = wL^2/8, deflection 5wL^4/(384EI)."""
    sec = sec_1010(p)
    Lt, w = 0.8, 1500.0
    x, els = line_model([0, 0, 0], [Lt, 0, 0], 4, sec)
    K = fem.assemble(len(x), els, [], E, G)
    F = np.zeros(K.shape[0])
    feq = {}
    for k, e in enumerate(els):
        q = e.R @ np.array([0, 0, -w])
        feq[k] = fem.linear_load_feq(e.L, q, q)
        F[e.dofs] += fem.big_T(e.R).T @ feq[k]
    n = len(x) - 1
    fixed = [0, 1, 2, 3, 6 * n + 1, 6 * n + 2]
    u = fem.Solver(K, fixed).solve(F)
    assert -u[6 * (n // 2) + 2] == pytest.approx(5 * w * Lt**4 / (384 * E * sec.Iy), rel=1e-9)
    e = els[1]
    q = e.R @ np.array([0, 0, -w])
    r = fem.internal_forces(e, fem.element_end_forces(e, u, E, G, feq[1]), q, q)
    assert np.hypot(r[-1, 5], r[-1, 6]) == pytest.approx(w * Lt**2 / 8, rel=1e-9)


def test_euler_column_geometric_stiffness(p):
    sec = sec_1010(p)
    Lt = 1.0
    x, els = line_model([0, 0, 0], [0, 0, Lt], 8, sec)
    K = fem.assemble(len(x), els, [], E, G)
    Kg = fem.assemble_kg(len(x), els, np.full(len(els), -1.0))      # 1 N compression
    n = len(x) - 1
    fixed = [0, 1, 2, 5, 6 * n, 6 * n + 1]                           # pinned-pinned + torsion
    S = fem.Solver(K, fixed)
    lam, _ = fem.buckling_lambda(S.Kff, Kg[np.ix_(S.free, S.free)])
    assert lam == pytest.approx(np.pi**2 * E * min(sec.Iy, sec.Iz) / Lt**2, rel=2e-4)


# --------------------------------------------------------------------------- 2. Burrard truss
def test_burrard_truss():
    """Every member against the worked example, through the same fem.py path the stand uses.
    stand/burrard.py holds the solve so this check and the figures can never diverge."""
    res = burrard.solve()
    for m in res.bars:
        assert m.N_in_P == pytest.approx(m.ref_in_P, abs=m.tol), m.name
    assert res.min_yield().name == res.ref_min["yield_member"]
    assert res.min_yield().SF_yield == pytest.approx(res.ref_min["yield"], abs=0.01)
    assert res.min_buckling().name == res.ref_min["buckling_member"]
    assert res.min_buckling().SF_buckling == pytest.approx(res.ref_min["buckling_euler_K1"], abs=0.01)
    ab = next(m for m in res.bars if m.name == "AB")
    assert ab.N_in_P == pytest.approx(-5.763, abs=2e-3)              # not the notes' 5.673


# --------------------------------------------------------------------------- 3/4. pinned rectangle
def rectangle(w=0.6, h=1.0, e=0.15):
    mm = 1e-3
    ms = {1: Member(1, np.array([0, 0, 0.0]), np.array([0, 0, h]), "1010"),
          2: Member(2, np.array([w, 0, 0.0]), np.array([w, 0, h]), "1010"),
          3: Member(3, np.array([0, 0, h]), np.array([w + e, 0, h]), "1010")}
    js = [Joint("TL", np.array([0, 0, h]), [1, 3], [], [BracketSpec("triangle", 3, 1, "+y")]),
          Joint("TR", np.array([w, 0, h]), [2, 3], [], [BracketSpec("triangle", 3, 2, "+y")]),
          Joint("BL", np.array([0, 0, 0.0]), [1], [], []),
          Joint("BR", np.array([w, 0, 0.0]), [2], [], [])]
    return Geometry(ms, js[:2], [], np.array([w + e, 0, h]), 3)


def solve_rectangle(p, F_vec, kr):
    g = rectangle()
    m = model.build(g, p, mode="test")
    springs = [b.spring(m, p.si.springs.k_t_factor, kr) for b in m.brackets]
    K = fem.assemble(m.n_nodes, m.elements, springs, m.E, m.G)
    base = [m.member_nodes[1][0], m.member_nodes[2][0]]
    fixed = [6 * n + k for n in base for k in range(3)] + [6 * base[0] + 3, 6 * base[0] + 5]
    fixed += [6 * n + 1 for n in range(m.n_nodes)] + [6 * n + 3 for n in range(m.n_nodes)] \
        + [6 * n + 5 for n in range(m.n_nodes)]                       # planar (x-z)
    F = np.zeros(m.n_dof)
    F[6 * m.thrust_node:6 * m.thrust_node + 3] = F_vec
    S = fem.Solver(K, fixed)
    u = S.solve(F)
    N = {mid: -fem.element_end_forces(m.elements[m.member_elements[mid][0]], u, m.E, m.G, None)[0]
         for mid in (1, 2)}
    return m, u, N


def test_pinned_rectangle_vertical_couple(p):
    w, e, Fv = 0.6, 0.15, 1000.0
    m, u, N = solve_rectangle(p, [0, 0, -Fv], p.si.springs.k_theta_pinned)
    assert -N[2] == pytest.approx(Fv * (1 + e / w), rel=1e-3)        # right column, compression
    assert -N[1] == pytest.approx(-Fv * e / w, rel=1e-3)             # left column, tension


def test_pinned_rectangle_horizontal_is_mechanism(p):
    H = 50.0
    m, u, N = solve_rectangle(p, [H, 0, 0], p.si.springs.k_theta_pinned)
    d_pin = np.abs(u.reshape(-1, 6)[:, :3]).max()
    assert d_pin > p.si.checks.mechanism_disp                         # -> mechanism flag
    m, u, N = solve_rectangle(p, [H, 0, 0], p.si.springs.k_theta_rigid)
    d_rig = u[6 * m.member_nodes[2][-1]]
    # rigid-jointed, pin-based portal with a stiff beam: H h^3 / (6 E I); flexible beam -> larger
    lower = H * 1.0**3 / (6 * E * m.sections[1].Iz)
    assert lower < d_rig < 1.5 * lower
    assert d_pin > 1e3 * d_rig


# --------------------------------------------------------------------------- 5. bolt group B
def test_bolt_group_B():
    n = np.array([0, 0, 1.0])
    line = np.array([1.0, 0, 0])
    bolts = np.array([[-0.0127, 0, 0], [0.0127, 0, 0]])
    fmax, fslot, Fz = joints.bolt_group(np.array([0, 100.0, 0]), np.array([0, 0, 20.8]), bolts, n, line)
    assert fmax == pytest.approx(868.9, abs=0.5)
    assert fslot == pytest.approx(0.0, abs=1e-9)


def test_wrench_transfer_statics():
    """M_P = M_X + (X - P) x F: moving a pure force must create the lever moment."""
    br = model.BracketSpring("J", 0, 0, "triangle", 1, 2, "+y", "", 0, 1, np.zeros(3), 1, 1)
    leg = joints.Leg("b", 2, True, np.array([0.02, 0, 0]), np.eye(3))
    W = np.r_[0, 0, 100.0, 0, 0, 0]
    _, MP, _, _ = joints.leg_wrench(br, leg, W)
    assert MP == pytest.approx([0, 100 * 0.02, 0])     # (X-P) x F = (-0.02,0,0) x (0,0,100)


def test_friction_radius(p):
    caps = joints.capacities(p)
    assert caps.r_f == pytest.approx(4.6e-3, abs=0.05e-3)
    assert caps.F_fric == pytest.approx(1000.0)


def test_column_formula_switch(p):
    sy = p.si.material.sigma_y
    Cc = np.sqrt(2 * np.pi**2 * E / sy)
    assert Cc == pytest.approx(89, abs=0.5)
    A, I = 281.9e-6, 1.84e-8
    r = np.sqrt(I / A)
    pe, k1 = members.critical_load(E, sy, A, I, 1.01 * Cc * r)
    pj, k2 = members.critical_load(E, sy, A, I, 0.99 * Cc * r)
    assert (k1, k2) == ("Euler", "Johnson")
    assert pe == pytest.approx(pj, rel=0.05)          # continuous at C_c (tangent point)
    a, _ = members.critical_load(E, sy, A, I, Cc * r * (1 + 1e-9))
    b, _ = members.critical_load(E, sy, A, I, Cc * r * (1 - 1e-9))
    assert a == pytest.approx(b, rel=1e-6) == pytest.approx(A * sy / 2, rel=1e-6)


# --------------------------------------------------------------------------- 6/7. stand runs
@pytest.fixture(scope="module")
def stand_study(p):
    g = geometry.load(p.si.inputs.geometry, p.si.inputs.brackets)
    m = model.build(g, p)
    return analysis.run_study(m, p, log=lambda *a: None)


def test_stand_global_equilibrium(stand_study):
    """Applied + base line load + restraint reactions = 0 on every run (force and moment)."""
    for s in stand_study.solves + stand_study.sweep:
        # mechanism-invalid P solves move ~10 m: K u - F recovery is round-off limited there
        tol = 1e-7 if s.valid else 1e-4
        assert s.eq_residual < tol, s.key
        np.testing.assert_allclose(s.loads.applied_resultant + s.loads.base_resultant, 0,
                                   atol=1e-9 * s.loads.summary["thrust_factored_N"])


def test_stand_restraint_reactions_vanish(stand_study, p):
    """3-2-1 restraint carries nothing (< restraint_tol_rel x thrust) on every valid solve."""
    for s in stand_study.solves + stand_study.sweep:
        tol = p.si.checks.restraint_tol_rel if s.valid else 1e-4
        assert s.restraint_rel < tol, s.key


def test_stand_sandbag_mass(stand_study):
    s = stand_study.solves[0]
    assert s.loads.summary["Fz_applied_N"] == pytest.approx(2224 - 133 - 165.1, abs=1.0)
    assert s.loads.summary["sandbag_net_kg"] == pytest.approx(196.4, abs=0.2)


def test_stand_rigid_runs_have_no_mechanism(stand_study):
    for e in stand_study.eig_checks:
        if e["run"].startswith("R"):
            assert not e["mechanism"]


def test_bearing_compression_only(stand_study):
    for s in stand_study.solves:
        assert np.all(s.bearing_forces >= -1e-6), s.key


def test_2d_mode_runs(p):
    g = geometry.load(p.si.inputs.geometry, p.si.inputs.brackets)
    m = model.build(g, p, mode="2d")
    st = analysis.run_study(m, p, log=lambda *a: None)
    for s in st.solves:
        assert s.eq_residual < 1e-6 and s.restraint_rel < p.si.checks.restraint_tol_rel
        assert s.loads.summary["thrust_factored_N"] == pytest.approx(0.5 * 2224)


# --------------------------------------------------------------------------- ground mode
@pytest.fixture(scope="module")
def ground_solves():
    pg = params.load(overrides={"base.mode": "ground"})
    g = geometry.load(pg.si.inputs.geometry, pg.si.inputs.brackets)
    m = model.build(g, pg, "3d")
    eng = analysis.Engine(m, pg)
    cache = {}
    run = analysis.RunSpec("R", pg.si.springs.k_theta_rigid, True)
    return pg, eng, [eng.solve(run, c, cache) for c in ("none", "+y")]


def test_ground_equilibrium_and_compression_only(ground_solves):
    """Applied loads + bags + ground springs balance; every closed contact pushes up,
    every open contact carries nothing (the ground never pulls)."""
    pg, eng, sols = ground_solves
    for s in sols:
        assert s.eq_residual < 1e-6
        Fz = s.ground_F[:, 2]
        on = np.array(s.contact)
        assert (Fz[on] >= -1e-9).all()
        assert np.allclose(s.ground_F[~on], 0.0)
        # total ground reaction = bags + weight - thrust
        b = eng.bags
        W = b.total_kg * pg.si.model.g
        assert Fz.sum() == pytest.approx(W - s.loads.applied_resultant[2], rel=1e-6)


def test_sandbags_meet_tipping_FS(ground_solves):
    pg, eng, _ = ground_solves
    for ch in eng.bags.checks:
        assert ch["FS_tip"] >= pg.si.sandbags.FS_tip - 1e-9
        assert ch["FS_lift"] >= pg.si.sandbags.FS_tip - 1e-9
