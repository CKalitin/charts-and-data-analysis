"""CLI.

  python -m stand run [--2d] [--case NAME ...] [--set key=value ...] [--params FILE] [--no-plots]
  python -m stand plots [--2d] [--set ...]   # re-render figures from the cached run (no solve)
  python -m stand test [pytest args]
  python -m stand params [--changed] [--reset]
  python -m stand model [--2d]            # how every joint was modelled (nodes, offsets, legs)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from . import params as params_mod
from .params import PROJECT_DIR


def _load(args):
    return params_mod.load(args.params, params_mod.parse_set(args.set))


def _build(p, mode):
    from . import geometry, model
    g = geometry.load(p.si.inputs.geometry, p.si.inputs.brackets)
    try:
        return model.build(g, p, mode)
    except model.ModelError as e:
        sys.exit(f"model error: {e}")


def cmd_run(args) -> None:
    from . import analysis, envelope, report
    p = _load(args)
    mode = "2d" if args.two_d else "3d"
    m = _build(p, mode)
    print(report.header(p, m, mode, args.case))
    unknown = [c for c in (args.case or []) if c not in p.si.loads.cases]
    if unknown:
        from .model import parse_case
        for c in unknown:
            parse_case(c)            # validates the name
    study = analysis.run_study(m, p, args.case, log=lambda s: print(report.yellow(f"note    {s}")))
    env = envelope.build(study, p)
    print(report.console(study, env, p))
    out = _out_dir(args, p, mode)
    files = report.write_all(study, env, p, out)
    from .charts import _render
    _render.save_cache(study, env, p, out)
    if not args.no_plots:
        files += _plots(study, env, p, out)
    print("\n" + report.dim("wrote   " + "\n        ".join(_rel(f) for f in files)))


def _rel(f: Path) -> str:
    return str(f.relative_to(PROJECT_DIR)) if f.is_relative_to(PROJECT_DIR) else str(f)


def _out_dir(args, p, mode) -> Path:
    """results/[2d/][set_<changes>/][case_<cases>/] — a variant never overwrites the defaults."""
    if getattr(args, "out", None):
        return Path(args.out)
    from .charts._render import suffix
    out = PROJECT_DIR / p.si.output.dir
    if mode == "2d":
        out = out / "2d"
    if p.changes:
        out = out / ("set" + suffix(p))
    if getattr(args, "case", None):
        out = out / ("case_" + "_".join(args.case).replace("+", "p").replace("-", "m"))
    return out


def _plots(study, env, p, out: Path) -> list[Path]:
    from . import charts, report, viz
    files = [viz.write_html(study, env, p, out / "stand.html")]
    files += charts.render_all(study, env, p, out / "figures", log=lambda s: print(report.dim(f"plots   {s}")))
    return files


def cmd_plots(args) -> None:
    """Re-render stand.html + figures from the cached study of a previous run (no solve)."""
    from . import report
    from .charts import _render
    p = _load(args)
    out = _out_dir(args, p, "2d" if args.two_d else "3d")
    study, env, p_run = _render.load_cache(out)
    files = _plots(study, env, p_run, out)
    print(report.dim("wrote   " + "\n        ".join(_rel(f) for f in files)))


def cmd_test(args) -> None:
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", *args.pytest_args], cwd=PROJECT_DIR))


def cmd_params(args) -> None:
    from . import report
    if args.reset:
        path = Path(args.params) if args.params else params_mod.DEFAULT_PARAMS_PATH
        if path.exists() and not args.yes:
            sys.exit(f"{path} exists; pass --reset --yes to overwrite it with the defaults")
        params_mod.write_defaults(path)
        print(f"wrote defaults to {path}")
        return
    p = _load(args)
    changed = {c.key: c for c in p.changes}
    group = None
    for q in params_mod.SCHEMA:
        if args.changed and q.key not in changed:
            continue
        g = q.key.split(".")[0]
        if g != group:
            print(report.bold(g))
            group = g
        val = p.display(q.key)
        flag = f"[{q.flag}]" if q.flag else ""
        line = f"  {q.key.split('.', 1)[1]:28s} {val:30s} {flag:13s} {report.dim(q.help)}"
        if q.key in changed:
            line = report.yellow(f"* {q.key.split('.', 1)[1]:26s} {val:30s} {flag:13s} "
                                 f"(default {params_mod._fmt(q.default)}, {changed[q.key].source})")
        print(line)
    if not p.changes:
        print(report.dim("\nall parameters at defaults"))


def cmd_model(args) -> None:
    import numpy as np
    from . import joints, report
    p = _load(args)
    mode = "2d" if args.two_d else "3d"
    m = _build(p, mode)
    print(report.header(p, m, mode, None))
    joints.prepare(m, p)
    rows = []
    copies = {}
    for br in m.brackets:
        copies[(br.joint, br.index)] = copies.get((br.joint, br.index), 0) + 1
    for br in m.brackets:
        if br.copy:
            continue
        da = np.linalg.norm(br.X - m.x[br.na]) * 1e3
        db = np.linalg.norm(br.X - m.x[br.nb]) * 1e3
        rows.append([br.joint, str(br.index), br.type, f"M{br.a}", f"M{br.b}", f"x{copies[(br.joint, br.index)]}",
                     f"{da:.1f}", f"{db:.1f}", " | ".join(o.desc for o in br.legs), br.note])
    print("\n" + report.bold("brackets") + report.dim("  (arm = rigid link from member centreline node to the joint point)"))
    print(report.table(rows, ["joint", "#", "type", "a", "b", "n", "arm_a mm", "arm_b mm", "corner options", "note"],
                       "llllllrrll"))
    rows = [[b.joint, f"M{b.end_of}", f"M{b.bears_on}", "".join(f"{v:+.2f}" for v in b.n),
             f"{np.linalg.norm(m.x[b.n_end] - m.x[b.n_on]) * 1e3:.1f}"] for b in m.bearings]
    print("\n" + report.bold("bearing (compression only)"))
    print(report.table(rows, ["joint", "end of", "bears on", "axis n", "gap to node mm"], "llllr"))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m stand", description="Mojave Sphinx test stand frame + joint SF model")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--params", help="parameter file (default: params.yaml)")
        sp.add_argument("--set", action="append", metavar="KEY=VALUE",
                        help="override a parameter for this run, e.g. --set loads.DF=2.5 (repeatable)")

    r = sub.add_parser("run", help="solve every run/case and write results/")
    common(r)
    r.add_argument("--2d", dest="two_d", action="store_true", help="front side frame only (x-z plane)")
    r.add_argument("--case", action="append", help="only this load case (repeatable), e.g. --case +x")
    r.add_argument("--out", help="output directory (default results/, results/2d/)")
    r.add_argument("--no-plots", action="store_true", help="skip stand.html and figures/")
    r.set_defaults(fn=cmd_run)

    pl = sub.add_parser("plots", help="re-render html + figures from the last run's cache (no solve)")
    common(pl)
    pl.add_argument("--2d", dest="two_d", action="store_true")
    pl.add_argument("--case", action="append")
    pl.add_argument("--out")
    pl.set_defaults(fn=cmd_plots)

    t = sub.add_parser("test", help="run the validation suite (pytest)")
    t.add_argument("pytest_args", nargs=argparse.REMAINDER)
    t.set_defaults(fn=cmd_test)

    q = sub.add_parser("params", help="list parameters (changed ones highlighted)")
    common(q)
    q.add_argument("--changed", action="store_true", help="only parameters that differ from defaults")
    q.add_argument("--reset", action="store_true", help="rewrite params.yaml from the defaults")
    q.add_argument("--yes", action="store_true", help="confirm --reset overwrite")
    q.set_defaults(fn=cmd_params)

    mm = sub.add_parser("model", help="print how every joint/bracket/bearing was modelled")
    common(mm)
    mm.add_argument("--2d", dest="two_d", action="store_true")
    mm.set_defaults(fn=cmd_model)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
