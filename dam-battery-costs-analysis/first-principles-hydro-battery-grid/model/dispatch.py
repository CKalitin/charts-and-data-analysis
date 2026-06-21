"""Single-point dispatch: run one (hydro MW, battery MWh) system against the 5-min load
record and return the full per-interval time series for plotting.

Same physics as the sweep (see simulate.py): firm hydro serves load up to its MW cap and
charges the battery with spare capacity; the battery discharges 1:1 to cover any deficit.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import config as cfg


def dispatch(df: pd.DataFrame, hydro_mw: float, battery_mwh: float) -> pd.DataFrame:
    """Return df with per-interval columns: hydro_mw, charge_mw, discharge_mw, soc_mwh,
    served_mw, unserved_mw (all powers in MW; soc in MWh)."""
    dt  = cfg.DT_H
    eff = cfg.BATTERY_ROUNDTRIP_EFF
    Hcap = hydro_mw * dt                      # max hydro energy per interval (MWh)

    load = df["load_mw"].to_numpy()
    n = len(load)

    hydro_p   = np.empty(n)
    charge_p  = np.empty(n)
    dis_p     = np.empty(n)
    soc_arr   = np.empty(n)
    served_p  = np.empty(n)

    soc = battery_mwh                         # commissioned pre-charged (see simulate.py)
    for i in range(n):
        Le = load[i] * dt
        spare   = Hcap - Le if Hcap > Le else 0.0
        deficit = Le - Hcap if Le > Hcap else 0.0

        room = (battery_mwh - soc) / eff
        charge_in = spare if spare < room else room
        if charge_in < 0.0:
            charge_in = 0.0
        soc += charge_in * eff

        dis = deficit if deficit < soc else soc
        soc -= dis

        served_direct = Hcap if Hcap < Le else Le
        hydro_energy = served_direct + charge_in

        hydro_p[i]  = hydro_energy / dt
        charge_p[i] = charge_in / dt
        dis_p[i]    = dis / dt
        served_p[i] = (served_direct + dis) / dt
        soc_arr[i]  = soc

    out = df.copy()
    out["hydro_mw"]     = hydro_p
    out["charge_mw"]    = charge_p
    out["discharge_mw"] = dis_p
    out["served_mw"]    = served_p
    out["unserved_mw"]  = out["load_mw"] - out["served_mw"]
    out["soc_mwh"]      = soc_arr
    return out


def dispatch_summary(disp: pd.DataFrame) -> dict:
    dt = cfg.DT_H
    load_e   = disp["load_mw"].sum()   * dt
    served_e = disp["served_mw"].sum() * dt
    charge_e = disp["charge_mw"].sum() * dt
    return {
        "load_twh":     load_e / 1e6,
        "served_twh":   served_e / 1e6,
        "unserved_pct": (1 - served_e / load_e) * 100,
        "throughput_twh": charge_e / 1e6,
        "equiv_cycles": (charge_e * cfg.BATTERY_ROUNDTRIP_EFF) / max(disp["soc_mwh"].max(), 1e-9),
        "soc_max_gwh":  disp["soc_mwh"].max() / 1e3,
    }


if __name__ == "__main__":
    from data_load import load_bpa_load
    from model.simulate import run_sweep, min_cost_full_point

    df = load_bpa_load()
    res = run_sweep(df["load_mw"].to_numpy())
    pt = min_cost_full_point(res)
    print(f"Dispatching {pt['hydro_mw']:,.0f} MW hydro + {pt['battery_mwh']/1e3:,.1f} GWh battery")
    disp = dispatch(df, pt["hydro_mw"], pt["battery_mwh"])
    s = dispatch_summary(disp)
    for k, v in s.items():
        print(f"  {k:16s}: {v:,.3f}")
