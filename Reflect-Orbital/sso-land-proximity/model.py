"""SSO ground-track propagator.

All functions are pure: same inputs -> same outputs, no globals mutated. Physical
constants are defined once here; config.py holds tunables.

Coordinate frame
----------------
RAAN = 0, AoP = 0 (circular orbit, so AoP is irrelevant). Orbital-plane unit
vectors in ECI:  P = [1, 0, 0],  Q = [0, cos i, sin i].  ECF = ECI rotated by
-GMST about Z.  GMST_0 = 0 is arbitrary: the land fraction integrated over a full
day is RAAN-independent.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MU_EARTH    = 398600.4418        # km^3/s^2
R_EARTH     = 6371.0             # km (mean sphere)
OMEGA_EARTH = 2 * np.pi / 86164.1  # rad/s (sidereal rotation rate)


@dataclass(frozen=True)
class OrbitParams:
    alt_km:  float
    inc_deg: float

    @property
    def inc_rad(self) -> float:
        return np.radians(self.inc_deg)

    @property
    def period_s(self) -> float:
        """Circular orbital period from the vis-viva / Kepler third law."""
        return 2 * np.pi * np.sqrt((R_EARTH + self.alt_km) ** 3 / MU_EARTH)


def propagate_orbit(params: OrbitParams, n_orbits: int,
                    n_per_orbit: int) -> tuple[np.ndarray, np.ndarray]:
    """Propagate a circular SSO ground track for ``n_orbits`` full revolutions.

    Returns
    -------
    lats : (N,) sub-satellite latitude, degrees
    lons : (N,) sub-satellite longitude, degrees (accounting for Earth rotation)

    Time steps are uniform along the orbit, so for a circular orbit every sample
    carries equal time weight — the fraction of samples in a category equals the
    fraction of orbit *time* in that category.
    """
    inc = params.inc_rad
    T_s = params.period_s

    P = np.array([1.0, 0.0, 0.0])
    Q = np.array([0.0, np.cos(inc), np.sin(inc)])

    all_lats, all_lons = [], []
    for orb in range(n_orbits):
        t0 = orb * T_s
        u = np.linspace(0, 2 * np.pi, n_per_orbit, endpoint=False)  # argument of latitude

        r_eci = np.outer(np.cos(u), P) + np.outer(np.sin(u), Q)     # (N, 3) on unit sphere

        t = t0 + (u / (2 * np.pi)) * T_s
        gmst = OMEGA_EARTH * t                                       # (N,)

        x_ecf =  r_eci[:, 0] * np.cos(gmst) + r_eci[:, 1] * np.sin(gmst)
        y_ecf = -r_eci[:, 0] * np.sin(gmst) + r_eci[:, 1] * np.cos(gmst)
        z_ecf =  r_eci[:, 2]

        all_lats.append(np.degrees(np.arcsin(np.clip(z_ecf, -1.0, 1.0))))
        all_lons.append(np.degrees(np.arctan2(y_ecf, x_ecf)))

    return np.concatenate(all_lats), np.concatenate(all_lons)
