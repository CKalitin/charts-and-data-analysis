"""Chart families. Each module: figures(study, env, p) -> [(name, build)], runnable alone:

    python -m stand.charts.ranking [results/3d]     # re-render one family from the cache
    python -m stand plots [--2d]                     # re-render every family from the cache

Families are imported lazily so `python -m stand.charts.<family>` runs cleanly.
"""
from __future__ import annotations

import importlib
import time
from pathlib import Path

FAMILIES = ["layout", "stand_sf", "ranking", "joint_terms", "cases", "forces", "deflection", "base_load", "ground", "sweep"]


def plan(study, env, p):
    out = []
    for name in FAMILIES:
        out += importlib.import_module(f"{__name__}.{name}").figures(study, env, p)
    return out


def render_all(study, env, p, out: Path, log=print) -> list[Path]:
    from . import _render as R
    files = []
    t0 = time.time()
    if out.is_dir():                     # no stale figures from renamed/removed charts
        for f in out.glob("*.png"):
            f.unlink()
        for f in out.glob("*.svg"):
            f.unlink()
    items = plan(study, env, p)
    present = [n for n, _ in items]
    for name, build in items:
        files += R.save_fig(build(), out / R.fig_stem(name, present), p.si.output.svg)
    log(f"{len(items)} figures in {time.time() - t0:.1f} s")
    return files


def names(study, env, p) -> list[str]:
    return [n for n, _ in plan(study, env, p)]
