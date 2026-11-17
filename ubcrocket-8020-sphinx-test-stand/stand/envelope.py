"""Design envelope: worst value of every item over all valid solves (+ the k_theta sweep)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .analysis import Solve, Study, item_U

PLACEHOLDER_BY_TYPE = {
    "triangle": "triangle.tilt_arm",
    "plate_t5": "plate.thickness, plate.fy",
    "plate_other": "no capacity model (forces only)",
}


def _run_group(s: Solve) -> str:
    return s.run.name if s.run.name in ("P", "R") else "sweep"


@dataclass
class Envelope:
    members: list[dict]
    joints: list[dict]                   # one row per bracket leg / group
    joint_min: dict[str, dict]           # joint id -> governing row
    valid: list[Solve]
    lam: tuple[float, str]
    thrust: dict
    sandbag: dict
    sweep_rows: list[dict]               # item -> U per k
    sweep_interior: list[dict]
    notes: list[str] = field(default_factory=list)


def build(study: Study, p) -> Envelope:
    valid = [s for s in study.solves if s.valid] + [s for s in study.sweep if s.valid]
    m = study.model

    # ---------------------------------------------------------------- members
    mem_rows = []
    for mid in sorted(m.members):
        mem = m.members[mid]
        best = {}
        per_run = {"P": np.inf, "R": np.inf}
        for s in valid:
            r = s.member_rows[mid]
            for chk in ("SF_yield", "SF_buckle", "SF_bc"):
                if chk not in best or r[chk] < best[chk][0]:
                    best[chk] = (r[chk], s, r)
            g = _run_group(s)
            if g in per_run:
                per_run[g] = min(per_run[g], r["SF"])
        y_sf, y_s, y_r = best["SF_yield"]
        b_sf, b_s, b_r = best["SF_buckle"]
        c_sf, c_s, c_r = best["SF_bc"]
        sfs = {"yield": y_sf, "buckle": b_sf, "beam-col": c_sf}
        gov = min(sfs, key=sfs.get)
        gov_s = {"yield": y_s, "buckle": b_s, "beam-col": c_s}[gov]
        mem_rows.append({
            "id": f"M{mid}", "profile": mem.profile, "L_mm": mem.L * 1e3,
            "SF": sfs[gov], "gov_check": gov, "gov_run": gov_s.run.label, "gov_case": gov_s.case,
            "SF_yield": y_sf, "sigma_MPa": y_r["sigma"] / 1e6, "N_N": y_r["N"], "My_Nm": y_r["My"],
            "Mz_Nm": y_r["Mz"], "at_mm": y_r["x_mm"], "yield_solve": y_s.key,
            "SF_buckle": b_sf, "Pcr_N": b_r["Pcr"], "Ncomp_N": b_r["Ncomp"], "KL_mm": b_r["KL_mm"],
            "buckle_axis": b_r["buckle_axis"], "buckle_type": b_r["buckle_type"], "buckle_solve": b_s.key,
            "bc_ratio": c_r["bc_ratio"], "SF_bc": c_sf, "bc_solve": c_s.key,
            "tau_MPa": max(s.member_rows[mid]["tau"] for s in valid) / 1e6,
            "SF_P": per_run["P"], "SF_R": per_run["R"],
            "flags": "J unverified (torsion, stiffness)",
        })
    mem_rows.sort(key=lambda r: r["SF"])

    # ---------------------------------------------------------------- joints
    best: dict[tuple, tuple] = {}
    per_run: dict[tuple, dict] = {}
    for s in valid:
        for r in s.joint_rows:
            k = (r["joint"], r["bracket"], r["copy"], r["leg"])
            u = r["U"] if np.isfinite(r["U"]) else -np.inf
            if r["type"] == "plate_other":
                u = np.hypot(np.hypot(r["Fx"], r["Fy"]), r["Fz"])     # largest force, for reporting
            if k not in best or u > best[k][0]:
                best[k] = (u, s, r)
            pr = per_run.setdefault(k, {"P": np.nan, "R": np.nan})
            g = _run_group(s)
            if g in pr and np.isfinite(r["SF"]):
                pr[g] = np.nanmin([pr[g], r["SF"]])
    caps = study.caps
    joint_rows = []
    for k, (u, s, r) in best.items():
        row = {"joint": r["joint"], "bracket": r["bracket"], "copy": r["copy"], "type": r["type"],
               "leg": r["leg"], "member": f"M{r['member']}", "a": f"M{r['a']}", "b": f"M{r['b']}",
               "SF": r["SF"], "U": r["U"], "gov_term": r["gov_term"],
               "gov_run": s.run.label, "gov_case": s.case,
               "Fx_N": r["Fx"], "Fy_N": r["Fy"], "Fz_N": r["Fz"],
               "Mx_Nm": r["Mx"], "My_Nm": r["My"], "Mz_Nm": r["Mz"]}
        for t in ("U_shear", "U_pull", "U_Mx", "U_My", "U_Mz", "U_bend_line", "U_bend_stem"):
            row[t] = r[t]
        if r["type"] == "triangle":
            row.update(F_fric_N=caps.F_fric, F_pull_N=caps.F_pull, Mx_max_Nm=caps.M_tilt,
                       My_max_Nm=caps.M_tilt, Mz_max_Nm=caps.M_twist)
        elif r["type"] == "plate_t5":
            row.update(F_fric_N=caps.F_fric, F_pull_N=caps.F_pull,
                       M_line_max_Nm=caps.plate_M_line_A if r["leg"] == "A" else caps.plate_M_line_B,
                       f_bolt_max_N=r.get("f_bolt_max"), Fz_bolt_max_N=r.get("Fz_bolt_max"))
            if r["leg"] == "B":
                row.update(M_stem_lower_hole_Nm=r.get("M_stem_lower_hole"), M_stem_neck_Nm=r.get("M_stem_neck"),
                           M_lower_hole_max_Nm=caps.plate_M_lower_hole, M_neck_max_Nm=caps.plate_M_neck)
        row.update(corner=r["option"], n_corner_options=r["n_options"],
                   SF_P=per_run[k]["P"], SF_R=per_run[k]["R"],
                   placeholders=PLACEHOLDER_BY_TYPE.get(r["type"], ""), note=r["note"])
        joint_rows.append(row)
    joint_rows.sort(key=lambda r: (np.nan_to_num(r["SF"], nan=np.inf), r["joint"]))
    joint_min = {}
    for r in joint_rows:
        if r["joint"] not in joint_min or np.nan_to_num(r["SF"], nan=np.inf) < np.nan_to_num(
                joint_min[r["joint"]]["SF"], nan=np.inf):
            joint_min[r["joint"]] = r

    # ---------------------------------------------------------------- frame / serviceability
    lam_s = min(valid, key=lambda s: s.lam if np.isfinite(s.lam) else np.inf)
    th = max(valid, key=lambda s: np.linalg.norm(s.thrust_disp))
    tt = max(valid, key=lambda s: s.thrust_tilt_deg)
    thrust = {"disp_mm": th.thrust_disp * 1e3, "disp_solve": th.key,
              "tilt_deg": tt.thrust_tilt_deg, "tilt_solve": tt.key,
              "tilt_flag": tt.thrust_tilt_deg > p.si.checks.tilt_limit}
    by_case = {}
    for s in study.solves:
        by_case.setdefault(s.case, s.loads.summary)
    sandbag = {"net_kg": max(v["sandbag_net_kg"] for v in by_case.values()),
               "uniform_kg": max(v["sandbag_uniform_kg"] for v in by_case.values()),
               "uplift_N": max(v["Fz_applied_N"] for v in by_case.values()),
               "F_h_N": max(v["F_horizontal_N"] for v in by_case.values()),
               "M_overturn_Nm": max(v["M_overturn_Nm"] for v in by_case.values())}

    # ---------------------------------------------------------------- k_theta sweep
    sweep_rows, interior = [], []
    Us = [item_U(s) for s in study.sweep]
    keys = sorted(set().union(*Us)) if Us else []
    for k in keys:
        vals = [u.get(k, np.nan) for u in Us]
        ok = [i for i, s in enumerate(study.sweep) if s.valid]
        row = {"item": k, **{f"U_k{study.sweep[i].run.k_theta:g}": vals[i] for i in range(len(vals))}}
        if ok:
            i_max = max(ok, key=lambda i: vals[i])
            row["peak_k"] = study.sweep[i_max].run.k_theta
            row["peak_at_end"] = i_max in (ok[0], ok[-1])
            if not row["peak_at_end"]:
                interior.append({"item": k, "k": row["peak_k"], "U": vals[i_max],
                                 "U_ends": (vals[ok[0]], vals[ok[-1]])})
        sweep_rows.append(row)
    return Envelope(mem_rows, joint_rows, joint_min, valid, (lam_s.lam, lam_s.key), thrust, sandbag,
                    sweep_rows, interior)
