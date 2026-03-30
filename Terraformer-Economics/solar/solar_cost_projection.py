import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

output_dir = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(output_dir, exist_ok=True)

AUTHOR = 'Christopher Kalitin 2026'

from solar_data import (COMP_COLORS as COLORS, COMP_DISPLAY as DISPLAY,
                         STD_BASE, TERR_BASE)

# Stack order: constant components first (bottom), Module last (top) → yellow shrinks visibly
STD_STACK  = ['Inverter', 'SBOS', 'EBOS', 'Fieldwork', 'Officework', 'Other', 'Module']
TERR_STACK = [            'SBOS', 'EBOS', 'Fieldwork', 'Officework', 'Other', 'Module']

# ─── Year range and cost arrays ───────────────────────────────────────────────
START_YEAR, END_YEAR = 2022, 2036
MODULE_DECLINE = 0.20   # 20% cheaper per year

years = np.arange(START_YEAR, END_YEAR + 1, dtype=float)
n     = years - START_YEAR

def build_arrays(base):
    """Year-by-year cost per component; only Module declines."""
    return {
        comp: base['Module'] * (1 - MODULE_DECLINE) ** n if comp == 'Module'
              else np.full_like(n, v)
        for comp, v in base.items()
    }

std_arr  = build_arrays(STD_BASE)
terr_arr = build_arrays(TERR_BASE)

std_total  = sum(std_arr[c]  for c in STD_STACK)
terr_total = sum(terr_arr[c] for c in TERR_STACK)

# ─── Drawing helpers ──────────────────────────────────────────────────────────
def draw_line(ax):
    ax.plot(years, std_total,  color='#2980b9', linewidth=2.5,
            label='Standard Utility Array', zorder=3)
    ax.plot(years, terr_total, color='#27ae60', linewidth=2.5,
            label='Terraform Array', zorder=3)
    ax.fill_between(years, terr_total, std_total,
                    alpha=0.08, color='#e74c3c', label='Savings gap')

    for val, clr, ya in [(std_total[0],   '#2980b9',  0.016),
                         (terr_total[0],  '#27ae60',  0.016),
                         (std_total[-1],  '#2980b9', -0.035),
                         (terr_total[-1], '#27ae60', -0.035)]:
        xi = START_YEAR if (val == std_total[0] or val == terr_total[0]) else END_YEAR
        ax.annotate(f'{val:.3f}', xy=(xi, val), xytext=(xi, val + ya),
                    ha='center', fontsize=8, color=clr, fontweight='bold')

    ax.set_xlabel('Year', fontsize=10)
    ax.set_ylabel('Cost  (2022 standard array = 1.0)', fontsize=10)
    ax.set_title('Solar Array Cost Projection\n(Modules −20%/yr starting 2022)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.legend(fontsize=9.5, framealpha=0.9, edgecolor='#cccccc')
    ax.grid(True, linestyle='--', alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlim(START_YEAR, END_YEAR)
    ax.set_ylim(0.15, 1.08)

def draw_area(ax, arrays, stack_order, title, xlabel=False):
    values = [arrays[c]  for c in stack_order]
    colors = [COLORS[c]  for c in stack_order]
    ax.stackplot(years, values, colors=colors, alpha=0.88, linewidth=0)

    # Label each band at the 2022 start position
    running = 0.0
    for comp in stack_order:
        val = float(arrays[comp][0])
        if val >= 0.025:
            mid = running + val / 2
            tc  = '#444444' if comp == 'Module' else 'white'
            ax.text(START_YEAR + 0.35, mid, comp,
                    va='center', ha='left', fontsize=6.5,
                    color=tc, fontweight='bold', zorder=4)
        running += val

    ax.set_title(title, fontsize=10, fontweight='bold', pad=6)
    ax.set_ylabel('Cost  (2022 standard = 1.0)', fontsize=8)
    ax.set_xlim(START_YEAR, END_YEAR)
    ax.set_ylim(0, 1.08)
    ax.grid(True, axis='y', linestyle='--', alpha=0.35, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8)
    if xlabel:
        ax.set_xlabel('Year', fontsize=9)

# ─── Figure layout ────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 8), dpi=150)
gs  = fig.add_gridspec(2, 2, width_ratios=[1.4, 1], hspace=0.38, wspace=0.30)

ax_line = fig.add_subplot(gs[:, 0])     # line chart — full left column
ax_std  = fig.add_subplot(gs[0, 1])     # standard utility breakdown — top right
ax_terr = fig.add_subplot(gs[1, 1])     # terraform breakdown — bottom right

# ─── Line chart ───────────────────────────────────────────────────────────────
draw_line(ax_line)

# ─── Stacked area breakdowns ──────────────────────────────────────────────────
draw_area(ax_std,  std_arr,  STD_STACK,  'Standard Utility Array — Cost Breakdown')
draw_area(ax_terr, terr_arr, TERR_STACK, 'Terraform Array — Cost Breakdown', xlabel=True)

# ─── Shared legend ────────────────────────────────────────────────────────────
handles = [mpatches.Patch(color=COLORS[c], label=DISPLAY[c])
           for c in ['Module', 'Inverter', 'SBOS', 'EBOS', 'Fieldwork', 'Officework', 'Other']]
fig.legend(handles=handles, loc='lower center', ncol=7, fontsize=8.5,
           framealpha=0.9, edgecolor='#cccccc', bbox_to_anchor=(0.5, 0.003))

fig.suptitle('Terraform Solar Array Cost Savings Projection',
             fontsize=14, fontweight='bold', y=0.99)
fig.text(0.99, 0.002, AUTHOR, ha='right', va='bottom', fontsize=8, color='#888888')
fig.text(0.01, 0.002,
         'Modules assumed −20%/yr from 2022 · All other costs held constant',
         ha='left', va='bottom', fontsize=7.5, color='#666666', style='italic')

plt.subplots_adjust(left=0.06, right=0.98, top=0.93, bottom=0.11, hspace=0.40, wspace=0.30)
plt.savefig(os.path.join(output_dir, 'solar_cost_projection.png'),
            dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_cost_projection.png')

LEGEND_HANDLES = [mpatches.Patch(color=COLORS[c], label=DISPLAY[c])
                  for c in ['Module', 'Inverter', 'SBOS', 'EBOS', 'Fieldwork', 'Officework', 'Other']]
FOOTNOTE = 'Modules assumed −20%/yr from 2022 · All other costs held constant'

# ─── Standalone line chart ────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
draw_line(ax)
fig.suptitle('Terraform Solar Array Cost Savings Projection',
             fontsize=13, fontweight='bold', y=0.99)
fig.text(0.99, 0.01, AUTHOR,    ha='right', va='bottom', fontsize=8, color='#888888')
fig.text(0.01, 0.01, FOOTNOTE,  ha='left',  va='bottom', fontsize=7.5, color='#666666', style='italic')
plt.tight_layout(rect=[0, 0.04, 1, 0.97])
plt.savefig(os.path.join(output_dir, 'solar_cost_projection_line.png'),
            dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_cost_projection_line.png')

# ─── Side-by-side breakdowns ──────────────────────────────────────────────────
fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(13, 6), dpi=150)
draw_area(ax_l, std_arr,  STD_STACK,  'Standard Utility Array')
draw_area(ax_r, terr_arr, TERR_STACK, 'Terraform Array', xlabel=True)
ax_l.set_xlabel('Year', fontsize=9)

fig.legend(handles=LEGEND_HANDLES, loc='lower center', ncol=7, fontsize=8.5,
           framealpha=0.9, edgecolor='#cccccc', bbox_to_anchor=(0.5, 0.0))
fig.suptitle('Solar Array Cost Breakdown Projection  (Modules −20%/yr)',
             fontsize=13, fontweight='bold', y=0.99)
fig.text(0.99, 0.01, AUTHOR,   ha='right', va='bottom', fontsize=8, color='#888888')
fig.text(0.01, 0.01, FOOTNOTE, ha='left',  va='bottom', fontsize=7.5, color='#666666', style='italic')
plt.tight_layout(rect=[0, 0.09, 1, 0.96])
plt.savefig(os.path.join(output_dir, 'solar_cost_projection_breakdowns.png'),
            dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_cost_projection_breakdowns.png')
