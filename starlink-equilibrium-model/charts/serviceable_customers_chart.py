"""Serviceable customers vs. total satellite count -- combines orbital latitude
density, Phase 3's per-satellite/per-km2 capacity caps, and the WorldPop gridded
population data into one curve. See serviceable_customers_model.py for the full
mechanism (local per-latitude-band min of supply vs. demand, then summed).

Two chart families here:
  1. Global curve, one resolution (1km -- the only data available worldwide).
  2. US-only curve, TWO resolutions overlaid (1km vs. 100m) -- shows how much the
     model's output changes when the underlying population data is finer-grained.

Run: python charts/serviceable_customers_chart.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import population_density_grid as pdg
import serviceable_customers_model as scm
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"
SOURCE_NOTE = "Source: WorldPop pop. density + capacity_density_model.py + orbital_geometry.py"

# Known real constellation sizes, for reference lines (see starlink_shells.md / CLAUDE.md).
GEN1_SATS = 4408
CURRENT_FLEET_SATS = 10_900

SHELL_RATIO_NOTE = "Shells: 45deg x5 : 65deg x1 : 80deg x1 (rough ratio)"


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


def _add_fleet_reference_lines(ax):
    for n, label in [(GEN1_SATS, "Gen1 (4,408)"), (CURRENT_FLEET_SATS, "Current fleet (~10,900)")]:
        ax.axvline(n, color="0.5", linestyle=":", linewidth=1.0, zorder=1)
        ax.annotate(label, xy=(n, 1), xycoords=("data", "axes fraction"), xytext=(4, -4),
                    textcoords="offset points", fontsize=7.5, color="0.4", ha="left", va="top", rotation=90)


def _draw_curve(ax, sat_counts, served, color, label):
    ax.plot(sat_counts, served, color=color, linewidth=2, label=label, zorder=3)
    ceiling = served[-1]
    ax.axhline(ceiling, color=color, linestyle="--", linewidth=0.9, alpha=0.6, zorder=2)


# --------------------------------------------------------------------------------------
# Chart 1: global, 1km resolution
# --------------------------------------------------------------------------------------
def fig_serviceable_vs_satellites_global(grid: pdg.PopulationGrid):
    sat_counts = np.geomspace(100, 2_000_000, 40)
    served = scm.sweep_serviceable_customers(sat_counts, grid)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_curve(ax, sat_counts, served, "#4575b4", "Serviceable customers (global, 1km data)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Total satellites (log scale)")
    ax.set_ylabel("Serviceable customers (log scale)")
    ax.set_title("Serviceable customers vs. total satellites -- global")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.legend(loc="lower right", fontsize=8.5)

    max_lat = scm.max_latitude_covered()
    info_box.add_info_box(
        ax, fig,
        f"Ceiling: {_pop_formatter(served[-1], None)} (density-capped population, {max_lat:.0f}deg coverage).\n"
        f"{SHELL_RATIO_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_global.png"


def figures(grid: pdg.PopulationGrid):
    return [
        ("serviceable_global", lambda: fig_serviceable_vs_satellites_global(grid)),
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
