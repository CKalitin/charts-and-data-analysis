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


def transfer_tracks(baseline):
    """Ecliptic-frame Earth/Mars/transfer tracks for the baseline transfer --
    the shared geometry both trajectory_overview and mcc_trajectory plot, so
    it's computed in one place."""
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
    return r_earth_ecl, r_mars_ecl, earth_track, mars_track, transfer_track


def draw(ax, results, mcc_point_ecl=None, title_suffix="", show_info_box=True):
    """mcc_point_ecl: optional (x, y, z) ecliptic position to mark as the MCC
    burn (see charts/mcc_trajectory.py, which reuses this as its base layer).
    show_info_box=False lets a caller (mcc_trajectory.py) substitute its own,
    more specific info box instead of stacking two."""
    baseline = results.baseline
    r_earth_ecl, r_mars_ecl, earth_track, mars_track, transfer_track = transfer_tracks(baseline)

    ax.plot(earth_track[:, 0], earth_track[:, 1], color="#2775B6", lw=1.2, label="Earth orbit")
    ax.plot(mars_track[:, 0], mars_track[:, 1], color="#C1440E", lw=1.2, label="Mars orbit")
    ax.plot(transfer_track[:, 0], transfer_track[:, 1], color="#3FA34D", lw=2.0,
            label="Transfer trajectory")

    ax.scatter([0], [0], color="#F5B700", s=120, marker="*", zorder=5, label="Sun")
    ax.scatter([r_earth_ecl[0]], [r_earth_ecl[1]], color="#2775B6", s=50, zorder=5,
               label=f"Earth @ departure ({baseline.dep_epoch})")
    ax.scatter([r_mars_ecl[0]], [r_mars_ecl[1]], color="#C1440E", s=50, zorder=5,
               label=f"Mars @ arrival ({baseline.arr_epoch})")
    if mcc_point_ecl is not None:
        ax.scatter([mcc_point_ecl[0]], [mcc_point_ecl[1]], color="#111111", s=70, marker="D",
                   zorder=6, label=f"MCC burn (TMI + {config.MCC_EPOCH_OFFSET_DAYS:.0f} d)")

    ax.set_xlabel("Ecliptic X (km, heliocentric J2000)")
    ax.set_ylabel("Ecliptic Y (km, heliocentric J2000)")
    ax.set_title(f"Earth->Mars transfer trajectory, {baseline.tof_days:.0f}-day time of flight\n"
                 "(ecliptic plan view; psi affects only the departure burn, not this trajectory)"
                 + title_suffix)
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
    if show_info_box:
        text = "\n".join(f"{k}: {v}" for k, v in params.items())
        info_box.add_info_box(ax, ax.figure, text, mode="on")


def nominal_mcc_point_ecl(baseline):
    """Where the MCC burn sits on the NOMINAL trajectory (no injection error)
    -- this only depends on the transfer itself, not on psi, since psi only
    changes the departure burn, not the resulting heliocentric trajectory."""
    r_earth_ecl = frames.eq_to_ecl(baseline.r_earth_eq)
    v_transfer_dep_ecl = frames.eq_to_ecl(baseline.v_transfer_dep_eq)
    mcc_dt_s = config.MCC_EPOCH_OFFSET_DAYS * 86400.0
    r_mcc, _ = kepler.propagate(r_earth_ecl, v_transfer_dep_ecl, mcc_dt_s, config.GM_SUN)
    return r_mcc


def figures(results):
    def build():
        fig, ax = render.new_figure(figsize=(9, 9))
        draw(ax, results, mcc_point_ecl=nominal_mcc_point_ecl(results.baseline))
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
