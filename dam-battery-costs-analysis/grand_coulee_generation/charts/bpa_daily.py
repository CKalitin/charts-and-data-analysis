"""BPA 5-minute daily snapshots — three chart products.

Product A — combined (1 file): 4-row × 2-column grid, one row per quarter day.
  Left panel:  stacked area — generation by type (nuclear, hydro, fossil, wind, solar).
  Right panel: demand line — load + net exports.

Product A_ind — individual (4 files, one per quarter day): same left/right layout
  as Product A but each quarter day gets its own standalone 1×2 figure.
  Filenames: bpa_gen_and_demand_q1_jan01_2024.png, ..._q2_apr01_2024.png, etc.

Product B — overlay (1 file): side-by-side single-panel chart.
  Left panel:  net generation (MW) for all 4 quarter days — 4 lines.
  Right panel: demand = load + net exports for all 4 quarter days — 4 lines.
  Both panels share the same colour per quarter day (no solid/dashed needed).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

import config as cfg
import derived
from charts import common
from viz import render

# Slug for each quarter day — used in individual filenames.
_QUARTER_SLUG = {
    "Q1 · Jan 1": "q1_jan01",
    "Q2 · Apr 1": "q2_apr01",
    "Q3 · Jul 1": "q3_jul01",
    "Q4 · Oct 1": "q4_oct01",
}


# --- Shared helpers -------------------------------------------------------------------
def _resample_hourly(day_df: pd.DataFrame, col: str) -> tuple[np.ndarray, np.ndarray]:
    """Downsample 5-minute series to hourly means. Returns (hours 0..23, values)."""
    s = day_df.set_index("datetime")[col].resample("h").mean()
    return np.arange(len(s)), s.to_numpy()


def _gen_cols() -> list[str]:
    return [c for c, _, _ in cfg.GEN_TYPES]


# --- Panel draw helpers (draw onto a provided Axes) -----------------------------------
def _draw_stacked_area(ax, day_df: pd.DataFrame, day_label: str) -> None:
    stacks, labels, colors = [], [], []
    for col, label, color in cfg.GEN_TYPES:
        hours, vals = _resample_hourly(day_df, col)
        stacks.append(np.nan_to_num(vals, nan=0.0))
        labels.append(label)
        colors.append(color)
    ax.stackplot(hours, *stacks, labels=labels, colors=colors, alpha=0.85)
    ax.set_xlim(0, 23)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Generation (MW)")
    ax.set_title(f"{day_label} — generation by type", fontsize=9)
    ax.legend(loc="upper left", fontsize=7)


def _draw_demand(ax, day_df: pd.DataFrame, day_label: str) -> None:
    color = cfg.QUARTER_DAY_COLOR.get(day_label, "#333333")
    # Demand = load + net interchange
    day2 = day_df.copy()
    day2["demand_mw"] = derived.demand(day_df).values
    hours, demand_vals = _resample_hourly(day2, "demand_mw")
    hours_l, load_vals = _resample_hourly(day_df, "load_mw")
    ax.plot(hours, demand_vals, color=color, linewidth=2.2, label="Load + net exports")
    ax.plot(hours_l, load_vals, color="#aaaaaa", linewidth=1.2, linestyle="--",
            label="Load only")
    ax.set_xlim(0, 23)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("MW")
    ax.set_title(f"{day_label} — load + net exports", fontsize=9)
    ax.legend(fontsize=7, loc="upper left")


# --- Product A: combined 4×2 grid ----------------------------------------------------
def figures_quarterly_panels(bpa: pd.DataFrame):
    def build():
        n = len(cfg.QUARTER_DAYS)
        fig = Figure(figsize=(14, 4.0 * n), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        all_axes = []
        for row, (day_str, label) in enumerate(cfg.QUARTER_DAYS):
            day_df = derived.bpa_day(bpa, day_str)
            if day_df.empty:
                continue
            ax_l = fig.add_subplot(n, 2, row * 2 + 1)
            ax_r = fig.add_subplot(n, 2, row * 2 + 2)
            _draw_stacked_area(ax_l, day_df, label)
            _draw_demand(ax_r, day_df, label)
            all_axes.extend([ax_l, ax_r])
        fig.suptitle(
            f"BPA grid: generation by type and demand — quarterly snapshots {cfg.BPA_YEAR}",
            fontsize=12,
        )
        # Source + watermark on bottom row panels.
        if len(all_axes) >= 2:
            common.add_source(all_axes[-2], cfg.SOURCE_BPA)
            common.add_watermark(all_axes[-1])
        path = cfg.OUTPUT_DIR / "bpa_gen_by_type_and_load_quarterly_snapshot_2024.png"
        return fig, path

    return [("bpa_quarterly_panels_combined", build)]


# --- Product A_ind: individual 1×2 chart per quarter day ----------------------------
def figures_quarterly_individual(bpa: pd.DataFrame):
    plans = []
    for day_str, label in cfg.QUARTER_DAYS:
        slug = _QUARTER_SLUG.get(label, label.replace(" ", "_").lower())

        def build(ds=day_str, lbl=label, sl=slug):
            day_df = derived.bpa_day(bpa, ds)
            fig = Figure(figsize=(14, 4.5), dpi=render.DPI)
            FigureCanvasAgg(fig)
            fig.set_constrained_layout(True)
            ax_l = fig.add_subplot(1, 2, 1)
            ax_r = fig.add_subplot(1, 2, 2)
            _draw_stacked_area(ax_l, day_df, lbl)
            _draw_demand(ax_r, day_df, lbl)
            fig.suptitle(
                f"BPA grid: generation and demand — {lbl} ({cfg.BPA_YEAR})", fontsize=11
            )
            common.add_source(ax_l, cfg.SOURCE_BPA)
            common.add_watermark(ax_r)
            path = cfg.OUTPUT_DIR / f"bpa_gen_and_demand_{sl}_2024.png"
            return fig, path

        plans.append((f"bpa_individual_{slug}", build))
    return plans


# --- Product B: side-by-side overlay (net gen | demand), 4 lines each ---------------
def figures_overlay(bpa: pd.DataFrame):
    def build():
        fig = Figure(figsize=(14, 5.5), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax_gen = fig.add_subplot(1, 2, 1)
        ax_dem = fig.add_subplot(1, 2, 2)

        for day_str, label in cfg.QUARTER_DAYS:
            day_df = derived.bpa_day(bpa, day_str)
            if day_df.empty:
                continue
            color = cfg.QUARTER_DAY_COLOR.get(label, "#333333")

            # Net generation
            day2 = day_df.copy()
            day2["net_gen_mw"] = derived.net_generation(day_df).values
            hours_g, gen_vals = _resample_hourly(day2, "net_gen_mw")
            ax_gen.plot(hours_g, gen_vals, color=color, linewidth=2.0, label=label)

            # Demand
            day2["demand_mw"] = derived.demand(day_df).values
            hours_d, dem_vals = _resample_hourly(day2, "demand_mw")
            ax_dem.plot(hours_d, dem_vals, color=color, linewidth=2.0, label=label)

        for ax, title in [
            (ax_gen, "Net generation (MW)"),
            (ax_dem, "Demand — load + net exports (MW)"),
        ]:
            ax.set_xlim(0, 23)
            ax.set_ylim(bottom=0)
            ax.set_xlabel("Hour of day")
            ax.set_ylabel("MW")
            ax.set_title(title, fontsize=10)
            ax.legend(fontsize=9, loc="best")

        fig.suptitle(
            f"BPA grid: net generation vs demand — quarterly overlay {cfg.BPA_YEAR}",
            fontsize=12,
        )
        common.add_source(ax_gen, cfg.SOURCE_BPA)
        common.add_watermark(ax_dem)
        path = cfg.OUTPUT_DIR / "bpa_net_gen_vs_demand_quarterly_overlay_2024.png"
        return fig, path

    return [("bpa_overlay", build)]


if __name__ == "__main__":
    bpa = derived.load_bpa()
    all_plans = [
        *figures_quarterly_panels(bpa),
        *figures_quarterly_individual(bpa),
        *figures_overlay(bpa),
    ]
    for name, build in all_plans:
        fig, path = build()
        print("wrote", render.save_fig(fig, path))
