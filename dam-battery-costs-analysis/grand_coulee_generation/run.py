"""Thin orchestrator — loads all derived data once, runs every chart family.

Usage:
  python run.py            # generate all charts
  python run.py --count    # dry-run: print chart count without rendering
  python run.py --stats    # just print the key blog-post numbers, no charts

Run a single family directly for fast iteration:
  python charts/diurnal_season.py
  python charts/bpa_daily.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure the package root is on the path when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as cfg
import derived
from viz import render
from charts import (
    annual_timeseries,
    bpa_daily,
    capacity_factor,
    diurnal_season,
    spill_fraction,
    storage_vs_runofriver,
)


def print_stats(gcl) -> None:
    """Print key numbers for the blog post."""
    import numpy as np
    print("\n=== Grand Coulee key stats (2023) ===")
    if gcl.empty:
        print("  !! GCL data not loaded yet"); return

    print(f"Annual avg power: {gcl['power_mw'].mean():.0f} MW")
    print(f"Annual CF: {gcl['power_mw'].mean() / cfg.GCL_NAMEPLATE_MW * 100:.1f}%")

    hourly_avg = derived.annual_diurnal(gcl)
    night = hourly_avg.loc[2:5].mean()
    peak = hourly_avg.loc[17:20].mean()
    print(f"Avg overnight min (hr 2–5):  {night:.0f} MW")
    print(f"Avg evening peak (hr 17–20): {peak:.0f} MW")
    print(f"Daily swing ratio: {peak / night:.2f}x")

    n_spill = (gcl["spill_kcfs"] > 0).sum()
    print(f"Hours with any spill: {n_spill} / {len(gcl)}")

    sf = derived.monthly_spill_fraction(gcl) * 100
    peak_m = int(sf.idxmax())
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    print(f"Max spill fraction month: {months[peak_m - 1]} ({sf.loc[peak_m]:.1f}%)")
    print()


def main() -> None:
    dry_run = "--count" in sys.argv
    stats_only = "--stats" in sys.argv

    # Load data once — every chart family reuses these.
    t0 = time.time()
    gcl = derived.load_dam(cfg.GCL_CSV)
    bon = derived.load_dam(cfg.BON_CSV)
    bpa = derived.load_bpa()

    if gcl.empty:
        print("WARNING: GCL CSV not found — USACE charts will be skipped.")
        print(f"  Expected: {cfg.GCL_CSV}")
    if bon.empty:
        print("WARNING: Bonneville CSV not found — comparison chart will be skipped.")
    if bpa.empty:
        print("WARNING: BPA CSV not found — BPA charts will be skipped.")

    print_stats(gcl)
    if stats_only:
        return

    # Build the chart plan.
    plan: list = []
    if not gcl.empty:
        plan += diurnal_season.figures(gcl)
        plan += annual_timeseries.figures(gcl)
        plan += capacity_factor.figures(gcl)
        plan += spill_fraction.figures(gcl)
    if not gcl.empty and not bon.empty:
        plan += storage_vs_runofriver.figures(gcl, bon)
    if not bpa.empty:
        plan += bpa_daily.figures_quarterly_panels(bpa)
        plan += bpa_daily.figures_quarterly_individual(bpa)
        plan += bpa_daily.figures_overlay(bpa)

    if dry_run:
        print(f"Would generate {len(plan)} charts.")
        return

    cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")

    print(f"\nDone — {len(plan)} charts in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
