"""Vectorised (firm hydro MW × battery MWh) sweep against BPA 2024 load.

Dispatch model (per 5-minute interval, with load L):
  - Hydro is firm: it can supply up to its MW rating at any instant, no energy limit.
  - If L <= hydro cap : hydro serves all load; spare hydro capacity charges the battery
                        (stored = energy_in * eff).
  - If L >  hydro cap : hydro maxes out; the battery discharges (1:1) to cover the deficit;
                        any remaining deficit is unserved.
  Battery power is unconstrained — only its energy capacity binds.

Because each (hydro, battery) cell is in exactly one regime per interval (set by hydro vs L,
independent of battery size), charge and discharge terms can both be applied every step:
one is always zero.

Returns 2-D arrays over the (N_hydro × N_battery) grid:
  utilization : served energy / total load energy        [0, 1]
  system_cost : total capex [$]
  lcoe        : annualised cost / annual served energy    [$/MWh]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import config as cfg


def run_sweep(load_mw: np.ndarray, *, progress: bool = False) -> dict:
    """Sweep the (hydro MW, battery MWh) grid against a 5-min load series."""
    dt  = cfg.DT_H
    eff = cfg.BATTERY_ROUNDTRIP_EFF

    hydro_vals = np.linspace(0.0, cfg.HYDRO_MW_MAX,   cfg.N_GRID)      # (NH,)
    batt_vals  = np.linspace(0.0, cfg.BATTERY_MWH_MAX, cfg.N_GRID)     # (NB,)
    NH, NB = len(hydro_vals), len(batt_vals)

    hydro_cap_e = hydro_vals[:, None] * dt          # (NH,1) max hydro energy / interval
    batt_cap    = batt_vals[None, :]                # (1,NB) energy cap

    # Commission the battery pre-charged (start at full) — a sized system would be, and it
    # avoids a one-time startup charging transient. Negligible vs annual energy either way.
    soc    = np.broadcast_to(batt_vals, (NH, NB)).astype(float).copy()
    served = np.zeros((NH, NB))

    t0 = time.time()
    n  = len(load_mw)
    for i, L in enumerate(load_mw):
        Le = L * dt                                  # load energy this interval (scalar)
        spare   = np.maximum(hydro_cap_e - Le, 0.0)  # (NH,1) hydro left to charge
        deficit = np.maximum(Le - hydro_cap_e, 0.0)  # (NH,1) shortfall hydro can't cover

        # Charge: draw spare hydro to fill remaining battery room (room measured at input)
        room      = np.maximum(batt_cap - soc, 0.0) / eff   # (NH,NB) energy_in to fill
        charge_in = np.minimum(spare, room)                 # (NH,NB)
        soc += charge_in * eff

        # Discharge: cover deficit from stored energy (1:1)
        dis = np.minimum(deficit, soc)                      # (NH,NB)
        soc -= dis

        served += np.minimum(hydro_cap_e, Le) + dis         # direct + battery
        if progress and i % 20000 == 0:
            print(f"    step {i:,}/{n:,}  ({time.time()-t0:.1f}s)")

    total_load = float(load_mw.sum() * dt)           # MWh/yr
    utilization = served / total_load                # (NH,NB) in [0,1]

    system_cost = (hydro_vals[:, None] * cfg.HYDRO_COST_PER_MW
                   + batt_vals[None, :] * cfg.BATTERY_COST_PER_MWH)        # $
    annual_cost = (hydro_vals[:, None] * cfg.HYDRO_ANNUAL_COST_PER_MW
                   + batt_vals[None, :] * cfg.BATTERY_ANNUAL_COST_PER_MWH)
    with np.errstate(divide="ignore", invalid="ignore"):
        lcoe = np.where(served > 0, annual_cost / served, np.nan)

    return {
        "hydro_vals":  hydro_vals,
        "batt_vals":   batt_vals,
        "utilization": utilization,
        "system_cost": system_cost,
        "lcoe":        lcoe,
        "served":      served,
        "total_load_mwh": total_load,
        "elapsed_s":   time.time() - t0,
    }


def min_cost_full_point(results: dict) -> dict:
    """Cheapest (hydro MW, battery MWh) grid cell that serves >= FULL_SERVED_THRESHOLD."""
    util = results["utilization"]
    cost = results["system_cost"]
    mask = util >= cfg.FULL_SERVED_THRESHOLD
    if not mask.any():
        # Fall back to the highest-utilization cell if nothing hits the threshold.
        idx = np.unravel_index(np.argmax(util), util.shape)
    else:
        masked_cost = np.where(mask, cost, np.inf)
        idx = np.unravel_index(np.argmin(masked_cost), masked_cost.shape)
    i_h, i_b = int(idx[0]), int(idx[1])
    return {
        "i_hydro": i_h,
        "i_batt":  i_b,
        "hydro_mw":  float(results["hydro_vals"][i_h]),
        "battery_mwh": float(results["batt_vals"][i_b]),
        "utilization": float(util[i_h, i_b]),
        "system_cost": float(cost[i_h, i_b]),
        "lcoe":        float(results["lcoe"][i_h, i_b]),
    }


if __name__ == "__main__":
    from data_load import load_bpa_load

    df = load_bpa_load()
    print(f"Sweeping {cfg.N_GRID}x{cfg.N_GRID} grid over {len(df):,} intervals...")
    res = run_sweep(df["load_mw"].to_numpy(), progress=True)
    print(f"  done in {res['elapsed_s']:.1f}s  "
          f"| utilization {res['utilization'].min():.1%}-{res['utilization'].max():.1%}")
    pt = min_cost_full_point(res)
    print(f"\nMin-cost 100%-served point:")
    print(f"  hydro   : {pt['hydro_mw']:,.0f} MW")
    print(f"  battery : {pt['battery_mwh']/1e3:,.1f} GWh")
    print(f"  util    : {pt['utilization']:.4%}")
    print(f"  capex   : ${pt['system_cost']/1e9:,.1f} B")
    print(f"  LCOE    : ${pt['lcoe']:,.1f}/MWh")
