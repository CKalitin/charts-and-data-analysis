"""Earth-centered 2D/3D illustrations of the RAAN-sweep geometry: Earth,
v_Earth, v_infinity, and the best-in-plane departure burn for each of the
two orbital-plane families (equatorial and ecliptic), at each family's own
minimum-dV RAAN found by raan_sweep.py.

These are illustrative geometry charts, not the quantitative sweep itself
(see raan_dv.py for that) -- the point is to make the RAAN/family
definitions in raan_sweep.py's docstring visually concrete, the same role
the deleted departure_geometry_3d.py played for the old psi model.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import geometry3d as geo
import injection as inj
import raan_sweep
from viz import render


def _new_3d_figure(figsize=(8, 8)):
    """Fresh Figure + single 3D Axes via the OO API (mirrors render.new_figure,
    which only builds 2D axes -- calling fig.add_subplot() again after
    new_figure() would layer a second, stray axes)."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=figsize, dpi=render.DPI)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    return fig, ax


VIEW_HALF_EXTENT_KM = 1.8 * config.R_EARTH  # ~1.8 Earth radii half-extent
ARROW_LEN_KM = 1.55 * config.R_EARTH
EARTH_COLOR = "#2775B6"
HYPERBOLA_COLOR = "#D64545"
VEC_COLOR = "#F5B700"
VINF_COLOR = "#9B59B6"
FAMILY_COLOR = {"equatorial": "#2775B6", "ecliptic": "#C1440E"}
FAMILY_PLANE_COLOR = {"equatorial": "#8ECFE0", "ecliptic": "#F0B090"}
FAMILY_LABEL = {
    "equatorial": "Equatorial family (real polar orbit, contains Earth's spin axis)",
    "ecliptic": "Ecliptic family (\"solar-system-polar\", contains the ecliptic normal)",
}


def _draw_earth(ax):
    x, y, z = geo.sphere_surface(config.R_EARTH, n=36)
    ax.plot_surface(x, y, z, color=EARTH_COLOR, alpha=0.55, linewidth=0, shade=True)


def _draw_arrow_3d(ax, direction_hat, length, color, label, label_color, label_scale=1.15):
    end = direction_hat * length
    ax.quiver(0, 0, 0, end[0], end[1], end[2], color=color, linewidth=2.5, arrow_length_ratio=0.12)
    ax.text(*(end * label_scale), label, color=label_color, fontsize=8, ha="center")


def _default_view(n_hat):
    """A 3/4 perspective looking mostly down the orbit-plane normal (so the
    parking orbit reads as a clear ellipse, not an edge-on line), tilted off
    face-on for depth cues."""
    az = np.degrees(np.arctan2(n_hat[1], n_hat[0])) + 25.0
    el = np.degrees(np.arcsin(np.clip(n_hat[2], -1, 1))) + 35.0
    return el, az


def _plane_basis(n_hat):
    ref = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(ref, n_hat)) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    e1 = np.cross(n_hat, ref)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n_hat, e1)
    return e1, e2


def _best_burn(results, family, delta_raan_deg=None):
    """The best-in-plane burn (full state) for `family`, at its own
    minimum-dV RAAN offset from the cached sweep unless delta_raan_deg is
    given explicitly."""
    baseline = results.baseline
    sweep = raan_sweep.load(baseline)
    dv = sweep.dv_equatorial_kms if family == "equatorial" else sweep.dv_ecliptic_kms
    if delta_raan_deg is None:
        i = int(np.argmin(dv))
        delta_raan_deg = float(sweep.delta_raan_deg[i])
    n_hat = raan_sweep.plane_normal(baseline, family, delta_raan_deg)
    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM
    best = inj.solve_best_burn_for_plane(n_hat, baseline.v_inf_dep_eq, r_park,
                                          config.GM_EARTH, n_scan=360)
    return n_hat, delta_raan_deg, best


def draw_families_overview(ax, results):
    """Both families' own optimal planes together in one scene -- makes the
    two plane-family definitions, and how differently they orient
    themselves, visually concrete."""
    baseline = results.baseline
    v_earth_hat = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)
    v_inf_hat = baseline.v_inf_dep_eq / np.linalg.norm(baseline.v_inf_dep_eq)

    _draw_earth(ax)
    _draw_arrow_3d(ax, v_earth_hat, ARROW_LEN_KM, VEC_COLOR,
                    f"v_Earth\n{np.linalg.norm(baseline.v_earth_eq):.2f} km/s", "#B38600")
    _draw_arrow_3d(ax, v_inf_hat, ARROW_LEN_KM, VINF_COLOR,
                    f"v_infinity\n{np.linalg.norm(baseline.v_inf_dep_eq):.2f} km/s", "#6C3483")

    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM
    n_hat_ref = None
    for family in ("equatorial", "ecliptic"):
        n_hat, delta_raan, best = _best_burn(results, family)
        if n_hat_ref is None:
            n_hat_ref = n_hat
        e1, e2 = _plane_basis(n_hat)
        half = 1.7 * r_park
        X, Y, Z = geo.plane_patch(e1, e2, half, n=2)
        ax.plot_surface(X, Y, Z, color=FAMILY_PLANE_COLOR[family], alpha=0.20, linewidth=0)
        orbit_pts = geo.circle_points(e1, e2, r_park, n=200)
        ax.plot(orbit_pts[:, 0], orbit_pts[:, 1], orbit_pts[:, 2], color=FAMILY_COLOR[family],
                lw=2.0, label=f"{FAMILY_LABEL[family]}\n(own minimum, dRAAN={delta_raan:.0f} deg, "
                              f"{best.delta_v_mag:.2f} km/s)")

    ax.set_xlabel("Earth-equatorial X (km)")
    ax.set_ylabel("Earth-equatorial Y (km)")
    ax.set_zlabel("Earth-equatorial Z (km)")
    ax.set_title("The two 'polar' plane families, each at its own minimum-dV RAAN")
    geo.set_axes_equal_box(ax, VIEW_HALF_EXTENT_KM)
    elev, azim = _default_view(n_hat_ref)
    ax.view_init(elev=elev, azim=azim)
    ax.legend(loc="upper left", fontsize=7)


def draw_departure_3d(ax, results, family):
    baseline = results.baseline
    n_hat, delta_raan, best = _best_burn(results, family)
    v_earth_hat = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)

    _draw_earth(ax)
    _draw_arrow_3d(ax, v_earth_hat, ARROW_LEN_KM, VEC_COLOR,
                    f"v_Earth\n{np.linalg.norm(baseline.v_earth_eq):.2f} km/s", "#B38600")

    v_inf_mag = np.linalg.norm(baseline.v_inf_dep_eq)
    v_inf_hat = baseline.v_inf_dep_eq / v_inf_mag
    out_of_plane_deg = np.degrees(np.arcsin(np.clip(np.dot(v_inf_hat, n_hat), -1, 1)))
    _draw_arrow_3d(ax, v_inf_hat, ARROW_LEN_KM, VINF_COLOR,
                    f"v_infinity\n{v_inf_mag:.2f} km/s\n({out_of_plane_deg:+.1f} deg out of plane)",
                    "#6C3483")

    e1, e2 = _plane_basis(n_hat)
    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM
    orbit_pts = geo.circle_points(e1, e2, r_park, n=200)
    ax.plot(orbit_pts[:, 0], orbit_pts[:, 1], orbit_pts[:, 2], color=FAMILY_COLOR[family],
            lw=1.6, alpha=0.65, label="Parking orbit (this plane)")

    r_hat = best.r_burn / np.linalg.norm(best.r_burn)
    nu_burn = np.radians(best.injection.true_anomaly_burn_deg)
    peri_hat = geo.peri_direction(r_hat, best.injection.orbit_normal, nu_burn)
    p = config.GM_EARTH / v_inf_mag ** 2 * (best.injection.eccentricity ** 2 - 1)
    nu_span = np.radians(55.0)  # extend just far enough to visibly diverge within the view box
    hyp_pts = geo.conic_points(peri_hat, best.injection.orbit_normal, best.injection.eccentricity, p,
                                nu_burn, nu_burn + nu_span, n=150)
    ax.plot(hyp_pts[:, 0], hyp_pts[:, 1], hyp_pts[:, 2], color=HYPERBOLA_COLOR, lw=2.2,
            label="Orbit after burn (hyperbolic)")

    ax.scatter(*best.r_burn, color="black", s=25, zorder=6, label="Burn point")

    dv_vec = best.injection.v_after - best.v_before
    dv_dir = dv_vec / np.linalg.norm(dv_vec)
    dv_arrow_len = 0.9 * config.R_EARTH
    ax.quiver(*best.r_burn, *(dv_dir * dv_arrow_len), color="#111111", linewidth=1.8,
              arrow_length_ratio=0.2)
    ax.text(*(best.r_burn + dv_dir * dv_arrow_len * 1.15),
            f"burn\n{best.injection.delta_v_mag:.2f} km/s", fontsize=7.5, ha="center")

    ax.set_xlabel("Earth-equatorial X (km)")
    ax.set_ylabel("Earth-equatorial Y (km)")
    ax.set_zlabel("Earth-equatorial Z (km)")
    ax.set_title(f"{FAMILY_LABEL[family]}\n"
                 f"Best burn at its own minimum-dV RAAN (dRAAN={delta_raan:.0f} deg): "
                 f"{best.injection.delta_v_mag:.3f} km/s")
    geo.set_axes_equal_box(ax, VIEW_HALF_EXTENT_KM)
    elev, azim = _default_view(n_hat)
    ax.view_init(elev=elev, azim=azim)
    ax.legend(loc="upper left", fontsize=8)


def draw_departure_topdown(ax, results, family):
    """True orthographic top-down view of this family's own minimum-dV
    plane: right_hat is built from v_Earth's IN-PLANE component (so v_Earth
    generally points left, as in the old psi charts), up_hat completes the
    plane. Unlike the old psi model, this plane is only guaranteed to
    contain v_Earth exactly at dRAAN=0 -- away from that (as here, at each
    family's own optimum) v_Earth itself has a small out-of-plane
    component too, so its projected length is a real foreshortening,
    labeled explicitly rather than hidden, same as v_infinity's."""
    baseline = results.baseline
    n_hat, delta_raan, best = _best_burn(results, family)
    v_earth_hat = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)
    v_inf_mag = np.linalg.norm(baseline.v_inf_dep_eq)
    v_inf_hat = baseline.v_inf_dep_eq / v_inf_mag

    v_earth_in_plane = v_earth_hat - np.dot(v_earth_hat, n_hat) * n_hat
    right_hat = -v_earth_in_plane / np.linalg.norm(v_earth_in_plane)
    up_hat = np.cross(n_hat, right_hat)

    def proj(v):
        return geo.project_2d(v, right_hat, up_hat)

    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM

    earth_theta = np.linspace(0, 2 * np.pi, 100)
    ax.fill(config.R_EARTH * np.cos(earth_theta), config.R_EARTH * np.sin(earth_theta),
            color=EARTH_COLOR, alpha=0.55, zorder=2)

    orbit_pts = geo.circle_points(right_hat, up_hat, r_park, n=200)
    orbit_2d = proj(orbit_pts)
    ax.plot(orbit_2d[:, 0], orbit_2d[:, 1], color=FAMILY_COLOR[family], lw=1.6, alpha=0.65,
            zorder=3, label="Parking orbit (this plane)")

    ve_out_deg = np.degrees(np.arcsin(np.clip(np.dot(v_earth_hat, n_hat), -1, 1)))
    v_earth_end = proj(v_earth_hat * ARROW_LEN_KM)  # foreshortened by cos(ve_out_deg)
    ax.annotate("", xy=v_earth_end, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=VEC_COLOR, lw=2.5, mutation_scale=18))
    ax.text(*(v_earth_end * 1.12),
            f"v_Earth\n{np.linalg.norm(baseline.v_earth_eq):.2f} km/s\n"
            f"({ve_out_deg:+.1f} deg out of this plane)",
            color="#B38600", fontsize=8, ha="center", zorder=6)

    vinf_out_deg = np.degrees(np.arcsin(np.clip(np.dot(v_inf_hat, n_hat), -1, 1)))
    v_inf_end = proj(v_inf_hat * ARROW_LEN_KM)  # foreshortened by cos(vinf_out_deg)
    ax.annotate("", xy=v_inf_end, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=VINF_COLOR, lw=2.5, mutation_scale=18))
    ax.text(*(v_inf_end * 1.18),
            f"v_infinity\n{v_inf_mag:.2f} km/s\n({vinf_out_deg:+.1f} deg out of this plane)",
            color="#6C3483", fontsize=8, ha="center", zorder=6)

    r_hat = best.r_burn / np.linalg.norm(best.r_burn)
    nu_burn = np.radians(best.injection.true_anomaly_burn_deg)
    peri_hat = geo.peri_direction(r_hat, best.injection.orbit_normal, nu_burn)
    p = config.GM_EARTH / v_inf_mag ** 2 * (best.injection.eccentricity ** 2 - 1)
    nu_span = np.radians(55.0)
    hyp_pts = geo.conic_points(peri_hat, best.injection.orbit_normal, best.injection.eccentricity, p,
                                nu_burn, nu_burn + nu_span, n=150)
    hyp_2d = proj(hyp_pts)
    # angle BETWEEN THE TWO PLANES = acute angle between their normals
    plane_tilt_deg = np.degrees(np.arccos(np.clip(
        abs(np.dot(best.injection.orbit_normal, n_hat)), -1, 1)))
    ax.plot(hyp_2d[:, 0], hyp_2d[:, 1], color=HYPERBOLA_COLOR, lw=2.2, zorder=4,
            label=f"Orbit after burn (its plane is {plane_tilt_deg:.1f} deg from this one)")

    burn_2d = proj(best.r_burn)
    ax.scatter(*burn_2d, color="black", s=30, zorder=6, label="Burn point")

    dv_vec = best.injection.v_after - best.v_before
    dv_dir = dv_vec / np.linalg.norm(dv_vec)
    dv_proj = proj(dv_dir)
    dv_proj_norm = np.linalg.norm(dv_proj)
    dv_2d_hat = dv_proj / dv_proj_norm if dv_proj_norm > 1e-9 else np.array([0.0, -1.0])
    dv_out_of_plane_deg = np.degrees(np.arcsin(np.clip(np.dot(dv_dir, n_hat), -1, 1)))
    # fixed, short on-screen arrow length so it never clips past the view
    # box regardless of burn-point position near the edge (r_park ~= R_EARTH)
    dv_end = burn_2d + dv_2d_hat * 0.45 * config.R_EARTH
    ax.annotate("", xy=dv_end, xytext=burn_2d,
                arrowprops=dict(arrowstyle="-|>", color="#111111", lw=1.8, mutation_scale=14,
                                 zorder=7))
    ax.text(*(dv_end + 0.15 * config.R_EARTH * np.array([1, 1])),
            f"burn: {best.injection.delta_v_mag:.2f} km/s\n"
            f"({dv_out_of_plane_deg:+.1f} deg out of this plane)",
            fontsize=7.5, ha="center", zorder=6)

    ax.set_xlabel("In-plane, ~opposite v_Earth's in-plane component (km)")
    ax.set_ylabel("In-plane, perpendicular to that (km)")
    ax.set_title(f"Face-on to the {family} family's own minimum-dV plane "
                 f"(dRAAN={delta_raan:.0f} deg)\n"
                 f"Best-in-plane burn: {best.injection.delta_v_mag:.3f} km/s. Orthographic.")
    ax.set_xlim(-VIEW_HALF_EXTENT_KM, VIEW_HALF_EXTENT_KM)
    ax.set_ylim(-VIEW_HALF_EXTENT_KM, VIEW_HALF_EXTENT_KM)
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=7.5)


def figures(results):
    out = []

    def build_overview():
        fig, ax = _new_3d_figure()
        draw_families_overview(ax, results)
        return fig, config.OUTPUT_ROOT / "geometry" / "01_earth_both_families.png"
    out.append(("geometry_overview", build_overview))

    for i, family in enumerate(("equatorial", "ecliptic")):
        def build_3d(family=family, i=i):
            fig, ax = _new_3d_figure()
            draw_departure_3d(ax, results, family)
            return fig, config.OUTPUT_ROOT / "geometry" / f"{2 + i:02d}_departure_3d_{family}.png"
        out.append((f"geometry_3d_{family}", build_3d))

    for i, family in enumerate(("equatorial", "ecliptic")):
        def build_topdown(family=family, i=i):
            fig, ax = render.new_figure(figsize=(8, 8))
            draw_departure_topdown(ax, results, family)
            return fig, config.OUTPUT_ROOT / "geometry" / f"{4 + i:02d}_departure_topdown_{family}.png"
        out.append((f"geometry_topdown_{family}", build_topdown))

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
