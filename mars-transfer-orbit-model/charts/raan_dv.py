"""Minimum injection delta-v vs RAAN offset, for both orbital-plane families,
plus a version benchmarked against what a NORMAL (non-polar) mission pays.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import raan_sweep
from viz import render, info_box

EQ_COLOR = "#2775B6"
ECL_COLOR = "#C1440E"
FLOOR_COLOR = "#3FA34D"


def _draw_family_curves(ax, sweep):
    """The two swept families -- shared by both versions of this chart so they
    can never drift apart. Returns each family's (index, dv) minimum."""
    ax.plot(sweep.delta_raan_deg, sweep.dv_equatorial_kms, color=EQ_COLOR, lw=1.8,
            label="Equatorial family (real polar orbits, i=90° to Earth's equator)")
    ax.plot(sweep.delta_raan_deg, sweep.dv_ecliptic_kms, color=ECL_COLOR, lw=1.8,
            label="Ecliptic family (\"solar-system-polar\", plane contains ecliptic normal)")

    i_eq = int(sweep.dv_equatorial_kms.argmin())
    i_ecl = int(sweep.dv_ecliptic_kms.argmin())
    for idx, arr, color in ((i_eq, sweep.dv_equatorial_kms, EQ_COLOR),
                            (i_ecl, sweep.dv_ecliptic_kms, ECL_COLOR)):
        ax.scatter([sweep.delta_raan_deg[idx]], [arr[idx]], color=color, s=50, zorder=5,
                   edgecolor="black", linewidth=0.6)

    ax.axvline(0.0, color="#999999", ls=":", lw=1.2,
               label="dRAAN=0: the plane containing v_Earth exactly")

    ax.set_xlabel("RAAN offset from the v_Earth-containing plane, dRAAN (deg)")
    ax.set_ylabel("Minimum injection ΔV over the whole plane (km/s)")
    ax.set_xlim(-90, 90)
    return i_eq, i_ecl


def _base_params(baseline, sweep, i_eq, i_ecl):
    return {
        "parking altitude": f"{config.PARKING_ALTITUDE_KM:.0f} km",
        "departure / arrival": f"{baseline.dep_epoch} / {baseline.arr_epoch}",
        "C3": f"{baseline.C3:.2f} km²/s²",
        "v∞ (departure)": f"{np.linalg.norm(baseline.v_inf_dep_eq):.3f} km/s",
        "equatorial family min": f"{sweep.dv_equatorial_kms[i_eq]:.3f} km/s @ "
                                 f"dRAAN={sweep.delta_raan_deg[i_eq]:.0f}°",
        "ecliptic family min": f"{sweep.dv_ecliptic_kms[i_ecl]:.3f} km/s @ "
                               f"dRAAN={sweep.delta_raan_deg[i_ecl]:.0f}°",
    }


def _add_info_box(ax, params):
    info_box.add_info_box(ax, ax.figure, "\n".join(f"{k}: {v}" for k, v in params.items()),
                          mode="on")


def draw(ax, results, sweep):
    i_eq, i_ecl = _draw_family_curves(ax, sweep)
    ax.set_title("Minimum Injection ΔV vs RAAN")
    ax.legend(loc="upper center", fontsize=8)
    _add_info_box(ax, _base_params(results.baseline, sweep, i_eq, i_ecl))


def draw_vs_nonpolar(ax, results, sweep, bench):
    """Same sweep, with the non-polar reference orbits a normal mission would use.

    The floor line is drawn once and labelled for what it actually is: not a
    polar result, but the value ANY parking orbit of inclination >= |DLA| can
    reach by choosing its RAAN -- an ordinary launch-site orbit included."""
    baseline = results.baseline
    i_eq, i_ecl = _draw_family_curves(ax, sweep)

    ax.axhline(bench.dv_standard_kms, color=FLOOR_COLOR, lw=1.8, ls="--",
               label=f"Standard i={bench.standard_inc_deg:.1f}° parking orbit, best RAAN: "
                     f"{bench.dv_standard_kms:.3f} km/s (= the floor)")
    dv_max = max(sweep.dv_equatorial_kms.max(), sweep.dv_ecliptic_kms.max())
    ax.set_ylim(bench.dv_standard_kms - 0.25, dv_max + 0.45)
    ax.set_title("Polar vs Non-Polar Injection ΔV")
    ax.legend(loc="upper center", fontsize=7.5)

    params = _base_params(baseline, sweep, i_eq, i_ecl)
    params.update({
        "DLA (v∞ decl. vs equator)": f"{bench.dla_deg:+.2f}°",
        "v∞ out of the ecliptic": f"{bench.vinf_out_of_ecliptic_deg:+.2f}°",
        "floor reachable for any i ≥": f"{abs(bench.dla_deg):.2f}°",
        "polar penalty vs floor": f"+{1000 * (min(sweep.dv_equatorial_kms.min(), sweep.dv_ecliptic_kms.min()) - bench.dv_standard_kms):.0f} m/s",
    })
    _add_info_box(ax, params)


def figures(results):
    dep = results.baseline.dep_epoch
    out = config.OUTPUT_ROOT / "raan"

    def build():
        sweep = raan_sweep.load(results.baseline)
        fig, ax = render.new_figure()
        draw(ax, results, sweep)
        return fig, out / f"raan_dv_{dep}.png"

    def build_vs_nonpolar():
        sweep = raan_sweep.load(results.baseline)
        bench = raan_sweep.load_nonpolar_benchmarks(results.baseline)
        fig, ax = render.new_figure()
        draw_vs_nonpolar(ax, results, sweep, bench)
        return fig, out / f"raan_dv_vs_nonpolar_{dep}.png"

    return [("raan_dv", build), ("raan_dv_vs_nonpolar", build_vs_nonpolar)]


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
