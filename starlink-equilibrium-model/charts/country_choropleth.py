"""Shared per-country choropleth rendering -- Natural Earth 110m admin-0 country
boundaries (data/raw/ne_110m_admin_0_countries.geojson, downloaded 2026-08-14
specifically for the TAM model's price-by-country heatmap; a DIFFERENT file from
coverage_map.py's ne_110m_land.geojson, which has no per-country divisions at all).

Same "no cartopy/geopandas" convention as coverage_map.py -- plain matplotlib
Path/PathPatch, JSON-parsed by hand. One addition coverage_map.load_land_paths()
didn't need: Natural Earth's admin-0 file uses MultiPolygon geometries (countries
with islands/exclaves are multiple disconnected polygons), not just Polygon, so
this loader handles both.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np  # noqa: F401
from matplotlib.path import Path as MplPath  # noqa: F401
from matplotlib.patches import PathPatch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Boundary loading moved to the project root (country_geometry.py) so the model
# layer can use it too without importing upward from charts/. Re-exported here so
# existing `from country_choropleth import load_country_paths` callers still work.
from country_geometry import COUNTRIES_GEOJSON, load_country_paths, polygon_to_path  # noqa: F401

_polygon_to_path = polygon_to_path  # backwards-compatible alias


def draw_choropleth(ax, country_paths: dict[str, list["MplPath"]], values_by_iso3: dict[str, float],
                     cmap, norm, missing_color: str = "#e0e0e0", edge_color: str = "#999999"):
    """Draw every country in country_paths, colored by values_by_iso3[iso3] through
    cmap/norm -- countries with no value (missing from values_by_iso3, or NaN) get
    missing_color, so "no data" is visually distinct from "data at the low end of
    the scale," not silently merged into it."""
    for iso3, paths in country_paths.items():
        value = values_by_iso3.get(iso3)
        color = missing_color if (value is None or np.isnan(value)) else cmap(norm(value))
        for p in paths:
            ax.add_patch(PathPatch(p, facecolor=color, edgecolor=edge_color, linewidth=0.3, zorder=1))
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)
