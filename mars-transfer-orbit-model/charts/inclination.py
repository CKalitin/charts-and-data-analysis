"""Heliocentric inclination of Mars' orbit relative to the ecliptic.

Two panels answering the same question at two magnifications, because the
honest answer has two halves:

  TOP    True-scale EDGE-ON view, looking straight down Mars' line of nodes.
         In this projection the ecliptic (Earth's orbit plane, i = 0 by
         definition) collapses to a horizontal line and Mars' orbit plane
         collapses to a line tilted by exactly its inclination. Nothing is
         exaggerated: the angle you measure off the screen is the real one.
         Both nodes lie along the viewing direction, so they project onto
         the Sun.

  BOTTOM What that small angle is actually WORTH -- Mars' height above/below
         the ecliptic over one Mars year, in millions of km, with the
         heliocentric latitude (which peaks at exactly the inclination) on
         the twin axis.

The pairing is the point: 1.85 deg sounds negligible and is, angularly, but
it puts Mars up to ~7e6 km out of the ecliptic plane -- which is why an
Earth->Mars Lambert solve has to be done in 3D and why the transfer plane is
not the ecliptic.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import elements
import frames
import geometry3d as geo
from viz import render, info_box

EARTH_COLOR = "#2775B6"
MARS_COLOR = "#C1440E"
SUN_COLOR = "#F5B700"
NODE_COLOR = "#7A7A7A"
LAT_COLOR = "#6A4C93"

Z_HAT = np.array([0.0, 0.0, 1.0])
N_TRACK = 720  # samples per full orbit; the bottom panel is read off this curve


def _ecliptic_states(baseline):
    """Ecliptic-frame (r, v) for Earth at departure and Mars at arrival."""
    return (
        (frames.eq_to_ecl(baseline.r_earth_eq), frames.eq_to_ecl(baseline.v_earth_eq)),
        (frames.eq_to_ecl(baseline.r_mars_eq), frames.eq_to_ecl(baseline.v_mars_eq)),
    )


def geometry(baseline):
    """Everything both panels need, computed once."""
    (r_e, v_e), (r_m, v_m) = _ecliptic_states(baseline)
    el_earth = elements.from_state(r_e, v_e, config.GM_SUN)
    el_mars = elements.from_state(r_m, v_m, config.GM_SUN)
    earth_track = elements.orbit_track(r_e, v_e, config.GM_SUN, n_points=N_TRACK)
    mars_track = elements.orbit_track(r_m, v_m, config.GM_SUN, n_points=N_TRACK)
    return el_earth, el_mars, earth_track, mars_track, r_e, r_m


# --------------------------------------------------------------------------- #
# Top panel: true-scale edge-on view along the line of nodes
# --------------------------------------------------------------------------- #
PANEL_TITLE = "Height Above Ecliptic vs Distance From Sun"

STANDALONE_TITLE = "Mars Orbit Tilt vs Ecliptic"


def draw_edge_on(ax, baseline, el_mars, earth_track, mars_track, r_e, r_m,
                 ylim=(-0.28, 0.28), title=PANEL_TITLE, title_fontsize=9.5):
    """Edge-on view down the line of nodes.

    ylim (AU) sets only how much empty sky is framed around the planes -- the
    aspect is locked equal, so the tilt RENDERS at exactly i whatever ylim is.
    A tight symmetric window gives the thin strip the stacked panel wants; the
    standalone chart opens up the TOP only, so an info box has somewhere to sit
    while the annotations keep the same short leaders to the lines.
    """
    au = config.AU_KM
    # Look ALONG the node line: screen right = z_hat x node_hat (in the ecliptic
    # plane, perpendicular to the nodes), screen up = z_hat. The ecliptic then
    # projects to the horizontal axis and Mars' plane to a line at exactly i.
    right_hat = np.cross(Z_HAT, el_mars.node_hat)
    right_hat /= np.linalg.norm(right_hat)

    def proj(pts):
        return geo.project_2d(np.asarray(pts), right_hat, Z_HAT) / au

    earth_2d, mars_2d = proj(earth_track), proj(mars_track)
    e_pt, m_pt = proj(r_e), proj(r_m)

    ax.plot(earth_2d[:, 0], earth_2d[:, 1], color=EARTH_COLOR, lw=2.2, solid_capstyle="round")
    ax.plot(mars_2d[:, 0], mars_2d[:, 1], color=MARS_COLOR, lw=2.2, solid_capstyle="round")
    ax.scatter([0], [0], color=SUN_COLOR, s=140, marker="*", zorder=6,
               edgecolor="black", linewidth=0.4)
    ax.scatter([e_pt[0]], [e_pt[1]], color=EARTH_COLOR, s=38, zorder=6,
               edgecolor="black", linewidth=0.4)
    ax.scatter([m_pt[0]], [m_pt[1]], color=MARS_COLOR, s=38, zorder=6,
               edgecolor="black", linewidth=0.4)

    # The inclination wedge. A bare arc is only a few pixels tall at true scale on
    # a 1.85-degree opening, so SHADE the wedge between the two planes -- that is
    # what actually reads -- and keep the arc as the angle's formal marker.
    tan_i = np.tan(np.radians(el_mars.i_deg))
    x_wedge = np.linspace(0.0, 1.85, 2)  # runs to the axis edge: no visible cut
    ax.fill_between(x_wedge, 0.0, x_wedge * tan_i, color=MARS_COLOR, alpha=0.18, lw=0)
    arc_r = 0.9
    th = np.radians(np.linspace(0.0, el_mars.i_deg, 60))
    ax.plot(arc_r * np.cos(th), arc_r * np.sin(th), color="#333333", lw=1.0, zorder=5)
    mid = np.radians(el_mars.i_deg / 2)
    # Annotation positions are FIXED in AU, not scaled to ylim: the leaders have to
    # stay short, and only the free space around them changes between framings.
    y_label = -0.21   # the two plane labels, below the lines
    ax.annotate(f"i = {el_mars.i_deg:.3f}°", xy=(arc_r * np.cos(mid), arc_r * np.sin(mid)),
                xytext=(0.62, 0.15), fontsize=10, ha="left", va="bottom",
                color="#333333", arrowprops=dict(arrowstyle="-", color="#333333", lw=0.7))

    ax.annotate("ecliptic = Earth's orbit plane, i ≡ 0 (edge-on)",
                xy=(-1.25, 0.0), xytext=(-1.80, y_label), fontsize=8, color=EARTH_COLOR,
                ha="left", va="bottom",
                arrowprops=dict(arrowstyle="-", color=EARTH_COLOR, lw=0.6))
    ax.annotate("Mars orbit plane (edge-on)", xy=(1.50, 1.50 * tan_i), xytext=(1.02, y_label),
                fontsize=8, color=MARS_COLOR, ha="left", va="bottom",
                arrowprops=dict(arrowstyle="-", color=MARS_COLOR, lw=0.6))
    ax.annotate(f"Mars @ {baseline.arr_epoch}", xy=(m_pt[0], m_pt[1]),
                xytext=(6, -14), textcoords="offset points", fontsize=7.5, color=MARS_COLOR)
    ax.annotate(f"Earth @ {baseline.dep_epoch}", xy=(e_pt[0], e_pt[1]),
                xytext=(6, -14), textcoords="offset points", fontsize=7.5, color=EARTH_COLOR)

    ax.set_xlim(-1.85, 1.85)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.set_xlabel("Distance from the Sun in the ecliptic plane, perpendicular to the nodes (AU)")
    ax.set_ylabel("Height above\necliptic (AU)")
    ax.set_title(title, fontsize=title_fontsize)


# --------------------------------------------------------------------------- #
# Bottom panel: what 1.85 deg is worth in kilometres
# --------------------------------------------------------------------------- #
def draw_height(ax, baseline, el_mars, mars_track, r_m):
    lon = np.degrees(np.arctan2(mars_track[:, 1], mars_track[:, 0])) % 360.0
    z_mkm = mars_track[:, 2] / 1e6
    lat_deg = np.degrees(np.arcsin(mars_track[:, 2] / np.linalg.norm(mars_track, axis=1)))
    order = np.argsort(lon)  # longitude is monotonic along a prograde orbit, bar the wrap
    lon, z_mkm, lat_deg = lon[order], z_mkm[order], lat_deg[order]

    ax.axhline(0.0, color=EARTH_COLOR, lw=1.6,
               label="ecliptic plane (Earth's orbit), z ≡ 0")
    ax.plot(lon, z_mkm, color=MARS_COLOR, lw=2.0, label="Mars: height above the ecliptic")

    ax2 = ax.twinx()
    ax2.plot(lon, lat_deg, color=LAT_COLOR, lw=1.3, ls="--",
             label="Mars: heliocentric latitude (peaks at exactly i)")
    ax2.set_ylabel("Heliocentric latitude (deg)", color=LAT_COLOR)
    ax2.tick_params(axis="y", labelcolor=LAT_COLOR)
    ax2.grid(False)

    # At the ascending node the curve rises through zero (upper-left is clear); at
    # the descending node it falls (upper-right is clear). Label into the gap.
    for lon_node, name, (dx, ha) in ((el_mars.raan_deg, "ascending node", (-6, "right")),
                                     ((el_mars.raan_deg + 180.0) % 360.0,
                                      "descending node", (6, "left"))):
        ax.axvline(lon_node, color=NODE_COLOR, ls=":", lw=1.1)
        ax.annotate(f"{name}\n{lon_node:.1f}°", xy=(lon_node, 0.0), xytext=(dx, 10),
                    textcoords="offset points", fontsize=7.5, color=NODE_COLOR,
                    ha=ha, va="bottom")

    # Headroom so the peak callouts below are not clipped, and a twin-axis range
    # scaled from the same limits so latitude 0 stays aligned with height 0.
    z_lo, z_hi = float(z_mkm.min()) * 1.70, float(z_mkm.max()) * 1.30
    ax.set_ylim(z_lo, z_hi)
    deg_per_mkm = el_mars.i_deg / float(np.abs(z_mkm).max())
    ax2.set_ylim(z_lo * deg_per_mkm, z_hi * deg_per_mkm)

    i_hi, i_lo = int(z_mkm.argmax()), int(z_mkm.argmin())
    for idx, va, dy in ((i_hi, "bottom", 8), (i_lo, "top", -32)):
        ax.annotate(f"{z_mkm[idx]:+.2f}e6 km  ({z_mkm[idx] * 1e6 / config.AU_KM:+.3f} AU)",
                    xy=(lon[idx], z_mkm[idx]), xytext=(0, dy), textcoords="offset points",
                    fontsize=8, color=MARS_COLOR, ha="center", va=va)

    lon_arr = float(np.degrees(np.arctan2(r_m[1], r_m[0])) % 360.0)
    ax.scatter([lon_arr], [r_m[2] / 1e6], color=MARS_COLOR, s=45, zorder=6,
               edgecolor="black", linewidth=0.5,
               label=f"Mars @ arrival {baseline.arr_epoch}: {r_m[2] / 1e6:+.2f}e6 km")

    ax.set_xlim(0, 360)
    ax.set_xticks(np.arange(0, 361, 45))
    ax.set_xlabel("Heliocentric ecliptic longitude of Mars (deg, J2000)")
    ax.set_ylabel("Height above the ecliptic (millions of km)")
    ax.set_title("Height Above Ecliptic vs Heliocentric Longitude", fontsize=9.5)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower left", fontsize=8)
    return ax2


def _params(baseline, el_earth, el_mars, mars_track, r_m):
    """The taste-selected inputs behind both versions of this chart -- shared so
    the two-panel and edge-on-only charts can never quote different numbers."""
    z_max_mkm = float(np.abs(mars_track[:, 2]).max()) / 1e6
    return {
        "state epochs": f"Earth {baseline.dep_epoch} / Mars {baseline.arr_epoch}",
        "Mars i (vs ecliptic J2000)": f"{el_mars.i_deg:.3f}°",
        "Mars RAAN": f"{el_mars.raan_deg:.2f}°",
        "Earth i (same reference)": f"{el_earth.i_deg:.4f}°",
        "max |z| over one Mars year": f"{z_max_mkm:.2f}e6 km ({z_max_mkm * 1e6 / config.AU_KM:.4f} AU)",
        "Mars z at arrival": f"{r_m[2] / 1e6:+.2f}e6 km",
    }


def _add_info_box(ax, params):
    info_box.add_info_box(ax, ax.figure, "\n".join(f"{k}: {v}" for k, v in params.items()),
                          mode="on")


def draw(axes, results):
    """Both panels: the true angle on top, what it is worth in km below."""
    baseline = results.baseline
    el_earth, el_mars, earth_track, mars_track, r_e, r_m = geometry(baseline)
    ax_top, ax_bot = axes

    draw_edge_on(ax_top, baseline, el_mars, earth_track, mars_track, r_e, r_m)
    draw_height(ax_bot, baseline, el_mars, mars_track, r_m)
    _add_info_box(ax_bot, _params(baseline, el_earth, el_mars, mars_track, r_m))


def draw_edge_on_only(ax, results, ylim=(-0.30, 0.62)):
    """Just the edge-on tilt view, standalone. Identical geometry and identical
    true scale to the top panel -- the frame just opens upward to make room for
    the info box, which on the stacked version lives on the other panel."""
    baseline = results.baseline
    el_earth, el_mars, earth_track, mars_track, r_e, r_m = geometry(baseline)

    draw_edge_on(ax, baseline, el_mars, earth_track, mars_track, r_e, r_m,
                 ylim=ylim, title=STANDALONE_TITLE, title_fontsize=13)
    _add_info_box(ax, _params(baseline, el_earth, el_mars, mars_track, r_m))


def figures(results):
    arr = results.baseline.arr_epoch
    out = config.OUTPUT_ROOT / "geometry"

    def build_both():
        fig, axes = render.new_figure_grid(2, 1, figsize=(11, 7.5),
                                           height_ratios=[1.0, 2.4])
        draw(axes, results)
        fig.suptitle("Mars Orbit Tilt vs Ecliptic", fontsize=13)
        return fig, out / f"mars_ecliptic_inclination_{arr}.png"

    def build_edge_on():
        fig, ax = render.new_figure(figsize=(11, 4.2))
        draw_edge_on_only(ax, results)
        return fig, out / f"mars_ecliptic_inclination_edge_on_{arr}.png"

    return [("mars_ecliptic_inclination", build_both),
            ("mars_ecliptic_inclination_edge_on", build_edge_on)]


if __name__ == "__main__":
    import time
    import derived

    t0 = time.time()
    results = derived.load()
    plan = figures(results)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(config.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
