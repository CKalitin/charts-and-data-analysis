"""Monthly energy-source breakdown charts for the dam + battery model.

For each dam and each (MW, MWh) combination, produces 12 stacked-bar charts
(one per calendar month) showing how each hour's load is served:

  Blue  (positive)  — dam generation that directly serves load
  Green (positive)  — battery discharge serving load
  Red   (positive)  — unmet load (shortfall)
  Orange(negative)  — battery charging (excess dam output stored)

The dashed step line shows the daily energy budget ÷ 24 h (the average power
the dam would produce if spread flat across the day).  The actual dispatch
ramps at installed capacity at the start of the day and exhausts the budget
before switching to battery, so the bars are decidedly non-flat.

Output:
  outputs/model/<dam_slug>/<combo_folder>/<dam_slug>_<MW>mw_<MWh>mwh_<YYYY-MM>.png
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import calendar

import numpy as np
import pandas as pd
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

import config as cfg
from charts import common
from model import config as mc
from model.simulate import simulate_single
from viz import render

# ── colours ──────────────────────────────────────────────────────────────────
_C_DAM       = "#1f77b4"   # blue  — dam → load
_C_DISCHARGE = "#2ca02c"   # green — battery → load
_C_SHORTFALL = "#d62728"   # red   — unmet load
_C_CHARGE    = "#ff7f0e"   # orange — battery charging (negative bar)
_C_REF       = "#555555"   # dark grey — daily avg power reference

_MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ── figure helpers ────────────────────────────────────────────────────────────

def _base_fig(title: str):
    fig, ax = render.new_figure(figsize=(16, 5))
    ax.set_title(title, fontsize=10)
    return fig, ax


def _month_hour_ticks(ax, year: int, month: int) -> None:
    n_days     = calendar.monthrange(year, month)[1]
    day_starts = list(range(0, n_days * 24, 24))
    ax.xaxis.set_major_locator(FixedLocator(day_starts))
    ax.xaxis.set_major_formatter(FixedFormatter([str(d + 1) for d in range(n_days)]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.tick_params(axis="x", labelsize=7)
    ax.set_xlabel(f"Day of {_MONTH_LABELS[month-1]} {year}")


def _mask_month(ts: dict, month: int, year: int) -> np.ndarray:
    """Boolean mask over ts arrays selecting hours in the given month/year."""
    dti = pd.DatetimeIndex(ts["dates"])
    return (dti.month == month) & (dti.year == year)


# ── single-month chart ────────────────────────────────────────────────────────

def _draw_dispatch_month(
    ts: dict,
    month: int,
    year: int,
    dam,
    installed_mw: float,
    battery_mwh: float,
    combo_folder: str,
) -> tuple:
    """Stacked-bar energy breakdown for one month. Returns (fig, path)."""
    mask = _mask_month(ts, month, year)

    gen         = ts["gen"][mask]
    gen_avg_ref = ts["gen_avg_ref"][mask]   # daily budget/24 — reference line
    load        = ts["load"][mask]
    charge      = ts["charge"][mask]
    discharge   = ts["discharge"][mask]
    shortfall   = ts["shortfall"][mask]

    if len(gen) == 0:
        return None, None

    hours = np.arange(len(gen))

    # Positive stack components (sum = load[h] for each hour)
    load_from_gen = np.minimum(gen, load)   # dam energy serving load directly

    # ── figure ───────────────────────────────────────────────────────────────
    month_str  = _MONTH_LABELS[month - 1]
    mw_slug    = f"{installed_mw:.0f}"
    mwh_slug   = f"{battery_mwh:.0f}"
    title = (f"{dam.name}  ·  {month_str} {year}  ·  "
             f"{installed_mw:,.0f} MW / {battery_mwh:,.0f} MWh")
    fig, ax = _base_fig(title)

    # ── stacked fills ─────────────────────────────────────────────────────────
    # stackplot/fill_between create O(1) PolyCollection artists vs O(N) bars;
    # at 672-744 hourly points the visual is identical to a stacked bar chart.
    ax.stackplot(hours, load_from_gen, discharge, shortfall,
                 colors=[_C_DAM, _C_DISCHARGE, _C_SHORTFALL],
                 labels=["Dam → load", "Battery → load", "Unmet load"],
                 linewidth=0)
    ax.fill_between(hours, 0, -charge,
                    color=_C_CHARGE, alpha=0.85, label="Battery charging",
                    linewidth=0, step="post")

    # Daily avg power reference (budget / 24 h) — step function, changes each day
    ax.step(hours, gen_avg_ref, where="post",
            color=_C_REF, linewidth=0.8, linestyle="--", alpha=0.75,
            label="Daily avg power")

    ax.axhline(0, color="black", linewidth=0.4, alpha=0.3)
    ax.set_xlim(-0.5, len(hours) - 0.5)
    _month_hour_ticks(ax, year, month)
    ax.set_ylabel("Power (MW)")
    ax.legend(loc="upper right", fontsize=8, ncol=5)

    # Month-level served load fraction
    served  = load_from_gen.sum() + discharge.sum()
    total   = load.sum()
    slf_pct = 100 * served / total if total > 0 else 0.0

    common.add_source(ax, cfg.SOURCE_USACE)
    common.add_watermark(ax)
    common.add_box(ax, fig, [
        f"Installed: {installed_mw:,.0f} MW",
        f"Battery:   {battery_mwh:,.0f} MWh",
        f"Month SLF: {slf_pct:.1f}%",
        f"Eff: {mc.BATTERY_EFFICIENCY*100:.0f}%",
    ])

    out_dir = cfg.OUTPUT_DIR / "model" / dam.slug / combo_folder
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{dam.slug}_{mw_slug}mw_{mwh_slug}mwh_{year}-{month:02d}.png"
    return fig, path


# ── public entry point ────────────────────────────────────────────────────────

def figures_dispatch_profiles(
    df: pd.DataFrame,
    dam,
    extra_abs_combos: list | None = None,
) -> list:
    """Return plan list for all combos × 12 months for one dam.

    extra_abs_combos: optional list of (installed_mw, battery_mwh) in absolute
    MW/MWh (not fractions), appended after the standard MODEL_COMBOS.
    """
    nameplate = dam.nameplate_mw
    mwh_max   = nameplate * mc.MWH_PER_MW

    abs_combos = [(nameplate * mw_f, mwh_max * mwh_f) for mw_f, mwh_f in mc.MODEL_COMBOS]
    if extra_abs_combos:
        abs_combos += list(extra_abs_combos)

    plan = []
    for installed_mw, battery_mwh in abs_combos:
        combo_folder = f"{installed_mw:.0f}mw_{battery_mwh:.0f}mwh"

        ts = simulate_single(df, installed_mw, battery_mwh)

        dti = pd.DatetimeIndex(ts["dates"])
        ym_pairs = sorted(set(zip(dti.year.tolist(), dti.month.tolist())))

        for year, month in ym_pairs:
            def _build(
                ts=ts, month=month, year=year, dam=dam,
                installed_mw=installed_mw, battery_mwh=battery_mwh,
                combo_folder=combo_folder,
            ):
                return _draw_dispatch_month(
                    ts, month, year, dam,
                    installed_mw, battery_mwh, combo_folder,
                )
            plan.append((f"dispatch_{dam.code}_{combo_folder}_{year}_{month:02d}", _build))

    return plan


# ── standalone runner ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time
    import derived

    t0 = time.time()
    dam_by_code = {d.code: d for d in cfg.ALL_DAMS}
    plan = []

    for code in mc.MODEL_DAMS:
        dam = dam_by_code.get(code)
        if dam is None:
            print(f"WARNING: unknown dam code {code!r}")
            continue
        print(f"Loading {dam.name}...")
        df = derived.load_dam(dam.csv_path)
        if df.empty:
            print(f"  SKIP: no data")
            continue
        plan += figures_dispatch_profiles(df, dam)

    print(f"Generating {len(plan)} charts...")
    for name, build in plan:
        fig, path = build()
        if fig is None:
            continue
        render.save_fig(fig, path, dpi=render.BULK_DPI)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")

    print(f"\nDone in {time.time() - t0:.1f}s")
