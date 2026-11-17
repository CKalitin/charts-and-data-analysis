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


def build_case(model: StandModel, p, case: str) -> CaseLoads:
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
