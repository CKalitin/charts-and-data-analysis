"""Deflected shape (worst-tilt valid solve) and the frame buckling mode."""
from __future__ import annotations

import numpy as np
from matplotlib.lines import Line2D

from . import _render as R
from ..model import relative_to_base


def _shape(fig, study, u, scale, color, label, thrust_note: str | None):
    m = study.model
    axes, _ = R.view_axes(fig, study, extra_right_mm=600, plan=False)
    for k, (v, ax) in enumerate(axes.items()):
        i, j, *_ = R.VIEWS[v]
        for mid in m.members:
            ax.plot(*R.member_polyline(study, mid, i, j), color=R.HAIR, lw=1.5, solid_capstyle="round", zorder=1)
            ax.plot(*R.member_polyline(study, mid, i, j, u, scale), color=color, lw=1.3,
                    solid_capstyle="round", zorder=2)
        n = m.thrust_node
        D = m.x[n] * 1e3 + scale * u[6 * n:6 * n + 3] * 1e3
        ax.plot(D[i], D[j], "o", color=color, ms=4, mec="white", mew=0.8, zorder=3)
        if k == 0 and thrust_note:
            ax.annotate(thrust_note, (D[i], D[j]), xytext=(D[i] + 150, D[j] - 520), textcoords="data",
                        ha="left", va="top", fontsize=R.FS_TEXT, color=R.INK2,
                        arrowprops=dict(arrowstyle="-", color=R.MUTED, lw=0.6))
        R.finish_view(ax, v)
    a0 = axes["front"]
    a0.legend(handles=[Line2D([], [], color=R.HAIR, lw=1.6, label="undeformed"),
                       Line2D([], [], color=color, lw=1.6, label=label)], loc="upper left")
    return a0


def build_deflection(study, env, p):
    tt = max([s for s in study.solves if s.valid], key=lambda s: s.thrust_tilt_deg)
    sc = R.deform_scale(study, p)
    fig = R.new_figure(6.4 if study.model.mode == "2d" else 9.0, 7.4)
    d = tt.thrust_disp * 1e3
    a0 = _shape(fig, study, tt.ur, sc, R.SERIES[0], f"deformed × {sc:.0f}",
                f"thrust point\nδ = ({d[0]:+.1f}, {d[1]:+.1f}, {d[2]:+.1f}) mm\ntilt {tt.thrust_tilt_deg:.2f}°")
    R.title(fig, "Stand Deflected Shape")
    R.note(fig, "Displacements relative to the ground (best-fit rigid motion of the base removed).")
    R.info_box(a0, fig, R.param_lines(study, p, [f"case {tt.key} (largest tilt)",
                                                 f"tilt limit {p.si.checks.tilt_limit:g}°"]))
    return fig


def build_buckling(study, env, p):
    s = next(s for s in study.solves + study.sweep if s.key == env.lam[1])
    phi = relative_to_base(study.model, s.phi)
    amp = np.abs(phi.reshape(-1, 6)[:, :3]).max()
    fig = R.new_figure(6.4 if study.model.mode == "2d" else 9.0, 7.4)
    a0 = _shape(fig, study, phi / amp, 0.08 * np.ptp(study.model.x[:, 2]), R.SERIES[6],
                "mode shape (arbitrary amplitude)", None)
    R.title(fig, "Frame Buckling Mode")
    R.info_box(a0, fig, R.param_lines(study, p, [f"λ = {s.lam:.1f} × applied loads",
                                                 f"case {s.key} (lowest λ)"]))
    return fig


def figures(study, env, p):
    plan = [("deflection", lambda: build_deflection(study, env, p))]
    if np.isfinite(env.lam[0]):
        plan.append(("buckling_mode", lambda: build_buckling(study, env, p)))
    return plan


if __name__ == "__main__":
    R.main(figures)
