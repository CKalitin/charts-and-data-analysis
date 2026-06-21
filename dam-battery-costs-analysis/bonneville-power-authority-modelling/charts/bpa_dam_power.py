"""Per-dam hourly power profiles — stacked bar charts for selected days.

Shows the top-N dams by nameplate capacity individually; all remaining dams
are summed into an "Other" bucket. Hour axis covers 0-23 (Pacific), one bar
per hour with no gaps.

CONFIGURE: edit config.py
  DAM_POWER_QUARTER_DAYS  — list of (date_str, label) for quarter snapshots
  DAM_POWER_CUSTOM_DAYS   — additional inspection dates (YYYY-MM-DD)
  DAM_POWER_TOP_N         — how many dams to show individually (default 9)

Run:  python charts/bpa_dam_power.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.cm as mcm
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Patch

import config as cfg
import derived
from charts import common
from viz import render

OTHER_COLOR = "#aaaaaa"
_HOURS = np.arange(24)


def _sorted_dams() -> tuple[list, list]:
    """(top_n dams, other dams) sorted by nameplate MW descending."""
    ordered = sorted(cfg.ALL_DAMS, key=lambda d: d.nameplate_mw, reverse=True)
    return ordered[: cfg.DAM_POWER_TOP_N], ordered[cfg.DAM_POWER_TOP_N :]


def _dam_colors(top_dams: list) -> dict:
    return {dam.code: mcm.tab10(i / 10) for i, dam in enumerate(top_dams)}


def _load_day(dfs: dict, day_str: str) -> dict[str, np.ndarray]:
    """Extract 24-element power_mw arrays for all dams with data on day_str.

    df["hour"] is 0-23 after derived.load_dam (with_time_cols uses datetime.dt.hour).
    """
    result = {}
    for code, df in dfs.items():
        if df is None or df.empty:
            continue
        day_df = df[df["date"] == day_str]
        if day_df.empty:
            continue
        power = np.zeros(24)
        hr = day_df["hour"].to_numpy().astype(int)
        pw = np.where(
            day_df["power_mw"].isna().to_numpy(),
            0.0,
            day_df["power_mw"].to_numpy(dtype=float),
        )
        valid = (hr >= 0) & (hr < 24)
        power[hr[valid]] = pw[valid]
        result[code] = power
    return result


def _draw_dam_power(
    ax,
    day_str: str,
    dfs: dict,
    top_dams: list,
    other_dams: list,
    dam_colors: dict,
    title: str | None = None,
) -> list:
    """Draw stacked bar chart onto ax. Returns legend Patch list."""
    data = _load_day(dfs, day_str)

    bottom = np.zeros(24)
    legend_patches = []

    for dam in top_dams:
        if dam.code not in data:
            continue
        power = data[dam.code]
        color = dam_colors[dam.code]
        ax.bar(_HOURS, power, bottom=bottom, width=1.0,
               color=color, alpha=0.88, linewidth=0)
        bottom += power
        legend_patches.append(Patch(facecolor=color, alpha=0.88, label=dam.name))

    other_power = sum(
        data[dam.code] for dam in other_dams if dam.code in data
    )
    if isinstance(other_power, np.ndarray) and other_power.any():
        ax.bar(_HOURS, other_power, bottom=bottom, width=1.0,
               color=OTHER_COLOR, alpha=0.88, linewidth=0)
        legend_patches.append(Patch(facecolor=OTHER_COLOR, alpha=0.88, label="Other"))

    if not data:
        ax.text(0.5, 0.5, f"No data\n{day_str}",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=9, color="0.5")

    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(bottom=0)
    common.set_hour_ticks(ax)
    ax.set_xlabel("Hour of day (Pacific)")
    ax.set_ylabel("Power (MW)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    if title is not None:
        ax.set_title(title, fontsize=9)
    return legend_patches


def _all_days() -> list[tuple[str, str]]:
    days = list(cfg.DAM_POWER_QUARTER_DAYS)
    for d in cfg.DAM_POWER_CUSTOM_DAYS:
        days.append((d, d))
    return days


def figures_all_days(dfs: dict):
    """Individual stacked-bar chart per day + a combined grid chart."""
    top_dams, other_dams = _sorted_dams()
    dam_colors = _dam_colors(top_dams)
    out_dir = cfg.BPA_OUTPUT_DIR / "dam_power"
    all_days = _all_days()
    plans = []

    # Individual chart per day
    for day_str, label in all_days:
        def build(ds=day_str, lbl=label):
            fig = Figure(figsize=(12, 5.5), dpi=render.DPI)
            FigureCanvasAgg(fig)
            fig.set_constrained_layout(True)
            ax = fig.add_subplot(1, 1, 1)
            patches = _draw_dam_power(ax, ds, dfs, top_dams, other_dams, dam_colors, None)
            if patches:
                ax.legend(handles=patches, loc="upper left", fontsize=7.5, ncol=2)
            fig.suptitle(
                f"BPA dam hourly power — {lbl} ({cfg.USACE_YEAR})", fontsize=12
            )
            common.add_source(ax, cfg.SOURCE_USACE)
            common.add_watermark(ax)
            slug = ds.replace("-", "")
            return fig, out_dir / f"bpa_dam_power_{slug}.png"

        plans.append((f"bpa_dam_power_{day_str}", build))

    # Combined grid (all days in one figure)
    def build_combined():
        n = len(all_days)
        ncols = 2
        nrows = (n + ncols - 1) // ncols
        fig = Figure(figsize=(14, 4.5 * nrows), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        first_patches = None
        for i, (day_str, label) in enumerate(all_days):
            ax = fig.add_subplot(nrows, ncols, i + 1)
            patches = _draw_dam_power(
                ax, day_str, dfs, top_dams, other_dams, dam_colors, label
            )
            if first_patches is None and patches:
                first_patches = patches

        # Legend in the last panel (or first if only one)
        axes = fig.get_axes()
        if first_patches and axes:
            axes[-1].legend(
                handles=first_patches, loc="upper right",
                fontsize=6.5, ncol=1,
            )

        fig.suptitle(
            f"BPA dam hourly power — quarterly + custom days ({cfg.USACE_YEAR})",
            fontsize=12,
        )
        common.add_source(axes[0], cfg.SOURCE_USACE)
        common.add_watermark(axes[-1])
        return fig, out_dir / "bpa_dam_power_combined.png"

    plans.append(("bpa_dam_power_combined", build_combined))
    return plans


def figures_cf_all_days(dfs: dict):
    """Capacity factor bar chart per day — one per day + combined grid.

    Bars are coloured by dam type (storage vs RoR), sorted by CF descending on that day.
    """
    from charts.bpa_dam_types import _DAMS, STORAGE_COLOR, ROR_COLOR

    _type_map = {row[0]: row[3] for row in _DAMS}
    out_dir   = cfg.BPA_OUTPUT_DIR / "dam_power"
    all_days  = _all_days()

    def _day_cf_df(day_str: str) -> pd.DataFrame:
        data = _load_day(dfs, day_str)
        rows = []
        for dam in cfg.ALL_DAMS:
            if dam.code not in data:
                continue
            avg_power = float(data[dam.code].mean())
            rows.append({
                "name":               dam.name,
                "dam_type":           _type_map.get(dam.name, "ror"),
                "capacity_factor_pct": avg_power / dam.nameplate_mw * 100,
            })
        return (pd.DataFrame(rows)
                .sort_values("capacity_factor_pct", ascending=False)
                .reset_index(drop=True))

    def _draw_cf(ax, day_str: str, title: str | None = None) -> None:
        df = _day_cf_df(day_str)
        colors = [STORAGE_COLOR if t == "storage" else ROR_COLOR for t in df["dam_type"]]
        x = np.arange(len(df))
        ax.bar(x, df["capacity_factor_pct"], color=colors, width=0.75, alpha=0.88, linewidth=0)
        ax.set_xticks(x)
        ax.set_xticklabels(df["name"], rotation=45, ha="right", fontsize=7)
        ax.set_ylabel("Capacity factor (%)")
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        if title is not None:
            ax.set_title(title, fontsize=9)

    _legend = [
        Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
        Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
    ]
    plans = []

    # Individual chart per day
    for day_str, label in all_days:
        def build(ds=day_str, lbl=label):
            fig = Figure(figsize=(14, 6), dpi=render.DPI)
            FigureCanvasAgg(fig)
            fig.set_constrained_layout(True)
            ax = fig.add_subplot(1, 1, 1)
            _draw_cf(ax, ds)
            ax.legend(handles=_legend, loc="upper right", fontsize=9)
            fig.suptitle(f"BPA dam capacity factors — {lbl} ({cfg.USACE_YEAR})", fontsize=12)
            common.add_source(ax, cfg.SOURCE_USACE)
            common.add_watermark(ax)
            slug = ds.replace("-", "")
            return fig, out_dir / f"bpa_dam_cf_{slug}.png"
        plans.append((f"bpa_dam_cf_{day_str}", build))

    # Combined grid
    def build_combined():
        n = len(all_days)
        ncols = 2
        nrows = (n + ncols - 1) // ncols
        fig = Figure(figsize=(14, 4.5 * nrows), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        axes = []
        for i, (day_str, label) in enumerate(all_days):
            ax = fig.add_subplot(nrows, ncols, i + 1)
            _draw_cf(ax, day_str, title=label)
            axes.append(ax)
        if axes:
            axes[-1].legend(handles=_legend, loc="upper right", fontsize=7)
        fig.suptitle(
            f"BPA dam capacity factors — quarterly + custom days ({cfg.USACE_YEAR})", fontsize=12
        )
        common.add_source(axes[0], cfg.SOURCE_USACE)
        common.add_watermark(axes[-1])
        return fig, out_dir / "bpa_dam_cf_combined.png"

    plans.append(("bpa_dam_cf_combined", build_combined))
    return plans


if __name__ == "__main__":
    import time
    t0 = time.time()
    dfs = {dam.code: derived.load_dam(dam.csv_path) for dam in cfg.ALL_DAMS}
    out_dir = cfg.BPA_OUTPUT_DIR / "dam_power"
    out_dir.mkdir(parents=True, exist_ok=True)
    plans = [*figures_all_days(dfs), *figures_cf_all_days(dfs)]
    for name, build in plans:
        fig, path = build()
        print("  wrote", render.save_fig(fig, path))
    print(f"\nwrote {len(plans)} charts in {time.time() - t0:.1f}s")
