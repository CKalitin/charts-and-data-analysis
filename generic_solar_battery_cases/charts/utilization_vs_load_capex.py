"""Chart C — optimal utilization vs load capex ($/kW·yr annualized).

TWO VARIANTS — two fundamentally different objectives that produce different curve shapes:

PROFIT-MAX (our framework)
  Load capex is a CONSTANT offset over the entire (S, B) build space, so it never
  changes which hardware is optimal — that is income-determined. Utilization stays
  flat at the income-optimum until total system profit turns negative, then drops
  to zero (build nothing wins). This is a step function, not an S-curve.
  The physics: higher load capex cannot incentivize more solar/battery because the
  solar+battery argmax is already at its income-optimum; load capex only shifts the
  go/no-go threshold.

LCOE-MIN (shown for comparison)
  Minimize (load_cost + solar×S + batt×B) / served_kwh. Here load capex IS in the
  cost numerator divided by the served-energy denominator, so a larger load_cost
  forces the optimizer to maximize served_kwh → more solar+battery → rising S-curve.
  LCOE minimization — no revenue signal required.

The two curves show the fundamental difference between the two frameworks on the same axis.

    x : annualized load capex  ($/kW·yr)  [bottom]  + raw $/kW twin  [top]
    y : optimal utilization (%)
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


def _params_profit(sweep: derived.LoadCapexSweep, grid) -> dict[str, str]:
    return {
        "Objective": "Profit maximization",
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load income": f"${sweep.income_per_kwh:.3g}/kWh",
        "Solar cost": f"${sweep.solar_cost_ann:.3g}/kW·yr  (${sweep.solar_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kW)",
        "Battery cost": f"${sweep.batt_cost_ann:.3g}/kWh·yr  (${sweep.batt_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kWh)",
        "Solar+batt amort": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Load amortization": f"{sweep.load_amortization_years:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }


def _params_lcoe(sweep: derived.LoadCapexSweepLCOE, grid) -> dict[str, str]:
    return {
        "Objective": "LCOE minimization",
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Solar cost": f"${sweep.solar_cost_ann:.3g}/kW·yr  (${sweep.solar_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kW)",
        "Battery cost": f"${sweep.batt_cost_ann:.3g}/kWh·yr  (${sweep.batt_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kWh)",
        "Solar+batt amort": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Load amortization": f"{sweep.load_amortization_years:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }


def _x_setup(ax, load_cost_ann: np.ndarray, load_amortization_years: float) -> None:
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v)))
    ax.set_xlim(load_cost_ann.min(), load_cost_ann.max())
    ax.set_xlabel(axis_label("load_cost_ann"))
    ax.set_ylim(0, 100)
    ax.set_ylabel(axis_label("utilization_pct"))
    ax.grid(True, which="both", linestyle="--", alpha=0.35)

    amort = load_amortization_years
    sec = ax.secondary_xaxis("top", functions=(lambda v: v * amort, lambda v: v / amort))
    sec.set_xlabel(f"Load capex  ($/kW, {amort:g}-yr amortization)")
    sec.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v)))


def draw_profit(ax, sweep: derived.LoadCapexSweep) -> None:
    """Step-function result: flat utilization, then cliff to zero when load capex
    exceeds hardware profit. Correct prediction of the profit-max framework."""
    ax.plot(sweep.load_cost_ann, sweep.utilization * 100.0,
            color="#e07b00", linewidth=2.4, zorder=3,
            label="Profit-max")
    ax.fill_between(sweep.load_cost_ann, sweep.utilization * 100.0,
                    color="#e07b00", alpha=0.12, zorder=2)
    _x_setup(ax, sweep.load_cost_ann, sweep.load_amortization_years)
    ax.set_title("Optimal utilization vs load capex  [profit-max]")


def draw_lcoe(ax, sweep: derived.LoadCapexSweepLCOE) -> None:
    """S-curve result: rising utilization driven by spreading load cost over more
    kWh. LCOE minimization — no income signal required."""
    ax.plot(sweep.load_cost_ann, sweep.utilization * 100.0,
            color="#2a9d8f", linewidth=2.4, zorder=3,
            label="LCOE-min")
    ax.fill_between(sweep.load_cost_ann, sweep.utilization * 100.0,
                    color="#2a9d8f", alpha=0.12, zorder=2)
    _x_setup(ax, sweep.load_cost_ann, sweep.load_amortization_years)
    ax.set_title("Optimal utilization vs load capex  [LCOE-min]")


def draw_comparison(ax, profit_sweep: derived.LoadCapexSweep,
                    lcoe_sweep: derived.LoadCapexSweepLCOE) -> None:
    """Both curves on the same axes for direct comparison."""
    ax.plot(profit_sweep.load_cost_ann, profit_sweep.utilization * 100.0,
            color="#e07b00", linewidth=2.4, zorder=3, label="Profit-max (our model)")
    ax.fill_between(profit_sweep.load_cost_ann, profit_sweep.utilization * 100.0,
                    color="#e07b00", alpha=0.10, zorder=2)
    ax.plot(lcoe_sweep.load_cost_ann, lcoe_sweep.utilization * 100.0,
            color="#2a9d8f", linewidth=2.4, zorder=3, label="LCOE-min")
    ax.fill_between(lcoe_sweep.load_cost_ann, lcoe_sweep.utilization * 100.0,
                    color="#2a9d8f", alpha=0.10, zorder=2)
    ax.legend(fontsize=9, framealpha=0.85)
    _x_setup(ax, profit_sweep.load_cost_ann, profit_sweep.load_amortization_years)
    ax.set_title("Optimal utilization vs load capex  [profit-max vs LCOE-min]")


def figures(profit_sweep: derived.LoadCapexSweep, lcoe_sweep: derived.LoadCapexSweepLCOE, grid):
    from viz import render

    suffix = common.param_suffix({
        "sol": f"{profit_sweep.solar_cost_ann:.3g}",
        "bat": f"{profit_sweep.batt_cost_ann:.3g}",
        "lamort": f"{profit_sweep.load_amortization_years:g}yr",
    })

    def profit_fig():
        fig, ax = render.new_figure(figsize=(10, 6))
        draw_profit(ax, profit_sweep)
        common.info(ax, fig, _params_profit(profit_sweep, grid), mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_UTIL_VS_LOAD_CAPEX / f"profit_max_{suffix}.png"

    def lcoe_fig():
        fig, ax = render.new_figure(figsize=(10, 6))
        draw_lcoe(ax, lcoe_sweep)
        common.info(ax, fig, _params_lcoe(lcoe_sweep, grid), mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_UTIL_VS_LOAD_CAPEX / f"lcoe_min_{suffix}.png"

    def comparison_fig():
        fig, ax = render.new_figure(figsize=(10, 6))
        draw_comparison(ax, profit_sweep, lcoe_sweep)
        # Combined params for the info box.
        params = {
            "Site": common.site_label(),
            "Capacity factor": f"{grid.capacity_factor:.0%}",
            "Solar cost": f"${profit_sweep.solar_cost_ann:.3g}/kW·yr",
            "Battery cost": f"${profit_sweep.batt_cost_ann:.3g}/kWh·yr",
            "Load income (profit-max)": f"${profit_sweep.income_per_kwh:.3g}/kWh",
            "Load amortization": f"{profit_sweep.load_amortization_years:g} yr",
            "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
        }
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_UTIL_VS_LOAD_CAPEX / f"comparison_{suffix}.png"

    return [
        ("util_vs_load_capex/profit_max", profit_fig),
        ("util_vs_load_capex/lcoe_min", lcoe_fig),
        ("util_vs_load_capex/comparison", comparison_fig),
    ]


if __name__ == "__main__":
    import time

    import config as cfg
    import derived
    from viz import render

    t0 = time.time()
    grid = derived.load_served_grid()
    lcsw = derived.load_capex_sweep(grid)
    lcsw_lcoe = derived.load_capex_sweep_lcoe(grid)
    plan = figures(lcsw, lcsw_lcoe, grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
