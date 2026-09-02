"""Classical orbital elements from a heliocentric state vector.

Kept separate from kepler.py (which propagates a state forward) so the
"what orbit is this?" question lives in one place: the inclination / node
geometry the ecliptic-vs-Mars chart needs is the same geometry any later
element-based chart will want, and orbit_track() is the one full-period
sampler every heliocentric chart shares.

Elements are referenced to whatever frame the input state is expressed in --
pass ecliptic-frame vectors (frames.eq_to_ecl) to get the inclination and
RAAN relative to the ecliptic, equatorial vectors to get them relative to
the equator.
"""
from dataclasses import dataclass

import numpy as np

import kepler

_Z_HAT = np.array([0.0, 0.0, 1.0])


@dataclass
class Elements:
    a_km: float
    e: float
    i_deg: float           # inclination w.r.t. the input frame's XY plane
    raan_deg: float        # right ascension / longitude of the ascending node
    period_s: float        # inf for a non-closed (parabolic/hyperbolic) orbit
    h_hat: np.ndarray      # orbit-normal unit vector
    node_hat: np.ndarray   # unit vector toward the ASCENDING node (lies in the XY plane)


def from_state(r, v, mu):
    """Classical elements of the osculating orbit through state (r, v)."""
    r = np.asarray(r, dtype=float)
    v = np.asarray(v, dtype=float)
    r_norm = np.linalg.norm(r)

    h = np.cross(r, v)
    h_hat = h / np.linalg.norm(h)

    a = 1.0 / (2.0 / r_norm - np.dot(v, v) / mu)
    e_vec = np.cross(v, h) / mu - r / r_norm

    i = np.arccos(np.clip(h_hat[2], -1.0, 1.0))

    # n = z_hat x h points at the ascending node. Its magnitude is sin(i), so it
    # degenerates as i -> 0; a zero-inclination orbit has no defined node line and
    # we fall back to the frame's X axis rather than dividing by ~0.
    node = np.cross(_Z_HAT, h_hat)
    n_norm = np.linalg.norm(node)
    node_hat = node / n_norm if n_norm > 1e-12 else np.array([1.0, 0.0, 0.0])

    return Elements(
        a_km=float(a),
        e=float(np.linalg.norm(e_vec)),
        i_deg=float(np.degrees(i)),
        raan_deg=float(np.degrees(np.arctan2(node_hat[1], node_hat[0])) % 360.0),
        period_s=float(2 * np.pi * np.sqrt(a ** 3 / mu)) if a > 0 else float("inf"),
        h_hat=h_hat,
        node_hat=node_hat,
    )


def orbit_track(r0, v0, mu, n_points=300):
    """Sample one full osculating period starting from (r0, v0). Returns (N, 3) km."""
    ts = np.linspace(0.0, from_state(r0, v0, mu).period_s, n_points)
    return np.array([kepler.propagate(r0, v0, t, mu)[0] for t in ts])
