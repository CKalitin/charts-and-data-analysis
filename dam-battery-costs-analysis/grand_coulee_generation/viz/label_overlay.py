"""Non-overlapping point labels drawn in FIGURE space — works for 2D and 3D charts.

WHAT PROBLEM THIS SOLVES
========================
Two hard, recurring labelling problems, solved once:

1. 3D occlusion. On a 3D surface plotted with alpha < 1, anything you draw *in the 3D axes*
   (a scatter point, an ax.text) gets depth-sorted against the surface and disappears behind
   it. Nudging z ("lift the label above the surface") is fragile and breaks on rotation.
   The robust fix: don't draw the markers/labels in the 3D axes at all. Project each 3D data
   point to 2D figure-fraction coordinates and draw the dot, its label, and a leader line as
   FIGURE-LEVEL artists (fig.add_artist / fig.text). Figure artists render on top of the axes
   unconditionally — no depth sorting, no occlusion, ever.

2. Label collision. When many points cluster, their labels overlap into mush. This module
   resolves overlaps with an iterative minimum-translation-vector (MTV) push: each label is
   shoved out of any label-label or label-dot overlap along the axis of least penetration,
   re-measuring its bounding box after every move, until nothing overlaps (or MAX_ITER).
   A dotted leader line then connects each dot to its (possibly displaced) label.

The 2D case is the same machinery minus the projection step: the dot positions come straight
from ax.transData instead of a 3D projection.

WHY FIGURE COORDINATES
======================
Bounding-box overlap tests need a single, stable coordinate system. Figure fraction (0..1
over the whole canvas) is that system: it's where fig.text lives, it survives 3D rotation
(we recompute on every draw for 3D), and pixel<->fraction conversion is a simple transform.

USAGE (2D)
==========
    from label_overlay import LabelPoint, place_labels_2d
    pts = [LabelPoint(x=eff, y=capex, text=f"{name} ${cost:.2f}/kg",
                      marker="o", facecolor="orange", edgecolor="none") for ...]
    fig, ax = ...                      # draw your heatmap / scatter first
    place_labels_2d(fig, ax, pts)      # call AFTER tight/constrained layout is settled
    fig.savefig(...)

USAGE (3D)
==========
    from label_overlay import LabelPoint, attach_labels_3d
    pts = [LabelPoint(x=eff, y=capex, z=cost, text=..., marker="^",
                      facecolor="none", edgecolor="blue") for ...]
    # Connect on draw_event so labels re-project whenever the view rotates / figure redraws.
    attach_labels_3d(fig, ax, pts)
    fig.savefig(...)                   # for a static export this draws once, which is enough

TUNING
======
LABEL_OFFSET_(X|Y)  initial label offset from its dot (figure fraction)
LABEL_PAD_PX        minimum gap enforced between boxes (pixels)
DOT_RADIUS_PX       treat each dot as a circle of this radius for label-dot repulsion
MAX_ITER            de-collision iteration cap
initial_offsets     per-label first-guess offset overrides, keyed by the label's first word
                    — use a negative x for points near the right edge so the label starts on
                    the correct side instead of running off-canvas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import matplotlib.lines as mlines
from matplotlib.transforms import Bbox

# --- Tunables (sensible defaults; override via the function kwargs) --------------------
LABEL_OFFSET_X = 0.013
LABEL_OFFSET_Y = 0.004
LABEL_PAD_PX = 3.0
DOT_RADIUS_PX = 7.0
MAX_ITER = 80
LABEL_FONTSIZE = 8.0
LEADER_KW = dict(color="gray", linewidth=0.6, alpha=0.7, linestyle=":")


@dataclass
class LabelPoint:
    """One point to mark + label. z is used only for the 3D path."""
    x: float
    y: float
    text: str
    z: float | None = None
    marker: str = "o"
    facecolor: object = "none"
    edgecolor: object = "black"
    markersize: float = 8.0
    text_color: object = None   # defaults to matplotlib default when None


def _mtv_push(pos_a, b_a, b_b, pad, fig_h, fig_w, move_both):
    """Push box a out of box b along the minimum-translation axis.

    Returns (did_move, delta_for_b). If move_both, each box moves half the overlap and the
    caller applies `delta` to b; otherwise a takes the full push (used against fixed dot
    obstacles, which must not move). pos_a is mutated in place (figure-fraction coords).
    """
    ov_x = min(b_a.x1, b_b.x1) - max(b_a.x0, b_b.x0) + pad
    ov_y = min(b_a.y1, b_b.y1) - max(b_a.y0, b_b.y0) + pad
    if ov_x <= 0 or ov_y <= 0:
        return False, (0.0, 0.0)

    if ov_x < ov_y:
        push = ov_x / (2 if move_both else 1) / fig_w
        sign = 1 if (b_a.x0 + b_a.x1) >= (b_b.x0 + b_b.x1) else -1
        pos_a[0] += sign * push
        return True, (-sign * push, 0.0)
    else:
        push = ov_y / (2 if move_both else 1) / fig_h
        sign = 1 if (b_a.y0 + b_a.y1) >= (b_b.y0 + b_b.y1) else -1
        pos_a[1] += sign * push
        return True, (0.0, -sign * push)


def _resolve_and_draw(fig, dot_fig, points, *, offset_x, offset_y, pad_px, dot_radius_px,
                      max_iter, fontsize, initial_offsets, draw_dots, bounds=None):
    """Core: given dot positions in figure fraction, draw (optional) dots, de-collide labels,
    draw leader lines. Returns the list of created figure artists (so a 3D redraw can remove
    them before redrawing)."""
    artists = []
    renderer = fig.canvas.get_renderer()
    fig_h = fig.get_figheight() * fig.dpi
    fig_w = fig.get_figwidth() * fig.dpi

    # Fixed dot obstacles, as pixel bboxes.
    dot_px = []
    for (xf, yf) in dot_fig:
        xd, yd = fig.transFigure.transform((xf, yf))
        dot_px.append(Bbox([[xd - dot_radius_px, yd - dot_radius_px],
                            [xd + dot_radius_px, yd + dot_radius_px]]))

    # Optional dot markers (the 3D path draws its own dots here since the in-axes ones are
    # occluded; the 2D path usually already scattered them, so draw_dots=False there).
    if draw_dots:
        for (xf, yf), p in zip(dot_fig, points):
            dot = mlines.Line2D([xf], [yf], transform=fig.transFigure, marker=p.marker,
                                markerfacecolor=p.facecolor, markeredgecolor=p.edgecolor,
                                markeredgewidth=1, markersize=p.markersize, linestyle="none")
            fig.add_artist(dot)
            artists.append(dot)

    # Initial label positions + artists.
    lbl_pos = []
    for (xf, yf), p in zip(dot_fig, points):
        key = p.text.split()[0] if p.text else ""
        ox, oy = initial_offsets.get(key, (offset_x, offset_y))
        lbl_pos.append([xf + ox, yf + oy])
    lbl_artists = [fig.text(lx, ly, p.text, fontsize=fontsize, va="center",
                            **({"color": p.text_color} if p.text_color is not None else {}))
                   for (lx, ly), p in zip(lbl_pos, points)]
    artists.extend(lbl_artists)

    # Iterative de-collision.
    for _ in range(max_iter):
        moved = False
        # Label-label: move both halves. Refresh i's bbox after each push so subsequent pairs
        # use its CURRENT position, not a stale snapshot from the top of the iteration.
        for i in range(len(lbl_artists)):
            bi = lbl_artists[i].get_window_extent(renderer)
            for j in range(i + 1, len(lbl_artists)):
                bj = lbl_artists[j].get_window_extent(renderer)
                did, delta = _mtv_push(lbl_pos[i], bi, bj, pad_px, fig_h, fig_w, move_both=True)
                if did:
                    lbl_pos[j][0] += delta[0]
                    lbl_pos[j][1] += delta[1]
                    lbl_artists[i].set_position(lbl_pos[i])
                    lbl_artists[j].set_position(lbl_pos[j])
                    bi = lbl_artists[i].get_window_extent(renderer)
                    moved = True
        # Label-dot: dots are fixed obstacles, so only the label moves.
        for i in range(len(lbl_artists)):
            bi = lbl_artists[i].get_window_extent(renderer)
            for dot_bbox in dot_px:
                did, _ = _mtv_push(lbl_pos[i], bi, dot_bbox, pad_px, fig_h, fig_w, move_both=False)
                if did:
                    lbl_artists[i].set_position(lbl_pos[i])
                    bi = lbl_artists[i].get_window_extent(renderer)
                    moved = True
        # Clamp labels to stay within the supplied bounds (figure-fraction).
        if bounds is not None:
            x0b, y0b, x1b, y1b = bounds
            for i, t in enumerate(lbl_artists):
                bi = t.get_window_extent(renderer)
                bw = (bi.x1 - bi.x0) / fig_w
                bh = (bi.y1 - bi.y0) / fig_h
                lbl_pos[i][0] = max(x0b, min(x1b - bw, lbl_pos[i][0]))
                lbl_pos[i][1] = max(y0b, min(y1b - bh, lbl_pos[i][1]))
                t.set_position(lbl_pos[i])
        if not moved:
            break

    # Leader lines: dot -> nearest horizontal edge of the (settled) label box.
    for (xf, yf), t in zip(dot_fig, lbl_artists):
        bbox = t.get_window_extent(renderer)
        xd_dot, _ = fig.transFigure.transform((xf, yf))
        lx_px = bbox.x0 if xd_dot < (bbox.x0 + bbox.x1) / 2 else bbox.x1
        ly_px = (bbox.y0 + bbox.y1) / 2
        lx_fig, ly_fig = fig.transFigure.inverted().transform((lx_px, ly_px))
        line = mlines.Line2D([xf, lx_fig], [yf, ly_fig], transform=fig.transFigure, **LEADER_KW)
        fig.add_artist(line)
        artists.append(line)

    return artists


def place_labels_2d(fig, ax, points: Sequence[LabelPoint], *,
                    offset_x=LABEL_OFFSET_X, offset_y=LABEL_OFFSET_Y,
                    pad_px=LABEL_PAD_PX, dot_radius_px=DOT_RADIUS_PX, max_iter=MAX_ITER,
                    fontsize=LABEL_FONTSIZE, initial_offsets=None, draw_dots=False):
    """Label points on a 2D Axes. Call AFTER your layout is settled (constrained_layout /
    tight_layout), because label positions are computed from the final pixel geometry.

    draw_dots defaults False: you've usually already ax.scatter'd the markers. Set True to
    have this draw them as figure artists too (rarely needed in 2D).
    """
    fig.canvas.draw()  # ensure transforms + renderer are current
    dot_fig = []
    for p in points:
        xd, yd = ax.transData.transform((p.x, p.y))
        dot_fig.append(tuple(fig.transFigure.inverted().transform((xd, yd))))
    # Axes bounding box in figure-fraction coords — labels are clamped inside this.
    pos = ax.get_position()
    bounds = (pos.x0, pos.y0, pos.x1, pos.y1)
    return _resolve_and_draw(fig, dot_fig, points, offset_x=offset_x, offset_y=offset_y,
                             pad_px=pad_px, dot_radius_px=dot_radius_px, max_iter=max_iter,
                             fontsize=fontsize, initial_offsets=initial_offsets or {},
                             draw_dots=draw_dots, bounds=bounds)


def attach_labels_3d(fig, ax, points: Sequence[LabelPoint], *,
                     offset_x=LABEL_OFFSET_X, offset_y=LABEL_OFFSET_Y,
                     pad_px=LABEL_PAD_PX, dot_radius_px=DOT_RADIUS_PX, max_iter=MAX_ITER,
                     fontsize=LABEL_FONTSIZE, initial_offsets=None):
    """Label points on a 3D Axes WITHOUT occlusion. Markers + labels are drawn as figure
    artists (always on top of the semi-transparent surface). Hooks draw_event so the overlay
    re-projects and re-resolves whenever the figure redraws (e.g. interactive rotation); for a
    one-shot savefig this simply runs once. Every LabelPoint needs a z.

    The marker dots ARE drawn here (draw_dots=True), since in-axes 3D markers would be the very
    thing that disappears behind the surface.
    """
    from mpl_toolkits.mplot3d import proj3d  # local import keeps the 2D path mpl3d-free

    initial_offsets = initial_offsets or {}
    state = {"artists": [], "in_draw": False}

    def on_draw(_event=None):
        if state["in_draw"]:
            return
        state["in_draw"] = True
        try:
            while state["artists"]:
                state["artists"].pop().remove()

            proj = ax.get_proj()
            dot_fig = []
            for p in points:
                xs, ys, _ = proj3d.proj_transform(p.x, p.y, p.z, proj)
                xd, yd = ax.transData.transform((xs, ys))
                dot_fig.append(tuple(fig.transFigure.inverted().transform((xd, yd))))

            state["artists"] = _resolve_and_draw(
                fig, dot_fig, points, offset_x=offset_x, offset_y=offset_y, pad_px=pad_px,
                dot_radius_px=dot_radius_px, max_iter=max_iter, fontsize=fontsize,
                initial_offsets=initial_offsets, draw_dots=True)
        finally:
            state["in_draw"] = False

    fig.canvas.mpl_connect("draw_event", on_draw)
    fig.canvas.draw()  # trigger an initial placement so a headless savefig has labels
    return on_draw
