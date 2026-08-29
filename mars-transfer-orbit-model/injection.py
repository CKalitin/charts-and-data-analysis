"""Exact single-impulse hyperbolic-injection delta-v, and the per-plane
minimum over burn-point phasing.

This is the same exact (not textbook-tangential-only) patched-conic solve
used earlier in this project (previously in the now-deleted patched_conic.py,
which was built around psi -- a fixed burn-point-phasing-within-one-plane
parameterization that has since been removed entirely). The underlying
physics -- given a burn point (position + pre-burn circular velocity) and a
required outgoing v_infinity, solve for the exact non-tangential burn that
reaches it -- is unchanged and still exactly what's needed; it's now used
inside a RAAN sweep instead, where each RAAN candidate plane is scored by
its own best-achievable delta-v (minimized over where in that plane you burn).

Derivation (unchanged from before): given r_hat (burn point direction),
r_p (=|r_burn|), and the required v_infinity vector, the orbital plane
spanned by (r_burn, v_infinity) is fixed by their cross product up to a
sign (the two branches, analogous to Lambert's own short-way/long-way
ambiguity). Within a branch, theta = the angle from r_hat to v_infinity's
direction (measured about that branch's plane normal) is known, and the
eccentricity e of the unique conic through r_burn with that outgoing
asymptote solves:

    nu_inf(e)  = arccos(-1/e)
    nu_burn(e) = nu_inf(e) - theta
    p(e)       = mu/vinf^2 * (e^2 - 1)
    r_p * (1 + e*cos(nu_burn(e))) = p(e)      <- solve this for e

then v_after follows from the standard radial/transverse conic-velocity
formulas at nu_burn.
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

import config


@dataclass
class InjectionResult:
    delta_v_mag: float
    v_after: np.ndarray
    eccentricity: float
    true_anomaly_burn_deg: float
    orbit_normal: np.ndarray
    branch: str


def _solve_branch(r_hat, r_p, vinf_hat, vinf_mag, n_hat, mu):
    cos_theta = np.clip(np.dot(r_hat, vinf_hat), -1.0, 1.0)
    sin_theta = np.dot(n_hat, np.cross(r_hat, vinf_hat))
    theta = np.arctan2(sin_theta, cos_theta) % (2 * np.pi)
    t_hat = np.cross(n_hat, r_hat)

    def residual(e):
        nu_inf = np.arccos(-1.0 / e)
        nu_burn = nu_inf - theta
        p = mu / vinf_mag ** 2 * (e ** 2 - 1)
        return r_p * (1 + e * np.cos(nu_burn)) - p

    e_grid = np.concatenate([1.0 + np.geomspace(1e-6, 1.0, 400), np.linspace(2.0, 50.0, 200)])
    resid = np.array([residual(e) for e in e_grid])
    candidates = []
    for i in range(len(e_grid) - 1):
        if np.isfinite(resid[i]) and np.isfinite(resid[i + 1]) and np.sign(resid[i]) != np.sign(resid[i + 1]):
            try:
                e_root = brentq(residual, e_grid[i], e_grid[i + 1], xtol=1e-12, rtol=1e-13)
            except ValueError:
                continue
            nu_inf = np.arccos(-1.0 / e_root)
            nu_burn = nu_inf - theta
            p = mu / vinf_mag ** 2 * (e_root ** 2 - 1)
            h = np.sqrt(mu * p)
            v_radial = (mu / h) * e_root * np.sin(nu_burn)
            v_transverse = (mu / h) * (1 + e_root * np.cos(nu_burn))
            v_after = v_radial * r_hat + v_transverse * t_hat
            candidates.append((e_root, nu_burn, v_after))
    return candidates


def solve_injection_burn(r_burn, v_before, v_inf_required, mu_earth=config.GM_EARTH):
    """Exact minimum-delta-v single-impulse solve for a specific burn point.

    r_burn: (3,) km, position of the burn point (on a circular parking orbit).
    v_before: (3,) km/s, the pre-burn (circular, tangential) velocity there.
    v_inf_required: (3,) km/s, the fixed target hyperbolic excess velocity.
    """
    r_hat = r_burn / np.linalg.norm(r_burn)
    r_p = np.linalg.norm(r_burn)
    vinf_mag = np.linalg.norm(v_inf_required)
    vinf_hat = v_inf_required / vinf_mag

    cross = np.cross(r_hat, vinf_hat)
    cross_norm = np.linalg.norm(cross)
    if cross_norm < 1e-9:
        return None  # degenerate: r_burn (anti)parallel to v_infinity; measure-zero, skip
    n_candidate = cross / cross_norm

    best = None
    for n_hat, branch_name in [(n_candidate, "A"), (-n_candidate, "B")]:
        for e, nu_burn, v_after in _solve_branch(r_hat, r_p, vinf_hat, vinf_mag, n_hat, mu_earth):
            dv_vec = v_after - v_before
            dv_mag = np.linalg.norm(dv_vec)
            if best is None or dv_mag < best.delta_v_mag:
                best = InjectionResult(delta_v_mag=dv_mag, v_after=v_after, eccentricity=e,
                                        true_anomaly_burn_deg=np.degrees(nu_burn),
                                        orbit_normal=n_hat, branch=branch_name)
    return best


def minimum_delta_v_for_plane(n_hat, v_inf_required, r_park=config.R_EARTH + config.PARKING_ALTITUDE_KM,
                               mu_earth=config.GM_EARTH, n_scan=180):
    """The cheapest achievable injection delta-v from ANY point on a circular
    parking orbit in the plane with normal n_hat -- scans burn-point true
    anomaly around the full circle and returns the minimum (an apples-to-
    apples score for "how good is this plane", independent of burn phasing).

    For each burn point, BOTH parking-orbit traversal senses (prograde and
    retrograde relative to n_hat) are tried. These are physically distinct
    design choices -- same plane, same burn point, opposite pre-burn
    velocity direction -- and are not degenerate with each other: flipping
    n_hat -> -n_hat retraces the same positions but reverses v_before, so
    scanning only one sign of n_hat silently omits half the achievable
    burns. (Confirmed non-negligible in general: up to ~0.15 m/s difference
    checked directly against a +n_hat/-n_hat comparison during validation,
    small here but not asserted to stay small across the whole RAAN sweep,
    hence scanning both explicitly rather than assuming symmetry.)"""
    ref = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(ref, n_hat)) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    e1 = np.cross(n_hat, ref)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n_hat, e1)

    v_circ = np.sqrt(mu_earth / r_park)
    best_dv = np.inf
    best_nu = None
    for nu in np.linspace(0.0, 2 * np.pi, n_scan, endpoint=False):
        r_hat = np.cos(nu) * e1 + np.sin(nu) * e2
        v_hat = -np.sin(nu) * e1 + np.cos(nu) * e2
        r_burn = r_park * r_hat
        for sign in (1.0, -1.0):
            v_before = sign * v_circ * v_hat
            result = solve_injection_burn(r_burn, v_before, v_inf_required, mu_earth)
            if result is not None and result.delta_v_mag < best_dv:
                best_dv = result.delta_v_mag
                best_nu = nu
    return best_dv, best_nu
