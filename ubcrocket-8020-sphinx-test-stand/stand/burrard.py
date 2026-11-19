"""Burrard St Bridge truss — the solver's back test against a worked example.

A pin-jointed half truss with a published hand solution (brief section 9, MECH 360 L13).
It runs through the same fem.py path the stand does — element, assembly, force recovery —
so agreement here is what licenses trusting those pieces on a frame nobody has solved by
hand. One module so the pytest check and the figures can never drift apart.

Everything is reported per unit load P (forces as N/P, + tension), which is how the course
notes state the answer and so the only form in which the two can be compared directly.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import fem
from .params import PROJECT_DIR

POISSON_DIV = 2.6                      # G = E / 2.6, as the rest of the model uses

# The notes' own summary table (Yielding | Buckling (Euler)), transcribed from the worked
# example. member -> (f_s yield, P_crit [MN], f_s buckling); None where the member is in
# tension and the notes print infinity. The AB row is computed from their transposed
# T = -8.51 MN, so its two SFs are high by that ratio -- see Result.note.
NOTES_TABLE = {
    "AB": (3.88, 142.03, 16.69), "BD": (3.86, 213.69, 24.98), "DF": (3.37, 223.96, 22.88),
    "FH": (3.15, 230.62, 22.05), "HJ": (3.03, 232.92, 21.42),
    "AC": (6.11, None, None), "CE": (6.11, None, None), "EG": (4.03, None, None),
    "GI": (3.44, None, None), "IK": (None, None, None),      # IK yield cell not legible
    "BC": (3.21, None, None), "DE": (3.72, 5.84, 4.52), "FG": (13.00, 2.63, 7.98),
    "HI": (16.53, None, None), "JK": (None, None, None),     # JK carries no force
    "BE": (2.71, None, None), "DG": (3.66, None, None), "FI": (5.82, None, None),
    "HK": (9.47, None, None),
}


@dataclass(frozen=True)
class Bar:
    name: str
    a: str                             # end node names, as the notes label them
    b: str
    N_in_P: float                      # computed axial force / P, + tension
    ref_in_P: float                    # the notes' value
    SF_yield: float
    SF_buckling: float | None          # Euler K=1; compression members only
    ref_SF_yield: float | None = None      # the notes' values, None where not printed/legible
    ref_P_crit_MN: float | None = None
    ref_SF_buckling: float | None = None

    @property
    def residual(self) -> float:
        return self.N_in_P - self.ref_in_P

    @property
    def tol(self) -> float:
        """The agreement the notes' 4-significant-figure values can actually support."""
        return max(5e-3 * abs(self.N_in_P), 2e-3)


@dataclass(frozen=True)
class Result:
    source: str
    note: str
    E: float
    fy: float
    P: float
    nodes: dict[str, np.ndarray]       # name -> (x, y) m
    supports: dict[str, list[str]]
    loads_in_P: dict[str, float]
    bars: list[Bar]
    ref_min: dict                      # the notes' governing members and their SFs

    @property
    def worst(self) -> Bar:
        return max(self.bars, key=lambda m: abs(m.residual) / m.tol)

    def min_yield(self) -> Bar:
        return min(self.bars, key=lambda m: m.SF_yield)

    def P_crit_MN(self, m: Bar) -> float | None:
        """Euler critical load behind a buckling SF — the notes print it, so it is checkable."""
        return None if m.SF_buckling is None else m.SF_buckling * abs(m.N_in_P) * self.P / 1e6

    def min_buckling(self) -> Bar:
        return min((m for m in self.bars if m.SF_buckling is not None), key=lambda m: m.SF_buckling)


def solve(path: str | Path | None = None) -> Result:
    """Solve the half truss and pair every member with the value the notes print for it."""
    path = Path(path) if path else PROJECT_DIR / "references" / "prompt" / "burrard_validation.json"
    d = json.loads(Path(path).read_text())
    E, fy, P = d["E"], d["sigma_y"], d["P"]
    names = list(d["nodes"])
    idx = {k: i for i, k in enumerate(names)}
    x = np.array([[*d["nodes"][k], 0.0] for k in names], float)

    els, ids = [], []
    for mid, (A, I) in d["members"].items():
        a, b = idx[mid[0]], idx[mid[1]]
        ax = x[b] - x[a]
        R = fem.rotation(ax, np.array([0, 0, 1.0]))
        els.append(fem.FrameElement(a, b, R, float(np.linalg.norm(ax)),
                                    fem.Section(A, I, I, 2 * I, 1, 1), kind="truss"))
        ids.append(mid)

    K = fem.assemble(len(x), els, [], E, E / POISSON_DIV)
    fixed = [6 * i + k for i in range(len(x)) for k in (2, 3, 4, 5)]      # 2D, pin-jointed
    for node, dirs in d["supports"].items():
        fixed += [6 * idx[node] + {"x": 0, "y": 1}[dr] for dr in dirs]
    F = np.zeros(K.shape[0])
    for node, v in d["loads_in_P"].items():
        F[6 * idx[node] + 1] = v * P
    u = fem.Solver(K, fixed).solve(F)

    bars = []
    for mid, e in zip(ids, els):
        N = -fem.element_end_forces(e, u, E, E / POISSON_DIV, None)[0]
        sf_b = (np.pi**2 * E * e.sec.Iy / e.L**2) / -N if N < 0 else None
        ry, rpc, rb = NOTES_TABLE.get(mid, (None, None, None))
        bars.append(Bar(mid, mid[0], mid[1], N / P, d["expected_force_in_P"][mid],
                        fy / abs(N / e.sec.A) if abs(N) > 1e-9 * P else np.inf, sf_b,
                        ry, rpc, rb))

    return Result(d["source"], d["note"], E, fy, P,
                  {k: np.array(v, float) for k, v in d["nodes"].items()},
                  d["supports"], d["loads_in_P"], bars, d["expected_min_SF"])
