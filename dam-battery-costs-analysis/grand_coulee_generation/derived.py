"""Derived quantities — the single place aggregations and ratios are computed.

Every division is guarded to yield NaN (never inf) on an idle/zero denominator, and NaNs
are dropped before they reach a chart. Loaders that find no data return an empty frame so
callers can skip cleanly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config as cfg
import schema


# --- USACE dam derivations --------------------------------------------------------------
def with_time_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Attach hour / month / season columns from the datetime index column."""
    out = df.copy()
    out["hour"] = out["datetime"].dt.hour
    out["month"] = out["datetime"].dt.month
    out["season"] = out["month"].map(cfg.SEASON_BY_MONTH)
    return out


def load_dam(path) -> pd.DataFrame:
    """Load + time-decorate a scraped dam CSV. Empty frame if the file is missing."""
    if not path.exists():
        return pd.DataFrame()
    return with_time_cols(schema.load_usace(path))


def diurnal_by_season(df: pd.DataFrame) -> pd.DataFrame:
    """Mean power_mw by (hour × season). Columns ordered per cfg.SEASON_ORDER."""
    table = df.groupby(["hour", "season"])["power_mw"].mean().unstack("season")
    return table.reindex(columns=cfg.SEASON_ORDER)


def annual_diurnal(df: pd.DataFrame) -> pd.Series:
    """Annual-average power_mw by hour of day (0..23)."""
    return df.groupby("hour")["power_mw"].mean()


def daily_mean_power(df: pd.DataFrame) -> pd.Series:
    """Daily-average power_mw indexed by calendar day."""
    return df.set_index("datetime")["power_mw"].resample("D").mean()


def monthly_capacity_factor(df: pd.DataFrame, nameplate_mw: float) -> pd.Series:
    """Monthly mean power / nameplate, indexed 1..12."""
    return df.groupby("month")["power_mw"].mean() / nameplate_mw


def monthly_spill_fraction(df: pd.DataFrame) -> pd.Series:
    """Volume-weighted monthly spill fraction = Σ spill / Σ total_outflow, indexed 1..12.

    Volume-weighted (not a mean of per-hour ratios) so low-flow hours with tiny
    denominators cannot dominate; the denominator is guarded to NaN if a month is dry.
    """
    g = df.groupby("month")[["spill_kcfs", "total_outflow_kcfs"]].sum()
    denom = g["total_outflow_kcfs"].replace(0, np.nan)
    return g["spill_kcfs"] / denom


# --- BPA system derivations -------------------------------------------------------------
def load_bpa() -> pd.DataFrame:
    """Load the canonical BPA 5-minute frame. Empty frame if the file is missing."""
    if not cfg.BPA_RAW_CSV.exists():
        return pd.DataFrame()
    return schema.load_bpa(cfg.BPA_RAW_CSV)


def bpa_day(bpa: pd.DataFrame, day: str) -> pd.DataFrame:
    """All 5-minute rows for a single calendar day, with an `hours` axis (0..24)."""
    d = pd.Timestamp(day)
    mask = (bpa["datetime"] >= d) & (bpa["datetime"] < d + pd.Timedelta(days=1))
    out = bpa.loc[mask].copy()
    out["hours"] = (out["datetime"] - d).dt.total_seconds() / 3600.0
    return out


def net_generation(df: pd.DataFrame) -> pd.Series:
    """Total generation = sum of all generation-type columns (MW)."""
    cols = [c for c, _, _ in cfg.GEN_TYPES]
    return df[cols].sum(axis=1)


def demand(df: pd.DataFrame) -> pd.Series:
    """Load + net exports (MW) — what the balancing authority must serve.

    Net interchange is positive when BPA is a net exporter, so this is the total
    obligation met by in-area generation.
    """
    return df["load_mw"] + df["net_interchange_mw"]
