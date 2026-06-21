"""Heatmaps for the BPA hydro + battery sweep.

Axes (every chart):
  X = battery energy capacity (GWh)   0 -> 200
  Y = installed firm hydro (GW)       0 -> 20

Four charts:
  1. Utilization (% of 2024 load served)
  2. System cost ($B capex)
  3. LCOE ($/MWh served, log colour scale)
  4. LCOE with utilization contours overlaid

The min-cost 100%-served design point is starred on every chart.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.ticker as mticker
import numpy as np
from matplotlib.colors import LogNorm

import config as cfg
from charts import common
from viz import render

# Display scaling: model works in MW / MWh; charts show GW / GWh.
_GW  = 1e3
_GWh = 1e3

_UTIL_LEVELS = [50, 80, 90, 99, 99.9, 99.99]


def _draw_heatmap(ax, fig, Z, *, title, cbar_label, fmt=None,
                  vmin=None, vmax=None, log_scale=False,
                  add_contours=False, util_data=None,
                  contour_color="white", text_color="0.15"):
    hydro_gw = cfg.HYDRO_MW_MAX / _GW
    batt_gwh = cfg.BATTERY_MWH_MAX / _GWh
    x = np.linspace(0, batt_gwh, Z.shape[1])
    y = np.linspace(0, hydro_gw, Z.shape[0])

    if log_scale:
        valid = Z[np.isfinite(Z) & (Z > 0)]
        norm = LogNorm(vmin=valid.min() if len(valid) else 1,
                       vmax=valid.max() if len(valid) else 1e4)
        pcm = ax.pcolormesh(x, y, Z, cmap=cfg.CMAP, norm=norm, shading="nearest")
    else:
        pcm = ax.pcolormesh(x, y, Z, cmap=cfg.CMAP, vmin=vmin, vmax=vmax, shading="nearest")

    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(y[0], y[-1])

    cb = fig.colorbar(pcm, ax=ax, pad=0.02)
    cb.set_label(cbar_label, fontsize=9)
    if fmt and not log_scale:
        cb.ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
    elif log_scale:
        cb.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))

    ax.set_xlabel(cfg.axis_label("battery_gwh"), fontsize=9)
    ax.set_ylabel(cfg.axis_label("hydro_gw"), fontsize=9)
    ax.set_title(title, fontsize=10)

    # Utilization contour overlay (chart 4)
    if add_contours and util_data is not None:
        X, Y = np.meshgrid(x, y)
        cs = ax.contour(X, Y, util_data * 100, levels=_UTIL_LEVELS,
                        colors=contour_color, linewidths=0.7, alpha=0.7)
        ax.clabel(cs, fmt=lambda v: f"{v:g}%", fontsize=6.5, inline=True)

    common.add_source(ax, cfg.SOURCE_BPA, color=text_color)
    common.add_watermark(ax, color=text_color)


def _mark_point(ax, pt, *, color="white"):
    """Star the design point and annotate it."""
    bx = pt["battery_mwh"] / _GWh
    hy = pt["hydro_mw"] / _GW
    ax.plot(bx, hy, "*", color=color, markersize=15, zorder=10,
            markeredgecolor="0.2", markeredgewidth=0.6)
    label = (f"Min-cost @ ≥99.99% served\n"
             f"{hy:,.1f} GW · {bx:,.1f} GWh\n"
             f"Util {pt['utilization']*100:.3f}%\n"
             f"${pt['system_cost']/1e9:,.1f}B · ${pt['lcoe']:,.1f}/MWh")
    ax.annotate(label, xy=(bx, hy), xytext=(14, 10),
                textcoords="offset points", fontsize=7, color="0.1",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9,
                          edgecolor="0.5", linewidth=0.5),
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8))


def _box(stats, extra):
    return [
        f"Load: BPA 2024, exports excl.",
        f"Peak {stats['peak_mw']/_GW:,.1f} GW · mean {stats['mean_mw']/_GW:,.1f} GW",
        f"Hydro: $3M/MW · firm",
        f"Battery: $200k/MWh · {cfg.BATTERY_ROUNDTRIP_EFF:.0%} RT",
    ] + extra


def figures_heatmaps(results: dict, point: dict, stats: dict) -> list:
    out = cfg.OUTPUT_DIR / "heatmaps"

    def build_util():
        fig, ax = render.new_figure(figsize=(10, 7))
        _draw_heatmap(ax, fig, results["utilization"] * 100,
                      title="BPA hydro + battery — Utilization (% of 2024 load served)",
                      cbar_label="Utilization (%)",
                      fmt=lambda v, _: f"{v:.0f}%", vmin=0, vmax=100,
                      text_color="white")
        _mark_point(ax, point)
        common.add_box(ax, fig, _box(stats, ["Higher = more load served"]))
        return fig, out / "bpa_hydro_battery_utilization.png"

    def build_cost():
        fig, ax = render.new_figure(figsize=(10, 7))
        _draw_heatmap(ax, fig, results["system_cost"] / 1e9,
                      title="BPA hydro + battery — System Cost ($B capex)",
                      cbar_label="Total capex ($B)",
                      fmt=lambda v, _: f"${v:,.0f}B", text_color="white")
        _mark_point(ax, point)
        common.add_box(ax, fig, _box(stats, ["Total capital cost"]))
        return fig, out / "bpa_hydro_battery_cost.png"

    def build_lcoe():
        fig, ax = render.new_figure(figsize=(10, 7))
        _draw_heatmap(ax, fig, results["lcoe"],
                      title="BPA hydro + battery — LCOE ($/MWh served)",
                      cbar_label="LCOE ($/MWh)", log_scale=True)
        _mark_point(ax, point)
        common.add_box(ax, fig, _box(stats, ["Annualised cost / served energy"]))
        return fig, out / "bpa_hydro_battery_lcoe.png"

    def build_lcoe_util():
        fig, ax = render.new_figure(figsize=(10, 7))
        _draw_heatmap(ax, fig, results["lcoe"],
                      title="BPA hydro + battery — LCOE with utilization contours",
                      cbar_label="LCOE ($/MWh)", log_scale=True,
                      add_contours=True, util_data=results["utilization"],
                      contour_color="white", text_color="white")
        _mark_point(ax, point)
        common.add_box(ax, fig, _box(stats, ["Contours = utilization %"]))
        return fig, out / "bpa_hydro_battery_lcoe_utilization.png"

    return [
        ("util", build_util),
        ("cost", build_cost),
        ("lcoe", build_lcoe),
        ("lcoe_util", build_lcoe_util),
    ]


if __name__ == "__main__":
    import time
    from data_load import load_bpa_load, load_stats
    from model.simulate import run_sweep, min_cost_full_point

    t0 = time.time()
    df = load_bpa_load()
    stats = load_stats(df)
    res = run_sweep(df["load_mw"].to_numpy())
    pt = min_cost_full_point(res)
    plan = figures_heatmaps(res, pt, stats)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\n{len(plan)} heatmaps in {time.time()-t0:.1f}s")
