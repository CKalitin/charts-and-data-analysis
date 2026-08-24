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

import capacity_density_model as cdm

# Estimated current max capacity, expressed as an equivalent V3-satellite count (this
# chart family's x-axis unit) rather than a raw satellite count. The real ~10,900-
# satellite fleet is NOT V3-class hardware -- as of the sourcing in
# starlink_shells.md, zero V3 (Starship-launched) satellites are operational yet, so
# plotting the raw ~10,900 figure against a "Total satellites (V3)" axis would
# overstate today's real capacity by more than 10x. Instead: split the real fleet
# into its actual generations (4,408 Gen1 v1.0/v1.5 + ~6,492 Gen2 v2-Mini-class,
# starlink_shells.md's constellation-wide total), apply each generation's own real
# per-satellite downlink (satellite_capacity.csv: 20 / 96 Gbps respectively; V3's
# 1,024 Gbps has zero satellites in orbit to multiply by), sum to a total capacity in
# Gbps, then re-express that capacity as the count of V3 satellites that would
# deliver it -- directly comparable to this chart family's real V3-equivalent axis.
_REAL_GEN1_SATS = 4408
_REAL_GEN2_SATS = 10_900 - _REAL_GEN1_SATS
_GEN1_GBPS_PER_SAT = 20.0
_GEN2_GBPS_PER_SAT = 96.0
_V3_GBPS_PER_SAT = cdm.V3_SCENARIO.downlink_gbps_per_beam * cdm.V3_SCENARIO.beams_per_satellite
_CURRENT_CAPACITY_GBPS = _REAL_GEN1_SATS * _GEN1_GBPS_PER_SAT + _REAL_GEN2_SATS * _GEN2_GBPS_PER_SAT
ESTIMATED_CURRENT_CAPACITY_SATS = _CURRENT_CAPACITY_GBPS / _V3_GBPS_PER_SAT  # ~695

SHELL_RATIO_NOTE = "Real Gen1 shells: 53.0/53.2/70.0/97.6deg"
SOURCE_NOTE = "Source: WorldPop; FCC satellite filings; X-Lab/Penn State"


def _pop_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    return f"{x:.0f}"


def _add_fleet_reference_lines(ax):
    ax.axvline(ESTIMATED_CURRENT_CAPACITY_SATS, color="0.5", linestyle=":", linewidth=1.0, zorder=1)
    ax.annotate("Estimated current capacity", xy=(ESTIMATED_CURRENT_CAPACITY_SATS, 1),
                xycoords=("data", "axes fraction"), xytext=(4, -4), textcoords="offset points",
                fontsize=7.5, color="0.4", ha="left", va="top", rotation=90)


def _draw_curve(ax, sat_counts, served, color, label, linestyle="-"):
    ax.plot(sat_counts, served, color=color, linewidth=2, linestyle=linestyle, label=label, zorder=3)
    ceiling = served[-1]
    ax.axhline(ceiling, color=color, linestyle="--", linewidth=0.9, alpha=0.6, zorder=2)


def _tbps_formatter(x, _pos):
    if x <= 0:
        return "0"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= div:
            return f"{x / div:.1f}{suf}"
    if x < 1:
        return f"{x:.2g}"
    return f"{x:.0f}"


def _add_capacity_secondary_axis(ax, scenario: cdm.CapacityScenario = cdm.V3_SCENARIO):
    """Secondary TOP x-axis: cumulative max downlink capacity (Tbps) implied by the
    same satellite count on the bottom axis -- a straight linear rescaling of the
    SAME data (N * scenario's real total downlink Gbps/satellite / 1000), not an
    independent quantity. Uses the scenario's real total (downlink_gbps_per_beam x
    beams_per_satellite), which for V3_SCENARIO is pinned to the sourced 1,024 Gbps
    figure regardless of that scenario's beam-count placeholder (see
    ASSUMPTIONS.md #12) -- this axis is accurate even though the density-cap
    numbers elsewhere in these charts carry that caveat. matplotlib's
    secondary_xaxis inverts the given function to place ticks correctly regardless
    of whether the bottom axis is log- or linear-scaled, so this works unmodified
    on both chart families in this module.

    Explicit FuncFormatter on both major AND minor ticks -- a log-scaled secondary
    axis (inherited automatically here since the bottom axis is log on 5 of the 8
    charts using this helper) defaults to matplotlib's LogNorm-style formatter,
    which renders literal '$\\mathdefault{10^{2}}$' text instead of a plain number.
    Same bug class as _format_log_axes() below (caught there first, on the y-axis);
    catching it here too so it can't recur on this new axis.

    CALL THIS AFTER ax.set_xscale()/set_yscale(), not before -- confirmed by direct
    repro (2026-08-14): calling ax.set_xscale("log") AFTER this function has already
    set the secondary axis's formatter SILENTLY RESETS it back to the broken default
    (LogFormatterSciNotation), because changing the parent's scale re-syncs the
    secondary axis's own scale/formatter. Setting the scale first, THEN calling this,
    avoids the reset entirely -- verified with a minimal reproduction outside this
    codebase, not just observed once. Every log chart in this module follows that
    order; the linear charts don't call set_xscale at all, so order doesn't matter
    there."""
    gbps_per_sat = scenario.downlink_gbps_per_beam * scenario.beams_per_satellite

    def to_tbps(n):
        return n * gbps_per_sat / 1000.0

    def from_tbps(tbps):
        return tbps * 1000.0 / gbps_per_sat

    secax = ax.secondary_xaxis("top", functions=(to_tbps, from_tbps))
    secax.set_xlabel("Cumulative max capacity (Tbps)")
    secax.xaxis.set_major_formatter(mticker.FuncFormatter(_tbps_formatter))
    secax.xaxis.set_minor_formatter(mticker.NullFormatter())
    return secax


def _format_log_axes(ax):
    """Apply the plain (non-scientific) tick formatter to BOTH major and minor
    ticks. A log-scale y-axis spanning less than ~2 decades (e.g. the US-only chart)
    auto-enables minor tick labels that bypass a major-only formatter, rendering
    literal '$\\mathdefault{6\\times10^{6}}$' text -- caught on this exact chart, fixed
    here once so it can't recur on any future narrow-range log chart in this file."""
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pop_formatter))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
