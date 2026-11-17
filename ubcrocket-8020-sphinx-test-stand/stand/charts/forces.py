"""Member axial force (load path) and peak combined stress, on the true-scale views."""
from __future__ import annotations

import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D

from . import _render as R


def _reference_solve(study):
    """Pure factored thrust (no misalignment), rigid joints, bearing ON: the basic load path."""
    for s in study.solves:
        if s.valid and s.case == "none" and s.run.name == "R" and s.run.bearing:
            return s
    return next(s for s in study.solves if s.valid)


def build_axial(study, env, p):
    m = study.model
    s = _reference_solve(study)
    Nmax = max(abs(s.axial).max(), 1.0)
    fig = R.new_figure(6.8, 7.6) if m.mode == "2d" else R.new_figure(10.5, 9.4)
    axes, spare = R.view_axes(fig, study)
    for v, ax in axes.items():
        i, j, *_ = R.VIEWS[v]
        for k, e in enumerate(m.elements):
            N = s.axial[k]
            P = m.x[[e.n1, e.n2]] * 1e3
            w = 0.6 + 4.4 * abs(N) / Nmax
            ax.plot(P[:, i], P[:, j], color=R.TENSION if N > 0 else R.COMPRESSION, lw=w,
                    solid_capstyle="butt", zorder=2 + abs(N) / Nmax)
        if v == "front":                 # label the heaviest members once (mean N over the member)
            per = sorted(((np.mean(s.axial[m.member_elements[mid]]), mid) for mid in m.members),
                         key=lambda t: -abs(t[0]))[:7]
            labels = []
            for N, mid in per:
                P = m.members[mid].point(m.members[mid].L / 2) * 1e3
                labels.append((P[i], P[j], f"M{mid} {N / 1e3:+.2f} kN"))
            R.view_labels(ax, labels)
        R.finish_view(ax, v)
    handles = [Line2D([], [], color=R.TENSION, lw=3, label="tension"),
               Line2D([], [], color=R.COMPRESSION, lw=3, label="compression"),
               Line2D([], [], color=R.MUTED, lw=4.4 + 0.6, label=f"width ∝ |N|, max {Nmax / 1e3:.2f} kN")]
    host = spare if spare is not None else axes["front"]
    host.legend(handles=handles, loc="upper left")
    lines = R.param_lines(study, p, [f"case {s.key}"])
    if spare is not None:
        spare.text(0.0, 0.3, "\n".join(lines), transform=spare.transAxes, fontsize=R.FS_SMALL,
                   color=R.INK2, va="top", linespacing=1.5)
    else:
        R.info_box(axes["front"], fig, lines)
    R.title(fig, "Member Axial Force")
    return fig


def build_stress(study, env, p):
    """Peak |N|/A + |My|/Sy + |Mz|/Sz per element, worst over every valid solve."""
    m = study.model
    fy = p.si.material.sigma_y
    tm = p.si.checks.SF_target_member
    sig = np.zeros(len(m.elements))
    for s in env.valid:
        for k, e in enumerate(m.elements):
            r = s.internal[k]
            sec = e.sec
            v = np.abs(r[:, 1]) / sec.A + np.abs(r[:, 5]) * sec.cz / sec.Iy + np.abs(r[:, 6]) * sec.cy / sec.Iz
            sig[k] = max(sig[k], v.max())
    sig /= 1e6
    # ordinal blue ramp below the target stress, then status colours: [σ_y/SF, σ_y) and ≥ σ_y
    f_t, f_y = fy / 1e6 / tm, fy / 1e6
    edges = [e for e in (0, 10, 20, 40, 60) if e < f_t] + [f_t, f_y, max(sig.max(), f_y) * 1.05]
    colors = R.BLUE_RAMP[1:1 + len(edges) - 3] + [R.SERIOUS, R.CRIT]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(edges, cmap.N)
    fig = R.new_figure(6.8, 7.6) if m.mode == "2d" else R.new_figure(10.5, 9.4)
    axes, spare = R.view_axes(fig, study)
    order = np.argsort(sig)
    for v, ax in axes.items():
        i, j, *_ = R.VIEWS[v]
        for k in order:
            e = m.elements[k]
            P = m.x[[e.n1, e.n2]] * 1e3
            ax.plot(P[:, i], P[:, j], color=cmap(norm(sig[k])), lw=2.4, solid_capstyle="round", zorder=2)
        if v == "front":
            peak = {}
            for k in np.argsort(-sig):
                mid = m.elements[k].member
                if mid not in peak and len(peak) < 6:
                    e = m.elements[k]
                    peak[mid] = (0.5 * (m.x[e.n1] + m.x[e.n2]) * 1e3, sig[k])
            labels = [(P[i], P[j], f"M{mid} {sv:.0f} MPa") for mid, (P, sv) in peak.items()]
            R.view_labels(ax, labels)
        R.finish_view(ax, v)
    host = spare if spare is not None else axes["front"]
    cax = host.inset_axes([0.0, 0.62, 0.07, 0.36]) if spare is not None else host.inset_axes([0.02, 0.55, 0.035, 0.3])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax, spacing="uniform")
    cb.outline.set_visible(False)
    cb.set_ticks(edges)
    cb.set_ticklabels([f"{e:.0f}" for e in edges], fontsize=R.FS_SMALL)
    cb.set_label("peak σ (MPa)", fontsize=R.FS_SMALL, color=R.INK2)
    lines = R.param_lines(study, p, [f"σ_y = {fy / 1e6:.0f} MPa (6063-T6)", f"orange ≥ σ_y/{tm:g}, red ≥ σ_y",
                                     R.basis(study)])
    if spare is not None:
        spare.text(0.0, 0.5, "\n".join(lines), transform=spare.transAxes, fontsize=R.FS_SMALL,
                   color=R.INK2, va="top", linespacing=1.5)
    else:
        R.info_box(axes["front"], fig, lines)
    R.title(fig, "Peak Combined Stress")
    R.note(fig, "σ = |N|/A + |My|/Sy + |Mz|/Sz at the worst station of each sub-element.")
    return fig


def figures(study, env, p):
    return [("axial_force", lambda: build_axial(study, env, p)),
            ("peak_stress", lambda: build_stress(study, env, p))]


if __name__ == "__main__":
    R.main(figures)
