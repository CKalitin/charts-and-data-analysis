# Mars transfer orbit model: departure ΔV vs. heliocentric injection azimuth

Patched-conic model of a polar-parking-orbit departure to Mars, studying how
**ψ (psi), the "heliocentric injection azimuth"** — the angle between the
spacecraft's velocity at the trans-Mars-injection (TMI) burn point and
Earth's own heliocentric velocity vector — drives departure ΔV, mid-course-
correction (MCC) ΔV budget, and Mars arrival/flyby geometry.

## The core idea

A polar (i=90°) parking orbit's plane always contains Earth's spin axis, so
its RAAN can always be chosen to also contain Earth's heliocentric velocity
vector, `v_Earth`. Within that plane, ψ is defined by:

```
v_hat(psi) = cos(psi) * v_Earth_hat + sin(psi) * e_t0_hat      # burn velocity direction
r_hat(psi) = v_hat(psi) x n_hat                                # burn position direction
```
(`n_hat` = plane normal, `e_t0_hat` = in-plane direction ⊥ `v_Earth`; see
`patched_conic.py` docstring for the full derivation.) ψ=0° → burn velocity
parallel to `v_Earth`; ψ=±90° → perpendicular to it. Swept over **[-90°, +90°]**
by design: the excluded [90°,270°] range is the antiparallel half, which is
never cheaper than its ψ=0-side mirror and adds nothing to the study.

The required outgoing hyperbolic excess velocity, **v∞**, comes from a
Lambert solve on the *heliocentric* Earth→Mars leg and is **independent of
ψ** — ψ only controls how expensively the Earth-centered departure burn
reaches that fixed target. Because the parking-orbit plane contains
`v_Earth` but not, in general, `v∞` itself, even the best ψ pays a real
plane-misalignment penalty over the unconstrained (plane ∥ v∞) minimum —
that gap is the headline number this model quantifies.

**A direct consequence worth stating plainly: in this idealized construction,
ψ does not change the nominal heliocentric transfer, arrival date, or
arrival v∞/flyby geometry at all** — only the departure ΔV and (see below)
the MCC sensitivity depend on it. That's not a simplification; it falls out
of the patched-conic construction exactly, and turned out to be one of the
more interesting findings.

## Pipeline

1. **Ephemeris** (`ephemeris.py`) — Earth/Mars heliocentric state vectors,
   fetched live from JPL Horizons (DE441) and cached; falls back to
   astropy's built-in analytic ephemeris if the network is unavailable.
2. **Lambert solve** (`lambert.py`) — Izzo (2015) via the published
   `lamberthub` package, done in the ecliptic frame so `prograde=True`
   correctly selects the Type-1 (<180°) transfer.
3. **Window search** (`search.py`) — grid search over the real Mars 2020
   (Perseverance-era) launch period for the minimum-C3 Type-1 transfer.
4. **Departure burn** (`patched_conic.py`) — for each ψ, the *exact* single-
   impulse hyperbolic-injection solve (not the textbook tangential-burn
   special case): given the fixed burn point and the fixed target v∞
   vector, solves for the orbital-plane orientation and eccentricity that
   reach it, across both geometric branches (short-way/long-way, analogous
   to Lambert's own ambiguity), and returns the global-minimum-ΔV solution.
5. **Mid-course correction** (`mcc.py`) — Monte Carlo over TMI execution
   error (magnitude + pointing), each sample propagated out to the
   asymptotic regime, patched to the heliocentric frame, coasted to a
   fixed MCC epoch, then re-targeted to Mars via a **fresh Lambert solve**
   (not a linearized sensitivity matrix) — the MCC ΔV is what that
   re-targeting costs.
6. **Mars arrival** (`arrival.py`) — hyperbolic flyby geometry (periapsis
   velocity, turn angle, B-plane impact parameter) for the fixed arrival v∞.

## Validation (`validate.py` — run it, don't take this on faith)

13 independent checks, all passing as of this writeup:

- The universal-variable Kepler propagator (`kepler.py`) exactly returns a
  circular orbit to its start after one period, and round-trips a
  hyperbolic state forward+backward to ~1e-9 km / ~1e-12 km/s.
- The ephemeris method was cross-checked against **live JPL Horizons DE441**
  vectors: Earth to ~4 km / ~1 mm/s, Mars to ~4 km / ~1.8 m/s — this also
  caught and fixed a real bug (astropy's `HeliocentricMeanEcliptic` frame
  transform was silently introducing a ~1.3 million km error; the fix was
  direct ICRS-frame barycentric subtraction plus a manual fixed-obliquity
  rotation, which is what `frames.py` and `ephemeris.py` now do).
- Every Lambert solution is independently re-validated by propagating
  (r1, v1) forward with the Kepler propagator and confirming it reproduces
  r2 (residual ~1e-7 km for the baseline transfer).
- The exact hyperbolic-injection solver reduces to the textbook closed-form
  answer in the periapsis-tangential special case (exact match to 1e-13
  relative precision), and every ψ's solved burn was independently
  cross-checked by propagating 90 days forward and confirming the resulting
  asymptotic velocity direction matches the required v∞ to <1e-4 degrees.

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

- **Departure ΔV(ψ)**: ranges from ~4.28 km/s (ψ=-60°, the cheapest point in
  the swept range) up to ~13.8 km/s (ψ≈+78°) — a >3x spread driven purely by
  burn-point phasing. Even at the ψ optimum, that's ~14% above the
  unconstrained (plane ∥ v∞) theoretical floor of 3.77 km/s — the
  irreducible cost of being confined to "plane contains v_Earth."
- **MCC ΔV(ψ)**: rises gently from ~43 m/s (ψ=-90°) to ~60 m/s across most
  of the range, then rises sharply above ψ≈75° to >110 m/s (mean) / >220 m/s
  (P95) as the departure geometry becomes more radial and less tangential.
- **Mars arrival**: v∞ = 2.83 km/s; for a 500 km flyby periapsis altitude,
  periapsis velocity 5.48 km/s, turn angle 70.6° — and, per the point above,
  these numbers are the same for every ψ.

Charts: `outputs/departure/`, `outputs/mcc/`, `outputs/trajectory/`.

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
- Kizner, W. (1961), "A Method of Describing Miss Distances for Lunar and
  Interplanetary Trajectories," JPL TR 32-138 — B-plane/flyby geometry.
- Sergeyevsky, Snyder, Cunniff, *Interplanetary Mission Design Handbook, Vol.
  I* (JPL 82-43) — real-mission C3/v∞/MCC-budget context.
- JPL Horizons System (`ssd.jpl.nasa.gov/api/horizons.api`), DE441 — primary
  ephemeris source.

## Running it

```
pip install -r requirements.txt
python3 validate.py   # re-run all correctness checks
python3 run.py         # regenerate all charts into outputs/
python3 derived.py     # (re)compute the sweep results cache directly
```

Delete `cache/derived_results.npz` (or pass `--force` to `run.py`) to force
a recompute; delete `cache/horizons_*.json` to force fresh ephemeris fetches.
Both regenerate automatically as needed.

## Known simplifications (stated, not hidden)

- **Zero-SOI-radius patched conic**: the heliocentric "patch point" position
  is taken as Earth's position exactly (the ~6,371-9,24,000 km geocentric
  offset is dropped), standard practice in this method and small (~0.6% of
  the SOI radius vs. the Earth-Sun distance) next to the effects studied here.
- **ICRS ≈ mean equator/equinox of J2000**: the ~tens-of-milliarcsecond frame
  bias between them is not modeled; negligible next to ephemeris-level
  uncertainty already in play.
- **Circular, 400 km, polar parking orbit** — altitude and inclination are
  fixed; only ψ (burn phasing) is swept. Extending to a parking-altitude
  sweep would be a natural next step.
- **MCC model** re-targets to Mars' *position* at the original arrival date
  via a fresh Lambert solve, rather than a full B-plane target-plane
  formalism — simpler to implement correctly, and still a legitimate,
  standard simplification for a ΔV-budget estimate.
