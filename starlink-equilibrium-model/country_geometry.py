"""Natural Earth 110m admin-0 country boundaries as matplotlib Paths.

Lives at the project root, not under charts/, because it is consumed by BOTH the
chart layer (charts/country_choropleth.py, for choropleths) and the model layer
(household_grid.py, to attribute each lat/lon tile to a country). It was originally
written inside charts/country_choropleth.py; moving it here rather than copying it
keeps one source of truth and stops a model module having to import upward from the
chart layer.

Same "no cartopy/geopandas in this environment" convention as the rest of the
project -- plain matplotlib Path, JSON parsed by hand. Natural Earth's admin-0 file
uses MultiPolygon geometries (countries with islands/exclaves are several
disconnected polygons), so both Polygon and MultiPolygon are handled.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from matplotlib.path import Path as MplPath

COUNTRIES_GEOJSON = Path(__file__).resolve().parent / "data" / "raw" / "ne_110m_admin_0_countries.geojson"


def polygon_to_path(rings) -> MplPath:
    """One Polygon's rings (outer boundary + optional holes) -> one compound Path."""
    verts, codes = [], []
    for ring in rings:
        ring = np.asarray(ring)
        verts.append(ring)
        codes.append([MplPath.MOVETO] + [MplPath.LINETO] * (len(ring) - 2) + [MplPath.CLOSEPOLY])
    return MplPath(np.concatenate(verts), np.concatenate(codes))


def load_country_paths() -> dict[str, list[MplPath]]:
    """{iso3: [Path, ...]} -- a list because MultiPolygon countries (islands,
    exclaves) need more than one Path. Keyed by ADM0_A3, NOT ISO_A3 -- Natural
    Earth's ISO_A3 field is "-99" for 5 features (Norway, France, and 3 disputed
    territories this project doesn't need); ADM0_A3 has no such gaps."""
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
        out.setdefault(iso3, []).extend(polygon_to_path(rings) for rings in polygons)
    return out
