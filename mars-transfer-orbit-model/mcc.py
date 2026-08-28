"""Mid-course-correction delta-v as a function of psi.

Approach: Monte Carlo the TMI burn's execution error (magnitude + pointing),
propagate the ACTUAL (perturbed) departure hyperbola out to the asymptotic
regime to get the actual v_infinity, patch to the heliocentric frame
(zero-SOI-radius patched-conic approximation: heliocentric position at the
patch point = Earth's position; this is standard practice, e.g. Bate/
Mueller/White, and is justified here since Earth's SOI radius, ~9.24e5 km,
is ~0.6% of the Earth-Sun distance), propagate the actual heliocentric
trajectory forward to a chosen MCC epoch, then solve a FRESH Lambert problem
from that actual position to Mars' target position for the remaining time of
flight. The correction delta-v is the vector difference between the
required (re-targeted) velocity and the actual (uncorrected) velocity at the
MCC epoch. This re-uses the same validated Lambert solver and Kepler
propagator as the rest of the model rather than a separate linearized
state-transition-matrix machinery, at the cost of doing an exact (if
Monte-Carlo-sampled) re-target instead of a closed-form sensitivity.
"""
from dataclasses import dataclass

import numpy as np

import config
import frames
import kepler
import lambert
import patched_conic as pc

ASYMPTOTE_PROPAGATION_DAYS = 90.0


def _perpendicular_basis(v_hat, rng):
    ref = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(ref, v_hat)) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    p1 = np.cross(v_hat, ref)
    p1 /= np.linalg.norm(p1)
    p2 = np.cross(v_hat, p1)
    return p1, p2


@dataclass
class MccResult:
    psi_deg: float
    n_samples: int
    dv_samples_kms: np.ndarray

    @property
    def mean_kms(self):
        return float(np.mean(self.dv_samples_kms))

    @property
    def rss_kms(self):
        return float(np.sqrt(np.mean(self.dv_samples_kms ** 2)))

    @property
    def p95_kms(self):
        return float(np.percentile(self.dv_samples_kms, 95))


def mcc_budget(psi_deg, v_earth_eq, v_inf_required_eq, r_earth_eq, r_mars_eq,
               tof_days, n_samples=60, seed=0):
    rng = np.random.default_rng(seed + int(round((psi_deg + 90.0) * 1000)))

    geom = pc.burn_point_geometry(v_earth_eq, psi_deg)
    burn = pc.solve_injection_burn(geom, v_inf_required_eq)

    v_after_hat = burn.v_after / np.linalg.norm(burn.v_after)
    v_after_mag = np.linalg.norm(burn.v_after)
    p1, p2 = _perpendicular_basis(v_after_hat, rng)

    sigma_dv = config.MCC_INJECTION_DV_ERROR_KMS
    sigma_point = np.radians(config.MCC_INJECTION_POINTING_ERROR_DEG)

    remaining_tof_s = (tof_days - config.MCC_EPOCH_OFFSET_DAYS) * 86400.0
    mcc_dt_s = config.MCC_EPOCH_OFFSET_DAYS * 86400.0

    dv_samples = np.empty(n_samples)
    for i in range(n_samples):
        dmag = rng.normal(0.0, sigma_dv)
        tip = rng.normal(0.0, sigma_point)
        tilt = rng.normal(0.0, sigma_point)

        v_hat_actual = v_after_hat + tip * p1 + tilt * p2
        v_hat_actual /= np.linalg.norm(v_hat_actual)
        v_after_actual = (v_after_mag + dmag) * v_hat_actual

        # propagate the actual departure hyperbola out to the asymptotic regime
        _, v_long = kepler.propagate(geom.r_burn, v_after_actual,
                                      ASYMPTOTE_PROPAGATION_DAYS * 86400.0, config.GM_EARTH)
        v_inf_actual_eq = v_long  # converges to v_infinity at large propagation time

        # patch to heliocentric frame (zero-SOI-radius approximation)
        r_patch = r_earth_eq
        v_patch = v_earth_eq + v_inf_actual_eq

        r_mcc, v_mcc_actual = kepler.propagate(r_patch, v_patch, mcc_dt_s, config.GM_SUN)

        sol = lambert.solve(r_mcc, r_mars_eq, remaining_tof_s)
        v_required = frames.ecl_to_eq(sol.v1_ecl)

        dv_samples[i] = np.linalg.norm(v_required - v_mcc_actual)

    return MccResult(psi_deg=psi_deg, n_samples=n_samples, dv_samples_kms=dv_samples)
