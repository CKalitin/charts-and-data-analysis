"""Serviceable-customers model: combines three previously-separate pieces of this
project into one curve of servable customers vs. total constellation size N.

  1. orbital_geometry.py       -- expected satellites overhead by latitude, for a
                                   constellation split across REAL Starlink shells
                                   (Phase 2's well-sourced Gen1 geometry).
  2. capacity_density_model.py -- max customers per satellite (an aggregate capacity
                                   ceiling) AND max customer density per km^2 (an
                                   independent per-area beam-footprint ceiling)
                                   (Phase 3).
  3. population_density_grid.py -- real gridded population density (WorldPop), at
                                   whatever native resolution the caller passes in
                                   (1km or 100m -- this module is resolution-agnostic,
                                   it just consumes a PopulationGrid).

This is the "next integration step" flagged repeatedly in CLAUDE.md: Phase 5/6's
equilibrium_model.py still spreads each country's density cap over whole COUNTRY
land area (AG.LND.TOTL.K2). Here the density cap is applied per GRID CELL instead --
a direct fix to that known overstatement, and the point of downloading WorldPop data
in the first place.

Shell split: REAL Starlink Gen1 shell geometry (data/starlink_shells.csv via
orbital_geometry.load_shells_with_full_geometry() -- the same well-sourced 5-sub-
shell table Phase 2/3 use: 550km/53.0deg, 540km/53.2deg, 570km/70.0deg, 560km/97.6deg
split into two plane-count sub-groups, 4,408 satellites total). An early version of
this model used a hand-picked rough ratio (45/65/80deg, 5:1:1) as a placeholder --
the user corrected this ("use the real Starlink satellite plane data"), so
scale_shells_to_total() now scales the REAL per-shell plane counts (preserving each
shell's own true altitude/inclination and its real share of the total) to hit any
target N, rather than inventing a 3-shell stand-in. Fractional satellites per shell
at N != 4,408 are the same "expected value" treatment orbital_geometry.py already
uses elsewhere in this project, not a claim that Starlink literally launches
fractional satellites.

Two constraints combine locally, per 1deg latitude band, then sum -- NOT globally:
excess satellite capacity at a sparsely-populated latitude (e.g. 80deg) cannot serve
demand at a different, densely-populated latitude (e.g. 30deg), so the min() must be
taken band-by-band before summing, not on the two global totals (which would let one
band's surplus paper over another's shortfall).
"""
from __future__ import annotations

import numpy as np

import capacity_density_model as cdm
import orbital_geometry as og
import population_density_grid as pdg

BIN_WIDTH_DEG = 1.0


def real_shells() -> list[og.Shell]:
    """The well-sourced Gen1 5-sub-shell geometry (data/starlink_shells.csv via
    orbital_geometry.py) -- REAL altitude/inclination/orbital_planes/sats_per_plane,
    not a hand-picked ratio. Default base for every function below."""
    return og.load_shells_with_full_geometry()


def scale_shells_to_total(total_sats: float, base_shells: list[og.Shell] | None = None) -> list[og.Shell]:
    """Scale a real shell configuration's plane count proportionally to hit
    total_sats, preserving each shell's own altitude/inclination and its relative
    share of the total -- the "expected value" treatment used throughout this
    project for non-integer satellite counts. orbital_planes is fixed at 1 and
    sats_per_plane carries the (possibly fractional) count; only their product and
    the shell's own altitude feed the physics used here (period, latitude density),
    so the split between the two fields doesn't matter."""
    base_shells = base_shells if base_shells is not None else real_shells()
    base_total = sum(s.total_sats for s in base_shells)
    return [
        og.Shell(
            shell_id=s.shell_id, generation=s.generation, altitude_km=s.altitude_km,
            inclination_deg=s.inclination_deg, orbital_planes=1,
            sats_per_plane=total_sats * (s.total_sats / base_total),
            status="scaled",
        )
        for s in base_shells
    ]


def max_latitude_covered(base_shells: list[og.Shell] | None = None) -> float:
    base_shells = base_shells if base_shells is not None else real_shells()
    return max(og.max_latitude_deg(s.inclination_deg) for s in base_shells)


def sats_overhead_by_latitude(total_sats: float, base_shells: list[og.Shell] | None = None,
                               bin_width_deg: float = BIN_WIDTH_DEG):
    """Expected satellites overhead per latitude band, summed across all shells --
    the raw quantity both capacity_by_latitude() (multiplied by customers/satellite)
    and the per-satellite-cap model below (multiplied by density/satellite) scale
    from. NOT restricted to the covered band here -- callers apply that mask."""
    shells = scale_shells_to_total(total_sats, base_shells)
    centers, by_shell = og.expected_sats_by_latitude(shells, bin_width_deg=bin_width_deg)
    return centers, np.sum(list(by_shell.values()), axis=0)


def capacity_by_latitude(total_sats: float, scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                          base_shells: list[og.Shell] | None = None, bin_width_deg: float = BIN_WIDTH_DEG):
    """Aggregate simultaneous-customer capacity per latitude band, for total_sats
    split across the real shell geometry. Zero outside the union of shells'
    coverage bands."""
    centers, sats_overhead = sats_overhead_by_latitude(total_sats, base_shells, bin_width_deg)
    customers_per_sat = cdm.max_customers_per_satellite(scenario)
    cap = sats_overhead * customers_per_sat
    covered = np.abs(centers) <= max_latitude_covered(base_shells)
    return centers, np.where(covered, cap, 0.0)


def effective_density_cap_by_latitude(total_sats: float, scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                       base_shells: list[og.Shell] | None = None,
                                       bin_width_deg: float = BIN_WIDTH_DEG):
    """Effective per-area density ceiling (people/km^2) per latitude band, under the
    per-satellite-cap model: base_cap x satellites overhead that band -- the
    density-counterpart of capacity_by_latitude() above (which does the same for
    the aggregate per-satellite capacity cap instead). See the "Per-satellite
    density cap variant" section below for the full mechanism. Zero outside the
    union of shells' coverage bands."""
    centers, sats_overhead = sats_overhead_by_latitude(total_sats, base_shells, bin_width_deg)
    base_cap = cdm.max_customer_density_per_km2(scenario)
    covered = np.abs(centers) <= max_latitude_covered(base_shells)
    return centers, np.where(covered, base_cap * sats_overhead, 0.0)


def effective_density_cap_profile_average(total_sats: float,
                                           scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                           base_shells: list[og.Shell] | None = None,
                                           bin_width_deg: float = BIN_WIDTH_DEG) -> float:
    """A single number summarizing effective_density_cap_by_latitude() across the
    WHOLE real shell profile, instead of picking a few representative latitudes:
    the satellites-overhead-WEIGHTED average density ceiling. Weighting by
    sats_overhead (not a plain average across latitude bins) means this reflects
    where the real constellation actually puts its satellites -- dominated by the
    53deg shells (72% of Gen1), pulled down somewhat by the thinner 70/97.6deg
    coverage -- "the effective ceiling a typical satellite in this constellation
    supports," not an arbitrary single-latitude cut."""
    centers, sats_overhead = sats_overhead_by_latitude(total_sats, base_shells, bin_width_deg)
    base_cap = cdm.max_customer_density_per_km2(scenario)
    covered = np.abs(centers) <= max_latitude_covered(base_shells)
    cap_by_lat = np.where(covered, base_cap * sats_overhead, 0.0)
    weight = np.where(covered, sats_overhead, 0.0)
    total_weight = weight.sum()
    return float((cap_by_lat * weight).sum() / total_weight) if total_weight > 0 else 0.0


def _lat_bin_edges(bin_width_deg: float):
    edges = np.arange(-90, 90 + bin_width_deg, bin_width_deg)
    centers = (edges[:-1] + edges[1:]) / 2
    return centers


def _lat_bin_index(lat_centers: np.ndarray, bin_width_deg: float, n_bins: int) -> np.ndarray:
    # ascending bin index to match _lat_bin_edges()'s ascending order -- see the same
    # fix (and why) in population_density_grid.population_by_latitude().
    return np.clip(((lat_centers + 90.0) / bin_width_deg).astype(np.int64), 0, n_bins - 1)


def _capped_population_per_row(density_or_count_chunk: np.ndarray, area_row_km2: np.ndarray,
                                max_density_cap: float, already_density: bool) -> np.ndarray:
    """min(actual population, beam-footprint density cap x cell area), summed across
    each row -- the per-cell version of Phase 5's min(unconnected_pop, density_ceiling
    x land_area), applied at the raster's native resolution instead of a
    whole-country average area. `already_density=False` divides a population-COUNT
    chunk (people per pixel, e.g. the 100m 'ppp' product) by its own cell area first."""
    density = density_or_count_chunk if already_density else density_or_count_chunk / area_row_km2[:, None]
    with np.errstate(invalid="ignore"):
        # np.minimum, NOT np.fmin: fmin IGNORES NaN and returns the other operand,
        # so fmin(nan, cap) == cap -- every no-data cell (ocean, uncovered land)
        # would silently be counted as "at the cap" instead of contributing zero.
        # minimum propagates NaN as intended, which nansum then correctly excludes.
        return np.nansum(np.minimum(density, max_density_cap) * area_row_km2[:, None], axis=1)


def density_capped_population_by_latitude(grid: pdg.PopulationGrid,
                                           scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                           bin_width_deg: float = BIN_WIDTH_DEG):
    """Sum, per 1deg latitude band, of min(actual population, beam-footprint density
    cap x cell area) over every grid cell in that band. Independent of satellite
    count N -- this is the fixed DEMAND ceiling; capacity_by_latitude is the SUPPLY
    curve that grows with N. Whole-array version -- for a raster too large to hold in
    memory (the 100m population-count product), see the streaming variant below."""
    max_density_cap = cdm.max_customer_density_per_km2(scenario)
    lat_centers = (grid.lat_edges[:-1] + grid.lat_edges[1:]) / 2  # descending, north -> south
    area_row_km2 = pdg.row_areas_km2(grid)
    pop_row = _capped_population_per_row(grid.density, area_row_km2, max_density_cap, already_density=True)

    centers = _lat_bin_edges(bin_width_deg)
    out = np.zeros(len(centers))
    np.add.at(out, _lat_bin_index(lat_centers, bin_width_deg, len(centers)), pop_row)
    return centers, out


def density_capped_population_by_latitude_streaming(path,
                                                      scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                                      bin_width_deg: float = BIN_WIDTH_DEG,
                                                      row_chunk: int = 512, verbose: bool = False):
    """Streaming equivalent of density_capped_population_by_latitude(), for a
    population-COUNT raster too large to load whole (e.g. the 100m 'ppp' product --
    ~101GB uncompressed as float32 for the full USA). Reads row_chunk rows at a time
    via population_density_grid.open_raster_zarr() (tile-decode-on-demand).

    Deliberately does NOT call the shared _capped_population_per_row() helper: that
    version allocates a fresh full-size array at each of divide/fmin/multiply
    (~4x the chunk's memory footprint), which is fine for the small whole-grid path
    but OOM-killed this one at row_chunk=2048 x 430,711 cols (a real crash, not a
    theoretical concern -- caught by the background run actually dying). Every step
    here mutates `chunk` in place instead, since it's a fresh temporary each
    iteration (safe to mutate) -- peak memory is ~1x chunk size, not ~4x.
    row_chunk=512 (one tile-row) keeps each chunk under ~1GB."""
    meta = pdg._read_raster_meta(path)
    h, _w = meta["shape"]
    z = pdg.open_raster_zarr(path)
    max_density_cap = cdm.max_customer_density_per_km2(scenario)
    centers = _lat_bin_edges(bin_width_deg)
    out = np.zeros(len(centers))

    for r0 in range(0, h, row_chunk):
        r1 = min(r0 + row_chunk, h)
        chunk = np.asarray(z[r0:r1, :], dtype=np.float32)  # owned temporary -- safe to mutate in place
        chunk[chunk == meta["nodata"]] = np.nan
        lat_centers = meta["lat0"] - (np.arange(r0, r1) + 0.5) * meta["dy"]
        area_col = ((meta["dy"] * pdg.KM_PER_DEG) * (meta["dx"] * pdg.KM_PER_DEG
                    * np.cos(np.radians(lat_centers))))[:, None]

        np.divide(chunk, area_col, out=chunk)           # count/pixel -> people/km^2
        np.minimum(chunk, max_density_cap, out=chunk)   # apply the cap -- NOT np.fmin, see
                                                          # _capped_population_per_row's comment: fmin
                                                          # would silently turn every NaN (no-data/ocean)
                                                          # cell into a phantom "at the cap" contribution.
        chunk *= area_col                                # back to capped population per cell
        with np.errstate(invalid="ignore"):
            pop_row = np.nansum(chunk, axis=1)
        np.add.at(out, _lat_bin_index(lat_centers, bin_width_deg, len(centers)), pop_row)
        if verbose and (r0 // row_chunk) % 20 == 0:
            print(f"  row {r0:,}/{h:,} ({100*r0/h:.0f}%)")
    return centers, out


# ========================================================================================
# Per-satellite density cap variant (user request, 2026-08-10): the fixed-cap model above
# treats the areal beam-footprint density cap as constant regardless of satellite count N
# -- correct per capacity_density_model.py's original documented assumption ("independent
# of how many satellites are overhead"), but the user asked for a version where the cap
# scales PER SATELLITE instead: more satellites overhead a given latitude band raises the
# local areal ceiling proportionally (N x base_cap), not just the aggregate per-satellite
# capacity ceiling (which already scaled with N). As N grows large enough that the scaled
# cap exceeds even the densest populated cell, the demand ceiling approaches RAW (uncapped)
# population -- a materially different curve shape from the fixed-cap model, which sits at
# a permanent ceiling however large N gets.
#
# Because the cap now changes with EVERY N in a sweep (not just once), re-reading the raw
# raster per N is not an option (the 100m file alone takes ~10 minutes per PASS). Instead,
# a (latitude band x density bin) AREA histogram is precomputed ONCE (one pass over the
# data, in-memory or streaming), and the capped sum for any cap value is then a cheap
# array op against that histogram -- no more raw-data reads needed for the rest of a sweep.
# ========================================================================================

DENSITY_BIN_EDGES = np.logspace(-2, 5.3, 60)  # ~0.01 to ~200,000 people/km^2, log-spaced


def _density_bin_centers(density_bin_edges=DENSITY_BIN_EDGES) -> np.ndarray:
    return np.sqrt(density_bin_edges[:-1] * density_bin_edges[1:])  # geometric center, correct for log bins


def density_area_histogram_by_latitude(grid: pdg.PopulationGrid, bin_width_deg: float = BIN_WIDTH_DEG,
                                        density_bin_edges: np.ndarray = DENSITY_BIN_EDGES):
    """2D histogram of AREA (km^2), binned by (latitude band, density bin), from an
    in-memory grid. See the section docstring above for why this replaces a single
    scalar "capped population" -- it lets the cap be re-applied at query time for
    any value, not just the one it was computed with."""
    lat_centers = (grid.lat_edges[:-1] + grid.lat_edges[1:]) / 2
    area_row = pdg.row_areas_km2(grid)
    lat_centers_out = _lat_bin_edges(bin_width_deg)
    n_lat, n_dens = len(lat_centers_out), len(density_bin_edges) - 1

    lat_bin_idx = _lat_bin_index(lat_centers, bin_width_deg, n_lat).astype(np.int32)
    valid = ~np.isnan(grid.density)
    dens_bin_idx = np.clip(np.searchsorted(density_bin_edges, grid.density, side="right") - 1,
                            0, n_dens - 1).astype(np.int32)
    area_2d = np.broadcast_to(area_row[:, None], grid.density.shape)
    lat_idx_2d = np.broadcast_to(lat_bin_idx[:, None], grid.density.shape)

    hist = np.zeros((n_lat, n_dens))
    np.add.at(hist, (lat_idx_2d[valid], dens_bin_idx[valid]), area_2d[valid])
    return lat_centers_out, _density_bin_centers(density_bin_edges), hist


def density_area_histogram_by_latitude_streaming(path, bin_width_deg: float = BIN_WIDTH_DEG,
                                                   density_bin_edges: np.ndarray = DENSITY_BIN_EDGES,
                                                   row_chunk: int = 512, verbose: bool = False):
    """Streaming equivalent of density_area_histogram_by_latitude(), for a
    population-COUNT raster too large to load whole (the 100m 'ppp' product). Same
    row-chunked, in-place-mutation approach as density_capped_population_by_latitude_streaming()
    (see its docstring for why) -- one extra step here (digitizing into density
    bins) but still bounded by row_chunk's memory footprint, not the whole file's."""
    meta = pdg._read_raster_meta(path)
    h, _w = meta["shape"]
    z = pdg.open_raster_zarr(path)
    lat_centers_out = _lat_bin_edges(bin_width_deg)
    n_lat, n_dens = len(lat_centers_out), len(density_bin_edges) - 1
    hist = np.zeros((n_lat, n_dens))

    for r0 in range(0, h, row_chunk):
        r1 = min(r0 + row_chunk, h)
        chunk = np.asarray(z[r0:r1, :], dtype=np.float32)
        chunk[chunk == meta["nodata"]] = np.nan
        lat_centers = meta["lat0"] - (np.arange(r0, r1) + 0.5) * meta["dy"]
        area_col = ((meta["dy"] * pdg.KM_PER_DEG) * (meta["dx"] * pdg.KM_PER_DEG
                    * np.cos(np.radians(lat_centers))))[:, None]
        np.divide(chunk, area_col, out=chunk)  # count/pixel -> people/km^2, in place

        lat_bin_idx = _lat_bin_index(lat_centers, bin_width_deg, n_lat).astype(np.int32)
        valid = ~np.isnan(chunk)
        dens_bin_idx = np.clip(np.searchsorted(density_bin_edges, chunk, side="right") - 1,
                                0, n_dens - 1).astype(np.int32)
        area_2d = np.broadcast_to(area_col, chunk.shape)
        lat_idx_2d = np.broadcast_to(lat_bin_idx[:, None], chunk.shape)
        np.add.at(hist, (lat_idx_2d[valid], dens_bin_idx[valid]), area_2d[valid])
        del chunk, dens_bin_idx, valid, area_2d, lat_idx_2d
        if verbose and (r0 // row_chunk) % 20 == 0:
            print(f"  row {r0:,}/{h:,} ({100*r0/h:.0f}%)")
    return lat_centers_out, _density_bin_centers(density_bin_edges), hist


def capped_population_from_histogram(area_hist: np.ndarray, density_bin_centers: np.ndarray,
                                      effective_cap_per_lat: np.ndarray) -> np.ndarray:
    """min(actual population, cap) summed per latitude band, from a precomputed
    (lat x density) area histogram -- the cheap, repeatable half of the per-satellite
    -cap model; see the section docstring above."""
    return np.sum(area_hist * np.minimum(density_bin_centers[None, :], effective_cap_per_lat[:, None]), axis=1)


def served_fraction_by_latitude(total_sats: float, area_hist: np.ndarray, density_bin_centers: np.ndarray,
                                 lat_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                 base_shells: list[og.Shell] | None = None,
                                 bin_width_deg: float = BIN_WIDTH_DEG) -> np.ndarray:
    """Served population as a FRACTION of each latitude band's own raw (uncapped)
    population, at one N -- the per-band "how saturated is this band" diagnostic
    behind serviceable_customers_per_satellite_cap()'s aggregate total. NaN (not 0)
    where a band has zero population, so it reads as "no data" rather than
    "unserved" in a heatmap. Also returns which constraint bound each band
    ("supply", "demand", or "" where raw pop is zero) -- useful for diagnosing
    WHERE the aggregate-capacity bottleneck bites vs. the density-cap one; see the
    "supply-bound South Asia" finding in CLAUDE.md, found by exactly this split."""
    base_cap = cdm.max_customer_density_per_km2(scenario)
    customers_per_sat = cdm.max_customers_per_satellite(scenario)
    raw_by_band = np.sum(area_hist * density_bin_centers[None, :], axis=1)
    covered = np.abs(lat_centers) <= max_latitude_covered(base_shells)

    _, sats_overhead = sats_overhead_by_latitude(total_sats, base_shells, bin_width_deg)
    effective_cap = np.where(covered, base_cap * sats_overhead, 0.0)
    demand = capped_population_from_histogram(area_hist, density_bin_centers, effective_cap)
    supply = np.where(covered, sats_overhead * customers_per_sat, 0.0)
    served = np.minimum(supply, demand)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(raw_by_band > 0, served / raw_by_band, np.nan)


def sweep_served_fraction_by_latitude(sat_counts, area_hist: np.ndarray, density_bin_centers: np.ndarray,
                                       lat_centers: np.ndarray,
                                       scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                       base_shells: list[og.Shell] | None = None,
                                       bin_width_deg: float = BIN_WIDTH_DEG) -> np.ndarray:
    """served_fraction_by_latitude() at each N in sat_counts. Returns shape
    (len(sat_counts), len(lat_centers)) -- the (N x latitude) grid a saturation
    heatmap plots directly."""
    return np.array([
        served_fraction_by_latitude(n, area_hist, density_bin_centers, lat_centers, scenario, base_shells,
                                     bin_width_deg)
        for n in sat_counts
    ])


def serviceable_customers_per_satellite_cap(total_sats: float, area_hist: np.ndarray,
                                             density_bin_centers: np.ndarray, lat_centers: np.ndarray,
                                             scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                             base_shells: list[og.Shell] | None = None,
                                             bin_width_deg: float = BIN_WIDTH_DEG) -> float:
    """Like serviceable_customers(), but the areal density cap scales with
    satellites overhead per latitude band instead of staying fixed -- see the
    section docstring above for the mechanism and why."""
    _, sats_overhead = sats_overhead_by_latitude(total_sats, base_shells, bin_width_deg)
    base_cap = cdm.max_customer_density_per_km2(scenario)
    covered = np.abs(lat_centers) <= max_latitude_covered(base_shells)

    effective_cap = np.where(covered, base_cap * sats_overhead, 0.0)
    demand = capped_population_from_histogram(area_hist, density_bin_centers, effective_cap)
    customers_per_sat = cdm.max_customers_per_satellite(scenario)
    supply = np.where(covered, sats_overhead * customers_per_sat, 0.0)
    return float(np.minimum(supply, demand).sum())


def sweep_per_satellite_cap(sat_counts, area_hist: np.ndarray, density_bin_centers: np.ndarray,
                             lat_centers: np.ndarray, scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                             base_shells: list[og.Shell] | None = None,
                             bin_width_deg: float = BIN_WIDTH_DEG) -> np.ndarray:
    """Servable-customer count at each N in sat_counts, per-satellite-cap variant.
    Cheap per N -- only capped_population_from_histogram() and a few small array ops
    run per iteration, the expensive raw-data pass already happened once, upstream."""
    return np.array([
        serviceable_customers_per_satellite_cap(n, area_hist, density_bin_centers, lat_centers,
                                                 scenario, base_shells, bin_width_deg)
        for n in sat_counts
    ])


def serviceable_customers(total_sats: float, pop_cap_by_lat: tuple[np.ndarray, np.ndarray],
                           scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                           base_shells: list[og.Shell] | None = None,
                           bin_width_deg: float = BIN_WIDTH_DEG) -> float:
    """Total servable customers for a constellation of total_sats satellites.
    min() is taken PER LATITUDE BAND, then summed -- see module docstring."""
    _, pop_cap = pop_cap_by_lat
    _, sat_cap = capacity_by_latitude(total_sats, scenario, base_shells, bin_width_deg)
    return float(np.minimum(sat_cap, pop_cap).sum())


def sweep_from_pop_cap(sat_counts, pop_cap_by_lat: tuple[np.ndarray, np.ndarray],
                        scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                        base_shells: list[og.Shell] | None = None,
                        bin_width_deg: float = BIN_WIDTH_DEG) -> np.ndarray:
    """Servable-customer count at each N in sat_counts, given an already-computed
    (N-independent) demand ceiling -- shared by every sweep_* variant below so the
    ceiling is computed exactly ONCE regardless of how it was produced (whole-grid or
    streaming)."""
    return np.array([
        serviceable_customers(n, pop_cap_by_lat, scenario, base_shells, bin_width_deg)
        for n in sat_counts
    ])


def sweep_serviceable_customers(sat_counts, grid: pdg.PopulationGrid,
                                 scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                 base_shells: list[og.Shell] | None = None,
                                 bin_width_deg: float = BIN_WIDTH_DEG) -> np.ndarray:
    """Servable-customer count at each N in sat_counts, from an in-memory grid."""
    pop_cap_by_lat = density_capped_population_by_latitude(grid, scenario, bin_width_deg)
    return sweep_from_pop_cap(sat_counts, pop_cap_by_lat, scenario, base_shells, bin_width_deg)


if __name__ == "__main__":
    grid = pdg.load_or_build_grid()
    counts = np.geomspace(100, 2_000_000, 25)
    served = sweep_serviceable_customers(counts, grid)
    print(f"{'satellites':>12}  {'servable customers':>20}")
    for n, s in zip(counts, served):
        print(f"{n:12,.0f}  {s:20,.0f}")
