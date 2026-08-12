# Starlink Equilibrium Model — handoff doc

Read this first. This project spans many sessions/context windows. Update this file
at the end of every phase — not just at the end of a session — with what was
actually produced, every non-obvious decision and why, known gaps, and concrete next
steps. A fresh session must be able to pick this up cold from this file alone.

**See also `ASSUMPTIONS.md`** — every numeric assumption Claude picked rather than
the user confirming, in one place (satellite lifetime, cross-generation capacity
ratio, ARPU cap, etc.), separate from this file's phase-by-phase narrative. Update
it whenever a new unconfirmed assumption enters the model, and move an entry to its
"Confirmed" section the moment the user actually answers it — don't let it drift out
of sync with what's in the code.

## Model mechanism (the whole point, in one paragraph)

Plot cost ($) on the y-axis and cumulative satellite count on the x-axis. Revenue per
additional satellite falls with diminishing returns — each new satellite reaches
progressively less valuable / more remote demand — giving a roughly 1/x-shaped curve.
Satellite cost + required margin is a flat horizontal line. Where the two cross is the
equilibrium satellite count for that cost assumption, which in turn implies a market
size (addressable revenue) captured at that equilibrium. Running this across
different Starlink satellite-generation costs (v1.0 -> v3) turns into a
cost-vs-market-size sweep. The revenue curve is NOT assumed analytically — it has to
be built up from a real country-level telecom market model (what people currently
pay, what's unserved) crossed with hard physical limits on how many customers a
satellite/constellation can actually serve (bandwidth, beam count, density caps). See
the full phase plan: `C:\Users\Ckalitin-VICTUS\.claude\plans\reactive-zooming-harbor.md`
(may not be readable outside this machine/session — treat this CLAUDE.md as the
authoritative copy of the roadmap below, not that path).

## Phase status

| Phase | What | Status | Output |
|---|---|---|---|
| 0 | Scaffolding | done (2026-08-09) | `data/`, `results/`, `viz/`, this file |
| 1 | Country-level telecom market dataset | done (2026-08-09) | `data/telecom_market_by_country.csv` (217 rows) + `.md`, `build_telecom_dataset.py`, `charts/sanity_check_telecom.py`, `charts/market_overview.py` (4 charts) -> `results/sanity_check/`, `results/market/` |
| 2 | Orbital geometry & coverage | done (2026-08-09) | `data/starlink_shells.csv` + `.md`, `orbital_geometry.py`, `charts/coverage_map.py` (2 charts) -> `results/coverage/` |
| 3 | Satellite capacity & customer density constraints | done (2026-08-09) | `data/satellite_capacity.csv` + `.md`, `capacity_density_model.py`, `charts/capacity_density.py` (2 charts) -> `results/capacity/` |
| 4 | Satellite cost & manufacturing economics | done (2026-08-09) | `data/starlink_satellite_cost.csv` + `starlink_cost_per_gbps.csv` + `launch_cost_scenarios.csv` + `.md`, `cost_per_gbps_model.py`, `charts/satellite_cost.py` (2 charts) -> `results/cost/` |
| 5 | Equilibrium model (core chart) | done (2026-08-09) | `equilibrium_model.py`, `charts/equilibrium.py` -> `results/equilibrium/equilibrium_revenue_vs_cost.png` |
| 6 | Derived charts (continuous cost-vs-market curve, utilization, final revenue/satellite-by-orbit) | done (2026-08-09) | `ASSUMPTIONS.md`, `charts/phase6.py` -> `results/phase6/` (3 charts) |

## Phase roadmap (full detail)

### Phase 1 — Country-level telecom market dataset
One row per country (~195): population, unconnected/underserved population, fixed
broadband $/month & effective $/GB & household penetration %, mobile $/month &
effective $/GB & whether cellular is the dominant access mode, legacy satellite ISP
presence/share, coarse connectivity-cost context field. Sources: ITU DataHub/ICT
Price Baskets, GSMA Mobile Connectivity Index, World Bank ICT indicators, Ookla
Speedtest Global Index / Cable.co.uk, Viasat/EchoStar disclosures, Euroconsult/NSR.
Every figure cited with a confidence note (well-sourced / analyst estimate /
interpolated / no data). Deliverable also includes one sanity-check chart (not final).

### Phase 2 — Orbital geometry & coverage
Real Starlink shell data (altitude, inclination, planes x sats/plane) from FCC
filings/Celestrak/public trackers — replace the user's dictated "~45°/~60°" guesses
with real numbers. Known public shells to verify: ~550km/53.0°, ~570km/70.0°,
~560km/97.6° (near-polar), ~540km/53.2°, plus lower shells. World map overlay of
coverage bands by latitude.

### Phase 3 — Satellite capacity & customer density constraints (REQUIRED, not optional)
Max simultaneous customers per satellite (subscriber/session capacity — spot-beam
count, frequency reuse, ground terminal density, not just raw bandwidth $). Max
customer density per unit area (customers/km²) before a beam/cell is oversubscribed —
this is the mechanism that stops "size for 5M US customers" from implying "serve 5M
customers anywhere for free" (dense demand hits the density cap before it hits a
revenue limit). Bandwidth/capacity per satellite per generation from published SpaceX
figures. Feeds Phase 5 as a hard ceiling independent of Phase 4's cost economics.

### Phase 4 — Satellite cost & manufacturing economics
Cost per generation (v1.0/v1.5/v2 Mini/v2/v3). Start from public analyst estimates
(Quilty Space via SpaceNews) with Reflect-Orbital-style sourcing rigor. **User says
they already have a cost CSV to provide — not yet located (checked Downloads,
Desktop, repo — nothing found as of 2026-08-09). Ask the user for it before locking
Phase 4 numbers**, but don't block earlier phases on it.

### Phase 5 — Equilibrium model (the core chart)
x = cumulative satellite count, y = $. Revenue-per-satellite curve (Phase 1 demand
ranked by ARPU/willingness-to-pay, capped by Phase 3 density/capacity, gated by Phase
2 coverage) vs. flat satellite-cost+margin line (Phase 4). Intersection = equilibrium.
Sweep v1.0 -> v3. **Margin assumption must be confirmed with the user, not picked
unilaterally.**

### Phase 6 — Derived charts
Cost-vs-market-size curve as satellite cost falls — **must be continuous, not
discrete named tiers**. The `Terraform-Market-Ladder` project
(`Terraform-Market-Ladder/terraformer_market_ladder.py` on
`origin/claude/terraform-market-ladder-charts-agq4zx`) is only a loose conceptual
inspiration (cost down -> market unlocked up); do not copy its step-function
structure — country/segment telecom pricing doesn't decompose into clean discrete
tiers the way substitution-fuel markets did. Also: utilization curve (satellites vs.
addressable market $ vs. utilization %), and the final chart (revenue per satellite
vs. satellite number, segmented by orbital shell).

## Phase 1 — what was actually built (2026-08-09)

- `viz/` package (copied from the `charting-and-modeling` skill's bundled scripts):
  `render.py`, `plotting.py`, `info_box.py`, `axis_range.py`. Use these for every
  future chart in this project — don't rewrite matplotlib boilerplate per chart. See
  the edge-case catalog in that skill before debugging a rendering issue (log-axis
  tick labels need a manual `FuncFormatter`, not the matplotlib default, to avoid
  literal `$\mathdefault{...}$` text — already hit and fixed once in
  `charts/sanity_check_telecom.py`, don't re-hit it elsewhere).
- `data/raw/` holds the actual downloaded source files (World Bank API JSON,
  `mobile_data_pricing_2023.xlsx`, `broadband_pricing_2026.xlsx`) for reproducibility
  — `build_telecom_dataset.py` reads only from here, never re-fetches.
- `build_telecom_dataset.py` merges 4 World Bank indicators (population, internet-use
  %, fixed-broadband/100, mobile/100, GNI per capita PPP) with two commercial pricing
  surveys (broadband.co.uk $/month Feb-2026, bestbroadbanddeals.co.uk mobile $/GB
  2023) via a country-name alias table (`NAME_ALIASES`) — World Bank, ITU-style, and
  commercial-survey country naming conventions all differ (e.g. "Korea, Rep." vs
  "South Korea", "Congo, Rep." vs "Republic of the Congo", plus a mojibake hyphen in
  the broadband.co.uk sheet for "Timor-Leste"). If a future data pull introduces new
  country-name mismatches, extend that alias table rather than hand-patching the CSV.
- **Important finding for Phase 5:** World Bank's `internet_user_pct` (and therefore
  `unconnected_population_est`) counts people who don't use the internet for ANY
  reason — including in high-income countries with full coverage (France ~11.3%,
  Italy ~10.8% "unconnected" by this metric, ~7-8M people each). This is a
  usage/adoption gap (age, digital literacy, choice), NOT a coverage/availability gap.
  Starlink's actual addressable market is the coverage-gap subset, which this column
  overstates in developed markets. The sanity chart's own printed output flagged this
  automatically (France and Italy showed up in the "cheap data but >5M unconnected"
  list) — this is exactly the kind of counterintuitive finding to keep surfacing in
  printed output going forward, not just in plots. **Phase 5 should not use
  `unconnected_population_est` directly as "Starlink's addressable population"
  without correcting for this.**
- Legacy satellite ISP flag is deliberately conservative (only 17 countries flagged
  `True`) — see the dataset's own MD for the full caveat. Do not present this column
  as a competitive analysis; it's a rough "known large incumbent present" flag only.
- `charts/regions.py` is the single source of truth for World Bank region -> color
  mapping (7 actual region names, verified against the CSV — note the real MENA
  region name is "Middle East, North Africa, Afghanistan & Pakistan", not the
  shorter name you'd guess). Every chart module imports from here; don't hardcode a
  region list per chart or it will silently drift (this happened once already —
  `sanity_check_telecom.py`'s first draft had a wrong/incomplete region dict that
  bucketed the whole MENA region into "Other").
- `charts/market_overview.py` (6 figures in `results/market/`): unconnected
  population by region, top-25 target countries, mobile-$/GB-vs-broadband-$/month
  cost landscape, affordability-burden ranking, unconnected-pop-vs-wired-$/GB (the
  wired counterpart to the mobile version in `sanity_check_telecom.py` — note its
  $/GB is derived from the flat 300 GB/month assumption, so compare its SHAPE to the
  mobile chart, not absolute $/GB values), and connected-pop-vs-wired-$/month (the
  EXISTING paying market, i.e. the incumbent price Starlink competes against, as
  opposed to the unserved-population charts). **Finding: the three largest connected
  markets already have cheap wired broadband** — China (1.3B connected, $14/mo),
  India (1.0B connected, $9/mo), US (324M connected, $80/mo, expensive in absolute
  terms but a wealthy market). Starlink has little price-based room in these three;
  any share there would come from a non-price edge (unconnected rural pockets within
  them, latency, etc.), not a straight price cut. Relevant for Phase 5 — don't size
  "captured market" by assuming Starlink can undercut everywhere uniformly. These are Phase-1-only market
  landscape charts — no satellite cost/capacity/coverage constraint applied yet, so
  don't present them as "Starlink's target market," just "the market it would enter."
  Found and printed one striking outlier worth knowing: **Burundi's average fixed
  broadband price is ~179% of annual per-capita income** — broadband is
  effectively unpurchasable there at the surveyed retail price.
- Log-axis tick label fix (matplotlib default renders literal
  `$\mathdefault{10^n}$` text once `text.parse_math=False` is set) and info-box
  `mode="off"` sizing (the reserved margin is narrow — keep off-plot info box text
  to a few short words per line, not full sentences) are both now solved once in
  `charts/market_overview.py` and `charts/sanity_check_telecom.py` — copy the pattern
  rather than re-debugging it in future chart modules.

## Phase 2 — what was actually built (2026-08-09)

- `data/starlink_shells.csv` + `.md`: the well-sourced **Gen1 5-sub-shell table**
  (550km/53.0°, 540km/53.2°, 570km/70.0°, 560km/97.6° split into two plane-count
  sub-groups) with full planes x sats/plane geometry, totaling exactly 4,408
  satellites — a strong cross-check since that number is independently the
  widely-cited Phase-1 FCC authorization total. Also includes Gen2, the 2026
  altitude-lowering relocation, and Direct-to-Cell shells with altitude/inclination
  only (**no public plane-count data found for those** — left blank, not estimated).
  Current total satellites in orbit (~10,900 as of 2026-08-06, all generations) is
  recorded as context only, NOT decomposed into the model — **the coverage/density
  charts use only the 4,408-satellite Gen1 table and materially understate real
  current density** (~6,500 Gen2 satellites are excluded for lack of plane data).
  Flag this every time these charts are shown, don't present them as "current state."
- `orbital_geometry.py`: pure-function orbital mechanics (no J2/perturbation
  correction — a documented simplification, fine for market sizing, not for
  operations). Sanity-checked: computed orbital periods came out to ~95-96 minutes,
  matching real Starlink's well-known ~95 min LEO period — a good independent check
  that the physics is right. Key functions: `max_latitude_deg(inclination)`,
  `ground_track(shell)` (produces the real S-curve ground track including Earth's
  rotation), `latitude_density(shell)` / `expected_sats_by_latitude(shells)` (numeric
  sampling of time-averaged latitude density — satellites linger longest near their
  max-inclination turning points, same effect as a pendulum, confirmed in the density
  chart's peak right at the inclination angle).
- `charts/coverage_map.py` (2 figures in `results/coverage/`): a world map (Natural
  Earth 110m land polygons, `data/raw/ne_110m_land.geojson`, rendered directly with
  matplotlib `Path`/`PathPatch` — **no cartopy/geopandas installed in this
  environment**, don't assume they're available in a future session either, check
  first) with coverage latitude bands + one satellite's ground track per shell
  inclination traced over a **full 24h day** (~15 orbits, per user request — shows
  the real fan-of-parallel-passes pattern, since the ~95 min period doesn't evenly
  divide a day so each pass is shifted west by Earth's rotation); and a
  satellite-density-by-latitude stacked chart. Peak instantaneous density is ~144
  satellites overhead at ±52° latitude (Gen1 only). `orbital_geometry.ground_track()`
  takes a `duration_s` param for this (`None` = one orbit, `86400` = one day) — reuse
  that param rather than re-deriving the multi-orbit math elsewhere.
- **Two things Phase 3 needs from here:** (1) `max_latitude_deg()` for whether a
  country's latitude is covered by a given shell at all, (2)
  `expected_sats_by_latitude()` (or a Gen2-extended version of it, once plane data is
  found) as the raw input for per-latitude-band satellite capacity limits.

## Phase 3 — what was actually built (2026-08-09)

- `data/satellite_capacity.csv` + `.md`: per-generation throughput (v1.5 ~20 Gbps,
  v2 Mini 96 Gbps down / 6.7 Gbps up cross-confirmed by 2 independent sources, v3
  1,024 Gbps design target/unbuilt). **The load-bearing find is a full, reproducible
  density derivation** from Meinrath/Grindal/Fishbine/DeGidio, "Starlink Capacity
  Analysis v0.2" (X-Lab/Penn State, July 2025,
  https://thexlab.org/wp-content/uploads/2025/07/Starlink_Analysis_Working_Paper_v0.2.pdf):
  a v2 Mini beam (6 Gbps down / 0.419 Gbps up, 16 beams/satellite, 1.5° beamwidth,
  550 km altitude) supports max ~419 subscribers under 20:1 contention before
  breaching the US 100/20 Mbps broadband threshold (upload-limited), over a ~163 km²
  footprint — **6.66 subscribers/sq mi (2.57/km²) density ceiling, ~6,704
  customers/satellite**.
- `capacity_density_model.py`: reproduces that derivation as parameterized pure
  functions (`CapacityScenario` dataclass + `beam_footprint_area_km2`,
  `max_subscribers_per_beam`, `max_customer_density_per_km2`,
  `max_customers_per_satellite`) rather than hardcoding the result — **validated
  against the source paper's own numbers exactly** (162.8554 km² footprint, 419
  subscribers/beam, 6.66/sq mi, all matched to the source's stated figures). Re-run
  with a different `CapacityScenario` for a different assumption set instead of
  hand-deriving a new number.
- `charts/capacity_density.py` (2 figures in `results/capacity/`): a sensitivity bar
  chart (dedicated vs. 20:1-contended vs. the source's own "tighter overlapping
  beams" alternative — density ranges from 0.13 to 11.6 subscribers/km² depending
  entirely on assumptions, a >85x spread) and a max-theoretical-customers-by-latitude
  chart (Phase 2's satellite density x this phase's per-satellite cap — an explicit
  UPPER BOUND that ignores beam-footprint overlap between neighboring satellites).
- **The single most important finding of Phase 3, load-bearing for Phase 5:** at this
  capacity ceiling, the Gen1 constellation (4,408 sats) caps out at **~29.6M
  customers globally**, and even the full current fleet (~10,900 sats, all
  generations, naively assuming v2-Mini-class capacity for all of them) caps out at
  **~73.1M** — a **~31x gap** below Phase 1's ~2.3B-person unconnected-population
  figure. **Capacity, not demand, may be the binding constraint on Starlink's
  achievable market size.** Phase 5's equilibrium model must account for this: the
  revenue-per-satellite curve cannot assume demand is always the limiting factor —
  past some satellite count, the customer-density ceiling within already-covered
  areas binds first, not a lack of willing customers. This reframes the whole
  "equilibrium satellite count" question the user originally posed: it may be
  capacity-bound long before it's revenue/cost-bound at low satellite-generation
  costs.

## Phase 3 addendum — population-by-latitude overlay (2026-08-09, user-requested after Phase 3)

- `population_by_latitude.py` (root): bins Phase 1's country population/unconnected
  data into the same 1°-latitude rings Phase 2/3 use, so the two can be directly
  overlaid. **Approximation, clearly flagged**: each country's ENTIRE population is
  placed at its CAPITAL CITY's latitude (pulled from `data/raw/wb_countries.json` —
  already-fetched Phase 1 data, no new dependency). This is not a population-weighted
  centroid — known-bad cases are countries with deliberately relocated/non-
  representative capitals (Brasília, Abuja, Naypyidaw, Canberra,
  Astana/Nur-Sultan, Putrajaya). Sanity check: binned total came to 8.19B population /
  2.29B unserved (28%), matching Phase 1's country-level totals closely — a good
  consistency check that the binning itself isn't losing or double-counting anyone
  (3 small territories dropped for missing capital coordinates: Curaçao, Gibraltar,
  West Bank & Gaza).
- `charts/population_capacity_overlay.py` (2 figures in `results/capacity/`):
  - `population_by_latitude_served_unserved.png` — stacked bars (served bottom,
    unserved top) per 1° latitude ring. Two huge spikes dominate: ~29° (New
    Delhi/India) and ~40° (Beijing/China) — India's spike is almost entirely
    unserved (red), China's is almost entirely served (blue), a striking visual
    contrast in a single chart.
  - `normalized_capacity_vs_population_by_latitude.png` — satellite theoretical-max
    and total-population curves, EACH normalized to its own peak (0-1), overlaid.
    **Read this as a shape comparison only, not an absolute one** — Phase 3 already
    established capacity is ~31x short in absolute terms; this chart answers a
    different question (does the shape of where capacity concentrates match the
    shape of where people are?). Finding: **no, they peak by different mechanisms
    entirely** — population peaks at ~40° because that's where people live (India/
    China), satellite capacity peaks at ~52° because that's a shell's orbital
    turning point (the pendulum-lingering effect from Phase 2). These are
    uncorrelated mechanisms; the fact that both curves are elevated across most
    populated latitudes is closer to coincidence (Gen1's shells span 43-82° with
    accumulating overlap in the 45-55° band) than a designed match.
- Both new chart scripts reuse `orbital_geometry.py` and `capacity_density_model.py`
  as-is (no changes to Phase 2/3 code) — only new code is the population-binning
  layer and the chart module.
- Earlier in this same session, `charts/capacity_density.py`'s
  `max_customers_by_latitude.png` was reworked for legibility after the user
  couldn't parse it: added shell-max-latitude reference lines (color-matched to
  `charts/coverage_map.py`'s `INCLINATION_COLORS`), equator/Arctic-circle reference
  lines for orientation, switched the info box from a verbose paragraph (which
  got clipped by `mode="off"`'s narrow margin — see the info-box sizing lesson
  logged in the Phase 1 section) to short 2-3-word lines that actually fit, AND
  (per a follow-up user request) set an explicit `ax.set_ylim(1e4, max*1.5)` floor —
  a log-scale axis going down toward the true near-zero values at the poles wastes
  most of the chart's vertical space rendering a tail nobody needs to read precisely;
  cut it off just under the smallest MEANINGFUL value instead of letting autoscale
  chase the asymptote.

**Follow-up fix (2026-08-09)**: the user flagged that `population_by_latitude_served_unserved.png`'s
info box overlapped real data — `mode="on"`'s auto-scan couldn't find a clean spot
because small bars are scattered across nearly the whole x-range (unlike a chart with
one obvious empty region). Fixed by switching both `population_capacity_overlay.py`
charts to `mode="off", off_side="right"` with short (2-3 word) lines per the
established narrow-margin lesson. **General pattern now confirmed across 3+ charts
in this project: when bars/fills are scattered across most of the x-axis (not
concentrated with an obvious gap), default to `mode="off"` rather than trying
`mode="on"` first** — the auto-scan works best when there's a genuinely large empty
region for it to find, which sparse-but-nonzero data across the whole width doesn't
provide.

## Phase 3 addendum #2 — current (actual) Starlink subscribers by latitude (2026-08-09, revised)

User asked for real current customer counts by geography, explicitly anticipating
it would be hard. It was — see `data/starlink_subscribers.md` for the full research
trail. **SpaceX does not publish country-level subscriber data anywhere** (confirmed
by directly searching the full text of their SEC S-1 filing — fetched from SEC
EDGAR, 1.48M characters, zero country/region subscriber breakdown found; the filing
DOES have a geographic REVENUE table by "country of domicile," but Ireland's
outsized figure there is almost certainly a billing-entity artifact, not real
customer concentration — deliberately NOT used as a customer-geography proxy).

**First pass concluded only 2 countries (US, Brazil) had usable data and stopped
there. The user correctly pushed back**: SpaceX/regulators post frequent DATED
growth milestones, and those can be extrapolated forward instead of shrugged at.
Rebuilt with a proper methodology:

- **`data/starlink_subscriber_milestones.csv`** — raw, dated anchor points only (no
  derived numbers). Global: 12 real dated points, Dec 2022 -> June 2026 (roughly
  monthly resolution recently), plus one row explicitly tagged
  `analyst_forecast_not_actual` (Quilty Space's 16.8M year-end-2026 forecast — kept
  for context, excluded from extrapolation by default). Country rows: US (2 points,
  press + New Street Research), Brazil (1 point only), **Nigeria (3 points, 2 from
  the Nigerian Communications Commission — a telecom regulator, the best source type
  after the S-1 itself)**, **Kenya (2 points, both from the Communications Authority
  of Kenya)**. Superseded and DELETED the old single-snapshot `starlink_subscribers.csv`.
- **`starlink_subscriber_trend.py`** (root) — the extrapolation as reusable pure
  functions, not a one-off calculation: `estimate_current(scope, target_date)` uses
  constant-daily-geometric-growth-rate between a scope's **two most recent** real
  anchors (deliberately NOT the earliest ones — Nigeria's first 9 months implied
  ~11.6%/month, an early-hypergrowth rate that would be absurd to extrapolate 21
  months forward; the model always prefers the freshest pair). Brazil, with only one
  anchor, uses `estimate_via_global_relative_growth()` instead — scales its single
  662K point by the global relative growth between that date and the target, a
  **materially weaker assumption** (assumes Brazil tracks the global average; likely
  an UNDERestimate since Brazil was almost certainly outgrowing the global average
  around when its one data point was taken).
- **Results as of 2026-08-09**: Global ~14.0M, US ~2.94M, Brazil ~927K (weak
  method), Nigeria ~98K, Kenya ~30K. **Known total ~4.0M of ~14.0M (~28.5%)** — barely
  moved versus the original 2-country pass (~28%), because Nigeria and Kenya, while
  real regulator-sourced data, are small in absolute terms. The ~72% gap is still
  dominated by unlisted-but-plausibly-large markets (Canada, UK, France, Germany,
  Australia, Japan, Mexico, Philippines, ~155 others) that were searched for and
  came up empty this session.

`charts/current_subscribers_by_latitude.py` -> `results/capacity/current_subscribers_by_latitude.png`:
plots the 4 country ESTIMATES (not raw figures — always extrapolated to the same
target date so they're comparable) at capital latitude, against a faded
total-population-by-latitude backdrop (`twinx()`) for scale context.

**Two lessons learned mid-build, both worth carrying to future charts:**
1. `info_box.add_info_box(mode="off")` only resizes the axes it's called on — with a
   `twinx()` present, that desyncs the two axes' positions and visibly corrupts the
   layout (title/labels appear to vanish, covered by the unresized twin axis). Not
   yet fixed in shared `viz/info_box.py` — worked around locally with plain
   `ax.text()` + manual bbox on every twinx chart in this project so far.
2. When placing a manual `ax.text()` box, a single long unwrapped source-citation
   string will render as ONE long line that can silently extend far past where you'd
   expect from the anchor point — this caused a real overlap with the legend (the
   source line, anchored `ha="right"` at x=0.99, extended left far enough to
   underlap a legend positioned at the opposite corner). Always hand-wrap long
   citation strings into multiple short lines in manual `ax.text()` calls; the
   `info_box` helper only avoids this automatically via its scan, which `ax.text()`
   doesn't get.

**Do not let a future session distribute the undisclosed share across countries by
population or any other proxy without treating that as a new, explicitly-flagged
estimation exercise** — and when adding a new country, follow the same discipline:
find at least 2 DATED anchors from a named source, prefer regulator/official over
press/analyst, and use the 2 most RECENT anchors for extrapolation, never the
earliest. Re-run `starlink_subscriber_trend.py` periodically — these anchors go
stale within weeks given the observed growth rate.

## Phase 3 addendum #3 — subscribers revision 2: UK/Mexico/Canada added (2026-08-09, same session)

User pushed back a second time, specifically by name on UK/France, after revision 1
landed at "only 4 countries, ~72% undisclosed." Correctly — the first pass stopped
after one source type (dated subscriber milestones) without trying a second. Found
one: **Ookla's "2025 Global Satellite Broadband Performance Report"** (published
2026-02-04, Q3 2025 data) ranks countries by **share of Starlink's global Speedtest
samples** — a different metric, not a subscriber-count milestone, but real, named,
and dated. Added **`data/starlink_ookla_market_share.csv`**: US 22.5%, Mexico 5.7%,
Canada ~4.3%, UK 3.5% (11th largest market). New function
`estimate_via_ookla_share()` in `starlink_subscriber_trend.py` applies
`share% x global_value_at(target_date)`.

**Known total went from ~4.0M/~28.5% to ~5.9M/~42%** — a real improvement, not
cosmetic. `charts/current_subscribers_by_latitude.py` now visually distinguishes the
two confidence tiers: solid bars for the 4 milestone-based countries (US, Brazil,
Nigeria, Kenya), **hatched bars** for the 3 Ookla-share-based ones (Mexico, Canada,
UK) — don't remove that visual distinction in a future edit, it's load-bearing for
not overstating confidence.

**Important, deliberately-surfaced limitation**: cross-checking the US's own 22.5%
share against its DIRECT milestone anchor (2.0M, 2025-07-15) shows the share-based
method implies only ~1.6M for a similar date — **the share-of-samples method
understates by ~25% for the one country where both metrics exist.** This means
Mexico/Canada/UK's estimates are **directional, not precise** — could be biased
either direction for each of those specific countries, since the US comparison only
proves the method is imperfect, not which way it's off elsewhere. Also found and
logged (not resolved): a separate source's "Canada: 500K subscribers = 4.3% of
global" doesn't arithmetically hold (500K/7M ≈ 7.1%, not 4.3%) — both numbers kept
in the .md rather than silently picking one.

**France was searched again, deliberately, including French-language sources**
(ARCEP consultation filings, French tech press) — genuinely no subscriber or
share figure exists publicly, confirmed not just assumed. Same dead-end for
Germany, Australia, Japan, Philippines, and Indonesia (a confirmed top-5 market by
two different secondary sources, but neither states a %). **If a future session
wants to close more of the remaining ~58% gap, these are the next places to check**,
and the Ookla report itself (not yet fetched directly from ookla.com, only via
press coverage of it in this session) may have more country rows than what press
articles chose to quote — worth fetching directly if it can be found.

## Chart bug fixes round (2026-08-09, user-reported)

Three real bugs found by the user in `max_customers_by_latitude.png` and related
charts, all fixed at the SHARED helper level where possible (not per-chart patches):

1. **Shell-max-latitude labels rendered directly on top of their own dashed
   reference lines** (both centered on the same x-position with `rotation=90`,
   unreadable). Fixed in `charts/capacity_density.py` by switching from `ax.text()`
   to `ax.annotate()` with `xytext=(5, 0), textcoords="offset points"` — a small
   screen-space offset that survives axis inversion/rescaling, unlike a data-space
   offset would.
2. **`viz/info_box.py`'s `mode="off"` left a large dead-space gap between the axes
   edge and the box** — the old anchor formula (`1 + frac*0.5/(1-frac)`) centered the
   box in the reserved margin instead of hugging the edge, wasting roughly half the
   margin as blank space. Fixed by replacing it with a small FIXED pad (`0.035`, not
   frac-scaled) from the new axes edge — **this is a shared-helper fix, so it
   silently improved every chart in this project using `mode="off"`, not just the
   one the user pointed at.** Re-ran the full chart suite after the fix (Phase 1
   market charts, sanity check, all Phase 2/3 latitude charts) to confirm no
   regressions — found and fixed one: `unconnected_population_by_region.png`'s
   longest bar label started touching the now-closer box, fixed by settling on
   `pad=0.035` (tested `0.02` first, too tight for that specific chart's bar-label
   overhang).
3. **Latitude charts stopped at -60° instead of -90°**, inconsistent with the two
   charts that already used the full range. Changed `set_xlim(-60, 85)` ->
   `set_xlim(-90, 90)` in `current_subscribers_by_latitude.py` and all 3 figures in
   `population_capacity_overlay.py`, per explicit user request for
   completeness/comparability across charts.

**Lesson for future chart work in this project**: when a layout bug is found in the
shared `viz/info_box.py` helper (not chart-specific code), fix it there once and
re-run every chart that uses it, don't patch the one chart the user happened to
flag — the whole point of the shared helper is that a fix in one place fixes it
everywhere, but only if you actually re-run everywhere.

## Chart info boxes cut down to size (2026-08-09, binding going forward)

User: "limit the fucking size of your note boxes thats so much fucking noise on the
chart." Fair — info boxes across nearly every chart in the project had grown into
8-15 line paragraphs repeating detail that already lives in the companion `.md`
files. **Went through every chart file and cut every info box to 1-3 short lines
max**: a one-line caveat (if there's a real one worth having on the chart itself)
plus a bare `Source: filename.md` — no more restating full methodology, source
lists, or multi-sentence caveats in the chart image. Also shortened every `SOURCE_NOTE`
constant to just the filename (dropped the parenthetical author/publisher detail
that was getting appended into every box in that file). **This is now the binding
convention** — a chart's job is to show data; the "why should I trust this number"
explanation belongs in the `.md`, one hop away, not printed on the chart itself.
Same fix also caught two real layout bugs: `capacity_density.py`'s
`max_customers_by_latitude.png` box was long enough to clip off the right edge of
the figure at the reduced `off_frac`, fixed by shortening the text further rather
than widening the margin back out.

## Project-wide chart convention (2026-08-09, binding going forward)

**Every latitude x-axis chart in this project now has NORTH (positive latitude) on
the LEFT and south (negative) on the right** — the opposite of a default matplotlib
ascending axis, per explicit user instruction. Implemented as `ax.set_xlim(lo, hi)`
followed by `ax.invert_xaxis()` (simplest way to flip without renumbering ticks or
touching data). Applies to: `max_customers_by_latitude.png`,
`satellite_density_by_latitude.png`, `population_by_latitude_served_unserved.png`,
`normalized_capacity_vs_population_by_latitude.png`,
`current_subscribers_by_latitude.png`, `population_by_latitude_by_region.png`. Does
NOT apply to `coverage_bands_world_map.png` (latitude is the Y-axis there, already
north-up per standard map convention — no change needed). **Any new latitude chart
must follow this convention too** — add `ax.invert_xaxis()` after `set_xlim()`.

Also simplified `current_subscribers_by_latitude.png` per user feedback ("ugly",
asked what the grey bars were): removed the `twinx()` total-population backdrop
entirely (it was context-only and added visual noise without being asked for) and
removed the center annotation box, folding the same "known vs. undisclosed" numbers
into the existing top-right methodology note instead of a separate box. **Lesson:
don't add a "context only" secondary dataset (twinx, faded backdrop) to a chart
unless it was specifically asked for — it reads as clutter, not context, if the
user didn't request the comparison.**

## Phase 3 addendum #4 — population by latitude, split by region (2026-08-09)

`charts/population_capacity_overlay.py` gained a third figure,
`population_by_latitude_by_region.png`: same capital-city-latitude population
binning as before, but stacked/colored by the 7 World Bank regions (`charts/regions.py`)
instead of served/unserved. Required a new function,
`population_by_latitude.bin_by_latitude_and_region()`, alongside the existing
`bin_by_latitude()` — both reuse the same row-loading function, just aggregate
differently. Visually confirms the same two dominant spikes as the served/unserved
chart (China ~40°N East Asia & Pacific, India ~29°N South Asia) but now shows which
REGION every other bar belongs to, e.g. the ~53°N-ish cluster is clearly Europe &
Central Asia + North America together, not a single undifferentiated population mass.

## Phase 4 — what was actually built (2026-08-09)

- User pointed directly at `Reflect-Orbital/sso-land-proximity/data/reflect_orbital_sources.md`
  (+ identical `.xlsx`) as the seed source for this phase, then explicitly said it
  "might not be enough" and to research further. It wasn't enough on its own:
  traced every figure back and found **all 5 generations' cost figures trace to ONE
  analyst (Caleb Henry, Quilty Space) in ONE SpaceNews article dated 2024-05-09** —
  fine as a starting point, but single-sourced and, by this project's standards
  (2 years old in a fast-scaling production line), stale.
- **Load-bearing new finding**: New Space Economy (2026-04-13) reports v2 Mini now
  costs **~$400K/unit "at production volume"** (5 sats/day from Hawthorne) — roughly
  **half** the 2024 Quilty figure for the same generation. **Confidence: single
  source, NOT further attributed to Quilty or anyone else in that article** — treat
  as directional evidence of real cost decline, not a confirmed new baseline. Kept
  BOTH the 2024 ($800K) and 2026 (~$400K) v2 Mini points in
  `data/starlink_satellite_cost.csv` rather than overwriting — the decline itself
  is the finding, shown as a diamond marker + arrow in
  `satellite_cost_by_generation.png`.
- **Second independent metric found**: Gale Pooley (Utah Tech/Cato Institute) citing
  ARK Invest — satellite bandwidth cost fell **$300M/Gbps (2004) -> ~$40K/Gbps
  (current) -> ~$1K/Gbps (2028 forecast)**, a Wright's-Law framing (45% decline per
  cumulative Gbps-in-orbit doubling), **independent of the Quilty Space chain** (a
  real cross-check angle, not just a second citation of the same number). This is a
  fundamentally different metric than $/satellite — cost per unit of DELIVERED
  capacity, folding in Phase 3's per-generation Gbps figures. `data/starlink_cost_per_gbps.csv`
  + `satellite_cost_per_gbps.png`.
- **Real bug caught and fixed before shipping**: `charts/satellite_cost.py`'s first
  draft hatched bars via `"estimate" in confidence_string` — this incorrectly
  hatched v1.0 and v3 too, because their confidence labels ("analyst_estimate",
  "analyst_projection_..._estimate") contain the substring "estimate" despite being
  the STRONGEST tier (directly-quoted Quilty figures), not the weak
  interpolated/unconfirmed tier the hatching was meant to flag. Fixed with an
  explicit `WEAK_CONFIDENCE` set instead of substring matching — a reminder that
  substring-matching confidence/quality labels is fragile when strong and weak
  labels share common words.
- Launch cost (F9 rideshare $6,000/kg, Starship $67-200/kg — already in the seed
  file) was **deliberately NOT combined with satellite mass into a cost-to-orbit
  figure yet** — needs a user decision on which launch-cost assumption to pair with
  which generation first (see Known gaps below).

## Phase 4 revision + Phase 1 correction (2026-08-09, user answered all open questions)

User answered all four open items from Phase 4 in one message, rapid-fire. Recorded
exactly, don't re-litigate:

1. **Cost metric: $/Gbps.** "Hard stop." Not $/satellite.
2. **Launch cost pairing**: F9 for v1.0/v1.5/v2 Mini, Starship "initial" (conservative
   near-term, $200/kg) for v3, PLUS a second "Starship end-state" scenario
   (aspirational, $67/kg, not yet achieved) for v3.
3. **"Latest"** — use the latest known manufacturing-cost figure per generation, not
   an average or continuous model. v2 Mini therefore uses the 2026 ~$400K point.
4. **Required margin: 20%.**

Also: **"Yes I need correct numbers, obviously"** — re: correcting
`unconnected_population_est` for the adoption-vs-coverage-gap issue flagged since
Phase 1. Done — see the new `unconnected_population_est_coverage_corrected` column
and full methodology in `telecom_market_by_country.md`.

### What was built

- **`cost_per_gbps_model.py`** (root): pure-function model implementing decisions
  1-4 above. `data/launch_cost_scenarios.csv` holds the 3 launch-cost scenarios
  (`f9_internal_marginal` $857/kg — SpaceX's OWN cost, not the rideshare price;
  `starship_initial` $200/kg; `starship_endstate` $67/kg — all traced back to the
  Reflect Orbital sourcing file). **v2_full is excluded from every $/Gbps
  calculation** — no published capacity (Gbps) figure was found for it in any
  research pass this session, and $/Gbps cannot be computed without one.
- **`charts/satellite_cost.py`** rebuilt around `cost_per_gbps_model.py` ->
  `results/cost/cost_per_gbps_by_generation.png` (bars + a 20%-margin dashed line
  per generation) and `results/cost/satellite_cost_per_gbps_trend.png` (renamed
  from the old `satellite_cost_per_gbps.png` — same ARK Invest industry-wide trend
  chart from before, kept as a cross-check, clearly distinguished from the
  Starlink-specific generation chart).
- **Real bug caught before shipping**: v1.0 (20 Gbps, found via a new search this
  session) and v1.5 (still reusing v1.0's 20 Gbps figure, no separate source ever
  found) come out to $21,141/Gbps and $25,569/Gbps respectively — **v1.5 shows
  HIGHER $/Gbps than v1.0 despite being a later generation**, purely because v1.5's
  higher mass (more launch cost) isn't offset by any confirmed capacity increase in
  the data. Flagged explicitly in the chart's info box as a **data limitation, not a
  real regression** — v1.5's laser inter-satellite links almost certainly increase
  effective capacity, it's just never been independently measured/published
  separately from v1.0's figure.
- **Coverage-gap correction**: `build_telecom_dataset.py` now computes
  `unconnected_population_est_coverage_corrected` (High income countries only:
  floor effective connected % at `HIGH_INCOME_COVERAGE_FLOOR_PCT = 97.0`). Checked
  for a real per-country coverage-gap dataset first (ITU DataHub blocks automated
  fetch — confirmed AGAIN, same 403 as Phase 2; GSMA's historical bulk-export URL
  pattern that worked for 2020 returns 404 for every year 2024-2026 tried) — none
  accessible, so this is a **documented targeted assumption**, not measured data.
  Effect: individual high-income countries drop a lot (France 7.8M -> 2.1M, Japan
  17.8M -> 3.7M) but the **global total barely moves** (2.29B -> 2.23B, -2.5%) since
  most unconnected population was never in the high-income bucket. **Every chart
  that consumed `unconnected_population_est` was found via grep and switched to the
  corrected column, then re-run**: `charts/market_overview.py` (6 charts, including
  fixing a now-stale "CAUTION" note in `top25_unconnected_countries.png` that had
  been warning about exactly the problem just fixed), `charts/sanity_check_telecom.py`,
  `population_by_latitude.py` (cascades to both `charts/population_capacity_overlay.py`
  figures and `charts/current_subscribers_by_latitude.py`'s population backdrop),
  and a hardcoded `2.3e9` literal in `charts/capacity_density.py`'s Phase 3
  gap-finding print statement, changed to compute the corrected total dynamically
  from the CSV instead of a stale hardcoded number.
- **Dead code removed while in there**: `charts/current_subscribers_by_latitude.py`
  still imported and called `population_by_latitude.load_country_population_by_latitude()`
  from before the twinx population backdrop was removed (per earlier user feedback)
  — the loaded `rows` variable was never used afterward. Removed the import and call.

## Phase 5 — the core equilibrium model (2026-08-09)

Built immediately after Phase 4 closed out, per "Go into phase 5!" User also caught
two real bugs in Phase 4 output first — see the "$/Gbps line looked like a constant
offset" and "delete v1.5" fixes logged just above/below this section.

**Mechanism, adapted for $/Gbps** (the plan's original text said "x = satellite
count," written before the cost-metric decision): x-axis is CUMULATIVE GBPS
DEPLOYED, not satellite count directly, because a satellite is a different amount
of capacity in each generation — a single satellite-count x-axis wouldn't mean the
same thing across generations, while Gbps does. Satellite count is still reported
at every equilibrium point (`equilibrium_gbps / gbps_per_satellite(generation)`),
just not as the axis itself.

**`equilibrium_model.py`** (root) builds the demand side, per country:
- ARPU proxy = local incumbent price for the dominant access mode (mobile if
  `cellular_dominant_market`, else fixed broadband).
- Addressable customers = `min(coverage-corrected unconnected population, land_area_km2
  x Phase 3's density ceiling)` — **the density cap is REQUIRED per the user's
  earlier explicit instruction**, and it bites hard: 161 of 204 countries are
  density-bound, not population-bound, including India (7.6M addressable vs. a much
  larger raw unconnected population) — direct confirmation of Phase 3's finding.
  New data pulled for this: `data/raw/wb_AG.LND.TOTL.K2.json` (World Bank land area).
- Coverage gate (capital latitude within Gen1's ~82.4° max) — included for
  correctness, excludes ~nothing in practice.
- Countries ranked by ARPU descending, walked cumulatively into a revenue-per-Gbps
  step curve.

**Real data-quality bug caught and fixed before shipping**: the raw ARPU ranking put
Zimbabwe at $437/mo, ahead of every other country by a wide margin — implausible for
a low-income economy, and traced to the same "thin survey sample skews the average"
limitation already documented in `telecom_market_by_country.md`. Added
`ARPU_CAP_USD_MONTH = 100.0` (just above the US's own real $80/mo, the highest
plausible price point in the dataset) — caps 15 countries' ARPU, flagged as a
modeling choice via `arpu_capped` on each `CountryDemand`, not a silent data fix.

**Unconfirmed assumptions this model depends on are tracked in `ASSUMPTIONS.md`, not
duplicated here** — `SATELLITE_LIFETIME_YEARS`, `CUSTOMERS_PER_GBPS`,
`ARPU_CAP_USD_MONTH`, the ARPU-proxy definition, and the whole-country-vs-populated-area
density question all live there with full reasoning. Check that file before Phase 6,
and update it (don't just fix the code) if any of them change.

**Results** (`charts/equilibrium.py` -> `results/equilibrium/equilibrium_revenue_vs_cost.png`):

| Generation | Equilibrium capacity | Satellites | Countries served | Market size |
|---|---|---|---|---|
| v1.0 | 2.59M Gbps | 129,328 | 183/204 | $60.2B/yr |
| v2 Mini | 2.80M Gbps | 29,143 | 194/204 | $61.1B/yr |
| v3 (Starship initial) | 3.04M Gbps | 2,965 | 204/204 | $61.5B/yr |
| v3 (Starship end-state) | 3.04M Gbps | 2,965 | 204/204 | $61.5B/yr |

**The single most important finding of Phase 5**: both v3 scenarios saturate to the
EXACT SAME equilibrium (serving all 204 modeled countries) despite having different
costs — because at Starship-class $/Gbps, cost stops being the binding constraint
entirely; the model runs out of MODELED DEMAND before it runs out of profitability.
This is the demand-side mirror of Phase 3's finding that capacity may bind before
cost/revenue does — **together they mean the equilibrium question the user
originally posed doesn't have one binding constraint, it has (at least) three
(cost, revenue/demand, and physical capacity), and which one binds depends on where
in the cost curve you are.** At v1.0-class cost, cost binds (only 183/204 countries
profitable). At v3-class cost, demand as modeled binds (all 204 countries
profitable, cost line is far below the demand curve). Phase 3's separate finding
suggests physical capacity would bind before EITHER of those at real-world
constellation sizes, since even the full current ~10,900-satellite fleet caps out
around ~73M customers globally — far below what these equilibria would need
satellites to serve.

**Follow-up (2026-08-09)**: user asked to start the x-axis at 10,000 Gbps, then
tightened it further to 100,000 — the revenue curve is flat from 1 to ~1e5 Gbps
(every ARPU-capped country tied at the $100/mo ceiling), so that whole stretch
carried no information and wasted most of the log-scale plot. Settled on
`ax.set_xlim(1e5, points[-1][1] * 1.15)` in `charts/equilibrium.py`, which starts
almost exactly where the curve begins moving — same "don't render dead space"
principle as the info-box pad fixes above, just applied to an axis range instead of
a text box.

**What Phase 6 (or a revision of Phase 5) should do next**:
- Get the user to confirm/replace `SATELLITE_LIFETIME_YEARS` and the cross-generation
  `CUSTOMERS_PER_GBPS` assumption.
- Reconcile Phase 5's equilibrium satellite counts against Phase 3's own physical
  capacity ceiling (~73M customers globally at current fleet size) — right now
  Phase 5 answers "what's revenue-maximizing" without checking "is it physically
  buildable," which Phase 3 suggests it often isn't at these scales.
  Phase 6's utilization chart (satellites vs. addressable market $ vs. utilization %)
  is exactly where this reconciliation belongs.
- Consider whether `ARPU_CAP_USD_MONTH` should instead be a per-country cap tied to
  `connectivity_cost_pct_of_gni` (already in the dataset) rather than a single global
  dollar ceiling.

## Phase 6 — derived charts + a load-bearing ranking bug found while explaining them (2026-08-09)

Built immediately after Phase 5, per "Yes make the phase 6 charts." Also created
**`ASSUMPTIONS.md`** (root) at the user's request, consolidating all 10 unconfirmed
numeric assumptions scattered across `.py`/`.md` files into one place with
Where/Why/Impact-if-wrong per item, plus a "confirmed by user" log — read that file
before touching any constant in `equilibrium_model.py` or `capacity_density_model.py`.

**What was built** (`charts/phase6.py` -> `results/phase6/`, using new
`equilibrium_model.sweep_cost_curve()`):
1. `continuous_cost_vs_market_size.png` — the continuous version of Phase 5's 4-point
   equilibrium chart, sweeping cost/Gbps/year across 200 points instead of just the 4
   generation values (per the binding "must be continuous, not discrete tiers"
   decision).
2. `utilization.png` — reconciles Phase 5's revenue-optimal satellite counts against
   Phase 2's real coverage-minimum constellation (4,408 sats, Gen1 shell design: you
   physically cannot cover the globe with fewer, regardless of demand). **Real
   finding, directly validates the user's original dictated intuition**: v1.0 and v2
   Mini are demand-bound (100% utilization — demand alone needs more satellites than
   the coverage minimum). Both v3 scenarios are **coverage-bound at 67% utilization**
   — Starship-class cost makes so much demand profitable that satellite count would
   naturally fall below what continuous coverage requires; the constellation ends up
   flying largely empty capacity just to maintain global coverage.
3. `revenue_per_satellite_by_generation.png` — NOT segmented by orbital shell as the
   original plan text said (no per-shell demand mapping exists anywhere in this
   project — Phase 2's shells are redundant global coverage, not assigned to specific
   countries), segmented by generation instead, flagged in the chart's own info box.

**Two real bugs hit and fixed, both already-known bug classes from earlier phases
re-surfacing** (per the "fix at the shared/root cause, don't just patch the one
instance" lesson already logged twice above): the `$\mathdefault{10^n}` log-axis tick
bug and the v3-dual-scenario label-overlap bug (same class as `charts/equilibrium.py`,
grouping key needed adjusting per-chart since here the grouping axis is cost, not
Gbps). Also fixed two NEW bugs while reviewing images post-generation, both worth
knowing about if editing this file: (a) `fig_utilization()`'s manual info box (this
chart uses `twinx()`, so the shared `viz/info_box.py` helper is unsafe here per the
Phase 3-addendum-#2 lesson) originally sat top-left and visually collided with the
v1.0 bar's `$60.2B` value label — moved to bottom-left AND given an explicit white
`bbox` (the twinx-chart workaround pattern), since bars reach all the way down to
y=0 so ANY x-position at low y still sits inside a bar's colored area; a bbox is
needed for legibility regardless of exact placement. (b) `fig_revenue_per_satellite()`
plotted from `sat_start = start / g.downlink_gbps` where `start` includes a leading 0
— on a log-scale x-axis matplotlib auto-extends below 1 to accommodate that, which
generated minor-tick labels at 0.1/0.01/0.001 that a `:.0f` formatter rendered as
multiple duplicate "0" labels. Fixed with an explicit `ax.set_xlim(1, max_x * 1.15)`
floor — same "log axis needs an explicit nonzero floor" lesson already documented in
`charts/capacity_density.py`, now hit a third time in a different chart. **Also caught
a real scoping bug while fixing this**: `max_x` must be tracked across ALL
generations' loop iterations, not read from `xs` after the loop (which only held the
LAST generation's values — v1.0 has by far the largest satellite count of the three,
so using the wrong generation's max would have clipped its own line off the chart).

**The load-bearing finding, surfaced when the user asked to "analyze the market
ladder for what needs to be explained (knees)"**: the flat ~$8.7B plateau at the very
start of `continuous_cost_vs_market_size.png` (the highest-price end) is NOT
high-income markets, as a reader would reasonably assume. It's exactly the 15
countries hitting `ARPU_CAP_USD_MONTH = 100` (assumption #4 in `ASSUMPTIONS.md`), all
forced to tie at precisely $100/month. Of those 15: 6 are fragile/conflict economies
with implausible pre-cap survey data (Central African Republic, South Sudan, Yemen,
Turkmenistan, Syria, Zimbabwe — $150-437/mo pre-cap, the exact "thin sample size"
problem already flagged in `telecom_market_by_country.md`), the other 9 are tiny
wealthy territories (Bermuda, Cayman Islands, Greenland, Iceland, N. Mariana Islands,
Seychelles, Turks & Caicos, BVI, USVI) where a near-$100 price is plausibly real.
**Net effect: real high-income markets rank BELOW this artifact block.** The US
($80/mo, real data) doesn't crack the top 15 — it enters 16th, and is nonetheless the
single largest individual contributor to total market size ($9.84B, the biggest jump
in the whole curve). Verified by walking `build_country_demand()`'s output directly
(not inferred from the chart) — see the per-country table in this session's
transcript if a fresh session needs to re-derive it.

This also directly answers "are you pricing rural unconnected high-income users
appropriately" — **no, for two separable reasons, not one**: (1) ARPU is a flat
per-country average (mobile or fixed-broadband price) applied to EVERY addressable
person in that country uniformly — no urban/rural split exists anywhere in the model,
so a rural high-income customer (Starlink's actual core value prop: no wired
alternative, willing to pay a premium) is priced identically to their country's urban
average. (2) The one place in the model that superficially LOOKS like a premium tier
(the top of the ARPU ranking) is actually the cap artifact above, actively
SUPPRESSING real high-income countries rather than surfacing them.

**Two candidate fixes were presented to the user, not implemented — an open modeling
decision, do not pick unilaterally**: (A) data-quality fix — stop letting
cap-artifact countries rank at the top; drop them from the ranking or fall back to a
regional-median ARPU instead of the flat $100 ceiling. (B) new mechanism — add an
explicit remote/rural premium multiplier for high-income countries' addressable
population, to actually model the "no-alternative customers pay more" dynamic, which
does not exist in the model in any form today. These are orthogonal: A fixes bad data,
B adds new modeling capability. **Check this section's "answered" status before
re-raising this with the user** — if a fresh session picks this up cold, the
prior turn ended by asking the user to choose A, B, both, or leave flagged; look
for their answer earlier in conversation history before re-asking.

## Affordability analysis: GDP vs GNI, real benchmarks, and cap elasticity (2026-08-09)

User-requested after reviewing Phase 6's ARPU-cap finding. Three deliverables, all
exploratory groundwork for the user's own planned redesign (they said "I'm going to
redesign the model to account for premium remoteness myself" -- this work does NOT
implement that; it's the data/tooling to support their decision).

**New data**: `gdp_per_capita_ppp_usd` column added to `telecom_market_by_country.csv`
(World Bank `NY.GDP.PCAP.PP.CD`, same PPP basis as the existing GNI column, so the two
are directly comparable) via `build_telecom_dataset.py`. Rerun, same 217 rows, no
regressions in the unmatched-country lists.

**New model capability**: `equilibrium_model.build_country_demand()` gained
`income_cap_pct` and `income_basis` params (default `None`/`"gni"` preserves the
original flat `ARPU_CAP_USD_MONTH=100` behavior exactly -- nothing existing changed).
When given, replaces the flat dollar cap with a PER-COUNTRY cap of `income_cap_pct`%
of that country's own monthly GNI (or GDP) per capita -- e.g. at a 2% cap, Bermuda's
real cap becomes ~$150-200/mo (its own high income affords it) while a low-income
country's cap drops well below $100 (correctly tightening on bad survey outliers
instead of letting them all tie at one flat ceiling). Verified: flat cap = 15
countries capped; 2% GNI cap = 74 countries capped, and the specific bad-data
countries flagged in the Phase 6 finding (Zimbabwe, Turkmenistan, etc.) get pulled
DOWN toward something more plausible for their economy, while genuinely wealthy small
territories (Bermuda, Cayman) are allowed to exceed $100 since their real income
supports it.

**Research finding (confirmed via websearch, not assumed)**: the international
affordability-target literature is GNI-based, not GDP-based, specifically because GDP
counts production within a country's borders (inflated by multinational
profit-shifting, e.g. Ireland/Luxembourg) while GNI counts income actually received by
residents -- the right basis for "can a household afford this." Two real published
targets, both UN Broadband Commission / A4AI: **5% of monthly GNI/capita** (original
2011 target) and **2%** (2018 "1 for 2" / 2021 "Journey from 1 to 5" target, the
current standard). Both used as reference lines in the new charts.

**`charts/affordability.py`** -> `results/affordability/` (3 charts):
1. `gdp_vs_gni_per_capita.png` -- log-log scatter, y=x line, colored by region.
   Directly answers "does GDP differ from GNI": yes, materially, for a specific
   handful of economies -- Ireland and Luxembourg sit furthest below the line
   (GDP >> GNI, profit-shifting), Tuvalu/Kiribati/Greenland/Puerto Rico sit above it
   (GNI >> GDP, remittances/transfers). Most countries sit almost exactly on the
   line -- the divergence is a real but NARROW phenomenon, not a universal correction.
2. `connectivity_cost_pct_income_ranked.png` -- ALL 201 priced countries (not top-N),
   ranked by cost as % of monthly GNI/capita, GDP-basis overlaid, against the 2%/5%
   benchmark lines. Finding: 128/201 countries already meet the 2% target using
   today's raw incumbent prices -- the burden is concentrated in a real tail (~30
   countries above 5%, several fragile/conflict economies above 50-300%, an extreme
   outlier near 300%), not spread evenly.
3. `affordability_cap_elasticity.png` -- THE elasticity chart requested: sweeps
   `income_cap_pct` from 0.25% to 25% of GNI/capita (log scale) and re-solves
   equilibrium market size at each of the 4 real generation costs. **Real finding**:
   the curve is steep and still rising through both benchmark lines -- at the 2%
   target, market size is $43.0-45.5B/yr (166-204 countries served depending on
   generation); at 5%, $48.8-50.3B/yr (180-204 countries). Compare to the flat-$100-cap
   baseline's $60.2-61.5B/yr (Phase 5/6) -- **the flat cap was substantially MORE
   generous than either published affordability benchmark**, precisely because it let
   the bad-survey-data outlier countries (Phase 6's finding) inflate the top of the
   curve. A GNI-based cap at either real-world target would shrink modeled market size
   by roughly 18-30% relative to what's shown in every existing equilibrium/Phase 6
   chart. Curves also converge as the cap loosens (generation cost matters less once
   affordability stops binding) and spread apart as it tightens (generation cost
   matters MORE at tight caps, since fewer countries clear the bar at all).

**Two label-collision bugs hit and fixed while building these** (same recurring class
logged multiple times above): Ireland/Luxembourg's text labels overlapped in chart 1
(fixed with a sort-by-x + stagger-if-close heuristic); the y-axis formatter in chart 2
used `:.0f` on a log scale and collapsed every sub-0.5% value to a duplicate "0%"
label (fixed by switching to `:g`, the project's established "no scientific notation,
but also no bad rounding" format per longstanding convention). Also: `viz/info_box.py`
`mode="off", off_side="bottom"` collided with the x-axis label in chart 3 (the shrink-
margin math doesn't account for the xlabel's own space) -- switched to `mode="on"`
instead, which found genuine empty space in the plot itself. **Lesson for next
session**: `mode="off", off_side="bottom"` is riskier than the other three sides
specifically because it competes with the x-axis label for the same space; prefer
`mode="on"` for bottom placement unless the axes has no xlabel.

**Download complete (2026-08-09), still not integrated**: `download_worldpop.py`
(root) finished fetching WorldPop 1km gridded population density GeoTIFFs --
**215/217 countries, 0.82GB total** in `data/raw/worldpop/{iso3}_pd_1km.tif` (far
less than the original ~8.4GB estimate; per-country file size varies enormously with
land area/population). 2 misses, both non-standard territories absent from WorldPop's
own country list, not download failures: Channel Islands (CHI), Kosovo (XKX) -- same
class of gap already hit for pricing data elsewhere in this project. Zero download
errors. Manifest: `data/raw/worldpop/_manifest.csv` (columns: iso3, status, bytes,
detail).

This is STILL a download-only step -- `equilibrium_model.py`'s density-cap logic is
UNCHANGED, still spreading each country's density ceiling over whole land area (the
ASSUMPTIONS.md #6 approximation this data exists to fix). **Next step for whoever
picks up the integration**: for each country, read the GeoTIFF (e.g. via `rasterio`
or `PIL`+manual georeferencing -- neither confirmed installed in this environment,
check first), compute the POPULATED area (cells above some density threshold, or the
area containing the top X% of population) instead of `AG.LND.TOTL.K2`'s total land
area, and swap that into `build_country_demand()`'s `density_ceiling = area *
DENSITY_CAP_PER_KM2` line. Expect this to TIGHTEN the density cap for countries with
concentrated population (Egypt was the flagged example) and barely change it for
already-evenly-spread countries -- don't be surprised if the equilibrium market-size
numbers move down somewhat once this lands.

## Affordability addendum: served/unserved population by cost burden (2026-08-09)

User asked for one more cut: population (served vs. unserved), binned by connectivity
cost as % of monthly GNI/capita, instead of affordability.py's per-COUNTRY ranking.
`charts/served_population_vs_cost.py` -> `results/affordability/served_population_vs_connectivity_cost.png`
(reuses `affordability._raw_arpu` and its two target constants directly rather than
redefining them). Irregular bin edges (`BIN_EDGES` in that file) -- fine near the
cheap end where most population sits, coarse in the expensive tail so sparse bins
still register as real bars.

**Real finding, and a strong one**: unserved share climbs sharply and almost
monotonically with cost burden -- 13-29% unserved under 1% of GNI/capita, up to
66-82% unserved above 3%. The 2% and 5% affordability-target lines sit almost exactly
at the elbow of that climb. This is independent confirmation, from the population
side, of the same story `affordability_cap_elasticity.png` tells from the market-size
side: affordability and connectivity are tightly coupled in this dataset, not two
separate problems. (One non-monotonic wrinkle: the very first bin, 0-0.5%, has HIGHER
unserved% (29%) than the next bin, 0.5-1% (13%) -- not investigated further this
session, plausibly India, whose very cheap mobile $/GB puts it in the lowest-cost bin
despite a large usage-gap "unconnected" population per Phase 1's own already-flagged
metric limitation.)

**Follow-up (2026-08-09, same session)**: user said the binned bar chart was "not at
all what I wanted" and asked instead for a per-country SCATTER of % unconnected vs.
connectivity cost %, with a trend. Added `fig_pct_unconnected_vs_cost_scatter()` to
the same `charts/served_population_vs_cost.py` file (kept the binned chart too --
user said "keep it") -> `results/affordability/pct_unconnected_vs_connectivity_cost_scatter.png`.
200 countries, colored by region, log-x (cost spans 0.1%-300%+), linear-in-log-x
trend fit (`np.polyfit` on `log10(cost%)` vs. `%unconnected`) since a raw-x fit would
be dominated by the few extreme-cost outliers. **Pearson r = 0.59** (log-x vs.
%unconnected) -- a real, moderate positive correlation, visually dominated by
Sub-Saharan Africa (red) at the high-cost/high-unconnected end. **Not yet
investigated**: a horizontal band of points sitting at exactly ~3% unconnected across
many different cost levels -- very likely the `HIGH_INCOME_COVERAGE_FLOOR_PCT=97.0`
correction (ASSUMPTIONS.md #7) creating ties, not a real signal. Worth checking before
citing the r=0.59 figure as precise -- it may be somewhat inflated or deflated by that
artifact banding; not corrected for it this session.

**Follow-up (2026-08-09, same session): UN/A4AI benchmark lines removed at user's
request.** User: "delete that I don't want the UN contaminating my analysis." Removed
`TARGET_2011_PCT_GNI`/`TARGET_2018_PCT_GNI` constants and every reference-line/
annotation using them from `charts/affordability.py` (`fig_cost_pct_income_ranked`,
`fig_affordability_elasticity`) and `charts/served_population_vs_cost.py`
(`fig_served_population_vs_cost`, `fig_pct_unconnected_vs_cost_scatter`). All 5
affected charts regenerated -- **the underlying % cost, elasticity, and correlation
numbers are UNCHANGED**, only the external benchmark annotations were deleted. GNI
(vs. GDP) is still used as the income basis throughout -- that's a basic national-
accounts distinction (income received by residents vs. production within borders),
not itself a UN Broadband Commission construct, so it stayed. **Do not re-add the
2%/5% target lines or cite the UN Broadband Commission / A4AI in this project again
without asking first.**

**Follow-up (2026-08-09, same session): the scatter's trend line is now a
user-specified elasticity model, not a statistical fit.** User liked the scatter but
wanted "a better line for the elasticity": 0.75% cost -> 0% unconnected, 10% cost ->
100% unconnected, linear in log10(cost%) between those anchors and clipped flat to
0%/100% outside them. Replaced the `np.polyfit` regression line in
`fig_pct_unconnected_vs_cost_scatter()` with this anchored line (see
`ELASTICITY_X_LO/HI`, `ELASTICITY_Y_LO/HI` in `charts/served_population_vs_cost.py`).
The Pearson r=0.59 figure is still computed and shown in the info box for context, but
it now describes the SCATTER data, not the plotted line -- the two are independent.
If asked to adjust this again, it's these 4 constants, not a refit.

## Chart title rule made binding at the SKILL level (2026-08-09)

User, reacting to `pct_unconnected_vs_connectivity_cost_scatter.png`'s title ("Does
connectivity cost burden predict how unconnected a country is?"): **chart titles must
describe the axes, never phrase a question or narrate a finding.** This wasn't just a
one-chart fix -- edited the actual `charting-and-modeling` skill source
(`SKILL.md`'s "Chart labelling rules" section, at
`.../skills-plugin/0ed908d5.../skills/charting-and-modeling/SKILL.md` under this
machine's Claude app data) to add it as a **hard requirement**: title format is
`<Y-axis quantity> vs. <X-axis quantity>`, matching the actual axis labels/units, not
a paraphrase or a question. The interpretation/finding belongs in the info box or
surrounding prose, never the title. This applies to every future project that invokes
that skill, not just this one.

**Swept this project's existing charts for violations and fixed 5**:
`served_population_vs_cost.py`'s scatter ("Does connectivity cost burden predict..."
-> "% of population unconnected vs. connectivity cost, % of monthly GNI/capita"),
`affordability.py`'s GDP/GNI chart ("Does GDP per capita differ..." -> "GNI per
capita vs. GDP per capita, PPP, by country"), `population_capacity_overlay.py`'s
normalized overlay ("Does satellite capacity peak where people actually are?" ->
"Normalized satellite capacity and population vs. latitude"),
`capacity_density.py`'s sensitivity chart ("How sensitive is..." -> "Max subscriber
density vs. capacity-model scenario"), and `satellite_cost.py`'s ARK Invest trend
chart ("Satellite bandwidth cost is falling ~7,500x since 2004..." -> "Satellite
bandwidth cost, $/Gbps vs. year"). All charts regenerated except the last one --
**unrelated pre-existing bug found in the process**: `data/starlink_cost_per_gbps.csv`
does not exist on disk (no generator script, no git history -- likely lost, never
actually saved despite being referenced in the Phase 4 section above). The title fix
is in the code but `satellite_cost_per_gbps_trend.png` on disk is stale until that
source file is restored or re-researched. Flagged, not fixed -- out of scope for a
title-convention sweep.

## Known gaps / decisions needed before Phase 5 (do not pick unilaterally)

All four items previously logged here were answered by the user on 2026-08-09 — see
"Phase 4 revision + Phase 1 correction" above for the decisions and what was built
from them. Remaining open items:

- Try to find a second source for the $400K v2 Mini figure and the $40K/Gbps ARK
  Invest figure — both single-sourced as of this research pass.
- Try to find a second source / real capacity figure for v2_full so it can be
  included in the $/Gbps comparison (currently excluded entirely).
- Try to find a real per-country coverage-gap dataset to replace the
  `HIGH_INCOME_COVERAGE_FLOOR_PCT = 97.0` assumption with measured data (ITU
  DataHub and GSMA MCI both inaccessible as of this research pass — see
  `telecom_market_by_country.md`).

## Decisions locked in so far (don't re-litigate these)

- Build order: telecom dataset (Phase 1) before geometry/equilibrium/chart layers —
  user's explicit call, 2026-08-09.
- Geographic granularity: **country-level**, not sub-national — user's explicit call,
  2026-08-09. ~195 units, matches what public datasets actually report at.
- Satellite cost: use public analyst estimates now; swap in user's CSV once provided
  (see Phase 4 note above).
- Market-size-vs-cost output must be a **continuous curve**, not discrete steps —
  user's explicit correction, 2026-08-09, after initially over-anchoring on the
  Terraform market-ladder chart pattern.
- Satellite capacity/customer-density constraints are a **required, separate**
  component (Phase 3) — user's explicit correction, 2026-08-09; do not fold this into
  the cost model or skip it.
- Phase 4 cost metric is **$/Gbps**, not $/satellite — user's explicit call,
  2026-08-09, "hard stop."
- Launch cost pairing: F9 internal marginal cost for v1.0/v1.5/v2 Mini, Starship
  (both "initial" and "end-state" scenarios) for v3 — user's explicit call,
  2026-08-09.
- Per-generation manufacturing cost uses the LATEST known figure only, not an
  average or continuous model — user's explicit call, 2026-08-09 ("Latest").
- Required margin for Phase 5's equilibrium model is **20%** — user's explicit call,
  2026-08-09.
- High-income countries' `unconnected_population_est` is corrected for the
  adoption-vs-coverage-gap issue (97% coverage floor assumption) — user's explicit
  call, 2026-08-09 ("Yes I need correct numbers, obviously"). Every downstream chart
  now uses the corrected column.

## Known gaps / open items

- The satellite cost seed data (Reflect Orbital's sourcing file) has been located
  and used — see Phase 4 section above. Not a gap anymore.
- Unlimited-plan $/GB normalization method not yet decided — must be documented
  explicitly in `telecom_market_by_country.md` once chosen, not silently assumed.

## Next step for whoever picks this up

Phases 1-5 are done. Start **Phase 6 (derived charts)**, but two things first:

1. **Get the user to confirm or replace the two unconfirmed assumptions in
   `equilibrium_model.py`**: `SATELLITE_LIFETIME_YEARS = 5.0` and the
   cross-generation `CUSTOMERS_PER_GBPS` ratio — see "Phase 5" section above for why
   each exists and what changes if they're wrong. These weren't stopped on because
   they're technical parameters rather than the kind of business-strategy call
   (margin, cost metric) the user asked to be looped in on, but they materially
   change every equilibrium number, so surface them explicitly rather than letting
   them sit as buried defaults.
2. **Reconcile Phase 5's equilibrium satellite counts against Phase 3's physical
   capacity ceiling** before building Phase 6's utilization chart — Phase 5 answers
   "what's revenue-maximizing," not "is it buildable," and Phase 3 already showed
   the full current fleet caps out around ~73M customers globally, far below what
   several of Phase 5's equilibria imply. The utilization chart (satellites vs.
   addressable market $ vs. utilization %) is exactly where this belongs — build it
   as the reconciliation, not just another independent chart.
3. Then: the continuous cost-vs-market-size curve (sweep more finely than 4
   generation points — `cost_per_gbps_model.py` and `equilibrium_model.py` are both
   already structured as reusable functions, so this should mostly be re-running
   them across a finer cost grid rather than new modeling) and the final
   revenue-per-satellite-by-orbit chart.

## WorldPop world-map heatmap chart (2026-08-10)

New session, user request: re-download the gitignored `data/raw/worldpop/` GeoTIFFs
(a fresh container has none — see the "Download complete" note in the Phase 6
section above) and produce an actual population-density heatmap of the world from
them. Re-running `download_worldpop.py` reproduced the exact same **215/217**
result as the original run (CHI, XKX permanently absent from WorldPop's own country
list — not a network issue, confirmed by retrying those two alone to a clean
`no_data` status after transient connection resets cleared on retry).

**New environment dependency, not yet formalized as a requirements file**: this
container had NO scientific Python stack at all (no numpy/matplotlib/pip packages
beyond stdlib). Created a project-local `.venv/` (already covered by the repo's
`.gitignore` `.venv` entry, nothing to add) with `numpy`, `matplotlib`, `tifffile`,
`imagecodecs`. **Deliberately did NOT add `rasterio`/GDAL** — WorldPop's GeoTIFFs are
plain unprojected WGS84 rasters with simple `ModelPixelScaleTag`/`ModelTiepointTag`
georeferencing, so `tifffile` + manual tag parsing was enough and avoids a heavy
GDAL binary dependency. **A future session must `source .venv/bin/activate` (or
recreate it) before running any chart in this project** — nothing was installed
system-wide.

**New module: `population_density_grid.py`** (root) — mosaics the 215 independent,
unaligned per-country GeoTIFFs into one global 0.1deg lon/lat grid.
`SRC_DEG = 1/120` (WorldPop's native "1km" pixel) divides evenly into
`TARGET_DEG = 0.1` (`BLOCK = 12`), so downsampling is exact block-averaging, no
resampling/interpolation. Each country is read, NaN-masked (`GDAL_NODATA = -99999`),
block-reduced (tiny territories smaller than one block keep native resolution
instead of vanishing), then scatter-accumulated (sum + count, i.e. a true weighted
mean) into the shared grid via direct floor-division indexing — deliberately NOT
`np.searchsorted` on the descending latitude-edges array, which is a sign-convention
trap (caught before shipping, not after). Result cached to
`data/raw/worldpop/_grid_cache_0.1deg.npz` (inside the already-gitignored worldpop
dir) since the full mosaic takes ~1 minute — **always call
`load_or_build_grid()`, never `build_global_grid()` directly**, so a chart rerun is
instant.

**Sanity check run, not printed on the chart itself**: integrating the grid's
density x per-cell area (accounting for `cos(latitude)` cell-width shrinkage) back
out to a global population total gives **~8.85B**, vs. WorldPop's actual ~7.9B
(2020) — about 10-12% high, expected order of magnitude for a coarse 0.1deg
block-mean (mixed land/ocean coastal cells get averaged over valid land pixels only
but multiplied by the FULL cell area, biasing coastal/archipelago cells upward).
Good enough as a visual heatmap; **do not use this grid for a quantitative
population total** without correcting for that bias first — Phase 5/6's actual
demand model still uses whole-country `AG.LND.TOTL.K2` land area, not this grid (see
the still-open density-cap integration step logged in the Phase 6 section above).

**New chart: `charts/population_density_map.py`** ->
`results/population/population_density_heatmap.png`. Reuses
`coverage_map.load_land_paths()` / `draw_world_basemap()` directly (imported via a
second `sys.path.insert` of the `charts/` dir itself, since `charts/` has no
`__init__.py` and isn't a package) rather than duplicating the basemap code.
`pcolormesh` + `LogNorm` (population density spans 1 to ~48,200 people/km2 — linear
would show almost nothing), `plasma` colormap with `cmap.set_bad(alpha=0)` so
below-floor (`DENSITY_FLOOR = 1` person/km2) and no-data cells are fully transparent
and the grey land basemap shows through uninhabited land instead of leaving a hole.
Colorbar ticks set explicitly via `FuncFormatter` (the project's established
LogNorm-colorbar-ticks fix — see the edge-case catalog in the `charting-and-modeling`
skill; the default `LogFormatter` renders literal `$\mathdefault{10^n}$` otherwise).
Title follows the project's binding "vs. axes" rule even though this is a 2D map,
not a scatter: "Population density (people/km2) vs. longitude and latitude".

Visual result matches expectation: Nile valley, Ganges/Indus plains, Java, the
NE-US/BosWash corridor, and coastal China are the brightest (highest-density)
regions; Sahara, Amazon interior, Siberia, and central Australia render fully
transparent (below the 1 person/km2 floor) with the bare land basemap showing
through.

**Not yet done**: this is a **visualization-only** artifact, same status as the raw
GeoTIFF download itself — `equilibrium_model.py`'s density-cap logic is still
unchanged (whole-country land area, not populated area). If a future session
integrates the WorldPop data into the model per the Phase 6 "Next step for whoever
picks up the integration" note above, `population_density_grid.py`'s per-country
block-reduced arrays (before global-mosaic accumulation) are the natural building
block for a per-country "populated area above threshold X" function — don't
re-parse the GeoTIFFs a second time with a different approach.

## Serviceable-customers model: the actual density-cap integration (2026-08-10, same session)

Same session as the heatmap above. User asked for the integration step flagged as
"not yet done" just above -- immediately, same day -- plus a population-vs-latitude
refresh, population-vs-density histograms, and a data-resolution sensitivity check
(1km vs 100m). Built in this order:

**New module: `serviceable_customers_model.py`** (root) -- the actual integration.
Combines three previously-separate pieces for the first time:
`orbital_geometry.expected_sats_by_latitude()` (Phase 2), `capacity_density_model.py`'s
TWO Phase 3 caps (max customers/satellite -- an aggregate SUPPLY ceiling that grows
with satellite count N; max customers/km2 -- a per-area DEMAND ceiling, independent
of N), and `population_density_grid.py`'s real gridded population (replacing Phase
5/6's whole-country-land-area approximation with actual per-cell density).

Key modeling choices, all deliberate:
- **Shell split is a rough 3-inclination stand-in (45/65/80deg, ratio 5:1:1), per
  the user's explicit instruction** -- NOT `starlink_shells.csv`'s precise Gen1
  geometry (53.0/53.2/70.0/97.6deg). Fractional satellites per shell at any N (the
  same "expected value" treatment `orbital_geometry.py` already uses elsewhere), all
  three shells share one fixed altitude (`scenario.altitude_km`, 550km) for
  consistency with the Phase 3 capacity scenario, not real per-generation altitudes.
- **The min() of supply vs. demand is taken PER 1deg LATITUDE BAND, then summed --
  NOT on the two global totals.** Applying it globally would let satellite-capacity
  surplus at a sparse latitude (e.g. 80deg) silently "cover" a shortfall at a dense
  one (e.g. 30deg), which satellites can't actually do. This is the same
  finest-available-granularity principle as Phase 5's per-country min(), just at
  latitude-band granularity here (grid-cell granularity isn't possible since the
  orbital model only resolves latitude, not longitude).
- **The demand-side ceiling (density-capped population by latitude) is
  N-INDEPENDENT** (coverage extent is fixed by the widest shell, 80deg, regardless of
  N) **and is computed ONCE per sweep**, not per N -- `sweep_serviceable_customers()`
  relies on this for speed (a handful of seconds for a 40-point sweep, ~215-country
  grid).

**Real bug caught and fixed before shipping, in BOTH `population_density_grid.py`
and `serviceable_customers_model.py`**: the latitude-to-bin-index formula was
`(90 - lat) / bin_width`, which MIRRORS north and south (maps the north pole to
bin 0, which is actually the array's southernmost bin). Caught by eye: the first
`population_by_latitude_gridded.png` draft showed the huge India/China population
peak in the SOUTHERN hemisphere at -26deg, which is obviously wrong (real peak
~26-30deg NORTH). Fixed to `(lat + 90) / bin_width` in both files. **Important
downstream finding**: this bug did NOT change `serviceable_customers_model.py`'s
actual totals, because satellite capacity-by-latitude is symmetric around the
equator (pure orbital mechanics, no hemisphere preference) -- mirroring which
population value pairs with which (symmetric) capacity value doesn't change the sum.
Only the standalone latitude chart's display was actually wrong. Don't assume that
generalizes to a future asymmetric capacity model, though -- re-check this
invariant if shell altitudes/inclinations ever become hemisphere-asymmetric.

**New shared functions added to `population_density_grid.py`** (not duplicated
per-caller, per the skill's rule #1): `row_areas_km2()` (per-latitude-row cell area,
cos(lat)-scaled), `cell_population()`, `population_by_latitude()`. Also two new
single-raster loaders, used for the US-only work below:
`load_country_density_grid(iso3)` (reads one country's 1km tif directly, own
lon/lat edges, no global-grid mosaicking/quantization) and
`load_population_count_raster_as_density(path)` (converts a WorldPop *count* raster
-- people PER PIXEL, e.g. the 100m "ppp" product -- to density by dividing by each
pixel's own geographic area; the 1km product is already density, no conversion
needed there).

**New charts**:
- `charts/population_stats.py` -> `results/population/`: `population_by_latitude_gridded.png`
  (replaces the old capital-city-proxy chart with real gridded data -- multi-peaked,
  matches real geography much more precisely than the single-point-per-country
  version) and `population_vs_density_histogram_{global,us}.png` (log-x histogram,
  population summed into log-spaced density bins; global median ~687/km2, US median
  ~1,081/km2 -- log-spaced `DENSITY_BIN_EDGES` from 0.1 to ~126,000/km2).
- `charts/serviceable_customers_chart.py` -> `results/population/serviceable_customers_vs_satellites_global.png`:
  log-log sweep from 100 to 2,000,000 satellites. Shows the expected ramp-then-
  saturate shape -- linear growth on log-log until satellite capacity exceeds the
  local density-capped population ceiling, then flattens at **~1.13B customers**
  globally (density-capped population within the 80deg coverage envelope). Gen1
  (4,408) and current-fleet (~10,900) marked as vertical reference lines, both still
  on the steep/linear part of the curve. (An early cross-check claimed N=4,408 gave
  ~29.6M, "matching" Phase 3's original finding almost exactly -- **that was against
  the buggy pre-fix code below and is superseded**; see the bug writeup for the
  corrected value.)

## CRITICAL BUG, found and fixed same day: np.fmin silently zeroed out the whole density cap (2026-08-10)

User asked a sharp follow-up question ("isn't that beam density for one satellite?")
that led to re-examining the model, which surfaced a real, serious bug in
`serviceable_customers_model.py`'s core capping step -- **affecting every
serviceable-customers number shipped earlier the same day**, not just the
in-progress US 100m work.

**The bug**: `_capped_population_per_row()` and the streaming variant both used
`np.fmin(density, max_density_cap)` to clamp density to the cap. `np.fmin` has a
specific, easy-to-miss NaN behavior: **it IGNORES NaN and returns the other
operand** (`np.fmin(nan, cap) == cap`, not `nan`). Every no-data cell -- ocean, or
any land not covered by a country's WorldPop raster -- was silently converted into
"a cell at exactly the density cap" instead of contributing zero. For the GLOBAL
grid, where ~70% of the array is ocean (NaN), this is enormous: `nansum` no longer
excludes those cells (they're not NaN anymore after `fmin`), so the ceiling was
inflated by roughly `cap x total_ocean_area`.

**How it was caught**: not by inspection -- by the numbers not adding up. The 100m US
streaming run (see below) produced a "density-capped population" of 392M for the
US, which is mathematically IMPOSSIBLE: `capped_total` can never exceed
`cap x total_valid_land_area` (a hard upper bound from the min() itself), and the
US's real land area (~9.33M km2, cross-checked directly from the working 1km grid)
x the 2.57/km2 cap caps out at ~24M. Getting 392M -- 16x over the hard ceiling --
meant the arithmetic itself was broken, not just an assumption being generous.
Traced to the exact `fmin`-vs-`minimum` distinction via a sampled diagnostic pass.

**Fix**: `np.fmin` -> `np.minimum` (`minimum` propagates NaN as an operand should),
in both `_capped_population_per_row()` (grid.py's whole-array path) and
`density_capped_population_by_latitude_streaming()`'s in-place chunk loop. One-line
fix in two places, but the numeric impact is large:

| Quantity | Buggy (fmin) | Fixed (minimum) |
|---|---|---|
| Global density-capped ceiling | 1.13B | **188.6M** |
| Global serviceable @ N=4,408 (Gen1) | 29.6M | **24.5M** |
| Global serviceable @ N=10,900 (current fleet) | (not separately reported) | **55.8M** |
| US 1km density-capped ceiling | (not separately reported pre-fix) | **8.20M** |
| US 100m density-capped ceiling (streaming) | 392.1M (impossible) | recomputed after fix, see below |

`results/population/serviceable_customers_vs_satellites_global.png` was already
committed with the WRONG (1.13B-ceiling) numbers -- **regenerated and recommitted
with the fix**. Anyone reading the earlier commit's chart or this same day's earlier
CLAUDE.md text (the "1.13B ceiling," "99.7% of population lives above the cap,"
Gen1-matches-Phase-3 claims) should treat those specific NUMBERS as superseded by
this table; the MECHANISM description (per-latitude-band min of supply vs. demand,
shell ratios, etc.) is unaffected -- only the NaN-handling bug, not the modeling
logic itself, was wrong.

**Lesson for future numeric code in this project**: `np.fmin`/`np.fmax` are almost
never what you want when NaN means "excluded/no-data" rather than "a real value to
compare." Default to `np.minimum`/`np.maximum` (which propagate NaN) unless you have
a specific, deliberate reason to want NaN-skipping comparison behavior -- and if you
do use fmin/fmax on an array that can contain structural NaN (not measurement noise),
that's worth a comment explaining why the skip is intentional.

## US 1km vs. 100m resolution comparison (2026-08-10, same day, after the bug fix above)

`data/raw/worldpop/usa_ppp_2020_100m.tif` downloaded successfully (WorldPop's `wpgp`
"Unconstrained individual countries 2000-2020, 100m resolution" product,
`usa_ppp_2020.tif`, exactly 4,011,468,120 bytes as declared by the server --
confirmed via the same `hub.worldpop.org` REST API used by `download_worldpop.py`,
category `pop`, alias `wpgp`; the `pop_density` category only exposes 1km products,
hence needing a different category/alias for 100m). **This file is a population
COUNT product ("ppp" = people per pixel), NOT density** -- unlike the 1km product,
values must be divided by each pixel's own geographic area to get people/km2;
`load_population_count_raster_as_density()` / the streaming aggregator handle this.

**Too large to load whole**: 62,976 x 430,711 pixels, ~101GB uncompressed as
float32. Added `population_density_grid.open_raster_zarr()` (tifffile's zarr store,
tile-decode-on-demand) and
`serviceable_customers_model.density_capped_population_by_latitude_streaming()`
(row-chunked accumulation, never holding more than one chunk in memory).

**First streaming attempt OOM-killed** (exit 137) at `row_chunk=2048`: each chunk's
divide/fmin(now minimum)/multiply sequence allocated a FRESH full-size array at
every step (~4x the ~3.5GB chunk size = ~14GB, on a 15GB box). Fixed by mutating the
chunk buffer in place at every step (`out=chunk` on divide and minimum, `chunk *=
area_col`) and dropping to `row_chunk=512` (one tile-row, ~881MB/chunk) -- peak
memory now ~1x chunk size. Clean run: ~570s (~9.5 min) with `row_chunk=512`.

**Two full streaming runs were needed**: the first (memory-safe) run completed but
used the still-buggy `fmin` code (392.1M result, caught as impossible per the bug
section above); re-run after the `minimum` fix, giving **6.8M** for the 100m ceiling
(vs. **8.2M** for the same country at 1km, from the ALREADY-fixed whole-grid path --
a real, moderate **-17%** difference from using finer input data). Directionally
sensible: finer resolution resolves more small-scale density peaks that individually
exceed the cap and get clipped, which 1km's coarser averaging partially smooths away
-- so finer data should generally push the capped ceiling DOWN, not up, and it did.
Chart: `results/population/serviceable_customers_vs_satellites_us_1km_vs_100m.png`.

**One more bug, caught immediately after, same root-cause family (log-axis
formatting, not NaN this time)**: the US comparison chart's y-range (~200K to ~8M,
under 2 decades) was narrow enough that matplotlib auto-enabled MINOR tick labels,
which bypassed the chart's `set_major_formatter`-only fix and rendered literal
`$\mathdefault{6\times10^{6}}$` text -- the global chart's wider range (several
decades) never triggered this, so it shipped clean and hid the issue. Also: the
info box's one long unwrapped line was implicated in a `constrained_layout not
applied because axes sizes collapsed to zero` warning and a squished/cut-off box.
Fixed BOTH at the shared level (`_format_log_axes()`, applied to every chart in this
file, not just the one that showed the symptom) rather than patching the one chart
-- add `ax.yaxis.set_minor_formatter(mticker.NullFormatter())` alongside the major
formatter on any log-scale numeric axis in this project going forward, and keep
info-box text to short wrapped lines per the project's existing convention.

**Open question flagged mid-session, since answered**: the density cap (2.57
customers/km2) is a SINGLE BEAM's footprint limit; the fixed-cap model applies it as
a hard per-area ceiling independent of satellite count N, correctly matching
`capacity_density_model.py`'s original documented Phase 3 assumption. User's answer:
**"make it so that the density limit is only per satellite, make this another set of
charts (not replacing the old ones)."** Built as a genuinely separate model variant,
not a change to the existing one -- see the next section.

## Per-satellite density cap: a SECOND model variant, new charts (2026-08-10, same day)

New, separate curve family answering the open question above: instead of a FIXED
areal density cap, the cap now scales PER SATELLITE -- `effective_cap(lat, N) =
base_cap x sats_overhead(lat, N)`, i.e. each satellite overhead a latitude band
independently contributes its own beam-footprint allowance, so more satellites
raises the local areal ceiling too, not just the aggregate per-satellite capacity
ceiling (which already scaled with N in the original model). **The original
fixed-cap model and its charts are UNCHANGED** -- this is purely additive, per the
user's explicit instruction not to replace the old charts.

**New model code, all in `serviceable_customers_model.py`** (not a separate file --
shares `make_shells`/`max_latitude_covered`/etc. with the fixed-cap model, so it
lives alongside it under a clearly-marked "Per-satellite density cap variant"
section):
- `sats_overhead_by_latitude()` -- extracted from `capacity_by_latitude()` (a
  behavior-preserving refactor, verified: N=4,408/10,900 give byte-identical results
  to before) so both the aggregate-capacity supply curve AND the new per-satellite
  cap scaling read the same underlying satellites-overhead-by-latitude quantity.
- **Why a histogram, not a direct recompute**: the fixed-cap model could compute its
  (N-independent) demand ceiling ONCE per sweep, since the cap never changed. Here
  the cap changes at EVERY N, and re-reading the raw raster per N is not an option
  (the 100m file alone takes ~10 min per PASS, x46 sweep points would be ~7.5
  hours). Instead, `density_area_histogram_by_latitude()` (in-memory) and
  `..._streaming()` (100m, same row-chunked/in-place-mutation pattern as the
  existing streaming aggregator) build a (latitude band x density bin) AREA
  histogram ONCE -- `DENSITY_BIN_EDGES`, 59 log-spaced bins, 0.01 to ~200,000/km2.
  `capped_population_from_histogram()` then re-applies ANY cap value against that
  histogram as a cheap array op, no raw-data re-reads needed for the rest of a sweep.
  Cross-checked: summing the histogram's own (bin_center x area) reproduces the
  known raw population totals closely (global: 8.89B from the histogram vs. 8.85B
  from the exact grid sum, US 1km: consistent within the same small binning-
  approximation error) -- confirms the histogram isn't silently losing population.
- `serviceable_customers_per_satellite_cap()` / `sweep_per_satellite_cap()` mirror
  the fixed-cap model's `serviceable_customers()` / `sweep_from_pop_cap()` signature
  shape, taking a precomputed histogram instead of a precomputed scalar ceiling.

**Real, expected finding**: at low N the two models are nearly identical (both
dominated by the aggregate capacity constraint, not the density cap, at low
satellite counts). They diverge sharply once satellites overhead a band exceed ~1
-- the fixed-cap curve saturates at 188.6M (unchanged from before) while the
per-satellite curve keeps climbing, approaching **~8.9B (raw population)** by
N~5-10M satellites. This is the direct, correct answer to the earlier "why doesn't
the ceiling go to 8B" question **under this new assumption** -- with a per-satellite
cap, given enough satellites the areal constraint stops binding anywhere and the
model becomes purely population-limited, same as the user originally expected
before the fixed-cap assumption was explained.

**New charts, `charts/serviceable_customers_per_satellite_chart.py`** (imports
shared helpers -- `_draw_curve`, `_format_log_axes`, `_pop_formatter`,
`_add_fleet_reference_lines`, `SOURCE_NOTE`, `SHELL_RATIO_NOTE` -- directly from
`charts/serviceable_customers_chart.py` rather than duplicating them; `_draw_curve`
gained an optional `linestyle` param, default `"-"`, so the OLD chart file's calls
are behavior-unchanged):
- `serviceable_customers_vs_satellites_global_per_satellite_cap.png` -- fixed cap
  (dashed) vs. per-satellite cap (solid) overlaid, global, 1km data.
- `serviceable_customers_vs_satellites_us_per_satellite_cap.png` -- 4 curves:
  {1km, 100m} x {fixed, per-satellite}, US only. Needs a SECOND streaming pass over
  the 100m US raster (`density_area_histogram_by_latitude_streaming()`, cached to
  `data/raw/worldpop/_us_100m_density_area_hist.npz`) -- the earlier streaming cache
  (`_us_100m_pop_cap_by_lat.npz`, a single scalar-per-latitude-band ceiling) isn't
  enough for this variant since the cap now needs re-applying at every N.

**Layout bug hit a second time, same root cause as the earlier US 1km-vs-100m
chart**: an overlong single-line info-box string triggered the same
`constrained_layout not applied because axes sizes collapsed to zero` /
squished-plot symptom. Fixed the same way -- shorter, explicitly wrapped lines. Two
occurrences of the identical bug class now on record; keep info-box text short by
default rather than rediscovering this a third time.

## Real Starlink shell data (correcting the rough ratio) + linear-axis charts (2026-08-10, same day)

User, on seeing the per-satellite-cap chart: **"I didn't mean use literally my rough
ratio use the real Starlink satellite plane data."** The earlier "5:1:1 at
45/65/80deg" shell split (introduced when this whole serviceable-customers model was
first built) was meant as a rough verbal description of Starlink's shape, NOT a
literal instruction to invent a 3-shell stand-in -- correctly read now as: use
`data/starlink_shells.csv`'s real Gen1 geometry, already loaded elsewhere in this
project via `orbital_geometry.load_shells_with_full_geometry()`.

**Real shells are very different from the rough guess**: 5 sub-shells, NOT evenly
spread across 45/65/80deg -- 71.8% combined at 53.0/53.2deg, 16.3% at 70.0deg, 11.8%
at 97.6deg (near-polar), 4,408 satellites total. Max latitude covered by the union
is 82.4deg (the near-polar shell), vs. the rough model's 80deg -- barely changes the
fixed-cap ceiling number (still 188.6M at the displayed precision).

**Model refactor in `serviceable_customers_model.py`**: `make_shells()` (rough
ratio, deleted) -> `real_shells()` (loads the real CSV) + `scale_shells_to_total()`
(scales EACH real shell's plane count proportionally to hit any target N, preserving
its own true altitude/inclination -- no longer one shared synthetic altitude for all
shells). Every function that took a `ratios=SHELL_RATIOS` param now takes
`base_shells=None` (defaulting to `real_shells()`) instead -- `sats_overhead_by_latitude`,
`capacity_by_latitude`, `max_latitude_covered`, `serviceable_customers`,
`sweep_from_pop_cap`, `sweep_serviceable_customers`, `serviceable_customers_per_satellite_cap`,
`sweep_per_satellite_cap`. **All 6 previously-shipped serviceable-customers chart
PNGs were regenerated** with real shells (this is a correction to a wrong input
assumption, not a new/additive chart set like the per-satellite-cap variant was --
the old rough-ratio numbers were simply wrong and are not preserved anywhere).

**User's second question, answered with the actual numbers**: *"I'm surprised by it
being linear on the log-log graph, I'd expect diminishing returns much faster."*
Real mechanism, verified by computing `served(N)/N` directly: while EVERY latitude
band's satellite-derived capacity is still below its own local density-capped demand
ceiling (the constellation is capacity-bound, not demand-bound, ANYWHERE), total
capacity(N) = N x customers_per_satellite x (a fixed, N-independent sum of per-shell
time-fractions) -- an EXACTLY linear function of N, hence a perfectly straight
log-log line. This held almost exactly with the old rough-ratio model (`served/N`
was constant at ~6,704, the exact customers-per-satellite figure, from N=100 to
N~40,000). **With REAL shells the ratio is NOT constant** -- it declines steadily
from ~6,249 at N=100 down to ~1,622 by N~116,000 -- because the real shells are
UNEVENLY weighted (72% at 53deg vs. 11.8% near-polar), so different latitude bands'
demand ceilings get "used up" at very different rates relative to their real
orbital-driven satellite supply, causing earlier, more gradual visible curvature
than the toy model showed. **The deeper reason the bend is gradual rather than a
sharp knee either way**: the model has no mechanism to preferentially route
additional satellites toward still-undersupplied bands vs. already-saturated ones --
every additional satellite is distributed across ALL bands in the same fixed
orbital-mechanics-determined proportions, so the aggregate curve stays dominated by
the still-capacity-bound majority of bands until MANY individual bands have
saturated, not just the first one.

**New linear-axis chart variants added** (per user request, following the existing
`equilibrium.py` precedent of log-log + linear versions of the same chart): for the
3 chart families most relevant to this discussion --
`serviceable_customers_vs_satellites_global_linear.png`,
`serviceable_customers_vs_satellites_global_per_satellite_cap_linear.png`,
`serviceable_customers_vs_satellites_us_per_satellite_cap_linear.png`. **NOT** simply
reusing the log chart's `geomspace` sample points on a linear axis -- that would put
almost all 40 points in a dense cluster near zero and leave the visually-important
knee/saturation region sparse; each linear chart uses its own `np.linspace(0, MAX,
200)`, with `MAX` sized to that specific curve's own saturation point (looked up
numerically first, not guessed): 160K for the global fixed-cap-only chart, 7M for
the global fixed-vs-per-satellite comparison (per-satellite's own ceiling is far
later than fixed-cap's), 1.2M for the US comparison. Did NOT add a linear version of
the plain US 1km-vs-100m fixed-cap-only chart (`serviceable_customers_chart.py`) --
not requested, add if wanted.

**Cosmetic bug caught while reviewing the new linear charts, fixed at the shared
level**: `_add_fleet_reference_lines()` (Gen1 4,408 / current fleet ~10,900) used the
same vertical text offset for both labels, which worked fine on log-axis charts
(the two lines are visually far apart there) but overlapped into unreadable garbled
text on the wide-range linear charts (7M/1.2M axis, where 4,408 and 10,900 are both
essentially "at the left edge"). Fixed with a per-label vertical stagger
`[(4,-4), (4,-70)]` so the two labels never collide regardless of how close the
lines are in x -- applies to every chart using this helper, not just the ones that
showed the symptom, per this project's now well-established "fix shared helpers
once" convention.

## Servable population DENSITY vs. satellite count (2026-08-10, same day)

User: "Give me servable population density vs sat count." Distinct metric from
everything built so far in this file's model -- not a customer COUNT, but the
per-area density CEILING (people/km2) itself, as a function of N. Read as: extend
the per-satellite-cap mechanism (`effective_cap(lat, N) = base_cap x satellites
overhead that band`) into its own chart, showing the ceiling's growth directly
rather than folding it into a customer total.

**New model functions in `serviceable_customers_model.py`**:
`effective_density_cap_by_latitude()` -- the density-counterpart of
`capacity_by_latitude()` (which does the same thing for the aggregate capacity cap);
factors out the `base_cap x sats_overhead` line that was previously inlined only
inside `serviceable_customers_per_satellite_cap()`. `effective_density_cap_at_latitudes()`
samples that array at specific latitudes (nearest 1deg bin) -- for a chart that
tracks a handful of representative latitudes across a satellite-count sweep, rather
than the full per-band array at one N.

**New chart**: `charts/serviceable_customers_per_satellite_chart.py` gained a third
figure, `fig_servable_density_vs_satellites()` -> `results/population/servable_density_vs_satellites.png`.

Also re-sent (not regenerated -- unchanged since the Phase/session that built them)
`population_vs_density_histogram_global.png` and `_us.png`
(`charts/population_stats.py`) per the user's request to see them again.

**Revised same day, right after shipping**: first version plotted 5 representative
latitudes (0/30/53/70/80deg) as separate lines. User: **"don't make it a series of
latitudes, just use one for the Starlink profile."** Correct call -- an arbitrary
5-latitude sample isn't "the Starlink profile," it's 5 disconnected cuts through it.
Replaced with `effective_density_cap_profile_average()`: a single
satellites-overhead-WEIGHTED average across ALL covered latitude bands (weight =
`sats_overhead(lat, N)`, the same quantity the constellation actually distributes
satellites by) -- "the effective ceiling a typical satellite in this real
constellation supports," collapsing the whole shell profile into one honest number
instead of 5 arbitrary ones. `effective_density_cap_at_latitudes()` (the sampling
helper the first version used) was deleted along with it -- no longer had a caller,
and per this project's "no dead code" convention, an unused sampling helper doesn't
get kept around "in case it's useful later."

**Linear version added right after** (user: "Linear version please"):
`fig_servable_density_vs_satellites_linear()` -> `servable_density_vs_satellites_linear.png`.
Same x-range as the log-log version (0-2,000,000, for direct comparability) via
`np.linspace` (not `geomspace` -- this curve has no saturation point to size a
tighter range around, unlike every other linear chart in this project so far; it's
an exactly-proportional straight line in N by construction, since it's a weighted
sum of quantities each proportional to N). Legend placed `loc="lower right"` --
`"upper left"` collided with the Gen1 reference-line label, which sits right at the
y-axis on a chart where the line rises from the origin (unlike the serviceable-
customer charts, where "upper left" is genuinely empty because those curves start
near zero and only rise slowly at first).

## Why the serviceable-customers derivative doesn't match the density histogram, and the latitude saturation heatmap (2026-08-11)

User asked why d(serviceable customers)/dN isn't the same shape as the population-
vs-density histogram, given the servable-density curve is exactly proportional to N.
Investigated by splitting the per-latitude-band shortfall (`raw pop - served`) by
WHICH constraint binds, at several N (quick ad hoc script, not saved as a chart):

| N | total shortfall | supply-bound | density-cap-bound |
|---|---|---|---|
| 2,000,000 | 2,961M | 2,960M | 1.2M |
| 3,000,000 | 1,453M | 1,453M | 0M |
| 5,000,000 | 137M | 137M | 0M |

**Real finding: the density cap stops binding almost everywhere by ~N=2M.** From
there to full saturation (~N=6M), essentially 100% of the remaining shortfall is
AGGREGATE-CAPACITY-bound (`customers_per_satellite x satellites_overhead`), which
has NOTHING to do with per-cell density. The servable-density chart (a single
satellite-weighted-average number) was never the right quantity to explain this
tail -- it only describes the density-cap side, and that side stopped mattering long
before saturation.

**The actual mechanism**: the single most populous 1-degree latitude band on Earth
is **26.5N** (South Asia -- India/Bangladesh, ~279M people, matches the peak in
`population_by_latitude_gridded.png` exactly). Real Starlink shells concentrate 72%
of satellites at **53N**, for reasons unrelated to population. Checked directly:
aggregate supply at 26.5N reaches only 17% of that band's population at N=1M, 51% at
N=3M, 98.5% at N=5.8M -- **it takes ~5.8-6M satellites for aggregate capacity over
ONE latitude band to catch up with its own population**, and that's essentially the
whole tail of the global curve. Not "spread out," not really "density" either --
a mismatch between where satellites concentrate (orbital-mechanics-driven) and
where people actually live (demographics-driven).

**New model functions**: `served_fraction_by_latitude()` / `sweep_served_fraction_by_latitude()`
in `serviceable_customers_model.py` -- served population as a FRACTION of each
band's own raw population, at one N (or swept across many N into an (N x latitude)
grid). NaN (not 0) where a band has zero population, so it reads as "no data" in a
heatmap rather than "0% served."

**New chart, brainstormed with the user then built on request ("Heat map!")**:
`charts/latitude_saturation_heatmap.py` -> `results/population/latitude_saturation_heatmap.png`.
y=latitude, x=satellite count (log), color=% of that band's population served
(viridis, grey=no population in that band). This is the chart that finally answers
"why doesn't a map show this" -- it isn't a spatial story, it's a latitude x N
story. **Visually striking and immediately legible**: near-polar bands (~75-82deg,
sparse population) turn yellow almost instantly; a slow diagonal "wave" sweeps down
through the temperate latitudes as N grows; the ~20-30deg band (both hemispheres,
especially +26N/South Asia) is the very last sliver to turn yellow, right at the
edge of the plot (~N=6-8M) -- a direct visual match to the numbers above. Annotated
directly on the chart: dashed reference lines at 53N (shell concentration) and
26.5N (South Asia peak), plus the existing Gen1/current-fleet vertical lines.
One small but correct edge-case surfaced by the chart itself: a thin dark band right
at ~82.5-83N (just outside the 82.4deg coverage limit) has some population but stays
permanently at 0% served -- never colored grey (which would wrongly imply zero
population there) nor yellow (since it's outside every shell's coverage).

## Two follow-ups, same day: log-color heatmap + north-up population chart (2026-08-11)

**1. Log-color heatmap version** ("Make another version of that heatmap with log
Color map"). The linear 0-100% color scale crushes almost all of the interesting
low-%-served structure into uniform dark purple -- most of the heatmap's real
story (0.01% vs 1% vs 10% served) is invisible on a linear scale. Refactored
`charts/latitude_saturation_heatmap.py` to share a `_draw_saturation_heatmap()`
helper between two thin figure functions (`log_color=False`/`True`), rather than
duplicating the pcolormesh/annotation/axis code -- only the norm and colorbar
ticks/formatter actually differ. `LogNorm` can't take exact 0, so 0%-served cells
are clipped up to a `LOG_COLOR_FLOOR = 1e-4` (0.01%) before plotting; NaN
(no-population) cells are masked BEFORE the clip so they stay grey, not
misrepresented as "0.01% served". Colorbar ticks are explicit + `FuncFormatter`,
not LogNorm's default formatter -- the same `$\mathdefault{...}$` bug from the
`charting-and-modeling` skill's edge-case catalog, now hit a second time on a
colorbar (first time was `population_density_map.py`'s heatmap). **Hit the
established "overlong info-box line" layout bug a third time** while building this
-- one line concatenated `SHELL_RATIO_NOTE + SOURCE_NOTE` onto an already-long
line with no separating `\n`; fixed by giving it its own line, per the same pattern
now documented twice already above. Output: `latitude_saturation_heatmap_log.png`.

**2. North-up population-by-latitude chart** ("population as the x axis and
latitude as y axis... humans usually see north as up"). Added
`fig_population_by_latitude_horizontal()` to `charts/population_stats.py` --
literally the same data as `fig_population_by_latitude()` (same
`pdg.population_by_latitude()` call), just `fill_betweenx` instead of
`fill_between` and the axes swapped; y-axis is latitude ascending (-90 at bottom,
+90 at top) with NO inversion needed, since "north up" is naturally satisfied by
plain ascending order once latitude is the y-axis (unlike this project's other
latitude-on-x charts, which all need `invert_xaxis()` to put north on the left).
**Hit the SAME overlong-info-box-line bug a 4th time**, this time triggered by the
narrower portrait `figsize=(8.5, 10.5)` (a line that fit fine in the usual
11-12in-wide landscape figures didn't fit here) -- fixed the same way, explicit
`\n` per line. Output: `population_by_latitude_horizontal.png`. **Lesson now
recorded 4 times in this file**: always default new info-box calls to short,
explicitly-`\n`-wrapped lines (2-4 words each is safest) rather than letting a
line's length depend on how wide happens to be convenient at the call site --
narrower figures (portrait charts, multi-panel, etc.) shrink the safe margin
further than the landscape charts most of this project's history was built with.

## Satellite ground-coverage RANGE geometry + two new charts (2026-08-11)

User: satellite-density-by-latitude only counted satellites whose SUB-SATELLITE
POINT sits exactly at a given latitude -- asked for how far a satellite can
actually SERVE to the sides ("horizontal field of view"), researched from real
Starlink analyses, applied to that chart, then overlaid on population-by-latitude.

**Researched, not guessed** (WebSearch): Starlink's long-standing minimum user-
terminal elevation angle is **25 degrees**. Checked whether the FCC's 2026-04 STA
ruling (lowers the minimum to 10deg <400km, 20deg 400-500km, 5deg above 62N)
changes this for this project -- it doesn't: Gen1's real shells are all >=540km,
above every lowered tier, so 25deg remains the applicable figure. New
`ASSUMPTIONS.md` #11 entry.

**New geometry in `orbital_geometry.py`** (standard LEO visibility geometry, law of
sines on the Earth-center/satellite/ground-station triangle -- not a beam-footprint
calculation, a DIFFERENT concept from `capacity_density_model.py`'s ~163 km2 single
-beam footprint): `off_nadir_angle_deg()`, `ground_range_angular_radius_deg()`,
`ground_range_km()`. **Self-derived formula cross-validated against two
independently published figures for the 550km shell**: 25deg -> 941km computed vs.
"~900km" cited; 40deg (kept as `ALT_MIN_ELEVATION_DEG`, a stricter alternative from
a different source) -> 574km computed vs. "~580km" cited -- both matched closely,
confirming the derivation before it fed any chart.

**`expected_sats_reaching_latitude()`**: the range-extended satellite-density
function -- a satellite at latitude L covers [L-R, L+R] where R is ITS OWN shell's
coverage radius (real shells differ 540-570km, so R differs slightly per shell,
~927-968km / ~8.3-8.7deg). Implemented as a boxcar convolution (sum, not average)
of each shell's `expected_sats_by_latitude()` histogram -- deliberately NOT a
2D (lat x lon) treatment, a stated 1D latitude-marginal simplification consistent
with this module's other latitude-only treatments (documented in the function's
own docstring, not hidden). Total across all bins is no longer conserved at 4,408
(by design -- each satellite now counts toward every bin it can reach, ~17x the
raw total summed).

**New chart file `charts/satellite_range_coverage.py`** (2 figures, NOT replacing
`coverage_map.py`'s original overhead-only satellite-density chart):
1. `satellite_density_by_latitude_with_range.png` -- overhead-only (the original
   Phase 2 metric) vs. range-extended, same axes, both visible. **~6x difference at
   peak** (144 overhead vs. 870 range-extended at ~46-52deg) -- and the
   range-extended curve is visibly SMOOTHED/BROADENED relative to the sharp
   overhead-only spikes, exactly as expected from convolving with an ~8.5deg-wide
   window.
2. `satellite_range_vs_population_by_latitude.png` -- range-extended satellite
   density overlaid on population-by-latitude, twin y-axis, shared latitude x-axis.
   **Confirms and sharpens the same finding from the saturation-heatmap section
   above, from a completely different angle**: population peaks at 26deg (South
   Asia), satellite reach peaks at 46deg -- a 20-degree gap between where people are
   and where satellites concentrate, visible directly as two non-aligned peaks on
   one chart, no model math required to see it.

**Follow-up, same day: area fills -> bar charts.** User: the underlying data is
discretely binned by 1deg latitude (`BIN_WIDTH_DEG = 1.0`, unchanged since Phase 2),
so a smooth `fill_between`/`fill_betweenx` visually implies continuous
interpolation between bins that isn't real. Converted to `ax.bar()`/`ax.barh()`
(`width`/`height=1.0`, `align="center"`) in all 4 charts using this pattern:
`fig_population_by_latitude()`, `fig_population_by_latitude_horizontal()` (both
`charts/population_stats.py`), and both figures in
`charts/satellite_range_coverage.py`. Twin-axis chart 2's satellite curve stays a
LINE, not bars -- it's the range-EXTENDED (convolved/smoothed) series, and
bars-on-bars on a twin axis reads worse than bars+line. **Also answered**: 1deg
binning itself is NOT a listed `ASSUMPTIONS.md` entry -- it's a computational
resolution choice (`BIN_WIDTH_DEG`), not a real-world numeric assumption the user
needs to confirm/override, and nothing in this project has tested sensitivity to a
coarser/finer bin width.

**Second follow-up, same day: orientation fix.** User: "These graphs have flipped
axis to what I want / North = highest latitude = y axis top." Both
`charts/satellite_range_coverage.py` figures still used the OLDER latitude-on-x
(`invert_xaxis()`) convention from Phase 2, unlike `population_by_latitude_horizontal.png`
which already had it right (built two follow-ups ago). Flipped both to match:
`ax.bar()` -> `ax.barh()` (portrait `figsize=(9, 11)`, `ax.set_ylim(-90, 90)`, no
inversion needed -- ascending order already puts north at the top). The twin-axis
chart needed `ax1.twiny()` instead of `ax1.twinx()` since latitude is now the
SHARED axis (y) and each series gets its own independent x-axis instead of y --
satellite series plotted as `ax2.plot(ext_total, sat_centers, ...)` (values first,
latitude second, matching twiny's x-varies/y-shared convention). Left
`population_by_latitude_gridded.png` (the original vertical, latitude-on-x chart)
unchanged -- it already has a correctly-oriented sibling
(`population_by_latitude_horizontal.png`), so "fixing" it would just create a
duplicate of that chart under a different name.

## Range-extended satellite counts for the per-satellite density-cap term (2026-08-12)

User asked: "Do we have to regenerate the heatmaps with the new sat FOV?" -- the
new range-extended satellite-density geometry from the previous session
(`orbital_geometry.expected_sats_reaching_latitude()`) existed but the
per-satellite-cap model (`serviceable_customers_model.py`) still computed its
areal density cap from OVERHEAD-ONLY satellite counts
(`sats_overhead_by_latitude()`), not the range-extended ones -- an inconsistency
between the new geometry and the model that uses it. Before touching anything,
worked out which of the model's TWO satellite-count terms should actually change:

- **Areal density-cap term** (`base_cap x sats`, in `effective_density_cap_by_latitude()`):
  range-extension is VALID here. Different satellites reaching the same ground
  spot can each independently contribute their own beam allowance -- that's the
  whole premise of the per-satellite-cap model (more satellites overhead/reachable
  = more simultaneous beam capacity available at that spot).
- **Aggregate capacity term** (`customers_per_satellite x sats`, in
  `capacity_by_latitude()` and the supply side of `served_fraction_by_latitude()`
  / `serviceable_customers_per_satellite_cap()`): range-extension is INVALID here.
  A satellite has ONE finite customer-capacity budget. Counting it toward every
  latitude its coverage circle reaches (not just its own sub-satellite point)
  would multiply-count that budget -- the same satellite serving 6,704 customers
  claimed simultaneously at both 40deg and 50deg, which isn't physically real (a
  satellite's total capacity is shared across whichever users it actually talks to
  at once, not duplicated per latitude band it merely CAN reach).

Presented this distinction to the user via `AskUserQuestion`; they confirmed
"Yes, use range-extended (recommended)" for the density-cap term specifically,
leaving the capacity term untouched.

**Changes in `serviceable_customers_model.py`**:
- New `sats_reaching_latitude()` -- thin wrapper around
  `og.expected_sats_reaching_latitude()`, the range-extended counterpart to the
  existing `sats_overhead_by_latitude()`. Docstring states the validity split above
  so a future reader doesn't "fix" the two terms to match each other.
- `effective_density_cap_by_latitude()` now calls `sats_reaching_latitude()`
  instead of `sats_overhead_by_latitude()`.
- `effective_density_cap_profile_average()` simplified: instead of a second,
  redundant range-extension pass to build its weight array, it now reuses
  `effective_density_cap_by_latitude()`'s own output as the weight (mathematically
  identical, since `cap = base_cap x sats` is a constant multiple that cancels in
  the weighted-average ratio).
- `serviceable_customers_per_satellite_cap()` and `served_fraction_by_latitude()`
  (the function driving the saturation heatmaps) both now call
  `effective_density_cap_by_latitude()` for the demand/density side and keep their
  own separate, unchanged `sats_overhead_by_latitude()` call for the
  supply/capacity side -- previously both functions inlined ONE shared
  `sats_overhead_by_latitude()` call for both terms, which is exactly the
  conflation this fix corrects.

**Numeric sanity check at N=4,408 (Gen1)**: peak overhead satellite count is
~144 (at 52.5deg); peak range-extended (reaching) count is ~870 (at 45.5deg,
shifted -- a wider window pulls the peak toward the broader mid-latitude mass, not
just the sharpest overhead spike). Range-extended >= overhead everywhere covered,
as required. `effective_density_cap_profile_average(4408)` moved from a much
smaller overhead-weighted figure to **~1,464 people/km2** (base cap 2.57/km2 x
~570, i.e. roughly the range-extended-to-overhead ratio) -- makes the areal
density cap dramatically less binding than before, which is the physically
correct direction: a user can be served by ANY satellite whose coverage circle
reaches them, not only one exactly overhead, so the true local capacity was being
understated pre-fix.

**Downstream effect on the saturation heatmaps**: confirms the user's implicit
question -- yes, they needed regenerating, and the answer to "why" is that the
model itself (not just a display change) was recomputed. Because the density term
is now far less binding, the heatmaps show saturation happening EARLIER (lower N)
across most latitude bands than before -- consistent with, and reinforcing, the
"aggregate-capacity-bound, not density-bound" finding from the previous session's
heatmap section: with the density cap loosened further, capacity is left as an
even more clearly dominant bottleneck for the long tail of the curve.

**Regenerated** (all via their normal chart scripts, not by hand):
`serviceable_customers_vs_satellites_global_per_satellite_cap.png` (+ `_linear`),
`serviceable_customers_vs_satellites_us_per_satellite_cap.png` (+ `_linear`),
`servable_density_vs_satellites.png` (+ `_linear`), `latitude_saturation_heatmap.png`,
`latitude_saturation_heatmap_log.png`. Also fixed now-stale info-box/docstring
wording in `charts/serviceable_customers_per_satellite_chart.py` that still said
"satellites-overhead-weighted" for the servable-density chart's averaging --
updated to "range-extended-satellites-weighted" to match the actual mechanism.
