"""Country-level TAM (Total Addressable Market, in USD) for CURRENTLY-UNCONNECTED
populations only (2026-08-14, user request -- see CLAUDE.md's TAM-model section for
the full design conversation). Country-level granularity throughout, per the user's
explicit "note we're not going more granular than that."

Pricing rule per country (user-specified <20%/>=20% branch; internals revised
2026-08-23, see below):
  - If <20% of the population is unconnected: assume Starlink prices at whatever the
    LOCAL market already charges -- _raw_arpu() (charts/affordability.py), the same
    fixed/mobile dominant-access-mode proxy used throughout this project's
    affordability work (equilibrium_model.build_country_demand() uses the identical
    logic).
  - If >=20% is unconnected: price = that SAME local ARPU, multiplied by a bounded
    "scarcity premium" that scales with how little of the country Starlink's
    capacity can currently reach -- see _country_price() below for the formula and
    why.

**Revision 2026-08-23**: this branch previously derived a price from the elasticity
curve in served_population_vs_cost.py by inverting servable_fraction(N) through it
-- i.e. it treated a PHYSICAL SUPPLY constraint (how many satellites exist) as if it
were a DEMAND-side quantity (what price would leave that many people unconnected).
That conflation produced prices tens of times the real local price at low N (e.g.
India: $88.59/mo derived vs. $1.60/mo actually charged, at N=4,408) purely because
capacity was scarce, which has nothing to do with what the market would bear.
Replaced with a price anchored to each country's own real ARPU (see below) --
user-confirmed choice among two options presented, the other being to drop the
capacity-scaling behavior entirely and always use a straight ARPU/regional-median
fallback.

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

DATA = Path(__file__).resolve().parent / "data"

UNCONNECTED_PCT_THRESHOLD = 20.0  # user-specified: below this, use the local price unmodified

# Scarcity-premium ceiling for the >=20%-unconnected branch: at servable_fraction=0
# (capacity reaches almost no one), price = ARPU x this ceiling; at
# servable_fraction=1 (capacity reaches everyone), price = ARPU x 1 (no premium).
# Linear in between. A bounded, LOCAL-price-anchored replacement for the previous
# elasticity-curve-derived price (see module docstring) -- default picked as a
# reasonable, not user-confirmed, starting point; tune this one constant if a
# different scarcity-premium magnitude is wanted.
SCARCITY_PRICE_MULTIPLIER_CEILING = 3.0


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
    price_basis: str  # "existing_local_price" | "scarcity_premium_on_local_price" | "no_price_data"
    tam_usd_per_month: float


def load_telecom_rows() -> list[dict]:
    with open(DATA / "telecom_market_by_country.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_household_size() -> dict[str, float]:
    with open(DATA / "household_size_by_country.csv", encoding="utf-8") as f:
        return {r["iso3"]: float(r["household_size"]) for r in csv.DictReader(f)}


def _country_price(row: dict, servable_fraction: float, pct_unconnected: float) -> tuple[float, str]:
    """(price_usd_per_month, basis) for one country, per the rule in the module
    docstring. Both branches anchor to the same real local ARPU -- the >=20% branch
    additionally applies a bounded scarcity premium (see SCARCITY_PRICE_MULTIPLIER_CEILING)
    that relaxes to 1x (no premium) as servable_fraction approaches 1 (fully served)
    and rises to the ceiling as servable_fraction approaches 0 (capacity reaches
    almost no one). This does NOT protect against a bad/thin-sample ARPU figure
    (e.g. Zimbabwe's raw pre-cap ~$437/mo, ASSUMPTIONS.md #4) -- same known,
    already-flagged data-quality caveat as the <20% branch and the rest of this
    project's uncapped _raw_arpu() usage, not newly introduced here."""
    arpu = _raw_arpu(row)
    if not arpu:
        return 0.0, "no_price_data"
    if pct_unconnected < UNCONNECTED_PCT_THRESHOLD:
        return arpu, "existing_local_price"

    frac = min(max(servable_fraction, 0.0), 1.0)
    multiplier = SCARCITY_PRICE_MULTIPLIER_CEILING - (SCARCITY_PRICE_MULTIPLIER_CEILING - 1.0) * frac
    return arpu * multiplier, "scarcity_premium_on_local_price"


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


def sweep_tam_by_region(sat_counts, telecom_rows: list[dict], household_size: dict[str, float],
                         country_pop_by_lat: dict[str, tuple[np.ndarray, np.ndarray]],
                         global_lat_centers: np.ndarray, global_area_hist: np.ndarray,
                         global_dens_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                         base_shells: list[og.Shell] | None = None,
                         bin_width_deg: float = scm.BIN_WIDTH_DEG) -> dict[str, np.ndarray]:
    """{region: array of TAM $/month, one per sat_counts entry} -- same per-country
    computation as sweep_total_tam(), just grouped by `region` (the same World Bank
    region column used throughout this project, charts/regions.py) instead of
    summed to one global total. For the stacked-by-region TAM chart."""
    regions = sorted({r["region"] for r in telecom_rows})
    out: dict[str, list[float]] = {r: [] for r in regions}
    for n in sat_counts:
        rows = compute_country_tam(n, telecom_rows, household_size, country_pop_by_lat, global_lat_centers,
                                    global_area_hist, global_dens_centers, scenario, base_shells, bin_width_deg)
        by_region = dict.fromkeys(regions, 0.0)
        for row in rows:
            by_region[row.region] += row.tam_usd_per_month
        for r in regions:
            out[r].append(by_region[r])
    return {r: np.array(v) for r, v in out.items()}


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
        n_premium = sum(1 for r in rows if r.price_basis == "scarcity_premium_on_local_price")
        n_local = sum(1 for r in rows if r.price_basis == "existing_local_price")
        print(f"--- N={n:,}: {len(rows)} countries, total TAM=${total:,.0f}/mo "
              f"({n_premium} scarcity-premium-priced, {n_local} local-priced) ---")
        top = sorted(rows, key=lambda r: -r.tam_usd_per_month)[:8]
        for r in top:
            print(f"  {r.iso3}: TAM=${r.tam_usd_per_month:,.0f}/mo, price=${r.price_usd_per_month:,.2f} "
                  f"({r.price_basis}), servable={r.servable_fraction:.1%}, subs={r.addressable_subscriptions:,.0f}")
