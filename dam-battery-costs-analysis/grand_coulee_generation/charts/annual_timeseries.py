"""Full-year daily average power time series — generic for any USACE dam."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config as cfg
from config import DamConfig
import derived
from charts import common
from viz import plotting, render
from viz.plotting import RefLine, SeriesSpec

def draw(ax, fig, df, dam: DamConfig) -> None:
    daily = derived.daily_mean_power(df)
    series = [SeriesSpec(daily.index, daily.to_numpy(),
                         label="Daily avg output", color="#1f77b4", linewidth=1.4)]
    plotting.draw(
        ax, series,
        xlabel="", ylabel=cfg.axis_label("power_mw"),
        title=f"{dam.name} daily average output — {dam.year}",
        ref_lines=[RefLine(dam.nameplate_mw,
                           label=f"Nameplate {dam.nameplate_mw:,} MW",
                           color="#d62728")],
    )
    ax.set_ylim(bottom=0)


def figures(df, dam: DamConfig):
    def build():
        fig, ax = render.new_figure(figsize=(13, 5))
        draw(ax, fig, df, dam)
        cf = derived.daily_mean_power(df).mean() / dam.nameplate_mw
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        common.add_box(ax, fig, common.dam_box_lines(
            dam.nameplate_mw, dam.year, extra=[f"Ann. avg CF: {cf:.1%}"]))
        path = dam.output_dir / f"{dam.slug}_annual_timeseries_{dam.year}.png"
        return fig, path
    return [(f"annual_timeseries_{dam.code}", build)]


if __name__ == "__main__":
    for dam in cfg.ALL_DAMS:
        df = derived.load_dam(dam.csv_path)
        for _, build in figures(df, dam):
            fig, path = build()
            print("wrote", render.save_fig(fig, path))
