"""Ecliptic plan-view (top-down) of the heliocentric transfer trajectory."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import frames
import kepler
from viz import render, info_box


def _orbit_track(r0, v0, mu, n_points=300):
    """Sample one full osculating period starting from (r0, v0)."""
    period = 2 * np.pi * np.sqrt((1 / (2 / np.linalg.norm(r0) - np.linalg.norm(v0) ** 2 / mu)) ** 3 / mu)
    ts = np.linspace(0, period, n_points)
    pts = np.array([kepler.propagate(r0, v0, t, mu)[0] for t in ts])
    return pts


def draw(ax, results):
    baseline = results.baseline

    r_earth_ecl = frames.eq_to_ecl(baseline.r_earth_eq)
    v_earth_ecl = frames.eq_to_ecl(baseline.v_earth_eq)
    r_mars_ecl = frames.eq_to_ecl(baseline.r_mars_eq)
    v_mars_ecl = frames.eq_to_ecl(baseline.v_mars_eq)
    v_transfer_dep_ecl = frames.eq_to_ecl(baseline.v_transfer_dep_eq)

    earth_track = _orbit_track(r_earth_ecl, v_earth_ecl, config.GM_SUN)
    mars_track = _orbit_track(r_mars_ecl, v_mars_ecl, config.GM_SUN)

    tof_s = baseline.tof_days * 86400.0
    ts = np.linspace(0, tof_s, 300)
    transfer_track = np.array([
        kepler.propagate(r_earth_ecl, v_transfer_dep_ecl, t, config.GM_SUN)[0] for t in ts
    ])

    ax.plot(earth_track[:, 0], earth_track[:, 1], color="#2775B6", lw=1.2, label="Earth orbit")
    ax.plot(mars_track[:, 0], mars_track[:, 1], color="#C1440E", lw=1.2, label="Mars orbit")
    ax.plot(transfer_track[:, 0], transfer_track[:, 1], color="#3FA34D", lw=2.0,
            label="Transfer trajectory")

    ax.scatter([0], [0], color="#F5B700", s=120, marker="*", zorder=5, label="Sun")
    ax.scatter([r_earth_ecl[0]], [r_earth_ecl[1]], color="#2775B6", s=50, zorder=5,
               label=f"Earth @ departure ({baseline.dep_epoch})")
    ax.scatter([r_mars_ecl[0]], [r_mars_ecl[1]], color="#C1440E", s=50, zorder=5,
               label=f"Mars @ arrival ({baseline.arr_epoch})")

    ax.set_xlabel("Ecliptic X (km, heliocentric J2000)")
    ax.set_ylabel("Ecliptic Y (km, heliocentric J2000)")
    ax.set_title(f"Earth->Mars transfer trajectory, {baseline.tof_days:.0f}-day time of flight\n"
                 "(ecliptic plan view; psi affects only the departure burn, not this trajectory)")
    ax.set_aspect("equal")
    ax.legend(loc="upper left", fontsize=8)

    params = {
        "C3": f"{baseline.C3:.2f} km²/s²",
        "departure v∞": f"{np.linalg.norm(baseline.v_inf_dep_eq):.3f} km/s",
        "arrival v∞": f"{np.linalg.norm(baseline.v_inf_arr_eq):.3f} km/s",
        "flyby periapsis alt": f"{config.FLYBY_PERIAPSIS_ALT_KM:.0f} km",
        "flyby turn angle": f"{results.flyby.turn_angle_deg:.1f}°",
        "flyby periapsis v": f"{results.flyby.periapsis_velocity_kms:.3f} km/s",
    }
    text = "\n".join(f"{k}: {v}" for k, v in params.items())
    info_box.add_info_box(ax, ax.figure, text, mode="on")


def figures(results):
    def build():
        fig, ax = render.new_figure(figsize=(9, 9))
        draw(ax, results)
        return fig, config.OUTPUT_ROOT / "trajectory" / f"transfer_overview_{results.baseline.dep_epoch}.png"
    return [("trajectory_overview", build)]


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
