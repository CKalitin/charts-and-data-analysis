"""All tunables for the SSO ground-track land-proximity analysis.

The question: a sun-synchronous satellite at 550 km circles the Earth ~15 times
a day. What fraction of that orbit time is spent over land, over coastal water
(within 300 mi of a coast), versus over open ocean? The answer drives how much
of an imaging/illumination duty cycle is actually usable near populated coasts.

Nothing tunable is hardcoded at a call site — orbital parameters, the proximity
threshold, the land-data source, the grid resolution and all styling live here.
"""
from __future__ import annotations

from pathlib import Path

# --- Paths ------------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR    = PROJECT_DIR / "data"
OUTPUT_DIR  = PROJECT_DIR / "outputs"
LAND_CACHE  = PROJECT_DIR / "ne_110m_land.geojson"

# Global Solar Power Tracker (Global Energy Monitor), Feb 2026 release.
SOLAR_XLSX        = DATA_DIR / "Global-Solar-Power-Tracker-February-2026.xlsx"
SOLAR_SHEET       = "Utility-Scale (1 MW+)"
SOLAR_CACHE       = DATA_DIR / "solar_arrays.npz"     # parsed lat/lon/MW cache
# Which project statuses count as a real array "as listed in the file". Default to
# the arrays that physically exist on the ground today.
SOLAR_STATUS      = {"operating"}
# One solar-proximity chart is rendered per minimum-capacity floor (MW). 0 = every
# operating array; 100 = only large (>=100 MW) utility plants.
# Each case is (min_mw_floor, frozenset_of_excluded_countries).
# One solar-proximity chart is rendered per entry.
SOLAR_CASES: list[tuple[float, frozenset]] = [
    (0.0,   frozenset()),
    (100.0, frozenset()),
    (100.0, frozenset({"China", "Russia"})),
]

WATERMARK = "Christopher Kalitin 2026"

# --- Orbital parameters -----------------------------------------------------------------
ALT_KM      = 550        # satellite altitude
INC_DEG     = 97.6       # SSO inclination (~97.6 deg for a 550 km sun-synchronous orbit)
N_ORBITS    = 16         # full sidereal day ~= 15.04 orbits; 16 covers one day + margin
N_PER_ORBIT = 3000       # ground-track time steps per orbit (resolution vs speed)

# --- Analysis threshold -----------------------------------------------------------------
THRESHOLD_MI = 300
THRESHOLD_KM = THRESHOLD_MI * 1.60934   # 482.8 km

# --- Background classification raster ---------------------------------------------------
# The map fill is a per-cell classification (land / near-coast water / open ocean) so the
# three regions are shown directly as colored areas, not just inferred from the track.
MAP_NLON = 900           # longitude cells across the map background raster
MAP_NLAT = 450           # latitude cells

# --- Land data --------------------------------------------------------------------------
LAND_GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector"
    "/master/geojson/ne_110m_land.geojson"
)
# Features whose centroid latitude is below this threshold are treated as Antarctica
# and excluded from land classification and the map polygons.
ANTARCTICA_LAT_CUTOFF = -60.0

# --- Presentation (LIGHT MODE) ----------------------------------------------------------
# Region colors, per the brief: land = green, near-coast water = light blue, ocean = blue.
COL_LAND      = "#5BB85B"   # green        — over land (in analysis)
COL_NEAR      = "#A9D8F0"   # light blue   — coastal water, within THRESHOLD_MI of a coast
COL_OCEAN     = "#2E6FB5"   # blue         — open ocean, beyond the threshold
COL_LAND_EXCL = "#BDBDBD"   # neutral grey — land excluded from analysis (Antarctica)

# Coastline outline and the SSO ground track drawn on top of the colored regions.
COL_COAST  = "#3a6b3a"   # muted green coastline edge
COL_TRACK  = "#E8430F"   # vivid orange-red — the SSO ground track, reads on green+blue
COL_TRACK_EDGE = "#7a1f00"

FIG_BG     = "#FFFFFF"    # light-mode page background
AXES_BG    = COL_OCEAN    # map "sea level" base — overwritten cell-by-cell by the raster

OUTPUT_DPI = 300

# --- Atmospheric transmission --------------------------------------------------------
T_CLEAR    = 0.7    # one-way transmission through a clear atmosphere
T_OVERCAST = 0.2    # one-way transmission through overcast skies

ERA5_NC    = DATA_DIR / "era5_tcc.nc"   # ERA5 total cloud cover (download once)

# Grid cell size for aggregating solar arrays before plotting.
# At 0.5 deg, one dot per cell; matches ERA5 native resolution.
SOLAR_GRID_CELL_DEG = 0.5

# --- Solar-proximity chart palette ------------------------------------------------------
# Two-category background: within 300 mi of an operating array (gold) vs beyond (slate).
COL_SOLAR_NEAR = "#F2B705"   # gold        — within THRESHOLD of a solar array
COL_SOLAR_FAR  = "#E7ECF1"   # light slate — beyond the threshold
COL_SOLAR_DOT  = "#5A2E00"   # dark brown  — the array sites themselves (reads on gold)
COL_SOLAR_COAST = "#9AA7B4"  # neutral gray coastline, for geographic reference
COL_SOLAR_TRACK = "#0D3B86"  # dark blue SSO track (reads on both gold and slate)

CAT_SOLAR_FAR, CAT_SOLAR_NEAR = 0, 1
_SOLAR_LABELS = {
    CAT_SOLAR_NEAR: f"Within {THRESHOLD_MI} mi\nof a solar array",
    CAT_SOLAR_FAR:  f"Beyond {THRESHOLD_MI} mi",
}
_SOLAR_COLORS = {CAT_SOLAR_NEAR: COL_SOLAR_NEAR, CAT_SOLAR_FAR: COL_SOLAR_FAR}


def solar_label(code: int) -> str:
    return _SOLAR_LABELS[code]


def solar_color(code: int) -> str:
    return _SOLAR_COLORS[code]

# --- Single source of truth for category labels -----------------------------------------
CAT_LAND, CAT_NEAR, CAT_OCEAN = 0, 1, 2   # raster codes (also donut order)
CAT_LAND_EXCL = 3                          # excluded from analysis — drawn grey on the map

_LABELS = {
    CAT_LAND:  "Over land",
    CAT_NEAR:  f"Coastal water\n(within {THRESHOLD_MI} mi)",
    CAT_OCEAN: f"Open ocean\n(> {THRESHOLD_MI} mi)",
}
_COLORS = {CAT_LAND: COL_LAND, CAT_NEAR: COL_NEAR, CAT_OCEAN: COL_OCEAN}


def cat_label(code: int) -> str:
    return _LABELS[code]


def cat_color(code: int) -> str:
    return _COLORS[code]
