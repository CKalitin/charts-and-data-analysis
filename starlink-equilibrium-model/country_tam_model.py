"""Country-level TAM (Total Addressable Market, in USD) for CURRENTLY-UNCONNECTED
populations only (2026-08-14, user request -- see CLAUDE.md's TAM-model section for
the full design conversation). Country-level granularity throughout, per the user's
explicit "note we're not going more granular than that."

Pricing rule per country (user-specified):
  - If <20% of the population is unconnected: assume Starlink prices at whatever the
    LOCAL market already charges -- _raw_arpu() (charts/affordability.py), the same
    fixed/mobile dominant-access-mode proxy used throughout this project's
    affordability work (equilibrium_model.build_country_demand() uses the identical
    logic).
  - If >=20% is unconnected: derive a price from the elasticity curve instead of the
    local incumbent price (a market that expensive/uncompetitive presumably isn't a
    reliable price signal). Take this country's OWN capacity-constrained
    servable_fraction(N) (country_service_model.py -- the REAL satellite/population
    model, not a guess), treat (100 - servable_fraction*100) as the implied "%
    unconnected AT THIS PRICE," and invert the same log-linear elasticity curve
    served_population_vs_cost.py already establishes (cost_pct_from_pct_unconnected())
    to solve for the price (as % of monthly GNI/capita) that would leave exactly that
    many people priced out -- i.e. the capacity constraint determines the
    market-clearing price via the demand curve, not the other way around.

Addressable population = min(unconnected_population, servable_fraction(N) x
total_population) -- capacity CANNOT exceed the real capacity ceiling (from the
satellite model) or the real demand ceiling (there's no one to sell to beyond the
population that's actually unconnected); household_size_by_country.csv converts
people to subscriptions (one subscription per household, not per person -- see that
file's own doc for why, and its explicitly-flagged businesses/MDU simplification).

TAM ($/month) = addressable_subscriptions x price_usd_per_month, summed per country
for a global total. NOT annualized by default (matches the "USD subscription cost
monthly" framing the user asked for) -- multiply by 12 for an annual figure.
"""
from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import capacity_density_model as cdm
import country_service_model as csm
import orbital_geometry as og
import population_density_grid as pdg
import serviceable_customers_model as scm
from charts.affordability import _raw_arpu
from charts.served_population_vs_cost import cost_pct_from_pct_unconnected

DATA = Path(__file__).resolve().parent / "data"

UNCONNECTED_PCT_THRESHOLD = 20.0  # user-specified: below this, use the local price; at/above, use elasticity


@dataclass(frozen=True)
class CountryTAM:
    iso3: str
    country: str
    region: str
    population: float
    unconnected_population: float
    pct_unconnected: float
    servable_fraction: float
    addressable_population: float
    household_size: float
    addressable_subscriptions: float
    price_usd_per_month: float
    price_basis: str  # "existing_local_price" | "elasticity_derived"
    tam_usd_per_month: float


def load_telecom_rows() -> list[dict]:
    with open(DATA / "telecom_market_by_country.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_household_size() -> dict[str, float]:
    with open(DATA / "household_size_by_country.csv", encoding="utf-8") as f:
        return {r["iso3"]: float(r["household_size"]) for r in csv.DictReader(f)}


def _country_price(row: dict, servable_fraction: float, pct_unconnected: float) -> tuple[float, str]:
    """(price_usd_per_month, basis) for one country, per the rule in the module
    docstring. Falls back to the existing local price if GNI data is missing (can't
    invert the elasticity curve without a GNI basis to apply the %-of-GNI result
    to) -- flagged via the returned basis string, not silently substituted."""
    if pct_unconnected < UNCONNECTED_PCT_THRESHOLD:
        arpu = _raw_arpu(row)
        return (arpu, "existing_local_price") if arpu else (0.0, "no_price_data")

    gni = row["gni_per_capita_ppp_usd"]
    if not gni:
        arpu = _raw_arpu(row)
        return (arpu, "existing_local_price_gni_missing") if arpu else (0.0, "no_price_data")

    target_pct_unconnected = 100.0 * (1.0 - servable_fraction)
    cost_pct = float(cost_pct_from_pct_unconnected(target_pct_unconnected))
    price = cost_pct / 100.0 * (float(gni) / 12.0)
    return price, "elasticity_derived"


def compute_country_tam(total_sats: float, telecom_rows: list[dict], household_size: dict[str, float],
                         country_pop_by_lat: dict[str, tuple[np.ndarray, np.ndarray]],
                         global_lat_centers: np.ndarray, global_area_hist: np.ndarray,
                         global_dens_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                         base_shells: list[og.Shell] | None = None,
                         bin_width_deg: float = scm.BIN_WIDTH_DEG) -> list[CountryTAM]:
    """CountryTAM for every country with both telecom data and a cached population
    raster (country_pop_by_lat -- see country_service_model.load_all_country_population_by_latitude(),
    precomputed ONCE by the caller and reused across an N sweep)."""
    servable = csm.country_servable_fraction(total_sats, country_pop_by_lat, global_lat_centers,
                                              global_area_hist, global_dens_centers, scenario, base_shells,
                                              bin_width_deg)
    out = []
    for row in telecom_rows:
        iso3 = row["iso3"]
        if iso3 not in servable or np.isnan(servable[iso3]):
            continue
        pop, unconn = row["population"], row["unconnected_population_est_coverage_corrected"]
        if not pop or not unconn:
            continue
        pop, unconn = float(pop), float(unconn)
        pct_unconnected = 100.0 * unconn / pop
        frac = servable[iso3]

        addressable_pop = min(unconn, frac * pop)
        hh_size = household_size.get(iso3)
        if not hh_size:
            continue
        addressable_subs = addressable_pop / hh_size

        price, basis = _country_price(row, frac, pct_unconnected)
        tam = addressable_subs * price if basis != "no_price_data" else 0.0

        out.append(CountryTAM(
            iso3=iso3, country=row["country"], region=row["region"], population=pop,
            unconnected_population=unconn, pct_unconnected=pct_unconnected, servable_fraction=frac,
            addressable_population=addressable_pop, household_size=hh_size,
            addressable_subscriptions=addressable_subs, price_usd_per_month=price, price_basis=basis,
            tam_usd_per_month=tam,
        ))
    return out


def sweep_total_tam(sat_counts, telecom_rows: list[dict], household_size: dict[str, float],
                     country_pop_by_lat: dict[str, tuple[np.ndarray, np.ndarray]],
                     global_lat_centers: np.ndarray, global_area_hist: np.ndarray,
                     global_dens_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                     base_shells: list[og.Shell] | None = None,
                     bin_width_deg: float = scm.BIN_WIDTH_DEG) -> np.ndarray:
    """Total TAM ($/month, summed across every country) at each N in sat_counts."""
    out = []
    for n in sat_counts:
        rows = compute_country_tam(n, telecom_rows, household_size, country_pop_by_lat, global_lat_centers,
                                    global_area_hist, global_dens_centers, scenario, base_shells, bin_width_deg)
        out.append(sum(r.tam_usd_per_month for r in rows))
    return np.array(out)


if __name__ == "__main__":
    grid = pdg.load_or_build_grid()
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    telecom_rows = load_telecom_rows()
    household_size = load_household_size()

    iso3_list = [r["iso3"] for r in telecom_rows]
    pop_by_lat = csm.load_all_country_population_by_latitude(iso3_list, verbose=True)
    print(f"loaded {len(pop_by_lat)}/{len(iso3_list)} country rasters")

    for n in (4_408, 10_900, 100_000):
        rows = compute_country_tam(n, telecom_rows, household_size, pop_by_lat, lat_centers, hist, dens_centers)
        total = sum(r.tam_usd_per_month for r in rows)
        n_elastic = sum(1 for r in rows if r.price_basis == "elasticity_derived")
        n_local = sum(1 for r in rows if r.price_basis.startswith("existing_local_price"))
        print(f"--- N={n:,}: {len(rows)} countries, total TAM=${total:,.0f}/mo "
              f"({n_elastic} elasticity-priced, {n_local} local-priced) ---")
        top = sorted(rows, key=lambda r: -r.tam_usd_per_month)[:8]
        for r in top:
            print(f"  {r.iso3}: TAM=${r.tam_usd_per_month:,.0f}/mo, price=${r.price_usd_per_month:,.2f} "
                  f"({r.price_basis}), servable={r.servable_fraction:.1%}, subs={r.addressable_subscriptions:,.0f}")
