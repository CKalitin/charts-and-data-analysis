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
VINF_COLOR = "#9B59B6"


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


def _draw_v_inf_arrow(ax, v_inf_hat, label_speed_kms, out_of_plane_deg=None):
    """v_infinity is drawn at the SAME arrow length as v_Earth (both are pure
    direction indicators here, not to-scale against each other or against
    position) so the angle between them reads directly off the chart; true
    magnitudes are given in the label instead."""
    end = v_inf_hat * ARROW_LEN_KM
    ax.quiver(0, 0, 0, end[0], end[1], end[2], color=VINF_COLOR, linewidth=2.5,
              arrow_length_ratio=0.12)
    label_pos = end * 1.18
    suffix = f"\n({out_of_plane_deg:+.1f} deg out of plane)" if out_of_plane_deg is not None else ""
    ax.text(*label_pos, f"v_infinity\n{label_speed_kms:.2f} km/s{suffix}", color="#6C3483",
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

    v_inf_mag = np.linalg.norm(baseline.v_inf_dep_eq)
    v_inf_hat = baseline.v_inf_dep_eq / v_inf_mag
    out_of_plane_deg = np.degrees(np.arcsin(np.clip(np.dot(v_inf_hat, geom0.n_hat), -1, 1)))
    _draw_v_inf_arrow(ax, v_inf_hat, v_inf_mag, out_of_plane_deg)

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


def draw_departure_topdown(ax, results, psi_deg):
    """True orthographic top-down view of the v_Earth-containing orbital
    plane: right_hat = -v_Earth_hat (so v_Earth points left, as requested)
    and up_hat = e_t0_hat, both in-plane and mutually perpendicular. Vectors
    that lie exactly in this plane (v_Earth, the parking orbit, the burn
    point) project losslessly; v_infinity and the post-burn hyperbola
    generally do NOT lie exactly in this plane (that's the whole point of
    the psi != 0 result -- see README) so their projection is a real
    foreshortening, called out explicitly in the labels rather than hidden."""
    baseline = results.baseline
    geom0 = pc.burn_point_geometry(baseline.v_earth_eq, 0.0)
    v_earth_hat = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)
    n_hat = geom0.n_hat
    right_hat = -v_earth_hat
    up_hat = np.cross(n_hat, v_earth_hat)

    def proj(v):
        return geo.project_2d(v, right_hat, up_hat)

    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM

    earth_theta = np.linspace(0, 2 * np.pi, 100)
    ax.fill(config.R_EARTH * np.cos(earth_theta), config.R_EARTH * np.sin(earth_theta),
            color=EARTH_COLOR, alpha=0.55, zorder=2)

    orbit_pts = geo.circle_points(v_earth_hat, up_hat, r_park, n=200)
    orbit_2d = proj(orbit_pts)
    ax.plot(orbit_2d[:, 0], orbit_2d[:, 1], color=ORBIT_COLOR, lw=1.6, alpha=0.65,
            zorder=3, label="Original polar orbit")

    v_earth_end = proj(v_earth_hat * ARROW_LEN_KM)
    ax.annotate("", xy=v_earth_end, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=VEC_COLOR, lw=2.5, mutation_scale=18))
    ax.text(*(v_earth_end * 1.12), f"v_Earth\n{np.linalg.norm(baseline.v_earth_eq):.2f} km/s",
            color="#B38600", fontsize=8, ha="center", zorder=6)

    v_inf_mag = np.linalg.norm(baseline.v_inf_dep_eq)
    v_inf_hat = baseline.v_inf_dep_eq / v_inf_mag
    out_of_plane_deg = np.degrees(np.arcsin(np.clip(np.dot(v_inf_hat, n_hat), -1, 1)))
    v_inf_end = proj(v_inf_hat * ARROW_LEN_KM)  # foreshortened by cos(out_of_plane_deg)
    ax.annotate("", xy=v_inf_end, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=VINF_COLOR, lw=2.5, mutation_scale=18))
    ax.text(*(v_inf_end * 1.18), f"v_infinity\n{v_inf_mag:.2f} km/s\n"
            f"({out_of_plane_deg:+.1f} deg out of this plane)",
            color="#6C3483", fontsize=8, ha="center", zorder=6)

    geom = pc.burn_point_geometry(baseline.v_earth_eq, psi_deg)
    burn = pc.solve_injection_burn(geom, baseline.v_inf_dep_eq)
    nu_burn = np.radians(burn.true_anomaly_burn_deg)
    peri_hat = geo.peri_direction(geom.r_hat, burn.orbit_normal, nu_burn)
    p = config.GM_EARTH / v_inf_mag ** 2 * (burn.eccentricity ** 2 - 1)
    nu_span = np.radians(55.0)
    hyp_pts = geo.conic_points(peri_hat, burn.orbit_normal, burn.eccentricity, p,
                                nu_burn, nu_burn + nu_span, n=150)
    hyp_2d = proj(hyp_pts)
    # angle BETWEEN THE TWO PLANES = acute angle between their normals (abs()
    # of the dot product removes the sign ambiguity of "which way is normal")
    plane_tilt_deg = np.degrees(np.arccos(np.clip(abs(np.dot(burn.orbit_normal, n_hat)), -1, 1)))
    ax.plot(hyp_2d[:, 0], hyp_2d[:, 1], color=HYPERBOLA_COLOR, lw=2.2, zorder=4,
            label=f"Orbit after burn (its plane is {plane_tilt_deg:.1f} deg from this one)")

    burn_2d = proj(geom.r_burn)
    ax.scatter(*burn_2d, color="black", s=30, zorder=6, label="Burn point")

    # The burn direction can be heavily out-of-plane (that's the whole point
    # for psi far from the optimum) -- its projection can collapse to
    # near-zero length. Draw it at a fixed 2D arrow length regardless (like
    # v_Earth/v_infinity, direction-only) and state the true magnitude and
    # out-of-plane angle in the label rather than showing a near-invisible
    # projected arrow.
    dv_dir = burn.delta_v / burn.delta_v_mag
    dv_proj = proj(dv_dir)
    dv_proj_norm = np.linalg.norm(dv_proj)
    dv_2d_hat = dv_proj / dv_proj_norm if dv_proj_norm > 1e-9 else np.array([0.0, -1.0])
    dv_out_of_plane_deg = np.degrees(np.arcsin(np.clip(np.dot(dv_dir, n_hat), -1, 1)))
    # shorter than the v_Earth/v_infinity arrows: the burn point sits near
    # the view-box edge (r_park ~= R_EARTH), so a long arrow in an outward
    # or tangential direction would run past the axes limits and get clipped
    dv_end = burn_2d + dv_2d_hat * 0.45 * config.R_EARTH
    ax.annotate("", xy=dv_end, xytext=burn_2d,
                arrowprops=dict(arrowstyle="-|>", color="#111111", lw=1.8, mutation_scale=14,
                                 zorder=7))
    ax.text(*(dv_end + 0.15 * config.R_EARTH * np.array([1, 1])),
            f"burn: {burn.delta_v_mag:.2f} km/s\n({dv_out_of_plane_deg:+.1f} deg out of this plane)",
            fontsize=7.5, ha="center", zorder=6)

    ax.set_xlabel("In-plane, opposite v_Earth (km)")
    ax.set_ylabel("In-plane, perpendicular to v_Earth (km)")
    ax.set_title(f"Top-down view of the orbital plane, psi = {psi_deg:.0f} deg\n"
                 "(orthographic; v_Earth points left by construction)")
    ax.set_xlim(-VIEW_HALF_EXTENT_KM, VIEW_HALF_EXTENT_KM)
    ax.set_ylim(-VIEW_HALF_EXTENT_KM, VIEW_HALF_EXTENT_KM)
    ax.set_aspect("equal")
    # v_Earth/v_infinity labels always sit upper-left and the burn point
    # moves around the circle with psi; upper-right is clear of both across
    # the whole comparison set. (An outside-axes legend was tried first, but
    # combined with set_aspect("equal") + constrained_layout it left a large
    # blank margin -- an equal-aspect axes shrinks to fit whichever of
    # width/height the external legend leaves less of, then constrained_layout
    # pads the other dimension to match. Keeping the legend inside avoids it.)
    ax.legend(loc="upper right", fontsize=7.5)


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
    psi_offset = psi_cheapest + 15.0

    # The comparison set spanning the "why isn't the burn tangent" story:
    # the true optimum, 15 deg off it, the naive psi=0 ("v_Earth in-plane")
    # case, and the perpendicular extreme.
    comparison = [
        (psi_cheapest, "cheapest"),
        (psi_offset, "15deg_off_cheapest"),
        (0.0, "psi0_naive"),
        (90.0, "psi90_perpendicular"),
    ]

    for i, (psi, tag) in enumerate(comparison):
        def build_3d(psi=psi, tag=tag, i=i):
            fig, ax = _new_3d_figure()
            draw_departure(ax, results, psi)
            return fig, config.OUTPUT_ROOT / "geometry" / f"{3+i:02d}_departure_3d_psi_{psi:.0f}_{tag}.png"
        out.append((f"geometry_burn_3d_{tag}", build_3d))

    for i, (psi, tag) in enumerate(comparison):
        def build_topdown(psi=psi, tag=tag, i=i):
            fig, ax = render.new_figure(figsize=(8, 8))
            draw_departure_topdown(ax, results, psi)
            return fig, config.OUTPUT_ROOT / "geometry" / f"{7+i:02d}_departure_topdown_psi_{psi:.0f}_{tag}.png"
        out.append((f"geometry_burn_topdown_{tag}", build_topdown))

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
