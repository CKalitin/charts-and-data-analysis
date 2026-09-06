"""Market-ladder-style chart: population CONNECTED vs. cumulative capacity
deployed / satellite count -- same capacity-Gbps-primary-axis convention as
market_ladder.py / avg_price_market_ladder.py.

MIGRATED 2026-09-05 from serviceable_customers_model.sweep_per_satellite_cap()
(latitude-only) to tile_capacity_model.py's 2D (lat x lon) allocation -- "population
connected" doesn't depend on pricing/household size/ARPU, so this reads directly off
AllocationResult.total_served_people rather than the per-country TAM pipeline.

Sweeps here use COARSER (2deg) tiles than the 1deg production model -- see
charts/satellite_utilization.py's docstring for the validated <0.5% difference on
global totals.

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
import tile_capacity_model as tcm
from market_ladder import _human
from serviceable_customers_chart import ESTIMATED_CURRENT_CAPACITY_SATS, SOURCE_NOTE, _pop_formatter
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "market_ladder"

GBPS_PER_SAT = cdm.V3_SCENARIO.downlink_gbps_per_beam * cdm.V3_SCENARIO.beams_per_satellite  # 1,024

#: Coarser than the production 1deg grid -- see satellite_utilization.py's docstring.
SWEEP_TILE_DEG = 2.0

TILE_SHELL_NOTE = "Real Gen1 shells: 53.0/53.2/70.0/97.6deg, real 25deg-elevation coverage disks"

CAPACITY_XLIM_MAX = 1_000e6  # 1000M Gbps -- user-requested cutoff; the curve is
# already fully flat/saturated well before this (~100-200M), so nothing past it is lost
SAT_COUNTS_LOG = np.geomspace(100, 1_000_000, 30)  # -> ~1,024M Gbps, just past the cutoff
LINEAR_MAX_SATS = 1_000_000  # -> ~1,024M Gbps, same reasoning


def _add_fleet_reference_lines_capacity(ax):
    """Same estimated-current-capacity vertical reference line as
    serviceable_customers_chart._add_fleet_reference_lines(), converted from
    satellite count to Gbps since THIS chart's x-axis is capacity, not satellites."""
    x = ESTIMATED_CURRENT_CAPACITY_SATS * GBPS_PER_SAT
    ax.axvline(x, color="0.5", linestyle=":", linewidth=1.0, zorder=1)
    ax.annotate("Estimated current capacity", xy=(x, 1), xycoords=("data", "axes fraction"), xytext=(4, -4),
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
        "density cap scales with real satellites reaching each tile's coverage disk.\n"
        f"{TILE_SHELL_NOTE}. " + SOURCE_NOTE,
        mode="on",
    )


def fig_population_connected_log(tile, demand):
    served = np.array([r.total_served_people for r in tcm.sweep(SAT_COUNTS_LOG, tile=tile, demand=demand)])
    raw_pop = float(demand.population.sum())
    capacity_gbps = SAT_COUNTS_LOG * GBPS_PER_SAT

    fig, ax = render.new_figure(figsize=(13, 8))
    _draw_chart(ax, capacity_gbps, served, raw_pop, log_scale=True)
    return fig, OUT_ROOT / "population_connected_vs_capacity.png"


def fig_population_connected_linear(tile, demand):
    sat_counts = np.linspace(1, LINEAR_MAX_SATS, 40)
    served = np.array([r.total_served_people for r in tcm.sweep(sat_counts, tile=tile, demand=demand)])
    raw_pop = float(demand.population.sum())
    capacity_gbps = sat_counts * GBPS_PER_SAT

    fig, ax = render.new_figure(figsize=(13, 8))
    _draw_chart(ax, capacity_gbps, served, raw_pop, log_scale=False)
    return fig, OUT_ROOT / "population_connected_vs_capacity_linear.png"


def figures(tile=None, demand=None):
    tile = tile if tile is not None else tcm.make_tile_grid(SWEEP_TILE_DEG)
    demand = demand if demand is not None else tcm.build_demand(tile)
    return [
        ("population_connected_log", lambda: fig_population_connected_log(tile, demand)),
        ("population_connected_linear", lambda: fig_population_connected_linear(tile, demand)),
    ]


def main():
    tile = tcm.make_tile_grid(SWEEP_TILE_DEG)
    demand = tcm.build_demand(tile)
    for name, build in figures(tile, demand):
        fig, path = build()
        render.save_fig(fig, path)
        print(f"wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")


if __name__ == "__main__":
    main()
