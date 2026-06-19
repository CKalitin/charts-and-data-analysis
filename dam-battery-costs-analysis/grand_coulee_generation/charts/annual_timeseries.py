"""Plot 3 — Full-year daily average power time series for Grand Coulee.

Shows reservoir dispatch decisions over the year: spring runoff, summer peak demand,
autumn drawdown. The nameplate line gives context for how far below rated the dam runs.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config as cfg
import derived
from charts import common
from viz import plotting, render
from viz.plotting import RefLine, SeriesSpec


def draw(ax, fig, gcl) -> None:
    daily = derived.daily_mean_power(gcl)

    series = [SeriesSpec(daily.index, daily.to_numpy(),
                         label="Daily avg output", color="#1f77b4", linewidth=1.4)]
    plotting.draw(
        ax, series,
        xlabel="", ylabel=cfg.axis_label("power_mw"),
        title=f"Grand Coulee daily average output — {cfg.USACE_YEAR}",
        ref_lines=[RefLine(cfg.GCL_NAMEPLATE_MW, label=f"Nameplate {cfg.GCL_NAMEPLATE_MW:,} MW",
                           color="#d62728")],
    )
    ax.set_ylim(bottom=0)

    # Annotate seasonal periods as shaded spans + labels.
    _annot = [
        ("2023-04-01", "2023-06-30", "#2ca02c", "Spring runoff\n(possible spill)"),
        ("2023-07-01", "2023-08-31", "#d62728", "Summer peak\ndemand"),
        ("2023-10-01", "2023-12-31", "#8c564b", "Reservoir\ndrawdown"),
    ]
    import pandas as pd
    for start, end, color, label in _annot:
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end), alpha=0.10, color=color)
        mid = pd.Timestamp(start) + (pd.Timestamp(end) - pd.Timestamp(start)) / 2
        ax.text(mid, ax.get_ylim()[1] * 0.96, label, ha="center", va="top",
                fontsize=7.5, color=color,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7, edgecolor="none"))

    cf = daily.mean() / cfg.GCL_NAMEPLATE_MW
    common.add_box(ax, fig, common.gcl_box_lines([f"Ann. avg CF: {cf:.1%}"]))
    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)


def figures(gcl):
    def build():
        fig, ax = render.new_figure(figsize=(13, 5))
        draw(ax, fig, gcl)
        return fig, cfg.OUTPUT_DIR / "grand_coulee_annual_timeseries_2023.png"
    return [("annual_timeseries", build)]


if __name__ == "__main__":
    gcl = derived.load_dam(cfg.GCL_CSV)
    for name, build in figures(gcl):
        fig, path = build()
        print("wrote", render.save_fig(fig, path))
