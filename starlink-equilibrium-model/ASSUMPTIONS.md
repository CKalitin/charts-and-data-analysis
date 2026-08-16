# Model assumptions — full list

Every numeric assumption in this project that was picked by Claude rather than
measured or confirmed by the user, in one place. Companion to `CLAUDE.md` (which has
the fuller narrative per phase) — this file exists so the user can review and
confirm/override assumptions without hunting through six `.md` files and a dozen
`.py` modules to find them.

**How to use this file**: the "Not yet confirmed" section is the one that actually
needs your attention — each entry changes real numbers in the charts if you disagree
with it. The "Confirmed" section is a log of decisions you already made; it's here
for completeness, not because it needs another look.

---

## Not yet confirmed by the user (review these)

### 1. Satellite lifetime = 5 years
**Where**: `equilibrium_model.py`, `SATELLITE_LIFETIME_YEARS = 5.0`
**Why it exists**: Phase 4's cost-to-orbit is a one-time capex figure ($/Gbps);
Phase 1's ARPU is recurring monthly revenue. To find an equilibrium the two have to
be on the same time basis, so cost is divided by an assumed satellite lifespan to
annualize it. **A commonly cited Starlink design-life figure, not verified
per-generation.**
**Impact if wrong**: linear and direct — a 10-year lifetime would halve the
annualized cost line, roughly doubling every equilibrium capacity/satellite-count
number in `results/equilibrium/equilibrium_revenue_vs_cost.png`.

### 2. Customers-per-Gbps ratio applied to every generation
**Where**: `equilibrium_model.py`, `CUSTOMERS_PER_GBPS = 6704 / 96.0 ≈ 69.8`
**Why it exists**: Phase 3's density-ceiling derivation (X-Lab/Penn State paper) is
specific to v2 Mini's beam count and contention assumptions. No equivalent
derivation exists for v1.0 or v3, so this ratio is carried over unchanged, assuming
beam/contention characteristics scale proportionally with raw Gbps capacity across
generations. **Not verified for any generation except v2 Mini.**
**Impact if wrong**: directly rescales `gbps_needed` for every country, and
therefore every equilibrium satellite count.

### 3. The underlying density/capacity scenario itself
**Where**: `capacity_density_model.py`, `V2_MINI_BEAD_SCENARIO` (1.5° beamwidth, 550
km altitude, 20:1 contention, US 100/20 Mbps broadband threshold)
**Why it exists**: this is the ONE fully-worked density derivation found in public
research (see `data/satellite_capacity.md`) — inherited wholesale from that source,
not chosen independently. The source paper itself frames these as assumptions, not
disclosed SpaceX specs. An alternate scenario in the same source ("tighter
overlapping beams") gives a density ceiling ~4.5x looser (see
`results/capacity/density_ceiling_sensitivity.png`).
**Impact if wrong**: this is the single highest-leverage assumption in the whole
project — it sets the density cap that decides whether 161 of 204 countries are
population-bound or density-bound in the equilibrium model, and Phase 3's headline
"~31x capacity gap" finding.

### 4. ARPU cap = $100/month
**Where**: `equilibrium_model.py`, `ARPU_CAP_USD_MONTH = 100.0`
**Why it exists**: a small number of countries' survey-derived pricing (Zimbabwe
$437/mo, Turkmenistan $286/mo, etc.) is implausible for those economies — a known
"thin sample size" artifact already documented in `telecom_market_by_country.md`.
$100 was chosen as "just above the US's own real $80/mo," not derived from anything.
**Impact if wrong**: only affects the 15 capped countries (listed via
`CountryDemand.arpu_capped`); a materially different cap would move where those
countries sit in the revenue ranking and how much of the flat top segment of
`equilibrium_revenue_vs_cost.png` they represent.
**UPDATE (2026-08-09, found while explaining Phase 6's market-ladder chart to the
user)**: this is worse than "just a rounding choice." All 15 capped countries tie at
EXACTLY $100/month, so they occupy the very TOP of the ARPU ranking — ahead of every
real high-income market including the US ($80/mo real data, doesn't crack the top 15).
6 of the 15 are conflict/fragile economies whose PRE-CAP data was implausible (Central
African Republic, South Sudan, Yemen, Turkmenistan, Syria, Zimbabwe — $150-437/mo).
The model's "highest-value tier" is currently a data-quality artifact, not a
genuine premium signal, and it's also being used as the (only) stand-in for
"rural/remote high-income demand pays a premium" — which the model does not
otherwise represent at all. Two fixes proposed to the user, not yet decided: (A)
drop capped countries from the top of the ranking / use a regional-median fallback
instead of the flat $100 ceiling, (B) add a genuine remote-premium multiplier for
high-income countries as a new, separate mechanism. See CLAUDE.md's Phase 6 section
for the full writeup and per-country numbers.

### 5. ARPU proxy = incumbent's own price, not a discount to it
**Where**: `equilibrium_model.py`, `build_country_demand()` — uses
`fixed_broadband_usd_per_month` or `mobile_usd_per_month_illustrative` directly as
the achievable revenue ceiling per customer.
**Why it exists**: simplest available proxy for "what Starlink could plausibly
capture per customer" without a stated pricing strategy from the user. **Does not
model any competitive undercutting** — in reality Starlink would likely need to
price at or below the incumbent to win share, which would lower every revenue
figure in the model.
**Impact if wrong**: revenue curve is systematically optimistic if Starlink can't
actually charge the full incumbent price; every equilibrium point would shift left
(smaller) under a discounted-pricing assumption.

### 6. Density cap applied to whole-country land area, not populated area
**Where**: `equilibrium_model.py`, `DENSITY_CAP_PER_KM2 x land_area_km2`
**Why it exists**: no per-country urban/populated-area dataset was pulled — total
land area (World Bank `AG.LND.TOTL.K2`) was the readily available figure.
**Impact if wrong — this one is subtle and probably matters**: real population
concentrates in a fraction of a country's total land area (cities, arable land),
so true LOCAL density where people actually live is higher than population/total-area
suggests. Averaging the density cap over the whole country likely OVERSTATES
addressable customers for large countries with concentrated population (e.g. Egypt,
where ~95% of people live on ~5% of the land near the Nile) — the real
density-constrained ceiling in populated regions is probably tighter than this model
currently computes. This assumption biases the demand curve upward (optimistic),
opposite direction from assumption #5.

### 7. High-income coverage floor = 97%
**Where**: `build_telecom_dataset.py`, `HIGH_INCOME_COVERAGE_FLOOR_PCT = 97.0`
**Why it exists**: corrects the France/Italy adoption-vs-coverage-gap problem (Phase
1) by assuming near-universal infrastructure coverage in High income countries. No
real per-country coverage-gap dataset was found (ITU DataHub and GSMA MCI both
inaccessible — see `telecom_market_by_country.md`).
**Impact if wrong**: only affects High income countries' `unconnected_population_est_coverage_corrected`
— global total is insensitive (2.29B -> 2.23B) but individual country figures shift
substantially (France 7.8M -> 2.1M unconnected).

### 8. Illustrative usage volumes for $/GB <-> $/month conversion
**Where**: `build_telecom_dataset.py`, `ASSUMED_FIXED_BROADBAND_GB_PER_MONTH = 300.0`,
`ASSUMED_MOBILE_GB_PER_MONTH = 10.0`
**Why it exists**: no per-country usage-volume dataset exists at the granularity
needed; these are round, globally-illustrative figures, not measured.
**Impact if wrong**: affects `fixed_broadband_usd_per_gb_illustrative` and
`mobile_usd_per_month_illustrative` columns specifically — flagged in
`telecom_market_by_country.md` as "compare shape only, not exact values" for exactly
this reason. Does NOT affect the equilibrium model (which uses `_month` prices
directly, not the derived `_gb` ones).

### 9. Coverage gate at 82.4° latitude
**Where**: `equilibrium_model.py`, `MAX_COVERAGE_LAT_DEG = 82.4`
**Why it exists**: Gen1's near-polar shell's actual max latitude (real data, not a
guess — see `starlink_shells.md`). Applied as a hard country-inclusion filter.
**Impact if wrong**: minimal — no populated country's capital sits beyond 82.4°, so
this excludes ~nothing in practice. Listed for completeness, not because it's a
live risk.

### 10. No J2/orbital-perturbation correction
**Where**: `orbital_geometry.py`, module docstring
**Why it exists**: simplified circular-orbit geometry is adequate for market-sizing
(Phase 2/3's purpose) and was cross-checked against real Starlink's ~95 min period
(matched). Not adequate for actual satellite operations.
**Impact if wrong**: low — this is a documented simplification for a market model,
not a navigation system; the cross-check against real orbital period suggests the
error is small for this project's purposes.

### 11. Minimum elevation angle = 25° (ground coverage radius geometry)
**Where**: `orbital_geometry.py`, `MIN_ELEVATION_DEG = 25.0`
**Clarification (added 2026-08-13, was unclear before)**: this is the GROUND
TERMINAL's (the user's dish's) angle, not the satellite's — measured at the dish,
between its local horizon and the line of sight up to the satellite. A different
quantity from the satellite's own off-nadir/look angle (`off_nadir_angle_deg()`).
Confirmed from Geoff Huston's source slide, titled "Looking Up," and from
Starlink's own dish diagnostic tool reporting a `direction_elevation` field —
elevation is something the dish measures, not a satellite-side spec. Full detail
in `data/starlink_coverage_geometry.md`.
**Why it exists**: user asked for satellite coverage RADIUS ("how far to the sides
can you see"), which requires a minimum usable elevation angle — a user terminal
can't use a satellite too close to the horizon. 25° is the long-standing, widely-
cited Starlink minimum. Checked whether the FCC's 2026-04 STA ruling (which lowers
the minimum to 10-20° for satellites below 500km) supersedes this: it doesn't for
THIS project's real shells, since Gen1's shells are all ≥540km, above every lowered
tier. Cross-validated the resulting geometry against two independently published
figures for the 550km shell (25° → ~941km computed vs. ~900km cited; 40°, kept as
`ALT_MIN_ELEVATION_DEG`, → ~574km computed vs. ~580km cited) — both matched closely.
**Sourcing, dug deeper 2026-08-13 (user pushback: "that 25 degree number is not
official from Huston, unless it cites a source but I can't see one")**: correct —
re-checked Huston's slides directly and confirmed 25° has NO visible citation
there, stated as a bare fact. Traced through Shkelzen Cakaj, *"The Parameters
Comparison of the 'Starlink' LEO Satellites Constellation for Different Orbital
Shells,"* Frontiers in Communications and Networks, vol. 2, article 643095
(2021), whose own citation for the figure was just "Starlink (2020)" — **then,
same day, following up on "has SpaceX through FCC released anything," pulled and
read the actual FCC order text directly** (`docs.fcc.gov/public/attachments/fcc-21-48a1.pdf`,
extracted with `pypdf` after WebFetch's own PDF reader failed on it): **FCC Order
21-48**, approving SpaceX's Third Modification Application (SAT-MOD-20200417-00037,
filed April 17, 2020 — the likely referent of "Starlink (2020)"). Footnote 3,
verbatim: *"SpaceX is authorized to operate with earth station elevation angles
as low as 25 degrees for user terminals and gateways, and for gateways in the
polar regions ... as low as five degrees."* This is a primary source, not a
summary — 25° is the actual FCC-AUTHORIZED figure, tied explicitly in the order's
body text to the same altitude change (→540-570km) that produced this project's
real Gen1 shells. Also reconciles an apparent conflict found along the way: an
APNIC blog post states Starlink's ORIGINAL 2016 filing specified 40° (for
terrestrial-microwave interference protection, a different reason) — both are
real, just two different points on the same regulatory timeline (2016: 40°;
2020 request / 2021 grant: lowered to 25°). **Checked what public Starlink
tracker websites use** (the user's other question): starlink.sx has a
user-adjustable elevation setting rather than a fixed number; orbitalradar.com
computes elevation as a per-viewer result but doesn't publish its cutoff —
neither site converges on a single public "the number," which is fine, since this
project now has the primary FCC authorization directly. **Confidence: directly
confirmed from FCC order text** — upgraded from "well-attested, traced to an
unopened filing" a few hours earlier. Full chain and quotes in
`data/starlink_coverage_geometry.md`.
**Impact if wrong**: directly rescales the coverage radius (and therefore the
range-extended satellite density charts and the per-satellite density-cap model's
density term) — a lower elevation angle (as the 2026 ruling allows for lower
shells) would give a LARGER radius; a stricter figure like 40° gives a ~40%
smaller radius. Affects `charts/satellite_range_coverage.py`'s outputs directly,
plus (as of 2026-08-12) `serviceable_customers_model.py`'s
`sats_reaching_latitude()` / `effective_density_cap_by_latitude()` and everything
downstream (the per-satellite-cap serviceable-customers charts and the latitude
saturation heatmaps) — does not affect the aggregate-capacity term or any chart
outside this family.

### 12. V3 density-cap geometry uses v2 Mini's beam count/beamwidth as a placeholder
**Where**: `capacity_density_model.py`, `V3_SCENARIO` (`beams_per_satellite=16`,
`beamwidth_deg=1.5`, both copied from `V2_MINI_BEAD_SCENARIO`)
**Why it exists**: user asked to switch the serviceable-customers model
(`serviceable_customers_model.py` and its charts — NOT the earlier Phase 3/5
`capacity_density.py` / `population_capacity_overlay.py` charts, left on v2 Mini)
to V3. V3's TOTAL per-satellite capacity is real, sourced data (1,024 Gbps
downlink / 200 Gbps uplink, per `satellite_capacity.md`, cross-confirmed against
`cheatsheets.davidveksler.com`'s V1-V3 comparison). Its **beam count and
beamwidth are not publicly disclosed** — confirmed by that same davidveksler.com
source, which explicitly flags V3 beam-level specs as undisclosed. One single-source
claim of "2,048 beams" (a tweet quoting SpaceX, via Sawyer Merritt) surfaced during
research but conflicts with this project's own cross-confirmed v2 Mini beam count
(16) by two orders of magnitude depending on interpretation, isn't independently
corroborated, and wasn't used.
**What was done**: reused v2 Mini's beam count (16) and beamwidth (1.5°) as an
explicit placeholder, altitude set to V3's own real figure (345km, midpoint of the
330-370km planned range). `downlink_gbps_per_beam` and `uplink_gbps_per_beam` are
therefore DERIVED (1024/16 and 200/16), not independently sourced numbers.
**Impact if wrong — asymmetric, read carefully**: `max_customers_per_satellite()`
(the aggregate cap driving most of the serviceable-customers charts) is
**UNAFFECTED** by this placeholder — `beams_per_satellite` and
`downlink_gbps_per_beam` only ever appear multiplied together in that formula, and
their product is pinned to V3's real, sourced total (1,024 Gbps), regardless of
the true beam count. `max_customer_density_per_km2()` (the areal cap, feeding
`effective_density_cap_by_latitude()` and the per-satellite-cap model's density
term) **IS directly affected** — a real V3 beam count of, say, 192 or 2,048
instead of 16 would change the per-beam footprint's implied capacity substantially,
and this project has NOT independently derived which is closer to reality.
Treat any DENSITY-specific V3 number in this project's output with more caution
than the AGGREGATE-capacity numbers, until real V3 beam data is published.

### 13. Household size by country — secondary-sourced, 66/217 countries on a regional fallback
**Where**: `data/household_size_by_country.csv` (built by `build_household_size_dataset.py`),
used in `country_tam_model.py` to convert addressable population into addressable
subscriptions (`addressable_subscriptions = addressable_population / household_size`).
**Why it exists**: TAM is denominated in dollars per SUBSCRIPTION (one per
household), not per person — the user's own framing ("hence why households /
subscriptions per person is an important metric"). No such data existed in this
project before 2026-08-14.
**Source**: Wikipedia's "List of countries by number of households" (itself a
compilation of national census/survey figures, one per country, various reference
years 1994-2023) — 151 of 217 countries matched directly; the other 66 (mostly
small island states/territories) get a **regional median fallback** computed from
the region's own directly-sourced countries (same `region` column used throughout
this project), flagged per-row via a `confidence` column
(`direct_national_census_or_survey` vs. `regional_median_fallback`) — never
silently blended. Full detail, including why the UN Population Division's own
(more authoritative) database wasn't used instead (an interactive portal, not a
bulk download; a first WebFetch attempt returned an implausible value and was
caught, not shipped), in `data/household_size_by_country.md`.
**Not modeled**: businesses, multi-dwelling buildings needing more than one
connection, or shared/community connections — one household = one subscription,
uniformly, a real simplification for v1 (the user's own question: "What if it's a
building/company?" — not yet answered with a separate mechanism).
**Impact if wrong**: directly, linearly rescales addressable subscriptions (and
therefore TAM$) for every country — a country using the regional-fallback value
is more exposed to this than a directly-sourced one. The real range is large
(regional medians span 2.45-5.24 people/household), so getting this wrong for a
populous country materially moves that country's TAM.

### 14. TAM pricing rule: existing local price below 20% unconnected, elasticity-derived price above
**Where**: `country_tam_model.py`, `_country_price()`, `UNCONNECTED_PCT_THRESHOLD = 20.0`.
**User-specified rule, not derived**: below 20% unconnected, price = the country's
own existing incumbent price (`_raw_arpu()` — fixed or mobile, same selection logic
as `equilibrium_model.py`); at/above 20% unconnected, price is instead DERIVED by
inverting the elasticity curve (`served_population_vs_cost.py`'s
`cost_pct_from_pct_unconnected()`) using this country's OWN capacity-constrained
servable-% (from `country_service_model.py`) as the target "% unconnected at this
price" — i.e., the satellite capacity constraint determines a market-clearing
price via the demand curve, rather than assuming the existing (presumably
too-expensive, hence the high unconnected rate) local price would hold.
**A design choice made, not asked about**: `addressable_population =
min(unconnected_population, servable_fraction(N) x total_population)` is applied
identically regardless of which price branch a country falls into — the 20%
threshold only picks WHICH PRICE to charge, not whether the capacity constraint
applies. This seemed the only internally-consistent reading, but wasn't a separate
explicit user decision — worth double-checking if the below-20% branch's numbers
look off.
**Impact if wrong**: for elasticity-priced countries specifically, price is only as
good as the user-specified elasticity anchors themselves (0.75% cost -> 0%
unconnected, 10% -> 100%, chosen not fit — see `charts/served_population_vs_cost.py`'s
own docstring) AND this project's own capacity model's servable-% estimate. Errors
compound: a wrong servable-% feeds a wrong target-%-unconnected, which feeds a
wrong price via the (already-approximate) elasticity curve.

### 15. Full-world TAM: 100% share capture inside footprint, proportional connected/unconnected split
**Where**: `country_tam_full_model.py`, `compute_country_tam_full()`.
**User-specified rule, confirmed via AskUserQuestion, 2026-08-16**: within a
country's servable_fraction(N) footprint, Starlink is assumed to capture 100% of
that population's telecom business (no switching-friction/partial-adoption curve
-- the "just takes incumbent share" framing, taken literally). The user explicitly
declined the offered alternative (a partial-adoption ceiling below 100%).
**A design choice made, not separately asked about**: no sub-national data exists
to know WHICH specific people within a density bin (a latitude x population-density
cell) are already connected vs. unconnected, so the servable population is split
into "incumbent" (already-connected, priced at `_raw_arpu()`) and "new" (previously
unconnected, priced via `country_tam_model._country_price()`) segments
PROPORTIONALLY to the country's own overall connected/unconnected ratio --
`addressable_connected = servable_fraction x connected_population`,
`addressable_unconnected = servable_fraction x unconnected_population`. This
assumes Starlink's capacity-constrained reach doesn't systematically favor already-
connected (typically denser, urban) or unconnected (typically sparser, rural)
people within the same density bin -- plausible as a first cut, not verified.
**Impact if wrong**: if in reality Starlink's footprint at low N disproportionately
reaches already-connected urban areas (e.g. dense demand competes for capacity
first) rather than a proportional mix, the "incumbent" segment's revenue share
would be understated early in the N sweep and the "new" segment's overstated, or
vice versa if unconnected rural areas are reached first. Does not affect the TOTAL
addressable population (`servable_fraction x population`), only how it's split
between the two price mechanisms.

---

## Confirmed by the user (locked in, listed for completeness only)

These were explicit user decisions, not modeling choices — see `CLAUDE.md`'s
"Decisions locked in so far" section for the full record. Not open for review here,
just listed so this file is a complete picture of every number in the model:

- Cost metric: **$/Gbps**, not $/satellite.
- Launch cost pairing: F9 internal marginal cost (v1.0/v1.5/v2 Mini), Starship
  initial + end-state scenarios (v3).
- Manufacturing cost: **latest known figure** per generation, not an average.
- Required margin: **20%**.
- Geographic granularity: **country-level**.
- Satellite capacity/density constraints: **required**, not optional.
- Coverage-gap correction: **yes, apply it** (led to assumption #7 above).
