"""Equatorial(ICRS/J2000) <-> ecliptic(J2000) rotation.

Validated against JPL Horizons DE441 (2026-08-28 session): rotating an
ICRS-frame heliocentric state by the fixed IAU2006 J2000 mean obliquity
reproduces Horizons' "Ecliptic of J2000.0" heliocentric vectors to ~4 km /
~1 mm/s for Earth and ~4 km / ~1.8 m/s for Mars. See ephemeris.py docstring
for the full validation note.

ICRS is treated as equivalent to the "mean equator and equinox of J2000"
frame classical orbital elements are conventionally referenced to; the
difference (frame bias, tens of milliarcseconds) is negligible next to the
ephemeris-level uncertainty already in this model.
"""
import numpy as np

import config

_EPS = np.radians(config.OBLIQUITY_J2000_DEG)
_COS_EPS = np.cos(_EPS)
_SIN_EPS = np.sin(_EPS)

# Equatorial (ICRS/J2000) -> Ecliptic (J2000): rotation about x-axis by +eps.
R_EQ_TO_ECL = np.array([
    [1.0, 0.0, 0.0],
    [0.0, _COS_EPS, _SIN_EPS],
    [0.0, -_SIN_EPS, _COS_EPS],
])
R_ECL_TO_EQ = R_EQ_TO_ECL.T


def eq_to_ecl(v):
    """Rotate a (3,) or (N,3) vector from equatorial(ICRS) to ecliptic(J2000)."""
    v = np.asarray(v)
    if v.ndim == 1:
        return R_EQ_TO_ECL @ v
    return v @ R_EQ_TO_ECL.T


def ecl_to_eq(v):
    """Rotate a (3,) or (N,3) vector from ecliptic(J2000) to equatorial(ICRS)."""
    v = np.asarray(v)
    if v.ndim == 1:
        return R_ECL_TO_EQ @ v
    return v @ R_ECL_TO_EQ.T
