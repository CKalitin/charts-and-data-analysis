"""General plotting primitives — the anti-duplication core.

ONE general drawing function (`draw`) plus a few small composable helpers, so chart code
NEVER re-implements styling. Everything draws onto a caller-provided Axes, which keeps it
compatible with both one-off figures and the reused-figure performance path in render.py.

The point of this module: when you want to change how (say) reference-line labels look, or
how text boxes are styled, you change it in ONE function here and every chart in the project
updates. Per-chart styling code is how you end up fixing the same bug in nine files.

Supported out of the box (the cases that actually recur):
  - multiple series, line or scatter, with per-series label / color / marker / style
  - dashed constant reference lines (h or v) with optional inline labels (stoich ratio,
    safety limit, target, breakeven, ...)
  - in-axes text boxes (annotations) and figure-level notes / footnotes
  - value-gradient scatter with colorbar (encode a 3rd dimension — e.g. elapsed time —
    without a 3rd axis)

This module is intentionally domain-agnostic: it takes explicit xlabel/ylabel/colors, not a
project config. Wire your project's variable->label registry in at the CHART layer (the thing
that calls draw()), so labels are still single-sourced but this primitive stays reusable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

# Default styling knobs (override per-call as needed).
SCATTER_MARKER_SIZE = 14
LINE_WIDTH = 1.2
TIME_GRADIENT_CMAP = "viridis"


@dataclass
class SeriesSpec:
    """One plotted series. Line or scatter, fully styled per-series.

    marker defaults to None: a line is a clean line unless you ask for markers. (Set
    marker="o" explicitly for sparse series where each sample should be visible.)
    """
    x: Sequence
    y: Sequence
    label: str | None = None
    kind: str = "line"                # "line" | "scatter"
    color: object | None = None
    marker: str | None = None
    markersize: float = 3.0
    linewidth: float = LINE_WIDTH
    linestyle: str = "-"
    alpha: float = 1.0


@dataclass
class RefLine:
    """A dashed constant-value reference line (e.g. stoichiometric ratio, safety limit, target)."""
    value: float
    axis: str = "h"                   # "h" -> horizontal (y=value); "v" -> vertical (x=value)
    label: str | None = None
    color: object = "gray"
    linestyle: str = "--"
    linewidth: float = 1.0


@dataclass
class TextBox:
    """Free-floating annotation in axes-fraction coordinates (0..1). The default white
    rounded box on 0.8 alpha is the project-wide info-box look; change it in add_textbox()
    once and every box follows."""
    text: str
    loc: tuple[float, float] = (0.02, 0.98)
    ha: str = "left"
    va: str = "top"
    fontsize: float = 9.0


def add_constant_line(ax, ref: RefLine) -> None:
    line_fn = ax.axhline if ref.axis == "h" else ax.axvline
    line_fn(ref.value, color=ref.color, linestyle=ref.linestyle, linewidth=ref.linewidth)
    if ref.label:
        # Label sits at the far end of the line, in blended (axes-fraction, data) coords so it
        # tracks the line regardless of autoscale.
        if ref.axis == "h":
            ax.text(0.99, ref.value, f" {ref.label}", transform=ax.get_yaxis_transform(),
                    ha="right", va="bottom", fontsize=8, color=ref.color)
        else:
            ax.text(ref.value, 0.99, f" {ref.label}", transform=ax.get_xaxis_transform(),
                    ha="left", va="top", fontsize=8, color=ref.color, rotation=90)


def add_textbox(ax, box: TextBox) -> None:
    ax.text(box.loc[0], box.loc[1], box.text, transform=ax.transAxes,
            ha=box.ha, va=box.va, fontsize=box.fontsize,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="0.7"))


def add_note(fig, text: str) -> None:
    """Figure-level footnote (small, bottom-centered). Good for assumptions / data provenance."""
    fig.text(0.5, 0.01, text, ha="center", va="bottom", fontsize=8, color="0.35")


def draw(ax, series: list[SeriesSpec], *, xlabel: str, ylabel: str,
         title: str | None = None, ref_lines: Sequence[RefLine] = (),
         textboxes: Sequence[TextBox] = (), legend: bool = True,
         xscale: str = "linear", yscale: str = "linear",
         scatter_marker_size: float = SCATTER_MARKER_SIZE) -> None:
    """Draw a complete single-axes chart onto `ax`. This is the function chart modules call."""
    for s in series:
        if s.kind == "scatter":
            ax.scatter(s.x, s.y, label=s.label, color=s.color, marker=s.marker or "o",
                       s=scatter_marker_size, alpha=s.alpha)
        else:
            ax.plot(s.x, s.y, label=s.label, color=s.color, marker=s.marker,
                    markersize=s.markersize, linewidth=s.linewidth,
                    linestyle=s.linestyle, alpha=s.alpha)

    for ref in ref_lines:
        add_constant_line(ax, ref)
    for box in textboxes:
        add_textbox(ax, box)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    if xscale != "linear":
        ax.set_xscale(xscale)
    if yscale != "linear":
        ax.set_yscale(yscale)
    if legend and any(s.label for s in series):
        ax.legend(loc="best")


def gradient_scatter(ax, x, y, c, *, cmap: str | None = None, label: str | None = None,
                     marker_size: float = SCATTER_MARKER_SIZE):
    """Scatter colored by `c` (e.g. elapsed seconds, temperature). Returns the mappable so the
    caller can attach a colorbar: `cbar = fig.colorbar(mappable, ax=ax)`."""
    return ax.scatter(x, y, c=c, cmap=cmap or TIME_GRADIENT_CMAP, s=marker_size, label=label)
