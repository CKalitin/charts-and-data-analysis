# Starlink revenue estimates by year -- sourcing notes

`starlink_revenue_estimates.csv` -- every publicly available estimate of Starlink's
(and, for context, SpaceX's total) annual revenue this research pass could find,
2021-2026, kept as SEPARATE rows per source rather than reconciled into one number
per year. Multiple estimates for the same year often disagree (e.g. 2022: The
Information's leaked-document figure of $1.4B vs. Payload's bottom-up model of
$1.9B) -- both are kept, not silently picked between, consistent with this
project's established practice elsewhere (`starlink_satellite_cost.csv` keeps both
the 2024 and 2026 v2 Mini cost points rather than overwriting).

## Best available figures, by confidence tier

**Correction (2026-09-05): the first research pass stopped at the S-1 and missed that
SpaceX has actually IPO'd and reports real quarterly earnings now (Nasdaq: SPCX) --
caught by the user asking "we have Q2 results right? ... you didn't search hard
enough," which was correct.** SpaceX's official Q2 2026 earnings release (SEC EDGAR,
filed 2026-08-04) is a real post-IPO quarterly report, not a pre-IPO registration
statement, and gives the most current, most granular data available:

1. **Official (SpaceX's Q2 2026 earnings release, SEC EDGAR 8-K exhibit, filed
   2026-08-04 -- supersedes the S-1 as the most current official source) + the S-1
   registration statement itself (SEC EDGAR, filed/amended 2026-05-20) for full-year
   2023-2025**. Together, the single most authoritative source found:
   | Period | Starlink (Connectivity segment) revenue | SpaceX total revenue | YoY growth |
   |---|---|---|---|
   | FY2023 | $3,869M | $10,387M | -- |
   | FY2024 | $7,599M | $14,015M | +96.4% |
   | FY2025 | $11,387M | $18,674M | +49.8% |
   | Q1 2026 (3mo) | $3,257M | $4,694M | +31.6% |
   | Q2 2026 (3mo) | $4,291M | $7,814M | +66% YoY, +32% sequential |
   | H1 2026 (6mo) | $7,548M | $12,508M | +49.1% YoY |

   **Real finding from the Q2 release, not available at the time of the first
   research pass**: revenue is accelerating, not just growing YoY -- Q2 2026's
   $4,291M is 32% ABOVE Q1 2026's $3,257M in a single quarter. Annualizing Q2 alone
   (x4) implies a ~$17.2B/year run-rate; annualizing H1 (x2) implies ~$15.1B/year --
   both already well above the full FY2025 actual of $11.4B, with two quarters of
   2026 still to report. This puts Quilty Space's $20B full-year-2026 forecast (see
   below) within reach rather than looking aggressive, as it appeared before this
   data existed.

   Also discloses: Starlink Subscribers (FY2023: 2.3M, FY2024: 4.4M, FY2025: 8.9M,
   Q1 2026: 10.3M, **Q2 2026: 12.0M, doubled YoY from Q2 2025's 6.0M**) and Starlink
   ARPU $/month (FY2023: $99, FY2024: $91, FY2025: $81, Q1 2026: $66, **Q2 2026: $66,
   flat quarter-over-quarter for the first time in this series** -- ARPU's steady
   decline appears to have leveled off). Consumer revenue was $2,485M and Enterprise
   & Government revenue $1,806M in Q2 2026 alone -- Enterprise & Government grew
   108% YoY, more than double Consumer's 44% YoY growth, meaning the ACCELERATION in
   total revenue is disproportionately an enterprise/government story, not a
   consumer-subscriber story. Segment Adjusted EBITDA margin: 41% (FY2023) -> 50%
   (FY2024) -> 63% (FY2025) -> 61% (Q2 2026: $2,597M / $4,291M) -- roughly holding at
   the FY2025 level, not still climbing.
   Sources: [SpaceX Q2 2026 earnings release, SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1181412/000162828026052515/earningsreleaseq22608042.htm);
   SpaceX S-1/A#2, SEC EDGAR (`sec.gov/Archives/edgar/data/1181412/...`),
   filed/amended 2026-05-20 (per search results citing this filing date; the
   document itself does not print a single "filed on" date in the extracted text).

2. **Payload Research (Payload Space's own newsletter/research team)** -- named
   analyst, dated, bottom-up model (launch cadence, subscriber counts, terminal
   sales, disclosed government contract values) published after each year closes.
   Two of their year-end estimates (2023: $4.2B, 2024: $8.2B) can now be checked
   directly against the S-1's official numbers above -- both overshot the actual
   figure ($3.869B and $7.599B respectively), by 9% and 8%. Their preliminary 2025
   estimate ($10.4B, published just 16 days after year-end, well before the S-1
   existed) undershot the official $11.387B by about 9%. **Consistent pattern: this
   methodology has landed within roughly +/-10% of the eventual official number in
   all 3 years it can be checked** -- worth remembering as a rough error bar on any
   of Payload's *current-year, not-yet-reported* estimates.

3. **Quilty Space** -- satellite-industry analyst firm, reported via SpaceNews/Via
   Satellite. Their mid-2024 in-year forecast for full-year 2024 ($6.6B) undershot
   the actual $7.599B by about 13%, the largest miss of any estimate checked here --
   consistent with being a forecast made mid-year rather than a full-year
   after-the-fact reconstruction. Their 2026 forecast ($20B) is included but is
   explicitly a forward projection, not yet checkable.

4. **Press reporting of a leaked internal SpaceX document** (Wall Street Journal,
   also re-reported via The Information and Forbes, all citing the same underlying
   leak, Sept 2023) -- the only real pre-2022 data point found ($222M for 2021).
   No independent confirmation exists for this figure; it predates every other
   source in this file by 2+ years.

## What was NOT found

- **No revenue figure for 2019 or 2020** in any source checked -- Starlink's public
  beta began October 2020, so 2019 revenue was effectively $0 and 2020 revenue was
  minimal (a handful of months of beta-only service); no source quantifies it.
- **Payload Space's name was explicitly checked** (the user asked for it by name) --
  found and used (`payloadspace.com`), not to be confused with "Payload Research"
  (their in-house research/analyst arm that authors the estimate articles) or
  Quilty Space (an unrelated, separate analyst firm).

## Sources

- [SpaceX Reports Second Quarter 2026 Results (SEC EDGAR 8-K exhibit, filed 2026-08-04)](https://www.sec.gov/Archives/edgar/data/1181412/000162828026052515/earningsreleaseq22608042.htm)
- [SpaceX revenue surges 92% to $7.8 billion (Fortune, on the Q2 2026 release)](https://fortune.com/2026/08/04/spacex-revenue-surges-92-to-7-8-billion-blowing-past-wall-street-expectations-by-nearly-1-billion/)
- [SpaceX S-1/A#2 (SEC EDGAR)](https://www.sec.gov/Archives/edgar/data/1181412/000162828026040364/spaceexplorationtechnologib.htm)
- [Estimating SpaceX's 2023 Revenue (Payload)](https://payloadspace.com/estimating-spacexs-2023-revenue/)
- [Estimating SpaceX's 2024 Revenue (Payload)](https://payloadspace.com/estimating-spacexs-2024-revenue/)
- [Payload: SpaceX 2025 Revenue Hit $15B (Communications Daily recap)](https://communicationsdaily.com/news/2026/01/16/Payload-SpaceX-2025-Revenue-Hit-15B-2601150038)
- [Starlink On Track to Hit $6.6B in Revenue This Year, Quilty Report Estimates (Via Satellite)](https://www.satellitetoday.com/finance/2024/05/09/starlink-on-track-to-hit-6-6b-in-revenue-this-year-quilty-report-estimates/)
- [SpaceX's Starlink Generated $1.4 Billion in 2022 Revenue (The Information)](https://www.theinformation.com/briefings/spacexs-starlink-saw-1-4-billion-in-2022-revenue)
- [SpaceX's Starlink Revenue Jumps To $1.4 Billion But Falls Short Of Early Targets (Forbes, re: WSJ leak incl. 2021 figure)](https://www.forbes.com/sites/willskipworth/2023/09/13/spacexs-starlink-revenue-jumps-to-14-billion-but-falls-short-of-early-targets-report-says-as-musk-ukraine-controversy-brews/)
- [SpaceX is heavily reliant on Starlink for growth and profit as it marches toward Nasdaq listing (CNBC)](https://www.cnbc.com/2026/05/21/spacex-starlink-growth-profit-nasdaq-ipo.html)
