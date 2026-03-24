import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
import os
from matplotlib.transforms import Bbox
from electrolyzer_data import stack_points, plant_points, stack_estimate_points, plant_estimate_points, handmer_x, handmer_y

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

# --- Heatmap grid (efficiency x capex -> H2 cost) ---
electricity_price = 0.01
capacity_factor   = 0.25
lifetime_years    = 10
hours_per_year    = 8760

eff_grid  = np.linspace(40, 80, 400)
cost_grid = np.linspace(0, 2200, 400)
EFF, COST = np.meshgrid(eff_grid, cost_grid)

def h2_cost(e, c):
    return e * electricity_price + c * e / (lifetime_years * hours_per_year * capacity_factor)

H2_COST = h2_cost(EFF, COST)

# --- Overlay line definitions ---
_eff = np.linspace(min(handmer_x), 80, 500)
overlay_lines = {
    '2030_fit': (_eff, -9 * _eff + 760, 'green', '--', '2030 Fit: y = -9x+760'),
}

# --- Export configurations ---
exports = [
    (os.path.join(RESULTS_DIR, 'electrolyzer_heatmap.png'),          []),
    (os.path.join(RESULTS_DIR, 'electrolyzer_heatmap_with_fit.png'), ['2030_fit']),
]

# --- Label repulsion constants ---
LABEL_OFFSET_X = 0.013   # initial x offset from dot (figure fraction)
LABEL_OFFSET_Y = 0.004
LABEL_PAD_PX   = 3
DOT_RADIUS_PX  = 7
MAX_ITER       = 80

# Per-label initial placement overrides: label name -> (offset_x, offset_y)
# Use negative offset_x to start left of the dot (e.g. points at the right edge).
INITIAL_OFFSET_OVERRIDES = {
    'Terraform': (-LABEL_OFFSET_X, LABEL_OFFSET_Y),
}

def _mtv_push(pos_a, b_a, b_b, pad, fig_h, fig_w):
    """Push pos_a away from b_b using minimum translation vector. Only moves a."""
    ov_x = min(b_a.x1, b_b.x1) - max(b_a.x0, b_b.x0) + pad
    ov_y = min(b_a.y1, b_b.y1) - max(b_a.y0, b_b.y0) + pad
    if ov_x <= 0 or ov_y <= 0:
        return False
    if ov_x < ov_y:
        sign = 1 if (b_a.x0 + b_a.x1) >= (b_b.x0 + b_b.x1) else -1
        pos_a[0] += sign * ov_x / fig_w
    else:
        sign = 1 if (b_a.y0 + b_a.y1) >= (b_b.y0 + b_b.y1) else -1
        pos_a[1] += sign * ov_y / fig_h
    return True

def _place_labels(fig, ax, label_data):
    """
    Place labels with H2 cost, resolve all overlaps (label-label and label-dot),
    and draw dotted connector lines. label_data: [(x, y, text), ...]
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_h    = fig.get_figheight() * fig.dpi
    fig_w    = fig.get_figwidth()  * fig.dpi

    # Project dot positions to figure-fraction space
    dot_fig = []
    for x, y, _ in label_data:
        xd, yd = ax.transData.transform((x, y))
        dot_fig.append(fig.transFigure.inverted().transform((xd, yd)))

    # Fixed dot obstacle bboxes (display pixels)
    dot_px = []
    for xf, yf in dot_fig:
        xd, yd = fig.transFigure.transform((xf, yf))
        dot_px.append(Bbox([[xd - DOT_RADIUS_PX, yd - DOT_RADIUS_PX],
                             [xd + DOT_RADIUS_PX, yd + DOT_RADIUS_PX]]))

    # Initial label positions and artists (figure-fraction coords)
    # Per-label overrides let edge-of-chart points start on the correct side.
    lbl_pos = []
    for (xf, yf), (_, _, text) in zip(dot_fig, label_data):
        name = text.split()[0]  # first word is the company/label name
        ox, oy = INITIAL_OFFSET_OVERRIDES.get(name, (LABEL_OFFSET_X, LABEL_OFFSET_Y))
        lbl_pos.append([xf + ox, yf + oy])
    lbl_artists = [fig.text(lx, ly, text, fontsize=8, va='center')
                   for (lx, ly), (_, _, text) in zip(lbl_pos, label_data)]

    # Unified repulsion: only label i moves; bbox refreshed after every push
    for _ in range(MAX_ITER):
        moved = False
        for i in range(len(lbl_artists)):
            bi = lbl_artists[i].get_window_extent(renderer)
            for j in range(len(lbl_artists)):
                if j == i:
                    continue
                bj = lbl_artists[j].get_window_extent(renderer)
                if _mtv_push(lbl_pos[i], bi, bj, LABEL_PAD_PX, fig_h, fig_w):
                    lbl_artists[i].set_position(lbl_pos[i])
                    bi = lbl_artists[i].get_window_extent(renderer)
                    moved = True
            for dot_bbox in dot_px:
                if _mtv_push(lbl_pos[i], bi, dot_bbox, LABEL_PAD_PX, fig_h, fig_w):
                    lbl_artists[i].set_position(lbl_pos[i])
                    bi = lbl_artists[i].get_window_extent(renderer)
                    moved = True
        if not moved:
            break

    # Connector lines: dot -> nearest horizontal edge of label
    bboxes = [t.get_window_extent(renderer) for t in lbl_artists]
    for (xf, yf), bbox in zip(dot_fig, bboxes):
        xd_dot, _ = fig.transFigure.transform((xf, yf))
        lx_px  = bbox.x0 if xd_dot < (bbox.x0 + bbox.x1) / 2 else bbox.x1
        ly_px  = (bbox.y0 + bbox.y1) / 2
        lx_fig, ly_fig = fig.transFigure.inverted().transform((lx_px, ly_px))
        fig.add_artist(mlines.Line2D([xf, lx_fig], [yf, ly_fig],
                                     transform=fig.transFigure,
                                     color='gray', linewidth=0.6, alpha=0.7, linestyle=':'))


def build_chart(overlay_keys):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Heatmap background
    pcm = ax.pcolormesh(EFF, COST, H2_COST, cmap='plasma_r', shading='auto', zorder=0)
    cbar = fig.colorbar(pcm, ax=ax, pad=0.02)
    cbar.set_label('H\u2082 Cost ($/kgH\u2082)', fontsize=9)

    ax.plot(handmer_x, handmer_y, color='red', linewidth=2, label='Handmer 2024', zorder=3)

    for key in overlay_keys:
        x, y, color, ls, label = overlay_lines[key]
        ax.plot(x, y, color=color, linestyle=ls, linewidth=1.5, alpha=0.8, label=label, zorder=3)

    # Collect label data while scattering points
    label_data = []

    def scatter_and_collect(points, marker, color, hollow):
        for x, y, label, tech, year, est_eff in points:
            cost = h2_cost(x, y)
            text = f'{label} {tech} {year} ${cost:.2f}/kg{"*" if est_eff else ""}'
            label_data.append((x, y, text))
            if hollow:
                ax.scatter(x, y, marker=marker, facecolors='none', edgecolors=color, s=80, zorder=5)
            else:
                ax.scatter(x, y, marker=marker, color=color, s=80, zorder=5)

    scatter_and_collect(stack_points,          'o', 'orange', False)
    scatter_and_collect(plant_points,          '^', 'blue',   False)
    scatter_and_collect(stack_estimate_points, 'o', 'orange', True)
    scatter_and_collect(plant_estimate_points, '^', 'blue',   True)

    ax.scatter([], [], marker='o', color='orange', label='Electrolyzer stack')
    ax.scatter([], [], marker='^', color='blue',   label='Full plant')
    ax.scatter([], [], marker='o', facecolors='none', edgecolors='orange', label='Electrolyzer stack (estimate)')
    ax.scatter([], [], marker='^', facecolors='none', edgecolors='blue',   label='Full plant (estimate)')

    ax.set_xlim(min(handmer_x), 80)
    ax.set_ylim(0, 2200)
    ax.set_xlabel('Efficiency (kWh/kgH\u2082)')
    ax.set_ylabel('Capex ($/kW)')
    ax.set_title('Electrolyzer Cost vs Efficiency (H\u2082 Cost Heatmap)')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3, zorder=1)

    ax.text(0.5, 0.95, 'Christopher Kalitin 2026', transform=ax.transAxes,
            fontsize=12, color='white', alpha=1.0, ha='center', va='top')
    ax.text(0.01, 0.01, '* = estimated efficiency, $0.01/kWh, 25% CF, 10 yr amortization', transform=ax.transAxes,
            fontsize=8, color='gray', alpha=1.0, ha='left', va='bottom')

    plt.tight_layout()
    _place_labels(fig, ax, label_data)

    return fig, ax

for filename, overlay_keys in exports:
    fig, ax = build_chart(overlay_keys)
    plt.savefig(filename, dpi=150)
    plt.close(fig)

plt.show()
