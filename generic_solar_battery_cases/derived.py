"""Derived quantities: the profit optimization that turns physics into economics.

The served-energy grid (pure physics) is computed once and cached. Every economic
result here is a cheap argmax over that grid:

    profit(S, B) = income · served(S, B)
                 − solar_cost_ann  · S
                 − battery_cost_ann · B
                 − load_cost_ann   · L   (annualized load capex; default 0)

"Optimal" everywhere means the (S, B) that maximizes annual profit. When the best
hardware build still yields negative profit, "build nothing" (S=B=0, no load, profit=0)
wins — utilization is reported as 0%. This is implemented as a post-argmax clamp.

load_cost_ann is a constant offset over the (S, B) grid, so it never changes WHICH
build is optimal — only whether any build beats "build nothing".
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

import config as cfg
import model


# --------------------------------------------------------------------------- #
# Cached served-energy grid
# --------------------------------------------------------------------------- #
def _grid_cache_key(data_path, resample, rte, kw_solar, kwh_battery, load_kw) -> str:
    h = hashlib.sha1()
    for part in (str(data_path), str(resample), f"{rte:.6f}", f"{load_kw:.6f}"):
        h.update(part.encode())
    h.update(kw_solar.tobytes())
    h.update(kwh_battery.tobytes())
    return h.hexdigest()[:16]


def load_served_grid(
    data_path=cfg.DATA_FILE,
    resample=cfg.SWEEP_DT_RESAMPLE,
    rte=cfg.ROUND_TRIP_EFFICIENCY,
    kw_solar=cfg.KW_SOLAR_GRID,
    kwh_battery=cfg.KWH_BATTERY_GRID,
    load_kw=cfg.LOAD_KW,
    use_cache=True,
    verbose=True,
) -> model.ServedGrid:
    """Build (or load from cache) the price-independent served-energy grid."""
    key = _grid_cache_key(data_path, resample, rte, kw_solar, kwh_battery, load_kw)
    cache_path = cfg.CACHE_DIR / f"served_grid_{key}.npz"

    if use_cache and cache_path.exists():
        if verbose:
            print(f"Loading served grid from cache: {cache_path.name}")
        z = np.load(cache_path)
        return model.ServedGrid(
            kw_solar=z["kw_solar"], kwh_battery=z["kwh_battery"],
            served_kwh=z["served_kwh"], demand_kwh=float(z["demand_kwh"]),
            capacity_factor=float(z["capacity_factor"]),
            warmstart_iters=int(z["warmstart_iters"]),
        )

    data = model.load_nsrdb(data_path, resample=resample)
    if verbose:
        print(f"Building served grid: {kw_solar.size}x{kwh_battery.size} configs "
              f"over {data.n_steps:,} steps @ {data.dt_hours:.3g} h ...")
    grid = model.served_energy_grid(data, kw_solar, kwh_battery, load_kw, rte, verbose=verbose)

    if use_cache:
        cfg.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.savez(
            cache_path,
            kw_solar=grid.kw_solar, kwh_battery=grid.kwh_battery,
            served_kwh=grid.served_kwh, demand_kwh=grid.demand_kwh,
            capacity_factor=grid.capacity_factor, warmstart_iters=grid.warmstart_iters,
        )
        if verbose:
            print(f"Cached -> {cache_path.name}  (warm-start converged in {grid.warmstart_iters} iters)")
    return grid


# --------------------------------------------------------------------------- #
# Single profit-maximizing build
# --------------------------------------------------------------------------- #
@dataclass
class OptimalBuild:
    kw_solar: float
    kwh_battery: float
    served_kwh: float
    utilization: float
    profit_per_yr: float
    on_edge: bool          # optimum sits on the grid's upper boundary (possible clip)


def profit_grid(
    grid: model.ServedGrid, income_per_kwh: float,
    solar_cost_ann: float, batt_cost_ann: float,
    load_cost_ann: float = 0.0,
) -> np.ndarray:
    """Annual profit over the full (S, B) grid. Shape (nS, nB).

    load_cost_ann is a constant offset (annualized load capex); it shifts the
    absolute profit but never changes which (S, B) maximizes it.
    """
    return (
        income_per_kwh * grid.served_kwh
        - solar_cost_ann * grid.kw_solar[:, None]
        - batt_cost_ann * grid.kwh_battery[None, :]
        - load_cost_ann * cfg.LOAD_KW
    )


def optimal_build(
    grid: model.ServedGrid, income_per_kwh: float,
    solar_cost_ann: float, batt_cost_ann: float,
    load_cost_ann: float = 0.0,
) -> OptimalBuild:
    """The (S, B) maximizing annual profit, and its utilization / profit.

    If the best hardware build still yields negative profit, returns S=B=0
    (build nothing, profit=0, utilization=0).
    """
    profit = profit_grid(grid, income_per_kwh, solar_cost_ann, batt_cost_ann, load_cost_ann)
    i, j = np.unravel_index(int(np.argmax(profit)), profit.shape)
    best_profit = float(profit[i, j])
    if best_profit < 0.0:
        return OptimalBuild(kw_solar=0.0, kwh_battery=0.0, served_kwh=0.0,
                            utilization=0.0, profit_per_yr=0.0, on_edge=False)
    on_edge = (i == grid.kw_solar.size - 1 and i > 0) or (j == grid.kwh_battery.size - 1 and j > 0)
    return OptimalBuild(
        kw_solar=float(grid.kw_solar[i]),
        kwh_battery=float(grid.kwh_battery[j]),
        served_kwh=float(grid.served_kwh[i, j]),
        utilization=float(grid.served_kwh[i, j] / grid.demand_kwh),
        profit_per_yr=best_profit,
        on_edge=bool(on_edge),
    )


# --------------------------------------------------------------------------- #
# Chart A — cost plane: optimal utilization & profit over (solar cost, batt cost)
# --------------------------------------------------------------------------- #
@dataclass
class CostPlane:
    solar_cost_ann: np.ndarray     # (nCs,) y-axis
    batt_cost_ann: np.ndarray      # (nCb,) x-axis
    utilization: np.ndarray        # (nCs, nCb) optimal utilization, fraction
    profit_per_yr: np.ndarray      # (nCs, nCb) optimal annual profit ($)
    income_per_kwh: float
    edge_fraction: float           # share of cells whose optimum clipped the grid edge


def cost_plane(
    grid: model.ServedGrid,
    income_per_kwh: float = cfg.INCOME_PER_KWH,
    solar_cost_sweep: np.ndarray = cfg.SOLAR_COST_ANN_SWEEP,
    batt_cost_sweep: np.ndarray = cfg.BATT_COST_ANN_SWEEP,
    load_cost_ann: float = 0.0,
) -> CostPlane:
    """Re-optimize the build at every (solar cost, battery cost) point.

    Vectorized over the battery-cost axis (one (nCb, nS, nB) profit block per
    solar-cost row), so the whole plane is a handful of seconds.
    load_cost_ann shifts the absolute profit at every cell but not the argmax.
    """
    S, B = grid.kw_solar, grid.kwh_battery
    nB = B.size
    base = income_per_kwh * grid.served_kwh         # (nS, nB), income portion

    nCs, nCb = solar_cost_sweep.size, batt_cost_sweep.size
    util = np.empty((nCs, nCb))
    profit = np.empty((nCs, nCb))
    edge_hits = 0

    for ci, cs in enumerate(solar_cost_sweep):
        p_solar = base - cs * S[:, None]                                  # (nS, nB)
        block = p_solar[None, :, :] - batt_cost_sweep[:, None, None] * B[None, None, :]  # (nCb, nS, nB)
        flat = block.reshape(nCb, -1)
        idx = flat.argmax(axis=1)                                         # (nCb,)
        row_profit = flat[np.arange(nCb), idx] - load_cost_ann * cfg.LOAD_KW
        i, j = np.divmod(idx, nB)
        row_util = grid.served_kwh[i, j] / grid.demand_kwh
        no_build = row_profit < 0
        profit[ci] = np.where(no_build, 0.0, row_profit)
        util[ci] = np.where(no_build, 0.0, row_util)
        edge_hits += int(np.count_nonzero(
            ~no_build & (((i == S.size - 1) & (i > 0)) | ((j == nB - 1) & (j > 0)))
        ))

    return CostPlane(
        solar_cost_ann=solar_cost_sweep, batt_cost_ann=batt_cost_sweep,
        utilization=util, profit_per_yr=profit, income_per_kwh=income_per_kwh,
        edge_fraction=edge_hits / (nCs * nCb),
    )


# --------------------------------------------------------------------------- #
# Chart B — optimal utilization vs load income
# --------------------------------------------------------------------------- #
@dataclass
class IncomeSweep:
    income_per_kwh: np.ndarray     # (nK,) x-axis
    utilization: np.ndarray        # (nK,) optimal utilization, fraction
    profit_per_yr: np.ndarray      # (nK,)
    opt_kw_solar: np.ndarray       # (nK,)
    opt_kwh_battery: np.ndarray    # (nK,)
    solar_cost_ann: float
    batt_cost_ann: float
    edge_fraction: float


def income_sweep(
    grid: model.ServedGrid,
    income_values: np.ndarray = cfg.INCOME_SWEEP,
    solar_cost_ann: float = cfg.SOLAR_COST_ANN,
    batt_cost_ann: float = cfg.BATTERY_COST_ANN,
    load_cost_ann: float = 0.0,
) -> IncomeSweep:
    """Profit-maximizing utilization at each load-income level (fixed costs)."""
    S, B = grid.kw_solar, grid.kwh_battery
    nB = B.size
    cost_term = solar_cost_ann * S[:, None] + batt_cost_ann * B[None, :]   # (nS, nB)

    nK = income_values.size
    profit = income_values[:, None, None] * grid.served_kwh[None] - cost_term[None]
    flat = profit.reshape(nK, -1)
    idx = flat.argmax(axis=1)
    i, j = np.divmod(idx, nB)

    served = grid.served_kwh[i, j]
    total_profit = flat[np.arange(nK), idx] - load_cost_ann * cfg.LOAD_KW
    no_build = total_profit < 0
    edge = ~no_build & (((i == S.size - 1) & (i > 0)) | ((j == nB - 1) & (j > 0)))
    return IncomeSweep(
        income_per_kwh=income_values,
        utilization=np.where(no_build, 0.0, served / grid.demand_kwh),
        profit_per_yr=np.where(no_build, 0.0, total_profit),
        opt_kw_solar=np.where(no_build, 0.0, S[i]),
        opt_kwh_battery=np.where(no_build, 0.0, B[j]),
        solar_cost_ann=solar_cost_ann,
        batt_cost_ann=batt_cost_ann,
        edge_fraction=float(np.mean(edge)),
    )


# --------------------------------------------------------------------------- #
# Chart C — optimal utilization vs load capex ($/kW·yr)
# --------------------------------------------------------------------------- #
@dataclass
class LoadCapexSweep:
    """Sweep over annualized load capex at fixed income and solar/battery costs."""
    load_cost_ann: np.ndarray       # (nL,) x-axis, $/kW·yr
    utilization: np.ndarray         # (nL,) optimal utilization, fraction
    profit_per_yr: np.ndarray       # (nL,) net annual profit ($)
    income_per_kwh: float
    solar_cost_ann: float
    batt_cost_ann: float
    load_amortization_years: float

    @property
    def load_capex_raw(self) -> np.ndarray:
        """Raw load capex ($/kW) = annualized × amortization years."""
        return self.load_cost_ann * self.load_amortization_years


def load_capex_sweep(
    grid: model.ServedGrid,
    load_cost_ann_values: np.ndarray = cfg.LOAD_COST_ANN_SWEEP,
    income_per_kwh: float = cfg.INCOME_PER_KWH,
    solar_cost_ann: float = cfg.SOLAR_COST_ANN,
    batt_cost_ann: float = cfg.BATTERY_COST_ANN,
    load_amortization_years: float = cfg.LOAD_AMORTIZATION_YEARS,
) -> LoadCapexSweep:
    """Optimal utilization as load capex increases, at fixed income and hardware costs.

    load_cost_ann is a constant offset over (S, B), so the optimal hardware build
    never changes — only whether it beats "build nothing" (profit >= 0).
    """
    opt = optimal_build(grid, income_per_kwh, solar_cost_ann, batt_cost_ann, load_cost_ann=0.0)
    base_util = opt.utilization
    base_profit = opt.profit_per_yr   # hardware profit before load capex

    total_profit = base_profit - load_cost_ann_values * cfg.LOAD_KW
    no_build = total_profit < 0
    return LoadCapexSweep(
        load_cost_ann=load_cost_ann_values,
        utilization=np.where(no_build, 0.0, base_util),
        profit_per_yr=np.maximum(total_profit, 0.0),
        income_per_kwh=income_per_kwh,
        solar_cost_ann=solar_cost_ann,
        batt_cost_ann=batt_cost_ann,
        load_amortization_years=load_amortization_years,
    )


# --------------------------------------------------------------------------- #
# Chart D — load plane: income (y) × load capex (x)
# --------------------------------------------------------------------------- #
@dataclass
class LoadPlane:
    """Optimal utilization and profit over the (income × load capex) plane."""
    income_per_kwh: np.ndarray      # (nI,) y-axis
    load_cost_ann: np.ndarray       # (nCl,) x-axis, $/kW·yr annualized  ← primary axis
    utilization: np.ndarray         # (nI, nCl) profit-optimal utilization
    profit_per_yr: np.ndarray       # (nI, nCl)
    lcoe_utilization: np.ndarray    # (nI, nCl) LCOE-optimal utilization (income-independent)
    lcoe_min: np.ndarray            # (nCl,) minimum achievable LCOE at each load_capex level
    lvoe: np.ndarray                # (nI, nCl) Levelized Value of Energy = income - min_LCOE [$/kWh]
    solar_cost_ann: float
    batt_cost_ann: float
    load_amortization_years: float

    @property
    def load_capex_raw(self) -> np.ndarray:
        """Raw load capex ($/kW) = annualized × amortization years — used for the secondary axis."""
        return self.load_cost_ann * self.load_amortization_years


def load_plane(
    grid: model.ServedGrid,
    income_values: np.ndarray = cfg.LOAD_PLANE_INCOME_SWEEP,
    load_capex_raw_sweep: np.ndarray = cfg.LOAD_CAPEX_RAW_SWEEP,
    solar_cost_ann: float = cfg.SOLAR_COST_ANN,
    batt_cost_ann: float = cfg.BATTERY_COST_ANN,
    load_amortization_years: float = cfg.LOAD_AMORTIZATION_YEARS,
) -> LoadPlane:
    """Re-optimize at every (income, load capex) pair.

    Since load capex is a constant offset over (S, B), the argmax-optimal hardware
    build depends only on income. We precompute the income sweep, then broadcast
    over the load-capex axis in a single vectorized step.
    """
    load_cost_ann_sweep = load_capex_raw_sweep / load_amortization_years

    isw = income_sweep(grid, income_values, solar_cost_ann, batt_cost_ann, load_cost_ann=0.0)
    base_profit = isw.profit_per_yr    # (nI,) hardware profit at each income
    base_util = isw.utilization        # (nI,)

    # Broadcast: profit[i, j] = base_profit[i] - load_cost_ann[j] * LOAD_KW
    profit = base_profit[:, None] - load_cost_ann_sweep[None, :] * cfg.LOAD_KW  # (nI, nCl)
    util = np.where(profit >= 0, base_util[:, None], 0.0)
    profit = np.maximum(profit, 0.0)

    # LCOE-optimal utilization and minimum LCOE at each load_capex.
    # Income doesn't enter LCOE, so the argmin (S,B) is income-independent.
    lcoe_sw = load_capex_sweep_lcoe(grid, load_cost_ann_sweep,
                                     solar_cost_ann, batt_cost_ann, load_amortization_years)
    lcoe_util = np.tile(lcoe_sw.utilization, (income_values.size, 1))  # (nI, nCl)
    lcoe_min = lcoe_sw.lcoe                                             # (nCl,)

    # Levelized Value of Energy = income - min_LCOE(load_capex)  [$/kWh]
    # Positive = profitable; negative = don't build.
    # income enters directly (y-axis) and min_LCOE varies with load_capex (x-axis),
    # so this metric genuinely uses both axes of the plane.
    lvoe = income_values[:, None] - lcoe_min[None, :]                  # (nI, nCl)

    return LoadPlane(
        income_per_kwh=income_values,
        load_cost_ann=load_cost_ann_sweep,
        utilization=util,
        profit_per_yr=profit,
        lcoe_utilization=lcoe_util,
        lcoe_min=lcoe_min,
        lvoe=lvoe,
        solar_cost_ann=solar_cost_ann,
        batt_cost_ann=batt_cost_ann,
        load_amortization_years=load_amortization_years,
    )


# --------------------------------------------------------------------------- #
# Chart A (LCOE variant) — minimize $/kWh over the component-cost plane
# --------------------------------------------------------------------------- #
@dataclass
class CostPlaneLCOE:
    """LCOE-minimizing build at each (solar cost, battery cost) combination.

    Unlike profit-max, LCOE minimization puts ALL costs — including load capex —
    in the numerator of $/kWh_delivered. Larger load capex forces the optimizer
    to maximize served_kwh → more solar+battery → higher utilization everywhere,
    not just above an income threshold. This is why LCOE charts always show a
    utilization surface without the "build-nothing" flat floor.
    """
    solar_cost_ann: np.ndarray     # (nCs,) y-axis
    batt_cost_ann: np.ndarray      # (nCb,) x-axis
    utilization: np.ndarray        # (nCs, nCb) LCOE-optimal utilization, fraction
    lcoe: np.ndarray               # (nCs, nCb) minimum LCOE [$/kWh]
    load_cost_ann: float
    edge_fraction: float


def cost_plane_lcoe(
    grid: model.ServedGrid,
    load_cost_ann: float = 0.0,
    solar_cost_sweep: np.ndarray = cfg.SOLAR_COST_ANN_SWEEP,
    batt_cost_sweep: np.ndarray = cfg.BATT_COST_ANN_SWEEP,
) -> CostPlaneLCOE:
    """LCOE-minimizing build at every (solar cost, battery cost) point.

    Vectorized the same way as cost_plane(): outer loop over solar cost, inner
    block over the battery-cost axis. At each cost combination, minimizes
    LCOE(S,B) = (load_cost*L + solar_cost*S + batt_cost*B) / served(S,B).

    Note: load_cost_ann DOES change the argmin here (unlike profit_max), because
    it adds to the numerator — larger load cost forces maximizing served_kwh.
    """
    S, B = grid.kw_solar, grid.kwh_battery
    nB = B.size
    nCs, nCb = solar_cost_sweep.size, batt_cost_sweep.size
    served = grid.served_kwh                          # (nS, nB)

    util_arr = np.empty((nCs, nCb))
    lcoe_arr = np.empty((nCs, nCb))
    edge_hits = 0

    for ci, cs in enumerate(solar_cost_sweep):
        # hw_cost[j, i, k] = cs * S[i] + batt_sweep[j] * B[k]  — (nCb, nS, nB)
        hw = cs * S[None, :, None] + batt_cost_sweep[:, None, None] * B[None, None, :]
        total = load_cost_ann * cfg.LOAD_KW + hw       # (nCb, nS, nB)

        with np.errstate(divide="ignore", invalid="ignore"):
            lcoe_blk = np.where(served[None] > 0, total / served[None], np.inf)
        lcoe_blk[:, 0, 0] = np.inf   # exclude (S=0, B=0) — undefined LCOE

        flat = lcoe_blk.reshape(nCb, -1)
        idx = flat.argmin(axis=1)                      # (nCb,)
        i_opt, j_opt = np.divmod(idx, nB)

        util_arr[ci] = grid.served_kwh[i_opt, j_opt] / grid.demand_kwh
        lcoe_arr[ci] = flat[np.arange(nCb), idx]
        edge_hits += int(np.count_nonzero(
            (i_opt == S.size - 1) | (j_opt == nB - 1)
        ))

    return CostPlaneLCOE(
        solar_cost_ann=solar_cost_sweep,
        batt_cost_ann=batt_cost_sweep,
        utilization=util_arr,
        lcoe=lcoe_arr,
        load_cost_ann=load_cost_ann,
        edge_fraction=edge_hits / (nCs * nCb),
    )


# --------------------------------------------------------------------------- #
# Chart E — LCOE and utilization vs solar fraction (fixed total resource)
# --------------------------------------------------------------------------- #
@dataclass
class SolarFractionSweep:
    """LCOE and utilization along the solar-fraction frontier for one fixed total.

    The frontier is all (S, B) pairs where S_kW + B_kWh = total_units, with the
    solar fraction α = S / (S + B) ∈ (0, 1] sweeping from pure battery (α→0)
    to pure solar (α=1).

    When C_S [$/kW·yr] = C_B [$/kWh·yr] (the equal-cost case), total annual cost
    = C × total_units is constant across all α, so LCOE = C·total_units / served
    and minimising LCOE is identical to maximising served energy.  When costs
    differ, unit fraction ≠ cost fraction; the caller must interpret accordingly.

    pure-battery singularity (α→0): served → 0, LCOE → ∞.  The sweep starts
    at α=0.01 so this infinity is not plotted but the curve's rapid rise shows it.
    """
    alpha: np.ndarray           # (nA,) solar fraction, >0
    utilization: np.ndarray     # (nA,) served / demand_kwh
    lcoe: np.ndarray            # (nA,) $/kWh, inf where served≈0
    total_units: float
    solar_cost_ann: float
    batt_cost_ann: float
    equal_cost: bool            # True when C_S == C_B (unit fraction == cost fraction)
    opt_alpha: float            # α that maximises utilisation / minimises LCOE
    opt_utilization: float
    opt_lcoe: float


def solar_fraction_sweep(
    grid: model.ServedGrid,
    total_units: float,
    alpha_values: np.ndarray = cfg.SOLAR_FRACTION_ALPHA,
    solar_cost_ann: float = cfg.SOLAR_COST_ANN,
    batt_cost_ann: float = cfg.BATTERY_COST_ANN,
) -> SolarFractionSweep:
    """Sweep α = S / (S + B) with S + B = total_units fixed.

    Uses nearest-neighbour lookup in the served-energy grid, so the resolution
    is limited by the grid spacing (0.25 kW solar, 0.5 kWh battery).  At
    total_units > 30 the solar axis clips the grid; set total_units ≤ 30.
    """
    alpha = np.asarray(alpha_values, dtype=float)
    S_vals = alpha * total_units
    B_vals = (1.0 - alpha) * total_units

    # Vectorised nearest-neighbour lookup.
    i_s = np.argmin(np.abs(grid.kw_solar[:, None] - S_vals[None, :]), axis=0)
    j_b = np.argmin(np.abs(grid.kwh_battery[:, None] - B_vals[None, :]), axis=0)
    served = grid.served_kwh[i_s, j_b]

    annual_cost = solar_cost_ann * S_vals + batt_cost_ann * B_vals
    with np.errstate(divide="ignore", invalid="ignore"):
        lcoe = np.where(served > 0, annual_cost / served, np.inf)
    utilization = served / grid.demand_kwh

    # Optimal: lowest finite LCOE (= highest utilisation when costs are equal).
    finite = np.isfinite(lcoe)
    if finite.any():
        opt_idx = int(np.argmin(np.where(finite, lcoe, np.inf)))
        opt_a, opt_u, opt_l = float(alpha[opt_idx]), float(utilization[opt_idx]), float(lcoe[opt_idx])
    else:
        opt_a = opt_u = opt_l = float("nan")

    equal_cost = abs(solar_cost_ann - batt_cost_ann) / (solar_cost_ann + 1e-12) < 0.01
    return SolarFractionSweep(
        alpha=alpha, utilization=utilization, lcoe=lcoe,
        total_units=total_units, solar_cost_ann=solar_cost_ann,
        batt_cost_ann=batt_cost_ann, equal_cost=equal_cost,
        opt_alpha=opt_a, opt_utilization=opt_u, opt_lcoe=opt_l,
    )


def lcoe_surface(
    grid: model.ServedGrid,
    solar_cost_ann: float,
    batt_cost_ann: float,
    load_cost_ann: float = 0.0,
) -> np.ndarray:
    """LCOE at every (S, B) point, shape (nS, nB).

    Used by the LCOE build-plane chart to visualise the full cost heatmap.
    Cells with no service (served=0) are set to np.inf; (S=0,B=0) is always inf.
    """
    S, B = grid.kw_solar, grid.kwh_battery
    hw = solar_cost_ann * S[:, None] + batt_cost_ann * B[None, :]
    total = load_cost_ann * cfg.LOAD_KW + hw
    with np.errstate(divide="ignore", invalid="ignore"):
        lcoe = np.where(grid.served_kwh > 0, total / grid.served_kwh, np.inf)
    lcoe[0, 0] = np.inf
    return lcoe


# --------------------------------------------------------------------------- #
# Chart C (LCOE variant) — minimize $/kWh vs load capex
# --------------------------------------------------------------------------- #
@dataclass
class LoadCapexSweepLCOE:
    """LCOE-minimizing build at each load capex level.

    Unlike profit-max (where load capex is a constant that doesn't affect hardware
    sizing), LCOE minimization puts load capex in the numerator of $/kWh_delivered.
    Larger load capex → need to maximize kWh delivered → more solar/battery →
    rising utilization S-curve.
    """
    load_cost_ann: np.ndarray       # (nL,) $/kW·yr
    utilization: np.ndarray         # (nL,)
    lcoe: np.ndarray                # (nL,) $/kWh at the LCOE-optimal build
    opt_kw_solar: np.ndarray        # (nL,)
    opt_kwh_battery: np.ndarray     # (nL,)
    solar_cost_ann: float
    batt_cost_ann: float
    load_amortization_years: float

    @property
    def load_capex_raw(self) -> np.ndarray:
        return self.load_cost_ann * self.load_amortization_years


def load_capex_sweep_lcoe(
    grid: model.ServedGrid,
    load_cost_ann_values: np.ndarray = cfg.LOAD_COST_ANN_SWEEP,
    solar_cost_ann: float = cfg.SOLAR_COST_ANN,
    batt_cost_ann: float = cfg.BATTERY_COST_ANN,
    load_amortization_years: float = cfg.LOAD_AMORTIZATION_YEARS,
) -> LoadCapexSweepLCOE:
    """LCOE-minimizing build: minimize (load_cost + solar×S + batt×B) / served_kwh.

    Vectorized: computes the full (nL, nS, nB) LCOE tensor in one shot.
    The (S=0, B=0) cell is excluded (undefined LCOE, no service delivered).
    """
    S, B = grid.kw_solar, grid.kwh_battery
    nB = B.size
    nL = load_cost_ann_values.size

    hw_cost = solar_cost_ann * S[:, None] + batt_cost_ann * B[None, :]     # (nS, nB)
    served = grid.served_kwh                                                # (nS, nB)

    # total_cost[l, i, j] = load_cost_ann[l] * LOAD_KW + hw_cost[i, j]
    total_cost = (load_cost_ann_values * cfg.LOAD_KW)[:, None, None] + hw_cost[None]  # (nL, nS, nB)
    with np.errstate(divide="ignore", invalid="ignore"):
        lcoe = np.where(served[None] > 0, total_cost / served[None], np.inf)
    lcoe[:, 0, 0] = np.inf   # exclude (S=0, B=0) — no-build is not a meaningful LCOE

    flat = lcoe.reshape(nL, -1)
    idx = flat.argmin(axis=1)         # (nL,)
    i_opt, j_opt = np.divmod(idx, nB)

    return LoadCapexSweepLCOE(
        load_cost_ann=load_cost_ann_values,
        utilization=grid.served_kwh[i_opt, j_opt] / grid.demand_kwh,
        lcoe=flat[np.arange(nL), idx],
        opt_kw_solar=S[i_opt],
        opt_kwh_battery=B[j_opt],
        solar_cost_ann=solar_cost_ann,
        batt_cost_ann=batt_cost_ann,
        load_amortization_years=load_amortization_years,
    )
