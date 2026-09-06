"""World heatmap of satellite capacity utilization per lat/lon tile, plus an
animation of how it changes as the constellation grows.

Utilization here = the share of the satellite capacity passing over a tile that is
actually carrying customers, under tile_capacity_model.py's 2D allocation (every
customer who CAN be served IS served). It answers "where are the satellites busy,
and where are they flying over empty capacity" -- a different question from what
share of the population is served, and one the earlier latitude-pooled model could
not ask at all, since it had no longitude dimension to be busy or idle along.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from matplotlib.colors import Normalize
from matplotlib.patches import PathPatch
import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import capacity_density_model as cdm            # noqa: E402
import orbital_geometry as og                   # noqa: E402
import tile_capacity_model as tcm               # noqa: E402
from coverage_map import load_land_paths        # noqa: E402
from viz import render                          # noqa: E402

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "tile_capacity"

#: Real-world provenance, not repo paths -- a reader must be able to weigh the sources.
SOURCE_NOTE = ("Sources: WorldPop 1km population; Starlink Gen1 shell geometry from FCC "
               "filings/Celestrak; 25 deg minimum user-terminal elevation from FCC Order 21-48; "
               "household size from national censuses via Wikipedia compilation.")

STATIC_FLEETS = [
    (4_408, "Gen1 authorised constellation"),
    (10_900, "approximate fleet in orbit, 2026"),
    (100_000, ""),
]

#: Log-spaced fleet sizes for the animation. Starts below today's fleet and runs past
#: the point where the whole world population saturates (~6M satellites).
GIF_FLEETS = np.unique(np.round(np.geomspace(500, 5_000_000, 40))).astype(int)

#: Animation frames render smaller than the stills -- 40 full-DPI frames make an
#: unwieldy GIF, and the map reads fine at this size.
GIF_DPI = 100


def _headline(result: tcm.AllocationResult, scenario: cdm.CapacityScenario, note: str = "") -> str:
    """The three numbers the animation is actually about: fleet size, people reached,
    and how much of the fleet's capacity that uses."""
    people = result.population.sum()
    served_pct = 100 * result.total_served_people / people
    util = 100 * result.total_served / (result.total_sats * cdm.max_customers_per_satellite(scenario))
    tail = f"   ({note})" if note else ""
    return (f"{result.total_sats:,.0f} satellites     "
            f"{result.total_served_people/1e6:,.0f}M of {people/1e9:.2f}B people served ({served_pct:.1f}%)     "
            f"constellation utilization {util:.1f}%{tail}")


def _detail_text(result: tcm.AllocationResult, tile: tcm.TileGrid,
                 scenario: cdm.CapacityScenario) -> str:
    """The inputs that actually move this chart.

    The two field-of-view numbers are different angles of the same triangle, so both
    are named: 25 deg is measured at the user terminal, above its local horizon (the
    FCC assumption); ~8 deg is measured at Earth's centre, from the sub-satellite
    point out to the edge of the servable disk. The latter is a function of altitude
    only, not latitude -- but at the equator it also equals 8 deg of longitude, which
    is what "at equator" pins down for a reader looking at this map.
    """
    hh = float((result.population * result.household_size).sum() / result.population.sum())
    return (
        f"{scenario.label.split('_')[0].upper()} capacity scenario: "
        f"{cdm.max_customers_per_satellite(scenario):,.0f} connections/satellite, "
        f"{cdm.max_customer_density_per_km2(scenario):,.0f} connections/km2 per satellite in view   |   "
        f"{result.total_served/1e6:,.0f}M connections at {hh:.2f} people each\n"
        f"User FOV: {og.MIN_ELEVATION_DEG:.0f} deg   |   Sat FOV at equator: ~8 deg   |   "
        f"{tile.tile_deg:g} deg tiles\n"
        f"{SOURCE_NOTE}"
    )


def _fit_width(fig, text_artist, max_frac: float = 0.97) -> None:
    """Shrink a fig-level text until it fits the figure width.

    The headline's length changes every frame (satellite counts run from 3 to 7
    digits), so a fixed font size that fits one frame can overflow another. Measure
    the rendered extent and step the size down rather than guessing -- this project
    has hit text-overflow layout bugs repeatedly.
    """
    fig.canvas.draw()
    for _ in range(12):
        width_frac = text_artist.get_window_extent(fig.canvas.get_renderer()).width / fig.bbox.width
        if width_frac <= max_frac:
            return
        text_artist.set_fontsize(text_artist.get_fontsize() * 0.94)
        fig.canvas.draw()


def draw_utilization_map(ax, result: tcm.AllocationResult, tile: tcm.TileGrid, land_paths):
    """The single renderer behind both the static charts and every animation frame.

    Continents are drawn as unfilled outlines ON TOP of the mesh -- a filled basemap
    would hide exactly the tiles the chart is about.
    """
    lon_edges = np.linspace(-180, 180, tile.shape[1] + 1)
    lat_edges = np.linspace(-90, 90, tile.shape[0] + 1)
    util = np.ma.masked_invalid(result.utilization)

    mesh = ax.pcolormesh(lon_edges, lat_edges, util, cmap="plasma",
                         norm=Normalize(0, 1), shading="flat", zorder=1)
    for p in land_paths:
        ax.add_patch(PathPatch(p, facecolor="none", edgecolor="#33ffdd",
                               linewidth=0.45, alpha=0.85, zorder=3))
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(False)
    return mesh


def _make_figure(result, tile, land_paths, note, scenario, dpi=None, emphasis=False):
    """One figure. `emphasis=True` promotes the headline numbers to axis-label size
    directly under the plot, for the large-label animation."""
    fig, ax = render.new_figure(figsize=(14, 8.5), dpi=dpi)
    mesh = draw_utilization_map(ax, result, tile, land_paths)
    ax.set_title("Satellite capacity utilization vs longitude and latitude")
    cbar = fig.colorbar(mesh, ax=ax, pad=0.02, fraction=0.024)
    cbar.set_label("Share of overhead satellite capacity in use")
    # FuncFormatter rather than PercentFormatter: this project sets text.parse_math=False,
    # and several matplotlib default formatters emit mathtext that then renders literally.
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))

    # Text goes under the axes, not in an auto-placed in-axes box: a full-bleed world
    # map has no empty region for the info_box scan to find, so any in-axes placement
    # necessarily covers real tiles.
    headline = _headline(result, scenario, note)
    detail = _detail_text(result, tile, scenario)
    if emphasis:
        axis_label_size = ax.xaxis.label.get_fontsize()
        t = fig.text(0.5, 0.072, headline, fontsize=axis_label_size, fontweight="bold",
                     color="#111111", ha="center", va="bottom")
        _fit_width(fig, t)
        fig.text(0.012, 0.010, detail, fontsize=6.8, color="#555555",
                 va="bottom", ha="left", linespacing=1.5)
    else:
        fig.text(0.012, 0.012, headline + "\n" + detail, fontsize=7.5, color="#333333",
                 va="bottom", ha="left", linespacing=1.5)
    return fig


def figures(tile=None, demand=None, land_paths=None):
    tile = tile if tile is not None else tcm.make_tile_grid()
    demand = demand if demand is not None else tcm.build_demand(tile)
    land_paths = land_paths if land_paths is not None else load_land_paths()
    cache: dict = {}

    def build(n, note):
        def _b():
            res = tcm.solve(n, tile=tile, demand=demand, operator_cache=cache)
            fig = _make_figure(res, tile, land_paths, note, cdm.V3_SCENARIO)
            return fig, OUT_ROOT / f"utilization_map_{n}sats.png"
        return _b

    return [(f"utilization_map_{n}sats", build(n, note)) for n, note in STATIC_FLEETS]


#: Frames are written here as individual PNGs alongside the animations.
FRAME_DIRS = {False: OUT_ROOT / "frames", True: OUT_ROOT / "frames_large_labels"}
GIF_PATHS = {False: OUT_ROOT / "utilization_map_vs_satellites.gif",
             True: OUT_ROOT / "utilization_map_vs_satellites_large_labels.gif"}


def render_sweep(tile=None, demand=None, land_paths=None, fleets=GIF_FLEETS,
                 fps: float = 4.0, variants=(False, True), save_frames: bool = True,
                 verbose: bool = True) -> list[Path]:
    """Render both animation variants, and every frame as a PNG, in ONE pass.

    The model solve is by far the expensive part (~15 s per fleet size), and it does
    not depend on how the figure is labelled -- so each fleet size is solved once and
    both variants are drawn from the same AllocationResult. Rendering the variants in
    separate passes would double a ~9 minute job for no reason.

    Frames go through the same draw_utilization_map() renderer as the stills, and are
    assembled with Pillow rather than matplotlib's animation API, so there is no
    second code path to drift.
    """
    from PIL import Image

    tile = tile if tile is not None else tcm.make_tile_grid()
    demand = demand if demand is not None else tcm.build_demand(tile)
    land_paths = land_paths if land_paths is not None else load_land_paths()
    cache: dict = {}

    frames = {v: [] for v in variants}
    for v in variants:
        if save_frames:
            FRAME_DIRS[v].mkdir(parents=True, exist_ok=True)

    for i, n in enumerate(fleets, 1):
        res = tcm.solve(int(n), tile=tile, demand=demand, operator_cache=cache)
        for v in variants:
            fig = _make_figure(res, tile, land_paths, "", cdm.V3_SCENARIO,
                               dpi=GIF_DPI, emphasis=v)
            fig.canvas.draw()
            img = Image.frombytes("RGBA", fig.canvas.get_width_height(),
                                  bytes(fig.canvas.buffer_rgba())).convert("RGB")
            frames[v].append(img)
            if save_frames:
                # zero-padded index keeps the directory in fleet order; the satellite
                # count in the name makes a single frame identifiable on its own.
                img.save(FRAME_DIRS[v] / f"frame_{i:03d}_{int(n):09d}sats.png")
        if verbose:
            print(f"  frame {i}/{len(fleets)}: N={n:,} served {res.total_served/1e6:,.0f}M connections "
                  f"({res.total_served_people/1e6:,.0f}M people)")

    written = []
    for v in variants:
        path = GIF_PATHS[v]
        path.parent.mkdir(parents=True, exist_ok=True)
        frames[v][0].save(path, save_all=True, append_images=frames[v][1:],
                          duration=int(1000 / fps), loop=0, optimize=True)
        written.append(path)
    return written


if __name__ == "__main__":
    import time

    t0 = time.time()
    tile = tcm.make_tile_grid()
    demand = tcm.build_demand(tile)
    land = load_land_paths()

    plan = figures(tile, demand, land)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(OUT_ROOT.parent.parent)}")

    if "--gif" in sys.argv:
        print(f"\nrendering {len(GIF_FLEETS)} frames x 2 label variants...")
        for path in render_sweep(tile=tile, demand=demand, land_paths=land):
            print(f"  wrote {path.relative_to(OUT_ROOT.parent.parent)}")
        for v, d in FRAME_DIRS.items():
            print(f"  wrote {len(list(d.glob('*.png')))} PNGs to {d.relative_to(OUT_ROOT.parent.parent)}")

    print(f"\ndone in {time.time() - t0:.1f}s")
