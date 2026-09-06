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

import sys
from pathlib import Path

if not __package__:  # running as a script — add project root to path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import matplotlib.ticker as mticker
import numpy as np

import config as cfg
import derived
from labels import axis_label

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]

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


def _add_case_markers(
    ax, plane: derived.LoadPlane,
    value_data: np.ndarray | None = None,
    value_fmt=None,
) -> None:
    """Scatter ★ for each named load case; optional heatmap-value label near each star.

    value_data: (nI, nCl) array matching the plotted heatmap (NaN = no-build).
    value_fmt:  callable float -> str, e.g. lambda v: f"{v:.0f}%"
    """
    amort = plane.load_amortization_years
    _outline = [pe.withStroke(linewidth=2, foreground="black")]
    for (name, (income, capex_raw, case_amort)), color in zip(
        cfg.LOAD_CASES.items(), _CASE_COLORS
    ):
        capex_ann = capex_raw / amort
        ax.scatter(
            [capex_ann], [income],
            s=_CASE_SIZE, marker=_CASE_MARKER, color=color,
            edgecolors="black", linewidths=0.7, zorder=6,
            label=f"{name}  (${income:.4g}/kWh, ${capex_ann:.0f}/kW·yr)",
        )
        if value_data is not None and value_fmt is not None:
            i = int(np.argmin(np.abs(plane.income_per_kwh - income)))
            j = int(np.argmin(np.abs(plane.load_cost_ann - capex_ann)))
            val = float(value_data[i, j])
            if np.isfinite(val):
                ax.annotate(
                    value_fmt(val),
                    xy=(capex_ann, income),
                    xytext=(6, 6), textcoords="offset points",
                    fontsize=8, fontweight="bold", color="white",
                    zorder=8, path_effects=_outline,
                )
    ax.legend(loc="lower right", fontsize=8, framealpha=0.82)


def _axis_setup(ax, plane: derived.LoadPlane) -> None:
    """Log scales + dollar formatters on both axes.

    Primary (bottom) x-axis: annualized load capex $/kW·yr — the quantity that
    enters every calculation. Secondary (top): raw capex $/kW for intuition.
    """
    common.dollar_log_axis(ax, "x")
    common.dollar_log_axis(ax, "y")
    ax.set_xlabel(axis_label("load_cost_ann"))   # $/kW·yr on bottom
    ax.set_ylabel(axis_label("income_per_kwh"))
    ax.set_xlim(plane.load_cost_ann.min(), plane.load_cost_ann.max())
    ax.set_ylim(plane.income_per_kwh.min(), plane.income_per_kwh.max())

    amort = plane.load_amortization_years
    sec = ax.secondary_xaxis(
        "top", functions=(lambda v: v * amort, lambda v: v / amort)
    )
    sec.set_xlabel(f"Load capex  ($/kW, {amort:g}-yr amortization)")
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
        ax, plane.load_cost_ann, plane.income_per_kwh, plane.utilization * 100.0,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="Profit-optimal utilization vs load economics",
        vmin=0, vmax=100,
        contour_levels=[v * 100 for v in common.UTIL_CONTOURS] if contours else None,
        contour_fmt=lambda v: f"{v:.3g}%" if contours else None,
        label_side="inline",
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, plane.utilization * 100.0, lambda v: f"{v:.0f}%")
    return mesh


def draw_utilization_lcoe(ax, plane: derived.LoadPlane, *, contours: bool = True) -> object:
    """Utilization at the LCOE-minimizing (S, B) build over the (income × load capex) plane.

    LCOE = (load_cost × L + solar_cost × S + batt_cost × B) / served_kwh does not
    include income, so the optimal (S, B) depends only on load capex — not on income.
    This produces vertical stripes: each column (load capex value) has one utilization
    that repeats across all income levels.
    """
    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, plane.lcoe_utilization * 100.0,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="LCOE-optimal utilization vs load economics",
        vmin=0, vmax=100,
        contour_levels=[v * 100 for v in common.UTIL_CONTOURS] if contours else None,
        contour_fmt=(lambda v: f"{v:.3g}%") if contours else None,
        label_side="inline",
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, plane.lcoe_utilization * 100.0, lambda v: f"{v:.0f}%")
    return mesh


def draw_utilization_lvoe(
    ax, plane: derived.LoadPlane, *, contours: bool = True, mask_nobuild: bool = False
) -> object:
    """Utilization at the LVOE-maximizing (S, B) build over the (income × load capex) plane.

    LVOE = income − LCOE.  For a fixed (income, load_capex) cell, income is a constant,
    so argmax(LVOE) ≡ argmin(LCOE) — the same build chosen by LCOE minimization.
    Utilization therefore shows vertical stripes (income-independent), identical to the
    LCOE-optimal utilization chart, but framed in LVOE terms for consistency with the
    LVOE value chart.

    mask_nobuild: if True, cells where LVOE ≤ 0 are masked gray (matching the LVOE
    value heatmap's dark zone), so only economically viable cells show utilization.
    """
    util = plane.lcoe_utilization * 100.0
    if mask_nobuild:
        util = np.where(plane.lvoe > 0, util, np.nan)

    cmap_obj = None
    if mask_nobuild:
        cmap_obj = matplotlib.colormaps["plasma"].copy()
        cmap_obj.set_bad("#2A2A2A", alpha=1.0)

    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, util,
        xlabel=axis_label("load_cost_ann"), ylabel=axis_label("income_per_kwh"),
        title="LVOE-optimal utilization vs load economics",
        vmin=0, vmax=100,
        cmap=cmap_obj,
        contour_levels=[v * 100 for v in common.UTIL_CONTOURS] if contours else None,
        contour_fmt=(lambda v: f"{v:.3g}%") if contours else None,
        label_side="inline",
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, util, lambda v: f"{v:.0f}%")
    return mesh


def draw_lvoe(ax, plane: derived.LoadPlane, *, contours: bool = True) -> object:
    """Levelized Value of Energy (LVOE) = income − min_LCOE(load_capex)  [$/kWh].

    Net value per kWh delivered — the energy-normalized counterpart to LCOE.
    LCOE asks "what does each kWh cost?"; LVOE answers "what is each kWh worth
    after paying for it?" Both axes of the plane contribute:
      - income (y): the revenue per kWh
      - min_LCOE (function of x): the minimum achievable cost per kWh

    LVOE > 0 → profitable; diagonal boundary is where income = min_LCOE.
    The no-build zone (LVOE ≤ 0) is masked gray.
    """
    lvoe = plane.lvoe.copy()
    lvoe_plot = np.where(lvoe > 0, lvoe, np.nan)

    pos = lvoe_plot[np.isfinite(lvoe_plot)]
    norm = (mcolors.LogNorm(vmin=float(pos.min()), vmax=float(pos.max()))
            if pos.size else None)

    cmap_obj = matplotlib.colormaps[common.HEAT_CMAP].copy()
    cmap_obj.set_bad("#2A2A2A", alpha=1.0)

    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, lvoe_plot,
        xlabel=axis_label("load_cost_ann"), ylabel=axis_label("income_per_kwh"),
        title="Levelized Value of Energy  (income − min LCOE)",
        cmap=cmap_obj,
        norm=norm,
        contour_levels=common.log_nice_levels(lvoe_plot) if contours else None,
        contour_color="white",
        contour_fmt=(lambda v: common._dollar_fmt(v) + "/kWh") if contours else None,
        filter_stubs=True,
    )
    _axis_setup(ax, plane)
    lvoe_plot_data = np.where(plane.lvoe > 0, plane.lvoe, np.nan)
    _add_case_markers(ax, plane, lvoe_plot_data,
                      lambda v: common._dollar_fmt(v) + "/kWh")
    return mesh


def draw_profit_margin(ax, plane: derived.LoadPlane, *, contours: bool = True) -> object:
    """Profit margin = profit / revenue = (revenue − cost) / revenue  [%].

    Revenue = income_per_kwh × served_kwh; cost = load + solar + battery annualized.
    Uses the profit-optimal (S, B) build at each cell (same as draw_profit).
    No-build zone (margin ≤ 0) is masked gray.
    """
    served_kwh = plane.utilization * cfg.LOAD_KW * 8760.0  # (nI, nCl)
    revenue = plane.income_per_kwh[:, None] * served_kwh   # (nI, nCl)
    margin = np.where(revenue > 0, plane.profit_per_yr / revenue * 100.0, np.nan)
    margin = np.where(margin > 0, margin, np.nan)

    cmap_obj = matplotlib.colormaps[common.HEAT_CMAP].copy()
    cmap_obj.set_bad("#2A2A2A", alpha=1.0)

    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, margin,
        xlabel=axis_label("load_cost_ann"), ylabel=axis_label("income_per_kwh"),
        title="Profit margin vs load economics",
        vmin=0, vmax=100,
        cmap=cmap_obj,
        contour_levels=[10, 20, 30, 40, 50, 60, 70, 80, 90] if contours else None,
        contour_color="white",
        contour_fmt=(lambda v: f"{v:.0f}%") if contours else None,
        filter_stubs=True,
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, margin, lambda v: f"{v:.0f}%")
    ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
    return mesh


def draw_profit(ax, plane: derived.LoadPlane, *, contours: bool = True) -> object:
    """Profit heatmap with log color scale.

    The no-build zone (profit = 0) is masked and rendered gray; the log norm
    makes the large dynamic range across the build zone legible. Contour levels
    are at 1/2/5 × 10^n so they align with the log color scale.
    """
    profit_plot = np.where(plane.profit_per_yr > 0, plane.profit_per_yr, np.nan)

    pos = profit_plot[np.isfinite(profit_plot)]
    norm = (mcolors.LogNorm(vmin=float(pos.min()), vmax=float(pos.max()))
            if pos.size else None)

    cmap_obj = matplotlib.colormaps[common.HEAT_CMAP].copy()
    cmap_obj.set_bad("#2A2A2A", alpha=1.0)  # gray for no-build zone

    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, profit_plot,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="Profit-optimal net value vs load economics",
        cmap=cmap_obj,
        norm=norm,
        contour_levels=common.log_nice_levels(profit_plot) if contours else None,
        contour_color="white",
        contour_fmt=common._dollar_fmt if contours else None,
        filter_stubs=True,
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, profit_plot, common._dollar_fmt)
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
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"utilization_{suffix}.png"

    def util_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization(ax, plane, contours=False)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        common.info(ax, fig, params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"utilization_{suffix}_nocontours.png"

    def profit_margin_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit_margin(ax, plane)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label("Profit margin  (%)")
        common.info(ax, fig, params, mode="on")
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"profit_margin_{suffix}.png"

    def profit_margin_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit_margin(ax, plane, contours=False)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label("Profit margin  (%)")
        common.info(ax, fig, params, mode="on")
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"profit_margin_{suffix}_nocontours.png"

    def profit_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit(ax, plane)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label(axis_label("profit_per_yr"))
        # FuncFormatter overrides LogNorm's default tick labels (which would render
        # as "$\mathdefault{10^2}$" even with text.parse_math=False).
        cbar.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
        )
        common.info(ax, fig, params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"profit_{suffix}.png"

    def profit_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit(ax, plane, contours=False)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label(axis_label("profit_per_yr"))
        cbar.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
        )
        common.info(ax, fig, params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"profit_{suffix}_nocontours.png"

    def util_lcoe_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization_lcoe(ax, plane)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        lcoe_params = {**params, "Objective": "LCOE minimization"}
        common.info(ax, fig, lcoe_params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"utilization_lcoe_{suffix}.png"

    def util_lcoe_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization_lcoe(ax, plane, contours=False)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        lcoe_params = {**params, "Objective": "LCOE minimization"}
        common.info(ax, fig, lcoe_params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"utilization_lcoe_{suffix}_nocontours.png"

    def util_lvoe_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization_lvoe(ax, plane)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        lvoe_params = {**params, "Objective": "LVOE maximization (≡ LCOE minimization)"}
        common.info(ax, fig, lvoe_params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"utilization_lvoe_{suffix}.png"

    def util_lvoe_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization_lvoe(ax, plane, contours=False)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        lvoe_params = {**params, "Objective": "LVOE maximization (≡ LCOE minimization)"}
        common.info(ax, fig, lvoe_params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"utilization_lvoe_{suffix}_nocontours.png"

    def util_lvoe_masked_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization_lvoe(ax, plane, mask_nobuild=True)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        lvoe_params = {**params, "Objective": "LVOE maximization (≡ LCOE minimization)"}
        common.info(ax, fig, lvoe_params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"utilization_lvoe_{suffix}_masked.png"

    def util_lvoe_masked_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization_lvoe(ax, plane, mask_nobuild=True, contours=False)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        lvoe_params = {**params, "Objective": "LVOE maximization (≡ LCOE minimization)"}
        common.info(ax, fig, lvoe_params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"utilization_lvoe_{suffix}_masked_nocontours.png"

    def lvoe_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_lvoe(ax, plane)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label("Levelized Value of Energy  ($/kWh)")
        cbar.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
        )
        common.info(ax, fig, params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"lvoe_{suffix}.png"

    def lvoe_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_lvoe(ax, plane, contours=False)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label("Levelized Value of Energy  ($/kWh)")
        cbar.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
        )
        common.info(ax, fig, params, mode="on")
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_LOAD_PLANE_CONSTANT_LOAD / f"lvoe_{suffix}_nocontours.png"

    return [
        ("load_plane/constant_load/profit_margin", profit_margin_fig),
        ("load_plane/constant_load/profit_margin_nocontours", profit_margin_no_contours_fig),
        ("load_plane/constant_load/utilization", util_fig),
        ("load_plane/constant_load/utilization_nocontours", util_no_contours_fig),
        ("load_plane/constant_load/profit", profit_fig),
        ("load_plane/constant_load/profit_nocontours", profit_no_contours_fig),
        ("load_plane/constant_load/utilization_lcoe", util_lcoe_fig),
        ("load_plane/constant_load/utilization_lcoe_nocontours", util_lcoe_no_contours_fig),
        ("load_plane/constant_load/lvoe", lvoe_fig),
        ("load_plane/constant_load/lvoe_nocontours", lvoe_no_contours_fig),
        ("load_plane/constant_load/utilization_lvoe", util_lvoe_fig),
        ("load_plane/constant_load/utilization_lvoe_nocontours", util_lvoe_no_contours_fig),
        ("load_plane/constant_load/utilization_lvoe_masked", util_lvoe_masked_fig),
        ("load_plane/constant_load/utilization_lvoe_masked_nocontours", util_lvoe_masked_no_contours_fig),
    ]


# --------------------------------------------------------------------------- #
# Constant-budget variant — a fixed $/yr budget split three ways among
# load/solar/battery (jointly optimized), instead of a fixed 1 kW load with
# only solar/battery optimized. See derived.LoadPlaneBudget.
# --------------------------------------------------------------------------- #
def _scene_params_budget(plane: derived.LoadPlaneBudget, grid) -> dict[str, str]:
    return {
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Total budget": f"{common._dollar_fmt(plane.total_budget)}/yr  (load+solar+battery, jointly optimized)",
        "Solar cost": f"${plane.solar_cost_ann:.3g}/kW·yr  (${plane.solar_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kW)",
        "Battery cost": f"${plane.batt_cost_ann:.3g}/kWh·yr  (${plane.batt_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kWh)",
        "Solar+batt amort": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Load amortization": f"{plane.load_amortization_years:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }


def draw_utilization_budget(ax, plane: derived.LoadPlaneBudget, *, contours: bool = True) -> object:
    """Utilization at the budget-optimal (load, solar, battery) split.

    Each column (load capex value) has ONE optimal split, so utilization is
    constant across income until that column's breakeven, then drops to 0% —
    vertical stripes with a horizontal no-build cutoff per column, the mirror
    image of LoadPlane's income-driven cutoff shape.
    """
    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, plane.utilization * 100.0,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="Budget-optimal utilization vs load economics (fixed $/yr budget)",
        vmin=0, vmax=100,
        contour_levels=[v * 100 for v in common.UTIL_CONTOURS] if contours else None,
        contour_fmt=(lambda v: f"{v:.3g}%") if contours else None,
        label_side="inline",
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, plane.utilization * 100.0, lambda v: f"{v:.0f}%")
    return mesh


def draw_load_kw_budget(ax, plane: derived.LoadPlaneBudget, *, contours: bool = True) -> object:
    """Load size (kW) the budget buys at the optimal split — 0 (masked gray)
    below breakeven, where "build nothing" wins. Depends only on load capex
    (the column), not income, so this is pure vertical bands by construction —
    a direct visual of load_kw = f(budget, load_capex, solar/battery cost)."""
    load_kw_2d = np.where(plane.utilization > 0, plane.load_kw[None, :], np.nan)

    cmap_obj = matplotlib.colormaps[common.HEAT_CMAP].copy()
    cmap_obj.set_bad("#2A2A2A", alpha=1.0)
    pos = load_kw_2d[np.isfinite(load_kw_2d)]
    norm = (mcolors.LogNorm(vmin=float(pos.min()), vmax=float(pos.max()))
            if pos.size else None)

    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, load_kw_2d,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="Budget-optimal load size vs load economics (fixed $/yr budget)",
        cmap=cmap_obj, norm=norm,
        contour_levels=common.log_nice_levels(load_kw_2d) if contours else None,
        contour_color="white",
        contour_fmt=(lambda v: f"{v:,.0f} kW") if contours else None,
        filter_stubs=True,
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, load_kw_2d, lambda v: f"{v:,.0f} kW")
    return mesh


def draw_profit_budget(ax, plane: derived.LoadPlaneBudget, *, contours: bool = True) -> object:
    profit_plot = np.where(plane.profit_per_yr > 0, plane.profit_per_yr, np.nan)

    pos = profit_plot[np.isfinite(profit_plot)]
    norm = (mcolors.LogNorm(vmin=float(pos.min()), vmax=float(pos.max()))
            if pos.size else None)

    cmap_obj = matplotlib.colormaps[common.HEAT_CMAP].copy()
    cmap_obj.set_bad("#2A2A2A", alpha=1.0)

    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, profit_plot,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="Budget-optimal profit vs load economics (fixed $/yr budget)",
        cmap=cmap_obj, norm=norm,
        contour_levels=common.log_nice_levels(profit_plot) if contours else None,
        contour_color="white",
        contour_fmt=common._dollar_fmt if contours else None,
        filter_stubs=True,
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, profit_plot, common._dollar_fmt)
    return mesh


def draw_profit_margin_budget(ax, plane: derived.LoadPlaneBudget, *, contours: bool = True) -> object:
    """Profit margin = profit / revenue, at the budget-optimal split."""
    revenue = plane.income_per_kwh[:, None] * plane.served_kwh[None, :]   # (nI, nCl)
    with np.errstate(divide="ignore", invalid="ignore"):
        margin = np.where(revenue > 0, plane.profit_per_yr / revenue * 100.0, np.nan)
    margin = np.where(margin > 0, margin, np.nan)

    cmap_obj = matplotlib.colormaps[common.HEAT_CMAP].copy()
    cmap_obj.set_bad("#2A2A2A", alpha=1.0)

    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, margin,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="Budget-optimal profit margin vs load economics (fixed $/yr budget)",
        vmin=0, vmax=100,
        cmap=cmap_obj,
        contour_levels=[10, 20, 30, 40, 50, 60, 70, 80, 90] if contours else None,
        contour_color="white",
        contour_fmt=(lambda v: f"{v:.0f}%") if contours else None,
        filter_stubs=True,
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, margin, lambda v: f"{v:.0f}%")
    ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
    return mesh


def draw_lvoe_budget(ax, plane: derived.LoadPlaneBudget, *, contours: bool = True) -> object:
    """LVOE = income - LCOE at the budget-optimal split (= profit_per_yr / served_kwh,
    since cost is pinned at total_budget for every split)."""
    lvoe_plot = np.where(plane.lvoe > 0, plane.lvoe, np.nan)

    pos = lvoe_plot[np.isfinite(lvoe_plot)]
    norm = (mcolors.LogNorm(vmin=float(pos.min()), vmax=float(pos.max()))
            if pos.size else None)

    cmap_obj = matplotlib.colormaps[common.HEAT_CMAP].copy()
    cmap_obj.set_bad("#2A2A2A", alpha=1.0)

    mesh = common.draw_heatmap(
        ax, plane.load_cost_ann, plane.income_per_kwh, lvoe_plot,
        xlabel=axis_label("load_capex"), ylabel=axis_label("income_per_kwh"),
        title="Budget-optimal LVOE vs load economics (fixed $/yr budget)",
        cmap=cmap_obj, norm=norm,
        contour_levels=common.log_nice_levels(lvoe_plot) if contours else None,
        contour_color="white",
        contour_fmt=(lambda v: common._dollar_fmt(v) + "/kWh") if contours else None,
        filter_stubs=True,
    )
    _axis_setup(ax, plane)
    _add_case_markers(ax, plane, lvoe_plot, lambda v: common._dollar_fmt(v) + "/kWh")
    return mesh


def figures_budget(plane: derived.LoadPlaneBudget, grid):
    from viz import render

    params = _scene_params_budget(plane, grid)
    suffix = common.param_suffix({
        "budget": f"{plane.total_budget:.0f}",
        "sol": f"{plane.solar_cost_ann:.3g}",
        "bat": f"{plane.batt_cost_ann:.3g}",
        "lamort": f"{plane.load_amortization_years:g}yr",
    })
    out_dir = cfg.OUT_LOAD_PLANE_CONSTANT_BUDGET

    def util_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization_budget(ax, plane)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, out_dir / f"utilization_{suffix}.png"

    def util_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization_budget(ax, plane, contours=False)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, out_dir / f"utilization_{suffix}_nocontours.png"

    def load_kw_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_load_kw_budget(ax, plane)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label("Load size  (kW)")
        # FuncFormatter overrides LogNorm's default tick labels (which would render
        # as "$\mathdefault{10^3}$" even with text.parse_math=False).
        cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, out_dir / f"load_kw_{suffix}.png"

    def load_kw_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_load_kw_budget(ax, plane, contours=False)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label("Load size  (kW)")
        cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, out_dir / f"load_kw_{suffix}_nocontours.png"

    def profit_margin_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit_margin_budget(ax, plane)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label("Profit margin  (%)")
        common.info(ax, fig, params, mode="on")
        return fig, out_dir / f"profit_margin_{suffix}.png"

    def profit_margin_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit_margin_budget(ax, plane, contours=False)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label("Profit margin  (%)")
        common.info(ax, fig, params, mode="on")
        return fig, out_dir / f"profit_margin_{suffix}_nocontours.png"

    def profit_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit_budget(ax, plane)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label(axis_label("profit_per_yr"))
        cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v)))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, out_dir / f"profit_{suffix}.png"

    def profit_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit_budget(ax, plane, contours=False)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label(axis_label("profit_per_yr"))
        cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v)))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, out_dir / f"profit_{suffix}_nocontours.png"

    def lvoe_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_lvoe_budget(ax, plane)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label("Levelized Value of Energy  ($/kWh)")
        cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v)))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, out_dir / f"lvoe_{suffix}.png"

    def lvoe_no_contours_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_lvoe_budget(ax, plane, contours=False)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label("Levelized Value of Energy  ($/kWh)")
        cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v)))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, out_dir / f"lvoe_{suffix}_nocontours.png"

    return [
        ("load_plane/constant_budget/utilization", util_fig),
        ("load_plane/constant_budget/utilization_nocontours", util_no_contours_fig),
        ("load_plane/constant_budget/load_kw", load_kw_fig),
        ("load_plane/constant_budget/load_kw_nocontours", load_kw_no_contours_fig),
        ("load_plane/constant_budget/profit_margin", profit_margin_fig),
        ("load_plane/constant_budget/profit_margin_nocontours", profit_margin_no_contours_fig),
        ("load_plane/constant_budget/profit", profit_fig),
        ("load_plane/constant_budget/profit_nocontours", profit_no_contours_fig),
        ("load_plane/constant_budget/lvoe", lvoe_fig),
        ("load_plane/constant_budget/lvoe_nocontours", lvoe_no_contours_fig),
    ]


if __name__ == "__main__":
    import time
    from viz import render

    t0 = time.time()
    grid = derived.load_served_grid()
    lplane = derived.load_plane(grid)
    lplane_budget = derived.load_plane_budget(grid)
    plan = figures(lplane, grid) + figures_budget(lplane_budget, grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
