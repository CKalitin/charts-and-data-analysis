"""Full-world TAM (Total Addressable Market, USD) charts -- Starlink "just takes
incumbent share as it expands," NOT limited to currently-unconnected populations
(see country_tam_charts.py / country_tam_model.py for that separate, unchanged
model). See country_tam_full_model.py for the full pricing/segment mechanism, and
CLAUDE.md for the design conversation (user request, 2026-08-16).

Five outputs (2026-08-16):
  1. tam_full_by_country_100k.png -- world choropleth, each country colored by its
     TOTAL addressable market (USD/month) at N=100,000 satellites -- unlike
     country_tam_charts.py's price heatmap, this one is dominated by large, wealthy,
     ALREADY-connected markets (US, China, EU), not underserved ones, since revenue
     here includes captured incumbent share.
  2. tam_full_vs_satellites(_linear).png -- total TAM vs. total satellites, same
     "vs. satellite count" family (Tbps secondary axis) as every other chart in this
     project.
  3. tam_full_vs_satellites_by_region.png -- stacked by World Bank region.
  4. tam_full_vs_satellites_by_segment.png -- stacked by PRICING SEGMENT (revenue
     captured from already-connected incumbent switchers vs. revenue from newly-
     connected customers) -- the direct payoff of the split-pricing design decision,
     shows how the revenue MIX shifts as N grows, not just the total.
  5. tam_full_by_country_vs_satellites.csv / tam_full_by_continent_vs_satellites.csv
     -- wide-format exports, same SAT_BUCKETS as country_tam_charts.py (reused
     directly, for apples-to-apples comparison against the unconnected-only model).

Run: python charts/country_tam_full_charts.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np
from matplotlib.colors import LogNorm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tam_model as tm
from country_choropleth import draw_choropleth, load_country_paths
from country_tam_charts import SAT_BUCKETS, TAM_SOURCE_NOTE, _usd_formatter
from regions import REGION_COLORS, REGION_SHORT
from serviceable_customers_chart import _add_capacity_secondary_axis, _add_fleet_reference_lines
from viz import render, info_box

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "market"

REVENUE_MAP_SATS = 100_000  # same reference N as country_tam_charts.py's price heatmap

# Keyed to tam_model.tam_by_segment()'s own names. These were "incumbent"/"new"
# under the deleted country_tam_full_model; "connected"/"unconnected" say the same
# thing in the vocabulary the rest of the model uses, so there is one naming scheme
# rather than a translation layer here.
SEGMENT_COLORS = {"connected": "#762a83", "unconnected": "#2ca25f"}
SEGMENT_LABELS = {"connected": "Captured from incumbents (already-connected switchers)",
                   "unconnected": "Newly-connected (previously unconnected)"}

FULL_MODEL_NOTE = "Full-capture model: 100% share inside Starlink's\ncapacity footprint, split-priced by segment.\n" + TAM_SOURCE_NOTE


# --------------------------------------------------------------------------------------
# Chart 1: total TAM by country, choropleth, at N=100,000
# --------------------------------------------------------------------------------------
def fig_revenue_heatmap_by_country(rows: list[tm.CountryTAM], country_paths):
    fig, ax = render.new_figure(figsize=(16, 9))
    revenue = {r.iso3: r.tam_usd_per_month for r in rows if r.tam_usd_per_month > 0}

    import matplotlib as mpl
    cmap = mpl.colormaps["plasma"].copy()
    vmin, vmax = min(revenue.values()), max(revenue.values())
    norm = LogNorm(vmin=max(vmin, 1.0), vmax=vmax)
    draw_choropleth(ax, country_paths, revenue, cmap, norm)

    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(sm, ax=ax, pad=0.015, shrink=0.65)
    cbar.set_label("Total addressable market (USD/month, log scale)")
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    cbar.ax.yaxis.set_minor_formatter(mticker.NullFormatter())

    ax.set_title(f"Total addressable market by country (N={REVENUE_MAP_SATS:,} satellites)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    n_missing = len({r.iso3 for r in rows}) - len(revenue)
    top3 = sorted(rows, key=lambda r: -r.tam_usd_per_month)[:3]
    top3_str = ", ".join(f"{r.iso3} {_usd_formatter(r.tam_usd_per_month, None)}" for r in top3)
    info_box.add_info_box(
        ax, fig,
        f"{len(revenue)} countries priced ({n_missing} missing price data).\n"
        f"Top 3: {top3_str}.\n"
        "Grey = no revenue or no 110m country polygon.\n" + FULL_MODEL_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "tam_full_by_country_100k.png"


# --------------------------------------------------------------------------------------
# Chart 2: total TAM ($/month) vs. total satellites
# --------------------------------------------------------------------------------------
def fig_tam_full_vs_satellites(sat_counts, tam):
    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, tam, color="#762a83", linewidth=2, label="Total Addressable Market ($/mo)")
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    _add_capacity_secondary_axis(ax)
    ax.set_xlabel("Total satellites (V3, log scale)")
    ax.set_ylabel("Total addressable market (USD/month, log scale)")
    ax.set_title("Total addressable market vs. total satellites")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.legend(loc="lower right", fontsize=8.5)

    peak_n = sat_counts[np.argmax(tam)]
    info_box.add_info_box(
        ax, fig,
        f"Peak TAM {_usd_formatter(tam.max(), None)}/mo near N={peak_n:,.0f}.\n" + FULL_MODEL_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "tam_full_vs_satellites.png"


TAM_LINEAR_MAX_SATS = 200_000


def fig_tam_full_vs_satellites_linear(sat_counts, tam):
    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.plot(sat_counts, tam, color="#762a83", linewidth=2, label="Total Addressable Market ($/mo)")
    _add_fleet_reference_lines(ax)

    ax.set_xlim(0, TAM_LINEAR_MAX_SATS)
    ax.set_ylim(0, tam.max() * 1.08)
    _add_capacity_secondary_axis(ax)
    ax.set_xlabel("Total satellites (V3, linear scale)")
    ax.set_ylabel("Total addressable market (USD/month, linear scale)")
    ax.set_title("Total addressable market vs. total satellites (linear)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.legend(loc="upper right", fontsize=8.5)

    peak_n = sat_counts[np.argmax(tam)]
    info_box.add_info_box(
        ax, fig,
        f"Peak TAM {_usd_formatter(tam.max(), None)}/mo near N={peak_n:,.0f}.\n" + FULL_MODEL_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "tam_full_vs_satellites_linear.png"


# --------------------------------------------------------------------------------------
# Chart 3: total TAM, stacked by region, vs. total satellites
# --------------------------------------------------------------------------------------
def fig_tam_full_vs_satellites_stacked_by_region(sat_counts, by_region: dict[str, np.ndarray]):
    fig, ax = render.new_figure(figsize=(13, 8))
    regions = sorted(by_region.keys(), key=lambda r: -by_region[r].sum())
    ax.stackplot(sat_counts, *[by_region[r] for r in regions],
                colors=[REGION_COLORS[r] for r in regions], labels=[REGION_SHORT[r] for r in regions],
                alpha=0.9)
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    _add_capacity_secondary_axis(ax)
    ax.set_xlabel("Total satellites (V3, log scale)")
    ax.set_ylabel("Total addressable market (USD/month)")
    ax.set_title("Total addressable market by region vs. total satellites")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.legend(loc="upper right", fontsize=7.5, ncol=1)

    total = sum(by_region[r] for r in regions)
    peak_n = sat_counts[np.argmax(total)]
    info_box.add_info_box(
        ax, fig,
        f"Peak total TAM {_usd_formatter(total.max(), None)}/mo near N={peak_n:,.0f}.\n" + FULL_MODEL_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "tam_full_vs_satellites_by_region.png"


# --------------------------------------------------------------------------------------
# Chart 4: total TAM, stacked by pricing SEGMENT, vs. total satellites
# --------------------------------------------------------------------------------------
def fig_tam_full_vs_satellites_stacked_by_segment(sat_counts, by_segment: dict[str, np.ndarray]):
    fig, ax = render.new_figure(figsize=(12, 7.5))
    segments = ["unconnected", "connected"]  # newly-connected at bottom -- the smaller, more volatile series
    ax.stackplot(sat_counts, *[by_segment[s] for s in segments],
                colors=[SEGMENT_COLORS[s] for s in segments], labels=[SEGMENT_LABELS[s] for s in segments],
                alpha=0.9)
    _add_fleet_reference_lines(ax)

    ax.set_xscale("log")
    _add_capacity_secondary_axis(ax)
    ax.set_xlabel("Total satellites (V3, log scale)")
    ax.set_ylabel("Total addressable market (USD/month)")
    ax.set_title("Total addressable market by segment vs. total satellites")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.legend(loc="upper right", fontsize=8.5)

    total = by_segment["connected"] + by_segment["unconnected"]
    peak_n = sat_counts[np.argmax(total)]
    incumbent_share_at_peak = by_segment["connected"][np.argmax(total)] / total[np.argmax(total)]
    info_box.add_info_box(
        ax, fig,
        f"Peak total TAM {_usd_formatter(total.max(), None)}/mo near N={peak_n:,.0f} --\n"
        f"{incumbent_share_at_peak:.0%} incumbent-displacement revenue there.\n" + FULL_MODEL_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "tam_full_vs_satellites_by_segment.png"


# --------------------------------------------------------------------------------------
# CSV exports: same wide-format shape as country_tam_charts.export_tam_csv(), full-
# world numbers instead of unconnected-only.
# --------------------------------------------------------------------------------------
def export_tam_full_csv(telecom_rows: list[dict], household_size: dict[str, float],
                         country_pop_by_tile, tile, demand, buckets: list[int] = SAT_BUCKETS):
    """Writes tam_full_by_country_vs_satellites.csv (one row per country) and
    tam_full_by_continent_vs_satellites.csv (one row per region, countries summed)
    -- both wide-format, one column per N in `buckets`. Returns (country_path,
    continent_path)."""
    rows_per_bucket = dict(zip(buckets, tm.sweep_country_tam(
        buckets, telecom_rows, household_size, country_pop_by_tile, tile, demand,
        mode="full", verbose=True)))
    by_iso3_per_bucket = {n: {r.iso3: r.tam_usd_per_month for r in rows} for n, rows in rows_per_bucket.items()}

    bucket_cols = [f"tam_usd_per_month_n{n:,}".replace(",", "_") for n in buckets]

    country_path = OUT_ROOT / "tam_full_by_country_vs_satellites.csv"
    with open(country_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["iso3", "country", "region"] + bucket_cols)
        for row in telecom_rows:
            iso3 = row["iso3"]
            values = [by_iso3_per_bucket[n].get(iso3, "") for n in buckets]
            if all(v == "" for v in values):
                continue
            w.writerow([iso3, row["country"], row["region"]]
                       + [f"{v:.2f}" if v != "" else "" for v in values])

    regions = sorted({r["region"] for r in telecom_rows})
    continent_path = OUT_ROOT / "tam_full_by_continent_vs_satellites.csv"
    with open(continent_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["region"] + bucket_cols)
        for region in regions:
            totals = [sum(r.tam_usd_per_month for r in rows_per_bucket[n] if r.region == region)
                      for n in buckets]
            w.writerow([region] + [f"{t:.2f}" for t in totals])

    return country_path, continent_path


def main():
    telecom_rows, household_size, tile, demand, pop_by_tile = tm.load_inputs(verbose=True)
    args = (telecom_rows, household_size, pop_by_tile, tile, demand)

    revenue_rows = tm.sweep_country_tam([REVENUE_MAP_SATS], *args, mode="full")[0]
    fig, path = fig_revenue_heatmap_by_country(revenue_rows, load_country_paths())
    render.save_fig(fig, path)
    print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    # One sweep, reduced three ways (total, by region, by segment) -- each solve is
    # ~15 s, so three separate sweeps would triple the run for identical numbers.
    sat_counts = np.geomspace(100, 2_000_000, 30)
    rows_log = tm.sweep_country_tam(sat_counts, *args, mode="full", verbose=True)

    fig, path = fig_tam_full_vs_satellites(sat_counts, tm.total_tam(rows_log))
    render.save_fig(fig, path)
    print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    sat_counts_linear = np.linspace(1, TAM_LINEAR_MAX_SATS, 60)
    tam_linear = tm.total_tam(tm.sweep_country_tam(sat_counts_linear, *args, mode="full", verbose=True))
    fig, path = fig_tam_full_vs_satellites_linear(sat_counts_linear, tam_linear)
    render.save_fig(fig, path)
    print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    fig, path = fig_tam_full_vs_satellites_stacked_by_region(sat_counts, tm.tam_by_region(rows_log))
    render.save_fig(fig, path)
    print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    fig, path = fig_tam_full_vs_satellites_stacked_by_segment(sat_counts, tm.tam_by_segment(rows_log))
    render.save_fig(fig, path)
    print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    print("wrote 5 charts")

    country_path, continent_path = export_tam_full_csv(telecom_rows, household_size, pop_by_tile, tile, demand)
    print(f"  wrote {country_path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"  wrote {continent_path.relative_to(Path(__file__).resolve().parent.parent)}")


if __name__ == "__main__":
    main()
