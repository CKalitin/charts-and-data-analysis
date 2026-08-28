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
import patched_conic as pc
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

    print("\n4. Exact hyperbolic-injection solver vs closed-form periapsis-tangential case")
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
    geom = pc.BurnPointGeometry(psi_deg=0.0, n_hat=n_test, r_hat=r_hat, v_hat=t_hat,
                                 r_burn=r_p * r_hat, v_before=np.sqrt(mu / r_p) * t_hat)
    burn = pc.solve_injection_burn(geom, vinf_mag * vinf_hat, mu_earth=mu)
    check("recovers known eccentricity for a burn forced to periapsis",
          abs(burn.eccentricity - e_expected) < 1e-6,
          f"e_solved={burn.eccentricity:.6f}, e_expected={e_expected:.6f}")
    check("recovers closed-form delta-v for the periapsis-tangential case",
          abs(burn.delta_v_mag - dv_expected) < 1e-6,
          f"dV_solved={burn.delta_v_mag:.6f}, dV_expected={dv_expected:.6f} km/s")

    print("\n5. Injection-burn solve cross-checked against independent long-time propagation")
    v_earth_eq = baseline.v_earth_eq
    for psi in [-90, -45, 0, 45, 90]:
        geom = pc.burn_point_geometry(v_earth_eq, psi)
        burn = pc.solve_injection_burn(geom, baseline.v_inf_dep_eq)
        _, v_long = kepler.propagate(geom.r_burn, burn.v_after, 90 * 86400.0, config.GM_EARTH)
        vhat_num = v_long / np.linalg.norm(v_long)
        vhat_req = baseline.v_inf_dep_eq / np.linalg.norm(baseline.v_inf_dep_eq)
        ang_err = np.degrees(np.arccos(np.clip(np.dot(vhat_num, vhat_req), -1, 1)))
        check(f"psi={psi:4d} deg: propagated asymptote direction matches target v_infinity",
              ang_err < 1e-2, f"angle error={ang_err:.2e} deg")

    print("\n6. Frame rotation orthonormality")
    ok = (np.allclose(frames.R_EQ_TO_ECL @ frames.R_EQ_TO_ECL.T, np.eye(3), atol=1e-12)
          and abs(np.linalg.det(frames.R_EQ_TO_ECL) - 1) < 1e-12)
    check("equatorial<->ecliptic rotation matrix is a proper orthonormal rotation", ok)

    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{len(results)-n_fail}/{len(results)} checks passed.")
    if n_fail:
        raise SystemExit(f"{n_fail} validation check(s) FAILED")


if __name__ == "__main__":
    main()
