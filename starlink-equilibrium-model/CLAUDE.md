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

## Market ladder chart (2026-08-23, new session, user said the existing one wasn't satisfactory)

User asked for "another market ladder analysis" -- explicitly pointed at the Terraform
Industries blog post
(https://terraformindustries.wordpress.com/2026/06/16/the-enormous-size-of-the-oil-and-gas-market-drives-adoption-of-synthetic-fuel-production/)
and `Terraform-Market-Ladder/terraformer_market_ladder.py` as the pattern to copy, and asked
specifically for **v3 satellites**, **$/capacity/year vs. cumulative capacity**, with the
**same dual-x-axis formatting** as that script (`ax.secondary_xaxis("top", functions=(...))`,
bottom axis in the base unit, top axis relabeled in a second physical unit).

**What "the existing one" meant**: `charts/phase6.py`'s `continuous_cost_vs_market_size.png`
-- the chart CLAUDE.md's own Phase 6 section already logged as the one the user previously
asked to "analyze ... for what needs to be explained (knees)". That chart sweeps COST as a
free parameter (x = $/Gbps/year, y = $B/year captured) -- useful for the cost-vs-market
sweep, but it's not actually shaped like Terraform's ladder (price vs. cumulative volume) and
has no per-country/step detail at all, just one smooth swept curve.

**What was built**: `charts/market_ladder.py` -> `results/market_ladder/v3_market_ladder.png`
-- NEW chart, no model changes. It renders `equilibrium_model.build_revenue_curve()`'s
existing output (already computed for Phase 5/6, unchanged) as an actual descending
staircase, Terraform-ladder style:
  - x (bottom, log): cumulative capacity deployed, Gbps. x (top, secondary axis): cumulative
    v3 satellites, converted via v3's 1,024 Gbps/satellite (`data/satellite_capacity.csv`,
    `v3_broadband` row) -- this is why the chart is v3-only: that Gbps/satellite ratio is
    generation-specific, so the same secondary axis wouldn't mean the same thing for v1.0/v2
    Mini.
  - y (log): $/Gbps/year -- the ARPU-implied annual revenue rate per Gbps, i.e. the actual
    per-country "price" already computed in the revenue curve.
  - The staircase itself is all 204 countries' real steps (a `LineCollection`, plasma_r
    gradient by rank) -- NOT binned into synthetic tiers the way Terraform had to invent
    "markets" for substitution fuels. This project's standing "must be continuous, not
    discrete tiers" rule (Phase 6, above) was specifically about the swept-cost chart; it
    doesn't forbid drawing the real per-country granularity as a staircase here, since these
    steps are the actual data, not an artificial binning choice.
  - Only 7 of the 204 steps get individual labels (`HIGHLIGHT_COUNTRIES` in the script) --
    the biggest REAL markets by volume, spread across the full curve: Norway, United States,
    Mexico, Brazil, China, India, Fiji (floor). Labeling all 204 is unreadable; labeling more
    (Argentina/Russia/Nigeria/Indonesia were tried and cut) just crowds the one log-decade
    they all sit in without adding a materially different data point.
  - The 15 countries tied at the flat `ARPU_CAP_USD_MONTH=100` cap (the Phase 6 "artifact
    plateau" finding -- Bermuda, Central African Republic, ... -- see Phase 6 section above)
    are merged into ONE labeled block instead of 15 individual annotations, with the label
    explicitly calling it a cap artifact, not real pricing, pointing back at this file.
  - Both v3 cost scenarios (Starship "initial" $352/Gbps/yr and "end-state" $305/Gbps/yr,
    5yr life + 20% margin, `cost_per_gbps_model.py`) are drawn as dashed reference lines.
    **Both sit BELOW the entire demand ladder** (cheapest real country, Fiji, is
    $737/Gbps/yr -- more than 2x even the pricier v3 scenario) -- visual confirmation, on
    this chart, of the same Phase 5 finding that at v3-class cost, revenue/demand is not the
    binding constraint; the model runs out of modeled countries (204/204 served) before cost
    ever becomes the limiter.

**Bug hit and fixed while building this** (same recurring class as elsewhere in this
project): the "China" label's offset was small enough that its own text box, drawn on top
(higher zorder) after the dot+leader-line pass, fully occluded both -- looked like a floating
label with no connection to the curve. Not caught by looking at the chart as a whole, only by
cropping and zooming the rendered PNG region-by-region. Fixed by giving China a larger
offset. **Lesson for any future per-point annotation in this project**: a small
offset-in-points label can visually swallow its own anchor dot/leader when the box is drawn
above it in z-order -- worth a zoomed crop check per labeled point, not just a full-chart
glance, especially in a crowded region of the plot.

Also hit the already-documented "log axis needs an explicit nonzero floor" bug class a second
time in this file's own session: the secondary top axis's default `:,.0f` formatter rounded
every satellite count below 0.5 to a duplicate "0" near the left edge. Fixed by formatting
values under 10 satellites with one decimal instead of rounding to an integer, AND by setting
an explicit x-axis floor (200 Gbps, just under the $100-cap block's marker) rather than
starting at the true data minimum (~2 Gbps, Bermuda) -- the first few countries are
individually tiny and already summarized inside that block's label, so extending the axis
down to them added only visual noise, not information.

## Market ladder chart revision: decluttered + multi-generation cost lines + linear version (2026-08-23, same day)

User reviewed the chart above and asked for it simplified: delete the "serves all X/204
modeled countries" text from each cost line's note, delete the info-box's "Staircase: ...
Dashed lines: ..." paragraph, delete the "N countries at $100/mo ARPU cap" artifact-block
label, remove the highlighted-country labels entirely (Norway/US/Mexico/Brazil/China/
India/Fiji + their dot markers and leader lines), add reference lines for the OTHER
Starlink generations this project has cost data for (not just v3), and add a linear-axis
version alongside the log-log one (matching the `charts/equilibrium.py` precedent).

**What changed in `charts/market_ladder.py`**: `_draw_highlights()` (+ `HIGHLIGHT_COUNTRIES`,
`LABEL_OFFSETS`, `_DEFAULT_OFFSET`) and `_draw_artifact_cap_block()` deleted outright, not
just their text -- an unlabeled marker dot with nothing to explain it would have been worse
clutter than what it replaced. `_fmt_dollars()` deleted too (dead code once both callers were
gone). The `info_box.add_info_box()` call and its `param_text` paragraph deleted; the `viz`
import narrowed to just `render`. `_draw_v3_cost_lines()` renamed to `_draw_cost_lines()` and
generalized: it now takes the FULL `cost_per_gbps_model.build_generation_economics()` output
(v1.0, v2 Mini, both v3 scenarios -- the only 4 generations this project has $/Gbps data for;
v1.5 and v2_full are still excluded project-wide for the data-availability reasons already
documented in `cost_per_gbps_model.py`), not just the v3 subset, and no longer computes/prints
`em.find_equilibrium()` results at all (that was the "serves all X/Y" text being deleted). New
`GEN_COST_COLORS` dict replaces the old v3-only `V3_COST_COLORS`: blues for the older, more
expensive-per-Gbps generations (`v1.0` `#313695`, `v2 Mini` `#4575b4`), reds kept for v3
(`#8c1a10`/`#d73027`, unchanged from before). The secondary top x-axis stays
v3-only (satellite-count conversion still only makes sense for v3's 1,024 Gbps/sat), per the
module docstring's existing reasoning -- unaffected by this change.

**Chart-drawing code refactored into a shared `_draw_ladder(ax, points, econ,
v3_downlink_gbps, *, log_scale: bool)`**, called by two thin wrappers,
`fig_market_ladder_log()` (unchanged output filename, `v3_market_ladder.png`) and the new
`fig_market_ladder_linear()` (`v3_market_ladder_linear.png`) -- same `figures()`/`main()`
loop-and-save pattern as `charts/equilibrium.py`, for consistency with that file's existing
log+linear precedent in this project.

**Real bug caught and fixed before shipping, not just a cosmetic tweak**: the first attempt at
multi-generation cost-line labels used per-line `ax.annotate()` text anchored at each line's
own y-position with a fixed point-offset -- fine for the old 2-line (v3-only) chart, but with
4 lines it garbled illegibly on the linear-axis version specifically. Root cause: on a linear
y-axis spanning $0-$90K, all four generation costs ($5,074 / $2,564 / $352 / $305) sit within
~6% of each other near y=0 -- their DATA positions are all nearly identical in pixel terms, so
a per-line point-offset stacking scheme (tried first, using a log-distance-aware "how close in
rendered space" heuristic) still collided, because the offset was being added on top of
already-near-identical base positions rather than replacing them. **Fixed by switching to
`ax.legend()`** (each `axhline()` given a `label=`, one `ax.legend(loc="lower right")` call
instead of manual per-line text placement) -- a legend box lays out N labels in a fixed
vertical stack regardless of how close their underlying data values are, sidestepping the
whole collision problem rather than tuning around it. Confirmed by rendering both chart
versions and visually inspecting: log version's legend cleanly lists all 4 generations in the
previously-empty lower-right corner (freed up by deleting the country highlight labels);
linear version, where all 4 lines visually bunch up near y=0 as expected (documented in the
module docstring as an inherent linear-scale tradeoff, same caveat pattern as
`equilibrium.py`), now has a fully legible legend instead of overlapping text.

**Environment note for whoever runs this next**: this container had no scientific Python
stack at all (no matplotlib/numpy, no pip, no apt/sudo access, no `python3 -m venv` ensurepip
support) -- different from the "already has a project `.venv`" state some earlier CLAUDE.md
entries describe; that `.venv` did not exist here. Rebuilt it: `python3 -m venv --without-pip
.venv`, bootstrapped pip via `curl -sL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3
-`, then `.venv/bin/python3 -m pip install matplotlib numpy`. Run charts with
`.venv/bin/python3 charts/<script>.py`, not bare `python3`.

## Market ladder: widest-bars-labeled image + linear legend moved to top-right (2026-08-23, same day)

Two more small requests on the same chart, same session. (1) User asked for the 4 LONGEST
horizontal bars (i.e. the 4 countries with the widest `end - start` Gbps span in the
staircase -- a capacity-size cut, not a $/Gbps-price cut) labeled, **on a separate new image,
not merged into the already-decluttered main chart**. (2) After seeing
`v3_market_ladder_linear.png`, asked for that chart's cost-line legend moved from bottom-right
to top-right (bottom-right is where all 4 lines themselves bunch up on the linear axis, so a
bottom-right legend sat on top of the data it was labeling).

**Widest-4 computed directly from `equilibrium_model.build_revenue_curve()`'s existing
output**, sorted by `end - start` (not by revenue or by hand-picked "biggest real market"
judgment like the deleted highlight labels used) -- came out to **United States (146,829
Gbps), Brazil (307,915 Gbps), China (345,863 Gbps -- the single widest step), India (109,533
Gbps)**. Notably NOT the same set as the deleted `HIGHLIGHT_COUNTRIES` list (Norway, Mexico,
Fiji dropped; this is capacity-width, not price-decade-spread). New
`_draw_widest_bar_labels(ax, points, n=4)` in `charts/market_ladder.py`, same dot + leader-line
+ text-box visual language as the deleted `_draw_highlights()`, but labels now state the
step's WIDTH (`{end-start:,.0f} Gbps wide`) instead of ARPU -- the thing actually being
highlighted here. New `fig_market_ladder_widest_labeled()` -> a THIRD, separate output file,
`v3_market_ladder_widest_bars_labeled.png`; the plain log and linear charts are untouched, per
the user's explicit "don't replace existing" instruction. Registered in `figures()` /
`main()` alongside the other two, so a full `python charts/market_ladder.py` run now produces
3 PNGs, not 2.

**Legend location**: `_draw_cost_lines()` gained a `loc` param (default `"lower right"`);
`_draw_ladder()` now passes `loc="lower right" if log_scale else "upper right"` -- the log
chart's legend stays where it already worked (empty lower-right corner since the country
labels were deleted), only the linear chart's moved.

## Market ladder: labeled the capped-block "first bar", then legend -> inline labels (2026-08-23, same day)

Three more follow-ups on the same image set, same session.

**(1) "Label the first one too."** Read as: on `v3_market_ladder_widest_bars_labeled.png`,
also label the flat $100/mo-ARPU-cap plateau (the 15 merged countries described in the Phase 6
section above) -- it's the first, leftmost bar a reader's eye lands on, and on a LOG x-axis it
visually reads as the single longest bar in the whole image (spans ~2.7 of the plot's ~4.4
visible decades) even though its raw Gbps width (104,219) is smaller than each of the 4
countries already labeled by the widest-4-by-raw-width metric. New
`_draw_capped_block_label()`, same dot+leader+textbox style, called after
`_draw_widest_bar_labels()` in `fig_market_ladder_widest_labeled()` -- this image only, per the
same "separate image, don't touch the plain charts" scoping as the original widest-bars ask.

**(2) Cost-line labels moved from a legend box to inline text embedded just above each
line** -- left side on the log chart, user initially asked for right side on the linear chart,
then simplified to "nvm ... put the labels on the left [for linear too] and delete v3 starship
end state label as it overlaps." `_draw_cost_lines()` reworked: draws each `axhline()` first
(unlabeled), then a separate pass places `ax.annotate()` text at a fixed x-fraction (0.015
left-aligned) with a real PIXEL-based collision-avoidance stack (see bug below), and takes a
new `skip_labels` param -- `_draw_ladder()` passes `skip_labels=("v3 (Starship end-state)",)`
on the linear chart only (the log chart keeps all 4 labels; its v3 pair is legible without
skipping anything). The `v3 (Starship end-state)` DASHED LINE itself is still drawn on the
linear chart, only its text label is omitted.

**Real bug hit and fixed while building the pixel-stacking pass**: the first version stacked
labels TOP-DOWN in descending-cost order (push each subsequent, lower-cost label down by a
minimum pixel gap if it collides with the previous one). This works fine when there's open
space below the lowest line, which is true on the log chart -- but badly wrong on the linear
chart, where all 4 lines sit within a few pixels of the y=0 axis floor (confirmed by printing
`ax.transData.transform()` pixel coordinates directly: the axis floor itself was at pixel
y=68.75, and the v3 end-state/initial lines were at y=72.5/73.1 -- under 5px of real room
below them). Stacking downward from there pushed the lowest label PAST the axis floor,
overlapping both the other label and the axis border -- confirmed visually by cropping and
zooming the rendered PNG (same "don't just eyeball the whole chart, zoom the specific region"
lesson logged earlier this file, re-earned here). **Fixed by reversing the stacking direction
entirely**: process ASCENDING by cost (lowest/bottom-most line first) and push each
SUBSEQUENT, higher-cost label UPWARD if it would collide -- building the stack away from the
crowded axis floor and into the open space toward `y_hi`, which always has room regardless of
scale. General lesson for any future pixel-based label stacking in this project: stack away
from the nearest boundary, not in a fixed direction chosen for one scale and assumed to work
for both. This fix alone would have resolved the log-chart-first design intent too, but the
user's simplification (drop the one label that still didn't fit) landed before it needed
testing against that specific case.

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

## Deleted superseded vertical-orientation charts (2026-08-13)

User asked to delete non-horizontal (latitude-on-x) chart versions now that a
north-up (latitude-on-y) sibling exists showing the same data. Checked every file
in `results/population/` for such a pair -- only one exists:
`population_by_latitude_gridded.png` (`fig_population_by_latitude()`, latitude-on-x,
`invert_xaxis()`) vs. `population_by_latitude_horizontal.png`
(`fig_population_by_latitude_horizontal()`, latitude-on-y, north-up) in
`charts/population_stats.py` -- same underlying data
(`pdg.population_by_latitude()`), same info-box content, genuinely redundant once
the horizontal version existed. (The `charts/satellite_range_coverage.py` pair
does NOT have this problem -- those two figures were converted to horizontal IN
PLACE in an earlier follow-up, not duplicated, so there was never a separate
vertical file left behind for them.)

Deleted `fig_population_by_latitude()` from `charts/population_stats.py` (not just
the PNG -- per this project's no-dead-code convention) and its entry in
`figures()`; `git rm`'d `results/population/population_by_latitude_gridded.png`.
Verified no other file in the project referenced this function or filename
(`charts/population_capacity_overlay.py` has an unrelated same-named function that
writes a different chart, `population_by_latitude_served_unserved.png`, to
`results/capacity/` -- left untouched, not part of this cleanup).

## Retired the fixed (single-satellite) density-cap model from every chart (2026-08-13)

User: "We have too many servicable density graphs" -- asked for exactly 3 chart
pairs (log + linear each, 6 files total): density vs. satellites, global customers
vs. satellites, US 1km-vs-100m customers vs. satellites. Also, explicitly: "No fake
single-satellite density cap's either" -- the FIXED-cap model (areal beam-footprint
density cap held constant regardless of constellation size N,
`capacity_density_model.py`'s original documented assumption) had been charted
throughout this project as a dashed "vs." comparison against the newer per-satellite
(range-extended) model. The user's point: holding the density ceiling at what ONE
satellite's beam footprint can deliver, no matter how many satellites actually cover
a spot, doesn't reflect how the real constellation works -- charting it as a live
comparison read as implying it was an equally valid alternative, not what it is.

**Consolidated from 11 chart files down to 6** (all under
`charts/serviceable_customers_per_satellite_chart.py` now, single source of truth):
1. `servable_density_vs_satellites.png` / `_linear.png`
2. `serviceable_customers_vs_satellites_global.png` / `_linear.png`
3. `serviceable_customers_vs_satellites_us_1km_vs_100m.png` / `_linear.png`

Deleted (superseded, `git rm`'d): the old fixed-cap-only
`serviceable_customers_vs_satellites_global.png`/`_linear.png`/`_us_1km_vs_100m.png`
content (filenames REUSED by the per-satellite model's output, not deleted as
filenames -- see below), plus the now-redundant
`serviceable_customers_vs_satellites_global_per_satellite_cap.png`/`_linear.png`
and `_us_per_satellite_cap.png`/`_linear.png` (their content moved to the reused
filenames above, `_per_satellite_cap` suffix dropped since it's the only model now).

**`charts/serviceable_customers_chart.py` gutted to a shared-helpers-only module**
(no more `figures()`/`main()`/PNG output of its own) -- kept because
`charts/latitude_saturation_heatmap.py` and the per-satellite chart file both still
import its formatting/reference-line helpers (`_pop_formatter`,
`_add_fleet_reference_lines`, `_draw_curve`, `_format_log_axes`, `GEN1_SATS`,
`CURRENT_FLEET_SATS`, `SHELL_RATIO_NOTE`, `SOURCE_NOTE`); its docstring now explains
the retirement instead of describing charts it no longer produces.

**`charts/serviceable_customers_per_satellite_chart.py` rewritten**: every dashed
fixed-cap comparison curve, `CAP_NOTE`, and the density chart's "Fixed cap" `axhline`
removed. Global/US customer charts now show ONE real curve each (US chart still has
its two legitimate curves -- 1km vs. 100m population data resolution, a genuine
data-quality comparison, not a fake-vs-real model comparison). Info boxes reworded
to reference each curve's own raw-population ceiling (a true asymptote, not a
"cap") instead of the old fixed-cap ceiling number. Also dropped the now-unused
`US_100M_POP_CAP_CACHE` dependency (`_us_100m_pop_cap_by_lat.npz`, only ever fed the
fixed model's `sweep_from_pop_cap`) -- only `US_100M_DENSITY_HIST_CACHE`
(`_us_100m_density_area_hist.npz`) is needed now.

**Explicitly verified "everything uses the new FOV model"** while doing this (the
user's other ask): grepped every caller of `sats_overhead_by_latitude` vs.
`sats_reaching_latitude` across the project. Confirmed `effective_density_cap_by_latitude()`
(the density term, used by every remaining chart via `sweep_per_satellite_cap()` /
`effective_density_cap_profile_average()`) is range-extended
(`sats_reaching_latitude()`, Starlink's real ~25deg min-elevation FOV geometry);
`capacity_by_latitude()` (the aggregate term) stays overhead-only, correctly, since
that's a different, unaffected constraint. `charts/satellite_range_coverage.py`'s
two figures already used the range-extended geometry directly (not through the
demand model) since the session that built them -- unaffected either way. The
FIXED model's own functions in `serviceable_customers_model.py`
(`serviceable_customers()`, `sweep_serviceable_customers()`, `sweep_from_pop_cap()`,
`density_capped_population_by_latitude()` + its streaming variant) were left in
place, not deleted -- they're still a legitimate, well-documented alternate
scenario (the X-Lab paper's own original assumption) and the module's own
`if __name__ == "__main__":` demo still calls `sweep_serviceable_customers()` for a
quick CLI table; they're just no longer charted, which is what "fake" meant here --
charted as if a live comparison, not the code existing at all.

## Fixed a real bug: spurious 0%-served band at 82-83deg on the saturation heatmap (2026-08-13)

User spotted a purple (near-0%) horizontal bar around 81-82deg on the latitude
saturation heatmap and correctly called it erroneous. Root cause, found by
numerically dumping `served_fraction_by_latitude()`'s inputs latitude-by-latitude
near the boundary: `capacity_by_latitude()`, `effective_density_cap_by_latitude()`,
`served_fraction_by_latitude()`, and `serviceable_customers_per_satellite_cap()`
all applied a hard `covered = abs(centers) <= max_latitude_covered()` mask (82.4deg,
the near-polar shell's true limit) ON TOP OF the already-correctly-bounded
satellite-count data. The 1deg bin centered at 82.5 (spanning 82.0-83.0) has its
CENTER just past the 82.4 cutoff, so the mask zeroed the ENTIRE bin -- even though
its lower half (82.0-82.4) is genuinely reachable, has real satellite overhead
(verified: 7.2 sats at N=4,408, growing to 13,120 at N=8M) AND real population
(913 people, from the WorldPop grid). Result: that one bin showed 0% served at
EVERY N, when it should show ~100% (same as its neighbors).

**The fix, not a patch**: `og.latitude_density()` computes
`lat = degrees(arcsin(sin(i) * sin(u)))`, and `|arcsin(x)| <= 90` with
`|sin(i)*sin(u)| <= sin(i)` ALWAYS holds exactly (an identity, not a statistical
approximation from the Monte Carlo sampling) -- so `sats_overhead_by_latitude()`
and `sats_reaching_latitude()` are ALREADY exactly zero-bounded to each shell's
true coverage limit, with no separate mask needed. Confirmed numerically: the
83.5 bin (fully beyond 82.4) shows `overhead=0.000` at every N tested, exactly as
expected with no mask at all. **Removed the redundant-and-wrong `covered` masking
entirely** from all 4 functions above, instead of trying to hand-tune a
bin-edge-aware cutoff -- the natural data was already correct, the mask was the
only thing making it wrong. Deleted `max_latitude_covered()` itself too (zero
remaining callers after the fix, confirmed via repo-wide grep).

Verified the fix numerically before touching any chart: at N=4,408/100K/8M, the
82.5 bin now reads `frac=1.0` (was `0.0`); the 83.5 bin correctly still reads
`0.0` (genuinely beyond the polar shell's reach, not a bug); 84.5+ correctly reads
NaN (no population there, greys out on the heatmap, not "unserved"). Regenerated
`latitude_saturation_heatmap.png`/`_log.png` (visually confirmed the purple bar is
gone) and, for consistency, the per-satellite-cap serviceable-customers charts
(numbers moved negligibly -- the US charts came out byte-identical, since the US
grid has no population above ~72degN, well short of the affected 82-83deg band).

Left `lat_centers` in `served_fraction_by_latitude()`'s and
`serviceable_customers_per_satellite_cap()`'s signatures even though neither
function consumes it internally anymore (it was only ever used to build the now-
deleted mask) -- every caller already has the array on hand from the same
histogram call, and removing the parameter would mean touching 6 call sites across
2 chart files for a purely cosmetic gain. Documented in both functions'
docstrings so it doesn't read as an oversight.

## Deleted the original Phase 2 satellite-density-by-latitude chart (2026-08-13)

Same "delete the old, less-complete chart once a better one exists" pattern as
the `population_by_latitude_gridded.png` deletion earlier this session. Found via
a repo-wide audit (compared every `OUT_ROOT / "...png"` filename referenced in
`charts/*.py` against what's actually inside `results/*/`): `charts/coverage_map.py`'s
`fig_satellite_density_by_latitude()` produced `results/coverage/satellite_density_by_latitude.png`
-- Phase 2's original overhead-only, per-shell-stacked chart. Now that
`charts/satellite_range_coverage.py`'s `satellite_density_by_latitude_with_range.png`
(built this session) shows the same overhead-only total AND the range-extended
total overlaid, the old chart's only remaining unique content was the per-shell
color breakdown -- judged not worth keeping a whole separate, now-partially-
redundant chart file for. Deleted the function, its `figures()` entry, the PNG,
and the now-unused `mticker` import; `fig_coverage_bands()` (the world-map chart,
unaffected) and its shared `INCLINATION_COLORS` dict stay.

## Deepened the 25deg minimum-elevation-angle sourcing + new sources doc (2026-08-13)

User pushed back on the citation: "That 25 degree number is not official from
Huston, unless it cites a source but I can't see one, look harder into it." Then,
before a response was ready: "Ah I found the source in the paper." Re-fetched and
extracted raw text from Geoff Huston's actual PDF slides (not just a summary) to
confirm: correct, slide 5 states the 25deg figure as a bare fact with no visible
citation. Traced one level deeper to Shkelzen Cakaj's 2021 Frontiers in
Communications and Networks paper (peer-reviewed, unlike Huston's conference
slides) -- it explicitly covers both 25deg and 40deg for the 550km shell and
states SpaceX petitioned the FCC in 2020 to lower the angle from 40 to 25deg "to
improve reception." That paper's own citation for both numbers is just "Starlink
(2020)" -- one more level down than this project had previously gone, landing on
SpaceX's own FCC filing materials as the ultimate root, not an independent
measurement. Also checked eoPortal (a common secondary source in this space) for
an independent citation -- it doesn't mention elevation angle at all. Did not open
the raw FCC docket itself this pass (candidate URLs identified in
`data/starlink_coverage_geometry.md`, not fetched).

**Also answered, unprompted but clearly needed**: "Is that elevation angle for
the dish or the satellite?" It's the ground terminal's (the user's dish's) angle,
not the satellite's -- confirmed two ways from Huston's own slides: the relevant
slide is titled "Looking Up" (the ground-terminal perspective), and a later slide
shows live output from Starlink's own dish diagnostic CLI tool reporting a
`direction_elevation` field -- elevation is something the DISH measures and
reports, not a satellite-side spec. This is a genuinely different quantity from
the satellite's own off-nadir/look angle (`off_nadir_angle_deg()` in
`orbital_geometry.py`), which was already correctly implemented as the
satellite-side angle -- only the naming/explanation was ambiguous, not the math.

**New file**: `data/starlink_coverage_geometry.md` -- full citation chain (Huston
slides -> Cakaj 2021 paper -> "Starlink (2020)"), the dish-vs-satellite
clarification with its two pieces of evidence, and the coverage-radius cross-
validation numbers, in the same citation-heavy style as `satellite_capacity.md`
and `starlink_shells.md`. Added a one-line cross-reference from
`starlink_shells.md` (shell/plane geometry is a different question from coverage
radius, kept as separate files rather than merged). Updated `ASSUMPTIONS.md` #11
and `orbital_geometry.py`'s module-level comment block with the same deepened
chain and clarification -- no numeric constants changed (`MIN_ELEVATION_DEG`
stays 25.0), this was a sourcing/documentation correction, not a model fix, so no
charts needed regenerating from this part of the work.

## Traced the 25deg figure to the actual FCC order text (2026-08-13, same day, follow-up)

User asked directly: "What number do we use for the satellites? ... what do
[tracker sites] use? Has SpaceX (through FCC) released anything to suggest
something?" Pulled `docs.fcc.gov/public/attachments/fcc-21-48a1.pdf` and
extracted its text with `pypdf` (WebFetch's own PDF reader returned "no relevant
content found" on this file -- noted as a general lesson: pull FCC PDFs and
extract locally rather than trusting WebFetch's summary for these). Found the
primary source directly: **FCC Order 21-48**, footnote 3, verbatim: "SpaceX is
authorized to operate with earth station elevation angles as low as 25 degrees
for user terminals and gateways, and for gateways in the polar regions ... as low
as five degrees." This order approved SpaceX's "Third Modification Application"
(SAT-MOD-20200417-00037, filed April 17, 2020 -- almost certainly what Cakaj's
paper's "Starlink (2020)" citation meant), and its body text ties the 25deg figure
explicitly to the SAME altitude change (1,100-1,300km -> 540-570km) that produced
this project's real Gen1 shells.

Also resolved an apparent contradiction found along the way: an APNIC blog post
("Navigating Starlink's FCC paper trail") states the ORIGINAL 2016 Starlink filing
specified 40deg, "to protect terrestrial microwave links." Not a conflicting
claim -- a different, earlier point in the same regulatory timeline: 2016 filing
= 40deg (interference protection); SpaceX's 2020 modification request = lower to
25deg (paired with the lower 540-570km altitude, "to maintain coverage... improve
customer experience"); FCC's 2021 order = granted. `ALT_MIN_ELEVATION_DEG=40` in
this project is correctly the original, now-superseded 2016 figure.

**Tracker question, answered**: checked starlink.sx and orbitalradar.com
directly. Neither publishes a single fixed elevation/radius as "the" number --
starlink.sx has a user-adjustable "Minimum elevation" setting; orbitalradar.com
shows elevation as a per-viewer computed result without disclosing its cutoff.
starlink.sx does mention a "40deg visibility line," but that's the Dishy
hardware's own physical steering-range limit (a different concept from the
link-quality minimum elevation this project models), coincidentally the same
numeral as the superseded 2016 FCC figure.

Updated `data/starlink_coverage_geometry.md` (new primary-source section with the
verbatim FCC footnote and full reconciled timeline), `ASSUMPTIONS.md` #11
(confidence upgraded from "well-attested, traced to an unopened filing" to
"directly confirmed from FCC order text"), and `orbital_geometry.py`'s comment
block. No numeric constants changed -- `MIN_ELEVATION_DEG=25.0` was already
correct, now on much firmer footing.

## Switched the serviceable-customers model to V3 + added a Tbps secondary axis (2026-08-14)

User: "Let's use V3." New `capacity_density_model.V3_SCENARIO`: real, sourced
totals (1,024 Gbps downlink / 200 Gbps uplink per satellite, altitude 345km
midpoint of 330-370km planned) but beam count/beamwidth are NOT publicly
disclosed for V3 (confirmed absent even in the already-trusted davidveksler.com
source) -- reused v2 Mini's beam count (16) and beamwidth (1.5deg) as an
EXPLICIT PLACEHOLDER for the density-cap geometry only. New **ASSUMPTIONS.md
#12** spells out the asymmetric impact: `max_customers_per_satellite()` (the
aggregate cap) is UNAFFECTED by the placeholder, since beams-per-satellite and
Gbps-per-beam only ever appear multiplied together there and that product is
pinned to V3's real total; `max_customer_density_per_km2()` (the areal cap) IS
affected, a real flagged uncertainty. All 12 default-parameter sites in
`serviceable_customers_model.py` switched from `V2_MINI_BEAD_SCENARIO` to
`V3_SCENARIO`. Explicitly OUT of scope: the earlier Phase 3/5 charts
(`charts/capacity_density.py`, `charts/population_capacity_overlay.py`) stay on
v2 Mini -- this switch only touches the serviceable-customers model this
session has been building.

**Secondary top axis, every "vs. satellite count" chart**: user wants
satellite count to STAY the bottom (primary) x-axis, with cumulative max
capacity (Tbps) as a secondary TOP axis on the same chart -- `ax.secondary_xaxis
("top", functions=(to_tbps, from_tbps))`, added as `_add_capacity_secondary_axis()`
in the shared helpers module. `gbps_per_sat = downlink_gbps_per_beam x
beams_per_satellite` is pinned to V3's real 1,024 Gbps total regardless of the
beam-count placeholder above, so this axis is accurate even where the
density-cap numbers elsewhere in the same chart carry that caveat. Wired into
all 6 `serviceable_customers_per_satellite_chart.py` figures and both
`latitude_saturation_heatmap.py` figures (8 charts total).

**Two-layer bug, both found and fixed the same day (see the charting-and-modeling
skill's edge-case catalog, updated with both):**
1. The secondary axis showed literal `$\mathdefault{10^2}$` text -- matplotlib's
   default log-tick formatter generates mathtext syntax that `viz/render.py`'s
   project-wide `text.parse_math=False` (set to stop literal `$` in dollar-value
   labels from being parsed as LaTeX) can't render, so it prints literally
   instead. Existing project convention (`_format_log_axes()`) already covered
   this for primary axes; extended the same explicit-FuncFormatter treatment to
   the new secondary axis.
2. That fix didn't stick on first regeneration -- traced to a SECOND, previously
   undocumented cause via a minimal standalone repro: calling `ax.set_xscale
   ("log")` on the PARENT axis AFTER creating the secondary axis and setting its
   formatter silently RESETS the secondary axis's formatter back to the broken
   default (confirmed: identical code with the two calls reordered either
   reproduces or avoids the bug, nothing else changed). Fixed by moving
   `_add_capacity_secondary_axis()` to after `ax.set_xscale()`/`set_yscale()` in
   all 3 affected log-chart functions (the 3 linear-chart functions never call
   set_xscale, so order didn't matter there).

Both findings were narrowed down to 100% certainty (root cause traced to an
exact rcParams line + reproduced/toggled with a minimal standalone script, not
just observed once) before updating the shared charting-and-modeling skill's
edge-case catalog, per the user's explicit "only if 100%, so as to not add
noise" instruction -- generalized the existing (too-narrow, colorbar-only) skill
entry to cover ANY log-scaled axis including secondary axes, and added a new
row for the ordering gotcha.

## Utilization model + charts, per-country servable-%, and a full TAM-in-dollars model (2026-08-14, "the biggest change yet")

User's own framing. Four connected asks in one message, resolved with an
AskUserQuestion batch (4 questions) before any implementation:
1. **Household size** -> **real per-country data** (chosen over a global constant
   or regional tiers).
2. **Per-country servable-%** -> **full per-country population-by-latitude**
   weighting (chosen over capital-city or single-average-latitude proxies) --
   confirmed CHEAP, not expensive, once research showed all 216 per-country
   WorldPop rasters used to build the global mosaic are already cached locally
   (`data/raw/worldpop/*_pd_1km.tif`), so no new downloads were needed.
3. **Utilization world heatmap** -> **accept latitude-striping** (the model is
   1D/latitude-only; painting the per-band value as horizontal stripes on a world
   map is an honest rendering of what the model computes, not a simplified 2D
   result masquerading as one).
4. **TAM scope** -> user's own custom answer: **price heatmap + a TAM-vs-satellite-
   count/capacity chart** (not just a single headline $ number).

### New model: capacity UTILIZATION (`serviceable_customers_model.py`)
Utilization = served/supply (% of available satellite capacity actually used) --
a DIFFERENT question from the existing served/population "% served." New
functions: `capacity_utilization_by_latitude()`, `sweep_capacity_utilization_by_latitude()`
(per-band, for the world-map heatmap), `capacity_utilization()`,
`sweep_capacity_utilization()` (global aggregate, reuses the already-tested
`serviceable_customers_per_satellite_cap()` rather than re-deriving supply/demand,
since total supply always equals `N x customers_per_satellite` exactly).

**Verified numerically before writing a docstring claim about its shape**: guessed
it would rise-then-peak-then-decay (supply catching up to demand); actual behavior
under V3 is monotonically DECREASING across the whole practical range -- V3's
per-satellite capacity (200,000 customers/satellite) is so large that even N=1
already sits near its highest utilization (~95%) in the sweep. Caught this by
actually running the sweep before documenting it, not by assuming the
first-principles guess was right.

**New chart file `charts/satellite_utilization.py`** (3 figures):
`utilization_vs_satellites.png` (+ `_linear`) -- same "vs. satellite count"
pattern as the serviceable-customers charts, Tbps secondary axis included.
`utilization_heatmap_world.png` -- world map, genuine horizontal stripes (see
decision #3 above), at N=10,900 (today's real fleet size, a concrete default, not
an arbitrary one) -- reuses `coverage_map.py`'s land-outline basemap + a 1-column
`pcolormesh` (`lon_edges=[-180,180]`) to render a per-latitude-band value as full-
width stripes.

### New module: `country_service_model.py` -- per-country servable-%
`load_all_country_population_by_latitude()` loads each country's own cached
raster ONCE (a fixed ~217-raster cost, several minutes) and caches its
population-by-latitude distribution, since that doesn't depend on N.
`country_servable_fraction()` then weight-averages the already-computed GLOBAL
`served_fraction_by_latitude(N)` by each country's own distribution -- this
requires NO new cross-border capacity-allocation logic: the global function
already reflects capacity shared/competed across every country at a given
latitude (built from the all-countries-combined population histogram), so a
country's own number is just a weighted READOUT of that, not a separate
allocation decision. Verified this lines up correctly (same `_lat_bin_edges()`-
style bin scheme in both `population_by_latitude()` and
`served_fraction_by_latitude()`) rather than assuming it.

**Sanity-checked before trusting it**: at every N tested, Australia (sparse,
concentrated near the 53deg shell band) has the HIGHEST servable-%; India and
Egypt (dense, competing for the same mid-latitude capacity as everyone else at
that latitude) have the LOWEST -- exactly matches the "South Asia is supply-
constrained" finding from the 2026-08-11 saturation-heatmap work, from a
completely independent code path.

### New dataset: `data/household_size_by_country.csv` / `.md`
Built by `build_household_size_dataset.py` from Wikipedia's "List of countries by
number of households" (151/217 countries direct match; 66 on a regional-median
fallback, flagged per-row via a `confidence` column, region medians span
2.45-5.24 people/household -- a real, large spread, not a case where a global
constant would have been fine). Tried the UN Population Division's own database
first (more authoritative) -- it's an interactive portal, not a bulk download;
WebFetch returned an implausible value on a first attempt (caught by a sanity
check, not shipped) and the approach was abandoned in favor of the
already-compiled Wikipedia table. Full detail, including the ~20 country-name
mapping overrides needed, in `data/household_size_by_country.md`. New
**ASSUMPTIONS.md #13**.

### New module: `country_tam_model.py` -- the TAM engine
Pricing rule (user-specified): **<20% of a country's population unconnected** ->
price = that country's own existing incumbent price (`charts.affordability._raw_arpu()`,
reused, not reimplemented -- same fixed/mobile selection `equilibrium_model.py`
already uses). **>=20% unconnected** -> price is instead DERIVED by inverting the
elasticity curve: this country's own capacity-constrained servable-% (from
`country_service_model.py`) becomes the target "% unconnected at this price," fed
through `cost_pct_from_pct_unconnected()` (see below) to solve for the price that
would leave exactly that many people priced out. `UNCONNECTED_PCT_THRESHOLD = 20.0`.

`addressable_population = min(unconnected_population, servable_fraction(N) x
total_population)` -- applied identically regardless of price branch (own design
decision, flagged in **ASSUMPTIONS.md #14** as not separately confirmed with the
user). `addressable_subscriptions = addressable_population / household_size`.
`TAM ($/month) = addressable_subscriptions x price`.

**Hoisted the elasticity curve's anchor constants to module level**
(`charts/served_population_vs_cost.py`: `ELASTICITY_X_LO/HI`, `ELASTICITY_Y_LO/HI`,
`pct_unconnected_from_cost_pct()`, and the new inverse `cost_pct_from_pct_unconnected()`)
instead of duplicating the 0.75%/10% anchor values in the new TAM module -- one
source of truth for a curve two files now depend on.

**Verified the model produces a sensible, genuinely interesting result, not just
a number that runs**: at N=4,408 total TAM ~$4.94B/mo; N=10,900 ~$8.35B/mo (RISES,
more subscribers, prices still high); N=100,000 ~$5.80B/mo (FALLS -- India's
servable-% jumps to 71%, collapsing its elasticity-derived price from $77.92 to
$15.20/mo faster than its subscriber count grows). TAM peaking and then declining
as N grows is a real, economically coherent finding this model can show, not
something assumed away -- documented in the chart's own info box, not just here.

### New data: `data/raw/ne_110m_admin_0_countries.geojson` + `charts/country_choropleth.py`
Needed actual per-country BOUNDARY polygons for a choropleth (the existing
`ne_110m_land.geojson` is land-outline-only, no per-country divisions) --
downloaded Natural Earth's 110m admin-0 countries file (177 features, MultiPolygon
geometries, unlike the land file's Polygon-only). New shared loader
`load_country_paths()` (keyed by `ADM0_A3`, NOT `ISO_A3` -- Natural Earth's
`ISO_A3` is "-99" for 5 features including Norway and France) + `draw_choropleth()`,
reusable for any future per-country map. ~50 of 217 telecom-dataset countries have
no 110m-resolution polygon (small island states, Hong Kong/Macao/Singapore,
microstates) -- a known, documented limitation of the 110m simplification level,
shown as grey/missing on the map, not silently dropped from the info box's count.

### New chart file `charts/country_tam_charts.py` (3 figures)
`subscription_price_by_country_100k.png` -- the requested choropleth, log-color
by derived monthly USD price, at the user-specified N=100,000.
`tam_vs_satellites.png` (+ `_linear`) -- total TAM vs. satellite count, Tbps
secondary axis, explicitly noting the non-monotonic peak in its own info box.

All new/changed model files pass `pyflakes` clean. Regeneration of the
country-raster-dependent charts takes several minutes (217 raster loads) --
run once, cached in memory for that process, not re-read per N in a sweep.

**Lesson recurred AGAIN (6th+ time this project) while building these charts**:
`tam_vs_satellites.png`'s first render squished its axes to ~17% of the figure
width, title/legend text running off both edges -- the exact `constrained_layout`
collapse signature. Cause, once again: `TAM_SOURCE_NOTE` was appended directly
onto the end of another sentence (`"...compensates. " + TAM_SOURCE_NOTE`) instead
of starting its own `\n`-separated line, producing one ~150-character unwrapped
line. Fixed the same way every previous occurrence was fixed (explicit `\n`,
short segments) and shortened `TAM_SOURCE_NOTE` itself. Confirmed the fix with
`ax.get_position()` before and after (x1: 0.25 -> 0.997) rather than eyeballing
the image alone, to be certain it was actually resolved, not just visually
plausible. This is now documented in enough places (CLAUDE.md, more than once)
that any future recurrence should be treated as a signal to add a lint-style
guard (e.g. a helper that warns on any info-box string argument over ~80 chars
without a `\n`) rather than fixing it by hand an 7th time.

## TAM follow-up: stacked-by-region chart + CSV exports (2026-08-14, same day)

User: a CSV of monthly revenue by country vs. satellite count (a few buckets, not
a dense sweep), the same aggregated by continent, a stacked-by-region version of
`tam_vs_satellites.png` instead of one aggregate line, and confusion about why
peak TAM (~$11.1B/mo) is so much smaller than the real global telecom industry
(~$1.53T/year).

**Answered the money question with real numbers before writing any new code**
(wanted to rule out an actual bug, not just explain away a surprising result):
pulled real 2024/2025 global telecom revenue (~$1.53-1.55T/year =~ $127B/month,
PwC/Deloitte) and computed the model's own saturated-N numbers directly. At full
saturation (N>=500K), TAM converges to ~$4.33B/mo across ~503.7M subscribers,
blended average price **$8.59/month** -- and that subscriber count matches the
UNCONSTRAINED total unconnected-household count (503.7M, computed independently
from raw telecom+household data with no satellite model involved) almost exactly,
confirming capacity saturates the true demand ceiling correctly, not a modeling
error. The low blended price is a direct, mechanical consequence of the user's
OWN elasticity anchors (0.75% of monthly GNI/capita at 0% unconnected) applied to
a population that is, by construction, concentrated in low-GNI countries -- 0.75%
of a $2,000/year GNI is ~$1.25/month. Three real, additive reasons the total is
smaller than global telecom revenue, not one: (1) only ~2.23B of 8.19B people
(27.3%) are unconnected -- the other 72.7% already generate most of that $127B/mo
today and aren't in scope; (2) the unconnected segment is inherently lower-ARPU,
both because affordability is why they're unconnected and because the pricing
mechanism explicitly seeks an affordable price for them; (3) TAM here is ONE
residential subscription per household, not enterprise/B2B/equipment/roaming/TV
bundles that make up the rest of real telecom revenue.

**New in `country_tam_model.py`**: `sweep_tam_by_region()` -- same per-country
sweep as `sweep_total_tam()`, grouped by the existing World Bank `region` column
instead of summed to one total.

**New in `charts/country_tam_charts.py`**:
- `tam_vs_satellites_by_region.png` -- `ax.stackplot()` (per the charting-and-
  modeling skill's own guidance for positive stacked series), South Asia
  dominates both the peak and the post-peak decline -- directly visible now,
  confirming the India-driven story already found in the per-country numbers.
- `export_tam_csv()` -> `tam_by_country_vs_satellites.csv` (212 rows) and
  `tam_by_continent_vs_satellites.csv` (7 rows), both WIDE format (one column per
  bucket in `SAT_BUCKETS = [100, 1_000, 4_408, 10_900, 33_900, 100_000, 500_000,
  1_000_000, 2_000_000]`), not a dense per-N sweep table -- "a few buckets, not
  millions of lines," per the user's own framing.

## Full-world TAM model: "Starlink just takes incumbent share as it expands" (2026-08-16)

New, SEPARATE, parallel model -- `country_tam_model.py` / `country_tam_charts.py`
(unconnected-populations-only TAM) are UNCHANGED, still both intact and both still
the right answer to their own narrower question. User's request: size the market
assuming Starlink displaces existing incumbent telecom revenue as it expands, not
just fills the currently-unconnected gap. Answered with a written plan + an
`AskUserQuestion` batch (3 questions) before building, per this project's established
"ask before a big build" convention:

1. **Share capture inside the capacity footprint** -> **Full capture (100%)**
   (user declined the offered partial-adoption-ceiling alternative) -- within
   servable_fraction(N), Starlink wins ALL of that population's business, no
   switching-friction/competition curve.
2. **Pricing for already-connected switchers** -> **Split pricing** -- incumbent-
   price (`_raw_arpu()`) for the segment that was already connected (a straight
   revenue swap), elasticity-derived price (via `country_tam_model._country_price()`,
   reused directly) for the segment that was previously unconnected. Chosen
   specifically because it produces a bonus breakdown (incumbent-displacement vs.
   newly-connected revenue) as its own chart.
3. **Model scope** -> **new parallel files**, not a mode flag on the existing ones.

**The key insight that made this cheap to build**: `country_service_model.servable_fraction(N)`
is already built from TOTAL population density (`population_density_grid.py`), not
a connectivity-filtered subset -- so it already tells you what fraction of a
country's ENTIRE population (connected + unconnected) sits within capacity reach at
N satellites. The old TAM model's only unconnected-only-ness came from artificially
capping `addressable_population` at `unconnected_population`; removing that cap is
exactly "take incumbent share." Required no new capacity modeling at all.

**New: `country_tam_full_model.py`** (`CountryTAMFull` dataclass,
`compute_country_tam_full()`, `sweep_total_tam_full()`, `sweep_tam_full_by_region()`,
`sweep_tam_full_by_segment()`). `addressable_population = servable_fraction(N) x
total_population` (no unconnected cap). Split into "incumbent" (already-connected)
and "new" (previously unconnected) segments PROPORTIONALLY to the country's own
connected/unconnected ratio -- no sub-national data exists to know WHICH specific
people within a density bin are already connected, so this is an explicit
simplifying assumption, not measured (**ASSUMPTIONS.md #15**).

**New: `charts/country_tam_full_charts.py`** (5 outputs, reuses `SAT_BUCKETS`,
`TAM_SOURCE_NOTE`, `_usd_formatter` directly from `country_tam_charts.py` rather
than duplicating them):
- `tam_full_by_country_100k.png` -- revenue choropleth at N=100,000. Visually very
  different from the unconnected-only price heatmap: dominated by large WEALTHY
  markets (top 3: USA $9.4B/mo, China $5.3B/mo, Germany $1.9B/mo), not underserved
  ones, since revenue now includes captured incumbent share.
- `tam_full_vs_satellites.png` (+ `_linear`) -- clean sigmoid, saturates at
  **$45.6B/mo near N=257,728** (~4x the unconnected-only model's peak of ~$11.1B/mo
  at N=33,900, as expected -- this model captures the whole world's telecom
  spend, not just the underserved slice).
- `tam_full_vs_satellites_by_region.png` -- stacked by World Bank region. East Asia
  & Pacific (China-driven) and Europe & Central Asia dominate at scale -- a
  DIFFERENT leading region than the unconnected-only model's South Asia, because
  this model rewards large connected populations, not large unconnected ones.
- `tam_full_vs_satellites_by_segment.png` -- **the direct payoff of the split-
  pricing decision**: stacked incumbent-displacement vs. newly-connected revenue.
  At peak, **91% of TAM is incumbent-displacement** -- capturing existing,
  already-paying customers dominates the model almost everywhere once capacity
  stops being the binding constraint; newly-connected revenue is a real but
  secondary contribution that itself peaks (~$5B/mo) and then slightly recedes as
  a share of the (still-growing) total.
- `tam_full_by_country_vs_satellites.csv` / `tam_full_by_continent_vs_satellites.csv`
  -- same wide-format shape and `SAT_BUCKETS` as the unconnected-only model's CSVs,
  for direct side-by-side comparison.

**One real, INHERITED data-quality caveat surfaced prominently in this model's
output, flagged honestly rather than hidden**: at low N, Zimbabwe ranks 3rd-7th
globally by TAM (e.g. $236M/mo at N=4,408, ahead of the UK) -- this is the SAME
"thin survey sample" `_raw_arpu()` artifact already documented in Phase 6
(Zimbabwe's raw pre-cap ARPU is ~$437/mo, implausible for that economy) and
ASSUMPTIONS.md #4. It's not a NEW bug: this model deliberately reuses `_raw_arpu()`
uncapped for the incumbent-switcher segment (the same function/behavior
`country_tam_model.py` already used for its <20%-unconnected branch), but the
full-capture design surfaces it more visibly since Zimbabwe's "incumbent" segment
now contributes revenue regardless of its overall %-unconnected. Not fixed here --
same open item as ASSUMPTIONS.md #4's proposed fixes (drop/cap outlier countries,
or a regional-median fallback), not decided on unilaterally.

## New chart: Avg $/Gbps/year vs. cumulative capacity, derived from the TAM sweeps (2026-08-23)

User: take the TAM-vs-satellites charts (`country_tam_model.py` / `country_tam_full_model.py`)
and turn them into an "avg $/Gbps vs. capacity" market-ladder-style chart, with the same
per-generation cost reference lines as `market_ladder.py`. Confirmed via `AskUserQuestion`
which TAM model to use -- answer: **both**.

**New file: `charts/avg_price_market_ladder.py`**. For each swept satellite count N,
`avg_price = TAM(N) x 12 / (N x 1,024 Gbps/sat)` -- a single BLENDED average price per unit
of deployed capacity, directly comparable to `market_ladder.py`'s $/Gbps/yr axis, but derived
from the TAM sweep (population + pricing + capacity model) rather than the per-country ARPU
staircase. 4 outputs: `avg_price_per_gbps_vs_capacity_{unconnected,full}(_linear).png`.
Reuses `market_ladder.py`'s `_draw_cost_lines()` and `_human()` directly (imported as a flat
sibling module, `charts/` has no `__init__.py`, same pattern every other file in `charts/`
already uses for cross-imports).

**Real finding**: both curves cross all 4 generation cost lines somewhere in their range --
e.g. the unconnected-only curve is $24,588/Gbps/yr at N=100, falls to $25/Gbps/yr at
N=2,000,000, crossing v3's ~$305-352 threshold around N=150,000-200,000. This is a DIFFERENT
cut than `market_ladder.py`'s per-country ladder (which shows the full distribution of prices
across 204 countries at once) -- this chart instead shows what the SINGLE BLENDED average
would need to be at each fleet size, directly against the flat cost lines, closer in spirit
to `charts/equilibrium.py`'s revenue-vs-cost framing but built from the richer TAM model.

**Environment blocker hit and resolved**: this container had the global 0.1deg population
grid cached (`data/raw/worldpop/_grid_cache_0.1deg.npz`) but NONE of the ~215 per-country
WorldPop GeoTIFFs the TAM model needs (`country_service_model.load_all_country_population_by_latitude()`).
Re-ran `download_worldpop.py` (confirmed with the user first, ~0.82GB from hub.worldpop.org)
-- also wrote a PARALLELIZED version (`ThreadPoolExecutor`, 12 workers, same
fetch/download functions, same manifest/resumability) after the user flagged the sequential
version as too slow; cut download time substantially since it's I/O-bound (two network
round-trips + a courtesy sleep per country). Confirmed 215/217 countries, matching the
historical result exactly (CHI, XKX permanently absent from WorldPop's own country list).

**Second, sneakier bug**: even after the download, every chart came out empty / crashed
(`FT_Render_Glyph ... raster overflow` -- a matplotlib font-rendering crash triggered by
degenerate/NaN axis limits, not the real bug itself). Root cause: `population_density_grid.load_or_build_grid()`
uses `use_cache=True` by default, and the CACHED global grid file already present in this
container (36KB, present BEFORE any per-country raster existed here) was entirely NaN --
built once, empty, before the download, then silently reused on every later call, poisoning
`country_servable_fraction()` -> every TAM value -> the whole chart. Fixed by deleting the
stale cache file and letting `load_or_build_grid()` rebuild it fresh (verified: max density
48,210/km2 post-rebuild, matching the documented real figure exactly, vs. 100% NaN before).
**Lesson for a future session**: a "successfully loaded" grid/raster cache is not proof it
has real data in it -- if a TAM/serviceable-customers chart in this project ever comes back
empty or all-zero again, check `np.isnan(grid.density).all()` before assuming the model logic
is wrong.

**Third bug, a real and persistent one, in the shared `_draw_cost_lines()` helper (used by
both `market_ladder.py` and this new file) -- took THREE attempts to actually fix, not one**:
v3's two cost scenarios ($352 vs $305/Gbps/yr) sit close enough in value that their labels
collided. (1) First fix attempt: a fixed 15px, then 20px pixel gap computed via a mid-script
`ax.figure.canvas.draw()` call -- looked right in isolated reasoning but STILL rendered
overlapping text when actually checked with PIL pixel measurement (not just eyeballing the
full chart, which hid it at low zoom.) Root cause: `constrained_layout` renegotiates axes
geometry AGAIN at final `savefig()` time, so a mid-script canvas-draw pass is never guaranteed
to match the geometry text actually renders against -- worse on this file's chart specifically
because its secondary top axis + legend + off-plot info box compress the axes more than
`market_ladder.py`'s own charts. (2) Second attempt: switched to AXES-FRACTION positioning
(purely a function of `ax.get_ylim()`, no canvas-draw dependency at all) with a 0.028, then
0.05 fraction gap -- fixed the *original* pixel-timing bug, but PIL measurement STILL showed
labels overlapping, because 0.05 of THIS specific axes' height (~530-600px, shrunk by the
secondary axis) is still not enough room for two 15px-tall text lines when the two cost
VALUES themselves are only ~0.018 axes-fractions apart naturally -- there is categorically no
way to fit two separate non-overlapping single-line labels in a gap smaller than one text
line's own height, no matter how the offset/threshold is tuned. (3) **Actual fix**: cluster
lines whose natural positions land within `min_gap_frac` of each other and give the whole
cluster ONE combined multi-line label (neutral grey, since one text block can't represent
multiple line colors) instead of trying to stack them separately. Verified this time by
directly measuring rendered label pixel rows with PIL on the actual output files (both
`market_ladder.py`'s and this file's charts), not by re-inspecting the same eyeballed
screenshot repeatedly. **On the linear chart, all of v1.0/v2 Mini/v3-initial now cluster into
one 3-line grey block** (they're all within 5% of each other near the linear axis's low end)
-- loses per-line color-coding for those three specifically, but this is the same category of
tradeoff as the pre-existing, user-approved "drop v3 end-state's label on the linear chart"
call earlier in this same file: when the values are genuinely this close together, no
labeling scheme keeps both full color-coding AND full legibility, and legibility won.

**Follow-up, same day: info box removed** per user request ("Delete the TAM source note")
-- deleted the `info_box.add_info_box()` call, the now-unused `MODEL_SOURCE_NOTE` dict, and
the now-unused `info_box` import from `charts/avg_price_market_ladder.py`.

## New chart: population connected vs. cumulative capacity deployed (2026-08-23, same day)

User: "population connected vs cumulative capacity deployed / sat count." Read as: a
population-COUNT (not $) version of the same market-ladder x-axis convention (capacity Gbps
primary, v3 satellites secondary). Deliberately did NOT reuse the per-country TAM pipeline
(`country_tam_model.py`/`country_tam_full_model.py`, the slow ~217-raster load) -- "population
connected" doesn't depend on pricing, household size, or ARPU at all, only on the physical
density-cap + aggregate-capacity model already built and charted as
`results/population/serviceable_customers_vs_satellites_global(_linear).png`
(`serviceable_customers_model.sweep_per_satellite_cap()`, needs only the cached GLOBAL
population density grid -- no per-country rasters, runs in seconds not minutes).

**New file: `charts/population_connected_market_ladder.py`** -> 2 outputs,
`population_connected_vs_capacity(_linear).png`. NOT a new model -- same
`sweep_per_satellite_cap()` call as the existing chart, just re-axed (capacity Gbps primary /
satellites secondary, matching `market_ladder.py`/`avg_price_market_ladder.py`'s convention
instead of the existing chart's satellites-primary/Tbps-secondary one) and given fleet
reference lines (Gen1/current fleet) converted from satellite count to Gbps for the new x-axis.
Same `SAT_COUNTS_LOG` (100 to 20,000,000, 46 pts) and `LINEAR_MAX_SATS` (7,000,000) ranges as
the existing chart -- both were already tuned to this exact curve's own saturation point (~6M
sats), no reason to re-derive.

Confirms the same finding as the existing chart, now directly comparable on the same x-axis
as the avg-price and market-ladder charts: population served rises ~linearly with capacity
until ~100-200M Gbps deployed (~100,000-200,000 v3 satellites), then saturates at ~8.9B
(raw global population) by ~6M satellites -- current real fleet (~10,900 sats) sits far down
the linear-rise part of the curve, nowhere near the capacity-bound saturation point.

## New sub-project: `revenue_capacity_timeline/` -- real revenue & launch history vs. date (2026-09-05)

Separate, self-contained folder (own README, data, charts, results) -- NOT part of the
equilibrium/serviceable-customers/TAM model above, and doesn't modify any of it. Built for
one request: compile every available Starlink revenue estimate by date, get Jonathan
McDowell's real satellite-launch data by version and date, and turn the launch data into a
cumulative-max-capacity-vs-date table with a parallel axis in equivalent V3 satellites. Full
detail in `revenue_capacity_timeline/README.md`; key points:

- **Revenue** (`data/starlink_revenue_estimates.csv`/`.md`): compiled from SpaceX's own 2026
  S-1 IPO filing (fetched directly from SEC EDGAR -- requires a declared `User-Agent` with
  contact info or SEC blocks the request with a 403 "Undeclared Automated Tool" page, learned
  the hard way), Payload Research, Quilty Space, and WSJ/Information press-leak reporting.
  **Official S-1 numbers are authoritative and now available for 2023-2025**: Starlink
  (Connectivity segment) revenue $3,869M (2023) -> $7,599M (2024, +96.4%) -> $11,387M (2025,
  +49.8%), plus subscriber counts (2.3M/4.4M/8.9M) and ARPU ($99/$91/$81 per month, falling
  even as revenue rises sharply -- volume- and enterprise/government/mobile-driven growth).
  Pre-filing analyst estimates for the same years (Payload, Quilty) all landed within
  roughly +/-13% of the eventual official number -- kept alongside the official rows, not
  overwritten, so that track record is visible. 2021-2022 have no official figures (S-1 only
  presents 3 fiscal years) -- relies on a WSJ press-leak figure ($222M, 2021) and two
  disputed analyst estimates for 2022 ($1.4B Information vs $1.9B Payload, kept as separate
  rows since they disagree by ~35%).
- **Launch history** (`data/starlink_launches_wikipedia_raw.csv`/`starlink_launch_history.md`):
  all 424 real Falcon 9 Starlink launches, 2018-02-22 through 2026-09-02, parsed from
  Wikipedia's "List of Starlink and Starshield launches" -- but from the RAW WIKITEXT
  (`action=raw`), not the rendered page: WebFetch's HTML-to-markdown summarizer silently
  truncated the (very long) rendered page at January 2025, about halfway through, and
  reported "no more launches exist" rather than a truncation error. The raw wikitext, parsed
  with a small custom Python script (regex-split on `|-` row markers), came back complete.
  Cross-checked against McDowell's own aggregate totals (planet4589.org/space/con/star/stats.html,
  fetched separately) -- agree within ~0.2%, the expected gap for two snapshots taken 2 days
  apart during a period of near-weekly launches. **Real finding: zero V3 satellites have
  reached orbit as of this pull** -- every V3/Starship launch attempt in the data is a
  failure (0 satellites deployed), confirmed independently by McDowell's page too ("V3: 20
  satellites (failed to orbit)", "Gen3 Currently in Orbit: 0").
- **Capacity model** (`capacity_timeline_model.py` -> `data/cumulative_capacity_vs_date.csv`):
  per-launch capacity = deployed count x that generation's `downlink_gbps_total` from the
  MAIN project's own `../data/satellite_capacity.csv` (v1.0/v1.5 20 Gbps, v2 mini 96 Gbps,
  v3 1,024 Gbps -- not re-derived, reused as-is), summed as a running cumulative total.
  Deliberately GROSS cumulative (not net of deorbits) -- matches the user's own phrase
  "cumulative MAX capacity," and avoids needing a separate per-satellite deorbit-date
  dataset. v0.1/v0.9 prototypes get 0 Gbps (no comms payload, no published throughput).
  Only `outcome == "Success"` launches count (excludes one real Falcon 9 failure,
  2024-07-12, 20 sats deployed to a bad orbit).
- **Chart** (`charts/capacity_vs_date.py` -> `results/capacity_vs_date_log.png` + `_linear.png`):
  x = date (2019-2026), y (left) = cumulative max downlink capacity (Gbps, log or linear),
  y (right, parallel/secondary axis) = the same value / 1,024 = equivalent V3 satellites --
  same `ax.secondary_yaxis(functions=(...))` + "set formatter AFTER set_yscale" pattern
  already established for the main project's secondary axes
  (`charts/serviceable_customers_chart.py::_add_capacity_secondary_axis`). Latest point
  (2026-09-02): 12,868 real satellites launched, 875,824 Gbps cumulative capacity = 855.3
  equivalent V3 satellites. **Since no V3 satellite is actually in orbit, that number is a
  normalization unit against today's real v1.0+v1.5+v2-mini fleet, not a real V3 count** --
  said explicitly in the chart's own info box, not just here.
- **Combined table** (`build_summary_table.py` -> `data/revenue_and_capacity_by_year.csv`):
  joins the two datasets one row per calendar year. Headline cross-check: capacity grew
  ~23x from end-2021 to end-2025 (37.6K -> 675K Gbps) while revenue grew ~51x over the same
  window ($222M -> $11.4B, mixing a press-leak start point with an official-filing end
  point) -- revenue outpacing capacity by roughly 2x, consistent with the S-1's own
  disclosed shift toward higher-value enterprise/government/mobile revenue on top of raw
  subscriber growth.

**Follow-up, same day**: user asked for the capacity axis in Tbps, not Gbps -- `capacity_vs_date.py`
reworked to convert at load time (`/1000`) rather than just reformatting tick labels, so the
V3-equivalent conversion factor changes accordingly (1.024 Tbps/satellite, not 1,024 Gbps).
Then a second chart, `charts/revenue_vs_capacity.py` -> `results/revenue_vs_capacity_log.png`
+ `_linear.png`: x = cumulative max capacity (Tbps) at each fiscal year-end, y = Starlink
revenue ($B/year), same parallel-axis convention as the main project's
`charts/country_tam_charts.py` (`tam_vs_satellites_by_region.png` etc.) but built the other
way around (capacity primary here, since that's this sub-folder's real x-axis; V3-satellite-
equivalent secondary, via `ax.secondary_xaxis` instead of that file's `secondary_xaxis`-for-Tbps
usage). Plots every individual revenue estimate per year as its own point (marker shape keyed
to source_type: filled circle = official S-1, open square = analyst estimate, open triangle =
press leak) with one connecting line through the best-available point per year -- deliberately
does NOT reconcile disagreeing sources into a single number, matching the CSV's own
one-row-per-source-per-year structure. Bug caught before shipping: first draft annotated the
year label at EVERY point, producing overlapping duplicate text ("2024 2024 2024") wherever a
year has 2-3 estimates stacked near the same x -- fixed by labeling only the best-available
point per year. Also relocated the caveat/source text box from bottom-left to bottom-right
after confirming (linear chart) it was sitting directly on top of the 2021 data point --
bottom-right is empty on both the log and linear versions of this particular curve shape.

## `revenue_capacity_timeline/` renamed, Q2 2026 earnings added, chart-source rule added to the skill, TAM overlay chart (2026-09-05, same day)

Several fast follow-ups on the new sub-project from earlier this same day:

1. **User caught a real mistake**: charts in this sub-folder cited their own source as
   "Source: starlink_revenue_estimates.md" -- a repo filename, meaningless to a reader
   without the repo open. Fixed both charts to name the real origin instead ("Jonathan
   McDowell (planet4589.org)", "see legend" for the multi-source revenue chart). **Also
   added this as a hard rule in the `charting-and-modeling` skill itself**
   (`~/.claude/skills/charting-and-modeling/SKILL.md`, "Chart labelling rules" section) --
   a source citation must name the real-world author/org/dataset, never an internal
   `.md`/`.csv` path. Checked every other chart file in this whole project for the same
   mistake first -- all already cited real sources (World Bank, FCC, WorldPop, Natural
   Earth) -- so this was isolated to the two brand-new files, not a pervasive pattern.
2. **The sub-folder itself got renamed mid-session**, from `revenue_capacity_timeline/` to
   `spacex_revenue_capacity_timeline/` -- confirmed byte-for-byte identical content before
   continuing (not a duplicate from a separate process, despite briefly looking like one
   given the unrelated concurrent uncommitted changes elsewhere in the repo at the same
   time -- see point 4). Every script resolves paths via `Path(__file__)`, so nothing
   broke except the README's example shell commands.
3. **User: "we have Q2 results right? ... you didn't search hard enough."** Correct --
   the first revenue research pass stopped at SpaceX's pre-IPO S-1 filing and missed that
   SpaceX has since actually IPO'd (Nasdaq: SPCX) and reports real quarterly earnings.
   Fetched the Q2 2026 earnings release directly from SEC EDGAR (filed 2026-08-04):
   Connectivity segment revenue $4,291M, **up 32% SEQUENTIALLY from Q1 2026's $3,257M**
   (not just YoY) -- real acceleration, not just growth. H1 2026 total $7,548M. Starlink
   Subscribers reached 12.0M (doubled YoY); ARPU held flat at $66/month for the first time
   in the whole series (previously falling every period). Enterprise & Government revenue
   grew 108% YoY vs. Consumer's 44% -- the acceleration is disproportionately an
   enterprise/government story. Annualizing Q2 alone implies a ~$17.2B/year run-rate,
   already close to Quilty Space's $20B full-year-2026 forecast with two quarters left to
   report. Added to `data/starlink_revenue_estimates.csv`/`.md` as new quarter-specific
   metric rows (`starlink_segment_revenue_q1_only`/`_q2_only`/`_h1_only`, distinct from the
   full-year `starlink_segment_revenue` metric used by 2021-2025), and as a distinct star
   marker (not connected into the full-year line) on `charts/revenue_vs_capacity.py`.
4. **New chart, user request ("Overlay your revenue vs capacity onto my unconnected TAM
   model")**: `charts/revenue_vs_unconnected_tam_overlay.py` -> `results/revenue_vs_unconnected_tam_overlay_log.png`
   + `_linear.png`. Overlays this sub-folder's real revenue (annual figures / 12, plus the
   two real quarterly rates / 3 for the freshest/most precise points) onto the MAIN
   project's "Unconnected Addressable Market" model
   (`charts/country_tam_charts.py` -> `results/market/tam_vs_satellites.png`), same x
   (total satellites, V3-equivalent) and y (USD/month) axis definitions. **Deliberately
   reads the UAM curve from that chart's own already-computed CSV snapshot**
   (`results/market/tam_by_continent_vs_satellites.csv`, 9 discrete satellite-count
   buckets) rather than importing/re-running the live model code -- at the time this was
   built, the main project's TAM model was mid-refactor elsewhere in this repo
   (`country_tam_model.py` being renamed/rewritten into a new `tam_model.py`,
   uncommitted, alongside other unrelated new/deleted files -- `tile_capacity_model.py`,
   `country_tam_full_model.py` deleted, etc. -- discovered via `git status` while
   debugging an ImportError), so importing either risked either failing outright or
   silently depending on not-yet-validated in-flight logic. **Real, somewhat surprising
   finding**: actual Starlink revenue tracks almost exactly along the UAM model's curve
   at today's real satellite counts (~40-855 equivalent V3 satellites, i.e. the model's
   very earliest, steepest-rising segment) -- surprising because actual revenue includes
   already-connected switchers, enterprise, government, and mobile customers that this
   unconnected-only model doesn't count at all, yet the two lines nearly coincide in the
   real-world range so far. Not yet explained -- flagged as a finding, not resolved,
   directly in the chart's own caveat note.
   Two of the now-familiar recurring bug classes hit again while building this, both
   fixed: (a) an unwrapped single-line source-note string collided with the 2021 data
   point (fixed with explicit short `\n`-wrapped lines, same lesson logged many times
   elsewhere in this file); (b) the log-scale y-axis auto-extended down to the 2021 point
   (~$18.5M/mo), which also needed an explicit floor (`ax.set_ylim(1e7, ...)`) for the
   same "log axis needs a nonzero floor" reason documented repeatedly above. The linear
   version originally swept the same 0-2,000,000-satellite range as the log chart's
   9-bucket data and rendered every real point invisibly close to x=0 -- fixed by capping
   the linear x-axis at 50,000 (just past the model's peak) instead, another instance of
   the project's standing "don't render dead space" principle.

**If a future session regenerates `results/market/tam_by_continent_vs_satellites.csv`
after the in-flight `tam_model.py` refactor lands, re-run
`charts/revenue_vs_unconnected_tam_overlay.py`** -- it always reads that CSV fresh, never
caches its own copy, so it will pick up the new numbers automatically, but the "tracks
almost exactly" finding above should be re-verified against whatever the refactored model
produces rather than assumed to still hold.

## 2D (lat x lon) capacity allocation — the longitude fix (2026-09-05)

User: "capacity is only allocated per-latitude, not per-longitude as well... satellites
on opposite sides of the Earth obviously can't serve the same customer... we need to
allocate capacity by the 25 degree FOV we derived earlier... subdivide capacity into
latitude and longitude tiles... two neighbouring countries are 'competing' for the same
satellite." Correct on every point. `LONGITUDE_FOV_CAPACITY_REVIEW.md` (written the same
day by a previous session, at the user's request) has the original framing; a **RESOLVED**
section now appended to it has the full write-up. Summary here.

**New files**: `tile_capacity_model.py` (the model), `tile_capacity_validation.py`
(exact max-flow reference), `charts/tile_utilization_map.py` (world heatmap + GIF) ->
`results/tile_capacity/`. **Nothing existing was rewired** — `serviceable_customers_model.py`,
`country_service_model.py` and both TAM models are untouched, because other sessions were
revising the market layer in parallel. That migration is the remaining work.

**Two quantified bugs in the old path**, both measured rather than argued:
1. `orbital_geometry.expected_sats_reaching_latitude()` **overcounts satellites in view by
   ~19x** — it convolves the latitude histogram with a boxcar of half-width R, counting
   every satellite whose LATITUDE is within R at ANY longitude (the whole 40,000 km ring)
   instead of those inside the DISK of radius R. 19.1x global at N=10,900, 27.8x at the
   equator, 4.3x at 80deg. The correct equatorial figure is ~45 satellites in view, which
   cross-checks against `N x disk_area / earth_area`. That function now carries a
   docstring saying so and pointing at the replacement; **its behaviour is unchanged**, so
   nothing downstream moved.
2. **Capacity teleportation along a ring** — the old model enforced "capacity can't
   teleport" across latitudes (its own stated design rule) while violating the identical
   constraint along a latitude.

Net effect, old vs new served customers: **1.49x overstated at N=4,408, 1.54x at 10,900,
1.46x at 33,900, 1.34x at 100,000, 1.00x at 1,000,000** (both models are simply
population-bound at saturation). The overstatement is ~1.5x rather than ~19x because the
aggregate per-satellite capacity term, pooled per ring, usually bound before the density
cap did.

**How the model works.** Ground and satellite positions share one 1degx1deg tile grid.
Satellites are placed by each real shell's latitude profile and spread uniformly in
longitude (RAAN assumption, ASSUMPTIONS.md #16). Each satellite serves a spherical cap of
Earth-central radius R = 90 - eps - asin(Re cos eps/(Re+h)) — 8.33-8.70deg (927-968 km) for
Gen1's 540-570 km shells, 5.71deg (635 km) at V3's planned 345 km. It carries ONE customer
budget shared across everything in that disk, so neighbouring tiles compete: a bipartite
transportation problem, not a per-band min().

**The performance trick that made a full 2D treatment cheaper than the approximation it
was meant to justify**: angular distance between two tiles depends only on
(lat_i, lat_j, delta_lon), so the disk operator is block-circulant in longitude and
collapses to one small matrix multiply per longitude frequency — ~15 ms for the whole
180x360 grid, versus minutes for an explicit ~20M-edge sparse matrix. A full solve is
~15 s. Partially-overlapping tiles get fractional longitude weights, which reproduces the
exact spherical-cap area to within 0.4% at every latitude.

**Allocation** is damped proportional water-filling: each round, ground tiles request from
the satellites they can see in proportion to remaining free capacity, oversubscribed
satellites ration proportionally, repeat. Costs exactly three disk convolutions per supply
group per round, and is feasible by construction every round.

**Verified against an exact max-flow (Dinic, hand-written — no scipy in this environment)
on the same graph**: 0.977-0.994 of the optimum, never above it, at both 4deg and 6deg tiles.

**`AllocationResult.unreachable_slack()` is the check that settles whether a dark patch on
the map is a bug**: it reports the share of covered satellite tiles with BOTH spare capacity
AND unserved demand within reach — the only places better routing could help. At N=100,000
that is 4.7% of tiles holding ~1.5% of served customers, matching the independently measured
gap from optimum. It confirmed the two big dark regions are REAL, not artifacts: central
Sahara sits at 16% utilization with exactly ZERO unmet demand within 940 km (its coverage
disk holds almost nobody), while central Europe is at 100% with 39M customers queued.

**Four real bugs, every one caught by a check rather than by reading the code** — worth
knowing about before editing any of this:
1. **FFT round-off served uncovered tiles for free.** irfft leaves ~1e-16 where the true
   reachable capacity is exactly zero; the allocator divides unmet demand by reachable
   capacity, so that noise became a ~1e16 request ratio. Total served came out ~50% ABOVE
   total capacity consumed. Caught by a flow-conservation audit, not by eye. Fixed with
   `DiskOperator.NOISE_FLOOR_REL = 1e-10`; the audit now runs on every solve so this class
   cannot return silently. **General lesson: any `a / conv(b)` in this project needs a
   noise floor on the convolution.**
2. **Log-spaced density-bin CENTRES made capped demand exceed 100% of world population**
   (100.4%). `DemandTiles` now stores population per bin alongside area, so
   `min(pop_bin, cap x area_bin)` is exact in the uncapped limit.
3. **The reweighting oscillated and rendered as concentric rings — and the first fix
   was not enough.** The reweighting is a multiplicative accumulation with NO fixed
   point: the weight spread grows geometrically, hits ~1e6 by round 16 and pins at the
   clip bounds by round 17. Successive rounds push a wave of demand outward from each
   population centre, rendering as concentric rings of alternating utilization, with
   satellites DIRECTLY over people less used than ones a coverage radius away. Damping
   the step (eta 1.0 -> 0.25) raised the peak total and fixed a transect near Mexico, so
   it looked solved — **but the user spotted a clear residual arc over Europe in the
   shipped chart, and they were right**: at the best-total round the ripples were still
   plainly there, just relocated. The actual fix is to **average the allocation over all
   reweighting rounds**. Each round's rings sit at a different radius, so averaging
   cancels them, and a convex combination of feasible flows is itself feasible (row sums
   stay under demand, column sums under capacity, total is the mean of the totals). At
   N=100,000: greedy 5,242M clean map / best single round 5,774M heavy ringing / **average
   of rounds 0-16 5,612M with a map as smooth as greedy**. Costs 2.8% of the peak total,
   still +7% over greedy, and drops the validated optimality from 0.996-0.999 to
   **0.977-0.994** — a deliberate, documented trade for a physically coherent map.
   **Two lessons.** (a) The rings were the tell; the TOTAL alone never exposed them.
   (b) Worse, a global smoothness metric (total variation) actively MISSED them — TV
   *improved* as the rings developed, because it is dominated by the coastline halos.
   Only looking at a zoomed crop of the actual map found it. Do not trust a scalar
   summary to police spatial artifacts in this project.
4. **An early validation run reported ratios ABOVE 1.0** (impossible for a feasible flow).
   Cause: the model uses fractional tile-overlap weights while the Dinic graph used hard
   0/1 adjacency — different problems. `DiskOperator(fractional=False)` exists so the two
   run on the identical graph. **Lesson: when a reference disagrees, check you are
   comparing the same problem before touching the algorithm.**

**Charts** (`charts/tile_utilization_map.py`, single `draw_utilization_map()` renderer
shared by stills and animation frames): `utilization_map_{4408,10900,100000}sats.png` and
`utilization_map_vs_satellites.gif` (40 log-spaced fleet sizes, 500 -> 5,000,000).
Continents are unfilled outlines drawn OVER the mesh. Parameters sit under the axes via
`fig.text` rather than `info_box` — a full-bleed world map has no empty region for the
info-box scan to find, so any in-axes placement necessarily covers real tiles.
The maps show the physics directly: land saturated, oceans idle, and a ~940 km
partial-utilization halo around every coastline and Pacific island, which is exactly the
coverage disk made visible.

**Open / next**: migrate `country_service_model.country_servable_fraction()` (and the TAM
models through it) onto per-tile served fractions, so a country reads out its OWN tiles
instead of a longitude-pooled latitude band; then retire
`expected_sats_reaching_latitude()`. Also unresolved and pre-existing: the model runs
Gen1's 540-570 km shell geometry with V3's capacity scenario, whose real altitude is
345 km — that halves the coverage disk area, and `build_supply(altitude_override_km=345)`
exists to test it but no run has been shipped.

## Units fix: the model works in CONNECTIONS, not people (2026-09-05, same session)

User: "How do we model households? Ie. people per connection." The honest answer was
that we didn't — and that this was a real bug, not just a gap.

**The error.** `capacity_density_model.py` produces SUBSCRIBER counts (one dish, one
household): 419 per beam under 20:1 contention, 200,000 per V3 satellite, 195/km2.
Every capacity model in this project — the old `serviceable_customers_model.py` and the
new `tile_capacity_model.py` alike — compared those directly against WorldPop PEOPLE.
That asserts one person per dish. It does not overstate the market; it **understates how
many people a satellite reaches, by roughly the household size**. Note the old TAM model
did divide by household size, but only at the very END, to price subscriptions — the
binding capacity constraint upstream was still applied in the wrong units, so the error
was baked in before pricing ever ran.

**The fix.** `tile_capacity_model.py` now works in connections internally.
`household_grid.py` (new) attributes `data/household_size_by_country.csv` to lat/lon
tiles by probing each tile at 4x4 interior points against Natural Earth 110m country
polygons and averaging over whichever probes land inside a country. **Probing tile
CENTRES alone matched only 87.8% of world population** — a 1deg tile over a coastal city
often has its centre offshore — while subsampling reaches **97.6%**; unmatched tiles take
the population-weighted global mean. Result: 8.85B people -> **2.50B connections**,
population-weighted mean **3.86 people/connection**. `AllocationResult.served` is
connections; `.served_people` and `.total_served_people` multiply back out.

**Effect on the headline numbers** (people served, V3 scenario):

| N satellites | before (people==dishes) | after (connections) |
|---|---|---|
| 4,408 | 444M | **1,378M** |
| 10,900 | 994M | **2,986M** |
| 33,900 | 2,622M | **6,219M** |
| 100,000 | 5,547M | **8,484M** |

Saturation moves from N~1,000,000 down to **N~300,000**.

**Layering cleanup done at the same time**: `load_country_paths()`/`_polygon_to_path()`
moved OUT of `charts/country_choropleth.py` into a new root-level `country_geometry.py`,
so the model layer can use country boundaries without importing upward from `charts/`.
`country_choropleth.py` re-exports them, so its two existing dependents
(`charts/country_tam_charts.py`, `charts/country_tam_full_charts.py`) are unchanged.

## MODEL_SPEC.md (2026-09-05)

User asked for "a model spec that shows how we do everything from start to end."
Written as `MODEL_SPEC.md` (root): the full pipeline in 11 sections — shells and
latitude density, the 25deg coverage disk and its block-circulant operator, WorldPop
demand and the people->connections conversion, the two capacity ceilings, the
transportation problem and why the reweighting rounds are averaged, outputs, the six
verification results, the assumptions it rests on, how to run it, and what is still
open. Includes a table of the five bugs that verification caught which reading the code
did not. **Keep it current** — it is meant to be readable end to end without the code
open, and it is the document to hand a fresh session before CLAUDE.md's narrative.

## Coverage-geometry diagram + FOV wording (2026-09-05)

User asked what "coverage radius 8.3/8.4/8.6/8.7 deg" meant on the utilization chart,
then: "Aren't we using 25 degrees as the assumption?" Both numbers are right — they are
angles at different vertices of ONE triangle, and the chart label had invited exactly
this confusion by quoting the derived one in the same unit as the input:

| vertex | angle | what it is |
|---|---|---|
| user terminal | **25 deg** | elevation above the local horizon — the FCC input |
| satellite | 56.5 deg | off-nadir look angle |
| Earth's centre | **8.45 deg** | sub-satellite point to the edge of the servable disk |

`(90 + 25) + 56.55 + 8.45 = 180.00` exactly, verified numerically for every shell
altitude. The 8.3-8.7 spread is only Gen1's four shell altitudes (540-570 km); a higher
satellite sees further. Per the user's instruction the chart note is now just
**"User FOV: 25 deg | Sat FOV at equator: ~8 deg"** — "at equator" is a fair gloss:
the angle is a function of altitude, not latitude, but at the equator it also equals
8 deg of longitude, which is what a reader of that map wants pinned down.

**New: `charts/coverage_geometry_diagram.py` -> `results/coverage/coverage_geometry.png`.**
Two panels, both TRUE TO SCALE with real curvature and no exaggerated altitude (which
matters — the disk is only ~8.5 deg wide precisely because 550 km is small next to
Earth's 6,378 km radius): left, the whole Earth with the angle at its centre; right, a
zoom on the satellite and user terminal with the off-nadir and elevation angles, the
local horizon, altitude and ground spot radius.

**`_verify_drawn_angles()` measures the three angles back out of the plotted
coordinates and raises if they disagree with the labels or don't sum to 180.** This is
worth copying: a diagram whose labels come from formulas rather than from its own
geometry can be silently wrong, and this one was — the first draft measured the
elevation to the WRONG END of the horizon line (giving 155 deg, drawn as a huge arc)
while still printing "25 deg" beside it. Also hit the documented ghost-axes trap:
`render.new_figure()` returns `(fig, ax)`, and taking only `[0]` then calling
`add_subplot` twice left the original axes orphaned, rendering as a stray 0-1 tick/grid
frame behind the whole diagram.

## Utilization animation: large-label variant + per-frame PNGs (2026-09-05)

User asked for a second GIF emphasising satellite number / people served /
constellation utilization at axis-label size under the chart, the original GIF kept,
and every frame as a PNG in its own folder. `charts/tile_utilization_map.py` gained
`render_sweep()`, which solves each fleet size ONCE and draws both label variants from
the same `AllocationResult` — the solve is ~15 s and the labelling is free, so rendering
the variants in separate passes would have doubled a ~13 minute job for nothing.
Outputs: `utilization_map_vs_satellites.gif`, `..._large_labels.gif`, and 40 PNGs each
in `results/tile_capacity/frames/` and `frames_large_labels/`. `_fit_width()` measures
the rendered headline and steps the font down until it fits — the satellite count runs
from 3 to 7 digits, so a size that fits one frame can overflow another.

## Chart: household size by country, ranked (2026-09-05)

`charts/household_size.py` -> `results/population/household_size_by_country_ranked.png`.
217 countries ranked by people per household, bars coloured by World Bank region
(`charts/regions.py`), **hatched where the value is a regional-median fallback rather
than a national survey (66 of 217)** -- do not drop that hatching in a later edit, it is
the difference between a measurement and an inference and several fallback countries sit
at the extremes. Range **2.05 (Germany) to 8.66 (Senegal)**, a 4.2x spread, so this is
not a variable a global constant could stand in for. The hatched bars form visible flat
plateaus -- that IS the fallback, a whole region sharing one inferred value, and the
footer says so rather than leaving a reader to wonder why the curve has steps.

**Real discrepancy surfaced and stated on the chart rather than papered over**: the
country-population-weighted mean is **3.93**, but the model applies **3.86**. Different
weighting, not an error -- the model weights by WorldPop's gridded population rather than
World Bank country totals, and 2.4% of population falls outside a matched country
polygon and takes the global mean. The first draft labelled the 3.93 line "used by the
model", which was simply wrong; `_model_mean()` now reads the figure back out of
`tile_capacity_model.build_demand()` itself instead of recomputing something similar.

**Two layout fixes worth reusing.** (1) `fig.set_layout_engine("none")` does NOT make
`subplots_adjust` work -- it leaves a placeholder engine that still refuses it and only
emits a warning. To reserve space for figure-level footer text under constrained_layout,
shrink the engine's rect: `fig.get_layout_engine().set(rect=(0, 0.145, 1, 0.855))`.
(2) Labelling the top 4 and bottom 4 of a 217-bar ranking put rotated text on bars
~0.05 inch apart, which overlapped no matter the offset; only well-separated ranks get a
callout now (the two endpoints plus the four most populous countries) and the extremes
are listed in the footer instead.

## Tile capacity model integrated into the TAM model (2026-09-05)

User: "we need to integrate [the tile capacity model] into the new model for allocating
capacity. Is that model well documented?" Answers to the three decisions they made when
asked: **capacity swap first, revenue ranking as a later separate task**; **edit
everything needed including the other session's files**; **leave the pricing divergence
alone but chart it**.

### State of the code before this work

`tam_model.py` (which replaced the deleted `country_tam_model.py` +
`country_tam_full_model.py`) and `country_service_model.py` were both genuinely well
documented -- `tam_model`'s docstring even named the integration seam and anticipated
this task. But two things were badly wrong and one was subtle:

1. **`PRICING.md` was entirely stale** -- it documented the two deleted modules and a
   `_country_price()` / `SCARCITY_PRICE_MULTIPLIER_CEILING = 3.0` rule that no longer
   exists, and its revision history argued *against* elasticity pricing, which is what
   the model now uses. Fully rewritten.
2. **Three chart modules were broken at import** (`country_tam_charts.py`,
   `country_tam_full_charts.py`, `avg_price_market_ladder.py`) -- all still importing the
   deleted models. All three repaired.
3. `charts/country_tam_charts.py`'s price heatmap read `r.price_usd_per_month` and
   `r.price_basis`, fields the new `CountryTAM` does not have. Repointed to
   `price_unconnected_usd_per_month`. **Consequence worth knowing: the derived price now
   depends only on a country's own %unconnected and GNI/capita, so it does NOT vary with
   satellite count.** The old scarcity premium made it N-dependent and the chart was
   drawn at two N; drawing it twice now produces two identical images, so it is drawn
   once and the filename lost its `_100k` suffix.

### What changed

- **`country_service_model.py` rewritten tile-based.** Was: weight a GLOBAL
  per-latitude-band served-fraction by each country's population-by-latitude. Now:
  weight `tile_capacity_model`'s per-tile served-fraction by each country's own
  population per 1deg tile. Same weighted-readout idea, but the tile model has already
  resolved who competes with whom, so no capacity teleports around a latitude ring.
  New `load_all_country_population_by_tile()` builds per-country tile footprints from
  the same cached WorldPop rasters, stored SPARSE (a country occupies few of the 64,800
  tiles).
- **`tam_model.py` decoupled from capacity.** `compute_country_tam()` now takes an
  already-computed `{iso3: servable_fraction}` and is pure pricing + aggregation -- the
  old signature threaded five latitude-histogram arguments through the module purely to
  hand them to the capacity call. New `sweep_country_tam()` solves ONCE per N and returns
  per-country rows; `total_tam()` / `tam_by_region()` / `tam_by_segment()` are cheap
  reducers over that. **This matters for runtime, not just tidiness**: a solve is ~15 s,
  and the old three separate sweep functions each re-solved every N for identical
  numbers. New `load_inputs()` holds the one-time setup all three chart modules shared.

### Two caching bugs, one of them mine, both of the same family

Solving is ~15 s per N and a chart run sweeps ~99 distinct N, so servable fractions are
cached to disk. Both bugs are the "a cache that loads successfully is not a cache that
holds the right thing" family this project keeps re-encountering:

1. **My country-tile cache silently returned a partial answer.** A 10-country smoke test
   wrote the cache; the subsequent 217-country request then got 10 countries back with no
   error, and the TAM run reported "10 countries" totals. Fixed by making the cache
   INCREMENTAL -- reuse what is cached, build and merge whatever is missing.
2. **Stale-config risk on the servable cache.** Keyed on capacity scenario + tile size +
   every shell's altitude/inclination/count, hashed into the FILENAME so a config change
   lands on a different file, with the key also stored inside and re-checked on load.

Measured: cold 19.6 s, warm 0.000 s, identical results.

### What the integration actually changed, decomposed

TAM goes UP, not down -- which is not what "we fixed a 1.5x overstatement" would lead
you to expect. **Two fixes with opposite signs are bundled in this switch**, and it
would be easy (and wrong) to report only the net. Measured at N=10,900, TAM $B/month:

| stage | unconnected | full |
|---|---|---|
| (a) old: latitude-pooled capacity, 1 person = 1 dish | 4.67 | 11.68 |
| (b) + longitude fix (tiles), still 1 person = 1 dish | **3.21** | **8.61** |
| (c) + households fix (connections) = what ships | **6.60** | **20.19** |

The longitude fix alone cuts TAM ~31%. The households fix (people are not dishes; see
the units section above) more than reverses it. Net ~1.4x up for `unconnected`,
~1.7x for `full`.

**The longitude fix is not a uniform haircut -- it REDISTRIBUTES, and sharply.**
Servable fraction at N=10,900, old -> longitude-only:

| country | old | longitude only | effect |
|---|---|---|---|
| India | 8.3% | 2.0% | **0.24x** |
| Brazil | 49.4% | 20.6% | 0.42x |
| Nigeria | 11.7% | 5.0% | 0.43x |
| China | 9.4% | 5.1% | 0.55x |
| Indonesia | 18.7% | 10.4% | 0.56x |
| Russia | 32.3% | 38.2% | 1.18x |
| Australia | 83.8% | 100.0% | 1.19x |
| United States | 12.6% | 26.5% | **2.10x** |

Exactly the predicted mechanism, now measured: ring-pooling was crediting dense
low-latitude countries with capacity that was really sitting over empty ocean at their
latitude, and India was the biggest beneficiary of that error. The USA *gains* from the
fix because it shares its latitude band with Europe's and Asia's populations, which
were diluting its pooled share -- once capacity is local, it keeps what is overhead.

### Sanity check on the new per-country numbers

At N=4,408: Australia 100%, Canada 72%, Russia 40%, USA 27%, Indonesia 16%, Nigeria 10%,
China 6.1%, India 3.8%. Sparse high-latitude countries saturate first; dense low-latitude
ones last -- the same supply-constrained-South-Asia finding this project reached from the
saturation heatmap, now reproduced through a completely independent code path.

### New chart

`charts/derived_vs_real_price.py` -> `results/market/derived_vs_real_price_by_country.png`,
built at the user's request to size the pricing assumption rather than leave it in prose.
Log-log scatter of elasticity-derived price against each country's real local price, y=x
diagonal, 10x/0.1x guides, coloured by region. **Median 1.04x, but the large unconnected
markets sit far above: Fiji 21x, Sri Lanka 14x, India 9.9x, Pakistan 9.8x, Nigeria 6.7x.**
The extreme low-ratio points (Zimbabwe 0.0x, South Sudan, Syria) are the known bad-ARPU
survey outliers of ASSUMPTIONS.md #4 showing up from a new angle.

**Layout note**: `set_aspect("equal")` on this chart fought constrained_layout and forced
the axes taller than the figure, clipping the title AND the x tick labels. Dropped it --
with equal x/y limits, y=x is the corner-to-corner diagonal anyway.

### Still open

- **Revenue-ranked allocation.** `tile_capacity_model` maximises connections served and is
  revenue-blind; TAM prices whatever got served. The user's stated intent is to serve the
  highest-revenue customers first within each tile's reachable set. Note the shape of the
  problem before starting: the UNCONNECTED price is exogenous (a country's real
  %unconnected and GNI, independent of N), so ranking on it is well defined -- but the
  CONNECTED price in `mode="full"` is lerped by how much of that country's connected
  population is served, which depends on the allocation, so that half needs a fixed point
  or an explicit simplification.
- `orbital_geometry.expected_sats_reaching_latitude()` (the ~19x overcount) is now unused
  by the market path but still used by `serviceable_customers_model.py` and its charts.

## Migrated the remaining latitude-only charts onto the tile model (2026-09-05, same day)

User: "Update existing charts with this new method. Eg. satellite utilization needs
regeneration now, look for others that need it too." A repo-wide grep for
`serviceable_customers_model` found **four chart families** still built on the
latitude-only model (the TAM integration earlier this session only touched the market
layer, not these): `charts/satellite_utilization.py`, `charts/
serviceable_customers_per_satellite_chart.py`, `charts/latitude_saturation_heatmap.py`,
`charts/population_connected_market_ladder.py`. All four called functions that trace
back to `orbital_geometry.expected_sats_reaching_latitude()` (the ~19x ring-overcounted
density cap) or the ring-pooled aggregate capacity term -- so all four were carrying the
same longitude bug this session already fixed for the market layer, just not yet for
these.

**New shared readouts added to `tile_capacity_model.py`** (not duplicated per chart):
`fleet_utilization(result)` (global scalar), `served_fraction_by_latitude(result, tile)`
(population-weighted marginal over longitude, for the saturation heatmap),
`density_cap_connections_per_km2()` / `density_cap_profile_average_people()` (the areal
ceiling, standalone from a full solve since only the ceiling itself is wanted). The last
one is a DELIBERATE change, not a like-for-like port: the old latitude-only version
weighted its single summary number by where SATELLITES concentrate (cap-weighted,
answering "what ceiling does a typical satellite support"); this one weights by where
PEOPLE actually are (population-weighted), which is now possible and is the more useful
reading of "what ceiling does a typical person experience."

**Performance decision, made before writing any chart code**: a full-resolution (1deg)
solve costs ~15-16s, and these charts need dozens-to-hundreds of points per sweep to
render a smooth curve -- at 1deg that's tens of minutes PER chart. Measured timing
across tile sizes first: 2deg tiles solve in ~2s (worst case) and differ from 1deg by
**<0.5%** on global totals (served_people at N=100,000: 8,484M @ 1deg vs 8,514M @ 2deg).
**All four migrated chart files now sweep at 2deg**, not the production 1deg -- the
per-tile utilization MAP (`tile_utilization_map.py`, built earlier this session) still
solves at full 1deg resolution since it only needs a handful of fixed fleet sizes, not
a hundred-point sweep.

**One figure retired outright, not migrated**: `satellite_utilization.py`'s world-map
utilization heatmap. It was already latitude-striped by construction (the old model has
no longitude dimension); `charts/tile_utilization_map.py` already draws the same
question correctly per-tile, so migrating the old one would only produce a worse
duplicate. `git rm`'d `results/population/utilization_heatmap_world.png`.

**One chart pair deliberately left un-migrated, clearly flagged rather than silently
skipped**: `serviceable_customers_per_satellite_chart.py`'s US 1km-vs-100m
population-resolution comparison. It asks a narrow question (does WorldPop raster
resolution change the answer) using the SAME old capacity model on both curves as a
controlled A/B, so the longitude bug cancels out of the comparison between them. A real
2D version would need the US's 100m raster re-streamed into the global tile grid (~10
min pass) AND the US modelled with its real neighbours (Canada/Mexico) instead of in
isolation, which changes what the comparison even measures -- judged not worth rushing.
Both the module docstring and each figure's info box now say so explicitly. (This
comparison's cache file happens to be absent in the current environment anyway, so
`main()` already skips it -- unaffected either way.)

**Verified after regenerating**: `latitude_saturation_heatmap.png` now saturates by
~N=150,000-300,000 instead of needing up to 6-8M -- consistent with the corrected
global model's own saturation point. The asymmetric grey band (uncovered latitudes
start around +83 in the north but only -55 in the south) is real, not a bug: Arctic
settlements have real WorldPop population up to high latitude, Antarctica has none.
`serviceable_customers_vs_satellites_global.png` and `population_connected_vs_capacity
.png` both now saturate at the same point the main model's own headline table shows
(~N=300,000). `servable_density_vs_satellites.png` is an exact straight line on log-log
axes, as expected (the density cap is exactly proportional to N).

## Elasticity pricing mechanism diagram: chained arrows + market-share labels (2026-09-05)

`charts/elasticity_pricing_diagram.py` -> `results/tam/elasticity_pricing_mechanism.png`
existed already (built by another session, illustrates tam_model.py's pricing for one
illustrative "Country A"). User asked for a geometry change: the two arrows used to
diverge from one shared start point (Country A's real position); now they CHAIN --
step 1 (blue) still traces the elasticity curve down from Country A's real position to
y=0 (serving the originally-unconnected population drives %unconnected to 0), and step 2
(red) now starts exactly where step 1 ENDS and runs horizontally to Country A's own
x-coordinate at y=0 (not to the dot itself, which stays at y=60 -- a vertical dotted
guide ties the two together). This reads as a real narrative match to `tam_model.py`'s
two modes: step 1 = mode="unconnected" (captures the original %unconnected share), step 2
= mode="full" (additionally captures the already-connected population at their real
incumbent price). Labelled accordingly: arrow ends say "XX% Starlink market share" (XX =
Country A's original %unconnected) and "100% Starlink market share". Country A's
illustrative numbers changed 30%/5% -> 60%/10%. Legend renamed per request to "Step 2:
Serve existing users and interpolate to incumbent price"; the inline caption explaining
that step was deleted per a same-turn follow-up.

**One real layout bug hit while fixing this**: the market-share labels first placed
ABOVE the y=0 line collided with the diagonal blue arrow, the dashed curve, and each
other at the tight three-line junction near floor_x. Fixed by moving both labels BELOW
y=0 into the axis's small negative margin (`ax.set_ylim(-3, 103)` already provided just
enough room) -- a cleaner fix than nudging either label sideways, since sideways
crowds toward each other while below has empty space.
