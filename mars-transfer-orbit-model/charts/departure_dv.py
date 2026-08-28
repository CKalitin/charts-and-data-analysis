"""Departure delta-v as a function of heliocentric injection azimuth (psi)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from viz import render, info_box


def _theoretical_minimum_kms(v_inf_kms, r_park_km, mu_earth):
    """delta-v if the parking-orbit plane could freely contain v_infinity
    (tangential periapsis burn) -- the unconstrained lower bound psi cannot
    beat, shown as a reference line."""
    v_after = np.sqrt(v_inf_kms ** 2 + 2 * mu_earth / r_park_km)
    v_circ = np.sqrt(mu_earth / r_park_km)
    return v_after - v_circ


def draw(ax, results):
    psi = results.psi_deg
    dv = results.dv_departure_kms
    baseline = results.baseline

    ax.plot(psi, dv, color="#2775B6", lw=1.8, label="Injection ΔV(ψ)")

    r_park = config.R_EARTH + config.PARKING_ALTITUDE_KM
    v_inf = np.linalg.norm(baseline.v_inf_dep_eq)
    dv_min_theoretical = _theoretical_minimum_kms(v_inf, r_park, config.GM_EARTH)
    ax.axhline(dv_min_theoretical, color="#999999", ls=":", lw=1.3,
               label=f"Unconstrained min (plane ∥ v∞): {dv_min_theoretical:.3f} km/s")

    i_min = int(np.argmin(dv))
    ax.scatter([psi[i_min]], [dv[i_min]], color="#D64545", zorder=5, s=28,
               label=f"ψ minimum: {dv[i_min]:.3f} km/s @ ψ={psi[i_min]:.0f}°")

    ax.set_xlabel("Heliocentric injection azimuth, ψ (deg)")
    ax.set_ylabel("Trans-Mars injection ΔV (km/s)")
    ax.set_title("Departure ΔV vs. heliocentric injection azimuth ψ\n"
                  "(polar parking orbit, plane fixed to contain v_Earth)")
    ax.set_xlim(config.PSI_MIN_DEG, config.PSI_MAX_DEG)
    ax.legend(loc="upper center")

    params = {
        "parking altitude": f"{config.PARKING_ALTITUDE_KM:.0f} km",
        "parking inclination": f"{config.PARKING_INCLINATION_DEG:.0f}° (polar)",
        "departure": baseline.dep_epoch,
        "arrival": baseline.arr_epoch,
        "C3": f"{baseline.C3:.2f} km²/s²",
        "v∞ (departure)": f"{v_inf:.3f} km/s",
    }
    text = "\n".join(f"{k}: {v}" for k, v in params.items())
    info_box.add_info_box(ax, ax.figure, text, mode="on")


def figures(results):
    def build():
        fig, ax = render.new_figure()
        draw(ax, results)
        return fig, config.OUTPUT_ROOT / "departure" / (
            f"departure_dv_vs_psi_{config.PARKING_ALTITUDE_KM:.0f}km_"
            f"{results.baseline.dep_epoch}.png")
    return [("departure_dv_vs_psi", build)]


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
