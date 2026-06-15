"""Chart A — the cost plane.

Two heatmaps over the component-cost plane, at a FIXED load income; every cell
re-optimizes the build (profit-max over the kW×kWh grid):

    x : battery cost  $/(kWh·yr)   (log)   + capex twin on top
    y : solar cost    $/(kW·yr)    (log)   + capex twin on right
    color : optimal utilization (one figure) / optimal annual profit (the other)

Cheap hardware (lower-left) → it pays to overbuild → high utilization & profit.
"""

from __future__ import annotations

import config as cfg
import derived
from labels import axis_label

from . import common


def _scene_params(plane: derived.CostPlane, grid) -> dict[str, str]:
    return {
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load": f"{cfg.LOAD_KW:g} kW constant",
        "Load income": f"${plane.income_per_kwh:.3g}/kWh",
        "Amortization": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }


def draw_utilization(ax, plane: derived.CostPlane, twins: bool = True):
    # Inline labels (not side="left"): the left margin already holds the y-axis
    # dollar tick labels, so spine labels parked there collide with them. The
    # iso-util lines are L-shaped (flat top, steep right knee) and fan apart along
    # their flat runs, which is exactly where inline clabel places each label.
    mesh = common.draw_heatmap(
        ax, plane.batt_cost_ann, plane.solar_cost_ann, plane.utilization * 100.0,
        xlabel=axis_label("batt_cost_ann"), ylabel=axis_label("solar_cost_ann"),
        title="Optimal utilization vs component cost",
        vmin=0, vmax=100,
        contour_levels=[v * 100 for v in common.UTIL_CONTOURS],
        contour_fmt=lambda v: f"{v:.3g}%",
    )
    common.dollar_log_axis(ax, "x")
    common.dollar_log_axis(ax, "y")
    if twins:
        common.add_capex_twin(ax, "x")
        common.add_capex_twin(ax, "y")
    return mesh


def draw_profit(ax, plane: derived.CostPlane, twins: bool = True):
    profit = plane.profit_per_yr
    mesh = common.draw_heatmap(
        ax, plane.batt_cost_ann, plane.solar_cost_ann, profit,
        xlabel=axis_label("batt_cost_ann"), ylabel=axis_label("solar_cost_ann"),
        title="Optimal profit vs component cost",
        contour_levels=common.nice_levels(profit), contour_color="white",
        contour_fmt=lambda v: common._dollar_fmt(v),
    )
    common.dollar_log_axis(ax, "x")
    common.dollar_log_axis(ax, "y")
    if twins:
        common.add_capex_twin(ax, "x")
        common.add_capex_twin(ax, "y")
    return mesh


# --------------------------------------------------------------------------- #
# LCOE-min variants (Chart A)
# --------------------------------------------------------------------------- #
def _scene_params_lcoe(plane: derived.CostPlaneLCOE, grid) -> dict[str, str]:
    return {
        "Objective": "LCOE minimization",
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load": f"{cfg.LOAD_KW:g} kW constant",
        "Load capex (fixed)": f"${plane.load_cost_ann:.3g}/kW·yr",
        "Amortization": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }


def draw_utilization_lcoe(ax, plane: derived.CostPlaneLCOE, twins: bool = True):
    """LCOE-optimal utilization over the (solar, battery) cost plane.

    Without load capex the result is intentionally flat: LCOE = cs·S / served(S,B)
    and when gen < load always, served ≈ CF·S·8760, so LCOE ≈ cs/(CF·8760) —
    independent of S. The argmin picks the minimum-viable build (≈ CF utilisation)
    regardless of cost. With non-zero load capex the chart shows interesting
    variation because load cost forces maximising served_kwh.
    """
    import numpy as np

    util_pct = plane.utilization * 100.0
    u_min, u_max = float(np.nanmin(util_pct)), float(np.nanmax(util_pct))
    flat = (u_max - u_min) < 5.0  # less than 5 pp variation → auto-range

    mesh = common.draw_heatmap(
        ax, plane.batt_cost_ann, plane.solar_cost_ann, util_pct,
        xlabel=axis_label("batt_cost_ann"), ylabel=axis_label("solar_cost_ann"),
        title="LCOE-optimal utilization vs component cost",
        vmin=None if flat else 0,
        vmax=None if flat else 100,
        contour_levels=common.nice_levels(util_pct) if flat
                       else [v * 100 for v in common.UTIL_CONTOURS],
        contour_fmt=lambda v: f"{v:.3g}%",
    )
    common.dollar_log_axis(ax, "x")
    common.dollar_log_axis(ax, "y")
    if twins:
        common.add_capex_twin(ax, "x")
        common.add_capex_twin(ax, "y")
    if flat:
        ax.text(0.5, 0.04,
                f"Flat surface ({u_min:.1f}–{u_max:.1f}%): "
                "without load capex LCOE-min always picks the smallest viable build\n"
                "(util ≈ capacity factor). Add non-zero load capex to see variation.",
                transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5,
                color="white",
                bbox=dict(boxstyle="round,pad=0.3", fc="black", ec="none", alpha=0.55))
    return mesh


def draw_lcoe_value(ax, plane: derived.CostPlaneLCOE, twins: bool = True):
    """Minimum achievable LCOE ($/kWh) over the (solar, battery) cost plane."""
    import matplotlib.colors as mcolors
    import matplotlib.ticker as mticker
    from labels import axis_label as al

    lcoe = plane.lcoe
    mesh = common.draw_heatmap(
        ax, plane.batt_cost_ann, plane.solar_cost_ann, lcoe,
        xlabel=axis_label("batt_cost_ann"), ylabel=axis_label("solar_cost_ann"),
        title="Minimum LCOE vs component cost",
        cmap="viridis_r",
        contour_levels=common.nice_levels(lcoe),
        contour_color="white",
        contour_fmt=lambda v: common._dollar_fmt(v),
        filter_stubs=True,
    )
    common.dollar_log_axis(ax, "x")
    common.dollar_log_axis(ax, "y")
    if twins:
        common.add_capex_twin(ax, "x")
        common.add_capex_twin(ax, "y")
    return mesh


# --------------------------------------------------------------------------- #
# Figure builders
# --------------------------------------------------------------------------- #
def figures(plane: derived.CostPlane, grid):
    """Yield (name, build_fn) pairs; build_fn(render_module) -> (fig, path)."""
    from viz import render

    params = _scene_params(plane, grid)
    suffix = common.param_suffix({"inc": f"{plane.income_per_kwh:.3g}",
                                  "amort": f"{cfg.AMORTIZATION_YEARS:g}"})

    def util_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization(ax, plane)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_COST_PLANE / f"utilization_{suffix}.png"

    def profit_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit(ax, plane)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label(axis_label("profit_per_yr"))
        common.dollar_colorbar(cbar)
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_COST_PLANE / f"profit_{suffix}.png"

    return [("cost_plane/utilization", util_fig), ("cost_plane/profit", profit_fig)]


def figures_lcoe(plane: derived.CostPlaneLCOE, grid):
    from viz import render

    params = _scene_params_lcoe(plane, grid)
    suffix = common.param_suffix({"lcap": f"{plane.load_cost_ann:.3g}",
                                  "amort": f"{cfg.AMORTIZATION_YEARS:g}"})

    def util_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization_lcoe(ax, plane)
        fig.colorbar(mesh, ax=ax, pad=0.12).set_label(axis_label("utilization_pct"))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_COST_PLANE / f"lcoe_utilization_{suffix}.png"

    def lcoe_fig():
        import matplotlib.ticker as mticker
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_lcoe_value(ax, plane)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
        cbar.set_label(axis_label("lcoe"))
        cbar.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
        )
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_COST_PLANE / f"lcoe_value_{suffix}.png"

    return [("cost_plane/lcoe_utilization", util_fig), ("cost_plane/lcoe_value", lcoe_fig)]
