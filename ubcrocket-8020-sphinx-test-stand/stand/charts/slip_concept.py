"""Why a slipped joint is not the end of the story: the same rotation, in 2D and in 3D.

A concept drawing, not a result — nothing here is read from a solve. Left: the 2D
idealisation, where the joint is a point and a slipped joint rotates freely under an end
load. Right: the same rotation with real sections, where the horizontal member's top-left
edge closes onto the vertical member and bears, reacting the moment friction gave up.

    python -m stand.charts.slip_concept [out_dir]
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Circle, Polygon

from . import _render as R

ROT_DEG = 11.0                                   # exaggerated so the mechanism is visible
FACE = {"front": "#dedcd7", "top": "#efeeea", "right": "#c3c1bb"}
EDGE = "#8a8984"
GHOST = "#dcdbd6"
LOAD_C, CONTACT_C, GAP_C = R.SERIES[0], R.CRIT, R.SERIES[2]


# --------------------------------------------------------------------------- isometric box
def _iso(p):
    """(x, y, z) -> screen. z runs away from the viewer, up and to the right."""
    x, y, z = p
    return x + 0.52 * z, y + 0.30 * z


def _corners(x0, x1, y0, y1, z0, z1) -> dict:
    return {(i, j, k): np.array([(x0, x1)[i], (y0, y1)[j], (z0, z1)[k]], float)
            for i in (0, 1) for j in (0, 1) for k in (0, 1)}


def _rot_z(c: dict, pivot, deg: float) -> dict:
    t = np.radians(deg)
    M = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    out = {}
    for k, v in c.items():
        q = v.copy()
        q[:2] = np.asarray(pivot) + M @ (v[:2] - np.asarray(pivot))
        out[k] = q
    return out


FACES = {"front": [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
         "top": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
         "right": [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]}


def _box(ax, c: dict, *, zorder: int, ghost: bool = False) -> None:
    for name, keys in FACES.items():
        xy = [_iso(c[k]) for k in keys]
        ax.add_patch(Polygon(xy, closed=True, zorder=zorder,
                             facecolor="white" if ghost else FACE[name],
                             edgecolor=GHOST if ghost else EDGE,
                             linewidth=0.8, linestyle=(0, (3, 2)) if ghost else "solid"))


def _edge(ax, c: dict, a, b, **kw) -> None:
    (x0, y0), (x1, y1) = _iso(c[a]), _iso(c[b])
    ax.plot([x0, x1], [y0, y1], **kw)


def _arrow(ax, p0, p1, color, lw=1.6, z=12):
    ax.annotate("", xy=p1, xytext=p0, zorder=z,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=11))


def _swing(ax, centre, r, a0, a1, color, *, z=None, lw=1.4, zorder=11):
    """The real path the point sweeps: an arc centred on the pivot, from a0 to a1 (degrees,
    CCW positive). A hand-picked connectionstyle rad is NOT this — it bulges by an arbitrary
    amount and on a shallow sweep it reads as turning the other way."""
    th = np.radians(np.linspace(a0, a1, 48))
    pts = np.stack([centre[0] + r * np.cos(th), centre[1] + r * np.sin(th)], axis=1)
    if z is not None:
        pts = np.array([_iso((x, y, z)) for x, y in pts])
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=lw, zorder=zorder, solid_capstyle="round")
    ax.annotate("", xy=pts[-1], xytext=pts[-5], zorder=zorder,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=11))
    return pts


# --------------------------------------------------------------------------- 2D panel
def draw_2d(ax) -> None:
    px, py = 0.0, 2.0                                  # the joint
    ax.plot([0, 0], [-0.1, 3.4], color=R.SAFE_MEMBER, lw=7, solid_capstyle="round", zorder=2)
    ax.plot([px, 3.3], [py, py], color=GHOST, lw=7, solid_capstyle="round", zorder=2)

    t = np.radians(ROT_DEG)
    ex, ey = px + 3.3 * np.cos(t), py + 3.3 * np.sin(t)
    ax.plot([px, ex], [py, ey], color="#a3a19b", lw=7, solid_capstyle="round", zorder=3)

    ax.add_patch(Circle((px, py), 0.17, facecolor="white", edgecolor=R.INK,
                        lw=1.4, zorder=6))
    pts = _swing(ax, (px, py), 2.45, 0.0, ROT_DEG, LOAD_C, zorder=7)
    ax.annotate("θ", xy=(pts[-1][0] + 0.16, 0.5 * (pts[0][1] + pts[-1][1])),
                fontsize=R.FS_LABEL, color=LOAD_C, ha="left", va="center", zorder=7)
    _arrow(ax, (ex, ey + 0.12), (ex, ey + 1.25), LOAD_C)
    ax.annotate("F", xy=(ex, ey + 1.3), fontsize=R.FS_LABEL, color=LOAD_C,
                fontweight="bold", ha="center", va="bottom")

    ax.annotate("nothing takes the moment\nonce friction lets go", xy=(px + 0.22, py - 0.1),
                xytext=(0.85, 1.15), fontsize=R.FS_SMALL, color=R.INK2, ha="left", va="top",
                arrowprops=dict(arrowstyle="-", color=R.MUTED, lw=0.6))
    _triad_2d(ax, 2.9, 0.25)
    ax.set_xlim(-1.0, 4.4)
    ax.set_ylim(-0.6, 5.4)


def _triad_2d(ax, x, y) -> None:
    _arrow(ax, (x, y), (x + 0.7, y), R.INK2, lw=1.0, z=9)
    _arrow(ax, (x, y), (x, y + 0.7), R.INK2, lw=1.0, z=9)
    ax.add_patch(Circle((x, y), 0.11, facecolor="white", edgecolor=R.INK2, lw=1.0, zorder=9))
    ax.plot([x], [y], marker="o", ms=2.0, color=R.INK2, zorder=10)
    for s, dx, dy in (("x", 0.82, 0), ("y", 0, 0.82), ("z", -0.26, -0.22)):
        ax.annotate(s, xy=(x + dx, y + dy), fontsize=R.FS_SMALL, color=R.INK2,
                    ha="center", va="center", zorder=10)


# --------------------------------------------------------------------------- 3D panel
def draw_3d(ax) -> None:
    col = _corners(0.0, 1.0, -0.2, 4.0, 0.0, 1.0)          # vertical member
    beam0 = _corners(1.0, 4.3, 2.0, 3.0, 0.0, 1.0)         # horizontal member, as built
    pivot = (1.35, 2.5)                                    # the bolt
    beam1 = _rot_z(beam0, pivot, ROT_DEG)

    _box(ax, beam0, zorder=2, ghost=True)
    _box(ax, col, zorder=3)
    _bracket(ax)
    _box(ax, beam1, zorder=6)

    # the top-left edge has swung into the column face; the bottom-left has opened a gap
    _edge(ax, beam1, (0, 1, 0), (0, 1, 1), color=CONTACT_C, lw=3.4, zorder=9,
          solid_capstyle="round")
    _edge(ax, beam1, (0, 0, 0), (0, 0, 1), color=GAP_C, lw=2.2, zorder=9,
          linestyle=(0, (2, 1.6)))

    tip = beam1[(1, 1, 0)]
    ex, ey = _iso(tip)
    _arrow(ax, (ex, ey + 0.1), (ex, ey + 1.25), LOAD_C)
    ax.annotate("F", xy=(ex, ey + 1.3), fontsize=R.FS_LABEL, color=LOAD_C,
                fontweight="bold", ha="center", va="bottom")

    # the reaction the contact applies to the beam: normal to the column face, +x
    cx, cy = _iso(0.5 * (beam1[(0, 1, 0)] + beam1[(0, 1, 1)]))
    _arrow(ax, (cx, cy), (cx + 1.0, cy), CONTACT_C, lw=2.0, z=11)
    ax.annotate("bearing reaction", xy=(cx + 1.05, cy), fontsize=R.FS_SMALL,
                color=CONTACT_C, fontweight="bold", ha="left", va="center", zorder=11)
    ax.annotate("the top edge has closed onto the\ncolumn and now bears on it",
                xy=(cx - 0.06, cy + 0.05), xytext=(-1.5, 5.0),
                fontsize=R.FS_SMALL, color=CONTACT_C, ha="left", va="top",
                arrowprops=dict(arrowstyle="-", color=CONTACT_C, lw=0.6))
    gx, gy = _iso(beam1[(0, 0, 0)])
    ax.annotate("gap opens", xy=(gx - 0.06, gy - 0.02), xytext=(gx - 0.9, gy - 0.85),
                fontsize=R.FS_SMALL, color=GAP_C, ha="right", va="top",
                arrowprops=dict(arrowstyle="-", color=GAP_C, lw=0.6))

    # same sweep, in the x-y plane about the bolt, then projected
    a0 = np.degrees(np.arctan2(2.0 - pivot[1], 4.3 - pivot[0]))
    pts = _swing(ax, pivot, 3.1, a0, a0 + ROT_DEG, LOAD_C, z=0.0, zorder=11)
    ax.annotate("θ", xy=(pts[-1][0] + 0.2, 0.5 * (pts[0][1] + pts[-1][1])),
                fontsize=R.FS_LABEL, color=LOAD_C, ha="left", va="center", zorder=11)

    ax.annotate("triangle bracket", xy=_iso(np.array([1.45, 1.75, 0.5])),
                xytext=(2.2, 0.55), fontsize=R.FS_SMALL, color=R.INK2, ha="left", va="top",
                arrowprops=dict(arrowstyle="-", color=R.MUTED, lw=0.6))
    _triad_3d(ax, 4.9, 0.35)
    ax.set_xlim(-1.6, 7.2)
    ax.set_ylim(-0.6, 5.4)


def _bracket(ax) -> None:
    """L of the triangle bracket, in the inside corner, on both members' faces."""
    for z in (0.08, 0.62):
        pts = [(1.0, 2.0, z), (1.0, 1.25, z), (1.08, 1.25, z), (1.78, 1.92, z),
               (1.78, 2.0, z)]
        ax.add_patch(Polygon([_iso(np.array(p)) for p in pts], closed=True, zorder=5,
                             facecolor="#9e9c96", edgecolor=EDGE, lw=0.7))
    for a, b in (((1.0, 1.25, 0.08), (1.0, 1.25, 0.62)),
                 ((1.78, 2.0, 0.08), (1.78, 2.0, 0.62)),
                 ((1.08, 1.25, 0.08), (1.08, 1.25, 0.62))):
        (x0, y0), (x1, y1) = _iso(np.array(a)), _iso(np.array(b))
        ax.plot([x0, x1], [y0, y1], color=EDGE, lw=0.7, zorder=5)


def _triad_3d(ax, x, y) -> None:
    for d, s in (((1, 0, 0), "x"), ((0, 1, 0), "y"), ((0, 0, 1), "z")):
        p1 = _iso(np.array(d, float) * 0.78)
        _arrow(ax, (x, y), (x + p1[0], y + p1[1]), R.INK2, lw=1.0, z=9)
        ax.annotate(s, xy=(x + p1[0] * 1.3, y + p1[1] * 1.3), fontsize=R.FS_SMALL,
                    color=R.INK2, ha="center", va="center", zorder=10)


# --------------------------------------------------------------------------- figure
def build():
    fig = R.new_figure(10.6, 4.9)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.5])
    a, b = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    draw_2d(a)
    draw_3d(b)
    for ax, t in ((a, "2D model: the joint is a point"), (b, "3D: the members have sections")):
        ax.set_aspect("equal")
        ax.set_title(t)
        ax.axis("off")
    R.title(fig, "Joint Rotation After Slip, 2D vs 3D")
    R.note(fig, f"Rotation drawn at {ROT_DEG:g}°, exaggerated; the real slip is a fraction of that.")
    return fig


def figures(*_):
    return [("slip_concept", build)]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    from ..params import PROJECT_DIR

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_DIR / "results" / "concepts"
    for p in R.save_fig(build(), out / "figures" / "slip_2d_vs_3d"):
        print(f"wrote   {p.relative_to(PROJECT_DIR) if p.is_relative_to(PROJECT_DIR) else p}")
