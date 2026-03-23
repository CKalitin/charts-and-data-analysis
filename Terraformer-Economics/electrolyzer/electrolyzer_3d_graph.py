import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.transforms import Bbox
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d import proj3d
from electrolyzer_data import (stack_points, plant_points,
                                stack_estimate_points, plant_estimate_points,
                                handmer_x, handmer_y)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

# --- Assumptions ---
electricity_price = 0.01
capacity_factor   = 0.25
lifetime_years    = 10
hours_per_year    = 8760

eff_grid  = np.linspace(40, 80, 200)
cost_grid = np.linspace(0, 2200, 200)
EFF, COST = np.meshgrid(eff_grid, cost_grid)

def h2_cost(e, c):
    return e * electricity_price + c * e / (lifetime_years * hours_per_year * capacity_factor)

H2_COST    = h2_cost(EFF, COST)
Z_RANGE    = H2_COST.max() - H2_COST.min()
Z_LINE_LIFT = Z_RANGE * 0   # lift lines just above surface so depth-sorter keeps them visible

# --- Model lines that can be overlaid on the surface ---
# Each entry: (eff_array, capex_array, color, linestyle, label)
def _handmer_line():
    e = np.array(handmer_x)
    c = np.array(handmer_y)
    mask = (e >= eff_grid.min()) & (e <= eff_grid.max()) & \
           (c >= cost_grid.min()) & (c <= cost_grid.max())
    return e[mask], c[mask], 'red', '-', 'Handmer 2024'

def _fit_2030_line():
    e = np.linspace(min(handmer_x), 80, 200)
    c = -9 * e + 760
    mask = (c >= cost_grid.min()) & (c <= cost_grid.max())
    return e[mask], c[mask], 'green', '--', '2030 Fit: capex = -9·eff + 760'

overlay_lines = {
    'handmer':   _handmer_line(),
    '2030_fit':  _fit_2030_line(),
}

# --- Export configurations: (filename, [overlay keys]) ---
exports = [
    ('electrolyzer_3d_graph.png',           []),
    ('electrolyzer_3d_graph_with_lines.png', ['handmer', '2030_fit']),
]

# ---------------------------------------------------------------------------

LABEL_OFFSET_X = 0.013
LABEL_OFFSET_Y = 0.004
LABEL_PAD_PX   = 3
DOT_RADIUS_PX  = 7
MAX_ITER       = 80

def _mtv_push(pos_a, b_a, b_b, pad, fig_h, fig_w, move_both=True):
    ov_x = min(b_a.x1, b_b.x1) - max(b_a.x0, b_b.x0) + pad
    ov_y = min(b_a.y1, b_b.y1) - max(b_a.y0, b_b.y0) + pad
    if ov_x <= 0 or ov_y <= 0:
        return False, None

    if ov_x < ov_y:
        push = ov_x / (2 if move_both else 1) / fig_w
        sign = 1 if (b_a.x0 + b_a.x1) >= (b_b.x0 + b_b.x1) else -1
        pos_a[0] += sign * push
        delta = (-sign * push, 0)
    else:
        push = ov_y / (2 if move_both else 1) / fig_h
        sign = 1 if (b_a.y0 + b_a.y1) >= (b_b.y0 + b_b.y1) else -1
        pos_a[1] += sign * push
        delta = (0, -sign * push)

    return True, delta


def build_figure(overlay_keys):
    point_data      = []
    overlay_artists = []
    in_draw         = [False]

    def collect_points(points, marker, facecolor, edgecolor):
        for x, y, label, tech, year, est_eff in points:
            if x < 40 or x > 80:
                continue
            z = h2_cost(x, y)
            text = f'{label} {tech} {year} ${z:.2f}/kg{"*" if est_eff else ""}'
            point_data.append((x, y, z, text, facecolor, edgecolor, marker))

    collect_points(stack_points,          'o', 'orange', 'none')
    collect_points(plant_points,          '^', 'blue',   'none')
    collect_points(stack_estimate_points, 'o', 'none',   'orange')
    collect_points(plant_estimate_points, '^', 'none',   'blue')

    fig = plt.figure(figsize=(10, 10))
    ax  = fig.add_subplot(111, projection='3d')

    ax.plot_surface(EFF, COST, H2_COST, cmap='viridis_r',
                    alpha=0.6, rcount=100, ccount=100, antialiased=True)

    # Draw model lines on the surface
    for key in overlay_keys:
        e_line, c_line, color, ls, lbl = overlay_lines[key]
        z_line = h2_cost(e_line, c_line) + Z_LINE_LIFT
        ax.plot3D(e_line, c_line, z_line,
                  color=color, linewidth=2.5, linestyle=ls, label=lbl, zorder=5)
    if overlay_keys:
        ax.legend(loc='upper right', fontsize=9)

    # --- draw_event: project points to 2D figure space, resolve label overlaps ---
    def on_draw(_event):
        if in_draw[0]:
            return
        in_draw[0] = True

        while overlay_artists:
            overlay_artists.pop().remove()

        proj     = ax.get_proj()
        renderer = fig.canvas.get_renderer()
        fig_h    = fig.get_figheight() * fig.dpi
        fig_w    = fig.get_figwidth()  * fig.dpi

        dot_fig = []
        for x3d, y3d, z3d, *_ in point_data:
            xs, ys, _ = proj3d.proj_transform(x3d, y3d, z3d, proj)
            xd, yd    = ax.transData.transform((xs, ys))
            xf, yf    = fig.transFigure.inverted().transform((xd, yd))
            dot_fig.append((xf, yf))

        dot_px = []
        for (xf, yf) in dot_fig:
            xd, yd = fig.transFigure.transform((xf, yf))
            r = DOT_RADIUS_PX
            dot_px.append(Bbox([[xd - r, yd - r], [xd + r, yd + r]]))

        for (xf, yf), (_, _, _, _, fc, ec, mk) in zip(dot_fig, point_data):
            dot = mlines.Line2D([xf], [yf], transform=fig.transFigure,
                                marker=mk, markerfacecolor=fc,
                                markeredgecolor=ec, markeredgewidth=1,
                                markersize=8, linestyle='none')
            fig.add_artist(dot)
            overlay_artists.append(dot)

        lbl_pos     = [[xf + LABEL_OFFSET_X, yf + LABEL_OFFSET_Y] for xf, yf in dot_fig]
        lbl_artists = []
        for (lx, ly), (_, _, _, text, *_) in zip(lbl_pos, point_data):
            t = fig.text(lx, ly, text, fontsize=7, va='center')
            overlay_artists.append(t)
            lbl_artists.append(t)

        for _ in range(MAX_ITER):
            moved = False

            # Label-label repulsion — refresh bbox for i after every move so
            # subsequent pairs (i, k) use i's actual current position, not a
            # stale snapshot from the start of the outer iteration.
            for i in range(len(lbl_artists)):
                bi = lbl_artists[i].get_window_extent(renderer)
                for j in range(i + 1, len(lbl_artists)):
                    bj = lbl_artists[j].get_window_extent(renderer)
                    did_move, delta = _mtv_push(
                        lbl_pos[i], bi, bj,
                        LABEL_PAD_PX, fig_h, fig_w, move_both=True)
                    if did_move:
                        lbl_pos[j][0] += delta[0]
                        lbl_pos[j][1] += delta[1]
                        lbl_artists[i].set_position(lbl_pos[i])
                        lbl_artists[j].set_position(lbl_pos[j])
                        bi = lbl_artists[i].get_window_extent(renderer)
                        moved = True

            # Label-dot repulsion — use fresh bbox per label (label-label pass
            # above may have already moved this label).
            for i in range(len(lbl_artists)):
                bi = lbl_artists[i].get_window_extent(renderer)
                for dot_bbox in dot_px:
                    did_move, _ = _mtv_push(
                        lbl_pos[i], bi, dot_bbox,
                        LABEL_PAD_PX, fig_h, fig_w, move_both=False)
                    if did_move:
                        lbl_artists[i].set_position(lbl_pos[i])
                        bi = lbl_artists[i].get_window_extent(renderer)
                        moved = True

            if not moved:
                break

        bboxes = [t.get_window_extent(renderer) for t in lbl_artists]
        for (xf, yf), bbox in zip(dot_fig, bboxes):
            xd_dot, _ = fig.transFigure.transform((xf, yf))
            lx_px = bbox.x0 if xd_dot < (bbox.x0 + bbox.x1) / 2 else bbox.x1
            ly_px = (bbox.y0 + bbox.y1) / 2
            lx_fig, ly_fig = fig.transFigure.inverted().transform((lx_px, ly_px))
            line = mlines.Line2D([xf, lx_fig], [yf, ly_fig],
                                 transform=fig.transFigure,
                                 color='gray', linewidth=0.6, alpha=0.6, linestyle='--')
            fig.add_artist(line)
            overlay_artists.append(line)

        in_draw[0] = False

    fig.canvas.mpl_connect('draw_event', on_draw)

    ax.set_xlabel('Efficiency (kWh/kgH\u2082)', labelpad=12)
    ax.set_ylabel('Capex ($/kW)', labelpad=12)
    ax.set_zlabel('H\u2082 Cost ($/kgH\u2082)', labelpad=122)
    ax.set_title('Electrolyzer H\u2082 Cost vs Efficiency & Capex\n'
                 f'($0.01/kWh electricity, {int(capacity_factor*100)}% CF, {lifetime_years}yr lifetime)',
                 fontsize=18)

    fig.text(0.5, 0.90, 'Christopher Kalitin 2026', ha='center', fontsize=14, color='black')
    fig.text(0.12, 0.05, '* = estimated efficiency', ha='left', fontsize=10, color='gray')

    return fig


for filename, overlay_keys in exports:
    fig = build_figure(overlay_keys)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, filename), dpi=150)
    plt.close(fig)
