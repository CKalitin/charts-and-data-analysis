"""Two projections of the same psi sweep, for direct side-by-side comparison:

- "orbital-plane view": screen is the plane that actually contains the
  parking orbit (and v_Earth). The orbit renders as a true circle, psi as
  a true angle -- this is the right view for teaching what psi IS. The
  vantage point for this is near Earth's EQUATOR looking sideways, NOT
  above a pole -- the orbit-plane normal has zero component along Earth's
  spin axis (confirmed numerically), so there is no "down" here.
- "ecliptic view": screen is the actual ecliptic plane (viewing axis = the
  ecliptic normal, a literal bird's-eye view of the solar system). v_Earth
  is still undistorted (it defines the ecliptic), but the parking orbit
  is now a real, moderately squashed ellipse (minor/major axis ratio
  ~35.8%, not a near-degenerate line -- checked, not assumed) because the
  orbit's plane is tilted ~111 deg from the ecliptic normal. v_infinity's
  large (~14.4 deg) out-of-ecliptic tilt is invisible here by construction
  (that component points straight at the viewer) -- only its small
  (~3.1 deg) in-ecliptic component survives the projection. That's the
  complementary point of the "ecliptic" view: it's the one where the
  out-of-ecliptic component is exactly what's hidden -- a separate radial
  (Sun-looking-at-Earth) view would show that component directly instead.

Both views share the same v_Earth-based "right" screen axis (so v_Earth
points left in both, for comparability) and the same content (the full
psi sweep) -- projection is the only thing that changes between them.
"""
import sys
from pathlib import Path

import matplotlib as mpl
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # for departure_geometry_3d (sibling module)

import config
import frames
import geometry3d as geo
import patched_conic as pc
from departure_geometry_3d import ARROW_LEN_KM, EARTH_COLOR, VEC_COLOR, VINF_COLOR
from viz import info_box, render

SWEEP_PSI_DEG = np.arange(-90, 91, 15)  # -90, -75, ..., 90 (13 values)
CMAP = mpl.colormaps["plasma"]
VIEW_HALF_EXTENT_KM_SWEEP = 1.9 * config.R_EARTH


def _sweep_geometry(baseline):
    """All TRUE 3D geometry for the sweep, computed once, independent of
    which screen it will later be projected onto."""
    geom0 = pc.burn_point_geometry(baseline.v_earth_eq, 0.0)
    v_earth_hat = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)
    n_hat = geom0.n_hat  # orbital-plane normal (psi-independent)
    e_t0_hat = np.cross(n_hat, v_earth_hat)  # true in-plane basis, perpendicular to v_Earth
    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM

    orbit_pts_3d = geo.circle_points(v_earth_hat, e_t0_hat, r_park, n=200)

    v_inf_mag = np.linalg.norm(baseline.v_inf_dep_eq)
    v_inf_hat = baseline.v_inf_dep_eq / v_inf_mag

    burns = []
    for psi in SWEEP_PSI_DEG:
        geom = pc.burn_point_geometry(baseline.v_earth_eq, float(psi))
        burn = pc.solve_injection_burn(geom, baseline.v_inf_dep_eq)
        nu_burn = np.radians(burn.true_anomaly_burn_deg)
        peri_hat = geo.peri_direction(geom.r_hat, burn.orbit_normal, nu_burn)
        p = config.GM_EARTH / v_inf_mag ** 2 * (burn.eccentricity ** 2 - 1)
        nu_span = np.radians(40.0)
        hyp_pts_3d = geo.conic_points(peri_hat, burn.orbit_normal, burn.eccentricity, p,
                                       nu_burn, nu_burn + nu_span, n=60)
        burns.append(dict(psi=float(psi), burn=burn, r_burn_3d=geom.r_burn, hyp_pts_3d=hyp_pts_3d))

    return dict(v_earth_hat=v_earth_hat, n_hat=n_hat, e_t0_hat=e_t0_hat, r_park=r_park,
                orbit_pts_3d=orbit_pts_3d, v_inf_hat=v_inf_hat, v_inf_mag=v_inf_mag, burns=burns)


def draw(ax, results, screen_right_hat, screen_up_hat, viewing_axis_hat, view_title, view_note):
    baseline = results.baseline
    geo3d = _sweep_geometry(baseline)

    def proj(v):
        return geo.project_2d(v, screen_right_hat, screen_up_hat)

    earth_theta = np.linspace(0, 2 * np.pi, 100)
    ax.fill(config.R_EARTH * np.cos(earth_theta), config.R_EARTH * np.sin(earth_theta),
            color=EARTH_COLOR, alpha=0.55, zorder=2)

    orbit_2d = proj(geo3d["orbit_pts_3d"])
    ax.plot(orbit_2d[:, 0], orbit_2d[:, 1], color="#3FA34D", lw=1.4, alpha=0.6,
            zorder=3, label="Parking orbit (psi-independent)")

    v_earth_hat = geo3d["v_earth_hat"]
    v_earth_end = proj(v_earth_hat * ARROW_LEN_KM)
    ax.annotate("", xy=v_earth_end, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=VEC_COLOR, lw=2.5, mutation_scale=18,
                                 zorder=8))
    ax.text(*(v_earth_end * 1.12), f"v_Earth\n{np.linalg.norm(baseline.v_earth_eq):.2f} km/s",
            color="#B38600", fontsize=8, ha="center", zorder=8)

    v_inf_hat, v_inf_mag = geo3d["v_inf_hat"], geo3d["v_inf_mag"]
    out_of_screen_deg = np.degrees(np.arcsin(np.clip(np.dot(v_inf_hat, viewing_axis_hat), -1, 1)))
    v_inf_end = proj(v_inf_hat * ARROW_LEN_KM)
    ax.annotate("", xy=v_inf_end, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=VINF_COLOR, lw=2.5, mutation_scale=18,
                                 zorder=8))
    ax.text(*(v_inf_end * 1.18), f"v_infinity\n{v_inf_mag:.2f} km/s\n"
            f"({out_of_screen_deg:+.1f} deg out of THIS screen)",
            color="#6C3483", fontsize=8, ha="center", zorder=8)

    psi_cheapest = float(results.psi_deg[np.argmin(results.dv_departure_kms)])
    norm = mpl.colors.Normalize(vmin=SWEEP_PSI_DEG.min(), vmax=SWEEP_PSI_DEG.max())

    dv_rows = []
    for entry in geo3d["burns"]:
        psi, burn = entry["psi"], entry["burn"]
        color = CMAP(norm(psi))
        dv_rows.append((psi, burn.delta_v_mag))

        hyp_2d = proj(entry["hyp_pts_3d"])
        is_cheapest = abs(psi - psi_cheapest) < 1e-6
        ax.plot(hyp_2d[:, 0], hyp_2d[:, 1], color=color, lw=2.6 if is_cheapest else 1.6, zorder=5)

        burn_2d = proj(entry["r_burn_3d"])
        marker = "*" if is_cheapest else "o"
        ms = 11 if is_cheapest else 5
        ax.scatter(*burn_2d, color=color, s=ms ** 2, marker=marker, zorder=6,
                   edgecolor="black", linewidth=0.4)

    sm = mpl.cm.ScalarMappable(cmap=CMAP, norm=norm)
    sm.set_array([])
    cbar = ax.figure.colorbar(sm, ax=ax, pad=0.02, shrink=0.85)
    cbar.set_label("Heliocentric injection azimuth, psi (deg)")

    ax.set_xlabel("Screen-right (= -v_Earth direction, km)")
    ax.set_ylabel("Screen-up (km)")
    ax.set_title(f"{view_title}\ncolor = psi; star = cheapest (psi={psi_cheapest:.0f} deg)")
    ax.set_xlim(-VIEW_HALF_EXTENT_KM_SWEEP, VIEW_HALF_EXTENT_KM_SWEEP)
    ax.set_ylim(-VIEW_HALF_EXTENT_KM_SWEEP, VIEW_HALF_EXTENT_KM_SWEEP)
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=8)

    # In-axes auto-placed info box (viz/info_box.py) rather than text pushed
    # outside the axes bounds -- the latter repeatedly fought
    # constrained_layout (blank margins, clipped titles) elsewhere in this
    # project; this utility is the proven fix for exactly that.
    dv_min = min(dv_rows, key=lambda r: r[1])
    dv_max = max(dv_rows, key=lambda r: r[1])
    note = (view_note + "\n\n"
            f"dV range across sweep: {dv_min[1]:.2f} km/s (psi={dv_min[0]:.0f}) to "
            f"{dv_max[1]:.2f} km/s (psi={dv_max[0]:.0f})\n"
            "(full per-psi dV values: see departure_dv.py chart / README)")
    info_box.add_info_box(ax, ax.figure, note, mode="on", fontsize=7.5)


def figures(results):
    baseline = results.baseline
    v_earth_hat = baseline.v_earth_eq / np.linalg.norm(baseline.v_earth_eq)
    geom0 = pc.burn_point_geometry(baseline.v_earth_eq, 0.0)
    n_hat = geom0.n_hat
    ecl_normal_eq = frames.ecl_to_eq(np.array([0.0, 0.0, 1.0]))

    # View (b): screen = the true orbital plane itself. Viewed from near
    # Earth's equator (n_hat has zero component along the spin axis) -- the
    # orbit is an exact circle, psi is an exact angle.
    right_b = -v_earth_hat
    up_b = np.cross(n_hat, v_earth_hat)

    # View (a): screen = the ecliptic plane (true bird's-eye view of the
    # solar system, viewing axis = ecliptic normal). Orbit renders as a
    # foreshortened ellipse (minor/major ~35.8%, verified, not "nearly a
    # line" -- the orbit-plane normal sits 111 deg from the ecliptic
    # normal, not close to 90).
    right_a = -v_earth_hat
    up_a = np.cross(ecl_normal_eq, right_a)

    out = []

    def build_a():
        fig, ax = render.new_figure(figsize=(9.5, 8))
        draw(ax, results, right_a, up_a, ecl_normal_eq,
             "View (a): looking straight down the ECLIPTIC normal (bird's-eye view of the solar system)",
             "This screen IS the ecliptic. The orbit is a real ellipse here\n"
             "(minor/major axis = 35.8%, not a near-degenerate line -- the\n"
             "orbit plane sits 111 deg from the ecliptic normal). v_infinity's\n"
             "large (~14.4 deg) out-of-ecliptic tilt is invisible by construction\n"
             "in this view (a radial, Sun-looking-at-Earth view would show it directly).")
        return fig, config.OUTPUT_ROOT / "geometry" / "11a_departure_sweep_ecliptic_view.png"
    out.append(("geometry_sweep_ecliptic", build_a))

    def build_b():
        fig, ax = render.new_figure(figsize=(9.5, 8))
        draw(ax, results, right_b, up_b, n_hat,
             "View (b): face-on to the ORBITAL plane (vantage near Earth's equator, not a pole)",
             "This screen contains the true orbit exactly (a real circle) and\n"
             "v_Earth exactly -- psi is a true angle here. v_infinity still has\n"
             "a small (~7.9 deg) tilt out of even this custom plane.")
        return fig, config.OUTPUT_ROOT / "geometry" / "11b_departure_sweep_orbital_plane_view.png"
    out.append(("geometry_sweep_orbital_plane", build_b))

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
