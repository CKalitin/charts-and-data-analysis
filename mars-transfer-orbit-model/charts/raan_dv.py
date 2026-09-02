"""Minimum injection delta-v vs RAAN offset, for both orbital-plane families,
on one shared axis."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import raan_sweep
from viz import render, info_box


def draw(ax, results, sweep):
    baseline = results.baseline

    ax.plot(sweep.delta_raan_deg, sweep.dv_equatorial_kms, color="#2775B6", lw=1.8,
            label="Equatorial family (real polar orbits, i=90° to Earth's equator)")
    ax.plot(sweep.delta_raan_deg, sweep.dv_ecliptic_kms, color="#C1440E", lw=1.8,
            label="Ecliptic family (\"solar-system-polar\", plane contains ecliptic normal)")

    i_eq = int(sweep.dv_equatorial_kms.argmin())
    i_ecl = int(sweep.dv_ecliptic_kms.argmin())
    ax.scatter([sweep.delta_raan_deg[i_eq]], [sweep.dv_equatorial_kms[i_eq]], color="#2775B6",
               s=50, zorder=5, edgecolor="black", linewidth=0.6)
    ax.scatter([sweep.delta_raan_deg[i_ecl]], [sweep.dv_ecliptic_kms[i_ecl]], color="#C1440E",
               s=50, zorder=5, edgecolor="black", linewidth=0.6)

    ax.axvline(0.0, color="#999999", ls=":", lw=1.2,
               label="dRAAN=0: the plane containing v_Earth exactly")

    ax.set_xlabel("RAAN offset from the v_Earth-containing plane, dRAAN (deg)")
    ax.set_ylabel("Minimum injection ΔV over the whole plane (km/s)")
    ax.set_title("Minimum departure ΔV vs RAAN, both orbital-plane families\n"
                 "(each point: best achievable burn anywhere in that one plane)")
    ax.set_xlim(-90, 90)
    ax.legend(loc="upper center", fontsize=8)

    params = {
        "parking altitude": f"{config.PARKING_ALTITUDE_KM:.0f} km",
        "departure / arrival": f"{baseline.dep_epoch} / {baseline.arr_epoch}",
        "C3": f"{baseline.C3:.2f} km²/s²",
        "v∞ (departure)": f"{__import__('numpy').linalg.norm(baseline.v_inf_dep_eq):.3f} km/s",
        "equatorial family min": f"{sweep.dv_equatorial_kms[i_eq]:.3f} km/s @ "
                                   f"dRAAN={sweep.delta_raan_deg[i_eq]:.0f}°",
        "ecliptic family min": f"{sweep.dv_ecliptic_kms[i_ecl]:.3f} km/s @ "
                                 f"dRAAN={sweep.delta_raan_deg[i_ecl]:.0f}°",
    }
    text = "\n".join(f"{k}: {v}" for k, v in params.items())
    info_box.add_info_box(ax, ax.figure, text, mode="on")


def figures(results):
    def build():
        sweep = raan_sweep.load(results.baseline)
        fig, ax = render.new_figure()
        draw(ax, results, sweep)
        return fig, config.OUTPUT_ROOT / "raan" / f"raan_dv_{results.baseline.dep_epoch}.png"
    return [("raan_dv", build)]


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
