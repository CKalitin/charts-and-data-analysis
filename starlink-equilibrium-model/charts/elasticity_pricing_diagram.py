"""Illustrates tam_model.py's elasticity pricing mechanism for ONE example country
("Country A", illustrative -- not a real dataset row). Same axes (range, scale,
labels) as charts/served_population_vs_cost.py's `fig_pct_unconnected_vs_cost_scatter`
elasticity chart -- x = connectivity cost (% of monthly GNI/capita, log), y = % of
population unconnected (linear) -- since this diagram explains the mechanism drawn
on top of that exact chart, not a different one.

The two arrows are CHAINED, not diverging from one shared point:

  Step 1 (blue): starts at Country A's real, current position (its own %unconnected
    on the y-axis, at the cost the elasticity curve implies for that %unconnected)
    and follows the curve DOWN to y=0 -- serving every originally-unconnected person
    drives that country's own %unconnected to 0, and the curve's implied price falls
    to its floor (0.75%) as it goes. Ending %unconnected = 0 means Starlink has
    captured exactly the ORIGINAL %unconnected share of the country's total
    population -- labelled at the arrow's end as "XX% Starlink market share".
  Step 2 (red, STRICTLY HORIZONTAL at y=0): starts exactly where step 1 ends, and
    moves sideways -- at a FIXED 0% unconnected -- from the curve's floor price up
    to Country A's real incumbent price. This is Starlink additionally capturing the
    country's ALREADY-CONNECTED population (mode="full" in tam_model.py), priced at
    what they already pay today. Ends at Country A's own x-coordinate (a light
    vertical guide ties the two together) -- "100% Starlink market share": every
    person in the country, connected or not, is now a Starlink customer.

Country A's numbers (60% unconnected, 10%-of-GNI incumbent price) are fixed,
illustrative inputs, not looked up from telecom_market_by_country.csv.

Run: python charts/elasticity_pricing_diagram.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tam_model as tm
from served_population_vs_cost import load_country_scatter_points, pct_unconnected_from_cost_pct
from viz import render

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "tam"

COUNTRY_A_PCT_UNCONNECTED_TODAY = 60.0
COUNTRY_A_COST_PCT = 10.0

CURVE_COLOR = "black"
STEP1_COLOR = "#4575b4"   # elasticity pricing of the unconnected population
STEP2_COLOR = "#d73027"   # interpolation toward the incumbent price
DOT_COLOR = "#d73027"


def draw(ax):
    # Same x-domain as the original elasticity chart: exactly the real countries'
    # cost% min/max (served_population_vs_cost.fig_pct_unconnected_vs_cost_scatter).
    pts = load_country_scatter_points()
    log_x = np.log10([p[2] for p in pts])
    x_lo, x_hi = 10 ** log_x.min(), 10 ** log_x.max()

    x_fit = np.logspace(np.log10(x_lo), np.log10(x_hi), 300)
    y_fit = pct_unconnected_from_cost_pct(x_fit)
    ax.plot(x_fit, y_fit, color=CURVE_COLOR, lw=2, ls="--", zorder=2,
             label="Elasticity: 0.75% cost -> 0% unconnected, 10% -> 100%")

    floor_x = tm.elasticity_cost_pct(0.0)                              # 0.75%
    start_x = tm.elasticity_cost_pct(COUNTRY_A_PCT_UNCONNECTED_TODAY)  # ~3.55%
    start_y = COUNTRY_A_PCT_UNCONNECTED_TODAY                          # 60
    market_share_unconnected = COUNTRY_A_PCT_UNCONNECTED_TODAY

    # Step 1: from Country A's real current position, follow the curve down to y=0.
    mask = (x_fit >= floor_x) & (x_fit <= start_x)
    x1, y1 = x_fit[mask], y_fit[mask]
    ax.plot(x1, y1, color=STEP1_COLOR, lw=3, label="Step 1: Serve unconnected users, using elasticity to determine pricing", zorder=3)
    ax.annotate("", xy=(x1[0], y1[0]), xytext=(x1[2], y1[2]),
                arrowprops=dict(arrowstyle="-|>", color=STEP1_COLOR, lw=3, mutation_scale=20), zorder=4)

    # Step 2: starts exactly where step 1 ENDS (floor_x, 0), STRICTLY horizontal
    # (y=0 throughout) over to Country A's own x-coordinate -- NOT the dot itself
    # (which sits at y=60), just directly below it. A vertical guide ties the two
    # together so "same x value as Country A" reads as an explicit relationship,
    # not a coincidence.
    ax.plot([], [], color=STEP2_COLOR, lw=3,
            label="Step 2: Serve existing users and interpolate to incumbent price")
    ax.annotate("", xy=(COUNTRY_A_COST_PCT, 0.0), xytext=(floor_x, 0.0),
                arrowprops=dict(arrowstyle="-|>", color=STEP2_COLOR, lw=3, mutation_scale=20), zorder=3)
    ax.plot([COUNTRY_A_COST_PCT, COUNTRY_A_COST_PCT], [0.0, start_y],
             color=DOT_COLOR, lw=1.0, ls=":", alpha=0.6, zorder=2)

    # Country A's real, current position -- label above-left, clear of both the
    # blue curve (which continues rising to the upper-right) and the red
    # horizontal line two rows below -- a leader line ties it back to the point.
    ax.annotate(f"Country A: {COUNTRY_A_PCT_UNCONNECTED_TODAY:.0f}% unconnected today",
                xy=(start_x, start_y), xytext=(-70, 30), textcoords="offset points",
                fontsize=8, color="black", ha="right", va="bottom",
                arrowprops=dict(arrowstyle="-", color="black", lw=0.6, alpha=0.6))

    # Arrow-end market-share labels -- the payoff of the diagram. Both sit BELOW
    # y=0 (in the axis's small negative margin), clear of the diagonal blue line,
    # the dashed curve, and the step-2 caption text above the red line -- all three
    # collided with an above-the-line placement at this junction.
    ax.annotate(f"{market_share_unconnected:.0f}% Starlink market share", xy=(floor_x, 0.0),
                xytext=(-10, 15), textcoords="offset points", fontsize=8.5, fontweight="bold",
                color=STEP1_COLOR, ha="right", va="top")
    ax.annotate("100% Starlink market share", xy=(COUNTRY_A_COST_PCT, 0.0),
                xytext=(3, 12), textcoords="offset points", fontsize=8.5, fontweight="bold",
                color=STEP2_COLOR, ha="left", va="top")

    ax.scatter([COUNTRY_A_COST_PCT], [start_y], color=DOT_COLOR, s=100, zorder=5,
               edgecolor="white", linewidth=0.8)
    ax.annotate("Country A", xy=(COUNTRY_A_COST_PCT, start_y),
                xytext=(10, -14), textcoords="offset points", fontsize=9, fontweight="bold",
                color=DOT_COLOR, va="top")

    ax.set_xscale("log")
    ax.set_ylim(-3, 103)
    ax.set_xlabel("Connectivity cost, % of monthly GNI/capita (raw incumbent price, uncapped, log scale)")
    ax.set_ylabel("% of population unconnected")
    ax.set_title("% of population unconnected vs. connectivity cost, % of monthly GNI/capita")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.legend(loc="upper left", fontsize=8)


def figures():
    def build():
        fig, ax = render.new_figure(figsize=(11, 7.5))
        draw(ax)
        return fig, OUT_ROOT / "elasticity_pricing_mechanism.png"

    return [("elasticity_pricing_mechanism", build)]


if __name__ == "__main__":
    for name, build in figures():
        fig, path = build()
        render.save_fig(fig, path)
        print(f"wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
