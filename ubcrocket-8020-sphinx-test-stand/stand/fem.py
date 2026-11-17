"""3D direct-stiffness core: element matrices, assembly, solve, force recovery.

Pure numpy for everything except eigenvalues (scipy.sparse.linalg.eigsh).
DOF order per node: [ux, uy, uz, rx, ry, rz]. Element local x runs n1 -> n2.

Sign conventions
  * Element end forces f = k u_loc - f_eq are forces exerted ON the element by its
    nodes, in local axes.  Internal axial force N is tension-positive.
  * A spring connects side a (node na) and side b (node nb) at a point X through
    rigid arms.  Its wrench W_b = -K_s d (d = motion of b relative to a at X) is
    the force/moment the spring applies to side b, at X; side a gets -W_b.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

DOF = 6


# --------------------------------------------------------------------------- frame
def rotation(x_axis: np.ndarray, y_hint: np.ndarray) -> np.ndarray:
    """3x3 with rows = local x, y, z in global; local y = y_hint made perpendicular to x."""
    ex = x_axis / np.linalg.norm(x_axis)
    y = y_hint - (y_hint @ ex) * ex
    n = np.linalg.norm(y)
    if n < 1e-6:
        raise ValueError("reference vector parallel to element axis")
    ey = y / n
    ez = np.cross(ex, ey)
    return np.vstack([ex, ey, ez])


def default_y_hint(x_axis: np.ndarray) -> np.ndarray:
    ex = x_axis / np.linalg.norm(x_axis)
    return np.array([0.0, 0.0, 1.0]) if abs(ex[2]) < 0.9 else np.array([1.0, 0.0, 0.0])


def frame_k_local(E, G, A, Iy, Iz, J, L) -> np.ndarray:
    k = np.zeros((12, 12))
    k[0, 0] = k[6, 6] = E * A / L
    k[0, 6] = k[6, 0] = -E * A / L
    k[3, 3] = k[9, 9] = G * J / L
    k[3, 9] = k[9, 3] = -G * J / L
    # bending in local x-y plane: v (1, 7), rz (5, 11), uses Iz
    a, b, c, d = 12 * E * Iz / L**3, 6 * E * Iz / L**2, 4 * E * Iz / L, 2 * E * Iz / L
    for (i, j, v) in [(1, 1, a), (1, 5, b), (1, 7, -a), (1, 11, b), (5, 5, c), (5, 7, -b),
                      (5, 11, d), (7, 7, a), (7, 11, -b), (11, 11, c)]:
        k[i, j] = k[j, i] = v
    # bending in local x-z plane: w (2, 8), ry (4, 10), uses Iy
    a, b, c, d = 12 * E * Iy / L**3, 6 * E * Iy / L**2, 4 * E * Iy / L, 2 * E * Iy / L
    for (i, j, v) in [(2, 2, a), (2, 4, -b), (2, 8, -a), (2, 10, -b), (4, 4, c), (4, 8, b),
                      (4, 10, d), (8, 8, a), (8, 10, b), (10, 10, c)]:
        k[i, j] = k[j, i] = v
    return k


def frame_kg_local(P, A, Iy, Iz, L) -> np.ndarray:
    """Consistent geometric stiffness for axial force P (tension +)."""
    g = np.zeros((12, 12))
    s = P / L
    for (i, j, v) in [(1, 1, 6 / 5), (1, 5, L / 10), (1, 7, -6 / 5), (1, 11, L / 10),
                      (5, 5, 2 * L**2 / 15), (5, 7, -L / 10), (5, 11, -L**2 / 30),
                      (7, 7, 6 / 5), (7, 11, -L / 10), (11, 11, 2 * L**2 / 15),
                      (2, 2, 6 / 5), (2, 4, -L / 10), (2, 8, -6 / 5), (2, 10, -L / 10),
                      (4, 4, 2 * L**2 / 15), (4, 8, L / 10), (4, 10, -L**2 / 30),
                      (8, 8, 6 / 5), (8, 10, L / 10), (10, 10, 2 * L**2 / 15)]:
        g[i, j] = g[j, i] = s * v
    r2 = (Iy + Iz) / A
    g[3, 3] = g[9, 9] = s * r2
    g[3, 9] = g[9, 3] = -s * r2
    return g


def big_T(R: np.ndarray) -> np.ndarray:
    T = np.zeros((12, 12))
    for i in range(4):
        T[3 * i:3 * i + 3, 3 * i:3 * i + 3] = R
    return T


def linear_load_feq(L: float, q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Consistent nodal loads (local) for a load varying linearly q1 -> q2 (local, N/m)."""
    f = np.zeros(12)
    f[0] = L * (2 * q1[0] + q2[0]) / 6
    f[6] = L * (q1[0] + 2 * q2[0]) / 6
    # y: force + rz
    f[1] = L * (7 * q1[1] + 3 * q2[1]) / 20
    f[7] = L * (3 * q1[1] + 7 * q2[1]) / 20
    f[5] = L**2 * (3 * q1[1] + 2 * q2[1]) / 60
    f[11] = -L**2 * (2 * q1[1] + 3 * q2[1]) / 60
    # z: force + ry (opposite sign)
    f[2] = L * (7 * q1[2] + 3 * q2[2]) / 20
    f[8] = L * (3 * q1[2] + 7 * q2[2]) / 20
    f[4] = -L**2 * (3 * q1[2] + 2 * q2[2]) / 60
    f[10] = L**2 * (2 * q1[2] + 3 * q2[2]) / 60
    return f


@dataclass
class Section:
    A: float
    Iy: float           # about local y (resists w deflection)
    Iz: float           # about local z (resists v deflection)
    J: float
    cy: float           # outer fibre |y| (for Mz)
    cz: float           # outer fibre |z| (for My)
    w: float = 0.0      # self-weight N/m


@dataclass
class FrameElement:
    n1: int
    n2: int
    R: np.ndarray
    L: float
    sec: Section
    member: int = -1    # owning member id (-1 for test models)
    kind: str = "frame"  # frame | truss

    def k_global(self, E, G) -> np.ndarray:
        s = self.sec
        if self.kind == "truss":
            kl = np.zeros((12, 12))
            kl[0, 0] = kl[6, 6] = E * s.A / self.L
            kl[0, 6] = kl[6, 0] = -E * s.A / self.L
        else:
            kl = frame_k_local(E, G, s.A, s.Iy, s.Iz, s.J, self.L)
        T = big_T(self.R)
        return T.T @ kl @ T

    def kg_global(self, P) -> np.ndarray:
        s = self.sec
        T = big_T(self.R)
        if self.kind == "truss":
            g = np.zeros((12, 12))
            for i, j in [(1, 1), (2, 2), (7, 7), (8, 8)]:
                g[i, j] = P / self.L
            for i, j in [(1, 7), (2, 8)]:
                g[i, j] = g[j, i] = -P / self.L
        else:
            g = frame_kg_local(P, s.A, s.Iy, s.Iz, self.L)
        return T.T @ g @ T

    @property
    def dofs(self) -> np.ndarray:
        return np.r_[DOF * self.n1:DOF * self.n1 + 6, DOF * self.n2:DOF * self.n2 + 6]


# --------------------------------------------------------------------------- springs
def skew(r: np.ndarray) -> np.ndarray:
    return np.array([[0, -r[2], r[1]], [r[2], 0, -r[0]], [-r[1], r[0], 0]])


def arm(r: np.ndarray) -> np.ndarray:
    """6x6: node DOFs -> motion of a rigidly attached point at node + r."""
    T = np.eye(6)
    T[:3, 3:] = -skew(r)          # u_X = u + theta x r = u - r x theta
    return T


@dataclass
class Spring:
    """Zero-length spring between sides a and b at point X (rigid arms to each node)."""
    na: int
    nb: int
    X: np.ndarray
    xa: np.ndarray        # node positions (for arms)
    xb: np.ndarray
    Ks: np.ndarray        # 6x6 at X, global axes
    tag: dict = field(default_factory=dict)

    def B(self) -> np.ndarray:
        return np.hstack([-arm(self.X - self.xa), arm(self.X - self.xb)])

    @property
    def dofs(self) -> np.ndarray:
        return np.r_[DOF * self.na:DOF * self.na + 6, DOF * self.nb:DOF * self.nb + 6]

    def k_global(self) -> np.ndarray:
        B = self.B()
        return B.T @ self.Ks @ B

    def rel(self, u: np.ndarray) -> np.ndarray:
        return self.B() @ u[self.dofs]

    def wrench_on_b(self, u: np.ndarray) -> np.ndarray:
        return -self.Ks @ self.rel(u)


def iso_spring_K(kt: float, kr: float) -> np.ndarray:
    return np.diag([kt, kt, kt, kr, kr, kr])


def axial_spring_K(k: float, n: np.ndarray) -> np.ndarray:
    K = np.zeros((6, 6))
    K[:3, :3] = k * np.outer(n, n)
    return K


# --------------------------------------------------------------------------- assembly / solve
def assemble(n_nodes: int, elements, springs, E, G) -> np.ndarray:
    K = np.zeros((DOF * n_nodes, DOF * n_nodes))
    for e in elements:
        d = e.dofs
        K[np.ix_(d, d)] += e.k_global(E, G)
    for s in springs:
        d = s.dofs
        K[np.ix_(d, d)] += s.k_global()
    return K


def assemble_kg(n_nodes: int, elements, axial: np.ndarray) -> np.ndarray:
    Kg = np.zeros((DOF * n_nodes, DOF * n_nodes))
    for e, P in zip(elements, axial):
        d = e.dofs
        Kg[np.ix_(d, d)] += e.kg_global(P)
    return Kg


class Solver:
    """Solve K u = F with fixed DOFs; caches K_ff^-1 for repeated right-hand sides."""

    def __init__(self, K: np.ndarray, fixed: np.ndarray):
        self.K = K
        n = K.shape[0]
        self.fixed = np.asarray(sorted(set(int(i) for i in fixed)), dtype=int)
        mask = np.ones(n, bool)
        mask[self.fixed] = False
        self.free = np.nonzero(mask)[0]
        self.Kff = K[np.ix_(self.free, self.free)]
        self._inv = None

    def solve(self, F: np.ndarray) -> np.ndarray:
        """F: (n,) or (n, m). Returns u with zeros at fixed DOFs."""
        if self._inv is None:
            self._inv = np.linalg.inv(self.Kff)
        u = np.zeros_like(F, dtype=float)
        rhs = F[self.free]
        x = self._inv @ rhs
        for _ in range(3):                  # iterative refinement (P runs are ill-conditioned)
            x = x + self._inv @ (rhs - self.Kff @ x)
        u[self.free] = x
        return u

    def reactions(self, u: np.ndarray, F: np.ndarray) -> np.ndarray:
        return (self.K @ u - F)[self.fixed]


# --------------------------------------------------------------------------- recovery
def element_end_forces(e: FrameElement, u: np.ndarray, E, G, feq_local: np.ndarray | None) -> np.ndarray:
    T = big_T(e.R)
    s = e.sec
    if e.kind == "truss":
        kl = np.zeros((12, 12))
        kl[0, 0] = kl[6, 6] = E * s.A / e.L
        kl[0, 6] = kl[6, 0] = -E * s.A / e.L
    else:
        kl = frame_k_local(E, G, s.A, s.Iy, s.Iz, s.J, e.L)
    f = kl @ (T @ u[e.dofs])
    if feq_local is not None:
        f = f - feq_local
    return f


def internal_forces(e: FrameElement, f: np.ndarray, q1: np.ndarray, q2: np.ndarray,
                    n_pts: int = 5) -> np.ndarray:
    """Stress resultants at n_pts stations: columns [x, N, Vy, Vz, T, My, Mz] (local).

    q1, q2: local distributed load (N/m) at the element ends.
    """
    L = e.L
    F1, M1 = f[:3], f[3:6]
    ex = np.array([1.0, 0, 0])
    out = []
    for x in np.linspace(0.0, L, n_pts):
        Fl = F1 + q1 * x + (q2 - q1) * x**2 / (2 * L)               # resultant on left part
        Vq = -q1 * x**2 / 2 - (q2 - q1) * x**3 / (6 * L)            # int (s - x) q ds
        Ml = M1 + np.cross(-x * ex, F1) + np.cross(ex, Vq)          # moment of left part about x
        out.append([x, -Fl[0], -Fl[1], -Fl[2], -Ml[0], -Ml[1], -Ml[2]])
    return np.array(out)


# --------------------------------------------------------------------------- eigen
def lowest_modes(Kff: np.ndarray, k: int = 6):
    """Smallest eigenpairs of a symmetric (semi)definite matrix (shift-invert near 0)."""
    from scipy.sparse.linalg import eigsh
    scale = float(np.max(np.abs(np.diag(Kff))))
    k = min(k, Kff.shape[0] - 2)
    vals, vecs = eigsh(Kff, k=k, sigma=-1e-9 * scale, which="LM")
    order = np.argsort(vals)
    return vals[order] / scale, vecs[:, order]


def buckling_lambda(Kff: np.ndarray, Kgff: np.ndarray, k: int = 4):
    """Lowest positive lambda of (K + lambda Kg) phi = 0.

    With K = L L^T: C = L^-1 (-Kg) L^-T is symmetric, C psi = mu psi, mu = 1/lambda,
    phi = L^-T psi.  The largest mu gives the lowest positive lambda.
    """
    from scipy.sparse.linalg import eigsh
    A = -0.5 * (Kgff + Kgff.T)
    try:
        Linv = np.linalg.inv(np.linalg.cholesky(Kff))
    except np.linalg.LinAlgError:
        return np.nan, None                  # K not positive definite (mechanism)
    C = Linv @ A @ Linv.T
    C = 0.5 * (C + C.T)
    k = min(k, C.shape[0] - 2)
    mu, psi = eigsh(C, k=k, which="LA")
    i = int(np.argmax(mu))
    if mu[i] <= 1e-12 * max(1.0, float(np.max(np.abs(mu)))):
        return np.inf, None
    return 1.0 / mu[i], Linv.T @ psi[:, i]
