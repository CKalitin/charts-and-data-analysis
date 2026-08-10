"""Phase 5: the core equilibrium chart. Revenue-per-Gbps (declining, ranked by
country ARPU, capped by Phase 3 density + coverage) vs. cost-per-Gbps+margin (flat,
per generation, annualized over SATELLITE_LIFETIME_YEARS) -- see equilibrium_model.py
for the full mechanism and every ASSUMPTION this depends on.

Two versions of the same chart: log-log (shows the full range, the primary version)
and linear-linear (user-requested -- note the v3 cost lines sit very close to zero
on a linear y-axis given the revenue curve's range up to $83,800/Gbps/yr, which is
an inherent readability tradeoff of linear scale for this data, not a bug).

Run: python charts/equilibrium.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cost_per_gbps_model as cgm
import equilibrium_model as em
from viz import render

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "equilibrium"
GEN_COLORS = {"v1.0": "#4575b4", "v2_mini": "#fee090", "v3": "#d73027"}


def _draw_equilibrium(ax, points, econ, *, log_scale: bool):
    xs, ys = [], []
    for start, end, rev, c in points:
        xs += [start, end]
        ys += [rev, rev]
    ax.plot(xs, ys, color="#2c5488", linewidth=1.3, label="Revenue per Gbps (by country ARPU)")
    ax.fill_between(xs, 0, ys, color="#4575b4", alpha=0.12)

    results = []
    for g in econ:
        cost_annual = g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS
        result = em.find_equilibrium(points, cost_annual)
        color = GEN_COLORS.get(g.generation, "#999999")
        ax.axhline(cost_annual, color=color, linestyle="--", linewidth=1.3, alpha=0.8)
        if result:
            eq_gbps, n = result
            eq_sats = eq_gbps / g.downlink_gbps
            ax.scatter([eq_gbps], [cost_annual], color=color, s=60, zorder=5, edgecolor="black", linewidth=0.6)
            results.append((g.label, eq_gbps, cost_annual, eq_sats, color))

    # Multiple generations can saturate the SAME equilibrium point (both v3 scenarios
    # hit "serve all modeled demand" here) -- group by x-position so their labels
    # don't render on top of each other, and merge into one annotation per group.
    groups: dict[float, list] = {}
    for label, eq_gbps, cost_annual, eq_sats, color in results:
        groups.setdefault(round(eq_gbps), []).append((label, cost_annual, eq_sats, color))
    for eq_gbps, entries in groups.items():
        entries.sort(key=lambda e: -e[1])  # highest cost first, for vertical label order
        text = "\n".join(f"{lbl}: {sats:,.0f} sats" for lbl, _cost, sats, _c in entries)
        y = entries[0][1]
        ax.annotate(text, xy=(eq_gbps, y), xytext=(8, 10), textcoords="offset points",
                    fontsize=7.5, color=entries[0][3])

    scale_word = "log scale" if log_scale else "linear scale"
    ax.set_xlabel(f"Cumulative capacity deployed, Gbps ({scale_word})")
    ax.set_ylabel(f"$/Gbps/year ({scale_word})")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.legend(loc="upper right", fontsize=8.5)
    ax.text(0.02, 0.97, "Assumes 5yr satellite life, 20% margin. See equilibrium_model.py",
           transform=ax.transAxes, ha="left", va="top", fontsize=7.5, color="0.4")


def fig_equilibrium_log(points, econ):
    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_equilibrium(ax, points, econ, log_scale=True)
    ax.set_xscale("log")
    ax.set_yscale("log")
    # The revenue curve is flat (all ARPU-capped countries tied at the ceiling) from
    # 1 to ~1e5 Gbps -- that stretch carries no information, so start the axis where
    # the curve actually starts moving instead of wasting most of the plot on it.
    ax.set_xlim(1e5, points[-1][1] * 1.15)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_title("Starlink equilibrium: revenue vs. cost per Gbps, by satellite generation (log-log)")
    return fig, OUT_ROOT / "equilibrium_revenue_vs_cost.png"


def fig_equilibrium_linear(points, econ):
    fig, ax = render.new_figure(figsize=(12, 7.5))
    _draw_equilibrium(ax, points, econ, log_scale=False)
    ax.set_xlim(0, points[-1][1] * 1.05)
    ax.set_ylim(0, points[0][2] * 1.08)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M"))
    ax.set_title("Starlink equilibrium: revenue vs. cost per Gbps, by satellite generation (linear)")
    return fig, OUT_ROOT / "equilibrium_revenue_vs_cost_linear.png"


def figures(points, econ):
    return [
        ("equilibrium_log", lambda: fig_equilibrium_log(points, econ)),
        ("equilibrium_linear", lambda: fig_equilibrium_linear(points, econ)),
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

    print(f"\n{len(demand)} countries in demand model, {sum(1 for c in demand if c.arpu_capped)} ARPU-capped.")
    print(f"Revenue curve: ${points[0][2]:,.0f}/Gbps/yr (best market) down to ${points[-1][2]:,.0f}/Gbps/yr (weakest).")
    print(f"Total addressable demand modeled: {points[-1][1]:,.0f} Gbps.\n")

    print("Equilibria by generation:")
    for g in econ:
        cost_annual = g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS
        result = em.find_equilibrium(points, cost_annual)
        if result is None:
            print(f"  {g.label}: NO EQUILIBRIUM -- cost exceeds even the best market")
            continue
        eq_gbps, n_countries = result
        eq_sats = eq_gbps / g.downlink_gbps
        market = em.market_size_usd(points, eq_gbps)
        print(f"  {g.label}: {eq_gbps:,.0f} Gbps, {eq_sats:,.0f} satellites, {n_countries} countries, "
              f"${market/1e9:,.2f}B/yr market")

    last_two = [g for g in econ if g.generation == "v3"]
    if len(last_two) == 2:
        r0 = em.find_equilibrium(points, last_two[0].cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS)
        r1 = em.find_equilibrium(points, last_two[1].cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS)
        if r0 and r1 and r0[1] == len(demand) and r1[1] == len(demand):
            print(f"\nNOTE: both v3 scenarios serve ALL {len(demand)} modeled countries -- at Starship-class\n"
                  f"cost, revenue is no longer the binding constraint on satellite count. This means\n"
                  f"Phase 3's physical density/capacity ceiling (not cost) becomes the real limit on\n"
                  f"how big the constellation can profitably get, consistent with Phase 3's own finding\n"
                  f"that capacity, not demand, may bind first at low satellite-generation costs.")


if __name__ == "__main__":
    main()
