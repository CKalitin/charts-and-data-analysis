"""Universal-variable two-body propagator (Vallado's algorithm).

Works uniformly for elliptical, parabolic, and hyperbolic orbits. Used both
to independently validate the Lambert solutions (propagate r1,v1 forward by
the time of flight and confirm r2 is reproduced) and for the mid-course-
correction re-targeting.

Reference: Vallado, "Fundamentals of Astrodynamics and Applications," 4th
ed., Algorithm 8 (Kepler / universal variables) with Algorithm 1 (Stumpff
functions).
"""
import numpy as np


def _stumpff_c2c3(psi):
    """Stumpff functions c2(psi), c3(psi), vectorized, valid for psi <0, =0, >0."""
    psi = np.asarray(psi, dtype=float)
    c2 = np.empty_like(psi)
    c3 = np.empty_like(psi)

    pos = psi > 1e-6
    neg = psi < -1e-6
    zero = ~(pos | neg)

    sp = np.sqrt(np.abs(psi[pos]))
    c2[pos] = (1 - np.cos(sp)) / psi[pos]
    c3[pos] = (sp - np.sin(sp)) / sp ** 3

    sp = np.sqrt(np.abs(psi[neg]))
    c2[neg] = (1 - np.cosh(sp)) / psi[neg]
    c3[neg] = (np.sinh(sp) - sp) / sp ** 3

    c2[zero] = 1.0 / 2.0
    c3[zero] = 1.0 / 6.0
    return c2, c3


def propagate(r0, v0, dt, mu, tol=1e-9, max_iter=100):
    """Propagate (r0, v0) forward by dt seconds under two-body gravity mu.

    r0, v0: (3,) arrays, km and km/s. dt: seconds (can be negative).
    Returns (r, v) at t0+dt.
    """
    r0 = np.asarray(r0, dtype=float)
    v0 = np.asarray(v0, dtype=float)
    r0_norm = np.linalg.norm(r0)
    v0_norm = np.linalg.norm(v0)
    vr0 = np.dot(r0, v0) / r0_norm
    alpha = 2.0 / r0_norm - v0_norm ** 2 / mu  # 1/a

    sqrt_mu = np.sqrt(mu)

    if alpha > 1e-10:  # ellipse: good first guess
        chi = sqrt_mu * dt * alpha
    elif alpha < -1e-10:  # hyperbola
        a = 1.0 / alpha
        chi = np.sign(dt) * np.sqrt(-a) * np.log(
            (-2 * mu * alpha * dt) /
            (np.dot(r0, v0) + np.sign(dt) * np.sqrt(-mu * a) * (1 - r0_norm * alpha))
        )
    else:  # near-parabolic fallback
        h = np.linalg.norm(np.cross(r0, v0))
        p = h ** 2 / mu
        s = 0.5 * np.arctan(1.0 / (3.0 * np.sqrt(mu / p ** 3) * dt)) if dt != 0 else 0.0
        w = np.arctan(np.tan(s) ** (1.0 / 3.0))
        chi = np.sqrt(p) * 2.0 / np.tan(2.0 * w) if dt != 0 else 0.0

    for _ in range(max_iter):
        psi = chi ** 2 * alpha
        c2, c3 = _stumpff_c2c3(np.array([psi]))
        c2, c3 = c2[0], c3[0]
        r_pred = (chi ** 2 * c2 + (vr0 * r0_norm / sqrt_mu) * chi * (1 - psi * c3)
                  + r0_norm * (1 - psi * c2))
        # F(chi) == sqrt(mu)*dt at the root (Vallado eq. for universal Kepler's equation);
        # do NOT divide by sqrt_mu here, the residual below expects raw F.
        F = (chi ** 3 * c3 + (vr0 * r0_norm / sqrt_mu) * chi ** 2 * c2
             + r0_norm * chi * (1 - psi * c3))
        d_chi = (sqrt_mu * dt - F) / r_pred
        chi += d_chi
        if abs(d_chi) < tol:
            break
    else:
        raise RuntimeError("universal-variable Kepler propagation did not converge")

    psi = chi ** 2 * alpha
    c2, c3 = _stumpff_c2c3(np.array([psi]))
    c2, c3 = c2[0], c3[0]

    f = 1 - chi ** 2 * c2 / r0_norm
    g = dt - chi ** 3 * c3 / sqrt_mu
    r = f * r0 + g * v0
    r_norm = np.linalg.norm(r)

    fdot = sqrt_mu / (r_norm * r0_norm) * (psi * c3 - 1) * chi
    gdot = 1 - chi ** 2 * c2 / r_norm
    v = fdot * r0 + gdot * v0

    return r, v
