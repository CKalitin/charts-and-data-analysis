"""2D (latitude x longitude) tiled satellite-capacity allocation model.

WHY THIS EXISTS -- the bug it replaces
======================================
Every earlier capacity model in this project (serviceable_customers_model.py and
everything downstream of it) marginalized longitude away completely: it computed
one satellite-supply number per 1deg LATITUDE BAND and compared it against that
whole band's population. Two separate errors follow from that, both of which this
module fixes:

1. CAPACITY TELEPORTATION. A latitude band is a full 40,000 km ring around the
   Earth. Pooling its satellite capacity lets idle capacity over the mid-Pacific
   serve demand in South Asia at the same latitude -- physically impossible: a
   satellite's usable ground footprint is a disk of ~940 km radius (Gen1, 550 km,
   25deg minimum elevation), not a ring. The old model already enforced "capacity
   can't teleport" ACROSS latitudes (its own stated design rule) while silently
   violating the identical constraint ALONG a latitude.

2. A ~19x OVERCOUNT of satellites in view. orbital_geometry.expected_sats_reaching_
   latitude() convolves the per-latitude satellite histogram with a boxcar of
   half-width R -- i.e. it counts EVERY satellite whose latitude is within R,
   at ANY longitude (the whole ring), as "reaching" a ground point. The correct
   count is the satellites inside the DISK of radius R. Measured against the
   correct disk integral at N=10,900: 19.1x too high globally, 27.8x at the
   equator (the ring is widest relative to the disk there), 4.3x at 80deg (where
   the ring shrinks toward the pole and the two converge). That function feeds the
   areal density cap in the old model, so the old density ceiling is ~19x too
   generous.

THE MODEL
=========
Ground and satellite positions share one TILE_DEG x TILE_DEG lat/lon tile grid.

Supply. Satellites' sub-satellite points are distributed with a latitude profile
from orbital_geometry.latitude_density() (the same time-averaged "pendulum
lingering at the turning points" density Phase 2 established) and are UNIFORM IN
LONGITUDE -- justified by real Starlink shells spreading their orbital planes
approximately evenly in RAAN, plus Earth's rotation smearing each ground track
across all longitudes over many orbits. This is an EXPECTED value: the
instantaneous realization fluctuates, and taking min(supply, demand) on expected
values is optimistic by Jensen's inequality (flagged, not corrected -- the same
expectation-based treatment the rest of this project uses).

Reach. A satellite serves ground points inside a spherical cap of Earth-central
angular radius R = 90 - eps - asin(Re*cos(eps)/(Re+h)), where eps = 25deg is the
FCC-authorized minimum user-terminal elevation angle (ASSUMPTIONS.md #11) and h is
the SHELL's own altitude. R is 8.33-8.70deg (927-968 km) for Gen1's real 540-570 km
shells, and 5.71deg (635 km) for V3's planned 345 km. The relation is reciprocal:
a satellite can serve a ground point exactly when that ground point can see the
satellite above 25deg, so the same disk works read either direction.

Allocation. Each satellite has ONE finite customer budget shared across everything
inside its disk, so neighbouring tiles (and neighbouring countries) genuinely
compete for it. That makes this a bipartite transportation problem between
satellite-position tiles (supply, capacity C x satellites-per-tile) and ground
tiles (demand), with disk adjacency. It is solved by proportional water-filling
(allocate() below) rather than a pooled per-band min().

Two constraints still apply, as they did before, but now both are 2D:
  - aggregate per-satellite customer capacity C (allocated, as above);
  - the areal beam-footprint density ceiling, base_cap x satellites-reaching-the-
    tile, where "reaching" is now the correct DISK integral rather than the ring.

Units: CONNECTIONS (subscriptions), not people. Satellite capacity is natively
denominated in subscribers -- one dish, one household -- so demand is converted from
WorldPop people into connections per tile before anything is allocated, using that
tile's country household size (household_grid.py). Comparing people against
subscriber capacity directly, as every earlier model in this project did, asserts one
person per dish and understates how many people a satellite reaches by roughly the
household size (population-weighted global mean ~4.2). Results are reported in both
units: AllocationResult.served is connections, .served_people multiplies back out.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import capacity_density_model as cdm
import household_grid as hhg
import orbital_geometry as og
import population_density_grid as pdg

TILE_DEG = 1.0
#: Tolerance for the served-vs-consumed flow-conservation audit in allocate().
#: Sized to pass ordinary float accumulation and DiskOperator's noise clipping
#: (both ~1e-4 relative or below at every tile size tested) while still catching
#: the structural failure it was written for, which was ~50% off.
ALLOCATION_CONSERVATION_TOL = 2e-3
DENSITY_BIN_EDGES = np.logspace(-2, 5.3, 60)  # people/km^2, log-spaced; matches serviceable_customers_model


# ---------------------------------------------------------------------------
# Tile grid
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TileGrid:
    """A global lat/lon tile grid. Latitude ASCENDING (row 0 = south pole), matching
    this project's _lat_bin_edges() convention, NOT PopulationGrid's descending rows."""
    tile_deg: float
    lat_centers: np.ndarray  # (n_lat,) ascending
    lon_centers: np.ndarray  # (n_lon,)
    area_km2: np.ndarray     # (n_lat,) per-tile area; lon width shrinks with cos(lat)

    @property
    def shape(self) -> tuple[int, int]:
        return len(self.lat_centers), len(self.lon_centers)

    def area_2d(self) -> np.ndarray:
        return np.broadcast_to(self.area_km2[:, None], self.shape)


def make_tile_grid(tile_deg: float = TILE_DEG) -> TileGrid:
    n_lat, n_lon = round(180.0 / tile_deg), round(360.0 / tile_deg)
    lat_c = -90.0 + (np.arange(n_lat) + 0.5) * tile_deg
    lon_c = -180.0 + (np.arange(n_lon) + 0.5) * tile_deg
    area = (tile_deg * pdg.KM_PER_DEG) * (tile_deg * pdg.KM_PER_DEG * np.cos(np.radians(lat_c)))
    return TileGrid(tile_deg, lat_c, lon_c, area)


# ---------------------------------------------------------------------------
# The disk operator -- the core piece the old latitude-only model was missing
# ---------------------------------------------------------------------------

class DiskOperator:
    """Sums a field over the spherical cap of angular radius `radius_deg` around
    each tile: out[i] = sum over tiles within R of i of X[that tile].

    Implemented in the longitude-frequency domain. Angular distance between two
    tiles depends only on (lat_i, lat_j, delta_lon), so the adjacency matrix is
    block-circulant in longitude and the whole operator collapses to one small
    complex matrix multiply per longitude frequency -- ~15 ms for the full
    180x360 grid, versus minutes for an explicit ~20M-edge sparse matrix.

    Longitude weights are FRACTIONAL (each tile is weighted by the fraction of its
    longitude span inside the disk) rather than a rounded 0/1 boxcar; latitude is
    a hard cut at row centres. Validated against the exact spherical cap area: at
    1deg tiles this recovers pi*(Re*R)^2 to within 0.4% at every latitude.

    Self-adjoint (adjacency is symmetric), so the SAME operator both gathers
    supply toward a ground tile and gathers demand toward a satellite tile.
    """

    def __init__(self, tile: TileGrid, radius_deg: float, fractional: bool = True):
        self.radius_deg = float(radius_deg)
        self.tile = tile
        self.fractional = fractional
        n_lat, n_lon = tile.shape
        lat = np.radians(tile.lat_centers)
        s, c = np.sin(lat), np.cos(lat)

        # cos(dlon_max) = (cos R - sin(lat_i) sin(lat_j)) / (cos(lat_i) cos(lat_j))
        num = np.cos(np.radians(radius_deg)) - s[:, None] * s[None, :]
        den = c[:, None] * c[None, :]
        with np.errstate(divide="ignore", invalid="ignore"):
            cos_dlon = np.where(den > 1e-12, num / den, np.where(num <= 0, -1.0, 1.0))

        dlon_max = np.full(cos_dlon.shape, -1.0)      # -1 marks "no longitude works"
        dlon_max[cos_dlon <= -1.0] = 180.0            # disk spans the full latitude circle
        partial = (cos_dlon > -1.0) & (cos_dlon < 1.0)
        dlon_max[partial] = np.degrees(np.arccos(cos_dlon[partial]))

        half_width_tiles = dlon_max / tile.tile_deg
        offset = np.minimum(np.arange(n_lon), n_lon - np.arange(n_lon))  # circular |delta|
        if fractional:
            weights = np.clip(half_width_tiles[:, :, None] - offset[None, None, :] + 0.5, 0.0, 1.0)
        else:
            # Hard "is the tile centre inside the disk" test -- coarser, but a genuine
            # 0/1 graph, which is what an exact max-flow reference needs to run on.
            weights = (offset[None, None, :] <= half_width_tiles[:, :, None]).astype(float)
        weights[half_width_tiles < 0] = 0.0
        # Real because the weight vector is symmetric in delta_lon.
        self._kernel_hat = np.fft.rfft(weights, axis=2).real.astype(np.float64)

    #: Outputs below this fraction of the result's own peak are treated as zero.
    #: The round trip through rfft/irfft leaves ~1e-14-relative round-off where the
    #: true sum is exactly zero (a tile no satellite can reach). That noise is not
    #: cosmetic: the allocator divides unmet demand by reachable capacity, so a
    #: 1e-16 "reachable capacity" becomes a ~1e16 request ratio and hands free
    #: service to ground tiles with no coverage at all -- it inflated total served
    #: customers ~50% above total capacity consumed before it was caught by a
    #: flow-conservation audit. 1e-10 sits far above the round-off floor and far
    #: below any physically meaningful contribution (a satellite spending 1e-10 of
    #: its orbit over a tile).
    NOISE_FLOOR_REL = 1e-10

    def apply(self, field: np.ndarray) -> np.ndarray:
        n_lon = field.shape[1]
        spectrum = np.einsum("ijf,jf->if", self._kernel_hat, np.fft.rfft(field, axis=1))
        out = np.fft.irfft(spectrum, n=n_lon, axis=1)
        np.maximum(out, 0.0, out=out)          # inputs are non-negative; so is the true sum
        peak = out.max()
        if peak > 0:
            out[out < self.NOISE_FLOOR_REL * peak] = 0.0
        return out


# ---------------------------------------------------------------------------
# Supply: satellite sub-satellite-point density per tile, grouped by coverage radius
# ---------------------------------------------------------------------------

@dataclass
class SupplyGroup:
    """Satellites sharing one coverage radius (i.e. one shell altitude). Kept
    separate rather than merged because a satellite's reach is set by its own
    altitude, and Gen1's shells span 540-570 km (R = 8.33-8.70deg)."""
    label: str
    altitude_km: float
    radius_deg: float
    sats_per_tile: np.ndarray  # (n_lat, n_lon)
    operator: DiskOperator

    @property
    def total_sats(self) -> float:
        return float(self.sats_per_tile.sum())


def real_shells() -> list[og.Shell]:
    return og.load_shells_with_full_geometry()


def scale_shells_to_total(total_sats: float, base_shells: list[og.Shell] | None = None) -> list[og.Shell]:
    """Scale a shell set's satellite counts proportionally to hit total_sats,
    preserving each shell's own altitude/inclination and share of the fleet --
    the same expected-value treatment serviceable_customers_model.py uses."""
    base_shells = base_shells if base_shells is not None else real_shells()
    base_total = sum(s.total_sats for s in base_shells)
    return [
        og.Shell(shell_id=s.shell_id, generation=s.generation, altitude_km=s.altitude_km,
                 inclination_deg=s.inclination_deg, orbital_planes=1,
                 sats_per_plane=total_sats * (s.total_sats / base_total), status="scaled")
        for s in base_shells
    ]


def build_supply(total_sats: float, tile: TileGrid, base_shells: list[og.Shell] | None = None,
                 min_elevation_deg: float = og.MIN_ELEVATION_DEG,
                 altitude_override_km: float | None = None,
                 operator_cache: dict | None = None,
                 fractional: bool = True) -> list[SupplyGroup]:
    """Satellite sub-satellite-point counts per tile, one SupplyGroup per distinct
    shell altitude. Longitude-uniform (see module docstring); latitude profile from
    the real per-shell orbital geometry.

    altitude_override_km replaces every shell's altitude for the COVERAGE RADIUS and
    grouping only (the latitude profile still comes from each shell's real
    inclination). Use it to ask "what if this fleet flew at V3's planned 345 km
    instead of Gen1's 540-570 km" -- which shrinks R from ~8.4deg to 5.7deg and
    more than halves each satellite's footprint area.
    """
    shells = scale_shells_to_total(total_sats, base_shells)
    n_lat, n_lon = tile.shape
    operator_cache = operator_cache if operator_cache is not None else {}

    by_altitude: dict[float, np.ndarray] = {}
    for shell in shells:
        alt = altitude_override_km if altitude_override_km is not None else shell.altitude_km
        _, frac = og.latitude_density(shell, bin_width_deg=tile.tile_deg)
        per_tile = frac * shell.total_sats / n_lon  # uniform across longitude
        by_altitude[alt] = by_altitude.get(alt, np.zeros(n_lat)) + per_tile

    groups = []
    for alt, per_lat in sorted(by_altitude.items()):
        radius = og.ground_range_angular_radius_deg(alt, min_elevation_deg)
        key = (round(radius, 6), tile.tile_deg, n_lon, fractional)
        if key not in operator_cache:
            operator_cache[key] = DiskOperator(tile, radius, fractional=fractional)
        groups.append(SupplyGroup(
            label=f"{alt:.0f}km", altitude_km=alt, radius_deg=radius,
            sats_per_tile=np.broadcast_to(per_lat[:, None], (n_lat, n_lon)).copy(),
            operator=operator_cache[key],
        ))
    return groups


def sats_reaching_tile(groups: list[SupplyGroup]) -> np.ndarray:
    """Expected satellites simultaneously in view (above min elevation) from each
    tile -- the CORRECT disk integral. This is the quantity
    orbital_geometry.expected_sats_reaching_latitude() gets ~19x too high by
    summing the whole latitude ring instead of the disk."""
    return sum(g.operator.apply(g.sats_per_tile) for g in groups)


# ---------------------------------------------------------------------------
# Demand: population per tile, capped by the areal beam-footprint density ceiling
# ---------------------------------------------------------------------------

@dataclass
class DemandTiles:
    """Per-tile population, plus paired (tile x density-bin) AREA and POPULATION
    histograms so the areal density cap can be re-applied at any value without
    re-reading the raster -- the same precompute trick serviceable_customers_model.py
    uses, extended from (latitude x density) to (latitude x longitude x density).

    Storing population per bin alongside area (rather than reconstructing it from a
    bin centre, as the earlier latitude-only model did) matters: with 59 log-spaced
    bins each ~1.33x wide, a geometric bin centre misestimates each bin's real
    population by a few percent, which showed up as the capped demand exceeding
    100% of world population once the cap stopped binding. min(pop_bin, cap x
    area_bin) is exact in that limit and uses each bin's true mean density."""
    tile: TileGrid
    population: np.ndarray        # (n_lat, n_lon) raw people
    area_hist: np.ndarray         # (n_lat, n_lon, n_density_bins) km^2
    pop_hist: np.ndarray          # (n_lat, n_lon, n_density_bins) people
    household_size: np.ndarray    # (n_lat, n_lon) people per connection
    household_report: dict        # coverage of the country-polygon attribution

    @property
    def connections(self) -> np.ndarray:
        """Raw demand in CONNECTIONS -- the unit satellite capacity is denominated
        in. See household_grid.py for why the two must not be compared directly."""
        return self.population / self.household_size


def build_demand(tile: TileGrid, grid: pdg.PopulationGrid | None = None,
                 density_bin_edges: np.ndarray = DENSITY_BIN_EDGES,
                 household_size: np.ndarray | None = None) -> DemandTiles:
    """Aggregate the fine (0.1deg) WorldPop density grid into tiles, keeping the
    SUB-TILE density distribution as an area histogram. Keeping it matters: the
    areal density cap binds inside dense cities, which a tile-mean density would
    average away."""
    grid = grid if grid is not None else pdg.load_or_build_grid()
    n_lat, n_lon = tile.shape
    n_bins = len(density_bin_edges) - 1

    src_lat = (grid.lat_edges[:-1] + grid.lat_edges[1:]) / 2   # descending
    src_lon = (grid.lon_edges[:-1] + grid.lon_edges[1:]) / 2
    src_area = pdg.row_areas_km2(grid)

    row_idx = np.clip(((src_lat + 90.0) / tile.tile_deg).astype(np.int64), 0, n_lat - 1)
    col_idx = np.clip(((src_lon + 180.0) / tile.tile_deg).astype(np.int64), 0, n_lon - 1)

    density = grid.density
    valid = ~np.isnan(density)
    dens_bin = np.clip(np.searchsorted(density_bin_edges, density, side="right") - 1, 0, n_bins - 1)

    rr = np.broadcast_to(row_idx[:, None], density.shape)[valid]
    cc = np.broadcast_to(col_idx[None, :], density.shape)[valid]
    aa = np.broadcast_to(src_area[:, None], density.shape)[valid]
    bb = dens_bin[valid]

    pp = aa * density[valid]

    flat = (rr * n_lon + cc) * n_bins + bb
    shape3 = (n_lat, n_lon, n_bins)
    area_hist = np.bincount(flat, weights=aa, minlength=n_lat * n_lon * n_bins).reshape(shape3)
    pop_hist = np.bincount(flat, weights=pp, minlength=n_lat * n_lon * n_bins).reshape(shape3)
    population = pop_hist.sum(axis=2)

    if household_size is None:
        household_size, report = hhg.household_size_by_tile(tile.lat_centers, tile.lon_centers, population)
    else:
        household_size = np.broadcast_to(household_size, population.shape).astype(float)
        report = {"tiles_matched": None, "population_matched_share": None,
                  "fallback_household_size": None}

    return DemandTiles(tile, population, area_hist, pop_hist, household_size, report)


def capped_demand(demand: DemandTiles, density_cap_connections: np.ndarray) -> np.ndarray:
    """min(demand, areal density ceiling) per tile, in CONNECTIONS, evaluated
    sub-tile against the stored density histogram.

    `density_cap_connections` is the beam-footprint ceiling in connections/km^2. The
    stored histogram is in people, so the cap is converted into people/km^2 by
    multiplying by that tile's household size, applied there, and the result divided
    back -- algebraically identical to capping in connection space, but it reuses the
    population histogram instead of needing a second one. Exactly recovers raw
    demand as the cap grows large."""
    cap_people = (density_cap_connections * demand.household_size)[:, :, None]
    capped_people = np.sum(np.minimum(demand.pop_hist, cap_people * demand.area_hist), axis=2)
    return capped_people / demand.household_size


# ---------------------------------------------------------------------------
# Allocation
# ---------------------------------------------------------------------------

@dataclass
class AllocationResult:
    """Everything on the supply side is in CONNECTIONS (subscriptions), because that
    is what satellite capacity is denominated in. `population` and `served_people`
    are the only people-valued fields."""
    served: np.ndarray             # (n_lat, n_lon) connections served, per GROUND tile
    demand: np.ndarray             # (n_lat, n_lon) density-capped connection demand offered
    population: np.ndarray         # (n_lat, n_lon) raw people
    household_size: np.ndarray     # (n_lat, n_lon) people per connection
    used_by_group: list            # per SupplyGroup, (n_lat, n_lon) connections carried
    capacity_by_group: list        # per SupplyGroup, (n_lat, n_lon) connections available
    total_sats: float
    iterations: int
    greedy_total: float   # what a single un-reweighted water-filling pass achieved

    @property
    def total_served(self) -> float:
        """Connections served."""
        return float(self.served.sum())

    @property
    def served_people(self) -> np.ndarray:
        """Connections served x that tile's people per connection."""
        return self.served * self.household_size

    @property
    def total_served_people(self) -> float:
        return float(self.served_people.sum())

    @property
    def utilization(self) -> np.ndarray:
        """Fraction of the satellite capacity passing over each tile that is
        actually carrying customers. NaN where no satellite ever flies (beyond
        the highest shell's coverage latitude), since 0/0 is undefined."""
        used = sum(self.used_by_group)
        cap = sum(self.capacity_by_group)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(cap > 0, used / cap, np.nan)

    def unreachable_slack(self, groups: list) -> dict:
        """Diagnostic: is a low-utilization tile physically starved, or did the
        allocator just leave throughput on the table?

        Returns the share of covered satellite tiles that have BOTH spare capacity
        and unserved demand within reach -- the only places a better routing could
        help. Everywhere else, low utilization is real: there is nobody left to serve
        inside the coverage disk.

        This is what settles whether a dark patch on the utilization map is a bug.
        Measured at N=100,000: central Sahara sits at 16% utilization with exactly
        zero unmet demand within reach (genuinely starved -- its coverage disk holds
        almost nobody), while central Europe is at 100% with 39M customers queued.
        Only 4.7% of covered tiles have both, holding ~1.5% of served customers'
        worth of spare capacity, consistent with the 1-2% gap from the exact
        max-flow optimum that tile_capacity_validation.py measures independently.
        """
        capacity = sum(self.capacity_by_group)
        free = capacity - sum(self.used_by_group)
        unmet = np.maximum(self.demand - self.served, 0.0)
        reachable_unmet = sum(g.operator.apply(unmet) for g in groups) / len(groups)
        covered = capacity > 0
        both = covered & (free > 1e-6 * capacity.max()) & (reachable_unmet > 0)
        return {
            "covered_tiles": int(covered.sum()),
            "tiles_with_spare_and_reachable_demand": int(both.sum()),
            "share_of_covered_tiles": float(both.sum() / max(covered.sum(), 1)),
            "spare_capacity_on_those_tiles": float(free[both].sum()),
        }

    @property
    def served_fraction(self) -> np.ndarray:
        """Served PEOPLE as a fraction of each ground tile's raw population -- the
        people basis, since "what share of the population has service" is the
        natural reading. NaN where nobody lives, so a heatmap shows "no data"
        rather than "0% served"."""
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(self.population > 0, self.served_people / self.population, np.nan)


def _water_fill(demand_tiles: np.ndarray, groups: list[SupplyGroup], capacity: list,
                weights: list, max_iter: int, tol: float):
    """One proportional water-filling pass. ALWAYS produces a feasible flow.

    Each round: every ground tile with unmet demand requests from the satellites it
    can see, splitting its request across them in proportion to (remaining free
    capacity x weight); every oversubscribed satellite tile rations its remaining
    capacity proportionally among the requests it received. Repeat until no tile
    with unmet demand can still reach free capacity.

    Every quantity needed is a disk sum, so a round costs exactly three
    DiskOperator.apply() calls per supply group -- no explicit ~20M-edge graph.
    The algebra is exact, not a sampling of individual requests: writing
    r_i = unmet_i / (reachable weighted free capacity), the requests arriving at
    satellite tile j are (free_j w_j) * Disk(r)_j, and the customers won by ground
    tile i are r_i * Disk(free * w * ration)_i. Because Disk is self-adjoint these
    two sum to the same total, so the implied per-edge flow
    x_ij = r_i * free_j * w_j * ration_j * A_ij has row sums <= unmet and column
    sums <= free every round -- feasibility holds by construction, never by
    post-hoc repair.
    """
    unmet = demand_tiles.astype(np.float64).copy()
    free = [c.copy() for c in capacity]
    served = np.zeros_like(unmet)
    used = [np.zeros_like(c) for c in capacity]
    total_demand = unmet.sum()

    iterations = 0
    for iterations in range(1, max_iter + 1):
        weighted_free = [f * w for f, w in zip(free, weights)]
        reachable = sum(g.operator.apply(x) for g, x in zip(groups, weighted_free))
        active = (unmet > 0) & (reachable > 0)
        if not active.any():
            break

        r = np.zeros_like(unmet)
        np.divide(unmet, reachable, out=r, where=active)

        rations, consumed = [], []
        for g, f, x in zip(groups, free, weighted_free):
            requests = x * g.operator.apply(r)
            ration = np.ones_like(f)
            np.divide(f, requests, out=ration, where=requests > f)
            rations.append(ration)
            consumed.append(np.minimum(f, requests))

        gain = sum(g.operator.apply(x * ration)
                   for g, x, ration in zip(groups, weighted_free, rations))
        delta = np.minimum(r * gain, unmet)   # the clip guards float drift only
        if delta.sum() <= tol * max(total_demand, 1.0):
            break

        served += delta
        unmet -= delta
        for k in range(len(free)):
            free[k] = np.maximum(free[k] - consumed[k], 0.0)
            used[k] += consumed[k]

    return served, used, iterations


def allocate(demand_tiles: np.ndarray, groups: list[SupplyGroup], capacity_per_sat: float,
             outer_rounds: int = 17, max_iter: int = 60, tol: float = 1e-9,
             eta: float = 0.25, slack_floor: float = 0.03):
    """Allocate satellite capacity to ground demand. Returns the AVERAGE of every
    reweighting round, which is both near-optimal and spatially coherent.

    A single water-filling pass terminates at a MAXIMAL flow -- no ground tile with
    unmet demand can still reach free capacity -- which is not the MAXIMUM flow. It
    commits capacity greedily, so a tile that had several options can consume the one
    satellite some other tile depended on. Against an exact max-flow reference on the
    same graph, one pass lands 6-8% short of the optimum (tile_capacity_validation.py).

    Closing that gap: repeat the pass, reweighting each satellite tile by how much
    slack it had last time, so demand drifts off contended satellites and onto idle
    ones. Weights only steer WHERE requests go, never how much capacity exists, so
    every pass is independently feasible.

    Why the ROUNDS ARE AVERAGED rather than taking the best one. The reweighting is a
    multiplicative accumulation with no fixed point: the weight spread grows
    geometrically, reaching ~1e6 by round 16 and pinning at the clip bounds by round
    17. Individual rounds are feasible and the total peaks near round 16, but the
    per-round MAP is not physical -- successive rounds push a wave of demand outward
    from each population centre, rendering as concentric rings of alternating
    utilization, with satellites directly over people less used than ones a coverage
    radius away. The rings are plainly visible over Europe and were spotted by eye;
    note that a global smoothness metric MISSED them entirely (total variation
    actually improves as the rings develop, because it is dominated by the coastline
    halos), so this was caught by looking at the map, not by a summary statistic.

    Because each round's rings sit at a different radius, averaging cancels them, and
    a convex combination of feasible flows is itself feasible -- row sums stay under
    demand, column sums under capacity, and the total is just the mean of the totals.
    Measured at N=100,000: greedy 5,242M with a clean map, best single round 5,774M
    with heavy ringing, average of rounds 0-16 5,612M with a map as smooth as greedy.
    The average gives up 2.8% of the peak total to be physically coherent, and is
    still 7% above greedy. This is the standard ergodic-averaging fix for an
    oscillating first-order iteration, not an ad-hoc smoothing of the output.

    Returns (served, used_by_group, capacity_by_group, iterations, greedy_total),
    where greedy_total is the un-reweighted first pass -- a useful lower-bound proxy
    for less coordinated routing (see ASSUMPTIONS.md #18).
    """
    capacity = [g.sats_per_tile * capacity_per_sat for g in groups]
    weights = [np.ones_like(c) for c in capacity]

    acc_served = np.zeros_like(demand_tiles, dtype=np.float64)
    acc_used = [np.zeros_like(c) for c in capacity]
    rounds = max(1, outer_rounds)
    greedy_total = None
    iterations = 0

    for _ in range(rounds):
        served, used, iterations = _water_fill(demand_tiles, groups, capacity, weights,
                                               max_iter, tol)
        if greedy_total is None:
            greedy_total = float(served.sum())
        acc_served += served
        for k, u in enumerate(used):
            acc_used[k] += u

        slack = [1.0 - np.divide(u, c, out=np.zeros_like(c), where=c > 0)
                 for u, c in zip(used, capacity)]
        weights = [np.clip(w * ((sl + slack_floor) / (sl.mean() + slack_floor)) ** eta, 1e-6, 1e6)
                   for w, sl in zip(weights, slack)]

    served = acc_served / rounds
    used = [u / rounds for u in acc_used]

    # Flow-conservation audit. Every customer served must be carried by some
    # satellite, so served <= capacity consumed always. This caught a real bug where
    # FFT round-off let uncovered tiles be served for free, inflating the total ~50%
    # over consumed capacity; the guard stays so that class cannot return silently.
    # The tolerance covers ordinary float accumulation plus DiskOperator's own noise
    # clipping, which trims gain and consumed at very slightly different points.
    total = float(served.sum())
    consumed = sum(float(u.sum()) for u in used)
    if total > consumed * (1 + ALLOCATION_CONSERVATION_TOL) + 1.0:
        raise AssertionError(
            f"flow conservation violated: {total:,.0f} customers served but only "
            f"{consumed:,.0f} of satellite capacity consumed. Every unit served must "
            f"come from some satellite -- see DiskOperator.NOISE_FLOOR_REL.")
    return served, used, capacity, iterations, greedy_total


def solve(total_sats: float, tile: TileGrid | None = None, demand: DemandTiles | None = None,
          scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
          base_shells: list[og.Shell] | None = None,
          min_elevation_deg: float = og.MIN_ELEVATION_DEG,
          altitude_override_km: float | None = None,
          apply_density_cap: bool = True,
          operator_cache: dict | None = None,
          outer_rounds: int = 12, max_iter: int = 60) -> AllocationResult:
    """Full model at one constellation size. Returns per-tile served customers,
    utilization and served fraction.

    apply_density_cap=False drops the areal beam-footprint ceiling and offers raw
    (uncapped) connection demand, isolating the aggregate-capacity constraint.
    """
    tile = tile if tile is not None else make_tile_grid()
    demand = demand if demand is not None else build_demand(tile)
    groups = build_supply(total_sats, tile, base_shells, min_elevation_deg,
                          altitude_override_km, operator_cache)

    if apply_density_cap:
        cap = cdm.max_customer_density_per_km2(scenario) * sats_reaching_tile(groups)
        offered = capped_demand(demand, cap)
    else:
        offered = demand.connections

    served, used, capacity, iters, greedy_total = allocate(
        offered, groups, cdm.max_customers_per_satellite(scenario),
        outer_rounds=outer_rounds, max_iter=max_iter)

    return AllocationResult(served=served, demand=offered, population=demand.population,
                            household_size=demand.household_size,
                            used_by_group=used, capacity_by_group=capacity,
                            total_sats=float(total_sats), iterations=iters,
                            greedy_total=float(greedy_total))


def sweep(sat_counts, tile: TileGrid | None = None, demand: DemandTiles | None = None,
          **kwargs) -> list[AllocationResult]:
    """solve() at each N, reusing one tile grid, one demand build and one operator
    cache -- the DiskOperator kernels depend only on radius and grid, not on N, so
    building them once cuts a sweep's cost by most of its runtime."""
    tile = tile if tile is not None else make_tile_grid()
    demand = demand if demand is not None else build_demand(tile)
    cache = kwargs.pop("operator_cache", {})
    return [solve(n, tile=tile, demand=demand, operator_cache=cache, **kwargs) for n in sat_counts]


# ---------------------------------------------------------------------------
# Global (non-country) summary readouts -- for the "vs satellite count" and
# latitude-marginal charts that used to read serviceable_customers_model.py's
# 1D latitude-pooled functions. Added 2026-09-05 when those chart families were
# migrated onto this 2D model; see CLAUDE.md.
# ---------------------------------------------------------------------------

def fleet_utilization(result: AllocationResult, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO) -> float:
    """Share of the WHOLE fleet's capacity actually carrying customers -- a single
    scalar, as opposed to AllocationResult.utilization's per-tile array."""
    total_capacity = result.total_sats * cdm.max_customers_per_satellite(scenario)
    return result.total_served / total_capacity if total_capacity > 0 else 0.0


def served_fraction_by_latitude(result: AllocationResult, tile: TileGrid) -> np.ndarray:
    """Population-weighted average of AllocationResult.served_fraction, marginalized
    over longitude -- the (N x latitude) saturation heatmap's per-row value at one N.

    Replaces serviceable_customers_model.served_fraction_by_latitude(), which
    computed this from the buggy ring-pooled density cap
    (og.expected_sats_reaching_latitude(), ~19x too generous -- see
    LONGITUDE_FOV_CAPACITY_REVIEW.md). Here it is a straight readout of the already-
    correct 2D allocation: no separate latitude-only computation exists to get wrong.
    NaN where a latitude row has no population, matching the old convention."""
    frac = result.served_fraction
    pop = result.population
    weight = np.where(np.isnan(frac), 0.0, pop)
    row_weight = weight.sum(axis=1)
    row_num = np.nansum(np.where(np.isnan(frac), 0.0, frac) * weight, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(row_weight > 0, row_num / row_weight, np.nan)


def density_cap_connections_per_km2(total_sats: float, tile: TileGrid,
                                    scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                                    base_shells: list[Shell] | None = None,
                                    operator_cache: dict | None = None) -> np.ndarray:
    """Per-tile areal density ceiling (connections/km^2), standalone from solve() --
    cheap (no allocation, just the disk sum), useful whenever only the CEILING
    itself is wanted, not who actually gets served against it."""
    groups = build_supply(total_sats, tile, base_shells, operator_cache=operator_cache)
    return cdm.max_customer_density_per_km2(scenario) * sats_reaching_tile(groups)


def density_cap_profile_average_people(total_sats: float, tile: TileGrid, demand: DemandTiles,
                                       scenario: cdm.CapacityScenario = cdm.V3_SCENARIO,
                                       base_shells: list[Shell] | None = None,
                                       operator_cache: dict | None = None) -> float:
    """A single number summarizing the areal density ceiling across the whole world,
    in PEOPLE/km^2 (connections/km^2 x each tile's household size) -- the 2D
    counterpart of serviceable_customers_model.effective_density_cap_profile_average().

    Weighted by POPULATION, not by the cap itself. The old latitude-only version
    weighted by where satellites concentrate (cap-weighted), answering "what ceiling
    does a typical SATELLITE support" -- defensible when the only available
    dimension was latitude, but this model can now weight by where people actually
    ARE, which is the more useful reading of "what ceiling does a typical PERSON
    experience." A deliberate change, not a like-for-like port -- see CLAUDE.md.
    """
    cap_conn = density_cap_connections_per_km2(total_sats, tile, scenario, base_shells, operator_cache)
    cap_people = cap_conn * demand.household_size
    total_pop = demand.population.sum()
    return float((cap_people * demand.population).sum() / total_pop) if total_pop > 0 else 0.0


if __name__ == "__main__":
    import time

    t0 = time.time()
    tile = make_tile_grid()
    demand = build_demand(tile)
    hh_mean = float((demand.population * demand.household_size).sum() / demand.population.sum())
    print(f"tiles {tile.shape}, world population {demand.population.sum()/1e9:.2f}B "
          f"-> {demand.connections.sum()/1e9:.2f}B connections "
          f"({time.time()-t0:.1f}s to build demand)")
    print(f"  household size: {hh_mean:.2f} people/connection (population-weighted), "
          f"{100*demand.household_report['population_matched_share']:.1f}% of population "
          f"matched to a country polygon")
    print(f"V3 scenario: {cdm.max_customers_per_satellite(cdm.V3_SCENARIO):,.0f} connections/sat, "
          f"{cdm.max_customer_density_per_km2(cdm.V3_SCENARIO):,.1f} connections/km^2 per satellite in view\n")

    cache = {}
    print(f"{'N sats':>10} {'connections':>13} {'people':>11} {'% of pop':>9} {'utilization':>12} {'s':>6}")
    for n in (1_000, 4_408, 10_900, 33_900, 100_000, 300_000, 1_000_000):
        t1 = time.time()
        res = solve(n, tile=tile, demand=demand, operator_cache=cache)
        util = res.total_served / (n * cdm.max_customers_per_satellite(cdm.V3_SCENARIO))
        print(f"{n:>10,} {res.total_served/1e6:>11.1f}M {res.total_served_people/1e6:>9.0f}M "
              f"{100*res.total_served_people/demand.population.sum():>8.1f}% "
              f"{100*util:>11.1f}% {time.time()-t1:>5.1f}")
