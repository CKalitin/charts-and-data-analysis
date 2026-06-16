"""Build plane — the (kW solar × kWh battery) heatmap at fixed prices.

Shows what the optimizer in Charts A/B is choosing among: utilization and annual
profit across every candidate build, with the profit-maximizing point marked.

    x : battery capacity (kWh)
    y : solar nameplate  (kW)
    color : utilization (%) / annual profit ($)
"""

from __future__ import annotations

import sys
from pathlib import Path

if not __package__:  # running as a script — add project root to path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import config as cfg
import derived
import model
from labels import axis_label

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]


def _params(grid: model.ServedGrid) -> dict[str, str]:
    p = {
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load": f"{cfg.LOAD_KW:g} kW constant",
        "Load income": f"${cfg.INCOME_PER_KWH:.3g}/kWh",
        "Solar cost": f"${cfg.SOLAR_COST_ANN:.3g}/kW·yr  (${cfg.SOLAR_CAPEX_PER_KW:.0f}/kW)",
        "Battery cost": f"${cfg.BATTERY_COST_ANN:.3g}/kWh·yr  (${cfg.BATTERY_CAPEX_PER_KWH:.0f}/kWh)",
        "Amortization": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }
    if cfg.LOAD_COST_ANN > 0:
        p["Load capex"] = (f"${cfg.LOAD_COST_ANN:.3g}/kW·yr  "
                           f"(${cfg.LOAD_CAPEX_PER_KW:.0f}/kW, {cfg.LOAD_AMORTIZATION_YEARS:g} yr)")
    return p


def _mark_optimum(ax, opt: derived.OptimalBuild) -> None:
    ax.scatter([opt.kwh_battery], [opt.kw_solar], s=90, marker="*",
               color="white", edgecolor="black", linewidth=0.8, zorder=5,
               label=f"Optimum: {opt.kw_solar:g} kW + {opt.kwh_battery:g} kWh "
                     f"(util {opt.utilization:.1%})")
    ax.legend(loc="lower right", fontsize=8, framealpha=0.7)


def draw_utilization(ax, grid: model.ServedGrid, opt: derived.OptimalBuild):
    mesh = common.draw_heatmap(
        ax, grid.kwh_battery, grid.kw_solar, grid.utilization * 100.0,
        xlabel=axis_label("kwh_battery"), ylabel=axis_label("kw_solar"),
        title="Load utilization across builds", vmin=0, vmax=100,
        contour_levels=[v * 100 for v in common.UTIL_CONTOURS],
        contour_fmt=lambda v: f"{v:.3g}%",
        contour_color="black",
    )
    _mark_optimum(ax, opt)
    return mesh


def draw_profit(ax, grid: model.ServedGrid, opt: derived.OptimalBuild):
    profit = derived.profit_grid(grid, cfg.INCOME_PER_KWH, cfg.SOLAR_COST_ANN,
                                 cfg.BATTERY_COST_ANN, cfg.LOAD_COST_ANN)
    mesh = common.draw_heatmap(
        ax, grid.kwh_battery, grid.kw_solar, profit,
        xlabel=axis_label("kwh_battery"), ylabel=axis_label("kw_solar"),
        title="Annual profit across builds",
        contour_levels=common.nice_levels(profit), contour_color="white",
        contour_fmt=common._dollar_fmt,
    )
    _mark_optimum(ax, opt)
    return mesh


def _params_lcoe(grid: model.ServedGrid) -> dict[str, str]:
    p = {
        "Objective": "LCOE minimization",
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load": f"{cfg.LOAD_KW:g} kW constant",
        "Solar cost": f"${cfg.SOLAR_COST_ANN:.3g}/kW·yr  (${cfg.SOLAR_CAPEX_PER_KW:.0f}/kW)",
        "Battery cost": f"${cfg.BATTERY_COST_ANN:.3g}/kWh·yr  (${cfg.BATTERY_CAPEX_PER_KWH:.0f}/kWh)",
        "Amortization": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }
    if cfg.LOAD_COST_ANN > 0:
        p["Load capex"] = (f"${cfg.LOAD_COST_ANN:.3g}/kW·yr  "
                           f"(${cfg.LOAD_CAPEX_PER_KW:.0f}/kW, {cfg.LOAD_AMORTIZATION_YEARS:g} yr)")
    return p


def _mark_lcoe_optimum(ax, i_opt: int, j_opt: int,
                        grid: model.ServedGrid, lcoe_min: float) -> None:
    kw_s = float(grid.kw_solar[i_opt])
    kwh_b = float(grid.kwh_battery[j_opt])
    util = float(grid.served_kwh[i_opt, j_opt] / grid.demand_kwh)
    ax.scatter([kwh_b], [kw_s], s=90, marker="*",
               color="white", edgecolor="black", linewidth=0.8, zorder=5,
               label=f"LCOE-min: {kw_s:g} kW + {kwh_b:g} kWh  "
                     f"(util {util:.1%}, LCOE {common._dollar_fmt(lcoe_min)}/kWh)")
    ax.legend(loc="lower right", fontsize=8, framealpha=0.7)


def draw_lcoe(ax, grid: model.ServedGrid, load_cost_ann: float = 0.0):
    """LCOE surface over the (S, B) build plane; star marks the minimum.

    The "bowl" shape shows why LCOE-min requires non-trivial hardware: both
    under-building (high LCOE because served_kwh is small) and over-building
    (high LCOE because cost rises faster than served_kwh) are penalised.
    The minimum sits at a balance point that shifts with hardware costs.
    """
    lcoe = derived.lcoe_surface(grid, cfg.SOLAR_COST_ANN, cfg.BATTERY_COST_ANN, load_cost_ann)

    # Finite values only (exclude inf cells for colormap scaling).
    finite = lcoe[np.isfinite(lcoe)]
    plot_lcoe = np.where(np.isfinite(lcoe), lcoe, np.nan)

    idx = int(np.nanargmin(lcoe))
    i_opt, j_opt = np.unravel_index(idx, lcoe.shape)
    lcoe_min = float(lcoe[i_opt, j_opt])

    mesh = common.draw_heatmap(
        ax, grid.kwh_battery, grid.kw_solar, plot_lcoe,
        xlabel=axis_label("kwh_battery"), ylabel=axis_label("kw_solar"),
        title="LCOE heatmap across builds",
        cmap="viridis_r",
        vmin=float(np.nanpercentile(finite, 2)),
        vmax=float(np.nanpercentile(finite, 80)),  # cap at p80 so bowl detail is visible
        contour_levels=common.nice_levels(finite[finite <= np.nanpercentile(finite, 90)]),
        contour_color="white",
        contour_fmt=lambda v: common._dollar_fmt(v),
        filter_stubs=True,
    )
    _mark_lcoe_optimum(ax, i_opt, j_opt, grid, lcoe_min)
    return mesh


_FRONTIER_STYLES = [
    # (label, color, linestyle)
    ("Battery overbuild frontier",          "#e63946", "-"),
    ("Equal solar/battery trade frontier",  "#f89849", "-"),
    ("Battery underbuild frontier",         "#2a9d8f", "-"),
]

# (slope kW/kWh, intercept kW) — parallel to _FRONTIER_STYLES
_FRONTIER_LINES = [
    (3.5 / 50.0,  0.0),   # overbuild:   y = (3.5/50)*x  (shallow, near x-axis)
    (-1.0,       73.0),   # equal-trade: y = 73 - x  (through (40, 33))
    (1.5,        35.0),   # underbuild:  y = 35 + 1.5*x  (starts above data max)
]


def _visible_midpoint(slope: float, intercept: float,
                      x_max: float, y_max: float):
    """Midpoint of line y=slope*x+intercept clipped to [0,x_max]×[0,y_max]."""
    xs = []
    for x in (0.0, x_max):
        y = slope * x + intercept
        if 0.0 <= y <= y_max:
            xs.append(x)
    if slope != 0.0:
        for y in (0.0, y_max):
            x = (y - intercept) / slope
            if 0.0 <= x <= x_max:
                xs.append(x)
    if len(xs) < 2:
        return None
    x_mid = (min(xs) + max(xs)) / 2.0
    return x_mid, slope * x_mid + intercept


def _add_frontier_lines(ax, grid: model.ServedGrid, y_ext: float = 50.0) -> None:
    """Overlay three frontier lines; labels drawn directly on the lines."""
    x_max = float(grid.kwh_battery.max())
    xs = np.linspace(0.0, x_max, 600)

    for (label, color, ls), (slope, intercept) in zip(_FRONTIER_STYLES, _FRONTIER_LINES):
        ax.plot(xs, slope * xs + intercept,
                color=color, linewidth=2.0, linestyle=ls, zorder=4)

    y_data = float(grid.kw_solar.max())
    ax.axhline(y_data, color="gray", linewidth=0.8, linestyle=":", alpha=0.65, zorder=3)

    ax.set_xlim(0.0, x_max)
    ax.set_ylim(0.0, y_ext)
    ax.set_ylabel(axis_label("kw_solar") + f"  (extended to {y_ext:.0f} kW)")

    # Force layout so transData is correct for display-space angle computation.
    ax.figure.canvas.draw()

    for (label, color, _ls), (slope, intercept) in zip(_FRONTIER_STYLES, _FRONTIER_LINES):
        pos = _visible_midpoint(slope, intercept, x_max, y_ext)
        if pos is None:
            continue
        xp, yp = pos
        dx = x_max * 0.01
        p1 = ax.transData.transform((xp, yp))
        p2 = ax.transData.transform((xp + dx, yp + slope * dx))
        angle = float(np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0])))
        ax.text(xp, yp, label, color=color, fontsize=8.0,
                rotation=angle, rotation_mode="anchor",
                ha="center", va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.95))


def draw_lcoe_frontiers(ax, grid: model.ServedGrid, load_cost_ann: float = 0.0) -> object:
    """LCOE build-plane with battery-sizing frontier lines overlaid.

    The three frontier lines divide the (S, B) build space into regions:
      - Battery overbuild zone (below line 1: high battery, low solar)
      - Balanced zone (between lines 1 and 3)
      - Battery underbuild zone (above line 3: high solar, low battery)

    The y-axis is extended beyond the data range so line 3 (which starts at
    35 kW solar, above the 30-kW grid max) is visible as a conceptual frontier.
    """
    mesh = draw_lcoe(ax, grid, load_cost_ann)
    _add_frontier_lines(ax, grid)
    # Lines are labelled directly; keep only the LCOE-min star in a small legend.
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc="upper right", fontsize=8, framealpha=0.7)
    ax.set_title("LCOE heatmap across builds — with sizing frontiers")
    return mesh

def figures_lcoe(grid: model.ServedGrid):
    from viz import render

    params = _params_lcoe(grid)
    suffix_kw = {
        "sol": f"{cfg.SOLAR_COST_ANN:.3g}", "bat": f"{cfg.BATTERY_COST_ANN:.3g}",
        "amort": f"{cfg.AMORTIZATION_YEARS:g}yr",
    }
    if cfg.LOAD_COST_ANN > 0:
        suffix_kw["lcap"] = f"{cfg.LOAD_COST_ANN:.3g}"
    suffix = common.param_suffix(suffix_kw)

    def lcoe_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_lcoe(ax, grid, cfg.LOAD_COST_ANN)
        import matplotlib.ticker as mticker
        cbar = fig.colorbar(mesh, ax=ax)
        cbar.set_label(axis_label("lcoe"))
        cbar.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
        )
        # Place info box at top-right instead of auto
        from viz.info_box import BOX_KW
        ax.text(0.98, 0.98, common.param_text(params),
                transform=ax.transAxes, ha="right", va="top",
                fontsize=9, bbox=BOX_KW)
        # Place watermark at top-left instead of auto
        ax.text(0.02, 0.98, cfg.WATERMARK_TEXT,
                transform=ax.transAxes, ha="left", va="top",
                fontsize=12, color="#cccccc", alpha=0.9)
        return fig, cfg.OUT_BUILD_PLANE / f"lcoe_{suffix}.png"

    return [("build_plane/lcoe", lcoe_fig)]


def figures_lcoe_frontiers(grid: model.ServedGrid):
    from viz import render
    import matplotlib.ticker as mticker

    params = _params_lcoe(grid)
    params["Frontiers"] = "overbuild / equal-trade / underbuild"
    suffix_kw = {
        "sol": f"{cfg.SOLAR_COST_ANN:.3g}", "bat": f"{cfg.BATTERY_COST_ANN:.3g}",
        "amort": f"{cfg.AMORTIZATION_YEARS:g}yr",
    }
    if cfg.LOAD_COST_ANN > 0:
        suffix_kw["lcap"] = f"{cfg.LOAD_COST_ANN:.3g}"
    suffix = common.param_suffix(suffix_kw)

    def fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_lcoe_frontiers(ax, grid, cfg.LOAD_COST_ANN)
        cbar = fig.colorbar(mesh, ax=ax)
        cbar.set_label(axis_label("lcoe"))
        cbar.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
        )
        # Hardcode info box at bottom-right, raised 10% to clear the chart.
        from viz.info_box import BOX_KW
        ax.text(0.98, 0.12, common.param_text(params),
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=9, bbox=BOX_KW)
        common.watermark(ax, fig)
        return fig, cfg.OUT_BUILD_PLANE / f"lcoe_frontiers_{suffix}.png"

    return [("build_plane/lcoe_frontiers", fig)]


def figures(grid: model.ServedGrid):
    from viz import render

    opt = derived.optimal_build(grid, cfg.INCOME_PER_KWH, cfg.SOLAR_COST_ANN,
                                cfg.BATTERY_COST_ANN, cfg.LOAD_COST_ANN)
    params = _params(grid)
    suffix_kw = {
        "inc": f"{cfg.INCOME_PER_KWH:.3g}", "sol": f"{cfg.SOLAR_COST_ANN:.3g}",
        "bat": f"{cfg.BATTERY_COST_ANN:.3g}", "amort": f"{cfg.AMORTIZATION_YEARS:g}yr",
    }
    if cfg.LOAD_COST_ANN > 0:
        suffix_kw["lcap"] = f"{cfg.LOAD_COST_ANN:.3g}"
    suffix = common.param_suffix(suffix_kw)

    def util_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_utilization(ax, grid, opt)
        fig.colorbar(mesh, ax=ax).set_label(axis_label("utilization_pct"))
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_BUILD_PLANE / f"utilization_{suffix}.png"

    def profit_fig():
        fig, ax = render.new_figure(figsize=(9, 7))
        mesh = draw_profit(ax, grid, opt)
        cbar = fig.colorbar(mesh, ax=ax)
        cbar.set_label(axis_label("profit_per_yr"))
        common.dollar_colorbar(cbar)
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_BUILD_PLANE / f"profit_{suffix}.png"

    return [("build_plane/utilization", util_fig), ("build_plane/profit", profit_fig)]


if __name__ == "__main__":
    import time

    import config as cfg
    import derived
    from viz import render

    t0 = time.time()
    grid = derived.load_served_grid()
    plan = [*figures(grid), *figures_lcoe(grid), *figures_lcoe_frontiers(grid)]
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
