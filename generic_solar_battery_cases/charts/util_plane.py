"""Util-plane charts: utilization (y) vs load capex or load income (x).

For each utilization bin the minimum-hardware-cost (S,B) build is found —
the efficiency frontier. Every point on that frontier has a well-defined
LCOE, LVOE, and profit for any (load_capex, income) combination.

Eight heatmaps (4 metrics × 2 contour variants):
  util × load capex  →  LVOE   (color)  [contours + no-contours]
  util × load capex  →  profit (color)  [contours + no-contours]
  util × load income →  LVOE   (color)  [contours + no-contours]
  util × load income →  profit (color)  [contours + no-contours]

Axes: x = income/capex (log), y = utilization (linear %).
"""

from __future__ import annotations

import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker
import numpy as np

import config as cfg
import derived
import model
from labels import axis_label

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]

_N_UTIL = 200   # utilization bins for y-axis


# --------------------------------------------------------------------------- #
# Efficiency frontier
# --------------------------------------------------------------------------- #
def _frontier(
    grid: model.ServedGrid,
    solar_cost_ann: float,
    batt_cost_ann: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """For each utilization bin: cheapest (S,B) build on the efficiency frontier.

    Returns (util_centers_pct, hw_cost_ann, served_kwh_yr), each (N_UTIL,).
    Gaps within the valid utilization range are filled by linear interpolation
    (the frontier is continuous; gaps are artifacts of the discrete S,B grid).
    """
    S, B = grid.kw_solar, grid.kwh_battery
    hw   = solar_cost_ann * S[:, None] + batt_cost_ann * B[None, :]
    srv  = grid.served_kwh
    util = srv / grid.demand_kwh

    hw_f, srv_f, util_f = hw.flatten(), srv.flatten(), util.flatten()
    ok = srv_f > 0
    hw_v, srv_v, util_v = hw_f[ok], srv_f[ok], util_f[ok]

    bins    = np.linspace(0.0, util_v.max(), _N_UTIL + 1)
    centers = 0.5 * (bins[:-1] + bins[1:]) * 100.0   # → percent
    bidx    = np.clip(np.digitize(util_v, bins) - 1, 0, _N_UTIL - 1)

    f_hw  = np.full(_N_UTIL, np.nan)
    f_srv = np.full(_N_UTIL, np.nan)
    for b in range(_N_UTIL):
        m = bidx == b
        if m.any():
            best     = int(np.argmin(hw_v[m]))
            f_hw[b]  = hw_v[m][best]
            f_srv[b] = srv_v[m][best]

    # Fill interior gaps by linear interpolation (don't extrapolate beyond range).
    finite_mask = np.isfinite(f_hw)
    if finite_mask.sum() >= 2:
        x_fin = centers[finite_mask]
        lo, hi = x_fin.min(), x_fin.max()
        gap = ~finite_mask & (centers >= lo) & (centers <= hi)
        if gap.any():
            f_hw[gap]  = np.interp(centers[gap], x_fin, f_hw[finite_mask])
            f_srv[gap] = np.interp(centers[gap], x_fin, f_srv[finite_mask])

    return centers, f_hw, f_srv


# --------------------------------------------------------------------------- #
# Plane data helpers
# --------------------------------------------------------------------------- #
def _vs_load_capex(
    f_hw: np.ndarray, f_srv: np.ndarray,
    load_capex_raw: np.ndarray, income: float, amort: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (lvoe, profit) each shape (N_UTIL, nL). NaN where invalid."""
    lca   = load_capex_raw / amort                                       # (nL,)
    total = f_hw[:, None] + lca[None, :] * cfg.LOAD_KW                  # (nU, nL)
    valid = np.isfinite(f_hw) & (f_srv > 0)
    lcoe  = np.where(valid[:, None], total / f_srv[:, None], np.nan)
    lvoe   = income - lcoe
    profit = np.where(valid[:, None],
                      income * f_srv[:, None] - total, np.nan)
    return lvoe, profit


def _vs_income(
    f_hw: np.ndarray, f_srv: np.ndarray,
    income_values: np.ndarray,
    load_cost_ann: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (lvoe, profit) each shape (N_UTIL, nI). NaN where invalid."""
    total = f_hw + load_cost_ann * cfg.LOAD_KW                          # (nU,)
    valid = np.isfinite(f_hw) & (f_srv > 0)
    lcoe  = np.where(valid, total / f_srv, np.nan)                      # (nU,)
    lvoe   = income_values[None, :] - lcoe[:, None]                    # (nU, nI)
    profit = np.where(valid[:, None],
                      income_values[None, :] * f_srv[:, None] - total[:, None],
                      np.nan)                                            # (nU, nI)
    return lvoe, profit


# --------------------------------------------------------------------------- #
# Draw function
# --------------------------------------------------------------------------- #
def _draw_heatmap_panel(
    ax,
    util_centers: np.ndarray,      # (nU,) in percent
    x_arr: np.ndarray,             # (nX,) income or capex — log-spaced, becomes x-axis
    z_pct: np.ndarray,             # (nU, nX) — rows = util, cols = x_arr
    *,
    title: str,
    xlabel: str,
    metric: str,                   # "lvoe" or "profit"
    show_contours: bool = True,
) -> object:
    """Heatmap: x = income/capex (log), y = utilization (linear %).

    z_pct shape: (nU, nX) — i.e. rows are utilization, columns are x_arr values.
    """
    if metric == "lvoe":
        pos = z_pct[np.isfinite(z_pct) & (z_pct > 0)]
        norm = mcolors.LogNorm(vmin=float(pos.min()), vmax=float(pos.max())) if pos.size else None
        z_plot = np.where(z_pct > 0, z_pct, np.nan)
        cfmt   = lambda v: common._dollar_fmt(v) + "/kWh"
        clab   = "LVOE  ($/kWh)"
    else:  # profit
        pos = z_pct[np.isfinite(z_pct) & (z_pct > 0)]
        norm = mcolors.LogNorm(vmin=float(pos.min()), vmax=float(pos.max())) if pos.size else None
        z_plot = np.where(z_pct > 0, z_pct, np.nan)
        cfmt   = common._dollar_fmt
        clab   = "Profit  ($/yr)"

    cmap_obj = matplotlib.colormaps[common.HEAT_CMAP].copy()
    cmap_obj.set_bad("#2A2A2A", alpha=1.0)

    # draw_heatmap expects z shape (len(y), len(x)) = (nU, nX) — matches z_plot ✓
    mesh = common.draw_heatmap(
        ax, x_arr, util_centers, z_plot,
        xlabel=xlabel,
        ylabel="Utilization  (%)",
        title=title,
        cmap=cmap_obj,
        norm=norm,
        contour_levels=common.log_nice_levels(z_plot) if (pos.size and show_contours) else None,
        contour_color="white",
        contour_fmt=cfmt,
        filter_stubs=True,
    )
    ax.set_xscale("log")
    common.dollar_log_axis(ax, "x")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=12.0, color="#cccccc", alpha=0.9)
    return mesh, clab


# --------------------------------------------------------------------------- #
# Per-metric draw functions
# --------------------------------------------------------------------------- #
def draw_lvoe_vs_load_capex(ax, grid, solar_cost_ann, batt_cost_ann, income,
                             amort, load_capex_raw, *, show_contours=True):
    util_c, f_hw, f_srv = _frontier(grid, solar_cost_ann, batt_cost_ann)
    lvoe, _ = _vs_load_capex(f_hw, f_srv, load_capex_raw, income, amort)
    return _draw_heatmap_panel(
        ax, util_c, load_capex_raw, lvoe,
        title="LVOE vs utilization and load capex",
        xlabel=axis_label("load_capex"),
        metric="lvoe", show_contours=show_contours,
    )


def draw_profit_vs_load_capex(ax, grid, solar_cost_ann, batt_cost_ann, income,
                               amort, load_capex_raw, *, show_contours=True):
    util_c, f_hw, f_srv = _frontier(grid, solar_cost_ann, batt_cost_ann)
    _, profit = _vs_load_capex(f_hw, f_srv, load_capex_raw, income, amort)
    return _draw_heatmap_panel(
        ax, util_c, load_capex_raw, profit,
        title="Profit vs utilization and load capex",
        xlabel=axis_label("load_capex"),
        metric="profit", show_contours=show_contours,
    )


def draw_lvoe_vs_income(ax, grid, solar_cost_ann, batt_cost_ann,
                         income_values, load_cost_ann=0.0, *, show_contours=True):
    util_c, f_hw, f_srv = _frontier(grid, solar_cost_ann, batt_cost_ann)
    lvoe, _ = _vs_income(f_hw, f_srv, income_values, load_cost_ann)
    return _draw_heatmap_panel(
        ax, util_c, income_values, lvoe,
        title="LVOE vs utilization and load income",
        xlabel=axis_label("income_per_kwh"),
        metric="lvoe", show_contours=show_contours,
    )


def draw_profit_vs_income(ax, grid, solar_cost_ann, batt_cost_ann,
                           income_values, load_cost_ann=0.0, *, show_contours=True):
    util_c, f_hw, f_srv = _frontier(grid, solar_cost_ann, batt_cost_ann)
    _, profit = _vs_income(f_hw, f_srv, income_values, load_cost_ann)
    return _draw_heatmap_panel(
        ax, util_c, income_values, profit,
        title="Profit vs utilization and load income",
        xlabel=axis_label("income_per_kwh"),
        metric="profit", show_contours=show_contours,
    )


# --------------------------------------------------------------------------- #
# Figure builders
# --------------------------------------------------------------------------- #
def figures(grid: model.ServedGrid, served_grid):
    from viz import render

    sol = cfg.SOLAR_COST_ANN
    bat = cfg.BATTERY_COST_ANN
    amort = cfg.LOAD_AMORTIZATION_YEARS
    load_capex_raw = cfg.LOAD_CAPEX_RAW_SWEEP
    income_values  = cfg.LOAD_PLANE_INCOME_SWEEP

    _base_params = {
        "Site":            common.site_label(),
        "Capacity factor": f"{served_grid.capacity_factor:.0%}",
        "Load":            f"{cfg.LOAD_KW:g} kW constant",
        "Solar cost":      f"${sol:.3g}/kW·yr",
        "Battery cost":    f"${bat:.3g}/kWh·yr",
        "Load amort":      f"{amort:g} yr",
    }
    suffix = common.param_suffix({"sol": f"{sol:.3g}", "bat": f"{bat:.3g}"})

    def _fig(draw_fn, subdir, name, cbar_label, params):
        def make_fig():
            fig, ax = render.new_figure(figsize=(9, 7))
            mesh, _ = draw_fn(ax)
            cbar = fig.colorbar(mesh, ax=ax, pad=0.12)
            cbar.set_label(cbar_label)
            cbar.ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
            )
            common.info(ax, fig, params, mode="on")
            return fig, cfg.OUT_UTIL_PLANE / subdir / f"{name}_{suffix}.png"
        return make_fig

    charts = []

    # Income charts — vary fixed load cost ($/kW·yr annualized)
    for lc_ann in [0.0, 10.0, 100.0, 1000.0]:
        lc_slug = f"lc{lc_ann:g}".replace(".", "p")
        lc_params = {**_base_params, "Load cost (fixed)": f"${lc_ann:g}/kW·yr"}
        for show_c, subdir in [(False, "no_contours"), (True, "contours")]:
            charts += [
                (f"util_plane/{subdir}/lvoe_vs_income_{lc_slug}", _fig(
                    lambda ax, sc=show_c, lc=lc_ann: draw_lvoe_vs_income(
                        ax, grid, sol, bat, income_values, lc, show_contours=sc),
                    subdir, f"lvoe_vs_income_{lc_slug}", "LVOE  ($/kWh)", lc_params)),
                (f"util_plane/{subdir}/profit_vs_income_{lc_slug}", _fig(
                    lambda ax, sc=show_c, lc=lc_ann: draw_profit_vs_income(
                        ax, grid, sol, bat, income_values, lc, show_contours=sc),
                    subdir, f"profit_vs_income_{lc_slug}", "Profit  ($/yr)", lc_params)),
            ]

    # Capex charts — include fixed income; three representative income levels
    for inc in [0.01, 0.1, 1.0]:
        inc_slug = f"inc{inc:g}".replace(".", "p")
        capex_params = {**_base_params, "Income (fixed)": f"${inc:g}/kWh"}
        for show_c, subdir in [(False, "no_contours"), (True, "contours")]:
            charts += [
                (f"util_plane/{subdir}/lvoe_vs_load_capex_{inc_slug}", _fig(
                    lambda ax, sc=show_c, i=inc: draw_lvoe_vs_load_capex(
                        ax, grid, sol, bat, i, amort, load_capex_raw, show_contours=sc),
                    subdir, f"lvoe_vs_load_capex_{inc_slug}", "LVOE  ($/kWh)", capex_params)),
                (f"util_plane/{subdir}/profit_vs_load_capex_{inc_slug}", _fig(
                    lambda ax, sc=show_c, i=inc: draw_profit_vs_load_capex(
                        ax, grid, sol, bat, i, amort, load_capex_raw, show_contours=sc),
                    subdir, f"profit_vs_load_capex_{inc_slug}", "Profit  ($/yr)", capex_params)),
            ]

    return charts


if __name__ == "__main__":
    import time
    from viz import render

    t0 = time.time()
    g = derived.load_served_grid()
    plan = figures(g, g)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
