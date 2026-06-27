"""Chart: ERA5-weighted effective transmission at solar array sites.

Left: World map — proximity zones coloured by T_eff of nearest array (plasma gradient).
Right top: Formula display — "31.4%  x  0.61  =  19.2%" showing the orbit-time math.
Right bottom: Histogram of T_eff values across in-range orbit points.

T_eff = f_cloud * T_OVERCAST + (1 - f_cloud) * T_CLEAR

Independently runnable:  python charts/transmission_proximity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import matplotlib.cm as mcm
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

import config as cfg
from charts import common
from charts.proximity_map import _split_track_at_wrap
from charts.solar_proximity import _case_label, _case_slug
from derived import SolarAssets, SolarProximityData, CloudCover, OrbitTransmission
from viz import render


import matplotlib
_PLASMA = matplotlib.colormaps["plasma"]
_NORM   = mcolors.Normalize(vmin=cfg.T_OVERCAST, vmax=cfg.T_CLEAR)


def _plasma_color(teff: float):
    return _PLASMA(_NORM(teff))


# ── Map ───────────────────────────────────────────────────────────────────────────────

def draw_map(ax, data: SolarProximityData, solar: SolarAssets,
             lon_edges, lat_edges, teff_raster, land_rings):
    """Gradient proximity map. Returns the pcolormesh artist for the colorbar."""
    ax.set_facecolor(cfg.COL_SOLAR_FAR)

    pcm = ax.pcolormesh(
        lon_edges, lat_edges, teff_raster,
        cmap="plasma", vmin=cfg.T_OVERCAST, vmax=cfg.T_CLEAR,
        shading="flat", zorder=2, rasterized=True,
    )
    ax.add_collection(LineCollection(list(land_rings), colors=cfg.COL_SOLAR_COAST,
                                     linewidths=0.5, alpha=0.9, zorder=3))

    lon, lat = _split_track_at_wrap(data.lons, data.lats)
    ax.plot(lon, lat, color=cfg.COL_SOLAR_TRACK, lw=0.9, alpha=0.95, zorder=4,
            solid_capstyle="round",
            path_effects=[pe.Stroke(linewidth=1.7, foreground="white", alpha=0.4),
                          pe.Normal()])

    ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.tick_params(colors="0.35", labelsize=7)
    ax.set_xlabel("Longitude (deg)", color="0.25", fontsize=8)
    ax.set_ylabel("Latitude (deg)", color="0.25", fontsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("0.6")
    ax.grid(True, color="0.80", linewidth=0.4, alpha=0.5)
    ax.set_title(
        f"Effective atmospheric transmission at solar array sites  ·  "
        f"{cfg.ALT_KM} km SSO  ·  {solar.n:,} arrays{_case_label(solar)}",
        color="0.15", fontsize=10, pad=8, loc="left")

    ax.legend(handles=[
        Line2D([0], [0], color=cfg.COL_SOLAR_TRACK, lw=1.5, label="SSO ground track"),
        Line2D([0], [0], color="none", marker="s", markerfacecolor=cfg.COL_SOLAR_FAR,
               markersize=8, markeredgecolor="0.6", label=f"Beyond {cfg.THRESHOLD_MI} mi"),
    ], loc="upper left", fontsize=7.5, framealpha=0.92, facecolor="white", edgecolor="0.7")

    return pcm


def draw_colorbar(ax_cbar, pcm):
    cbar = ax_cbar.figure.colorbar(pcm, cax=ax_cbar, orientation="vertical")
    # Large pad pushes "T_eff" well above the "clear sky" annotation below it.
    ax_cbar.set_title("Trans.\nEff.", color="0.15", fontsize=8, pad=4)
    cbar.ax.tick_params(labelsize=7.5, colors="0.25")
    cbar.set_ticks(np.round(np.arange(cfg.T_OVERCAST, cfg.T_CLEAR + 0.001, 0.1), 2))
    cbar.ax.text(0.5, 1.09, "clear sky\n(f_cloud=0)",
                 transform=cbar.ax.transAxes, ha="center", va="bottom",
                 fontsize=6.5, color="0.40")
    cbar.ax.text(0.5, -0.03, "overcast\n(f_cloud=1)",
                 transform=cbar.ax.transAxes, ha="center", va="top",
                 fontsize=6.5, color="0.40")


# ── Formula display ────────────────────────────────────────────────────────────────────

def draw_formula(ax, ot: OrbitTransmission):
    """Three-number 'A × B = C' panel summarising orbit-wide effective transmission."""
    ax.set_facecolor(cfg.FIG_BG)
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    ax.text(0.5, 1.04, "Orbit-time effective transmission",
            ha="center", va="bottom", transform=ax.transAxes,
            fontsize=10, color="0.12")

    # Column x positions and operator x positions
    xs     = [0.12, 0.50, 0.88]
    x_ops  = [0.31, 0.69]
    nums   = [f"{ot.pct_near:.1f}%", f"{ot.mean_teff:.3f}", f"{ot.net_utility:.1f}%"]
    labels = ["in range", "mean trans. eff.\n(in-range orbit)", "net orbit trans.\nefficiency"]
    colors = ["0.08", "0.08", "#1A6B1A"]

    for x, num, col, lab in zip(xs, nums, colors, labels):
        ax.text(x, 0.67, num, ha="center", va="bottom", transform=ax.transAxes,
                fontsize=23, fontweight="bold", color=col)
        ax.text(x, 0.55, lab, ha="center", va="top", transform=ax.transAxes,
                fontsize=8.5, color="0.42")

    for x_op, sym in zip(x_ops, ["×", "="]):
        ax.text(x_op, 0.64, sym, ha="center", va="center", transform=ax.transAxes,
                fontsize=20, color="0.50")

    # Thin rule + explanatory footnote
    ax.axhline(0.32, xmin=0.03, xmax=0.97, color="0.82", lw=0.9)
    ax.text(0.5, 0.20,
            f"= {ot.net_utility:.1f}% of all orbit time spent within {cfg.THRESHOLD_MI} mi\n"
            f"of a solar array with appreciable atmospheric transmission",
            ha="center", va="center", transform=ax.transAxes,
            fontsize=7.5, color="0.42", style="italic")


# ── T_eff histogram ────────────────────────────────────────────────────────────────────

def draw_teff_hist(ax, ot: OrbitTransmission):
    """Histogram of T_eff values across all in-range orbit points, bars plasma-coloured."""
    ax.set_facecolor(cfg.FIG_BG)

    bins = np.linspace(cfg.T_OVERCAST, cfg.T_CLEAR, 22)
    counts, edges = np.histogram(ot.teff_in_range, bins=bins)
    pct = counts / counts.sum() * 100

    for left, right, p in zip(edges[:-1], edges[1:], pct):
        mid = 0.5 * (left + right)
        ax.bar(mid, p, width=(right - left) * 0.88,
               color=_plasma_color(mid), edgecolor="white", linewidth=0.5, zorder=2)

    # Mean vertical line — anchor annotation to the computed max so it's always in frame.
    ax.axvline(ot.mean_teff, color="0.20", lw=1.4, ls="--", zorder=4)
    ax.text(ot.mean_teff + 0.003, pct.max() * 0.97,
            f" mean\n {ot.mean_teff:.3f}", fontsize=7.5, color="0.20", va="top", zorder=5)

    ax.set_xlim(cfg.T_OVERCAST - 0.01, cfg.T_CLEAR + 0.01)
    ax.set_xticks(np.round(np.arange(cfg.T_OVERCAST, cfg.T_CLEAR + 0.001, 0.1), 2))
    ax.set_xlabel("Transmission efficiency", color="0.25", fontsize=8)
    ax.set_ylabel("% of in-range\norbit time", color="0.25", fontsize=8)
    ax.tick_params(colors="0.35", labelsize=7.5)
    ax.set_title("Transmission efficiency distribution (in-range orbit points)",
                 color="0.15", fontsize=9.5, pad=6)
    ax.grid(True, color="0.88", linewidth=0.4, axis="y", zorder=1)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor("0.7")


# ── Info lines + figure assembly ──────────────────────────────────────────────────────

def _info_lines(solar: SolarAssets, cloud: CloudCover, period_min: float) -> list[str]:
    return [
        f"Altitude: {cfg.ALT_KM} km",
        f"Inclination: {cfg.INC_DEG} deg (SSO)",
        f"Period: {period_min:.1f} min  ({1440 / period_min:.2f}/day)",
        f"Threshold: {cfg.THRESHOLD_MI} mi  ({cfg.THRESHOLD_KM:.0f} km)",
        f"Arrays: {solar.n:,}  ({solar.total_gw:.0f} GW total)",
        f"Min size: >= {solar.min_mw:g} MW",
        f"Excluded: {', '.join(sorted(solar.exclude_countries))}",
        f"Trans. eff. = f_cloud*{cfg.T_OVERCAST} + (1-f)*{cfg.T_CLEAR}",
        f"Cloud: {cloud.source}",
    ]


def figures(data: SolarProximityData, solar: SolarAssets,
            lon_edges, lat_edges, teff_raster,
            land_rings, cloud: CloudCover, ot: OrbitTransmission,
            period_min: float) -> list:
    """Return [(name, build_fn)] for the combined chart plus each panel individually."""
    slug  = _case_slug(solar)
    label = _case_label(solar)
    info  = _info_lines(solar, cloud, period_min)
    src   = "Solar: GEM Global Solar Power Tracker, Feb 2026  |  Cloud: ERA5 (2018-2023)"

    # ── Combined ──────────────────────────────────────────────────────────────────
    def build_combined():
        fig, _ = render.new_figure(figsize=(16, 7))
        fig.clf(); fig.set_constrained_layout(False); fig.set_facecolor(cfg.FIG_BG)

        ax_map     = fig.add_axes([0.03, 0.09, 0.49, 0.80])
        ax_cbar    = fig.add_axes([0.54, 0.19, 0.014, 0.60])
        ax_formula = fig.add_axes([0.61, 0.47, 0.37, 0.41])
        ax_hist    = fig.add_axes([0.61, 0.09, 0.37, 0.35])

        pcm = draw_map(ax_map, data, solar, lon_edges, lat_edges, teff_raster, land_rings)
        draw_colorbar(ax_cbar, pcm)
        draw_formula(ax_formula, ot)
        draw_teff_hist(ax_hist, ot)

        fig.text(0.5, 0.975, f"Orbitally Reflected Cloud-Weighted Solar Transmission Efficiency at >100 MW Solar Array Sites",
                 ha="center", va="top", color="0.10", fontsize=13, fontweight="bold")
        common.add_source(ax_map, src)
        common.add_box(ax_map, fig, info)
        fig.text(0.95, 0.025, cfg.WATERMARK, ha="center", va="bottom",
                 fontsize=8, color="black", style="italic")

        return fig, cfg.OUTPUT_DIR / f"sso_transmission_proximity{slug}.png"

    # ── Map only ──────────────────────────────────────────────────────────────────
    def build_map():
        fig, _ = render.new_figure(figsize=(13, 6.5))
        fig.clf(); fig.set_constrained_layout(False); fig.set_facecolor(cfg.FIG_BG)

        ax_map  = fig.add_axes([0.04, 0.09, 0.85, 0.82])
        ax_cbar = fig.add_axes([0.91, 0.19, 0.018, 0.62])

        pcm = draw_map(ax_map, data, solar, lon_edges, lat_edges, teff_raster, land_rings)
        draw_colorbar(ax_cbar, pcm)

        fig.text(0.5, 0.975, f"Orbitally Reflected Cloud-Weighted Solar Transmission Efficiency at >100 MW Solar Array Sites",
                 ha="center", va="top", color="0.10", fontsize=13, fontweight="bold")
        common.add_source(ax_map, src)
        common.add_box(ax_map, fig, info)
        fig.text(0.96, 0.03, cfg.WATERMARK, ha="right", va="bottom",
                 fontsize=8, color="black", style="italic")

        return fig, cfg.OUTPUT_DIR / f"sso_transmission_map{slug}.png"

    # ── Formula only ──────────────────────────────────────────────────────────────
    def build_formula():
        fig, _ = render.new_figure(figsize=(9, 4))
        fig.clf(); fig.set_constrained_layout(False); fig.set_facecolor(cfg.FIG_BG)

        ax = fig.add_axes([0.02, 0.05, 0.96, 0.88])
        draw_formula(ax, ot)

        fig.text(0.98, 0.02, cfg.WATERMARK, ha="right", va="bottom",
                 fontsize=8, color="black", style="italic")

        return fig, cfg.OUTPUT_DIR / f"sso_transmission_formula{slug}.png"

    # ── Histogram only ────────────────────────────────────────────────────────────
    def build_hist():
        fig, _ = render.new_figure(figsize=(7, 5))
        fig.clf(); fig.set_constrained_layout(False); fig.set_facecolor(cfg.FIG_BG)

        ax = fig.add_axes([0.14, 0.13, 0.82, 0.77])
        draw_teff_hist(ax, ot)

        fig.text(0.99, 0.02, cfg.WATERMARK, ha="right", va="bottom",
                 fontsize=8, color="black", style="italic")

        return fig, cfg.OUTPUT_DIR / f"sso_transmission_hist{slug}.png"

    return [
        (f"transmission_proximity{slug}",  build_combined),
        (f"transmission_map{slug}",        build_map),
        (f"transmission_formula{slug}",    build_formula),
        (f"transmission_hist{slug}",       build_hist),
    ]


# ── Standalone entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import time
    import derived
    from model import OrbitParams, propagate_orbit

    TARGET = (100.0, frozenset({"China", "Russia"}))

    t0 = time.time()
    params = OrbitParams(alt_km=cfg.ALT_KM, inc_deg=cfg.INC_DEG)
    lats, lons = propagate_orbit(params, cfg.N_ORBITS, cfg.N_PER_ORBIT)
    rings = derived.land_polygons(derived.load_land_assets())

    min_mw, excl = TARGET
    solar  = derived.load_solar_assets(min_mw, excl)
    sdata  = derived.compute_solar(lats, lons, solar)
    cloud  = derived.load_cloud_cover()
    teff   = derived.compute_teff(solar, cloud)
    lon_e, lat_e, teff_raster = derived.classify_teff_grid(solar, teff)
    ot     = derived.compute_orbit_transmission(sdata, solar, teff)

    print(f"  In range:    {ot.pct_near:.1f}%")
    print(f"  Mean T_eff:  {ot.mean_teff:.3f}")
    print(f"  Net utility: {ot.net_utility:.1f}%")

    plan = figures(sdata, solar, lon_e, lat_e, teff_raster, rings,
                   cloud, ot, params.period_s / 60.0)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}  ({time.time()-t0:.1f}s)")
