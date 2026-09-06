"""Elasticity-derived subscription price against each country's real local price.

tam_model prices every newly-connected customer from an elasticity curve anchored on
%unconnected and GNI/capita -- deliberately NOT on what the local terrestrial market
charges today, because the curve is meant to express willingness to pay for satellite
service rather than to reproduce a $1.60 Indian mobile plan.

That is a real modelling choice with a real consequence, and this chart exists to
make its size visible rather than leaving it in a docstring: it plots the derived
price against the incumbent price for every country that has both. The median country
sits close to the diagonal, but the large unconnected markets -- the ones that
dominate TAM -- sit well above it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tam_model as tm                            # noqa: E402
from affordability import _raw_arpu               # noqa: E402
from regions import REGION_COLORS, REGION_SHORT   # noqa: E402
from viz import render, info_box                  # noqa: E402

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "market"

SOURCE_NOTE = ("Sources: World Bank (GNI/capita, population, internet use); "
               "cable.co.uk and bestbroadbanddeals.co.uk pricing surveys.")

#: Called out by name: the four biggest markets plus the largest divergences in each
#: direction. Everything else would be unreadable at 200 points.
LABEL_ALWAYS = {"India", "China", "United States", "Indonesia", "Nigeria"}
LABEL_EXTREMES = 4

#: Per-label nudges, only for points whose default offset collides with a neighbour.
_OFFSETS = {
    "India": (8, 4, "left", "bottom"),
    "Cambodia": (-8, -8, "right", "top"),
    "Zimbabwe": (-8, 6, "right", "bottom"),
    "Syrian Arab Republic": (-8, -10, "right", "top"),
    "Central African Republic": (-8, 6, "right", "bottom"),
    "Indonesia": (-8, 5, "right", "bottom"),
    "Nigeria": (7, 5, "left", "bottom"),
    "United States": (-10, 8, "right", "bottom"),
    "China": (-9, -9, "right", "top"),
}
_DEFAULT_OFFSET = (6, 6, "left", "bottom")


def _points():
    rows = tm.load_telecom_rows()
    out = []
    for r in rows:
        pop, unc = r["population"], r["unconnected_population_est_coverage_corrected"]
        gni = r["gni_per_capita_ppp_usd"]
        arpu = _raw_arpu(r)
        if not (pop and unc and gni and arpu):
            continue
        pop, unc, gni = float(pop), float(unc), float(gni)
        pct = 100.0 * unc / pop
        derived = tm.elasticity_price_usd_month(pct, gni)
        out.append({"country": r["country"], "region": r["region"], "real": float(arpu),
                    "derived": derived, "ratio": derived / float(arpu), "pct_unconnected": pct})
    return out


def draw(ax, pts):
    for region, color in REGION_COLORS.items():
        sel = [p for p in pts if p["region"] == region]
        if sel:
            ax.scatter([p["real"] for p in sel], [p["derived"] for p in sel], s=22,
                       color=color, alpha=0.85, linewidths=0.3, edgecolors="white",
                       label=REGION_SHORT[region], zorder=3)

    lo = min(min(p["real"] for p in pts), min(p["derived"] for p in pts)) * 0.7
    hi = max(max(p["real"] for p in pts), max(p["derived"] for p in pts)) * 1.4
    diag = np.array([lo, hi])
    ax.plot(diag, diag, color="#111111", lw=1.2, ls="--", zorder=2,
            label="Derived = real local price")
    for mult in (10, 0.1):
        ax.plot(diag, diag * mult, color="#888888", lw=0.9, ls=":", zorder=2)
    # Labelled at the right-hand end of each guide line, unrotated. A rotated label
    # anchored at the left end sat half outside the axes and read as a stray tick.
    ax.annotate("10x local price", xy=(hi / 10 / 1.15, hi / 1.15), xytext=(-4, 0),
                textcoords="offset points", fontsize=7.5, color="#666666",
                ha="right", va="center")
    ax.annotate("0.1x local price", xy=(hi / 1.15, hi * 0.1 / 1.15), xytext=(-4, 0),
                textcoords="offset points", fontsize=7.5, color="#666666",
                ha="right", va="center")

    ranked = sorted(pts, key=lambda p: -p["ratio"])
    named = {p["country"] for p in ranked[:LABEL_EXTREMES]} | {p["country"] for p in ranked[-LABEL_EXTREMES:]}
    named |= LABEL_ALWAYS
    for p in pts:
        if p["country"] not in named:
            continue
        dx, dy, ha, va = _OFFSETS.get(p["country"], _DEFAULT_OFFSET)
        ax.annotate(f"{p['country']} {p['ratio']:.1f}x", xy=(p["real"], p["derived"]),
                    xytext=(dx, dy), textcoords="offset points", fontsize=7,
                    ha=ha, va=va, color="#222222",
                    arrowprops=dict(arrowstyle="-", color="#888888", lw=0.5))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    # Deliberately NOT set_aspect("equal"): with constrained_layout it forces the axes
    # box taller than the figure can hold, clipping the title and the x tick labels.
    # Equal limits already make y=x the corner-to-corner diagonal.
    # Explicit FuncFormatter on both axes: this project sets text.parse_math=False,
    # and matplotlib's default log formatter emits mathtext that then prints literally.
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:g}"))
        axis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xlabel("Real local price today, USD/month (log scale)")
    ax.set_ylabel("Elasticity-derived price, USD/month (log scale)")
    ax.set_title("Elasticity-derived price vs real local price, by country")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.95)


def fig_derived_vs_real_price():
    pts = _points()
    fig, ax = render.new_figure(figsize=(11.5, 9))
    draw(ax, pts)

    ratios = np.array([p["ratio"] for p in pts])
    above = sorted(pts, key=lambda p: -p["ratio"])[:3]
    largest = ", ".join(f"{p['country']} {p['ratio']:.0f}x" for p in above)
    info_box.add_info_box(
        ax, fig,
        f"{len(pts)} countries with both prices.\n"
        f"Median {np.median(ratios):.2f}x local price.\n"
        f"{int((ratios > 3).sum())} above 3x, {int((ratios < 0.5).sum())} below 0.5x.\n"
        f"Largest: {largest}.\n"
        "Price is set by %unconnected and GNI/capita,\n"
        "not anchored to the local market.\n"
        + SOURCE_NOTE,
        mode="on",
    )
    return fig, OUT_ROOT / "derived_vs_real_price_by_country.png"


def figures():
    return [("derived_vs_real_price_by_country", fig_derived_vs_real_price)]


if __name__ == "__main__":
    for name, build in figures():
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(OUT_ROOT.parent.parent)}")
    pts = _points()
    for p in sorted(pts, key=lambda p: -p["ratio"])[:8]:
        print(f"  {p['country'][:24]:<24} {p['pct_unconnected']:5.1f}% unconn  "
              f"real ${p['real']:7.2f} -> derived ${p['derived']:7.2f}  ({p['ratio']:5.1f}x)")
