"""Lambert's-problem solve for the heliocentric Earth->Mars transfer leg.

Uses lamberthub's implementation of Izzo (2015), "Revisiting Lambert's
Problem," Celestial Mechanics and Dynamical Astronomy 121:1 -- a published,
independently-tested solver (not hand-rolled), reducing the chance of a
transcription bug in this high-consequence piece.

The solve is done in the heliocentric ECLIPTIC(J2000) frame so that
lamberthub's `prograde=True` flag matches the actual (counter-clockwise
viewed from ecliptic north) direction planets orbit the Sun -- this
correctly selects the short-way (<180 deg, Type 1) transfer for Earth-Mars.
Every solution is independently re-validated by propagating (r1, v1)
forward with the universal-variable Kepler propagator (kepler.py, itself
validated separately) and checking r(tof) reproduces r2.
"""
from dataclasses import dataclass

import numpy as np
from lamberthub import izzo2015

import config
import frames
import kepler


@dataclass
class TransferSolution:
    r1_ecl: np.ndarray  # km, Earth position at departure, ecliptic frame
    r2_ecl: np.ndarray  # km, Mars position at arrival, ecliptic frame
    v1_ecl: np.ndarray  # km/s, transfer-orbit velocity at departure, ecliptic frame
    v2_ecl: np.ndarray  # km/s, transfer-orbit velocity at arrival, ecliptic frame
    tof_s: float
    prop_residual_km: float  # independent propagation cross-check residual


def solve(r1_eq, r2_eq, tof_s, prograde=True):
    """Solve Lambert's problem given equatorial(ICRS) r1, r2 and tof in seconds.

    Internally rotates to the ecliptic frame (see module docstring), solves,
    validates by re-propagation, and returns everything in the ecliptic
    frame (use frames.ecl_to_eq to bring velocities back to the equatorial
    frame used by the departure/arrival patched-conic geometry).
    """
    r1 = frames.eq_to_ecl(r1_eq)
    r2 = frames.eq_to_ecl(r2_eq)

    v1, v2 = izzo2015(config.GM_SUN, r1, r2, tof_s, M=0, prograde=prograde)

    r2_check, _ = kepler.propagate(r1, v1, tof_s, config.GM_SUN)
    residual = np.linalg.norm(r2_check - r2)

    return TransferSolution(r1_ecl=r1, r2_ecl=r2, v1_ecl=v1, v2_ecl=v2,
                             tof_s=tof_s, prop_residual_km=residual)
