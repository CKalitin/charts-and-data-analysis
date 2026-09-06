"""Country-level TAM (Total Addressable Market, USD/month) model. Replaces
country_tam_model.py and country_tam_full_model.py (both deleted 2026-09-05) --
this single file covers what used to be two separate models, switched by one
`mode` argument, per the user's explicit "simple toggle" request.

Pricing is entirely elasticity-curve-derived now (no ARPU cap, no scarcity
multiplier, no <20%/>=20% branch -- all removed, per user instruction to scrub
the old system and keep this "as simple as possible"):

  - `elasticity_cost_pct(pct_unconnected)` is the inverse of
    charts/served_population_vs_cost.py's user-specified elasticity curve
    (0.75% of monthly GNI/capita at 0% unconnected -> 10% at 100% unconnected,
    linear in log10(cost%)) -- imported from there, not redefined, so there is
    one source of truth for the two anchor values.
  - UNCONNECTED customers are always priced by that curve, using the
    country's own (real, current) %unconnected -- a single number per
    country, independent of satellite count N.
  - CONNECTED customers (mode="full" only) are priced by lerping from their
    country's own existing incumbent price (t=0, none of them served yet)
    down toward the elasticity curve's floor price at 0% unconnected (t=1,
    all of that country's connected population served) -- t is that
    country's own share of ITS connected population served.

Capacity: this file no longer computes it at all. `compute_country_tam()` takes
an already-computed `{iso3: servable_fraction}` and does pure pricing and
aggregation -- capacity in, TAM out. That separation landed 2026-09-05 when the
capacity layer moved from pooled latitude bands to the 2D tile allocation
(`tile_capacity_model.py` via `country_service_model.py`); the old signature
threaded five latitude-histogram arguments through this module purely to hand
them to the capacity call, and none of them mean anything now. Solving is also
~15 s per satellite count, so a sweep must solve ONCE per N and share that
result across every aggregation -- hence `sweep_country_tam()` plus the cheap
`total_tam()` / `tam_by_region()` / `tam_by_segment()` reducers, rather than
three sweeps that each re-solve.

mode="unconnected": addressable = min(unconnected_population, capacity).
mode="full": capacity serves unconnected population FIRST (up to the full
unconnected count), then whatever capacity is left over serves connected
population -- per-country, not per-latitude-band (simpler, user's explicit
choice over the finer-grained alternative).
"""
from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import capacity_density_model as cdm
import country_service_model as csm
import orbital_geometry as og
import tile_capacity_model as tcm
from charts.affordability import _raw_arpu
from charts.served_population_vs_cost import (
    ELASTICITY_X_LO, ELASTICITY_X_HI, ELASTICITY_Y_LO, ELASTICITY_Y_HI,
)

DATA = Path(__file__).resolve().parent / "data"

Mode = Literal["unconnected", "full"]

_LOG_X_LO, _LOG_X_HI = np.log10(ELASTICITY_X_LO), np.log10(ELASTICITY_X_HI)


def elasticity_cost_pct(pct_unconnected: float) -> float:
    """%unconnected -> connectivity cost, as % of monthly GNI/capita. Inverse of
    served_population_vs_cost.pct_unconnected_from_cost_pct(), same two anchors."""
    frac = np.clip(pct_unconnected, ELASTICITY_Y_LO, ELASTICITY_Y_HI) / (ELASTICITY_Y_HI - ELASTICITY_Y_LO)
    return 10 ** (_LOG_X_LO + frac * (_LOG_X_HI - _LOG_X_LO))


def elasticity_price_usd_month(pct_unconnected: float, gni_per_capita_usd_year: float) -> float:
    """%unconnected + a country's GNI/capita -> elasticity-derived price, $/month."""
    return elasticity_cost_pct(pct_unconnected) / 100 * gni_per_capita_usd_year / 12


def floor_price_usd_month(gni_per_capita_usd_year: float) -> float:
    """The elasticity curve's cheapest price (at 0% unconnected) for one country."""
    return elasticity_price_usd_month(0.0, gni_per_capita_usd_year)


@dataclass(frozen=True)
class CountryTAM:
    iso3: str
    country: str
    region: str
    population: float
    connected_population: float
    unconnected_population: float
    pct_unconnected: float
    servable_fraction: float
    served_unconnected: float
    served_connected: float
    household_size: float
    price_unconnected_usd_per_month: float
    price_connected_usd_per_month: float
    tam_unconnected_usd_per_month: float
    tam_connected_usd_per_month: float
    tam_usd_per_month: float


def load_telecom_rows() -> list[dict]:
    with open(DATA / "telecom_market_by_country.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_household_size() -> dict[str, float]:
    with open(DATA / "household_size_by_country.csv", encoding="utf-8") as f:
        return {r["iso3"]: float(r["household_size"]) for r in csv.DictReader(f)}


def compute_country_tam(servable: dict[str, float], telecom_rows: list[dict],
                        household_size: dict[str, float],
                        mode: Mode = "unconnected") -> list[CountryTAM]:
    """One CountryTAM per country that has telecom data, household-size data, and a
    servable fraction. `servable` comes from
    country_service_model.country_servable_fraction() -- this function does no
    capacity work of its own."""
    out = []
    for row in telecom_rows:
        iso3 = row["iso3"]
        frac = servable.get(iso3)
        if frac is None or np.isnan(frac):
            continue
        pop, unconn = row["population"], row["unconnected_population_est_coverage_corrected"]
        gni = row["gni_per_capita_ppp_usd"]
        hh_size = household_size.get(iso3)
        if not (pop and unconn and gni and hh_size):
            continue
        pop, unconn, gni = float(pop), float(unconn), float(gni)
        connected = pop - unconn
        pct_unconnected = 100.0 * unconn / pop

        capacity = frac * pop
        served_unconnected = min(unconn, capacity)
        price_unconnected = elasticity_price_usd_month(pct_unconnected, gni)

        served_connected = 0.0
        price_connected = 0.0
        if mode == "full":
            leftover_capacity = max(0.0, capacity - unconn)
            served_connected = min(connected, leftover_capacity)
            existing_price = _raw_arpu(row)
            if existing_price and connected > 0:
                t = served_connected / connected
                price_connected = existing_price + t * (floor_price_usd_month(gni) - existing_price)

        subs_unconnected = served_unconnected / hh_size
        subs_connected = served_connected / hh_size
        tam_unconnected = subs_unconnected * price_unconnected
        tam_connected = subs_connected * price_connected

        out.append(CountryTAM(
            iso3=iso3, country=row["country"], region=row["region"], population=pop,
            connected_population=connected, unconnected_population=unconn,
            pct_unconnected=pct_unconnected, servable_fraction=frac,
            served_unconnected=served_unconnected, served_connected=served_connected,
            household_size=hh_size, price_unconnected_usd_per_month=price_unconnected,
            price_connected_usd_per_month=price_connected,
            tam_unconnected_usd_per_month=tam_unconnected,
            tam_connected_usd_per_month=tam_connected,
            tam_usd_per_month=tam_unconnected + tam_connected,
        ))
    return out


def load_inputs(tile=None, verbose: bool = False):
    """(telecom_rows, household_size, tile, demand, country_pop_by_tile) -- the
    one-time setup every TAM chart needs, in one place so the three chart modules
    do not each carry their own copy of it. Building the per-country tile footprints
    reads ~215 WorldPop rasters on a cold cache (minutes); it is cached to disk after
    that."""
    telecom_rows = load_telecom_rows()
    household_size = load_household_size()
    tile = tile if tile is not None else tcm.make_tile_grid()
    demand = tcm.build_demand(tile)
    pop_by_tile = csm.load_all_country_population_by_tile(
        [r["iso3"] for r in telecom_rows], tile, verbose=verbose)
    return telecom_rows, household_size, tile, demand, pop_by_tile


def sweep_country_tam(sat_counts, telecom_rows: list[dict], household_size: dict[str, float],
                      country_pop_by_tile, tile=None, demand=None, mode: Mode = "unconnected",
                      scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                      base_shells: list[og.Shell] | None = None,
                      use_cache: bool = True, verbose: bool = False) -> list[list[CountryTAM]]:
    """Per-country TAM rows at each N -- ONE tile-model solve per N, reused by every
    reducer below. Call this once and reduce it three ways; calling total_tam(),
    tam_by_region() and tam_by_segment() as separate sweeps would triple the
    (dominant) solve cost for identical results."""
    fracs = csm.sweep_country_servable_fraction(sat_counts, country_pop_by_tile, tile, demand,
                                                scenario, base_shells, use_cache=use_cache,
                                                verbose=verbose)
    out = []
    for i in range(len(sat_counts)):
        servable = {iso3: arr[i] for iso3, arr in fracs.items()}
        out.append(compute_country_tam(servable, telecom_rows, household_size, mode))
    return out


def total_tam(rows_per_n: list[list[CountryTAM]]) -> np.ndarray:
    """Total TAM ($/month, every country summed) at each swept N."""
    return np.array([sum(r.tam_usd_per_month for r in rows) for rows in rows_per_n])


def tam_by_region(rows_per_n: list[list[CountryTAM]], regions: list[str] | None = None) -> dict[str, np.ndarray]:
    """{region: array of TAM $/month} -- same rows, grouped instead of summed."""
    if regions is None:
        regions = sorted({r.region for rows in rows_per_n for r in rows})
    out = {reg: [] for reg in regions}
    for rows in rows_per_n:
        totals = dict.fromkeys(regions, 0.0)
        for r in rows:
            if r.region in totals:
                totals[r.region] += r.tam_usd_per_month
        for reg in regions:
            out[reg].append(totals[reg])
    return {reg: np.array(v) for reg, v in out.items()}


def tam_by_segment(rows_per_n: list[list[CountryTAM]]) -> dict[str, np.ndarray]:
    """{"unconnected": array, "connected": array} of TAM $/month -- the revenue mix
    between newly-connected and already-connected customers. Only meaningful for
    mode="full"; mode="unconnected" always leaves "connected" all zero."""
    return {
        "unconnected": np.array([sum(r.tam_unconnected_usd_per_month for r in rows) for rows in rows_per_n]),
        "connected": np.array([sum(r.tam_connected_usd_per_month for r in rows) for rows in rows_per_n]),
    }


if __name__ == "__main__":
    telecom_rows = load_telecom_rows()
    household_size = load_household_size()
    iso3_list = [r["iso3"] for r in telecom_rows]

    tile = tcm.make_tile_grid()
    demand = tcm.build_demand(tile)
    pop_by_tile = csm.load_all_country_population_by_tile(iso3_list, tile, verbose=True)
    print(f"loaded {len(pop_by_tile)}/{len(iso3_list)} country tile footprints")

    sat_counts = [4_408, 10_900, 100_000]
    for mode in ("unconnected", "full"):
        rows_per_n = sweep_country_tam(sat_counts, telecom_rows, household_size, pop_by_tile,
                                       tile, demand, mode=mode, verbose=True)
        for n, rows in zip(sat_counts, rows_per_n):
            total = sum(r.tam_usd_per_month for r in rows)
            print(f"--- mode={mode} N={n:,}: {len(rows)} countries, total TAM=${total:,.0f}/mo ---")
            for r in sorted(rows, key=lambda r: -r.tam_usd_per_month)[:8]:
                print(f"  {r.iso3}: ${r.tam_usd_per_month:,.0f}/mo "
                      f"(unconn ${r.tam_unconnected_usd_per_month:,.0f} @ ${r.price_unconnected_usd_per_month:,.2f}, "
                      f"conn ${r.tam_connected_usd_per_month:,.0f} @ ${r.price_connected_usd_per_month:,.2f}), "
                      f"servable={r.servable_fraction:.1%}")
