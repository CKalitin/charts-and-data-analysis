"""Vectorised dam + battery sweep.

Given a dam's historic hourly DataFrame, sweeps a grid of
(installed_mw, battery_mwh) and returns 2-D result arrays (N_mw × N_mwh).

Generation model
----------------
Each calendar day:
  - daily_avg_mw  = mean hourly power_mw for that day (from historic data)
  - gen_flat      = min(daily_avg_mw, installed_mw)   [constant for 24 h]
  - capacity_spill = max(0, daily_avg_mw − installed_mw) × 24  [MWh, lost]

Load model
----------
  load[h] = historic hourly power_mw — what must leave the dam each hour.

Battery
-------
  delta[h] = gen_flat[h] − load[h]
  If delta > 0 : charge  → soc += delta × BATTERY_EFFICIENCY
  If delta < 0 : discharge → soc += delta  (negative)
  soc clipped to [0, battery_mwh]
  Overflow (soc > cap) → battery spill; shortfall (soc would go < 0) → unserved.

Returns (via run_sweep)
-----------------------
  mw_vals     : 1-D array shape (N_mw,)
  mwh_vals    : 1-D array shape (N_mwh,)
  slf         : served load fraction      shape (N_mw, N_mwh)
  system_cost : total capex [$]           shape (N_mw, N_mwh)
  lcoe        : $/MWh of served energy    shape (N_mw, N_mwh)
  total_spill : MWh/year                  shape (N_mw, N_mwh)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from model import config as mc


def _prepare(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Return (daily_avg, load_hourly) aligned to complete 24-h days only.

    NaN power_mw values are linearly interpolated before aggregation so that
    a handful of missing hours don't poison an entire day's average.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["date", "hour"])

    # Drop duplicate (date, hour) pairs — some scraped CSVs double-write rows
    df = df.drop_duplicates(subset=["date", "hour"], keep="first")

    # Interpolate NaN power_mw (linear; edge NaNs forward/backfilled)
    df["power_mw"] = (df["power_mw"]
                      .interpolate(method="linear")
                      .ffill()
                      .bfill())

    # Keep only dates with exactly 24 hourly rows
    counts = df.groupby("date")["hour"].count()
    full_dates = counts[counts == 24].index
    df = df[df["date"].isin(full_dates)].sort_values(["date", "hour"])

    daily_avg   = df.groupby("date")["power_mw"].mean().sort_index().to_numpy()
    load_hourly = df["power_mw"].to_numpy()   # length = N_days × 24
    return daily_avg, load_hourly


def run_sweep(df: pd.DataFrame, nameplate_mw: float) -> dict:
    """Sweep (installed_mw, battery_mwh) grid for one dam.

    MW  axis : 0 → nameplate_mw                in N_GRID steps
    MWh axis : 0 → nameplate_mw × MWH_PER_MW  in N_GRID steps

    Dispatch model: each day's historic average power sets a daily energy
    budget (MWh).  The dam runs at full installed capacity until the budget
    is exhausted; any excess goes to the battery.  Battery then covers any
    remaining load.  This is unlike the old flat-power model where output
    was constant throughout the day.
    """
    daily_avg, load_hourly = _prepare(df)
    N_days  = len(daily_avg)
    N_hours = N_days * 24

    mw_vals  = np.linspace(0, nameplate_mw,                     mc.N_GRID)
    mwh_vals = np.linspace(0, nameplate_mw * mc.MWH_PER_MW,    mc.N_GRID)
    N_mw, N_mwh = len(mw_vals), len(mwh_vals)

    # ── Daily generation budget per MW setting ────────────────────────────────
    # gen_daily[d, i] = min(daily_avg[d], mw_vals[i])   shape (N_days, N_mw)
    # = the average power the dam can sustain given the installed capacity
    gen_daily = np.minimum(
        daily_avg[:, np.newaxis],
        mw_vals[np.newaxis, :]
    )
    # daily_budget[d, i] = energy the dam is allowed to produce on day d
    daily_budget = gen_daily * 24   # MWh/day  shape (N_days, N_mw)

    # Capacity spill per day: energy available but capped out by installed MW
    cap_spill_daily = np.maximum(
        daily_avg[:, np.newaxis] - mw_vals[np.newaxis, :], 0
    ) * 24   # shape (N_days, N_mw)

    # ── Vectorised hourly simulation ───────────────────────────────────────────
    # remaining tracks daily budget per (MW, MWh) cell because gen now depends
    # on battery state — throttled to actual absorption (load + battery space).
    # Shape (N_mw, N_mwh) so each cell independently tracks its budget.
    soc           = np.zeros((N_mw, N_mwh))
    total_served  = np.zeros((N_mw, N_mwh))
    battery_spill = np.zeros((N_mw, N_mwh))
    remaining     = np.zeros((N_mw, N_mwh))

    cap = mwh_vals[np.newaxis, :]   # shape (1, N_mwh)

    for h in range(N_hours):
        if h % 24 == 0:
            d = h // 24
            # Each MWh column gets the same MW-axis budget for this day
            remaining[:, :] = daily_budget[d, :, np.newaxis]

        load_h = load_hourly[h]   # scalar

        # Space available in battery (in gen-input units, accounting for eff)
        space = np.maximum(0.0, (cap - soc) / mc.BATTERY_EFFICIENCY)  # (N_mw, N_mwh)

        # Gen = min(turbine_cap, budget_remaining, what load+battery can absorb)
        # Turbine throttles when battery full and load < installed capacity;
        # this ensures no energy is wasted and budget counts only what is used.
        gen_h = np.minimum(
            np.minimum(mw_vals[:, np.newaxis], remaining),
            load_h + space
        )   # (N_mw, N_mwh)

        remaining -= gen_h
        np.maximum(remaining, 0.0, out=remaining)   # guard float errors

        delta        = gen_h - load_h              # (N_mw, N_mwh)
        delta_stored = np.where(delta > 0,
                                delta * mc.BATTERY_EFFICIENCY,
                                delta)

        proposed = soc + delta_stored

        # Overflow should be ~0 due to throttling; kept for float-error guard
        overflow = np.maximum(proposed - cap, 0)
        battery_spill += overflow

        shortfall = np.maximum(-proposed, 0)
        soc       = np.clip(proposed, 0, cap)

        total_served += np.maximum(load_h - shortfall, 0)

    # ── Aggregate ─────────────────────────────────────────────────────────────
    total_load      = load_hourly.sum()                         # MWh/year
    cap_spill_total = cap_spill_daily.sum(axis=0)               # (N_mw,)
    total_spill     = cap_spill_total[:, np.newaxis] + battery_spill  # (N_mw, N_mwh)

    slf = total_served / total_load   # [0, 1]

    # System cost: total capex [$]
    system_cost = (mw_vals[:, np.newaxis]  * mc.DAM_TURBINE_COST_PER_MW
                   + mwh_vals[np.newaxis, :] * mc.BATTERY_COST_PER_MWH)

    # LCOE: annualised cost / annual served energy [$/MWh]
    annual_cost = (mw_vals[:, np.newaxis]  * mc.DAM_ANNUAL_COST_PER_MW
                   + mwh_vals[np.newaxis, :] * mc.BATTERY_ANNUAL_COST_PER_MWH)
    with np.errstate(divide="ignore", invalid="ignore"):
        lcoe = np.where(total_served > 0, annual_cost / total_served, np.nan)

    return {
        "mw_vals":        mw_vals,
        "mwh_vals":       mwh_vals,
        "slf":            slf,
        "system_cost":    system_cost,
        "lcoe":           lcoe,
        "total_spill":    total_spill,
        "total_load_mwh": total_load,
    }


def simulate_single(df: pd.DataFrame, installed_mw: float, battery_mwh: float) -> dict:
    """Single (installed_mw, battery_mwh) simulation returning full hourly time series.

    Uses the same budget-based dispatch as run_sweep: each day the dam runs
    at full installed_mw capacity until its daily energy budget is exhausted.

    Returned arrays are ordered chronologically (same order as _prepare):
        gen         (N_hours,)  actual hourly dispatch (variable within day)
        gen_avg_ref (N_hours,)  daily budget ÷ 24 — reference line for charts
        load        (N_hours,)  historic hourly load
        charge      (N_hours,)  energy stored in battery this hour [MWh]
        discharge   (N_hours,)  energy drawn from battery this hour [MWh]
        shortfall   (N_hours,)  unmet load this hour [MWh]
        dates       (N_hours,)  numpy array of datetime64 dates for grouping
    """
    df_c = df.copy()
    df_c["date"] = pd.to_datetime(df_c["date"])
    df_c = df_c.sort_values(["date", "hour"])
    df_c = df_c.drop_duplicates(subset=["date", "hour"], keep="first")
    df_c["power_mw"] = (df_c["power_mw"]
                        .interpolate(method="linear")
                        .ffill()
                        .bfill())
    counts = df_c.groupby("date")["hour"].count()
    full_dates = counts[counts == 24].index
    df_c = df_c[df_c["date"].isin(full_dates)].sort_values(["date", "hour"])

    daily_avg    = df_c.groupby("date")["power_mw"].mean().sort_index().to_numpy()
    load_hourly  = df_c["power_mw"].to_numpy()
    dates_hourly = df_c["date"].to_numpy()

    N_days  = len(daily_avg)
    N_hours = N_days * 24

    # Per-day budget: min(daily_avg, installed_mw) × 24 MWh
    gen_daily   = np.minimum(daily_avg, installed_mw)   # (N_days,)
    gen_avg_ref = np.repeat(gen_daily, 24)               # reference line for charts

    gen_arr       = np.zeros(N_hours)
    charge_arr    = np.zeros(N_hours)
    discharge_arr = np.zeros(N_hours)
    shortfall_arr = np.zeros(N_hours)

    soc       = 0.0
    cap       = float(battery_mwh)
    remaining = 0.0

    for h in range(N_hours):
        if h % 24 == 0:
            d = h // 24
            remaining = float(gen_daily[d]) * 24   # daily budget (MWh)

        load_h = float(load_hourly[h])
        # Battery absorption capacity (in generation-input terms)
        space = max(0.0, (cap - soc) / mc.BATTERY_EFFICIENCY)
        # Turbine throttles to what load + battery can absorb; budget caps the rest
        gen_h     = max(0.0, min(installed_mw, remaining, load_h + space))
        remaining = max(0.0, remaining - gen_h)
        gen_arr[h] = gen_h

        delta = gen_h - load_h
        if delta >= 0:
            charge = min(delta * mc.BATTERY_EFFICIENCY, cap - soc)
            soc += charge
            charge_arr[h] = charge
        else:
            needed = -delta
            discharge = min(needed, soc)
            soc -= discharge
            discharge_arr[h] = discharge
            shortfall_arr[h] = needed - discharge

    return {
        "gen":         gen_arr,
        "gen_avg_ref": gen_avg_ref,
        "load":        load_hourly,
        "charge":      charge_arr,
        "discharge":   discharge_arr,
        "shortfall":   shortfall_arr,
        "dates":       dates_hourly,
    }


if __name__ == "__main__":
    import time
    import config as cfg
    import derived

    for code in mc.MODEL_DAMS:
        dam = next(d for d in cfg.ALL_DAMS if d.code == code)
        df  = derived.load_dam(dam.csv_path)
        if df.empty:
            print(f"{code}: no data"); continue
        t0 = time.time()
        r  = run_sweep(df, dam.nameplate_mw)
        print(f"{dam.name:20s}  SLF {r['slf'].min():.1%}–{r['slf'].max():.1%}"
              f"  LCOE ${r['lcoe'][~np.isnan(r['lcoe'])].min():,.0f}–"
              f"${r['lcoe'][~np.isnan(r['lcoe'])].max():,.0f}/MWh"
              f"  ({time.time()-t0:.1f}s)")
