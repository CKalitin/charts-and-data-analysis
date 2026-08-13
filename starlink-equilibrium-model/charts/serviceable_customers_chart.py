"""Shared helpers for the serviceable-customers chart family
(charts/serviceable_customers_per_satellite_chart.py, charts/latitude_saturation_heatmap.py)
-- formatting, fleet reference lines, and the "draw one curve + its dashed ceiling
line" primitive used by every chart in that family. Produces no charts of its own.

History: this file originally held the FIXED (single-satellite) density-cap model's
own charts -- the areal beam-footprint density cap held constant regardless of
constellation size N, capacity_density_model.py's original documented assumption,
contrasted against the per-satellite (range-extended) model as a dashed reference
curve. User request (2026-08-13): dropped that comparison from every chart -- a
cap that never rises past what ONE satellite's beam footprint can deliver,
regardless of how many satellites actually cover a spot, doesn't reflect how a
real many-satellite constellation serves an area, so charting it as a live
"vs." comparison read as misleading rather than illuminating. The per-satellite
(range-extended, real Starlink FOV geometry) model in
charts/serviceable_customers_per_satellite_chart.py is now the only charted model;
this file just keeps the formatting/reference-line helpers both remaining chart
files share, so they don't drift out of sync with each other.
"""
from __future__ import annotations

import matplotlib.ticker as mticker

# Known real constellation sizes, for reference lines (see starlink_shells.md / CLAUDE.md).
GEN1_SATS = 4408
CURRENT_FLEET_SATS = 10_900

SHELL_RATIO_NOTE = "Real Gen1 shells: 53.0/53.2/70.0/97.6deg"
SOURCE_NOTE = "Source: WorldPop pop. density + capacity_density_model.py + orbital_geometry.py"


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


def _add_fleet_reference_lines(ax):
    # Vertical stagger (-4, -70) so the two labels never overlap even when both lines
    # sit within a few pixels of each other -- happens on a wide linear axis where
    # 4,408 and 10,900 are both essentially "at the left edge" (e.g. a multi-million
    # sat_counts range); a log axis spreads them out enough that this never showed up.
    offsets = [(4, -4), (4, -70)]
    for (n, label), xytext in zip([(GEN1_SATS, "Gen1 (4,408)"), (CURRENT_FLEET_SATS, "Current fleet (~10,900)")],
                                   offsets):
        ax.axvline(n, color="0.5", linestyle=":", linewidth=1.0, zorder=1)
        ax.annotate(label, xy=(n, 1), xycoords=("data", "axes fraction"), xytext=xytext,
                    textcoords="offset points", fontsize=7.5, color="0.4", ha="left", va="top", rotation=90)


def _draw_curve(ax, sat_counts, served, color, label, linestyle="-"):
    ax.plot(sat_counts, served, color=color, linewidth=2, linestyle=linestyle, label=label, zorder=3)
    ceiling = served[-1]
    ax.axhline(ceiling, color=color, linestyle="--", linewidth=0.9, alpha=0.6, zorder=2)


def _format_log_axes(ax):
    """Apply the plain (non-scientific) tick formatter to BOTH major and minor
    ticks. A log-scale y-axis spanning less than ~2 decades (e.g. the US-only chart)
    auto-enables minor tick labels that bypass a major-only formatter, rendering
    literal '$\\mathdefault{6\\times10^{6}}$' text -- caught on this exact chart, fixed
    here once so it can't recur on any future narrow-range log chart in this file."""
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
