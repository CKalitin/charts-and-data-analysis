import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mc
import os

def lighten(color, amount=0.45):
    r, g, b = mc.to_rgb(color)
    return (1-(1-r)*amount, 1-(1-g)*amount, 1-(1-b)*amount)

output_dir = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(output_dir, exist_ok=True)

AUTHOR = 'Christopher Kalitin 2026'

from solar_data import (BREAKDOWN_COMPS as comp_order, SUB_COMPONENTS as data,
                         COMP_DISPLAY as comp_display, COMP_COLORS as comp_colors)
# Text color inside solid blocks (Module needs dark text — yellow is light)
solid_text = {
    'Module':     '#444444',
    'SBOS':       'white',
    'EBOS':       'white',
    'Fieldwork':  'white',
    'Officework': 'white',
    'Other':      'white',
}

MIN_LABEL_PCT = 4.5   # don't label segments shorter than this

fig, ax = plt.subplots(figsize=(15, 9), dpi=150)
bar_width = 0.65

for xi, comp in enumerate(comp_order):
    color = comp_colors[comp]
    stc   = solid_text[comp]

    running_bottom = 0.0
    for sub_name, pct, tf_frac in data[comp]:
        block_start = running_bottom
        solid_h = pct * tf_frac
        na_h    = pct * (1 - tf_frac)

        # Solid (terraform) portion — drawn at the bottom of the block
        if solid_h > 0:
            ax.bar(xi, solid_h, bottom=running_bottom, color=color, width=bar_width,
                   edgecolor='white', linewidth=0.5, zorder=3)
        running_bottom += solid_h

        # Hatched N/A portion — drawn on top of solid
        if na_h > 0:
            ax.bar(xi, na_h, bottom=running_bottom, color=color, width=bar_width,
                   alpha=0.38, edgecolor='white', linewidth=0.5, hatch='////', zorder=3)
        running_bottom += na_h

        # One label per block, centred on the full block height
        if pct >= MIN_LABEL_PCT:
            block_center = block_start + pct / 2
            txt_color = stc if tf_frac >= 0.5 else '#333333'
            ax.text(xi, block_center, f'{sub_name}\n{pct:.1f}%',
                    ha='center', va='center', fontsize=6.5,
                    color=txt_color, fontweight='bold', zorder=4)

# ─── Axes formatting ──────────────────────────────────────────────────────────
ax.set_xticks(range(len(comp_order)))
ax.set_xticklabels([comp_display[c] for c in comp_order], fontsize=10.5)
ax.set_ylabel('% of Component Cost', fontsize=10)
ax.set_ylim(0, 108)
ax.set_xlim(-0.55, len(comp_order) - 0.45)
ax.set_title('Solar Array Sub-Component Cost Breakdown', fontsize=13, fontweight='bold', pad=14)
ax.grid(True, axis='y', linestyle='--', alpha=0.4, zorder=0)
ax.set_axisbelow(True)

# ─── Legend ───────────────────────────────────────────────────────────────────
handles = [mpatches.Patch(color=comp_colors[c], label=comp_display[c]) for c in comp_order]
handles.append(mpatches.Patch(
    facecolor='#bbbbbb', alpha=0.38, hatch='////', edgecolor='#888888',
    label='N/A — not applicable to Terraform'
))
ax.legend(handles=handles, loc='upper right', fontsize=8.5,
          framealpha=0.9, edgecolor='#cccccc')

fig.text(0.5,  0.01, '"N/A" = Not applicable to Terraform',
         ha='center', fontsize=8, color='#555555', style='italic')
fig.text(0.99, 0.01, AUTHOR, ha='right', va='bottom', fontsize=8, color='#888888')

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join(output_dir, 'solar_subcomponent_breakdown.png'),
            dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_subcomponent_breakdown.png')
