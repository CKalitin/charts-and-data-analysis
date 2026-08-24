"""Affordability analysis: GDP vs GNI per capita, connectivity cost as % of income,
and an elasticity sweep of market size to the income-cap assumption. User-requested
(2026-08-09) while reviewing Phase 6's finding that the ARPU_CAP_USD_MONTH=100 flat
cap let bad-survey-data outlier countries rank above every real high-income market
(see CLAUDE.md's Phase 6 section, ASSUMPTIONS.md #4). This does NOT replace that cap
in the shipped model -- it's the exploratory groundwork the user asked for so they
can pick a cap themselves.

Four charts:
  1. gdp_vs_gni_per_capita.png -- do GDP and GNI per capita actually differ? Log-log
     scatter with a y=x reference line; countries far off the line are exactly the
     profit-shifting (GDP >> GNI, e.g. Ireland/Luxembourg) or remittance/resource-
     income (GNI >> GDP) cases where picking the wrong basis would matter.
  2. connectivity_cost_pct_income_ranked.png -- ALL countries (not top-N), ranked by
     connectivity cost as % of monthly income, GNI basis (the internationally
     standard basis -- see below) with the GDP basis overlaid for direct comparison.
     This uses each country's OWN raw, uncapped ARPU-proxy price -- unlike the
     equilibrium model's ARPU, nothing here is capped, because the point is to see
     how burdensome the real price actually is.
  2b. connectivity_cost_pct_income_ranked_gni_only.png -- same as #2, GNI basis only,
     no GDP series (user-requested standalone version, 2026-08-23).
  3. affordability_cap_elasticity.png -- the requested elasticity chart. Sweeps
     equilibrium_model.build_country_demand(income_cap_pct=...) across a range of
     per-country income caps (replacing the flat $100 cap with X% of each country's
     own monthly GNI/capita) and re-solves the equilibrium market size at each of the
     4 real generation costs. Shows how sensitive total addressable market is to
     where the affordability cap is set.

WHY GNI, NOT GDP, IS THE BASIS: GDP measures production WITHIN a country's borders
(inflated by multinational profit-shifting in e.g. Ireland) while GNI measures income
actually RECEIVED by residents (what a household could actually spend), which is what
"affordability" means. Chart 1 shows this divergence directly.

NOTE (2026-08-09): earlier versions of these charts marked the UN Broadband
Commission / A4AI published affordability targets (5% / 2% of GNI per capita) as
reference lines. Removed at the user's explicit request ("I don't want the UN
contaminating my analysis") -- the % cost and elasticity figures themselves are
unchanged, only the external benchmark annotations were deleted. Don't re-add them
without asking.

Run: python charts/affordability.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cost_per_gbps_model as cgm
import equilibrium_model as em
from charts.regions import REGION_COLORS
from viz import render, info_box

DATA = Path(__file__).resolve().parent.parent / "data"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "affordability"
GEN_COLORS = {"v1.0": "#4575b4", "v2_mini": "#fee090", "v3": "#d73027"}


def _load_rows():
    with open(DATA / "telecom_market_by_country.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _raw_arpu(r) -> float | None:
    """Same dominant-access-mode proxy as equilibrium_model.build_country_demand(),
    but WITHOUT any cap -- this file wants the real, unclamped incumbent price."""
    cellular_dominant = r["cellular_dominant_market"] == "True"
    bb_month, mob_month = r["fixed_broadband_usd_per_month"], r["mobile_usd_per_month_illustrative"]
    if cellular_dominant and mob_month:
        return float(mob_month)
    if bb_month:
        return float(bb_month)
    if mob_month:
        return float(mob_month)
    return None


# --------------------------------------------------------------------------------------
# Chart 1: does GDP per capita differ from GNI per capita?
# --------------------------------------------------------------------------------------
def fig_gdp_vs_gni():
    rows = _load_rows()
    pts = []
    for r in rows:
        gdp, gni = r["gdp_per_capita_ppp_usd"], r["gni_per_capita_ppp_usd"]
        if gdp and gni:
            pts.append((r["country"], r["region"], float(gdp), float(gni)))

    fig, ax = render.new_figure(figsize=(9, 8.5))
    for region, color in REGION_COLORS.items():
        xs = [p[2] for p in pts if p[1] == region]
        ys = [p[3] for p in pts if p[1] == region]
        ax.scatter(xs, ys, color=color, s=22, alpha=0.75, edgecolor="none", label=region, zorder=3)

    lo = min(min(p[2] for p in pts), min(p[3] for p in pts)) * 0.85
    hi = max(max(p[2] for p in pts), max(p[3] for p in pts)) * 1.15
    ax.plot([lo, hi], [lo, hi], color="0.3", linestyle="--", linewidth=1, zorder=1, label="GDP = GNI")

    # Label the biggest divergences -- these are exactly the profit-shifting /
    # remittance cases the module docstring calls out, not random noise. Sorted by
    # x-position and staggered vertically so close points (e.g. Ireland and
    # Luxembourg, both extreme GDP outliers) don't render their labels on top of
    # each other -- same label-collision class already hit in charts/phase6.py.
    ratios = sorted(pts, key=lambda p: abs(np.log(p[2] / p[3])), reverse=True)[:6]
    ratios.sort(key=lambda p: p[2])
    prev_log_gdp = None
    stack = 0
    for country, region, gdp, gni in ratios:
        log_gdp = np.log10(gdp)
        stack = stack + 1 if prev_log_gdp is not None and abs(log_gdp - prev_log_gdp) < 0.08 else 0
        prev_log_gdp = log_gdp
        ax.annotate(country, xy=(gdp, gni), xytext=(4, 4 + stack * 11), textcoords="offset points",
                    fontsize=7.5, color="0.2")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.set_xlabel("GDP per capita, PPP (log scale)")
    ax.set_ylabel("GNI per capita, PPP (log scale)")
    ax.set_title("GNI per capita vs. GDP per capita, PPP, by country")
    ax.legend(loc="upper left", fontsize=7, ncol=1)
    info_box.add_info_box(
        ax, fig,
        "Above line: GNI > GDP (remittances/resource income).\n"
        "Below line: GDP > GNI (profit-shifting). Source: World Bank.",
        mode="off", off_side="bottom", off_frac=0.1,
    )
    return fig, OUT_ROOT / "gdp_vs_gni_per_capita.png"


# --------------------------------------------------------------------------------------
# Chart 2: connectivity cost as % of income, ALL countries, ranked (GNI + GDP basis)
# --------------------------------------------------------------------------------------
def fig_cost_pct_income_ranked():
    rows = _load_rows()
    pts = []
    for r in rows:
        arpu = _raw_arpu(r)
        gni, gdp = r["gni_per_capita_ppp_usd"], r["gdp_per_capita_ppp_usd"]
        if arpu and gni:
            pct_gni = 100 * (arpu * 12) / float(gni)
            pct_gdp = 100 * (arpu * 12) / float(gdp) if gdp else None
            pts.append((r["country"], pct_gni, pct_gdp))

    pts.sort(key=lambda p: -p[1])
    ranks = list(range(1, len(pts) + 1))
    gni_vals = [p[1] for p in pts]
    gdp_vals = [p[2] for p in pts]

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.scatter(ranks, gni_vals, s=10, color="#4575b4", label="% of monthly GNI/capita", zorder=3)
    ax.scatter(ranks, gdp_vals, s=10, color="#fc8d59", alpha=0.7, label="% of monthly GDP/capita", zorder=2)

    ax.set_yscale("log")
    ax.set_xlabel(f"Country rank, by cost as % of monthly GNI/capita (1 = most burdensome, n={len(pts)})")
    ax.set_ylabel("Connectivity cost, % of monthly income (log scale)")
    ax.set_title("Connectivity cost as % of income")
    # ":g" (not ":.0f") -- fixed-decimal rounding collapses every value below 0.5%
    # to a duplicate "0%" tick label, the same class of bug already hit and fixed in
    # charts/phase6.py (log axis + fixed-decimal formatter is a recurring trap).
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.legend(loc="upper right", fontsize=9)
    return fig, OUT_ROOT / "connectivity_cost_pct_income_ranked.png"


# --------------------------------------------------------------------------------------
# Chart 2b: same as above, GNI basis ONLY -- no GDP series
# --------------------------------------------------------------------------------------
def fig_cost_pct_income_ranked_gni_only():
    rows = _load_rows()
    pts = []
    for r in rows:
        arpu = _raw_arpu(r)
        gni = r["gni_per_capita_ppp_usd"]
        if arpu and gni:
            pct_gni = 100 * (arpu * 12) / float(gni)
            pts.append((r["country"], pct_gni))

    pts.sort(key=lambda p: -p[1])
    ranks = list(range(1, len(pts) + 1))
    gni_vals = [p[1] for p in pts]

    fig, ax = render.new_figure(figsize=(12, 7.5))
    ax.scatter(ranks, gni_vals, s=10, color="#4575b4", label="% of monthly GNI/capita", zorder=3)

    ax.set_yscale("log")
    ax.set_xlabel(f"Country rank, by cost as % of monthly GNI/capita (1 = most burdensome, n={len(pts)})")
    ax.set_ylabel("Connectivity cost, % of monthly income (log scale)")
    ax.set_title("Connectivity cost as % of income")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.legend(loc="upper right", fontsize=9)
    return fig, OUT_ROOT / "connectivity_cost_pct_income_ranked_gni_only.png"


# --------------------------------------------------------------------------------------
# Chart 3: elasticity -- market size vs. the income-cap % assumption
# --------------------------------------------------------------------------------------
def fig_affordability_elasticity(econ):
    cap_values = np.logspace(np.log10(0.25), np.log10(25), 40)

    fig, ax = render.new_figure(figsize=(11, 7.5))
    for g in econ:
        cost_annual = g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS
        xs, ys = [], []
        for cap_pct in cap_values:
            demand = em.build_country_demand(income_cap_pct=cap_pct, income_basis="gni")
            points = em.build_revenue_curve(demand)
            result = em.find_equilibrium(points, cost_annual)
            if result is None:
                continue
            eq_gbps, n = result
            market = em.market_size_usd(points, eq_gbps) / 1e9
            xs.append(cap_pct)
            ys.append(market)
        color = GEN_COLORS.get(g.generation, "#999999")
        label = g.label.split(" (")[0]
        # v3's two launch scenarios are cost-identical enough at this resolution that
        # a repeated label would just overlap -- keep only the first per generation.
        if label not in [l.get_label() for l in ax.get_lines()]:
            ax.plot(xs, ys, color=color, linewidth=1.8, marker="o", markersize=3, label=label)

    ax.set_xscale("log")
    ax.set_xlabel("Income-cap assumption, % of monthly GNI/capita (log scale)")
    ax.set_ylabel("Equilibrium market size captured, $B/year")
    ax.set_title("Elasticity: market size vs. the affordability-cap assumption")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}B"))
    ax.legend(loc="lower right", fontsize=9)

    info_box.add_info_box(
        ax, fig,
        "Replaces flat $100 cap with X% of\neach country's own GNI/capita.\nSource: World Bank; Quilty Space (SpaceNews)",
        mode="on",
    )
    return fig, OUT_ROOT / "affordability_cap_elasticity.png"


def figures(econ):
    return [
        ("gdp_vs_gni", fig_gdp_vs_gni),
        ("cost_pct_income_ranked", fig_cost_pct_income_ranked),
        ("cost_pct_income_ranked_gni_only", fig_cost_pct_income_ranked_gni_only),
        ("affordability_elasticity", lambda: fig_affordability_elasticity(econ)),
    ]


def main():
    econ = cgm.build_generation_economics()
    plan = figures(econ)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")


if __name__ == "__main__":
    main()
