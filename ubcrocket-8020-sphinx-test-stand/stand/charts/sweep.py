"""Safety factor vs joint rotational stiffness (the P/R bounding assumption test)."""
from __future__ import annotations

import numpy as np

from . import _render as R
from ..analysis import item_U


def build(study, env, p, n: int = 6):
    Us = [item_U(s) for s in study.sweep]
    ks = np.array([s.run.k_theta for s in study.sweep])
    valid = np.array([s.valid for s in study.sweep])
    worst = sorted(Us[-1], key=lambda k: -Us[-1][k])
    picks, bases = [], set()
    for k in worst:                                   # one line per physical joint / member
        base = k.split("#")[0]
        if base not in bases:
            picks.append(k)
            bases.add(base)
        if len(picks) == n:
            break
    fig = R.new_figure(7.0, 4.4)
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ends = []
    for c, k in enumerate(picks):
        sf = np.array([1 / U[k] if U.get(k, 0) > 0 else np.nan for U in Us])
        ax.plot(ks, sf, ":", color=R.SERIES[c], lw=0.9, zorder=2)
        ax.plot(ks[valid], sf[valid], "-o", color=R.SERIES[c], lw=1.8, ms=3.8, mec="white", mew=0.7, zorder=3)
        ends.append((sf[-1], k))
    lo = min(e[0] for e in ends) / 1.5
    hi = max(1.3, max(np.nanmax([1 / U[k] for U in Us for k in picks if U.get(k, 0) > 0]) * 1.4,
                      p.si.checks.SF_target_joint * 1.25))
    ax.set_ylim(lo, hi)
    gap = 0.055 * np.log10(hi / lo)
    for (sf, k), l in zip(ends, R.spread([np.log10(e[0]) for e in ends], gap)):
        name = k
        if "#" in k:
            jid, rest = k.split("#")
            br, leg = rest.split(":")
            b, c = br.split(".")
            name = f"{jid} bracket {b}{' copy ' + str(int(c) + 1) if c != '0' else ''}, leg {leg}"
        ax.annotate(name, (ks[-1], sf), xytext=(ks[-1] * 2.2, 10**l), textcoords="data",
                    fontsize=R.FS_SMALL, color=R.INK2, va="center",
                    arrowprops=dict(arrowstyle="-", color=R.HAIR, lw=0.6))
    if (~valid).any():
        kv = ks[~valid].max()
        right = np.sqrt(kv * ks[ks > kv].min()) if (ks > kv).any() else kv
        ax.axvspan(ks.min() / 1.6, right, color=R.FAINT, zorder=0, lw=0)
        ax.text(ks.min() / 1.4, hi / 1.04, "mechanism-dominated", fontsize=R.FS_SMALL, color=R.MUTED, va="top")
    for yv, lab in ((1.0, "SF 1"), (p.si.checks.SF_target_joint, f"target {p.si.checks.SF_target_joint:g}")):
        if lo < yv < hi:
            ax.axhline(yv, color=R.MUTED, lw=0.8, zorder=1)
            ax.text(ks.max() * 60, yv, f"{lab} ", fontsize=R.FS_SMALL, color=R.MUTED, va="bottom", ha="right")
    ax.set_xlim(ks.min() / 1.6, ks.max() * 60)
    ax.set_xticks(ks)
    R.log_axis(ax.xaxis)
    R.log_axis(ax.yaxis)
    ax.set_xlabel("joint rotational stiffness k_θ / (EI/L)")
    ax.set_ylabel("safety factor (log)")
    R.title(fig, "Safety Factor vs Joint Rotational Stiffness")
    R.note(fig, f"Dotted: points whose frame moves > {p.si.checks.sweep_mech_ratio:g}× the rigid run (excluded). "
                "Run P = left end, run R = right end.")
    R.info_box(ax, fig, R.param_lines(study, p, [f"case {study.sweep_case}, bearing "
                                                 f"{'ON' if study.sweep_bearing else 'OFF'}"]))
    return fig


def figures(study, env, p):
    return [("ktheta_sweep", lambda: build(study, env, p))]


if __name__ == "__main__":
    R.main(figures)
