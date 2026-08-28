"""All tunables for the Mars transfer / heliocentric-injection-azimuth model.

Nothing tunable is hardcoded at a call site below this file.
"""
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
CACHE_DIR = PROJECT_DIR / "cache"
OUTPUT_ROOT = PROJECT_DIR / "outputs"

# --- Physical constants -----------------------------------------------------
# GM values: Vallado, "Fundamentals of Astrodynamics and Applications," 4th ed.,
# Table (Astrodynamic Constants), DE405-consistent. km^3/s^2.
GM_SUN = 1.32712440018e11
GM_EARTH = 398600.4418
GM_MARS = 42828.314258067

# Earth: keep consistent with supersyncronous-transfer-modelling/model.py
# (MU_EARTH=398600 rounded, R_EARTH=6371 mean radius) for cross-project consistency;
# the ~0.1% difference from equatorial radius (6378.137 km) is negligible next to the
# psi-driven delta-v effects (tens-hundreds of m/s on km/s-scale burns) this model studies.
R_EARTH = 6371.0  # km, mean radius
R_MARS = 3389.5  # km, mean radius (source: JPL Mars fact sheet)

# J2000 mean obliquity of the ecliptic (IAU 2006), used for the validated
# equatorial(ICRS)<->ecliptic rotation. degrees.
OBLIQUITY_J2000_DEG = 23.4392911111

# --- Parking orbit -----------------------------------------------------------
PARKING_ALTITUDE_KM = 400.0  # circular polar parking orbit altitude
PARKING_INCLINATION_DEG = 90.0

# --- Heliocentric injection azimuth (psi) sweep ------------------------------
PSI_MIN_DEG = -90.0
PSI_MAX_DEG = 90.0
PSI_STEPS = 181  # 1-degree resolution

# --- Real Mars transfer window (Jul 2020 - Feb 2021) -------------------------
# Actual Mars 2020 (Perseverance) launch period per JPL press kit:
# https://www.jpl.nasa.gov/news/press_kits/mars_2020/launch/quick_facts/
DEPARTURE_WINDOW_START = "2020-07-20"
DEPARTURE_WINDOW_END = "2020-08-11"
DEPARTURE_SEARCH_STEP_DAYS = 1

# Arrival search window: wide enough to bracket the minimum-C3 Type-1 (<180 deg
# transfer angle) solution for any departure date in the window above.
ARRIVAL_WINDOW_START = "2021-01-15"
ARRIVAL_WINDOW_END = "2021-04-15"
ARRIVAL_SEARCH_STEP_DAYS = 2

# --- Mid-course correction ----------------------------------------------------
MCC_EPOCH_OFFSET_DAYS = 10.0  # days after TMI burn
MCC_INJECTION_DV_ERROR_KMS = 0.001  # 1 m/s 1-sigma execution error, magnitude
MCC_INJECTION_POINTING_ERROR_DEG = 0.5  # 1-sigma pointing error
MCC_PSI_STEP_DEG = 5.0  # coarser grid than the departure-dV sweep (Monte Carlo per point)
MCC_N_SAMPLES = 2000

# --- Mars arrival / flyby -----------------------------------------------------
FLYBY_PERIAPSIS_ALT_KM = 500.0  # target flyby periapsis altitude above Mars
