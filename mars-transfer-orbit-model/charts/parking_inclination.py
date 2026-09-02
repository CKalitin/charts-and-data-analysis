"""Injection delta-v as a function of parking-orbit inclination.

Each inclination is scored by its OWN best case: the RAAN that comes closest to
putting the departure v_infinity in the plane, and the cheapest burn point within
it. So the curve is "what does this inclination cost you if you fly it well",
not "what does an arbitrary orbit at this inclination cost".

The shape is the whole story. Above |DLA| -- the declination of v_infinity
relative to Earth's equator -- some RAAN puts v_infinity exactly in the plane,
and every such plane reaches the identical single-impulse floor, so the curve is
flat. Below |DLA| no RAAN can, the residual out-of-plane angle grows as
|DLA| - i, and a real plane-change penalty appears.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import raan_sweep
from viz import render, info_box

CURVE_COLOR = "#2775B6"
FLOOR_COLOR = "#3FA34D"
KNEE_COLOR = "#D64545"
MARKER_COLOR = "#111111"


def draw(ax, results, inc_sweep):
    baseline = results.baseline
    dla = abs(inc_sweep.dla_deg)
    floor = float(inc_sweep.dv_kms.min())

    ax.plot(inc_sweep.inclination_deg, inc_sweep.dv_kms, color=CURVE_COLOR, lw=2.0,
            label="Best achievable ΔV at this inclination (over RAAN and burn point)")
    ax.axhline(floor, color=FLOOR_COLOR, lw=1.6, ls="--",
               label=f"Floor (plane contains v∞): {floor:.3f} km/s")
    ax.axvline(dla, color=KNEE_COLOR, lw=1.4, ls=":",
               label=f"|DLA| = {dla:.2f}°: above this, some RAAN puts v∞ in the plane")

    # The two inclinations the project actually cares about.
    for inc, name in ((config.STANDARD_PARKING_INCLINATION_DEG, "standard 28.5° parking orbit"),
                      (config.PARKING_INCLINATION_DEG, "polar (this project)")):
        dv = float(np.interp(inc, inc_sweep.inclination_deg, inc_sweep.dv_kms))
        ax.scatter([inc], [dv], color=MARKER_COLOR, s=45, zorder=6)
        # A point sitting on the axis edge needs its label pulled inward, or half the
        # text renders outside the axes (the polar point is exactly at x=90).
        ha, dx = ("right", -6) if inc > 80 else ("center", 0)
        ax.annotate(f"{name}\n{dv:.3f} km/s", xy=(inc, dv), xytext=(dx, 26),
                    textcoords="offset points", fontsize=8, ha=ha, va="bottom",
                    arrowprops=dict(arrowstyle="-", color=MARKER_COLOR, lw=0.6))

    dv0 = float(inc_sweep.dv_kms[0])
    ax.annotate(f"equatorial: {dv0:.3f} km/s\n(+{1000 * (dv0 - floor):.0f} m/s over the floor)",
                xy=(0.0, dv0), xytext=(14, -4), textcoords="offset points",
                fontsize=8, ha="left", va="top", color=CURVE_COLOR)

    ax.set_xlabel("Parking orbit inclination to Earth's equator (deg)")
    ax.set_ylabel("Minimum injection ΔV (km/s)")
    ax.set_title("Minimum Injection ΔV vs Parking Orbit Inclination")
    ax.set_xlim(0, 90)
    ax.set_xticks(np.arange(0, 91, 10))
    ax.set_ylim(floor - 0.25, dv0 + 0.45)
    ax.legend(loc="upper right", fontsize=8)

    params = {
        "parking altitude": f"{config.PARKING_ALTITUDE_KM:.0f} km",
        "departure / arrival": f"{baseline.dep_epoch} / {baseline.arr_epoch}",
        "C3": f"{baseline.C3:.2f} km²/s²",
        "v∞ (departure)": f"{np.linalg.norm(baseline.v_inf_dep_eq):.3f} km/s",
        "DLA (v∞ decl. vs equator)": f"{inc_sweep.dla_deg:+.2f}°",
        "floor": f"{floor:.3f} km/s, reached for any i ≥ {dla:.2f}°",
        "equatorial penalty": f"+{1000 * (dv0 - floor):.0f} m/s",
        "inclination step": f"{config.INCLINATION_SWEEP_STEP_DEG:.1f}°",
    }
    info_box.add_info_box(ax, ax.figure, "\n".join(f"{k}: {v}" for k, v in params.items()),
                          mode="on")


def figures(results):
    def build():
        inc_sweep = raan_sweep.load_inclination_sweep(results.baseline)
        fig, ax = render.new_figure()
        draw(ax, results, inc_sweep)
        return fig, (config.OUTPUT_ROOT / "raan"
                     / f"injection_dv_vs_inclination_{results.baseline.dep_epoch}.png")
    return [("injection_dv_vs_inclination", build)]


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
