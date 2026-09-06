"""Latitude x satellite-count saturation heatmap -- answers "why does it take so
many satellites to fully serve the population" with a picture instead of a table.

MIGRATED 2026-09-05 from serviceable_customers_model.py's latitude-only served-
fraction to a population-weighted MARGINAL of tile_capacity_model.py's 2D (lat x
lon) allocation. The old function derived this from the ring-pooled density cap
(og.expected_sats_reaching_latitude(), ~19x too generous -- see
LONGITUDE_FOV_CAPACITY_REVIEW.md); here there is no separate latitude-only
computation to get wrong -- served_fraction_by_latitude() is a straight population-
weighted readout of the already-correct 2D solve (tile_capacity_model.py).

Built after discovering (2026-08-11, see CLAUDE.md) that the long tail of the
serviceable-customers-vs-N curve is NOT a density-cap story for almost the whole
range -- a mismatch between orbital geometry (Starlink's real Gen1 shells
concentrate satellites at 53N) and population geography (the single most populous
latitude band on Earth is ~26N, India/Bangladesh). A world map can't show this
(it's a latitude x satellite-count relationship, not a spatial one); this heatmap
can. That finding was about the AGGREGATE capacity term (customers_per_satellite x
satellites overhead), which the longitude bug never touched -- so the mechanism
described above is unaffected by this migration; only the density-cap side of the
"is this band saturated" question was wrong before.

Sweeps here use COARSER (2deg) tiles than the 1deg production model -- see
satellite_utilization.py's docstring for the validated <0.5% difference on global
totals; the same reasoning applies to this per-latitude marginal.

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

import tile_capacity_model as tcm
from serviceable_customers_chart import ESTIMATED_CURRENT_CAPACITY_SATS, SOURCE_NOTE, _add_capacity_secondary_axis
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"

#: Coarser than the production 1deg grid -- see satellite_utilization.py's docstring.
SWEEP_TILE_DEG = 2.0

TILE_SHELL_NOTE = "Real Gen1 shells: 53.0/53.2/70.0/97.6deg, real 25deg-elevation coverage disks"

# Reference latitudes worth annotating directly on the heatmap.
LAT_ANNOTATIONS = [
    (26.5, "South Asia (peak pop., ~279M/deg)"),
    (53.0, "Starlink shell concentration (72% of sats)"),
]

LOG_COLOR_FLOOR = 1e-4  # 0.01% -- LogNorm can't take exact 0, so exact-0 cells are clipped up to this


def _sweep_served_fraction_by_latitude(sat_counts, tile, demand):
    """(n_lat, n_sats) served-fraction grid -- ONE tile-model solve per N, reused by
    both colorbar-scale variants. The old file ran an equivalent sweep TWICE (once
    per figure function); computed once here instead."""
    cache: dict = {}
    results = tcm.sweep(sat_counts, tile=tile, demand=demand, operator_cache=cache)
    frac = np.array([tcm.served_fraction_by_latitude(r, tile) for r in results])  # (n_sats, n_lat)
    return frac.T  # (n_lat, n_sats), matching pcolormesh(x=sat_counts, y=lat_centers, ...)


def _mask_uncovered_bands(frac_masked):
    """Bands with real population that sit permanently beyond every shell's coverage
    (e.g. ~83deg, just past the near-polar shell's ~82.4deg reach) read as 0% served
    at every satellite count in the sweep -- rendered as a solid dark-purple line
    running the full width of the chart, which reads as a rendering glitch rather
    than a real result. Mask those rows the same way as true no-population rows
    (grey), since "never reachable regardless of fleet size" and "no one lives here"
    both mean the same thing for this chart's purpose: nothing to show."""
    never_served = ~frac_masked.mask.all(axis=1) & (np.ma.filled(frac_masked, 0).max(axis=1) == 0)
    return np.ma.masked_where(np.broadcast_to(never_served[:, None], frac_masked.shape), frac_masked)


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
    ax.axvline(ESTIMATED_CURRENT_CAPACITY_SATS, color="white", linestyle=":", linewidth=1.1, alpha=0.85, zorder=3)
    for lat, label in LAT_ANNOTATIONS:
        ax.axhline(lat, color="white", linestyle="--", linewidth=0.8, alpha=0.6, zorder=3)
        ax.annotate(label, xy=(sat_counts[-1], lat), xytext=(-6, 4), textcoords="offset points",
                    fontsize=8, color="white", ha="right", va="bottom", path_effects=halo)
    # Fleet label drawn after the latitude ones so its own halo isn't covered.
    ax.annotate("Estimated current capacity", xy=(ESTIMATED_CURRENT_CAPACITY_SATS, 88), xytext=(4, 0),
                textcoords="offset points", fontsize=7.5, color="white", ha="left", va="top", rotation=90,
                path_effects=halo)

    ax.set_xscale("log")
    ax.set_xlim(sat_counts[0], sat_counts[-1])
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Total satellites (V3, log scale)")
    ax.set_ylabel("Latitude (degrees)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    _add_capacity_secondary_axis(ax)
    return pcm


def fig_latitude_saturation_heatmap(frac, sat_counts, lat_centers):
    frac_masked = np.ma.masked_invalid(frac)  # (n_lat, n_sats); NaN (no pop in band) -> transparent
    frac_masked = _mask_uncovered_bands(frac_masked)

    fig, ax = render.new_figure(figsize=(13, 8))
    pcm = _draw_saturation_heatmap(ax, fig, frac_masked, sat_counts, lat_centers, log_color=False)
    ax.set_title("Population served vs. total satellites, by latitude band")

    cbar = fig.colorbar(pcm, ax=ax, pad=0.015)
    cbar.set_label("% of that latitude band's population served")
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))

    info_box.add_info_box(
        ax, fig,
        "Grey = no population, or permanently beyond satellite coverage.\n"
        "Almost all of the N=2M-6M tail is aggregate-capacity-bound,\n"
        "not density-cap-bound.\n"
        + TILE_SHELL_NOTE + ". " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "latitude_saturation_heatmap.png"


def fig_latitude_saturation_heatmap_log(frac, sat_counts, lat_centers):
    frac_masked = np.ma.masked_invalid(frac)
    frac_masked = _mask_uncovered_bands(frac_masked)

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
        f"0% clipped to {LOG_COLOR_FLOOR:.2%} (LogNorm floor).\n"
        "Grey = no population, or permanently beyond satellite coverage.\n"
        + TILE_SHELL_NOTE + ". " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "latitude_saturation_heatmap_log.png"


def figures(tile=None, demand=None):
    tile = tile if tile is not None else tcm.make_tile_grid(SWEEP_TILE_DEG)
    demand = demand if demand is not None else tcm.build_demand(tile)
    sat_counts = np.geomspace(100, 8_000_000, 70)
    frac = _sweep_served_fraction_by_latitude(sat_counts, tile, demand)
    return [
        ("latitude_saturation_heatmap",
         lambda: fig_latitude_saturation_heatmap(frac, sat_counts, tile.lat_centers)),
        ("latitude_saturation_heatmap_log",
         lambda: fig_latitude_saturation_heatmap_log(frac, sat_counts, tile.lat_centers)),
    ]


def main():
    plan = figures()
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")


if __name__ == "__main__":
    main()
