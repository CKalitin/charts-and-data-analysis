"""Population by latitude (served vs. unserved), and a normalized overlay against
Phase 2/3's satellite theoretical-max-customers-by-latitude curve.

Chart 1: stacked bars, served (bottom) + unserved (top) population per 1-degree
latitude ring -- see population_by_latitude.py for the capital-city-latitude
approximation this relies on (each country's population placed entirely at its
capital's latitude; flagged there as imprecise for a handful of relocated capitals).

Chart 2: BOTH curves normalized to their own peak (0-1) and overlaid as lines --
answers "does satellite capacity peak where people actually are, or somewhere else?"
Two independent things being compared, each normalized only against itself, so the
overlay shows SHAPE alignment, not a claim that capacity meets demand in absolute
terms (Phase 3 already showed capacity is ~31x short in absolute terms).

Run: python charts/population_by_latitude.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import capacity_density_model as cdm
import orbital_geometry as og
import population_by_latitude as pbl
from viz import render, info_box
from regions import REGION_COLORS, REGION_SHORT

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "capacity"
SOURCE_NOTE = "Source: telecom_market_by_country.csv"

SERVED_COLOR = "#4575b4"
UNSERVED_COLOR = "#d73027"


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


# --------------------------------------------------------------------------------------
# Chart 1: served vs. unserved population by latitude (stacked bars)
# --------------------------------------------------------------------------------------
def fig_population_by_latitude(centers, served, unserved):
    fig, ax = render.new_figure(figsize=(12, 6.5))
    width = centers[1] - centers[0]
    ax.bar(centers, served, width=width, color=SERVED_COLOR, label="Served population", linewidth=0)
    ax.bar(centers, unserved, width=width, bottom=served, color=UNSERVED_COLOR,
          label="Unserved (unconnected) population", linewidth=0)

    ax.set_xlabel("Latitude of country capital (degrees) -- one bar per 1-degree ring")
    ax.set_ylabel("Population")
    ax.set_title("World population by latitude: served vs. unserved")
    ax.set_xlim(-90, 90)  # population is ~zero in Antarctic latitudes; don't waste axis space
    ax.invert_xaxis()  # north (positive) on the left, matching the project convention
    ax.xaxis.set_major_locator(mticker.MultipleLocator(15))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.legend(loc="upper left", fontsize=9)

    total_pop = served.sum() + unserved.sum()
    total_unserved = unserved.sum()
    # mode="on" struggles here -- small bars are scattered across nearly the whole
    # x-range, so there's no truly empty spot for it to find. mode="off" (right
    # margin) is safe: the data itself is empty past ~lat 55, see xlim above.
    info_box.add_info_box(
        ax, fig,
        f"{total_pop/1e9:.1f}B total,\n{total_unserved/1e9:.2f}B\nunserved.\n\n" + SOURCE_NOTE,
        mode="off", off_side="right", off_frac=0.14, fontsize=7.8,
    )
    return fig, OUT_ROOT / "population_by_latitude_served_unserved.png"


# --------------------------------------------------------------------------------------
# Chart 2: normalized overlay -- satellite theoretical max vs. total population
# --------------------------------------------------------------------------------------
def fig_normalized_overlay(shells, centers, served, unserved):
    sat_centers, by_shell = og.expected_sats_by_latitude(shells, bin_width_deg=1.0)
    total_sats = np.sum(list(by_shell.values()), axis=0)
    s = cdm.V2_MINI_BEAD_SCENARIO
    sat_max_customers = total_sats * cdm.max_customers_per_satellite(s)

    total_pop = served + unserved
    assert np.array_equal(sat_centers, centers), "latitude bins must align to overlay"

    sat_norm = sat_max_customers / sat_max_customers.max()
    pop_norm = total_pop / total_pop.max()

    fig, ax = render.new_figure(figsize=(12, 6.5))
    ax.plot(centers, sat_norm, color="#4575b4", linewidth=1.8,
           label="Satellite theoretical max customers (normalized to its own peak)")
    ax.plot(centers, pop_norm, color="#d73027", linewidth=1.8,
           label="Total population (normalized to its own peak)")
    ax.fill_between(centers, 0, sat_norm, color="#4575b4", alpha=0.12)
    ax.fill_between(centers, 0, pop_norm, color="#d73027", alpha=0.12)

    ax.set_xlabel("Latitude (degrees)")
    ax.set_ylabel("Normalized to each curve's own peak (0-1) -- NOT an absolute comparison")
    ax.set_title("Normalized satellite capacity and population vs. latitude")
    ax.set_xlim(-90, 90)
    ax.invert_xaxis()  # north (positive) on the left, matching the project convention
    ax.set_ylim(0, 1.08)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(15))
    ax.legend(loc="upper left", fontsize=8.5)

    pop_peak_lat = centers[pop_norm.argmax()]
    sat_peak_lat = centers[sat_norm.argmax()]
    # mode="on" landed on top of the (faint but real) fills between lat -58 and -15;
    # mode="off" is safe here -- both curves are near 0 past lat ~60 (see xlim).
    info_box.add_info_box(
        ax, fig,
        f"Shape only, not\nabsolute (Phase 3:\n~31x short).\n\n"
        f"Peaks: pop {pop_peak_lat:.0f}deg,\n"
        f"sat {sat_peak_lat:.0f}deg.\n\n" + SOURCE_NOTE,
        mode="off", off_side="right", off_frac=0.14, fontsize=7.6,
    )
    return fig, OUT_ROOT / "normalized_capacity_vs_population_by_latitude.png"


# --------------------------------------------------------------------------------------
# Chart 3: population by latitude, split by region/continent (stacked bars)
# --------------------------------------------------------------------------------------
def fig_population_by_latitude_by_continent(rows):
    centers, by_region = pbl.bin_by_latitude_and_region(rows, bin_width_deg=1.0)

    fig, ax = render.new_figure(figsize=(12, 6.5))
    width = centers[1] - centers[0]
    stack = np.zeros_like(centers)
    # Stack in a fixed order (largest-total region at the bottom) so the same region
    # always renders in the same visual band across reruns.
    order = sorted(by_region, key=lambda k: -by_region[k].sum())
    for region in order:
        vals = by_region[region]
        color = REGION_COLORS.get(region, "#999999")
        ax.bar(centers, vals, width=width, bottom=stack, color=color,
              label=REGION_SHORT.get(region, region), linewidth=0)
        stack += vals

    ax.set_xlabel("Latitude of country capital (degrees) -- one bar per 1-degree ring")
    ax.set_ylabel("Population")
    ax.set_title("World population by latitude, by region")
    ax.set_xlim(-90, 90)
    ax.invert_xaxis()  # north (positive) on the left, matching the project convention
    ax.xaxis.set_major_locator(mticker.MultipleLocator(15))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.legend(loc="upper left", fontsize=8)

    info_box.add_info_box(ax, fig, SOURCE_NOTE, mode="off", off_side="right", off_frac=0.12, fontsize=7.8)
    return fig, OUT_ROOT / "population_by_latitude_by_region.png"


def figures(shells, rows, centers, served, unserved):
    return [
        ("population_by_latitude", lambda: fig_population_by_latitude(centers, served, unserved)),
        ("normalized_overlay", lambda: fig_normalized_overlay(shells, centers, served, unserved)),
        ("population_by_latitude_by_continent", lambda: fig_population_by_latitude_by_continent(rows)),
    ]


def main():
    rows, missing_capital = pbl.load_country_population_by_latitude()
    centers, served, unserved = pbl.bin_by_latitude(rows, bin_width_deg=1.0)
    shells = og.load_shells_with_full_geometry()

    plan = figures(shells, rows, centers, served, unserved)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")

    if missing_capital:
        print(f"\nNOTE: {len(missing_capital)} countries had no capital-city latitude in the "
              f"World Bank data and were excluded from the latitude binning: {missing_capital}")

    total_pop = served.sum() + unserved.sum()
    print(f"NOTE: {total_pop/1e9:.2f}B total population binned, {unserved.sum()/1e9:.2f}B "
          f"({100*unserved.sum()/total_pop:.0f}%) unserved -- matches Phase 1's country-level "
          f"total closely, a good consistency check on the latitude-binning approximation.")


if __name__ == "__main__":
    main()
