"""Utility line charts — optimal utilization as a 1-D curve.

Four chart types, two optimization objectives × two x-axes:
  vs income   × profit-optimal  — S-curve (build scales up with revenue)
  vs income   × LVOE-optimal    — step function at LCOE_min breakeven
  vs capex    × profit-optimal  — horizontal step, drops at load breakeven
  vs capex    × LVOE-optimal    — rising staircase (more capex → higher util preferred)

Parameter variations:
  vs income charts: load_cost_ann in [0, 10, 100, 1000] $/kW·yr (fixed)
  vs capex  charts: income in [0.01, 0.1, 1.0] $/kWh (fixed)
"""

from __future__ import annotations

import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.ticker as mticker
import numpy as np

import config as cfg
import derived
from labels import axis_label

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]

_LOAD_COST_ANN_SLICES = [0.0, 10.0, 100.0, 1000.0]   # $/kW·yr, fixed for vs-income charts
_INCOME_SLICES        = [0.01, 0.1, 1.0]               # $/kWh,   fixed for vs-capex charts


# --------------------------------------------------------------------------- #
# Shared axis helpers
# --------------------------------------------------------------------------- #
def _setup_axis(ax, x_arr: np.ndarray, xlabel: str) -> None:
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"${v:g}" if v >= 1 else f"${v:.3g}"))
    ax.set_xlim(x_arr.min(), x_arr.max())
    ax.set_ylim(0, 105)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Utilization  (%)")
    ax.grid(True, which="both", linestyle="--", alpha=0.35)


# --------------------------------------------------------------------------- #
# vs income
# --------------------------------------------------------------------------- #
def draw_util_vs_income_profit(ax, grid, income_values: np.ndarray,
                                sol: float, bat: float,
                                lc_ann: float = 0.0) -> None:
    """Profit-maximising utilization at each income level (S-curve)."""
    sweep = derived.income_sweep(grid, income_values, sol, bat, lc_ann)
    u = sweep.utilization * 100.0
    ax.fill_between(income_values, u, color="#7b2fbe", alpha=0.12, zorder=2)
    ax.plot(income_values, u, color="#7b2fbe", linewidth=2.4, zorder=3)
    ax.set_title(f"Profit-optimal utilization vs load income\n"
                 f"(load cost ${lc_ann:g}/kW·yr)")
    _setup_axis(ax, income_values, axis_label("income_per_kwh"))


def draw_util_vs_income_lvoe(ax, grid, income_values: np.ndarray,
                              sol: float, bat: float,
                              lc_ann: float = 0.0) -> None:
    """LVOE-maximising (= LCOE-minimising) utilization vs income — step function."""
    lcoe_surf = derived.lcoe_surface(grid, sol, bat, lc_ann)
    finite = np.isfinite(lcoe_surf)
    idx = int(np.argmin(np.where(finite, lcoe_surf, np.inf)))
    i, j = np.unravel_index(idx, lcoe_surf.shape)
    lcoe_min = float(lcoe_surf[i, j])
    util_lcoe = float(grid.served_kwh[i, j] / grid.demand_kwh * 100.0)

    u = np.where(income_values >= lcoe_min, util_lcoe, 0.0)
    ax.fill_between(income_values, u, color="#e07b00", alpha=0.12, zorder=2)
    ax.plot(income_values, u, color="#e07b00", linewidth=2.4, zorder=3,
            label=f"LCOE min = {common._dollar_fmt(lcoe_min)}/kWh")
    ax.axvline(lcoe_min, color="#e07b00", linewidth=1.0, linestyle=":", alpha=0.7)
    ax.set_title(f"LVOE-optimal utilization vs load income\n"
                 f"(load cost ${lc_ann:g}/kW·yr)")
    ax.legend(fontsize=8, framealpha=0.85)
    _setup_axis(ax, income_values, axis_label("income_per_kwh"))


# --------------------------------------------------------------------------- #
# vs capex
# --------------------------------------------------------------------------- #
def draw_util_vs_capex_profit(ax, grid, load_cost_arr: np.ndarray,
                               income: float, sol: float, bat: float) -> None:
    """Profit-optimal utilization vs load capex.

    The optimal (S,B) build is income-dependent but NOT load-capex-dependent
    (load_cost * L cancels in the argmax). So utilization is constant until
    the accumulated load cost exceeds the profit earned without it, at which
    point the system becomes unprofitable → no build → util=0.
    """
    # Optimal build at zero load cost (argmax unaffected by load_cost_ann)
    opt = derived.optimal_build(grid, income, sol, bat, load_cost_ann=0.0)
    if opt.utilization == 0.0:
        # Not profitable even without load cost
        ax.plot(load_cost_arr, np.zeros_like(load_cost_arr),
                color="#7b2fbe", linewidth=2.4, zorder=3)
        breakeven_lc = 0.0
    else:
        # profit_0 = income * served - hw (at lc_ann=0, already computed)
        # breakeven: profit_0 - lc_ann * L = 0 → lc_ann = profit_0 / L
        profit_no_load = float(
            income * opt.served_kwh
            - cfg.SOLAR_COST_ANN * opt.kw_solar
            - cfg.BATTERY_COST_ANN * opt.kwh_battery
        )
        # Use actual sol/bat costs (not cfg defaults)
        profit_no_load = float(
            income * opt.served_kwh
            - sol * opt.kw_solar
            - bat * opt.kwh_battery
        )
        breakeven_lc = max(0.0, profit_no_load / cfg.LOAD_KW)
        u = np.where(load_cost_arr <= breakeven_lc, opt.utilization * 100.0, 0.0)
        ax.fill_between(load_cost_arr, u, color="#7b2fbe", alpha=0.12, zorder=2)
        ax.plot(load_cost_arr, u, color="#7b2fbe", linewidth=2.4, zorder=3,
                label=f"Breakeven ${breakeven_lc:,.0f}/kW·yr")
        if breakeven_lc > load_cost_arr.min():
            ax.axvline(breakeven_lc, color="#7b2fbe", linewidth=1.0,
                       linestyle=":", alpha=0.7)
        ax.legend(fontsize=8, framealpha=0.85)

    ax.set_title(f"Profit-optimal utilization vs load capex\n"
                 f"(income ${income:g}/kWh)")
    _setup_axis(ax, load_cost_arr, axis_label("load_cost_ann"))


def draw_util_vs_capex_lvoe(ax, grid, load_cost_arr: np.ndarray,
                             income: float, sol: float, bat: float) -> None:
    """LVOE-optimal (= total LCOE-minimising) utilization vs load capex.

    As load capex grows, the build that minimises total_LCOE =
    (hw + lc*L) / served shifts toward higher utilization (spreading the
    fixed load cost over more kWh). The curve rises monotonically, then
    vanishes once min LCOE exceeds the income.
    """
    S, B = grid.kw_solar, grid.kwh_battery
    hw = sol * S[:, None] + bat * B[None, :]     # (nS, nB)
    srv = grid.served_kwh                          # (nS, nB)

    hw_flat  = hw.flatten()
    srv_flat = srv.flatten()
    ok       = srv_flat > 0
    hw_ok    = hw_flat[ok]
    srv_ok   = srv_flat[ok]

    nL = len(load_cost_arr)
    util_arr    = np.zeros(nL)
    lcoe_min_arr = np.full(nL, np.inf)
    for k, lc_ann in enumerate(load_cost_arr):
        lcoe_ok  = (hw_ok + lc_ann * cfg.LOAD_KW) / srv_ok
        best     = int(np.argmin(lcoe_ok))
        util_arr[k]     = srv_ok[best] / grid.demand_kwh * 100.0
        lcoe_min_arr[k] = lcoe_ok[best]

    viable = lcoe_min_arr < income
    u_plot = np.where(viable, util_arr, np.nan)
    ax.fill_between(load_cost_arr, np.where(viable, util_arr, 0.0),
                    color="#e07b00", alpha=0.12, zorder=2)
    ax.plot(load_cost_arr, u_plot, color="#e07b00", linewidth=2.4, zorder=3)
    ax.set_title(f"LVOE-optimal utilization vs load capex\n"
                 f"(income ${income:g}/kWh)")
    _setup_axis(ax, load_cost_arr, axis_label("load_cost_ann"))


# --------------------------------------------------------------------------- #
# Figure builders
# --------------------------------------------------------------------------- #
def figures(grid):
    from viz import render

    sol = cfg.SOLAR_COST_ANN
    bat = cfg.BATTERY_COST_ANN
    income_values  = cfg.INCOME_SWEEP
    load_cost_arr  = cfg.LOAD_COST_ANN_SWEEP

    _base_params = {
        "Site":            common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load":            f"{cfg.LOAD_KW:g} kW constant",
        "Solar cost":      f"${sol:.3g}/kW·yr",
        "Battery cost":    f"${bat:.3g}/kWh·yr",
    }
    hw_suffix = common.param_suffix({"sol": f"{sol:.3g}", "bat": f"{bat:.3g}"})

    def _fig(draw_fn, subdir, name, params):
        def make_fig():
            fig, ax = render.new_figure(figsize=(10, 6))
            draw_fn(ax)
            common.info(ax, fig, params, mode="on")
            common.watermark(ax, fig)
            return fig, cfg.OUT_UTIL_LINES / subdir / f"{name}_{hw_suffix}.png"
        return make_fig

    charts = []

    # ── vs income: loop over fixed load cost slices ──────────────────────────
    for lc_ann in _LOAD_COST_ANN_SLICES:
        lc_slug = f"lc{lc_ann:g}".replace(".", "p")
        params = {**_base_params, "Load cost (fixed)": f"${lc_ann:g}/kW·yr"}

        charts += [
            (f"util_lines/vs_income/profit/{lc_slug}", _fig(
                lambda ax, lc=lc_ann: draw_util_vs_income_profit(
                    ax, grid, income_values, sol, bat, lc),
                "vs_income/profit_opt", f"util_vs_income_profit_{lc_slug}", params)),
            (f"util_lines/vs_income/lvoe/{lc_slug}", _fig(
                lambda ax, lc=lc_ann: draw_util_vs_income_lvoe(
                    ax, grid, income_values, sol, bat, lc),
                "vs_income/lvoe_opt", f"util_vs_income_lvoe_{lc_slug}", params)),
        ]

    # ── vs capex: loop over fixed income slices ───────────────────────────────
    for inc in _INCOME_SLICES:
        inc_slug = f"inc{inc:g}".replace(".", "p")
        params = {**_base_params, "Income (fixed)": f"${inc:g}/kWh"}

        charts += [
            (f"util_lines/vs_capex/profit/{inc_slug}", _fig(
                lambda ax, i=inc: draw_util_vs_capex_profit(
                    ax, grid, load_cost_arr, i, sol, bat),
                "vs_capex/profit_opt", f"util_vs_capex_profit_{inc_slug}", params)),
            (f"util_lines/vs_capex/lvoe/{inc_slug}", _fig(
                lambda ax, i=inc: draw_util_vs_capex_lvoe(
                    ax, grid, load_cost_arr, i, sol, bat),
                "vs_capex/lvoe_opt", f"util_vs_capex_lvoe_{inc_slug}", params)),
        ]

    return charts


if __name__ == "__main__":
    import time
    from viz import render

    t0 = time.time()
    g = derived.load_served_grid()
    plan = figures(g)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
