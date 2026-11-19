"""Lowest safety factors: joints (worst leg each) and members, log-scale dot plot."""
from __future__ import annotations

import numpy as np

from . import _render as R


def _panel(ax, rows, target, lo, hi, marker) -> None:
    y = np.arange(len(rows))[::-1]
    for xv, c in ((1.0, R.INK2), (target, R.MUTED)):
        ax.axvline(xv, color=c, lw=0.8, zorder=1)
    for yi, (sf, name, gov) in zip(y, rows):
        c = R.bin_color(sf, target, R.SAFE_JOINT)
        ax.plot(sf, yi, marker, ms=5.5, color=c, mec="white", mew=1.0, zorder=3)
        ax.annotate(f"{sf:.2f}  {gov}", (sf, yi), xytext=(6, 0), textcoords="offset points",
                    fontsize=R.FS_SMALL, color=R.INK2, va="center")
    ax.set_yticks(y, [r[1] for r in rows])
    ax.grid(axis="y", color=R.FAINT, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xscale("log")
    R.log_axis(ax.xaxis)
    ax.set_xlim(lo, hi)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.spines["left"].set_visible(False)


def build(study, env, p, n_j: int = 14, n_m: int = 8):
    tm, tj = p.si.checks.SF_target_member, p.si.checks.SF_target_joint
    jrows, seen = [], set()
    for r in env.joints:
        if np.isfinite(r["SF"]) and r["joint"] not in seen:
            seen.add(r["joint"])
            jrows.append((r["SF"], f"{r['joint']} {r['type']}, leg on {r['member']}",
                          R.TERM_LABEL.get(r["gov_term"], "")))
        if len(jrows) == n_j:
            break
    mrows = [(r["SF"], f"{r['id']} ({r['profile']})", r["gov_check"]) for r in env.members[:n_m]]
    allsf = [r[0] for r in jrows + mrows]
    lo, hi = max(0.02, min(allsf) / 1.5), max(max(allsf) * 2.4, max(tm, tj) * 2.4)
    fig = R.new_figure(7.2, 0.21 * (len(jrows) + len(mrows)) + 2.1)
    gs = fig.add_gridspec(2, 1, height_ratios=[len(jrows) + 0.8, len(mrows) + 0.8])
    a1, a2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1], sharex=None)
    _panel(a1, jrows, tj, lo, hi, "o")
    _panel(a2, mrows, tm, lo, hi, "s")
    a1.set_title("Joints (worst bracket leg)")
    a2.set_title("Members")
    a1.tick_params(labelbottom=False)
    a2.set_xlabel("safety factor (log scale)")
    for xv, lab, c in ((1.0, "SF 1", R.INK2), (tj, f"target {tj:g}", R.MUTED)):
        a1.text(xv, len(jrows) - 0.45, f" {lab}", fontsize=R.FS_SMALL, color=c, va="bottom")
    R.title(fig, "Lowest Safety Factors")
    R.info_box(a2, fig, R.param_lines(study, p, [R.basis(study)]))
    return fig


def figures(study, env, p):
    return [("sf_ranking", lambda: build(study, env, p))]


if __name__ == "__main__":
    R.main(figures)
