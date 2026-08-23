"""Satellite ground-coverage RANGE (how far to the sides a satellite can serve a
user, per orbital_geometry.py's new coverage-radius geometry) applied to the
satellite-density-by-latitude concept, then overlaid on the population-by-latitude
curve so the two can be compared directly.

Two charts:
  1. Satellite density by latitude -- sub-satellite-point-only (the ORIGINAL
     Phase 2 metric, "how many satellites are exactly overhead") vs. range-
     extended ("how many satellites could actually serve a user here, including
     ones whose coverage circle reaches this latitude from elsewhere"). Real
     shells (540-570km) each get their own coverage radius from their own
     altitude -- not a single shared number.
  2. The range-extended curve overlaid on population-by-latitude (twin y-axis,
     shared latitude x-axis) -- does satellite REACH concentrate where people are?

Run: python charts/satellite_range_coverage.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import orbital_geometry as og
import population_density_grid as pdg
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"
SOURCE_NOTE = "Source: starlink_shells.md + orbital_geometry.py (see ASSUMPTIONS.md #11)"


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


# --------------------------------------------------------------------------------------
# Chart 1: satellite density by latitude -- overhead-only vs. range-extended
# --------------------------------------------------------------------------------------
def fig_satellite_density_with_range(shells: list[og.Shell]):
    centers, raw_by_shell = og.expected_sats_by_latitude(shells)
    _, ext_by_shell = og.expected_sats_reaching_latitude(shells)
    raw_total = np.sum(list(raw_by_shell.values()), axis=0)
    ext_total = np.sum(list(ext_by_shell.values()), axis=0)

    fig, ax = render.new_figure(figsize=(9, 11))
    ax.barh(centers, ext_total, height=1.0, align="center", color="#fdae61", alpha=0.75, linewidth=0,
           label="Range-extended (satellites that can REACH this latitude)")
    ax.barh(centers, raw_total, height=1.0, align="center", color="#4575b4", alpha=0.9, linewidth=0,
           label="Overhead only (sub-satellite point exactly here)")

    ax.set_ylabel("Latitude (degrees)")
    ax.set_xlabel("Expected satellite count")
    ax.set_title("Satellite density by latitude,\noverhead-only vs. range-extended")
    ax.set_ylim(-90, 90)  # ascending, north at the top
    ax.yaxis.set_major_locator(mticker.MultipleLocator(15))
    ax.legend(loc="lower right", fontsize=8)

    info_box.add_info_box(
        ax, fig,
        f"Coverage radius ~{og.ground_range_km(shells[0].altitude_km):.0f}km/satellite "
        f"({og.MIN_ELEVATION_DEG:.0f}deg min. elevation).\n"
        f"Peak overhead: {raw_total.max():.0f} at {centers[raw_total.argmax()]:.0f}deg.\n"
        f"Peak range-extended: {ext_total.max():.0f} at {centers[ext_total.argmax()]:.0f}deg.\n"
        + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "satellite_density_by_latitude_with_range.png"


# --------------------------------------------------------------------------------------
# Chart 2: range-extended satellite density overlaid on population by latitude
# --------------------------------------------------------------------------------------
def fig_satellite_range_vs_population(shells: list[og.Shell], grid: pdg.PopulationGrid):
    sat_centers, ext_by_shell = og.expected_sats_reaching_latitude(shells)
    ext_total = np.sum(list(ext_by_shell.values()), axis=0)
    pop_centers, pop = pdg.population_by_latitude(grid, bin_width_deg=1.0)

    fig, ax1 = render.new_figure(figsize=(9, 11))
    ax1.barh(pop_centers, pop, height=1.0, align="center", color="#74add1", alpha=0.6, linewidth=0,
            label="Population")
    ax1.set_ylabel("Latitude (degrees)")
    ax1.set_xlabel("Population")
    ax1.set_ylim(-90, 90)  # ascending, north at the top
    ax1.yaxis.set_major_locator(mticker.MultipleLocator(15))
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))

    ax2 = ax1.twiny()  # shares the y-axis (latitude); independent x-axis on top
    ax2.plot(ext_total, sat_centers, color="#d73027", linewidth=2.2, label="Range-extended satellite density")
    ax2.set_xlabel("Expected satellites reaching this latitude")
    ax2.set_xlim(0, ext_total.max() * 1.15)

    h1, lab1 = ax1.get_legend_handles_labels()
    h2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, lab1 + lab2, loc="lower right", fontsize=8)

    ax1.set_title("Population and range-extended\nsatellite density vs. latitude")
    peak_pop_lat = pop_centers[pop.argmax()]
    peak_sat_lat = sat_centers[ext_total.argmax()]
    info_box.add_info_box(
        ax1, fig,
        f"Pop. peaks at {peak_pop_lat:.0f}deg; satellite reach peaks at {peak_sat_lat:.0f}deg --\n"
        "different mechanisms (demographics vs. orbital turning points).\n"
        + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "satellite_range_vs_population_by_latitude.png"


def figures(shells: list[og.Shell], grid: pdg.PopulationGrid):
    return [
        ("satellite_density_with_range", lambda: fig_satellite_density_with_range(shells)),
        ("satellite_range_vs_population", lambda: fig_satellite_range_vs_population(shells, grid)),
    ]


def main():
    shells = og.load_shells_with_full_geometry()
    grid = pdg.load_or_build_grid()
    plan = figures(shells, grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")


if __name__ == "__main__":
    main()
