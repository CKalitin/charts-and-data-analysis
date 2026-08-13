"""TAM (Total Addressable Market, USD) charts for currently-unconnected populations
-- see country_tam_model.py for the full pricing/TAM mechanism, and CLAUDE.md for
the design conversation (user request, 2026-08-14, "the biggest change yet").

Two charts:
  1. subscription_price_by_country_100k.png -- world choropleth, each country
     colored by its derived monthly subscription price (USD) at N=100,000
     satellites -- the country-level pricing output BEFORE it's turned into a
     dollar TAM figure, exactly as requested.
  2. tam_vs_satellites(_linear).png -- total TAM ($/month, summed across every
     country) vs. total satellites, same "vs. satellite count" family as the
     serviceable-customers and utilization charts (satellite count on the bottom
     x-axis, cumulative max capacity in Tbps on a secondary top axis). NOT
     monotonic -- see country_tam_model.py's own run output: TAM can DECLINE as N
     grows past the point where rising servable-% collapses elasticity-derived
     prices faster than subscriber growth compensates. A real finding, not a bug.

Run: python charts/country_tam_charts.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np
from matplotlib.colors import LogNorm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import country_service_model as csm
import country_tam_model as ctm
import population_density_grid as pdg
import serviceable_customers_model as scm
from country_choropleth import draw_choropleth, load_country_paths
from serviceable_customers_chart import _add_capacity_secondary_axis, _add_fleet_reference_lines
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "market"
TAM_SOURCE_NOTE = ("Source: telecom_market_by_country.md + household_size_by_country.md "
                    "+ WorldPop pop. density + capacity_density_model.py")

PRICE_MAP_SATS = 100_000  # user-specified N for the price heatmap


def _usd_formatter(x, _pos):
    if x <= 0:
        return "$0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"${x / div:.1f}{suf}"
    return f"${x:.0f}"


# --------------------------------------------------------------------------------------
# Chart 1: subscription price by country, choropleth, at N=100,000
# --------------------------------------------------------------------------------------
def fig_price_heatmap_by_country(rows: list[ctm.CountryTAM], country_paths):
    fig, ax = render.new_figure(figsize=(16, 9))
    prices = {r.iso3: r.price_usd_per_month for r in rows if r.price_usd_per_month > 0}

    import matplotlib as mpl
    cmap = mpl.colormaps["plasma"].copy()
    vmin, vmax = min(prices.values()), max(prices.values())
    norm = LogNorm(vmin=max(vmin, 0.5), vmax=vmax)
    draw_choropleth(ax, country_paths, prices, cmap, norm)

    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(sm, ax=ax, pad=0.015, shrink=0.65)
    cbar.set_label("Derived monthly subscription price (USD, log scale)")
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    cbar.ax.yaxis.set_minor_formatter(mticker.NullFormatter())

    ax.set_title(f"Derived monthly subscription price by country (N={PRICE_MAP_SATS:,} satellites)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    n_elastic = sum(1 for r in rows if r.price_basis == "elasticity_derived")
    n_local = sum(1 for r in rows if r.price_basis.startswith("existing_local_price"))
    n_missing = len({r.iso3 for r in rows}) - len(prices)
    info_box.add_info_box(
        ax, fig,
        f"{len(prices)} countries priced ({n_elastic} elasticity-derived,\n"
        f"{n_local} existing local price, {n_missing} missing price data).\n"
        "Grey = no price data or no 110m country polygon (~50 small\n"
        "states/territories excluded from the basemap resolution).\n"
        "<20% unconnected -> existing local price; >=20% -> elasticity-derived.\n"
        + TAM_SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "subscription_price_by_country_100k.png"


# --------------------------------------------------------------------------------------
# Chart 2: total TAM ($/month) vs. total satellites
# --------------------------------------------------------------------------------------
def fig_tam_vs_satellites(sat_counts, tam):
    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, tam, color="#2ca25f", linewidth=2, label="Total TAM (unconnected populations, $/mo)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    _add_capacity_secondary_axis(ax)
    ax.set_xlabel("Total satellites (log scale)")
    ax.set_ylabel("Total addressable market (USD/month, log scale)")
    ax.set_title("Total addressable market (unconnected populations) vs. total satellites")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.legend(loc="lower right", fontsize=8.5)

    peak_n = sat_counts[np.argmax(tam)]
    info_box.add_info_box(
        ax, fig,
        f"Peak TAM {_usd_formatter(tam.max(), None)}/mo near N={peak_n:,.0f} --\n"
        "NOT monotonic: rising servable-% can collapse elasticity-derived\n"
        "prices faster than subscriber growth compensates. " + TAM_SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "tam_vs_satellites.png"


TAM_LINEAR_MAX_SATS = 200_000


def fig_tam_vs_satellites_linear(sat_counts, tam):
    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, tam, color="#2ca25f", linewidth=2, label="Total TAM (unconnected populations, $/mo)")
    _add_fleet_reference_lines(ax)

    ax.set_xlim(0, TAM_LINEAR_MAX_SATS)
    ax.set_ylim(0, tam.max() * 1.08)
    _add_capacity_secondary_axis(ax)
    ax.set_xlabel("Total satellites (linear scale)")
    ax.set_ylabel("Total addressable market (USD/month, linear scale)")
    ax.set_title("Total addressable market (unconnected populations) vs. total satellites (linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.legend(loc="upper right", fontsize=8.5)

    peak_n = sat_counts[np.argmax(tam)]
    info_box.add_info_box(
        ax, fig,
        f"Peak TAM {_usd_formatter(tam.max(), None)}/mo near N={peak_n:,.0f} --\n"
        "NOT monotonic, see the log version's info box. " + TAM_SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "tam_vs_satellites_linear.png"


def main():
    grid = pdg.load_or_build_grid()
    lat_centers, dens_centers, hist = scm.density_area_histogram_by_latitude(grid)
    telecom_rows = ctm.load_telecom_rows()
    household_size = ctm.load_household_size()
    iso3_list = [r["iso3"] for r in telecom_rows]

    print("loading per-country population-by-latitude (one-time, ~217 rasters)...")
    pop_by_lat = csm.load_all_country_population_by_latitude(iso3_list, verbose=True)

    price_rows = ctm.compute_country_tam(PRICE_MAP_SATS, telecom_rows, household_size, pop_by_lat, lat_centers,
                                          hist, dens_centers)
    country_paths = load_country_paths()
    fig, path = fig_price_heatmap_by_country(price_rows, country_paths)
    render.save_fig(fig, path)
    print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    sat_counts = np.geomspace(100, 2_000_000, 30)
    tam = ctm.sweep_total_tam(sat_counts, telecom_rows, household_size, pop_by_lat, lat_centers, hist, dens_centers)

    fig, path = fig_tam_vs_satellites(sat_counts, tam)
    render.save_fig(fig, path)
    print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    sat_counts_linear = np.linspace(1, TAM_LINEAR_MAX_SATS, 60)
    tam_linear = ctm.sweep_total_tam(sat_counts_linear, telecom_rows, household_size, pop_by_lat, lat_centers,
                                      hist, dens_centers)
    fig, path = fig_tam_vs_satellites_linear(sat_counts_linear, tam_linear)
    render.save_fig(fig, path)
    print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    print("wrote 3 charts")


if __name__ == "__main__":
    main()
