"""Plot 1 — Grand Coulee average diurnal profile by season.

Average hourly power (MW) vs hour of day, one line per meteorological season. The seasonal
spread is the proof that the dam's dispatch shape changes with the water year while still
peaking within each day.
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


def draw(ax, fig, gcl) -> None:
    table = derived.diurnal_by_season(gcl)
    hours = table.index.to_numpy()
    series = [
        SeriesSpec(hours, table[s].to_numpy(), label=s, color=cfg.SEASON_COLOR[s],
                   linewidth=2.0)
        for s in cfg.SEASON_ORDER if s in table.columns
    ]
    plotting.draw(
        ax, series,
        xlabel=cfg.axis_label("hour"), ylabel=cfg.axis_label("power_mw"),
        title=f"Grand Coulee diurnal generation profile by season ({cfg.USACE_YEAR})",
    )
    ax.set_xticks(range(0, 24, 3))
    ax.set_xlim(0, 23)

    # Annotate each season's evening peak directly on its curve.
    for s in cfg.SEASON_ORDER:
        if s not in table.columns:
            continue
        col = table[s].dropna()
        if col.empty:
            continue
        h_peak = int(col.idxmax())
        ax.annotate(f"{col.loc[h_peak]:,.0f} MW", xy=(h_peak, col.loc[h_peak]),
                    xytext=(0, 6), textcoords="offset points", ha="center",
                    fontsize=8, color=cfg.SEASON_COLOR[s])

    common.add_box(ax, fig, common.gcl_box_lines())
    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)


def figures(gcl):
    def build():
        fig, ax = render.new_figure()
        draw(ax, fig, gcl)
        return fig, cfg.OUTPUT_DIR / "grand_coulee_diurnal_by_season_2023.png"
    return [("diurnal_by_season", build)]


if __name__ == "__main__":
    gcl = derived.load_dam(cfg.GCL_CSV)
    for name, build in figures(gcl):
        fig, path = build()
        print("wrote", render.save_fig(fig, path))
