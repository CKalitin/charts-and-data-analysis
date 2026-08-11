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
**Why it exists**: user asked for satellite coverage RADIUS ("how far to the sides
can you see"), which requires a minimum usable elevation angle — a user terminal
can't use a satellite too close to the horizon. 25° is the long-standing, widely-
cited Starlink minimum. Checked whether the FCC's 2026-04 STA ruling (which lowers
the minimum to 10-20° for satellites below 500km) supersedes this: it doesn't for
THIS project's real shells, since Gen1's shells are all ≥540km, above every lowered
tier. Cross-validated the resulting geometry against two independently published
figures for the 550km shell (25° → ~941km computed vs. ~900km cited; 40°, kept as
`ALT_MIN_ELEVATION_DEG`, → ~574km computed vs. ~580km cited) — both matched closely.
**Impact if wrong**: directly rescales the coverage radius (and therefore the
range-extended satellite density charts) — a lower elevation angle (as the 2026
ruling allows for lower shells) would give a LARGER radius; a stricter figure like
40° gives a ~40% smaller radius. Does not affect any other chart in this project —
only `charts/satellite_range_coverage.py`'s outputs depend on this constant.

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
