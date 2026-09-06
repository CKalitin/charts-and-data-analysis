# Tile capacity model — full specification

How `tile_capacity_model.py` turns real orbital geometry, real gridded population and
published per-satellite capacity figures into "how many people can this constellation
actually serve, and where." Written to be readable start to end without the code open.

Companions: `ASSUMPTIONS.md` (every unconfirmed number, with impact-if-wrong),
`CLAUDE.md` (phase-by-phase project narrative), `LONGITUDE_FOV_CAPACITY_REVIEW.md`
(the bug this model was built to fix).

---

## 0. What the model answers, and what it does not

**Answers.** For a constellation of N satellites: how many simultaneous connections
can be sold, how many people that reaches, which ground tiles get served, and how
busy the satellites over each tile are.

**Does not answer.** Price, revenue, willingness to pay, competition, or market
share. Those live in the market layer (`tam_model.py`), which consumes this model's
served-capacity output. This model is purely physical: geometry, capacity, and who
can reach whom.

**Unit of account: CONNECTIONS** (subscriptions — one dish, one household), because
that is what satellite capacity is natively denominated in. People are converted in
and out at the boundaries. See §4.

---

## 1. Pipeline at a glance

```
data/starlink_shells.csv ──► orbital_geometry ──► satellites per tile      (§2)
                                     │
FCC Order 21-48 (25° elev) ──► coverage disk radius R ──► DiskOperator     (§3)
                                     │
WorldPop 1 km rasters ──► population_density_grid ──► people per tile      (§4)
data/household_size_by_country.csv ──► household_grid ──► people/connection
                                     │
                             demand in connections
                                     │
data/satellite_capacity.csv ──► capacity_density_model ──► two ceilings    (§5)
                                     │
                          transportation problem ──► allocate()            (§6)
                                     │
                    served / utilization / served-fraction per tile        (§7)
```

Every stage is a pure function of its inputs; nothing is stateful and nothing is
cached except the WorldPop mosaic and the disk kernels.

---

## 2. Supply: where the satellites are

### 2.1 Shells

`data/starlink_shells.csv`, Gen1's five sub-shells with full plane geometry —
550 km/53.0°, 540 km/53.2°, 570 km/70.0°, and 560 km/97.6° split into two plane
groups. 4,408 satellites total, which independently matches the widely cited FCC
Phase-1 authorisation figure.

For any N, `scale_shells_to_total()` scales every shell's count proportionally,
preserving each shell's real altitude, inclination, and share of the fleet.
Fractional satellites are the expected-value treatment used throughout this project.

### 2.2 Latitude distribution

A circular orbit of inclination `i` has sub-satellite latitude

```
lat(u) = arcsin( sin(i) · sin(u) ),      u = argument of latitude, 0..2π
```

Satellites move at constant rate in `u` but not in latitude, so they linger near the
turning points `±i` — the same effect as a pendulum at the top of its swing.
`orbital_geometry.latitude_density()` samples `u` densely and histograms the result
into 1° bins rather than using the closed form, which has an integrable singularity
at the turning points. Sanity check: computed orbital periods come out at ~95 min,
matching real Starlink.

This is exactly zero outside `|lat| ≤ i` by construction, since
`|sin(i)·sin(u)| ≤ sin(i)` always — so no coverage-cutoff mask is needed anywhere,
and adding one was previously a real bug.

### 2.3 Longitude distribution

**Uniform.** Satellites per tile:

```
n_s(φ, λ) = N_s · f_s(φ) / n_lon
```

Justification: real Starlink shells spread their orbital planes approximately evenly
in RAAN, and Earth's rotation smears each ground track across all longitudes over
successive orbits, so the time-averaged satellite density above a latitude circle is
genuinely longitude-independent. Assumed from the shell design, not computed from
TLEs — **ASSUMPTIONS.md #16**.

Satellites are grouped by distinct altitude (four groups for Gen1: 540/550/560/570
km), because reach depends on altitude and must not be averaged across shells.

---

## 3. Reach: the coverage disk

### 3.1 Geometry

A user terminal needs the satellite at least `ε = 25°` above its **local horizon**.
This is the elevation angle measured **at the dish**, not a satellite property, and
not a "25° field of view" — the dish's usable cone is 65° half-angle from vertical.
`ε = 25°` is the FCC-authorised Starlink Gen1 minimum, confirmed verbatim in FCC
Order 21-48 footnote 3 (**ASSUMPTIONS.md #11**).

The satellite's matching off-nadir angle, from the law of sines on the
Earth-centre / satellite / ground-station triangle:

```
η(h) = arcsin( R_e · cos(ε) / (R_e + h) )
```

and the Earth-central angular radius of the servable ground cap:

```
R(h) = 90° − ε − η(h)
```

| altitude | η (off-nadir) | R (Earth-central) | ground radius | share of Earth |
|---|---|---|---|---|
| 345 km (V3 planned) | 59.3° | 5.71° | 635 km | 0.25% |
| 540 km | 56.7° | 8.33° | 927 km | 0.53% |
| 550 km (Gen1 main) | 56.6° | 8.45° | 941 km | 0.55% |
| 570 km | 56.3° | 8.70° | 968 km | 0.58% |

Cross-validated against two independently published figures for the 550 km shell:
25° → 941 km computed vs "~900 km" cited; 40° → 578 km vs "~580 km" cited.

`results/coverage/coverage_geometry.png` (`charts/coverage_geometry_diagram.py`)
draws this triangle true to scale, curvature included, with all three angles, the
altitude and the ground spot radius labelled. The diagram measures its own drawn
angles and refuses to render if they disagree with the labels or fail to sum to 180 —
a diagram whose labels are computed separately from its geometry can otherwise
disagree with itself silently.

**The relation is reciprocal**: a satellite can serve a ground point exactly when
that point can see the satellite above 25°. So the same disk is read in both
directions, and one operator serves both.

### 3.2 The disk operator

`DiskOperator.apply(X)` computes, for every tile, the sum of `X` over all tiles
within `R`:

```
out[i] = Σ_j  w_ij · X[j],     w_ij > 0 iff angular distance(i, j) ≤ R
```

Angular distance on the sphere:

```
cos d = sin φ_i · sin φ_j + cos φ_i · cos φ_j · cos(Δλ)
```

which depends only on `(φ_i, φ_j, Δλ)` — **never on absolute longitude**. So for
each pair of latitude rows the admissible longitudes form a contiguous interval:

```
cos(Δλ_max) = ( cos R − sin φ_i · sin φ_j ) / ( cos φ_i · cos φ_j )
```

clamped to "no longitude works" above 1 and "the whole circle" below −1.

Tiles are weighted by the fraction of their longitude span inside the disk,

```
w(k) = clip( Δλ_max/Δλ_tile − |k| + 0.5 , 0, 1 )
```

rather than a rounded 0/1 boxcar. The adjacency matrix is therefore **block-circulant
in longitude**, and the whole operator collapses to one small matrix multiply per
longitude frequency:

```
out = irfft_λ( Σ_j  K̂[i, j, f] · rfft_λ(X)[j, f] )
```

**~15 ms for the full 180×360 grid**, versus minutes for an explicit ~20M-edge sparse
matrix. This is what made a full 2D treatment cheaper than the 1D approximation it
was supposed to justify.

Properties, both verified:
- reproduces the exact spherical-cap area `π(R_e·R)²` to within **0.4%** at every
  latitude;
- **exactly self-adjoint** (adjacency is symmetric), so the same operator gathers
  supply toward a ground tile and gathers demand toward a satellite tile.

`DiskOperator(fractional=False)` gives a genuine 0/1 graph, used only so the exact
max-flow reference in §8 runs on an identical problem.

**Numerical note.** `apply()` clips outputs below `1e-10` of their own peak to zero.
The rfft/irfft round trip leaves ~1e-16 where the true sum is exactly zero, and §6
divides unmet demand by reachable capacity — a 1e-16 "reachable capacity" becomes a
~1e16 request ratio and hands free service to tiles with no coverage at all. That
inflated served customers ~50% above capacity consumed before it was caught.

---

## 4. Demand: people, then connections

### 4.1 Population per tile

WorldPop 1 km per-country density rasters (215 of 217 countries; Channel Islands and
Kosovo are absent from WorldPop's own list) are mosaicked by
`population_density_grid.py` onto a global 0.1° grid — exact block-averaging, since
WorldPop's 1/120° pixel divides evenly into 0.1°. That grid is then aggregated into
the model's 1° tiles.

**Sub-tile density is retained, not averaged away.** Each tile stores paired
(density-bin → area) and (density-bin → population) histograms over 59 log-spaced
bins from 0.01 to ~200,000 people/km². This matters because the areal density
ceiling of §5.2 bites inside dense cities, which a tile-mean density would erase.

Storing population per bin rather than reconstructing it from a bin centre is not
cosmetic: with bins ~1.33× wide, geometric centres made capped demand exceed 100% of
world population.

Total: **8.85 B people**. (This mosaic integrates ~10-12% above WorldPop's own 2020
total because coastal cells average over valid land pixels but multiply by full cell
area — fine for relative geography, and not used as an authoritative population
count.)

### 4.2 People per connection

Satellite capacity counts **subscribers** — one dish, one household. Population
counts **people**. Comparing them directly asserts one person per dish; every
capacity model in this project did that before 2026-09-05, which *understated* how
many people a satellite reaches by roughly the household size.

`household_grid.py` fixes it. `data/household_size_by_country.csv` (151 of 217 from a
national census or survey, 66 on a regional-median fallback — **ASSUMPTIONS.md #13**)
is attributed to tiles by probing each tile at 4×4 interior points against Natural
Earth 110m country polygons and averaging the household size over whichever probes
land inside a country. Probing tile centres alone matched only 87.8% of world
population — a 1° tile over a coastal city often has its centre offshore — while
subsampling reaches **97.6%**. Unmatched tiles take the population-weighted global
mean.

```
demand_connections(tile) = population(tile) / household_size(tile)
```

**8.85 B people → 2.50 B connections**, population-weighted mean **3.86 people per
connection**.

Known limitation: one household size per whole country. Rural households are
generally larger than urban ones, and Starlink's addressable demand skews rural, so
the true rural figure is probably above the national average — making this
conversion mildly conservative in exactly the segment that matters most.

---

## 5. The two capacity ceilings

Both come from `capacity_density_model.py`, reproducing the X-Lab/Penn State
"Starlink Capacity Analysis v0.2" derivation as parameterised functions. Default
scenario is **V3** (`V3_SCENARIO`): 1,024 Gbps downlink / 200 Gbps uplink per
satellite (real, sourced), 20:1 contention, US 100/20 Mbps threshold.

Subscribers per beam, whichever direction binds:

```
n_beam = min( G_down/ s_down , G_up / s_up ) · contention
```

### 5.1 Aggregate per-satellite capacity

```
C = n_beam · beams_per_satellite     →  200,000 connections per V3 satellite
```

This is **exact for V3 regardless of its undisclosed beam count**: beams and
per-beam Gbps only ever appear multiplied, and their product is pinned to V3's real
1,024 Gbps total.

### 5.2 Areal density ceiling

```
c₀ = n_beam / beam_footprint_area     →  195 connections/km² per satellite in view
```

This one **does** depend on V3's undisclosed beam count and beamwidth, which are
placeholdered from v2 Mini — a real, flagged uncertainty (**ASSUMPTIONS.md #12**).

The ceiling scales with how many satellites can actually reach a tile:

```
c(tile) = c₀ · Σ_shells DiskOperator_s( n_s )[tile]
```

**This is where the ~19× bug lived.** The superseded
`orbital_geometry.expected_sats_reaching_latitude()` convolved the latitude
histogram with a boxcar, counting every satellite whose *latitude* was within R at
*any* longitude — the whole 40,000 km ring instead of the disk. Measured at
N = 10,900: 19.1× too high globally, 27.8× at the equator, 4.3× at 80° where ring and
disk converge. The correct equatorial figure is ~45 satellites in view, which
cross-checks against `N · disk_area / earth_area`.

### 5.3 Offered demand

Applied sub-tile against the stored histograms, in connections:

```
D_i = (1/h_i) · Σ_bins  min( P_ib , h_i · c_i · A_ib )
```

where `P_ib`/`A_ib` are population and area in density bin `b` of tile `i`, and `h_i`
is people per connection. Capping in people-space and dividing back is algebraically
identical to capping in connection space, and reuses the one histogram.

---

## 6. Allocation

### 6.1 The problem

Each satellite carries **one** finite connection budget shared across everything
inside its disk, so neighbouring tiles — and neighbouring countries — genuinely
compete for it. That makes this a bipartite transportation problem between satellite
tiles `j` (supply `K_j = C · n_j`) and ground tiles `i` (demand `D_i`), with disk
adjacency `A_ij`:

```
maximise   Σ_ij x_ij
subject to Σ_j x_ij ≤ D_i     (nobody is served twice)
           Σ_i x_ij ≤ K_j     (a satellite cannot exceed its budget)
           x_ij = 0 unless A_ij
```

At 1° tiles that is ~65,000 nodes a side and ~20M edges — far too large to build
explicitly, which is why everything below is expressed as disk convolutions.

**Why this replaces a per-band `min()`.** The old model compared supply and demand
pooled over a whole latitude *ring*, which lets idle capacity over the mid-Pacific
serve South Asia at the same latitude. It already enforced "capacity can't teleport"
across latitudes — its own stated design rule — while silently violating the
identical constraint along one.

### 6.2 Proportional water-filling

One pass, repeated until no tile with unmet demand can still reach free capacity.
Each round:

1. every ground tile with unmet demand requests from the satellites it can see,
   splitting its request in proportion to (remaining free capacity × weight);
2. every oversubscribed satellite rations its remaining capacity proportionally
   among the requests received.

Writing `r_i = unmet_i / Σ_j A_ij·free_j·w_j`, the algebra is exact — not a sampling
of individual requests:

```
requests_j  = free_j · w_j · Disk(r)_j
ration_j    = min(1, free_j / requests_j)
consumed_j  = min(free_j, requests_j)
gained_i    = r_i · Disk(free · w · ration)_i
```

Because `Disk` is self-adjoint, `Σ_i gained_i = Σ_j consumed_j` identically, so the
implied per-edge flow has row sums ≤ demand and column sums ≤ capacity **every
round**. Feasibility holds by construction, never by post-hoc repair. Cost: exactly
three disk convolutions per supply group per round.

### 6.3 Reweighting, and why the rounds are averaged

A single pass ends at a **maximal** flow, not a **maximum** one — it commits capacity
greedily, so a tile with several options can consume the one satellite another tile
depended on. Measured against exact max-flow: **6-8% short**.

Repeating the pass while reweighting each satellite by its previous slack pushes
demand off contended satellites onto idle ones, recovering that gap. But the
reweighting is a multiplicative accumulation with **no fixed point**: the weight
spread grows geometrically, reaches ~1e6 by round 16 and pins at the clip bounds by
round 17. Individual rounds stay feasible and the total peaks near round 16, but each
round pushes a *wave* of demand outward from every population centre, rendering as
**concentric rings of alternating utilization** — satellites directly over people
less used than ones a coverage radius away.

The fix is to **average the allocation over all reweighting rounds**. Each round's
rings sit at a different radius, so averaging cancels them, and a convex combination
of feasible flows is itself feasible (row sums stay under demand, column sums under
capacity, total is the mean of the totals). This is the standard ergodic-averaging
remedy for an oscillating first-order iteration, not an ad-hoc smoothing of output.

At N = 100,000, in people:

| allocation | served | map |
|---|---|---|
| single greedy pass | 5,242 M | clean |
| best single reweighted round | 5,774 M | heavy ringing |
| **average of rounds 0-16** | **5,612 M** | **clean** |

Costs 2.8% of the peak, still +7% over greedy, and is what the model reports.

> **Two lessons worth carrying.** The rings were the tell — the *total* alone never
> exposed them. And a global smoothness metric (total variation) actively **missed**
> them: TV *improved* as the rings developed, because it is dominated by the
> coastline halos. Only a zoomed crop of the actual map found it.

---

## 7. Outputs

`AllocationResult`, all per tile on the 180×360 grid:

| field | unit | meaning |
|---|---|---|
| `served` | connections | connections carried, per ground tile |
| `served_people` | people | `served × household_size` |
| `demand` | connections | density-capped demand offered |
| `population` | people | raw WorldPop population |
| `household_size` | people/connection | the conversion factor used |
| `utilization` | fraction | `used / capacity`, per satellite tile — NaN where no satellite flies |
| `served_fraction` | fraction | `served_people / population` — NaN where nobody lives |
| `greedy_total` | connections | single un-reweighted pass, a lower-bound proxy for less coordinated routing |

Headline numbers, V3 scenario on Gen1 shell geometry:

| N satellites | connections | people | % of world | fleet utilization |
|---|---|---|---|---|
| 1,000 | 105 M | 364 M | 4.1% | 52.5% |
| 4,408 (Gen1) | 391 M | 1,378 M | 15.6% | 44.4% |
| 10,900 (~today) | 838 M | 2,986 M | 33.7% | 38.4% |
| 33,900 (Gen2) | 1,741 M | 6,219 M | 70.3% | 25.7% |
| 100,000 | 2,388 M | 8,484 M | 95.9% | 11.9% |
| 300,000 | 2,501 M | 8,850 M | 100.0% | 4.2% |

Fleet-wide utilization falls monotonically because V3's per-satellite capacity is so
large that demand, not supply, is scarce almost from the start — and because most
satellites are over ocean.

Charts: `charts/tile_utilization_map.py` → `results/tile_capacity/`. Three stills; two
40-frame animations across fleet size (`utilization_map_vs_satellites.gif` and
`..._large_labels.gif`, the latter promoting fleet size / people served /
constellation utilization to axis-label size under the plot, auto-shrunk to fit since
the satellite count runs from 3 to 7 digits); and every frame as a PNG under
`frames/` and `frames_large_labels/`. Both variants are drawn from the SAME solve per
fleet size — the model is the expensive part and does not depend on labelling. The maps show the physics directly: land
saturated, oceans idle, and a ~940 km partial-utilization halo around every coastline
and Pacific island, which is the coverage disk made visible.

---

## 8. Verification

Nothing below was argued; all of it was measured.

1. **Disk operator vs exact spherical geometry.** Recovers `π(R_e·R)²` to within
   0.4% at every latitude; binary mode matches a direct great-circle distance test
   tile for tile; exactly self-adjoint.
2. **Allocator vs exact max-flow.** `tile_capacity_validation.py` builds the same
   bipartite problem at 4° and 6° tiles and solves it exactly with a hand-written
   Dinic (no scipy in this environment). The reported allocation reaches
   **0.977-0.994 of the optimum, never above it.**
3. **Flow conservation.** Every `allocate()` call asserts served ≤ capacity consumed.
   This exists because the FFT-noise bug of §3.2 produced served ~50% *above*
   consumed, and the guard makes that class of failure impossible to return silently.
4. **Is a dark patch a bug?** `AllocationResult.unreachable_slack()` reports the share
   of covered satellite tiles with **both** spare capacity **and** unserved demand
   within reach — the only places better routing could help. At N = 100,000 that is
   4.7% of tiles holding ~1.5% of served connections, matching the independently
   measured gap from optimum. It confirmed the two large dark regions are real:
   central Sahara sits at 16% utilization with **zero** unmet demand within 940 km,
   while central Europe is at 100% with 39 M queued.
5. **Orbital sanity.** Computed periods ~95 min; Gen1 shells total exactly 4,408.
6. **Demand sanity.** Capped demand converges to exactly 100.0% of world population
   as the cap is relaxed.

### Bugs this verification caught that reading the code did not

| bug | symptom | found by |
|---|---|---|
| FFT round-off served uncovered tiles free | served 50% above capacity consumed | conservation audit |
| log-bin centres | capped demand at 100.4% of world population | totals check |
| reweighting oscillation | concentric rings around population centres | looking at a zoomed map |
| people vs subscribers | — | this spec's own unit review |
| fractional vs binary adjacency | validation ratios above 1.0 | impossible-result check |

---

## 9. Assumptions

Full entries with impact-if-wrong in `ASSUMPTIONS.md`. The ones this model rests on
most heavily:

| # | assumption | direction if wrong |
|---|---|---|
| 11 | 25° minimum elevation | sets coverage radius; well sourced (FCC Order 21-48) |
| 12 | V3 beam count/beamwidth placeholdered from v2 Mini | affects the areal cap only, not the aggregate |
| 13 | household size, 66/217 on a regional fallback | scales people-per-connection |
| 16 | satellites uniform in longitude | clumped RAAN would create persistently under-served longitudes |
| 17 | expected values, not distributions | **optimistic** — `E[min] ≤ min(E)` by Jensen |
| 18 | globally optimal routing | **upper bound**; `greedy_total` is the lower-bound companion |
| 19 | 1° tiles | 4° and 6° runs differ ~1%; no finer run done |

Two structural simplifications worth stating plainly: no J2/orbital perturbation, and
the model runs Gen1's 540-570 km shell geometry with V3's capacity scenario, whose
real planned altitude is 345 km — that would more than halve each coverage disk.
`build_supply(altitude_override_km=345)` exists to test it; no run has been shipped.

---

## 10. Running it

```bash
.venv/bin/python tile_capacity_model.py          # headline table
.venv/bin/python tile_capacity_validation.py     # vs exact max-flow
.venv/bin/python household_grid.py               # household attribution coverage
.venv/bin/python charts/tile_utilization_map.py         # stills
.venv/bin/python charts/tile_utilization_map.py --gif   # stills + animation (~10 min)
```

A solve at 1° takes ~15 s. Reuse one `TileGrid`, one `DemandTiles` and one
`operator_cache` across a sweep — the disk kernels depend only on radius and grid,
not on N, and rebuilding them is most of the cost. `tcm.sweep()` does this.

Requires the WorldPop rasters in `data/raw/worldpop/` (~0.82 GB, `download_worldpop.py`)
and the mosaic cache. **A "successfully loaded" cache is not proof it holds real
data** — an all-NaN cache built before the rasters existed has silently poisoned
this project's charts before. Check `np.isnan(grid.density).all()` first.

---

## 11. Not done yet

- ~~Migrate the market layer.~~ **Done 2026-09-05.**
  `country_service_model.country_servable_fraction()` now reads each country's own
  tiles out of this model, and `tam_model.py` takes the resulting
  `{iso3: servable_fraction}` and does pure pricing. The market numbers no longer
  carry the longitude bug. See `PRICING.md` and CLAUDE.md.
- **Retire `orbital_geometry.expected_sats_reaching_latitude()`** once nothing
  depends on it. It still returns exactly what it always did, with a docstring
  stating the 19× overcount.
- **Serve highest-revenue demand first.** The allocator maximises connections,
  treating all demand as equally valuable; `tam_model` then prices whatever got
  served. Ranking demand by revenue within each tile's reachable set is the intended
  next step, and is why this is a transportation problem rather than a per-band
  `min()`. Shape of that problem, worth knowing before starting: the UNCONNECTED
  price is exogenous (a country's real %unconnected and GNI, independent of N), so
  ranking on it is well defined -- but the CONNECTED price in `mode="full"` is lerped
  by how much of that country's connected population is served, which depends on the
  allocation, so that half needs a fixed point or an explicit simplification.
- **Decide the altitude question** in §9.
- Real RAAN from TLEs, if longitude clumping ever matters.
