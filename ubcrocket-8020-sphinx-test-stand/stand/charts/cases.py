"""Per-load-case views: SF heatmap of the critical items, thrust-point tilt and deflection."""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Rectangle

from . import _render as R

TINT = {R.CRIT: "#f4cccc", R.SERIOUS: "#fbe0d4", "safe": "#f5f5f2"}


def _cases(study):
    seen = []
    for s in study.solves:
        if s.case not in seen:
            seen.append(s.case)
    return seen


def build_heatmap(study, env, p, n_j: int = 12, n_m: int = 5):
    """Rows: worst joints (worst leg) + members; columns: load cases; cell = worst valid SF."""
    tm, tj = p.si.checks.SF_target_member, p.si.checks.SF_target_joint
    cases = _cases(study)
    jkeys, seen = [], set()
    for r in env.joints:
        if np.isfinite(r["SF"]) and r["joint"] not in seen:
            seen.add(r["joint"])
            jkeys.append((r["joint"], r["bracket"], r["copy"], r["leg"], r["member"], R.bracket_name(r)))
        if len(jkeys) == n_j:
            break
    mids = [int(r["id"][1:]) for r in env.members[:n_m]]
    rows, labels, targets = [], [], []
    for jk in jkeys:
        vals = []
        for c in cases:
            v = [r["SF"] for s in study.solves if s.valid and s.case == c for r in s.joint_rows
                 if (r["joint"], r["bracket"], r["copy"], r["leg"]) == jk[:4]]
            vals.append(min(v) if v else np.nan)
        rows.append(vals)
        labels.append(jk[5])
        targets.append(tj)
    for mid in mids:
        rows.append([min((s.member_rows[mid]["SF"] for s in study.solves if s.valid and s.case == c),
                         default=np.nan) for c in cases])
        labels.append(f"M{mid} ({study.model.members[mid].profile})")
        targets.append(tm)
    A = np.array(rows)
    fig = R.new_figure(1.9 + 0.78 * len(cases) + 1.6, 0.25 * len(rows) + 1.7)
    ax = fig.add_subplot(1, 1, 1)
    for i, (vals, t) in enumerate(zip(A, targets)):
        worst = np.nanmin(vals)
        for jx, v in enumerate(vals):
            c = R.bin_color(v, t, "safe")
            ax.add_patch(Rectangle((jx - 0.5, i - 0.5), 1, 1, facecolor=TINT[c], edgecolor="white", lw=1.5))
            ax.text(jx, i, f"{v:.2f}", ha="center", va="center", fontsize=R.FS_SMALL,
                    color=R.INK if v == worst else R.INK2, fontweight="bold" if v == worst else "normal")
    if mids:
        ax.axhline(len(jkeys) - 0.5, color=R.INK2, lw=0.8)
    ax.set_xlim(-0.5, len(cases) - 0.5)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_xticks(range(len(cases)), cases)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(rows)), labels)
    ax.spines[:].set_visible(False)
    ax.set_xlabel("misalignment load case")
    ax.xaxis.set_label_position("top")
    R.title(fig, "Safety Factor by Load Case")
    R.note(fig, f"Cell = worst valid run for that case; bold = the item's governing case. "
                f"Red tint < 1, orange < target ({tj:g}).")
    return fig


def build_thrust(study, env, p):
    cases = _cases(study)
    valid = [s for s in study.solves if s.valid]
    runs = list(dict.fromkeys(s.run.label for s in valid))

    def series(run, f):
        return np.array([next((f(s) for s in valid if s.run.label == run and s.case == c), np.nan) for c in cases])
    # runs that coincide (e.g. bearing ON vs OFF) are drawn once and named together
    groups: list[list[str]] = []
    for run in runs:
        t = series(run, lambda s: s.thrust_tilt_deg)
        for g in groups:
            if np.allclose(series(g[0], lambda s: s.thrust_tilt_deg), t, rtol=5e-3):
                g.append(run)
                break
        else:
            groups.append([run])
    fig = R.new_figure(7.2, 3.8)
    gs = fig.add_gridspec(1, 2)
    a1, a2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    x = np.arange(len(cases))
    off = np.linspace(-0.12, 0.12, len(groups)) if len(groups) > 1 else [0.0]
    for k, g in enumerate(groups):
        lab = " ≈ ".join(g)
        tilt = series(g[0], lambda s: s.thrust_tilt_deg)
        disp = series(g[0], lambda s: np.linalg.norm(s.thrust_disp) * 1e3)
        for ax, v in ((a1, tilt), (a2, disp)):
            ax.plot(x + off[k], v, "o", color=R.SERIES[k], ms=5.5, mec="white", mew=0.8, label=lab, zorder=3)
            for xi, vi in zip(x + off[k], v):
                ax.annotate(f"{vi:.2f}" if ax is a1 else f"{vi:.1f}", (xi, vi), xytext=(0, 6),
                            textcoords="offset points", ha="center", fontsize=R.FS_SMALL, color=R.INK2)
    lim = p.si.checks.tilt_limit
    a1.axhline(lim, color=R.CRIT, lw=0.8)
    a1.text(len(cases) - 0.5, lim, f"limit {lim:g}°", fontsize=R.FS_SMALL, color=R.CRIT, va="bottom", ha="right")
    for ax in (a1, a2):                  # headroom for the value labels
        ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    for ax, lab in ((a1, "tilt (°)"), (a2, "|δ| (mm)")):
        ax.set_xticks(x, cases)
        ax.set_ylabel(lab)
        ax.grid(axis="y", color=R.HAIR, lw=0.6)
        ax.set_axisbelow(True)
        ax.spines["left"].set_visible(False)
    a1.set_title("Tilt of the thrust axis")
    a2.set_title("Thrust-point displacement")
    a2.legend(loc="lower right", title="valid runs", title_fontsize=R.FS_SMALL)
    R.title(fig, "Thrust-Point Tilt and Deflection by Load Case")
    R.note(fig, "Relative to the ground (base rigid fit). Only valid (non-mechanism) runs shown.")
    R.info_box(a1, fig, R.param_lines(study, p))
    return fig


def figures(study, env, p):
    return [("sf_by_case", lambda: build_heatmap(study, env, p)),
            ("thrust_by_case", lambda: build_thrust(study, env, p))]


if __name__ == "__main__":
    R.main(figures)
