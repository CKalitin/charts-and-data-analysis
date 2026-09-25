"""All tunables for the nail learning-curve analysis. Nothing tunable lives at a call site."""
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATA = PROJECT_DIR / "data"
OUTPUT_ROOT = PROJECT_DIR / "outputs"

# ---- unit conversions ---------------------------------------------------------------
LB_PER_KEG = 100.0            # AISA "kegs of 100 pounds"
KG_PER_LB = 0.45359237
LB_PER_GROSS_TON = 2240.0     # Lesley (1859) reports rolled iron / nails in gross tons

# ---- analysis window ----------------------------------------------------------------
LAST_YEAR = 2000              # "late 1900s"

# ---- technology eras & fit windows (inclusive years) ---------------------------------
# Each technology accumulates its OWN experience from its own start.
FIT_WINDOWS = {
    "hand_forged": (1695, 1792),   # Early UK (Beveridge / Greenwich Hospital)
    "cut": (1814, 1886),           # cut-nail era to its production peak, before wire displaced it
    "wire": (1890, 1940),          # wire-nail mechanization era, to the real-price trough
}
SECONDARY_WINDOWS = {
    "wire_postwar": ("wire", 1946, LAST_YEAR),   # post-WWII: input-cost / import era
}

# ---- hand-forged (UK) production scenarios --------------------------------------------
# No tabulated output exists. Anchor: ~50,000 West Midlands nailers c.1800; Adam Smith's
# 800-2,300 nails/day per nailer; ~85 nails/lb; ~50% effective utilization.
# Annual output O(t) = O_1800 * exp(g (t-1800)). With an exponential history the stock of
# past output is Q(t) = O(t)/g, so the NUMBER OF DOUBLINGS (what sets the learning rate)
# depends only on g; O_1800 only shifts the curve left/right.
HAND_FORGED_SCENARIOS = {          # name: (O_1800 [kt/yr], g [1/yr])
    "low": (20.0, 0.015),          # more doublings -> smallest implied |LR|
    "central": (40.0, 0.010),
    "high": (80.0, 0.005),
}

# ---- US cut nails before AISA coverage (1872) ------------------------------------------
# Benchmarks (kegs/yr): 1810 Gallatin report; 1856 Lesley. Between benchmarks: log-linear.
# Before 1810: extrapolate back at CUT_PRE1810_GROWTH from 1810 to US cut-nail start.
CUT_START_YEAR = 1795
CUT_PRE1810_GROWTH = {"low": 0.03, "central": 0.052, "high": 0.08}
CUT_1856_SCALE = {"low": 0.7, "central": 1.0, "high": 1.3}   # Lesley's total is "approximate"

# ---- wire nails after AISA coverage (1920) ---------------------------------------------
# Consumption = Sichel domestic absorption (2012$) / Sichel real price (2012$/lb);
# validated against AISA tonnage (1872-1914, residual = exports). Log-linear interpolation
# between benchmark years. Central basis is US consumption: the "production" alternative,
# consumption * (1 - import share), inherits a 1987->1992 source break in Sichel's import
# share (70% -> 29%) that fakes a 4x jump in US output.
WIRE_X_BASIS = "us_consumption"   # or "us_production" (sensitivity)

# ---- presentation -----------------------------------------------------------------------
TECH_STYLE = {   # dataviz reference palette slots 1-3 (all-pairs validated); gray = context
    "hand_forged": dict(color="#2a78d6", marker="s", label="Hand-forged (England)"),
    "mixed": dict(color="#8a8984", marker="D", label="Mixed forged + cut (US, 1795-1813)"),
    "cut": dict(color="#eb6834", marker="o", label="Machine-cut (US)"),
    "wire": dict(color="#1baf7a", marker="^", label="Wire (US)"),
}
SOURCE_NOTE = ("Sources: prices - Sichel (2022, JEP) digitized from vector figures, checked vs HSUS E-131; "
               "AISA Annual Statistical Reports (cut, post-1890). Volumes - AISA 1872-1920; "
               "Gallatin 1810, Lesley 1856; Sichel absorption & import share 1942-2000.")
DPI = 200
