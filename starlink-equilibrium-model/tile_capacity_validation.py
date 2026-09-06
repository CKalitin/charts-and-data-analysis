"""Validate tile_capacity_model.allocate()'s proportional water-filling against an
EXACT max-flow optimum, on a coarsened copy of the same problem.

allocate() terminates at a MAXIMAL flow: no ground tile with unmet demand can still
see any free satellite capacity. That is not automatically the MAXIMUM flow -- an
optimal solution may need augmenting paths that re-route capacity already committed
elsewhere. This script measures the gap on the real geometry rather than assuming
it away, by building the same bipartite transportation problem at a coarse tile size
and solving it exactly with Dinic's algorithm (pure numpy/python -- scipy is not
installed in this environment and one validation script does not justify adding it).

Coarse tiles are fine here: both algorithms run on the IDENTICAL graph, so the test
measures the allocator, not the discretization.

Both sides use DiskOperator's BINARY adjacency (fractional=False). The production
model weights partially-overlapping tiles by their overlap fraction, which is a
strictly richer connectivity than any 0/1 graph can express -- comparing that
against a 0/1 max-flow reference measures the discretization, not the allocator,
and did in fact produce nonsense ratios above 1.0 before the two were matched up.
The fractional weighting is validated separately, against the exact spherical-cap
area (see DiskOperator's docstring).
"""
from __future__ import annotations

from collections import deque

import numpy as np

import capacity_density_model as cdm
import tile_capacity_model as tcm


class Dinic:
    """Standard Dinic max-flow on integer capacities, flat-array edge lists."""

    def __init__(self, n: int):
        self.n = n
        self.head = [[] for _ in range(n)]  # node -> list of edge ids
        self.to: list[int] = []
        self.cap: list[int] = []

    def add(self, u: int, v: int, c: int) -> None:
        self.head[u].append(len(self.to)); self.to.append(v); self.cap.append(c)
        self.head[v].append(len(self.to)); self.to.append(u); self.cap.append(0)

    def max_flow(self, s: int, t: int) -> int:
        flow = 0
        while True:
            level = [-1] * self.n
            level[s] = 0
            q = deque([s])
            while q:
                u = q.popleft()
                for e in self.head[u]:
                    if self.cap[e] > 0 and level[self.to[e]] < 0:
                        level[self.to[e]] = level[u] + 1
                        q.append(self.to[e])
            if level[t] < 0:
                return flow
            it = [0] * self.n

            def dfs(u: int, f: int) -> int:
                if u == t:
                    return f
                while it[u] < len(self.head[u]):
                    e = self.head[u][it[u]]
                    v = self.to[e]
                    if self.cap[e] > 0 and level[v] == level[u] + 1:
                        d = dfs(v, min(f, self.cap[e]))
                        if d > 0:
                            self.cap[e] -= d
                            self.cap[e ^ 1] += d
                            return d
                    it[u] += 1
                return 0

            while True:
                pushed = dfs(s, 1 << 62)
                if pushed == 0:
                    break
                flow += pushed


def run(tile_deg: float, total_sats: float, quantum: float) -> None:
    """Compare both solvers at one constellation size. `quantum` is the integer unit
    (people) capacities are rounded to for the exact solver."""
    import sys
    sys.setrecursionlimit(100_000)

    tile = tcm.make_tile_grid(tile_deg)
    demand_tiles = tcm.build_demand(tile)
    groups = tcm.build_supply(total_sats, tile, fractional=False)
    cap_per_sat = cdm.max_customers_per_satellite(cdm.V3_SCENARIO)
    density_cap = cdm.max_customer_density_per_km2(cdm.V3_SCENARIO) * tcm.sats_reaching_tile(groups)
    offered = tcm.capped_demand(demand_tiles, density_cap)

    served, used, capacity, iters, greedy = tcm.allocate(offered, groups, cap_per_sat)
    approx = served.sum()

    # --- exact reference -----------------------------------------------------
    n_lat, n_lon = tile.shape
    n_tiles = n_lat * n_lon
    n_groups = len(groups)
    # node ids: 0 = source, 1..n_groups*n_tiles = supply, then ground, then sink
    S, T = 0, 1 + n_groups * n_tiles + n_tiles
    g = Dinic(T + 1)

    dem_i = np.rint(offered.ravel() / quantum).astype(np.int64)
    ground0 = 1 + n_groups * n_tiles
    for i in np.nonzero(dem_i)[0]:
        g.add(ground0 + int(i), T, int(dem_i[i]))

    lat_idx, lon_idx = np.divmod(np.arange(n_tiles), n_lon)
    lat_r = np.radians(tile.lat_centers)
    lon_r = np.radians(tile.lon_centers)
    for gi, grp in enumerate(groups):
        sup = np.rint((grp.sats_per_tile * cap_per_sat).ravel() / quantum).astype(np.int64)
        cos_R = np.cos(np.radians(grp.radius_deg))
        base = 1 + gi * n_tiles
        for j in np.nonzero(sup)[0]:
            g.add(S, base + int(j), int(sup[j]))
            jl, jo = lat_idx[j], lon_idx[j]
            cosd = (np.sin(lat_r[jl]) * np.sin(lat_r)[:, None]
                    + np.cos(lat_r[jl]) * np.cos(lat_r)[:, None] * np.cos(lon_r - lon_r[jo])[None, :])
            for i in np.nonzero((cosd >= cos_R).ravel() & (dem_i > 0))[0]:
                g.add(base + int(j), ground0 + int(i), 1 << 40)

    exact = g.max_flow(S, T) * quantum
    ratio = approx / exact if exact else float("nan")
    print(f"  tile {tile_deg:>4.1f}deg N={total_sats:>9,.0f} | exact max-flow {exact/1e6:>8.1f}M"
          f" | 1 greedy pass {greedy/1e6:>8.1f}M ({greedy/exact:6.4f})"
          f" | reweighted {approx/1e6:>8.1f}M ({ratio:6.4f})")


if __name__ == "__main__":
    print("Proportional water-filling vs exact max-flow, same graph:\n")
    for tile_deg in (6.0, 4.0):
        for n in (4_408, 33_900, 300_000):
            run(tile_deg, n, quantum=5_000.0)
