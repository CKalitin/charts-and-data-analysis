"""Chart: world map (classified land / coastal water / open ocean) + the SSO
ground track overlaid, alongside a donut of the orbit-time fractions.

The map background is a per-cell classification raster, so the three regions are
shown directly as filled colors (green land, light-blue coastal water, blue open
ocean). The SSO ground track is drawn on top in a contrasting orange-red.

Independently runnable:  python charts/proximity_map.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import matplotlib.patheffects as pe
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import config as cfg
from charts import common
from derived import ProximityData
from viz import render


def _split_track_at_wrap(lons: np.ndarray, lats: np.ndarray):
    """Insert NaNs where the track crosses the antimeridian so the polyline does
    not draw a horizontal streak across the whole map at each +180/-180 wrap."""
    lon = lons.astype(float).copy()
    lat = lats.astype(float).copy()
    jumps = np.where(np.abs(np.diff(lon)) > 180.0)[0]
    lon = np.insert(lon, jumps + 1, np.nan)
    lat = np.insert(lat, jumps + 1, np.nan)
    return lon, lat


def draw_map(ax, data: ProximityData, lon_edges, lat_edges, grid_codes, land_rings):
    """World map: classified background + coastlines + SSO ground track."""
    ax.set_facecolor(cfg.COL_OCEAN)

    # ── Classified background raster (green / light-blue / blue / grey) ──────────
    cmap = ListedColormap([cfg.COL_LAND, cfg.COL_NEAR, cfg.COL_OCEAN, cfg.COL_LAND_EXCL])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    ax.pcolormesh(lon_edges, lat_edges, grid_codes, cmap=cmap, norm=norm,
                  shading="flat", zorder=1, rasterized=True)

    # ── Coastline outlines (thin) for crisp land edges ──────────────────────────
    segs = [ring for ring in land_rings]
    ax.add_collection(LineCollection(segs, colors=cfg.COL_COAST, linewidths=0.5,
                                     alpha=0.8, zorder=2))

    # ── SSO ground track on top, broken at antimeridian wraps ───────────────────
    lon, lat = _split_track_at_wrap(data.lons, data.lats)
    ax.plot(lon, lat, color=cfg.COL_TRACK, lw=0.9, alpha=0.95, zorder=4,
            solid_capstyle="round",
            path_effects=[pe.Stroke(linewidth=1.7, foreground=cfg.COL_TRACK_EDGE,
                                    alpha=0.45), pe.Normal()])

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.tick_params(colors="0.35", labelsize=7)
    ax.set_xlabel("Longitude (deg)", color="0.25", fontsize=8)
    ax.set_ylabel("Latitude (deg)", color="0.25", fontsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("0.6")
    ax.grid(True, color="0.85", linewidth=0.4, alpha=0.5)
    ax.set_title(
        f"SSO ground track  ·  {cfg.ALT_KM} km / {cfg.INC_DEG} deg  ·  "
        f"full day ({cfg.N_ORBITS} orbits)",
        color="0.15", fontsize=10, pad=8, loc="left")

    handles = [
        Patch(facecolor=cfg.COL_LAND,      edgecolor=cfg.COL_COAST, label="Land"),
        Patch(facecolor=cfg.COL_NEAR,      edgecolor="0.6",
              label=f"Coastal water (<{cfg.THRESHOLD_MI} mi)"),
        Patch(facecolor=cfg.COL_OCEAN,     edgecolor="0.6", label="Open ocean"),
        Patch(facecolor=cfg.COL_LAND_EXCL, edgecolor="0.5",
              label="Antarctica (excluded)"),
        Line2D([0], [0], color=cfg.COL_TRACK, lw=1.5, label="SSO ground track"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=7, framealpha=0.9,
              facecolor="white", edgecolor="0.7", ncol=2)


def draw_donut(ax, data: ProximityData):
    """Donut of orbit-time fractions: land / coastal water / open ocean."""
    ax.set_facecolor(cfg.FIG_BG)
    ax.set_aspect("equal")

    codes  = [cfg.CAT_LAND, cfg.CAT_NEAR, cfg.CAT_OCEAN]
    values = [data.pct_land, data.pct_near, data.pct_ocean]
    colors = [cfg.cat_color(c) for c in codes]
    labels = [cfg.cat_label(c) for c in codes]

    wedges, _ = ax.pie(
        values, colors=colors, startangle=90, counterclock=False,
        explode=[0.02] * 3,
        wedgeprops=dict(width=0.52, edgecolor=cfg.FIG_BG, linewidth=1.5),
    )

    for wedge, val in zip(wedges, values):
        mid = np.radians((wedge.theta1 + wedge.theta2) / 2)
        ax.text(0.70 * np.cos(mid), 0.70 * np.sin(mid), f"{val:.1f}%",
                ha="center", va="center", fontsize=12, fontweight="bold",
                color="0.12",
                path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])

    for wedge, label, col in zip(wedges, labels, colors):
        mid = np.radians((wedge.theta1 + wedge.theta2) / 2)
        xp, yp = 1.22 * np.cos(mid), 1.22 * np.sin(mid)
        ha = "left" if xp > 0.1 else "right" if xp < -0.1 else "center"
        ax.text(xp, yp, label, ha=ha, va="center", fontsize=8.5,
                color="0.15", fontweight="bold")

    ax.text(0, 0, f"{data.pct_land + data.pct_near:.0f}%\nnear land",
            ha="center", va="center", fontsize=11, color="0.12", fontweight="bold")
    ax.set_title("Orbit-time fraction", color="0.15", fontsize=9, pad=14)
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.45, 1.45)


def _info_lines(data: ProximityData, period_min: float) -> list[str]:
    return [
        f"Altitude: {cfg.ALT_KM} km",
        f"Inclination: {cfg.INC_DEG} deg (SSO)",
        f"Period: {period_min:.1f} min  ({1440/period_min:.2f} orbits/day)",
        f"Threshold: {cfg.THRESHOLD_MI} mi  ({cfg.THRESHOLD_KM:.0f} km)",
        f"Samples: {data.lats.size:,}",
    ]


def figures(data: ProximityData, lon_edges, lat_edges, grid_codes,
            land_rings, period_min: float) -> list:
    """Return [(name, build_fn)] pairs. build_fn -> (fig, path)."""
    def build():
        fig, _ = render.new_figure(figsize=(14, 7))
        fig.clf()
        fig.set_constrained_layout(False)   # we place axes manually with add_axes
        fig.set_facecolor(cfg.FIG_BG)
        ax_map = fig.add_axes([0.04, 0.09, 0.58, 0.82])
        ax_pie = fig.add_axes([0.66, 0.12, 0.31, 0.74])

        draw_map(ax_map, data, lon_edges, lat_edges, grid_codes, land_rings)
        draw_donut(ax_pie, data)

        fig.text(0.5, 0.975,
                 f"SSO satellite — fraction of orbit time within "
                 f"{cfg.THRESHOLD_MI} miles of land",
                 ha="center", va="top", color="0.10", fontsize=13, fontweight="bold")

        common.add_source(ax_map, "Land: Natural Earth 110m")
        common.add_box(ax_map, fig, _info_lines(data, period_min))
        # Watermark on the white figure margin (under the donut), black text.
        fig.text(0.815, 0.05, cfg.WATERMARK, ha="center", va="bottom",
                 fontsize=8, color="black", style="italic")
        return fig, cfg.OUTPUT_DIR / "sso_land_proximity.png"

    return [("proximity_map", build)]


# ── Standalone entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import time

    import derived
    from model import OrbitParams, propagate_orbit

    t0 = time.time()
    params = OrbitParams(alt_km=cfg.ALT_KM, inc_deg=cfg.INC_DEG)
    lats, lons = propagate_orbit(params, cfg.N_ORBITS, cfg.N_PER_ORBIT)

    assets = derived.load_land_assets()
    data = derived.compute(lats, lons, assets)
    lon_e, lat_e, grid = derived.classify_grid(assets)
    rings = derived.land_polygons(assets)

    plan = figures(data, lon_e, lat_e, grid, rings, params.period_s / 60.0)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}  ({time.time()-t0:.1f}s)")
