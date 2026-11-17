"""Terminal tables, CSV files and the markdown summary."""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import numpy as np
import yaml

from . import analysis
from . import params as params_mod
from .analysis import Study
from .envelope import Envelope
from .joints import SPEC_QUOTED_SECTIONS

# ------------------------------------------------------------------ terminal styling
_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _COLOR else s


def dim(s): return _c("2", s)
def bold(s): return _c("1", s)
def red(s): return _c("31", s)
def yellow(s): return _c("33", s)
def green(s): return _c("32", s)


def sf_str(sf: float, target: float, width: int = 6) -> str:
    if sf is None or not np.isfinite(sf):
        return f"{'-' if sf is None or np.isnan(sf) else 'inf':>{width}}"
    s = f"{sf:>{width}.2f}"
    return red(s) if sf < 1 else yellow(s) if sf < target else green(s)


def fmt(v, nd=1) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    if isinstance(v, (float, np.floating)):
        if not np.isfinite(v):
            return "inf"
        return f"{v:.{nd}f}"
    return str(v)


def table(rows: list[list[str]], header: list[str], align: str) -> str:
    """Fixed-width table; ANSI codes are ignored for width."""
    import re
    strip = lambda s: re.sub(r"\033\[[0-9;]*m", "", s)  # noqa: E731
    w = [max(len(strip(h)), *(len(strip(r[i])) for r in rows)) for i, h in enumerate(header)]
    def line(cells):
        out = []
        for c, wi, a in zip(cells, w, align):
            pad = " " * (wi - len(strip(c)))
            out.append(pad + c if a == "r" else c + pad)
        return "  ".join(out).rstrip()
    return "\n".join([dim(line(header))] + [line(r) for r in rows])


# ------------------------------------------------------------------ console report
def header(p, m, mode: str, case_filter) -> str:
    out = [bold(f"mojave sphinx stand · {mode.upper()} · {p.path.name}")
           + (dim(f" · cases: {', '.join(case_filter)}") if case_filter else "")]
    if p.changes:
        out.append(yellow(f"  {len(p.changes)} parameter(s) differ from defaults:"))
        out += [yellow(f"    {c}") for c in p.changes]
    else:
        out.append(dim("  all parameters at defaults"))
    out.append(dim(f"model   {len(m.members)} members · {len(m.elements)} elements · {m.n_nodes} nodes · "
                   f"{m.n_dof} DOF · {len(m.joints)} joints · {len(m.brackets)} bracket springs · "
                   f"{len(m.bearings)} bearings"))
    out.append(dim(("restr   " if m.ground_mode else "restr   3-2-1: ") + " | ".join(m.restraint_desc)))
    for n in m.notes:
        out.append(yellow(f"note    {n}"))
    return "\n".join(out)


def console(study: Study, env: Envelope, p) -> str:
    si = p.si
    tm, tj = si.checks.SF_target_member, si.checks.SF_target_joint
    s0 = study.solves[0].loads.summary
    out = []
    out.append(dim(f"loads   thrust {s0['thrust_factored_N']:.0f} N (= {si.loads.thrust:.0f} N x DF {si.loads.DF:g}"
                   + (" x 0.5, 2D" if study.model.mode == "2d" else "") + ")"
                   f" · misalign {si.loads.misalign_x:g}/{si.loads.misalign_y:g} · net uplift {s0['Fz_applied_N']:.0f} N"))
    n_runs = len({s.run.label for s in study.solves})
    out.append(dim(f"runs    {n_runs} runs x {len({s.case for s in study.solves})} cases = {len(study.solves)} solves"
                   f" + {len(study.sweep)} sweep · {study.timings['total']:.1f} s"))
    if study.mechanism_cases:
        out.append(yellow(f"mech    run P invalid (node moves > {si.checks.mechanism_disp * 1e3:g} mm) for "
                          f"{', '.join(study.mechanism_cases)} -> run R used"))
    val = [s for s in study.solves + study.sweep if s.valid]
    inv = [s for s in study.solves + study.sweep if not s.valid]
    worst_eq = max(s.eq_residual for s in val)
    worst_r = max(s.restraint_rel for s in val)
    ok = worst_r < si.checks.restraint_tol_rel
    out.append(f"audit   valid solves: equilibrium {worst_eq:.1e} · 3-2-1 reactions {worst_r:.1e} x thrust "
               + (green("ok") if ok else red("FAIL"))
               + (dim(f" · mechanism solves (round-off) {max(s.restraint_rel for s in inv):.0e}") if inv else ""))
    sb = env.sandbag
    if study.bags is not None:
        b = study.bags
        gs = [analysis.ground_stats(study, s, si.ground.mu) for s in val if s.run.name == "R"]
        out.append(f"base    ground springs k_s {si.ground.k_s / 1e6:.0f} MN/m³ · sandbags "
                   f"{bold(f'{len(b.stations)} x {b.kg_each:.0f} kg = {b.total_kg:.0f} kg')} (FS {si.sandbags.FS_tip:g}: {b.gov})")
        out.append(f"ground  contact {100 * min(g['contact'] for g in gs):.0f}-{100 * max(g['contact'] for g in gs):.0f} % of base"
                   f" · peak {max(g['q_peak'] for g in gs) / 1e3:.1f} kN/m · sliding FS ≥ {min(g['slide_FS'] for g in gs):.1f}"
                   f" · lowest base-joint SF {min(g['base_joint_SF'] for g in gs):.2f} (run R)")
    else:
        out.append(f"base    sandbag >= {bold(f'{sb['net_kg']:.1f} kg')} (net uplift {sb['uplift_N']:.0f} N / g)"
                   f" · {sb['uniform_kg']:.0f} kg if spread uniformly (overturning {sb['M_overturn_Nm']:.0f} N·m)")
    lam, lk = env.lam
    out.append(f"frame   buckling λ = {sf_str(lam, tm, 0)}  {dim(lk)}")
    th = env.thrust
    tilt = f"{th['tilt_deg']:.3f}°"
    out.append(f"thrust  |δ| = {np.linalg.norm(th['disp_mm']):.2f} mm {dim(th['disp_solve'])} · tilt "
               + (red(tilt) + f" > {si.checks.tilt_limit:g}°" if th["tilt_flag"] else green(tilt))
               + f" {dim(th['tilt_solve'])}")
    if env.sweep_interior:
        out.append(yellow(f"sweep   {len(env.sweep_interior)} item(s) peak at an interior k_theta "
                          f"(case {study.sweep_case}); included in the envelope"))
    else:
        out.append(dim(f"sweep   k_theta sweep ({study.sweep_case}, bearing "
                       f"{'ON' if study.sweep_bearing else 'OFF'}): every utilisation peaks at an end"))

    n = int(si.output.n_lowest)
    jr = [r for r in env.joints if np.isfinite(r["SF"])][:n]
    out.append("\n" + bold(f"lowest joint SF") + dim(f"  (target {tj:g}; demand includes DF)"))
    out.append(table([[sf_str(r["SF"], tj), r["joint"], f"{r['bracket']}.{r['copy']}", r["type"], r["leg"],
                       r["member"], r["gov_term"].removeprefix("U_"), f"{100 * r[r['gov_term']] / r['U']:.0f}%",
                       fmt(np.hypot(r["Fx_N"], r["Fy_N"]), 0), fmt(r["Fz_N"], 0),
                       fmt(np.linalg.norm([r["Mx_Nm"], r["My_Nm"], r["Mz_Nm"]]), 1),
                       f"{r['gov_run']}/{r['gov_case']}"] for r in jr],
                     ["SF", "joint", "bkt", "type", "leg", "on", "governs", "share", "F_shear", "F_z",
                      "|M|", "run/case"], "rlllllrlrrrl"))
    mr = env.members[:n]
    out.append("\n" + bold("lowest member SF") + dim(f"  (target {tm:g})"))
    out.append(table([[sf_str(r["SF"], tm), r["id"], r["profile"], r["gov_check"], fmt(r["sigma_MPa"], 1),
                       fmt(r["N_N"], 0), fmt(r["My_Nm"], 1), fmt(r["Mz_Nm"], 1), sf_str(r["SF_buckle"], tm),
                       sf_str(r["SF_bc"], tm), f"{r['gov_run']}/{r['gov_case']}"] for r in mr],
                     ["SF", "id", "prof", "governs", "σ MPa", "N", "My", "Mz", "SF_buck", "SF_bc", "run/case"],
                     "rlllrrrrrrl"))
    return "\n".join(out)


# ------------------------------------------------------------------ files
def write_csv(path: Path, rows: list[dict]) -> None:
    keys: list[str] = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, (float, np.floating)) else v) for k, v in r.items()})


def placeholders_md(p) -> list[str]:
    out = []
    for flag in ("placeholder", "unverified", "assumption"):
        for q in p.flagged(flag):
            out.append(f"| `{q.key}` | {p.display(q.key)} | {flag} | {q.help} |")
    return out


def summary_md(study: Study, env: Envelope, p, figures: list[str] | None = None) -> str:
    si, m = p.si, study.model
    tm, tj = si.checks.SF_target_member, si.checks.SF_target_joint
    L = []
    L.append(f"# Mojave Sphinx stand — {m.mode.upper()} safety summary\n")
    L.append(f"params: `{p.path.name}` · {len(study.solves)} solves + {len(study.sweep)} sweep · "
             f"targets: member SF ≥ {tm:g}, joint SF ≥ {tj:g} (DF = {si.loads.DF:g} already in the loads)\n")
    if p.changes:
        L.append("**Parameters changed from defaults**\n")
        L += [f"- `{c.key}`: {params_mod._fmt(c.default)} → **{params_mod._fmt(c.value)}** "
              f"{params_mod._unit_of(c.key)} ({c.source})" for c in p.changes]
        L.append("")
    for n in m.notes:
        L.append(f"> {n}\n")

    sb, th = env.sandbag, env.thrust
    lam, lk = env.lam
    worst_r = max(s.restraint_rel for s in study.solves + study.sweep if s.valid)
    L.append("## Headline\n")
    L.append("| quantity | value | governing |\n|---|---|---|")
    jmin = next((r for r in env.joints if np.isfinite(r["SF"])), None)
    if jmin:
        L.append(f"| lowest joint SF | **{jmin['SF']:.2f}** ({jmin['joint']} {jmin['type']} leg {jmin['leg']} "
                 f"on {jmin['member']}, {jmin['gov_term']}) | {jmin['gov_run']}/{jmin['gov_case']} |")
    mmin = env.members[0]
    L.append(f"| lowest member SF | **{mmin['SF']:.2f}** ({mmin['id']} {mmin['gov_check']}) | "
             f"{mmin['gov_run']}/{mmin['gov_case']} |")
    L.append(f"| frame buckling λ | **{lam:.2f}** ({'pass' if lam >= tm else 'FAIL'} vs {tm:g}) | {lk} |")
    L.append(f"| thrust-point deflection | {np.linalg.norm(th['disp_mm']):.2f} mm "
             f"(x {th['disp_mm'][0]:+.2f}, y {th['disp_mm'][1]:+.2f}, z {th['disp_mm'][2]:+.2f}) | {th['disp_solve']} |")
    L.append(f"| thrust-point tilt | {th['tilt_deg']:.3f}° {'**> ' + format(si.checks.tilt_limit, 'g') + '° flag**' if th['tilt_flag'] else '(ok)'} "
             f"| {th['tilt_solve']} |")
    if study.bags is not None:
        b = study.bags
        L.append(f"| sandbags (FS {si.sandbags.FS_tip:g} on tipping and lift) | **{len(b.stations)} × {b.kg_each:.0f} kg "
                 f"= {b.total_kg:.0f} kg** | {b.gov} |")
    L.append(f"| sandbag mass (net uplift / g, FS 1) | **{sb['net_kg']:.1f} kg** ({sb['uplift_N']:.0f} N) | all cases |")
    if study.bags is None:
      L.append(f"| sandbag mass if spread uniformly on the base | {sb['uniform_kg']:.0f} kg "
             f"(overturning {sb['M_overturn_Nm']:.0f} N·m about the base centroid) | worst case |")
    if study.bags is None:
        L.append(f"| 3-2-1 restraint reactions | {worst_r:.1e} × thrust "
                 f"({'ok' if worst_r < si.checks.restraint_tol_rel else 'FAIL'}) | all valid solves |\n")
    else:
        L.append("")
        L += ground_md(study, p)
    L.append("Displacements are relative to the best-fit rigid motion of the base nodes (i.e. to the ground).\n")
    L.append("**In this folder:** [figures](#figures) (below, and in `figures/`) · `viewer.html` (interactive 3D, "
             "click any bracket for its free-body diagram; download and open locally) · `tables/members.csv`, "
             "`tables/joints.csv`, `tables/ktheta_sweep.csv` · `params_used.yaml` (exact inputs of this run)\n")

    n = int(si.output.n_lowest)
    L.append(f"## Lowest {n} joint SFs\n")
    L.append("SF = 1/U with U = Σ term demand/capacity (linear interaction). *Share* = that term's part of U; "
             "*SF if alone* = the SF if only that term acted.\n")
    L.append("| SF | joint | bracket | type | leg | on | governs | share | SF if alone | run/case |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    from .charts._render import TERM_LABEL
    for r in [r for r in env.joints if np.isfinite(r["SF"])][:n]:
        g = r["gov_term"]
        L.append(f"| {r['SF']:.2f} | {r['joint']} | {r['bracket']}{' copy ' + str(r['copy'] + 1) if r['copy'] else ''} | "
                 f"{r['type']} | {r['leg']} | {r['member']} | {TERM_LABEL.get(g, g)} | {100 * r[g] / r['U']:.0f} % | "
                 f"{1 / r[g]:.2f} | {r['gov_run']}/{r['gov_case']} |")
    L.append("")
    L.append(f"## Lowest {n} member SFs\n")
    L.append("| SF | member | profile | governs | σ (MPa) | N (N) | My (N·m) | Mz (N·m) | SF yield | SF buckle | SF beam-col | run/case |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in env.members[:n]:
        L.append(f"| {r['SF']:.2f} | {r['id']} | {r['profile']} | {r['gov_check']} | {r['sigma_MPa']:.1f} | {r['N_N']:.0f} | "
                 f"{r['My_Nm']:.1f} | {r['Mz_Nm']:.1f} | {r['SF_yield']:.2f} | {fmt(r['SF_buckle'], 2)} | "
                 f"{fmt(r['SF_bc'], 2)} | {r['gov_run']}/{r['gov_case']} |")
    L.append("")

    L.append("## Mechanism checks\n")
    if study.mechanism_cases:
        L.append(f"- **Run P invalid** for cases {', '.join(study.mechanism_cases)}: a node moves more than "
                 f"{si.checks.mechanism_disp * 1e3:g} mm → *mechanism — pinned result invalid; joints carry "
                 "moment*. Run R used for those cases.")
    for e in study.eig_checks:
        L.append(f"- {e['run']}: lowest K eigenvalue / max diag = {e['lowest'][0]:.2e}"
                 + (" **(mechanism)**" if e["mechanism"] else "") + "; softest mode dominated by "
                 + ", ".join(d for d, _ in e["mode_dofs"][:3]))
    L.append("")

    L.append(f"## k_θ sweep ({study.sweep_case}, bearing {'ON' if study.sweep_bearing else 'OFF'})\n")
    L.append("| k_θ / (EI/L) | max node δ (mm) | valid | λ | lowest SF |\n|---|---|---|---|---|")
    from .analysis import item_U
    for s in study.sweep:
        U = item_U(s)
        k_worst = max(U, key=U.get)
        L.append(f"| {s.run.k_theta:g} | {s.max_disp * 1e3:.3g} | {'yes' if s.valid else 'no'} | {s.lam:.2f} | "
                 f"{1 / U[k_worst]:.2f} ({k_worst}) |")
    if env.sweep_interior:
        L.append("\nItems whose utilisation peaks at an interior k_θ (value used in the envelope):\n")
        for it in env.sweep_interior[:20]:
            L.append(f"- {it['item']}: U = {it['U']:.3f} at k = {it['k']:g} (ends {it['U_ends'][0]:.3f} / {it['U_ends'][1]:.3f})")
    else:
        L.append("\nEvery utilisation peaks at an end of the valid sweep range: the P/R bound holds.")
    L.append("")

    caps = study.caps
    L.append("## Joint capacities used\n")
    L.append(f"- friction per bolt μF_i = {caps.F_fric:.0f} N, pull F_i = {caps.F_pull:.0f} N, "
             f"triangle tilt M = F_i·a = {caps.M_tilt:.1f} N·m, twist μF_i·r_f = {caps.M_twist:.2f} N·m "
             f"(r_f = {caps.r_f * 1e3:.2f} mm)")
    secs = caps.sections
    L.append(f"- T-plate sections (computed from the outline): A line b_net = {secs['b_net_A_line'] * 1e3:.1f} mm "
             f"(brief {SPEC_QUOTED_SECTIONS['b_net_A_line'] * 1e3:.1f}); B line {secs['b_net_B_line'] * 1e3:.1f} mm "
             f"(brief {SPEC_QUOTED_SECTIONS['b_net_B_line'] * 1e3:.1f}); B through lower hole "
             f"{secs['b_net_B_lower_hole'] * 1e3:.1f} mm (brief {SPEC_QUOTED_SECTIONS['b_net_B_lower_hole'] * 1e3:.1f}); "
             f"stem neck {secs['b_neck'] * 1e3:.1f} mm (added check)")
    L.append("")
    L.append("## Unverified inputs\n")
    L.append("| parameter | value | flag | meaning |\n|---|---|---|---|")
    L += placeholders_md(p)
    L.append("| plate_other brackets | — | no capacity | forces reported only |")
    if figures:
        from .charts._render import fig_stem
        L.append("\n## Figures\n")
        for name in figures:
            L.append(f"### {FIGURE_TITLES.get(name, name)}\n\n![{name}](figures/{fig_stem(name, figures)}.png)\n")
    return "\n".join(L) + "\n"


FIGURE_TITLES = {
    "stand_sf": "Safety factor by member and joint (front / side / plan)",
    "sf_ranking": "Lowest safety factors",
    "joint_sf_terms": "Joint SF and the share of each failure term",
    "sf_by_case": "SF of the critical items in every load case",
    "thrust_by_case": "Thrust-point tilt and deflection by load case",
    "axial_force": "Member axial force (load path)",
    "peak_stress": "Peak combined stress",
    "deflection": "Deflected shape (worst-tilt case)",
    "buckling_mode": "Frame buckling mode",
    "sandbag_demand": "Sandbag demand on the base",
    "ground_reaction": "Ground reaction on the base (governing case)",
    "ground_by_case": "Ground reaction by load case (plan)",
    "ktheta_sweep": "SF vs joint rotational stiffness",
}


def write_all(study: Study, env: Envelope, p, out: Path, figures: list[str] | None = None) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    files = []
    tab = out / "tables"
    tab.mkdir(exist_ok=True)
    write_csv(tab / "members.csv", env.members)
    write_csv(tab / "joints.csv", env.joints)
    write_csv(tab / "ktheta_sweep.csv", env.sweep_rows)
    files += [tab / "members.csv", tab / "joints.csv", tab / "ktheta_sweep.csv"]
    (out / "summary.md").write_text(summary_md(study, env, p, figures))
    files.append(out / "summary.md")
    used = {}
    for k, v in p.raw.items():
        d = used
        parts = k.split(".")
        for q in parts[:-1]:
            d = d.setdefault(q, {})
        d[parts[-1]] = v
    (out / "params_used.yaml").write_text(
        "# exact parameters of this run\n" + yaml.safe_dump(used, sort_keys=False))
    files.append(out / "params_used.yaml")
    return files


RESULTS_INDEX = """# Results

Generated by `python -m stand run` (3D) and `python -m stand run --2d`. Do not edit by hand;
rerun instead. Start with **[3d/summary.md](3d/summary.md)**: headline numbers, lowest-SF
tables and every figure inline.

| folder | what |
|---|---|
| [`3d/`](3d/summary.md) | full 3D stand, brief's base model: sandbag line load that exactly balances the stand |
| [`3d_ground/`](3d_ground/summary.md) | full 3D stand resting on compression-only gravel springs with discrete sandbags (`run --ground`): real ground reaction, bag sizing, lift-off |
| [`2d/`](2d/summary.md) | 2D side frame (cross-check of the 3D model, in-plane cases only) |
| `variants/` | runs with changed parameters or a subset of cases, e.g. `variants/3d_DF2.5/` (created by `--set` / `--case`) |

Each run folder has the same layout:

| file | what |
|---|---|
| `summary.md` | headline numbers, lowest-SF tables, checks, capacities, unverified inputs, all figures |
| `viewer.html` | interactive 3D model: pick a run/case, click any bracket for its free-body diagram (all 6 force/moment components per leg vs capacity), click joints and members. GitHub cannot render it: download and open in a browser |
| `figures/NN_*.png` | the figures, numbered in reading order |
| `tables/members.csv` | per member: governing check, run/case, forces, stresses, every SF |
| `tables/joints.csv` | per bracket leg / bolt group: 6 leg-frame components, capacities, each utilisation term, SF |
| `tables/ktheta_sweep.csv` | utilisation of every item vs joint rotational stiffness |
| `params_used.yaml` | exact inputs of that run |
"""


def write_index(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text(RESULTS_INDEX)
    return root / "README.md"


def ground_md(study, p) -> list[str]:
    """Ground-contact section: bags, per-case contact, k_s sensitivity."""
    si, b, m = p.si, study.bags, study.model
    g = si.model.g
    L = ["## Ground contact\n",
         f"Base on {len(m.ground)} compression-only contact springs (k_s = {si.ground.k_s / 1e6:.0f} MN/m³, "
         f"compacted gravel; {si.ground.contact_width * 1e3:.1f} mm wide; horizontal = {si.ground.kh_ratio:g} × "
         f"vertical). No assumed base load: the ground pushes up only where the base presses down.\n",
         "**Sandbags** (rigid-body statics, equal mass per station, rounded up to "
         f"{si.sandbags.round_to:g} kg):\n",
         "| station | where | mass |\n|---|---|---|"]
    for (mid, s0, Lb), P in zip(b.stations, b.points(m)):
        L.append(f"| M{mid} @ {s0 * 1e3:.0f} mm, {Lb * 1e3:.0f} mm long | x {P[0] * 1e3:.0f}, y {P[1] * 1e3:.0f} mm "
                 f"| {b.kg_each:.0f} kg |")
    L.append(f"\nSized by {b.gov} (needs {b.kg_needed:.1f} kg each before rounding).\n")
    L.append("| case | FS tipping | FS lift | contact | peak q kN/m | sliding FS (μ "
             f"{si.ground.mu:g}) | lowest base-joint SF |\n|---|---|---|---|---|---|---|")
    for ch in b.checks:
        sols = [s for s in study.solves if s.valid and s.run.name == "R" and s.case == ch["case"]]
        gs = [analysis.ground_stats(study, s, si.ground.mu) for s in sols]
        L.append(f"| {ch['case']} | {ch['FS_tip']:.2f} | {ch['FS_lift']:.2f} | "
                 f"{100 * min(x['contact'] for x in gs):.0f} % | {max(x['q_peak'] for x in gs) / 1e3:.1f} | "
                 f"{_fs(min(x['slide_FS'] for x in gs))} | {min(x['base_joint_SF'] for x in gs):.2f} |")
    if study.ground_sweep:
        L.append("\n**Sensitivity to ground stiffness** (run R, all cases):\n")
        L.append("| k_s MN/m³ | lowest base-joint SF | lowest joint SF | peak q kN/m | least contact |\n|---|---|---|---|---|")
        for ks, sols in study.ground_sweep:
            gs = [analysis.ground_stats(study, s, si.ground.mu) for s in sols]
            jmin = min(r["SF"] for s in sols for r in s.joint_rows if np.isfinite(r["SF"]))
            L.append(f"| {ks / 1e6:.0f} | {min(x['base_joint_SF'] for x in gs):.2f} | {jmin:.2f} | "
                     f"{max(x['q_peak'] for x in gs) / 1e3:.1f} | {100 * min(x['contact'] for x in gs):.0f} % |")
    L.append("")
    return L


def _fs(v: float) -> str:
    return "∞" if not np.isfinite(v) else f"{v:.1f}"
