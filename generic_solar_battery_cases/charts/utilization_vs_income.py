"""Chart B — optimal utilization vs load income ($/kWh).

Optimal utilization vs load income — the profit-maximizing build across the
income sweep. Load capex ($/kW) cannot define "optimal" because it says nothing
about what delivered energy is worth; load *income* ($/kWh) is the correct
independent variable. Solar and battery costs are held fixed (info box).

    x : load income  $/kWh delivered  (log)
    y : optimal utilization (%)        — utilization of the profit-max build
"""

from __future__ import annotations

import numpy as np

import config as cfg
import derived
from labels import axis_label

from . import common


def _params(sweep: derived.IncomeSweep, grid) -> dict[str, str]:
    return {
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load": f"{cfg.LOAD_KW:g} kW constant",
        "Solar cost": f"${sweep.solar_cost_ann:.3g}/kW·yr  (${sweep.solar_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kW)",
        "Battery cost": f"${sweep.batt_cost_ann:.3g}/kWh·yr  (${sweep.batt_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kWh)",
        "Amortization": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }


def draw(ax, sweep: derived.IncomeSweep) -> None:
    ax.plot(sweep.income_per_kwh, sweep.utilization * 100.0,
            color="#7b2fbe", linewidth=2.4, zorder=3)
    ax.fill_between(sweep.income_per_kwh, sweep.utilization * 100.0,
                    color="#7b2fbe", alpha=0.12, zorder=2)

    ax.set_xscale("log")
    import matplotlib.ticker as mticker
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"${v:g}" if v >= 1 else f"${v:.3g}"))
    ax.set_xlim(sweep.income_per_kwh.min(), sweep.income_per_kwh.max())
    ax.set_ylim(0, 100)
    ax.set_xlabel(axis_label("income_per_kwh"))
    ax.set_ylabel(axis_label("utilization_pct"))
    ax.set_title("Optimal utilization vs load income")
    ax.grid(True, which="both", linestyle="--", alpha=0.35)


def figures(sweep: derived.IncomeSweep, grid):
    from viz import render

    suffix = common.param_suffix({
        "sol": f"{sweep.solar_cost_ann:.3g}", "bat": f"{sweep.batt_cost_ann:.3g}",
        "amort": f"{cfg.AMORTIZATION_YEARS:g}",
    })

    def fig_fn():
        fig, ax = render.new_figure(figsize=(10, 6))
        draw(ax, sweep)
        common.info(ax, fig, _params(sweep, grid), mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_UTIL_VS_INCOME / f"util_vs_income_{suffix}.png"

    return [("utilization_vs_income", fig_fn)]
