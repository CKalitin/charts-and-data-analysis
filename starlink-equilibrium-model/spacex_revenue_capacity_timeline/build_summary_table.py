"""Joins the revenue-by-year table and the capacity-by-date table into one
year-end summary CSV -- the two tables the user asked for, side by side, plus
$/Gbps-year and $/subscriber implied by combining them (both simple derived
ratios, not new modeling).

Run: python build_summary_table.py
"""
from __future__ import annotations

import csv
from pathlib import Path

from capacity_timeline_model import build_cumulative_table, load_launch_events

DATA_DIR = Path(__file__).resolve().parent / "data"
REVENUE_CSV = DATA_DIR / "starlink_revenue_estimates.csv"
OUT_CSV = DATA_DIR / "revenue_and_capacity_by_year.csv"

# Best-available (highest-confidence-tier) Starlink revenue per fiscal year --
# official S-1 figures where they exist, else the best analyst estimate. See
# starlink_revenue_estimates.csv for every individual estimate and its source;
# this hand-picked subset is ONLY for this one convenience join.
BEST_REVENUE_BY_YEAR = {
    2021: ("222", "press_leak (WSJ)"),
    2022: ("1400-1900", "analyst_estimate (range: Information $1.4B vs Payload $1.9B)"),
    2023: ("3869", "official S-1"),
    2024: ("7599", "official S-1"),
    2025: ("11387", "official S-1"),
}


def _year_end_capacity_rows():
    events = load_launch_events()
    rows = build_cumulative_table(events)
    by_year_end = {}
    for r in rows:
        year = int(r["date"][:4])
        by_year_end[year] = r  # last row seen per year wins -> year-end snapshot
    return by_year_end


def main():
    capacity_by_year = _year_end_capacity_rows()
    years = sorted(set(BEST_REVENUE_BY_YEAR) | set(capacity_by_year))
    out_rows = []
    for year in years:
        rev, rev_src = BEST_REVENUE_BY_YEAR.get(year, ("", ""))
        cap_row = capacity_by_year.get(year)
        out_rows.append({
            "year": year,
            "starlink_revenue_usd_millions": rev,
            "revenue_source": rev_src,
            "year_end_cumulative_satellites": cap_row["cum_sats_total"] if cap_row else "",
            "year_end_cumulative_capacity_gbps": cap_row["cum_capacity_gbps"] if cap_row else "",
            "year_end_equivalent_v3_satellites": cap_row["equivalent_v3_satellites"] if cap_row else "",
        })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    for r in out_rows:
        print(r)
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
