"""Plot 5 — Grand Coulee monthly spill fraction.

Spill fraction = volume-weighted Σ(spill_kcfs) / Σ(total_outflow_kcfs) per month.
Spring months show highest spill — this is the water-year constraint: when the reservoir
is full and tributary inflows are high, the dam cannot absorb all the flow through turbines
and must spill, eliminating its ability to reduce output further (the wind-curtailment
argument from 2011 BPA controversy).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import config as cfg
import derived
from charts import common
from viz import render, plotting

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SPILL_COLOR = "#ff7f0e"
SPRING_COLOR = "#2ca02c"


def draw(ax, fig, gcl) -> None:
    sf = derived.monthly_spill_fraction(gcl).reindex(range(1, 13)) * 100  # as %
    xs = np.arange(1, 13)

    bars = ax.bar(xs, sf.to_numpy(), color=SPILL_COLOR, width=0.7, alpha=0.85)

    # Highlight spring months.
    spring_months = [3, 4, 5]
    for m in spring_months:
        bars[m - 1].set_color(SPRING_COLOR)
        bars[m - 1].set_label("Spring (high spill)" if m == 3 else "")

    # Annotate spring constraint.
    peak_month = int(sf.idxmax())
    ax.annotate(
        f"High spill = dam cannot\nreduce output further\n(wind curtailment risk)",
        xy=(peak_month, sf.loc[peak_month]),
        xytext=(peak_month + 1.5, sf.loc[peak_month] * 0.85),
        fontsize=8, ha="left",
        arrowprops=dict(arrowstyle="->", color="0.4", lw=1),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="0.7"),
    )

    ax.set_xticks(xs)
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlabel(cfg.axis_label("month"))
    ax.set_ylabel("Spill fraction (%)")
    ax.set_title(f"Grand Coulee monthly spill fraction — {cfg.USACE_YEAR}")
    ax.set_ylim(bottom=0)

    # Legend for spring colour
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor=SPILL_COLOR, label="Spill fraction"),
        Patch(facecolor=SPRING_COLOR, label="Spring (high spill)"),
    ], loc="upper right")

    max_month = MONTH_LABELS[peak_month - 1]
    common.add_box(ax, fig, [f"Peak spill month: {max_month}", f"Year: {cfg.USACE_YEAR}"])
    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)


def figures(gcl):
    def build():
        fig, ax = render.new_figure()
        draw(ax, fig, gcl)
        return fig, cfg.OUTPUT_DIR / "grand_coulee_spill_fraction_2023.png"
    return [("spill_fraction", build)]


if __name__ == "__main__":
    gcl = derived.load_dam(cfg.GCL_CSV)
    for name, build in figures(gcl):
        fig, path = build()
        print("wrote", render.save_fig(fig, path))
