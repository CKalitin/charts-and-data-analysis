"""All tunables for the penicillin learning-curve analysis. Nothing tunable lives at a call site."""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_ROOT = PROJECT_DIR / "outputs"

US_PRODUCTION_CSV = DATA_DIR / "us_production.csv"
US_PRICES_CSV = DATA_DIR / "us_prices.csv"
WORLD_ANCHORS_CSV = DATA_DIR / "world_production_anchors.csv"
WORLD_PRICES_CSV = DATA_DIR / "world_prices.csv"
DERIVED_CSV = OUTPUT_ROOT / "derived_series.csv"
FIT_SUMMARY_CSV = OUTPUT_ROOT / "fit_summary.csv"

# --- Unit conversions ---------------------------------------------------------------------
# 1 BU (a.k.a. BOU) = 1e9 international (Oxford) units of penicillin activity.
# Potassium penicillin G, theoretical 1,595 units/mg  ->  1 BOU = 0.627 kg, 1.595 BOU/kg.
# (United Laboratories: "1 BOU = 0.63 kg"; BusinessToday: "roughly 1.6 BOU = 1 kg".)
BU_PER_KG_K_SALT = 1.595
BU_PER_TONNE = BU_PER_KG_K_SALT * 1000.0

# US Tariff Commission switched from billions of units to pounds in 1976. Their conversion
# factors were salt-specific (procaine 458 M units/lb, K salt 723 M units/lb, Pen V 769 M/lb),
# so we calibrate the MIX from the last years reported in both units (1974, 1975):
#   production: 670.7 and 646.8 M units/lb   sales: 627.2 and 606.3 M units/lb
BU_PER_KLB_PRODUCTION = (670.7 + 646.8) / 2      # BU per 1,000 lb
BU_PER_KLB_SALES = (627.2 + 606.3) / 2
# SOC-1948: 64.6 trillion units sold = 108,300 lb  -> 0.5965 BU/lb (used for the 1950 $/lb quote)
BU_PER_LB_1948 = 64_600 / 108_300

# --- Inflation ---------------------------------------------------------------------------
CPI_BASIS_YEAR = 2025

# --- Fit selection -------------------------------------------------------------------------
# Pre-1965 Tariff Commission sales values cover bulk AND dosage forms (packaged vials/tablets).
# While the active ingredient dominated cost (through 1948: >$1,600/BU, i.e. >$0.50 of API per
# 300,000-unit dose) packaging is a small share, so those years are kept. From 1952-1964 the
# all-forms value runs ~3-6x the bulk price (1964: $89/BU all forms vs $15.7/BU feed-grade bulk),
# so those points are plotted but excluded from every fit.
ALL_FORMS_FIT_CUTOFF_YEAR = 1948

# Era split for the segmented fits (inclusive year ranges).
ERAS = {
    "Wartime scale-up (1943-1950)": (1943, 1950),
    "US bulk market (1962-1984)": (1962, 1984),
    "Global / China era (1985-2024)": (1985, 2024),
}

# World production scenarios -> which anchor column to use.
SCENARIOS = ("low", "central", "high")

# --- Presentation --------------------------------------------------------------------------
WATERMARK = "Christopher Kalitin 2026"
COLORS = {
    "us_bulk": "#1f77b4",
    "quoted": "#9467bd",
    "all_forms_fit": "#1f77b4",
    "all_forms_excluded": "#1f77b4",
    "world": "#d62728",
    "fit": "0.15",
    "band": "0.80",
    "us_prod": "#1f77b4",
    "world_prod": "#d62728",
}
ERA_COLORS = ["#2ca02c", "#1f77b4", "#d62728"]

# Years to label directly on the learning-curve scatter.
LABEL_YEARS = {1943, 1945, 1948, 1950, 1952, 1962, 1970, 1984, 1985, 1995, 2003, 2013, 2024}
