"""Hourly generation profile for specific (dam, day) pairs.

CONFIGURE: edit DAY_PROFILE_DAYS and DAY_PROFILE_MODE in config.py.

  DAY_PROFILE_DAYS : list of ("dam_code", "YYYY-MM-DD") — mix dams freely.
  DAY_PROFILE_MODE : "overlay"    → all entries on one chart
                     "individual" → one chart per entry
                     "both"       → both

Outputs → outputs/<dam>/day_profiles/

Run:  python charts/day_profile.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.cm as mcm
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

import config as cfg
import derived
from charts import common
from viz import render, plotting
from viz.plotting import RefLine, SeriesSpec


def _resolve_entries(dfs: dict) -> list[tuple]:
    """Resolve config DAY_PROFILE_DAYS → list of (dam, df, date), skipping unknowns."""
    dam_by_code = {d.code: d for d in cfg.ALL_DAMS}
    entries = []
    for dam_code, date in cfg.DAY_PROFILE_DAYS:
        dam = dam_by_code.get(dam_code)
        if dam is None:
            print(f"  WARNING: unknown dam code {dam_code!r} in DAY_PROFILE_DAYS")
            continue
        df = dfs.get(dam_code)
        if df is None or df.empty:
            print(f"  WARNING: no data loaded for {dam_code!r}")
            continue
        entries.append((dam, df, date))
    return entries


def _day_data(df: pd.DataFrame, day: str) -> pd.DataFrame:
    return df[df["date"] == day].sort_values("hour")


def _tab_color(i: int, n: int) -> tuple:
    if n <= 10:
        return mcm.tab10(i / 10)
    return mcm.plasma(i / max(n - 1, 1))


def _base_fig(title: str):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    fig = Figure(figsize=(13, 5), dpi=render.DPI)
    FigureCanvasAgg(fig)
    fig.set_constrained_layout(True)
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title(title, fontsize=11)
    return fig, ax


def _draw_power(day_df: pd.DataFrame, day: str, dam):
    hours   = day_df["hour"].to_numpy()
    power   = day_df["power_mw"].to_numpy()
    peak_cf = power.max() / dam.nameplate_mw * 100
    avg_cf  = power.mean() / dam.nameplate_mw * 100

    fig, ax = _base_fig(f"{dam.name} — power output: {day}")
    plotting.draw(
        ax,
        [SeriesSpec(hours, power, label="Power output", color="#1f77b4",
                    linewidth=2.2, marker="o", markersize=4)],
        xlabel="Hour of day (Pacific)",
        ylabel=cfg.axis_label("power_mw"),
        title="",
        ref_lines=[RefLine(dam.nameplate_mw,
                           label=f"Nameplate {dam.nameplate_mw:,} MW",
                           color="#d62728")],
    )
    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(bottom=0)
    common.set_hour_ticks(ax)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.legend(loc="upper left", fontsize=8)

    peak_h = int(hours[np.argmax(power)])
    ax.annotate(f"Peak\n{power.max():,.0f} MW\n({peak_cf:.1f}% CF)",
                xy=(peak_h, power.max()),
                xytext=(0, 10), textcoords="offset points",
                ha="center", fontsize=8, color="#d62728")

    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)
    common.add_box(ax, fig, [
        f"Date: {day}",
        f"Peak CF: {peak_cf:.1f}%",
        f"Avg CF:  {avg_cf:.1f}%",
        f"Nameplate: {dam.nameplate_mw:,} MW",
    ])
    return fig


def _load_min_head_lookup() -> dict[str, float]:
    """Load min_head_ft per dam_code from bpa_dams_summary.csv."""
    summary = cfg.DATA_DIR / "bpa_dams_summary.csv"
    if not summary.exists():
        return {}
    df = pd.read_csv(summary)
    return dict(zip(df["dam_code"], df["min_head_ft"]))


def _draw_head(day_df: pd.DataFrame, day: str, dam, min_head: float | None = None):
    hours = day_df["hour"].to_numpy()
    head  = day_df["head_ft"].to_numpy()

    fig, ax = _base_fig(f"{dam.name} — hydraulic head: {day}")
    ax.plot(hours, head, color="#2ca02c", linewidth=2.2,
            marker="s", markersize=4, label="Head (ft)")
    if min_head is not None and np.isfinite(min_head):
        ax.axhline(min_head, color="#d62728", linestyle="--", linewidth=1.4,
                   label=f"Min active head {min_head:,.1f} ft")
    h_min = np.nanmin(head)
    h_max = np.nanmax(head)
    base  = min_head if (min_head is not None and np.isfinite(min_head)) else h_min
    pad   = max((h_max - base) * 0.15, 0.5)
    ax.set_ylim(base - pad, h_max + pad)
    ax.set_xlim(-0.5, 23.5)
    ax.set_ylabel("Head (ft)")
    ax.set_xlabel("Hour of day (Pacific)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.1f}"))
    ax.legend(loc="upper left", fontsize=8)
    common.set_hour_ticks(ax)
    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)
    return fig


def _draw_outflow(day_df: pd.DataFrame, day: str, dam):
    hours    = day_df["hour"].to_numpy()
    gen_flow = day_df["gen_flow_kcfs"].to_numpy()
    spill    = day_df["spill_kcfs"].to_numpy()
    total    = day_df["total_outflow_kcfs"].to_numpy()

    fig, ax = _base_fig(f"{dam.name} — outflow: {day}")
    ax.plot(hours, total,    color="#1f77b4", linewidth=2.2, marker="o", markersize=4,
            label="Total outflow")
    ax.plot(hours, gen_flow, color="#2ca02c", linewidth=1.8, marker="s", markersize=3,
            linestyle="--", label="Generation flow")
    ax.plot(hours, spill,    color="#d62728", linewidth=1.8, marker="^", markersize=3,
            linestyle=":",  label="Spill")
    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Flow (kcfs)")
    ax.set_xlabel("Hour of day (Pacific)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.legend(loc="upper left", fontsize=8)
    common.set_hour_ticks(ax)
    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)
    return fig


def _draw_combined(day_df: pd.DataFrame, day: str, dam, min_head: float | None = None):
    """Two-panel figure: power (top) + head (bottom), shared x-axis."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    hours = day_df["hour"].to_numpy()
    power = day_df["power_mw"].to_numpy()
    head  = day_df["head_ft"].to_numpy()
    peak_cf = power.max() / dam.nameplate_mw * 100
    avg_cf  = power.mean() / dam.nameplate_mw * 100

    fig = Figure(figsize=(13, 8), dpi=render.DPI)
    FigureCanvasAgg(fig)
    fig.set_constrained_layout(True)
    fig.suptitle(f"{dam.name} — power & hydraulic head: {day}", fontsize=12)

    ax_pow = fig.add_subplot(2, 1, 1)
    ax_hd  = fig.add_subplot(2, 1, 2, sharex=ax_pow)

    plotting.draw(
        ax_pow,
        [SeriesSpec(hours, power, label="Power output", color="#1f77b4",
                    linewidth=2.2, marker="o", markersize=4)],
        xlabel="", ylabel=cfg.axis_label("power_mw"), title="",
        ref_lines=[RefLine(dam.nameplate_mw,
                           label=f"Nameplate {dam.nameplate_mw:,} MW",
                           color="#d62728")],
    )
    ax_pow.set_xlim(-0.5, 23.5)
    ax_pow.set_ylim(bottom=0)
    ax_pow.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax_pow.tick_params(labelbottom=False)
    ax_pow.legend(loc="upper left", fontsize=8)
    peak_h = int(hours[np.argmax(power)])
    ax_pow.annotate(f"Peak\n{power.max():,.0f} MW\n({peak_cf:.1f}% CF)",
                    xy=(peak_h, power.max()), xytext=(0, 10),
                    textcoords="offset points", ha="center", fontsize=8, color="#d62728")
    common.add_box(ax_pow, fig, [
        f"Date: {day}",
        f"Peak CF: {peak_cf:.1f}%",
        f"Avg CF:  {avg_cf:.1f}%",
        f"Nameplate: {dam.nameplate_mw:,} MW",
    ])

    ax_hd.plot(hours, head, color="#2ca02c", linewidth=2.2,
               marker="s", markersize=4, label="Head (ft)")
    if min_head is not None and np.isfinite(min_head):
        ax_hd.axhline(min_head, color="#d62728", linestyle="--", linewidth=1.4,
                      label=f"Min active head {min_head:,.1f} ft")
    h_min_c = np.nanmin(head)
    h_max_c = np.nanmax(head)
    base_c  = min_head if (min_head is not None and np.isfinite(min_head)) else h_min_c
    pad_c   = max((h_max_c - base_c) * 0.15, 0.5)
    ax_hd.set_ylim(base_c - pad_c, h_max_c + pad_c)
    ax_hd.set_xlim(-0.5, 23.5)
    ax_hd.set_ylabel("Head (ft)")
    ax_hd.set_xlabel("Hour of day (Pacific)")
    ax_hd.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.1f}"))
    ax_hd.legend(loc="upper left", fontsize=8)
    common.set_hour_ticks(ax_hd)
    common.add_source(ax_hd, cfg.SOURCE_USACE)
    common.add_watermark(ax_hd)
    return fig


def figures_individual(entries: list[tuple]):
    """Three charts per (dam, date): combined (power+head), power only, head only."""
    min_head_lookup = _load_min_head_lookup()
    plans = []
    for dam, df, date in entries:
        out_dir  = dam.output_dir / "day_profiles"
        min_head = min_head_lookup.get(dam.code)
        def build_combined(d=date, dam=dam, df=df, out=out_dir, mh=min_head):
            day_df = _day_data(df, d)
            if day_df.empty:
                print(f"  WARNING: no data for {dam.code} {d}")
                return None, None
            return _draw_combined(day_df, d, dam, min_head=mh), out / f"{dam.slug}_{d}.png"
        def build_power(d=date, dam=dam, df=df, out=out_dir):
            day_df = _day_data(df, d)
            if day_df.empty:
                return None, None
            return _draw_power(day_df, d, dam), out / f"{dam.slug}_{d}_power.png"
        def build_head(d=date, dam=dam, df=df, out=out_dir, mh=min_head):
            day_df = _day_data(df, d)
            if day_df.empty:
                return None, None
            return _draw_head(day_df, d, dam, min_head=mh), out / f"{dam.slug}_{d}_head.png"
        plans.append((f"day_profile_{dam.code}_{date}",       build_combined))
        plans.append((f"day_profile_{dam.code}_{date}_power", build_power))
        plans.append((f"day_profile_{dam.code}_{date}_head",  build_head))
    return plans


_MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _month_df(df: pd.DataFrame, month: int) -> pd.DataFrame:
    """All rows for a given calendar month, sorted by datetime."""
    return df[pd.to_datetime(df["date"]).dt.month == month].sort_values("datetime").reset_index(drop=True)


def _month_hour_ticks(ax, month_df: pd.DataFrame):
    """Place one x-tick per day, labelled 1, 2, …, N."""
    dates = pd.to_datetime(month_df["date"])
    # index of the first row for each calendar day
    day_starts = month_df.index[~dates.duplicated(keep="first")]
    day_nums   = dates.iloc[day_starts].dt.day.tolist()
    ax.set_xticks(day_starts)
    ax.set_xticklabels([str(d) for d in day_nums], fontsize=7)
    ax.set_xlabel("Day of month")


def _draw_month_power(month_df: pd.DataFrame, month: int, year: int, dam):
    label = f"{_MONTH_LABELS[month - 1]} {year}"
    hours = month_df.index.to_numpy()
    power = month_df["power_mw"].to_numpy()
    peak_cf = power.max() / dam.nameplate_mw * 100
    avg_cf  = power.mean() / dam.nameplate_mw * 100

    fig, ax = _base_fig(f"{dam.name} — power output: {label}")
    ax.plot(hours, power, color="#1f77b4", linewidth=1.2, label="Power output")
    ax.axhline(dam.nameplate_mw, color="#d62728", linestyle="--", linewidth=1.2,
               label=f"Nameplate {dam.nameplate_mw:,} MW")
    ax.set_ylim(bottom=0)
    ax.set_xlim(0, len(hours) - 1)
    ax.set_ylabel(cfg.axis_label("power_mw"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.legend(loc="upper left", fontsize=8)
    _month_hour_ticks(ax, month_df)
    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)
    common.add_box(ax, fig, [
        f"Month: {label}",
        f"Peak CF: {peak_cf:.1f}%",
        f"Avg CF:  {avg_cf:.1f}%",
        f"Nameplate: {dam.nameplate_mw:,} MW",
    ])
    return fig


def _draw_month_head(month_df: pd.DataFrame, month: int, year: int, dam,
                     min_head: float | None = None):
    label = f"{_MONTH_LABELS[month - 1]} {year}"
    hours = month_df.index.to_numpy()
    head  = month_df["head_ft"].to_numpy()

    fig, ax = _base_fig(f"{dam.name} — hydraulic head: {label}")
    ax.plot(hours, head, color="#2ca02c", linewidth=1.2, label="Head (ft)")
    if min_head is not None:
        ax.axhline(min_head, color="#d62728", linestyle="--", linewidth=1.2,
                   label=f"Min active head {min_head:,.1f} ft")
    h_min = np.nanmin(head)
    h_max = np.nanmax(head)
    base  = min_head if (min_head is not None and np.isfinite(min_head)) else h_min
    pad   = max((h_max - base) * 0.15, 0.5)
    lo    = base - pad
    ax.set_ylim(lo, h_max + pad)
    ax.set_xlim(0, len(hours) - 1)
    ax.set_ylabel("Head (ft)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.1f}"))
    ax.legend(loc="upper left", fontsize=8)
    _month_hour_ticks(ax, month_df)
    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)
    return fig


def _draw_month_combined(month_df: pd.DataFrame, month: int, year: int, dam,
                         min_head: float | None = None):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    label   = f"{_MONTH_LABELS[month - 1]} {year}"
    hours   = month_df.index.to_numpy()
    power   = month_df["power_mw"].to_numpy()
    head    = month_df["head_ft"].to_numpy()
    peak_cf = power.max() / dam.nameplate_mw * 100
    avg_cf  = power.mean() / dam.nameplate_mw * 100

    fig = Figure(figsize=(16, 8), dpi=render.DPI)
    FigureCanvasAgg(fig)
    fig.set_constrained_layout(True)
    fig.suptitle(f"{dam.name} — power & hydraulic head: {label}", fontsize=12)

    ax_pow = fig.add_subplot(2, 1, 1)
    ax_hd  = fig.add_subplot(2, 1, 2, sharex=ax_pow)

    ax_pow.plot(hours, power, color="#1f77b4", linewidth=1.2, label="Power output")
    ax_pow.axhline(dam.nameplate_mw, color="#d62728", linestyle="--", linewidth=1.2,
                   label=f"Nameplate {dam.nameplate_mw:,} MW")
    ax_pow.set_ylim(bottom=0)
    ax_pow.set_xlim(0, len(hours) - 1)
    ax_pow.set_ylabel(cfg.axis_label("power_mw"))
    ax_pow.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax_pow.tick_params(labelbottom=False)
    ax_pow.legend(loc="upper left", fontsize=8)

    ax_hd.plot(hours, head, color="#2ca02c", linewidth=1.2, label="Head (ft)")
    if min_head is not None and np.isfinite(min_head):
        ax_hd.axhline(min_head, color="#d62728", linestyle="--", linewidth=1.2,
                      label=f"Min active head {min_head:,.1f} ft")
    h_min = np.nanmin(head)
    h_max = np.nanmax(head)
    base  = min_head if (min_head is not None and np.isfinite(min_head)) else h_min
    pad   = max((h_max - base) * 0.15, 0.5)
    ax_hd.set_ylim(base - pad, h_max + pad)
    ax_hd.set_xlim(0, len(hours) - 1)
    ax_hd.set_ylabel("Head (ft)")
    ax_hd.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.1f}"))
    ax_hd.legend(loc="upper left", fontsize=8)
    _month_hour_ticks(ax_hd, month_df)
    common.add_source(ax_hd, cfg.SOURCE_USACE)
    common.add_watermark(ax_hd)
    common.add_box(ax_pow, fig, [
        f"Month: {label}",
        f"Peak CF: {peak_cf:.1f}%",
        f"Avg CF:  {avg_cf:.1f}%",
        f"Nameplate: {dam.nameplate_mw:,} MW",
    ])
    return fig


def figures_month_profiles(dfs: dict):
    """Three charts per (dam × month): combined, power, head over the full month.

    X-axis = sequential hour index across the month; ticks = day of month.
    Output: outputs/bpa_dams/<dam>/month_profiles/
    """
    dam_by_code  = {d.code: d for d in cfg.ALL_DAMS}
    min_head_lkp = _load_min_head_lookup()
    plans = []

    for code in cfg.DAY_PROFILE_MONTHLY_DAMS:
        dam = dam_by_code.get(code)
        df  = dfs.get(code)
        if dam is None or df is None or df.empty:
            continue
        out_dir  = dam.output_dir / "month_profiles"
        min_head = min_head_lkp.get(code)

        for month in range(1, 13):
            slug = f"{dam.slug}_{cfg.USACE_YEAR}-{month:02d}"
            def build_combined(m=month, dam=dam, df=df, out=out_dir, mh=min_head):
                mdf = _month_df(df, m)
                if mdf.empty:
                    return None, None
                return (_draw_month_combined(mdf, m, cfg.USACE_YEAR, dam, min_head=mh),
                        out / f"{dam.slug}_{cfg.USACE_YEAR}-{m:02d}.png")
            def build_power(m=month, dam=dam, df=df, out=out_dir):
                mdf = _month_df(df, m)
                if mdf.empty:
                    return None, None
                return (_draw_month_power(mdf, m, cfg.USACE_YEAR, dam),
                        out / f"{dam.slug}_{cfg.USACE_YEAR}-{m:02d}_power.png")
            def build_head(m=month, dam=dam, df=df, out=out_dir, mh=min_head):
                mdf = _month_df(df, m)
                if mdf.empty:
                    return None, None
                return (_draw_month_head(mdf, m, cfg.USACE_YEAR, dam, min_head=mh),
                        out / f"{dam.slug}_{cfg.USACE_YEAR}-{m:02d}_head.png")

            plans.append((f"month_profile_{code}_{month:02d}",       build_combined))
            plans.append((f"month_profile_{code}_{month:02d}_power", build_power))
            plans.append((f"month_profile_{code}_{month:02d}_head",  build_head))

    return plans


def figures_overlay(entries: list[tuple]):
    """All (dam, date) entries on one chart. Saved to outputs/day_profiles/."""
    out_dir = cfg.OUTPUT_DIR / "day_profiles"

    def build():
        fig, ax = render.new_figure(figsize=(11, 5.5))
        n = len(entries)
        for i, (dam, df, date) in enumerate(entries):
            day_df = _day_data(df, date)
            if day_df.empty:
                print(f"  WARNING: no data for {dam.code} {date}")
                continue
            hours = day_df["hour"].to_numpy()   # already 0-23 after load_dam()
            power = day_df["power_mw"].to_numpy()
            peak_cf = power.max() / dam.nameplate_mw * 100
            ax.plot(hours, power, color=_tab_color(i, n), linewidth=2.0,
                    marker="o", markersize=3,
                    label=f"{dam.name} {date}  (peak {peak_cf:.1f}% CF)")

        ax.set_xlim(-0.5, 23.5)
        ax.set_ylim(bottom=0)
        common.set_hour_ticks(ax)
        ax.set_xlabel("Hour of day (Pacific)")
        ax.set_ylabel(cfg.axis_label("power_mw"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.set_title(f"Hourly generation — selected days ({cfg.USACE_YEAR})")
        ax.legend(loc="best", fontsize=8)

        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)

        slug = "_".join(f"{c}{d.replace('-','')}" for c, d in cfg.DAY_PROFILE_DAYS)
        return fig, out_dir / f"overlay_{slug}.png"

    return [("day_profile_overlay", build)]


if __name__ == "__main__":
    dfs = {dam.code: derived.load_dam(dam.csv_path) for dam in cfg.ALL_DAMS}
    entries = _resolve_entries(dfs)
    if not entries:
        print("ERROR: no valid entries in DAY_PROFILE_DAYS")
        sys.exit(1)

    dam_by_code = {d.code: d for d in cfg.ALL_DAMS}
    for dam, _, _ in entries:
        (dam.output_dir / "day_profiles").mkdir(parents=True, exist_ok=True)
    for code in cfg.DAY_PROFILE_MONTHLY_DAMS:
        dam = dam_by_code.get(code)
        if dam:
            (dam.output_dir / "month_profiles").mkdir(parents=True, exist_ok=True)
    (cfg.OUTPUT_DIR / "day_profiles").mkdir(parents=True, exist_ok=True)

    mode = cfg.DAY_PROFILE_MODE
    plans: list = []
    if mode in ("individual", "both"):
        plans += figures_individual(entries)
    if mode in ("overlay", "both") and len(entries) >= 2:
        plans += figures_overlay(entries)
    elif mode == "overlay" and len(entries) == 1:
        plans += figures_individual(entries)
    plans += figures_month_profiles(dfs)

    for name, build in plans:
        result = build()
        if result[0] is not None:
            fig, path = result
            print("wrote", render.save_fig(fig, path))
