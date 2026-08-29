"""Heliocentric view of the transfer trajectory with the MCC burn located on
it, answering "is that where the burns are?" -- yes: MCC_EPOCH_OFFSET_DAYS
after TMI, which is still deep in the transfer, not near Earth or Mars.

Reuses trajectory_overview.draw() for the base layer (Earth/Mars orbits,
transfer trajectory, Sun/Earth/Mars markers) instead of duplicating that
track-plotting code, then adds the MCC-specific layer: the burn marker and
a zoomed inset, since the position miss this model corrects (tens of
thousands of km) is invisible at heliocentric scale (spacecraft is ~150
million km out by then).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # for trajectory_overview (sibling module)

import config
import frames
import mcc
import trajectory_overview as traj
from viz import render, info_box

# A single, deterministic, illustrative 1-sigma execution error (not a random
# Monte Carlo draw) so the chart is reproducible: full 1-sigma dv-magnitude
# error, full 1-sigma pointing error tipped in one fixed perpendicular
# direction.
ILLUSTRATIVE_DMAG_KMS = config.MCC_INJECTION_DV_ERROR_KMS
ILLUSTRATIVE_TIP_RAD = np.radians(config.MCC_INJECTION_POINTING_ERROR_DEG)
ILLUSTRATIVE_TILT_RAD = 0.0


def draw(ax, results, psi_deg=None):
    baseline = results.baseline
    if psi_deg is None:
        psi_deg = float(results.psi_deg[np.argmin(results.dv_departure_kms)])

    corr = mcc.single_correction(
        psi_deg, baseline.v_earth_eq, baseline.v_inf_dep_eq, baseline.r_earth_eq,
        baseline.r_mars_eq, baseline.tof_days,
        ILLUSTRATIVE_DMAG_KMS, ILLUSTRATIVE_TIP_RAD, ILLUSTRATIVE_TILT_RAD,
    )
    r_mcc_nom_ecl = frames.eq_to_ecl(corr.r_mcc_nominal)
    r_mcc_act_ecl = frames.eq_to_ecl(corr.r_mcc_actual)

    traj.draw(ax, results, mcc_point_ecl=r_mcc_nom_ecl,
              title_suffix=f"\n(psi={psi_deg:.0f} deg -- MCC point zoomed below: "
                            f"not near Earth or Mars, ~{config.MCC_EPOCH_OFFSET_DAYS:.0f} d "
                            f"/ {100*config.MCC_EPOCH_OFFSET_DAYS/baseline.tof_days:.0f}% into transit)",
              show_info_box=False)

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
