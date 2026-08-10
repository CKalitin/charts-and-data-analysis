"""Phase 2: world map of Starlink orbital coverage bands + ground tracks, plus a
satellite-density-by-latitude chart.

Uses the well-sourced Gen1 5-sub-shell geometry (data/starlink_shells.csv +
orbital_geometry.py) -- see starlink_shells.md for why Gen2/2026-relocation shells
are excluded from the density calc (no public plane-count data for them).

World land outline: Natural Earth 110m land polygons (data/raw/ne_110m_land.geojson),
rendered directly with matplotlib Path/PathPatch -- no cartopy/geopandas dependency.

Run: python charts/coverage_map.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import orbital_geometry as og
from viz import render, info_box

LAND_GEOJSON = Path(__file__).resolve().parent.parent / "data" / "raw" / "ne_110m_land.geojson"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "coverage"

SOURCE_NOTE = "Source: starlink_shells.md"

# One representative color per distinct inclination present in the well-sourced shells.
INCLINATION_COLORS = {
    53.0: "#4575b4",
    53.2: "#4575b4",
    70.0: "#1a9850",
    97.6: "#d73027",
}
INCLINATION_LABELS = {
    53.0: "53.0deg shell (Gen1)",
    53.2: "53.2deg shell (Gen1)",
    70.0: "70.0deg shell (Gen1)",
    97.6: "97.6deg shell (Gen1, near-polar)",
}


def load_land_paths():
    d = json.load(open(LAND_GEOJSON, encoding="utf-8"))
    paths = []
    for feat in d["features"]:
        rings = feat["geometry"]["coordinates"]
        verts, codes = [], []
        for ring in rings:
            ring = np.asarray(ring)
            verts.append(ring)
            codes.append([MplPath.MOVETO] + [MplPath.LINETO] * (len(ring) - 2) + [MplPath.CLOSEPOLY])
        verts = np.concatenate(verts)
        codes = np.concatenate(codes)
        paths.append(MplPath(verts, codes))
    return paths


def draw_world_basemap(ax, land_paths):
    for p in land_paths:
        ax.add_patch(PathPatch(p, facecolor="#e0e0e0", edgecolor="#999999", linewidth=0.3, zorder=1))
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")


# --------------------------------------------------------------------------------------
# Chart 1: coverage bands + sample ground tracks over a world map
# --------------------------------------------------------------------------------------
def fig_coverage_bands(shells, land_paths):
    fig, ax = render.new_figure(figsize=(14, 8))
    draw_world_basemap(ax, land_paths)

    seen_incl = sorted({round(s.inclination_deg, 1) for s in shells})
    # Draw widest (highest max-latitude) band first so narrower bands layer on top and stay visible.
    seen_incl.sort(key=lambda i: -og.max_latitude_deg(i))
    for incl in seen_incl:
        max_lat = og.max_latitude_deg(incl)
        color = INCLINATION_COLORS.get(incl, "#888888")
        ax.axhspan(-max_lat, max_lat, color=color, alpha=0.10, zorder=2)
        ax.axhline(max_lat, color=color, linewidth=0.6, linestyle=":", alpha=0.6, zorder=2)
        ax.axhline(-max_lat, color=color, linewidth=0.6, linestyle=":", alpha=0.6, zorder=2)

    plotted_incl = set()
    for shell in sorted(shells, key=lambda s: s.inclination_deg):
        incl = round(shell.inclination_deg, 1)
        if incl in plotted_incl:
            continue
        plotted_incl.add(incl)
        lon, lat = og.ground_track(shell, lon0_deg=0.0, duration_s=86400)
        breaks = np.where(np.abs(np.diff(lon)) > 180)[0]
        segs_lon = np.split(lon, breaks + 1)
        segs_lat = np.split(lat, breaks + 1)
        n_orbits_today = round(86400 / shell.period_s)
        color = INCLINATION_COLORS.get(incl, "#888888")
        label = f"{INCLINATION_LABELS.get(incl, f'{incl} deg shell')} -- {n_orbits_today} orbits/day"
        for j, (sl, sla) in enumerate(zip(segs_lon, segs_lat)):
            ax.plot(sl, sla, color=color, linewidth=0.7, alpha=0.55, zorder=3,
                    label=label if j == 0 else None)

    ax.set_title("Starlink coverage bands and one satellite's ground track over a full day, per shell inclination")
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    info_box.add_info_box(
        ax, fig, "One satellite/shell, traced over 24h. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "coverage_bands_world_map.png"


# --------------------------------------------------------------------------------------
# Chart 2: expected satellites overhead by latitude, per shell (stacked)
# --------------------------------------------------------------------------------------
def fig_satellite_density_by_latitude(shells):
    centers, by_shell = og.expected_sats_by_latitude(shells, bin_width_deg=1.0)

    fig, ax = render.new_figure(figsize=(11, 6.5))
    shell_order = sorted(shells, key=lambda s: s.inclination_deg)
    stack = np.zeros_like(centers)
    for shell in shell_order:
        vals = by_shell[shell.shell_id]
        color = INCLINATION_COLORS.get(round(shell.inclination_deg, 1), "#888888")
        ax.fill_between(centers, stack, stack + vals, color=color, alpha=0.75,
                        step=None, label=f"{shell.shell_id} ({shell.inclination_deg}deg, {shell.total_sats} sats)")
        stack += vals

    ax.set_xlabel("Latitude (degrees)")
    ax.set_ylabel("Expected satellites overhead (instantaneous, stacked by shell)")
    ax.set_title("Gen1 satellite density by latitude (well-sourced shells only)")
    ax.set_xlim(-90, 90)
    ax.invert_xaxis()  # north (positive) on the left, matching the project convention
    ax.xaxis.set_major_locator(mticker.MultipleLocator(15))
    ax.legend(loc="upper left", fontsize=7.5)

    peak_lat = centers[stack.argmax()]
    info_box.add_info_box(
        ax, fig,
        f"Peak: {stack.max():.0f} sats at {peak_lat:.0f}deg. Gen1 only. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "satellite_density_by_latitude.png"


def figures(shells, land_paths):
    return [
        ("coverage_bands", lambda: fig_coverage_bands(shells, land_paths)),
        ("density_by_latitude", lambda: fig_satellite_density_by_latitude(shells)),
    ]


def main():
    shells = og.load_shells_with_full_geometry()
    land_paths = load_land_paths()
    plan = figures(shells, land_paths)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")

    print(f"\nShell geometry loaded: {len(shells)} sub-shells, "
          f"{sum(s.total_sats for s in shells)} total satellites (Gen1 only)")
    for s in shells:
        print(f"  {s.shell_id}: {s.inclination_deg}deg, {s.altitude_km}km, "
              f"max_lat={og.max_latitude_deg(s.inclination_deg):.1f}deg, "
              f"{s.total_sats} sats, period={s.period_s/60:.1f} min")


if __name__ == "__main__":
    main()
