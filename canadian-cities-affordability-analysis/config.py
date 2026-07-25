"""Tunables for the Canadian-cities affordability pilot.

Pilot scope (deliberately narrow — this proves the data pipeline before scaling to the
full 16-city / 4-metric sweep): Vancouver, Toronto, San Francisco, Los Angeles.
Metrics: house-price growth and wage growth, annual, 2005-present.

Nothing tunable is hardcoded at a call site — city list, source identifiers, date range,
and the label/color registry all live here.
"""
from __future__ import annotations

from pathlib import Path

# --- Paths --------------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR    = PROJECT_DIR / "data"
RAW_DIR     = DATA_DIR / "raw"
PANEL_CSV   = DATA_DIR / "panel.csv"
OUTPUT_DIR  = PROJECT_DIR / "outputs"

START_YEAR = 2005
END_YEAR   = 2024   # last full year with data on all four series at probe time

# --- Cities (pilot subset) ------------------------------------------------------------------
# color: CA cities in red family, US cities in blue family, so the "where do CA cities sit"
# question reads at a glance without needing the legend.
CITIES = {
    "vancouver": {
        "label": "Vancouver",
        "country": "CA",
        "color": "#d62728",
        # StatCan NHPI (table 18-10-0205-01) geography member id
        "nhpi_geo_id": 39,
        # StatCan table 11-10-0239-01 coordinate for median wage income
        # (Geography.AgeGroup.Gender.IncomeSource.Statistics, padded to 10 dims)
        "wage_coordinate": "21.1.1.4.5.0.0.0.0.0",
    },
    "toronto": {
        "label": "Toronto",
        "country": "CA",
        "color": "#ff7f0e",
        "nhpi_geo_id": 20,
        "wage_coordinate": "17.1.1.4.5.0.0.0.0.0",
    },
    "san_francisco": {
        "label": "San Francisco",
        "country": "US",
        "color": "#1f77b4",
        "zillow_region_name": "San Francisco, CA",
        "qcew_area_substr": "San Francisco",
    },
    "los_angeles": {
        "label": "Los Angeles",
        "country": "US",
        "color": "#17becf",
        "zillow_region_name": "Los Angeles, CA",
        # LA's QCEW MSA area code has changed at least once across 2005-2024 (OMB
        # redelineation); scrape.py matches by name substring, not a hardcoded code.
        "qcew_area_substr": "Los Angeles",
    },
}

CA_CITIES = [c for c, v in CITIES.items() if v["country"] == "CA"]
US_CITIES = [c for c, v in CITIES.items() if v["country"] == "US"]

# --- Sources --------------------------------------------------------------------------------
ZILLOW_ZHVI_URL = ("https://files.zillowstatic.com/research/public_csvs/zhvi/"
                    "Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv")
QCEW_BULK_ZIP_TMPL = "https://data.bls.gov/cew/data/files/{year}/csv/{year}_annual_by_area.zip"
STATCAN_WDS_BASE = "https://www150.statcan.gc.ca/t1/wds/rest"
STATCAN_NHPI_PRODUCT_ID = "18100205"   # New housing price index, monthly (2007=100)
STATCAN_WAGE_PRODUCT_ID = "11100239"   # Income of individuals ... selected CMAs
STATCAN_CPI_PRODUCT_ID = "18100004"    # CPI, monthly, not seasonally adjusted
STATCAN_CPI_COORDINATE = "2.2.0.0.0.0.0.0.0.0"   # Canada, All-items

FRED_CPI_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"  # US, monthly, NSA

# All series are converted to REAL terms (deflated by the city's own national CPI) before
# indexing, so the within-country "house price growth vs wage growth" gap isn't distorted by
# comparing a nominal series to a real one. Canada's wage table is already reported in
# constant dollars; everything else here is nominal at the source and gets deflated here.

SOURCE_NOTES = {
    "house_price_us": "Zillow ZHVI, all-homes tier, metro, monthly -> annual mean",
    "house_price_ca": "StatCan 18-10-0205-01 New Housing Price Index, total (house+land), "
                       "2007=100 -- NEW CONSTRUCTION, not resale; index, not a $ level",
    "wage_us": "BLS QCEW, all industries/ownership, annual avg weekly wage, metro (MSA)",
    "wage_ca": "StatCan 11-10-0239-01, median wage/salary/commission income (2024 constant $), "
               "individuals 15+, CMA",
}

# --- Presentation -----------------------------------------------------------------------
_LABELS = {
    "house_price_index": "House price index (2005 = 100)",
    "wage_index":        "Wage income index (2005 = 100)",
    "decoupling_gap_pp": "House-price growth minus wage growth (pp, cumulative since 2005)",
}


def axis_label(name: str) -> str:
    return _LABELS.get(name, name)
