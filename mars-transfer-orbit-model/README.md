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

### Why the burn is never actually tangent to the parking orbit

It's tempting to assume ψ=0° (`v_Earth` in-plane) is the free lunch — but
for the baseline transfer the burn is off-tangent at *every* ψ, including
ψ=0°, and ψ=0° isn't even close to the minimum (it costs 7.48 km/s vs. the
4.28 km/s optimum at ψ=-60°). The reason is a distinction that's easy to
miss: **`n_hat` (the orbital-plane normal) is fixed by `v_Earth` alone and
does not depend on ψ at all** — confirmed numerically, it's identical
across the whole sweep. ψ only moves the burn point *within* that one fixed
plane; it never re-orients the plane itself.

A burn is tangent (the cheap, scalar-ΔV case) only when the required
outgoing v∞ lies **in that same plane**. But v∞ is not `v_Earth` — it's
`v_transfer,depart − v_Earth` from the Lambert solve, and for the baseline
transfer it sits **14.7° away from `v_Earth`'s own direction**, with
**7.9° of that lying out of the very plane `v_Earth` defines**. Since the
plane's orientation never changes with ψ, that 7.9° gap can't be closed by
picking a different ψ — it's a fixed misalignment tax paid by every burn in
the family. What ψ actually controls is only how much *extra* the burn
must fight that fixed 7.9° tilt: at ψ=-60° the required burn deviates only
12.4° from the local tangential direction; at ψ=0° it's 40.4°; at ψ=+90° it's
85.8° (nearly radial). ΔV tracks that deviation angle almost exactly.

So the original intuition — "put `v_Earth` in the plane, that's obviously
the cheap case" — implicitly assumes v∞ points the same way `v_Earth`
does. It doesn't, and the 14.7° gap decomposes cleanly into two effects,
verified numerically (not just asserted):

**1. This is not a Hohmann transfer — the transfer angle is 142.8°, not
180°.** A textbook Hohmann transfer (purely tangential departure, exactly
parallel to the departure planet's velocity) requires *both* a coplanar,
circular target orbit *and* a transfer angle of exactly 180°. Ours is
neither, by construction: the search in `search.py` finds the minimum-C3
transfer that actually rendezvouses with Mars's real position on a real
arrival date within the real 2020 launch window — a fixed-time boundary
value problem (Lambert's problem), not a free choice of target geometry.
Proof this alone matters, independent of inclination: artificially
flattening Mars onto the ecliptic (same heliocentric distance and
longitude, zero latitude) but keeping the same 142.8° transfer angle still
gives a **3.0° misalignment** between v∞ and `v_Earth` — a non-tangential
departure is inherent to any Lambert transfer whose angle isn't 180°, even
in the fully idealized 2D coplanar case.

**2. Mars's real orbital inclination supplies the rest, and it's a strongly
amplified effect.** Mars sits at only **0.95° ecliptic latitude** at the
arrival epoch (out of its ~1.85° max inclination — it isn't at its extreme
point on this date). Swept from 0% to 100% of that true latitude while
re-solving Lambert each time, the v∞/`v_Earth` angle scales smoothly and
monotonically from 3.0° to 14.7° (0.24° latitude → 4.8°; 0.47° → 7.9°; 0.71°
→ 11.3°; 0.95° → 14.7°) — checked specifically to rule out this being a
bug rather than a real, if strong, sensitivity of the Lambert-solved
velocity *direction* to small out-of-plane target perturbations (this
sensitivity is a known feature of Lambert geometry: r1×r2, which defines
the transfer plane, shrinks toward zero as the transfer angle approaches
180°, so a transfer angle already most of the way there — sin(142.8°) =
0.61 — makes the transfer plane genuinely more sensitive to small
out-of-plane target displacements than a 90° transfer would be).

Putting `v_Earth` in the parking-orbit plane guarantees only that *one* of
the two relevant vectors is in-plane — and, per the above, it's essentially
never the one a tangential burn actually needs. (Real missions describe
the resulting v∞ tilt as the "declination of the launch asymptote.")

### A note on the "top-down" geometry charts

If you looked at `outputs/geometry/07`–`10_departure_topdown_*.png` and
expected a polar orbit to appear edge-on (a line) — that's the right
instinct for looking straight down **Earth's spin axis** (the everyday
"map of Earth from the north pole" view), and in that view a polar orbit
genuinely would be a line, since Earth's axis lies *in* the polar orbit's
plane by definition. But that's deliberately not what these charts show.
They look face-on to the **orbital plane itself** — down its normal vector
`n_hat = z_hat × v_Earth_hat`, which is perpendicular to Earth's spin axis,
not aligned with it (confirmed numerically: `n_hat` always has zero
z-component). That vantage point is effectively from Earth's equator,
looking sideways at the polar orbit's own great circle face-on — which is
exactly why it renders as a circle. This view was chosen deliberately,
because it's the only one that shows `v_Earth`, v∞, the orbit, and the
burn geometry all without collapsing any of them: a literal down-the-axis
view would flatten the polar orbit to a line (as expected) but would also
badly foreshorten `v_Earth` and v∞, which both sit close to the ecliptic,
far from Earth's spin axis.

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
  **Mean vs. P95**: at each ψ, `mcc.mcc_budget` runs a Monte Carlo (2000
  draws by default) of TMI execution error, each draw producing one MCC
  ΔV. "Mean" is the average of those draws — the typical correction cost.
  "P95" is the 95th percentile — the cost exceeded only 5% of the time,
  i.e. the number a mission would actually hold propellant margin against
  (you don't get to re-fly a shortfall, so real budgets target P95/P99, not
  the mean). The mean-to-P95 gap roughly doubles near ψ=90°, meaning that
  region isn't just worse on average — its tail is fatter, a sign of a more
  nonlinear/sensitive targeting geometry there.
- **Mars arrival**: v∞ = 2.83 km/s; for a 500 km flyby periapsis altitude,
  periapsis velocity 5.48 km/s, turn angle 70.6° — and, per the point above,
  these numbers are the same for every ψ.

## Geometry illustrations (`charts/departure_geometry_3d.py`, `charts/departure_geometry_sweep.py`, `charts/mcc_trajectory.py`)

Beyond the quantitative sweeps, `outputs/geometry/` makes the ψ definition
and the departure burn concrete:

- `01_earth_polar_orbit_plain.png` — Earth, `v_Earth`, and the polar
  parking orbit, viewed close-in (~1.8 Earth radii half-extent — tight
  enough that Earth and the orbit fill the frame; view angle is chosen
  automatically to look mostly down the orbit-plane normal so the orbit
  reads as a clear ellipse rather than an edge-on line).
- `02_earth_polar_orbit_plane_highlighted.png` — same, with the orbital
  plane itself drawn as a translucent patch, making it visually obvious
  that `v_Earth` lies flat within it (by construction — see the ψ
  derivation above).
- `03`–`06_departure_3d_psi_*.png` — the comparison set spanning the "why
  isn't the burn tangent" story (see below): the original circular parking
  orbit plus the post-burn hyperbola, burn point, ΔV vector, `v_Earth`,
  **and `v_infinity`** (added so the angle between the two — the actual
  cause of the off-tangent burn — is visible directly on the chart), at
  ψ=-60° (cheapest), ψ=-45° (15° off it), ψ=0° (the naive "v_Earth
  in-plane" expectation), and ψ=+90° (perpendicular extreme). ΔV visibly
  climbs (4.28 → 4.56 → 7.48 → 13.30 km/s) as the burn direction swings
  further from tangential.
- `07`–`10_departure_topdown_psi_*.png` — the same four cases as a true
  **orthographic top-down projection onto the orbital plane** (not a
  perspective 3D shot): screen-x = `-v_Earth_hat` (so `v_Earth` always
  points left, as requested) and screen-y = the in-plane direction
  perpendicular to it. The parking orbit, `v_Earth`, and the burn point
  project losslessly (they're exactly in this plane); `v_infinity`, the
  post-burn hyperbola, and the ΔV vector generally are NOT exactly in this
  plane (that's the whole finding), so their projected lengths/positions
  are a real foreshortening — each is labeled with its true out-of-plane
  angle rather than silently distorting it.
- `11_departure_sweep_overlay.png` — a single-image sanity check: all 13
  psi values from -90° to +90° (15° steps) overlaid on one face-on-to-plane
  view, color-coded by ψ, each with its burn point and the first ~40° of
  its hyperbola. `v_Earth` and `v_infinity` are drawn once (they don't
  depend on ψ); the cheapest case is starred. The point of this chart is
  what a curve like `departure_dv.py`'s can't show directly: the burn point
  sweeps smoothly around the fixed circle and the hyperbolas fan out
  continuously as ψ varies, with no jumps or discontinuities — a visual
  check that the exact injection-burn solver (`patched_conic.py`) behaves
  sanely across the whole swept range, not just at the handful of ψ values
  spot-checked individually elsewhere.
- `outputs/mcc/mcc_trajectory_psi_-60.png` — answers "is that where the MCC
  burns are?": plots the full heliocentric Earth→Mars transfer with the MCC
  burn point marked at TMI+10 days. It's near Earth, not out near Mars —
  only ~5% of the way through the 193-day transit. Because the resulting
  position miss (tens of thousands of km) is invisible against the ~150
  million km heliocentric scale, a zoomed inset shows the nominal vs.
  uncorrected point for one concrete, deterministic 1-sigma execution error
  (not a random Monte Carlo draw, so the chart is reproducible), together
  with the miss distance and the resulting MCC ΔV for that specific case.
  The same nominal MCC point is also marked on the main
  `outputs/trajectory/transfer_overview_*.png` chart.

Charts: `outputs/departure/`, `outputs/mcc/`, `outputs/trajectory/`, `outputs/geometry/`.

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
