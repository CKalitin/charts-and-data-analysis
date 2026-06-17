"""Chart B — optimal utilization vs load income ($/kWh).

Two line charts:
  1. Profit-optimal: the (S,B) build that maximises annual profit at each income.
     Produces an S-curve — zero below breakeven, rising toward 100% at high income.

  2. LVOE-optimal: the (S,B) build that minimises LCOE (= maximises LVOE for any
     fixed income). This build is income-independent; the curve is a horizontal
     step that jumps from 0 to a constant utilization at the LCOE breakeven income
     (where income first exceeds min LCOE). The two curves diverge at high income
     because profit-optimal overbuilds (larger solar+battery → higher utilization),
     while LVOE-optimal always stays at the minimum-cost build.
"""

from __future__ import annotations

import sys
from pathlib import Path

if not __package__:  # running as a script — add project root to path
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


def _axis_setup(ax, income_values: np.ndarray) -> None:
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"${v:g}" if v >= 1 else f"${v:.3g}"))
    ax.set_xlim(income_values.min(), income_values.max())
    ax.set_ylim(0, 105)
    ax.set_xlabel(axis_label("income_per_kwh"))
    ax.set_ylabel(axis_label("utilization_pct"))
    ax.grid(True, which="both", linestyle="--", alpha=0.35)


def draw_profit_optimal(ax, sweep: derived.IncomeSweep) -> None:
    """Profit-maximising utilization at each income level (S-curve)."""
    ax.fill_between(sweep.income_per_kwh, sweep.utilization * 100.0,
                    color="#7b2fbe", alpha=0.12, zorder=2)
    ax.plot(sweep.income_per_kwh, sweep.utilization * 100.0,
            color="#7b2fbe", linewidth=2.4, zorder=3,
            label="Profit-optimal")
    _axis_setup(ax, sweep.income_per_kwh)
    ax.set_title("Profit-optimal utilization vs load income")


def draw_lvoe_optimal(ax, grid: derived.model.ServedGrid,
                      income_values: np.ndarray,
                      solar_cost_ann: float = cfg.SOLAR_COST_ANN,
                      batt_cost_ann: float = cfg.BATTERY_COST_ANN) -> None:
    """LVOE-maximising (= LCOE-minimising) utilization vs income.

    The optimal build is income-independent; the curve is a horizontal step
    that appears once income exceeds the minimum achievable LCOE.
    """
    lcoe_surface = derived.lcoe_surface(grid, solar_cost_ann, batt_cost_ann,
                                        load_cost_ann=0.0)
    finite = np.isfinite(lcoe_surface)
    idx = int(np.argmin(np.where(finite, lcoe_surface, np.inf)))
    i, j = np.unravel_index(idx, lcoe_surface.shape)
    lcoe_min = float(lcoe_surface[i, j])
    util_lcoe = float(grid.served_kwh[i, j] / grid.demand_kwh * 100.0)

    util_line = np.where(income_values >= lcoe_min, util_lcoe, 0.0)

    ax.fill_between(income_values, util_line, color="#e07b00", alpha=0.12, zorder=2)
    ax.plot(income_values, util_line, color="#e07b00", linewidth=2.4, zorder=3,
            label=f"LVOE-optimal  (LCOE min = {common._dollar_fmt(lcoe_min)}/kWh)")
    ax.axvline(lcoe_min, color="#e07b00", linewidth=1.0, linestyle=":",
               alpha=0.7)
    _axis_setup(ax, income_values)
    ax.set_title("LVOE-optimal utilization vs load income")
    ax.legend(fontsize=8, framealpha=0.85)


def _params(sweep: derived.IncomeSweep, grid) -> dict[str, str]:
    return {
        "Site":            common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load":            f"{cfg.LOAD_KW:g} kW constant",
        "Solar cost":      f"${sweep.solar_cost_ann:.3g}/kW·yr  (${sweep.solar_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kW)",
        "Battery cost":    f"${sweep.batt_cost_ann:.3g}/kWh·yr  (${sweep.batt_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kWh)",
        "Amortization":    f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }


def figures(sweep: derived.IncomeSweep, grid):
    from viz import render

    suffix = common.param_suffix({
        "sol":   f"{sweep.solar_cost_ann:.3g}",
        "bat":   f"{sweep.batt_cost_ann:.3g}",
        "amort": f"{cfg.AMORTIZATION_YEARS:g}",
    })
    params = _params(sweep, grid)

    def profit_fig():
        fig, ax = render.new_figure(figsize=(10, 6))
        draw_profit_optimal(ax, sweep)
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_UTIL_VS_INCOME / f"util_vs_income_profit_{suffix}.png"

    def lvoe_fig():
        fig, ax = render.new_figure(figsize=(10, 6))
        draw_lvoe_optimal(ax, grid, sweep.income_per_kwh,
                          sweep.solar_cost_ann, sweep.batt_cost_ann)
        common.info(ax, fig, {**params, "Objective": "LVOE maximisation (≡ LCOE min)"}, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_UTIL_VS_INCOME / f"util_vs_income_lvoe_{suffix}.png"

    return [
        ("utilization_vs_income/profit", profit_fig),
        ("utilization_vs_income/lvoe",   lvoe_fig),
    ]


if __name__ == "__main__":
    import time
    from viz import render

    t0 = time.time()
    g = derived.load_served_grid()
    isw = derived.income_sweep(g)
    plan = figures(isw, g)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
