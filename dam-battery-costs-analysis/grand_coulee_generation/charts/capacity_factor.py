"""Plot 4 — Grand Coulee monthly capacity factor bar chart.

CF = monthly avg power / nameplate (6,809 MW). The annual average hovers around 35%,
but spring and summer months can exceed 50% while winter drawdown months fall below 25%.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import config as cfg
import derived
from charts import common
from viz import render

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BAR_COLOR = "#1f77b4"
ANNUAL_LINE_COLOR = "#d62728"


def draw(ax, fig, gcl) -> None:
    cf = derived.monthly_capacity_factor(gcl, cfg.GCL_NAMEPLATE_MW)
    # Reindex so all 12 months present even if some months have no data.
    cf = cf.reindex(range(1, 13))
    xs = np.arange(1, 13)

    bars = ax.bar(xs, cf.to_numpy() * 100, color=BAR_COLOR, width=0.7, alpha=0.85,
                  label="Monthly CF")
    annual_cf = cf.mean()
    ax.axhline(annual_cf * 100, color=ANNUAL_LINE_COLOR, linestyle="--", linewidth=1.4,
               label=f"Annual avg {annual_cf:.1%}")

    # Value labels above each bar.
    for bar, v in zip(bars, cf.to_numpy()):
        if np.isfinite(v):
            ax.text(bar.get_x() + bar.get_width() / 2, v * 100 + 0.5, f"{v:.0%}",
                    ha="center", va="bottom", fontsize=8)

    ax.set_xticks(xs)
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlabel(cfg.axis_label("month"))
    ax.set_ylabel("Capacity factor (%)")
    ax.set_title(f"Grand Coulee monthly capacity factor — {cfg.USACE_YEAR}")
    ax.set_ylim(0, max(cf.max() * 110, 70))
    ax.legend(loc="upper right")

    common.add_box(ax, fig, common.gcl_box_lines([f"Annual avg CF: {annual_cf:.1%}"]))
    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)


def figures(gcl):
    def build():
        fig, ax = render.new_figure()
        draw(ax, fig, gcl)
        return fig, cfg.OUTPUT_DIR / "grand_coulee_cf_by_month_2023.png"
    return [("capacity_factor", build)]


if __name__ == "__main__":
    gcl = derived.load_dam(cfg.GCL_CSV)
    for name, build in figures(gcl):
        fig, path = build()
        print("wrote", render.save_fig(fig, path))
