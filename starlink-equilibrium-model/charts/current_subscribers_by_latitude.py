"""Current Starlink subscribers vs. latitude. Revision 2: after the user twice
pushed back on giving up too easily, this now covers 7 countries via TWO different
real data sources instead of the original 2:

  - Milestone extrapolation (highest confidence): US, Brazil, Nigeria, Kenya --
    dated subscriber-count anchors from SpaceX/regulators/analysts, extrapolated
    forward with starlink_subscriber_trend.estimate_current() /
    estimate_via_global_relative_growth().
  - Ookla market-share (lower confidence, shown visually distinct -- hatched bars):
    Mexico, Canada, UK -- Ookla's "share of Starlink's global Speedtest samples"
    (Q3 2025) applied to today's global total. A cross-check against the US's own
    direct milestone shows this share-based method understates the US by ~25%
    (1.6M implied vs. 2.0M actual for a similar date) -- so these 3 are directional,
    not precise. See data/starlink_subscribers.md for the full discrepancy writeup.

France was searched again, including French-language ARCEP/press sources, and
genuinely has no public subscriber or market-share figure -- not a missed search,
an actual public-data gap. Same for Germany, Australia, Japan, Philippines, and
Indonesia (a confirmed top-5 market with no % ever stated).

Run: python charts/current_subscribers_by_latitude.py
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import starlink_subscriber_trend as sst
from viz import render

DATA = Path(__file__).resolve().parent.parent / "data"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "capacity"
TARGET_DATE = date(2026, 8, 9)

# (iso3, label, color) -- milestone-based countries first, then Ookla-share-based.
MILESTONE_COUNTRIES = [("USA", "US", "#4575b4"), ("BRA", "Brazil", "#1a9850"),
                      ("NGA", "Nigeria", "#d73027"), ("KEN", "Kenya", "#fc8d59")]
SHARE_COUNTRIES = [("MEX", "Mexico", "#762a83"), ("CAN", "Canada", "#8073ac"), ("GBR", "United Kingdom", "#b2abd2")]


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


def capital_lat(iso3: str) -> float:
    for c in json.load(open(DATA / "raw" / "wb_countries.json", encoding="utf-8"))[1]:
        if c["id"] == iso3:
            return float(c["latitude"])
    raise KeyError(iso3)


def load_ookla_shares():
    shares = {}
    with open(DATA / "starlink_ookla_market_share.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            shares[r["iso3"]] = float(r["share_pct_of_global_samples"])
    return shares


def compute_estimates():
    global_est, _, _, _ = sst.estimate_current("global", TARGET_DATE)
    us_est, *_ = sst.estimate_current("us", TARGET_DATE)
    nigeria_est, *_ = sst.estimate_current("nigeria", TARGET_DATE)
    kenya_est, *_ = sst.estimate_current("kenya", TARGET_DATE)
    brazil_est = sst.estimate_via_global_relative_growth(662000, date(2026, 2, 15), TARGET_DATE)

    shares = load_ookla_shares()
    share_estimates = {iso3: sst.estimate_via_ookla_share(shares[iso3], TARGET_DATE)
                       for iso3, _, _ in SHARE_COUNTRIES}

    milestone_estimates = {"USA": us_est, "BRA": brazil_est, "NGA": nigeria_est, "KEN": kenya_est}
    return global_est, milestone_estimates, share_estimates


def main():
    global_est, milestone_est, share_est = compute_estimates()

    fig, ax = render.new_figure(figsize=(13, 7))

    known_total = 0.0
    for iso3, label, color in MILESTONE_COUNTRIES:
        est = milestone_est[iso3]
        lat = capital_lat(iso3)
        ax.bar([lat], [est], width=3, color=color, zorder=3,
              label=f"{label}: ~{_pop_formatter(est, None)} (milestone-based)")
        known_total += est

    for iso3, label, color in SHARE_COUNTRIES:
        est = share_est[iso3]
        lat = capital_lat(iso3)
        ax.bar([lat], [est], width=3, color=color, zorder=3, hatch="///", edgecolor="white",
              label=f"{label}: ~{_pop_formatter(est, None)} (Ookla share-based, directional)")
        known_total += est

    undisclosed = global_est - known_total
    pct_known = 100 * known_total / global_est

    ax.set_xlabel("Latitude of capital city (degrees)")
    ax.set_ylabel("Estimated Starlink subscribers")
    ax.set_title(f"Current Starlink subscribers by latitude, extrapolated to {TARGET_DATE} -- 7 countries estimated")
    ax.set_xlim(-90, 90)
    ax.invert_xaxis()  # north (positive) on the left, matching the project convention
    ax.xaxis.set_major_locator(mticker.MultipleLocator(15))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.legend(loc="upper left", fontsize=7.8, ncol=1)

    ax.text(0.99, 0.55,
           f"Hatched = directional (Ookla share-based), not precise.\n"
           f"Known: {pct_known:.0f}% of global. Source: starlink_subscribers.md",
           transform=ax.transAxes, ha="right", va="center", fontsize=7.3,
           bbox=dict(boxstyle="round", facecolor="white", alpha=0.92, edgecolor="0.7"))

    path = OUT_ROOT / "current_subscribers_by_latitude.png"
    render.save_fig(fig, path)
    print(f"wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    print(f"\nEstimates as of {TARGET_DATE}:")
    print(f"  Global: ~{global_est:,.0f}")
    for iso3, label, _ in MILESTONE_COUNTRIES:
        print(f"  {label}: ~{milestone_est[iso3]:,.0f}  (milestone-based)")
    for iso3, label, _ in SHARE_COUNTRIES:
        print(f"  {label}: ~{share_est[iso3]:,.0f}  (Ookla share-based)")
    print(f"  Known total: ~{known_total:,.0f} ({pct_known:.1f}% of global)")
    print(f"  Undisclosed: ~{undisclosed:,.0f} ({100-pct_known:.1f}% of global)")


if __name__ == "__main__":
    main()
