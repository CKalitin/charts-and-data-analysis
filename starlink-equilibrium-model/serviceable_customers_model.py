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


def density_capped_population_by_latitude(grid: pdg.PopulationGrid,
                                           scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                           bin_width_deg: float = BIN_WIDTH_DEG):
    """Sum, per 1deg latitude band, of min(actual population, beam-footprint density
    cap x cell area) over every grid cell in that band -- the per-cell version of
    Phase 5's min(unconnected_pop, density_ceiling x land_area), applied at the
    grid's native resolution instead of a whole-country average area. Independent of
    satellite count N -- this is the fixed DEMAND ceiling; capacity_by_latitude is
    the SUPPLY curve that grows with N."""
    max_density_cap = cdm.max_customer_density_per_km2(scenario)

    lat_centers_fine = (grid.lat_edges[:-1] + grid.lat_edges[1:]) / 2  # descending, north -> south
    area_row_km2 = pdg.row_areas_km2(grid)

    servable_density = np.fmin(grid.density, max_density_cap)  # NaN (no data) stays NaN
    servable_pop_row = np.nansum(servable_density * area_row_km2[:, None], axis=1)

    edges = np.arange(-90, 90 + bin_width_deg, bin_width_deg)
    centers = (edges[:-1] + edges[1:]) / 2
    # ascending bin index to match centers[]'s ascending order -- see the same fix
    # (and why) in population_density_grid.population_by_latitude().
    bin_idx = np.clip(((lat_centers_fine + 90.0) / bin_width_deg).astype(np.int64), 0, len(centers) - 1)
    out = np.zeros(len(centers))
    np.add.at(out, bin_idx, servable_pop_row)
    return centers, out


def serviceable_customers(total_sats: float, pop_cap_by_lat: tuple[np.ndarray, np.ndarray],
                           scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                           ratios=SHELL_RATIOS, bin_width_deg: float = BIN_WIDTH_DEG) -> float:
    """Total servable customers for a constellation of total_sats satellites.
    min() is taken PER LATITUDE BAND, then summed -- see module docstring."""
    _, pop_cap = pop_cap_by_lat
    _, sat_cap = capacity_by_latitude(total_sats, scenario, ratios, bin_width_deg)
    return float(np.minimum(sat_cap, pop_cap).sum())


def sweep_serviceable_customers(sat_counts, grid: pdg.PopulationGrid,
                                 scenario: cdm.CapacityScenario = cdm.V2_MINI_BEAD_SCENARIO,
                                 ratios=SHELL_RATIOS, bin_width_deg: float = BIN_WIDTH_DEG) -> np.ndarray:
    """Servable-customer count at each N in sat_counts. Computes the (N-independent)
    density-capped population ceiling ONCE and reuses it across the whole sweep."""
    pop_cap_by_lat = density_capped_population_by_latitude(grid, scenario, bin_width_deg)
    return np.array([
        serviceable_customers(n, pop_cap_by_lat, scenario, ratios, bin_width_deg)
        for n in sat_counts
    ])


if __name__ == "__main__":
    grid = pdg.load_or_build_grid()
    counts = np.geomspace(100, 2_000_000, 25)
    served = sweep_serviceable_customers(counts, grid)
    print(f"{'satellites':>12}  {'servable customers':>20}")
    for n, s in zip(counts, served):
        print(f"{n:12,.0f}  {s:20,.0f}")
