"""Bins Phase 1's country-level population data into 1-degree latitude rings, so it
can be compared directly against Phase 2/3's satellite-density-by-latitude model.

APPROXIMATION, clearly flagged: each country's ENTIRE population is placed at its
CAPITAL CITY's latitude (from data/raw/wb_countries.json -- the same World Bank
source Phase 1 already used, no new data dependency). This is not a population-
weighted centroid. It is a reasonable proxy for most countries (capitals are usually
within the populated region) but a known-bad proxy for countries with deliberately
relocated/non-representative capitals -- Brasilia, Abuja, Naypyidaw, Canberra,
Astana/Nur-Sultan, Putrajaya are the standard examples. Treat latitude bins as
approximate, especially near those specific countries' capital latitudes.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent / "data"
TELECOM_CSV = DATA / "telecom_market_by_country.csv"
WB_COUNTRIES_JSON = DATA / "raw" / "wb_countries.json"


def load_country_population_by_latitude():
    """Returns list of dicts: country, iso3, capital_lat, population, unconnected, served."""
    capitals = {}
    for c in json.load(open(WB_COUNTRIES_JSON, encoding="utf-8"))[1]:
        if c["region"]["id"] == "NA":
            continue
        lat = c.get("latitude")
        if lat:
            capitals[c["id"]] = float(lat)

    rows = []
    missing_capital = []
    with open(TELECOM_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            iso3 = r["iso3"]
            try:
                pop = float(r["population"])
                unconn = float(r["unconnected_population_est_coverage_corrected"])
            except (ValueError, KeyError):
                continue
            lat = capitals.get(iso3)
            if lat is None:
                missing_capital.append(r["country"])
                continue
            rows.append({
                "country": r["country"], "iso3": iso3, "capital_lat": lat, "region": r["region"],
                "population": pop, "unconnected": unconn, "served": pop - unconn,
            })
    return rows, missing_capital


def bin_by_latitude(rows, bin_width_deg: float = 1.0):
    """Sum served/unserved population into latitude bins. Returns (centers, served, unserved)."""
    edges = np.arange(-90, 90 + bin_width_deg, bin_width_deg)
    centers = (edges[:-1] + edges[1:]) / 2
    served = np.zeros_like(centers)
    unserved = np.zeros_like(centers)
    for r in rows:
        idx = np.searchsorted(edges, r["capital_lat"], side="right") - 1
        idx = min(max(idx, 0), len(centers) - 1)
        served[idx] += r["served"]
        unserved[idx] += r["unconnected"]
    return centers, served, unserved


def bin_by_latitude_and_region(rows, bin_width_deg: float = 1.0):
    """Sum total population into latitude bins, split by World Bank region.

    Returns (centers, {region: array}). Same capital-city-latitude approximation as
    bin_by_latitude() -- see module docstring.
    """
    edges = np.arange(-90, 90 + bin_width_deg, bin_width_deg)
    centers = (edges[:-1] + edges[1:]) / 2
    by_region: dict[str, np.ndarray] = {}
    for r in rows:
        idx = np.searchsorted(edges, r["capital_lat"], side="right") - 1
        idx = min(max(idx, 0), len(centers) - 1)
        arr = by_region.setdefault(r["region"], np.zeros_like(centers))
        arr[idx] += r["population"]
    return centers, by_region
