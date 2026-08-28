"""Mid-course-correction delta-v statistics as a function of psi."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from viz import render, info_box


def draw(ax, results):
    psi = results.psi_mcc_deg
    baseline = results.baseline

    ax.fill_between(psi, results.mcc_mean_kms * 1000, results.mcc_p95_kms * 1000,
                     color="#2775B6", alpha=0.18, label="Mean-P95 band")
    ax.plot(psi, results.mcc_mean_kms * 1000, color="#2775B6", lw=1.8, marker="o",
            ms=3, label="Mean MCC ΔV")
    ax.plot(psi, results.mcc_p95_kms * 1000, color="#D64545", lw=1.2, ls="--",
            marker="o", ms=2.5, label="P95 MCC ΔV")

    ax.set_xlabel("Heliocentric injection azimuth, ψ (deg)")
    ax.set_ylabel("Mid-course-correction ΔV (m/s)")
    ax.set_title("Mid-course-correction ΔV budget vs. ψ\n"
                  "(Monte Carlo over TMI execution error, re-targeted via fresh Lambert solve)")
    ax.set_xlim(config.PSI_MIN_DEG, config.PSI_MAX_DEG)
    ax.legend(loc="upper center")

    params = {
        "TMI execution error (1σ)": f"{config.MCC_INJECTION_DV_ERROR_KMS*1000:.1f} m/s",
        "TMI pointing error (1σ)": f"{config.MCC_INJECTION_POINTING_ERROR_DEG:.2f}°",
        "MCC epoch": f"TMI + {config.MCC_EPOCH_OFFSET_DAYS:.0f} d",
        "Monte Carlo samples": f"{config.MCC_N_SAMPLES} per ψ",
        "departure / arrival": f"{baseline.dep_epoch} / {baseline.arr_epoch}",
    }
    text = "\n".join(f"{k}: {v}" for k, v in params.items())
    info_box.add_info_box(ax, ax.figure, text, mode="on")


def figures(results):
    def build():
        fig, ax = render.new_figure()
        draw(ax, results)
        return fig, config.OUTPUT_ROOT / "mcc" / f"mcc_dv_vs_psi_{results.baseline.dep_epoch}.png"
    return [("mcc_dv_vs_psi", build)]


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
