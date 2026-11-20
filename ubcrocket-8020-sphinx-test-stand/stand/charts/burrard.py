"""Burrard truss back test — the truss carrying its member forces.

The numeric comparison against the course notes is a table (report.burrard_summary), not a
chart: 19 values against 19 reference values is tabular data. Standalone (no study, no cache):

    python -m stand.charts.burrard [out_dir]
    python -m stand burrard
"""
from __future__ import annotations

import numpy as np

from .. import burrard as B
from . import _render as R

def _info(res: B.Result, extra: list[str] | None = None) -> list[str]:
    return [f"E {res.E / 1e9:g} GPa, σy {res.fy / 1e6:g} MPa",
            f"load P = {res.P / 1e6:g} MN",
            "member labels: N/P = axial force ÷ P, + tension",
            "pin-jointed, Euler K = 1"] + (extra or [])


# --------------------------------------------------------------------------- truss forces
def draw_forces(ax, res: B.Result) -> None:
    n = res.nodes
    big = max(abs(b.N_in_P) for b in res.bars)

    for b in res.bars:
        (x0, y0), (x1, y1) = n[b.a], n[b.b]
        col = R.COMPRESSION if b.N_in_P < 0 else R.TENSION if b.N_in_P > 0 else R.MUTED
        ax.plot([x0, x1], [y0, y1], color=col, solid_capstyle="round",
                lw=0.8 + 4.2 * abs(b.N_in_P) / big, zorder=2)
        # label off the member, pushed along its own normal so it never sits on the line
        dx, dy = x1 - x0, y1 - y0
        L = np.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        if abs(dx) < 1e-9:                         # vertical: push clear of the load arrows
            nx, ny, off = 1.0, 0.0, 13.0
        else:
            if ny < 0:
                nx, ny = -nx, -ny                  # otherwise always label on the upper side
            off = 9.0
        txt = "0.00" if abs(b.N_in_P) < 5e-3 else f"{b.N_in_P:+.2f}"
        ax.annotate(txt, xy=((x0 + x1) / 2, (y0 + y1) / 2),
                    xytext=(nx * off, ny * off), textcoords="offset points",
                    ha="center", va="center", fontsize=R.FS_SMALL, color=col, zorder=5)

    xs = [p[0] for p in n.values()]
    ys = [p[1] for p in n.values()]
    ax.scatter(xs, ys, s=11, color=R.INK, zorder=4)
    for name, (px, py) in n.items():
        bottom = py == 0
        ax.annotate(name, xy=(px, py), xytext=(-10 if bottom else 0, -5 if bottom else 8),
                    textcoords="offset points", ha="right" if bottom else "center",
                    fontsize=R.FS_TEXT, color=R.INK, fontweight="bold", zorder=6)

    # loads hang below the bottom chord: inside the truss they land on the vertical members
    for node, v in res.loads_in_P.items():
        px, py = n[node]
        ax.annotate("", xy=(px, py - 3.6), xytext=(px, py - 1.2), zorder=3,
                    arrowprops=dict(arrowstyle="-|>", color=R.INK2, lw=0.9))
        ax.annotate(f"{abs(v):g}P", xy=(px, py - 3.9), ha="center", va="top",
                    fontsize=R.FS_SMALL, color=R.INK2)
    for node in res.supports:
        px, py = n[node]
        ax.scatter([px], [py], s=70, marker="^", facecolor="none",
                   edgecolor=R.INK2, lw=0.9, zorder=3)

    ax.set_aspect("equal")
    ax.set_xlabel("span (m)")
    ax.set_ylabel("height (m)")
    ax.set_ylim(-8.5, max(ys) + 8)
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_xticks([0, 8, 18, 28, 38, 48])
    ax.set_yticks([0, 8, 16])
    ax.plot([], [], color=R.TENSION, lw=2.5, label="tension")
    ax.plot([], [], color=R.COMPRESSION, lw=2.5, label="compression")
    ax.legend(loc="upper left", ncol=2)


# --------------------------------------------------------------------------- plan
def figures(res: B.Result | None = None):
    res = res or B.solve()

    def forces():
        fig = R.new_figure(9.2, 4.0)
        ax = fig.add_subplot()
        draw_forces(ax, res)
        R.title(fig, "Burrard Half Truss Member Forces")
        R.note(fig, f"Source: {res.source}")
        R.info_box(ax, fig, _info(res, [f"governing: {res.min_yield().name} yield "
                                        f"SF {res.min_yield().SF_yield:.2f}",
                                        f"{res.min_buckling().name} buckling "
                                        f"SF {res.min_buckling().SF_buckling:.2f}"]))
        return fig

    return [("burrard_forces", forces)]


if __name__ == "__main__":
    import sys
    import time
    from pathlib import Path

    from ..params import PROJECT_DIR

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_DIR / "results" / "validation"
    t0 = time.time()
    r = B.solve()
    plan = figures(r)
    for i, (name, build) in enumerate(plan, 1):
        for f in R.save_fig(build(), out / "figures" / f"{i:02d}_{name}"):
            print(f"  wrote {f.relative_to(PROJECT_DIR) if f.is_relative_to(PROJECT_DIR) else f}")
    print(f"{len(plan)} chart(s) in {time.time() - t0:.1f} s")
