"""Per-country servable-% at a given satellite count N (2026-08-14, for the TAM
model -- see CLAUDE.md). Answers "what % of country X's population can we serve at
N satellites" WITHOUT any new cross-border capacity-allocation logic: the existing
GLOBAL served_fraction_by_latitude(N) already reflects shared/competed satellite
capacity across every country at a given latitude (it's built from the global,
all-countries-combined population density histogram). A country's own servable-%
is then just that same per-band result, weighted-averaged by THAT COUNTRY's own
population-by-latitude distribution -- recovering the country-level number without
re-deriving how capacity gets split between neighbors.

Uses the per-country WorldPop 1km rasters already cached locally for the global
mosaic (216 files, data/raw/worldpop/{iso3}_pd_1km.tif via population_density_grid.
load_country_density_grid()) -- no new downloads needed. A country's own
population-by-latitude distribution doesn't depend on N, so it's loaded ONCE per
country and reused across an entire satellite-count sweep; only the (cheap, no
raster I/O) global served_fraction_by_latitude(N) changes per N.
"""
from __future__ import annotations

import numpy as np

import capacity_density_model as cdm
import orbital_geometry as og
import population_density_grid as pdg
import serviceable_customers_model as scm

WORLDPOP_DIR = pdg.WORLDPOP_DIR


def available_country_iso3() -> set[str]:
    """ISO3 codes with a cached per-country 1km density raster on disk."""
    return {p.name.split("_pd_1km.tif")[0].upper() for p in WORLDPOP_DIR.glob("*_pd_1km.tif")}


def load_all_country_population_by_latitude(iso3_list: list[str], bin_width_deg: float = scm.BIN_WIDTH_DEG,
                                             verbose: bool = False) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """{iso3: (lat_centers, pop_by_lat)} for every iso3 in iso3_list with a cached
    raster -- the one-time (per-country raster I/O) cost, reused across an entire N
    sweep. Skips (does not raise on) any iso3 without a cached file, since
    telecom_market_by_country.csv includes some territories WorldPop doesn't cover
    (matches population_density_grid.PopulationGrid.missing_iso3's existing
    convention for the global mosaic)."""
    available = available_country_iso3()
    out = {}
    skipped = []
    for i, iso3 in enumerate(iso3_list):
        if iso3 not in available:
            skipped.append(iso3)
            continue
        grid = pdg.load_country_density_grid(iso3)
        centers, pop = pdg.population_by_latitude(grid, bin_width_deg=bin_width_deg)
        out[iso3] = (centers, pop)
        if verbose and (i % 25 == 0):
            print(f"  loaded {i + 1}/{len(iso3_list)} country rasters ({iso3})")
    if verbose and skipped:
        print(f"  skipped {len(skipped)} countries with no cached raster: {skipped}")
    return out


def country_servable_fraction(total_sats: float, country_pop_by_lat: dict[str, tuple[np.ndarray, np.ndarray]],
                               global_lat_centers: np.ndarray, global_area_hist: np.ndarray,
                               global_dens_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                               base_shells: list[og.Shell] | None = None,
                               bin_width_deg: float = scm.BIN_WIDTH_DEG) -> dict[str, float]:
    """{iso3: servable_fraction} at one N -- the global per-band served_fraction,
    weight-averaged by each country's own population-by-latitude (from
    load_all_country_population_by_latitude(), computed once and reused across a
    whole sweep). Relies on population_by_latitude() and
    served_fraction_by_latitude() using the IDENTICAL latitude bin scheme
    (both np.arange(-90, 90+w, w)) so `global_frac`'s array lines up index-for-
    index with each country's own `pop` array with no re-indexing needed --
    verified by construction, not by chance (see both functions' shared
    _lat_bin_edges()-style edges)."""
    global_frac = scm.served_fraction_by_latitude(total_sats, global_area_hist, global_dens_centers,
                                                    global_lat_centers, scenario, base_shells, bin_width_deg)
    out = {}
    for iso3, (_centers, pop) in country_pop_by_lat.items():
        weight = np.where(np.isnan(global_frac), 0.0, pop)
        total_weight = weight.sum()
        if total_weight <= 0:
            out[iso3] = np.nan
            continue
        served = np.nansum(weight * global_frac)
        out[iso3] = float(served / total_weight)
    return out


def sweep_country_servable_fraction(sat_counts, country_pop_by_lat: dict[str, tuple[np.ndarray, np.ndarray]],
                                     global_lat_centers: np.ndarray, global_area_hist: np.ndarray,
                                     global_dens_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                                     base_shells: list[og.Shell] | None = None,
                                     bin_width_deg: float = scm.BIN_WIDTH_DEG) -> dict[str, np.ndarray]:
    """{iso3: array of servable_fraction, one per sat_counts entry} -- for a
    per-country TAM-vs-satellite-count sweep. Country rasters are NOT re-read here
    (country_pop_by_lat is precomputed once by the caller); only the cheap global
    served_fraction_by_latitude(N) call and the weighted averages repeat per N."""
    by_iso3: dict[str, list[float]] = {iso3: [] for iso3 in country_pop_by_lat}
    for n in sat_counts:
        fracs = country_servable_fraction(n, country_pop_by_lat, global_lat_centers, global_area_hist,
                                           global_dens_centers, scenario, base_shells, bin_width_deg)
        for iso3, f in fracs.items():
            by_iso3[iso3].append(f)
    return {iso3: np.array(vals) for iso3, vals in by_iso3.items()}


if __name__ == "__main__":
    grid = pdg.load_or_build_grid()
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)

    sample_iso3 = ["USA", "IND", "BRA", "NGA", "RUS", "AUS", "EGY", "CAN"]
    pop_by_lat = load_all_country_population_by_latitude(sample_iso3, verbose=True)
    print(f"loaded {len(pop_by_lat)}/{len(sample_iso3)} sample countries")

    for n in (4_408, 10_900, 100_000):
        fracs = country_servable_fraction(n, pop_by_lat, lat_centers, hist, dens_centers)
        print(f"--- N={n:,} ---")
        for iso3, f in sorted(fracs.items(), key=lambda kv: -kv[1]):
            print(f"  {iso3}: {f:.2%}")
