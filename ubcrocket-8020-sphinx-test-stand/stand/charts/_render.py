"""Headless rendering layer — the one place matplotlib is configured (adapted from the
charting skill's render.py).  OO Agg only, rcParams set once, cheap save (no tight bbox).

Also holds what every chart family shares, so a fix lands everywhere at once:
palette + SF status bins, title band, info box (input parameters), 1D label
de-collision, projections, filename suffix from changed parameters.
"""
from __future__ import annotations

import pickle
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless; MUST precede the figure imports below

import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from . import _info_box  # noqa: E402

# --- palette (dataviz reference instance; status colours used by exception) -----------
INK, INK2, MUTED, HAIR, FAINT = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#f0efec"
SAFE_MEMBER, SAFE_JOINT = "#b9b8b2", "#8a8984"
CRIT, SERIOUS = "#d03b3b", "#ec835a"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
TENSION, COMPRESSION = "#2a78d6", "#eb6834"      # diverging pair (cool / warm)
TERM_LABEL = {"U_shear": "slip (shear)", "U_pull": "bolt pull", "U_Mx": "tilt Mx", "U_My": "tilt My",
              "U_Mz": "twist Mz", "U_bend_line": "plate bend (line)", "U_bend_stem": "plate bend (stem)"}
TERM_COLOR = {t: SERIES[i] for i, t in enumerate(TERM_LABEL)}

DPI = 200
TITLE_IN, FOOT_IN = 0.40, 0.22       # reserved bands (inches)
FS_SMALL, FS_TEXT, FS_LABEL = 6.6, 7.4, 8.5

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": FS_LABEL, "axes.titlesize": FS_LABEL,
    "axes.titleweight": "normal", "axes.titlecolor": INK2, "axes.titlelocation": "left",
    "axes.edgecolor": HAIR, "axes.linewidth": 0.8, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": FS_TEXT, "ytick.labelsize": FS_TEXT,
    "xtick.major.size": 0, "ytick.major.size": 0, "xtick.minor.size": 0, "ytick.minor.size": 0,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    "text.color": INK, "legend.fontsize": FS_TEXT, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "figure.constrained_layout.use": True, "text.parse_math": False, "svg.fonttype": "none",
})


# ------------------------------------------------------------------ figure + save
def new_figure(w_in: float, h_in: float, foot: bool = True) -> Figure:
    """Fresh Figure (no axes) with a title band on top and an optional footnote band."""
    fig = Figure(figsize=(w_in, h_in), dpi=DPI)
    FigureCanvasAgg(fig)
    bottom = FOOT_IN / h_in if foot else 0.0
    fig.get_layout_engine().set(rect=(0, bottom, 1, 1 - bottom - TITLE_IN / h_in))
    return fig


# reading order of the figures; files are numbered from it (01_stand_sf.png, ...)
FIGURE_ORDER = ["layout", "stand_sf", "sf_ranking", "joint_sf_terms", "sf_by_case", "thrust_by_case", "axial_force",
                "peak_stress", "deflection", "buckling_mode", "sandbag_demand", "ground_reaction", "ground_by_case", "ktheta_sweep"]


def fig_stem(name: str, present: list[str] | None = None) -> str:
    """'stand_sf' -> '01_stand_sf', numbered in FIGURE_ORDER among the figures present in this run."""
    order = [n for n in FIGURE_ORDER if present is None or n in present]
    return f"{order.index(name) + 1:02d}_{name}" if name in order else name


def save_fig(fig: Figure, path: Path, svg: bool = False) -> list[Path]:
    """PNG (document) [+ SVG (editable)]. Cheap path: no bbox_inches='tight'."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = [path.with_suffix(".png")] + ([path.with_suffix(".svg")] if svg else [])
    for o in out:
        fig.savefig(o)
    return out


def title(fig: Figure, text: str) -> None:
    fig.text(0.01, 1 - 0.07 / fig.get_figheight(), text, ha="left", va="top",
             fontsize=11, fontweight="bold", color=INK)


def note(fig: Figure, text: str) -> None:
    """One-line footnote (method notes only; parameters go in the info box)."""
    fig.text(0.01, 0.012, textwrap.shorten(text, int(fig.get_figwidth() * 21), placeholder="…"),
             color=MUTED, fontsize=FS_SMALL, ha="left", va="bottom")


# ------------------------------------------------------------------ parameters on the chart
def param_lines(study, p, extra: list[str] | None = None) -> list[str]:
    """The inputs that move the result (taste-selected), plus anything changed from defaults."""
    si = p.si
    lines = [f"thrust {si.loads.thrust:.0f} N × DF {si.loads.DF:g}"
             + (" × ½ (2D)" if study.model.mode == "2d" else ""),
             f"misalignment {si.loads.misalign_x:g}·F",
             f"bolt F_i {si.bolts.preload / 1e3:g} kN, μ {si.bolts.mu:g}"]
    changed = [c for c in p.changes if c.key not in ("loads.thrust_N", "loads.DF", "loads.misalign_x",
                                                     "bolts.preload_N", "bolts.mu")]
    lines += [f"{c.key.split('.')[-1]} = {c.value}" for c in changed]
    return lines + (extra or [])


def info_box(ax, fig, lines: list[str], fontsize: float = FS_SMALL) -> None:
    """Auto-placed in the emptiest spot of `ax` — call LAST (after data, labels, legend)."""
    _info_box.add_info_box(ax, fig, "\n".join(lines), mode="on", fontsize=fontsize)


def suffix(p) -> str:
    """Filename suffix from changed parameters ('' at defaults) — same source as the info box."""
    if not p.changes:
        return ""
    parts = [f"{c.key.split('.')[-1]}{c.value}" for c in p.changes]
    return "_" + "_".join(parts).replace(" ", "").replace("/", "-").replace("[", "").replace("]", "")


def basis(study) -> str:
    return (f"worst of {len({s.run.label for s in study.solves})} runs × "
            f"{len({s.case for s in study.solves})} cases + k_θ sweep")


# ------------------------------------------------------------------ shared helpers
def bin_color(sf: float, target: float, safe: str) -> str:
    if sf is None or not np.isfinite(sf):
        return safe
    return CRIT if sf < 1 else SERIOUS if sf < target else safe


def spread(values, min_gap: float) -> list[float]:
    """1D de-collision: push positions apart by >= min_gap, preserving order and mean."""
    if len(values) == 0:
        return []
    order = np.argsort(values)
    v = np.array(values, float)[order]
    for _ in range(200):
        moved = False
        for i in range(1, len(v)):
            if v[i] - v[i - 1] < min_gap - 1e-12:
                mid = 0.5 * (v[i] + v[i - 1])
                v[i - 1], v[i] = mid - min_gap / 2, mid + min_gap / 2
                moved = True
        if not moved:
            break
    out = np.empty_like(v)
    out[order] = v
    return list(out)


HALO = dict(boxstyle="square,pad=0.12", facecolor="white", edgecolor="none", alpha=0.85)


def view_labels(ax, labels, base_z: float = 120.0) -> None:
    """Point labels on a stand view: (x, y, text).  Base-row points (y < base_z, front view)
    go in staggered rows under the base; the rest stack to the right, de-collided in y."""
    base = sorted([l for l in labels if l[1] < base_z], key=lambda l: l[0])
    rest = [l for l in labels if l[1] >= base_z]
    arrow = dict(arrowstyle="-", color=HAIR, lw=0.6, shrinkA=0, shrinkB=2)
    for k, ((x, y, s), x2) in enumerate(zip(base, spread([l[0] for l in base], 170.0))):
        ax.annotate(s, (x, y), xytext=(x2, -150 - 120 * (k % 2)), textcoords="data", fontsize=FS_SMALL,
                    color=INK2, ha="center", va="top", zorder=7, bbox=HALO, arrowprops=arrow)
    for (x, y, s), y2 in zip(rest, spread([l[1] for l in rest], 64.0)):
        ax.annotate(s, (x, y), xytext=(x + 55, y2), textcoords="data", fontsize=FS_SMALL,
                    color=INK2, ha="left", va="center", zorder=7, bbox=HALO, arrowprops=arrow)
    if base:
        lo, hi = ax.get_ylim()
        ax.set_ylim(min(lo, -340), hi)


def place_point_labels(ax, fig, labels, *, candidates=None, fontsize=FS_SMALL,
                       settle=True) -> list:
    """Greedy non-overlapping point labels.

    `labels` is [(x, y, text, kwargs)] in data coords, optionally with a 5th element giving
    that label's own candidate offsets (a member id may only slide to either side of its own
    line, a node id may go anywhere). Place the most constrained first — one call for the
    whole chart, so every label sees the ones already down. Each label is created once as an
    annotation in *offset points*, then moved: the first candidate offset whose rendered box
    clears every box already placed wins; if none does, the least-overlapping one is kept.
    Solved here rather than per chart so a fix lands everywhere (see also view_labels, which
    is the leader-line variant for a handful of called-out points).
    """
    if candidates is None:                      # 8 compass directions at two radii
        candidates = [(round(r * np.cos(a), 1), round(r * np.sin(a), 1))
                      for r in (9.0, 15.0, 22.0)        # crowded views need the outer ring
                      for a in np.radians([45, 135, 225, 315, 0, 90, 180, 270])]
    arts, cands = [], []
    for lab in labels:
        x, y, text, kw = lab[:4]
        cands.append(list(lab[4]) if len(lab) > 4 else candidates)
        arts.append(ax.annotate(text, xy=(x, y), xytext=cands[-1][0],
                                textcoords="offset points", fontsize=fontsize,
                                bbox=HALO, **kw))
    # Placement is only valid against the FINAL geometry: axis limits, equal aspect, legend
    # and title must all be set first, or the data->display mapping changes underneath it.
    # One draw settles constrained_layout, then it is frozen — it re-solves on every draw and
    # would shift the axes, invalidating every box already measured. Pass settle=False when
    # the caller has already done this (placing across several axes of one figure).
    if settle:
        fig.canvas.draw()
        fig.set_layout_engine("none")
    renderer = fig.canvas.get_renderer()

    def put(t, dx, dy):
        t.set_position((dx, dy))
        t.set_ha("left" if dx > 1 else "right" if dx < -1 else "center")
        t.set_va("bottom" if dy > 1 else "top" if dy < -1 else "center")
        return t.get_window_extent(renderer)

    ax_bb = ax.get_window_extent(renderer)
    placed: list = []
    for t, cand in zip(arts, cands):
        best, best_bb, best_score = cand[0], None, None
        for dx, dy in cand:
            bb = put(t, dx, dy)
            # overlapping a neighbour is the real defect; leaving the axes is a lesser one
            score = sum(_overlap(bb, q) for q in placed) + 0.25 * _outside(bb, ax_bb)
            if score == 0:
                best, best_bb = (dx, dy), bb
                break
            if best_score is None or score < best_score:
                best, best_bb, best_score = (dx, dy), bb, score
        placed.append(put(t, *best) if best_bb is None else (put(t, *best) or best_bb))
    return arts


def _outside(bb, ax_bb) -> float:
    """Area of `bb` sticking out past the axes rectangle."""
    inside_w = max(0.0, min(bb.x1, ax_bb.x1) - max(bb.x0, ax_bb.x0))
    inside_h = max(0.0, min(bb.y1, ax_bb.y1) - max(bb.y0, ax_bb.y0))
    return max(0.0, (bb.x1 - bb.x0) * (bb.y1 - bb.y0) - inside_w * inside_h)


def _overlap(a, b) -> float:
    w = min(a.x1, b.x1) - max(a.x0, b.x0)
    h = min(a.y1, b.y1) - max(a.y0, b.y0)
    return w * h if w > 0 and h > 0 else 0.0


def bracket_name(r) -> str:
    """'N5 bracket 1' (+ ' copy 2' for duplicated brackets), leg and member."""
    copy = f" copy {r['copy'] + 1}" if r.get("copy") else ""
    return f"{r['joint']} bracket {r['bracket']}{copy}, leg {r['leg']} on {r['member']}"


def log_axis(axis) -> None:
    axis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
    axis.set_minor_formatter(mticker.NullFormatter())


# third-angle orthographic views: (horizontal index, vertical index, depth index, labels)
VIEWS = {"front": (0, 2, 1, "x (mm)", "z (mm)", "Front (x–z)"),
         "side": (1, 2, 0, "y (mm)", "z (mm)", "Side (y–z)"),
         "plan": (0, 1, 2, "x (mm)", "y (mm)", "Plan (x–y)")}


def view_axes(fig, study, extra_right_mm: float = 450.0, plan: bool = True):
    """True-scale front / side (/ plan) axes sharing one mm scale. Returns {view: ax}."""
    m = study.model
    span = np.ptp(m.x, axis=0) * 1e3 + 300
    if m.mode == "2d":
        return {"front": fig.add_subplot(1, 1, 1)}, None
    if plan:
        gs = fig.add_gridspec(2, 2, width_ratios=[span[0] + extra_right_mm, span[1]],
                              height_ratios=[span[2], span[1]])
        axes = {"front": fig.add_subplot(gs[0, 0]), "side": fig.add_subplot(gs[0, 1]),
                "plan": fig.add_subplot(gs[1, 0])}
        spare = fig.add_subplot(gs[1, 1])
        spare.axis("off")
        return axes, spare
    gs = fig.add_gridspec(1, 2, width_ratios=[span[0] + extra_right_mm, span[1]])
    return {"front": fig.add_subplot(gs[0]), "side": fig.add_subplot(gs[1])}, None


def finish_view(ax, view: str) -> None:
    *_, xl, yl, t = VIEWS[view]
    ax.set_aspect("equal")
    ax.set_title(t)
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    ax.spines[:].set_visible(False)


def member_polyline(study, mid: int, i: int, j: int, u: np.ndarray | None = None, scale: float = 0.0):
    m = study.model
    ns = m.member_nodes[mid]
    P = m.x[ns] * 1e3
    if u is not None:
        P = P + scale * u.reshape(-1, 6)[ns, :3] * 1e3
    return P[:, i], P[:, j]


def deform_scale(study, p) -> float:
    m = study.model
    dmax = max((s.max_disp for s in study.solves if s.valid), default=0.0)
    return p.si.output.deform_frac * np.ptp(m.x[:, 2]) / dmax if dmax > 0 else 0.0


# ------------------------------------------------------------------ cache + standalone runs
def cache_path(out: Path) -> Path:
    return out / ".cache" / "study.pkl"


def save_cache(study, env, p, out: Path) -> Path:
    path = cache_path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump((study, env, p), fh)
    return path


def load_cache(out: Path):
    path = cache_path(out)
    if not path.exists():
        raise SystemExit(f"no cached study at {path}; run `python -m stand run` first")
    with open(path, "rb") as fh:
        return pickle.load(fh)


def main(figures_fn) -> None:
    """`python -m stand.charts.<family> [results_dir]`: re-render one family from the cache."""
    import sys
    import time
    from ..params import PROJECT_DIR
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_DIR / "results" / "3d"
    study, env, p = load_cache(out)
    t0 = time.time()
    plan = figures_fn(study, env, p)
    for name, build in plan:
        from . import names
        for f in save_fig(build(), out / "figures" / fig_stem(name, names(study, env, p)), p.si.output.svg):
            print(f"  wrote {f.relative_to(PROJECT_DIR) if f.is_relative_to(PROJECT_DIR) else f}")
    print(f"{len(plan)} chart(s) in {time.time() - t0:.1f} s")
