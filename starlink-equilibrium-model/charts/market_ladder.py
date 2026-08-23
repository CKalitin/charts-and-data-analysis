"""Market ladder: $/Gbps/year vs. cumulative capacity, v3 satellites.

Directly analogous to the Terraform Industries market-ladder chart
(https://terraformindustries.wordpress.com/2026/06/16/..., see
`Terraform-Market-Ladder/terraformer_market_ladder.py`): y = the price a market will pay,
x = cumulative volume unlocked at that price or better. Here the "price" is a country's
ARPU-implied revenue per Gbps/year and the "volume" is cumulative capacity (Gbps) -- this
data already exists, unchanged, as `equilibrium_model.build_revenue_curve()` (Phase 5). This
chart is a NEW way of drawing it (staircase + labeled steps + dual x-axis), not a new model.

Two differences from Terraform's ladder, both deliberate:
  1. The staircase here is the REAL per-country granularity (204 countries), not synthetic
     named tiers -- Terraform had to invent "markets" to bin fuel demand into; we already have
     the real unit (country). This project has a standing rule that a swept-cost curve must be
     continuous, not discrete tiers (see CLAUDE.md, "Phase 6") -- that rule was about a
     DIFFERENT chart (`continuous_cost_vs_market_size.png`, cost swept as a free parameter).
     It doesn't apply here: the steps below are the actual data, not an artificial binning
     choice.
  2. Only ~12 of the 204 steps are labeled (the biggest real markets by volume, plus the
     ladder's floor/ceiling) -- labeling all 204 would be unreadable. See
     HIGHLIGHT_COUNTRIES below for the exact list and why each was picked.

Scope: v3 ONLY, per the user's explicit request (not all 4 generations like
`charts/equilibrium.py`). v3's Gbps/satellite (1,024, from `data/satellite_capacity.csv`) is
what makes the secondary top x-axis (satellite count) meaningful -- a v1.0 satellite is a
different amount of capacity, so this conversion wouldn't hold for another generation. Both
v3 cost scenarios (Starship "initial" and "end-state", see cost_per_gbps_model.py) are drawn
as reference lines since both are legitimate v3 cost assumptions, not a choice between them.

Run: python charts/market_ladder.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.cm as cm
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.ticker import FuncFormatter, NullFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cost_per_gbps_model as cgm
import equilibrium_model as em
from viz import info_box, render

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "market_ladder"

V3_COST_COLORS = {
    "v3 (Starship initial)": "#8c1a10",
    "v3 (Starship end-state)": "#d73027",
}

# The biggest REAL markets by volume (a reader's actual question: "which countries move this
# curve?"), plus the ladder's floor (Fiji, cheapest) and ceiling neighbour (Norway, the first
# real -- not cap-artifact -- country). Deliberately excludes the 15 countries tied at the
# $100/mo ARPU cap (Bermuda, Central African Republic, ...) -- those are merged into ONE
# labeled block instead (see _draw_artifact_cap_block below), because labeling all 15
# individually would be noise: they're a data-cap artifact, not 15 independently interesting
# markets (the same finding already logged in CLAUDE.md's Phase 6 section). Also deliberately
# short (7, not all ~15 plausible candidates) -- Argentina/Russia/China/Nigeria/Indonesia all
# sit within one log-decade of each other on this curve, so a longer list just crowds that one
# region; these 7 are spread across the FULL curve, each one a genuinely distinct step.
HIGHLIGHT_COUNTRIES = {
    "Norway", "United States", "Mexico", "Brazil", "China", "India", "Fiji",
}

_DEFAULT_OFFSET = (10, 14, "left", "bottom")
LABEL_OFFSETS: dict[str, tuple[float, float, str, str]] = {
    "Norway": (-10, 28, "right", "bottom"),
    "United States": (12, -30, "left", "top"),
    "Mexico": (12, 20, "left", "bottom"),
    "Brazil": (12, -28, "left", "top"),
    "China": (55, 40, "left", "bottom"),
    "India": (-14, 26, "right", "bottom"),
    "Fiji": (14, -30, "left", "top"),
}


def _fmt_dollars(v: float) -> str:
    if v >= 1e9:
        return f"${v / 1e9:.2f}B/yr"
    if v >= 1e6:
        return f"${v / 1e6:.2f}M/yr"
    if v >= 1e3:
        return f"${v / 1e3:.1f}K/yr"
    return f"${v:.0f}/yr"


def _human(x: float) -> str:
    if x >= 1e6:
        return f"{x / 1e6:g}M"
    if x >= 1e3:
        return f"{x / 1e3:g}k"
    return f"{x:g}"


def _draw_staircase(ax, points):
    """Fine per-country staircase, colored by rank position (plasma_r, matching the
    Terraform ladder's palette) via a LineCollection -- 204 tiny segments render as a smooth
    gradient, which is the honest visual for this many real steps (vs. Terraform's ~15
    hand-picked markets, each big enough to render as a distinct colored tread)."""
    n = len(points)
    colors = cm.plasma_r(np.linspace(0.12, 0.9, n))
    segs = [[(start, rev), (end, rev)] for start, end, rev, _c in points]
    ax.add_collection(LineCollection(segs, colors=colors, linewidths=3.2, zorder=3))
    xs = [v for start, end, rev, _c in points for v in (start, end)]
    ys = [v for start, end, rev, _c in points for v in (rev, rev)]
    ax.fill_between(xs, 0, ys, color="#4575b4", alpha=0.08, zorder=1)
    return colors


def _draw_artifact_cap_block(ax, points):
    """The 15 countries tied at ARPU_CAP_USD_MONTH=100 -- merged into one labeled span
    instead of 15 individual annotations. See module docstring."""
    capped = [(start, end, rev, c) for start, end, rev, c in points if c.arpu_capped]
    if not capped:
        return
    lo = capped[0][0] if capped[0][0] > 0 else capped[0][1] * 1e-3
    hi = capped[-1][1]
    rev = capped[0][2]
    total_gbps = sum(c.gbps_needed for _s, _e, _r, c in capped)
    xmid = np.sqrt(max(lo, hi * 1e-4) * hi)
    ax.plot([xmid], [rev], marker="o", ms=6, color="#333333",
             markeredgecolor="white", markeredgewidth=0.8, zorder=4)
    label = (f"{len(capped)} countries at $100/mo ARPU cap (artifact -- see CLAUDE.md)\n"
             f"{_fmt_dollars(rev)}/Gbps · {total_gbps:,.0f} Gbps combined")
    ax.annotate(label, xy=(xmid, rev), xytext=(0, 14), textcoords="offset points",
                fontsize=7.5, ha="left", va="bottom", color="0.15", zorder=6,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.4", lw=0.8, alpha=0.95))


def _draw_highlights(ax, points):
    anchors = []
    xmax = points[-1][1]
    for start, end, rev, c in points:
        if c.country not in HIGHLIGHT_COUNTRIES:
            continue
        xmid = np.sqrt(max(start, xmax * 1e-6) * end)
        dx, dy, ha, va = LABEL_OFFSETS.get(c.country, _DEFAULT_OFFSET)
        anchors.append((c, rev, xmid, dx, dy, ha, va))

    for c, rev, xmid, dx, dy, ha, va in anchors:
        ax.plot([xmid], [rev], marker="o", ms=6, color="black",
                 markeredgecolor="white", markeredgewidth=0.8, zorder=5)
        ax.annotate("", xy=(xmid, rev), xytext=(dx, dy), textcoords="offset points",
                     zorder=5, arrowprops=dict(arrowstyle="-", color="0.3", lw=0.7, alpha=0.6))

    for c, rev, xmid, dx, dy, ha, va in anchors:
        label = f"{c.country}\n${c.arpu_usd_month:.0f}/mo · {_fmt_dollars(rev)}/Gbps"
        ax.annotate(label, xy=(xmid, rev), xytext=(dx, dy), textcoords="offset points",
                     fontsize=7.5, ha=ha, va=va, color="0.1", zorder=6,
                     bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.5", lw=0.8, alpha=0.95))


def _draw_v3_cost_lines(ax, points, v3_econ):
    for g in v3_econ:
        cost_annual = g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS
        color = V3_COST_COLORS.get(g.label, "#d73027")
        ax.axhline(cost_annual, color=color, linestyle="--", linewidth=1.4, alpha=0.85, zorder=4)
        result = em.find_equilibrium(points, cost_annual)
        n_total = len(points)
        note = f"{g.label}: ${cost_annual:,.0f}/Gbps/yr"
        if result:
            eq_gbps, n = result
            note += f" -- serves all {n}/{n_total} modeled countries" if n == n_total else f" -- {n}/{n_total} countries"
        ax.text(0.985, cost_annual, note, transform=ax.get_yaxis_transform(),
                 ha="right", va="bottom", fontsize=7.5, color=color)


def fig_market_ladder():
    demand = em.build_country_demand()
    points = em.build_revenue_curve(demand)
    econ = cgm.build_generation_economics()
    v3_econ = [g for g in econ if g.generation == "v3"]
    v3_downlink_gbps = v3_econ[0].downlink_gbps  # scenario-independent, 1,024 Gbps/sat

    fig, ax = render.new_figure(figsize=(13, 8))

    _draw_staircase(ax, points)
    _draw_artifact_cap_block(ax, points)
    _draw_highlights(ax, points)
    _draw_v3_cost_lines(ax, points, v3_econ)

    ax.set_xscale("log")
    ax.set_yscale("log")
    xmax = points[-1][1]
    # Floor set just under the $100-cap block's marker (~450 Gbps, see
    # _draw_artifact_cap_block), not at the true data minimum (~2 Gbps, Bermuda) -- the first
    # few countries are each individually tiny and already summarized inside that block's
    # label, so there's nothing informative to show by extending the axis down to them.
    x_lo = 200.0
    ax.set_xlim(x_lo, xmax * 1.6)
    y_all = [rev for _s, _e, rev, _c in points] + [
        g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS for g in v3_econ
    ]
    ax.set_ylim(min(y_all) * 0.7, max(y_all) * 1.4)

    ax.set_xlabel("Cumulative capacity deployed, Gbps (log scale)")
    ax.set_ylabel("$/Gbps/year (log scale)")
    ax.set_title("$/Gbps/year vs. cumulative capacity deployed")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _human(v)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.yaxis.set_minor_formatter(NullFormatter())

    secax = ax.secondary_xaxis(
        "top", functions=(lambda x: x / v3_downlink_gbps, lambda s: s * v3_downlink_gbps))
    secax.set_xlabel(f"Cumulative v3 satellites ({v3_downlink_gbps:,.0f} Gbps/sat)")
    # Near the left edge, 1 satellite's worth of capacity (1,024 Gbps) is itself most of the
    # visible x-range -- ":,.0f" would round every tick below 0.5 sats down to a duplicate "0"
    # (same log-axis-formatter class of bug documented project-wide, e.g.
    # charts/capacity_density.py). Show one decimal below 10 satellites instead.
    secax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.1f}" if v < 10 else f"{v:,.0f}"))
    secax.xaxis.set_minor_formatter(NullFormatter())

    param_text = (
        "Staircase: 204 countries ranked by ARPU descending (equilibrium_model.py).\n"
        "Dashed lines: v3 cost/Gbps/yr, 5yr life + 20% margin (cost_per_gbps_model.py)."
    )
    info_box.add_info_box(ax, fig, param_text, mode="on", fontsize=7.5)

    return fig, OUT_ROOT / "v3_market_ladder.png"


def main():
    fig, path = fig_market_ladder()
    render.save_fig(fig, path)
    print(f"wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")


if __name__ == "__main__":
    main()
