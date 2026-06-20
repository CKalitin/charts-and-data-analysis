"""Orchestrator for the dam + battery economic model sweep.

Usage:
  python run_model.py            # run all dams, generate all charts
  python run_model.py --count    # dry-run: print chart count

Results per dam  → outputs/bpa_dams/<dam>/model/
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as cfg
import derived
from model import config as mc
from model.simulate import run_sweep
from model.charts.heatmaps import figures_heatmaps
from model.charts.month_breakdown import figures_dispatch_profiles
from viz import render


def main() -> None:
    dry_run = "--count" in sys.argv
    t0 = time.time()

    dam_by_code = {d.code: d for d in cfg.ALL_DAMS}
    plan: list = []

    for code in mc.MODEL_DAMS:
        dam = dam_by_code.get(code)
        if dam is None:
            print(f"WARNING: unknown dam code {code!r}")
            continue

        print(f"Loading {dam.name}...")
        df = derived.load_dam(dam.csv_path)
        if df.empty:
            print(f"  SKIP: no data")
            continue

        if not dry_run:
            (cfg.OUTPUT_DIR / "model" / dam.slug).mkdir(parents=True, exist_ok=True)

        print(f"  Sweeping {mc.N_GRID}×{mc.N_GRID} grid ({mc.N_GRID**2:,} runs)...")
        t1 = time.time()
        results = run_sweep(df, dam.nameplate_mw)
        print(f"  Done in {time.time() - t1:.1f}s  "
              f"| SLF range {results['slf'].min():.2%}–{results['slf'].max():.2%}")

        op = [(2100, 2000), (1000, 0)] if dam.code == "chj" else None
        plan += figures_heatmaps(results, dam, operating_points=op)
        extra = [(1000, 0), (2100, 2000)] if dam.code == "chj" else None
        plan += figures_dispatch_profiles(df, dam, extra_abs_combos=extra)

    if dry_run:
        print(f"Would generate {len(plan)} charts.")
        return

    for name, build in plan:
        fig, path = build()
        if fig is None or path is None:
            continue
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")

    print(f"\nDone — {len(plan)} charts in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
