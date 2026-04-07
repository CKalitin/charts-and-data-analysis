"""
Single source of truth for all solar array cost data.
Edit values here — all charts derive their data from this file.
"""

# ─── Component ordering ───────────────────────────────────────────────────────
COMPONENTS      = ['Module', 'Inverter', 'SBOS', 'EBOS', 'Fieldwork', 'Officework', 'Other']
BREAKDOWN_COMPS = ['Module',             'SBOS', 'EBOS', 'Fieldwork', 'Officework', 'Other']

# ─── Style ────────────────────────────────────────────────────────────────────
COMP_COLORS = {
    'Module':     '#f1c40f',
    'Inverter':   '#7f8c8d',
    'SBOS':       '#8e44ad',
    'EBOS':       '#2980b9',
    'Fieldwork':  '#27ae60',
    'Officework': '#e67e22',
    'Other':      '#e74c3c',
}
COMP_DISPLAY = {
    'Module':     'Module',
    'Inverter':   'Inverter',
    'SBOS':       'SBOS (Structural)',
    'EBOS':       'EBOS (Electrical)',
    'Fieldwork':  'Fieldwork',
    'Officework': 'Officework',
    'Other':      'Other',
}

# ─── Component share of total standard PV system cost (%) ────────────────────
COMPONENT_WEIGHTS = {
    'Module':     32.04,
    'Inverter':    4.13,
    'SBOS':       11.03,
    'EBOS':       15.16,
    'Fieldwork':  20.33,
    'Officework':  5.68,
    'Other':      11.63,
}

# ─── Sub-component breakdown ──────────────────────────────────────────────────
# (name, % of that component's total cost, terraform_fraction)
#   1.0   = fully applicable to Terraform
#   0.0   = N/A (Terraform doesn't pay)
#   float = partial (Fieldwork items, proportional to BoS cost decline)
SUB_COMPONENTS = {
    'Module': [
        ('Cells',              47.45, 1.0),
        ('Frame',               5.50, 1.0),
        ('Junction Box',        1.83, 1.0),
        ('Other Material',     11.61, 1.0),
        ('Depreciation',        2.85, 1.0),
        ('Overhead & Profit',  21.59, 1.0),
        ('Shipping',            9.17, 1.0),
    ],
    'Inverter': [
        ('Inverter',          100.00, 0.0),   # entirely N/A for Terraform
    ],
    'SBOS': [
        ('Torque Tubes',       41.76, 0.0),
        ('Driven Piers',       10.61, 1.0),
        ('Module Rails',        7.54, 1.0),
        ('Fasteners',           1.40, 1.0),
        ('Slew Drive',          6.98, 0.0),
        ('Dampers',             1.82, 0.0),
        ('Motor',              11.17, 0.0),
        ('Control Electronics', 3.49, 0.0),
        ('Shipping',            9.36, 0.3),
        ('ESS Pad',             5.87, 0.0),
    ],
    'EBOS': [
        ('Transformers',       16.62, 0.0),
        ('Switches',            4.94, 1.0),
        ('Breakers',           10.39, 1.0),
        ('Conductors',          6.62, 1.0),
        ('Combiner Boxes',      5.06, 1.0),
        ('Grounding',           4.81, 1.0),
        ('Substation',         18.18, 0.0),
        ('Transmission',        8.18, 0.0),
        ('Network Upgrade',    25.19, 0.0),
    ],
    'Fieldwork': [
        ('EBOS Labour',        15.97, 0.3182),
        ('SBOS Labour',        21.69, 0.2891),
        ('ESS Labour',         13.25, 0.0000),
        ('Labour Burden',      27.66, 0.3036),
        ('Equipment Rental',   18.18, 0.3036),
        ('Inspection',          3.25, 1.0000),
    ],
    'Officework': [
        ('Warehousing',        10.18, 1.0),
        ('Logistics',           7.48, 1.0),
        ('Permits',             2.94, 1.0),
        ('Engineering',        23.44, 0.5),
        ('Interconnect',       45.77, 0.0),
        ('Outreach',           10.18, 0.0),
    ],
    'Other': [
        ('Sales Tax',          34.90, 0.5),
        ('Contingency',        11.50, 1.0),
        ('Management',         13.30, 0.0),
        ('Profit',             40.30, 0.0),
    ],
}

# ─── Derived values (do not edit — computed from above) ──────────────────────
_tf_frac = {
    comp: sum(pct * tf for _, pct, tf in subs) / 100.0
    for comp, subs in SUB_COMPONENTS.items()
}

# % of total standard PV system cost per component, split by terraform/N/A
TERRAFORM_PCT = [COMPONENT_WEIGHTS[c] * _tf_frac[c]       for c in COMPONENTS]
NA_PCT        = [COMPONENT_WEIGHTS[c] * (1 - _tf_frac[c]) for c in COMPONENTS]

# Fraction of total standard array cost (0.0–1.0 scale) per component
STD_BASE  = {c: COMPONENT_WEIGHTS[c] / 100.0              for c in COMPONENTS}
TERR_BASE = {c: COMPONENT_WEIGHTS[c] * _tf_frac[c] / 100.0 for c in COMPONENTS}

import solar_cost_savings
import solar_cost_projection
import solar_subcomponent_breakdown