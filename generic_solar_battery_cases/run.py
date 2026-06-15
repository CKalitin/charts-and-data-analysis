"""Entry point: build every chart for the solar+battery generic-use-case model.

All real logic lives in the layers below (config / model / derived / charts);
this just orchestrates and reports. The one expensive step (the served-energy
grid) is computed once, cached, and shared by every chart.

    python run.py            # build and save all charts
    python run.py --count    # list planned charts without rendering
    python run.py --no-cache # force-rebuild the served grid
"""

from __future__ import annotations

import argparse
import sys
import time

import numpy as np

import config as cfg
import derived
import model
from charts import (build_plane, common, cost_plane, daily_timeseries as daily_timeseries_chart,
                    load_plane as load_plane_chart, solar_fraction as solar_fraction_chart,
                    terraform_lcoe as terraform_lcoe_chart,
                    timeseries, utilization_vs_income, utilization_vs_load_capex)
from viz import render


def _report(grid: model.ServedGrid, plane: derived.CostPlane,
            isw: derived.IncomeSweep, lcsw: derived.LoadCapexSweep) -> None:
    """Print key findings, flagging anything counterintuitive."""
    print("\n" + "=" * 70)
    print("FINDINGS")
    print("=" * 70)
    print(f"Site {common.site_label()} | capacity factor {grid.capacity_factor:.1%} "
          f"| load {cfg.LOAD_KW:g} kW | demand {grid.demand_kwh:,.0f} kWh/yr")
    print(f"Max achievable utilization on grid: {grid.utilization.max():.4%} "
          f"(warm-start converged in {grid.warmstart_iters} iters)")

    # Default operating point.
    opt = derived.optimal_build(grid, cfg.INCOME_PER_KWH, cfg.SOLAR_COST_ANN,
                                cfg.BATTERY_COST_ANN, cfg.LOAD_COST_ANN)
    print(f"\nAt income ${cfg.INCOME_PER_KWH:.3g}/kWh, solar ${cfg.SOLAR_COST_ANN:.3g}/kW·yr, "
          f"battery ${cfg.BATTERY_COST_ANN:.3g}/kWh·yr, load capex ${cfg.LOAD_COST_ANN:.3g}/kW·yr:")
    print(f"  optimal build = {opt.kw_solar:g} kW solar + {opt.kwh_battery:g} kWh battery "
          f"-> utilization {opt.utilization:.1%}, profit ${opt.profit_per_yr:,.0f}/yr")

    # Income thresholds for utilization milestones.
    print("\nLoad income needed to make each utilization the profit-optimal choice:")
    u = isw.utilization
    for target in (0.25, 0.50, 0.90, 0.99):
        idx = np.argmax(u >= target)
        if u[idx] >= target:
            print(f"  >= {target:>5.0%}: ${isw.income_per_kwh[idx]:.3g}/kWh")
        else:
            print(f"  >= {target:>5.0%}: not reached on the income sweep")

    # Load capex threshold.
    profitable_mask = lcsw.utilization > 0
    if profitable_mask.any():
        threshold = float(lcsw.load_cost_ann[profitable_mask][-1])
        print(f"\nLoad capex breakeven: system profitable up to "
              f"${threshold:.3g}/kW·yr  (${threshold * cfg.LOAD_AMORTIZATION_YEARS:.0f}/kW "
              f"at {cfg.LOAD_AMORTIZATION_YEARS:g}-yr amort)")

    # Named load cases.
    print("\nNamed load cases (optimal utilization at default solar/battery costs):")
    for name, (income, capex_raw, amort) in cfg.LOAD_CASES.items():
        lc_ann = capex_raw / amort
        case_opt = derived.optimal_build(grid, income, cfg.SOLAR_COST_ANN,
                                         cfg.BATTERY_COST_ANN, lc_ann)
        print(f"  {name}: income=${income:.4g}/kWh, capex=${capex_raw:.0f}/kW ({amort}yr) "
              f"-> util {case_opt.utilization:.1%}, profit ${case_opt.profit_per_yr:,.0f}/yr")

    # Counterintuitive flags.
    print("\nFlags:")
    breakeven_idx = np.argmax(isw.opt_kw_solar > 0)
    print(f"  * Below ${isw.income_per_kwh[breakeven_idx]:.3g}/kWh income the optimum is to build "
          f"NOTHING (income < solar breakeven) -> utilization 0%. "
          f"This is the substantive difference from a capex-driven frame: with no revenue signal, "
          f"no build is justified.")
    print(f"  * Load capex shifts when 'no-build' wins but NOT which hardware is optimal —")
    print(f"    utilization is flat until the system turns unprofitable, then drops to 0%.")
    if plane.edge_fraction > 0.01:
        print(f"  * {plane.edge_fraction:.0%} of cost-plane cells hit the build-grid edge — "
              f"raise KW_SOLAR_GRID / KWH_BATTERY_GRID maxima for those cheap-cost corners.")
    if isw.edge_fraction > 0.01:
        print(f"  * {isw.edge_fraction:.0%} of income-sweep points hit the build-grid edge.")
    print("=" * 70 + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", action="store_true", help="list planned charts, render nothing")
    ap.add_argument("--no-cache", action="store_true", help="force-rebuild the served grid")
    args = ap.parse_args()

    t0 = time.time()
    grid = derived.load_served_grid(use_cache=not args.no_cache)
    plane = derived.cost_plane(grid)
    cp_lcoe = derived.cost_plane_lcoe(grid)
    isw = derived.income_sweep(grid)
    lcsw = derived.load_capex_sweep(grid)
    lcsw_lcoe = derived.load_capex_sweep_lcoe(grid)
    lplane = derived.load_plane(grid)
    sf_sweeps = [derived.solar_fraction_sweep(grid, T)
                 for T in cfg.SOLAR_FRACTION_TOTAL_UNITS]

    # Native-resolution data for the time-series chart.
    data = model.load_nsrdb(cfg.DATA_FILE, resample=None)

    plan = [
        *cost_plane.figures(plane, grid),
        *cost_plane.figures_lcoe(cp_lcoe, grid),
        *utilization_vs_income.figures(isw, grid),
        *build_plane.figures(grid),
        *build_plane.figures_lcoe(grid),
        *build_plane.figures_lcoe_frontiers(grid),
        *timeseries.figures(data, grid),
        *daily_timeseries_chart.figures(data, grid),
        *daily_timeseries_chart.figures_daily(data, grid),
        *utilization_vs_load_capex.figures(lcsw, lcsw_lcoe, grid),
        *load_plane_chart.figures(lplane, grid),
        *solar_fraction_chart.figures(sf_sweeps, grid),
        *terraform_lcoe_chart.figures(data, grid),
    ]

    if args.count:
        print(f"{len(plan)} charts planned:")
        for name, _ in plan:
            print(f"  - {name}")
        return

    _report(grid, plane, isw, lcsw)

    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")

    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    sys.exit(main())
