"""psi-parameterized polar-parking-orbit departure burn.

Definition of psi ("heliocentric injection azimuth"): the angle, at the TMI
burn point, between the spacecraft's circular parking-orbit velocity vector
and Earth's heliocentric velocity vector v_Earth. psi=0 -> burn-point
velocity parallel to v_Earth; psi=+/-90 deg -> perpendicular to it.

Geometry (derived in the brainstorm, re-derived here in code comments):

A polar (i=90 deg, equatorial-frame) parking orbit's plane always contains
Earth's spin axis z_hat. Choosing RAAN so the plane ALSO contains v_Earth's
full 3D direction (always possible for a polar orbit, since a plane through
z_hat can be rotated to contain any other direction) fixes the orbital
plane normal:

    n_hat = normalize(z_hat x v_Earth_hat)

Within that plane, build the orthonormal in-plane basis {v_Earth_hat, e_t0_hat}
with e_t0_hat = n_hat x v_Earth_hat. For a circular orbit, position and
velocity are both in-plane and mutually perpendicular; a short derivation
(position r_hat(nu) = cos(nu) v_Earth_hat + sin(nu) e_t0_hat, velocity
v_hat(nu) = d(r_hat)/dnu) shows that if the burn point's velocity makes
angle psi with v_Earth_hat, then:

    v_hat(psi) = cos(psi) * v_Earth_hat + sin(psi) * e_t0_hat
    r_hat(psi) = v_hat(psi) x n_hat

This is the ONLY thing psi controls -- it does not (and must not) depend on
the required outgoing v_infinity, which is a fixed output of the Lambert
solve. The injection delta-v is then whatever it costs, in general a
non-tangential burn, to reach that v_infinity from that specific parking-
orbit point -- see `solve_injection_burn` for the exact (not tangential-
burn-only) patched-conic construction.
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

import config

Z_HAT = np.array([0.0, 0.0, 1.0])


@dataclass
class BurnPointGeometry:
    psi_deg: float
    n_hat: np.ndarray  # orbital plane normal (angular momentum direction)
    r_hat: np.ndarray  # burn-point position direction
    v_hat: np.ndarray  # burn-point pre-burn velocity direction
    r_burn: np.ndarray  # km
    v_before: np.ndarray  # km/s


def burn_point_geometry(v_earth_eq, psi_deg, parking_alt_km=config.PARKING_ALTITUDE_KM,
                         mu_earth=config.GM_EARTH):
    """Parking-orbit burn point for a given heliocentric-injection-azimuth psi.

    v_earth_eq: Earth's heliocentric velocity vector, equatorial(ICRS/J2000) frame
    (same frame classical orbital elements i/Omega/omega are referenced to).
    """
    v_earth_hat = v_earth_eq / np.linalg.norm(v_earth_eq)
    n_hat = np.cross(Z_HAT, v_earth_hat)
    n_hat /= np.linalg.norm(n_hat)
    e_t0_hat = np.cross(n_hat, v_earth_hat)

    psi = np.radians(psi_deg)
    v_hat = np.cos(psi) * v_earth_hat + np.sin(psi) * e_t0_hat
    r_hat = np.cross(v_hat, n_hat)

    r_park = config.R_EARTH + parking_alt_km
    v_circ = np.sqrt(mu_earth / r_park)

    return BurnPointGeometry(
        psi_deg=psi_deg, n_hat=n_hat, r_hat=r_hat, v_hat=v_hat,
        r_burn=r_park * r_hat, v_before=v_circ * v_hat,
    )


@dataclass
class InjectionBurn:
    v_after: np.ndarray
    delta_v: np.ndarray
    delta_v_mag: float
    eccentricity: float
    periapsis_radius_km: float
    true_anomaly_burn_deg: float
    branch: str


def _solve_branch(r_hat, r_p, vinf_hat, vinf_mag, n_hat, mu, branch_name):
    """One plane-normal branch of the exact hyperbolic-injection targeting solve.

    Given the burn point (r_hat, r_p) and required asymptotic velocity
    (vinf_hat, vinf_mag), with orbital-plane normal n_hat fixed (so the
    angular separation theta between r_hat and the asymptote, measured in
    the positive sense about n_hat, is determined), solve for the
    eccentricity e of the unique conic through r_burn with that asymptote,
    then reconstruct v_after. Returns a list of InjectionBurn candidates
    (there can be more than one root).
    """
    cos_theta = np.clip(np.dot(r_hat, vinf_hat), -1.0, 1.0)
    sin_theta = np.dot(n_hat, np.cross(r_hat, vinf_hat))
    theta = np.arctan2(sin_theta, cos_theta) % (2 * np.pi)  # [0, 2pi)

    t_hat = np.cross(n_hat, r_hat)  # in-plane, in direction of increasing true anomaly

    def residual(e):
        nu_inf = np.arccos(-1.0 / e)
        nu_burn = nu_inf - theta
        p = mu / vinf_mag ** 2 * (e ** 2 - 1)
        return r_p * (1 + e * np.cos(nu_burn)) - p

    # Scan for sign changes across a wide, dense-near-1 grid of eccentricities.
    e_grid = np.concatenate([
        1.0 + np.geomspace(1e-6, 1.0, 400),
        np.linspace(2.0, 50.0, 200),
    ])
    resid = np.array([residual(e) for e in e_grid])
    roots = []
    for i in range(len(e_grid) - 1):
        if np.sign(resid[i]) != np.sign(resid[i + 1]) and np.isfinite(resid[i]) and np.isfinite(resid[i + 1]):
            try:
                e_root = brentq(residual, e_grid[i], e_grid[i + 1], xtol=1e-12, rtol=1e-13)
                roots.append(e_root)
            except ValueError:
                continue

    candidates = []
    for e in roots:
        nu_inf = np.arccos(-1.0 / e)
        nu_burn = nu_inf - theta
        p = mu / vinf_mag ** 2 * (e ** 2 - 1)
        h = np.sqrt(mu * p)
        v_radial = (mu / h) * e * np.sin(nu_burn)
        v_transverse = (mu / h) * (1 + e * np.cos(nu_burn))
        v_after = v_radial * r_hat + v_transverse * t_hat
        candidates.append((e, nu_burn, v_after))
    return candidates, theta


def solve_injection_burn(geom: BurnPointGeometry, v_inf_required, mu_earth=config.GM_EARTH):
    """Exact minimum-delta-v single-impulse solve for the hyperbolic injection.

    geom fixes the burn point (position + pre-burn velocity), already
    determined purely by psi. v_inf_required is the (fixed, psi-independent)
    outgoing hyperbolic excess velocity vector from the Lambert solve, in the
    SAME equatorial frame as geom.

    Considers both plane-normal branches (the orbital plane spanned by
    r_burn and v_inf_required is defined by their cross product up to sign,
    exactly analogous to the short-way/long-way ambiguity in Lambert's
    problem) and all eccentricity roots within each, returning the global
    minimum-delta-v solution.
    """
    r_hat = geom.r_hat
    r_p = np.linalg.norm(geom.r_burn)
    vinf_mag = np.linalg.norm(v_inf_required)
    vinf_hat = v_inf_required / vinf_mag

    cross = np.cross(r_hat, vinf_hat)
    cross_norm = np.linalg.norm(cross)
    if cross_norm < 1e-9:
        raise ValueError(
            "Degenerate geometry: r_burn direction is (anti)parallel to v_infinity "
            "direction; the orbital plane is not uniquely determined. This is a "
            "measure-zero coincidence for a continuous psi sweep -- did not expect "
            "to hit it on a discretized grid."
        )
    n_candidate = cross / cross_norm

    best = None
    for n_hat, branch_name in [(n_candidate, "A"), (-n_candidate, "B")]:
        candidates, theta = _solve_branch(r_hat, r_p, vinf_hat, vinf_mag, n_hat, mu_earth, branch_name)
        for e, nu_burn, v_after in candidates:
            dv_vec = v_after - geom.v_before
            dv_mag = np.linalg.norm(dv_vec)
            p = mu_earth / vinf_mag ** 2 * (e ** 2 - 1)
            r_peri = p / (1 + e)
            result = InjectionBurn(
                v_after=v_after, delta_v=dv_vec, delta_v_mag=dv_mag,
                eccentricity=e, periapsis_radius_km=r_peri,
                true_anomaly_burn_deg=np.degrees(nu_burn), branch=branch_name,
            )
            if best is None or dv_mag < best.delta_v_mag:
                best = result

    if best is None:
        raise RuntimeError("no valid hyperbolic-injection root found for this psi / v_infinity")
    return best
