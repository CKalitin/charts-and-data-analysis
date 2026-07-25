"""Derived quantities: base-100 real indices per city, and the house-price/wage decoupling gap.

Everything here operates on the tidy panel from data_load.build_panel() -- one place, so a
chart never recomputes an index differently than another chart.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

import config as cfg


def add_indices(panel: pd.DataFrame, base_year: int | None = None) -> pd.DataFrame:
    """Adds house_price_index / wage_index (base_year = 100) and decoupling_gap_pp
    (cumulative house-price growth minus cumulative wage growth, in percentage points)."""
    base_year = cfg.START_YEAR if base_year is None else base_year
    out = panel.copy()
    for col, idx_col in [("house_price_real", "house_price_index"),
                         ("wage_real", "wage_index")]:
        base_by_city = out.loc[out["year"] == base_year].set_index("city")[col]
        out[idx_col] = out[col] / out["city"].map(base_by_city) * 100.0
    out["decoupling_gap_pp"] = out["house_price_index"] - out["wage_index"]
    return out


def latest_year_ranking(indexed: pd.DataFrame) -> pd.DataFrame:
    """One row per city: cumulative real house-price growth, wage growth, and the gap,
    at the last year common to all cities. Sorted by gap, descending (most decoupled first)."""
    last_year = indexed["year"].max()
    snap = indexed[indexed["year"] == last_year].copy()
    snap["house_price_growth_pct"] = snap["house_price_index"] - 100.0
    snap["wage_growth_pct"] = snap["wage_index"] - 100.0
    return snap.sort_values("decoupling_gap_pp", ascending=False).reset_index(drop=True)
