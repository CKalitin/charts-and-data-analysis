"""Mars arrival hyperbolic flyby characterization.

Note this is deliberately NOT a function of psi: in the idealized
patched-conic construction used here, the heliocentric transfer orbit (and
therefore the arrival v_infinity) is fixed entirely by the Lambert solve
between Earth's and Mars' positions -- psi only controls how the Earth-
centered departure hyperbola reaches that same, fixed, required v_infinity.
So the nominal flyby geometry is one number, not a sweep; what DOES vary
with psi is the MCC budget needed to actually hit it in the presence of
injection errors (see mcc.py).
"""
from dataclasses import dataclass

import numpy as np

import config


@dataclass
class FlybyGeometry:
    v_inf_kms: float
    periapsis_alt_km: float
    periapsis_radius_km: float
    periapsis_velocity_kms: float
    eccentricity: float
    turn_angle_deg: float
    b_plane_radius_km: float  # impact parameter


def flyby_geometry(v_inf_vec_kms, periapsis_alt_km=config.FLYBY_PERIAPSIS_ALT_KM,
                    mu_mars=config.GM_MARS, r_mars=config.R_MARS):
    v_inf = np.linalg.norm(v_inf_vec_kms)
    r_p = r_mars + periapsis_alt_km

    a = -mu_mars / v_inf ** 2  # hyperbolic semi-major axis, negative
    e = 1 - r_p / a
    v_p = np.sqrt(v_inf ** 2 + 2 * mu_mars / r_p)
    turn_angle = 2 * np.arcsin(1 / e)
    b = -a * np.sqrt(e ** 2 - 1)  # impact parameter (B-plane radius); -a since a<0 for a hyperbola

    return FlybyGeometry(
        v_inf_kms=v_inf, periapsis_alt_km=periapsis_alt_km, periapsis_radius_km=r_p,
        periapsis_velocity_kms=v_p, eccentricity=e, turn_angle_deg=np.degrees(turn_angle),
        b_plane_radius_km=b,
    )
