"""Shared chart furniture — single-sourced across every chart in this project."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from viz import info_box


def add_source(ax, text: str, color: str = "0.15") -> None:
    """Source credit inside axes, bottom-left. Call BEFORE add_box."""
    ax.text(0.01, 0.02, text, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7.5, color=color)


def add_watermark(ax, color: str = "0.15") -> None:
    """Author credit inside axes, bottom-right. Call BEFORE add_box."""
    ax.text(0.99, 0.02, "Christopher Kalitin 2026", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7.5, color=color, style="italic")


def add_box(ax, fig, lines, mode: str = "on") -> None:
    """Auto-place an info box. Call AFTER add_source / add_watermark."""
    info_box.add_info_box(ax, fig, "\n".join(lines), mode=mode)
