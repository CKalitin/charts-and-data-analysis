"""Pulls raw data for the pilot from Zillow, BLS QCEW, StatCan WDS, and FRED.

Every fetch is cached to data/raw/ so reruns don't re-hit the network. Run directly to
(re)populate the cache: `python scrape.py`.
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

TIMEOUT = 30


def _cached_bytes(path: Path, url: str, **kwargs) -> bytes:
    if path.exists():
        return path.read_bytes()
    resp = requests.get(url, timeout=TIMEOUT, **kwargs)
    resp.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    return resp.content


def fetch_zillow_zhvi() -> Path:
    """US metro house-price levels ($), monthly, since 2000."""
    path = cfg.RAW_DIR / "zillow_zhvi_metro.csv"
    _cached_bytes(path, cfg.ZILLOW_ZHVI_URL)
    return path


def fetch_fred_cpi() -> Path:
    """US CPI-U, monthly, NSA -- deflator for the US nominal series."""
    path = cfg.RAW_DIR / "fred_cpiaucsl.csv"
    _cached_bytes(path, cfg.FRED_CPI_URL)
    return path


def fetch_qcew_annual_wage(city_key: str, year: int) -> float:
    """Annual average weekly wage ($, nominal), all industries/ownership, for one metro-year.

    Downloads BLS's bulk 'annual by area' zip for the year (cached), pulls the one area file
    that matches this city, and reads the all-industry/all-ownership total row.
    """
    cache = cfg.RAW_DIR / "qcew" / f"{city_key}_{year}.json"
    if cache.exists():
        return json.loads(cache.read_text())["annual_avg_wkly_wage"]

    zip_path = cfg.RAW_DIR / "qcew" / f"{year}_annual_by_area.zip"
    zip_bytes = _cached_bytes(zip_path, cfg.QCEW_BULK_ZIP_TMPL.format(year=year))

    city = cfg.CITIES[city_key]
    # Match by "<substring> ... MSA.csv" rather than a hardcoded area code: OMB redraws MSA
    # boundaries periodically (LA's code alone changed at least once across 2005-2024) and
    # the code isn't stable, but "the one MSA-suffixed file containing this city's name" is.
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        match = next(n for n in zf.namelist()
                     if n.endswith(" MSA.csv") and city["qcew_area_substr"] in n)
        with zf.open(match) as f:
            import csv
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
            row = next(r for r in reader
                       if r["own_code"] == "0" and r["industry_code"] == "10")

    wage = float(row["annual_avg_wkly_wage"])
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"annual_avg_wkly_wage": wage, "area_fips": row["area_fips"]}))
    return wage


def _statcan_fetch(product_id: str, coordinate: str, latest_n: int) -> list[dict]:
    cache = cfg.RAW_DIR / "statcan" / f"{product_id}_{coordinate}.json"
    if cache.exists():
        return json.loads(cache.read_text())

    resp = requests.post(
        f"{cfg.STATCAN_WDS_BASE}/getDataFromCubePidCoordAndLatestNPeriods",
        json=[{"productId": int(product_id), "coordinate": coordinate, "latestN": latest_n}],
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    result = resp.json()[0]
    if result["status"] != "SUCCESS":
        raise RuntimeError(f"StatCan fetch failed for {product_id}/{coordinate}: {result}")
    points = result["object"]["vectorDataPoint"]

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(points))
    return points


def fetch_statcan_nhpi(city_key: str) -> list[dict]:
    """Canada new-housing price index (2007=100, total house+land), monthly, since 1981."""
    geo_id = cfg.CITIES[city_key]["nhpi_geo_id"]
    coordinate = f"{geo_id}.1.0.0.0.0.0.0.0.0"
    n_months = (2027 - 1981) * 12
    return _statcan_fetch(cfg.STATCAN_NHPI_PRODUCT_ID, coordinate, n_months)


def fetch_statcan_wage(city_key: str) -> list[dict]:
    """Canada CMA median wage/salary/commission income, 2024 constant $, annual, since 1976."""
    coordinate = cfg.CITIES[city_key]["wage_coordinate"]
    n_years = 2027 - 1976
    return _statcan_fetch(cfg.STATCAN_WAGE_PRODUCT_ID, coordinate, n_years)


def fetch_statcan_cpi() -> list[dict]:
    """Canada all-items CPI, monthly, since 1914 -- deflator for the CA nominal series (NHPI)."""
    n_months = (2027 - 1914) * 12
    return _statcan_fetch(cfg.STATCAN_CPI_PRODUCT_ID, cfg.STATCAN_CPI_COORDINATE, n_months)


def fetch_all() -> None:
    print("Zillow ZHVI...")
    fetch_zillow_zhvi()
    print("FRED CPI...")
    fetch_fred_cpi()
    print("StatCan CPI...")
    fetch_statcan_cpi()
    for city_key, city in cfg.CITIES.items():
        if city["country"] == "US":
            print(f"QCEW wages: {city['label']}...")
            for year in range(cfg.START_YEAR, cfg.END_YEAR + 1):
                fetch_qcew_annual_wage(city_key, year)
        else:
            print(f"StatCan NHPI + wages: {city['label']}...")
            fetch_statcan_nhpi(city_key)
            fetch_statcan_wage(city_key)
    print("Done.")


if __name__ == "__main__":
    fetch_all()
