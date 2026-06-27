"""Chart: when is the SSO satellite within 300 mi of a solar array?

Same propagated SSO ground track as the land-proximity chart, but classified
against the operating utility-scale arrays in the Global Solar Power Tracker
instead of against land. The map background is a two-category raster — gold where
a point is within 300 mi of an array, light slate beyond — with coastlines for
geographic reference and the array sites themselves drawn as small dots. The
donut gives the orbit-time fraction spent within range of a solar array.

Independently runnable:  python charts/solar_proximity.py
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
from charts.proximity_map import _split_track_at_wrap
from derived import SolarAssets, SolarProximityData
from viz import render


def _case_label(solar: "SolarAssets") -> str:
    """Human-readable parenthetical for chart titles — empty when no filters."""
    parts = []
    if solar.min_mw > 0:
        parts.append(f">= {solar.min_mw:g} MW")
    if solar.exclude_countries:
        excl = ", ".join(sorted(solar.exclude_countries))
        parts.append(f"excl. {excl}")
    return f" ({', '.join(parts)})" if parts else ""


def _case_slug(solar: "SolarAssets") -> str:
    """Filename suffix; :g avoids sci notation per repo convention."""
    parts = []
    if solar.min_mw > 0:
        parts.append(f"min{solar.min_mw:g}MW")
    if solar.exclude_countries:
        excl = "".join(c[:3] for c in sorted(solar.exclude_countries))
        parts.append(f"excl{excl}")
    return ("_" + "_".join(parts)) if parts else ""


def draw_map(ax, data: SolarProximityData, solar: SolarAssets,
             lon_edges, lat_edges, grid_codes, land_rings):
    """World map: solar-proximity background + coastlines + array sites + SSO track."""
    ax.set_facecolor(cfg.COL_SOLAR_FAR)

    # ── Two-category background: within / beyond 300 mi of a solar array ─────────
    cmap = ListedColormap([cfg.COL_SOLAR_FAR, cfg.COL_SOLAR_NEAR])
    norm = BoundaryNorm([-0.5, 0.5, 1.5], cmap.N)
    ax.pcolormesh(lon_edges, lat_edges, grid_codes, cmap=cmap, norm=norm,
                  shading="flat", zorder=1, rasterized=True)

    # ── Coastlines for geographic reference ─────────────────────────────────────
    ax.add_collection(LineCollection(list(land_rings), colors=cfg.COL_SOLAR_COAST,
                                     linewidths=0.5, alpha=0.9, zorder=2))

    # ── Solar array sites ───────────────────────────────────────────────────────
    ax.scatter(solar.lons, solar.lats, s=1.0, c=cfg.COL_SOLAR_DOT, alpha=0.55,
               linewidths=0, zorder=3, rasterized=True)

    # ── SSO ground track on top, broken at antimeridian wraps ───────────────────
    lon, lat = _split_track_at_wrap(data.lons, data.lats)
    ax.plot(lon, lat, color=cfg.COL_SOLAR_TRACK, lw=0.9, alpha=0.95, zorder=4,
            solid_capstyle="round",
            path_effects=[pe.Stroke(linewidth=1.7, foreground="white", alpha=0.4),
                          pe.Normal()])

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.tick_params(colors="0.35", labelsize=7)
    ax.set_xlabel("Longitude (deg)", color="0.25", fontsize=8)
    ax.set_ylabel("Latitude (deg)", color="0.25", fontsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("0.6")
    ax.grid(True, color="0.80", linewidth=0.4, alpha=0.5)
    ax.set_title(
        f"SSO ground track vs solar arrays{_case_label(solar)}  ·  "
        f"{cfg.ALT_KM} km / {cfg.INC_DEG} deg  ·  full day ({cfg.N_ORBITS} orbits)",
        color="0.15", fontsize=10, pad=8, loc="left")

    handles = [
        Patch(facecolor=cfg.COL_SOLAR_NEAR, edgecolor="0.6",
              label=f"Within {cfg.THRESHOLD_MI} mi of a solar array"),
        Patch(facecolor=cfg.COL_SOLAR_FAR, edgecolor="0.6", label="Beyond range"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=cfg.COL_SOLAR_DOT,
               markersize=4, label=f"Solar array ({solar.n:,})"),
        Line2D([0], [0], color=cfg.COL_SOLAR_TRACK, lw=1.5, label="SSO ground track"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=7, framealpha=0.92,
              facecolor="white", edgecolor="0.7", ncol=2)


def draw_donut(ax, data: SolarProximityData):
    """Donut of orbit-time fraction within / beyond 300 mi of a solar array."""
    ax.set_facecolor(cfg.FIG_BG)
    ax.set_aspect("equal")

    codes  = [cfg.CAT_SOLAR_NEAR, cfg.CAT_SOLAR_FAR]
    values = [data.pct_near, data.pct_far]
    colors = [cfg.solar_color(c) for c in codes]
    labels = [cfg.solar_label(c) for c in codes]

    wedges, _ = ax.pie(
        values, colors=colors, startangle=90, counterclock=False,
        explode=[0.02] * 2,
        wedgeprops=dict(width=0.52, edgecolor=cfg.FIG_BG, linewidth=1.5),
    )

    for wedge, val in zip(wedges, values):
        mid = np.radians((wedge.theta1 + wedge.theta2) / 2)
        ax.text(0.70 * np.cos(mid), 0.70 * np.sin(mid), f"{val:.1f}%",
                ha="center", va="center", fontsize=12, fontweight="bold",
                color="0.12",
                path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])

    for wedge, label in zip(wedges, labels):
        mid = np.radians((wedge.theta1 + wedge.theta2) / 2)
        xp, yp = 1.22 * np.cos(mid), 1.22 * np.sin(mid)
        ha = "left" if xp > 0.1 else "right" if xp < -0.1 else "center"
        ax.text(xp, yp, label, ha=ha, va="center", fontsize=8.5,
                color="0.15", fontweight="bold")

    ax.text(0, 0, f"{data.pct_near:.0f}%\nin range", ha="center", va="center",
            fontsize=11, color="0.12", fontweight="bold")
    ax.set_title("Orbit-time fraction", color="0.15", fontsize=9, pad=14)
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.45, 1.45)


def _info_lines(data: SolarProximityData, solar: SolarAssets,
                period_min: float) -> list[str]:
    lines = [
        f"Altitude: {cfg.ALT_KM} km",
        f"Inclination: {cfg.INC_DEG} deg (SSO)",
        f"Period: {period_min:.1f} min  ({1440/period_min:.2f} orbits/day)",
        f"Threshold: {cfg.THRESHOLD_MI} mi  ({cfg.THRESHOLD_KM:.0f} km)",
        f"Arrays: {solar.n:,} operating  ({solar.total_gw:,.0f} GW)",
    ]
    if solar.min_mw > 0:
        lines.append(f"Min size: >= {solar.min_mw:g} MW")
    if solar.exclude_countries:
        lines.append(f"Excluded: {', '.join(sorted(solar.exclude_countries))}")
    return lines


def figures(data: SolarProximityData, solar: SolarAssets, lon_edges, lat_edges,
            grid_codes, land_rings, period_min: float) -> list:
    """Return [(name, build_fn)] pairs. build_fn -> (fig, path)."""
    def build():
        fig, _ = render.new_figure(figsize=(14, 7))
        fig.clf()
        fig.set_constrained_layout(False)   # we place axes manually with add_axes
        fig.set_facecolor(cfg.FIG_BG)
        ax_map = fig.add_axes([0.04, 0.09, 0.58, 0.82])
        ax_pie = fig.add_axes([0.66, 0.12, 0.31, 0.74])

        draw_map(ax_map, data, solar, lon_edges, lat_edges, grid_codes, land_rings)
        draw_donut(ax_pie, data)

        fig.text(0.5, 0.975,
                 f"SSO satellite — fraction of orbit time within "
                 f"{cfg.THRESHOLD_MI} miles of a solar array{_case_label(solar)}",
                 ha="center", va="top", color="0.10", fontsize=13, fontweight="bold")

        common.add_source(ax_map, "Solar: Global Solar Power Tracker (GEM), Feb 2026")
        common.add_box(ax_map, fig, _info_lines(data, solar, period_min))
        fig.text(0.815, 0.05, cfg.WATERMARK, ha="center", va="bottom",
                 fontsize=8, color="black", style="italic")
        return fig, cfg.OUTPUT_DIR / f"sso_solar_proximity{_case_slug(solar)}.png"

    return [(f"solar_proximity{_case_slug(solar)}", build)]


# ── Standalone entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import time

    import derived
    from model import OrbitParams, propagate_orbit

    t0 = time.time()
    params = OrbitParams(alt_km=cfg.ALT_KM, inc_deg=cfg.INC_DEG)
    lats, lons = propagate_orbit(params, cfg.N_ORBITS, cfg.N_PER_ORBIT)
    rings = derived.land_polygons(derived.load_land_assets())

    plan = []
    for min_mw, excl in cfg.SOLAR_CASES:
        solar = derived.load_solar_assets(min_mw, excl)
        data = derived.compute_solar(lats, lons, solar)
        lon_e, lat_e, grid = derived.classify_solar_grid(solar)
        plan += figures(data, solar, lon_e, lat_e, grid, rings, params.period_s / 60.0)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}  ({time.time()-t0:.1f}s)")
