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
BENCH_CACHE_FILE = config.CACHE_DIR / "nonpolar_benchmarks.npz"
INC_CACHE_FILE = config.CACHE_DIR / "inclination_sweep.npz"


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


def raan0_for_family(baseline, family):
    """The actual RAAN (family's own build frame) of the plane containing
    v_Earth exactly -- the shared ΔRAAN=0 reference point for that family."""
    if family == "equatorial":
        v_hat = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)
    elif family == "ecliptic":
        v_hat = frames.eq_to_ecl(baseline.v_earth_eq)
    else:
        raise ValueError(f"unknown family: {family!r}")
    return np.degrees(np.arctan2(v_hat[1], v_hat[0]))


def plane_normal(baseline, family, delta_raan_deg):
    """Public helper: the plane normal (equatorial/ICRS frame, as injection.py
    expects) for `family` ('equatorial' or 'ecliptic') at RAAN offset
    delta_raan_deg from that family's own v_Earth-containing reference plane
    -- reconstructs exactly the planes compute() scores, for reuse by the
    geometry illustration charts."""
    raan0 = raan0_for_family(baseline, family)
    return _plane_normal(delta_raan_deg, raan0, family)


def compute(baseline, verbose=True):
    raan0_eq = raan0_for_family(baseline, "equatorial")
    raan0_ecl = raan0_for_family(baseline, "ecliptic")

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


# --------------------------------------------------------------------------- #
# Non-polar benchmarks: what a NORMAL (non-polar) mission would pay
# --------------------------------------------------------------------------- #
# The governing quantity is DLA, the declination of the departure v_infinity
# relative to Earth's equator. A circular parking orbit of inclination i can be
# oriented (by choice of RAAN) to CONTAIN v_infinity if and only if i >= |DLA|,
# and any plane that contains v_infinity reaches the same single-impulse
# minimum -- the floor -- because the geometry is invariant under rotation about
# the v_infinity axis. So the floor is not special to polar orbits: it is
# available to every inclination at or above |DLA|, including an ordinary
# launch-site parking orbit. Below |DLA| the plane cannot contain v_infinity at
# any RAAN and a real plane-change penalty appears -- which is what makes the
# equatorial (i=0) case genuinely expensive.


@dataclass
class NonPolarBenchmarks:
    dla_deg: float                  # declination of v_inf w.r.t. Earth's equator
    vinf_out_of_ecliptic_deg: float
    dv_floor_kms: float             # any plane containing v_inf
    dv_equatorial_kms: float        # i = 0 to Earth's equator (cannot contain v_inf)
    dv_ecliptic_plane_kms: float    # i = 0 to the ecliptic (23.4 deg to the equator)
    dv_standard_kms: float          # STANDARD_PARKING_INCLINATION_DEG at its best RAAN
    standard_inc_deg: float
    standard_raan_deg: float


def _normal_from_inc_raan(inc_rad, raan_rad):
    """Plane normal(s) for inclination + RAAN. raan_rad may be an array, so the
    constant z-component is broadcast rather than left scalar."""
    raan_rad = np.asarray(raan_rad, dtype=float)
    return np.stack([np.sin(raan_rad) * np.sin(inc_rad),
                     -np.cos(raan_rad) * np.sin(inc_rad),
                     np.full(raan_rad.shape, np.cos(inc_rad))])


def best_raan_normal(vinf_hat, inc_deg, n_grid=200001):
    """Normal + RAAN of the inclination-`inc_deg` plane that comes CLOSEST to
    containing vinf_hat, and the residual out-of-plane angle of v_inf (deg).

    Closed form for the residual: with n.vinf = sin(i)*A*sin(RAAN-phi) + cos(i)*sin(DLA)
    and A = cos(DLA), the reachable range of n.vinf is [sin(DLA-i), sin(DLA+i)], so the
    best attainable out-of-plane angle is max(0, |DLA| - i) -- zero exactly when
    i >= |DLA|. The RAAN itself is picked by a dense scan of |n.vinf| (pure arithmetic,
    far cheaper than the delta-v solve it feeds); the closed form is returned alongside
    as the value the scan should reproduce."""
    inc = np.radians(inc_deg)
    dla = abs(np.degrees(np.arcsin(np.clip(vinf_hat[2], -1.0, 1.0))))
    raans = np.linspace(0.0, 2 * np.pi, n_grid)
    normals = _normal_from_inc_raan(inc, raans)
    dots = normals.T @ vinf_hat
    k = int(np.argmin(np.abs(dots)))
    residual_deg = float(np.degrees(np.arcsin(np.clip(abs(dots[k]), 0.0, 1.0))))
    return normals[:, k], float(np.degrees(raans[k])), residual_deg, max(0.0, dla - inc_deg)


def plane_containing_vinf(vinf_hat, inc_deg, n_grid=200001):
    """Normal (equatorial frame) and RAAN of the inclination-`inc_deg` plane that
    contains vinf_hat, or (None, None) when inc_deg < |DLA| and none exists.

    Solved by a dense 1-D scan on the single unknown (RAAN) of |n . vinf_hat|;
    the residual is smooth and the scan is pure arithmetic, so this costs far
    less than the delta-v solve it feeds."""
    inc = np.radians(inc_deg)
    dla = abs(np.degrees(np.arcsin(np.clip(vinf_hat[2], -1.0, 1.0))))
    if inc_deg < dla - 1e-9:
        return None, None
    raans = np.linspace(0.0, 2 * np.pi, n_grid)
    normals = _normal_from_inc_raan(inc, raans)          # (3, N)
    k = int(np.argmin(np.abs(normals.T @ vinf_hat)))
    return normals[:, k], float(np.degrees(raans[k]))


def compute_nonpolar_benchmarks(baseline, verbose=True):
    vinf = baseline.v_inf_dep_eq
    vinf_hat = vinf / np.linalg.norm(vinf)
    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM
    n_scan = RAAN_SWEEP_SCAN_PER_PLANE * 2   # these are only a handful of planes; afford the resolution

    def dv(n):
        # minimum_delta_v_for_plane builds its in-plane basis from this vector without
        # normalising it, so a non-unit normal (e.g. cross(vinf_hat, z), whose length is
        # cos(DLA)) silently distorts the geometry. Normalise here, once.
        n_hat = np.asarray(n, dtype=float)
        n_hat = n_hat / np.linalg.norm(n_hat)
        return inj.minimum_delta_v_for_plane(n_hat, vinf, r_park, config.GM_EARTH, n_scan=n_scan)[0]

    dla = float(np.degrees(np.arcsin(vinf_hat[2])))
    vinf_ecl = frames.eq_to_ecl(vinf)
    out_of_ecl = float(np.degrees(np.arcsin(vinf_ecl[2] / np.linalg.norm(vinf_ecl))))

    n_std, raan_std = plane_containing_vinf(vinf_hat, config.STANDARD_PARKING_INCLINATION_DEG)
    if n_std is None:
        raise ValueError(
            f"STANDARD_PARKING_INCLINATION_DEG={config.STANDARD_PARKING_INCLINATION_DEG} is below "
            f"|DLA|={abs(dla):.2f} deg for this window, so no RAAN puts v_infinity in that plane. "
            "Pick a higher benchmark inclination, or handle the plane-change case explicitly.")

    result = NonPolarBenchmarks(
        dla_deg=dla,
        vinf_out_of_ecliptic_deg=out_of_ecl,
        dv_floor_kms=float(dv(np.cross(vinf_hat, np.array([0.0, 0.0, 1.0])))),
        dv_equatorial_kms=float(dv(np.array([0.0, 0.0, 1.0]))),
        dv_ecliptic_plane_kms=float(dv(frames.ecl_to_eq(np.array([0.0, 0.0, 1.0])))),
        dv_standard_kms=float(dv(n_std)),
        standard_inc_deg=float(config.STANDARD_PARKING_INCLINATION_DEG),
        standard_raan_deg=raan_std,
    )
    if verbose:
        print(f"Non-polar benchmarks: DLA={dla:+.2f} deg, floor={result.dv_floor_kms:.4f}, "
              f"i={result.standard_inc_deg:.1f} deg={result.dv_standard_kms:.4f}, "
              f"ecliptic-plane={result.dv_ecliptic_plane_kms:.4f}, "
              f"equatorial={result.dv_equatorial_kms:.4f} km/s")
    return result


def load_nonpolar_benchmarks(baseline, force=False, verbose=True):
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not force and BENCH_CACHE_FILE.exists():
        d = np.load(BENCH_CACHE_FILE)
        return NonPolarBenchmarks(**{k: float(d[k]) for k in d.files})
    result = compute_nonpolar_benchmarks(baseline, verbose=verbose)
    np.savez(BENCH_CACHE_FILE, **result.__dict__)
    return result


# --------------------------------------------------------------------------- #
# Parking-orbit inclination sweep
# --------------------------------------------------------------------------- #
@dataclass
class InclinationSweep:
    inclination_deg: np.ndarray   # 0..90; covers every possible parking-orbit plane
    dv_kms: np.ndarray            # best over RAAN and burn point, for that inclination
    best_raan_deg: np.ndarray
    out_of_plane_deg: np.ndarray  # residual angle of v_inf to the plane: max(0, |DLA| - i)
    dla_deg: float


def compute_inclination_sweep(baseline, verbose=True):
    """Cheapest achievable injection delta-v as a function of parking-orbit inclination.

    For each inclination only ONE plane is scored: the RAAN that comes closest to
    putting v_infinity in the plane (best_raan_normal). That is a real shortcut over
    a 2-D (inclination x RAAN) brute force, and it rests on delta-v increasing
    monotonically with the residual out-of-plane angle -- checked against a brute-force
    RAAN scan in validate.py rather than assumed."""
    vinf = baseline.v_inf_dep_eq
    vinf_hat = vinf / np.linalg.norm(vinf)
    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM
    incs = np.arange(0.0, 90.0 + 1e-9, config.INCLINATION_SWEEP_STEP_DEG)

    dv = np.empty_like(incs)
    raans = np.empty_like(incs)
    oop = np.empty_like(incs)

    t0 = time.time()
    for k, inc in enumerate(incs):
        n_hat, raan, resid, _ = best_raan_normal(vinf_hat, float(inc))
        n_hat = n_hat / np.linalg.norm(n_hat)
        dv[k], _ = inj.minimum_delta_v_for_plane(n_hat, vinf, r_park, config.GM_EARTH,
                                                  n_scan=RAAN_SWEEP_SCAN_PER_PLANE)
        raans[k], oop[k] = raan, resid
    if verbose:
        print(f"Inclination sweep: {len(incs)} inclinations in {time.time() - t0:.1f}s")

    return InclinationSweep(
        inclination_deg=incs, dv_kms=dv, best_raan_deg=raans, out_of_plane_deg=oop,
        dla_deg=float(np.degrees(np.arcsin(np.clip(vinf_hat[2], -1.0, 1.0)))),
    )


def load_inclination_sweep(baseline, force=False, verbose=True):
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not force and INC_CACHE_FILE.exists():
        d = np.load(INC_CACHE_FILE)
        return InclinationSweep(
            inclination_deg=d["inclination_deg"], dv_kms=d["dv_kms"],
            best_raan_deg=d["best_raan_deg"], out_of_plane_deg=d["out_of_plane_deg"],
            dla_deg=float(d["dla_deg"]))
    r = compute_inclination_sweep(baseline, verbose=verbose)
    np.savez(INC_CACHE_FILE, inclination_deg=r.inclination_deg, dv_kms=r.dv_kms,
             best_raan_deg=r.best_raan_deg, out_of_plane_deg=r.out_of_plane_deg,
             dla_deg=r.dla_deg)
    return r


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
