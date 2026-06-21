"""Generate Chief Joseph heatmaps with a $10M/MW dam turbine cost assumption.

The dispatch physics (SLF, spill) are identical to the standard run — only the
cost / LCOE surfaces are recomputed with the higher turbine price.
Battery cost stays at the standard $200k/MWh.

Output: outputs/model/chief_joseph_10m_turbine/
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

import config as cfg
import derived
from model import config as mc
from model.simulate import run_sweep
from model.charts.heatmaps import figures_heatmaps
from viz import render

DAM_COST   = 10_000_000                       # $/MW  ($10M/MW)
DAM_ANNUAL = DAM_COST / mc.DAM_AMORTIZATION_YR
OUT_DIR    = cfg.OUTPUT_DIR / "model" / "chief_joseph_10m_turbine"

CHJ_OPERATING_POINTS = [
    (2300, 0,    17,   13),
    (2100, 1000, 40,    5),
    (1800, 1000, 50,    0),
    (1000, 0,    20,  -50),
]


def main() -> None:
    dam = next((d for d in cfg.ALL_DAMS if d.code == "chj"), None)
    if dam is None:
        print("ERROR: CHJ dam not found in cfg.ALL_DAMS")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading {dam.name}...")
    df = derived.load_dam(dam.csv_path)

    print(f"Sweeping {mc.N_GRID}x{mc.N_GRID} grid...")
    t0 = time.time()
    results = run_sweep(df, dam.nameplate_mw)
    print(f"  Done in {time.time() - t0:.1f}s")

    # Recompute cost / LCOE with $10M/MW turbine — physics results are reused
    mw_vals      = results["mw_vals"]
    mwh_vals     = results["mwh_vals"]
    total_served = results["slf"] * results["total_load_mwh"]  # MWh/yr

    system_cost = (mw_vals[:, np.newaxis]  * DAM_COST
                   + mwh_vals[np.newaxis, :] * mc.BATTERY_COST_PER_MWH)
    annual_cost = (mw_vals[:, np.newaxis]  * DAM_ANNUAL
                   + mwh_vals[np.newaxis, :] * mc.BATTERY_ANNUAL_COST_PER_MWH)
    with np.errstate(divide="ignore", invalid="ignore"):
        lcoe = np.where(total_served > 0, annual_cost / total_served, np.nan)

    results_10m = {**results, "system_cost": system_cost, "lcoe": lcoe}

    plan = figures_heatmaps(
        results_10m, dam,
        operating_points=CHJ_OPERATING_POINTS,
        out_dir_override=OUT_DIR,
        dam_cost_per_mw=DAM_COST,
        filename_suffix="_10m_turbine",
    )

    print(f"Rendering {len(plan)} charts to {OUT_DIR.relative_to(cfg.PROJECT_DIR)}/")
    for name, build in plan:
        fig, path = build()
        if fig is None or path is None:
            continue
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")

    print("Done.")


if __name__ == "__main__":
    main()
