"""Configuration for the dam + battery economic model.

Sweep axes:
  MW  : 0 → nameplate_mw          in N_GRID steps
  MWh : 0 → nameplate_mw × 24     in N_GRID steps
"""
from __future__ import annotations

# Dams included in the model sweep (USACE codes)
MODEL_DAMS: list[str] = ["chj", "gcl", "jda", "dwr"]

# ── Capital costs ──────────────────────────────────────────────────────────────
DAM_TURBINE_COST_PER_MW:  float = 3_000_000   # $/MW installed
BATTERY_COST_PER_MWH:     float = 200_000      # $/MWh installed

# ── Amortization ───────────────────────────────────────────────────────────────
DAM_AMORTIZATION_YR:      int   = 50
BATTERY_AMORTIZATION_YR:  int   = 20

# Annualised capital costs (used for LCOE)
DAM_ANNUAL_COST_PER_MW:   float = DAM_TURBINE_COST_PER_MW / DAM_AMORTIZATION_YR
BATTERY_ANNUAL_COST_PER_MWH: float = BATTERY_COST_PER_MWH / BATTERY_AMORTIZATION_YR

# ── Battery ─────────────────────────────────────────────────────────────────────
BATTERY_EFFICIENCY: float = 1.00   # round-trip; applied at charge

# ── Sweep resolution ────────────────────────────────────────────────────────────
N_GRID: int = 100   # points on each axis → N_GRID² simulations per dam

# ── Battery axis max ─────────────────────────────────────────────────────────────
# Max battery size = nameplate_mw × MWH_PER_MW
MWH_PER_MW: int = 3

# ── Monthly breakdown combinations ──────────────────────────────────────────────
# (mw_fraction, mwh_fraction)
# mw_fraction  : fraction of nameplate_mw
# mwh_fraction : fraction of nameplate_mw × MWH_PER_MW  (the MWh axis max)
# Folder names are auto-generated from the actual MW/MWh values at chart time.
MODEL_COMBOS: list[tuple[float, float]] = [
    (1.00, 0.00),   # nameplate MW, no battery
    (0.50, 0.50),   # 50% turbine, 50% battery
    (0.75, 0.25),   # 75% turbine, 25% battery
    (0.25, 0.75),   # 25% turbine, 75% battery
]
