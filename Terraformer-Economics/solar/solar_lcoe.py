import matplotlib.pyplot as plt
import os

output_dir = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(output_dir, exist_ok=True)

AUTHOR = 'Christopher Kalitin 2026'

# ─── Shared parameters ────────────────────────────────────────────────────────
YEARS          = 25
SOLAR_RESOURCE = 2000     # kWh/m²/yr
ARRAY_SIZE_KW  = 1000     # kW
OPEX_PER_KW    = 5.89     # $/kW/year

# Terraform array costs
ARRAY_COST_CURRENT  = 654   # $/kW
ARRAY_COST_TERMINAL = 254   # $/kW

# Standard utility array
ARRAY_COST_UTILITY  = 1277  # $/kW
DISCOUNT_UTILITY    = 0.05  # 5%

annual_energy = ARRAY_SIZE_KW * SOLAR_RESOURCE   # kWh/year

# ─── Helpers ──────────────────────────────────────────────────────────────────
def crf(discount_rate):
    return 1 / YEARS if discount_rate == 0 else \
           discount_rate / (1 - (1 + discount_rate) ** -YEARS)

def lcoe_parts(array_cost_kw, discount_rate=0.0, opex=True):
    """Return (base_capex, discount_premium, opex) in $/MWh.
    base_capex       = CAPEX at 0% discount
    discount_premium = extra cost from applying the real discount rate
    """
    scale        = ARRAY_SIZE_KW / annual_energy * 1e3
    base_capex   = array_cost_kw * crf(0.0)           * scale
    total_capex  = array_cost_kw * crf(discount_rate) * scale
    discount_prem = total_capex - base_capex
    opex_         = OPEX_PER_KW * scale if opex else 0.0
    return base_capex, discount_prem, opex_

# ─── Cases: (label, base_capex, discount_premium, opex, note) ────────────────
cases = [
    ('Standard Utility\nSolar',
     *lcoe_parts(ARRAY_COST_UTILITY, DISCOUNT_UTILITY, opex=True),
     f'${ARRAY_COST_UTILITY}/kW · {DISCOUNT_UTILITY:.0%} discount rate'),

    ('Terraform\nCurrent',
     *lcoe_parts(ARRAY_COST_CURRENT, 0.0, opex=True),
     f'${ARRAY_COST_CURRENT}/kW · 0% discount rate'),

    ('Terraform\nTerminal',
     *lcoe_parts(ARRAY_COST_TERMINAL, 0.0, opex=True),
     f'${ARRAY_COST_TERMINAL}/kW · 0% discount rate'),

    ('Terraform\nTerminal (No OPEX)',
     *lcoe_parts(ARRAY_COST_TERMINAL, 0.0, opex=False),
     f'${ARRAY_COST_TERMINAL}/kW · 0% discount rate · no OPEX'),
]

labels        = [c[0] for c in cases]
capex_vals    = [c[1] for c in cases]
discount_vals = [c[2] for c in cases]
opex_vals     = [c[3] for c in cases]
totals        = [c[1] + c[2] + c[3] for c in cases]
notes         = [c[4] for c in cases]

CAPEX_COLOR    = '#2980b9'
DISCOUNT_COLOR = '#8e44ad'
OPEX_COLOR     = '#e74c3c'

SHARED_NOTE = (f'Lifetime: {YEARS} yr  ·  Solar resource: {SOLAR_RESOURCE:,} kWh/m²/yr  ·  '
               f'Array: {ARRAY_SIZE_KW:,} kW  ·  OPEX: ${OPEX_PER_KW}/kW/yr')

# ─── Drawing function ─────────────────────────────────────────────────────────
def draw_lcoe_chart(cases, title, filename, figsize=(10, 6.5)):
    labels        = [c[0] for c in cases]
    capex_vals    = [c[1] for c in cases]
    discount_vals = [c[2] for c in cases]
    opex_vals     = [c[3] for c in cases]
    totals        = [c[1] + c[2] + c[3] for c in cases]
    notes         = [c[4] for c in cases]

    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    bar_width = 0.45
    xs = range(len(cases))

    ax.bar(xs, capex_vals, width=bar_width, color=CAPEX_COLOR,
           edgecolor='white', linewidth=0.6, label='CAPEX (0% discount)', zorder=3)
    ax.bar(xs, discount_vals, bottom=capex_vals, width=bar_width, color=DISCOUNT_COLOR,
           edgecolor='white', linewidth=0.6, label='Discount rate premium', zorder=3)
    capex_tops = [c + d for c, d in zip(capex_vals, discount_vals)]
    ax.bar(xs, opex_vals, bottom=capex_tops, width=bar_width, color=OPEX_COLOR,
           edgecolor='white', linewidth=0.6, label='OPEX', zorder=3)

    MIN_LABEL = 0.8
    for i, (capex, disc, opex) in enumerate(zip(capex_vals, discount_vals, opex_vals)):
        if capex >= MIN_LABEL:
            ax.text(i, capex / 2, f'{capex:.2f}',
                    ha='center', va='center', fontsize=8.5, color='white',
                    fontweight='bold', zorder=4)
        if disc >= MIN_LABEL:
            ax.text(i, capex + disc / 2, f'{disc:.2f}',
                    ha='center', va='center', fontsize=8.5, color='white',
                    fontweight='bold', zorder=4)
        if opex >= MIN_LABEL:
            ax.text(i, capex + disc + opex / 2, f'{opex:.2f}',
                    ha='center', va='center', fontsize=8.5, color='white',
                    fontweight='bold', zorder=4)

    for i, (total, note) in enumerate(zip(totals, notes)):
        ax.text(i, total + 0.22, f'{total:.2f} $/MWh',
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#333333')
        ax.text(i, -1.8, note, ha='center', va='top', fontsize=6.5,
                color='#666666', style='italic')

    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel('LCOE ($/MWh)', fontsize=10)
    ax.set_ylim(-3.5, max(totals) * 1.18)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    ax.grid(True, axis='y', linestyle='--', alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.axhline(0, color='#aaaaaa', linewidth=0.8)
    ax.legend(fontsize=9.5, framealpha=0.9, edgecolor='#cccccc')

    fig.text(0.01, 0.005, SHARED_NOTE, ha='left', fontsize=7, color='#666666', style='italic')
    fig.text(0.99, 0.005, AUTHOR, ha='right', va='bottom', fontsize=8, color='#888888')

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {filename}')

# ─── Chart 1: all cases ───────────────────────────────────────────────────────
draw_lcoe_chart(cases, 'Solar Array LCOE by Case', 'solar_lcoe.png')

# ─── Chart 2: Terraform only ──────────────────────────────────────────────────
terraform_cases = [c for c in cases if c[0].startswith('Terraform')]
draw_lcoe_chart(terraform_cases, 'Terraform Solar Array LCOE',
                'solar_lcoe_terraform.png', figsize=(8, 6.5))
