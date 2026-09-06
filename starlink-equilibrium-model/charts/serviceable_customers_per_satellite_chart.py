"""Serviceable customers vs. total satellite count.

MIGRATED 2026-09-05 (charts 1 and 2 below) from serviceable_customers_model.py's
latitude-only per-satellite-cap model to tile_capacity_model.py's 2D (lat x lon)
allocation -- see LONGITUDE_FOV_CAPACITY_REVIEW.md for why the old model's density
cap (built from orbital_geometry.expected_sats_reaching_latitude(), which pools
capacity around a whole latitude RING instead of a satellite's actual ~940 km
coverage DISK) overcounted satellites in view by ~19x. Chart 3 (the US 1km vs. 100m
population-resolution comparison) is explicitly NOT migrated -- see that section's
own note for why.

Sweeps here use COARSER (2deg) tiles than the 1deg production model -- validated to
differ <0.5% on global totals; see satellite_utilization.py's docstring for the
same reasoning, which applies unchanged here.

Two chart pairs (log + linear each), four files total:
  1. servable_density_vs_satellites(_linear).png -- ONE curve, the population-
     weighted average areal density ceiling across every populated tile.
  2. serviceable_customers_vs_satellites_global(_linear).png -- global.

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
import tile_capacity_model as tcm
from serviceable_customers_chart import (
    SOURCE_NOTE,
    _add_capacity_secondary_axis, _add_fleet_reference_lines, _draw_curve, _format_log_axes, _pop_formatter,
)
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"
US_100M_DENSITY_HIST_CACHE = pdg.WORLDPOP_DIR / "_us_100m_density_area_hist.npz"

#: Coarser than the production 1deg grid -- see satellite_utilization.py's docstring.
SWEEP_TILE_DEG = 2.0

TILE_SHELL_NOTE = "Real Gen1 shells: 53.0/53.2/70.0/97.6deg, real 25deg-elevation coverage disks"


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
# ONE curve, population-weighted across every tile.
# --------------------------------------------------------------------------------------
def fig_servable_density_vs_satellites(tile, demand):
    sat_counts = np.geomspace(100, 2_000_000, 30)
    cache: dict = {}
    caps = np.array([tcm.density_cap_profile_average_people(n, tile, demand, operator_cache=cache)
                     for n in sat_counts])

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, caps, color="#d73027", linewidth=2, label="Servable density (population-weighted)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    _add_capacity_secondary_axis(ax)  # AFTER set_xscale -- see its docstring: creating this
    # before the parent's scale is set gets silently reset back to the broken default formatter
    ax.set_xlabel("Total satellites (V3, log scale)")
    ax.set_ylabel("Servable population density (people/km2, log scale)")
    ax.set_title("Servable population density vs. total satellites")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_density_formatter))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.legend(loc="lower right", fontsize=8.5)

    info_box.add_info_box(
        ax, fig,
        "Population-weighted average areal density ceiling, over the real 2D\n"
        "satellite coverage disk each tile can actually reach (not a latitude ring).\n"
        f"{TILE_SHELL_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "servable_density_vs_satellites.png"


DENSITY_LINEAR_MAX_SATS = 2_000_000  # same range as the log-log version, for direct comparison


def fig_servable_density_vs_satellites_linear(tile, demand):
    # This curve is a straight proportional line in N (no saturation to size the axis
    # around, unlike the serviceable-CUSTOMERS charts) -- evenly-spaced points still
    # matter for a clean linear render, so linspace, not geomspace.
    sat_counts = np.linspace(1, DENSITY_LINEAR_MAX_SATS, 40)
    cache: dict = {}
    caps = np.array([tcm.density_cap_profile_average_people(n, tile, demand, operator_cache=cache)
                     for n in sat_counts])

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, caps, color="#d73027", linewidth=2, label="Servable density (population-weighted)")
    _add_fleet_reference_lines(ax)
    _add_capacity_secondary_axis(ax)

    ax.set_xlim(0, DENSITY_LINEAR_MAX_SATS)
    ax.set_ylim(0, caps.max() * 1.05)
    ax.set_xlabel("Total satellites (V3, linear scale)")
    ax.set_ylabel("Servable population density (people/km2, linear scale)")
    ax.set_title("Servable population density vs. total satellites (linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_density_formatter))
    ax.legend(loc="lower right", fontsize=8.5)

    info_box.add_info_box(
        ax, fig,
        "Population-weighted average areal density ceiling, over the real 2D\n"
        "satellite coverage disk each tile can actually reach (not a latitude ring).\n"
        f"{TILE_SHELL_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "servable_density_vs_satellites_linear.png"


# --------------------------------------------------------------------------------------
# Chart 2: global, 1km resolution
# --------------------------------------------------------------------------------------
def fig_serviceable_vs_satellites_global(tile, demand):
    sat_counts = np.geomspace(100, 20_000_000, 30)
    served = np.array([r.total_served_people for r in tcm.sweep(sat_counts, tile=tile, demand=demand)])

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

    raw_pop = float(demand.population.sum())
    info_box.add_info_box(
        ax, fig,
        f"Approaches raw population ({_pop_formatter(raw_pop, None)}) as N grows --\n"
        "density cap scales with real satellites reaching each tile's coverage disk.\n"
        f"{TILE_SHELL_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_global.png"


GLOBAL_LINEAR_MAX_SATS = 7_000_000  # covers the curve's own saturation (~6M)


def fig_serviceable_vs_satellites_global_linear(tile, demand):
    sat_counts = np.linspace(1, GLOBAL_LINEAR_MAX_SATS, 40)
    served = np.array([r.total_served_people for r in tcm.sweep(sat_counts, tile=tile, demand=demand)])

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

    raw_pop = float(demand.population.sum())
    info_box.add_info_box(
        ax, fig,
        f"Approaches raw population ({_pop_formatter(raw_pop, None)}) as N grows --\n"
        "density cap scales with real satellites reaching each tile's coverage disk.\n"
        f"{TILE_SHELL_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_global_linear.png"


# --------------------------------------------------------------------------------------
# Chart 3: US only, 1km vs. 100m population data, overlaid -- resolution sensitivity.
#
# DELIBERATELY NOT MIGRATED. This pair asks a narrow, still-valid question -- "does
# WorldPop raster resolution change the answer" -- using the SAME (old, latitude-only)
# capacity model on both curves as a controlled A/B, so the comparison between them is
# unaffected by the longitude bug (it cancels: both curves carry it identically). A
# proper 2D version would need the US's 100m raster re-streamed into the global tile
# grid (a ~10 minute pass) AND the US no longer modelled in isolation -- with real
# longitude, it genuinely competes with Canada and Mexico for the same satellites,
# which changes what the comparison even measures. Left on the old model, clearly
# flagged, rather than rushed. Still optional/conditional exactly as before: it only
# runs if the (large, previously-computed) 100m histogram cache exists on disk.
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
        "NOT migrated to the 2D tile model (see this file's own module docstring) --\n"
        "resolution A/B only, on the superseded latitude-only capacity model.",
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
        "NOT migrated to the 2D tile model (see this file's own module docstring) --\n"
        "resolution A/B only, on the superseded latitude-only capacity model.",
        mode="on",
    )
    return fig, OUT_ROOT / "serviceable_customers_vs_satellites_us_1km_vs_100m_linear.png"


def figures(tile=None, demand=None):
    tile = tile if tile is not None else tcm.make_tile_grid(SWEEP_TILE_DEG)
    demand = demand if demand is not None else tcm.build_demand(tile)
    return [
        ("servable_density_vs_satellites", lambda: fig_servable_density_vs_satellites(tile, demand)),
        ("servable_density_vs_satellites_linear",
         lambda: fig_servable_density_vs_satellites_linear(tile, demand)),
        ("serviceable_global", lambda: fig_serviceable_vs_satellites_global(tile, demand)),
        ("serviceable_global_linear", lambda: fig_serviceable_vs_satellites_global_linear(tile, demand)),
    ]


def main():
    tile = tcm.make_tile_grid(SWEEP_TILE_DEG)
    demand = tcm.build_demand(tile)
    plan = figures(tile, demand)
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
