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
import kepler
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

    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{len(results)-n_fail}/{len(results)} checks passed.")
    if n_fail:
        raise SystemExit(f"{n_fail} validation check(s) FAILED")


if __name__ == "__main__":
    main()
