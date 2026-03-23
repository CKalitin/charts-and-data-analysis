import matplotlib.pyplot as plt
import numpy as np
import os
from electrolyzer_data import stack_points, plant_points, stack_estimate_points, plant_estimate_points, handmer_x, handmer_y

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

# --- Overlay line definitions: name -> (x, y, color, linestyle, label) ---
_eff = np.linspace(min(handmer_x), 80, 500)
overlay_lines = {
    '2030_fit': (_eff, -9 * _eff + 760, 'green', '--', '2030 Fit: y = -9x+760'),
}

# --- Export configurations: (filename, [overlay keys to include]) ---
exports = [
    (os.path.join(RESULTS_DIR, 'electrolyzer_cost_vs_eff.png'),          []),
    (os.path.join(RESULTS_DIR, 'electrolyzer_cost_vs_eff_with_fit.png'), ['2030_fit']),
]

# --- Annotation config ---
xy_text_offset = (7, -3)
label_annotation_overrides = {
    'Terraform': ((-7, -3), 'right'),
}

def annotate_point(ax, x, y, label, tech, year, est_eff):
    text = label + ' ' + tech + ' ' + str(year) + ('*' if est_eff else '')
    offset, ha = label_annotation_overrides.get(label, (xy_text_offset, 'left'))
    ax.annotate(text, (x, y), textcoords='offset points', xytext=offset, fontsize=8, ha=ha)

def build_chart(overlay_keys):
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(handmer_x, handmer_y, color='red', linewidth=2, label='Handmer 2024')

    for key in overlay_keys:
        x, y, color, ls, label = overlay_lines[key]
        ax.plot(x, y, color=color, linestyle=ls, linewidth=1.5, alpha=0.5, label=label)

    for x, y, label, tech, year, est_eff in stack_points:
        ax.scatter(x, y, marker='o', color='orange', s=80, zorder=5)
        annotate_point(ax, x, y, label, tech, year, est_eff)

    for x, y, label, tech, year, est_eff in plant_points:
        ax.scatter(x, y, marker='^', color='blue', s=80, zorder=5)
        annotate_point(ax, x, y, label, tech, year, est_eff)

    for x, y, label, tech, year, est_eff in stack_estimate_points:
        ax.scatter(x, y, marker='o', color='orange', s=80, zorder=5, facecolors='none', edgecolors='orange')
        annotate_point(ax, x, y, label, tech, year, est_eff)

    for x, y, label, tech, year, est_eff in plant_estimate_points:
        ax.scatter(x, y, marker='^', color='blue', s=80, zorder=5, facecolors='none', edgecolors='blue')
        annotate_point(ax, x, y, label, tech, year, est_eff)

    ax.scatter([], [], marker='o', color='orange', label='Electrolyzer stack')
    ax.scatter([], [], marker='^', color='blue', label='Full plant')
    ax.scatter([], [], marker='o', facecolors='none', edgecolors='orange', label='Electrolyzer stack (estimate)')
    ax.scatter([], [], marker='^', facecolors='none', edgecolors='blue', label='Full plant (estimate)')

    ax.set_xlim(right=80)
    ax.set_xlabel('Efficiency (kWh/kgH\u2082)')
    ax.set_ylabel('Cost ($/kW)')
    ax.set_title('Electrolyzer Cost vs Efficiency')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.4)

    ax.text(0.5, 0.95, 'Christopher Kalitin 2026', transform=ax.transAxes,
            fontsize=12, color='black', alpha=1.0, ha='center', va='top')
    ax.text(0.01, 0.01, '* = estimated efficiency', transform=ax.transAxes,
            fontsize=8, color='gray', alpha=1.0, ha='left', va='bottom')

    return fig, ax

for filename, overlay_keys in exports:
    fig, ax = build_chart(overlay_keys)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close(fig)

plt.show()
