"""Starlink revenue ($B) vs. cumulative max deployed capacity (Tbps), with a
parallel secondary x-axis in equivalent V3 satellites -- same axis-pairing
convention as the main project's `charts/country_tam_charts.py`
(`tam_vs_satellites_by_region.png` etc: satellite count primary, Tbps secondary),
just built the other direction here (capacity primary, since that's this
sub-folder's own real historical x-axis; V3-satellite-equivalent secondary).

x = year-end cumulative max downlink capacity (Tbps), from
../data/cumulative_capacity_vs_date.csv (same gross-cumulative, not-net-of-deorbits
figure as capacity_vs_date.py). y = Starlink revenue for that fiscal year, $B, from
../data/starlink_revenue_estimates.csv.

Every individual revenue ESTIMATE for a year is plotted (not silently reconciled to
one number) -- marker shape/fill encodes source type (official filing = filled
circle; analyst estimate = open square; press-leak-of-internal-docs = open
triangle). A single connecting line runs through the best-available point per FULL
YEAR (official filing where one exists, else the analyst/press figure) so the
overall trend reads clearly while the underlying disagreement between sources stays
visible as scattered points at the same x.

2026 has no full-year figure yet, but SpaceX has since IPO'd (Nasdaq: SPCX) and now
reports real quarterly earnings -- Q2 2026's $4,291M, annualized (x4), gives a
~$17.2B/year run-rate. Drawn with the SAME marker as every other official-filing
point (not a distinct shape) -- only its text label ("2026, Q2 run-rate") and its
exclusion from the best-by-year connecting line distinguish it, since it's a
run-rate projection from one quarter, not a reported full-year number.

Run: python charts/revenue_vs_capacity.py
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from capacity_timeline_model import (  # noqa: E402
    V3_GBPS_PER_SAT, build_cumulative_table, capacity_tbps_at_or_before, load_launch_events,
)
from viz import render  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REVENUE_CSV = DATA_DIR / "starlink_revenue_estimates.csv"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results"

V3_TBPS_PER_SAT = V3_GBPS_PER_SAT / 1000.0  # 1.024 Tbps/satellite

Q2_2026_END = date(2026, 6, 30)
Q2_2026_REVENUE_USD_MILLIONS = 4291.0  # SpaceX Q2 2026 earnings release, SEC EDGAR, 2026-08-04

SOURCE_STYLE = {
    "official_filing": dict(marker="o", facecolor="#2166ac", edgecolor="#2166ac", size=90, label="Official (SpaceX S-1 / earnings)"),
    "analyst_estimate": dict(marker="s", facecolor="none", edgecolor="#d6604d", size=70, label="Analyst estimate (Payload / Quilty)"),
    "press_leak_of_internal_docs": dict(marker="^", facecolor="none", edgecolor="#4d4d4d", size=70, label="Press report of leaked internal docs"),
}

SOURCE_NOTE = "Revenue source: see legend. Capacity: Jonathan McDowell (planet4589.org), via Wikipedia"
CAVEAT_NOTE = "Capacity is gross launched, not net of deorbits. Every estimate is a separate point, not reconciled."


def _year_end_capacity_tbps() -> dict[int, float]:
    events = load_launch_events()
    rows = build_cumulative_table(events)
    by_year: dict[int, float] = {}
    for r in rows:
        by_year[int(r["date"][:4])] = float(r["cum_capacity_gbps"]) / 1000.0
    return by_year


def _load_revenue_points(capacity_by_year: dict[int, float]):
    """Returns (points, best_by_year) where points is a list of
    (year, capacity_tbps, revenue_billions, source_type) for every individual
    estimate, and best_by_year is {year: (capacity_tbps, revenue_billions)} for the
    single best-available (official > analyst > press) point per year."""
    points = []
    with open(REVENUE_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["metric"] != "starlink_segment_revenue":
                continue  # excludes the 2026 quarter-only rows, which use distinct metric names
            year = int(row["fiscal_year"])
            if year not in capacity_by_year:
                continue
            revenue_b = float(row["value_usd_millions"]) / 1000.0
            points.append((year, capacity_by_year[year], revenue_b, row["source_type"]))

    priority = {"official_filing": 0, "analyst_estimate": 1, "press_leak_of_internal_docs": 2}
    best_by_year: dict[int, tuple[float, float]] = {}
    best_priority: dict[int, int] = {}
    for year, cap, rev, src in points:
        p = priority[src]
        if year not in best_priority or p < best_priority[year]:
            best_priority[year] = p
            best_by_year[year] = (cap, rev)
    return points, best_by_year


def _q2_2026_run_rate_point():
    """(capacity_tbps, revenue_billions) for the Q2 2026 annualized run-rate --
    real quarterly capacity as of 2026-06-30, real Q2 revenue x4."""
    events = load_launch_events()
    rows = build_cumulative_table(events)
    cap_tbps = capacity_tbps_at_or_before(rows, Q2_2026_END)
    revenue_b = (Q2_2026_REVENUE_USD_MILLIONS * 4) / 1000.0
    return cap_tbps, revenue_b


def _add_v3_satellite_secondary_xaxis(ax):
    """Parallel (secondary) x-axis: equivalent V3 satellites = Tbps / 1.024.

    Same "call after set_xscale, explicit FuncFormatter on major AND minor ticks"
    pattern as charts/serviceable_customers_chart.py's
    _add_capacity_secondary_axis() / this sub-folder's own
    capacity_vs_date.py::_add_v3_equivalent_axis -- see either docstring for the
    full matplotlib-formatter-reset reasoning."""
    def to_v3(tbps):
        return tbps / V3_TBPS_PER_SAT

    def from_v3(v3_sats):
        return v3_sats * V3_TBPS_PER_SAT

    secax = ax.secondary_xaxis("top", functions=(to_v3, from_v3))
    secax.set_xlabel("Equivalent V3 satellites (capacity / 1.024 Tbps)")
    secax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    secax.xaxis.set_minor_formatter(mticker.NullFormatter())
    return secax


def _draw(ax, points, best_by_year, run_rate_point, *, log_scale: bool):
    if log_scale:
        ax.set_xscale("log")
        ax.set_yscale("log")

    _add_v3_satellite_secondary_xaxis(ax)  # AFTER set_xscale -- see its docstring

    years_sorted = sorted(best_by_year)
    line_x = [best_by_year[y][0] for y in years_sorted]
    line_y = [best_by_year[y][1] for y in years_sorted]
    ax.plot(line_x, line_y, color="0.6", linewidth=1.5, linestyle="-", zorder=2)

    seen_labels = set()
    for year, cap, rev, src in points:
        style = SOURCE_STYLE[src]
        label = style["label"] if style["label"] not in seen_labels else None
        seen_labels.add(style["label"])
        ax.scatter(cap, rev, marker=style["marker"], s=style["size"],
                   facecolor=style["facecolor"], edgecolor=style["edgecolor"],
                   linewidth=1.4, zorder=3, label=label)

    # One year label per year, anchored to the BEST (highest-priority-source) point,
    # not per individual estimate -- avoids duplicate overlapping "2024 2024" text
    # where a year has 2-3 disagreeing estimates stacked at nearly the same x.
    for year in sorted(best_by_year):
        cap, rev = best_by_year[year]
        ax.annotate(str(year), xy=(cap, rev), xytext=(7, 5), textcoords="offset points",
                    fontsize=8, color="0.25")

    # Same marker/style as every other official-filing point -- only the label text
    # ("2026, Q2 run-rate") and its exclusion from the connecting line mark this as a
    # different KIND of point, not a different-looking one (per user request: dots
    # stay dots, quarterly vs. annual is a labeling distinction, not a visual one).
    rr_cap, rr_rev = run_rate_point
    official_style = SOURCE_STYLE["official_filing"]
    ax.scatter(rr_cap, rr_rev, marker=official_style["marker"], s=official_style["size"],
               facecolor=official_style["facecolor"], edgecolor=official_style["edgecolor"],
               linewidth=1.4, zorder=4)
    ax.annotate("2026\n(Q2 run-rate)", xy=(rr_cap, rr_rev), xytext=(7, -14), textcoords="offset points",
                fontsize=8, color="0.25")

    all_caps = [p[1] for p in points] + [rr_cap]
    all_revs = [p[2] for p in points] + [rr_rev]
    if log_scale:
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())
        ax.set_xlim(20, max(all_caps) * 1.6)
        ax.set_ylim(0.15, max(all_revs) * 1.6)
    else:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_xlim(0, max(all_caps) * 1.1)
        ax.set_ylim(0, max(all_revs) * 1.15)

    ax.set_xlabel("Cumulative max downlink capacity (Tbps)")
    ax.set_ylabel("Starlink revenue ($B/year)")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.text(0.98, 0.02, f"{CAVEAT_NOTE}\n{SOURCE_NOTE}", transform=ax.transAxes,
             fontsize=7.5, va="bottom", ha="right", color="0.35",
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", alpha=0.85))


def _load():
    capacity_by_year = _year_end_capacity_tbps()
    points, best_by_year = _load_revenue_points(capacity_by_year)
    return points, best_by_year, _q2_2026_run_rate_point()


def fig_revenue_vs_capacity_log():
    points, best_by_year, run_rate_point = _load()
    fig, ax = render.new_figure()
    _draw(ax, points, best_by_year, run_rate_point, log_scale=True)
    ax.set_title("Starlink revenue ($B/year) vs. cumulative max downlink capacity (Tbps)")
    return fig, "revenue_vs_capacity_log.png"


def fig_revenue_vs_capacity_linear():
    points, best_by_year, run_rate_point = _load()
    fig, ax = render.new_figure()
    _draw(ax, points, best_by_year, run_rate_point, log_scale=False)
    ax.set_title("Starlink revenue ($B/year) vs. cumulative max downlink capacity (Tbps)")
    return fig, "revenue_vs_capacity_linear.png"


def figures():
    return [fig_revenue_vs_capacity_log, fig_revenue_vs_capacity_linear]


def main():
    for fn in figures():
        fig, filename = fn()
        path = render.save_fig(fig, OUT_ROOT / filename)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
