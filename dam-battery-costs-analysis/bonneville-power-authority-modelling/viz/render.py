"""Headless rendering layer — the one place matplotlib is configured.

This is the performance backbone. It uses the object-oriented Agg API (NO pyplot),
sets all rcParams ONCE at import, and provides three things chart code needs:

  - new_figure()   : a fresh single-axes Figure (one-off charts, or any chart with a
                     colorbar — colorbars do not clear cleanly from a reused figure)
  - ReusableFigure : a Figure held open and cleared with ax.cla() between charts. This is
                     the bulk-sweep pattern: allocation cost is paid once per worker, not
                     once per chart, which is the difference between "X seconds" and
                     "Z.Z minutes" when you render hundreds of charts.
  - save_fig()     : mkdir + savefig on a CHEAP path (no bbox_inches='tight', which forces
                     an extra full render pass just to measure the tight bounding box)

Chart functions should draw onto a *provided* Axes (def draw(ax, ...)) so the exact same
chart code works for both a one-off figure and the reused-figure sweep path. That single
convention is what lets the fast path and the pretty path share one implementation instead
of drifting into two.

Why pyplot is banned here: pyplot keeps global figure state that is not process-safe (it
breaks under multiprocessing) and leaks figures if you forget plt.close(). The OO API
(Figure + FigureCanvasAgg) has neither problem.

The DEFAULTS below are deliberately conservative; pass overrides at call time, or edit them
once here. Keep ALL styling in this module — never set rcParams or figure styling at a call
site, or you reintroduce the duplication this layer exists to prevent.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, fork/spawn-safe; MUST precede the figure imports below

from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

# --- Defaults (edit once, here — not at call sites) ------------------------------------
FIGSIZE = (10, 6)
DPI = 150            # presentation-quality single charts
BULK_DPI = 90        # bulk sweeps: raster cost scales ~DPI^2, so this is a big lever
GRID = True
BULK_PNG_COMPRESS_LEVEL = 1   # zlib level 0-9; lower = faster + larger files

# Configure style ONCE at import — never per figure.
matplotlib.rcParams.update({
    "figure.constrained_layout.use": True,   # cheaper + safer than per-figure tight_layout()
    "axes.grid": GRID,
    "grid.linestyle": "--",
    "grid.alpha": 0.4,
    "font.size": 10,
    "legend.fontsize": 9,
    "savefig.bbox": None,                     # explicitly NOT 'tight' (avoids extra render pass)
    "text.parse_math": False,                 # treat $ as a literal character, not LaTeX math
})


def new_figure(figsize=None, dpi=None):
    """Create a fresh Figure + single Axes via the OO API. Returns (fig, ax).

    Use this for one-off charts and for ANY chart that adds a colorbar (a reused figure
    accumulates colorbar axes that ax.cla() will not remove).
    """
    fig = Figure(figsize=figsize or FIGSIZE, dpi=dpi or DPI)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(1, 1, 1)
    return fig, ax


def save_fig(fig, path: Path | str, dpi: int | None = None,
             compress_level: int | None = None) -> Path:
    """Write `fig` to `path` (parent dirs created). Cheap path: fixed layout, tuned PNG zlib.

    Deliberately does NOT pass bbox_inches='tight' — that triggers a second render pass to
    compute the bounding box, which is pure overhead at scale. Lay out with constrained_layout
    (set in rcParams) instead.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pil_kwargs = None
    if compress_level is not None and path.suffix.lower() == ".png":
        pil_kwargs = {"compress_level": compress_level}
    fig.savefig(path, dpi=dpi or DPI, pil_kwargs=pil_kwargs)
    return path


class ReusableFigure:
    """A single Figure reused across many charts — the per-worker performance pattern.

    Call `.axes()` to get a CLEARED Axes to draw on, then `.save(path)`. The Figure itself is
    never torn down, so the (surprisingly large) figure-allocation cost is paid once per worker
    instead of once per chart. On a sweep of hundreds/thousands of line charts this is the
    single biggest win after using the Agg OO API at all.

    Caveat: do NOT use this for charts that add a colorbar — use new_figure() for those, since
    colorbar axes are not removed by ax.cla() and will accumulate across charts.
    """

    def __init__(self, figsize=None, dpi=None):
        self.fig = Figure(figsize=figsize or FIGSIZE, dpi=dpi or BULK_DPI)
        FigureCanvasAgg(self.fig)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self._dpi = dpi or BULK_DPI

    def axes(self):
        """Return a freshly-cleared Axes ready to draw the next chart on."""
        self.ax.cla()
        return self.ax

    def save(self, path: Path | str, compress_level: int | None = None) -> Path:
        return save_fig(self.fig, path, dpi=self._dpi,
                        compress_level=(BULK_PNG_COMPRESS_LEVEL
                                        if compress_level is None else compress_level))
