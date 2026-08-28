"""Heliocentric view of the transfer trajectory with the MCC burn located on
it, answering "is that where the burns are?" -- yes: MCC_EPOCH_OFFSET_DAYS
after TMI, which is still deep in the transfer, not near Earth or Mars.

The position miss this model corrects (tens of thousands of km) is
invisible at heliocentric scale (spacecraft is ~150 million km out by then)
-- hence the zoomed inset around the MCC point.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import frames
import kepler
import mcc
from viz import render, info_box

# A single, deterministic, illustrative 1-sigma execution error (not a random
# Monte Carlo draw) so the chart is reproducible: full 1-sigma dv-magnitude
# error, full 1-sigma pointing error tipped in one fixed perpendicular
# direction.
ILLUSTRATIVE_DMAG_KMS = config.MCC_INJECTION_DV_ERROR_KMS
ILLUSTRATIVE_TIP_RAD = np.radians(config.MCC_INJECTION_POINTING_ERROR_DEG)
ILLUSTRATIVE_TILT_RAD = 0.0


def _track(r0, v0, mu, t_end_s, n=300):
    ts = np.linspace(0, t_end_s, n)
    return np.array([kepler.propagate(r0, v0, t, mu)[0] for t in ts])


def draw(ax, results, psi_deg=None):
    baseline = results.baseline
    if psi_deg is None:
        psi_deg = float(results.psi_deg[np.argmin(results.dv_departure_kms)])

    corr = mcc.single_correction(
        psi_deg, baseline.v_earth_eq, baseline.v_inf_dep_eq, baseline.r_earth_eq,
        baseline.r_mars_eq, baseline.tof_days,
        ILLUSTRATIVE_DMAG_KMS, ILLUSTRATIVE_TIP_RAD, ILLUSTRATIVE_TILT_RAD,
    )

    r_earth_ecl = frames.eq_to_ecl(baseline.r_earth_eq)
    v_earth_ecl = frames.eq_to_ecl(baseline.v_earth_eq)
    r_mars_ecl = frames.eq_to_ecl(baseline.r_mars_eq)
    v_mars_ecl = frames.eq_to_ecl(baseline.v_mars_eq)
    v_transfer_dep_ecl = frames.eq_to_ecl(baseline.v_transfer_dep_eq)

    earth_track = _track(r_earth_ecl, v_earth_ecl, config.GM_SUN, 2 * np.pi * np.sqrt(
        np.linalg.norm(r_earth_ecl) ** 3 / config.GM_SUN))
    mars_track = _track(r_mars_ecl, v_mars_ecl, config.GM_SUN, 2 * np.pi * np.sqrt(
        np.linalg.norm(r_mars_ecl) ** 3 / config.GM_SUN))

    tof_s = baseline.tof_days * 86400.0
    transfer_track = _track(r_earth_ecl, v_transfer_dep_ecl, config.GM_SUN, tof_s, n=400)

    mcc_epoch_s = config.MCC_EPOCH_OFFSET_DAYS * 86400.0
    r_mcc_nom_ecl = frames.eq_to_ecl(corr.r_mcc_nominal)
    r_mcc_act_ecl = frames.eq_to_ecl(corr.r_mcc_actual)

    ax.plot(earth_track[:, 0], earth_track[:, 1], color="#2775B6", lw=1.0, label="Earth orbit")
    ax.plot(mars_track[:, 0], mars_track[:, 1], color="#C1440E", lw=1.0, label="Mars orbit")
    ax.plot(transfer_track[:, 0], transfer_track[:, 1], color="#3FA34D", lw=1.8,
            label="Nominal transfer trajectory")
    ax.scatter([0], [0], color="#F5B700", s=100, marker="*", zorder=5, label="Sun")
    ax.scatter([r_earth_ecl[0]], [r_earth_ecl[1]], color="#2775B6", s=45, zorder=5,
               label="Earth @ departure")
    ax.scatter([r_mars_ecl[0]], [r_mars_ecl[1]], color="#C1440E", s=45, zorder=5,
               label="Mars @ arrival")
    ax.scatter([r_mcc_nom_ecl[0]], [r_mcc_nom_ecl[1]], color="#111111", s=45, marker="D",
               zorder=6, label=f"MCC burn (TMI + {config.MCC_EPOCH_OFFSET_DAYS:.0f} d)")

    ax.set_xlabel("Ecliptic X (km, heliocentric J2000)")
    ax.set_ylabel("Ecliptic Y (km, heliocentric J2000)")
    ax.set_title(f"MCC burn location on the Earth->Mars transfer (psi={psi_deg:.0f} deg)\n"
                 "Not near Earth or Mars: still ~10 days / a few % of the way into the transfer")
    ax.set_aspect("equal")
    ax.legend(loc="upper left", fontsize=8)

    # zoomed inset around the MCC point: nominal vs uncorrected-actual position.
    # Native ax.inset_axes (fractions of the parent axes bbox) rather than the
    # axes_grid1 zoomed_inset_axes helper -- the latter's AxesDivider locator
    # fights with the constrained_layout engine set globally in render.py and
    # silently corrupts the whole figure's layout.
    axins = ax.inset_axes([0.60, 0.06, 0.36, 0.36], zorder=10)
    axins.set_facecolor("white")
    axins.patch.set_alpha(1.0)
    half = corr.position_miss_km * 3.0
    axins.plot([r_mcc_nom_ecl[0]], [r_mcc_nom_ecl[1]], "o", color="#3FA34D", ms=7,
               label="Nominal (on-target)")
    axins.plot([r_mcc_act_ecl[0]], [r_mcc_act_ecl[1]], "x", color="#D64545", ms=9, mew=2,
               label="Uncorrected (TMI error)")
    axins.annotate("", xy=r_mcc_nom_ecl[:2], xytext=r_mcc_act_ecl[:2],
                    arrowprops=dict(arrowstyle="->", color="#111111", lw=1.3))
    cx, cy = r_mcc_nom_ecl[0], r_mcc_nom_ecl[1]
    axins.set_xlim(cx - half, cx + half)
    axins.set_ylim(cy - half, cy + half)
    axins.set_xticks([])
    axins.set_yticks([])
    axins.set_title("zoom @ MCC point", fontsize=7.5)
    for spine in axins.spines.values():
        spine.set_edgecolor("#666666")
    axins.text(0.03, 0.97, f"miss: {corr.position_miss_km:,.0f} km\nMCC ΔV: "
               f"{corr.dv_mcc_kms*1000:.1f} m/s", transform=axins.transAxes,
               fontsize=7, va="top", ha="left",
               bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor="#999999"))
    ax.indicate_inset_zoom(axins, edgecolor="#666666")

    params = {
        "psi": f"{psi_deg:.0f}°",
        "illustrative TMI error": f"{ILLUSTRATIVE_DMAG_KMS*1000:+.1f} m/s mag, "
                                   f"{np.degrees(ILLUSTRATIVE_TIP_RAD):.2f}° pointing (1σ, fixed dir.)",
        "MCC epoch": f"TMI + {config.MCC_EPOCH_OFFSET_DAYS:.0f} d",
        "position miss at MCC": f"{corr.position_miss_km:,.0f} km",
        "MCC ΔV (this sample)": f"{corr.dv_mcc_kms*1000:.1f} m/s",
    }
    text = "\n".join(f"{k}: {v}" for k, v in params.items())
    info_box.add_info_box(ax, ax.figure, text, mode="on")


def figures(results):
    def build():
        fig, ax = render.new_figure(figsize=(9, 9))
        draw(ax, results)
        psi = float(results.psi_deg[np.argmin(results.dv_departure_kms)])
        return fig, config.OUTPUT_ROOT / "mcc" / f"mcc_trajectory_psi_{psi:.0f}.png"
    return [("mcc_trajectory", build)]


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
