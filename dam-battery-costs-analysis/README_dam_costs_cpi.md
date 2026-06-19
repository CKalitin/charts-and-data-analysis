# Hydroelectric Dam Costs — Global Dataset

Data compiled for analysis of hydroelectric dam construction costs vs. capacity ($/MW),
spanning US, Canadian, Chinese, and international projects from 1936–2025.

As usual, amazing thanks to Claude.

## Files

| File | Rows | Description |
|---|---|---|
| `dam_costs.csv` | 31 | **Primary source of truth.** All dams, all fields, sorted by year completed. Includes 4 capacity-only rows with no cost data. |
| `dam_costs_ranked.csv` | 27 | Costed dams only, sorted ascending by `usd_per_mw_2025`. Drop-in for plotting. |
| `cpi_factors.csv` | 89 | BLS CPI-U annual averages 1936–2024 with inflation factors to 2025$. |

---

## Schema — `dam_costs.csv`

| Column | Type | Units | Description |
|---|---|---|---|
| `name` | str | — | Dam / project name |
| `country` | str | — | Country or countries |
| `region` | str | — | River and state/province |
| `region_group` | str | — | `US`, `Canada`, `China`, `International` |
| `year_complete` | int | year | Year all generating units commissioned |
| `cost_nominal_local_m` | float\|empty | $M local currency | Construction cost in local currency, nominal year-of-construction dollars |
| `local_currency` | str | — | `USD` or `CAD` |
| `cost_year` | int\|empty | year | Year the cost figure is denominated in (may differ from year_complete for multi-year projects) |
| `cad_usd_rate` | float\|empty | — | CAD/USD spot rate used for conversion (only populated for CAD entries) |
| `cost_usd_nominal_m` | float\|empty | $M USD | Cost in nominal USD (CAD entries already converted at `cad_usd_rate`) |
| `cpi_factor_to_2025` | float\|empty | — | `CPI_2025 / CPI[cost_year]`; multiply `cost_usd_nominal_m` by this to get 2025$ |
| `cost_2025_usd_m` | float\|empty | $M 2025 USD | `cost_usd_nominal_m * cpi_factor_to_2025` |
| `capacity_mw` | int | MW | Installed nameplate capacity |
| `usd_per_mw_nominal` | int\|empty | $/MW | `cost_usd_nominal_m * 1e6 / capacity_mw` |
| `usd_per_mw_2025` | int\|empty | 2025 $/MW | `cost_2025_usd_m * 1e6 / capacity_mw` |
| `has_cost_data` | bool | — | `False` for 4 capacity-only entries (no reliable cost source found) |
| `notes` | str | — | Source details, caveats, turbine counts |
| `source_url` | str | — | Primary source URL |

---

## Quick start

```python
import pandas as pd

df = pd.read_csv("dam_costs.csv")

# Costed entries only
costed = df[df["has_cost_data"]].copy()

# Cost overrun proxy: how much did cost_year differ from year_complete?
costed["cost_year_lag"] = costed["year_complete"] - costed["cost_year"]

# $/MW in 2025$ by region
print(costed.groupby("region_group")["usd_per_mw_2025"].describe())

# Load CPI table
cpi = pd.read_csv("cpi_factors.csv")
```

---

## Inflation methodology

All inflation adjustments use **BLS CPI-U annual averages** (base period 1982–84 = 100).

- 2025 base ≈ **319.8** (estimated annual average from BLS monthly data through mid-2025)
- Factor = `319.8 / CPI[cost_year]`
- Full table in `cpi_factors.csv`

**Source:** U.S. Bureau of Labor Statistics  
https://www.bls.gov/cpi/tables/supplemental-files/historical-cpi-u-202505.xlsx

### CPI-U vs. other indices

CPI-U is a general consumer price index. Construction costs inflate faster than CPI in most eras.
The **ENR Construction Cost Index** would give higher 2025-adjusted values for historic dams.
Using CPI-U here for consistency and reproducibility; treat absolute $/MW figures for pre-1970
dams as a lower bound on real-terms cost.

### CAD → USD conversion

CAD entries are converted to USD at the approximate annual spot rate for `cost_year` before
CPI adjustment:

| Year | Rate used |
|---|---|
| 1968 | 0.93 |
| 1974 | 0.98 |
| 1987 | 0.76 |
| 1992 | 0.83 |
| 1994 | 0.73 |
| 2020 | 0.75 |
| 2021 | 0.79 |
| 2022 | 0.78 |

---

## Key observations

### US historic (1930s–40s, 2025$)
- Hoover ~**$543K/MW**, Grand Coulee (orig) ~**$1.3M/MW**, Shasta ~**$947K/MW**
- Depression-era labor costs were extremely low in nominal terms; even adjusted to 2025$ these
  are well under $2M/MW

### US modern (1960s–80s, 2025$)
- Robert Moses Niagara ~**$3.6M/MW**, Bonneville Ph2 ~**$4.2M/MW**, Rocky Reach ~**$1.7M/MW**
- Real costs rose sharply 1960s–80s: labour, safety regulation, environmental compliance

### Canada recent (2020–2025, 2025$)
- Site C ~**$13.6M/MW**, Muskrat Falls ~**$14.3M/MW**, Keeyask ~**$10.7M/MW**
- These are already near-nominal 2025 dollars (CPI factor 1.09–1.24×); the cost explosion
  vs. earlier Canadian projects is real, not an inflation artefact
- All three projects had massive overruns vs. original estimates (2× or more)

### China modern (2000–2022, 2025$)
- Xiluodu ~**$604K/MW**, Three Gorges ~**$1.97M/MW**, Baihetan ~**$2.1M/MW**, Wudongde ~**$1.9M/MW**
- China is building at 5–20× lower $/MW than contemporary Canadian projects in real terms
- Xiluodu cost figure ($6.2B for 13.86 GW) is suspiciously low; some sources cite up to $12B.
  Even at $12B that's ~$865K/MW 2025$

### Itaipu (1984, 2025$)
- ~**$4.3M/MW** in 2025 dollars; $19.6B nominal for 14 GW
- Comparable to US projects of similar era; Brazil/Paraguay had significant corruption in
  procurement per the GIHub case study

### The Site C comparison
- Site C at C$16B / 1,100 MW ≈ C$14.5M/MW ≈ **USD $13.6M/MW in 2025$**
- This is the same order of magnitude as nuclear; the post premise holds

### The Hoover "$1M/MW" figure
- In 2025 CPI-U adjusted dollars: $49M × 23.0 = $1.13B ÷ 2,079 MW ≈ **$543K/MW**
- The ~$1M/MW figure likely uses ENR Construction Cost Index (which inflates faster than CPI)
  or a different inflation endpoint. Clarify which index before citing in the post.

---

## Data gaps

These dams have confirmed capacity but no reliable public construction cost:

| Dam | Country | MW | Notes |
|---|---|---|---|
| Peace Canyon Dam | Canada | 694 | BC Hydro; no cost in Wikipedia or BC Hydro public docs |
| Mica Dam | Canada | 2,805 | Original 1973 cost not published; 2015 expansion (units 5&6) ≈ C$1B per KWL.ca |
| Moses-Saunders Dam | USA/Canada | 1,957 | St. Lawrence Seaway project; cost bundled with navigation works |
| Revelstoke Dam | Canada | 2,480 | BC Hydro; no original construction cost in public sources |

---

## Sources

All individual source URLs are in the `source_url` column of `dam_costs.csv`. Primary references:

- Wikipedia infoboxes (dam-specific articles) — used for cost, capacity, year
- [BLS CPI-U historical table](https://www.bls.gov/cpi/tables/supplemental-files/historical-cpi-u-202505.xlsx)
- [BC Hydro Site C project page](https://www.bchydro.com/energy-in-bc/projects/site_c.html)
- [CBC — Keeyask cost reporting](https://www.cbc.ca/news/canada/manitoba/manitoba-hydro-keeyask-generating-station-electricity-1.5918974)
- [Marketplace.org — Shasta Dam construction cost](https://www.marketplace.org/story/2017/04/03/new-deal-shasta-and-jobs)
- [Power Technology — Xiluodu](https://www.power-technology.com/projects/xiluodu-dam-jinsha-yangtze-china/)
- [Water Power Magazine — Baihetan](https://www.waterpowermagazine.com/analysis/spotlight-on-large-dams/)
- [EnergyNow — Site C final cost](https://energynow.ca/2026/06/commentary-bcs-site-c-hydro-project-was-not-a-white-elephant-and-neither-is-more-hydro-and-natural-gas-projects-stewart-muir/)
