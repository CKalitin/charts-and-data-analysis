"""Cumulative max Starlink capacity vs. date, with a parallel axis in equivalent
V3 satellites.

x = calendar date (real launch history, 2019-2026). y (left, log) = cumulative max
downlink capacity, Tbps -- a running total of launched capacity, not net of
deorbits (see ../data/starlink_launch_history.md). y (right, log, parallel axis) =
the same quantity divided by V3's real 1.024 Tbps/satellite figure (from the main
project's data/satellite_capacity.csv, 1,024 Gbps) -- "how many V3-class satellites
would be needed to match this much deployed capacity." As of this data pull NO v3
satellite has reached orbit (every v3/Starship launch attempt has failed) -- the
right-hand axis is a normalization unit, not a real V3 satellite count, and the
chart's info box says so explicitly.

Run: python charts/capacity_vs_date.py
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from capacity_timeline_model import V3_GBPS_PER_SAT  # noqa: E402
from viz import render  # noqa: E402

DATA_CSV = Path(__file__).resolve().parent.parent / "data" / "cumulative_capacity_vs_date.csv"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results"

V3_TBPS_PER_SAT = V3_GBPS_PER_SAT / 1000.0  # 1.024 Tbps/satellite

SOURCE_NOTE = "Source: Jonathan McDowell (planet4589.org) launch data, via Wikipedia"
CAVEAT_NOTE = "Gross launched, not net of deorbits. No V3 sat has reached orbit yet."


def _load():
    rows = list(csv.DictReader(open(DATA_CSV)))
    dates = [date.fromisoformat(r["date"]) for r in rows]
    capacity_tbps = [float(r["cum_capacity_gbps"]) / 1000.0 for r in rows]
    return dates, capacity_tbps


def _tbps_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e3, "K"),):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    if x < 1:
        return f"{x:.2g}"
    return f"{x:.0f}"


def _v3_formatter(x, _pos):
    if x <= 0:
        return "0"
    if x < 1:
        return f"{x:.2g}"
    if x >= 1e6:
        return f"{x / 1e6:.1f}M"
    if x >= 1e3:
        return f"{x / 1e3:.1f}K"
    return f"{x:.0f}"


def _add_v3_equivalent_axis(ax):
    """Parallel (secondary) y-axis: equivalent V3 satellites = Tbps / 1.024.

    Same "call after set_yscale, explicit FuncFormatter on major AND minor ticks"
    pattern already established in charts/serviceable_customers_chart.py's
    _add_capacity_secondary_axis() -- see that function's docstring for the full
    reasoning (matplotlib silently resets a secondary axis's formatter back to the
    literal-mathdefault-text default if set_yscale is called after the secondary
    axis already exists)."""
    def to_v3(tbps):
        return tbps / V3_TBPS_PER_SAT

    def from_v3(v3_sats):
        return v3_sats * V3_TBPS_PER_SAT

    secax = ax.secondary_yaxis("right", functions=(to_v3, from_v3))
    secax.set_ylabel("Equivalent V3 satellites (capacity / 1.024 Tbps)")
    secax.yaxis.set_major_formatter(mticker.FuncFormatter(_v3_formatter))
    secax.yaxis.set_minor_formatter(mticker.NullFormatter())
    return secax


def _draw(ax, dates, capacity_tbps, *, log_scale: bool):
    ax.plot(dates, capacity_tbps, color="#2166ac", linewidth=2, zorder=3)
    ax.fill_between(dates, capacity_tbps, 1e-3, color="#2166ac", alpha=0.12, zorder=1)

    if log_scale:
        ax.set_yscale("log")
        ax.set_ylim(1.0, max(capacity_tbps) * 1.6)
    else:
        ax.set_ylim(0, max(capacity_tbps) * 1.1)

    _add_v3_equivalent_axis(ax)  # AFTER set_yscale -- see its docstring

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(date(2019, 1, 1), date(2026, 12, 31))

    if log_scale:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_tbps_formatter))
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    else:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative max downlink capacity (Tbps)")
    ax.text(0.015, 0.97, f"{CAVEAT_NOTE}\n{SOURCE_NOTE}", transform=ax.transAxes,
             fontsize=7.5, va="top", ha="left", color="0.35",
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", alpha=0.85))


def fig_capacity_vs_date_log():
    dates, capacity_tbps = _load()
    fig, ax = render.new_figure()
    _draw(ax, dates, capacity_tbps, log_scale=True)
    ax.set_title("Cumulative max downlink capacity (Tbps) vs. date")
    return fig, "capacity_vs_date_log.png"


def fig_capacity_vs_date_linear():
    dates, capacity_tbps = _load()
    fig, ax = render.new_figure()
    _draw(ax, dates, capacity_tbps, log_scale=False)
    ax.set_title("Cumulative max downlink capacity (Tbps) vs. date")
    return fig, "capacity_vs_date_linear.png"


def figures():
    return [fig_capacity_vs_date_log, fig_capacity_vs_date_linear]


def main():
    for fn in figures():
        fig, filename = fn()
        path = render.save_fig(fig, OUT_ROOT / filename)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
