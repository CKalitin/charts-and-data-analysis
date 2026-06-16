"""Income profiles — 3-panel line charts sliced at fixed load capex values.

For each of several fixed load capex values ($/kW·yr annualized), sweeps over
load income ($/kWh) and shows three metrics:
  1. Profit-optimal utilization (%)
  2. Annual revenue & cost ($/yr)
  3. Profit margin = profit / revenue (%)

Each slice is recomputed fresh via derived.income_sweep() at the exact capex
value — no grid snapping from the load plane.
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

# Load capex slices to profile ($/kW·yr annualized).
_CAPEX_ANN_SLICES = [1.0, 10.0, 100.0, 1000.0]


def draw_slice(axes, sw: derived.IncomeSweep, capex_ann: float,
               xlim: tuple[float, float] = (0.001, 10.0)) -> None:
    """Fill three Axes with utilization / revenue+cost / margin for one income sweep."""
    ax_util, ax_profit, ax_margin = axes

    income = sw.income_per_kwh
    util = sw.utilization
    profit = sw.profit_per_yr

    served_kwh = util * cfg.LOAD_KW * 8760.0
    revenue = income * served_kwh
    build = profit > 0

    util_plot   = np.where(build, util * 100.0,        np.nan)
    cost_plot   = np.where(build, revenue - profit,    np.nan)
    revenue_plot = np.where(build, revenue,            np.nan)
    margin      = np.where(revenue > 0, profit / revenue * 100.0, np.nan)
    margin_plot = np.where(build & (margin > 0), margin, np.nan)

    # Restrict to visible x range so y-axes scale to visible data.
    vis = (income >= xlim[0]) & (income <= xlim[1])
    inc_v = income[vis]

    # ── panel 1: utilization ─────────────────────────────────────────────────
    ax_util.plot(inc_v, util_plot[vis], color="#4a90d9", linewidth=2.0)
    ax_util.set_ylabel("Utilization (%)")
    ax_util.set_ylim(0, 105)
    ax_util.set_title("Profit-optimal utilization")

    # ── panel 2: revenue + cost ───────────────────────────────────────────────
    ax_profit.fill_between(inc_v, revenue_plot[vis], cost_plot[vis],
                           color="#2ca25f", alpha=0.18)
    ax_profit.plot(inc_v, revenue_plot[vis], color="#2ca25f", linewidth=2.0, label="Revenue")
    ax_profit.plot(inc_v, cost_plot[vis],    color="#d0021b", linewidth=2.0, label="Cost",
                   linestyle="--")
    ax_profit.legend(fontsize=8, framealpha=0.85)
    ax_profit.set_ylabel("$/yr")
    ax_profit.set_ylim(bottom=0)
    ax_profit.set_title("Annual revenue & cost")
    ax_profit.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
    )

    # ── panel 3: margin ───────────────────────────────────────────────────────
    ax_margin.plot(inc_v, margin_plot[vis], color="#e07b00", linewidth=2.0)
    ax_margin.set_ylabel("Profit margin (%)")
    ax_margin.set_ylim(0, 105)
    ax_margin.set_title("Profit margin")

    for ax in axes:
        ax.set_xscale("log")
        ax.set_xlim(*xlim)
        common.dollar_log_axis(ax, "x")
        ax.set_xlabel(axis_label("income_per_kwh"))
        ax.grid(True, which="major", alpha=0.35)
        ax.grid(True, which="minor", alpha=0.12)
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=9.0, color="#888888", alpha=0.9)


def figures(plane: derived.LoadPlane, grid):
    from viz import render

    amort = plane.load_amortization_years
    params = {
        "Site":            common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load":            f"{cfg.LOAD_KW:g} kW constant",
        "Solar cost":      f"${plane.solar_cost_ann:.3g}/kW·yr",
        "Battery cost":    f"${plane.batt_cost_ann:.3g}/kWh·yr",
        "Load amort":      f"{amort:g} yr",
    }
    suffix = common.param_suffix({
        "sol":    f"{plane.solar_cost_ann:.3g}",
        "bat":    f"{plane.batt_cost_ann:.3g}",
        "lamort": f"{amort:g}yr",
    })

    # Precompute one income sweep per capex slice (exact values, no snapping).
    income_values = cfg.LOAD_PLANE_INCOME_SWEEP
    sweeps: dict[float, derived.IncomeSweep] = {}
    for capex_ann in _CAPEX_ANN_SLICES:
        sweeps[capex_ann] = derived.income_sweep(
            grid,
            income_values=income_values,
            solar_cost_ann=plane.solar_cost_ann,
            batt_cost_ann=plane.batt_cost_ann,
            load_cost_ann=capex_ann,
        )

    result = []

    for capex_ann in _CAPEX_ANN_SLICES:
        sw = sweeps[capex_ann]
        capex_raw = capex_ann * amort
        slug = f"{capex_ann:g}".replace(".", "p")
        slice_params = {**params, "Load capex": f"${capex_ann:g}/kW·yr  (${capex_raw:.0f}/kW)"}

        for xlim, xsuffix in [((0.001, 10.0), ""), ((0.001, 1.0), "_x1"), ((0.001, 0.1), "_x01")]:
            def make_fig(sw=sw, capex_ann=capex_ann, capex_raw=capex_raw, slug=slug,
                         slice_params=slice_params, xlim=xlim, xsuffix=xsuffix):
                fig = render.Figure(figsize=(17, 5), dpi=render.DPI)
                render.FigureCanvasAgg(fig)
                axes = fig.subplots(1, 3)

                draw_slice(axes, sw, capex_ann, xlim=xlim)

                fig.suptitle(
                    f"Load capex = ${capex_ann:g}/kW·yr  (${capex_raw:.0f}/kW, {amort:g}-yr amort)",
                    fontsize=13,
                )
                fig.subplots_adjust(wspace=0.45, top=0.9)
                common.info(axes[2], fig, slice_params, mode="on")

                out = cfg.OUT_INCOME_PROFILES / f"income_profiles_{slug}{xsuffix}_{suffix}.png"
                return fig, out

            result.append((f"income_profiles/{slug}{xsuffix}", make_fig))

    return result


if __name__ == "__main__":
    import time
    from viz import render

    t0 = time.time()
    g = derived.load_served_grid()
    lplane = derived.load_plane(g)
    plan = figures(lplane, g)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
