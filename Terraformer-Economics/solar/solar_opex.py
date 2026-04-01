import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

output_dir = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(output_dir, exist_ok=True)

AUTHOR = 'Christopher Kalitin 2026'

# ─── OPEX data: (component, % of total OPEX, terraform_fraction) ──────────────
OPEX = [
    ('Cleaning',         15.20, 0.50),
    ('Inspection',        8.65, 0.50),
    ('New BOS',           7.67, 0.50),
    ('New Modules',       1.81, 1.00),
    ('New Inverters',    13.95, 0.00),
    ('Land Lease',       12.83, 0.00),
    ('Property Tax',     11.72, 0.33),
    ('Insurance',        17.71, 0.50),
    ('Asset Management', 10.46, 0.00),
]

COLORS = {
    'Cleaning':          '#3498db',
    'Inspection':        '#1abc9c',
    'New BOS':           '#8e44ad',
    'New Modules':       '#f1c40f',
    'New Inverters':     '#e74c3c',
    'Land Lease':        '#27ae60',
    'Property Tax':      '#95a5a6',
    'Insurance':         '#e67e22',
    'Asset Management':  '#2c3e50',
}

# ─── Bar chart ────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 6.5), dpi=150)

bar_width = 0.45
x_std, x_terr = 0, 1
bottom_std = bottom_terr = 0.0
legend_handles = []

for comp, pct, tf_frac in OPEX:
    color    = COLORS[comp]
    solid_h  = pct * tf_frac
    na_h     = pct * (1 - tf_frac)

    # Standard bar: solid (terraform) portion
    if solid_h > 0:
        ax.bar(x_std, solid_h, bottom=bottom_std, color=color, width=bar_width,
               edgecolor='white', linewidth=0.6, zorder=3)
        if solid_h >= 2.5:
            ax.text(x_std, bottom_std + solid_h / 2, f'{solid_h:.1f}%',
                    ha='center', va='center', fontsize=7, color='white',
                    fontweight='bold', zorder=4)
    bottom_std += solid_h

    # Standard bar: N/A (hatched) portion
    if na_h > 0:
        ax.bar(x_std, na_h, bottom=bottom_std, color=color, width=bar_width,
               alpha=0.38, edgecolor='white', linewidth=0.6, hatch='////', zorder=3)
        if na_h >= 2.5:
            ax.text(x_std, bottom_std + na_h / 2, f'{na_h:.1f}%',
                    ha='center', va='center', fontsize=7, color=color,
                    fontweight='bold', zorder=4)
    bottom_std += na_h

    # Terraform bar: solid only
    if solid_h > 0:
        ax.bar(x_terr, solid_h, bottom=bottom_terr, color=color, width=bar_width,
               edgecolor='white', linewidth=0.6, zorder=3)
        if solid_h >= 2.5:
            ax.text(x_terr, bottom_terr + solid_h / 2, f'{solid_h:.1f}%',
                    ha='center', va='center', fontsize=7, color='white',
                    fontweight='bold', zorder=4)
    bottom_terr += solid_h

    legend_handles.append(mpatches.Patch(color=color, label=comp))

legend_handles.append(mpatches.Patch(
    facecolor='#aaaaaa', alpha=0.38, hatch='////', edgecolor='#888888',
    label='N/A (not applicable to Terraform)'
))

# Totals above bars
offset = 0.8
ax.text(x_std,  bottom_std  + offset, f'{bottom_std:.1f}%',
        ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#333333')
ax.text(x_terr, bottom_terr + offset, f'{bottom_terr:.1f}%',
        ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#333333')

# Savings bracket
savings = bottom_std - bottom_terr
mid_y   = (bottom_terr + bottom_std) / 2
ax.annotate('', xy=(x_std - bar_width / 2 - 0.02, bottom_std),
            xytext=(x_std - bar_width / 2 - 0.02, bottom_terr),
            arrowprops=dict(arrowstyle='<->', color='#555555', lw=1.2))
ax.text(x_std - bar_width / 2 - 0.08, mid_y,
        f'Savings\n{savings:.1f}%', ha='right', va='center',
        fontsize=8, color='#555555', style='italic')

ax.set_xticks([x_std, x_terr])
ax.set_xticklabels(['Standard Utility OPEX', 'Terraform OPEX'], fontsize=10.5)
ax.set_ylabel('% of Total OPEX', fontsize=10)
ax.set_ylim(0, max(bottom_std, bottom_terr) * 1.12)
ax.set_xlim(-0.65, 1.5)
ax.set_title('Solar Array OPEX Breakdown: Standard vs Terraform',
             fontsize=12, fontweight='bold', pad=12)
ax.grid(True, axis='y', linestyle='--', alpha=0.4, zorder=0)
ax.set_axisbelow(True)

ax.legend(handles=legend_handles, loc='upper right', fontsize=8,
          framealpha=0.9, edgecolor='#cccccc')

fig.text(0.99, 0.01, AUTHOR, ha='right', va='bottom', fontsize=8, color='#888888')
fig.text(0.01, 0.01, "Land price factored into array capex, not opex", ha='left', va='bottom', fontsize=8, color='#888888')

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join(output_dir, 'solar_opex_breakdown.png'),
            dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_opex_breakdown.png')
