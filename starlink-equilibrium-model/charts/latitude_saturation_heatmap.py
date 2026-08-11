"""Latitude x satellite-count saturation heatmap -- answers "why does it take so
many satellites to fully serve the population" with a picture instead of a table.

Built after discovering (2026-08-11, see CLAUDE.md) that the long tail of the
serviceable-customers-vs-N curve is NOT a density-cap story for almost the whole
range -- from ~N=2M to full saturation (~N=6M), essentially 100% of the remaining
shortfall is AGGREGATE CAPACITY-bound (customers_per_satellite x satellites
overhead), not density-cap-bound. The real driver: the single most populous
latitude band on Earth (~26N, India/Bangladesh, ~279M people in one degree of
latitude) is far from where Starlink's real Gen1 shells concentrate satellites
(53N) -- a mismatch between orbital geometry and population geography, not a
density-per-cell problem at all. A world map can't show this (it's a
latitude x satellite-count relationship, not a spatial one); this heatmap can.

Run: python charts/latitude_saturation_heatmap.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.patheffects as path_effects
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.colors import LogNorm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import population_density_grid as pdg
import serviceable_customers_model as scm
from serviceable_customers_chart import GEN1_SATS, CURRENT_FLEET_SATS, SHELL_RATIO_NOTE, SOURCE_NOTE
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"

# Reference latitudes worth annotating directly on the heatmap.
LAT_ANNOTATIONS = [
    (26.5, "South Asia (peak pop., ~279M/deg)"),
    (53.0, "Starlink shell concentration (72% of sats)"),
]


LOG_COLOR_FLOOR = 1e-4  # 0.01% -- LogNorm can't take exact 0, so exact-0 cells are clipped up to this


def _draw_saturation_heatmap(ax, fig, frac_masked, sat_counts, lat_centers, *, log_color: bool):
    """Shared draw for both colorbar-scale variants -- everything except the
    color-mapping itself (norm, colorbar ticks/formatter) is identical."""
    cmap = mpl.colormaps["viridis"].copy()
    cmap.set_bad(color="0.92")  # bands with zero population: light grey, not "0% served"

    if log_color:
        # Clip only the non-masked (real) values up to the floor; NaN stays NaN so
        # it's still masked (grey), not colored as "0.01% served".
        clipped = np.ma.where(frac_masked.mask, frac_masked, np.maximum(frac_masked, LOG_COLOR_FLOOR))
        pcm = ax.pcolormesh(sat_counts, lat_centers, clipped, cmap=cmap,
                            norm=LogNorm(vmin=LOG_COLOR_FLOOR, vmax=1.0), shading="nearest")
    else:
        pcm = ax.pcolormesh(sat_counts, lat_centers, frac_masked, cmap=cmap, vmin=0, vmax=1, shading="nearest")

    halo = [path_effects.withStroke(linewidth=2.5, foreground="black")]
    for n, _label in [(GEN1_SATS, "Gen1 (4,408)"), (CURRENT_FLEET_SATS, "Current fleet (~10,900)")]:
        ax.axvline(n, color="white", linestyle=":", linewidth=1.1, alpha=0.85, zorder=3)
    for lat, label in LAT_ANNOTATIONS:
        ax.axhline(lat, color="white", linestyle="--", linewidth=0.8, alpha=0.6, zorder=3)
        ax.annotate(label, xy=(sat_counts[-1], lat), xytext=(-6, 4), textcoords="offset points",
                    fontsize=8, color="white", ha="right", va="bottom", path_effects=halo)
    # Fleet labels drawn after the latitude ones so their own halo isn't covered.
    for n, label in [(GEN1_SATS, "Gen1"), (CURRENT_FLEET_SATS, "Current fleet")]:
        ax.annotate(label, xy=(n, 88), xytext=(4, 0), textcoords="offset points",
                    fontsize=7.5, color="white", ha="left", va="top", rotation=90, path_effects=halo)

    ax.set_xscale("log")
    ax.set_xlim(sat_counts[0], sat_counts[-1])
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Total satellites (log scale)")
    ax.set_ylabel("Latitude (degrees)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    return pcm


def fig_latitude_saturation_heatmap(hist, dens_centers, lat_centers):
    sat_counts = np.geomspace(100, 8_000_000, 70)
    frac = scm.sweep_served_fraction_by_latitude(sat_counts, hist, dens_centers, lat_centers)
    frac_masked = np.ma.masked_invalid(frac.T)  # (n_lat, n_sats); NaN (no pop in band) -> transparent

    fig, ax = render.new_figure(figsize=(13, 8))
    pcm = _draw_saturation_heatmap(ax, fig, frac_masked, sat_counts, lat_centers, log_color=False)
    ax.set_title("Population served vs. total satellites, by latitude band")

    cbar = fig.colorbar(pcm, ax=ax, pad=0.015)
    cbar.set_label("% of that latitude band's population served")
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))

    info_box.add_info_box(
        ax, fig,
        "Grey = no population in that band. Almost all of the N=2M-6M tail is\n"
        "aggregate-capacity-bound (not density-cap-bound) -- see CLAUDE.md.\n"
        + SHELL_RATIO_NOTE + ". " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "latitude_saturation_heatmap.png"


def fig_latitude_saturation_heatmap_log(hist, dens_centers, lat_centers):
    sat_counts = np.geomspace(100, 8_000_000, 70)
    frac = scm.sweep_served_fraction_by_latitude(sat_counts, hist, dens_centers, lat_centers)
    frac_masked = np.ma.masked_invalid(frac.T)

    fig, ax = render.new_figure(figsize=(13, 8))
    pcm = _draw_saturation_heatmap(ax, fig, frac_masked, sat_counts, lat_centers, log_color=True)
    ax.set_title("Population served vs. total satellites, by latitude band (log color scale)")

    # Explicit ticks + FuncFormatter, NOT the default LogNorm formatter -- the
    # project's established fix (see charting-and-modeling skill's edge-case
    # catalog): LogNorm's default colorbar formatter renders literal
    # "$\\mathdefault{10^{-2}}$" text even with rcParams text.parse_math=False.
    cbar = fig.colorbar(pcm, ax=ax, pad=0.015)
    cbar.set_label("% of that latitude band's population served (log scale)")
    cbar.set_ticks([1e-4, 1e-3, 1e-2, 1e-1, 1.0])
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.2%}" if v < 0.01 else f"{v:.0%}"))

    info_box.add_info_box(
        ax, fig,
        "Log color scale -- reveals low-%-served structure the linear version hides.\n"
        f"0% clipped to {LOG_COLOR_FLOOR:.2%} (LogNorm floor). Grey = no population.\n"
        + SHELL_RATIO_NOTE + ". " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "latitude_saturation_heatmap_log.png"


def figures(grid: pdg.PopulationGrid):
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    return [
        ("latitude_saturation_heatmap", lambda: fig_latitude_saturation_heatmap(hist, dens_centers, lat_centers)),
        ("latitude_saturation_heatmap_log",
         lambda: fig_latitude_saturation_heatmap_log(hist, dens_centers, lat_centers)),
    ]


def main():
    grid = pdg.load_or_build_grid()
    plan = figures(grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")


if __name__ == "__main__":
    main()
