"""RAAN sweep for two orbital-plane families, both scored the same way:
for each candidate plane, the minimum achievable injection delta-v (see
injection.py) to reach the fixed baseline transfer's departure v_infinity,
minimized over where in that plane you burn.

Two families:
  - EQUATORIAL ("real" polar orbits): plane contains Earth's spin axis.
    i = 90 deg relative to Earth's actual equator, always -- these are
    physically launchable polar orbits.
  - ECLIPTIC ("solar-system-polar"): plane contains the ecliptic normal
    instead. NOT i=90 relative to Earth's equator in general (it varies
    with RAAN, and is 90 relative to the ECLIPTIC instead) -- not a real
    "polar" orbit in the standard sense, but geometrically cleaner
    relative to v_Earth (v_Earth is exactly in the ecliptic, so the
    ecliptic normal and v_Earth are exactly orthogonal, unlike Earth's
    spin axis and v_Earth, which are not).

For each family, RAAN is swept over the FULL 360 degrees, but both
families have an exact 180-degree periodicity (Omega and Omega+180 trace
the identical great-circle plane once inclination is fixed at exactly 90
deg relative to the family's own reference axis) -- this is checked
explicitly in validate.py rather than assumed.

Both are reported on the SAME x-axis: RAAN offset (deg) from that family's
own v_Earth-containing plane (0 deg = the one plane special to this whole
project so far), so the two curves are directly comparable.
"""
import time
from dataclasses import dataclass

import numpy as np

import config
import frames
import injection as inj

RAAN_SWEEP_STEP_DEG = 5.0
RAAN_SWEEP_SCAN_PER_PLANE = 180  # burn-point resolution within each candidate plane

CACHE_FILE = config.CACHE_DIR / "raan_sweep.npz"


@dataclass
class RaanSweepResults:
    delta_raan_deg: np.ndarray  # shared x-axis: RAAN offset from the v_Earth-containing plane
    dv_equatorial_kms: np.ndarray
    dv_ecliptic_kms: np.ndarray
    raan_v_earth_equatorial_deg: float  # the actual RA of v_Earth (equatorial frame)
    raan_v_earth_ecliptic_deg: float  # the actual ecliptic longitude of v_Earth


def _plane_normal(delta_deg, raan0_deg, frame):
    """Unit normal of the polar-type plane at RAAN = raan0 + delta, built in
    `frame` ('equatorial' or 'ecliptic') then returned in the equatorial
    frame injection.py expects."""
    raan = np.radians(raan0_deg + delta_deg)
    n = np.array([-np.sin(raan), np.cos(raan), 0.0])  # always in the BUILD frame's own x-y plane
    if frame == "ecliptic":
        n = frames.ecl_to_eq(n)
    return n


def compute(baseline, verbose=True):
    v_earth_hat_eq = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)
    raan0_eq = np.degrees(np.arctan2(v_earth_hat_eq[1], v_earth_hat_eq[0]))

    v_earth_ecl = frames.eq_to_ecl(baseline.v_earth_eq)
    raan0_ecl = np.degrees(np.arctan2(v_earth_ecl[1], v_earth_ecl[0]))

    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM
    deltas = np.arange(-180.0, 180.0 + 1e-9, RAAN_SWEEP_STEP_DEG)

    dv_eq = np.empty_like(deltas)
    dv_ecl = np.empty_like(deltas)

    t0 = time.time()
    for i, d in enumerate(deltas):
        n_eq = _plane_normal(d, raan0_eq, "equatorial")
        dv_eq[i], _ = inj.minimum_delta_v_for_plane(n_eq, baseline.v_inf_dep_eq, r_park,
                                                      config.GM_EARTH, n_scan=RAAN_SWEEP_SCAN_PER_PLANE)
        n_ecl = _plane_normal(d, raan0_ecl, "ecliptic")
        dv_ecl[i], _ = inj.minimum_delta_v_for_plane(n_ecl, baseline.v_inf_dep_eq, r_park,
                                                       config.GM_EARTH, n_scan=RAAN_SWEEP_SCAN_PER_PLANE)
    if verbose:
        print(f"RAAN sweep: {len(deltas)} points x 2 families in {time.time()-t0:.1f}s")

    return RaanSweepResults(delta_raan_deg=deltas, dv_equatorial_kms=dv_eq, dv_ecliptic_kms=dv_ecl,
                             raan_v_earth_equatorial_deg=raan0_eq, raan_v_earth_ecliptic_deg=raan0_ecl)


def load(baseline, force=False, verbose=True):
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not force and CACHE_FILE.exists():
        d = np.load(CACHE_FILE)
        return RaanSweepResults(
            delta_raan_deg=d["delta_raan_deg"], dv_equatorial_kms=d["dv_equatorial_kms"],
            dv_ecliptic_kms=d["dv_ecliptic_kms"],
            raan_v_earth_equatorial_deg=float(d["raan_v_earth_equatorial_deg"]),
            raan_v_earth_ecliptic_deg=float(d["raan_v_earth_ecliptic_deg"]),
        )
    results = compute(baseline, verbose=verbose)
    np.savez(CACHE_FILE, delta_raan_deg=results.delta_raan_deg,
             dv_equatorial_kms=results.dv_equatorial_kms, dv_ecliptic_kms=results.dv_ecliptic_kms,
             raan_v_earth_equatorial_deg=results.raan_v_earth_equatorial_deg,
             raan_v_earth_ecliptic_deg=results.raan_v_earth_ecliptic_deg)
    return results


if __name__ == "__main__":
    import derived
    d = derived.load()
    r = load(d.baseline, force=True)
    i_eq = int(np.argmin(r.dv_equatorial_kms))
    i_ecl = int(np.argmin(r.dv_ecliptic_kms))
    print(f"Equatorial family: min dV = {r.dv_equatorial_kms[i_eq]:.3f} km/s at "
          f"dRAAN = {r.delta_raan_deg[i_eq]:.0f} deg")
    print(f"Ecliptic family:   min dV = {r.dv_ecliptic_kms[i_ecl]:.3f} km/s at "
          f"dRAAN = {r.delta_raan_deg[i_ecl]:.0f} deg")
