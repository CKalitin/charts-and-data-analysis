"""Single source of derived results: the baseline transfer, the psi sweeps,
and the nominal flyby geometry. Computed once, cached to disk (npz), loaded
by chart modules. Delete cache/derived_results.npz to force a recompute.
"""
import time
from dataclasses import dataclass

import numpy as np

import arrival
import config
import mcc
import patched_conic as pc
import search

CACHE_FILE = config.CACHE_DIR / "derived_results.npz"


@dataclass
class SweepResults:
    baseline: search.BaselineTransfer
    flyby: arrival.FlybyGeometry
    psi_deg: np.ndarray  # fine grid, departure dV sweep
    dv_departure_kms: np.ndarray
    eccentricity: np.ndarray
    true_anomaly_burn_deg: np.ndarray
    branch: np.ndarray  # 'A' or 'B'
    psi_mcc_deg: np.ndarray  # coarse grid, MCC sweep
    mcc_mean_kms: np.ndarray
    mcc_rss_kms: np.ndarray
    mcc_p95_kms: np.ndarray


def _compute(verbose=True):
    t0 = time.time()
    baseline = search.find_minimum_c3_transfer(verbose=verbose)
    flyby = arrival.flyby_geometry(baseline.v_inf_arr_eq)

    psi_deg = np.linspace(config.PSI_MIN_DEG, config.PSI_MAX_DEG, config.PSI_STEPS)
    dv = np.empty_like(psi_deg)
    ecc = np.empty_like(psi_deg)
    nu_burn = np.empty_like(psi_deg)
    branch = np.empty(len(psi_deg), dtype="<U1")

    for i, psi in enumerate(psi_deg):
        geom = pc.burn_point_geometry(baseline.v_earth_eq, psi)
        burn = pc.solve_injection_burn(geom, baseline.v_inf_dep_eq)
        dv[i] = burn.delta_v_mag
        ecc[i] = burn.eccentricity
        nu_burn[i] = burn.true_anomaly_burn_deg
        branch[i] = burn.branch

    if verbose:
        print(f"departure dV(psi) sweep: {len(psi_deg)} points in {time.time()-t0:.1f}s")

    t1 = time.time()
    psi_mcc = np.arange(config.PSI_MIN_DEG, config.PSI_MAX_DEG + 1e-9, config.MCC_PSI_STEP_DEG)
    mcc_mean = np.empty_like(psi_mcc)
    mcc_rss = np.empty_like(psi_mcc)
    mcc_p95 = np.empty_like(psi_mcc)
    for i, psi in enumerate(psi_mcc):
        res = mcc.mcc_budget(psi, baseline.v_earth_eq, baseline.v_inf_dep_eq,
                              baseline.r_earth_eq, baseline.r_mars_eq, baseline.tof_days,
                              n_samples=config.MCC_N_SAMPLES)
        mcc_mean[i] = res.mean_kms
        mcc_rss[i] = res.rss_kms
        mcc_p95[i] = res.p95_kms

    if verbose:
        print(f"MCC(psi) sweep: {len(psi_mcc)} points x {config.MCC_N_SAMPLES} samples "
              f"in {time.time()-t1:.1f}s")

    return SweepResults(
        baseline=baseline, flyby=flyby, psi_deg=psi_deg, dv_departure_kms=dv,
        eccentricity=ecc, true_anomaly_burn_deg=nu_burn, branch=branch,
        psi_mcc_deg=psi_mcc, mcc_mean_kms=mcc_mean, mcc_rss_kms=mcc_rss, mcc_p95_kms=mcc_p95,
    )


def load(force=False, verbose=True):
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not force and CACHE_FILE.exists():
        d = np.load(CACHE_FILE, allow_pickle=True)
        baseline = d["baseline"].item()
        flyby = d["flyby"].item()
        return SweepResults(
            baseline=baseline, flyby=flyby, psi_deg=d["psi_deg"],
            dv_departure_kms=d["dv_departure_kms"], eccentricity=d["eccentricity"],
            true_anomaly_burn_deg=d["true_anomaly_burn_deg"], branch=d["branch"],
            psi_mcc_deg=d["psi_mcc_deg"], mcc_mean_kms=d["mcc_mean_kms"],
            mcc_rss_kms=d["mcc_rss_kms"], mcc_p95_kms=d["mcc_p95_kms"],
        )

    results = _compute(verbose=verbose)
    np.savez(
        CACHE_FILE,
        baseline=np.array(results.baseline, dtype=object),
        flyby=np.array(results.flyby, dtype=object),
        psi_deg=results.psi_deg, dv_departure_kms=results.dv_departure_kms,
        eccentricity=results.eccentricity, true_anomaly_burn_deg=results.true_anomaly_burn_deg,
        branch=results.branch, psi_mcc_deg=results.psi_mcc_deg,
        mcc_mean_kms=results.mcc_mean_kms, mcc_rss_kms=results.mcc_rss_kms,
        mcc_p95_kms=results.mcc_p95_kms,
    )
    return results


if __name__ == "__main__":
    r = load(force=True)
    print(f"\nBaseline: depart {r.baseline.dep_epoch}, arrive {r.baseline.arr_epoch}, "
          f"C3={r.baseline.C3:.3f} km^2/s^2")
    print(f"Flyby: v_inf={r.flyby.v_inf_kms:.3f} km/s, turn={r.flyby.turn_angle_deg:.1f} deg, "
          f"periapsis v={r.flyby.periapsis_velocity_kms:.3f} km/s")
    print(f"Departure dV(psi): min={r.dv_departure_kms.min():.3f} km/s at "
          f"psi={r.psi_deg[np.argmin(r.dv_departure_kms)]:.0f} deg, "
          f"max={r.dv_departure_kms.max():.3f} km/s at "
          f"psi={r.psi_deg[np.argmax(r.dv_departure_kms)]:.0f} deg")
