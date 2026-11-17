"""Joint SF (log) beside what drives it.

The joint check is a linear interaction sum, U = Σ demand_k / capacity_k, SF = 1/U.
The terms add in U, not in SF, so the composition is shown as each term's SHARE of U
(100 % bar) next to the SF itself on a log axis: read the SF on the left, the cause on
the right.
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Patch

from . import _render as R


def build(study, env, p, n: int = 18):
    tj = p.si.checks.SF_target_joint
    rows = [r for r in env.joints if np.isfinite(r["SF"])][:n][::-1]
    terms = [t for t in R.TERM_LABEL if any(np.nan_to_num(r[t]) > 1e-3 for r in rows)]
    fig = R.new_figure(7.6, 0.23 * len(rows) + 1.9)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0])
    a1, a2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    y = np.arange(len(rows))
    sfs = np.array([r["SF"] for r in rows])
    lo, hi = max(0.02, sfs.min() / 1.6), max(tj * 2.5, sfs.max() * 2.5)
    for xv, c in ((1.0, R.INK2), (tj, R.MUTED)):
        a1.axvline(xv, color=c, lw=0.8, zorder=1)
    for yi, r in zip(y, rows):
        c = R.bin_color(r["SF"], tj, R.SAFE_JOINT)
        a1.plot(r["SF"], yi, "o", ms=5.5, color=c, mec="white", mew=1.0, zorder=3)
        a1.annotate(f"{r['SF']:.2f}", (r["SF"], yi), xytext=(6, 0), textcoords="offset points",
                    fontsize=R.FS_SMALL, color=R.INK2, va="center")
    a1.set_xscale("log")
    R.log_axis(a1.xaxis)
    a1.set_xlim(lo, hi)
    a1.set_yticks(y, [R.bracket_name(r) for r in rows])
    a1.grid(axis="y", color=R.FAINT, lw=0.6)
    a1.set_axisbelow(True)
    a1.set_ylim(-0.6, len(rows) - 0.1)
    a1.spines["left"].set_visible(False)
    a1.set_xlabel("safety factor (log)")
    a1.set_title("Safety factor")
    for xv, lab, c in ((1.0, "1", R.INK2), (tj, f"{tj:g}", R.MUTED)):
        a1.text(xv, len(rows) - 0.45, f" {lab}", fontsize=R.FS_SMALL, color=c, va="bottom")

    left = np.zeros(len(rows))
    U = np.array([r["U"] for r in rows])
    for t in terms:
        share = np.array([np.nan_to_num(r[t]) for r in rows]) / U
        a2.barh(y, share, left=left, height=0.64, color=R.TERM_COLOR[t], edgecolor="white", linewidth=1.0,
                zorder=2)
        left += share
    a2.set_xlim(0, 1)
    a2.set_xticks([0, 0.5, 1], ["0", "50 %", "100 %"])
    a2.set_yticks([])
    a2.set_ylim(-0.6, len(rows) - 0.1)
    a2.spines["left"].set_visible(False)
    a2.set_xlabel("share of demand / capacity")
    a2.set_title("What governs")
    a2.legend(handles=[Patch(color=R.TERM_COLOR[t], label=R.TERM_LABEL[t]) for t in terms],
              loc="upper center", bbox_to_anchor=(0.5, -0.13 * 18 / max(len(rows), 8)), ncols=3,
              handlelength=1.0, columnspacing=1.2)
    R.title(fig, "Joint Safety Factor and Governing Term")
    R.note(fig, f"SF = 1/U, U = Σ term demand/capacity (linear interaction); each leg at its worst run/case; "
                f"{R.basis(study)}.")
    R.info_box(a1, fig, R.param_lines(study, p))
    return fig


def figures(study, env, p):
    return [("joint_sf_terms", lambda: build(study, env, p))]


if __name__ == "__main__":
    R.main(figures)
