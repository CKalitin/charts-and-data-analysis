"""New market-ladder-style chart: population CONNECTED vs. cumulative capacity
deployed / satellite count -- same capacity-Gbps-primary-axis convention as
market_ladder.py / avg_price_market_ladder.py, but reuses the ALREADY-BUILT
"serviceable customers" model (serviceable_customers_model.sweep_per_satellite_cap(),
charts/serviceable_customers_per_satellite_chart.py) rather than the per-country TAM
pipeline -- "population connected" doesn't depend on pricing/household size/ARPU at
all, only on the physical density-cap + aggregate-capacity model, which needs just
the GLOBAL population density grid (already cached, no per-country raster reload).

served = min(aggregate satellite capacity, density-capped population), summed across
every 1deg latitude band -- see serviceable_customers_model.py's per-satellite-cap
section for the full mechanism. This IS the same quantity the existing
serviceable_customers_vs_satellites_global(_linear).png charts, just re-axed here
(capacity Gbps primary / satellites secondary, matching this session's market-ladder
chart family) instead of their satellites-primary / Tbps-secondary convention -- not
a new model.

Run: python charts/population_connected_market_ladder.py
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
from market_ladder import _human
from serviceable_customers_chart import CURRENT_FLEET_SATS, GEN1_SATS, SHELL_RATIO_NOTE, SOURCE_NOTE, _pop_formatter
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "market_ladder"

GBPS_PER_SAT = cdm.V3_SCENARIO.downlink_gbps_per_beam * cdm.V3_SCENARIO.beams_per_satellite  # 1,024

CAPACITY_XLIM_MAX = 1_000e6  # 1000M Gbps -- user-requested cutoff; the curve is
# already fully flat/saturated well before this (~100-200M), so nothing past it is lost
SAT_COUNTS_LOG = np.geomspace(100, 1_000_000, 40)  # -> ~1,024M Gbps, just past the cutoff
LINEAR_MAX_SATS = 1_000_000  # -> ~1,024M Gbps, same reasoning


def _add_fleet_reference_lines_capacity(ax):
    """Same Gen1/current-fleet vertical reference lines as
    serviceable_customers_chart._add_fleet_reference_lines(), converted from
    satellite count to Gbps since THIS chart's x-axis is capacity, not satellites."""
    offsets = [(4, -4), (4, -70)]
    for (n, label), xytext in zip(
            [(GEN1_SATS, "Gen1 (4,408)"), (CURRENT_FLEET_SATS, "Current fleet (~10,900)")], offsets):
        x = n * GBPS_PER_SAT
        ax.axvline(x, color="0.5", linestyle=":", linewidth=1.0, zorder=1)
        ax.annotate(label, xy=(x, 1), xycoords=("data", "axes fraction"), xytext=xytext,
                     textcoords="offset points", fontsize=7.5, color="0.4", ha="left", va="top", rotation=90)


def _draw_chart(ax, capacity_gbps, served, raw_pop, *, log_scale: bool):
    ax.plot(capacity_gbps, served, color="#4575b4", linewidth=2.2, zorder=3,
             label="Population connected (global, 1km data)")
    ax.fill_between(capacity_gbps, 0, served, color="#4575b4", alpha=0.08, zorder=1)
    _add_fleet_reference_lines_capacity(ax)

    if log_scale:
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(capacity_gbps[0] * 0.9, CAPACITY_XLIM_MAX)
        ax.set_ylim(served.min() * 0.7, raw_pop * 1.3)
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())
        scale_word = "log scale"
    else:
        ax.set_xlim(0, CAPACITY_XLIM_MAX)
        ax.set_ylim(0, served.max() * 1.08)
        scale_word = "linear scale"

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _human(v)))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.set_xlabel(f"Cumulative capacity deployed, Gbps ({scale_word})")
    ax.set_ylabel(f"Population connected ({scale_word})")
    ax.set_title("Population connected vs. cumulative capacity deployed")

    secax = ax.secondary_xaxis("top", functions=(lambda x: x / GBPS_PER_SAT, lambda s: s * GBPS_PER_SAT))
    secax.set_xlabel(f"Cumulative v3 satellites ({GBPS_PER_SAT:,.0f} Gbps/sat)")
    secax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.1f}" if v < 10 else f"{v:,.0f}"))
    secax.xaxis.set_minor_formatter(mticker.NullFormatter())

    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.9)
    info_box.add_info_box(
        ax, ax.figure,
        f"Approaches raw population ({_pop_formatter(raw_pop, None)}) as capacity grows --\n"
        "density cap scales with range-extended satellites reaching each band.\n"
        f"{SHELL_RATIO_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )


def fig_population_connected_log(grid):
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    served = scm.sweep_per_satellite_cap(SAT_COUNTS_LOG, hist, dens_centers, lat_centers)
    raw_pop = float(np.sum(hist * dens_centers[None, :]))
    capacity_gbps = SAT_COUNTS_LOG * GBPS_PER_SAT

    fig, ax = render.new_figure(figsize=(13, 8))
    _draw_chart(ax, capacity_gbps, served, raw_pop, log_scale=True)
    return fig, OUT_ROOT / "population_connected_vs_capacity.png"


def fig_population_connected_linear(grid):
    sat_counts = np.linspace(0, LINEAR_MAX_SATS, 200)
    sat_counts[0] = 1.0
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    served = scm.sweep_per_satellite_cap(sat_counts, hist, dens_centers, lat_centers)
    raw_pop = float(np.sum(hist * dens_centers[None, :]))
    capacity_gbps = sat_counts * GBPS_PER_SAT

    fig, ax = render.new_figure(figsize=(13, 8))
    _draw_chart(ax, capacity_gbps, served, raw_pop, log_scale=False)
    return fig, OUT_ROOT / "population_connected_vs_capacity_linear.png"


def main():
    grid = pdg.load_or_build_grid()

    fig, path = fig_population_connected_log(grid)
    render.save_fig(fig, path)
    print(f"wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    fig, path = fig_population_connected_linear(grid)
    render.save_fig(fig, path)
    print(f"wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")


if __name__ == "__main__":
    main()
