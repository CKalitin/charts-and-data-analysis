"""Peak hourly capacity-factor charts — generic for any USACE dam.

Two chart families per dam, both saved to {dam.output_dir}/peak_cf/:

  Monthly (12 charts): each day's peak hourly CF for that month.
  Annual summary (1 chart): highest hourly CF reached in each calendar month.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

import config as cfg
from config import DamConfig
import derived
from charts import common
from viz import render

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BAR_COLOR = "#1f77b4"
REF_LINE_COLOR = "#d62728"


def _daily_peak_cf(df: pd.DataFrame, nameplate_mw: int) -> pd.Series:
    """MultiIndex (month, date) Series of each day's peak hourly CF (0–100 %)."""
    return df.groupby(["month", "date"])["power_mw"].max() / nameplate_mw * 100


def figures_monthly(df, dam: DamConfig):
    """12 monthly bar charts: peak hourly CF per day, shared Y scale."""
    out_dir = dam.output_dir / "peak_cf"
    daily_cf = _daily_peak_cf(df, dam.nameplate_mw)
    global_max = daily_cf.max()
    ylim = (0, min(global_max * 1.12, 105))
    annual_avg = df["power_mw"].mean() / dam.nameplate_mw * 100

    plans = []
    for m in range(1, 13):
        if m not in daily_cf.index.get_level_values(0):
            continue
        month_series = daily_cf.loc[m]

        def build(ms=month_series, month=m):
            days = pd.to_datetime(ms.index).day
            vals = ms.to_numpy()

            fig = Figure(figsize=(10, 5), dpi=render.DPI)
            FigureCanvasAgg(fig)
            fig.set_constrained_layout(True)
            ax = fig.add_subplot(1, 1, 1)

            ax.bar(days, vals, color=BAR_COLOR, width=0.75, alpha=0.85)

            peak_idx = int(np.argmax(vals))
            ax.annotate(f"{vals[peak_idx]:.1f}%",
                        xy=(days[peak_idx], vals[peak_idx]),
                        xytext=(0, 5), textcoords="offset points",
                        ha="center", fontsize=8, fontweight="bold", color="0.2")

            ax.axhline(annual_avg, color=REF_LINE_COLOR, linestyle="--", linewidth=1.2,
                       label=f"Annual avg CF {annual_avg:.1f}%")
            ax.axhline(100, color="0.55", linestyle=":", linewidth=0.8,
                       label="Nameplate (100%)")

            ax.set_xlim(0.0, len(days) + 0.5)
            ax.set_ylim(*ylim)
            ax.set_xticks(days)
            ax.set_xticklabels([str(d) for d in days], fontsize=8)
            ax.set_xlabel(f"Day of {MONTH_NAMES[month - 1]}")
            ax.set_ylabel("Peak hourly CF (%)")
            ax.set_title(f"{dam.name} — peak hourly CF: "
                         f"{MONTH_NAMES[month - 1]} {dam.year}")
            ax.legend(loc="upper left", fontsize=8)

            common.add_source(ax, cfg.SOURCE_USACE)
            common.add_watermark(ax)
            common.add_box(ax, fig, common.dam_box_lines(
                dam.nameplate_mw, dam.year,
                extra=[f"Month peak: {vals.max():.1f}%"]))

            path = out_dir / f"{dam.slug}_peak_cf_{month:02d}_{MONTH_NAMES[month - 1].lower()}_{dam.year}.png"
            return fig, path

        plans.append((f"peak_cf_monthly_{dam.code}_{m:02d}", build))
    return plans


def figures_annual_summary(df, dam: DamConfig):
    """Single bar chart: highest CF reached per calendar month."""
    out_dir = dam.output_dir / "peak_cf"

    def build():
        daily_cf = _daily_peak_cf(df, dam.nameplate_mw)
        monthly_peak = daily_cf.groupby(level=0).max().reindex(range(1, 13))

        fig = Figure(figsize=(10, 5), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)

        xs = np.arange(1, 13)
        bars = ax.bar(xs, monthly_peak.to_numpy(), color=BAR_COLOR, width=0.75, alpha=0.85)
        for bar, v in zip(bars, monthly_peak):
            if np.isfinite(v):
                ax.text(bar.get_x() + bar.get_width() / 2, v + 0.4,
                        f"{v:.1f}%", ha="center", va="bottom", fontsize=8)

        annual_avg = df["power_mw"].mean() / dam.nameplate_mw * 100
        ax.axhline(annual_avg, color=REF_LINE_COLOR, linestyle="--", linewidth=1.2,
                   label=f"Annual avg CF {annual_avg:.1f}%")
        ax.axhline(100, color="0.55", linestyle=":", linewidth=0.8,
                   label="Nameplate (100%)")

        ax.set_xticks(xs)
        ax.set_xticklabels(MONTH_NAMES, fontsize=9)
        ax.set_xlabel("Month")
        ax.set_ylabel("Highest hourly CF in month (%)")
        ax.set_title(f"{dam.name} — highest instantaneous CF by month, {dam.year}")
        ax.set_ylim(0, monthly_peak.max() * 1.15)
        ax.legend(loc="upper right", fontsize=8)

        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        common.add_box(ax, fig, common.dam_box_lines(dam.nameplate_mw, dam.year))

        path = out_dir / f"{dam.slug}_peak_cf_by_month_{dam.year}.png"
        return fig, path

    return [(f"peak_cf_summary_{dam.code}", build)]


if __name__ == "__main__":
    for dam in cfg.ALL_DAMS:
        df = derived.load_dam(dam.csv_path)
        (dam.output_dir / "peak_cf").mkdir(parents=True, exist_ok=True)
        for _, build in [*figures_monthly(df, dam), *figures_annual_summary(df, dam)]:
            fig, path = build()
            print("wrote", render.save_fig(fig, path))
