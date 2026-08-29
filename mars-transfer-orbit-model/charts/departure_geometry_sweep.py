"""One chart, many psi values: a sanity-check overlay of the burn point and
post-burn hyperbola for a whole sweep of psi, all against the same fixed
v_Earth/v_infinity/orbit -- so continuity across psi (smoothly moving burn
point, smoothly fanning hyperbolas, delta-v growing away from the optimum)
is visible directly, instead of trusting the departure_dv.py curve alone.
"""
import sys
from pathlib import Path

import matplotlib as mpl
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # for departure_geometry_3d (sibling module)

import config
import geometry3d as geo
import patched_conic as pc
from departure_geometry_3d import ARROW_LEN_KM, EARTH_COLOR, VEC_COLOR, VINF_COLOR
from viz import render

SWEEP_PSI_DEG = np.arange(-90, 91, 15)  # -90, -75, ..., 90 (13 values)
CMAP = mpl.colormaps["plasma"]
VIEW_HALF_EXTENT_KM_SWEEP = 1.9 * config.R_EARTH


def draw(ax, results):
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
    ax.plot(orbit_2d[:, 0], orbit_2d[:, 1], color="#3FA34D", lw=1.4, alpha=0.6,
            zorder=3, label="Parking orbit (psi-independent)")

    v_earth_end = proj(v_earth_hat * ARROW_LEN_KM)
    ax.annotate("", xy=v_earth_end, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=VEC_COLOR, lw=2.5, mutation_scale=18,
                                 zorder=8))
    ax.text(*(v_earth_end * 1.12), f"v_Earth\n{np.linalg.norm(baseline.v_earth_eq):.2f} km/s",
            color="#B38600", fontsize=8, ha="center", zorder=8)

    v_inf_mag = np.linalg.norm(baseline.v_inf_dep_eq)
    v_inf_hat = baseline.v_inf_dep_eq / v_inf_mag
    out_of_plane_deg = np.degrees(np.arcsin(np.clip(np.dot(v_inf_hat, n_hat), -1, 1)))
    v_inf_end = proj(v_inf_hat * ARROW_LEN_KM)
    ax.annotate("", xy=v_inf_end, xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=VINF_COLOR, lw=2.5, mutation_scale=18,
                                 zorder=8))
    ax.text(*(v_inf_end * 1.18), f"v_infinity\n{v_inf_mag:.2f} km/s\n"
            f"({out_of_plane_deg:+.1f} deg out of this plane)",
            color="#6C3483", fontsize=8, ha="center", zorder=8)

    psi_cheapest = float(results.psi_deg[np.argmin(results.dv_departure_kms)])
    norm = mpl.colors.Normalize(vmin=SWEEP_PSI_DEG.min(), vmax=SWEEP_PSI_DEG.max())

    dv_rows = []
    for psi in SWEEP_PSI_DEG:
        color = CMAP(norm(psi))
        geom = pc.burn_point_geometry(baseline.v_earth_eq, float(psi))
        burn = pc.solve_injection_burn(geom, baseline.v_inf_dep_eq)
        dv_rows.append((psi, burn.delta_v_mag))

        nu_burn = np.radians(burn.true_anomaly_burn_deg)
        peri_hat = geo.peri_direction(geom.r_hat, burn.orbit_normal, nu_burn)
        p = config.GM_EARTH / v_inf_mag ** 2 * (burn.eccentricity ** 2 - 1)
        nu_span = np.radians(40.0)
        hyp_pts = geo.conic_points(peri_hat, burn.orbit_normal, burn.eccentricity, p,
                                    nu_burn, nu_burn + nu_span, n=60)
        hyp_2d = proj(hyp_pts)
        lw = 2.6 if abs(psi - psi_cheapest) < 1e-6 else 1.6
        ax.plot(hyp_2d[:, 0], hyp_2d[:, 1], color=color, lw=lw, zorder=5)

        burn_2d = proj(geom.r_burn)
        marker = "*" if abs(psi - psi_cheapest) < 1e-6 else "o"
        ms = 11 if abs(psi - psi_cheapest) < 1e-6 else 5
        ax.scatter(*burn_2d, color=color, s=ms ** 2, marker=marker, zorder=6,
                   edgecolor="black", linewidth=0.4)

    sm = mpl.cm.ScalarMappable(cmap=CMAP, norm=norm)
    sm.set_array([])
    cbar = ax.figure.colorbar(sm, ax=ax, pad=0.02, shrink=0.85)
    cbar.set_label("Heliocentric injection azimuth, psi (deg)")

    ax.set_xlabel("In-plane, opposite v_Earth (km)")
    ax.set_ylabel("In-plane, perpendicular to v_Earth (km)")
    ax.set_title("Departure burn sweep across psi (face-on to the orbital plane)\n"
                 f"color = psi; star = cheapest (psi={psi_cheapest:.0f} deg)")
    ax.set_xlim(-VIEW_HALF_EXTENT_KM_SWEEP, VIEW_HALF_EXTENT_KM_SWEEP)
    ax.set_ylim(-VIEW_HALF_EXTENT_KM_SWEEP, VIEW_HALF_EXTENT_KM_SWEEP)
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=8)

    table_lines = ["psi(deg)  dV(km/s)"] + [f"{p:6.0f}    {d:.3f}" for p, d in dv_rows]
    ax.text(1.30, 0.98, "\n".join(table_lines), transform=ax.transAxes, fontsize=7,
            va="top", ha="left", family="monospace",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="#999999"))


def figures(results):
    def build():
        fig, ax = render.new_figure(figsize=(10.5, 8))
        draw(ax, results)
        return fig, config.OUTPUT_ROOT / "geometry" / "11_departure_sweep_overlay.png"
    return [("geometry_sweep_overlay", build)]


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
