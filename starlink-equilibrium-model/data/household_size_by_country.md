# Average household size by country — sources & methodology

Companion to [`household_size_by_country.csv`](household_size_by_country.csv), built
by [`build_household_size_dataset.py`](../build_household_size_dataset.py). Follows
the citation convention from `starlink_shells.md` / `satellite_capacity.md`: every
figure cited with a confidence note.

Researched 2026-08-14, for the TAM-in-dollars model (user request: "how big is a
household?" — needed to convert a population count into a subscription count, since
Starlink sells one subscription per household/premise, not per person).

---

## Source

Wikipedia, ["List of countries by number of households"](https://en.wikipedia.org/wiki/List_of_countries_by_number_of_households)
(fetched 2026-08-14) — itself a compilation of national census and household-survey
figures, one per country, each with its own reference year (ranging 1994-2023 across
the table; most recent census/survey available per country, not a single vintage).
**Confidence: real, sourced per-country figures, but from a secondary
(Wikipedia-compiled) source, not verified against each national statistics office
individually in this research session** — same confidence tier as other
Wikipedia/secondary-compiled tables already used in this project (`starlink_shells.md`'s
shell table drew on Wikipedia the same way).

**Why not the UN Population Division's own database** (the more authoritative
primary source, `population.un.org/household/`)? It's an interactive portal, not a
bulk downloadable table. Tried fetching it directly — the page is JS-rendered and
WebFetch could not reliably extract a complete, accurate table from it (a first
attempt returned implausible values, e.g. "Afghanistan: 11.4", clearly a scraping
artifact of the interactive UI, not a real household-size figure — caught by a
sanity check, not shipped). If a future session needs UN-primary figures instead,
the portal supports per-country CSV/PDF export through its own UI, which would need
to be done manually or via a proper browser-automation fetch, not a plain WebFetch.

---

## Coverage and fallback

**151 of 217 countries** in `telecom_market_by_country.csv` matched directly to a
Wikipedia row (after resolving ~20 country-name differences between Wikipedia's
common names and this project's World Bank-style names — e.g. "Ivory Coast" →
"Cote d'Ivoire", "DR Congo" → "Congo, Dem. Rep.", "Czech Republic" → "Czechia"; see
`NAME_OVERRIDES` in the build script for the full list).

**66 countries with no direct match** (mostly small island states and territories
not in Wikipedia's table — e.g. many Pacific/Caribbean micro-states) get a
**regional median fallback**: the median household size of the OTHER countries in
the same `region` column already used throughout this project. Every region had at
least one directly-sourced country, so no country fell through to a global-median
last resort. Each row's `confidence` column distinguishes
`direct_national_census_or_survey` from `regional_median_fallback` explicitly — the
TAM model and any chart built from this file should treat the fallback rows as
lower-confidence, not silently blend them with the real figures.

**Regional medians** (for context — computed from the direct-match countries only):

| Region | n direct | Median household size |
|---|---|---|
| Sub-Saharan Africa | 40 | 4.88 |
| Middle East, North Africa, Afghanistan & Pakistan | 11 | 5.24 |
| South Asia | 4 | 4.52 |
| East Asia & Pacific | 22 | 3.90 |
| Latin America & Caribbean | 26 | 3.62 |
| Europe & Central Asia | 45 | 2.58 |
| North America | 3 | 2.45 |

The real spread here is large (2.45-5.24, more than 2x) — this is NOT a case where a
single global constant would have been a reasonable shortcut; household size
genuinely varies enough by region that per-country (or at minimum per-region) data
matters for a dollar-denominated TAM figure.

---

## What this means for the TAM model

`household_size_by_country.csv`'s `household_size` column is the divisor turning a
population count into a subscription count:
`addressable_subscriptions = addressable_population / household_size`. This assumes
**one subscription per household** (residential premise), not per person — the
project's working assumption for what a "customer" is throughout (matches
`capacity_density_model.py`'s "subscriber"/"BSL" terminology, itself inherited from
the X-Lab paper's own household-count framing).

**Not modeled: businesses, multi-dwelling buildings needing >1 connection, or
shared/community connections.** A single household-size divisor implicitly assumes
every residential premise needs exactly one subscription and ignores commercial/
enterprise demand entirely — flagged as a real, known simplification for v1 of the
TAM model, not silently assumed away. See `ASSUMPTIONS.md` for the formal entry.
