"""Satellite capacity UTILIZATION -- % of available satellite capacity actually
used to serve customers (served/supply), a DIFFERENT question from the
serviceable-customers family's served/population -- see
serviceable_customers_model.capacity_utilization_by_latitude()'s docstring.
User request 2026-08-14.

Two charts:
  1. utilization_vs_satellites(_linear).png -- global aggregate utilization vs.
     total satellites, same "vs. satellite count" family as the serviceable-
     customers charts (satellite count on the bottom x-axis, cumulative max
     capacity in Tbps on a secondary top axis).
  2. utilization_heatmap_world.png -- the requested "corollary" world-map view, at
     one fixed N. Per the user's own expectation and this session's scoping
     discussion: the underlying model is latitude-only (no per-country/per-cell
     distinction in satellite supply), so this map shows genuine horizontal
     STRIPES -- the same utilization value at every longitude within a 1deg
     latitude band -- not per-cell variation like the population density map. This
     is an honest rendering of what the model actually computes, not a
     simplification of a richer 2D result.

Run: python charts/satellite_utilization.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np
from matplotlib.colors import Normalize

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import population_density_grid as pdg
import serviceable_customers_model as scm
from coverage_map import draw_world_basemap, load_land_paths
from serviceable_customers_chart import (
    SHELL_RATIO_NOTE, SOURCE_NOTE, _add_capacity_secondary_axis, _add_fleet_reference_lines, CURRENT_FLEET_SATS,
)
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"


def _pct_formatter(x, _pos):
    return f"{x:.0%}" if x >= 0.01 else f"{x:.1%}"


# --------------------------------------------------------------------------------------
# Chart 1: global aggregate utilization vs. total satellites
# --------------------------------------------------------------------------------------
def fig_utilization_vs_satellites(hist, dens_centers, lat_centers):
    sat_counts = np.geomspace(1, 2_000_000, 46)
    util = scm.sweep_capacity_utilization(sat_counts, hist, dens_centers, lat_centers)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, util, color="#4575b4", linewidth=2, label="Capacity utilization (global)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    _add_capacity_secondary_axis(ax)  # AFTER set_xscale -- see its docstring
    ax.set_xlabel("Total satellites (log scale)")
    ax.set_ylabel("% of available satellite capacity used (log scale)")
    ax.set_title("Satellite capacity utilization vs. total satellites")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pct_formatter))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.legend(loc="lower left", fontsize=8.5)

    info_box.add_info_box(
        ax, fig,
        f"Peak utilization {util.max():.1%} near N={sat_counts[util.argmax()]:,.0f}.\n"
        "Monotonically decaying for this scenario -- V3's huge per-satellite\n"
        "capacity means demand, not supply, is scarce almost everywhere. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "utilization_vs_satellites.png"


UTIL_LINEAR_MAX_SATS = 2_000_000


def fig_utilization_vs_satellites_linear(hist, dens_centers, lat_centers):
    sat_counts = np.linspace(1, UTIL_LINEAR_MAX_SATS, 200)
    util = scm.sweep_capacity_utilization(sat_counts, hist, dens_centers, lat_centers)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, util, color="#4575b4", linewidth=2, label="Capacity utilization (global)")
    _add_fleet_reference_lines(ax)

    ax.set_xlim(0, UTIL_LINEAR_MAX_SATS)
    ax.set_ylim(0, util.max() * 1.08)
    _add_capacity_secondary_axis(ax)
    ax.set_xlabel("Total satellites (linear scale)")
    ax.set_ylabel("% of available satellite capacity used (linear scale)")
    ax.set_title("Satellite capacity utilization vs. total satellites (linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.legend(loc="upper right", fontsize=8.5)

    info_box.add_info_box(
        ax, fig,
        "Same data as the log version, linear axes -- most of the visible\n"
        "range already sits near the low-utilization tail. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "utilization_vs_satellites_linear.png"


# --------------------------------------------------------------------------------------
# Chart 2: world-map utilization heatmap at one fixed N (latitude-striped, see module docstring)
# --------------------------------------------------------------------------------------
UTIL_MAP_SATS = CURRENT_FLEET_SATS  # today's real constellation size -- concrete, not arbitrary


def fig_utilization_heatmap_world(hist, dens_centers, lat_centers, land_paths):
    util = scm.capacity_utilization_by_latitude(UTIL_MAP_SATS, hist, dens_centers, lat_centers)
    lat_edges = np.arange(-90, 90 + scm.BIN_WIDTH_DEG, scm.BIN_WIDTH_DEG)
    lon_edges = np.array([-180.0, 180.0])
    data = np.ma.masked_invalid(util[:, None])  # (n_lat, 1) -- constant across longitude, by construction

    fig, ax = render.new_figure(figsize=(16, 9))
    draw_world_basemap(ax, land_paths)

    import matplotlib as mpl
    cmap = mpl.colormaps["viridis"].copy()
    cmap.set_bad(alpha=0)  # uncovered / no-supply bands: basemap shows through, not a color
    pcm = ax.pcolormesh(lon_edges, lat_edges, data, cmap=cmap, norm=Normalize(vmin=0, vmax=1),
                        shading="flat", zorder=2, alpha=0.85)

    cbar = fig.colorbar(pcm, ax=ax, pad=0.015, shrink=0.65)
    cbar.set_label("% of available satellite capacity used")
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))

    ax.set_title(f"Satellite capacity utilization by latitude, world map (N={UTIL_MAP_SATS:,} satellites)")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)

    info_box.add_info_box(
        ax, fig,
        f"Latitude-striped, not per-country: this model computes utilization\n"
        "per latitude band only (no per-country/per-cell supply distinction),\n"
        "so every longitude at a given latitude shows the SAME value -- an\n"
        "honest rendering of the model, not a simplified 2D result.\n"
        f"{SHELL_RATIO_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "utilization_heatmap_world.png"


def figures(grid: pdg.PopulationGrid, land_paths):
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    return [
        ("utilization_vs_satellites", lambda: fig_utilization_vs_satellites(hist, dens_centers, lat_centers)),
        ("utilization_vs_satellites_linear",
         lambda: fig_utilization_vs_satellites_linear(hist, dens_centers, lat_centers)),
        ("utilization_heatmap_world", lambda: fig_utilization_heatmap_world(hist, dens_centers, lat_centers, land_paths)),
    ]


def main():
    grid = pdg.load_or_build_grid()
    land_paths = load_land_paths()
    plan = figures(grid, land_paths)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")


if __name__ == "__main__":
    main()
