"""Serviceable-customers model: combines three previously-separate pieces of this
project into one curve of servable customers vs. total constellation size N.

  1. orbital_geometry.py       -- expected satellites overhead by latitude, for a
                                   constellation split across shells at given
                                   inclinations (Phase 2).
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

Shell split: the user specified a rough, hand-picked ratio approximating current
Starlink shell inclinations (NOT starlink_shells.csv's precise Gen1 geometry --
deliberately simplified here to 3 representative inclinations: mostly ~45deg with
smaller ~65deg and ~80deg components, ratio 5:1:1), not tied to any specific
generation's real plane/sats-per-plane counts. Satellites are assumed split across
these three inclinations in that fixed proportion at every N (including fractional
N per shell) -- the same "expected value" treatment orbital_geometry.py already uses
elsewhere in this project, not a claim that Starlink literally launches fractional
satellites.

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

# Rough approximation of current Starlink shell inclinations, per user: mostly ~45deg,
# with smaller ~65deg and ~80deg components. NOT starlink_shells.csv's precise Gen1
# figures (53.0/53.2/70.0/97.6deg) -- a deliberately simplified 3-shell stand-in.
SHELL_RATIOS = [(45.0, 5.0), (65.0, 1.0), (80.0, 1.0)]
BIN_WIDTH_DEG = 1.0


def make_shells(total_sats: float, ratios=SHELL_RATIOS, altitude_km: float = 550.0) -> list[og.Shell]:
    """Split total_sats across the given (inclination_deg, weight) ratios.

    orbital_planes is fixed at 1 and sats_per_plane carries the (possibly fractional)
    count -- only their product (total_sats) and the shared altitude feed the physics
    used here (period, latitude density), so the split between the two fields doesn't
    matter.
    """
    total_weight = sum(w for _, w in ratios)
    return [
        og.Shell(
            shell_id=f"rough_{incl:.0f}deg",
            generation="rough_model",
            altitude_km=altitude_km,
            inclination_deg=incl,
            orbital_planes=1,
            sats_per_plane=total_sats * w / total_weight,
            status="model",
        )
        for incl, w in ratios
    ]


def max_latitude_covered(ratios=SHELL_RATIOS) -> float:
    return max(og.max_latitude_deg(incl) for incl, _ in ratios)


def capacity_by_latitude(total_sats: float, scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                          ratios=SHELL_RATIOS, bin_width_deg: float = BIN_WIDTH_DEG):
    """Aggregate simultaneous-customer capacity per latitude band, for total_sats
    split across `ratios`. Zero outside the union of shells' coverage bands."""
    shells = make_shells(total_sats, ratios, altitude_km=scenario.altitude_km)
    centers, by_shell = og.expected_sats_by_latitude(shells, bin_width_deg=bin_width_deg)
    sats_overhead = np.sum(list(by_shell.values()), axis=0)
    customers_per_sat = cdm.max_customers_per_satellite(scenario)
    cap = sats_overhead * customers_per_sat
    covered = np.abs(centers) <= max_latitude_covered(ratios)
    return centers, np.where(covered, cap, 0.0)


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


def serviceable_customers(total_sats: float, pop_cap_by_lat: tuple[np.ndarray, np.ndarray],
                           scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                           ratios=SHELL_RATIOS, bin_width_deg: float = BIN_WIDTH_DEG) -> float:
    """Total servable customers for a constellation of total_sats satellites.
    min() is taken PER LATITUDE BAND, then summed -- see module docstring."""
    _, pop_cap = pop_cap_by_lat
    _, sat_cap = capacity_by_latitude(total_sats, scenario, ratios, bin_width_deg)
    return float(np.minimum(sat_cap, pop_cap).sum())


def sweep_from_pop_cap(sat_counts, pop_cap_by_lat: tuple[np.ndarray, np.ndarray],
                        scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                        ratios=SHELL_RATIOS, bin_width_deg: float = BIN_WIDTH_DEG) -> np.ndarray:
    """Servable-customer count at each N in sat_counts, given an already-computed
    (N-independent) demand ceiling -- shared by every sweep_* variant below so the
    ceiling is computed exactly ONCE regardless of how it was produced (whole-grid or
    streaming)."""
    return np.array([
        serviceable_customers(n, pop_cap_by_lat, scenario, ratios, bin_width_deg)
        for n in sat_counts
    ])


def sweep_serviceable_customers(sat_counts, grid: pdg.PopulationGrid,
                                 scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                 ratios=SHELL_RATIOS, bin_width_deg: float = BIN_WIDTH_DEG) -> np.ndarray:
    """Servable-customer count at each N in sat_counts, from an in-memory grid."""
    pop_cap_by_lat = density_capped_population_by_latitude(grid, scenario, bin_width_deg)
    return sweep_from_pop_cap(sat_counts, pop_cap_by_lat, scenario, ratios, bin_width_deg)


if __name__ == "__main__":
    grid = pdg.load_or_build_grid()
    counts = np.geomspace(100, 2_000_000, 25)
    served = sweep_serviceable_customers(counts, grid)
    print(f"{'satellites':>12}  {'servable customers':>20}")
    for n, s in zip(counts, served):
        print(f"{n:12,.0f}  {s:20,.0f}")
