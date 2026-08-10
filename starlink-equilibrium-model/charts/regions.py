"""Single source of truth for World Bank region -> color, shared by every chart module.

Region names must match data/telecom_market_by_country.csv `region` values exactly
(World Bank's own region taxonomy) -- verified against the actual CSV, not guessed.
"""
from __future__ import annotations

REGION_COLORS = {
    "Sub-Saharan Africa": "#d73027",
    "South Asia": "#fc8d59",
    "East Asia & Pacific": "#fee090",
    "Latin America & Caribbean": "#91bfdb",
    "Middle East, North Africa, Afghanistan & Pakistan": "#4575b4",
    "Europe & Central Asia": "#1a9850",
    "North America": "#762a83",
}

REGION_SHORT = {
    "Sub-Saharan Africa": "Sub-Saharan Africa",
    "South Asia": "South Asia",
    "East Asia & Pacific": "East Asia & Pacific",
    "Latin America & Caribbean": "Latin America & Caribbean",
    "Middle East, North Africa, Afghanistan & Pakistan": "MENA + Afghanistan/Pakistan",
    "Europe & Central Asia": "Europe & Central Asia",
    "North America": "North America",
}
