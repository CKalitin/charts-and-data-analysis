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


def add_source(ax, text: str, color: str = "0.15") -> None:
    """Source credit inside axes at bottom-left. Call BEFORE add_box so the
    info-box scanner sees this text as occupied and avoids it."""
    ax.text(0.01, 0.02, text, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7.5, color=color)


def add_watermark(ax, loc: str = "bottom_right", color: str = "0.15") -> None:
    """Author credit inside axes. Call BEFORE add_box.

    loc: "bottom_right" (default) or "top_left" (use on scatter plots where
         the legend occupies the lower-right corner).
    """
    if loc == "top_left":
        ax.text(0.01, 0.98, "Christopher Kalitin 2026", transform=ax.transAxes,
                ha="left", va="top", fontsize=7.5, color=color, style="italic")
    else:
        ax.text(0.99, 0.02, "Christopher Kalitin 2026", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7.5, color=color, style="italic")


def add_box(ax, fig, lines, mode: str = "on") -> None:
    """Auto-place an info box. Call AFTER add_source/add_watermark so the scanner
    sees those texts as occupied and won't place the box on top of them."""
    info_box.add_info_box(ax, fig, "\n".join(lines), mode=mode)


def add_fig_footer(fig, axes_list, source_text: str) -> None:
    """For multi-panel figures: place source on bottom-left panel, watermark on bottom-right."""
    if axes_list:
        add_source(axes_list[-2] if len(axes_list) >= 2 else axes_list[-1], source_text)
        add_watermark(axes_list[-1])


def dam_box_lines(nameplate_mw: int, year: int = cfg.USACE_YEAR,
                  extra: list[str] | None = None) -> list[str]:
    """Generic info-box lines for any USACE dam."""
    lines = [
        "Data: USACE NWD",
        f"Year: {year}",
        f"Nameplate: {nameplate_mw:,} MW",
    ]
    return (extra or []) + lines


def gcl_box_lines(extra: list[str] | None = None) -> list[str]:
    """Grand Coulee convenience wrapper around dam_box_lines."""
    return dam_box_lines(cfg.GCL_NAMEPLATE_MW, extra=extra)


def _hour_label(h: int) -> str:
    if h == 0:  return "12 AM"
    if h == 12: return "12 PM"
    if h < 12:  return f"{h} AM"
    return f"{h - 12} PM"


def set_hour_ticks(ax, step: int = 3) -> None:
    """Replace integer hour ticks with formatted time labels (3 AM, 12 PM, etc.)."""
    ticks = list(range(0, 24, step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([_hour_label(h) for h in ticks])
