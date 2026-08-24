"""Serviceable customers vs. total satellite count -- the constellation's ONLY
charted demand model as of 2026-08-13 (see charts/serviceable_customers_chart.py's
docstring for why the earlier fixed-cap comparison was dropped, not just hidden).

The areal beam-footprint density cap scales with satellites REACHING a latitude
band -- range-extended via orbital_geometry.expected_sats_reaching_latitude(),
using Starlink's real ~25deg minimum-elevation FOV geometry (see ASSUMPTIONS.md
#11) -- while the aggregate per-satellite capacity cap stays overhead-only (a
satellite has one finite capacity budget; it can't be counted toward every
latitude it merely CAN reach without multiply-counting that budget). See
serviceable_customers_model.py's sats_reaching_latitude() / sats_overhead_by_latitude()
docstrings for the full validity argument, and its "Per-satellite density cap
variant" section for the demand-side mechanism.

Three chart pairs (log + linear each), six files total:
  1. servable_density_vs_satellites(_linear).png -- ONE curve, the real Starlink
     shell profile's range-extended-satellites-weighted average density ceiling.
  2. serviceable_customers_vs_satellites_global(_linear).png -- global, 1km data.
  3. serviceable_customers_vs_satellites_us_1km_vs_100m(_linear).png -- US only,
     two curves overlaid (1km vs. 100m population data resolution).

Run: python charts/serviceable_customers_per_satellite_chart.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import population_density_grid as pdg
import serviceable_customers_model as scm
from serviceable_customers_chart import (
    SHELL_RATIO_NOTE, SOURCE_NOTE,
    _add_capacity_secondary_axis, _add_fleet_reference_lines, _draw_curve, _format_log_axes, _pop_formatter,
)
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"
US_100M_DENSITY_HIST_CACHE = pdg.WORLDPOP_DIR / "_us_100m_density_area_hist.npz"


def _density_formatter(x, _pos):
    if x <= 0:
        return "0"
    if x < 10:
        return f"{x:.2g}"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


# --------------------------------------------------------------------------------------
# Chart 1: servable population DENSITY (not customer count) vs. total satellites --
# ONE curve for the real Starlink shell profile (range-extended-satellites-weighted
# average across all covered latitudes), not a per-latitude breakout.
# --------------------------------------------------------------------------------------
def fig_servable_density_vs_satellites():
    sat_counts = np.geomspace(100, 2_000_000, 40)
    caps = np.array([scm.effective_density_cap_profile_average(n) for n in sat_counts])

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, caps, color="#d73027", linewidth=2, label="Servable density (Starlink shell profile)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    _add_capacity_secondary_axis(ax)  # AFTER set_xscale -- see its docstring: creating this
    # before the parent's scale is set gets silently reset back to the broken default formatter
    ax.set_xlabel("Total satellites (V3, log scale)")
    ax.set_ylabel("Servable population density (people/km2, log scale)")
    ax.set_title("Servable population density vs. total satellites (Starlink shell profile)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_density_formatter))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.legend(loc="lower right", fontsize=8.5)

    info_box.add_info_box(
        ax, fig,
        "Range-extended-satellites-weighted average density ceiling across the real\n"
        "shell profile (dominated by the 53deg shells, 72% of satellites), using\n"
        "Starlink's ~25deg min. elevation FOV geometry (FCC Order 21-48).\n"
        + SHELL_RATIO_NOTE + ". " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "servable_density_vs_satellites.png"


DENSITY_LINEAR_MAX_SATS = 2_000_000  # same range as the log-log version, for direct comparison


def fig_servable_density_vs_satellites_linear():
    # This curve is a straight proportional line in N (no saturation to size the axis
    # around, unlike the serviceable-CUSTOMERS charts) -- evenly-spaced points still
    # matter for a clean linear render, so linspace, not geomspace.
    sat_counts = np.linspace(0, DENSITY_LINEAR_MAX_SATS, 200)
    sat_counts[0] = 1.0
    caps = np.array([scm.effective_density_cap_profile_average(n) for n in sat_counts])

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, caps, color="#d73027", linewidth=2, label="Servable density (Starlink shell profile)")
    _add_fleet_reference_lines(ax)
    _add_capacity_secondary_axis(ax)

    ax.set_xlim(0, DENSITY_LINEAR_MAX_SATS)
    ax.set_ylim(0, caps.max() * 1.05)
    ax.set_xlabel("Total satellites (V3, linear scale)")
    ax.set_ylabel("Servable population density (people/km2, linear scale)")
    ax.set_title("Servable population density vs. total satellites (Starlink shell profile, linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_density_formatter))
    ax.legend(loc="lower right", fontsize=8.5)

    info_box.add_info_box(
        ax, fig,
        "Range-extended-satellites-weighted average density ceiling across the real\n"
        "shell profile (dominated by the 53deg shells, 72% of satellites), using\n"
        "Starlink's ~25deg min. elevation FOV geometry (FCC Order 21-48).\n"
        + SHELL_RATIO_NOTE + ". " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "servable_density_vs_satellites_linear.png"


# --------------------------------------------------------------------------------------
# Chart 2: global, 1km resolution
# --------------------------------------------------------------------------------------
def fig_serviceable_vs_satellites_global(grid: pdg.PopulationGrid):
    sat_counts = np.geomspace(100, 20_000_000, 46)
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    served = scm.sweep_per_satellite_cap(sat_counts, hist, dens_centers, lat_centers)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_curve(ax, sat_counts, served, "#4575b4", "Serviceable customers (global, 1km data)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    _add_capacity_secondary_axis(ax)  # AFTER set_xscale -- see its docstring
    ax.set_xlabel("Total satellites (V3, log scale)")
    ax.set_ylabel("Serviceable customers (log scale)")
    ax.set_title("Serviceable customers vs. total satellites -- global")
    _format_log_axes(ax)
    ax.legend(loc="lower right", fontsize=8.5)

    raw_pop = float(np.sum(hist * dens_centers[None, :]))
    info_box.add_info_box(
        ax, fig,
        f"Approaches raw population ({_pop_formatter(raw_pop, None)}) as N grows --\n"
        "density cap scales with range-extended satellites reaching each band.\n"
        f"{SHELL_RATIO_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_global.png"


GLOBAL_LINEAR_MAX_SATS = 7_000_000  # covers the curve's own saturation (~6M)


def fig_serviceable_vs_satellites_global_linear(grid: pdg.PopulationGrid):
    sat_counts = np.linspace(0, GLOBAL_LINEAR_MAX_SATS, 200)
    sat_counts[0] = 1.0
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    served = scm.sweep_per_satellite_cap(sat_counts, hist, dens_centers, lat_centers)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_curve(ax, sat_counts, served, "#4575b4", "Serviceable customers (global, 1km data)")
    _add_fleet_reference_lines(ax)
    _add_capacity_secondary_axis(ax)

    ax.set_xlim(0, GLOBAL_LINEAR_MAX_SATS)
    ax.set_ylim(0, served.max() * 1.08)
    ax.set_xlabel("Total satellites (V3, linear scale)")
    ax.set_ylabel("Serviceable customers (linear scale)")
    ax.set_title("Serviceable customers vs. total satellites -- global (linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.legend(loc="lower right", fontsize=8.5)

    raw_pop = float(np.sum(hist * dens_centers[None, :]))
    info_box.add_info_box(
        ax, fig,
        f"Approaches raw population ({_pop_formatter(raw_pop, None)}) as N grows --\n"
        "density cap scales with range-extended satellites reaching each band.\n"
        f"{SHELL_RATIO_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_global_linear.png"


# --------------------------------------------------------------------------------------
# Chart 3: US only, 1km vs. 100m population data, overlaid -- resolution sensitivity
# --------------------------------------------------------------------------------------
def fig_serviceable_vs_satellites_us_resolution(us_grid_1km: pdg.PopulationGrid,
                                                 hist_100m: tuple[np.ndarray, np.ndarray, np.ndarray]):
    sat_counts = np.geomspace(100, 20_000_000, 46)

    lat_centers_1km, dens_centers_1km, hist_1km = scm.density_area_histogram_by_latitude(us_grid_1km)
    served_1km = scm.sweep_per_satellite_cap(sat_counts, hist_1km, dens_centers_1km, lat_centers_1km)

    lat_centers_100m, dens_centers_100m, hist_100m_arr = hist_100m
    served_100m = scm.sweep_per_satellite_cap(sat_counts, hist_100m_arr, dens_centers_100m, lat_centers_100m)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_curve(ax, sat_counts, served_1km, "#4575b4", "Serviceable customers (US, 1km data)")
    _draw_curve(ax, sat_counts, served_100m, "#d73027", "Serviceable customers (US, 100m data)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    _add_capacity_secondary_axis(ax)  # AFTER set_xscale -- see its docstring
    ax.set_xlabel("Total satellites (V3, log scale)")
    ax.set_ylabel("Serviceable customers (log scale)")
    ax.set_title("Serviceable customers vs. total satellites -- US, 1km vs. 100m population data")
    _format_log_axes(ax)
    ax.legend(loc="lower right", fontsize=8.5)

    raw_1km = float(np.sum(hist_1km * dens_centers_1km[None, :]))
    raw_100m = float(np.sum(hist_100m_arr * dens_centers_100m[None, :]))
    pct_diff = 100 * (raw_100m - raw_1km) / raw_1km
    info_box.add_info_box(
        ax, fig,
        f"Raw pop.: 1km {_pop_formatter(raw_1km, None)}, 100m {_pop_formatter(raw_100m, None)} ({pct_diff:+.0f}%)\n"
        "-- each curve approaches its own raw population as N grows.\n"
        "Same satellite-capacity curve; only pop. data resolution differs. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_us_1km_vs_100m.png"


US_LINEAR_MAX_SATS = 1_200_000  # covers the US curve's own saturation (~1M)


def fig_serviceable_vs_satellites_us_resolution_linear(us_grid_1km: pdg.PopulationGrid,
                                                        hist_100m: tuple[np.ndarray, np.ndarray, np.ndarray]):
    sat_counts = np.linspace(0, US_LINEAR_MAX_SATS, 200)
    sat_counts[0] = 1.0

    lat_centers_1km, dens_centers_1km, hist_1km = scm.density_area_histogram_by_latitude(us_grid_1km)
    served_1km = scm.sweep_per_satellite_cap(sat_counts, hist_1km, dens_centers_1km, lat_centers_1km)

    lat_centers_100m, dens_centers_100m, hist_100m_arr = hist_100m
    served_100m = scm.sweep_per_satellite_cap(sat_counts, hist_100m_arr, dens_centers_100m, lat_centers_100m)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_curve(ax, sat_counts, served_1km, "#4575b4", "Serviceable customers (US, 1km data)")
    _draw_curve(ax, sat_counts, served_100m, "#d73027", "Serviceable customers (US, 100m data)")
    _add_fleet_reference_lines(ax)
    _add_capacity_secondary_axis(ax)

    ax.set_xlim(0, US_LINEAR_MAX_SATS)
    ax.set_ylim(0, max(served_1km.max(), served_100m.max()) * 1.08)
    ax.set_xlabel("Total satellites (V3, linear scale)")
    ax.set_ylabel("Serviceable customers (linear scale)")
    ax.set_title("Serviceable customers vs. total satellites -- US, 1km vs. 100m population data (linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.legend(loc="lower right", fontsize=8.5)

    raw_1km = float(np.sum(hist_1km * dens_centers_1km[None, :]))
    raw_100m = float(np.sum(hist_100m_arr * dens_centers_100m[None, :]))
    pct_diff = 100 * (raw_100m - raw_1km) / raw_1km
    info_box.add_info_box(
        ax, fig,
        f"Raw pop.: 1km {_pop_formatter(raw_1km, None)}, 100m {_pop_formatter(raw_100m, None)} ({pct_diff:+.0f}%)\n"
        "-- each curve approaches its own raw population as N grows.\n"
        "Same satellite-capacity curve; only pop. data resolution differs. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_us_1km_vs_100m_linear.png"


def figures(grid: pdg.PopulationGrid):
    return [
        ("servable_density_vs_satellites", fig_servable_density_vs_satellites),
        ("servable_density_vs_satellites_linear", fig_servable_density_vs_satellites_linear),
        ("serviceable_global", lambda: fig_serviceable_vs_satellites_global(grid)),
        ("serviceable_global_linear", lambda: fig_serviceable_vs_satellites_global_linear(grid)),
    ]


def main():
    grid = pdg.load_or_build_grid()
    plan = figures(grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")

    if US_100M_DENSITY_HIST_CACHE.exists():
        us_grid_1km = pdg.load_country_density_grid("USA")
        cached_hist = np.load(US_100M_DENSITY_HIST_CACHE)
        hist_100m = (cached_hist["lat_centers"], cached_hist["dens_centers"], cached_hist["hist"])
        for build in (fig_serviceable_vs_satellites_us_resolution,
                      fig_serviceable_vs_satellites_us_resolution_linear):
            fig, path = build(us_grid_1km, hist_100m)
            render.save_fig(fig, path)
            print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    else:
        print(f"  skipped US charts: {US_100M_DENSITY_HIST_CACHE.name} not found in data/raw/worldpop/")


if __name__ == "__main__":
    main()
