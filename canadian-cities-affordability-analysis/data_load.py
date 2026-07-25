"""Raw pulls -> one tidy annual panel: city, year, house_price_real, wage_real.

Both series are converted to REAL (CPI-deflated) terms in the city's own currency before
being turned into base-100 indices, so the within-city "house price growth vs wage growth"
comparison isn't distorted by mixing a nominal series against a real one:
  - US: Zillow ZHVI and QCEW wages are nominal at the source -> deflated by US CPI (FRED).
  - Canada: NHPI is nominal at the source -> deflated by Canadian CPI (StatCan).
            The wage table (11-10-0239-01) is already reported in constant 2024 dollars,
            so it is used as-is (deflating it again would double-count inflation).
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

import config as cfg
import scrape


def _year_avg(dates: list[str], values: list[float]) -> pd.Series:
    df = pd.DataFrame({"date": pd.to_datetime(dates), "value": values})
    return df.groupby(df["date"].dt.year)["value"].mean()


def _load_fred_cpi() -> pd.Series:
    path = scrape.fetch_fred_cpi()
    df = pd.read_csv(path)
    df.columns = ["date", "cpi"]
    df["date"] = pd.to_datetime(df["date"])
    df["cpi"] = pd.to_numeric(df["cpi"], errors="coerce")
    return df.groupby(df["date"].dt.year)["cpi"].mean()


def _load_statcan_cpi() -> pd.Series:
    points = scrape.fetch_statcan_cpi()
    dates = [p["refPer"] for p in points]
    values = [p["value"] for p in points]
    return _year_avg(dates, values)


def _load_zillow_house_price(city_key: str) -> pd.Series:
    path = scrape.fetch_zillow_zhvi()
    df = pd.read_csv(path)
    region = cfg.CITIES[city_key]["zillow_region_name"]
    row = df[(df["RegionName"] == region) & (df["RegionType"] == "msa")]
    if row.empty:
        raise ValueError(f"Zillow region not found: {region}")
    month_cols = [c for c in df.columns if c[:4].isdigit()]
    s = row[month_cols].iloc[0].astype(float)
    s.index = pd.to_datetime(s.index)
    return s.groupby(s.index.year).mean()


def _load_qcew_wage(city_key: str) -> pd.Series:
    years = range(cfg.START_YEAR, cfg.END_YEAR + 1)
    wages = {y: scrape.fetch_qcew_annual_wage(city_key, y) for y in years}
    # QCEW reports a weekly wage; annualize so it's a comparable dollar level, not that it
    # matters for an index normalized to its own base year.
    return pd.Series({y: w * 52 for y, w in wages.items()})


def _load_statcan_nhpi(city_key: str) -> pd.Series:
    points = scrape.fetch_statcan_nhpi(city_key)
    dates = [p["refPer"] for p in points]
    values = [p["value"] for p in points]
    return _year_avg(dates, values)


def _load_statcan_wage(city_key: str) -> pd.Series:
    points = scrape.fetch_statcan_wage(city_key)
    s = pd.Series({int(p["refPer"][:4]): p["value"] for p in points})
    return s


def build_panel() -> pd.DataFrame:
    """Returns long-format DataFrame[city, year, house_price_real, wage_real]."""
    years = list(range(cfg.START_YEAR, cfg.END_YEAR + 1))
    us_cpi = _load_fred_cpi()
    ca_cpi = _load_statcan_cpi()

    rows = []
    for city_key, city in cfg.CITIES.items():
        if city["country"] == "US":
            house_nom = _load_zillow_house_price(city_key)
            wage_nom = _load_qcew_wage(city_key)
            cpi = us_cpi
            house_real = house_nom / cpi * cpi.loc[cfg.START_YEAR]
            wage_real = wage_nom / cpi * cpi.loc[cfg.START_YEAR]
        else:
            house_nom = _load_statcan_nhpi(city_key)
            cpi = ca_cpi
            house_real = house_nom / cpi * cpi.loc[cfg.START_YEAR]
            wage_real = _load_statcan_wage(city_key)   # already real (constant 2024$)

        for y in years:
            rows.append({
                "city": city_key,
                "year": y,
                "house_price_real": house_real.get(y),
                "wage_real": wage_real.get(y),
            })

    panel = pd.DataFrame(rows).sort_values(["city", "year"]).reset_index(drop=True)
    cfg.DATA_DIR.mkdir(parents=True, exist_ok=True)
    panel.to_csv(cfg.PANEL_CSV, index=False)
    return panel


def load_panel() -> pd.DataFrame:
    if cfg.PANEL_CSV.exists():
        return pd.read_csv(cfg.PANEL_CSV)
    return build_panel()


if __name__ == "__main__":
    panel = build_panel()
    print(panel.to_string(index=False))
