"""Phase 6: derived charts.

  1. Continuous cost-vs-market-size curve -- sweeps cost/Gbps/year continuously
     through equilibrium_model.py instead of just the 4 discrete generation points,
     per the user's explicit instruction that this must be a continuous curve, not
     discrete tiers (see CLAUDE.md).
  2. Utilization chart -- reconciles Phase 5's revenue-optimal satellite counts
     against Phase 2's actual coverage-minimum constellation size (4,408 for Gen1).
     A constellation can't be smaller than what continuous global coverage requires,
     regardless of how few satellites the ranked demand curve alone would justify --
     so utilization can drop below 100% for cheap-cost generations where demand runs
     out before the coverage-minimum satellite count does.
  3. Revenue per satellite vs. satellite number, by generation. The original plan
     called for "segmented by orbital shell" -- NOT implemented, because nothing in
     this project currently maps a specific country's demand to a specific orbital
     shell (Phase 2's shells all provide redundant global-latitude coverage; there's
     no natural per-shell demand assignment to plot). Segmented by GENERATION
     instead, which is the grouping the model actually supports.

Run: python charts/phase6.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cost_per_gbps_model as cgm
import equilibrium_model as em
import orbital_geometry as og
from viz import render

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "phase6"
GEN_COLORS = {"v1.0": "#4575b4", "v2_mini": "#fee090", "v3": "#d73027"}


# --------------------------------------------------------------------------------------
# Chart 1: continuous cost-vs-market-size curve
# --------------------------------------------------------------------------------------
def fig_continuous_cost_vs_market(points, econ):
    costs_annual = [g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS for g in econ]
    lo, hi = min(costs_annual) * 0.5, points[0][2] * 1.02
    cost_range = np.logspace(np.log10(lo), np.log10(hi), 200)
    sweep = em.sweep_cost_curve(points, cost_range)

    fig, ax = render.new_figure(figsize=(11, 7))
    xs = [c for c, g, m, n in sweep]
    ys = [m / 1e9 for c, g, m, n in sweep]
    ax.plot(xs, ys, color="#2c5488", linewidth=2)
    ax.fill_between(xs, 0, ys, color="#4575b4", alpha=0.12)

    gen_points = []
    for g in econ:
        cost_annual = g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS
        result = em.find_equilibrium(points, cost_annual)
        if result is None:
            continue
        eq_gbps, n = result
        market = em.market_size_usd(points, eq_gbps) / 1e9
        color = GEN_COLORS.get(g.generation, "#999999")
        ax.scatter([cost_annual], [market], color=color, s=70, zorder=5, edgecolor="black", linewidth=0.7)
        gen_points.append((g.label, cost_annual, market, color))

    # v3's two launch scenarios land almost on top of each other -- group by rounded
    # position so their labels don't overlap (same fix as charts/equilibrium.py).
    groups: dict[tuple, list] = {}
    for label, cost_annual, market, color in gen_points:
        groups.setdefault((round(np.log10(cost_annual), 1), round(market, 1)), []).append((label, color))
    for (log_cost, market), entries in groups.items():
        cost_annual = 10 ** log_cost
        text = "\n".join(lbl for lbl, _c in entries)
        ax.annotate(text, xy=(cost_annual, market), xytext=(6, -10), textcoords="offset points",
                    fontsize=8, color=entries[0][1])

    ax.set_xscale("log")
    ax.invert_xaxis()  # cost falling left-to-right reads as "cost falling over time/generations"
    ax.set_xlabel("Cost, $/Gbps/year, falling --> (log scale)")
    ax.set_ylabel("Market size captured, $B/year")
    ax.set_title("Continuous cost-vs-market-size curve")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}B"))
    ax.text(0.02, 0.03, "Dots: the 4 actual generation cost points. Source: equilibrium_model.py",
           transform=ax.transAxes, ha="left", va="bottom", fontsize=7.5, color="0.4")

    return fig, OUT_ROOT / "continuous_cost_vs_market_size.png"


# --------------------------------------------------------------------------------------
# Chart 2: utilization -- demand-optimal vs. coverage-minimum constellation size
# --------------------------------------------------------------------------------------
def fig_utilization(points, econ):
    coverage_min_sats = sum(s.total_sats for s in og.load_shells_with_full_geometry())

    labels, markets, utils, sat_counts = [], [], [], []
    for g in econ:
        cost_annual = g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS
        result = em.find_equilibrium(points, cost_annual)
        if result is None:
            continue
        eq_gbps, n = result
        demand_sats = eq_gbps / g.downlink_gbps
        actual_sats = max(demand_sats, coverage_min_sats)
        per_sat_cap = em.CUSTOMERS_PER_GBPS * g.downlink_gbps
        theoretical_max_customers = actual_sats * per_sat_cap
        customers_served = eq_gbps * em.CUSTOMERS_PER_GBPS
        utilization = 100 * customers_served / theoretical_max_customers

        labels.append(g.label)
        markets.append(em.market_size_usd(points, eq_gbps) / 1e9)
        utils.append(utilization)
        sat_counts.append((demand_sats, actual_sats))

    fig, ax = render.new_figure(figsize=(10.5, 6.5))
    x = np.arange(len(labels))
    colors = [GEN_COLORS.get(g.generation, "#999999") for g in econ if em.find_equilibrium(points, g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS)]
    bars = ax.bar(x, markets, color=colors, width=0.5)
    for b, m in zip(bars, markets):
        ax.annotate(f"${m:.1f}B", xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 5), textcoords="offset points", ha="center", fontsize=8.5)

    ax2 = ax.twinx()
    ax2.plot(x, utils, "o-", color="black", linewidth=1.5, markersize=8, zorder=5, label="Utilization %")
    for xi, u, (demand_sats, actual_sats) in zip(x, utils, sat_counts):
        note = f"{u:.0f}%" if demand_sats >= coverage_min_sats else f"{u:.0f}%\n(coverage-bound)"
        ax2.annotate(note, xy=(xi, u), xytext=(0, 10), textcoords="offset points",
                    ha="center", fontsize=8, color="0.2")
    ax2.set_ylim(0, 115)
    ax2.set_ylabel("Utilization % (customers served / constellation's theoretical max)")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Market size captured, $B/year")
    ax.set_title(f"Utilization: demand vs. the {coverage_min_sats:,}-satellite coverage-minimum constellation")
    ax.text(0.02, 0.03,
           f"Coverage minimum: {coverage_min_sats:,} sats (Gen1 shell design).\n"
           f"'Coverage-bound' = demand alone needs fewer sats than that.",
           transform=ax.transAxes, ha="left", va="bottom", fontsize=7.5, color="0.3",
           bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor="0.7"))

    return fig, OUT_ROOT / "utilization.png"


# --------------------------------------------------------------------------------------
# Chart 3: revenue per satellite vs. satellite number, by generation
# --------------------------------------------------------------------------------------
def fig_revenue_per_satellite(points, econ):
    fig, ax = render.new_figure(figsize=(11, 7))

    seen_gen = set()
    max_x = 0.0
    for g in econ:
        if g.generation in seen_gen:
            continue  # v3's two launch scenarios have identical Gbps/satellite -- one line covers both
        seen_gen.add(g.generation)
        xs, ys = [], []
        for start, end, rev_per_gbps, c in points:
            sat_start = start / g.downlink_gbps
            sat_end = end / g.downlink_gbps
            rev_per_sat = rev_per_gbps * g.downlink_gbps
            xs += [sat_start, sat_end]
            ys += [rev_per_sat, rev_per_sat]
        max_x = max(max_x, max(xs))
        color = GEN_COLORS.get(g.generation, "#999999")
        label = g.label.split(" (")[0]  # drop "(Starship initial)" etc -- Gbps/satellite is scenario-independent
        ax.plot(xs, ys, color=color, linewidth=1.6, label=f"{label} ({g.downlink_gbps:.0f} Gbps/sat)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    # xs includes a leading 0 (cumulative count starts at 0) which log scale can't
    # represent -- matplotlib auto-extends the axis below 1 to fit it, generating
    # minor ticks at 0.1/0.01/... that a ":.0f" formatter renders as duplicate "0"
    # labels. Pin the floor at 1 satellite (the smallest meaningful value) instead.
    ax.set_xlim(1, max_x * 1.15)
    ax.set_xlabel("Cumulative satellite number (log scale)")
    ax.set_ylabel("Revenue per satellite, $/year (log scale)")
    ax.set_title("Revenue per satellite vs. satellite number, by generation")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.legend(loc="upper right", fontsize=9)
    ax.text(0.02, 0.03,
           "NOT segmented by orbital shell -- no per-shell demand mapping exists\n"
           "in this model (see module docstring). Segmented by generation instead.",
           transform=ax.transAxes, ha="left", va="bottom", fontsize=7.5, color="0.4")

    return fig, OUT_ROOT / "revenue_per_satellite_by_generation.png"


def figures(points, econ):
    return [
        ("continuous_cost_vs_market", lambda: fig_continuous_cost_vs_market(points, econ)),
        ("utilization", lambda: fig_utilization(points, econ)),
        ("revenue_per_satellite", lambda: fig_revenue_per_satellite(points, econ)),
    ]


def main():
    demand = em.build_country_demand()
    points = em.build_revenue_curve(demand)
    econ = cgm.build_generation_economics()

    plan = figures(points, econ)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")

    coverage_min_sats = sum(s.total_sats for s in og.load_shells_with_full_geometry())
    print(f"\nCoverage-minimum constellation (Gen1 real shell design): {coverage_min_sats:,} satellites")
    for g in econ:
        cost_annual = g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS
        result = em.find_equilibrium(points, cost_annual)
        if result is None:
            continue
        eq_gbps, n = result
        demand_sats = eq_gbps / g.downlink_gbps
        bound = "demand-bound" if demand_sats >= coverage_min_sats else "COVERAGE-BOUND"
        print(f"  {g.label}: {demand_sats:,.0f} demand-optimal satellites ({bound})")


if __name__ == "__main__":
    main()
