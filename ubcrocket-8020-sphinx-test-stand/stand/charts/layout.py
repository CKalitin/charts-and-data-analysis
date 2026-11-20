"""Node and member key: the map every other figure and table is read against.

Labels every member (M..) along its own line and every joint (N..) at its node, on the same
true-scale orthographic views the rest of the figures use. In the 3D stand the front and back
frames project onto each other, so items landing on one spot in a view share one label
("M7/M9") — they are separated in the side and plan views.
"""
from __future__ import annotations

import numpy as np
from matplotlib.lines import Line2D

from . import _render as R

MEMBER_C, NODE_C = R.SERIES[0], R.INK
FLAT_MM = 45.0            # a member shorter than this in projection is edge-on in this view
GROUP_MM = 32.0           # items closer than this in projection share a label


def _ids(names: list[str]) -> str:
    return "/".join(sorted(set(names), key=lambda s: (s[0], int(s[1:]))))


def _member_labels(study, i, j) -> list:
    """One rotated label per member, on its own line; edge-on members are left to the views
    that show them in length, otherwise their label would sit on a single point."""
    m = study.model
    groups: dict[tuple, list] = {}
    for mid in m.members:
        xs, ys = R.member_polyline(study, mid, i, j)
        p0, p1 = np.array([xs[0], ys[0]]), np.array([xs[-1], ys[-1]])
        if np.linalg.norm(p1 - p0) < FLAT_MM:
            continue
        mid_pt = 0.5 * (p0 + p1)
        ang = np.degrees(np.arctan2(*(p1 - p0)[::-1]))
        key = (round(mid_pt[0] / GROUP_MM), round(mid_pt[1] / GROUP_MM), round(ang / 15))
        groups.setdefault(key, []).append((f"M{mid}", mid_pt, ang, p1 - p0))

    out = []
    for items in groups.values():
        names = [it[0] for it in items]
        _, mid_pt, ang, d = items[0]
        if ang > 90:
            ang -= 180
        elif ang < -90:
            ang += 180
        n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) or 1.0)     # unit normal, label side
        if n[1] < 0:
            n = -n
        out.append((mid_pt[0], mid_pt[1], _ids(names),
                    dict(rotation=ang, color=MEMBER_C, zorder=6), n))
    return out


def _node_labels(ax, study, i, j) -> list:
    m = study.model
    groups: dict[tuple, list] = {}
    for jt in m.joints:
        X = jt.at * 1e3
        groups.setdefault((round(X[i] / GROUP_MM), round(X[j] / GROUP_MM)), []).append((jt.id, X))
    pts = [(g[0][1][i], g[0][1][j], _ids([x[0] for x in g])) for g in groups.values()]
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=16, color=NODE_C,
               edgecolor="white", linewidth=0.7, zorder=7)
    return [(x, y, s, dict(color=NODE_C, fontweight="bold", zorder=8)) for x, y, s in pts]


def draw(ax, study, p, view: str) -> list:
    """Geometry only; returns the labels for build() to place once the figure is final."""
    m = study.model
    i, j, *_ = R.VIEWS[view]
    for mid in m.members:
        ax.plot(*R.member_polyline(study, mid, i, j), color=R.SAFE_MEMBER, lw=2.0,
                solid_capstyle="round", zorder=2)
    # member ids may only slide to either side of their own line, so they are the constrained
    # ones and go first; node ids can take any direction around the node
    mem = [(x, y, text, kw, [(n[0] * r, n[1] * r) for r in (7, 15) for n in (n1, -n1)])
           for x, y, text, kw, n1 in _member_labels(study, i, j)]
    labels = mem + _node_labels(ax, study, i, j)
    tp = m.thrust_point * 1e3
    if j == 2:
        ax.annotate("", xy=(tp[i], tp[j] + 220), xytext=(tp[i], tp[j]), zorder=6,
                    arrowprops=dict(arrowstyle="-|>", color=R.INK, lw=1.0, mutation_scale=8))
    R.finish_view(ax, view)
    ax.margins(0.10)                     # room for labels at the extremes, else they clip
    return labels


def build(study, env, p):
    m = study.model
    fig = R.new_figure(7.4, 8.2) if m.mode == "2d" else R.new_figure(11.5, 10.2)
    axes, spare = R.view_axes(fig, study)
    pending = {v: draw(ax, study, p, v) for v, ax in axes.items()}
    handles = [Line2D([], [], color=R.SAFE_MEMBER, lw=2.4, label="member"),
               Line2D([], [], color=MEMBER_C, lw=0, marker="s", ms=5, label="member id  M.."),
               Line2D([], [], color=NODE_C, lw=0, marker="o", ms=4.5, label="joint  N.."),
               Line2D([], [], color=R.INK, marker="^", lw=0, ms=5, label="thrust")]
    host = spare if spare is not None else axes["front"]
    host.legend(handles=handles, loc="upper left")
    counts = (f"{len(m.members)} members · {len(m.joints)} joints · "
              f"{sum(len(j.brackets) for j in m.joints)} brackets")
    if spare is not None:
        spare.text(0.0, 0.3, counts, transform=spare.transAxes, fontsize=R.FS_SMALL,
                   color=R.INK2, va="top")
    R.title(fig, "Node and Member Key" + (" (2D side frame)" if m.mode == "2d" else ""))
    R.note(fig, "Items projecting onto one spot in a view share a label; the other views separate them.")
    # labels last: the axes are only in their final place once legend and title are in
    fig.canvas.draw()
    fig.set_layout_engine("none")
    for v, ax in axes.items():
        R.place_point_labels(ax, fig, pending[v], settle=False)
    return fig


def figures(study, env, p):
    return [("layout", lambda: build(study, env, p))]


if __name__ == "__main__":
    R.main(figures)
