"""Ternary allocation — how to split a FIXED $/yr budget between load, solar,
and battery spend.

Every other chart in this project asks "given a load, what's the optimal
hardware?" (an argmax). This one asks a different question: given a constant
annual dollar rate, what's the best 3-way SPLIT of that budget across load /
solar / battery spend? Each point in the triangle is one such split — it
directly fixes a build (L, S, B) via the ANNUALIZED $/(unit·yr) cost of each
component (matching the $/yr budget's units), with no optimizer choosing
among builds. The heatmap is therefore the RESULTANT utilization/profit that
split produces, not an optimal one.

Layout: 100% load at the top vertex ("load on the bottom" — read via
horizontal gridlines), 100% solar at bottom-left, 100% battery at
bottom-right.

Total budget is fixed at config.TERNARY_TOTAL_BUDGET ($/yr) across every
case, so the two cases are directly comparable — only the load's own
annualized cost and income per kWh change between them (see
config.TERNARY_CASES). Solar/battery $/(unit·yr) costs stay at project
defaults in every case.
"""

from __future__ import annotations

import sys
from pathlib import Path

if not __package__:  # running as a script — add project root to path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.colors as mcolors
import matplotlib.tri as mtri
import numpy as np

import config as cfg
import derived
import model
from labels import axis_label

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]

_SQRT3_2 = np.sqrt(3.0) / 2.0

# Vertices: top = 100% load, bottom-left = 100% solar, bottom-right = 100% battery.
_V_LOAD = (0.5, _SQRT3_2)
_V_SOLAR = (0.0, 0.0)
_V_BATTERY = (1.0, 0.0)


# --------------------------------------------------------------------------- #
# Ternary geometry
# --------------------------------------------------------------------------- #
def _to_xy(f_load: np.ndarray, f_solar: np.ndarray, f_battery: np.ndarray):
    """Barycentric (f_load, f_solar, f_battery) -> Cartesian (x, y)."""
    x = 0.5 * f_load + f_battery
    y = f_load * _SQRT3_2
    return x, y


def _draw_ternary_frame(ax) -> None:
    """Triangle outline, vertex labels, faint 20%-interval gridlines + edge
    tick labels. No cartesian axes/ticks — this is not an x/y chart."""
    tri_x = [_V_SOLAR[0], _V_BATTERY[0], _V_LOAD[0], _V_SOLAR[0]]
    tri_y = [_V_SOLAR[1], _V_BATTERY[1], _V_LOAD[1], _V_SOLAR[1]]
    ax.plot(tri_x, tri_y, color="black", linewidth=1.3, zorder=6)

    for t in (0.2, 0.4, 0.6, 0.8):
        y = t * _SQRT3_2
        # load = t: horizontal line, parallel to the solar-battery (bottom) edge.
        ax.plot([0.5 * t, 1 - 0.5 * t], [y, y], color="0.7", linewidth=0.6,
                linestyle="--", zorder=1)
        # solar = t: line from the bottom edge to the left (load-solar) edge.
        ax.plot([1 - t, 0.5 - 0.5 * t], [0.0, (1 - t) * _SQRT3_2],
                color="0.7", linewidth=0.6, linestyle="--", zorder=1)
        # battery = t: line from the bottom edge to the right (load-battery) edge.
        ax.plot([t, 0.5 + 0.5 * t], [0.0, (1 - t) * _SQRT3_2],
                color="0.7", linewidth=0.6, linestyle="--", zorder=1)

        # Tick labels: load on the left edge, solar on the bottom edge,
        # battery on the right edge (each edge shows the variable whose
        # vertex it's adjacent to and whose value increases toward that vertex).
        ax.text(0.5 * t - 0.025, y, f"{t * 100:.0f}", fontsize=6.5, color="0.4",
                ha="right", va="center", rotation=60, zorder=1)
        ax.text(1 - t, -0.025, f"{t * 100:.0f}", fontsize=6.5, color="0.4",
                ha="center", va="top", zorder=1)
        ax.text(0.5 + 0.5 * t + 0.02, (1 - t) * _SQRT3_2, f"{t * 100:.0f}",
                fontsize=6.5, color="0.4", ha="left", va="center", rotation=-60, zorder=1)

    ax.text(_V_LOAD[0], _V_LOAD[1] + 0.035, "100% Load", ha="center", va="bottom",
            fontsize=10, fontweight="bold", zorder=6)
    ax.text(_V_SOLAR[0] - 0.03, _V_SOLAR[1] - 0.03, "100% Solar", ha="right", va="top",
            fontsize=10, fontweight="bold", zorder=6)
    ax.text(_V_BATTERY[0] + 0.03, _V_BATTERY[1] - 0.03, "100% Battery", ha="left", va="top",
            fontsize=10, fontweight="bold", zorder=6)

    ax.set_xlim(-0.16, 1.16)
    ax.set_ylim(-0.10, _SQRT3_2 + 0.14)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(False)


# --------------------------------------------------------------------------- #
# Draw functions
# --------------------------------------------------------------------------- #
def draw_utilization(ax, ta: derived.TernaryAllocation, *, show_contours: bool = True):
    """Resultant (not optimized) utilization at every budget split. The
    profit-optimal split (same point marked on the profit/LVOE panels) is
    marked here too, labeled with ITS utilization — utilization is resultant,
    not optimized, so the profit-best point isn't necessarily the highest
    utilization on the triangle."""
    x, y = _to_xy(ta.f_load, ta.f_solar, ta.f_battery)
    z = ta.utilization * 100.0
    triang = mtri.Triangulation(x, y)

    mesh = ax.tricontourf(triang, z, levels=np.linspace(0.0, 100.0, 41),
                          cmap=common.HEAT_CMAP, zorder=2)
    if show_contours:
        levels = [v * 100 for v in common.UTIL_CONTOURS if 0 < v * 100 < 100]
        cs = ax.tricontour(triang, z, levels=levels, colors="black",
                           linewidths=0.8, alpha=0.85, zorder=3)
        ax.clabel(cs, fmt=lambda v: f"{v:.3g}%", fontsize=7.5, inline=True, colors="black")

    best = int(np.nanargmax(ta.profit_per_yr))
    xb, yb = float(x[best]), float(y[best])
    ax.scatter([xb], [yb], s=90, marker="*", color="white", edgecolor="black",
              linewidth=0.8, zorder=5,
              label=(f"Best (max profit): {ta.f_load[best]:.0%} load / {ta.f_solar[best]:.0%} solar / "
                     f"{ta.f_battery[best]:.0%} battery  ({z[best]:.3g}% util)"))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=7.5, framealpha=0.85)

    _draw_ternary_frame(ax)
    ax.set_title("Resultant utilization — every 3-way budget split")
    return mesh


def _draw_diverging_metric(ax, ta: derived.TernaryAllocation, z: np.ndarray, *,
                           title: str, unit_fmt, best_fmt, show_contours: bool = True):
    """Shared renderer for profit/LVOE: both are $-valued, sign-diverging at a
    breakeven of 0, and share the star/legend + breakeven-contour treatment —
    only the value array and $ formatting differ between them."""
    x, y = _to_xy(ta.f_load, ta.f_solar, ta.f_battery)
    triang = mtri.Triangulation(x, y)
    finite = np.isfinite(z)
    if not finite.all():
        triang.set_mask(np.any(~finite[triang.triangles], axis=1))

    zmin, zmax = float(np.nanmin(z)), float(np.nanmax(z))
    crosses_zero = zmin < 0.0 < zmax
    # Robust (2nd/98th percentile) bounds: a handful of splits near the
    # pure-load vertex (tiny hardware, near-zero served energy) can blow LCOE
    # up toward +/-infinity — a real but extreme singularity, not the story
    # this chart is telling. Raw min/max would let that single corner force a
    # huge range and crush the genuine variation elsewhere into a sliver (the
    # same failure mode as an un-autoclipped outlier cluster).
    p_lo, p_hi = (float(v) for v in np.nanpercentile(z, [2.0, 98.0]))

    if crosses_zero:
        # Genuine sign change, but DON'T force a symmetric +/-max(|p_lo|,|p_hi|)
        # range (wastes span mirroring a magnitude the minority side never
        # reaches, crushing the majority side into a handful of colormap
        # steps — a near-solid-green triangle even though profit genuinely
        # ranges from ~$0 to ~$500k) and DON'T use TwoSlopeNorm even with
        # asymmetric bounds (it always puts the zero-crossing at the exact
        # PIXEL midpoint regardless of how asymmetric the value ranges either
        # side of it are — e.g. lo=-0.02, hi=0.11 still gets split 50/50 by
        # pixels, so the narrow negative side is stretched ~5x relative to
        # the positive side, and the color-per-dollar rate visibly jumps at
        # the crossing — a "kink" that reads as a non-smooth band). A plain
        # linear map over the data's own [lo, hi] has ONE constant rate
        # throughout — genuinely smooth — and RdYlGn still reads red/yellow/
        # green at whatever fraction of [lo, hi] zero actually falls; the
        # explicit black "breakeven" contour below marks it exactly either way.
        lo = min(p_lo, -1e-6 * max(abs(p_hi), 1.0))
        hi = max(p_hi, 1e-6 * max(abs(p_lo), 1.0))
        norm = mcolors.Normalize(vmin=lo, vmax=hi)
        levels = np.linspace(lo, hi, 41)
        cmap = "RdYlGn"
    else:
        # No sign change: forcing a symmetric +/-vmax range around 0 would waste
        # the unused half of the colorbar on the sign that never occurs, crushing
        # the real variation into a sliver (e.g. LVOE staying positive but ranging
        # 2.4-5.0 $/kWh) — use the metric's own tight range with a one-sided map.
        lo, hi = (p_lo, p_hi) if p_hi > p_lo else (zmin, zmin + 1.0)
        norm = mcolors.Normalize(vmin=lo, vmax=hi)
        levels = np.linspace(lo, hi, 41)
        cmap = "Greens" if zmin >= 0.0 else "Reds_r"
    extend = "both" if (zmin < lo or zmax > hi) else "neither"
    mesh = ax.tricontourf(triang, z, levels=levels, cmap=cmap, norm=norm, zorder=2, extend=extend)

    if crosses_zero:
        cs0 = ax.tricontour(triang, z, levels=[0.0], colors="black",
                            linewidths=1.6, zorder=4)
        ax.clabel(cs0, fmt=lambda v: "breakeven", fontsize=7.5, inline=True, colors="black")

    if show_contours:
        # Pick levels from the same robust (clipped) range as the fill, so a
        # far-out singularity value doesn't spend most of the level budget on
        # contours that never re-enter the visible area.
        levels_c = common.nice_levels(np.clip(z, lo, hi))
        levels_c = levels_c[np.abs(levels_c) > 1e-9]
        if levels_c.size:
            cs = ax.tricontour(triang, z, levels=levels_c, colors="0.15",
                               linewidths=0.6, alpha=0.8, zorder=3)
            ax.clabel(cs, fmt=unit_fmt, fontsize=7, inline=True, colors="0.15")

    best = int(np.nanargmax(z))
    xb, yb = float(x[best]), float(y[best])
    ax.scatter([xb], [yb], s=90, marker="*", color="white", edgecolor="black",
              linewidth=0.8, zorder=5,
              label=(f"Best: {ta.f_load[best]:.0%} load / {ta.f_solar[best]:.0%} solar / "
                     f"{ta.f_battery[best]:.0%} battery  ({best_fmt(float(z[best]))})"))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=7.5, framealpha=0.85)

    _draw_ternary_frame(ax)
    ax.set_title(title)
    return mesh


def _lvoe_fmt(v: float) -> str:
    """$/kWh formatter with enough precision for LVOE's typically narrow, sub-$10
    range — common._dollar_fmt's whole-dollar rounding collapses a $4.2-$5.0
    span into repeated "$5" ticks."""
    if v == 0:
        return "$0"
    if abs(v) >= 100:
        return f"${v:,.0f}"
    if abs(v) >= 1:
        return f"${v:.2f}"
    if abs(v) >= 0.001:
        return f"${v:.3g}"
    return f"${v:.0e}"


def _lvoe_colorbar(cbar) -> None:
    import matplotlib.ticker as mticker
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _lvoe_fmt(v)))


def draw_profit(ax, ta: derived.TernaryAllocation, *, show_contours: bool = True):
    """Resultant annual profit at every budget split, diverging at breakeven."""
    return _draw_diverging_metric(
        ax, ta, ta.profit_per_yr,
        title="Resultant annual profit — every 3-way budget split",
        unit_fmt=common._dollar_fmt,
        best_fmt=lambda v: f"${v:,.0f}/yr",
        show_contours=show_contours,
    )


def draw_lvoe(ax, ta: derived.TernaryAllocation, *, show_contours: bool = True):
    """Resultant Levelized Value of Energy (income - LCOE) at every budget
    split, diverging at breakeven. NaN at the pure-load vertex (no hardware,
    no service delivered — LCOE undefined) is masked out of the triangulation."""
    return _draw_diverging_metric(
        ax, ta, ta.lvoe,
        title="Resultant LVOE — every 3-way budget split",
        unit_fmt=lambda v: _lvoe_fmt(v) + "/kWh",
        best_fmt=lambda v: f"{_lvoe_fmt(v)}/kWh",
        show_contours=show_contours,
    )


# --------------------------------------------------------------------------- #
# Figure builders
# --------------------------------------------------------------------------- #
def _new_triple_figure(figsize=(24, 8), dpi=None):
    """Three side-by-side ternary panels sharing one Figure (util | profit | LVOE)."""
    from viz import render
    fig = render.Figure(figsize=figsize, dpi=dpi or render.DPI)
    render.FigureCanvasAgg(fig)
    ax1 = fig.add_subplot(1, 3, 1)
    ax2 = fig.add_subplot(1, 3, 2)
    ax3 = fig.add_subplot(1, 3, 3)
    return fig, ax1, ax2, ax3


def _params(ta: derived.TernaryAllocation, grid: model.ServedGrid, case_name: str) -> dict[str, str]:
    p = {
        "Case": case_name,
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Total budget": f"{common._dollar_fmt(ta.total_budget)}/yr",
        "Load income": f"${ta.income_per_kwh:.3g}/kWh",
        "Load cost": f"${ta.load_cost_ann:.3g}/kW·yr  ({ta.load_amortization_years:g} yr amort.)",
        "Solar cost": f"${ta.solar_cost_ann:.3g}/kW·yr  ({ta.amortization_years:g} yr amort.)",
        "Battery cost": f"${ta.batt_cost_ann:.3g}/kWh·yr  ({ta.amortization_years:g} yr amort.)",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }
    return p


def figures(ta: derived.TernaryAllocation, grid: model.ServedGrid, case_name: str):
    from viz import render

    params = _params(ta, grid, case_name)
    suffix = common.param_suffix({"budget": f"{ta.total_budget:.0f}",
                                  "inc": f"{ta.income_per_kwh:.3g}"})
    out_dir = cfg.OUT_TERNARY / case_name

    def util_fig():
        fig, ax = render.new_figure(figsize=(9, 8))
        mesh = draw_utilization(ax, ta, show_contours=True)
        fig.colorbar(mesh, ax=ax, pad=0.02, shrink=0.85).set_label(axis_label("utilization_pct_resultant"))
        common.info(ax, fig, params, mode="off", off_side="left")
        common.watermark(ax, fig)
        return fig, out_dir / f"utilization_contours_{suffix}.png"

    def util_fig_plain():
        fig, ax = render.new_figure(figsize=(9, 8))
        mesh = draw_utilization(ax, ta, show_contours=False)
        fig.colorbar(mesh, ax=ax, pad=0.02, shrink=0.85).set_label(axis_label("utilization_pct_resultant"))
        common.info(ax, fig, params, mode="off", off_side="left")
        common.watermark(ax, fig)
        return fig, out_dir / f"utilization_no_contours_{suffix}.png"

    def profit_fig():
        fig, ax = render.new_figure(figsize=(9, 8))
        mesh = draw_profit(ax, ta, show_contours=True)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.02, shrink=0.85)
        cbar.set_label(axis_label("profit_per_yr_resultant"))
        common.dollar_colorbar(cbar)
        common.info(ax, fig, params, mode="off", off_side="left")
        common.watermark(ax, fig)
        return fig, out_dir / f"profit_contours_{suffix}.png"

    def profit_fig_plain():
        fig, ax = render.new_figure(figsize=(9, 8))
        mesh = draw_profit(ax, ta, show_contours=False)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.02, shrink=0.85)
        cbar.set_label(axis_label("profit_per_yr_resultant"))
        common.dollar_colorbar(cbar)
        common.info(ax, fig, params, mode="off", off_side="left")
        common.watermark(ax, fig)
        return fig, out_dir / f"profit_no_contours_{suffix}.png"

    def lvoe_fig():
        fig, ax = render.new_figure(figsize=(9, 8))
        mesh = draw_lvoe(ax, ta, show_contours=True)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.02, shrink=0.85)
        cbar.set_label(axis_label("lvoe"))
        _lvoe_colorbar(cbar)
        common.info(ax, fig, params, mode="off", off_side="left")
        common.watermark(ax, fig)
        return fig, out_dir / f"lvoe_contours_{suffix}.png"

    def lvoe_fig_plain():
        fig, ax = render.new_figure(figsize=(9, 8))
        mesh = draw_lvoe(ax, ta, show_contours=False)
        cbar = fig.colorbar(mesh, ax=ax, pad=0.02, shrink=0.85)
        cbar.set_label(axis_label("lvoe"))
        _lvoe_colorbar(cbar)
        common.info(ax, fig, params, mode="off", off_side="left")
        common.watermark(ax, fig)
        return fig, out_dir / f"lvoe_no_contours_{suffix}.png"

    def _combined(show_contours: bool):
        fig, ax1, ax2, ax3 = _new_triple_figure()
        mesh1 = draw_utilization(ax1, ta, show_contours=show_contours)
        fig.colorbar(mesh1, ax=ax1, pad=0.02, shrink=0.8).set_label(axis_label("utilization_pct_resultant"))
        mesh2 = draw_profit(ax2, ta, show_contours=show_contours)
        cbar2 = fig.colorbar(mesh2, ax=ax2, pad=0.02, shrink=0.8)
        cbar2.set_label(axis_label("profit_per_yr_resultant"))
        common.dollar_colorbar(cbar2)
        mesh3 = draw_lvoe(ax3, ta, show_contours=show_contours)
        cbar3 = fig.colorbar(mesh3, ax=ax3, pad=0.02, shrink=0.8)
        cbar3.set_label(axis_label("lvoe"))
        _lvoe_colorbar(cbar3)
        # "left" (used by the single-panel figures) would collide with cbar2,
        # which sits immediately to ax3's left in this 3-panel layout.
        common.info(ax3, fig, params, mode="off", off_side="bottom")
        common.watermark(ax1, fig)
        return fig

    def combined_fig():
        return _combined(True), out_dir / f"combined_contours_{suffix}.png"

    def combined_fig_plain():
        return _combined(False), out_dir / f"combined_no_contours_{suffix}.png"

    return [
        (f"ternary_allocation/{case_name}/utilization_contours", util_fig),
        (f"ternary_allocation/{case_name}/utilization_no_contours", util_fig_plain),
        (f"ternary_allocation/{case_name}/profit_contours", profit_fig),
        (f"ternary_allocation/{case_name}/profit_no_contours", profit_fig_plain),
        (f"ternary_allocation/{case_name}/lvoe_contours", lvoe_fig),
        (f"ternary_allocation/{case_name}/lvoe_no_contours", lvoe_fig_plain),
        (f"ternary_allocation/{case_name}/combined_contours", combined_fig),
        (f"ternary_allocation/{case_name}/combined_no_contours", combined_fig_plain),
    ]


def all_cases_figures(grid: model.ServedGrid):
    """Build the ternary allocation for every case in cfg.TERNARY_CASES."""
    plan = []
    for case_name, (income, load_capex, load_amort) in cfg.TERNARY_CASES.items():
        ta = derived.ternary_allocation(
            grid, total_budget=cfg.TERNARY_TOTAL_BUDGET, income_per_kwh=income,
            load_cost_ann=load_capex / load_amort, load_amortization_years=load_amort,
        )
        if ta.off_grid_fraction > 0.005:
            print(f"  [{case_name}] {ta.off_grid_fraction:.0%} of splits exceed the "
                  f"calibrated build grid (utilization clipped, not re-simulated)")
        plan += figures(ta, grid, case_name)
    return plan


if __name__ == "__main__":
    import time

    import config as cfg
    import derived
    from viz import render

    t0 = time.time()
    grid = derived.load_served_grid()
    plan = all_cases_figures(grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
