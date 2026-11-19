"""Sandbag demand: the base line load that cancels the stand's loads, in plan.

q_z < 0 pulls the base down (must be supplied by sandbags); q_z > 0 is ground bearing.
Profiles are drawn perpendicular to each base member; labels give the sandbag mass that
member must carry so nowhere along it lifts.
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Patch

from . import _render as R
from ..loads import base_q

DOWN, UP = R.COMPRESSION, R.TENSION        # sandbag demand (warm) vs ground bearing (cool)


def _worst_case(study):
    sols = [s for s in study.solves if s.valid and s.run.name == "R" and s.run.bearing]
    return max(sols or study.solves, key=lambda s: -s.loads.base_q_range[0])


def build(study, env, p):
    m = study.model
    s = _worst_case(study)
    L = s.loads
    g = p.si.model.g
    fig = R.new_figure(8.6 if m.mode == "3d" else 7.4, 5.4 if m.mode == "3d" else 4.2)
    ax = fig.add_subplot(1, 1, 1)
    qmax = max(abs(L.base_q_range[0]), abs(L.base_q_range[1]), 1.0)
    per_member: dict[int, float] = {}
    normals: dict[int, np.ndarray] = {}
    if m.mode == "3d":
        scale = 75.0 / qmax                          # mm of offset per N/m
        for mid in m.members:
            P = m.x[m.member_nodes[mid]] * 1e3
            ax.plot(P[:, 0], P[:, 1], color=R.SAFE_MEMBER if mid in m.geo.base_members else R.HAIR,
                    lw=1.6 if mid in m.geo.base_members else 0.8, solid_capstyle="round", zorder=2)
        for k in m.base_elements:
            e = m.elements[k]
            p1, p2 = m.x[e.n1], m.x[e.n2]
            t = np.linspace(0, 1, 9)
            pts = p1[None] + t[:, None] * (p2 - p1)[None]
            q = np.array([base_q(L.base_theta, x, L.base_centroid)[2] for x in pts])
            d = (p2 - p1)[:2] / np.linalg.norm((p2 - p1)[:2])
            nrm = np.array([-d[1], d[0]])
            base_xy = pts[:, :2] * 1e3
            for sign, c in ((1, DOWN), (-1, UP)):
                mask = (-q * sign) > 0
                if mask.any():
                    poly_q = np.where(mask, -q, 0.0)
                    pr = base_xy + (poly_q * scale)[:, None] * nrm[None]
                    ax.fill(np.r_[base_xy[:, 0], pr[::-1, 0]], np.r_[base_xy[:, 1], pr[::-1, 1]],
                            color=c, alpha=0.55, lw=0, zorder=1)
            per_member[e.member] = per_member.get(e.member, 0.0) + max(0, -q.min()) * e.L
            normals[e.member] = nrm
        for mid, w in per_member.items():
            if w > 2.0 * g:                # label on the side opposite the sandbag profile
                P = m.members[mid].point(m.members[mid].L / 2) * 1e3
                n = -normals[mid]
                ax.annotate(f"{w / g:.0f} kg", (P[0], P[1]), xytext=(10 * n[0], 10 * n[1]),
                            textcoords="offset points", fontsize=R.FS_SMALL, color=R.INK2, zorder=4,
                            ha="center" if abs(n[0]) < 0.5 else ("left" if n[0] > 0 else "right"),
                            va="center" if abs(n[1]) < 0.5 else ("bottom" if n[1] > 0 else "top"),
                            bbox=R.HALO)
        ax.set_aspect("equal")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        ax.spines[:].set_visible(False)
        ax.margins(0.08)
    else:
        for k in m.base_elements:
            e = m.elements[k]
            xs = np.array([m.x[e.n1][0], m.x[e.n2][0]]) * 1e3
            q = np.array([base_q(L.base_theta, m.x[n], L.base_centroid)[2] for n in (e.n1, e.n2)])
            ax.fill_between(xs, 0, -q, where=-q >= 0, color=DOWN, alpha=0.55, lw=0, interpolate=True)
            ax.fill_between(xs, 0, -q, where=-q < 0, color=UP, alpha=0.55, lw=0, interpolate=True)
        ax.axhline(0, color=R.INK2, lw=0.8)
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("sandbag demand −q_z (N/m)")
    ax.legend(handles=[Patch(color=DOWN, alpha=0.55, label="sandbag demand (pull down)"),
                       Patch(color=UP, alpha=0.55, label="ground bearing (push up)")], loc="upper left")
    R.title(fig, "Sandbag Demand on the Base")
    R.note(fig, "Linear line load on the base members that exactly cancels the applied loads (force and moment); "
                "kg = bags each member needs so no part of it lifts.")
    R.info_box(ax, fig, R.param_lines(study, p, [
        f"case {s.key}",
        f"net uplift {L.summary['Fz_applied_N']:.0f} N → {L.summary['sandbag_net_kg']:.0f} kg total",
        f"q_z from {L.base_q_range[0]:.0f} to {L.base_q_range[1]:+.0f} N/m",
        f"uniform bags would need {L.summary['sandbag_uniform_kg']:.0f} kg"]))
    return fig


def figures(study, env, p):
    if study.model.ground_mode:
        return []                      # replaced by charts/ground.py
    return [("sandbag_demand", lambda: build(study, env, p))]


if __name__ == "__main__":
    R.main(figures)
