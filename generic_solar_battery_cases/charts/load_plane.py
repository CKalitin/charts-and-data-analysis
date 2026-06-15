"""Chart D — the load plane: optimal utilization and profit over (income × load capex).

Each cell re-optimizes the hardware build (kW solar + kWh battery) for that (income,
load capex) combination, with solar and battery costs held fixed. The three named load
cases (Terraform Electrolyzer, Colossus Data Center, NaOH Electrolyzer) are marked as
reference points.

    x : load capex  ($/kW raw)   [bottom]  + $/kW·yr annualized twin  [top]
    y : load income ($/kWh)      [log]
    color : optimal utilization (one figure) / optimal annual profit (the other)
"""

from __future__ import annotations

import matplotlib.ticker as mticker
import numpy as np

import config as cfg
import derived
from labels import axis_label

from . import common

# Scatter style for the named load cases.
_CASE_COLORS = ["#e63946", "#2a9d8f", "#f4a261"]
_CASE_MARKER = "*"
_CASE_SIZE = 180


def _scene_params(plane: derived.LoadPlane, grid) -> dict[str, str]:
    return {
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load": f"{cfg.LOAD_KW:g} kW constant",
        "Solar cost": f"${plane.solar_cost_ann:.3g}/kW·yr  (${plane.solar_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kW)",
        "Battery cost": f"${plane.batt_cost_ann:.3g}/kWh·yr  (${plane.batt_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kWh)",
        "Solar+batt amort": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Load amortization": f"{plane.load_amortization_years:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }


def _add_case_markers(ax, plane: derived.LoadPlane) -> None:
    """Scatter ★ for each named load case; label in the legend."""
    for (name, (income, capex_raw, _)), color in zip(
        cfg.LOAD_CASES.items(), _CASE_COLORS
    ):
        ax.scatter(
            [capex_raw], [income],
            s=_CASE_SIZE, marker=_CASE_MARKER, color=color,
            edgecolors="black", linewidths=0.7, zorder=6,
            label=f"{name}  (${income:.4g}/kWh, ${capex_raw:,.0f}/kW)",
        )
    ax.legend(loc="lower right", fontsize=8, framealpha=0.82)


def _axis_setup(ax, plane: derived.LoadPlane) -> None:
    """Log scales + dollar formatters on both axes + annualized twin on top."""
    common.dollar_log_axis(ax, "x")
    common.dollar_log_axis(ax, "y")
    ax.set_xlabel(axis_label("load_capex"))
    ax.set_ylabel(axis_label("income_per_kwh"))
    ax.set_xlim(plane.load_capex_raw.min(), plane.load_capex_raw.max())
    ax.set_ylim(plane.income_per_kwh.min(), plane.income_per_kwh.max())

    amort = plane.load_amortization_years
    sec = ax.secondary_xaxis(
        "top", functions=(lambda v: v / amort, lambda v: v * amort)
    )
    sec.set_xlabel(f"Load capex  ($/kW·yr, {amort:g}-yr amortization)")
    sec.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v)))


def draw_utilization(ax, plane: derived.LoadPlane, *, contours: bool = True) -> object:
    # Inline labels (NOT spine labels). The iso-util lines are *not* separated at
    # the left edge: at low load capex, utilization-vs-income is a near step
    # function (0 below breakeven, ~100% above), so every contour 10%..99% crosses
    # the left edge at almost the same (breakeven) income. side="left" therefore
    # collapses all their leftmost endpoints onto one point and stacks the labels
    # in the bottom-left corner. The contours DO fan out and separate along the
    # diagonal no-build frontier, which is exactly where inline clabel places them.
    mesh = common.draw_heatmap(
        ax, plane.load_capex_raw, plane.income_per_kwh, plane.utilization * 100.0,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="Optimal utilization vs load economics",
        vmin=0, vmax=100,
        contour_levels=[v * 100 for v in common.UTIL_CONTOURS] if contours else None,
        contour_fmt=lambda v: f"{v:.3g}%" if contours else None,
        label_side="inline",
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane)
    return mesh


def draw_profit(ax, plane: derived.LoadPlane) -> object:
    # filter_stubs=True: the highest profit levels exist only in a small high-income /
    # low-capex corner, producing short stub lines that look like truncated fragments.
    mesh = common.draw_heatmap(
        ax, plane.load_capex_raw, plane.income_per_kwh, plane.profit_per_yr,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="Optimal net value vs load economics",
        contour_levels=common.nice_levels(plane.profit_per_yr),
        contour_color="white",
        contour_fmt=common._dollar_fmt,
        filter_stubs=True,
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane)
    return mesh


def figures(plane: derived.LoadPlane, grid):
    from viz import render

    params = _scene_params(plane, grid)
    suffix = common.param_suffix({
        "sol": f"{plane.solar_cost_ann:.3g}",
        "bat": f"{plane.batt_cost_ann:.3g}",
        "lamort": f"{plane.load_amortization_years:g}yr",
    })

    def util_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization(ax, plane)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_LOAD_PLANE / f"utilization_{suffix}.png"

    def util_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization(ax, plane, contours=False)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_LOAD_PLANE / f"utilization_{suffix}_nocontours.png"

    def profit_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit(ax, plane)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label(axis_label("profit_per_yr"))
        common.dollar_colorbar(cbar)
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_LOAD_PLANE / f"profit_{suffix}.png"

    return [
        ("load_plane/utilization", util_fig),
        ("load_plane/utilization_nocontours", util_no_contours_fig),
        ("load_plane/profit", profit_fig),
    ]
