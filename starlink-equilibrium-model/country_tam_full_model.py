"""Country-level TAM (Total Addressable Market, USD) for the ENTIRE population --
NOT just currently-unconnected people (see country_tam_model.py for that, still
intact and unchanged). Models Starlink "just takes incumbent share as it expands"
(2026-08-16 user request, answered via AskUserQuestion before building this):

- **Share capture**: within whatever fraction of a country's population Starlink
  can physically reach at N satellites -- servable_fraction(N), the SAME
  capacity-constrained function country_tam_model.py already uses -- Starlink is
  assumed to win ALL of that population's business. 100% capture inside the
  footprint, 0% outside it. No switching-friction/partial-adoption curve, per the
  user's literal "just takes" framing (user-confirmed: "Full capture (100%)", not
  the partial-adoption-ceiling alternative offered).
- servable_fraction(N) itself doesn't distinguish connected from unconnected
  people -- it's built from TOTAL population density (population_density_grid.py),
  not a connectivity-filtered subset -- so removing country_tam_model.py's
  `min(unconnected_population, ...)` cap and letting the full population flow
  through requires no new capacity modeling, just a formula change.
- **Pricing (user-confirmed: "Split pricing")**: the servable population is split
  into two segments by price mechanism, since a straight incumbent-price swap and
  a new-customer elasticity price are different economic events:
    - "Incumbent" segment: the part of the servable population that was ALREADY
      connected (paying an existing provider) -- assumed to switch to Starlink at
      roughly the price they're already paying (`_raw_arpu()`), a revenue swap,
      not new price discovery.
    - "New" segment: the part that was previously UNCONNECTED -- priced via
      country_tam_model.py's OWN `_country_price()` (the same <20%-unconnected ->
      local price / >=20% -> elasticity-derived threshold rule), reused directly
      rather than reimplemented, applied here to price newly-served customers
      specifically rather than the whole country at once.
  No sub-national data exists to know WHICH people within a density bin are
  already connected, so the servable population is split into these two segments
  PROPORTIONALLY to the country's own overall connected/unconnected ratio -- an
  explicit simplifying assumption, consistent with this project's country-level
  granularity convention (documented here, not hidden).

TAM ($/month) = incumbent-segment subscriptions x incumbent price + new-segment
subscriptions x new price, summed per country for a global total. NOT annualized
by default, matching country_tam_model.py's convention.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import capacity_density_model as cdm
import country_service_model as csm
import orbital_geometry as og
import serviceable_customers_model as scm
from charts.affordability import _raw_arpu
from country_tam_model import _country_price, load_household_size, load_telecom_rows

# re-exported for callers that only need this module (mirrors country_tam_model.py's
# own module-level load_telecom_rows/load_household_size -- same CSVs, no reason to
# duplicate the loaders)
__all__ = ["CountryTAMFull", "compute_country_tam_full", "sweep_total_tam_full",
           "sweep_tam_full_by_region", "sweep_tam_full_by_segment", "load_telecom_rows",
           "load_household_size"]


@dataclass(frozen=True)
class CountryTAMFull:
    iso3: str
    country: str
    region: str
    population: float
    connected_population: float
    unconnected_population: float
    servable_fraction: float
    addressable_population: float
    addressable_connected_population: float
    addressable_unconnected_population: float
    household_size: float
    subscriptions_incumbent: float
    subscriptions_new: float
    price_incumbent_usd_per_month: float
    price_new_usd_per_month: float
    price_incumbent_basis: str  # "existing_local_price" | "no_price_data"
    price_new_basis: str  # "existing_local_price" | "existing_local_price_gni_missing" | "elasticity_derived" | "no_price_data"
    tam_incumbent_usd_per_month: float
    tam_new_usd_per_month: float
    tam_usd_per_month: float


def compute_country_tam_full(total_sats: float, telecom_rows: list[dict], household_size: dict[str, float],
                              country_pop_by_lat: dict[str, tuple[np.ndarray, np.ndarray]],
                              global_lat_centers: np.ndarray, global_area_hist: np.ndarray,
                              global_dens_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                              base_shells: list[og.Shell] | None = None,
                              bin_width_deg: float = scm.BIN_WIDTH_DEG) -> list[CountryTAMFull]:
    """CountryTAMFull for every country with both telecom data and a cached
    population raster -- same shape as country_tam_model.compute_country_tam(),
    country_pop_by_lat precomputed ONCE by the caller and reused across an N sweep."""
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
        connected = pop - unconn
        pct_unconnected = 100.0 * unconn / pop
        frac = servable[iso3]

        addressable_connected = frac * connected
        addressable_unconnected = frac * unconn

        hh_size = household_size.get(iso3)
        if not hh_size:
            continue
        subs_incumbent = addressable_connected / hh_size
        subs_new = addressable_unconnected / hh_size

        price_incumbent = _raw_arpu(row)
        basis_incumbent = "existing_local_price" if price_incumbent else "no_price_data"
        tam_incumbent = subs_incumbent * price_incumbent if price_incumbent else 0.0

        price_new, basis_new = _country_price(row, frac, pct_unconnected)
        tam_new = subs_new * price_new if basis_new != "no_price_data" else 0.0

        out.append(CountryTAMFull(
            iso3=iso3, country=row["country"], region=row["region"], population=pop,
            connected_population=connected, unconnected_population=unconn, servable_fraction=frac,
            addressable_population=frac * pop, addressable_connected_population=addressable_connected,
            addressable_unconnected_population=addressable_unconnected, household_size=hh_size,
            subscriptions_incumbent=subs_incumbent, subscriptions_new=subs_new,
            price_incumbent_usd_per_month=price_incumbent, price_new_usd_per_month=price_new,
            price_incumbent_basis=basis_incumbent, price_new_basis=basis_new,
            tam_incumbent_usd_per_month=tam_incumbent, tam_new_usd_per_month=tam_new,
            tam_usd_per_month=tam_incumbent + tam_new,
        ))
    return out


def sweep_total_tam_full(sat_counts, telecom_rows: list[dict], household_size: dict[str, float],
                          country_pop_by_lat: dict[str, tuple[np.ndarray, np.ndarray]],
                          global_lat_centers: np.ndarray, global_area_hist: np.ndarray,
                          global_dens_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                          base_shells: list[og.Shell] | None = None,
                          bin_width_deg: float = scm.BIN_WIDTH_DEG) -> np.ndarray:
    """Total TAM ($/month, summed across every country) at each N in sat_counts."""
    out = []
    for n in sat_counts:
        rows = compute_country_tam_full(n, telecom_rows, household_size, country_pop_by_lat, global_lat_centers,
                                         global_area_hist, global_dens_centers, scenario, base_shells, bin_width_deg)
        out.append(sum(r.tam_usd_per_month for r in rows))
    return np.array(out)


def sweep_tam_full_by_region(sat_counts, telecom_rows: list[dict], household_size: dict[str, float],
                              country_pop_by_lat: dict[str, tuple[np.ndarray, np.ndarray]],
                              global_lat_centers: np.ndarray, global_area_hist: np.ndarray,
                              global_dens_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                              base_shells: list[og.Shell] | None = None,
                              bin_width_deg: float = scm.BIN_WIDTH_DEG) -> dict[str, np.ndarray]:
    """{region: array of TAM $/month} -- same per-country computation as
    sweep_total_tam_full(), grouped by World Bank region instead of summed to one
    global total. For the stacked-by-region TAM chart."""
    regions = sorted({r["region"] for r in telecom_rows})
    out: dict[str, list[float]] = {r: [] for r in regions}
    for n in sat_counts:
        rows = compute_country_tam_full(n, telecom_rows, household_size, country_pop_by_lat, global_lat_centers,
                                         global_area_hist, global_dens_centers, scenario, base_shells, bin_width_deg)
        by_region = dict.fromkeys(regions, 0.0)
        for row in rows:
            by_region[row.region] += row.tam_usd_per_month
        for r in regions:
            out[r].append(by_region[r])
    return {r: np.array(v) for r, v in out.items()}


def sweep_tam_full_by_segment(sat_counts, telecom_rows: list[dict], household_size: dict[str, float],
                               country_pop_by_lat: dict[str, tuple[np.ndarray, np.ndarray]],
                               global_lat_centers: np.ndarray, global_area_hist: np.ndarray,
                               global_dens_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                               base_shells: list[og.Shell] | None = None,
                               bin_width_deg: float = scm.BIN_WIDTH_DEG) -> dict[str, np.ndarray]:
    """{"incumbent": array, "new": array} of TAM $/month -- same total as
    sweep_total_tam_full(), split by revenue captured from already-connected
    switchers vs. newly-connected customers. The direct payoff of the split-pricing
    design decision: shows how the revenue MIX shifts as N grows, not just the total."""
    incumbent, new = [], []
    for n in sat_counts:
        rows = compute_country_tam_full(n, telecom_rows, household_size, country_pop_by_lat, global_lat_centers,
                                         global_area_hist, global_dens_centers, scenario, base_shells, bin_width_deg)
        incumbent.append(sum(r.tam_incumbent_usd_per_month for r in rows))
        new.append(sum(r.tam_new_usd_per_month for r in rows))
    return {"incumbent": np.array(incumbent), "new": np.array(new)}


if __name__ == "__main__":
    import population_density_grid as pdg

    grid = pdg.load_or_build_grid()
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    telecom_rows = load_telecom_rows()
    household_size = load_household_size()

    iso3_list = [r["iso3"] for r in telecom_rows]
    pop_by_lat = csm.load_all_country_population_by_latitude(iso3_list, verbose=True)
    print(f"loaded {len(pop_by_lat)}/{len(iso3_list)} country rasters")

    for n in (4_408, 10_900, 100_000):
        rows = compute_country_tam_full(n, telecom_rows, household_size, pop_by_lat, lat_centers, hist, dens_centers)
        total = sum(r.tam_usd_per_month for r in rows)
        total_incumbent = sum(r.tam_incumbent_usd_per_month for r in rows)
        total_new = sum(r.tam_new_usd_per_month for r in rows)
        print(f"--- N={n:,}: {len(rows)} countries, total TAM=${total:,.0f}/mo "
              f"(${total_incumbent:,.0f} incumbent-displaced, ${total_new:,.0f} newly-connected) ---")
        top = sorted(rows, key=lambda r: -r.tam_usd_per_month)[:8]
        for r in top:
            print(f"  {r.iso3}: TAM=${r.tam_usd_per_month:,.0f}/mo (incumbent=${r.tam_incumbent_usd_per_month:,.0f}, "
                  f"new=${r.tam_new_usd_per_month:,.0f}), servable={r.servable_fraction:.1%}, "
                  f"subs={r.subscriptions_incumbent + r.subscriptions_new:,.0f}")
