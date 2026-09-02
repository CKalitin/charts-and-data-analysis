"""Regression/validation checks, run once and documented in README.md.

Not a formal test framework (this repo doesn't use one) -- a standalone
script that re-runs every independent cross-check made during development
and prints PASS/FAIL, so the validation story is reproducible rather than
just asserted in prose.
"""
import numpy as np

import config
import ephemeris
import frames
import injection as inj
import kepler
import raan_sweep
import search

PASS = "PASS"
FAIL = "FAIL"

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  [{PASS if ok else FAIL}] {name}" + (f"  ({detail})" if detail else ""))


def main():
    print("1. Kepler universal-variable propagator")
    mu = config.GM_EARTH
    r0 = np.array([7000.0, 0.0, 0.0])
    v_circ = np.sqrt(mu / np.linalg.norm(r0))
    v0 = np.array([0.0, v_circ, 0.0])
    T = 2 * np.pi * np.sqrt(np.linalg.norm(r0) ** 3 / mu)
    r1, v1 = kepler.propagate(r0, v0, T, mu)
    check("circular orbit returns to start after one period",
          np.linalg.norm(r1 - r0) < 1e-6 and np.linalg.norm(v1 - v0) < 1e-9,
          f"|dr|={np.linalg.norm(r1-r0):.2e} km, |dv|={np.linalg.norm(v1-v0):.2e} km/s")

    r0h = np.array([8000.0, 0.0, 0.0])
    v0h = np.array([2.0, 12.0, 1.0])
    dt = 3600 * 10
    rF, vF = kepler.propagate(r0h, v0h, dt, mu)
    rB, vB = kepler.propagate(rF, vF, -dt, mu)
    check("hyperbolic forward+backward propagation round-trips",
          np.linalg.norm(rB - r0h) < 1e-6 and np.linalg.norm(vB - v0h) < 1e-9,
          f"|dr|={np.linalg.norm(rB-r0h):.2e} km")

    print("\n2. Ephemeris vs JPL Horizons DE441 (fixed reference vectors, 2026-08-28 session)")
    r_earth, v_earth = ephemeris._fetch_astropy("earth", "2020-07-30 00:00:00")
    r_jpl = np.array([9.144837557028542E+07, -1.112507364373438E+08, -4.822736675348621E+07])
    v_jpl = np.array([2.328688880719881E+01, 1.635819526022974E+01, 7.092343288119275E+00])
    dr = np.linalg.norm(r_earth - r_jpl)
    dv = np.linalg.norm(v_earth - v_jpl) * 1000
    check("astropy-fallback Earth state matches Horizons DE441 to <100 km / <10 mm/s",
          dr < 100 and dv < 10, f"dr={dr:.2f} km, dv={dv:.3f} mm/s")

    print("\n3. Lambert solver (Izzo 2015 via lamberthub) self-consistency")
    baseline = search.find_minimum_c3_transfer(verbose=False)
    check("propagating the Lambert solution's (r1,v1) forward by tof reproduces r2",
          baseline.prop_residual_km < 1e-3,
          f"residual={baseline.prop_residual_km:.2e} km")
    check("baseline C3 is in the physically expected range for this window",
          5.0 < baseline.C3 < 30.0, f"C3={baseline.C3:.2f} km^2/s^2")

    print("\n4. Frame rotation orthonormality")
    ok = (np.allclose(frames.R_EQ_TO_ECL @ frames.R_EQ_TO_ECL.T, np.eye(3), atol=1e-12)
          and abs(np.linalg.det(frames.R_EQ_TO_ECL) - 1) < 1e-12)
    check("equatorial<->ecliptic rotation matrix is a proper orthonormal rotation", ok)

    print("\n5. Exact hyperbolic-injection solver (injection.py) vs closed-form periapsis-tangential case")
    r_p = 6771.0
    vinf_mag = 3.5
    e_expected = 1 + r_p * vinf_mag ** 2 / mu
    v_after_expected = np.sqrt(vinf_mag ** 2 + 2 * mu / r_p)
    dv_expected = v_after_expected - np.sqrt(mu / r_p)
    nu_inf_expected = np.arccos(-1 / e_expected)
    r_hat = np.array([1.0, 0.0, 0.0])
    n_test = np.array([0.0, 0.0, 1.0])
    t_hat = np.cross(n_test, r_hat)
    vinf_hat = np.cos(nu_inf_expected) * r_hat + np.sin(nu_inf_expected) * t_hat
    res = inj.solve_injection_burn(r_p * r_hat, np.sqrt(mu / r_p) * t_hat, vinf_mag * vinf_hat, mu)
    check("recovers known eccentricity for a burn forced to periapsis",
          abs(res.eccentricity - e_expected) < 1e-6,
          f"e_solved={res.eccentricity:.6f}, e_expected={e_expected:.6f}")
    check("recovers closed-form delta-v for the periapsis-tangential case",
          abs(res.delta_v_mag - dv_expected) < 1e-6,
          f"dV_solved={res.delta_v_mag:.6f}, dV_expected={dv_expected:.6f} km/s")

    print("\n6. Injection solve cross-checked against independent long-time propagation")
    baseline = search.find_minimum_c3_transfer(verbose=False)
    v_earth_hat = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)
    n_hat_polar = np.cross(np.array([0.0, 0.0, 1.0]), v_earth_hat)
    n_hat_polar /= np.linalg.norm(n_hat_polar)
    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM
    best = inj.solve_best_burn_for_plane(n_hat_polar, baseline.v_inf_dep_eq, r_park, mu, n_scan=360)
    _, v_long = kepler.propagate(best.r_burn, best.injection.v_after, 90 * 86400.0, mu)
    vhat_num = v_long / np.linalg.norm(v_long)
    vhat_req = baseline.v_inf_dep_eq / np.linalg.norm(baseline.v_inf_dep_eq)
    ang_err = np.degrees(np.arccos(np.clip(np.dot(vhat_num, vhat_req), -1, 1)))
    check("best-in-plane burn's propagated asymptote direction matches target v_infinity",
          ang_err < 1e-2, f"angle error={ang_err:.2e} deg, min dV over this plane={best.delta_v_mag:.3f} km/s")

    print("\n7. RAAN sweep periodicity (Omega and Omega+180 deg must trace the identical plane)")
    sweep = raan_sweep.load(baseline)
    n = len(sweep.delta_raan_deg)
    half = n // 2
    # delta_raan_deg runs -180..+180; index i and index (i+half) are 180 deg apart
    max_diff_eq = 0.0
    max_diff_ecl = 0.0
    for i in range(half):
        max_diff_eq = max(max_diff_eq, abs(sweep.dv_equatorial_kms[i] - sweep.dv_equatorial_kms[i + half]))
        max_diff_ecl = max(max_diff_ecl, abs(sweep.dv_ecliptic_kms[i] - sweep.dv_ecliptic_kms[i + half]))
    check("equatorial family: dV(Omega) == dV(Omega+180) across the whole sweep",
          max_diff_eq < 1e-2, f"max diff={max_diff_eq:.2e} km/s (scan resolution sets this floor, not zero)")
    check("ecliptic family: dV(Omega) == dV(Omega+180) across the whole sweep",
          max_diff_ecl < 1e-2, f"max diff={max_diff_ecl:.2e} km/s (scan resolution sets this floor, not zero)")

    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{len(results)-n_fail}/{len(results)} checks passed.")
    if n_fail:
        raise SystemExit(f"{n_fail} validation check(s) FAILED")


if __name__ == "__main__":
    main()
