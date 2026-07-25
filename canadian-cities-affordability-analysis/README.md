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
  used as-is. Canada's house-price series (CREA MLS HPI benchmark price) is nominal → deflated
  by Canadian CPI (StatCan 18-10-0004-01).

## Sources
| Series | Source | Table/ID | Coverage |
|---|---|---|---|
| US house price | Zillow ZHVI (all-homes tier) | `Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv` | monthly, 2000+ |
| CA house price | CREA MLS HPI, composite benchmark price (resale market, by real estate board) | `crea.ca/files/mls-hpi-data/...` | monthly, 2005+ |
| US wages | BLS QCEW, all industries/ownership | annual-by-area bulk files | annual, 1990+ |
| CA wages | StatCan median wage/salary/commission income, individuals 15+ | 11-10-0239-01 | annual, 1976+ |
| US CPI | FRED `CPIAUCSL` | — | monthly |
| CA CPI | StatCan CPI, all-items, Canada | 18-10-0004-01 | monthly |

## A data-source correction made during this pilot
The first pass used StatCan's New Housing Price Index for Canadian house prices, which turned
out to be **the wrong instrument**: it tracks new-construction, quality-adjusted builder
prices, and put Vancouver's 2005-2024 real house-price growth at a flat +0.3% — wildly at odds
with the well-documented resale-market boom. The correct resale-based series
(Teranet-National Bank HPI) turned out to be unreachable: `housepriceindex.ca` serves an
incomplete TLS certificate chain (confirmed as the vendor's own server misconfiguration, not
routed around).

**Fix: CREA (Canadian Real Estate Association) publishes its official MLS® HPI dataset as a
direct download** (discovered via the "MLS HPI" tool page, since the file's URL is versioned
by publication month with no stable "latest" alias — `scrape.py` re-discovers it each run). It
gives, per real-estate board, monthly since 2005: a resale composite HPI *and* an actual dollar
benchmark price. It has valid TLS, needs no key, and covers every city in the eventual 16-city
roster (`GREATER_VANCOUVER`, `GREATER_TORONTO`, `CALGARY`, `EDMONTON`, `WINNIPEG`, `OTTAWA`,
`HALIFAX_DARTMOUTH`, `MONTREAL_CMA` are all present as sheet names) — so this fix also clears
the path for the full sweep, not just the pilot's two cities.

US-side data (Zillow ZHVI, BLS QCEW) was cross-checked against known history and looks right:
both cities show the 2008-2012 crash and recovery at plausible magnitudes.

## Pilot findings
Cumulative real growth, 2005-2024:

| City | House price | Wages | Gap (house − wage, pp) |
|---|---|---|---|
| Toronto | +111.0% | +13.6% | **+97.5** |
| Vancouver | +112.4% | +24.3% | **+88.1** |
| Los Angeles | +12.2% | +10.9% | +1.3 |
| San Francisco | +18.9% | +43.8% | −24.9 |

This is the shape the theory predicted: Vancouver and Toronto real house prices roughly
**doubled** while real wages rose by a fifth to a quarter — an ~90 percentage-point gap between
what housing costs and what people earn. Neither Canadian city took a real 2008-crash dip that
shows up in the data (both barely dipped and kept climbing), while SF/LA dropped 35%+ in real
terms and took a decade-plus to recover. San Francisco's negative gap is a genuine, separate
finding: even there, QCEW's average wage (skewed by tech compensation) outpaced real house-price
growth over this specific window, partly because 2005 sat near a pre-crash local price peak.

## Outputs
- `outputs/timeseries/<city>.png` — house price vs. wage index, one panel per city
- `outputs/ranking/house_price_index_overlay.png` — all 4 cities' house-price trajectories, one axes
- `outputs/ranking/decoupling_gap_ranking.png` — cumulative gap ranking

## Next steps
1. Scale to the full 16-city sweep (CREA's workbook already covers all the Canadian cities;
   add the remaining US metros via Zillow/QCEW the same way).
2. Add the remaining two metrics: GDP per capita and rent.
3. Rent for Canada should come from CMHC's Rental Market Survey (annual, coarser than the
   other series here); GDP per capita for Canada is the thinnest series available (StatCan's
   experimental CMA GDP table only starts ~2009) and should be flagged the same way NHPI was
   here if it turns out to distort the comparison.
