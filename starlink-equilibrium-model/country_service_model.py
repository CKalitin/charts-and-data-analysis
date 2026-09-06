"""Per-country servable-% at a given satellite count N -- read out from
tile_capacity_model.py's 2D (lat x lon) allocation.

WHAT CHANGED, AND WHY (2026-09-05)
==================================
This module used to weight a GLOBAL per-latitude-band served-fraction by each
country's population-by-latitude. That inherited a real bug from the layer below:
a latitude band is a full 40,000 km ring, so pooling its capacity let idle
satellites over the mid-Pacific serve demand in South Asia at the same latitude,
and every country sitting on a band was handed the same answer regardless of
longitude. Measured effect on servable customers: ~1.5x overstated at realistic
fleet sizes (see LONGITUDE_FOV_CAPACITY_REVIEW.md).

The readout is now per TILE. tile_capacity_model allocates satellite capacity
across a 1 degree lat/lon grid, where each satellite's budget is shared only within
its ~940 km coverage disk, so neighbouring countries genuinely compete for the same
satellite. A country's servable-% is its own population-weighted average of the
served-fraction of the tiles it actually occupies:

    servable(iso3) = sum over tiles of  country_pop[tile] * served_fraction[tile]
                     -------------------------------------------------------------
                                 sum over tiles of  country_pop[tile]

That is the same weighted-readout idea as before -- no new cross-border allocation
logic is invented here, because the tile model has already resolved who competes
with whom -- just at 1 degree x 1 degree instead of a whole latitude ring.

Population weights come from the per-country WorldPop 1 km rasters already cached
for the global mosaic (data/raw/worldpop/{iso3}_pd_1km.tif). A country's own
population distribution does not depend on N, so it is built once and reused across
an entire sweep, and cached to disk so a second process does not repeat the ~215
raster reads.

Residual assumption: within a single tile that straddles a border, capacity is
shared between countries in proportion to their population in that tile. At 1
degree most tiles are one country, and this is far weaker than the whole-ring
pooling it replaces -- but it is an assumption, not a derivation.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

import capacity_density_model as cdm
import orbital_geometry as og
import population_density_grid as pdg
import tile_capacity_model as tcm

WORLDPOP_DIR = pdg.WORLDPOP_DIR

#: {iso3: (tile_row, tile_col, population)} -- sparse, since a country occupies a
#: small fraction of the 64,800 tiles. Dense would be ~215 x 64,800 floats.
CountryTiles = dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]


def available_country_iso3() -> set[str]:
    """ISO3 codes with a cached per-country 1km density raster on disk."""
    return {p.name.split("_pd_1km.tif")[0].upper() for p in WORLDPOP_DIR.glob("*_pd_1km.tif")}


def _cache_path(tile_deg: float):
    return WORLDPOP_DIR / f"_country_pop_by_tile_{tile_deg:g}deg.npz"


def _one_country_by_tile(iso3: str, tile: tcm.TileGrid):
    """One country's population summed into the tile grid, returned sparse."""
    grid = pdg.load_country_density_grid(iso3)
    pop = pdg.cell_population(grid)
    lat_c = (grid.lat_edges[:-1] + grid.lat_edges[1:]) / 2   # descending, as PopulationGrid stores it
    lon_c = (grid.lon_edges[:-1] + grid.lon_edges[1:]) / 2
    n_lat, n_lon = tile.shape

    # Ascending tile index, matching TileGrid.lat_centers -- (lat + 90), NOT (90 - lat).
    # The mirrored form is a bug this project has already hit once, and it silently
    # flips the northern hemisphere into the southern.
    rows = np.clip(((lat_c + 90.0) / tile.tile_deg).astype(np.int64), 0, n_lat - 1)
    cols = np.clip(((lon_c + 180.0) / tile.tile_deg).astype(np.int64), 0, n_lon - 1)

    valid = ~np.isnan(pop)
    rr = np.broadcast_to(rows[:, None], pop.shape)[valid]
    cc = np.broadcast_to(cols[None, :], pop.shape)[valid]
    flat = np.bincount(rr * n_lon + cc, weights=pop[valid], minlength=n_lat * n_lon)
    nz = np.nonzero(flat)[0]
    return (nz // n_lon).astype(np.int32), (nz % n_lon).astype(np.int32), flat[nz]


def load_all_country_population_by_tile(iso3_list: list[str], tile: tcm.TileGrid | None = None,
                                        use_cache: bool = True, verbose: bool = False) -> CountryTiles:
    """{iso3: (rows, cols, population)} for every iso3 with a cached raster.

    Reads ~215 country rasters, which takes minutes, so results are cached to disk
    keyed on tile size. The cache is INCREMENTAL: countries already in it are reused,
    any requested country missing from it is built and merged back in. That matters --
    an earlier version simply returned the intersection of the cache with the request,
    so a cache written by a 10-country smoke test then satisfied a 217-country request
    with 10 countries and no error. Silently-partial caches are a failure mode this
    project has hit more than once.

    Countries with no cached raster are SKIPPED, not raised on --
    telecom_market_by_country.csv covers territories WorldPop does not (the same
    convention PopulationGrid.missing_iso3 already uses).
    """
    tile = tile if tile is not None else tcm.make_tile_grid()
    cache = _cache_path(tile.tile_deg)

    have: CountryTiles = {}
    if use_cache and cache.exists():
        d = np.load(cache, allow_pickle=False)
        codes = [c for c in str(d["iso3"]).split(",") if c]
        offs = d["offsets"]
        have = {code: (d["rows"][offs[i]:offs[i + 1]], d["cols"][offs[i]:offs[i + 1]],
                       d["pop"][offs[i]:offs[i + 1]]) for i, code in enumerate(codes)}

    available = available_country_iso3()
    missing = [c for c in iso3_list if c not in have and c in available]
    skipped = [c for c in iso3_list if c not in available]

    if missing:
        if verbose:
            print(f"  building {len(missing)} country tile footprints "
                  f"({len(have)} already cached)...")
        for i, iso3 in enumerate(missing, 1):
            have[iso3] = _one_country_by_tile(iso3, tile)
            if verbose and i % 25 == 0:
                print(f"    {i}/{len(missing)} ({iso3})")
        if use_cache:
            _save_country_tiles(cache, have)
    if verbose and skipped:
        print(f"  skipped {len(skipped)} countries with no cached raster: {skipped}")

    return {c: have[c] for c in iso3_list if c in have}


def _save_country_tiles(cache, tiles: CountryTiles) -> None:
    codes = sorted(tiles)
    lens = [len(tiles[c][0]) for c in codes]
    offsets = np.concatenate([[0], np.cumsum(lens)]).astype(np.int64)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache, iso3=",".join(codes), offsets=offsets,
        rows=np.concatenate([tiles[c][0] for c in codes]) if codes else np.zeros(0, np.int32),
        cols=np.concatenate([tiles[c][1] for c in codes]) if codes else np.zeros(0, np.int32),
        pop=np.concatenate([tiles[c][2] for c in codes]) if codes else np.zeros(0, float),
    )


def _servable_cache_path(tile: tcm.TileGrid, scenario: cdm.CapacityScenario,
                         base_shells: list[og.Shell] | None):
    """Cache file + the key it must match.

    Solving the tile model costs ~15 s per N, and a chart run sweeps dozens of N, so
    the per-country fractions are worth keeping on disk. The key covers everything
    that changes the answer -- capacity scenario, tile size, and every shell's
    altitude/inclination/count -- and is hashed into the FILENAME, so changing any of
    them lands on a different file rather than silently reusing stale numbers. The
    key is also stored inside the file and re-checked on load. This project has
    already been burned once by a cache that loaded successfully and contained the
    wrong thing (the all-NaN population grid), hence the belt and braces.
    """
    shells = base_shells if base_shells is not None else tcm.real_shells()
    sig = "|".join(f"{sh.altitude_km:.1f}/{sh.inclination_deg:.2f}/{sh.total_sats}"
                   for sh in sorted(shells, key=lambda x: x.shell_id))
    key = f"{scenario.label}|tile{tile.tile_deg:g}|{sig}"
    digest = hashlib.sha1(key.encode()).hexdigest()[:12]
    return WORLDPOP_DIR / f"_servable_cache_{digest}.json", key


def _load_servable_cache(path, key) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}
    try:
        blob = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    return blob.get("values", {}) if blob.get("key") == key else {}


def _save_servable_cache(path, key, values: dict[str, dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"key": key, "values": values}))


def _cache_key_for(total_sats: float) -> str:
    return f"{float(total_sats):.6g}"


def country_servable_fraction_from_result(result: tcm.AllocationResult,
                                          country_pop_by_tile: CountryTiles) -> dict[str, float]:
    """{iso3: servable_fraction} from an already-solved allocation.

    Split out from country_servable_fraction() so a sweep solves the tile model ONCE
    per N and reads out every country from that one result -- solving is the whole
    cost (~15 s), the readout is microseconds.

    Tiles whose served_fraction is NaN (no population in the tile model's own grid)
    get zero weight rather than poisoning the average.
    """
    frac = result.served_fraction
    out = {}
    for iso3, (rows, cols, pop) in country_pop_by_tile.items():
        f = frac[rows, cols]
        weight = np.where(np.isnan(f), 0.0, pop)
        total = weight.sum()
        if total <= 0:
            out[iso3] = np.nan
            continue
        out[iso3] = float(np.nansum(weight * np.nan_to_num(f)) / total)
    return out


def country_servable_fraction(total_sats: float, country_pop_by_tile: CountryTiles,
                              tile: tcm.TileGrid | None = None,
                              demand: tcm.DemandTiles | None = None,
                              scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                              base_shells: list[og.Shell] | None = None,
                              operator_cache: dict | None = None,
                              use_cache: bool = True) -> dict[str, float]:
    """{iso3: servable_fraction} at one N. Convenience wrapper: solves the tile
    model, then reads every country out of that one solve."""
    tile = tile if tile is not None else tcm.make_tile_grid()
    path, key = _servable_cache_path(tile, scenario, base_shells)
    if use_cache:
        cached = _load_servable_cache(path, key).get(_cache_key_for(total_sats))
        if cached is not None and all(iso3 in cached for iso3 in country_pop_by_tile):
            return {iso3: cached[iso3] for iso3 in country_pop_by_tile}

    demand = demand if demand is not None else tcm.build_demand(tile)
    result = tcm.solve(total_sats, tile=tile, demand=demand, scenario=scenario,
                       base_shells=base_shells, operator_cache=operator_cache)
    fracs = country_servable_fraction_from_result(result, country_pop_by_tile)

    if use_cache:
        values = _load_servable_cache(path, key)
        values.setdefault(_cache_key_for(total_sats), {}).update(fracs)
        _save_servable_cache(path, key, values)
    return fracs


def sweep_country_servable_fraction(sat_counts, country_pop_by_tile: CountryTiles,
                                    tile: tcm.TileGrid | None = None,
                                    demand: tcm.DemandTiles | None = None,
                                    scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                                    base_shells: list[og.Shell] | None = None,
                                    use_cache: bool = True,
                                    verbose: bool = False) -> dict[str, np.ndarray]:
    """{iso3: array of servable_fraction, one per sat_counts entry}.

    One tile-model solve per N (~15 s each), reusing one tile grid, one demand build
    and one operator cache across the whole sweep -- the disk kernels depend only on
    radius and grid, not on N, and rebuilding them is most of the per-solve cost.
    """
    tile = tile if tile is not None else tcm.make_tile_grid()
    operator_cache: dict = {}
    by_iso3: dict[str, list[float]] = {iso3: [] for iso3 in country_pop_by_tile}
    for i, n in enumerate(sat_counts, 1):
        fracs = country_servable_fraction(n, country_pop_by_tile, tile, demand, scenario,
                                          base_shells, operator_cache, use_cache=use_cache)
        for iso3, f in fracs.items():
            by_iso3[iso3].append(f)
        if verbose:
            print(f"  {i}/{len(sat_counts)}: N={n:,.0f}")
    return {iso3: np.array(v) for iso3, v in by_iso3.items()}


if __name__ == "__main__":
    import time

    t0 = time.time()
    tile = tcm.make_tile_grid()
    demand = tcm.build_demand(tile)
    sample = ["USA", "IND", "BRA", "NGA", "RUS", "AUS", "EGY", "CAN", "CHN", "IDN"]
    pop_by_tile = load_all_country_population_by_tile(sample, tile, verbose=True)
    print(f"loaded {len(pop_by_tile)}/{len(sample)} sample countries in {time.time()-t0:.1f}s")

    cache: dict = {}
    for n in (4_408, 10_900, 100_000):
        fracs = country_servable_fraction(n, pop_by_tile, tile, demand, operator_cache=cache)
        print(f"--- N={n:,} ---")
        for iso3, f in sorted(fracs.items(), key=lambda kv: -kv[1]):
            print(f"  {iso3}: {f:.2%}")
