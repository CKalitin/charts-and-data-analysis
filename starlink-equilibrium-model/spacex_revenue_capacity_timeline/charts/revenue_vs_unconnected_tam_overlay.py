"""Overlays REAL Starlink revenue (this sub-folder's own data) onto the main
project's "Unconnected Addressable Market" (UAM) model
(charts/country_tam_charts.py -> results/market/tam_vs_satellites.png) --
answers "how does what Starlink actually earns compare to the model's estimate of
the theoretical ceiling from serving ONLY currently-unconnected people."

x = total satellites (V3-equivalent, log). y = $/month (log) -- same axis
definitions as the original UAM chart, so this is a literal overlay, not a
re-derived comparison. Real revenue points are converted from $/year to $/month
(divide by 12) for full calendar years, EXCEPT the two most recent points (Q1/Q2
2026), which use the REAL reported quarterly revenue directly (revenue / 3 months)
-- a more precise monthly figure than an annual average, and the freshest data
available (see ../data/starlink_revenue_estimates.md, "Q2 2026" correction).

Deliberately does NOT re-run the UAM model live. When this chart was first built the
main project's `country_tam_model.py` was mid-refactor into `tam_model.py`, so
importing either module risked an ImportError or in-flight logic. That refactor has
since landed (2026-09-05), together with a capacity rewrite that moved the servable
fraction from pooled latitude bands onto the 2D tile allocation -- but reading a
checked-in snapshot rather than importing the model is still the right call here,
because re-running the model live would add ~15 s per satellite count to a chart that
only needs 9 of them.

The snapshot is results/market/tam_by_continent_vs_satellites.csv (SAT_BUCKETS from
charts/country_tam_charts.py -- 9 discrete satellite counts, not a dense sweep,
summed across all regions). **That CSV was regenerated on 2026-09-05 and its numbers
moved materially** (the longitude and households fixes together raise UAM ~1.4x at
N=10,900); this chart was re-run against the new one. If it is regenerated again,
re-run this script -- it always re-reads the CSV fresh and never caches its own copy.

Run: python charts/revenue_vs_unconnected_tam_overlay.py
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
MAIN_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UAM_CONTINENT_CSV = MAIN_PROJECT_ROOT / "results" / "market" / "tam_by_continent_vs_satellites.csv"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results"

V3_TBPS_PER_SAT = V3_GBPS_PER_SAT / 1000.0  # 1.024 Tbps/satellite

Q1_2026_END, Q1_2026_REVENUE_M = date(2026, 3, 31), 3257.0
Q2_2026_END, Q2_2026_REVENUE_M = date(2026, 6, 30), 4291.0

SOURCE_NOTE = ("UAM model: World Bank + WorldPop + FCC.\n"
               "Revenue: SpaceX S-1 / earnings.\n"
               "Satellites: Jonathan McDowell (planet4589.org).")
CAVEAT_NOTE = ("UAM = ceiling from unconnected people only.\n"
               "Actual revenue also includes switchers,\n"
               "enterprise, government, mobile.")


def _usd_formatter(x, _pos):
    if x <= 0:
        return "$0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"${x / div:.1f}{suf}"
    return f"${x:.0f}"


def _load_uam_curve():
    """Returns (sat_counts, tam_usd_per_month) from the existing checked-in UAM
    snapshot, summed across all World Bank regions."""
    rows = list(csv.DictReader(open(UAM_CONTINENT_CSV, newline="", encoding="utf-8")))
    bucket_cols = [c for c in rows[0].keys() if c != "region"]
    sat_counts = [int(c.replace("tam_usd_per_month_n", "").replace("_", "")) for c in bucket_cols]
    totals = [sum(float(r[c]) for r in rows if r[c]) for c in bucket_cols]
    paired = sorted(zip(sat_counts, totals))
    return [p[0] for p in paired], [p[1] for p in paired]


def _load_annual_revenue_points():
    """Best-available (official > analyst > press) full-year revenue, converted
    from $B/year to $/month, at each fiscal year's real equivalent-V3-satellite
    count (from actual launch history, not the UAM model's swept N)."""
    events = load_launch_events()
    cum_rows = build_cumulative_table(events)
    v3_by_year: dict[int, float] = {}
    for r in cum_rows:
        year = int(r["date"][:4])
        v3_by_year[year] = float(r["equivalent_v3_satellites"])

    priority = {"official_filing": 0, "analyst_estimate": 1, "press_leak_of_internal_docs": 2}
    best: dict[int, tuple[float, int, float]] = {}  # year -> (priority, revenue_usd_month)
    with open(REVENUE_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["metric"] != "starlink_segment_revenue":
                continue
            year = int(row["fiscal_year"])
            if year not in v3_by_year:
                continue
            p = priority[row["source_type"]]
            if year not in best or p < best[year][0]:
                revenue_usd_month = float(row["value_usd_millions"]) * 1e6 / 12.0
                best[year] = (p, year, revenue_usd_month)

    return [(year, v3_by_year[year], rev) for _, year, rev in best.values()]


def _load_quarterly_points():
    """Real reported quarterly revenue / 3 -- the actual monthly rate, not an
    annual average -- for the two most recent quarters (freshest data)."""
    events = load_launch_events()
    cum_rows = build_cumulative_table(events)
    out = []
    for end_date, revenue_m, label in (
        (Q1_2026_END, Q1_2026_REVENUE_M, "Q1 2026"),
        (Q2_2026_END, Q2_2026_REVENUE_M, "Q2 2026"),
    ):
        cap_tbps = capacity_tbps_at_or_before(cum_rows, end_date)
        v3_sats = cap_tbps / V3_TBPS_PER_SAT
        revenue_usd_month = revenue_m * 1e6 / 3.0
        out.append((label, v3_sats, revenue_usd_month))
    return out


def _draw(ax, sat_counts, tam, annual_points, quarterly_points, *, log_scale: bool):
    ax.plot(sat_counts, tam, color="#2ca25f", linewidth=2, zorder=2,
             label="Unconnected Addressable Market (model)")

    # Annual (year-figure ÷12) and quarterly (real quarter ÷3) points are the same
    # KIND of thing -- actual reported revenue, converted to a $/month rate -- so
    # they get the same dot style. Only the text label next to each point says
    # whether it's a full year or a single quarter; one combined legend entry.
    ax.scatter([p[1] for p in annual_points], [p[2] for p in annual_points],
               marker="o", s=90, facecolor="#2166ac", edgecolor="#2166ac", zorder=3,
               label="Actual Starlink revenue")
    for year, x, y in annual_points:
        ax.annotate(str(year), xy=(x, y), xytext=(6, 5), textcoords="offset points",
                    fontsize=7.5, color="0.25")

    ax.scatter([p[1] for p in quarterly_points], [p[2] for p in quarterly_points],
               marker="o", s=90, facecolor="#2166ac", edgecolor="#2166ac", zorder=4)
    for label, x, y in quarterly_points:
        ax.annotate(label, xy=(x, y), xytext=(6, -12), textcoords="offset points",
                    fontsize=7.5, color="0.25")

    if log_scale:
        ax.set_xscale("log")
        ax.set_yscale("log")
        # Explicit floor just under the smallest real point (2021, ~$18.5M/mo) --
        # without this, matplotlib auto-extends the axis down to that point,
        # wasting most of the plot on empty space below every other point (same
        # "log axis needs an explicit nonzero floor" lesson as elsewhere in this
        # project, e.g. charts/capacity_density.py).
        ax.set_ylim(1e7, max(max(tam), max(p[2] for p in annual_points), max(p[2] for p in quarterly_points)) * 1.3)

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    if log_scale:
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())

    ax.set_xlabel("Total satellites (V3-equivalent" + (", log scale)" if log_scale else ", linear scale)"))
    ax.set_ylabel("USD/month" + (", log scale" if log_scale else ""))
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.text(0.985, 0.03, f"{CAVEAT_NOTE}\n{SOURCE_NOTE}", transform=ax.transAxes,
             fontsize=7, va="bottom", ha="right", color="0.35",
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", alpha=0.85))


def _load():
    sat_counts, tam = _load_uam_curve()
    annual_points = _load_annual_revenue_points()
    quarterly_points = _load_quarterly_points()
    return sat_counts, tam, annual_points, quarterly_points


def fig_overlay_log():
    sat_counts, tam, annual_points, quarterly_points = _load()
    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw(ax, sat_counts, tam, annual_points, quarterly_points, log_scale=True)
    ax.set_title("Revenue (USD/month) vs. total satellites (V3-equivalent)")
    return fig, "revenue_vs_unconnected_tam_overlay_log.png"


LINEAR_MAX_SATS = 50_000  # just past the UAM model's peak (~33,900) -- the real data
# (max ~855 equivalent V3 sats so far) and the model's interesting rise-and-peak shape
# both live in this range; the full 2,000,000-sat swept range used by the log chart
# would squeeze everything of interest into a few pixels at the left edge (checked:
# rendered that way first, all real points and the curve's rise were indistinguishable
# from x=0 -- same "don't render dead space" lesson as elsewhere in this project).


def fig_overlay_linear():
    sat_counts, tam, annual_points, quarterly_points = _load()
    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw(ax, sat_counts, tam, annual_points, quarterly_points, log_scale=False)
    ax.set_xlim(0, LINEAR_MAX_SATS)
    max_y = max(max(tam), max(p[2] for p in annual_points), max(p[2] for p in quarterly_points))
    ax.set_ylim(0, max_y * 1.1)
    ax.set_title("Revenue (USD/month) vs. total satellites (V3-equivalent)")
    return fig, "revenue_vs_unconnected_tam_overlay_linear.png"


def figures():
    return [fig_overlay_log, fig_overlay_linear]


def main():
    for fn in figures():
        fig, filename = fn()
        path = render.save_fig(fig, OUT_ROOT / filename)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
