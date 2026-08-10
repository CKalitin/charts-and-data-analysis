"""Orchestrator -- pull data (cached), build the panel, render every chart.

  python run.py            # generate all charts
  python run.py --count    # dry-run: print the chart count
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as cfg
import data_load
import model.derived as derived
from charts.ranking import figures_decoupling_ranking, figures_overlay
from charts.timeseries import figures_city_panels
from viz import render


def main() -> None:
    dry_run = "--count" in sys.argv
    t0 = time.time()

    panel = data_load.build_panel()
    indexed = derived.add_indices(panel)
    ranking = derived.latest_year_ranking(indexed)

    print(ranking[["city", "year", "house_price_growth_pct", "wage_growth_pct",
                   "decoupling_gap_pp"]].to_string(index=False))

    plan = [
        *figures_city_panels(indexed),
        *figures_overlay(indexed),
        *figures_decoupling_ranking(ranking),
    ]

    if dry_run:
        print(f"\nWould generate {len(plan)} charts.")
        return

    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")

    print(f"\nDone -- {len(plan)} charts in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
