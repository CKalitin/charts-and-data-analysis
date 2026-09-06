# Revenue & capacity timeline

New, self-contained sub-folder (separate from the main equilibrium model) built for one
request: find every available Starlink revenue estimate vs. date, get Jonathan McDowell's
real satellite-launch data by version and date, and turn the latter into a cumulative
max-capacity-vs-date table with a parallel axis in equivalent Starlink V3 satellites.

## Files

- `data/starlink_revenue_estimates.csv` / `.md` -- every revenue estimate found (SpaceX's
  own S-1 filing, Payload Research, Quilty Space, and WSJ/Information press-leak reporting),
  kept as separate rows per source rather than reconciled, with a confidence-tier writeup.
- `data/starlink_launches_wikipedia_raw.csv` / `starlink_launch_history.md` -- all 424
  real Starlink Falcon 9 launches (2018-2026-09-02) plus the (all-failed, 0-deployed) V3
  Starship test flights, parsed from Wikipedia's raw wikitext (sourced from Jonathan
  McDowell's own launch statistics), with full provenance and cross-check against
  McDowell's own aggregate totals.
- `capacity_timeline_model.py` -- turns the raw launch list into
  `data/cumulative_capacity_vs_date.csv` (cumulative satellites by generation, cumulative
  max Gbps, and equivalent V3 satellites, one row per launch date).
- `build_summary_table.py` -- joins the revenue table and the capacity table into
  `data/revenue_and_capacity_by_year.csv`, one row per calendar year.
- `charts/capacity_vs_date.py` -- `results/capacity_vs_date_log.png` / `_linear.png`.
  x = date. Left axis: cumulative max downlink capacity (Tbps). Right (parallel) axis:
  equivalent V3 satellites (capacity / 1.024 Tbps).
- `charts/revenue_vs_capacity.py` -- `results/revenue_vs_capacity_log.png` / `_linear.png`.
  x = cumulative max downlink capacity (Tbps) at each fiscal year-end, y = Starlink revenue
  ($B/year) for that year. Top (parallel) axis: equivalent V3 satellites, same conversion as
  above. Every individual revenue estimate for a year is plotted as its own point (marker
  shape = source type), with one line through the best-available (official > analyst >
  press) point per year -- same "don't silently reconcile disagreeing sources" convention as
  the revenue CSV itself. Also plots a distinct star marker for the Q2 2026 real quarterly
  revenue, annualized (x4) -- a run-rate, not a full-year actual, styled differently on purpose.
- `charts/revenue_vs_unconnected_tam_overlay.py` -- `results/revenue_vs_unconnected_tam_overlay_log.png`
  / `_linear.png`. Overlays this folder's real revenue data onto the MAIN project's
  "Unconnected Addressable Market" model (`charts/country_tam_charts.py` ->
  `results/market/tam_vs_satellites.png`) -- same x (total satellites, V3-equivalent) and y
  (USD/month) axis definitions, read from that chart's own already-computed CSV snapshot
  (`results/market/tam_by_continent_vs_satellites.csv`) rather than re-running the live model
  (see the script's own docstring for why -- the main project's TAM model code was mid-refactor,
  uncommitted, elsewhere in this repo at the time this was built). Real finding: actual revenue
  tracks almost exactly along the model's curve at today's real satellite counts (~40-855
  equivalent V3 satellites) -- surprising, since actual Starlink revenue includes
  already-connected switchers, enterprise, government, and mobile customers that this
  unconnected-only model doesn't count at all; said explicitly in the chart's own caveat note.

## Headline numbers (as of this research, 2026-09-05)

| Year-end | Cumulative satellites (gross launched) | Cumulative max capacity | Equivalent V3 satellites | Starlink revenue (best available) |
|---|---|---|---|---|
| 2021 | 1,944 | 37.6 Tbps | 36.8 | $222M (press leak) |
| 2022 | 3,666 | 72.1 Tbps | 70.4 | $1.4-1.9B (analyst estimates, disputed) |
| 2023 | 5,650 | 182.9 Tbps | 178.6 | $3,869M (official S-1) |
| 2024 | 7,612 | 371.2 Tbps | 362.6 | $7,599M (official S-1) |
| 2025 | 10,781 | 675.5 Tbps | 659.6 | $11,387M (official S-1) |
| 2026-09-02 (latest) | 12,868 | 875.8 Tbps | 855.3 | Q1: $3,257M, Q2: $4,291M (official quarterly) |

**Real finding worth carrying forward**: capacity has grown roughly 23x since end-2021
(37.6K -> 876K Gbps) while revenue grew about 51x over the same real-vs-estimated window
($222M -> ~$11.4B) -- revenue has outpaced deployed capacity by roughly 2x, consistent with
the official S-1's own disclosed trend of rising ARPU-adjusted monetization per subscriber
being offset by even faster subscriber growth, plus a shift toward higher-value
enterprise/government/mobile revenue (see `starlink_revenue_estimates.md`). **No V3
satellite has reached orbit as of this data pull** -- every Starship/V3 launch attempt
found in the source data has failed to deploy; the "equivalent V3 satellites" axis is a
normalization unit against today's real v1.0+v1.5+v2-mini fleet, not an actual V3 count.

**Correction (2026-09-05)**: SpaceX has actually IPO'd (Nasdaq: SPCX) and reports real
quarterly earnings now -- the first research pass stopped at the pre-IPO S-1 filing and
missed this until the user asked "we have Q2 results right?". Q2 2026 (reported 2026-08-04):
Connectivity segment revenue $4,291M, up 32% SEQUENTIALLY from Q1 2026's $3,257M -- revenue
is accelerating quarter-over-quarter, not just growing YoY. Annualizing Q2 alone implies a
~$17.2B/year run-rate, already close to Quilty Space's full-year-2026 forecast of $20B with
two quarters still to report. See `data/starlink_revenue_estimates.md` for full detail.

## This folder was renamed after it was first created

Originally created as `revenue_capacity_timeline/`; renamed to `spacex_revenue_capacity_timeline/`
partway through the same work session (all file contents carried over unchanged -- confirmed
byte-for-byte before continuing). Every script here resolves its own paths via `Path(__file__)`,
so the rename didn't break anything; only this README's example commands needed updating.

## Regenerate everything

```bash
.venv/bin/python3 spacex_revenue_capacity_timeline/capacity_timeline_model.py
.venv/bin/python3 spacex_revenue_capacity_timeline/build_summary_table.py
.venv/bin/python3 spacex_revenue_capacity_timeline/charts/capacity_vs_date.py
.venv/bin/python3 spacex_revenue_capacity_timeline/charts/revenue_vs_capacity.py
.venv/bin/python3 spacex_revenue_capacity_timeline/charts/revenue_vs_unconnected_tam_overlay.py
```
