"""Market-landscape charts from data/telecom_market_by_country.csv (Phase 1).

These describe the CURRENT telecom market -- where the unserved population sits, what
people already pay, and how burdensome that is relative to income. They are NOT yet
Starlink-specific: no satellite cost, capacity, or coverage constraint has entered the
model (that's Phases 2-5, see CLAUDE.md). Read these as "the market Starlink would be
entering," not "the market Starlink will actually win."

Run: python charts/market_overview.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from viz import render, info_box
from regions import REGION_COLORS, REGION_SHORT

DATA_CSV = Path(__file__).resolve().parent.parent / "data" / "telecom_market_by_country.csv"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "market"

SOURCE_NOTE = "Source: World Bank; broadband.co.uk; bestbroadbanddeals.co.uk"


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


def _usd_formatter(x, _pos):
    return f"${x:g}"


def load_rows():
    with open(DATA_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(row, key):
    v = row.get(key, "")
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------------------
# Chart 1: total unconnected population by region
# --------------------------------------------------------------------------------------
def fig_unconnected_by_region(rows):
    totals = {}
    for r in rows:
        u = _f(r, "unconnected_population_est_coverage_corrected")
        if u is None:
            continue
        totals[r["region"]] = totals.get(r["region"], 0) + u

    order = sorted(totals, key=lambda k: -totals[k])
    fig, ax = render.new_figure(figsize=(10, 6.5))
    colors = [REGION_COLORS.get(k, "#999999") for k in order]
    labels = [REGION_SHORT.get(k, k) for k in order]
    bars = ax.barh(labels, [totals[k] for k in order], color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Estimated unconnected population")
    ax.set_title("Unconnected population by region")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    for b, k in zip(bars, order):
        ax.annotate(_pop_formatter(totals[k], None), xy=(b.get_width(), b.get_y() + b.get_height() / 2),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8.5)
    total_all = sum(totals.values())
    short_note = f"World\ntotal:\n{_pop_formatter(total_all, None)}\n\nSource:\nWorld Bank"
    info_box.add_info_box(ax, fig, short_note, mode="off", off_side="right", off_frac=0.16, fontsize=8.5)
    return fig, OUT_ROOT / "unconnected_population_by_region.png"


# --------------------------------------------------------------------------------------
# Chart 2: top 25 countries by unconnected population -- the target list
# --------------------------------------------------------------------------------------
def fig_top_unconnected_countries(rows, n=25):
    pts = [(r["country"], r["region"], _f(r, "unconnected_population_est_coverage_corrected")) for r in rows]
    pts = [(c, reg, u) for c, reg, u in pts if u is not None]
    pts.sort(key=lambda p: -p[2])
    top = pts[:n]

    fig, ax = render.new_figure(figsize=(10, 9))
    colors = [REGION_COLORS.get(reg, "#999999") for _, reg, _ in top]
    labels = [c for c, _, _ in top]
    bars = ax.barh(labels, [u for _, _, u in top], color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Estimated unconnected population")
    ax.set_title(f"Top {n} countries by unconnected population")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    for b, (_, _, u) in zip(bars, top):
        ax.annotate(_pop_formatter(u, None), xy=(b.get_width(), b.get_y() + b.get_height() / 2),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8)

    handles = [plt_patch(color) for color in REGION_COLORS.values()]
    ax.legend(handles, [REGION_SHORT[k] for k in REGION_COLORS], loc="lower right", fontsize=7.5)
    info_box.add_info_box(ax, fig, "Coverage-gap corrected. " + SOURCE_NOTE, mode="on")
    return fig, OUT_ROOT / f"top{n}_unconnected_countries.png"


def plt_patch(color):
    from matplotlib.patches import Patch
    return Patch(facecolor=color)


# --------------------------------------------------------------------------------------
# Chart 3: cost landscape -- mobile $/GB vs fixed broadband $/month, sized by unconnected pop
# --------------------------------------------------------------------------------------
def fig_cost_landscape(rows):
    pts = []
    for r in rows:
        gb = _f(r, "mobile_usd_per_gb")
        month = _f(r, "fixed_broadband_usd_per_month")
        u = _f(r, "unconnected_population_est_coverage_corrected") or 0
        if gb is None or month is None or gb <= 0 or month <= 0:
            continue
        pts.append((r["country"], r["region"], gb, month, u))

    fig, ax = render.new_figure(figsize=(11, 7.5))
    for region in REGION_COLORS:
        sub = [p for p in pts if p[1] == region]
        if not sub:
            continue
        sizes = [12 + 40 * (u / 1e8) ** 0.5 for *_, u in sub]
        ax.scatter([p[2] for p in sub], [p[3] for p in sub], s=sizes,
                   color=REGION_COLORS[region], alpha=0.65, label=REGION_SHORT[region],
                   edgecolors="none")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Mobile data cost, $/GB (log scale)")
    ax.set_ylabel("Fixed broadband cost, $/month (log scale)")
    ax.set_title("Current telecom cost landscape (point size ~ unconnected population)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))

    # log-log linear fit (power law in linear space) + R^2
    log_x = np.log10([p[2] for p in pts])
    log_y = np.log10([p[3] for p in pts])
    slope, intercept = np.polyfit(log_x, log_y, 1)
    fit_y = slope * log_x + intercept
    ss_res = np.sum((log_y - fit_y) ** 2)
    ss_tot = np.sum((log_y - log_y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    x_line = np.array([log_x.min(), log_x.max()])
    ax.plot(10 ** x_line, 10 ** (slope * x_line + intercept), color="black",
            linestyle="--", linewidth=1.3, zorder=1, label=f"Trend (R²={r2:.2f})")

    ax.legend(loc="upper left", fontsize=8)

    labels = {"United States", "India", "Nigeria", "Germany", "Brazil", "China",
              "United Kingdom", "Indonesia", "Pakistan", "Ethiopia"}
    for c, reg, gb, month, u in pts:
        if c in labels:
            ax.annotate(c, xy=(gb, month), xytext=(6, 6), textcoords="offset points", fontsize=7.5)

    info_box.add_info_box(ax, fig, f"{len(pts)} countries plotted\n{SOURCE_NOTE}", mode="on")
    return fig, OUT_ROOT / "cost_landscape_mobile_vs_broadband.png"


# --------------------------------------------------------------------------------------
# Chart 4: affordability burden -- top 20 countries by connectivity cost as % of GNI/capita
# --------------------------------------------------------------------------------------
def fig_affordability_burden(rows, n=20):
    pts = [(r["country"], r["region"], _f(r, "connectivity_cost_pct_of_gni")) for r in rows]
    pts = [(c, reg, v) for c, reg, v in pts if v is not None]
    pts.sort(key=lambda p: -p[2])
    top = pts[:n]

    fig, ax = render.new_figure(figsize=(10, 8))
    colors = [REGION_COLORS.get(reg, "#999999") for _, reg, _ in top]
    labels = [c for c, _, _ in top]
    bars = ax.barh(labels, [v for _, _, v in top], color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Fixed broadband annual cost, % of GNI per capita")
    ax.set_title(f"Least affordable fixed broadband, top {n} countries")
    for b, (_, _, v) in zip(bars, top):
        ax.annotate(f"{v:.1f}%", xy=(b.get_width(), b.get_y() + b.get_height() / 2),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8)
    info_box.add_info_box(ax, fig, "Analog of ITU's ICT Price Basket. " + SOURCE_NOTE, mode="on")
    return fig, OUT_ROOT / f"affordability_burden_top{n}.png"



# --------------------------------------------------------------------------------------
# Chart 5: unserved population vs. fixed-broadband (wired) bandwidth cost, $/GB
# --------------------------------------------------------------------------------------
def fig_unconnected_vs_broadband_gb(rows):
    pts = []
    for r in rows:
        u = _f(r, "unconnected_population_est_coverage_corrected")
        gb = _f(r, "fixed_broadband_usd_per_gb_illustrative")
        if u is None or gb is None or u <= 0 or gb <= 0:
            continue
        pts.append((r["country"], r["region"], u, gb))

    fig, ax = render.new_figure(figsize=(11, 7.5))
    for region in REGION_COLORS:
        sub = [p for p in pts if p[1] == region]
        if not sub:
            continue
        ax.scatter([p[2] for p in sub], [p[3] for p in sub], s=16,
                   color=REGION_COLORS[region], alpha=0.75, label=REGION_SHORT[region],
                   edgecolors="none")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Est. unconnected population (log scale)")
    ax.set_ylabel("Fixed (wired) broadband cost, $/GB illustrative (log scale)")
    ax.set_title("Unserved population vs. wired internet bandwidth cost, by country")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.legend(loc="upper left", fontsize=8, ncol=2)

    top = sorted(pts, key=lambda p: -p[2])[:10]
    for c, reg, u, gb in top:
        ax.annotate(c, xy=(u, gb), xytext=(6, 6), textcoords="offset points", fontsize=7.5,
                    arrowprops=dict(arrowstyle="-", color="0.4", lw=0.5, alpha=0.6))

    info_box.add_info_box(
        ax, fig,
        f"{len(pts)} countries. Wired $/GB is illustrative: derived from a flat\n"
        "300 GB/month usage assumption, not real per-GB billing (wired plans\n"
        "are typically unlimited/flat-rate). Compare its SHAPE to mobile\n"
        f"$/GB, not absolute values. {SOURCE_NOTE}",
        mode="on",
    )
    return fig, OUT_ROOT / "unconnected_pop_vs_broadband_gb_cost.png"



# --------------------------------------------------------------------------------------
# Chart 6: connected population vs. wired (fixed broadband) monthly cost
# --------------------------------------------------------------------------------------
def fig_connected_vs_broadband_month(rows):
    pts = []
    for r in rows:
        pop = _f(r, "population")
        unconn = _f(r, "unconnected_population_est_coverage_corrected")
        month = _f(r, "fixed_broadband_usd_per_month")
        if pop is None or unconn is None or month is None or month <= 0:
            continue
        connected = pop - unconn
        if connected <= 0:
            continue
        pts.append((r["country"], r["region"], connected, month))

    fig, ax = render.new_figure(figsize=(11, 7.5))
    for region in REGION_COLORS:
        sub = [p for p in pts if p[1] == region]
        if not sub:
            continue
        ax.scatter([p[2] for p in sub], [p[3] for p in sub], s=16,
                   color=REGION_COLORS[region], alpha=0.75, label=REGION_SHORT[region],
                   edgecolors="none")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Est. connected population (log scale)")
    ax.set_ylabel("Fixed (wired) broadband cost, $/month (log scale)")
    ax.set_title("Already-connected population vs. wired internet cost, by country")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.legend(loc="upper left", fontsize=8, ncol=2)

    top = sorted(pts, key=lambda p: -p[2])[:10]
    for c, reg, connected, month in top:
        ax.annotate(c, xy=(connected, month), xytext=(6, 6), textcoords="offset points", fontsize=7.5,
                    arrowprops=dict(arrowstyle="-", color="0.4", lw=0.5, alpha=0.6))

    info_box.add_info_box(ax, fig, f"{len(pts)} countries. Existing paying market, not unserved. " + SOURCE_NOTE, mode="on")
    return fig, OUT_ROOT / "connected_pop_vs_broadband_month_cost.png"



# --------------------------------------------------------------------------------------
# Chart 7: GDP per capita (PPP) vs. mobile data cost, $/GB
# --------------------------------------------------------------------------------------
def fig_gdp_vs_mobile_cost(rows):
    pts = []
    for r in rows:
        gdp = _f(r, "gdp_per_capita_ppp_usd")
        gb = _f(r, "mobile_usd_per_gb")
        u = _f(r, "unconnected_population_est_coverage_corrected") or 0
        if gdp is None or gb is None or gdp <= 0 or gb <= 0:
            continue
        pts.append((r["country"], r["region"], gdp, gb, u))

    fig, ax = render.new_figure(figsize=(11, 7.5))
    for region in REGION_COLORS:
        sub = [p for p in pts if p[1] == region]
        if not sub:
            continue
        sizes = [12 + 40 * (u / 1e8) ** 0.5 for *_, u in sub]
        ax.scatter([p[2] for p in sub], [p[3] for p in sub], s=sizes,
                   color=REGION_COLORS[region], alpha=0.65, label=REGION_SHORT[region],
                   edgecolors="none")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("GDP per capita, PPP $ (log scale)")
    ax.set_ylabel("Mobile data cost, $/GB (log scale)")
    ax.set_title("Mobile data cost vs. GDP per capita, PPP, by country")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd_formatter))

    log_x = np.log10([p[2] for p in pts])
    log_y = np.log10([p[3] for p in pts])
    slope, intercept = np.polyfit(log_x, log_y, 1)
    fit_y = slope * log_x + intercept
    ss_res = np.sum((log_y - fit_y) ** 2)
    ss_tot = np.sum((log_y - log_y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    x_line = np.array([log_x.min(), log_x.max()])
    ax.plot(10 ** x_line, 10 ** (slope * x_line + intercept), color="black",
            linestyle="--", linewidth=1.3, zorder=1, label=f"Trend (R²={r2:.2f})")

    ax.legend(loc="upper right", fontsize=8)

    labels = {"United States", "India", "Nigeria", "Germany", "Brazil", "China",
              "United Kingdom", "Indonesia", "Pakistan", "Ethiopia"}
    for c, reg, gdp, gb, u in pts:
        if c in labels:
            ax.annotate(c, xy=(gdp, gb), xytext=(6, 6), textcoords="offset points", fontsize=7.5)

    info_box.add_info_box(ax, fig, f"{len(pts)} countries plotted\nPoint size ~ unconnected pop.\n{SOURCE_NOTE}",
                           mode="on")
    return fig, OUT_ROOT / "gdp_per_capita_vs_mobile_cost.png"


def figures(rows):
    return [
        ("unconnected_by_region", lambda: fig_unconnected_by_region(rows)),
        ("top_unconnected_countries", lambda: fig_top_unconnected_countries(rows)),
        ("cost_landscape", lambda: fig_cost_landscape(rows)),
        ("affordability_burden", lambda: fig_affordability_burden(rows)),
        ("unconnected_vs_broadband_gb", lambda: fig_unconnected_vs_broadband_gb(rows)),
        ("connected_vs_broadband_month", lambda: fig_connected_vs_broadband_month(rows)),
        ("gdp_vs_mobile_cost", lambda: fig_gdp_vs_mobile_cost(rows)),
    ]


def main():
    rows = load_rows()
    plan = figures(rows)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")

    big_cheap = []
    for r in rows:
        pop, unconn, month = _f(r, "population"), _f(r, "unconnected_population_est_coverage_corrected"), _f(r, "fixed_broadband_usd_per_month")
        if pop is None or unconn is None or month is None:
            continue
        connected = pop - unconn
        if connected > 3e8 and month > 0:
            big_cheap.append((r["country"], connected, month))
    if big_cheap:
        big_cheap.sort(key=lambda p: -p[1])
        names = ", ".join(f"{c} ({_pop_formatter(conn, None)} connected, ${m:.0f}/mo)" for c, conn, m in big_cheap)
        print(f"NOTE: the largest already-connected markets already have CHEAP wired broadband: "
              f"{names}. These are huge populations but low price headroom -- Starlink would need "
              f"a non-price edge (coverage of rural/unconnected pockets within these countries, "
              f"latency, etc.) to win share here, not a straight price cut.")

    extreme = [(r["country"], _f(r, "connectivity_cost_pct_of_gni")) for r in rows]
    extreme = [(c, v) for c, v in extreme if v is not None and v > 100]
    if extreme:
        extreme.sort(key=lambda p: -p[1])
        names = ", ".join(f"{c} ({v:.0f}% of GNI/capita)" for c, v in extreme)
        print(f"NOTE: {len(extreme)} countries have fixed-broadband annual cost EXCEEDING "
              f"per-capita income: {names}. Broadband is effectively unpurchasable at the "
              f"surveyed retail price in these markets -- a strong signal for where a cheaper "
              f"alternative (e.g. Starlink) has the most theoretical room, if it can undercut "
              f"this, not evidence today's price is what people actually pay.")


if __name__ == "__main__":
    main()
