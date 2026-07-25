# Canadian cities affordability pilot

Pilot slice of a larger planned analysis (GDP per capita, rent, house price, and wage growth
across a sweep of Canadian and US cities, ranked, to put numbers on "Canadian housing has
decoupled from local income"). This pilot deliberately narrows scope to **2 of 4 metrics**
(house price, wages) and **4 of 16 cities** (Vancouver, Toronto, San Francisco, Los Angeles)
to prove out the data pipeline before scaling up.

## Run
```
python run.py            # pulls data (cached), builds the panel, renders every chart
python run.py --count    # dry-run: print the chart count
```
Each module is independently runnable: `python scrape.py`, `python data_load.py`,
`python charts/timeseries.py`, `python charts/ranking.py`.

## Method
All series run 2005-2024, annual, and are converted to **real (CPI-deflated) indices, base
year 2005 = 100**, in the city's own currency, before comparison — so growth rates are
comparable across currencies even though price *levels* aren't. Deflation:
- US series (Zillow ZHVI, BLS QCEW) are nominal at the source → deflated by US CPI (FRED
  `CPIAUCSL`).
- Canada's wage series (StatCan 11-10-0239-01) is already reported in constant 2024 dollars →
  used as-is. Canada's house-price series (StatCan NHPI) is nominal → deflated by Canadian CPI
  (StatCan 18-10-0004-01).

## Sources
| Series | Source | Table/ID | Coverage |
|---|---|---|---|
| US house price | Zillow ZHVI (all-homes tier) | `Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv` | monthly, 2000+ |
| CA house price | StatCan New Housing Price Index | 18-10-0205-01, total (house+land), 2007=100 | monthly, 1981+ |
| US wages | BLS QCEW, all industries/ownership | annual-by-area bulk files | annual, 1990+ |
| CA wages | StatCan median wage/salary/commission income, individuals 15+ | 11-10-0239-01 | annual, 1976+ |
| US CPI | FRED `CPIAUCSL` | — | monthly |
| CA CPI | StatCan CPI, all-items, Canada | 18-10-0004-01 | monthly |

## ⚠️ Known data-quality issue found by this pilot
**StatCan's New Housing Price Index is the wrong instrument for the "Canadian housing
decoupled from income" question**, and this pilot's own numbers show why: it puts Vancouver's
2005→2024 *real* house-price growth at **+0.3%** — essentially flat — while every resale-market
measure (Teranet, CREA benchmark price) shows Vancouver real estate roughly doubling in real
terms over the same window. NHPI tracks new-construction, quality-adjusted builder selling
prices, which is a fundamentally different (and far more muted) series than what buyers
actually experienced in the resale market. It's a reasonable trend proxy for "new home
construction costs" but understates the affordability story this analysis is trying to test.

**The correct series (Teranet-National Bank HPI, resale-based) could not be pulled**: the
vendor's own site (`housepriceindex.ca`) serves an incomplete TLS certificate chain — confirmed
as a genuine server-side misconfiguration, not a proxy issue, and not something to route around
by disabling certificate verification. Before scaling to the full 16-city sweep, the Canadian
house-price source needs to change to one of:
- Teranet HPI via a properly-configured mirror or a manually-downloaded file, or
- CREA's MLS Home Price Index (no public API; would need a manual export), or
- StatCan's NHPI kept only as a labeled secondary series, not the headline house-price number.

US-side data (Zillow ZHVI, BLS QCEW) checks out against known history: both cities show the
2008-2012 crash and recovery at plausible magnitudes.

## Pilot findings (as-computed, with the caveat above)
Cumulative real growth, 2005-2024:

| City | House price | Wages | Gap (house − wage, pp) |
|---|---|---|---|
| Los Angeles | +12.2% | +10.9% | **+1.3** |
| Toronto | +12.3% | +13.6% | −1.3 |
| Vancouver | +0.3%* | +24.3% | −24.1* |
| San Francisco | +18.9% | +43.8% | −24.9 |

\* Vancouver's house-price figure is the NHPI artifact described above — treat as unreliable
until the resale-price source is swapped in.

The SF result is real and interesting on its own: even in one of the most expensive housing
markets in North America, QCEW's average wage (heavily skewed by tech compensation) grew
faster than real house prices over this specific window — largely because 2005 was near a
local price peak just before the 2008 crash, and tech wages have risen sharply since.

## Outputs
- `outputs/timeseries/<city>.png` — house price vs. wage index, one panel per city
- `outputs/ranking/house_price_index_overlay.png` — all 4 cities' house-price trajectories, one axes
- `outputs/ranking/decoupling_gap_ranking.png` — cumulative gap ranking

## Next steps
1. Resolve the Canadian house-price source (see caveat above).
2. Re-run the pilot with the corrected series and re-check whether Vancouver/Toronto still
   look muted relative to Teranet's known resale trend.
3. Scale to the full 16-city sweep and add the remaining two metrics (GDP per capita, rent).
