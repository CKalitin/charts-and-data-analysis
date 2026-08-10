"""Mosaic the per-country WorldPop 1km population-density GeoTIFFs
(data/raw/worldpop/{iso3}_pd_1km.tif, from download_worldpop.py) into one coarse
global lon/lat grid suitable for a world-map heatmap.

Each source file is an independent, unaligned raster (own tiepoint/origin, WGS84
lon/lat pixels, ~0.0083333deg = 1/120deg per pixel -- the "1km" grid). There is no
single global array to mosaic into directly; instead each country is block-averaged
down to TARGET_DEG resolution (0.0083333 * 12 = 0.1deg exactly, so the standard
WorldPop pixel size divides evenly into a round target -- no interpolation needed)
and scatter-accumulated (sum + count, for a true weighted mean where neighboring
countries' cells land in the same output bin) into one global grid.

Output is cached to data/raw/worldpop/_grid_cache_<deg>deg.npz -- this directory is
already gitignored (large downloaded data), and rebuilding from all ~215 GeoTIFFs
takes real time, so callers should always go through load_or_build_grid() rather
than re-running build_global_grid() per chart.
"""
from __future__ import annotations

import csv
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import tifffile

DATA = Path(__file__).resolve().parent / "data"
WORLDPOP_DIR = DATA / "raw" / "worldpop"
NODATA = -99999.0  # fallback only -- _read_country_raster prefers the file's own GDAL_NODATA tag
SRC_DEG = 1.0 / 120.0  # WorldPop's native "1km" pixel size, exact
TARGET_DEG = 0.1  # -> 3600 x 1800 global grid; SRC_DEG * 12 == TARGET_DEG exactly
BLOCK = round(TARGET_DEG / SRC_DEG)  # 12
KM_PER_DEG = 111.32  # spherical approximation, used everywhere cell area is derived from degrees


@dataclass(frozen=True)
class PopulationGrid:
    lon_edges: np.ndarray  # (ncols+1,)
    lat_edges: np.ndarray  # (nrows+1,) descending (north -> south, row 0 = top)
    density: np.ndarray  # (nrows, ncols) people/km^2, NaN where no data
    n_countries: int
    missing_iso3: list[str]


def _cache_path(target_deg: float) -> Path:
    return WORLDPOP_DIR / f"_grid_cache_{target_deg:g}deg.npz"


def _read_country_raster(path: Path):
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        arr = page.asarray().astype(np.float32)
        scale = page.tags[33550].value  # (dx, dy, 0)
        tie = page.tags[33922].value  # (i, j, k, lon0, lat0, 0) for pixel (0,0)'s top-left corner
        nodata_tag = page.tags.get(42113)  # GDAL_NODATA -- read per-file, don't assume -99999
        nodata = float(nodata_tag.value) if nodata_tag is not None else NODATA
    arr[arr == nodata] = np.nan
    lon0, lat0 = tie[3], tie[4]
    dx, dy = scale[0], scale[1]
    return arr, lon0, lat0, dx, dy


def _grid_from_raster(arr, lon0, lat0, dx, dy, block: int = 1,
                       n_countries: int = 1, missing_iso3: list[str] | None = None) -> "PopulationGrid":
    """Wrap one already-loaded (and already density-valued) raster array into a
    PopulationGrid using ITS OWN lon/lat edges -- no mosaicking, for callers that
    want a single country/region in isolation."""
    reduced = _block_reduce_mean(arr, block)
    eff_block = block if reduced.shape != arr.shape else 1
    rh, rw = reduced.shape
    lon_edges = lon0 + np.arange(rw + 1) * dx * eff_block
    lat_edges = lat0 - np.arange(rh + 1) * dy * eff_block
    return PopulationGrid(lon_edges, lat_edges, reduced.astype(np.float32), n_countries, missing_iso3 or [])


def load_country_density_grid(iso3: str, block: int = 1) -> "PopulationGrid":
    """Load one country's own 1km density raster directly (not mosaicked into the
    shared global grid) -- avoids the global grid's cross-border quantization when a
    chart wants ONE country in isolation (e.g. a US-only histogram or model run)."""
    path = WORLDPOP_DIR / f"{iso3.lower()}_pd_1km.tif"
    arr, lon0, lat0, dx, dy = _read_country_raster(path)
    return _grid_from_raster(arr, lon0, lat0, dx, dy, block=block)


def load_population_count_raster_as_density(path: Path, block: int = 1) -> "PopulationGrid":
    """Load a WorldPop *population-count* raster (the 100m 'ppp' product -- people
    PER PIXEL, not density) and convert to people/km^2 by dividing each pixel by its
    own geographic area (pixel width shrinks with cos(latitude), same convention used
    everywhere else in this module)."""
    arr, lon0, lat0, dx, dy = _read_country_raster(path)
    lat_centers = lat0 - (np.arange(arr.shape[0]) + 0.5) * dy
    cell_area_km2 = (dy * KM_PER_DEG) * (dx * KM_PER_DEG * np.cos(np.radians(lat_centers)))
    with np.errstate(invalid="ignore"):
        density = arr / cell_area_km2[:, None]
    return _grid_from_raster(density, lon0, lat0, dx, dy, block=block)


def _block_reduce_mean(arr: np.ndarray, block: int) -> np.ndarray:
    """Crop to a multiple of `block` and average each block x block tile, ignoring NaN."""
    h, w = arr.shape
    h2, w2 = (h // block) * block, (w // block) * block
    if h2 == 0 or w2 == 0:
        return arr  # tiny territory smaller than one block -> keep native resolution
    cropped = arr[:h2, :w2].reshape(h2 // block, block, w2 // block, block)
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Mean of empty slice")
        return np.nanmean(cropped, axis=(1, 3))


def build_global_grid(target_deg: float = TARGET_DEG) -> PopulationGrid:
    block = round(target_deg / SRC_DEG)
    n_lon = round(360.0 / target_deg)
    n_lat = round(180.0 / target_deg)
    lon_edges = np.linspace(-180.0, 180.0, n_lon + 1)
    lat_edges = np.linspace(90.0, -90.0, n_lat + 1)  # descending: row 0 = north

    sum_grid = np.zeros((n_lat, n_lon), dtype=np.float64)
    count_grid = np.zeros((n_lat, n_lon), dtype=np.int32)

    tif_files = sorted(WORLDPOP_DIR.glob("*_pd_1km.tif"))
    for f in tif_files:
        arr, lon0, lat0, dx, dy = _read_country_raster(f)
        reduced = _block_reduce_mean(arr, block)
        rh, rw = reduced.shape
        eff_block = block if reduced.shape != arr.shape else 1

        row_idx = np.arange(rh)
        col_idx = np.arange(rw)
        cell_lat = lat0 - (row_idx + 0.5) * dy * eff_block
        cell_lon = lon0 + (col_idx + 0.5) * dx * eff_block

        # Uniform grid -> direct floor-division index, no searchsorted sign pitfalls.
        col_g = np.clip(((cell_lon + 180.0) / target_deg).astype(np.int64), 0, n_lon - 1)
        row_g = np.clip(((90.0 - cell_lat) / target_deg).astype(np.int64), 0, n_lat - 1)

        valid = ~np.isnan(reduced)
        rr, cc = np.meshgrid(row_g, col_g, indexing="ij")
        rr, cc, vv = rr[valid], cc[valid], reduced[valid]
        np.add.at(sum_grid, (rr, cc), vv)
        np.add.at(count_grid, (rr, cc), 1)

    with np.errstate(invalid="ignore", divide="ignore"):
        density = np.where(count_grid > 0, sum_grid / np.maximum(count_grid, 1), np.nan)

    missing = _load_missing_iso3(tif_files)
    return PopulationGrid(lon_edges, lat_edges, density.astype(np.float32), len(tif_files), missing)


def _load_missing_iso3(tif_files: list[Path]) -> list[str]:
    have = {f.name.split("_")[0].upper() for f in tif_files}
    manifest = WORLDPOP_DIR / "_manifest.csv"
    missing = []
    if manifest.exists():
        with open(manifest, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["iso3"].upper() not in have:
                    missing.append(r["iso3"])
    return missing


def load_or_build_grid(target_deg: float = TARGET_DEG, use_cache: bool = True) -> PopulationGrid:
    cache = _cache_path(target_deg)
    if use_cache and cache.exists():
        d = np.load(cache, allow_pickle=False)
        missing = [s for s in str(d["missing_iso3"]).split(",") if s] if "missing_iso3" in d else []
        return PopulationGrid(d["lon_edges"], d["lat_edges"], d["density"], int(d["n_countries"]), missing)

    grid = build_global_grid(target_deg)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache,
        lon_edges=grid.lon_edges,
        lat_edges=grid.lat_edges,
        density=grid.density,
        n_countries=grid.n_countries,
        missing_iso3=",".join(grid.missing_iso3),
    )
    return grid


def row_areas_km2(grid: "PopulationGrid") -> np.ndarray:
    """Per-row cell area (km^2), (nrows,) -- lon-width shrinks with cos(latitude);
    lat-height is constant. Broadcast against `grid.density` as `area[:, None]`."""
    lat_centers = (grid.lat_edges[:-1] + grid.lat_edges[1:]) / 2
    cell_h_km = abs(grid.lat_edges[0] - grid.lat_edges[1]) * KM_PER_DEG
    cell_w_km = abs(grid.lon_edges[1] - grid.lon_edges[0]) * KM_PER_DEG * np.cos(np.radians(lat_centers))
    return cell_h_km * cell_w_km


def cell_population(grid: "PopulationGrid") -> np.ndarray:
    """Per-cell population (density x cell area), 2D, NaN where the grid has no data."""
    return grid.density * row_areas_km2(grid)[:, None]


def population_by_latitude(grid: "PopulationGrid", bin_width_deg: float = 1.0):
    """Total population per bin_width_deg latitude band, from the gridded density.
    Returns (bin_centers, population_per_bin)."""
    lat_centers = (grid.lat_edges[:-1] + grid.lat_edges[1:]) / 2
    pop_row = np.nansum(cell_population(grid), axis=1)

    edges = np.arange(-90, 90 + bin_width_deg, bin_width_deg)
    centers = (edges[:-1] + edges[1:]) / 2
    # centers[] runs ASCENDING (-89.5 -> 89.5, from np.arange(-90, 90+w, w)), so the
    # bin index must ascend with latitude too -- (lat + 90) / w, NOT (90 - lat) / w
    # (that mirrored version was a real bug, caught by an implausible south-heavy
    # population-by-latitude chart: India/China's real northern-hemisphere peak was
    # showing up mirrored into the southern hemisphere).
    bin_idx = np.clip(((lat_centers + 90.0) / bin_width_deg).astype(np.int64), 0, len(centers) - 1)
    out = np.zeros(len(centers))
    np.add.at(out, bin_idx, pop_row)
    return centers, out


if __name__ == "__main__":
    import time

    t0 = time.time()
    g = load_or_build_grid(use_cache=False)
    dt = time.time() - t0
    valid = ~np.isnan(g.density)
    print(f"Built {g.density.shape[0]}x{g.density.shape[1]} grid @ {TARGET_DEG}deg from "
          f"{g.n_countries} countries in {dt:.1f}s")
    print(f"  {valid.sum():,} populated cells, max density {np.nanmax(g.density):,.0f} people/km^2")
    print(f"  missing (no WorldPop data): {g.missing_iso3}")
