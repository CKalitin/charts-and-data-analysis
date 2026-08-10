# Country-level telecom market dataset — sources & methodology

Companion to [`telecom_market_by_country.csv`](telecom_market_by_country.csv) (217
rows: World Bank's full country/economy list, i.e. sovereign states plus a handful of
territories WB tracks separately — e.g. Puerto Rico, Hong Kong SAR — excludes only
WB's own regional/income-group aggregates). Built by
[`../build_telecom_dataset.py`](../build_telecom_dataset.py); raw source files are
kept in [`raw/`](raw/) for reproducibility.

Follows the citation convention from
`Reflect-Orbital/sso-land-proximity/data/reflect_orbital_sources.md`: every figure
gets a source and a confidence note. Nothing here is fabricated — fields with no
public bulk source are either derived with an explicitly documented assumption, or
left blank/flagged, never silently filled in.

---

## Fields sourced directly, well-sourced (bulk, no paywall)

**`population`** — World Bank indicator `SP.POP.TOTL`, most recent non-empty value
per country (mostly 2023-2025). Ultimate source is UN World Population Prospects.
https://data.worldbank.org/indicator/SP.POP.TOTL — 217/217 countries covered.

**`internet_user_pct`** — World Bank `IT.NET.USER.ZS` ("Individuals using the
Internet, % of population"). https://data.worldbank.org/indicator/IT.NET.USER.ZS —
213/217 covered (4 missing: mostly territories with no ITU submission).

**`fixed_broadband_subs_per_100`** — World Bank `IT.NET.BBND.P2`.
https://data.worldbank.org/indicator/IT.NET.BBND.P2 — 208/217 covered.

**`mobile_subs_per_100`** — World Bank `IT.CEL.SETS.P2`.
https://data.worldbank.org/indicator/IT.CEL.SETS.P2 — 214/217 covered.

**`gni_per_capita_ppp_usd`** — World Bank `NY.GNP.PCAP.PP.CD` (GNI per capita, PPP,
current international $). https://data.worldbank.org/indicator/NY.GNP.PCAP.PP.CD —
used only as the denominator for the affordability field below.

All four World Bank indicators pulled via the bulk API
(`api.worldbank.org/v2/country/all/indicator/{CODE}?format=json&mrnev=1`,
"most recent non-empty value" per country) — raw JSON responses in `raw/wb_*.json`.
World Bank's telecom indicators are themselves sourced from ITU, so these numbers are
one step removed from ITU's primary collection, not independently surveyed by WB.

**`fixed_broadband_usd_per_month`** — average monthly cost of a fixed broadband
contract in USD, from the **broadband.co.uk Global Broadband Price League, February
2026 edition** (2,631 tariffs surveyed across 214 countries, sample dates ~Feb 4-6
2026). https://www.broadband.co.uk/global-broadband-price-league — raw file:
`raw/broadband_pricing_2026.xlsx`. **Confidence: analyst survey, not
regulator-verified.** Convenience sample of advertised retail tariffs, not
usage-weighted or subscriber-weighted — a country with a handful of very cheap or
very expensive plans sampled can skew the average. 20 countries have no row (mostly
low-income/conflict-affected states with too few advertised broadband plans to
survey: Chad, CAR, DR Congo, Cabo Verde, Cuba, Djibouti, Eritrea, Guinea,
Guinea-Bissau, Kiribati, Niger, Nauru, North Korea, West Bank & Gaza, Sudan, São
Tomé & Príncipe, Tuvalu, Kosovo, St. Martin, Channel Islands) — left blank, not
estimated.

**`mobile_usd_per_gb`** — average price of 1GB of mobile data in USD, from the
**bestbroadbanddeals.co.uk (formerly cable.co.uk) Worldwide Mobile Data Pricing
study, 2023 vintage** (237 countries surveyed, ~5,600 plans, sample dates mostly
mid-2023). https://www.bestbroadbanddeals.co.uk/mobiles/worldwide-data-pricing/ —
raw file: `raw/mobile_data_pricing_2023.xlsx`. **Confidence: analyst survey, 2023
data — flagged as stale relative to the Feb-2026 broadband figures above; global
average $/GB has historically fallen over time, so 2023 mobile prices likely
overstate current cost in fast-improving markets.** 4 countries excluded by the
source itself with a stated reason (not a match failure): Bulgaria ("all unlimited,
no average-use data" — see note below), Eritrea and North Korea ("no providers"
surveyable), Channel Islands not separately surveyed.

---

## Fields derived with an explicitly documented assumption

No bulk source gives both $/month AND $/GB for the same access type in the same
country, so two fields are cross-derived using a single global illustrative
usage-volume assumption — **these are NOT per-country data, they are one flat
assumption applied everywhere**, and should be replaced the moment a real per-country
usage dataset is found:

- **`fixed_broadband_usd_per_gb_illustrative`** = `fixed_broadband_usd_per_month` /
  **300 GB/month** (a round illustrative global household usage figure; actual usage
  varies enormously by country, roughly 100s of GB in high-income markets to much
  less where fixed broadband is a minority service).
- **`mobile_usd_per_month_illustrative`** = `mobile_usd_per_gb` x **10 GB/month** (a
  round illustrative global mobile usage figure).

Treat both illustrative columns as order-of-magnitude only, useful for ranking
countries relative to each other, not as a precise "what a typical bill looks like"
number.

**Unlimited plans:** the source surveys' own methodology (per their published notes)
already handles unlimited fixed-broadband plans by using the plan's advertised price
directly (no per-GB conversion needed at the source level for the $/month field).
Bulgaria was excluded entirely from the *mobile* $/GB dataset because, per the
source's own flag, its mobile market is "all unlimited, no average-use data" — there
was no way for the source to derive a $/GB figure at all, so it's blank here too, not
estimated.

---

## Fields derived, no assumption needed

**`unconnected_population_est`** = `population` x `(1 - internet_user_pct/100)`.
ITU's own "Facts and Figures" report (https://www.itu.int/itu-d/reports/statistics/facts-figures-2025/)
gives a 2.2-billion-offline headline figure but only breaks it down by region/income
group, not by country — so country-level unconnected population has to be derived
from the World Bank internet-use indicator rather than cited directly. Blank where
`internet_user_pct` is missing. **This is a USAGE-gap metric, not a coverage-gap
metric — see the corrected column below, which should be preferred for anything
about Starlink's addressable market.**

**`unconnected_population_est_coverage_corrected`** (added 2026-08-09, user-requested
fix for the adoption-vs-coverage-gap issue flagged when this dataset was first
built): for **High income** countries only, floors the effective connected % at
**`HIGH_INCOME_COVERAGE_FLOOR_PCT = 97.0`** (i.e. `unconnected = population x (1 -
max(internet_user_pct, 97) / 100)`) before computing unconnected population; all
other income tiers are unchanged from `unconnected_population_est`. **Rationale**:
World Bank's `internet_user_pct` counts non-use for ANY reason (age, digital
literacy, personal choice), not just lack of infrastructure — high-income countries
have near-universal terrestrial coverage almost by definition of that income
classification, so their full usage gap overstates what Starlink could realistically
address (the exact problem originally flagged: France ~11.3%, Italy ~10.8%
"unconnected" despite full coverage). **This is a targeted, documented ASSUMPTION,
not measured data** — no accessible country-level coverage-gap dataset was found:
ITU DataHub blocks automated fetch (403, confirmed twice in this project — see
Phase 2's `starlink_shells.md` research notes for the first instance), and GSMA
Mobile Connectivity Index's historical bulk-export URL pattern (`MCI_Data_{year}.xlsx`,
worked for 2020) returns 404 for 2024-2026. The 97% floor is a reasonable
assumption for "near-universal high-income-country coverage," not a cited figure —
if a future session finds real per-country coverage-gap data, replace this
correction rather than keep the assumption. **Effect**: individual high-income
countries drop substantially (France 7.8M -> 2.1M, Italy 6.4M -> 1.8M, US 18.1M ->
10.3M, Japan 17.8M -> 3.7M) but the GLOBAL total barely moves (2.29B -> 2.23B, -2.5%)
since most of the world's unconnected population was never in the high-income
bucket to begin with — the correction matters a lot per-country, very little in
aggregate. **Every chart/finding elsewhere in this project that used the original
`unconnected_population_est` should be treated as using the USAGE-gap number, not
Starlink's realistic addressable market** — charts rebuilt after 2026-08-09 use the
corrected column instead; see `CLAUDE.md` for which ones were and weren't rebuilt.

**`cellular_dominant_market`** (boolean) = fixed-broadband penetration is very low in
absolute terms (<5 per 100) OR far below mobile penetration (fixed/mobile ratio <
0.08). This is a threshold judgment call, not a labeled source field — no dataset
directly states "is this market cellular-dominant." The thresholds are a reasonable
first pass, not calibrated against a ground-truth list; revisit if a phase-2/3 model
result looks sensitive to exactly where the line is drawn.

**`connectivity_cost_pct_of_gni`** = `fixed_broadband_usd_per_month x 12 / gni_per_capita_ppp_usd x 100`.
A rough affordability indicator in the same spirit as ITU's ICT Price Basket
methodology (which expresses basket price as % of GNI per capita) — not ITU's actual
published basket value, just a locally-computed analog using the broadband.co.uk
price instead of ITU's own basket price. Blank wherever the broadband price is
missing.

---

## Field with NO bulk source at all — hand-coded, not sourced

**`legacy_satellite_isp_present`** (boolean) — whether a legacy GEO satellite
broadband ISP (Viasat, HughesNet, Eutelsat Konnect, NBN Sky Muster, etc.) has a
meaningful commercial presence in that country. **Confidence: qualitative judgment
from public knowledge of these operators' known coverage footprints, not a sourced
number.** Research (see `CLAUDE.md`) confirmed there is no public bulk country-level
dataset for legacy satellite ISP subscriber share — Viasat/EchoStar SEC filings
report US-only subscriber totals (e.g. Viasat ~257,000 US residential subscribers,
Q1 2025, down sharply post-Starlink, per public financial press coverage), and
industry analyst reports (Euroconsult/Novaspace, NSR) publish only regional/global
aggregates behind a paywall, not country tables. Currently flagged `True` only for
markets with a well-known national or large-scale GEO satellite broadband program:
US, Canada, Mexico, UK, France, Germany, Italy, Spain, Poland, Romania, Greece,
Portugal, Ireland, Australia, New Zealand, Brazil, India. **Every other country is
`False` by default, which almost certainly undercounts smaller/regional operators —
treat this column as "known-large-presence" not "no satellite ISP exists here."**
Do not treat this as authoritative without a follow-up pass.

---

## What Phase 2/3 should NOT assume this dataset already covers

- No sub-national/regional breakdown (user explicitly chose country-level).
- No satellite-specific competitor pricing (this is legacy/GEO presence only, a
  boolean, not a $/GB comparison — that would need a separate research pass).
- No time series — every field is a single latest-available snapshot, vintages differ
  by field (broadband prices Feb 2026, mobile prices 2023, WB indicators mostly
  2023-2025) and are NOT all the same reference year. Do not chart these as if they
  were contemporaneous without noting the vintage mismatch.
