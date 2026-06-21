"""Thin orchestrator — loads data once per dam, runs every chart family.

Usage:
  python run.py            # generate all charts
  python run.py --count    # dry-run: print chart count without rendering
  python run.py --stats    # print key stats only, no charts

Add a new dam: add a DamConfig to config.ALL_DAMS — no changes needed here.
Run a single family: python charts/diurnal_season.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as cfg
import derived
from viz import render
from charts import (
    annual_timeseries,
    bpa_daily,
    bpa_dam_power,
    bpa_dam_types,
    capacity_factor,
    day_profile,
    diurnal_season,
    peak_cf,
    spill_fraction,
    storage_vs_runofriver,
)


def print_stats(dfs: dict) -> None:
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for dam in cfg.ALL_DAMS:
        df = dfs.get(dam.code)
        if df is None or df.empty:
            continue
        print(f"\n=== {dam.name} key stats ({dam.year}) ===")
        print(f"Annual avg power: {df['power_mw'].mean():.0f} MW")
        print(f"Annual CF: {df['power_mw'].mean() / dam.nameplate_mw * 100:.1f}%")
        hourly = derived.annual_diurnal(df)
        night, peak = hourly.loc[2:5].mean(), hourly.loc[17:20].mean()
        print(f"Overnight min (hr 2-5):  {night:.0f} MW")
        print(f"Evening peak (hr 17-20): {peak:.0f} MW")
        print(f"Daily swing ratio: {peak / night:.2f}x")
        n_spill = (df["spill_kcfs"] > 0).sum()
        print(f"Hours with spill: {n_spill} / {len(df)}")
        sf = derived.monthly_spill_fraction(df) * 100
        if sf.notna().any():
            peak_m = int(sf.idxmax())
            print(f"Peak spill month: {months[peak_m - 1]} ({sf.loc[peak_m]:.1f}%)")
    print()


def main() -> None:
    dry_run = "--count" in sys.argv
    stats_only = "--stats" in sys.argv
    t0 = time.time()

    # Load each dam's data once.
    dfs: dict = {}
    for dam in cfg.ALL_DAMS:
        dfs[dam.code] = derived.load_dam(dam.csv_path)
    missing = [dam.code for dam in cfg.ALL_DAMS if dfs[dam.code].empty]
    n_good = len(cfg.ALL_DAMS) - len(missing)
    if missing:
        print(f"INFO: {n_good}/{len(cfg.ALL_DAMS)} dams have data  (missing: {missing})")

    bpa = derived.load_bpa()
    if bpa.empty:
        print(f"WARNING: BPA CSV not found — {cfg.BPA_RAW_CSV}")

    print_stats(dfs)
    if stats_only:
        return

    plan: list = []

    # Per-dam chart families — one loop covers every dam in ALL_DAMS.
    for dam in cfg.ALL_DAMS:
        df = dfs[dam.code]
        if df.empty:
            continue
        plan += diurnal_season.figures(df, dam)
        plan += annual_timeseries.figures(df, dam)
        plan += capacity_factor.figures(df, dam)
        plan += capacity_factor.figures_cf_range_monthly(df, dam)
        plan += capacity_factor.figures_cf_range_daily(df, dam)
        plan += spill_fraction.figures(df, dam)
        plan += peak_cf.figures_monthly(df, dam)
        plan += peak_cf.figures_annual_summary(df, dam)

    # Day-profile inspection charts (configured in config.py).
    dp_entries = day_profile._resolve_entries(dfs)
    if dp_entries:
        dp_mode = cfg.DAY_PROFILE_MODE
        if dp_mode in ("individual", "both"):
            plan += day_profile.figures_individual(dp_entries)
        if dp_mode in ("overlay", "both") and len(dp_entries) >= 2:
            plan += day_profile.figures_overlay(dp_entries)
        elif dp_mode == "overlay" and len(dp_entries) == 1:
            plan += day_profile.figures_individual(dp_entries)
    plan += day_profile.figures_month_profiles(dfs)

    # Cross-dam comparison — requires both specific dams.
    gcl_df, bon_df = dfs.get(cfg.GCL.code), dfs.get(cfg.BON.code)
    if gcl_df is not None and not gcl_df.empty and bon_df is not None and not bon_df.empty:
        plan += storage_vs_runofriver.figures(gcl_df, bon_df)

    # Per-dam hourly power profiles (uses USACE dam data).
    plan += bpa_dam_power.figures_all_days(dfs)
    plan += bpa_dam_power.figures_cf_all_days(dfs)

    # BPA dam-type classification charts (no live data needed).
    plan += bpa_dam_types.figures_all_dams()
    plan += bpa_dam_types.figures_totals_mw()
    plan += bpa_dam_types.figures_reservoir_af()
    plan += bpa_dam_types.figures_totals_af()
    plan += bpa_dam_types.figures_energy_storage_gwh()
    plan += bpa_dam_types.figures_scatter_mw_vs_gwh()
    plan += bpa_dam_types.figures_avg_flow_bar(dfs)
    plan += bpa_dam_types.figures_cf_bar(dfs)
    plan += bpa_dam_types.figures_cf_vs_capacity_scatter(dfs)
    plan += bpa_dam_types.figures_peak_cf_bar(dfs)
    plan += bpa_dam_types.figures_peak_cf_vs_capacity_scatter(dfs)
    plan += bpa_dam_types.figures_load_factor_bar(dfs)
    plan += bpa_dam_types.figures_scatter_flow_vs_storage(dfs)
    plan += bpa_dam_types.figures_scatter_flow_vs_active_storage(dfs)
    plan += bpa_dam_types.figures_spill_bars(dfs)
    plan += bpa_dam_types.figures_spill_energy_bars(dfs)

    # BPA system charts.
    if not bpa.empty:
        plan += bpa_daily.figures_quarterly_panels(bpa)
        plan += bpa_daily.figures_quarterly_individual(bpa)
        plan += bpa_daily.figures_overlay(bpa)
        plan += bpa_daily.figures_day_profile(bpa)

    if dry_run:
        print(f"Would generate {len(plan)} charts.")
        return

    for dam in cfg.ALL_DAMS:
        (dam.output_dir / "peak_cf").mkdir(parents=True, exist_ok=True)
        (dam.output_dir / "day_profiles").mkdir(parents=True, exist_ok=True)
        (dam.output_dir / "month_profiles").mkdir(parents=True, exist_ok=True)
    (cfg.OUTPUT_DIR / "day_profiles").mkdir(parents=True, exist_ok=True)
    cfg.BPA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (cfg.BPA_OUTPUT_DIR / "day_profiles").mkdir(parents=True, exist_ok=True)
    (cfg.BPA_OUTPUT_DIR / "dam_power").mkdir(parents=True, exist_ok=True)

    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")

    print(f"\nDone — {len(plan)} charts in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
