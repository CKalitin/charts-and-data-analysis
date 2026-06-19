"""Auto-placed info boxes — the thing matplotlib gives legends (loc='best') but not text.

A model chart should always state the input parameters that produced it (see SKILL.md: this
takes taste — axis limits, and the model inputs that actually move the result). That text has
to go somewhere that doesn't bury the data. matplotlib has no 'best' for arbitrary text, so we
build it.

TWO PLACEMENTS
==============
mode="on"   The box floats INSIDE the axes, auto-positioned to the emptiest region. We measure
            the box once, then SCAN a fine grid of candidate positions and score each by what it
            would cover, in a STRICT PRIORITY ORDER (the rule that actually matters on a busy
            chart):
                1. never cover a TEXT label  (contour clabels, annotations, legend text)
                2. then, avoid LINES         (plotted curves AND contour lines)
                3. then, avoid other data    (scatter points) and prefer a corner
            The lowest-score position wins. This is what keeps the box off the "95%" contour and
            its label on a heatmap, landing it in the genuinely empty corner instead.
mode="off"  The box sits OUTSIDE the plot in a reserved margin (default: to the right). Use this
            when the box is large enough that no in-axes spot is clean. We shrink the axes to
            make room so the box never overlaps the data at all.

Call AFTER the data + other artists are drawn (occupancy is measured from what's on the axes)
and after layout settles. Returns the created Text artist.

WHY A SCAN + PRIORITISED OCCUPANCY (and not scipy/anything heavy)
=================================================================
"Best location" = render the box at each candidate, see what's under it, choose the clearest.
We do exactly that, cheaply: measure the box's pixel size ONCE (a single draw), then slide that
rectangle over a grid of positions doing pure-arithmetic overlap tests. Occupancy is split by
artist KIND so we can rank text-overlap above line-overlap above everything — the priority that
a human applies by eye. No extra deps, fast enough to call on every chart in a sweep.
"""

from __future__ import annotations

import numpy as np
from matplotlib.collections import PathCollection, QuadMesh
from matplotlib.text import Text
from matplotlib.transforms import Bbox

BOX_KW = dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor="0.7")
PAD_FRAC = 0.02              # inset from the axes edge for candidate positions (axes fraction)
TEXT_PAD_PX = 5             # inflate text bboxes so the box keeps visible clearance from labels
SCAN_N = 24                 # candidate grid resolution per axis (24×24 positions)
MAX_SAMPLE_PTS = 4000       # cap on sampled line/scatter points (uniform stride) for speed

# Score weights — chosen so the priority is effectively lexicographic:
# any text overlap dominates any amount of line overlap, which dominates scatter + corner bias.
W_TEXT = 100.0              # × fraction of the box area covered by text bboxes
W_LINE = 10.0              # × fraction of line/contour points falling inside the box
W_SCAT = 3.0               # × fraction of scatter points inside the box
W_CORNER = 0.5             # × normalized distance from the nearest axes corner (tie-breaker)


# --------------------------------------------------------------------------- #
# Occupancy collection (split by artist KIND so scoring can prioritise)
# --------------------------------------------------------------------------- #
def _subsample(pts: np.ndarray) -> np.ndarray:
    if len(pts) > MAX_SAMPLE_PTS:
        return pts[:: int(np.ceil(len(pts) / MAX_SAMPLE_PTS))]
    return pts


def _line_and_scatter_px(ax, fig):
    """Pixel coords of (line/contour vertices, scatter points), clipped to the axes box.

    Lines include Line2D AND any path-based collection (contour LineCollections / ContourSets) —
    the latter is what the old version missed, letting boxes land on contour curves.
    """
    renderer = fig.canvas.get_renderer()
    bbox = ax.get_window_extent(renderer)
    line_pts, scat_pts = [], []

    for ln in ax.get_lines():
        xy = np.column_stack([ln.get_xdata(), ln.get_ydata()])
        if len(xy):
            line_pts.append(ax.transData.transform(xy))

    for coll in ax.collections:
        if isinstance(coll, QuadMesh):
            continue                       # the heatmap background covers everything — ignore it
        if isinstance(coll, PathCollection):   # scatter
            off = coll.get_offsets()
            if off is not None and len(off):
                scat_pts.append(ax.transData.transform(np.asarray(off)))
            continue
        # LineCollection / ContourSet and friends: pull vertices from the paths (data coords).
        verts = [p.vertices for p in coll.get_paths() if len(p.vertices)]
        if verts:
            line_pts.append(ax.transData.transform(np.vstack(verts)))

    def _finish(chunks):
        if not chunks:
            return np.empty((0, 2))
        P = np.vstack(chunks)
        inside = ((P[:, 0] >= bbox.x0) & (P[:, 0] <= bbox.x1) &
                  (P[:, 1] >= bbox.y0) & (P[:, 1] <= bbox.y1))
        return _subsample(P[inside])

    return _finish(line_pts), _finish(scat_pts), bbox


def _text_bboxes(ax, fig):
    """Pixel bboxes of every TEXT label drawn within the axes — the highest-priority
    thing to avoid (contour clabels, annotations, legend entries). Structural text
    (title, axis labels, tick labels) is excluded; it lives outside the data area."""
    renderer = fig.canvas.get_renderer()
    ax_bbox = ax.get_window_extent(renderer)
    exclude = {ax.title, ax.xaxis.label, ax.yaxis.label}
    exclude |= set(ax.get_xticklabels()) | set(ax.get_yticklabels())

    out = []
    for t in ax.findobj(Text):
        if t in exclude or not t.get_text().strip():
            continue
        try:
            bb = t.get_window_extent(renderer)
        except Exception:
            continue
        # Keep only labels that actually sit inside the axes drawing area.
        if bb.x1 > ax_bbox.x0 and bb.x0 < ax_bbox.x1 and bb.y1 > ax_bbox.y0 and bb.y0 < ax_bbox.y1:
            # Inflate by TEXT_PAD_PX on each side — ensures visible clearance even when
            # the box doesn't technically overlap the label.
            out.append(Bbox([[bb.x0 - TEXT_PAD_PX, bb.y0 - TEXT_PAD_PX],
                             [bb.x1 + TEXT_PAD_PX, bb.y1 + TEXT_PAD_PX]]))

    leg = ax.get_legend()
    if leg is not None:
        lb = leg.get_window_extent(renderer)
        out.append(Bbox([[lb.x0 - TEXT_PAD_PX, lb.y0 - TEXT_PAD_PX],
                         [lb.x1 + TEXT_PAD_PX, lb.y1 + TEXT_PAD_PX]]))
    return out


# --------------------------------------------------------------------------- #
# Box measurement + scan
# --------------------------------------------------------------------------- #
def _measure_box_px(ax, fig, text, fontsize):
    """Render the box once to get its pixel width/height, then remove it."""
    renderer = fig.canvas.get_renderer()
    t = ax.text(0.5, 0.5, text, transform=ax.transAxes, ha="left", va="bottom",
                fontsize=fontsize, bbox=BOX_KW)
    fig.canvas.draw()
    tb = t.get_window_extent(renderer)
    t.remove()
    return tb.width, tb.height


def _overlap_area(ax0, ay0, ax1, ay1, bb):
    dx = max(0.0, min(ax1, bb.x1) - max(ax0, bb.x0))
    dy = max(0.0, min(ay1, bb.y1) - max(ay0, bb.y0))
    return dx * dy


def _count_inside(pts, x0, y0, x1, y1):
    if not len(pts):
        return 0
    return int(((pts[:, 0] >= x0) & (pts[:, 0] <= x1) &
                (pts[:, 1] >= y0) & (pts[:, 1] <= y1)).sum())


def _best_position(ax_bbox, w, h, text_bboxes, line_pts, scat_pts):
    """Slide the w×h box over a grid inside the axes; return the lowest-score (x0, y0)."""
    pad_x, pad_y = PAD_FRAC * ax_bbox.width, PAD_FRAC * ax_bbox.height
    x_lo, x_hi = ax_bbox.x0 + pad_x, ax_bbox.x1 - pad_x - w
    y_lo, y_hi = ax_bbox.y0 + pad_y, ax_bbox.y1 - pad_y - h
    # Box larger than the axes in a dimension: clamp to the low edge.
    xs = np.linspace(x_lo, x_hi, SCAN_N) if x_hi > x_lo else np.array([ax_bbox.x0 + pad_x])
    ys = np.linspace(y_lo, y_hi, SCAN_N) if y_hi > y_lo else np.array([ax_bbox.y0 + pad_y])

    box_area = max(1.0, w * h)
    corners = [(ax_bbox.x0, ax_bbox.y0), (ax_bbox.x1, ax_bbox.y0),
               (ax_bbox.x0, ax_bbox.y1), (ax_bbox.x1, ax_bbox.y1)]
    diag = float(np.hypot(ax_bbox.width, ax_bbox.height)) or 1.0
    n_line, n_scat = max(1, len(line_pts)), max(1, len(scat_pts))

    best, best_xy = None, (xs[0], ys[0])
    for x0 in xs:
        for y0 in ys:
            x1, y1 = x0 + w, y0 + h
            text_cov = sum(_overlap_area(x0, y0, x1, y1, bb) for bb in text_bboxes) / box_area
            line_cov = _count_inside(line_pts, x0, y0, x1, y1) / n_line
            scat_cov = _count_inside(scat_pts, x0, y0, x1, y1) / n_scat
            cx, cy = x0 + w / 2, y0 + h / 2
            corner = min(np.hypot(cx - px, cy - py) for px, py in corners) / diag
            score = W_TEXT * text_cov + W_LINE * line_cov + W_SCAT * scat_cov + W_CORNER * corner
            if best is None or score < best:
                best, best_xy = score, (x0, y0)
    return best_xy


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def add_watermark(ax, fig, text: str, *,
                  fontsize: float = 9.0, alpha: float = 0.32,
                  color: str = "black") -> None:
    """Auto-place a faint attribution text inside the axes at the emptiest spot.

    Uses the identical scan as add_info_box (so it avoids the info box if one
    was already placed) but renders plain text with no background box and low
    alpha — the watermark reads *below* data rather than on top of it.
    Call AFTER add_info_box so its text bbox is already registered and avoided.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    # Measure raw text footprint (no box) so the scan uses an accurate size.
    t = ax.text(0.5, 0.5, text, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=fontsize)
    fig.canvas.draw()
    tb = t.get_window_extent(renderer)
    w, h = tb.width, tb.height
    t.remove()

    text_bboxes = _text_bboxes(ax, fig)
    line_pts, scat_pts, ax_bbox = _line_and_scatter_px(ax, fig)
    x0, y0 = _best_position(ax_bbox, w, h, text_bboxes, line_pts, scat_pts)

    fx = (x0 - ax_bbox.x0) / ax_bbox.width
    fy = (y0 - ax_bbox.y0) / ax_bbox.height
    ax.text(fx, fy, text, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=fontsize, color=color, alpha=alpha)


def add_info_box(ax, fig, text: str, *, mode: str = "on", fontsize: float = 9.0,
                 off_side: str = "right", off_frac: float = 0.26):
    """Place an info box. mode='on' → auto-best location inside the axes (scan + prioritised
    occupancy); mode='off' → a reserved margin outside the axes (off_side).

    Returns the Text artist. Call after data + legend are drawn.
    """
    if mode == "off":
        return _add_off_plot(ax, fig, text, fontsize=fontsize, side=off_side, frac=off_frac)

    # On-plot auto-placement scores 2D pixels; meaningless on a 3D projection. For 3D, drop a
    # text2D box in the top-right corner (the conventional, rarely-occluded spot).
    if hasattr(ax, "text2D"):
        return _axes_text(ax, 0.98, 0.98, text, ha="right", va="top",
                          fontsize=fontsize, bbox=BOX_KW)

    fig.canvas.draw()
    w, h = _measure_box_px(ax, fig, text, fontsize)
    text_bboxes = _text_bboxes(ax, fig)
    line_pts, scat_pts, ax_bbox = _line_and_scatter_px(ax, fig)
    x0, y0 = _best_position(ax_bbox, w, h, text_bboxes, line_pts, scat_pts)

    # Convert the chosen pixel corner to axes fraction and anchor the box's lower-left there.
    fx = (x0 - ax_bbox.x0) / ax_bbox.width
    fy = (y0 - ax_bbox.y0) / ax_bbox.height
    return ax.text(fx, fy, text, transform=ax.transAxes, ha="left", va="bottom",
                   fontsize=fontsize, bbox=BOX_KW)


def _axes_text(ax, x, y, text, **kw):
    """Axes-fraction text that works on both 2D and 3D axes. Axes3D.text expects (x, y, z, s)
    and ignores transform; its text2D(x, y, s) is the 2D-overlay equivalent."""
    if hasattr(ax, "text2D"):
        kw.pop("transform", None)
        return ax.text2D(x, y, text, transform=ax.transAxes, **kw)
    return ax.text(x, y, text, **kw)


def _add_off_plot(ax, fig, text, *, fontsize, side, frac):
    """Shrink the axes to free a margin, then put the box in it (never overlaps data)."""
    fig.canvas.draw()
    box = ax.get_position()
    if side == "right":
        ax.set_position([box.x0, box.y0, box.width * (1 - frac), box.height])
        x, y, ha, va = 1 + frac * 0.5 / (1 - frac), 0.98, "left", "top"
    elif side == "left":
        ax.set_position([box.x0 + box.width * frac, box.y0, box.width * (1 - frac), box.height])
        x, y, ha, va = -frac * 0.9 / (1 - frac), 0.98, "left", "top"
    elif side == "top":
        ax.set_position([box.x0, box.y0, box.width, box.height * (1 - frac)])
        x, y, ha, va = 0.5, 1 + frac * 0.4 / (1 - frac), "center", "bottom"
    else:  # bottom
        ax.set_position([box.x0, box.y0 + box.height * frac, box.width, box.height * (1 - frac)])
        x, y, ha, va = 0.5, -frac * 0.4 / (1 - frac), "center", "top"
    return _axes_text(ax, x, y, text, transform=ax.transAxes, ha=ha, va=va,
                      fontsize=fontsize, bbox=BOX_KW)
