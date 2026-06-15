"""All tunables for the solar+battery generic-use-case model, in one place.

Nothing tunable is hardcoded at a call site. The economic schema this whole
project is built around:

    profit_per_year(S, B) = income_per_kWh · served_kWh(S, B)
                          − solar_cost_ann  · S          [$/(kW·yr) · kW]
                          − battery_cost_ann · B         [$/(kWh·yr) · kWh]
                          − load_cost_ann   · L          [$/(kW·yr) · kW, default 0]

`served_kWh(S, B)` is pure physics (independent of every price), so it is
computed ONCE over the (solar kW × battery kWh) grid and cached; every
optimization below is then a cheap argmax over that single grid.

Costs are *annualized*: a one-time capex is divided by the amortization period
to get a $/(kW·yr) figure directly comparable to annual income. Raw capex is
recoverable as annualized × amortization_years (shown on chart twin axes).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "nsrdb_data"
OUTPUT_ROOT = PROJECT_DIR / "outputs"
CACHE_DIR = PROJECT_DIR / ".cache"

DATA_FILE = DATA_DIR / "nsrdb_836224_2024.csv"

# Per-chart-family output subdirectories (keep outputs/ navigable, never a flat dump).
OUT_COST_PLANE = OUTPUT_ROOT / "cost_plane"
OUT_UTIL_VS_INCOME = OUTPUT_ROOT / "utilization_vs_income"
OUT_BUILD_PLANE = OUTPUT_ROOT / "build_plane"
OUT_TIMESERIES = OUTPUT_ROOT / "timeseries"
OUT_UTIL_VS_LOAD_CAPEX = OUTPUT_ROOT / "util_vs_load_capex"
OUT_LOAD_PLANE = OUTPUT_ROOT / "load_plane"

# --------------------------------------------------------------------------- #
# Physics
# --------------------------------------------------------------------------- #
REFERENCE_IRRADIANCE_W_M2 = 1000.0   # GHI at which a panel makes nameplate (STC)
ROUND_TRIP_EFFICIENCY = 0.90         # battery round-trip efficiency, (0, 1]
LOAD_KW = 1.0                        # constant load the system serves

# Steady-state (circular) warm-start: iterate year-end SOC -> year-start SOC to
# a fixed point so there is no empty-battery artifact on Jan 1. This is what lets
# utilization exceed 99.8% instead of being capped by the first cold day.
WARMSTART_MAX_ITERS = 8
WARMSTART_TOL = 1e-4                 # converged when max |ΔSOC| / capacity < tol

# Optional time downsampling for the heavy served-grid sweep (None = native
# 10-min resolution; "1h" etc. speeds up the one-time grid build). The
# single-config time-series chart always uses native resolution.
SWEEP_DT_RESAMPLE: str | None = None

# --------------------------------------------------------------------------- #
# Economics — capex inputs + amortization (forward-looking costs)
# --------------------------------------------------------------------------- #
SOLAR_CAPEX_PER_KW = 200.0           # $/kW one-time
BATTERY_CAPEX_PER_KWH = 200.0        # $/kWh one-time
AMORTIZATION_YEARS = 20.0            # years the solar + battery hardware earns income


def annualize(capex: float | np.ndarray) -> float | np.ndarray:
    """Capex ($/kW or $/kWh) -> annualized cost ($/(kW·yr) or $/(kWh·yr))."""
    return np.asarray(capex, dtype=float) / AMORTIZATION_YEARS


# Annualized component costs used as the default operating point.
SOLAR_COST_ANN = float(annualize(SOLAR_CAPEX_PER_KW))      # $/(kW·yr)
BATTERY_COST_ANN = float(annualize(BATTERY_CAPEX_PER_KWH))  # $/(kWh·yr)

# Default load income ($ earned per kWh actually delivered to the load).
INCOME_PER_KWH = 0.10

# Load capex — cost of the load equipment itself, amortized separately.
# Default 0 so all existing charts are unchanged; set to model specific applications.
LOAD_CAPEX_PER_KW = 0.0             # $/kW one-time (0 = pure income analysis)
LOAD_AMORTIZATION_YEARS = 10.0      # years the load equipment operates


def annualize_load(capex: float | np.ndarray) -> float | np.ndarray:
    return np.asarray(capex, dtype=float) / LOAD_AMORTIZATION_YEARS


LOAD_COST_ANN = float(annualize_load(LOAD_CAPEX_PER_KW))   # $/(kW·yr), default 0

# Named load cases (income $/kWh, load_capex $/kW, load_amort_years).
# Marked as reference points on the load-plane chart.
LOAD_CASES: dict[str, tuple[float, float, int]] = {
    "Terraform Electrolyzer": (0.0125,    50.0, 5),
    "Colossus 1 Data Center":   (5.0,   28_000.0, 5),
    "NaOH Electrolyzer":      (0.16,     400.0, 5),
}

# --------------------------------------------------------------------------- #
# Inner optimization grid: solar nameplate (kW) × battery capacity (kWh)
# --------------------------------------------------------------------------- #
# Ranges must be generous enough that the profit-maximizing build does not clip
# the grid edge at cheap-cost / high-income corners (charts flag it if it does).
KW_SOLAR_GRID = np.round(np.arange(0.0, 50.0 + 1e-9, 0.05), 6)     # 0–50 kW
KWH_BATTERY_GRID = np.round(np.arange(0.0, 50.0 + 1e-9, 0.05), 6)   # 0–50 kWh

# NOTE CHRIS!!
# I've precomputed 50x50 grid at 0.5 resolution and at 0.05 resolution.
# They take 22.2 and 135.2 seconds respectively.
# Took 50 minutes for the 0.05 grid with 10-min data! On my Victus R5 7535HS Laptop.

# --------------------------------------------------------------------------- #
# Chart A — cost plane sweep (x: battery $/(kWh·yr), y: solar $/(kW·yr))
# Income held fixed at INCOME_PER_KWH; each cell re-optimizes the build.
# --------------------------------------------------------------------------- #
SOLAR_COST_ANN_SWEEP = np.logspace(0, np.log10(300.0), 90)    # $1 – $300 /(kW·yr)
BATT_COST_ANN_SWEEP = np.logspace(0, np.log10(300.0), 90)     # $1 – $300 /(kWh·yr)

# --------------------------------------------------------------------------- #
# Chart B — optimal utilization vs load income ($/kWh).
# Solar & battery costs held fixed at SOLAR_COST_ANN / BATTERY_COST_ANN.
# --------------------------------------------------------------------------- #
INCOME_SWEEP = np.logspace(-3, 1, 200)   # $0.001 – $10 /kWh

# Chart C — optimal utilization vs load capex ($/kW·yr annualized).
# Income & solar/battery costs held fixed.
LOAD_COST_ANN_SWEEP = np.logspace(-1, 4, 200)   # $0.1 – $10,000 /(kW·yr)

# Chart D — load plane: income (y) × load capex (x), both log-scale.
# Covers Terraform ($50/kW, $0.0125/kWh) through Colossus ($28 k/kW, $5/kWh).
LOAD_CAPEX_RAW_SWEEP = np.logspace(0, 5, 100)       # $1 – $100,000 /kW raw capex
LOAD_PLANE_INCOME_SWEEP = np.logspace(-3, 1, 100)   # $0.001 – $10 /kWh

# Chart E — LCOE and utilization vs solar fraction.
# Holds total hardware (kW solar + kWh battery) constant at each T value;
# sweeps α = solar fraction from 0 (pure battery) to 1 (pure solar).
# Assumption: C_S [$/kW·yr] = C_B [$/kWh·yr] — then "unit fraction = cost
# fraction" and LCOE = C × T / served, so the chart is the inverse of
# the utilization curve.
SOLAR_FRACTION_ALPHA = np.linspace(0.01, 1.0, 1000)  # skip 0 (served=0, LCOE=∞)
SOLAR_FRACTION_TOTAL_UNITS = [4.0, 8.0, 16.0, 24.0]  # kW+kWh total resource
OUT_SOLAR_FRACTION = OUTPUT_ROOT / "solar_fraction"
OUT_WEEKLY_TIMESERIES = OUTPUT_ROOT / "weekly_timeseries"
OUT_DAILY_TIMESERIES  = OUTPUT_ROOT / "daily_timeseries"

# --------------------------------------------------------------------------- #
# Time-series chart — one representative build to visualize dispatch.
# --------------------------------------------------------------------------- #
TS_KW_SOLAR = 6.0
TS_KWH_BATTERY = 12.0

# Attribution shown on every chart.
WATERMARK_TEXT = "Christopher Kalitin 2026"
