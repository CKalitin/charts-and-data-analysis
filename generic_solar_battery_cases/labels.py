"""Single source of truth for axis labels and units.

Every chart calls :func:`axis_label` instead of hand-typing a string, so a
variable can never be silently mislabeled and renaming a unit is one edit.
The whole project's vocabulary lives here.
"""

from __future__ import annotations

# name -> human-readable axis label (with units).
_LABELS: dict[str, str] = {
    # Economic drivers (the independent variables of the analysis)
    "income_per_kwh":   "Load income  ($/kWh)",
    "solar_cost_ann":   "Solar cost  ($/kW·yr)",
    "batt_cost_ann":    "Battery cost  ($/kWh·yr)",
    "solar_capex":      "Solar capex  ($/kW)",
    "batt_capex":       "Battery capex  ($/kWh)",
    "load_cost_ann":    "Load capex  ($/kW·yr)",
    "load_capex":       "Load capex  ($/kW)",
    # Build (the inner optimization variables)
    "kw_solar":         "Solar nameplate  (kW)",
    "kwh_battery":      "Battery capacity  (kWh)",
    # Outcomes
    "utilization_pct":  "Optimal utilization  (%)",
    "profit_per_yr":    "Optimal profit  ($/yr)",
    "lcoe":             "LCOE  ($/kWh)",
    "solar_fraction":   "Solar fraction  α",
    "served_kwh":       "Energy delivered to load  (kWh/yr)",
    # Time-series quantities
    "ghi":              "GHI  (kWh/m²/day)",
    "gen_kwh":          "Solar production  (kWh/day)",
    "soc_kwh":          "Battery state of charge  (kWh)",
    "load_kwh":         "Load energy  (kWh/day)",
}


def axis_label(name: str) -> str:
    """Return the registered axis label for ``name`` (KeyError if unknown — by
    design, so a typo fails loudly instead of producing a mislabeled chart)."""
    return _LABELS[name]
