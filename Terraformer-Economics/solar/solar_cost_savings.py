import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mc
import numpy as np
import os

def lighten(color, amount=0.45):
    """Blend a hex color toward white by `amount` (0=original, 1=white)."""
    r, g, b = mc.to_rgb(color)
    return (1-(1-r)*amount, 1-(1-g)*amount, 1-(1-b)*amount)

output_dir = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(output_dir, exist_ok=True)

from solar_data import (COMPONENTS as components, COMP_COLORS as comp_colors,
                         COMP_DISPLAY as comp_labels, TERRAFORM_PCT, NA_PCT)

terraform_pct   = TERRAFORM_PCT
na_pct          = NA_PCT
colors_list     = [comp_colors[c] for c in components]
total_terraform = sum(terraform_pct)
total_na        = sum(na_pct)

AUTHOR  = 'Christopher Kalitin 2026'
NA_NOTE = ''

# ─── Shared helpers ──────────────────────────────────────────────────────────
def build_wedge_data():
    """Return parallel lists for each non-zero pie wedge."""
    sizes, colors_, labels, hatches = [], [], [], []
    for i, comp in enumerate(components):
        color = comp_colors[comp]
        label = comp_labels[comp]
        tp, na = terraform_pct[i], na_pct[i]
        if tp > 0:
            sizes.append(tp)
            colors_.append(color)
            labels.append(f'{label}\n{tp:.1f}%')
            hatches.append('')
        if na > 0:
            sizes.append(na)
            colors_.append(lighten(color, 0.55))
            labels.append(f'{label} N/A\n{na:.1f}%')
            hatches.append('////')
    return sizes, colors_, labels, hatches

def make_legend_handles():
    handles = []
    for comp in components:
        handles.append(mpatches.Patch(color=comp_colors[comp], label=comp_labels[comp]))
    handles.append(mpatches.Patch(
        facecolor='#cccccc', hatch='////', edgecolor='#aaaaaa',
        label='N/A (not applicable to Terraform)'
    ))
    return handles

# ─── Drawing functions ────────────────────────────────────────────────────────
def draw_component_pie(ax):
    sizes, colors_, labels, hatches = build_wedge_data()
    wedges, _, _ = ax.pie(
        sizes,
        labels=labels,
        colors=colors_,
        autopct='',
        startangle=90,
        wedgeprops=dict(linewidth=1.2, edgecolor='white'),
        textprops=dict(fontsize=7.5),
        pctdistance=0.82,
        labeldistance=1.12,
    )
    for w, h in zip(wedges, hatches):
        if h:
            w.set_hatch(h)
            w.set_alpha(0.85)

def draw_stacked_bars(ax):
    bar_width = 0.45
    x_std, x_terr = 0, 1
    bottom_std = bottom_terr = 0.0

    for i, _ in enumerate(components):
        color = colors_list[i]
        tp = terraform_pct[i]
        na = na_pct[i]

        if tp > 0:
            ax.bar(x_std, tp, bottom=bottom_std, color=color, width=bar_width,
                   edgecolor='white', linewidth=0.6, zorder=3)
            if tp >= 2.5:
                ax.text(x_std, bottom_std + tp / 2, f'{tp:.1f}%',
                        ha='center', va='center', fontsize=7.5, color='white',
                        fontweight='bold', zorder=4)
        bottom_std += tp

        if na > 0:
            ax.bar(x_std, na, bottom=bottom_std, color=color, width=bar_width,
                   alpha=0.38, edgecolor='white', linewidth=0.6, hatch='////', zorder=3)
            if na >= 2.5:
                ax.text(x_std, bottom_std + na / 2, f'{na:.1f}%',
                        ha='center', va='center', fontsize=7.5, color=color,
                        fontweight='bold', zorder=4)
        bottom_std += na

        if tp > 0:
            ax.bar(x_terr, tp, bottom=bottom_terr, color=color, width=bar_width,
                   edgecolor='white', linewidth=0.6, zorder=3)
            if tp >= 2.5:
                ax.text(x_terr, bottom_terr + tp / 2, f'{tp:.1f}%',
                        ha='center', va='center', fontsize=7.5, color='white',
                        fontweight='bold', zorder=4)
        bottom_terr += tp

    # Totals above bars
    ax.text(x_std,  bottom_std  + 0.6, f'{bottom_std:.1f}%',
            ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#333333')
    ax.text(x_terr, bottom_terr + 0.6, f'{bottom_terr:.1f}%',
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
    ax.set_xticklabels(['Standard Utility Array', 'Terraform Array'], fontsize=10.5)
    ax.set_ylabel('% of Total Array Cost', fontsize=10)
    ax.set_ylim(0, max(bottom_std, bottom_terr) * 1.10)
    ax.set_xlim(-0.65, 1.5)
    ax.grid(True, axis='y', linestyle='--', alpha=0.4, zorder=0)
    ax.set_axisbelow(True)

# ─── Simple summary pie ───────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 6), dpi=150)

pie_sizes  = [total_terraform, total_na]
pie_colors = ['#2980b9', '#c0c0c0']

wedges, texts, autotexts = ax.pie(
    pie_sizes,
    labels=[f'Terraform Pays\n{total_terraform:.1f}%', f'Not Applicable\n{total_na:.1f}%'],
    colors=pie_colors,
    explode=(0.03, 0.07),
    autopct='%1.1f%%',
    startangle=90,
    wedgeprops=dict(linewidth=1.5, edgecolor='white'),
    textprops=dict(fontsize=10),
    pctdistance=0.70,
)
autotexts[0].set_color('white')
autotexts[0].set_fontweight('bold')
autotexts[0].set_fontsize(11)
autotexts[1].set_fontweight('bold')
autotexts[1].set_fontsize(11)

ax.set_title('Terraform Solar Array Cost Savings', fontsize=13, fontweight='bold', pad=16)
fig.text(0.99, 0.01, AUTHOR, ha='right', va='bottom', fontsize=8, color='#888888')
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join(output_dir, 'solar_cost_savings_pie.png'), dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_cost_savings_pie.png')

# ─── Component breakdown pie (standalone) ────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 7), dpi=150)
draw_component_pie(ax)
ax.legend(handles=make_legend_handles(), loc='lower right', bbox_to_anchor=(1.3, 0),
          fontsize=8, framealpha=0.9, edgecolor='#cccccc')
ax.set_title('Terraform Solar Array Cost Breakdown by Component',
             fontsize=12, fontweight='bold', pad=18)
fig.text(0.99, 0.01, AUTHOR, ha='right', va='bottom', fontsize=8, color='#888888')
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join(output_dir, 'solar_cost_breakdown_pie.png'), dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_cost_breakdown_pie.png')

# ─── Stacked bar (standalone) ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 6.5), dpi=150)
draw_stacked_bars(ax)
ax.set_title('Solar Array Cost Breakdown: Standard vs Terraform',
             fontsize=12, fontweight='bold', pad=12)
ax.legend(handles=make_legend_handles(), loc='upper right', fontsize=8,
          framealpha=0.9, edgecolor='#cccccc')
fig.text(0.99, 0.01, AUTHOR, ha='right', va='bottom', fontsize=8, color='#888888')
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join(output_dir, 'solar_cost_breakdown_bars.png'), dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_cost_breakdown_bars.png')

# ─── Combined figure (pie + bar) ─────────────────────────────────────────────
fig, (ax_pie, ax_bar) = plt.subplots(1, 2, figsize=(17, 7), dpi=150)

draw_component_pie(ax_pie)
ax_pie.set_title('Cost Breakdown by Component', fontsize=11, fontweight='bold', pad=14)

draw_stacked_bars(ax_bar)
ax_bar.set_title('Standard vs Terraform Array', fontsize=11, fontweight='bold', pad=12)

fig.legend(handles=make_legend_handles(), loc='lower center', ncol=4, fontsize=8.5,
           framealpha=0.9, edgecolor='#cccccc', bbox_to_anchor=(0.5, 0.01))

fig.suptitle('Terraform Solar Array Cost Savings', fontsize=14, fontweight='bold', y=0.98)
fig.text(0.99, 0.01, AUTHOR, ha='right', va='bottom', fontsize=8, color='#888888')

plt.tight_layout(rect=[0, 0.10, 1, 0.95])
plt.savefig(os.path.join(output_dir, 'solar_cost_combined.png'), dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_cost_combined.png')
