# Mars transfer orbit model: departure ΔV vs. parking-orbit RAAN

Patched-conic model of a polar-parking-orbit departure to Mars, studying how
the parking orbit's **RAAN (right ascension of ascending node)** — which
great-circle plane, out of all the polar-type planes around Earth, the
departure burn happens in — drives the achievable departure ΔV.

This is a plane-selection study, not a burn-point-phasing study: for each
candidate plane, the model reports the *best possible* injection ΔV
achievable from anywhere in that plane (burn point and parking-orbit
traversal direction both optimized away), so what's left is purely the cost
of the plane's orientation.

## The core idea

A polar orbit is only "polar" relative to *something*. This model sweeps two
different families of planes, both loosely called "polar," which agree only
at one shared reference plane:

- **Equatorial family** — the plane contains Earth's spin axis. This is what
  "polar orbit" means in ordinary usage: inclination is exactly 90° to
  Earth's *equator*, for every RAAN. These are the real, physically
  launchable polar orbits.
- **Ecliptic family** — the plane contains the ecliptic normal instead of
  Earth's spin axis. Inclination to Earth's actual equator now *varies with
  RAAN* (since the ecliptic normal is tilted 23.44° from Earth's spin axis)
  — this is "polar relative to the solar system," not a real polar orbit in
  the standard sense, but it's the natural frame if you define "polar" by
  looking straight down on the plane of the ecliptic and asking for orbits
  perpendicular to *that* view instead of Earth's own spin.

For each family, RAAN is swept over the full 360°, reported as **ΔRAAN**:
the offset from that family's own plane that happens to contain Earth's
heliocentric velocity vector `v_Earth` (ΔRAAN=0 is a natural, shared
reference point for both curves, not a claim that the planes coincide there
— they don't, except at that one point). Both families have an exact
180°-periodicity — ΔRAAN and ΔRAAN+180° are the identical great-circle plane
once inclination is fixed at exactly 90° to the family's own reference axis
— checked explicitly (`validate.py` check 7), not assumed.

**What's swept vs. held fixed.** The heliocentric transfer itself (the
Lambert-solved Earth→Mars trajectory, and therefore the required departure
`v∞`) is completely independent of RAAN — the plane choice only affects how
expensively the Earth-centered departure burn reaches that fixed target.
Within each candidate plane, the burn point and the parking orbit's
traversal direction (prograde or retrograde, in that plane) are *both*
optimized to find the plane's own best case (`injection.minimum_delta_v_for_plane`)
— so the reported curve isolates the ΔV cost of plane orientation alone,
with everything else already minimized out.

## Why plane orientation matters at all

The cheapest possible burn (the unconstrained floor, ignoring any
polar-type-plane constraint) happens when the parking-orbit plane contains
`v∞` itself, letting the whole injection burn be a single tangential
speed-up. Neither family can achieve that in general, because `v∞` isn't
exactly `v_Earth`: it's `v_transfer,depart − v_Earth` from the Lambert
solve, and for the baseline transfer it sits **14.7°** away from `v_Earth`'s
own direction. A plane chosen to contain `v_Earth` (ΔRAAN=0) therefore still
carries a real misalignment against `v∞` — and away from ΔRAAN=0 that
penalty only grows, up to the point where the plane and `v∞` are badly
misaligned.

Both families' minima end up close to the ΔRAAN=0 reference plane (within
one 5° sweep step of it, given `v∞` is only 14.7° from `v_Earth`), but not
exactly at it and not exactly equal to each other, since the two families'
planes only coincide with each other at isolated points around the sweep.

## Pipeline

1. **Ephemeris** (`ephemeris.py`) — Earth/Mars heliocentric state vectors,
   fetched live from JPL Horizons (DE441) and cached; falls back to
   astropy's built-in analytic ephemeris if the network is unavailable.
2. **Lambert solve** (`lambert.py`) — Izzo (2015) via the published
   `lamberthub` package, done in the ecliptic frame so `prograde=True`
   correctly selects the Type-1 (<180°) transfer.
3. **Window search** (`search.py`) — grid search over the real Mars 2020
   (Perseverance-era) launch period for the minimum-C3 Type-1 transfer. This
   fixes the baseline transfer (and therefore `v∞`) once, independent of the
   RAAN sweep below.
4. **Exact injection solve** (`injection.py`) — for a given burn point (a
   position + pre-burn circular velocity on the 400 km parking orbit) and
   the fixed target `v∞` vector, the *exact* single-impulse hyperbolic-
   injection solve (not the textbook tangential-burn special case): solves
   for the orbital eccentricity and orientation that reach the target
   asymptote from that exact burn point, across both geometric branches
   (short-way/long-way, analogous to Lambert's own ambiguity). Also provides
   `minimum_delta_v_for_plane`, which scans burn-point true anomaly around
   the full circle **and both parking-orbit traversal directions** (see
   validation note below) to find a given plane's own best-achievable ΔV.
5. **RAAN sweep** (`raan_sweep.py`) — calls `minimum_delta_v_for_plane` for
   both plane families, at 5° steps of ΔRAAN over the full [-180°, +180°]
   range, and caches the result.

## Validation (`validate.py` — run it, don't take this on faith)

- The universal-variable Kepler propagator (`kepler.py`) exactly returns a
  circular orbit to its start after one period, and round-trips a
  hyperbolic state forward+backward to ~1e-6 km / ~1e-9 km/s.
- The ephemeris method was cross-checked against **live JPL Horizons DE441**
  vectors: Earth to ~4 km / ~1 mm/s — this also caught and fixed a real bug
  (astropy's `HeliocentricMeanEcliptic` frame transform was silently
  introducing a ~1.3 million km error; the fix was direct ICRS-frame
  barycentric subtraction plus a manual fixed-obliquity rotation, which is
  what `frames.py` and `ephemeris.py` now do).
- Every Lambert solution is independently re-validated by propagating
  (r1, v1) forward with the Kepler propagator and confirming it reproduces
  r2.
- The equatorial↔ecliptic rotation matrix is checked to be a proper
  orthonormal rotation (orthogonal, determinant +1).
- The exact hyperbolic-injection solver reduces to the textbook closed-form
  answer in the periapsis-tangential special case (exact match to 1e-13
  relative precision).
- The plane-minimum burn (`minimum_delta_v_for_plane`) is independently
  cross-checked by propagating its solved post-burn state 90 days forward
  with the Kepler propagator and confirming the resulting asymptotic
  velocity direction matches the required `v∞` to well under 1e-2 degrees.
- The RAAN sweep's 180°-periodicity is checked explicitly across the whole
  swept range for both families, not assumed from the geometry argument alone.

**A real gap caught and fixed during development**: `minimum_delta_v_for_plane`
initially scanned only one parking-orbit traversal direction per plane
(one sign convention for the orbit's angular momentum). Flipping that sign
traces the *same* burn positions but reverses the pre-burn velocity —
a genuinely different, physically valid design choice (which way you park
in that plane), not a redundant duplicate. Checked directly: for the
`v_Earth`-containing equatorial plane, the two traversal directions gave
4.2765 km/s vs. 4.2764 km/s — only ~0.15 m/s apart *here*, but that gap was
not verified to stay small across the rest of the sweep, so the fix (both
directions are now scanned explicitly at every burn point, not assumed
symmetric) was made rather than left as an undocumented approximation.

## Baseline transfer used

Real 2020 Mars launch period (per the JPL Mars 2020/Perseverance press
kit), minimum-C3 Type-1 solution found by grid search:

- Depart **2020-07-20**, arrive **2021-01-29** (193-day transit)
- C3 = 13.09 km²/s², departure v∞ = 3.62 km/s, arrival v∞ = 2.83 km/s

This lands at the departure-window's earliest allowed date, which is
expected, not a search artifact: real interplanetary launch periods are
routinely front-loaded for minimum C3, with the window extending later only
to buy schedule margin at increasing energy cost.

## Key results

- **Equatorial family**: minimum ΔV ≈ 3.78 km/s, near ΔRAAN ≈ -10°.
- **Ecliptic family**: minimum ΔV ≈ 3.80 km/s, near ΔRAAN ≈ -5°.
- Both sit only a few percent above the unconstrained (plane ∥ v∞) floor of
  ≈3.77 km/s — consistent with `v∞` being just 14.7° from `v_Earth`, so a
  plane deliberately chosen to contain `v_Earth` already comes close to the
  best possible orientation for either family.
- The two families' minima are close but not identical, and sit at slightly
  different ΔRAAN offsets — expected, since "contains Earth's spin axis"
  and "contains the ecliptic normal" are different constraints that only
  coincide with each other at isolated points around the sweep.

(Exact values as generated: see `outputs/raan/raan_dv_<dep_epoch>.png`,
regenerated by `raan_sweep.py` — re-run it after any change rather than
trusting the numbers quoted above, which are a snapshot.)

## Chart (`charts/raan_dv.py`)

`outputs/raan/raan_dv_<dep_epoch>.png` — both families' minimum-achievable
ΔV plotted against ΔRAAN on one shared axis, each family's global minimum
marked, and a reference line at ΔRAAN=0 (the plane containing `v_Earth`
exactly). An info box on the chart reports the baseline transfer's
parameters (C3, v∞, dates) and each family's minimum ΔV and location.

## References

- Bate, Mueller, White, *Fundamentals of Astrodynamics* (Dover) — patched-conic
  departure geometry and the burn-point/plane argument this model builds on.
- Vallado, *Fundamentals of Astrodynamics and Applications*, 4th ed. — Lambert
  (universal variables), interplanetary trajectory design, Kepler's-equation
  propagation (Algorithm 8, implemented in `kepler.py`).
- Izzo, D. (2015), "Revisiting Lambert's Problem," *Celestial Mechanics and
  Dynamical Astronomy* 121:1 — the Lambert algorithm used (via `lamberthub`).
- Curtis, *Orbital Mechanics for Engineering Students* — cross-check reference
  for worked patched-conic examples.
- Sergeyevsky, Snyder, Cunniff, *Interplanetary Mission Design Handbook, Vol.
  I* (JPL 82-43) — real-mission C3/v∞ context.
- JPL Horizons System (`ssd.jpl.nasa.gov/api/horizons.api`), DE441 — primary
  ephemeris source.

## Running it

```
pip install -r requirements.txt
python3 validate.py   # re-run all correctness checks
python3 run.py         # regenerate all charts into outputs/
python3 raan_sweep.py  # (re)compute the RAAN sweep cache directly
```

Pass `--force` to `run.py` to force a recompute of the baseline transfer;
delete `cache/raan_sweep.npz` to force a fresh RAAN sweep; delete
`cache/horizons_*.json` to force fresh ephemeris fetches. All regenerate
automatically as needed.

## Known simplifications (stated, not hidden)

- **Zero-SOI-radius patched conic**: the heliocentric "patch point" position
  is taken as Earth's position exactly (the ~6,371–924,000 km geocentric
  offset is dropped), standard practice in this method and small (~0.6% of
  the SOI radius vs. the Earth-Sun distance) next to the effects studied here.
- **ICRS ≈ mean equator/equinox of J2000**: the ~tens-of-milliarcsecond frame
  bias between them is not modeled; negligible next to ephemeris-level
  uncertainty already in play.
- **Circular, 400 km parking orbit** — altitude is fixed; only plane
  orientation (RAAN, within each of the two "polar" families) is swept.
  Extending to a parking-altitude sweep would be a natural next step.
- **RAAN sweep resolution**: 5° steps, 180 burn-point/traversal-direction
  samples per plane. Sufficient to resolve the smooth minima reported above,
  but a finer grid would sharpen the exact ΔRAAN location of each minimum.
