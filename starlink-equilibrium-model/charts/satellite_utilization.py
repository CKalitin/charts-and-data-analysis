"""Satellite capacity UTILIZATION -- % of available satellite capacity actually
used to serve customers (served/supply), a DIFFERENT question from the
serviceable-customers family's served/population.

MIGRATED 2026-09-05 from serviceable_customers_model.py's latitude-only functions
to tile_capacity_model.py's 2D (lat x lon) allocation. That model pooled satellite
capacity around whole 40,000 km latitude rings and used a density cap derived from
orbital_geometry.expected_sats_reaching_latitude(), which overcounts satellites in
view by ~19x (it sums every satellite at a given LATITUDE regardless of longitude,
not the ones actually within reach -- see LONGITUDE_FOV_CAPACITY_REVIEW.md). The
world-map utilization heatmap this file used to draw is retired outright rather than
migrated: charts/tile_utilization_map.py already renders the same question correctly
per TILE instead of as latitude stripes, so keeping this one would just be a worse
duplicate.

Sweeps here use COARSER (2deg) tiles than the 1deg production model. Each solve
costs ~15s at 1deg but ~2s at 2deg, and a smooth "vs satellite count" line needs
dozens of solves; validated against 1deg at a few points, 2deg differs by <0.5% on
these global totals (tile_capacity_validation.py's own cross-resolution check found
a similar <1% spread). The per-tile utilization MAP (tile_utilization_map.py) still
solves at the full 1deg resolution for its handful of fixed fleet sizes.

Run: python charts/satellite_utilization.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tile_capacity_model as tcm
from serviceable_customers_chart import _add_capacity_secondary_axis, _add_fleet_reference_lines
from viz import render

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"

#: Coarser than the production 1deg grid -- see module docstring for why that's fine
#: for a global total, and results/tile_capacity/ for the full-resolution per-tile maps.
SWEEP_TILE_DEG = 2.0


def _pct_formatter(x, _pos):
    return f"{x:.0%}" if x >= 0.01 else f"{x:.1%}"


def _sweep(sat_counts, tile, demand):
    return np.array([tcm.fleet_utilization(r) for r in tcm.sweep(sat_counts, tile=tile, demand=demand)])


# --------------------------------------------------------------------------------------
# Chart 1: global aggregate utilization vs. total satellites
# --------------------------------------------------------------------------------------
def fig_utilization_vs_satellites(tile, demand):
    sat_counts = np.geomspace(1, 2_000_000, 30)
    util = _sweep(sat_counts, tile, demand)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, util, color="#4575b4", linewidth=2, label="Capacity utilization (global)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    _add_capacity_secondary_axis(ax)  # AFTER set_xscale -- see its docstring
    ax.set_xlabel("Total satellites (V3, log scale)")
    ax.set_ylabel("% of available satellite capacity used (log scale)")
    ax.set_title("Satellite capacity utilization vs. total satellites")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pct_formatter))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.legend(loc="lower left", fontsize=8.5)

    return fig, OUT_ROOT / "utilization_vs_satellites.png"


UTIL_LINEAR_MAX_SATS = 2_000_000


def fig_utilization_vs_satellites_linear(tile, demand):
    sat_counts = np.linspace(1, UTIL_LINEAR_MAX_SATS, 60)
    util = _sweep(sat_counts, tile, demand)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, util, color="#4575b4", linewidth=2, label="Capacity utilization (global)")
    _add_fleet_reference_lines(ax)

    ax.set_xlim(0, UTIL_LINEAR_MAX_SATS)
    ax.set_ylim(0, util.max() * 1.08)
    _add_capacity_secondary_axis(ax)
    ax.set_xlabel("Total satellites (V3, linear scale)")
    ax.set_ylabel("% of available satellite capacity used (linear scale)")
    ax.set_title("Satellite capacity utilization vs. total satellites (linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.legend(loc="upper right", fontsize=8.5)

    return fig, OUT_ROOT / "utilization_vs_satellites_linear.png"


def figures(tile=None, demand=None):
    tile = tile if tile is not None else tcm.make_tile_grid(SWEEP_TILE_DEG)
    demand = demand if demand is not None else tcm.build_demand(tile)
    return [
        ("utilization_vs_satellites", lambda: fig_utilization_vs_satellites(tile, demand)),
        ("utilization_vs_satellites_linear", lambda: fig_utilization_vs_satellites_linear(tile, demand)),
    ]


def main():
    tile = tcm.make_tile_grid(SWEEP_TILE_DEG)
    demand = tcm.build_demand(tile)
    plan = figures(tile, demand)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")


if __name__ == "__main__":
    main()
