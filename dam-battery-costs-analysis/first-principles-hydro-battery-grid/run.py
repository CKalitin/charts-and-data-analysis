"""Orchestrator — load BPA load once, sweep, pick the design point, render every chart.

  python run.py            # generate all charts
  python run.py --count    # dry-run: print the chart count
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as cfg
from data_load import load_bpa_load, load_stats
from model.simulate import run_sweep, min_cost_full_point
from model.dispatch import dispatch, dispatch_summary
from charts.heatmaps import figures_heatmaps
from charts.timeseries import (figures_annual_daily, figures_quarter_days,
                               figures_months)
from viz import render


def main() -> None:
    dry_run = "--count" in sys.argv
    t0 = time.time()

    df = load_bpa_load()
    stats = load_stats(df)
    print(f"Loaded {stats['n']:,} intervals | "
          f"peak {stats['peak_mw']/1e3:.1f} GW, mean {stats['mean_mw']/1e3:.1f} GW, "
          f"{stats['twh']:.1f} TWh/yr")

    print(f"Sweeping {cfg.N_GRID}x{cfg.N_GRID} grid...")
    res = run_sweep(df["load_mw"].to_numpy())
    pt = min_cost_full_point(res)

    disp = dispatch(df, pt["hydro_mw"], pt["battery_mwh"])
    dsum = dispatch_summary(disp)

    print("\n-- Min-cost design that serves >=99.99% of 2024 load ------------")
    print(f"  Hydro     : {pt['hydro_mw']/1e3:6.2f} GW   (peak load {stats['peak_mw']/1e3:.2f} GW)")
    print(f"  Battery   : {pt['battery_mwh']/1e3:6.2f} GWh")
    print(f"  Capex     : ${pt['system_cost']/1e9:6.1f} B")
    print(f"  LCOE      : ${pt['lcoe']:6.1f} /MWh")
    print(f"  Served    : {pt['utilization']*100:.3f}%  (unserved {dsum['unserved_pct']:.3f}%)")
    print(f"  SURPRISE  : battery throughput only {dsum['throughput_twh']*1e3:.1f} GWh/yr "
          f"(~{dsum['equiv_cycles']:.1f} full cycles/yr) -- peak insurance, not a daily asset.")
    print("-----------------------------------------------------------------\n")

    plan = [
        *figures_heatmaps(res, pt, stats),
        *figures_annual_daily(disp, pt),
        *figures_quarter_days(disp, pt),
        *figures_months(disp, pt),
    ]

    if dry_run:
        print(f"Would generate {len(plan)} charts.")
        return

    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")

    print(f"\nDone — {len(plan)} charts in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
