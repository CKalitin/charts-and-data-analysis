"""Average diurnal generation profile by season — generic for any USACE dam."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config as cfg
from config import DamConfig
import derived
from charts import common
from viz import plotting, render
from viz.plotting import SeriesSpec


def draw(ax, fig, df, dam: DamConfig) -> None:
    table = derived.diurnal_by_season(df)
    hours = table.index.to_numpy()
    series = [
        SeriesSpec(hours, table[s].to_numpy(), label=s, color=cfg.SEASON_COLOR[s],
                   linewidth=2.0)
        for s in cfg.SEASON_ORDER if s in table.columns
    ]
    plotting.draw(
        ax, series,
        xlabel=cfg.axis_label("hour"), ylabel=cfg.axis_label("power_mw"),
        title=f"{dam.name} diurnal generation profile by season ({dam.year})",
    )
    common.set_hour_ticks(ax)
    ax.set_xlim(0, 23)
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


def figures(df, dam: DamConfig):
    def build():
        fig, ax = render.new_figure()
        draw(ax, fig, df, dam)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        common.add_box(ax, fig, common.dam_box_lines(dam.nameplate_mw, dam.year, extra=[
            "Each curve: average of every hour",
            "in the calendar quarter",
        ]))
        path = dam.output_dir / f"{dam.slug}_diurnal_by_season_{dam.year}.png"
        return fig, path
    return [(f"diurnal_season_{dam.code}", build)]


if __name__ == "__main__":
    import derived as _derived
    for dam in cfg.ALL_DAMS:
        df = _derived.load_dam(dam.csv_path)
        for _, build in figures(df, dam):
            fig, path = build()
            print("wrote", render.save_fig(fig, path))
