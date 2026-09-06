# Longitude / FOV capacity modeling — handoff for review

Written 2026-09-05, at the user's explicit request, before continuing any other
work on this project. Purpose: hand this exact concern — in the user's own
words — plus what's actually in the code today, to a fresh Claude session (or
a different reviewer) for a deeper look, without losing the framing in
paraphrase.

## The user's exact words (verbatim, two messages, same conversation)

> On capacity allocation: Is it that we only take latitude into account? In
> reality it's not that satellites are looking at an entire latitude band,
> they're instead looking on a 25 degree FOV below them and these are their
> servable customers. Any model has to be based on this. The latitude band
> per country method fails because if a country is wide entirely different
> satellites are serving the eastern vs western sides. Is this taken into
> account?

> If it's time averaged satellite density above a point, then this models it.
> However this doesn't seem to be the case, because I don't see any way that
> capacity is taken into account by longitude. It's not like satellites in
> the same latitude band on opposite sides of the Earth serve the same users.
> Look further into how this should be modeled. In fact, before you continue
> with anything else, do a quick md file write up sharing my EXACT WORDS and
> perspective to another Claude, and sharing some of your findings.

## What the code actually does today (confirmed by re-reading it, not from memory)

Every satellite-density function in this project marginalizes over longitude
completely — there is no longitude variable anywhere in the capacity/demand
pipeline:

- `orbital_geometry.latitude_density()` (`orbital_geometry.py:137`) samples a
  single satellite's argument-of-latitude `u` uniformly over one orbit and
  histograms `lat = asin(sin(i) * sin(u))` into 1° bins. This is a pure
  latitude marginal — longitude (`lam = atan2(cos(i)*sin(u), cos(u))`, computed
  two functions away in `ground_track()`) is never touched by this path.
- `expected_sats_by_latitude()` (`orbital_geometry.py:154`) turns that one
  satellite's time-fraction-per-latitude into "expected satellites overhead a
  latitude band at any instant," by an explicit **ergodic-equivalence
  argument**, stated in its own docstring: "one satellite sampled over time" is
  treated as equivalent to "many evenly-phased satellites in a plane sampled at
  one instant." That's a real, defensible property of a Walker-Delta-style
  constellation *if* planes are evenly spread in RAAN (right ascension of
  ascending node) — which real Starlink shells approximately are — but the
  code never actually models RAAN or checks that assumption; it's assumed, not
  computed.
- `expected_sats_reaching_latitude()` (`orbital_geometry.py:226`) — the
  "25° FOV" function the user is asking about — extends this by convolving the
  overhead-only histogram with a boxcar window of half-width
  `ground_range_angular_radius_deg()` (the real 25°-elevation coverage-circle
  radius, ~927–968 km for Gen1's real shells, already correctly derived and
  cross-validated against two independent published figures — see
  `ASSUMPTIONS.md` #11). **But it only extends the window north-south along the
  latitude axis.** Its own docstring says so directly: "Ignores the east-west
  extent of the coverage circle entirely (a 1D latitude-marginal
  simplification...)." So even the function that's explicitly about FOV/
  coverage radius doesn't add a longitude dimension — it makes the *latitude*
  window wider, nothing else.
- `serviceable_customers_model.py`'s docstring already states the project's own
  standing rule for latitude: "excess satellite capacity at a sparsely-
  populated latitude (e.g. 80°) cannot serve demand at a different, densely-
  populated latitude (e.g. 30°), so the min() must be taken band-by-band before
  summing, not on the two global totals." **This same logic is never applied
  across longitude at a fixed latitude.** `country_service_model.
  country_servable_fraction()` reads a single global per-latitude-band
  served-fraction (built from *every country's population at that latitude,
  summed together*) and applies that one ratio to every country sitting at
  that latitude, regardless of longitude.

## Is "time-averaged density above a point" a defense? Partially — and here's exactly where it breaks

The user's own conditional in the second message is the right test: *if* this
were modeling time-averaged satellite density directly above one fixed ground
point, it would be fine, because — given enough orbital planes spread evenly
in RAAN and Earth's rotation smearing each orbit's ground track across all
longitudes over many passes — the long-run time-average satellite count above
*any* fixed point on a given latitude circle genuinely does converge to the
same number as the ring's spatial average. That part of the ergodic argument
is real orbital mechanics, not hand-waving.

**But that's not actually what the model needs, and it's not what it's being
used for.** The model isn't asking "what's the average supply above one
point" in isolation — it's asking "can the aggregate supply around this whole
latitude ring meet the aggregate demand around this whole ring," and then
handing every country on that ring the *same* answer. That step is where the
physics breaks:

A satellite at 550 km altitude with a 25° minimum elevation angle has a hard
ground-coverage radius of **~940 km** (`ground_range_km()`, already computed in
this codebase). It categorically cannot serve a customer on the opposite side
of the planet at the same latitude. So when the pooled model computes "global
supply at 26°N vs. global demand at 26°N" and finds supply falls short, it is
implicitly assuming that the supply shortfall in South Asia (dense demand)
could in principle be filled by *idle* satellite capacity passing over, say,
the mid-Pacific or the Sahara at the same latitude (sparse demand) — capacity
that is real in the ring-wide sum but is never physically deliverable to South
Asia, because it's 900+ km outside any Indian satellite's reach at that
moment. **The current model already applies this "capacity can't teleport"
constraint across latitude bands (by the project's own stated design) but
silently violates the identical constraint across longitude within a single
latitude band.** That inconsistency, not "longitude is ignored" per se, is the
sharpest way to state the bug.

Net effect, best guess without having built the fix: **dense, unevenly-
distributed-by-longitude countries (India, China, Nigeria, Indonesia — the
same countries already flagged elsewhere in this project as capacity-bound)
are probably getting an overstated servable-fraction**, because they're
implicitly allowed to draw on "spare ring capacity" sitting over sparsely
populated longitudes at their own latitude that a real satellite could never
reach them from. Sparse countries are probably close to correct already, since
they're rarely the ones whose local demand exceeds *local* supply in the first
place.

## What a real fix needs

A genuine 2D treatment needs the actual **(latitude, longitude)** density of
satellites, not just latitude. The building blocks already exist in this
project and don't need to be invented from scratch:

- `orbital_geometry.ground_track()` (`orbital_geometry.py:99`) already computes
  full `(lon, lat)` for one satellite over time, including Earth's rotation —
  it's just never fed into a density/histogram function, only used for the
  single-satellite visualization in `charts/coverage_map.py`.
- The real per-shell plane/altitude/inclination data
  (`data/starlink_shells.csv`, loaded via
  `orbital_geometry.load_shells_with_full_geometry()`) has real orbital-plane
  counts per shell — the missing piece is a RAAN value per plane (not
  currently in the CSV; Starlink's planes are approximately evenly spread
  across 360° of RAAN per shell, which is a reasonable assumption to seed with,
  same category of assumption the latitude-only model already leans on for
  "evenly phased in argument of latitude").
- `ground_range_angular_radius_deg()` already gives the correct coverage-circle
  radius to use as a 2D (not just N-S) footprint once real `(lat, lon)`
  satellite positions exist.
- `population_density_grid.py` already has a working global 0.1°×0.1°
  lat/lon population grid (`load_or_build_grid()`) and the block-averaging
  infrastructure to go with it — the natural target resolution for a matching
  2D satellite-density grid, so the two could be compared cell-by-cell instead
  of ring-by-ring.

Shape of the fix, at a glance: for each shell, generate many (plane × RAAN,
satellite × mean-anomaly-in-plane) combinations, propagate each to `(lat, lon)`
over a long-enough time window (to average out the ~95 min orbit against the
24 h day, same reasoning already used for the existing multi-orbit ground-track
charts), histogram into the same 0.1° grid `population_density_grid.py` uses,
then convolve each cell with its shell's real ground-coverage circle (a true
2D disk this time, not a 1D boxcar) to get expected simultaneous satellite
coverage per grid cell. Country-level and per-latitude-band aggregates would
then be *readouts* of that grid, the same way `country_service_model.py`
already reads out per-country numbers from a shared latitude array — same
architecture, one more dimension.

This is a substantially bigger lift than anything the "servable fraction"
model has needed so far (a real 2D Monte Carlo or analytic satellite-position
model, plus a RAAN assumption not currently in any data file), which is why
the user was asked, and separately, whether to fold it into the in-flight TAM
pricing rewrite or scope it as its own task.

## Status / what's not yet decided

This document does not propose a specific implementation — it's the write-up
the user asked for, to be reviewed (by another Claude session or a human)
before deciding scope and approach. Open questions for whoever picks this up:

1. Is a full 2D Monte Carlo satellite-position model the right level of
   fidelity, or is there a cheaper closed-form approximation (e.g., treating
   longitude coverage as "uniform except within one coverage-radius of a
   country's own longitude span," rather than full orbital propagation)?
2. Where should RAAN-per-plane data come from — assumed evenly spread (an
   explicit, flagged assumption, consistent with this project's existing
   practice) or sourced from real TLE/Celestrak data for actual deployed
   shells?
3. Does this replace `serviceable_customers_model.py`'s latitude-only
   functions outright, or sit alongside them as a second, more granular model
   (the same "don't replace, add a variant" pattern already used elsewhere in
   this project for the fixed-vs-per-satellite density cap models)?

---

# RESOLVED (2026-09-05) — `tile_capacity_model.py`

The concern above is correct in full, and is now fixed by a new 2D model. This
section records what was actually measured and built; the analysis above is left
intact as the original framing.

## The bug, quantified

Two separate errors, both confirmed numerically rather than argued:

1. **`expected_sats_reaching_latitude()` overcounts satellites in view by ~19x.**
   It convolves the latitude histogram with a boxcar of half-width R, which counts
   every satellite whose LATITUDE is within R at ANY longitude — the whole ring.
   The correct count is the satellites inside the DISK of radius R. At N=10,900:
   19.1x too high globally, 27.8x at the equator (where the ring is longest relative
   to the disk), 4.3x at 80° (where the ring shrinks toward the pole and the two
   converge). The correct disk figure at the equator is ~45 satellites in view,
   which cross-checks against the independent estimate `N x disk_area / earth_area`.

2. **Capacity teleportation along a latitude ring**, exactly as described above.

Net effect on the headline model output — old latitude-pooled vs. new 2D:

| N satellites | old (1D) | new (2D) | overstatement |
|---|---|---|---|
| 4,408 (Gen1) | 660.1M | 444.0M | 1.49x |
| 10,900 (~today) | 1,530.6M | 993.9M | 1.54x |
| 33,900 (Gen2) | 3,828.2M | 2,621.6M | 1.46x |
| 100,000 | 7,413.7M | 5,547.3M | 1.34x |
| 1,000,000 | 8,887.1M | 8,850.1M | 1.00x |

The overstatement is ~1.5x, not ~19x, because the aggregate per-satellite capacity
constraint (pooled per ring — a milder error) usually bound before the density cap
did. It converges to 1.00x at saturation, where both models are simply
population-bound.

## Answers to the three open questions

1. **Fidelity.** Neither a full Monte Carlo nor the cheap approximation. The
   sub-satellite-point density field is analytically longitude-uniform under the
   RAAN assumption, so no orbital propagation is needed to place satellites — only
   to spread each one's *reach*. And because angular distance between two tiles
   depends only on (lat_i, lat_j, Δlon), the disk-coverage operator is block-
   circulant in longitude and collapses to one small matrix multiply per longitude
   frequency: ~15 ms for the full 180x360 grid, versus minutes for an explicit
   ~20M-edge sparse matrix. The full 2D treatment turned out to be cheaper than the
   approximation it was supposed to justify.
2. **RAAN.** Assumed evenly spread, flagged as ASSUMPTIONS.md #16, with a note that
   real TLEs would replace it if longitude clumping ever matters.
3. **Replace or sit alongside.** Sits alongside for now.
   `serviceable_customers_model.py` and the market models downstream are untouched,
   because they were being revised in parallel.
   `orbital_geometry.expected_sats_reaching_latitude()` still returns exactly what it
   always did, but now carries a docstring stating the 19x overcount and pointing at
   the replacement. It should be retired once the market layer is migrated.

## What the new model does

Ground and satellite positions share one 1°x1° tile grid. Satellites carry ONE
finite customer budget shared across everything inside their coverage disk, so
neighbouring tiles — and neighbouring countries — genuinely compete for the same
satellite. That makes it a bipartite transportation problem, solved by damped
proportional water-filling.

Verification, in the order it was done:
- The disk operator reproduces the exact spherical-cap area to within 0.4% at every
  latitude, and is exactly self-adjoint.
- The allocator was checked against an exact max-flow (Dinic) on the same graph at
  two coarse tile sizes: it lands at **0.996-0.999 of the optimum**, never above it.
- A flow-conservation audit (served <= capacity consumed) runs on every solve.

Three real bugs were caught by those checks rather than by inspection:
- FFT round-off left ~1e-16 "reachable capacity" where the true value is zero, so
  `unmet / reachable` exploded and tiles with NO coverage were served for free —
  inflating served customers ~50% above capacity consumed. Fixed with a relative
  noise floor in `DiskOperator.apply()`; the conservation audit exists so this class
  cannot return silently.
- Log-spaced density-bin CENTRES made capped demand exceed 100% of world population.
  Fixed by storing population per bin alongside area.
- The reweighting at its original undamped step overshot and oscillated, rendering
  as concentric rings of alternating utilization around every population centre,
  with satellites directly overhead less used than ones a coverage radius away.
  Damping to eta=0.25 gives a higher total AND a monotone, coherent map.
