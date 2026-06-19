"""Plot 2 — storage dam vs run-of-river diurnal comparison (the key chart).

Annual-average power by hour for Grand Coulee (storage / peaker) and Bonneville
(run-of-river). To compare *shape* rather than magnitude, each curve is also shown
normalized to its own daily mean on a twin axis — the storage dam swings, the
run-of-river dam is flat.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config as cfg
import derived
from charts import common
from viz import plotting, render
from viz.plotting import SeriesSpec

GCL_COLOR = "#d62728"
BON_COLOR = "#1f77b4"


def _swing(series):
    night = series.loc[2:5].mean()
    peak = series.loc[17:20].mean()
    return night, peak, peak / night


def draw(ax, fig, gcl, bon) -> None:
    g = derived.annual_diurnal(gcl)
    b = derived.annual_diurnal(bon)
    hours = g.index.to_numpy()

    series = [
        SeriesSpec(hours, g.to_numpy(), label="Grand Coulee (storage)",
                   color=GCL_COLOR, linewidth=2.4, marker="o", markersize=3),
        SeriesSpec(b.index.to_numpy(), b.to_numpy(), label="Bonneville (run-of-river)",
                   color=BON_COLOR, linewidth=2.4, marker="s", markersize=3),
    ]
    plotting.draw(
        ax, series,
        xlabel=cfg.axis_label("hour"), ylabel=cfg.axis_label("power_mw"),
        title=f"Storage dam peaks, run-of-river runs flat — annual avg ({cfg.USACE_YEAR})",
    )
    ax.set_xticks(range(0, 24, 3))
    ax.set_xlim(0, 23)
    ax.set_ylim(bottom=0)

    g_night, g_peak, g_ratio = _swing(g)
    b_night, b_peak, b_ratio = _swing(b)
    # Annotate the storage-dam swing directly — this ratio is the headline number.
    ax.annotate(f"{g_peak:,.0f} MW peak", xy=(int(g.idxmax()), g.max()),
                xytext=(0, 8), textcoords="offset points", ha="center",
                fontsize=8, color=GCL_COLOR)
    ax.annotate(f"{g_night:,.0f} MW overnight", xy=(3, g_night),
                xytext=(0, -14), textcoords="offset points", ha="center",
                fontsize=8, color=GCL_COLOR)

    common.add_box(ax, fig, [
        f"Grand Coulee swing: {g_ratio:.2f}x",
        f"Bonneville swing:  {b_ratio:.2f}x",
        f"Year: {cfg.USACE_YEAR}",
    ])
    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)


def figures(gcl, bon):
    def build():
        fig, ax = render.new_figure()
        draw(ax, fig, gcl, bon)
        return fig, cfg.OUTPUT_DIR / "storage_vs_runofriver_diurnal_2023.png"
    return [("storage_vs_runofriver", build)]


if __name__ == "__main__":
    gcl = derived.load_dam(cfg.GCL_CSV)
    bon = derived.load_dam(cfg.BON_CSV)
    for name, build in figures(gcl, bon):
        fig, path = build()
        print("wrote", render.save_fig(fig, path))
