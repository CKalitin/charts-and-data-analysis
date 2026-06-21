"""Capacity factor charts — generic for any USACE dam.

  figures()                — monthly average CF bar chart
  figures_cf_range_monthly() — monthly min/max range floating bars
  figures_cf_range_daily()   — daily min/max range floating bars (365 bars)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import config as cfg
from config import DamConfig
import derived
from charts import common
from viz import render

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BAR_COLOR        = "#1f77b4"
RANGE_COLOR      = "#1f77b4"
ANNUAL_LINE_COLOR = "#d62728"


def draw(ax, fig, df, dam: DamConfig) -> None:
    cf = derived.monthly_capacity_factor(df, dam.nameplate_mw).reindex(range(1, 13))
    xs = np.arange(1, 13)
    bars = ax.bar(xs, cf.to_numpy() * 100, color=BAR_COLOR, width=0.7, alpha=0.85,
                  label="Monthly CF")
    annual_cf = cf.mean()
    ax.axhline(annual_cf * 100, color=ANNUAL_LINE_COLOR, linestyle="--", linewidth=1.4,
               label=f"Annual avg {annual_cf:.1%}")
    for bar, v in zip(bars, cf.to_numpy()):
        if np.isfinite(v):
            ax.text(bar.get_x() + bar.get_width() / 2, v * 100 + 0.5, f"{v:.0%}",
                    ha="center", va="bottom", fontsize=8)
    ax.set_xticks(xs)
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlabel(cfg.axis_label("month"))
    ax.set_ylabel("Capacity factor (%)")
    ax.set_title(f"{dam.name} monthly capacity factor — {dam.year}")
    ax.set_ylim(0, max(cf.max() * 110, 70))
    ax.legend(loc="upper right")


def figures(df, dam: DamConfig):
    def build():
        fig, ax = render.new_figure()
        draw(ax, fig, df, dam)
        annual_cf = derived.monthly_capacity_factor(df, dam.nameplate_mw).mean()
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        common.add_box(ax, fig, common.dam_box_lines(
            dam.nameplate_mw, dam.year, extra=[f"Annual avg CF: {annual_cf:.1%}"]))
        path = dam.output_dir / f"{dam.slug}_cf_by_month_{dam.year}.png"
        return fig, path
    return [(f"capacity_factor_{dam.code}", build)]


def figures_cf_range_monthly(df, dam: DamConfig):
    """Monthly min/max CF floating bars — bar runs from min to max hourly CF each month."""
    def build():
        cf = df.copy()
        cf["cf_pct"] = cf["power_mw"] / dam.nameplate_mw * 100
        cf["month"]  = pd.to_datetime(cf["date"]).dt.month
        monthly = cf.groupby("month")["cf_pct"].agg(["min", "max"]).reindex(range(1, 13))

        xs     = np.arange(1, 13)
        mins   = monthly["min"].to_numpy()
        maxs   = monthly["max"].to_numpy()
        height = np.where(np.isfinite(maxs - mins), maxs - mins, 0)
        bottom = np.where(np.isfinite(mins), mins, 0)

        fig, ax = render.new_figure(figsize=(13, 5))
        ax.bar(xs, height, bottom=bottom, color=RANGE_COLOR, width=0.7, alpha=0.85)
        ax.set_xticks(xs)
        ax.set_xticklabels(MONTH_LABELS)
        ax.set_xlabel(cfg.axis_label("month"))
        ax.set_ylabel("Capacity factor (%)")
        ax.set_title(f"{dam.name} monthly CF range (min–max hourly) — {dam.year}")
        ax.set_ylim(0, 110)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        common.add_box(ax, fig, common.dam_box_lines(dam.nameplate_mw, dam.year,
            extra=["Bar: min to max hourly CF within each month"]))
        path = dam.output_dir / f"{dam.slug}_cf_range_monthly_{dam.year}.png"
        return fig, path
    return [(f"cf_range_monthly_{dam.code}", build)]


def figures_cf_range_daily(df, dam: DamConfig):
    """Daily min/max CF floating bars — bar runs from min to max hourly CF each day."""
    def build():
        cf = df.copy()
        cf["cf_pct"] = cf["power_mw"] / dam.nameplate_mw * 100
        daily = cf.groupby("date")["cf_pct"].agg(["min", "max"])
        daily = daily.sort_index().reset_index()

        # Map date → month for x-tick labels
        dates  = pd.to_datetime(daily["date"])
        xs     = np.arange(len(daily))
        mins   = daily["min"].to_numpy()
        maxs   = daily["max"].to_numpy()
        height = np.where(np.isfinite(maxs - mins), maxs - mins, 0)
        bottom = np.where(np.isfinite(mins), mins, 0)

        fig, ax = render.new_figure(figsize=(16, 5))
        ax.bar(xs, height, bottom=bottom, color=RANGE_COLOR, width=1.0, alpha=0.80, linewidth=0)

        # Month tick marks at the first day of each month
        month_starts = dates[dates.dt.day == 1]
        tick_pos   = [xs[dates[dates == d].index[0]] for d in month_starts]
        tick_labels = [d.strftime("%b") for d in month_starts]
        ax.set_xticks(tick_pos)
        ax.set_xticklabels(tick_labels)
        ax.set_xlim(-1, len(xs))
        ax.set_xlabel("Day of year")
        ax.set_ylabel("Capacity factor (%)")
        ax.set_title(f"{dam.name} daily CF range (min–max hourly) — {dam.year}")
        ax.set_ylim(0, 110)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        common.add_box(ax, fig, common.dam_box_lines(dam.nameplate_mw, dam.year,
            extra=["Bar: min to max hourly CF within each day"]))
        path = dam.output_dir / f"{dam.slug}_cf_range_daily_{dam.year}.png"
        return fig, path
    return [(f"cf_range_daily_{dam.code}", build)]


if __name__ == "__main__":
    for dam in cfg.ALL_DAMS:
        df = derived.load_dam(dam.csv_path)
        for _, build in [*figures(df, dam),
                         *figures_cf_range_monthly(df, dam),
                         *figures_cf_range_daily(df, dam)]:
            fig, path = build()
            print("wrote", render.save_fig(fig, path))
