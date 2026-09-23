"""Build every derived table and chart: python run.py  (or --count for a dry run)."""

from __future__ import annotations

import argparse
import time

import config as cfg
import derived
from charts import learning_curve, timeseries
from viz import render


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", action="store_true", help="print the planned chart count and exit")
    args = ap.parse_args()

    t0 = time.time()
    pts = derived.price_points()
    fits = derived.fits(pts)
    annual = derived.annual_table()
    plan = [*learning_curve.figures(pts, fits), *timeseries.figures(pts, annual)]
    if args.count:
        print(f"{len(plan)} charts planned")
        return

    cfg.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    pts.round(4).to_csv(cfg.OUTPUT_ROOT / "price_points.csv", index=False)
    annual.round(1).to_csv(cfg.DERIVED_CSV, index=False)
    table = derived.fit_table(fits)
    table.to_csv(cfg.FIT_SUMMARY_CSV, index=False)
    print(table.to_string(index=False))

    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
