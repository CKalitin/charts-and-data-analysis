"""All tunables for the Grand Coulee generation-profile analysis.

Paths, constants, the label/unit registry, and presentation knobs live here — nothing
tunable is hardcoded at a call site. Charts import `axis_label(name)` so a variable's
unit string is single-sourced and can never be silently mismatched between two charts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# --- Paths ------------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"
BPA_OUTPUT_DIR = OUTPUT_DIR / "bpa"   # BPA is a grid system, not a single dam
BPA_RAW_CSV = DATA_DIR / "bpa_5min_2024.csv"

# --- Domain constants -------------------------------------------------------------------
USACE_YEAR = 2023
BPA_YEAR = 2024

SOURCE_USACE = "Source: USACE Northwestern Division, 2023"
SOURCE_BPA = "Source: Bonneville Power Administration, 2024"


# --- Dam registry — add new dams here, nowhere else ------------------------------------
_LEGACY_CODES: frozenset[str] = frozenset()


@dataclass
class DamConfig:
    """All per-dam parameters.  Chart modules accept a DamConfig; run.py iterates ALL_DAMS."""
    code: str           # USACE project code  ("gcl", "bon")
    slug: str           # filename / folder prefix  ("grand_coulee", "bonneville")
    name: str           # display name for chart titles
    nameplate_mw: int   # installed capacity (MW)
    year: int = USACE_YEAR

    @property
    def csv_path(self) -> Path:
        if self.code in _LEGACY_CODES:
            return DATA_DIR / f"{self.slug}_hourly_{self.year}.csv"
        return DATA_DIR / "bpa_dams" / f"{self.slug}_hourly_{self.year}.csv"

    @property
    def output_dir(self) -> Path:
        return OUTPUT_DIR / "bpa_dams" / self.slug


GCL = DamConfig(code="gcl", slug="grand_coulee", name="Grand Coulee", nameplate_mw=6809)
BON = DamConfig(code="bon", slug="bonneville",   name="Bonneville",   nameplate_mw=1093)

# fmt: off
ALL_DAMS: list[DamConfig] = [
    GCL,
    BON,
    DamConfig(code="chj", slug="chief_joseph",    name="Chief Joseph",     nameplate_mw=2614),
    DamConfig(code="jda", slug="john_day",         name="John Day",         nameplate_mw=2484),
    DamConfig(code="tda", slug="the_dalles",       name="The Dalles",       nameplate_mw=2048),
    DamConfig(code="mcn", slug="mcnary",           name="McNary",           nameplate_mw=1127),
    DamConfig(code="lgs", slug="little_goose",     name="Little Goose",     nameplate_mw=930),
    DamConfig(code="lwg", slug="lower_granite",    name="Lower Granite",    nameplate_mw=930),
    DamConfig(code="lmn", slug="lower_monumental", name="Lower Monumental", nameplate_mw=930),
    DamConfig(code="ihr", slug="ice_harbor",       name="Ice Harbor",       nameplate_mw=695),
    DamConfig(code="lib", slug="libby",            name="Libby",            nameplate_mw=605),
    DamConfig(code="dwr", slug="dworshak",         name="Dworshak",         nameplate_mw=460),
    DamConfig(code="hgh", slug="hungry_horse",     name="Hungry Horse",     nameplate_mw=428),
    DamConfig(code="lop", slug="lookout_point",    name="Lookout Point",    nameplate_mw=138),
    DamConfig(code="det", slug="detroit",          name="Detroit",          nameplate_mw=126),
    DamConfig(code="gpr", slug="green_peter",      name="Green Peter",      nameplate_mw=92),
    DamConfig(code="los", slug="lost_creek",       name="Lost Creek",       nameplate_mw=56),
    DamConfig(code="alf", slug="albeni_falls",     name="Albeni Falls",     nameplate_mw=49),
    DamConfig(code="hcr", slug="hills_creek",      name="Hills Creek",      nameplate_mw=34),
    DamConfig(code="cgr", slug="cougar",           name="Cougar",           nameplate_mw=28),
    DamConfig(code="fos", slug="foster",           name="Foster",           nameplate_mw=23),
    DamConfig(code="bcl", slug="big_cliff",        name="Big Cliff",        nameplate_mw=23),
    DamConfig(code="dex", slug="dexter",           name="Dexter",           nameplate_mw=17),
]
# fmt: on

# Convenience aliases kept for any code that references them directly.
GCL_NAMEPLATE_MW = GCL.nameplate_mw
BON_NAMEPLATE_MW = BON.nameplate_mw
GCL_CSV = GCL.csv_path
BON_CSV = BON.csv_path

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
    ("nuclear_mw", "Nuclear", "#5d04b7"),
    ("fossil_mw", "Fossil / Biomass", "#db2117"),
    ("hydro_mw", "Hydro", "#167aed"),
    ("wind_mw", "Wind", "#3cc532"),
    ("solar_mw", "Solar", "#f5b700"),
]

# --- Per-dam power profile chart --------------------------------------------------------
# Days for the stacked hourly power chart (uses USACE_YEAR data).
DAM_POWER_QUARTER_DAYS: list[tuple[str, str]] = [
    (f"{USACE_YEAR}-01-01", "Q1 · Jan 1"),
    (f"{USACE_YEAR}-04-01", "Q2 · Apr 1"),
    (f"{USACE_YEAR}-07-01", "Q3 · Jul 1"),
    (f"{USACE_YEAR}-10-01", "Q4 · Oct 1"),
]
DAM_POWER_CUSTOM_DAYS: list[str] = [
    f"{USACE_YEAR}-05-16",
    f"{USACE_YEAR}-07-15",
]
DAM_POWER_TOP_N: int = 9   # show this many dams individually; rest → "Other"

# --- BPA day-profile tool ---------------------------------------------------------------
BPA_DAY_PROFILE_DAYS: list[str] = [
    "2024-05-16",
    "2024-07-15",
]

# --- USACE dam day-profile inspection tool ----------------------------------------------
# Each entry is (dam_code, "YYYY-MM-DD"). Mix dams freely.
DAY_PROFILE_DAYS: list[tuple[str, str]] = [
    # Quarter snapshots (Jan 1, Apr 1, Jul 1, Oct 1)
    ("gcl", "2023-01-01"), ("gcl", "2023-04-01"), ("gcl", "2023-07-01"), ("gcl", "2023-10-01"),
    ("bon", "2023-01-01"), ("bon", "2023-04-01"), ("bon", "2023-07-01"), ("bon", "2023-10-01"),
    ("chj", "2023-01-01"), ("chj", "2023-04-01"), ("chj", "2023-07-01"), ("chj", "2023-10-01"),
    ("jda", "2023-01-01"), ("jda", "2023-04-01"), ("jda", "2023-07-01"), ("jda", "2023-10-01"),
    # Custom days
    ("gcl", "2023-05-16"), ("gcl", "2023-07-15"),
    ("bon", "2023-05-16"), ("bon", "2023-07-15"),
    ("chj", "2023-05-16"), ("chj", "2023-07-15"),
    ("jda", "2023-05-16"), ("jda", "2023-07-15"),
]
DAY_PROFILE_MODE: str = "individual"   # "overlay" | "individual" | "both"
DAY_PROFILE_MONTHLY_DAMS: list[str] = ["gcl", "bon", "chj", "jda"]

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
