"""Earth-centered 3D illustrations of the psi geometry: Earth, v_Earth,
the polar parking orbit, its plane, and the departure (post-burn) hyperbola.

These are illustrative geometry charts, not the quantitative psi sweep
(see departure_dv.py for that) -- the point is to make the abstract psi
definition in patched_conic.py's docstring visually concrete.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import geometry3d as geo
import patched_conic as pc
from viz import render


def _new_3d_figure(figsize=(8, 8)):
    """Fresh Figure + single 3D Axes via the OO API (mirrors render.new_figure,
    which only builds 2D axes -- see the skill's edge-case catalog: calling
    fig.add_subplot() again after new_figure() layers a second, stray axes)."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=figsize, dpi=render.DPI)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    return fig, ax

VIEW_HALF_EXTENT_KM = 1.8 * config.R_EARTH  # ~1.8 Earth radii half-extent (~1.4 diameters wide)
ARROW_LEN_KM = 1.55 * config.R_EARTH
EARTH_COLOR = "#2775B6"
ORBIT_COLOR = "#3FA34D"
HYPERBOLA_COLOR = "#D64545"
PLANE_COLOR = "#8ECFE0"
VEC_COLOR = "#F5B700"


def _draw_earth(ax):
    x, y, z = geo.sphere_surface(config.R_EARTH, n=36)
    ax.plot_surface(x, y, z, color=EARTH_COLOR, alpha=0.55, linewidth=0, shade=True)


def _draw_v_earth_arrow(ax, v_earth_hat, label_speed_kms):
    end = v_earth_hat * ARROW_LEN_KM
    ax.quiver(0, 0, 0, end[0], end[1], end[2], color=VEC_COLOR, linewidth=2.5,
              arrow_length_ratio=0.12)
    label_pos = end * 1.12
    ax.text(*label_pos, f"v_Earth\n{label_speed_kms:.2f} km/s", color="#B38600",
            fontsize=8, ha="center")


def _default_view(n_hat):
    """A 3/4 perspective looking mostly down the orbit-plane normal (so the
    parking orbit reads as a clear ellipse, not an edge-on line), tilted off
    face-on for depth cues."""
    az = np.degrees(np.arctan2(n_hat[1], n_hat[0])) + 25.0
    el = np.degrees(np.arcsin(np.clip(n_hat[2], -1, 1))) + 35.0
    return el, az


def _base_scene(ax, baseline, title, n_hat, elev=None, azim=None):
    v_earth_hat = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)
    _draw_earth(ax)
    _draw_v_earth_arrow(ax, v_earth_hat, np.linalg.norm(baseline.v_earth_eq))

    ax.set_xlabel("Earth-equatorial X (km)")
    ax.set_ylabel("Earth-equatorial Y (km)")
    ax.set_zlabel("Earth-equatorial Z (km)")
    ax.set_title(title)
    geo.set_axes_equal_box(ax, VIEW_HALF_EXTENT_KM)
    if elev is None or azim is None:
        elev, azim = _default_view(n_hat)
    ax.view_init(elev=elev, azim=azim)
    return v_earth_hat


def draw_plain(ax, results, highlight_plane=False):
    baseline = results.baseline
    geom0 = pc.burn_point_geometry(baseline.v_earth_eq, 0.0)
    v_earth_hat = _base_scene(
        ax, baseline,
        "Polar parking orbit and Earth's heliocentric velocity\n"
        + ("(orbit plane highlighted -- it contains v_Earth by construction)"
           if highlight_plane else "(psi-independent: every psi shares this orbit)"),
        geom0.n_hat,
    )

    e_t0_hat = np.cross(geom0.n_hat, v_earth_hat)
    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM

    if highlight_plane:
        half = 1.7 * r_park
        X, Y, Z = geo.plane_patch(v_earth_hat, e_t0_hat, half, n=2)
        ax.plot_surface(X, Y, Z, color=PLANE_COLOR, alpha=0.22, linewidth=0)

    orbit_pts = geo.circle_points(v_earth_hat, e_t0_hat, r_park, n=200)
    ax.plot(orbit_pts[:, 0], orbit_pts[:, 1], orbit_pts[:, 2], color=ORBIT_COLOR,
            lw=2.0, label=f"Polar parking orbit ({config.PARKING_ALTITUDE_KM:.0f} km alt)")
    ax.legend(loc="upper left", fontsize=8)


def draw_departure(ax, results, psi_deg):
    baseline = results.baseline
    geom0 = pc.burn_point_geometry(baseline.v_earth_eq, 0.0)
    v_earth_hat = _base_scene(
        ax, baseline,
        f"Departure burn at psi = {psi_deg:.0f} deg\n"
        f"(original polar orbit -> post-burn hyperbola)",
        geom0.n_hat,
    )

    e_t0_hat = np.cross(geom0.n_hat, v_earth_hat)
    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM

    orbit_pts = geo.circle_points(v_earth_hat, e_t0_hat, r_park, n=200)
    ax.plot(orbit_pts[:, 0], orbit_pts[:, 1], orbit_pts[:, 2], color=ORBIT_COLOR,
            lw=1.6, alpha=0.65, label="Original polar orbit")

    geom = pc.burn_point_geometry(baseline.v_earth_eq, psi_deg)
    burn = pc.solve_injection_burn(geom, baseline.v_inf_dep_eq)

    nu_burn = np.radians(burn.true_anomaly_burn_deg)
    peri_hat = geo.peri_direction(geom.r_hat, burn.orbit_normal, nu_burn)
    p = config.GM_EARTH / np.linalg.norm(baseline.v_inf_dep_eq) ** 2 * (burn.eccentricity ** 2 - 1)

    # extend just far enough past the burn point to visibly diverge within the view box
    nu_span = np.radians(55.0)
    hyp_pts = geo.conic_points(peri_hat, burn.orbit_normal, burn.eccentricity, p,
                                nu_burn, nu_burn + nu_span, n=150)
    ax.plot(hyp_pts[:, 0], hyp_pts[:, 1], hyp_pts[:, 2], color=HYPERBOLA_COLOR, lw=2.2,
            label="Orbit after burn (hyperbolic)")

    ax.scatter(*geom.r_burn, color="black", s=25, zorder=6, label="Burn point")

    dv_dir = burn.delta_v / np.linalg.norm(burn.delta_v)
    dv_arrow_len = 0.9 * config.R_EARTH
    ax.quiver(*geom.r_burn, *(dv_dir * dv_arrow_len), color="#111111", linewidth=1.8,
              arrow_length_ratio=0.2)
    ax.text(*(geom.r_burn + dv_dir * dv_arrow_len * 1.15),
            f"burn\n{burn.delta_v_mag:.2f} km/s", fontsize=7.5, ha="center")

    ax.legend(loc="upper left", fontsize=8)


def figures(results):
    out = []

    def build_plain():
        fig, ax = _new_3d_figure()
        draw_plain(ax, results, highlight_plane=False)
        return fig, config.OUTPUT_ROOT / "geometry" / "01_earth_polar_orbit_plain.png"
    out.append(("geometry_plain", build_plain))

    def build_plane():
        fig, ax = _new_3d_figure()
        draw_plain(ax, results, highlight_plane=True)
        return fig, config.OUTPUT_ROOT / "geometry" / "02_earth_polar_orbit_plane_highlighted.png"
    out.append(("geometry_plane", build_plane))

    psi_cheapest = float(results.psi_deg[np.argmin(results.dv_departure_kms)])

    def build_burn_cheapest():
        fig, ax = _new_3d_figure()
        draw_departure(ax, results, psi_cheapest)
        return fig, config.OUTPUT_ROOT / "geometry" / f"03_departure_psi_{psi_cheapest:.0f}_cheapest.png"
    out.append(("geometry_burn_cheapest", build_burn_cheapest))

    psi_offset = psi_cheapest + 15.0

    def build_burn_offset():
        fig, ax = _new_3d_figure()
        draw_departure(ax, results, psi_offset)
        return fig, config.OUTPUT_ROOT / "geometry" / f"04_departure_psi_{psi_offset:.0f}_15deg_off.png"
    out.append(("geometry_burn_offset", build_burn_offset))

    return out


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
