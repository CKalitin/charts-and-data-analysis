"""Shared chart furniture — single-sourced across every chart in this project.

Rules:
  - Source credit is placed INSIDE the axes (bottom-left, axes-fraction coords).
    Never use fig.text at y≈0 — constrained_layout doesn't reserve space there and
    the text collides with tick labels.
  - Watermark (bottom-right inside axes) appears on every chart.
  - Info box uses auto-placement (mode="on") so it avoids data; call add_box after
    data and legend are drawn.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config as cfg
from viz import info_box, plotting


def add_box(ax, fig, lines, mode: str = "on") -> None:
    """Auto-place an info box from a list of text lines."""
    info_box.add_info_box(ax, fig, "\n".join(lines), mode=mode)


def add_source(ax, text: str) -> None:
    """Source credit inside axes at bottom-left. Never overlaps tick labels."""
    ax.text(0.01, 0.02, text, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7.5, color="0.45")


def add_watermark(ax) -> None:
    """Author credit inside axes at bottom-right."""
    ax.text(0.99, 0.02, "Christopher Kalitin 2026", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7.5, color="0.55", style="italic")


def add_fig_footer(fig, axes_list, source_text: str) -> None:
    """For multi-panel figures: place source on bottom-left panel, watermark on bottom-right."""
    if axes_list:
        add_source(axes_list[-2] if len(axes_list) >= 2 else axes_list[-1], source_text)
        add_watermark(axes_list[-1])


def gcl_box_lines(extra: list[str] | None = None) -> list[str]:
    """Standard Grand Coulee info-box lines."""
    lines = [
        "Data: USACE NWD",
        f"Year: {cfg.USACE_YEAR}",
        f"Nameplate: {cfg.GCL_NAMEPLATE_MW:,} MW",
    ]
    return (extra or []) + lines
