"""All tunables for the Grand Coulee generation-profile analysis.

Paths, constants, the label/unit registry, and presentation knobs live here — nothing
tunable is hardcoded at a call site. Charts import `axis_label(name)` so a variable's
unit string is single-sourced and can never be silently mismatched between two charts.
"""

from __future__ import annotations

from pathlib import Path

# --- Paths ------------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"

GCL_CSV = DATA_DIR / "grand_coulee_hourly_2023.csv"
BON_CSV = DATA_DIR / "bonneville_hourly_2023.csv"
# The 5-minute BPA system file the user supplied lives one level up. It is 2024 data
# (the only year provided), so every BPA-derived chart is labelled 2024, not 2023.
BPA_RAW_CSV = PROJECT_DIR.parent / "bpa_5min_2024.csv"

# --- Domain constants -------------------------------------------------------------------
USACE_YEAR = 2023
BPA_YEAR = 2024
GCL_NAMEPLATE_MW = 6809          # Grand Coulee installed capacity

SOURCE_USACE = "Source: USACE Northwestern Division, 2023"
SOURCE_BPA = "Source: Bonneville Power Administration, 2024"

# Season map (meteorological) — shared by every seasonal aggregation.
SEASON_BY_MONTH = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Fall", 10: "Fall", 11: "Fall",
}
SEASON_ORDER = ["Winter", "Spring", "Summer", "Fall"]
SEASON_COLOR = {            # plasma-derived, distinct and print-safe
    "Winter": "#0d0887",
    "Spring": "#9c179e",
    "Summer": "#ed7953",
    "Fall": "#f0f921",
}

# First day of each calendar quarter — the BPA "snapshot days" the user asked for.
QUARTER_DAYS = [
    (f"{BPA_YEAR}-01-01", "Q1 · Jan 1"),
    (f"{BPA_YEAR}-04-01", "Q2 · Apr 1"),
    (f"{BPA_YEAR}-07-01", "Q3 · Jul 1"),
    (f"{BPA_YEAR}-10-01", "Q4 · Oct 1"),
]
QUARTER_DAY_COLOR = {       # tab10, one per snapshot day
    "Q1 · Jan 1": "#1f77b4",
    "Q2 · Apr 1": "#2ca02c",
    "Q3 · Jul 1": "#d62728",
    "Q4 · Oct 1": "#ff7f0e",
}

# BPA generation-by-type registry: canonical column -> (display label, color).
# Ordered low→high in the typical stack (baseload at the bottom).
GEN_TYPES = [
    ("nuclear_mw", "Nuclear", "#7f3fbf"),
    ("hydro_mw", "Hydro", "#1f77b4"),
    ("fossil_mw", "Fossil / Biomass", "#8c564b"),
    ("wind_mw", "Wind", "#2ca02c"),
    ("solar_mw", "Solar", "#f5b700"),
]

# --- Label / unit registry (single source of truth) ------------------------------------
_LABELS = {
    "hour": "Hour of day (Pacific)",
    "power_mw": "Power output (MW)",
    "capacity_factor": "Capacity factor",
    "spill_fraction": "Spill fraction of total outflow",
    "month": "Month",
    "datetime": "Date",
    "generation_mw": "Generation (MW)",
    "demand_mw": "Load + net exports (MW)",
}


def axis_label(name: str) -> str:
    """Return the canonical axis label for a variable name. Never hand-type a unit string."""
    return _LABELS.get(name, name)
