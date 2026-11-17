"""Stand coloured by safety factor: true-scale front / side / plan, members + joints."""
from __future__ import annotations

import numpy as np
from matplotlib.lines import Line2D

from . import _render as R


def draw(ax, study, env, p, view: str, label: bool) -> None:
    m = study.model
    i, j, *_ = R.VIEWS[view]
    tm, tj = p.si.checks.SF_target_member, p.si.checks.SF_target_joint
    sf_m = {int(r["id"][1:]): r["SF"] for r in env.members}
    for mid in sorted(m.members, key=lambda k: -sf_m[k]):           # failing members on top
        c = R.bin_color(sf_m[mid], tm, R.SAFE_MEMBER)
        safe = c == R.SAFE_MEMBER
        ax.plot(*R.member_polyline(study, mid, i, j), color=c, lw=1.5 if safe else 2.3,
                solid_capstyle="round", zorder=2 if safe else 3)
    # joints that project onto one spot (front/back pairs) share a marker and a label
    groups: dict[tuple, list] = {}
    for jt in m.joints:
        r = env.joint_min.get(jt.id)
        if r is not None and np.isfinite(r["SF"]):
            X = jt.at * 1e3
            groups.setdefault((round(X[i] / 30), round(X[j] / 30)), []).append((r["SF"], jt.id, X))
    labels = []
    for g in groups.values():
        sf, _, X = min(g)
        c = R.bin_color(sf, tj, R.SAFE_JOINT)
        safe = c == R.SAFE_JOINT
        ax.plot(X[i], X[j], "o", ms=3.2 if safe else 4.6, color=c, mec="white", mew=0.8, zorder=5)
        if not safe:
            ids = "/".join(sorted({x[1] for x in g}, key=lambda s: int(s[1:])))
            labels.append((X[i], X[j], f"{ids} {sf:.2f}"))
    if label:
        for mid, sf in sf_m.items():
            if sf < tm:
                P = m.members[mid].point(m.members[mid].L / 2) * 1e3
                labels.append((P[i], P[j], f"M{mid} {sf:.2f}"))
        R.view_labels(ax, labels)
    tp = m.thrust_point * 1e3
    if j == 2:
        ax.annotate("", xy=(tp[i], tp[j] + 220), xytext=(tp[i], tp[j]), zorder=6,
                    arrowprops=dict(arrowstyle="-|>", color=R.INK, lw=1.0, mutation_scale=8))
    R.finish_view(ax, view)


def build(study, env, p):
    m = study.model
    fig = R.new_figure(6.8, 7.6) if m.mode == "2d" else R.new_figure(10.5, 9.4)
    axes, spare = R.view_axes(fig, study)
    for v, ax in axes.items():
        draw(ax, study, env, p, v, label=(v == "front"))
    t = p.si.checks.SF_target_member
    handles = [Line2D([], [], color=R.CRIT, lw=2.4, label="SF < 1"),
               Line2D([], [], color=R.SERIOUS, lw=2.4, label=f"1 ≤ SF < {t:g}"),
               Line2D([], [], color=R.SAFE_MEMBER, lw=2.4, label=f"SF ≥ {t:g}"),
               Line2D([], [], color=R.INK2, marker="o", lw=0, ms=4.5, label="joint (worst bracket)"),
               Line2D([], [], color=R.INK, marker="^", lw=0, ms=5, label="thrust")]
    host = spare if spare is not None else axes["front"]
    host.legend(handles=handles, loc="upper left")
    lines = R.param_lines(study, p, [R.basis(study)])
    if spare is not None:
        spare.text(0.0, 0.25, "\n".join(lines), transform=spare.transAxes, fontsize=R.FS_SMALL,
                   color=R.INK2, va="top", linespacing=1.5)
    else:
        R.info_box(axes["front"], fig, lines)
    R.title(fig, "Safety Factor by Member and Joint")
    R.note(fig, "Front view labels: joints at one projected spot (front/back frame) share the worst SF.")
    return fig


def figures(study, env, p):
    return [("stand_sf", lambda: build(study, env, p))]


if __name__ == "__main__":
    R.main(figures)
