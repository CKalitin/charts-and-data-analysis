"""Shared chart primitives — the project's house style in one place.

Wraps the bundled viz helpers (render/plotting/info_box) with the conventions
this project repeats everywhere: plasma heatmaps with labelled colorbars and
contours, the dollar log-axis formatter, the annualized↔capex twin axis (point 2
of the brief: "left side *year, right side $/kW"), the watermark, and the
"same param dict drives both the info box and the filename" rule. Change the look
of any of these once here and every chart follows.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config as cfg
from viz import info_box

HEAT_CMAP = "plasma"          # heat (utilization, profit); reserve viridis for surfaces


# --------------------------------------------------------------------------- #
# Attribution + parameter provenance
# --------------------------------------------------------------------------- #
def watermark(ax, fig, text: str = cfg.WATERMARK_TEXT) -> None:
    """Attribution auto-placed inside the axes at the emptiest available spot.
    Call after info() so the scan sees and avoids the info box."""
    info_box.add_watermark(ax, fig, text, color="#cccccc", alpha=0.9, fontsize=12.0)


def param_text(params: dict[str, str]) -> str:
    """Render an info-box body from a param dict (insertion order preserved)."""
    return "\n".join(f"{k}: {v}" for k, v in params.items())


def param_suffix(params: dict[str, str]) -> str:
    """Compact, collision-free filename suffix from the SAME param dict as the
    info box, so the two can never disagree (skill rule)."""
    clean = []
    for k, v in params.items():
        token = f"{k}{v}".replace(" ", "").replace("$", "").replace("/", "p")
        token = token.replace("·", "").replace("%", "pct").replace(",", "")
        clean.append(token)
    return "_".join(clean)


def info(ax, fig, params: dict[str, str], mode: str = "on", off_side: str = "right") -> None:
    """Place the run's parameter box (auto-located on-plot by default)."""
    info_box.add_info_box(ax, fig, param_text(params), mode=mode, off_side=off_side)


def site_label() -> str:
    """e.g. '34.86, -118.17 (2024)' — coordinates + data year, read from the file."""
    import model
    lat, lon = model.read_coords(cfg.DATA_FILE)
    parts = cfg.DATA_FILE.stem.split("_")
    year = parts[2] if len(parts) >= 3 else "?"
    return f"{lat:.2f}, {lon:.2f} ({year})"


# --------------------------------------------------------------------------- #
# Dollar / log axis formatting
# --------------------------------------------------------------------------- #
def _dollar_fmt(v: float) -> str:
    if v == 0:
        return "$0"
    if abs(v) >= 1:
        return f"${v:,.0f}"
    if abs(v) >= 0.001:
        return f"${v:.3g}"
    return f"${v:.0e}"


def dollar_colorbar(cbar) -> None:
    """Format a colorbar's ticks as dollars (its label already names the unit)."""
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _dollar_fmt(v)))


def dollar_log_axis(ax, which: str) -> None:
    """Log-scale ``which`` ('x' or 'y') with readable dollar tick labels."""
    axis = ax.xaxis if which == "x" else ax.yaxis
    (ax.set_xscale if which == "x" else ax.set_yscale)("log")
    axis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _dollar_fmt(v)))


def add_capex_twin(ax, which: str, amort_years: float = cfg.AMORTIZATION_YEARS) -> None:
    """Add a secondary axis showing raw capex ($/kW or $/kWh) opposite the
    annualized $/(unit·yr) axis. They differ by ×amortization period."""
    fwd, inv = (lambda v: v * amort_years), (lambda v: v / amort_years)
    if which == "x":
        sec = ax.secondary_xaxis("top", functions=(fwd, inv))
        sec.set_xlabel(f"(capex, {amort_years:g}-yr amortization)")
        sec.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _dollar_fmt(v)))
    else:
        sec = ax.secondary_yaxis("right", functions=(fwd, inv))
        sec.set_ylabel(f"(capex, {amort_years:g}-yr amortization)")
        sec.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _dollar_fmt(v)))


# --------------------------------------------------------------------------- #
# Contour label helpers
# --------------------------------------------------------------------------- #
def spine_clabel(ax, cs, fmt, side: str = "left", fontsize: int = 8,
                 color: str = "white", pad_pts: int = 8) -> None:
    """Label contour lines at one axes edge with guaranteed non-overlap.

    Solves the overlapping-label problem for heatmaps where many iso-contour
    lines cluster near a transition boundary (e.g., the no-build frontier in a
    profit-vs-capex plane). Standard ``clabel(inline=True)`` fails there because
    multiple labels end up stacked on top of each other.

    This function instead places each label just OUTSIDE the specified axes edge,
    so labels never sit on a contour line. A 1D de-collision pass enforces minimum
    spacing in the transverse direction.

    Algorithm:
    1. For each contour level, find its path vertex closest to ``side`` (in
       display pixels, so log/linear scale is irrelevant).
    2. Sort entries by their transverse display coordinate.
    3. Forward + backward de-collision: enforce gap >= fontsize × 1.5 px.
    4. Place each label via ``ax.text(..., transform=ax.transAxes, clip_on=False)``
       at the computed position; white bbox ensures readability on any background.
    """
    # canvas.draw() forces layout so get_window_extent() returns the real axes
    # bounding box in display pixels. Without this call the bbox is zero/wrong
    # (layout hasn't run yet) and every label lands at position (0, 0).
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    ax_bbox = ax.get_window_extent(renderer)

    entries: list[dict] = []
    for segs, level in zip(cs.allsegs, cs.levels):
        if not segs:
            continue
        all_pts = np.vstack(segs)
        if len(all_pts) < 2:
            continue

        # Convert to display pixels — handles log/linear transparently.
        disp_pts = ax.transData.transform(all_pts)

        if side == "left":
            best = int(np.argmin(disp_pts[:, 0]))
            sort_val = float(disp_pts[best, 1])
        elif side == "right":
            best = int(np.argmax(disp_pts[:, 0]))
            sort_val = float(disp_pts[best, 1])
        elif side == "top":
            best = int(np.argmax(disp_pts[:, 1]))
            sort_val = float(disp_pts[best, 0])
        else:  # "bottom"
            best = int(np.argmin(disp_pts[:, 1]))
            sort_val = float(disp_pts[best, 0])

        label_text = fmt(level) if callable(fmt) else (fmt % level)
        entries.append({"sort": sort_val, "text": label_text})

    if not entries:
        return

    entries.sort(key=lambda e: e["sort"])

    # Convergence guard: spine labels only work when the contours are SEPARATED
    # at the chosen edge. If the field has a sharp transition (a near step), every
    # iso-line crosses this edge at almost the same point, so the endpoints pile
    # up and 1D de-collision can only stack the labels in a corner. Detect that —
    # a majority of consecutive endpoint gaps smaller than one label height — and
    # fall back to inline clabel, which labels each contour on its clearest
    # interior segment (where the lines DO fan apart, e.g. along a frontier).
    min_gap = fontsize * 1.5
    sort_vals = [e["sort"] for e in entries]
    tight = sum(1 for a, b in zip(sort_vals, sort_vals[1:]) if (b - a) < min_gap)
    if len(sort_vals) >= 3 and tight > (len(sort_vals) - 1) / 2:
        ax.clabel(cs, fmt=fmt, fontsize=fontsize, inline=True, colors=color)
        return

    # 1D de-collision: forward then backward pass.
    pos = [e["sort"] for e in entries]
    for j in range(1, len(pos)):
        if pos[j] - pos[j - 1] < min_gap:
            pos[j] = pos[j - 1] + min_gap
    for j in range(len(pos) - 2, -1, -1):
        if pos[j + 1] - pos[j] < min_gap:
            pos[j] = pos[j + 1] - min_gap

    # Fixed edge position in display pixels.
    if side == "left":
        fixed_pix = ax_bbox.x0 - pad_pts
        ha, va = "right", "center"
    elif side == "right":
        fixed_pix = ax_bbox.x1 + pad_pts
        ha, va = "left", "center"
    elif side == "top":
        fixed_pix = ax_bbox.y1 + pad_pts
        ha, va = "center", "bottom"
    else:  # "bottom"
        fixed_pix = ax_bbox.y0 - pad_pts
        ha, va = "center", "top"

    inv_axes = ax.transAxes.inverted()

    # White text is invisible on figure background; use dark text with white bbox.
    text_color = "black" if color.lower() in ("white", "#ffffff") else color

    for j, entry in enumerate(entries):
        p = pos[j]
        pix = np.array([fixed_pix, p] if side in ("left", "right") else [p, fixed_pix])
        fx, fy = inv_axes.transform(pix)
        ax.text(fx, fy, entry["text"],
                transform=ax.transAxes, ha=ha, va=va,
                fontsize=fontsize, color=text_color, clip_on=False,
                bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.70))


def _prefilter_stub_levels(
    ax, x: np.ndarray, y: np.ndarray, z: np.ndarray,
    levels: np.ndarray, min_span_fraction: float = 0.25,
) -> np.ndarray:
    """Filter ``levels`` whose contour paths span too little of the axes.

    In matplotlib >= 3.8, ``ContourSet.collections`` no longer exists, so
    post-hoc hiding is not possible. Instead, this function draws an invisible
    test contour, inspects each level's path span in display pixels, and returns
    only the levels whose longest path covers at least ``min_span_fraction`` of
    the axes width **or** height.

    This is a two-pass approach (test draw then real draw). The test contour is
    fully transparent so it never appears; ``cs.remove()`` cleans it up, with a
    silent fallback if that fails (leaving an invisible, harmless artist).
    """
    if not levels.size:
        return levels

    # Force layout so the axes bounding box is correct before span checks.
    ax.figure.canvas.draw()
    cs_test = ax.contour(x, y, z, levels=levels,
                         colors=[(0, 0, 0, 0)], linewidths=0)
    renderer = ax.figure.canvas.get_renderer()
    ax_bbox = ax.get_window_extent(renderer)
    w, h = ax_bbox.width, ax_bbox.height

    keep: list[float] = []
    for segs, lv in zip(cs_test.allsegs, cs_test.levels):
        if not segs:
            continue
        all_pts = np.vstack(segs)
        if len(all_pts) < 2:
            continue
        disp_pts = ax.transData.transform(all_pts)
        span_x = (disp_pts[:, 0].max() - disp_pts[:, 0].min()) / w
        span_y = (disp_pts[:, 1].max() - disp_pts[:, 1].min()) / h
        if span_x >= min_span_fraction or span_y >= min_span_fraction:
            keep.append(float(lv))

    try:
        cs_test.remove()
    except Exception:
        pass  # invisible artist stays — harmless if remove() is unsupported

    return np.array(keep, dtype=float)


# --------------------------------------------------------------------------- #
# Heatmap primitive
# --------------------------------------------------------------------------- #
def draw_heatmap(
    ax, x: np.ndarray, y: np.ndarray, z: np.ndarray, *,
    xlabel: str, ylabel: str, title: str,
    cmap: str = HEAT_CMAP, vmin: float | None = None, vmax: float | None = None,
    norm=None, contour_levels=None, contour_fmt=None, contour_color="white",
    label_side: str = "inline",   # "inline" | "left" | "right" | "top" | "bottom"
    filter_stubs: bool = False,   # hide short stub contours before labelling
):
    """pcolormesh heatmap with optional labelled contour overlay. Returns the
    mappable (caller attaches the colorbar). z has shape (len(y), len(x)).

    label_side:
      "inline" (default) — standard ``clabel`` in-line labels. Fine when
        contour lines are spread across the axes. Breaks when many parallel
        contours cluster near a transition boundary (labels stack on each other).
      "left" / "right" / "top" / "bottom" — spine labels via ``spine_clabel``:
        labels are placed just outside the specified axes edge, guaranteed
        non-overlapping. Use this whenever contours cluster near a boundary.

    filter_stubs:
      When True, calls ``hide_stub_contours`` before labelling to suppress short
      contour fragments that appear only in a corner (abrupt-ending artifact).
    """
    mesh_kw = dict(shading="auto", cmap=cmap)
    if norm is not None:
        mesh_kw["norm"] = norm
    else:
        mesh_kw["vmin"] = z.min() if vmin is None else vmin
        mesh_kw["vmax"] = z.max() if vmax is None else vmax
    mesh = ax.pcolormesh(x, y, z, **mesh_kw)

    if contour_levels is not None:
        levels = np.asarray([lv for lv in contour_levels
                             if z.min() < lv < z.max()], dtype=float)
        if filter_stubs and levels.size:
            levels = _prefilter_stub_levels(ax, x, y, z, levels)
        if levels.size:
            cs = ax.contour(x, y, z, levels=levels, colors=contour_color,
                            linewidths=0.8, alpha=0.85)
            if contour_fmt:
                if label_side == "inline":
                    # inline clabel auto-places each label on its contour's
                    # clearest (flattest, least-crowded) segment — the right
                    # choice when contours are separated SOMEWHERE in the
                    # interior (e.g. along a frontier), even if they converge
                    # onto a single edge. Label text matches the line color;
                    # pick contour_color (black/white) for contrast with the
                    # colormap region the contours sit in.
                    ax.clabel(cs, fmt=contour_fmt, fontsize=8,
                              inline=True, colors=contour_color)
                else:
                    spine_clabel(ax, cs, contour_fmt, side=label_side,
                                 color=contour_color)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(False)   # a grid over a heatmap is noise
    return mesh


def nice_levels(z: np.ndarray, target_count: int = 6) -> np.ndarray:
    """~target_count round contour levels spanning z, snapped to 1/2/2.5/5×10^k."""
    import math
    vmin, vmax = float(np.nanmin(z)), float(np.nanmax(z))
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
        return np.array([])
    raw = (vmax - vmin) / target_count
    mag = 10.0 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1.0, 2.0, 2.5, 5.0, 10.0) if raw <= m * mag)
    first = math.ceil(vmin / step) * step
    return np.arange(first, vmax + 0.5 * step, step)


# Contour level sets reused across charts.
UTIL_CONTOURS = [0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99, 0.999]


def util_contour_fmt(v: float) -> str:
    return f"{v * 100:.3g}%"
