"""Single source of derived results: the baseline transfer and the nominal
flyby geometry. Computed once, cached to disk (npz), loaded by chart
modules. Delete cache/derived_results.npz to force a recompute.

(Formerly also computed a psi sweep -- deleted along with patched_conic.py
and mcc.py; the departure model is being rebuilt around a RAAN sweep instead.)
"""
from dataclasses import dataclass

import numpy as np

import arrival
import config
import search

CACHE_FILE = config.CACHE_DIR / "derived_results.npz"


@dataclass
class SweepResults:
    baseline: search.BaselineTransfer
    flyby: arrival.FlybyGeometry


def _compute(verbose=True):
    baseline = search.find_minimum_c3_transfer(verbose=verbose)
    flyby = arrival.flyby_geometry(baseline.v_inf_arr_eq)
    return SweepResults(baseline=baseline, flyby=flyby)


def load(force=False, verbose=True):
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not force and CACHE_FILE.exists():
        d = np.load(CACHE_FILE, allow_pickle=True)
        return SweepResults(baseline=d["baseline"].item(), flyby=d["flyby"].item())

    results = _compute(verbose=verbose)
    np.savez(
        CACHE_FILE,
        baseline=np.array(results.baseline, dtype=object),
        flyby=np.array(results.flyby, dtype=object),
    )
    return results


if __name__ == "__main__":
    r = load(force=True)
    print(f"\nBaseline: depart {r.baseline.dep_epoch}, arrive {r.baseline.arr_epoch}, "
          f"C3={r.baseline.C3:.3f} km^2/s^2")
    print(f"Flyby: v_inf={r.flyby.v_inf_kms:.3f} km/s, turn={r.flyby.turn_angle_deg:.1f} deg, "
          f"periapsis v={r.flyby.periapsis_velocity_kms:.3f} km/s")
