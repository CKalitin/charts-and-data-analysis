"""World population density heatmap, overlaid on the same land-outline basemap used
by Phase 2's coverage_map.py (Natural Earth 110m land polygons, no cartopy/geopandas).

Data: WorldPop 1km unconstrained population density, ~2020, per country
(data/raw/worldpop/{iso3}_pd_1km.tif via download_worldpop.py), mosaicked to a single
0.1deg global grid by population_density_grid.py (block-averaged, cached as .npz --
see that module's docstring for why a direct global array isn't possible).

Run: python charts/population_density_map.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np
from matplotlib.colors import LogNorm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import population_density_grid as pdg
from coverage_map import draw_world_basemap, load_land_paths
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"
SOURCE_NOTE = "Source: WorldPop 1km pop. density ~2020, via download_worldpop.py"

DENSITY_FLOOR = 1.0  # people/km^2 -- below this, land is shown as basemap (uninhabited/rural)
COLOR_TICKS = [1, 10, 100, 1000, 10_000]


def fig_population_density_heatmap(grid: pdg.PopulationGrid, land_paths):
    fig, ax = render.new_figure(figsize=(16, 9))
    draw_world_basemap(ax, land_paths)

    density = np.ma.masked_where(~(grid.density >= DENSITY_FLOOR), grid.density)
    cmap = _density_cmap()
    vmax = float(np.nanmax(grid.density))
    pcm = ax.pcolormesh(
        grid.lon_edges, grid.lat_edges, density,
        cmap=cmap, norm=LogNorm(vmin=DENSITY_FLOOR, vmax=vmax),
        shading="flat", zorder=2,
    )

    cbar = fig.colorbar(pcm, ax=ax, pad=0.015, shrink=0.65)
    cbar.set_label("Population density (people/km2, log scale)")
    ticks = [t for t in COLOR_TICKS if t <= vmax] + [round(vmax, -2 if vmax > 1000 else 0)]
    cbar.set_ticks(ticks)
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

    ax.set_title("Population density (people/km2) vs. longitude and latitude")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)  # WorldPop has near-zero data in Antarctica; don't render dead space

    n_missing = len(grid.missing_iso3)
    info_box.add_info_box(
        ax, fig,
        f"{grid.n_countries} countries, 0.1deg grid. "
        f"Missing: {', '.join(grid.missing_iso3)} (no WorldPop data). " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "population_density_heatmap.png"


def _density_cmap():
    import matplotlib as mpl

    cmap = mpl.colormaps["plasma"].copy()
    cmap.set_bad(alpha=0)  # below-floor / no-data cells: fully transparent, basemap shows through
    return cmap


def figures(grid: pdg.PopulationGrid, land_paths):
    return [
        ("population_density_heatmap", lambda: fig_population_density_heatmap(grid, land_paths)),
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
