"""Shared plotting helpers so every chart in this project looks consistent.

Kept separate from ``solar_battery_core`` (which stays plotting-free) and from
the individual analysis scripts, so the house style -- watermark, parameter
box, output location -- lives in exactly one place.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.offsetbox import AnchoredText

WATERMARK_TEXT = "Christopher Kalitin 2026"

# All figures land here, created on demand.
OUTPUT_DIR = Path(__file__).with_name("output")


def add_watermark(ax: Axes, text: str = WATERMARK_TEXT) -> None:
    """Faint attribution near the top of the plot, out of the way of data."""
    ax.text(
        0.5,
        0.97,
        text,
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=13,
        color="black",
        alpha=0.30,
        zorder=5,
    )


def add_param_box_below(fig: plt.Figure, lines: Iterable[str], bottom_frac: float = 0.17) -> None:
    """Place the parameter box in the figure margin below all axes.

    Reserves ``bottom_frac`` of the figure height for the box by tightening
    the layout first, then pushing the subplots up.  Always outside the data
    area regardless of what the chart looks like.
    """
    fig.tight_layout(rect=[0, bottom_frac, 1, 1])
    fig.text(
        0.01,
        0.005,
        "\n".join(lines),
        transform=fig.transFigure,
        fontsize=9,
        family="monospace",
        va="bottom",
        bbox=dict(
            boxstyle="round,pad=0.4",
            facecolor="white",
            alpha=0.78,
            edgecolor="0.4",
        ),
    )


def add_param_box(ax: Axes, lines: Iterable[str], loc: str = "lower left") -> AnchoredText:
    """Draw a translucent box listing the run's parameters.

    ``loc`` takes the usual matplotlib location strings (e.g. ``"lower left"``,
    ``"upper right"``).  The default sits in the corner that is typically free
    of the colorbar and contour labels.
    """
    box = AnchoredText(
        "\n".join(lines),
        loc=loc,
        prop=dict(size=9, family="monospace"),
        frameon=True,
        borderpad=0.6,
    )
    box.patch.set_boxstyle("round,pad=0.4")
    box.patch.set_facecolor("white")
    box.patch.set_alpha(0.78)
    box.patch.set_edgecolor("0.4")
    box.set_zorder(6)
    ax.add_artist(box)
    return box


def save_figure(fig: plt.Figure, filename: str, dpi: int = 150, subdir: str = "") -> Path:
    """Save ``fig`` into output/<subdir>/ and return the path."""
    target = OUTPUT_DIR / subdir if subdir else OUTPUT_DIR
    target.mkdir(parents=True, exist_ok=True)
    path = target / filename
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path
