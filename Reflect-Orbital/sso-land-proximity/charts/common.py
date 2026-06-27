"""Shared chart furniture — single-sourced across every chart in this project."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config as cfg
from viz import info_box


def add_source(ax, text: str, color: str = "0.30") -> None:
    """Source credit inside axes, top-right. Call BEFORE add_box."""
    ax.text(0.99, 0.98, text, transform=ax.transAxes,
            ha="right", va="top", fontsize=7.5, color=color, zorder=20)


def add_watermark(ax, color: str = "0.30") -> None:
    """Author credit inside axes, bottom-right. Call BEFORE add_box."""
    ax.text(0.99, 0.02, cfg.WATERMARK, transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7.5, color=color, style="italic", zorder=20)


def add_box(ax, fig, lines, mode: str = "on", zorder: float = 30) -> None:
    """Info box pinned to the bottom-left corner of the axes.

    mode is accepted for API compatibility but placement is always lower-left.
    zorder is bumped high so the track / other data stays underneath.
    """
    text = ax.text(
        0.01, 0.02, "\n".join(lines),
        transform=ax.transAxes, ha="left", va="bottom",
        fontsize=9.0, zorder=zorder,
        bbox=info_box.BOX_KW,
    )
    return text
