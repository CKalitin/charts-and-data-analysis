"""Dispatch time-series charts for the chosen (hydro, battery) design point.

Three families:
  figures_annual_daily : one chart, daily hydro generation + battery charge/discharge (GWh/day)
  figures_quarter_days : 4 charts, first day of each quarter at 5-min resolution
  figures_months       : 12 charts, each month at 5-min resolution

The sub-daily / monthly charts are 2-panel: load + hydro on top (GW scale), battery power and
state-of-charge below (so the battery — which barely cycles at the min-cost design — is visible).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

import config as cfg
from charts import common
from viz import render

_GWh = 1e3


def _new_stack(figsize=(13, 8)):
    fig = Figure(figsize=figsize, dpi=render.DPI)
    FigureCanvasAgg(fig)
    fig.set_constrained_layout(True)
    ax_top, ax_bot = fig.subplots(2, 1, sharex=True, height_ratios=[2, 1])
    return fig, ax_top, ax_bot


def _point_lines(point):
    return [
        f"Design: {point['hydro_mw']/1e3:,.1f} GW hydro",
        f"        {point['battery_mwh']/1e3:,.1f} GWh battery",
        f"Battery: {cfg.BATTERY_ROUNDTRIP_EFF:.0%} round-trip",
        f"LCOE ${point['lcoe']:,.1f}/MWh",
    ]


def _draw_power_panels(fig, ax_top, ax_bot, sub, point, title, xfmt, xloc):
    t = sub["datetime"].to_numpy()

    # ── Top: load + hydro generation ────────────────────────────────────────────
    ax_top.plot(t, sub["load_mw"] / 1e3, color=cfg.COLOR_LOAD, lw=1.4, label="Load")
    ax_top.plot(t, sub["hydro_mw"] / 1e3, color=cfg.COLOR_HYDRO, lw=1.2,
                label="Hydro generation")
    ax_top.axhline(point["hydro_mw"] / 1e3, color=cfg.COLOR_HYDRO, lw=0.8, ls="--",
                   alpha=0.6, label=f"Hydro cap {point['hydro_mw']/1e3:,.1f} GW")
    ax_top.set_ylabel("Power (GW)")
    ax_top.set_ylim(bottom=0)
    ax_top.set_title(title, fontsize=11)
    ax_top.legend(fontsize=8, loc="upper right", ncol=2)

    # ── Bottom: battery power (discharge + / charge −) and SOC ───────────────────
    ax_bot.fill_between(t, 0, sub["discharge_mw"], color=cfg.COLOR_DISCHARGE,
                        alpha=0.85, label="Battery discharge")
    ax_bot.fill_between(t, 0, -sub["charge_mw"], color=cfg.COLOR_CHARGE,
                        alpha=0.85, label="Battery charge")
    ax_bot.axhline(0, color="0.5", lw=0.6)
    ax_bot.set_ylabel("Battery power (MW)")
    ax_bot.set_xlabel("")

    ax_soc = ax_bot.twinx()
    ax_soc.plot(t, sub["soc_mwh"] / _GWh, color=cfg.COLOR_SOC, lw=1.1, alpha=0.9,
                label="State of charge")
    ax_soc.set_ylabel("SOC (GWh)")
    ax_soc.set_ylim(bottom=0)

    l1, lab1 = ax_bot.get_legend_handles_labels()
    l2, lab2 = ax_soc.get_legend_handles_labels()
    ax_bot.legend(l1 + l2, lab1 + lab2, fontsize=8, loc="upper right", ncol=3)

    ax_bot.xaxis.set_major_locator(xloc)
    ax_bot.xaxis.set_major_formatter(xfmt)

    common.add_source(ax_top, cfg.SOURCE_BPA)
    common.add_watermark(ax_bot)
    common.add_box(ax_top, fig, _point_lines(point))


def figures_annual_daily(disp: pd.DataFrame, point: dict) -> list:
    """One chart: daily hydro generation (left) + battery charge/discharge throughput (right)."""
    out = cfg.OUTPUT_DIR / "timeseries"

    def build():
        g = disp.set_index("datetime")
        daily = pd.DataFrame({
            "hydro":     g["hydro_mw"].resample("D").sum()     * cfg.DT_H / _GWh,
            "charge":    g["charge_mw"].resample("D").sum()    * cfg.DT_H / _GWh,
            "discharge": g["discharge_mw"].resample("D").sum() * cfg.DT_H / _GWh,
        })

        fig, ax = render.new_figure(figsize=(14, 6))
        x = daily.index.to_numpy()
        ax.plot(x, daily["hydro"], color=cfg.COLOR_HYDRO, lw=1.3,
                label="Hydro generation")
        ax.set_ylabel("Hydro generation (GWh/day)")
        ax.set_ylim(bottom=0)
        ax.set_title(f"BPA hydro + battery dispatch — daily energy, {cfg.YEAR}", fontsize=11)

        ax_b = ax.twinx()
        ax_b.plot(x, daily["discharge"], color=cfg.COLOR_DISCHARGE, lw=1.1,
                  label="Battery discharged")
        ax_b.plot(x, daily["charge"], color=cfg.COLOR_CHARGE, lw=1.1,
                  label="Battery charged")
        ax_b.set_ylabel("Battery throughput (GWh/day)")
        ax_b.set_ylim(bottom=0)

        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

        l1, lab1 = ax.get_legend_handles_labels()
        l2, lab2 = ax_b.get_legend_handles_labels()
        ax.legend(l1 + l2, lab1 + lab2, fontsize=8, loc="upper right")

        common.add_source(ax, cfg.SOURCE_BPA)
        common.add_watermark(ax)
        common.add_box(ax, fig, _point_lines(point))
        return fig, out / f"bpa_dispatch_daily_{cfg.YEAR}.png"

    return [("annual_daily", build)]


def figures_quarter_days(disp: pd.DataFrame, point: dict) -> list:
    out = cfg.OUTPUT_DIR / "timeseries" / "quarter_days"
    g = disp.set_index("datetime")
    plans = []
    for date_str, label in cfg.QUARTER_DAYS:
        day = g.loc[date_str].reset_index()

        def build(sub=day, label=label, date_str=date_str):
            fig, ax_top, ax_bot = _new_stack()
            xloc = mdates.HourLocator(interval=3)
            xfmt = mdates.DateFormatter("%H:%M")
            _draw_power_panels(fig, ax_top, ax_bot, sub, point,
                               f"BPA dispatch — {label} {cfg.YEAR} (5-min)", xfmt, xloc)
            slug = date_str.replace("-", "")
            return fig, out / f"bpa_dispatch_day_{slug}.png"

        plans.append((f"quarter_{date_str}", build))
    return plans


def figures_months(disp: pd.DataFrame, point: dict) -> list:
    out = cfg.OUTPUT_DIR / "timeseries" / "months"
    g = disp.set_index("datetime")
    plans = []
    for m in range(1, 13):
        sub = g[g.index.month == m].reset_index()
        if sub.empty:
            continue

        def build(sub=sub, m=m):
            fig, ax_top, ax_bot = _new_stack(figsize=(14, 8))
            xloc = mdates.DayLocator(interval=3)
            xfmt = mdates.DateFormatter("%b %d")
            _draw_power_panels(fig, ax_top, ax_bot, sub, point,
                               f"BPA dispatch — {cfg.MONTH_NAMES[m-1]} {cfg.YEAR} (5-min)",
                               xfmt, xloc)
            return fig, out / f"bpa_dispatch_month_{m:02d}_{cfg.MONTH_NAMES[m-1].lower()}.png"

        plans.append((f"month_{m:02d}", build))
    return plans


if __name__ == "__main__":
    import time
    from data_load import load_bpa_load
    from model.simulate import run_sweep, min_cost_full_point
    from model.dispatch import dispatch

    t0 = time.time()
    df = load_bpa_load()
    res = run_sweep(df["load_mw"].to_numpy())
    pt = min_cost_full_point(res)
    disp = dispatch(df, pt["hydro_mw"], pt["battery_mwh"])
    plan = [*figures_annual_daily(disp, pt),
            *figures_quarter_days(disp, pt),
            *figures_months(disp, pt)]
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\n{len(plan)} charts in {time.time()-t0:.1f}s")
