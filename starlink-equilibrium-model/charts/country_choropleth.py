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

import json
from pathlib import Path

import numpy as np
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch

COUNTRIES_GEOJSON = Path(__file__).resolve().parent.parent / "data" / "raw" / "ne_110m_admin_0_countries.geojson"


def _polygon_to_path(rings) -> MplPath:
    """One Polygon's rings (outer boundary + optional holes) -> one compound Path."""
    verts, codes = [], []
    for ring in rings:
        ring = np.asarray(ring)
        verts.append(ring)
        codes.append([MplPath.MOVETO] + [MplPath.LINETO] * (len(ring) - 2) + [MplPath.CLOSEPOLY])
    return MplPath(np.concatenate(verts), np.concatenate(codes))


def load_country_paths() -> dict[str, list[MplPath]]:
    """{iso3: [Path, ...]} -- a list because MultiPolygon countries (islands,
    exclaves) need more than one Path to render correctly. Keyed by ADM0_A3, NOT
    ISO_A3 -- Natural Earth's ISO_A3 field is "-99" for 5 features (Norway,
    France, and 3 disputed territories this project doesn't need), ADM0_A3 has no
    such gaps."""
    d = json.load(open(COUNTRIES_GEOJSON, encoding="utf-8"))
    out: dict[str, list[MplPath]] = {}
    for feat in d["features"]:
        iso3 = feat["properties"].get("ADM0_A3")
        if not iso3:
            continue
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            polygons = [geom["coordinates"]]
        elif geom["type"] == "MultiPolygon":
            polygons = geom["coordinates"]
        else:
            continue
        out.setdefault(iso3, []).extend(_polygon_to_path(rings) for rings in polygons)
    return out


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
