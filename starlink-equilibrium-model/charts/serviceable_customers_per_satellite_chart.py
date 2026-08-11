"""Serviceable customers vs. total satellite count -- PER-SATELLITE density cap
variant (user request, 2026-08-10). A SEPARATE chart family from
charts/serviceable_customers_chart.py, not a replacement for it: that file's model
holds the areal beam-footprint density cap FIXED regardless of satellite count N
(capacity_density_model.py's original documented assumption). Here the cap scales
PER SATELLITE instead -- more satellites overhead a latitude band raises the local
areal ceiling too (N x base_cap), not just the aggregate per-satellite capacity
ceiling. See serviceable_customers_model.py's "Per-satellite density cap variant"
section for the full mechanism and why it changes the curve's shape (approaches raw
population at high N instead of sitting at a permanent ceiling).

Both charts here overlay the FIXED-cap curve (dashed) against the new PER-SATELLITE
-cap curve (solid, same color) so the difference the assumption makes is visible
directly, without needing to flip between two separate files.

Run: python charts/serviceable_customers_per_satellite_chart.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import capacity_density_model as cdm
import population_density_grid as pdg
import serviceable_customers_model as scm
from serviceable_customers_chart import (
    SHELL_RATIO_NOTE, SOURCE_NOTE,
    _add_fleet_reference_lines, _draw_curve, _format_log_axes, _pop_formatter,
)
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"
US_100M_POP_CAP_CACHE = pdg.WORLDPOP_DIR / "_us_100m_pop_cap_by_lat.npz"
US_100M_DENSITY_HIST_CACHE = pdg.WORLDPOP_DIR / "_us_100m_density_area_hist.npz"

CAP_NOTE = "Dashed = fixed cap. Solid = cap scales per satellite.\n" + SHELL_RATIO_NOTE + ". " + SOURCE_NOTE


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
# Chart 1: global, 1km resolution -- fixed cap vs. per-satellite cap, overlaid
# --------------------------------------------------------------------------------------
def fig_serviceable_vs_satellites_global_per_satellite_cap(grid: pdg.PopulationGrid):
    sat_counts = np.geomspace(100, 20_000_000, 46)
    served_fixed = scm.sweep_serviceable_customers(sat_counts, grid)
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    served_per_sat = scm.sweep_per_satellite_cap(sat_counts, hist, dens_centers, lat_centers)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_curve(ax, sat_counts, served_fixed, "#4575b4", "Fixed density cap (global, 1km)", linestyle="--")
    _draw_curve(ax, sat_counts, served_per_sat, "#4575b4", "Per-satellite density cap (global, 1km)", linestyle="-")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Total satellites (log scale)")
    ax.set_ylabel("Serviceable customers (log scale)")
    ax.set_title("Serviceable customers vs. total satellites -- global, fixed vs. per-satellite density cap")
    _format_log_axes(ax)
    ax.legend(loc="lower right", fontsize=8.5)

    raw_pop = float(np.sum(hist * dens_centers[None, :]))
    info_box.add_info_box(
        ax, fig,
        f"Fixed ceiling: {_pop_formatter(served_fixed[-1], None)}. Per-satellite -> "
        f"{_pop_formatter(raw_pop, None)} (raw pop.).\n" + CAP_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_global_per_satellite_cap.png"


GLOBAL_LINEAR_MAX_SATS = 7_000_000  # covers the per-satellite curve's own saturation (~6M)


def fig_serviceable_vs_satellites_global_per_satellite_cap_linear(grid: pdg.PopulationGrid):
    sat_counts = np.linspace(0, GLOBAL_LINEAR_MAX_SATS, 200)
    sat_counts[0] = 1.0
    served_fixed = scm.sweep_serviceable_customers(sat_counts, grid)
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    served_per_sat = scm.sweep_per_satellite_cap(sat_counts, hist, dens_centers, lat_centers)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_curve(ax, sat_counts, served_fixed, "#4575b4", "Fixed density cap (global, 1km)", linestyle="--")
    _draw_curve(ax, sat_counts, served_per_sat, "#4575b4", "Per-satellite density cap (global, 1km)", linestyle="-")
    _add_fleet_reference_lines(ax)

    ax.set_xlim(0, GLOBAL_LINEAR_MAX_SATS)
    ax.set_ylim(0, served_per_sat.max() * 1.08)
    ax.set_xlabel("Total satellites (linear scale)")
    ax.set_ylabel("Serviceable customers (linear scale)")
    ax.set_title("Serviceable customers vs. total satellites -- global, fixed vs. per-satellite cap (linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.legend(loc="lower right", fontsize=8.5)

    raw_pop = float(np.sum(hist * dens_centers[None, :]))
    info_box.add_info_box(
        ax, fig,
        f"Fixed ceiling: {_pop_formatter(served_fixed[-1], None)}. Per-satellite -> "
        f"{_pop_formatter(raw_pop, None)} (raw pop.).\n"
        "NOTE: fixed-cap curve saturates FAR left of this axis (~65K-100K sats) -- \n"
        "shown at true scale, not stretched to match. " + CAP_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_global_per_satellite_cap_linear.png"


# --------------------------------------------------------------------------------------
# Chart 2: US only -- {1km, 100m} x {fixed cap, per-satellite cap}, 4 curves
# --------------------------------------------------------------------------------------
def fig_serviceable_vs_satellites_us_per_satellite_cap(us_grid_1km: pdg.PopulationGrid,
                                                        pop_cap_100m: tuple[np.ndarray, np.ndarray],
                                                        hist_100m: tuple[np.ndarray, np.ndarray, np.ndarray]):
    sat_counts = np.geomspace(100, 20_000_000, 46)

    served_1km_fixed = scm.sweep_serviceable_customers(sat_counts, us_grid_1km)
    lat_centers_1km, dens_centers_1km, hist_1km = scm.density_area_histogram_by_latitude(us_grid_1km)
    served_1km_per_sat = scm.sweep_per_satellite_cap(sat_counts, hist_1km, dens_centers_1km, lat_centers_1km)

    served_100m_fixed = scm.sweep_from_pop_cap(sat_counts, pop_cap_100m)
    lat_centers_100m, dens_centers_100m, hist_100m = hist_100m
    served_100m_per_sat = scm.sweep_per_satellite_cap(sat_counts, hist_100m, dens_centers_100m, lat_centers_100m)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_curve(ax, sat_counts, served_1km_fixed, "#4575b4", "US, 1km, fixed cap", linestyle="--")
    _draw_curve(ax, sat_counts, served_1km_per_sat, "#4575b4", "US, 1km, per-satellite cap", linestyle="-")
    _draw_curve(ax, sat_counts, served_100m_fixed, "#d73027", "US, 100m, fixed cap", linestyle="--")
    _draw_curve(ax, sat_counts, served_100m_per_sat, "#d73027", "US, 100m, per-satellite cap", linestyle="-")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Total satellites (log scale)")
    ax.set_ylabel("Serviceable customers (log scale)")
    ax.set_title("Serviceable customers vs. total satellites -- US, 1km vs. 100m, fixed vs. per-satellite cap")
    _format_log_axes(ax)
    ax.legend(loc="lower right", fontsize=7.5, ncol=1)

    info_box.add_info_box(
        ax, fig,
        f"Fixed ceilings: 1km {_pop_formatter(served_1km_fixed[-1], None)}, "
        f"100m {_pop_formatter(served_100m_fixed[-1], None)}.\n" + CAP_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_us_per_satellite_cap.png"


US_LINEAR_MAX_SATS = 1_200_000  # covers the US per-satellite curve's own saturation (~1M)


def fig_serviceable_vs_satellites_us_per_satellite_cap_linear(us_grid_1km: pdg.PopulationGrid,
                                                               pop_cap_100m: tuple[np.ndarray, np.ndarray],
                                                               hist_100m: tuple[np.ndarray, np.ndarray, np.ndarray]):
    sat_counts = np.linspace(0, US_LINEAR_MAX_SATS, 200)
    sat_counts[0] = 1.0

    served_1km_fixed = scm.sweep_serviceable_customers(sat_counts, us_grid_1km)
    lat_centers_1km, dens_centers_1km, hist_1km = scm.density_area_histogram_by_latitude(us_grid_1km)
    served_1km_per_sat = scm.sweep_per_satellite_cap(sat_counts, hist_1km, dens_centers_1km, lat_centers_1km)

    served_100m_fixed = scm.sweep_from_pop_cap(sat_counts, pop_cap_100m)
    lat_centers_100m, dens_centers_100m, hist_100m = hist_100m
    served_100m_per_sat = scm.sweep_per_satellite_cap(sat_counts, hist_100m, dens_centers_100m, lat_centers_100m)

    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_curve(ax, sat_counts, served_1km_fixed, "#4575b4", "US, 1km, fixed cap", linestyle="--")
    _draw_curve(ax, sat_counts, served_1km_per_sat, "#4575b4", "US, 1km, per-satellite cap", linestyle="-")
    _draw_curve(ax, sat_counts, served_100m_fixed, "#d73027", "US, 100m, fixed cap", linestyle="--")
    _draw_curve(ax, sat_counts, served_100m_per_sat, "#d73027", "US, 100m, per-satellite cap", linestyle="-")
    _add_fleet_reference_lines(ax)

    ax.set_xlim(0, US_LINEAR_MAX_SATS)
    ax.set_ylim(0, max(served_1km_per_sat.max(), served_100m_per_sat.max()) * 1.08)
    ax.set_xlabel("Total satellites (linear scale)")
    ax.set_ylabel("Serviceable customers (linear scale)")
    ax.set_title("Serviceable customers vs. total satellites -- US, 1km vs. 100m, fixed vs. per-satellite cap (linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.legend(loc="lower right", fontsize=7.5, ncol=1)

    info_box.add_info_box(
        ax, fig,
        f"Fixed ceilings: 1km {_pop_formatter(served_1km_fixed[-1], None)}, "
        f"100m {_pop_formatter(served_100m_fixed[-1], None)}.\n"
        "NOTE: fixed-cap curves saturate FAR left of this axis (~20K-50K sats). " + CAP_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_us_per_satellite_cap_linear.png"


# --------------------------------------------------------------------------------------
# Chart 3: servable population DENSITY (not customer count) vs. total satellites --
# ONE curve for the real Starlink shell profile (satellites-overhead-weighted average
# across all covered latitudes), not a per-latitude breakout.
# --------------------------------------------------------------------------------------
def fig_servable_density_vs_satellites():
    sat_counts = np.geomspace(100, 2_000_000, 40)
    caps = np.array([scm.effective_density_cap_profile_average(n) for n in sat_counts])

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, caps, color="#d73027", linewidth=2, label="Servable density (Starlink shell profile)")

    base_cap = cdm.max_customer_density_per_km2(cdm.V2_MINI_BEAD_SCENARIO)
    ax.axhline(base_cap, color="0.3", linestyle="--", linewidth=1.3,
              label=f"Fixed cap ({base_cap:.2f}/km2)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Total satellites (log scale)")
    ax.set_ylabel("Servable population density (people/km2, log scale)")
    ax.set_title("Servable population density vs. total satellites, per-satellite cap (Starlink shell profile)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_density_formatter))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.legend(loc="lower right", fontsize=8.5)

    info_box.add_info_box(
        ax, fig,
        "Satellites-overhead-weighted average density ceiling across the real\n"
        "shell profile (dominated by the 53deg shells, 72% of satellites).\n"
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

    base_cap = cdm.max_customer_density_per_km2(cdm.V2_MINI_BEAD_SCENARIO)
    ax.axhline(base_cap, color="0.3", linestyle="--", linewidth=1.3,
              label=f"Fixed cap ({base_cap:.2f}/km2)")
    _add_fleet_reference_lines(ax)

    ax.set_xlim(0, DENSITY_LINEAR_MAX_SATS)
    ax.set_ylim(0, caps.max() * 1.05)
    ax.set_xlabel("Total satellites (linear scale)")
    ax.set_ylabel("Servable population density (people/km2, linear scale)")
    ax.set_title("Servable population density vs. total satellites, per-satellite cap (Starlink shell profile, linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_density_formatter))
    ax.legend(loc="lower right", fontsize=8.5)

    info_box.add_info_box(
        ax, fig,
        "Satellites-overhead-weighted average density ceiling across the real\n"
        "shell profile (dominated by the 53deg shells, 72% of satellites).\n"
        + SHELL_RATIO_NOTE + ". " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "servable_density_vs_satellites_linear.png"


def figures(grid: pdg.PopulationGrid):
    return [
        ("serviceable_global_per_sat", lambda: fig_serviceable_vs_satellites_global_per_satellite_cap(grid)),
        ("serviceable_global_per_sat_linear",
         lambda: fig_serviceable_vs_satellites_global_per_satellite_cap_linear(grid)),
        ("servable_density_vs_satellites", fig_servable_density_vs_satellites),
        ("servable_density_vs_satellites_linear", fig_servable_density_vs_satellites_linear),
    ]


def main():
    grid = pdg.load_or_build_grid()
    plan = figures(grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")

    if US_100M_POP_CAP_CACHE.exists() and US_100M_DENSITY_HIST_CACHE.exists():
        us_grid_1km = pdg.load_country_density_grid("USA")
        cached_pop_cap = np.load(US_100M_POP_CAP_CACHE)
        pop_cap_100m = (cached_pop_cap["centers"], cached_pop_cap["pop_cap"])
        cached_hist = np.load(US_100M_DENSITY_HIST_CACHE)
        hist_100m = (cached_hist["lat_centers"], cached_hist["dens_centers"], cached_hist["hist"])
        for build in (fig_serviceable_vs_satellites_us_per_satellite_cap,
                      fig_serviceable_vs_satellites_us_per_satellite_cap_linear):
            fig, path = build(us_grid_1km, pop_cap_100m, hist_100m)
            render.save_fig(fig, path)
            print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    else:
        print(f"  skipped US charts: need both {US_100M_POP_CAP_CACHE.name} and "
              f"{US_100M_DENSITY_HIST_CACHE.name} in data/raw/worldpop/")


if __name__ == "__main__":
    main()
