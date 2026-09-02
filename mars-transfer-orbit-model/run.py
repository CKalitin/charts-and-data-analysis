"""Thin orchestrator: load derived results once, render every chart family."""
import argparse
import time

import config
import derived
from charts import (inclination, orbit_geometry, parking_inclination, raan_dv,
                    trajectory_overview)
from viz import render

CHART_MODULES = [trajectory_overview, raan_dv, parking_inclination, orbit_geometry,
                 inclination]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", action="store_true", help="dry-run: print planned chart count")
    parser.add_argument("--force", action="store_true", help="recompute derived results (ignore cache)")
    args = parser.parse_args()

    results = derived.load(force=args.force)
    plan = []
    for mod in CHART_MODULES:
        plan.extend(mod.figures(results))

    if args.count:
        print(f"{len(plan)} charts planned")
        return

    t0 = time.time()
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(config.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
