"""Phase 1 sanity-check chart: unconnected population vs. mobile data cost, by country.

Not a final deliverable — this exists to visually validate
data/telecom_market_by_country.csv before it becomes an input to later phases.
Answers: which countries combine a large unserved population with expensive data
(Starlink's ideal early target markets, per the model's own framing) vs. countries
where the unserved population is either small or already served by cheap mobile data.

Run: python charts/sanity_check_telecom.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from viz import render, info_box
from viz.plotting import SeriesSpec, draw
from regions import REGION_COLORS


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:g}{suf}"
    return f"{x:g}"


def _usd_formatter(x, _pos):
    return f"${x:g}"

DATA_CSV = Path(__file__).resolve().parent.parent / "data" / "telecom_market_by_country.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "sanity_check" / "unconnected_pop_vs_mobile_gb_cost.png"

# Labelled outliers: (country name) -> (dx, dy, ha, va) offset in points for ax.annotate.
LABEL_OFFSETS = {
    "India": (8, 6, "left", "bottom"),
    "Nigeria": (8, 6, "left", "bottom"),
    "Pakistan": (8, -6, "left", "top"),
    "Ethiopia": (8, 6, "left", "bottom"),
    "Bangladesh": (-8, 6, "right", "bottom"),
    "Congo, Dem. Rep.": (8, -6, "left", "top"),
    "Indonesia": (8, 6, "left", "bottom"),
    "China": (-8, 6, "right", "bottom"),
    "Tanzania": (8, 6, "left", "bottom"),
    "Myanmar": (8, -6, "left", "top"),
}


def load_rows():
    with open(DATA_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        try:
            unconnected = float(r["unconnected_population_est_coverage_corrected"])
            gb_cost = float(r["mobile_usd_per_gb"])
        except (ValueError, KeyError):
            continue
        if unconnected <= 0 or gb_cost <= 0:
            continue
        out.append({
            "country": r["country"],
            "region": r["region"],
            "unconnected": unconnected,
            "gb_cost": gb_cost,
            "population": float(r["population"]),
        })
    return out


def build_figure(rows):
    fig, ax = render.new_figure(figsize=(11, 7.5))

    series = []
    for region, color in REGION_COLORS.items():
        pts = [r for r in rows if r["region"] == region]
        if not pts:
            continue
        series.append(SeriesSpec(
            x=[p["unconnected"] for p in pts],
            y=[p["gb_cost"] for p in pts],
            label=region,
            kind="scatter",
            color=color,
            alpha=0.75,
        ))
    other = [r for r in rows if r["region"] not in REGION_COLORS]
    if other:
        series.append(SeriesSpec(
            x=[p["unconnected"] for p in other],
            y=[p["gb_cost"] for p in other],
            label="Other",
            kind="scatter",
            color="#999999",
            alpha=0.6,
        ))

    draw(
        ax, series,
        xlabel="Est. unconnected population (log scale)",
        ylabel="Mobile data cost, $/GB (log scale)",
        title="Phase 1 sanity check: unserved population vs. mobile data cost, by country",
        xscale="log", yscale="log",
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))

    top = sorted(rows, key=lambda r: -r["unconnected"])[:10]
    for p in top:
        dx, dy, ha, va = LABEL_OFFSETS.get(p["country"], (6, 6, "left", "bottom"))
        ax.annotate(p["country"], xy=(p["unconnected"], p["gb_cost"]),
                    xytext=(dx, dy), textcoords="offset points",
                    fontsize=7.5, ha=ha, va=va,
                    arrowprops=dict(arrowstyle="-", color="0.4", lw=0.5, alpha=0.6))

    ax.legend(loc="lower left", fontsize=8, ncol=2)

    text = f"{len(rows)} countries. Sanity check only. Source: telecom_market_by_country.csv"
    info_box.add_info_box(ax, fig, text, mode="on")

    return fig


def main():
    rows = load_rows()
    fig = build_figure(rows)
    render.save_fig(fig, OUT_PATH)
    print(f"wrote {OUT_PATH.relative_to(Path(__file__).resolve().parent.parent)} ({len(rows)} countries plotted)")

    # Surface anything counterintuitive in printed output, not just the plot.
    cheap_and_unserved = [r for r in rows if r["gb_cost"] < 0.3 and r["unconnected"] > 5_000_000]
    if cheap_and_unserved:
        names = ", ".join(sorted(r["country"] for r in cheap_and_unserved)[:8])
        print(f"NOTE: {len(cheap_and_unserved)} countries have >5M unconnected people despite "
              f"cheap mobile data (<$0.30/GB) -- unconnected here is likely driven by coverage "
              f"gaps or affordability-of-devices, not data pricing. e.g. {names}")


if __name__ == "__main__":
    main()
