"""Shared chart furniture: marker registry, axis formatting, watermark, source line.
Every chart family imports from here so a style fix lands everywhere at once."""

from __future__ import annotations

import matplotlib.ticker as mticker
import numpy as np

import config as cfg

C = cfg.COLORS

# One marker style per price-series kind. Keys are produced by `series_key()`.
MARKERS = {
    "quoted": dict(marker="D", s=46, facecolor=C["quoted"], edgecolor="k", linewidth=0.5,
                   label="US, secondary-source quote (1943, 1950)"),
    "all_forms_fit": dict(marker="s", s=40, facecolor=C["all_forms_fit"], edgecolor="k",
                          linewidth=0.5, label="US Tariff Commission, bulk + dosage forms (1945-48)"),
    "all_forms_excluded": dict(marker="s", s=34, facecolor="none", edgecolor=C["all_forms_excluded"],
                               linewidth=1.0,
                               label="US Tariff Commission, bulk + dosage forms (1952-64, not fitted)"),
    "us_bulk": dict(marker="o", s=34, facecolor=C["us_bulk"], edgecolor="k", linewidth=0.5,
                    label="US Tariff Commission, bulk sales (1962-84)"),
    "world": dict(marker="^", s=48, facecolor=C["world"], edgecolor="k", linewidth=0.5,
                  label="World bulk price: trade data, China exports & quotes (1985-2024)"),
}
SERIES_ORDER = ("quoted", "all_forms_fit", "all_forms_excluded", "us_bulk", "world")


def series_key(row) -> str:
    if row.region == "World":
        return "world"
    if row.basis == "quoted":
        return "quoted"
    if row.basis == "all_forms":
        return "all_forms_fit" if row.in_fit else "all_forms_excluded"
    return "us_bulk"


def dollar_fmt(v, _=None) -> str:
    if v >= 1:
        return f"${v:,.0f}"
    return f"${v:.2g}"


def count_fmt(v, _=None) -> str:
    for scale, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if v >= scale:
            return f"{v / scale:g}{suffix}"
    return f"{v:g}"


def log_axes(ax, xfmt=count_fmt, yfmt=dollar_fmt) -> None:
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_major_locator(mticker.LogLocator(base=10, numticks=15))
    ax.yaxis.set_major_locator(mticker.LogLocator(base=10, numticks=15))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(xfmt))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(yfmt))
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.grid(True, which="major", ls="--", alpha=0.4)
    ax.grid(True, which="minor", ls=":", alpha=0.15)


def tonnes_top_axis(ax) -> None:
    """Secondary x-axis in tonnes of potassium penicillin G for a BU x-axis."""
    sec = ax.secondary_xaxis("top", functions=(lambda b: b / cfg.BU_PER_TONNE,
                                               lambda t: t * cfg.BU_PER_TONNE))
    sec.set_xlabel("Cumulative production [tonnes, potassium penicillin G equivalent]")
    sec.xaxis.set_major_formatter(mticker.FuncFormatter(count_fmt))
    sec.xaxis.set_minor_formatter(mticker.NullFormatter())


def per_kg_right_axis(ax) -> None:
    """Secondary y-axis in $/kg of K-salt for a $/BU y-axis."""
    sec = ax.secondary_yaxis("right", functions=(lambda p: p * cfg.BU_PER_KG_K_SALT,
                                                 lambda k: k / cfg.BU_PER_KG_K_SALT))
    sec.set_ylabel(f"Real price [{cfg.CPI_BASIS_YEAR} USD per kg]")
    sec.yaxis.set_major_formatter(mticker.FuncFormatter(dollar_fmt))
    sec.yaxis.set_minor_formatter(mticker.NullFormatter())


def scatter_points(ax, pts, xcol: str, keys=SERIES_ORDER) -> None:
    kinds = np.array([series_key(r) for r in pts.itertuples()])
    for k in keys:
        sel = pts[kinds == k]
        if len(sel):
            ax.scatter(sel[xcol], sel.real, zorder=4, **MARKERS[k])


def label_years(ax, pts, xcol: str, years=cfg.LABEL_YEARS, offsets=None) -> None:
    offsets = offsets or {}
    done = set()
    for r in pts.itertuples():
        if r.year not in years or r.year in done or (r.basis == "all_forms" and not r.in_fit
                                                     and r.year >= 1962):
            continue
        done.add(r.year)
        dx, dy, ha, va = offsets.get(r.year, (6, 6, "left", "bottom"))
        ax.annotate(str(r.year), xy=(getattr(r, xcol), r.real), xytext=(dx, dy),
                    textcoords="offset points", fontsize=7.5, color="0.25", ha=ha, va=va)


def add_watermark(ax) -> None:
    ax.text(0.99, 0.01, cfg.WATERMARK, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.5, color="0.35", style="italic", zorder=20)


def add_source(fig, text: str) -> None:
    fig.text(0.01, 0.005, text, ha="left", va="bottom", fontsize=6.8, color="0.35", wrap=True)


# World price observations are heterogeneous; one marker per kind so the reader can weigh them.
WORLD_KIND_STYLES = {
    "trade price": dict(marker="^", color="#d62728", label="Trade price (ISID, Zhang & Bjerke, BusinessToday)"),
    "market value / volume": dict(marker="v", color="#8c564b", label="Market value / volume (Elander 2003)"),
    "China export unit value": dict(marker="s", color="#1f77b4", label="China export unit value (CCCMHPIE)"),
    "China domestic quote": dict(marker="o", color="#ff7f0e", label="China domestic quote (industry reports)"),
    "producer avg selling price (ex-VAT)": dict(marker="D", color="#2ca02c",
                                                label="Producer avg selling price, ex-VAT (United Labs)"),
    "China market quote (Wind)": dict(marker="P", color="#9467bd", label="China market quote, Wind (April)"),
}
