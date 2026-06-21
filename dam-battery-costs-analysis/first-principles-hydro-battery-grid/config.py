"""All tunables for the first-principles BPA hydro + battery sizing analysis.

We take BPA's 2024 native control-area load (5-minute resolution, exports excluded)
and ask: across a grid of (firm hydro MW, battery MWh), how much of that load can a
hydro + battery system serve, what does it cost, and what is the resulting LCOE?

Nothing tunable is hardcoded at a call site — paths, costs, grid bounds, the dispatch
assumptions, and the label registry all live here.
"""
from __future__ import annotations

from pathlib import Path

# --- Paths ------------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR    = PROJECT_DIR / "data"
OUTPUT_DIR  = PROJECT_DIR / "outputs"
RAW_CSV     = DATA_DIR / "bpa_5min_2024.csv"

YEAR = 2024
SOURCE_BPA = "Source: Bonneville Power Administration, 2024"

# Column in the raw BPA file holding native control-area load (selected by substring).
LOAD_COL_SUBSTR = "BPA CONTROL AREA LOAD"
INTERVAL_MIN = 5                      # raw data resolution (minutes)
DT_H = INTERVAL_MIN / 60.0           # hours per interval (energy = MW * DT_H)

# --- Capital costs ----------------------------------------------------------------------
HYDRO_COST_PER_MW:   float = 3_000_000     # $/MW installed (firm dispatchable hydro)
BATTERY_COST_PER_MWH: float = 200_000      # $/MWh installed

# --- Amortization (for LCOE) ------------------------------------------------------------
HYDRO_AMORTIZATION_YR:   int = 50
BATTERY_AMORTIZATION_YR: int = 20
HYDRO_ANNUAL_COST_PER_MW:    float = HYDRO_COST_PER_MW   / HYDRO_AMORTIZATION_YR
BATTERY_ANNUAL_COST_PER_MWH: float = BATTERY_COST_PER_MWH / BATTERY_AMORTIZATION_YR

# --- Battery -----------------------------------------------------------------------------
# Round-trip efficiency, applied at charge: stored = energy_in * eff, discharge is 1:1.
# Battery power is unconstrained (energy-capped only).
BATTERY_ROUNDTRIP_EFF: float = 0.87

# --- Hydro model -------------------------------------------------------------------------
# Hydro is a firm dispatchable resource: it can produce up to its MW rating at any instant
# with NO seasonal/annual energy limit. The battery only time-shifts within the record.

# --- Sweep grid --------------------------------------------------------------------------
HYDRO_MW_MAX:  float = 20_000        # MW   (Y axis: 0 -> 20 GW)
BATTERY_MWH_MAX: float = 200_000     # MWh  (X axis: 0 -> 200 GWh)
N_GRID: int = 100                    # points per axis -> N_GRID**2 sims

# Utilization at/above this counts as "fully served" when picking the min-cost design point.
FULL_SERVED_THRESHOLD: float = 0.9999

# --- Snapshot days / months for the dispatch time series --------------------------------
QUARTER_DAYS = [
    (f"{YEAR}-01-01", "Q1 · Jan 1"),
    (f"{YEAR}-04-01", "Q2 · Apr 1"),
    (f"{YEAR}-07-01", "Q3 · Jul 1"),
    (f"{YEAR}-10-01", "Q4 · Oct 1"),
]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# --- Presentation ------------------------------------------------------------------------
CMAP = "inferno"
COLOR_LOAD      = "#111111"
COLOR_HYDRO     = "#167aed"
COLOR_DISCHARGE = "#3cc532"
COLOR_CHARGE    = "#f5b700"
COLOR_SOC       = "#9467bd"

_LABELS = {
    "power_mw":   "Power (MW)",
    "energy_gwh": "Energy (GWh/day)",
    "hydro_gw":   "Installed hydro capacity (GW)",
    "battery_gwh": "Battery energy capacity (GWh)",
    "soc_gwh":    "Battery state of charge (GWh)",
}


def axis_label(name: str) -> str:
    return _LABELS.get(name, name)
