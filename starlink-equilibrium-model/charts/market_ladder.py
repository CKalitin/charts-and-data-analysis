"""Market ladder: $/Gbps/year vs. cumulative capacity, v3 satellites.

Directly analogous to the Terraform Industries market-ladder chart
(https://terraformindustries.wordpress.com/2026/06/16/..., see
`Terraform-Market-Ladder/terraformer_market_ladder.py`): y = the price a market will pay,
x = cumulative volume unlocked at that price or better. Here the "price" is a country's
ARPU-implied revenue per Gbps/year and the "volume" is cumulative capacity (Gbps) -- this
data already exists, unchanged, as `equilibrium_model.build_revenue_curve()` (Phase 5). This
chart is a NEW way of drawing it (staircase + dual x-axis), not a new model.

The staircase is the REAL per-country granularity (204 countries), not synthetic named
tiers -- Terraform had to invent "markets" to bin fuel demand into; we already have the
real unit (country). This project has a standing rule that a swept-cost curve must be
continuous, not discrete tiers (see CLAUDE.md, "Phase 6") -- that rule was about a
DIFFERENT chart (`continuous_cost_vs_market_size.png`, cost swept as a free parameter).
It doesn't apply here: the steps below are the actual data, not an artificial binning
choice.

Reference cost lines are drawn for EVERY generation this project has $/Gbps economics for
(v1.0, v2 Mini, both v3 scenarios) -- not v3-only -- so a reader can see how far cost has
fallen across generations relative to the same demand curve. Only the secondary top x-axis
(satellite count) stays v3-only: v3's Gbps/satellite (1,024, from
`data/satellite_capacity.csv`) is what makes that conversion meaningful, and it wouldn't
hold for another generation's different per-satellite capacity.

Two versions of the same chart: log-log (the primary version, shows the full range) and
linear-linear (the older/cheaper generations' cost lines sit very close to zero on a
linear y-axis given the revenue curve's range up to $83,800/Gbps/yr -- an inherent
readability tradeoff of linear scale for this data, not a bug, same caveat as
`charts/equilibrium.py`'s linear version).

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
from viz import render

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "market_ladder"

GEN_COST_COLORS = {
    "v1.0": "#313695",
    "v2 Mini": "#4575b4",
    "v3 (Starship initial)": "#8c1a10",
    "v3 (Starship end-state)": "#d73027",
}


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


def _draw_cost_lines(ax, econ, *, side="left", skip_labels=()):
    """Flat cost/Gbps/yr reference line per satellite generation (5yr life + 20% margin,
    cost_per_gbps_model.py), each labeled with text embedded just above its own line
    (not a legend box -- user-requested). `skip_labels` omits a line's text entirely
    (e.g. the linear chart's v3 Starship end-state).

    Label Y-position is computed purely from ax.get_ylim()/get_yscale() (AXES-FRACTION
    space, not pixels) -- both callers finalize scale/limits before calling this, so
    this never depends on a canvas draw pass or on constrained_layout's geometry at
    save time (a real, measured bug in an earlier pixel-based version: matching pixel
    positions were computed via a mid-script `ax.figure.canvas.draw()`, but
    constrained_layout renegotiates axes geometry AGAIN at final `savefig()` time,
    so a chart with more competing elements -- e.g. a legend or secondary axis eating
    vertical room -- silently invalidated the earlier pixel math).

    Close lines are MERGED into one combined label rather than stacked separately.
    v3's two scenarios ($352 vs $305/Gbps/yr) sit closer together in value than one
    line of text is tall -- confirmed by direct pixel measurement (PIL) of rendered
    labels, not assumption: no amount of offset/stacking tuning can fit two separate
    non-overlapping text lines into a gap smaller than one text line's own height.
    Any pair (or run) of lines whose NATURAL positions land within `min_gap_frac` of
    each other gets ONE two-line annotation instead, positioned above the whole
    cluster -- still two colored dashed lines below, but one neutral-colored text
    block, which is the only way to avoid either overlapping text or a label crossing
    through a neighboring line it doesn't belong to."""
    ordered_desc = sorted(econ, key=lambda g: g.cost_per_gbps_with_margin_usd, reverse=True)
    for g in ordered_desc:
        cost_annual = g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS
        color = GEN_COST_COLORS.get(g.label, "#999999")
        ax.axhline(cost_annual, color=color, linestyle="--", linewidth=1.4, alpha=0.85, zorder=4)

    x_frac, ha = (0.015, "left") if side == "left" else (0.985, "right")
    y_lo, y_hi = ax.get_ylim()
    log_scale = ax.get_yscale() == "log"

    def to_frac(y):
        if log_scale:
            return (np.log10(y) - np.log10(y_lo)) / (np.log10(y_hi) - np.log10(y_lo))
        return (y - y_lo) / (y_hi - y_lo)

    def cost_of(g):
        return g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS

    # 0.05 = ~5% of axes height -- clears a single fontsize-7.5 text line (measured
    # 15-17px tall) with real margin even on the shortest axes seen so far (a chart
    # with a secondary top axis eating vertical room compresses the plot area more
    # than a bare one). Also the clustering threshold: two lines closer than this in
    # natural position get merged (see docstring) rather than stacked.
    min_gap_frac = 0.05

    labelable = sorted((g for g in ordered_desc if g.label not in skip_labels), key=cost_of)  # ascending
    clusters: list[list] = []
    for g in labelable:
        frac = to_frac(cost_of(g))
        if clusters and frac - to_frac(cost_of(clusters[-1][-1])) < min_gap_frac:
            clusters[-1].append(g)
        else:
            clusters.append([g])

    prev_frac = None
    for cluster in clusters:
        top_g = cluster[-1]  # highest cost in this cluster -- text sits above IT
        f = to_frac(cost_of(top_g)) + 0.006
        if prev_frac is not None and f < prev_frac + min_gap_frac:
            f = prev_frac + min_gap_frac
        prev_frac = f
        if len(cluster) == 1:
            color = GEN_COST_COLORS.get(top_g.label, "#999999")
            text = f"{top_g.label}: ${cost_of(top_g):,.0f}/Gbps/yr"
        else:
            color = "0.25"  # neutral -- this one text block speaks for multiple colored lines
            text = "\n".join(f"{g.label}: ${cost_of(g):,.0f}/Gbps/yr" for g in reversed(cluster))
        ax.annotate(text, xy=(x_frac, f), xycoords="axes fraction",
                     ha=ha, va="bottom", fontsize=7.5, color=color)


def _draw_ladder(ax, points, econ, v3_downlink_gbps, *, log_scale: bool):
    _draw_staircase(ax, points)

    xmax = points[-1][1]
    if log_scale:
        ax.set_xscale("log")
        ax.set_yscale("log")
        # Floor set just under the lowest few real steps, not the true data minimum
        # (~2 Gbps, Bermuda) -- the first few countries are each individually tiny,
        # so there's nothing informative to show by extending the axis down to them.
        ax.set_xlim(200.0, xmax * 1.6)
        y_all = [rev for _s, _e, rev, _c in points] + [
            g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS for g in econ
        ]
        y_lo, y_hi = min(y_all) * 0.7, max(y_all) * 1.4
        ax.set_ylim(y_lo, y_hi)
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.yaxis.set_minor_formatter(NullFormatter())
        scale_word = "log scale"
    else:
        y_lo, y_hi = 0, points[0][2] * 1.08
        ax.set_xlim(0, xmax * 1.05)
        ax.set_ylim(y_lo, y_hi)
        scale_word = "linear scale"

    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _human(v)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.set_xlabel(f"Cumulative capacity deployed, Gbps ({scale_word})")
    ax.set_ylabel(f"$/Gbps/year ({scale_word})")
    ax.set_title("$/Gbps/year vs. cumulative capacity deployed")

    secax = ax.secondary_xaxis(
        "top", functions=(lambda x: x / v3_downlink_gbps, lambda s: s * v3_downlink_gbps))
    secax.set_xlabel(f"Cumulative v3 satellites ({v3_downlink_gbps:,.0f} Gbps/sat)")
    # Near the left edge, 1 satellite's worth of capacity (1,024 Gbps) is itself most of the
    # visible x-range -- ":,.0f" would round every tick below 0.5 sats down to a duplicate "0"
    # (same log-axis-formatter class of bug documented project-wide, e.g.
    # charts/capacity_density.py). Show one decimal below 10 satellites instead.
    secax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.1f}" if v < 10 else f"{v:,.0f}"))
    secax.xaxis.set_minor_formatter(NullFormatter())

    # Drawn LAST, after every other axes element (labels/secondary axis) is in place --
    # this function forces an intermediate layout pass to read real pixel positions for
    # label stacking, and constrained_layout can still shift the axes slightly at final
    # save time if something is added after that pass. Minimize the window by going last.
    skip_labels = () if log_scale else ("v3 (Starship end-state)",)
    _draw_cost_lines(ax, econ, side="left", skip_labels=skip_labels)


_DEFAULT_LABEL_OFFSET = (10, 14, "left", "bottom")
# Per-country (dx, dy, ha, va) overrides where the default offset collides with the
# staircase, plot edge, or a cost-line label -- checked visually after a first render,
# same process as the deleted _draw_highlights() this replaces. Separate dicts because
# the log and linear renderings put the same 4 countries in very different screen
# positions (a linear y-axis crushes the low-revenue countries toward y=0).
WIDEST_LABEL_OFFSETS_LOG: dict[str, tuple[float, float, str, str]] = {
    "United States": (-12, -24, "right", "top"),
    "Brazil": (-12, -24, "right", "top"),
    "India": (-12, 18, "right", "bottom"),
    # China sits at ~90% across the log x-axis -- the default top-right offset (text
    # extending right) ran past the right edge of the plot. Bottom-left instead.
    "China": (-10, -14, "right", "top"),
}
WIDEST_LABEL_OFFSETS_LINEAR: dict[str, tuple[float, float, str, str]] = {
    "United States": (12, 14, "left", "bottom"),
    "Brazil": (12, 14, "left", "bottom"),
    "China": (12, 40, "left", "bottom"),
    # India sits at the rightmost edge of the linear x-axis -- the default/previous
    # right-extending offset ran past the plot edge. Top-left instead.
    "India": (-12, 68, "right", "bottom"),
}


def _bar_xmid(start, end, *, log_scale):
    if log_scale:
        return np.sqrt(start * end) if start > 0 else end * 1e-3
    return 0.5 * (start + end)


def _draw_widest_bar_labels(ax, points, n=4, *, log_scale=True):
    """Label the N widest steps in the staircase -- the biggest markets by CAPACITY
    (end - start Gbps span), a different cut than the deleted highlight labels' pick-by-
    biggest-real-markets-spread-across-the-curve approach. Dot + leader line + text box,
    same visual language as the old highlight labels, but on a SEPARATE image per user
    request -- the main log/linear charts stay label-free."""
    widest = sorted(points, key=lambda p: (p[1] - p[0]), reverse=True)[:n]
    offsets = WIDEST_LABEL_OFFSETS_LOG if log_scale else WIDEST_LABEL_OFFSETS_LINEAR
    for start, end, rev, c in widest:
        xmid = _bar_xmid(start, end, log_scale=log_scale)
        dx, dy, ha, va = offsets.get(c.country, _DEFAULT_LABEL_OFFSET)
        ax.plot([xmid], [rev], marker="o", ms=6, color="black",
                 markeredgecolor="white", markeredgewidth=0.8, zorder=5)
        ax.annotate("", xy=(xmid, rev), xytext=(dx, dy), textcoords="offset points",
                     zorder=5, arrowprops=dict(arrowstyle="-", color="0.3", lw=0.7, alpha=0.6))
        label = f"{c.country}\n{end - start:,.0f} Gbps · ${rev:,.0f}/Gbps/yr"
        ax.annotate(label, xy=(xmid, rev), xytext=(dx, dy), textcoords="offset points",
                     fontsize=8, ha=ha, va=va, color="0.1", zorder=6,
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.5", lw=0.8, alpha=0.95))


def _draw_capped_block_label(ax, points, *, log_scale=True):
    """Label the flat $100/mo-ARPU-cap plateau (15 merged countries, all tied at the same
    price -- see CLAUDE.md's Phase 6 finding) too -- on a LOG x-axis it visually reads as
    the single longest bar on the chart (spans ~2.7 of the plot's ~4.4 visible decades),
    even though its raw Gbps width (104,219) is smaller than each of the 4 countries
    _draw_widest_bar_labels already picked. Included on this image specifically because
    it's the first (leftmost) bar a reader's eye lands on, not because it wins on the same
    raw-Gbps-width metric as the other four."""
    capped = [(s, e, rev, c) for s, e, rev, c in points if c.arpu_capped]
    if not capped:
        return
    start, end, rev = capped[0][0], capped[-1][1], capped[0][2]
    xmid = _bar_xmid(max(start, end * 1e-4) if log_scale else start, end, log_scale=log_scale)
    ax.plot([xmid], [rev], marker="o", ms=6, color="black",
             markeredgecolor="white", markeredgewidth=0.8, zorder=5)
    # Log: point sits right at the left edge of the plot -- bottom-RIGHT (text extending
    # right) instead of bottom-left, which ran past the left edge.
    dx, dy, ha, va = (10, -30, "left", "top") if log_scale else (10, -14, "left", "top")
    ax.annotate("", xy=(xmid, rev), xytext=(dx, dy), textcoords="offset points",
                 zorder=5, arrowprops=dict(arrowstyle="-", color="0.3", lw=0.7, alpha=0.6))
    label = f"{len(capped)} countries at $100/mo cap (merged)\n{end - start:,.0f} Gbps · ${rev:,.0f}/Gbps/yr"
    ax.annotate(label, xy=(xmid, rev), xytext=(dx, dy), textcoords="offset points",
                 fontsize=8, ha=ha, va=va, color="0.1", zorder=6,
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.5", lw=0.8, alpha=0.95))


def fig_market_ladder_widest_labeled(points, econ, v3_downlink_gbps):
    fig, ax = render.new_figure(figsize=(13, 8))
    _draw_ladder(ax, points, econ, v3_downlink_gbps, log_scale=True)
    _draw_widest_bar_labels(ax, points, n=4, log_scale=True)
    _draw_capped_block_label(ax, points, log_scale=True)
    return fig, OUT_ROOT / "v3_market_ladder_widest_bars_labeled.png"


def fig_market_ladder_linear_widest_labeled(points, econ, v3_downlink_gbps):
    fig, ax = render.new_figure(figsize=(13, 8))
    _draw_ladder(ax, points, econ, v3_downlink_gbps, log_scale=False)
    _draw_widest_bar_labels(ax, points, n=4, log_scale=False)
    _draw_capped_block_label(ax, points, log_scale=False)
    return fig, OUT_ROOT / "v3_market_ladder_linear_widest_bars_labeled.png"


def fig_market_ladder_log(points, econ, v3_downlink_gbps):
    fig, ax = render.new_figure(figsize=(13, 8))
    _draw_ladder(ax, points, econ, v3_downlink_gbps, log_scale=True)
    return fig, OUT_ROOT / "v3_market_ladder.png"


def fig_market_ladder_linear(points, econ, v3_downlink_gbps):
    fig, ax = render.new_figure(figsize=(13, 8))
    _draw_ladder(ax, points, econ, v3_downlink_gbps, log_scale=False)
    return fig, OUT_ROOT / "v3_market_ladder_linear.png"


def figures(points, econ, v3_downlink_gbps):
    return [
        ("market_ladder_log", lambda: fig_market_ladder_log(points, econ, v3_downlink_gbps)),
        ("market_ladder_linear", lambda: fig_market_ladder_linear(points, econ, v3_downlink_gbps)),
        ("market_ladder_widest_labeled", lambda: fig_market_ladder_widest_labeled(points, econ, v3_downlink_gbps)),
        ("market_ladder_linear_widest_labeled", lambda: fig_market_ladder_linear_widest_labeled(points, econ, v3_downlink_gbps)),
    ]


def main():
    demand = em.build_country_demand()
    points = em.build_revenue_curve(demand)
    econ = cgm.build_generation_economics()
    v3_econ = [g for g in econ if g.generation == "v3"]
    v3_downlink_gbps = v3_econ[0].downlink_gbps  # scenario-independent, 1,024 Gbps/sat

    plan = figures(points, econ, v3_downlink_gbps)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")


if __name__ == "__main__":
    main()
