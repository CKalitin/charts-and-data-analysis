"""Served vs. unserved population, binned by connectivity cost as % of monthly
income. User-requested (2026-08-09) alongside the affordability analysis in
charts/affordability.py -- answers a different question than that file's ranked
chart: not "how many COUNTRIES clear the affordability bar" but "how much
POPULATION sits in each cost-burden tier, and how much of it is already unserved."

Same served/unserved stacked-bar convention as
charts/population_capacity_overlay.py's latitude chart (same colors), just binned by
connectivity-cost-%-of-GNI instead of latitude. Uses each country's RAW, uncapped
ARPU-proxy price (see affordability.py's _raw_arpu docstring) as % of monthly GNI per
capita -- the international-standard basis (see affordability.py module docstring for
why GNI, not GDP).

Run: python charts/served_population_vs_cost.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from charts.affordability import _raw_arpu
from charts.regions import REGION_COLORS
from viz import render, info_box

DATA = Path(__file__).resolve().parent.parent / "data"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "affordability"
SOURCE_NOTE = "Source: telecom_market_by_country.md"

SERVED_COLOR = "#4575b4"
UNSERVED_COLOR = "#d73027"

# User-specified elasticity anchors (2026-08-09): 0.75% cost -> 0% unconnected, 10%
# cost -> 100% unconnected, linear in log10(cost%) -- NOT a statistical fit through
# the scatter data (see fig_pct_unconnected_vs_cost_scatter below for that context).
# Hoisted to module level (2026-08-14) so country_tam_model.py can invert this SAME
# curve (cost% -> implied price, given a target %unconnected) without duplicating
# the anchor values.
ELASTICITY_X_LO, ELASTICITY_Y_LO = 0.75, 0.0
ELASTICITY_X_HI, ELASTICITY_Y_HI = 10.0, 100.0
ELASTICITY_SLOPE = ((ELASTICITY_Y_HI - ELASTICITY_Y_LO)
                     / (np.log10(ELASTICITY_X_HI) - np.log10(ELASTICITY_X_LO)))
ELASTICITY_INTERCEPT = ELASTICITY_Y_LO - ELASTICITY_SLOPE * np.log10(ELASTICITY_X_LO)


def pct_unconnected_from_cost_pct(cost_pct):
    """The elasticity curve as originally specified: cost% (of monthly GNI/capita)
    -> % unconnected. Clipped to [0, 100] -- only meaningful as a 0-100% model
    between the two anchors."""
    return np.clip(ELASTICITY_SLOPE * np.log10(cost_pct) + ELASTICITY_INTERCEPT, 0, 100)


def cost_pct_from_pct_unconnected(pct_unconnected):
    """INVERSE of the elasticity curve: given a target % unconnected (e.g. the %
    of a country's population capacity constraints mean we can't serve), solve for
    the cost% (of monthly GNI/capita) implied by the SAME log-linear relationship
    -- "what price would need to prevail for this many people to be priced out."
    Not separately clipped: pct_unconnected is already in [0, 100] by construction
    at every call site (100 - a servable fraction in [0, 1]), and the anchors ARE
    the curve's 0/100 endpoints, so the inverse is well-defined and finite across
    the whole valid input range with no singularity (log10(0.75) is finite)."""
    return 10 ** ((np.asarray(pct_unconnected, dtype=float) - ELASTICITY_INTERCEPT) / ELASTICITY_SLOPE)

# Bin edges for cost-as-%-of-monthly-GNI/capita. Irregular/log-ish spacing on
# purpose -- most countries cluster under 10%, so fine bins there and coarse bins
# in the long expensive tail keep every bar visually meaningful (a uniform bin width
# would leave the first 1-2 bins holding almost everyone and the rest nearly empty).
BIN_EDGES = [0, 0.5, 1, 2, 3, 5, 7, 10, 15, 25, 50, float("inf")]


def _bin_label(lo: float, hi: float) -> str:
    if hi == float("inf"):
        return f">{lo:g}%"
    return f"{lo:g}-{hi:g}%"


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


def load_binned_population():
    with open(DATA / "telecom_market_by_country.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    n_bins = len(BIN_EDGES) - 1
    served = np.zeros(n_bins)
    unserved = np.zeros(n_bins)
    skipped_no_price = 0

    for r in rows:
        arpu = _raw_arpu(r)
        gni = r["gni_per_capita_ppp_usd"]
        pop = r["population"]
        unconn = r["unconnected_population_est_coverage_corrected"]
        if not (arpu and gni and pop and unconn):
            skipped_no_price += 1
            continue

        pct_gni = 100 * (arpu * 12) / float(gni)
        pop_total = float(pop)
        pop_unserved = float(unconn)
        pop_served = max(0.0, pop_total - pop_unserved)

        for i in range(n_bins):
            lo, hi = BIN_EDGES[i], BIN_EDGES[i + 1]
            if lo <= pct_gni < hi:
                served[i] += pop_served
                unserved[i] += pop_unserved
                break

    labels = [_bin_label(BIN_EDGES[i], BIN_EDGES[i + 1]) for i in range(n_bins)]
    return labels, served, unserved, skipped_no_price


def fig_served_population_vs_cost(labels, served, unserved):
    fig, ax = render.new_figure(figsize=(12, 7))
    x = np.arange(len(labels))
    ax.bar(x, served, color=SERVED_COLOR, label="Served (connected) population", linewidth=0)
    ax.bar(x, unserved, bottom=served, color=UNSERVED_COLOR, label="Unserved (unconnected) population", linewidth=0)

    totals = served + unserved
    for i, (s, u, t) in enumerate(zip(served, unserved, totals)):
        if t <= 0:
            continue
        pct_unserved = 100 * u / t
        ax.annotate(f"{pct_unserved:.0f}% unserved", xy=(i, t), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=7.5, color="0.3")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_xlabel("Connectivity cost, % of monthly GNI/capita (raw incumbent price, uncapped)")
    ax.set_ylabel("Population")
    ax.set_title("Served vs. unserved population, by connectivity-cost burden")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.legend(loc="upper right", fontsize=9)

    total_pop = served.sum() + unserved.sum()
    total_unserved = unserved.sum()
    info_box.add_info_box(
        ax, fig,
        f"{total_pop/1e9:.1f}B total,\n{total_unserved/1e9:.2f}B unserved.\n" + SOURCE_NOTE,
        mode="on", fontsize=7.8,
    )
    return fig, OUT_ROOT / "served_population_vs_connectivity_cost.png"


def load_country_scatter_points():
    """One row per country (not binned/aggregated) -- (country, region, pct_gni,
    pct_unconnected). User explicitly wanted the un-aggregated version after the
    binned chart above obscured the country-level trend."""
    with open(DATA / "telecom_market_by_country.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    pts = []
    for r in rows:
        arpu = _raw_arpu(r)
        gni, pop, unconn = r["gni_per_capita_ppp_usd"], r["population"], r["unconnected_population_est_coverage_corrected"]
        if not (arpu and gni and pop and unconn):
            continue
        pct_gni = 100 * (arpu * 12) / float(gni)
        pct_unconnected = 100 * float(unconn) / float(pop)
        if pct_gni <= 0:
            continue
        pts.append((r["country"], r["region"], pct_gni, pct_unconnected))
    return pts


# --------------------------------------------------------------------------------------
# Chart 2: per-country scatter -- % unconnected vs. connectivity cost %, with trend
# --------------------------------------------------------------------------------------
def fig_pct_unconnected_vs_cost_scatter(pts):
    fig, ax = render.new_figure(figsize=(11, 7.5))
    for region, color in REGION_COLORS.items():
        xs = [p[2] for p in pts if p[1] == region]
        ys = [p[3] for p in pts if p[1] == region]
        ax.scatter(xs, ys, color=color, s=22, alpha=0.75, edgecolor="none", label=region, zorder=3)

    # User-specified elasticity line (2026-08-09), replacing the earlier statistical
    # fit: anchored at two chosen points -- 0.75% cost -> 0% unconnected, 10% cost ->
    # 100% unconnected -- linear in log10(cost%), not a regression through the data.
    # Clipped to [0, 100] outside the anchors since the line is only meaningful as a
    # 0-100% elasticity model between them. Constants/formula hoisted to module level
    # 2026-08-14 (see pct_unconnected_from_cost_pct() above) so country_tam_model.py
    # can invert this exact curve without duplicating the anchor values.
    log_x = np.log10([p[2] for p in pts])
    y = np.array([p[3] for p in pts])
    r = np.corrcoef(log_x, y)[0, 1]

    x_fit = np.logspace(log_x.min(), log_x.max(), 200)
    y_fit = pct_unconnected_from_cost_pct(x_fit)
    ax.plot(x_fit, y_fit, color="black", linewidth=2, linestyle="--", zorder=5,
           label="Elasticity: 0.75% cost -> 0% unconnected, 10% -> 100%")

    ax.set_xscale("log")
    ax.set_ylim(-3, 103)
    ax.set_xlabel("Connectivity cost, % of monthly GNI/capita (raw incumbent price, uncapped, log scale)")
    ax.set_ylabel("% of population unconnected")
    ax.set_title("% of population unconnected vs. connectivity cost, % of monthly GNI/capita")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.legend(loc="upper left", fontsize=7.5, ncol=1)

    info_box.add_info_box(
        ax, fig,
        f"n={len(pts)} countries.\nPearson r={r:.2f} (log-x).\n" + SOURCE_NOTE,
        mode="on", fontsize=7.8,
    )
    return fig, OUT_ROOT / "pct_unconnected_vs_connectivity_cost_scatter.png"


def main():
    labels, served, unserved, skipped = load_binned_population()
    fig, path = fig_served_population_vs_cost(labels, served, unserved)
    render.save_fig(fig, path)
    print(f"wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")

    total_pop = served.sum() + unserved.sum()
    print(f"\n{total_pop/1e9:.2f}B population binned ({skipped} countries skipped, no price/income/pop data).")
    for lo, hi, s, u in zip(BIN_EDGES[:-1], BIN_EDGES[1:], served, unserved):
        t = s + u
        if t <= 0:
            continue
        print(f"  {_bin_label(lo, hi):>9s}: {t/1e6:8.1f}M total, {100*u/t:5.1f}% unserved")

    pts = load_country_scatter_points()
    fig2, path2 = fig_pct_unconnected_vs_cost_scatter(pts)
    render.save_fig(fig2, path2)
    print(f"\nwrote {path2.relative_to(Path(__file__).resolve().parent.parent)}")
    log_x = np.log10([p[2] for p in pts])
    y = np.array([p[3] for p in pts])
    r = np.corrcoef(log_x, y)[0, 1]
    print(f"  n={len(pts)} countries, Pearson r={r:.3f} (%unconnected vs log10(cost%))")


if __name__ == "__main__":
    main()
