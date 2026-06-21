"""Full-year daily average power time series — generic for any USACE dam."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.dates as mdates
import pandas as pd

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


def figures_with_head(df, dam: DamConfig):
    """Power + head stacked two-panel chart. Requires a head_ft column in df."""
    def build():
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        fig = Figure(figsize=(13, 8))
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)

        ax_pwr, ax_hd = fig.subplots(2, 1, sharex=True)

        daily_pwr  = derived.daily_mean_power(df)
        daily_head = df.set_index("datetime")["head_ft"].resample("D").mean()

        # ── Power panel ───────────────────────────────────────────────────────
        ax_pwr.plot(daily_pwr.index, daily_pwr.to_numpy(),
                    color="#1f77b4", linewidth=1.4, label="Daily avg output")
        ax_pwr.axhline(dam.nameplate_mw, color="#d62728", linewidth=1.0,
                       linestyle="--", label=f"Nameplate {dam.nameplate_mw:,} MW")
        ax_pwr.set_ylabel(cfg.axis_label("power_mw"))
        ax_pwr.set_ylim(bottom=0)
        ax_pwr.set_title(f"{dam.name} — Power & Head  {dam.year}", fontsize=11)
        ax_pwr.legend(fontsize=8, loc="upper right")

        # ── Head panel ────────────────────────────────────────────────────────
        summary = pd.read_csv(cfg.PROJECT_DIR / "data" / "bpa_dams_summary.csv")
        summary_row = summary[summary["dam_code"] == dam.code]
        min_head = float(summary_row["min_head_ft"].iloc[0]) if not summary_row.empty else None

        ax_hd.plot(daily_head.index, daily_head.to_numpy(),
                   color="#2ca02c", linewidth=1.4, label="Daily avg head")
        if min_head is not None:
            ax_hd.axhline(min_head, color="#d62728", linewidth=1.0, linestyle="--",
                          label=f"Min active head {min_head:,.0f} ft")
        ax_hd.set_ylabel("Head (ft)")
        ax_hd.legend(fontsize=8, loc="upper right")

        ax_hd.xaxis.set_major_locator(mdates.MonthLocator())
        ax_hd.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

        cf = daily_pwr.mean() / dam.nameplate_mw
        common.add_source(ax_hd, cfg.SOURCE_USACE)
        common.add_watermark(ax_hd)
        common.add_box(ax_pwr, fig, common.dam_box_lines(
            dam.nameplate_mw, dam.year, extra=[f"Ann. avg CF: {cf:.1%}"]))

        path = dam.output_dir / f"{dam.slug}_annual_timeseries_{dam.year}_with_head.png"
        return fig, path
    return [(f"annual_timeseries_with_head_{dam.code}", build)]


if __name__ == "__main__":
    for dam in cfg.ALL_DAMS:
        df = derived.load_dam(dam.csv_path)
        for _, build in figures(df, dam):
            fig, path = build()
            print("wrote", render.save_fig(fig, path))
