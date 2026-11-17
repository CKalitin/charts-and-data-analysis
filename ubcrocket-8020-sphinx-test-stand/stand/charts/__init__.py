"""Chart families. Each module: figures(study, env, p) -> [(name, build)], runnable alone:

    python -m stand.charts.ranking [results_dir]     # re-render one family from the cache
    python -m stand plots [--2d]                     # re-render every family from the cache

Families are imported lazily so `python -m stand.charts.<family>` runs cleanly.
"""
from __future__ import annotations

import importlib
import time
from pathlib import Path

FAMILIES = ["stand_sf", "ranking", "joint_terms", "cases", "forces", "deflection", "base_load", "sweep"]


def plan(study, env, p):
    out = []
    for name in FAMILIES:
        out += importlib.import_module(f"{__name__}.{name}").figures(study, env, p)
    return out


def render_all(study, env, p, out: Path, log=print) -> list[Path]:
    from . import _render as R
    files = []
    t0 = time.time()
    for name, build in plan(study, env, p):
        files += R.save_fig(build(), out / f"{name}{R.suffix(p)}")
    log(f"{len(files) // 2} figures in {time.time() - t0:.1f} s")
    return files
