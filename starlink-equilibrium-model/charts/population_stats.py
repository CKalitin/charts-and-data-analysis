"""Population-vs-latitude and population-vs-density-histogram charts, built directly
from the gridded WorldPop data (population_density_grid.py) -- a materially more
accurate replacement for the old capital-city-latitude approximation in
population_by_latitude.py (Phase 3 addendum): every populated grid cell contributes
at its own real latitude, not its whole country's population lumped at one point.

Run: python charts/population_stats.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import population_density_grid as pdg
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"
SOURCE_NOTE = "Source: WorldPop, University of Southampton"


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


# --------------------------------------------------------------------------------------
# Chart 1: population vs. latitude, global, gridded (replaces the old capital-city proxy).
# North-up (latitude on y, population on x) -- easier to read at a glance since humans
# default to "north = up" (a map orientation), not "north = left". An earlier
# latitude-on-x version (population_by_latitude_gridded.png) was deleted once this one
# existed as a strict superset (same data, better orientation) -- see CLAUDE.md.
# --------------------------------------------------------------------------------------
def fig_population_by_latitude_horizontal(grid: pdg.PopulationGrid):
    centers, pop = pdg.population_by_latitude(grid, bin_width_deg=1.0)

    fig, ax = render.new_figure(figsize=(8.5, 10.5))
    ax.barh(centers, pop, height=1.0, align="center", color="#4575b4", alpha=0.85, linewidth=0)
    ax.set_ylabel("Latitude (degrees)")
    ax.set_xlabel("Population")
    ax.set_title("Population vs. latitude (north up)")
    ax.set_ylim(-90, 90)  # ascending, north at the top -- no inversion needed (map convention)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(15))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))

    peak_lat = centers[pop.argmax()]
    info_box.add_info_box(
        ax, fig,
        f"Peak: {_pop_formatter(pop.max(), None)} at {peak_lat:.0f}deg.\n"
        f"{grid.n_countries} countries, gridded.\n" + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "population_by_latitude_horizontal.png"


# --------------------------------------------------------------------------------------
# Chart 2: population vs. population density, histogram (one figure per region)
# --------------------------------------------------------------------------------------
DENSITY_BIN_EDGES = np.logspace(-1, 5.1, 32)  # 0.1 to ~126,000 people/km^2, log-spaced


def population_density_histogram(grid: pdg.PopulationGrid):
    pop_cell = pdg.cell_population(grid).ravel()
    density_cell = grid.density.ravel()
    valid = ~np.isnan(density_cell) & (density_cell > 0)
    hist, edges = np.histogram(density_cell[valid], bins=DENSITY_BIN_EDGES, weights=pop_cell[valid])
    return edges, hist


def fig_population_vs_density_histogram(grid: pdg.PopulationGrid, region_label: str, out_name: str):
    edges, hist = population_density_histogram(grid)
    centers = np.sqrt(edges[:-1] * edges[1:])  # geometric center, correct for log bins
    widths = np.diff(edges)

    fig, ax = render.new_figure(figsize=(11, 6.5))
    ax.bar(edges[:-1], hist, width=widths, align="edge", color="#fc8d59", edgecolor="white", linewidth=0.3)
    ax.set_xscale("log")
    ax.set_xlabel("Population density (people/km2, log scale)")
    ax.set_ylabel("Population (in this density bracket)")
    ax.set_title(f"Population vs. population density -- {region_label}")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}" if v >= 1 else f"{v:g}"))

    total = hist.sum()
    median_density = _weighted_median(centers, hist)
    info_box.add_info_box(
        ax, fig,
        f"{_pop_formatter(total, None)} total. Median density: {median_density:,.0f}/km2. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / out_name


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum = np.cumsum(w)
    if cum[-1] <= 0:
        return float("nan")
    idx = np.searchsorted(cum, cum[-1] / 2.0)
    return float(v[min(idx, len(v) - 1)])


def figures(global_grid: pdg.PopulationGrid, us_grid: pdg.PopulationGrid):
    return [
        ("population_by_latitude_horizontal", lambda: fig_population_by_latitude_horizontal(global_grid)),
        ("density_histogram_global", lambda: fig_population_vs_density_histogram(
            global_grid, "global", "population_vs_density_histogram_global.png")),
        ("density_histogram_us", lambda: fig_population_vs_density_histogram(
            us_grid, "United States", "population_vs_density_histogram_us.png")),
    ]


def main():
    global_grid = pdg.load_or_build_grid()
    us_grid = pdg.load_country_density_grid("USA")
    plan = figures(global_grid, us_grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")


if __name__ == "__main__":
    main()
