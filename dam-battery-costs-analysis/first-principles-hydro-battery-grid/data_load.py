"""Load BPA native control-area load (5-minute, 2024) → a clean DataFrame.

The raw file has a one-line banner above the header row, US-format local timestamps,
and a few sparse NaNs. We return a sorted, de-duplicated, gap-filled series of
(datetime, load_mw) at 5-minute resolution — the single input to the whole analysis.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

import config as cfg


def load_bpa_load(path: Path | str = cfg.RAW_CSV) -> pd.DataFrame:
    """Return DataFrame[datetime, load_mw] at 5-min resolution, NaNs interpolated."""
    raw = pd.read_csv(path, skiprows=1)

    load_col = next(c for c in raw.columns if cfg.LOAD_COL_SUBSTR in c)
    dt = pd.to_datetime(raw["Date/Time"], format="%m/%d/%y %H:%M", errors="coerce")
    load = pd.to_numeric(raw[load_col], errors="coerce")

    df = pd.DataFrame({"datetime": dt, "load_mw": load})
    df = df.dropna(subset=["datetime"]).drop_duplicates(subset=["datetime"], keep="first")
    df = df.sort_values("datetime").reset_index(drop=True)

    # Fill the handful of sparse NaN load values so the dispatch loop is gap-free.
    df["load_mw"] = df["load_mw"].interpolate(method="linear").ffill().bfill()
    return df


def load_stats(df: pd.DataFrame) -> dict:
    load = df["load_mw"].to_numpy()
    return {
        "n":         len(load),
        "min_mw":    float(load.min()),
        "mean_mw":   float(load.mean()),
        "peak_mw":   float(load.max()),
        "twh":       float(load.sum() * cfg.DT_H / 1e6),
    }


if __name__ == "__main__":
    df = load_bpa_load()
    s = load_stats(df)
    print(f"rows : {s['n']:,}")
    print(f"span : {df['datetime'].iloc[0]} -> {df['datetime'].iloc[-1]}")
    print(f"min  : {s['min_mw']:,.0f} MW")
    print(f"mean : {s['mean_mw']:,.0f} MW")
    print(f"peak : {s['peak_mw']:,.0f} MW")
    print(f"total: {s['twh']:,.2f} TWh/yr")
