"""Terraformer market ladders for synthetic methane and methanol.

A "market ladder": order every substitution market by reference price (high -> low) and
walk DOWN the price axis. As cumulative deployed production (measured in Terraformer units)
grows, progressively larger / cheaper markets are unlocked. Highest-price/smallest markets
sit top-left (unlocked first); bulk commodity markets sit bottom-right (unlocked last).

  x-axis : cumulative production deployed, in TERRAFORMERS
             1 Terraformer = 2.4 MMcf CH4/yr   (methane)
             1 Terraformer = ~87 t methanol/yr (methanol)
  y-axis : scale / reference price of the product in that market
  each step is annotated with the market name and its $/yr value.

Data: see methane_methanol_market_ladder.csv / .md in this repo (EIA, IGU, S&P Global,
IEA, Methanol Institute, ChemAnalyst). Prices are 2024 basis. This chart is built on the
NON-OVERLAPPING (de-double-counted) decomposition so the cumulative x-axis is physically
meaningful — subset tiers (e.g. total pipeline gas) are broken into their disjoint sectors.

Run:  python terraformer_market_ladder.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from matplotlib import cm
from matplotlib.collections import LineCollection
from matplotlib.ticker import FuncFormatter, NullFormatter

from viz import render
from viz import info_box

MARKET_SHARE_GREEN = "#1a9850"
MARKET_SHARE_RED = "#d73027"

# --------------------------------------------------------------------------------------
# CONFIG — all tunables here
# --------------------------------------------------------------------------------------
OUTPUT_ROOT = Path(__file__).resolve().parent / "outputs" / "market_ladder"

# Terraformer unit definitions (given)
TERRAFORMER_CH4_MMCF_YR = 2.4     # MMcf CH4 per Terraformer per year
TERRAFORMER_MEOH_T_YR = 87.0      # tonnes methanol per Terraformer per year

# Unit conversions
MMBTU_PER_MCF = 1.037             # 1 Mcf natural gas ~ 1.037 MMBtu
MMBTU_PER_TCF = 1.037e9           # 1 Tcf = 1e6 MMcf = 1.037e9 MMBtu
MMCF_PER_TCF = 1.0e6              # 1 Tcf = 1e6 MMcf

# Derived: Terraformers required per unit of annual volume
TERRAFORMERS_PER_TCF_CH4 = MMCF_PER_TCF / TERRAFORMER_CH4_MMCF_YR   # ~416,667
TERRAFORMERS_PER_MT_MEOH = 1.0e6 / TERRAFORMER_MEOH_T_YR            # ~11,494 per Mt

SIGNATURE = "Synthetic-fuel market ladder · 2024 price basis · sources: EIA / IGU / S&P Global / IEA / Methanol Institute"


# --------------------------------------------------------------------------------------
# MODEL — market definitions (non-overlapping) + ladder builder
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Market:
    name: str
    price: float          # reference / scale price (native units on the y-axis)
    volume: float         # annual physical volume, in METHANE/METHANOL-EQUIVALENT native units
                           # (Tcf CH4-equivalent, or Mt methanol-equivalent) — this is what sets
                           # the tier's WIDTH on the Terraformer x-axis.
    dollars_override: float | None = None
    # If set, this tier's $/yr uses THIS value instead of price*volume*dollars_per_vol.
    # Needed for "destination-product TAM" tiers (see mtx_tier() below): the tier's Terraformer
    # WIDTH is sized by the methanol/methane feed that *would* be consumed, but its $/yr is the
    # value of the downstream product market itself (a different price and a different,
    # un-converted volume) — the two can't share one price*volume formula.


@dataclass
class LadderStep:
    """One market placed on the ladder: its price, its width in Terraformers, and $/yr."""
    name: str
    price: float
    terraformers: float       # this market's own size, in Terraformers
    cum_lo: float             # cumulative Terraformers before this market
    cum_hi: float             # cumulative Terraformers after this market
    dollars_per_year: float   # this market's OWN (individual/incremental) value, $/yr
    cumulative_dollars_per_year: float  # running total of all markets unlocked up to & incl. this one, $/yr


# --- Methane: GLOBAL consuming sectors + global LNG trade + off-grid premium -----------
# volume in Tcf/yr; price in $/MMBtu. Non-overlapping decomposition of GLOBAL gas demand:
#   Total global demand   = 4,122 bcm = 145.6 Tcf/yr (IEA Global Energy Review 2025 / IGU
#                            Global Gas Report 2025)
#   Global LNG trade       = 411 Mtpa -> 19.7 Tcf/yr (IGU World LNG Report 2025; already
#                            global, carved OUT of the sectoral total below so it isn't
#                            double-counted — LNG cargoes end up inside power/industry/
#                            buildings demand in the IMPORTING country)
#   Gas-fired electricity  = 39% of global demand = 56.8 Tcf/yr (IEA World Energy Outlook
#                            2023 sector share x IGU global total)
#   Residential/commercial = 21% of global demand = 30.6 Tcf/yr (same source)
#   Ammonia feedstock      = 170 bcm -> 6.0 Tcf/yr (IEA Ammonia Technology Roadmap — a
#                            NAMED SUBSET of "industry", carved out, not additive to it)
#   Industrial (residual)  = 145.6 - 56.8 - 30.6 - 6.0 - 19.7 = 32.5 Tcf/yr — a PLUG figure
#                            (total minus every other named sector), not independently
#                            itemized; also absorbs the LNG-trade deduction (a simplification
#                            — real LNG cargoes split across power/industry/buildings in the
#                            importing country, not industry alone)
#   Remote/off-grid + CNG/LNG vehicle: kept at their old ILLUSTRATIVE (originally US-sized)
#                            volumes — no global physical-volume source was found for these
#                            two niche tiers. At <1% of the 145.6 Tcf total, layering them on
#                            top is an immaterial, flagged approximation, not a sourced figure.
#   Industrial/residential reference prices are US benchmarks (EIA) used as a GLOBAL proxy in
#   the absence of a single blended global price — same convention Casey's own chart uses for
#   Henry Hub as a "global bulk" floor price.
METHANE_MARKETS_GLOBAL = [
    Market("Remote / off-grid fuel\n(propane displacement)", 27.00, 1.34),
    Market("CNG/LNG vehicle fuel", 20.00, 0.04),
    Market("Global LNG trade (JKM-priced)", 11.91, 19.7),
    Market("Industrial process fuel\n(residual, ex-ammonia/LNG)", 3.50, 32.5),
    Market("Ammonia / fertilizer feedstock", 3.00, 6.0),
    Market("Residential / commercial\n(global buildings, 21% share)", 2.30, 30.6),
    Market("Gas-fired electricity\n(global power, 39% share)", 2.21, 56.8),
]

# --- Methanol, FEEDSTOCK-VALUE approach (kept as-is — "back pocket") ------------------
# Every tier priced as: methanol netback price x methanol tonnage CONSUMED in that use case.
# Assumption: Terraform sells raw METHANOL (feedstock) into each market, never the converted
# end-product. This is the ORIGINAL model from this repo's research (methane_methanol_market_
# ladder.csv/.md) and stays unmodified as an alternate, always-available view.
# volume in Mt/yr; price in $/t (methanol netback / reference value in that market).
METHANOL_MARKETS_FEEDSTOCK = [
    Market("Specialty chemicals", 600.0, 3.0),
    Market("Marine fuel\n(green-methanol premium)", 500.0, 2.2),
    Market("MTBE / gasoline octane", 380.0, 10.0),
    Market("Acetic acid", 360.0, 8.0),
    Market("Formaldehyde", 350.0, 24.0),
    Market("Methanol-to-olefins (MTO)", 340.0, 33.0),
    Market("Bulk fuel\n(gasoline blend / MTG / DME)", 320.0, 20.0),
]


# --- Methanol, DESTINATION-PRODUCT TAM approach ("Casey's approach") -------------------
# Answers a DIFFERENT question for the MTX (methanol-to-X conversion) tiers: not "how much
# methanol gets sold" but "how large is the whole downstream product market that becomes
# reachable once methanol-to-X conversion is cost-competitive." Assumption: for these tiers,
# Terraform (or a licensee) is assumed to convert methanol and sell the END PRODUCT — synthetic
# gasoline/diesel/jet fuel/olefins — not raw methanol. This is why the $/yr jumps by 1-2 orders
# of magnitude on these tiers: global gasoline/diesel/jet markets each dwarf the entire global
# methanol market on their own.
#
# The y-axis price stays "$/t methanol" (the max methanol synthesis cost for which the
# conversion is still profitable, i.e. downstream netback) — unchanged semantics. Only the
# WIDTH (Terraformers) and $/yr use the destination product's own volume/price:
#   width ($/yr basis)  = product_price x product_volume         (the actual TAM)
#   width (Terraformers) = product_volume x conversion_ratio x TERRAFORMERS_PER_MT_MEOH
#                          (how much methanol-equivalent production is needed to fully
#                          convert-and-serve that whole destination market)
#
# Non-MTX tiers (specialty/marine/MTBE/acetic acid/formaldehyde/DME) are NOT rebuilt — Casey's
# own chart treats these the same way (sold as-is or lightly purified, not converted), so they
# keep the feedstock-value framing.
#
# Sources for destination-product data:
#   Gasoline: 27.5 Mbpd (IEA, "Motor Gasoline demand... 27,504 kbd in 2024") x ~0.119 t/bbl
#             ~1,190 Mt/yr; wholesale ref price ~$839/t (derived from 2024 US retail ~$3.32/gal
#             less tax/margin -> RBOB-spot-class wholesale ~$2.35/gal, converted at 357 gal/t)
#   Diesel:   ~29 Mbpd gasoil/diesel (IEA Oil 2025, 2023 actual, 2024 approx) x ~0.134 t/bbl
#             ~1,418 Mt/yr; wholesale ref price ~$839/t (derived similarly from 2024 on-highway
#             retail ~$3.76/gal less tax/margin -> ULSD-spot-class wholesale ~$2.70/gal)
#   Jet fuel: ~7.5 Mbpd (Goldman Sachs/IEA 2024, range 6.46-8.0 Mbpd across sources, flagged)
#             x ~0.127 t/bbl ~330 Mt/yr; wholesale ref price ~$770/t (derived from 2024 US
#             Gulf Coast jet spot ~$2.33/gal, back-solved from the sourced 2025 avg $2.11/gal
#             and its stated 9.6% YoY decline)
#   Olefins:  ethylene >160 Mt + propylene >90 Mt = ~250 Mt/yr (S&P Global Olefin Industry
#             Outlook); price $800-1450/t range, $1,000/t blended midpoint used
#   Conversion ratios (t methanol feed per t product):
#     MTG gasoline: 2.584 (SOURCED — ExxonMobil Motunui plant historical operating data:
#                   1,000 t methanol -> 387 t gasoline)
#     MTO olefins, MTX diesel, MTX jet: 2.9 (ENGINEERING ESTIMATE/ASSUMPTION — MTO's commonly
#                   cited industry rule-of-thumb ratio, extended to diesel/jet for lack of a
#                   commercial-scale reference; MTX-to-diesel/jet is not yet at commercial
#                   scale, so this is explicitly a modeling assumption, not a cited figure)
#
# All dollar-per-tonne wholesale prices above are DERIVED (retail minus an assumed tax/margin
# to approximate a wholesale/spot basis, consistent with using benchmark — not retail — prices
# everywhere else in this chart), not directly read off a single citation; flagged accordingly.

TERRAFORMERS_PER_MT_MEOH_CONST = 1.0e6 / TERRAFORMER_MEOH_T_YR  # defined again for clarity below


def mtx_tier(name: str, methanol_price_ceiling: float, product_price_per_t: float,
             product_volume_mt: float, conversion_ratio: float) -> Market:
    """Build a destination-product TAM tier.

    y-axis position stays the methanol netback ceiling; $/yr and Terraformer-width instead
    reflect the destination PRODUCT's own global market (see module docstring above).
    """
    meoh_equivalent_mt = product_volume_mt * conversion_ratio
    dollars_per_year = product_price_per_t * product_volume_mt * 1.0e6
    return Market(name, methanol_price_ceiling, meoh_equivalent_mt, dollars_override=dollars_per_year)


METHANOL_MARKETS_MTX_TAM = [
    Market("Specialty chemicals", 600.0, 3.0),
    Market("Marine fuel\n(green-methanol premium)", 500.0, 2.2),
    Market("MTBE / gasoline octane", 380.0, 10.0),
    Market("Acetic acid", 360.0, 8.0),
    Market("Formaldehyde", 350.0, 24.0),
    mtx_tier("MTX aromatics/olefins\n(global olefins TAM)", 340.0,
             product_price_per_t=1000.0, product_volume_mt=250.0, conversion_ratio=2.9),
    Market("Bulk DME\n(residual direct-fuel use)", 320.0, 9.0),
    mtx_tier("MTG gasoline\n(global gasoline TAM)", 223.0,
             product_price_per_t=839.0, product_volume_mt=1190.0, conversion_ratio=2.584),
    mtx_tier("MTX diesel\n(global diesel TAM)", 190.0,
             product_price_per_t=839.0, product_volume_mt=1418.0, conversion_ratio=2.9),
    mtx_tier("MTX jet / Jet-A\n(global jet fuel TAM)", 167.0,
             product_price_per_t=770.0, product_volume_mt=330.0, conversion_ratio=2.9),
]


def build_ladder(markets: list[Market], terraformers_per_vol: float,
                 dollars_per_vol: float) -> list[LadderStep]:
    """Sort markets by price (high->low) and accumulate Terraformer width left->right.

    dollars_per_vol converts (price * volume) into $/yr:
      methane  : price[$/MMBtu] * volume[Tcf] * MMBTU_PER_TCF
      methanol : price[$/t]     * volume[Mt]  * 1e6 t/Mt
    """
    ordered = sorted(markets, key=lambda m: m.price, reverse=True)
    steps: list[LadderStep] = []
    cum = 0.0
    cum_dollars = 0.0
    for m in ordered:
        width = m.volume * terraformers_per_vol
        dpy = m.dollars_override if m.dollars_override is not None else m.price * m.volume * dollars_per_vol
        cum_dollars += dpy
        steps.append(LadderStep(m.name, m.price, width, cum, cum + width, dpy, cum_dollars))
        cum += width
    return steps


# --------------------------------------------------------------------------------------
# PLOTTING — one draw() for both ladders
# --------------------------------------------------------------------------------------
def _fmt_dollars(v: float) -> str:
    """$/yr in compact form."""
    if v >= 1e12:
        return f"${v / 1e12:.2f}T/yr"
    if v >= 1e9:
        return f"${v / 1e9:.1f}B/yr"
    return f"${v / 1e6:.0f}M/yr"


def _human(x: float) -> str:
    """Big count -> 100k / 1M / 10M (no mathtext — parse_math is off)."""
    if x >= 1e6:
        return f"{x / 1e6:g}M"
    if x >= 1e3:
        return f"{x / 1e3:g}k"
    return f"{x:g}"


def add_market_share_axis(ax, steps: list[LadderStep]) -> None:
    """Overlay Terraform's share of the currently-unlocked cumulative market, on a secondary
    (right) y-axis: share(x) = x / H_n, where x is Terraform's own cumulative production (the
    SAME quantity as the primary x-axis — no elasticity means no separate growth trajectory is
    needed, we just sweep the existing axis) and H_n is the cumulative ceiling of whichever
    tier x currently falls into.

    Within a tier this is exactly LINEAR in x (constant denominator) — but the x-axis is log,
    so it renders as a convex "exponential-looking" rise. At every tier boundary the ceiling H_n
    jumps up (a bigger, cheaper market just opened), so share drops discontinuously and climbs
    again. Only past the very last tier (x beyond total addressable size) does the curve cross
    100% and keep climbing — green below, red at/above (matching "no elasticity" breaking down:
    Terraform producing more than the fixed total market it could possibly reach).
    """
    cum_los = np.array([s.cum_lo for s in steps])
    cum_his = np.array([s.cum_hi for s in steps])
    xlo, xhi = ax.get_xlim()

    x_parts = []
    for lo, hi in zip(cum_los, cum_his):
        lo_c, hi_c = max(lo, xlo), min(hi, xhi)
        if hi_c > lo_c:
            x_parts.append(np.linspace(lo_c, hi_c, 150))   # dense: linear-in-x, but log-x screen
    if xhi > cum_his[-1]:                                   # extend past the last tier's ceiling
        x_parts.append(np.linspace(cum_his[-1], xhi, 150))
    x_all = np.unique(np.concatenate(x_parts))
    x_all = x_all[x_all > 0]

    tier_idx = np.clip(np.searchsorted(cum_his, x_all, side="left"), 0, len(steps) - 1)
    share = x_all / cum_his[tier_idx]

    ax2 = ax.twinx()
    # twinx() draws the new axes ON TOP of `ax` by default, which would put this line over
    # every price label drawn on `ax` — push it BEHIND ax instead, and make ax's own background
    # patch transparent so ax2's content shows through it (the standard twin-axis z-order flip).
    ax2.set_zorder(ax.get_zorder() - 1)
    ax.patch.set_visible(False)
    pts = np.array([x_all, share]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    seg_peak = np.maximum(share[:-1], share[1:])
    colors = np.where(seg_peak > 1.0, MARKET_SHARE_RED, MARKET_SHARE_GREEN)
    ax2.add_collection(LineCollection(segs, colors=colors, linewidths=1.8, zorder=7))

    ax2.axhline(1.0, color="0.35", lw=0.8, ls=":", zorder=6)
    ax2.set_ylim(0, max(1.15, float(share.max()) * 1.08))
    ax2.set_ylabel("Terraform's share of unlocked market", color="0.3", fontsize=8.5)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v * 100:.0f}%"))
    ax2.tick_params(axis="y", labelsize=8, colors="0.3")
    # constrained_layout was clipping this label — it doesn't reliably budget room for a twin
    # axis's own ylabel against the rightmost price-tier annotate boxes. Reserve a fixed slice
    # of figure width explicitly via the layout engine's own `rect`, rather than fighting it
    # with set_position() (broke the left axis earlier) or guessing at a wider figsize (shifted
    # the info-box scan's corner scoring last time). This only shrinks the managed area by a
    # fixed, small amount — it doesn't change the figure size, so it doesn't perturb the scan.
    ax.figure.get_layout_engine().set(rect=(0, 0, 0.95, 1))

    # info_box.add_info_box only scans `ax` — it has no idea ax2 (a separate Axes) exists, so
    # its occupancy scan is blind to this curve and to the % ticks just added. Mirror both onto
    # `ax` as fully invisible (alpha=0) artists: bbox/window-extent is still computed for alpha=0
    # text and line data is still readable via ax.get_lines() regardless of alpha, so the scan
    # avoids them correctly without anything actually being drawn twice on screen.
    fig = ax.figure
    fig.canvas.draw()   # settle transforms before converting ax2 screen coords -> ax data coords
    px = ax2.transData.transform(np.column_stack([x_all, share]))
    xd, yd = ax.transData.inverted().transform(px).T
    ax.plot(xd, yd, alpha=0, lw=1.8)
    for frac_y in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        ax.text(0.995, frac_y, "100%", transform=ax.transAxes, ha="right", va="center",
                alpha=0, fontsize=8)


_DEFAULT_OFFSET = (8, 10, "left", "bottom")


def draw(ax, fig, steps: list[LadderStep], *, title: str, y_label: str, x_top_label: str,
         top_per_terraformer_vol: float, yscale: str, price_fmt, y_ticks,
         top_fmt, label_offsets: dict, param_text: str) -> None:
    """Draw a descending market-ladder staircase with annotated steps.

    top_per_terraformer_vol : native volume per Terraformer, to label a secondary top x-axis
                              in physical units (Tcf or Mt).
    label_offsets           : {market_name: (dx_pts, dy_pts, ha, va)} per-point offset override,
                              in the SAME data-anchored offset-points scheme as the default —
                              never a distant shared column. Tune only the overlapping
                              neighbours (see skill: "Labels overlap into mush"); unlisted
                              names fall back to _DEFAULT_OFFSET.
    """
    n = len(steps)
    colors = cm.plasma_r(np.linspace(0.12, 0.9, n))

    # Descending staircase: horizontal tread per market + vertical risers between them.
    for i, s in enumerate(steps):
        c = colors[i]
        ax.plot([s.cum_lo, s.cum_hi], [s.price, s.price], color=c, lw=5,
                solid_capstyle="butt", zorder=3)
        if i + 1 < n:                       # riser down to the next (cheaper) market
            nxt = steps[i + 1]
            ax.plot([s.cum_hi, s.cum_hi], [s.price, nxt.price], color="0.6",
                    lw=1.0, ls="--", zorder=2)

    # Anchor markers + labels. Every label is anchored to ITS OWN dot via offset points (never
    # a shared distant column — that's what produced crossing leader lines previously). Crowded
    # neighbours get a larger, individually-tuned dy so they cascade instead of overlapping.
    #
    # Two-pass z-order (this is the fix for "lines on top of labels"): with a single annotate()
    # call per point, a LATER point's leader line can still render on TOP of an EARLIER point's
    # box, because equal zorder falls back to draw order. Drawing ALL leader arrows first (lower
    # zorder), then ALL text boxes on top (higher zorder) in a second pass guarantees every box
    # wins against every line, regardless of iteration order — fixed once, for every chart.
    xmax = steps[-1].cum_hi
    anchors = []
    for i, s in enumerate(steps):
        xmid = np.sqrt(max(s.cum_lo, xmax * 1e-4) * s.cum_hi)   # geometric mid on log-x
        ax.plot([xmid], [s.price], marker="o", ms=6, color=colors[i],
                markeredgecolor="white", markeredgewidth=0.8, zorder=4)
        dx, dy, ha, va = label_offsets.get(s.name, _DEFAULT_OFFSET)
        anchors.append((s, colors[i], xmid, dx, dy, ha, va))

    # Pass 1 — leader arrows only (no text), zorder below every box.
    for s, c, xmid, dx, dy, ha, va in anchors:
        if abs(dx) > 10 or abs(dy) > 14:
            ax.annotate("", xy=(xmid, s.price), xytext=(dx, dy), textcoords="offset points",
                        zorder=5, arrowprops=dict(arrowstyle="-", color=c, lw=0.7, alpha=0.6))

    # Pass 2 — text + boxes, zorder above every arrow drawn in pass 1.
    for s, c, xmid, dx, dy, ha, va in anchors:
        label = (f"{s.name}\n{price_fmt(s.price)}"
                 f" · Mkt {_fmt_dollars(s.dollars_per_year)}"
                 f" · Σ{_fmt_dollars(s.cumulative_dollars_per_year)}")
        bbox = dict(boxstyle="round,pad=0.25", fc="white", ec=c, lw=0.8, alpha=0.95)
        ax.annotate(label, xy=(xmid, s.price), xytext=(dx, dy), textcoords="offset points",
                    fontsize=7.5, ha=ha, va=va, color="0.12", zorder=6, bbox=bbox)

    ax.set_xscale("log")
    ax.set_yscale(yscale)
    ax.set_xlabel("Cumulative production deployed  [Terraformers]")
    ax.set_ylabel(y_label)
    ax.set_title(title, fontsize=12, weight="bold", pad=28)

    # Headroom so top labels don't clip.
    ax.set_xlim(steps[0].terraformers * 0.03, xmax * 1.7)
    if yscale == "log":
        ax.set_ylim(steps[-1].price * 0.85, steps[0].price * 1.6)
    else:
        pad = (steps[0].price - steps[-1].price) * 0.18
        ax.set_ylim(steps[-1].price - pad, steps[0].price + pad * 2.0)

    # Tick formatters — explicit, because parse_math=False makes the default log formatter
    # emit literal "$\mathdefault{10^n}$".
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _human(v)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    if yscale == "log":
        ax.set_yticks(y_ticks)
        ax.yaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: price_fmt(v)))

    # Secondary top axis: same data, relabelled in physical volume units.
    secax = ax.secondary_xaxis(
        "top", functions=(lambda x: x * top_per_terraformer_vol,
                           lambda v: v / top_per_terraformer_vol))
    secax.set_xlabel(x_top_label)
    secax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: top_fmt(v)))
    secax.xaxis.set_minor_formatter(NullFormatter())

    add_market_share_axis(ax, steps)

    # Signature footer (fixed, below the axes — never competes with the in-axes scan below).
    ax.text(0.5, -0.15, SIGNATURE, transform=ax.transAxes, ha="center", va="top",
            fontsize=6.5, color="0.5")

    # Parameter box (what produced this chart) — auto-placed in the emptiest spot, scanning
    # around every tread, riser, dot, and label already drawn. Must run LAST (skill: "Info box
    # buries the data" / "call order") so its occupancy scan sees everything above.
    # mode="off" was tried here but manually repositions the axes via set_position(), which
    # fights our global constrained_layout=True (it broke the left price-axis entirely). Stick
    # with mode="on" — the twin axis's line/ticks are made visible to this scan via the phantom
    # mirror artists added at the end of add_market_share_axis(), above.
    info_box.add_info_box(ax, fig, param_text, mode="on", fontsize=7.5)


def figures():
    """Return (name, build) pairs for all three ladders: methane (global), methanol
    (feedstock-value, unchanged "back pocket"), methanol (destination-product TAM rebuild)."""
    methane = build_ladder(METHANE_MARKETS_GLOBAL, TERRAFORMERS_PER_TCF_CH4, MMBTU_PER_TCF)
    methanol_fs = build_ladder(METHANOL_MARKETS_FEEDSTOCK, TERRAFORMERS_PER_MT_MEOH, 1.0e6)
    methanol_tam = build_ladder(METHANOL_MARKETS_MTX_TAM, TERRAFORMERS_PER_MT_MEOH, 1.0e6)

    # Crowded low-price methane tiers cluster in both x and y: cascade each label's dy upward
    # (anchored to its OWN dot, not a shared column) so boxes stack without crossing leaders.
    methane_offsets = {
        "Industrial process fuel\n(residual, ex-ammonia/LNG)": (10, 20, "left", "bottom"),
        "Ammonia / fertilizer feedstock": (14, 72, "left", "bottom"),
        "Residential / commercial\n(global buildings, 21% share)": (18, 124, "left", "bottom"),
        "Gas-fired electricity\n(global power, 39% share)": (-10, 176, "right", "bottom"),
    }
    methane_params = ("1 Terraformer = 2.4 MMcf CH4/yr\n"
                      "Prices: 2024 basis ($/MMBtu)\n"
                      "Volumes: GLOBAL, non-overlapping (de-double-counted)\n"
                      "IEA/IGU sector shares + Henry Hub as global floor price\n"
                      "Label: price · Mkt = own market size · Σ cumulative\n"
                      "Right axis: Terraform's share of currently-unlocked market\n"
                      "= own production / cumulative ceiling of its current tier\n"
                      "(green <100% · red ≥100%)")

    # Methanol (feedstock) clusters near $340-380: same cascade-from-own-dot treatment.
    methanol_fs_offsets = {
        "MTBE / gasoline octane": (10, 16, "left", "bottom"),
        "Acetic acid": (10, 50, "left", "bottom"),
        "Formaldehyde": (10, 84, "left", "bottom"),
        "Methanol-to-olefins (MTO)": (10, 118, "left", "bottom"),
    }
    methanol_fs_params = ("1 Terraformer = ~87 t methanol/yr\n"
                       "~100 Mt/yr global demand (2024)\n"
                       "y = methanol netback / reference value\n"
                       "FEEDSTOCK-VALUE approach: Terraform sells methanol,\n"
                       "not the converted end-product (see MTX-TAM variant)\n"
                       "Label: price · Mkt = own market size · Σ cumulative\n"
                       "Right axis: Terraform's share of currently-unlocked market\n"
                       "= own production / cumulative ceiling of its current tier\n"
                       "(green <100% · red ≥100%)")

    # Methanol (MTX-TAM): same $340-380 cluster, plus the 223/190/167 gasoline-diesel-jet
    # cluster now needs its own cascade (their Terraformer widths are huge, spreading them out
    # in x, but check for y-collisions on the linear axis and tune if needed).
    methanol_tam_offsets = {
        "MTBE / gasoline octane": (10, 16, "left", "bottom"),
        "Acetic acid": (10, 50, "left", "bottom"),
        "Formaldehyde": (10, 84, "left", "bottom"),
        "MTX aromatics/olefins\n(global olefins TAM)": (10, 118, "left", "bottom"),
        "Bulk DME\n(residual direct-fuel use)": (10, 152, "left", "bottom"),
        "MTG gasoline\n(global gasoline TAM)": (10, 20, "left", "bottom"),
        "MTX diesel\n(global diesel TAM)": (16, 90, "left", "bottom"),
        "MTX jet / Jet-A\n(global jet fuel TAM)": (-22, 160, "right", "bottom"),
    }
    methanol_tam_params = ("1 Terraformer = ~87 t methanol/yr\n"
                       "y = max methanol netback for conversion to stay profitable\n"
                       "MTX tiers priced as DESTINATION-PRODUCT TAM: assumes\n"
                       "Terraform sells the converted end-product (gasoline/\n"
                       "diesel/jet/olefins), not raw methanol — \"Casey's approach\"\n"
                       "Non-MTX tiers still feedstock-value (unchanged)\n"
                       "Conversion ratios: MTG 2.584 (sourced, Motunui); others\n"
                       "2.9 (MTO rule-of-thumb, extended to diesel/jet — ASSUMPTION)\n"
                       "Label: price · Mkt = own market size · Σ cumulative\n"
                       "Right axis: Terraform's share of currently-unlocked market\n"
                       "= own production / cumulative ceiling of its current tier\n"
                       "(green <100% · red ≥100%)")

    def build_methane():
        fig, ax = render.new_figure(figsize=(12, 7))
        draw(ax, fig, methane,
             title="Methane market ladder (GLOBAL) — cumulative Terraformers vs scale price",
             y_label="Scale price of methane  [$/MMBtu]",
             x_top_label="Cumulative CH4 volume served  [Tcf/yr]",
             top_per_terraformer_vol=TERRAFORMER_CH4_MMCF_YR / MMCF_PER_TCF,  # Tcf per Terraformer
             yscale="log",
             price_fmt=lambda p: f"${p:,.0f}" if p >= 10 else f"${p:,.1f}",
             y_ticks=[2, 3, 5, 10, 20, 30],
             top_fmt=lambda v: f"{v:g}",
             label_offsets=methane_offsets,
             param_text=methane_params)
        return fig, OUTPUT_ROOT / "methane_market_ladder.png"

    def build_methanol_feedstock():
        fig, ax = render.new_figure(figsize=(12, 7))
        draw(ax, fig, methanol_fs,
             title="Methanol market ladder (feedstock-value) — cumulative Terraformers vs scale price",
             y_label="Scale price of methanol  [$/tonne]",
             x_top_label="Cumulative methanol volume served  [Mt/yr]",
             top_per_terraformer_vol=TERRAFORMER_MEOH_T_YR / 1.0e6,  # Mt per Terraformer
             yscale="linear",
             price_fmt=lambda p: f"${p:,.0f}",
             y_ticks=None,
             top_fmt=lambda v: f"{v:g}",
             label_offsets=methanol_fs_offsets,
             param_text=methanol_fs_params)
        return fig, OUTPUT_ROOT / "methanol_market_ladder.png"

    def build_methanol_tam():
        fig, ax = render.new_figure(figsize=(12, 7))
        draw(ax, fig, methanol_tam,
             title="Methanol market ladder (destination-product TAM) — cumulative Terraformers vs scale price",
             y_label="Max methanol netback price  [$/tonne]",
             x_top_label="Cumulative methanol-equivalent volume  [Mt/yr]",
             top_per_terraformer_vol=TERRAFORMER_MEOH_T_YR / 1.0e6,  # Mt per Terraformer
             yscale="linear",
             price_fmt=lambda p: f"${p:,.0f}",
             y_ticks=None,
             top_fmt=lambda v: f"{v:g}",
             label_offsets=methanol_tam_offsets,
             param_text=methanol_tam_params)
        return fig, OUTPUT_ROOT / "methanol_market_ladder_mtx_tam.png"

    return [("methane", build_methane),
            ("methanol_feedstock", build_methanol_feedstock),
            ("methanol_mtx_tam", build_methanol_tam)]


if __name__ == "__main__":
    import time
    t0 = time.time()
    plan = figures()
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")

    # Surprising-finding printout (not just left in the plot): quantify how much the two
    # rebuilds moved the cumulative total.
    methane_g = build_ladder(METHANE_MARKETS_GLOBAL, TERRAFORMERS_PER_TCF_CH4, MMBTU_PER_TCF)
    meoh_fs = build_ladder(METHANOL_MARKETS_FEEDSTOCK, TERRAFORMERS_PER_MT_MEOH, 1.0e6)
    meoh_tam = build_ladder(METHANOL_MARKETS_MTX_TAM, TERRAFORMERS_PER_MT_MEOH, 1.0e6)
    print(f"\nMethane, global cumulative total:      {_fmt_dollars(methane_g[-1].cumulative_dollars_per_year)}"
          f"  (was ~$171B/yr under the old US-only scope — ~{methane_g[-1].cumulative_dollars_per_year/171.3e9:.1f}x)")
    print(f"Methanol, feedstock-value total:       {_fmt_dollars(meoh_fs[-1].cumulative_dollars_per_year)}")
    print(f"Methanol, destination-product TAM total: {_fmt_dollars(meoh_tam[-1].cumulative_dollars_per_year)}"
          f"  (~{meoh_tam[-1].cumulative_dollars_per_year/meoh_fs[-1].cumulative_dollars_per_year:.0f}x the feedstock-value total)")
    total_meoh_equiv_mt = meoh_tam[-1].cum_hi / TERRAFORMERS_PER_MT_MEOH
    print(f"Full MTX-TAM build-out implies ~{total_meoh_equiv_mt:,.0f} Mt/yr methanol-equivalent production"
          f" — ~{total_meoh_equiv_mt/100:.0f}x today's entire global methanol market (~100 Mt/yr).")
