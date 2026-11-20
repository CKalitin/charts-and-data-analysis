"""Interactive viewer: results/<mode>/viewer.html — 3D model + per-bracket free-body diagrams.

Everything is drawn client-side from one embedded JSON payload:
  - 3D: members (undeformed, coloured by SF; optional deformed overlay), joint rings, every
    bracket drawn as its outline (triangle L-angle profile / plate outline) with its bolts,
  - a state <select>: design envelope, every run/case, the buckling mode.
Click a bracket: the panel draws one isometric SVG free-body diagram per leg (bracket shape,
member faces dashed, bolts): the wrench the bracket puts on that leg's member at its bolt
(plates: group centroid), in the leg frame x slot / y across / z bolt axis (+ pull-off).
In-face forces orange, bolt-axis force green, moments purple curls (right-hand rule); the
governing load is boxed.  Below each: value, capacity, share of U, SF alone, what carries it.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

import numpy as np

from .analysis import Solve, Study
from .envelope import Envelope
from .joints import _closest_on_line_a
from .charts._render import (CRIT, HAIR, INK, INK2, MUTED, SAFE_JOINT, SAFE_MEMBER, SERIES, SERIOUS,
                             TERM_LABEL, deform_scale)


# --------------------------------------------------------------------------- payload helpers
def _r(v, sig=4):
    """Round for JSON (NaN/inf -> None)."""
    if v is None:
        return None
    v = float(v)
    if not math.isfinite(v):
        return None
    return float(f"{v:.{sig}g}")


def _vec(a, sig=5):
    return [_r(x, sig) for x in np.asarray(a, float).ravel()]


def _leg_items(br, r, caps) -> list[list]:
    """Rows [label, value, unit, capacity|None, U_term|None, carried by] for one leg row."""
    F = [r["Fx"], r["Fy"], r["Fz"]]
    M = [r["Mx"], r["My"], r["Mz"]]
    if br.type == "triangle":
        return [
            ["Fx along slot", F[0], "N", None, None, "friction"],
            ["Fy across slot", F[1], "N", None, None, "friction, then bearing"],
            ["→ shear √(Fx²+Fy²)", math.hypot(F[0], F[1]), "N", caps.F_fric, r["U_shear"], "friction μF_i"],
            ["Fz (+ pull-off)", F[2], "N", caps.F_pull, r["U_pull"],
             "bolt tension" if F[2] > 0 else "face contact"],
            ["Mx tilt", M[0], "N·m", caps.M_tilt, r["U_Mx"], "bolt + edge couple F_i·a"],
            ["My tilt", M[1], "N·m", caps.M_tilt, r["U_My"], "bolt + edge couple F_i·a"],
            ["Mz twist", M[2], "N·m", caps.M_twist, r["U_Mz"], "friction torque μF_i·r_f (weak)"],
        ]
    items = [[f"F{c}", F[i], "N", None, None, "bolt group"] for i, c in enumerate("xyz")]
    items += [[f"M{c}", M[i], "N·m", None, None, "bolt group"] for i, c in enumerate("xyz")]
    if br.type == "plate_t5":
        items += [
            ["→ max bolt shear", max(r["f_bolt_max"], r["f_bolt_slot_max"]), "N", caps.F_fric,
             r["U_shear"], "friction μF_i per bolt"],
            ["→ max bolt pull", r["Fz_bolt_max"], "N", caps.F_pull, r["U_pull"], "bolt tension F_i"],
            ["→ plate bend at bolt line", abs(M[0]), "N·m",
             caps.plate_M_line_A if r["leg"] == "A" else caps.plate_M_line_B, r["U_bend_line"],
             "plate section σ_y·b·t²/6"],
        ]
        if r["leg"] == "B":
            lo = r["M_stem_lower_hole"] / caps.plate_M_lower_hole
            ne = r["M_stem_neck"] / caps.plate_M_neck
            if lo >= ne:
                items.append(["→ stem bend at lower hole", r["M_stem_lower_hole"], "N·m",
                              caps.plate_M_lower_hole, r["U_bend_stem"], "plate section"])
            else:
                items.append(["→ stem bend at neck", r["M_stem_neck"], "N·m", caps.plate_M_neck,
                              r["U_bend_stem"], "plate section"])
    return items


def _leg_json(br, r, caps, src: str) -> dict:
    return {
        "leg": r["leg"], "member": int(r["member"]), "opt": r["option"], "src": src,
        "F": _vec([r["Fx"], r["Fy"], r["Fz"]]), "M": _vec([r["Mx"], r["My"], r["Mz"]]),
        "U": _r(r["U"]), "SF": _r(r["SF"]), "gov": TERM_LABEL.get(r["gov_term"], r["gov_term"]),
        "govk": r["gov_term"],
        "items": [[lab, _r(v), u, _r(c), _r(U), by] for lab, v, u, c, U, by in _leg_items(br, r, caps)],
    }


def _member_json(r: dict) -> list:
    return [_r(r["SF"]), r["gov_check"], _r(r["sigma"] / 1e6), _r(r["N"]), _r(r["My"]), _r(r["Mz"]),
            _r(r["SF_yield"]), _r(r["SF_buckle"]), _r(r["SF_bc"])]


def _state_from_solve(study: Study, s: Solve, title: str, dshape_mm, src_members=None) -> dict:
    m = study.model
    legs: dict[int, list] = {}
    for r in s.joint_rows:
        legs.setdefault(r["spring"], []).append(_leg_json(m.brackets[r["spring"]], r, study.caps, s.key))
    return {
        "key": s.key, "title": title, "valid": bool(s.valid), "note": s.note,
        "members": {int(mid): _member_json(r) + [s.key] for mid, r in s.member_rows.items()},
        "legs": legs,
        "bearing": [[_r(f), bool(on), s.key] for f, on in zip(s.bearing_forces, s.active)],
        "dshape": None if dshape_mm is None else [_vec(r, 4) for r in dshape_mm.reshape(-1, 6)[:, :3]],
        "ground": None if s.ground_F is None else
        [_r(s.ground_F[i, 2] / c.trib if c.trib > 0 else 0.0, 3) for i, c in enumerate(m.ground)],
        "info": (f"max δ {s.max_disp * 1e3:.2f} mm · thrust δ {np.linalg.norm(s.thrust_disp) * 1e3:.2f} mm · "
                 f"tilt {s.thrust_tilt_deg:.2f}° · λ {s.lam:.1f} · bearing iters {s.bearing_iters}"
                 if s.valid else s.note),
    }


def _envelope_state(study: Study, env: Envelope) -> dict:
    m = study.model
    by_key = {s.key: s for s in study.solves + study.sweep}
    spring_of = {(br.joint, br.index, br.copy): i for i, br in enumerate(m.brackets)}
    legs: dict[int, list] = {}
    for er in env.joints:
        i = spring_of[(er["joint"], er["bracket"], er["copy"])]
        s = by_key[f"{er['gov_run']}/{er['gov_case']}"]
        r = next(x for x in s.joint_rows if x["spring"] == i and x["leg"] == er["leg"])
        legs.setdefault(i, []).append(_leg_json(m.brackets[i], r, study.caps, s.key))
    for v in legs.values():
        v.sort(key=lambda d: d["leg"])
    members = {}
    for er in env.members:
        mid = int(er["id"][1:])
        members[mid] = [_r(er["SF"]), er["gov_check"], _r(er["sigma_MPa"]), _r(er["N_N"]), _r(er["My_Nm"]),
                        _r(er["Mz_Nm"]), _r(er["SF_yield"]), _r(er["SF_buckle"]), _r(er["SF_bc"]),
                        f"{er['gov_run']}/{er['gov_case']}"]
    bearing = []
    for k in range(len(m.bearings)):
        f, src = max(((s.bearing_forces[k], s.key) for s in env.valid), key=lambda t: t[0])
        bearing.append([_r(f), bool(f > 0), src])
    return {"key": "envelope", "title": "Design envelope — worst of all valid solves, per item",
            "valid": True, "note": "", "members": members, "legs": legs, "bearing": bearing,
            "dshape": None,
            "info": "each item shows its own governing run/case; deformed shape needs a single solve"}


def payload(study: Study, env: Envelope, p) -> dict:
    m = study.model
    si = p.si
    scale = deform_scale(study, p)
    caps = study.caps
    x_mm = m.x * 1e3
    members = [{"id": int(mid), "profile": m.members[mid].profile, "L": _r(m.members[mid].L * 1e3),
                "nodes": [int(n) for n in ns]} for mid, ns in m.member_nodes.items()]
    brackets = []
    for i, br in enumerate(m.brackets):
        opts = {}
        for o in br.legs:
            opts[o.desc] = [{"name": lg.name, "member": int(lg.member), "P": _vec(lg.P * 1e3),
                             "frame": [_vec(row) for row in lg.frame],
                             "bolts": None if lg.bolts is None else [_vec(b * 1e3) for b in lg.bolts]}
                            for lg in o.legs]
        O = br.X
        if br.type in ("plate_t5", "plate_other"):
            ma, mb = m.geom(br.a), m.geom(br.b)
            O = _closest_on_line_a(ma.p0, ma.e, mb.p0, mb.e)
        brackets.append({"O": _vec(O * 1e3), "i": i, "label": br.label, "joint": br.joint, "index": br.index, "copy": br.copy,
                         "type": br.type, "a": int(br.a), "b": int(br.b), "face": br.face, "note": br.note,
                         "X": _vec(br.X * 1e3), "opts": opts})
    bearings = [{"k": k, "label": b.label, "joint": b.joint, "end_of": int(b.end_of), "bears_on": int(b.bears_on),
                 "X": _vec(m.x[b.n_end] * 1e3), "n": _vec(b.n)} for k, b in enumerate(m.bearings)]
    joints = []
    for j in m.joints:
        joints.append({"id": j.id, "at": _vec(j.at * 1e3), "members": [int(x) for x in j.members],
                       "br": [i for i, br in enumerate(m.brackets) if br.joint == j.id],
                       "be": [k for k, b in enumerate(m.bearings) if b.joint == j.id]})
    states = [_envelope_state(study, env)]
    for s in study.solves:
        tag = "" if s.valid else "  — mechanism, invalid"
        dsh = scale * s.ur * 1e3 if s.valid else None
        states.append(_state_from_solve(study, s, f"{s.key}{tag}", dsh))
    lam_s = next((s for s in study.solves if s.key == env.lam[1]), None)
    if lam_s is not None and lam_s.phi is not None:
        from .model import relative_to_base
        phi = relative_to_base(m, lam_s.phi)
        amp = np.abs(phi.reshape(-1, 6)[:, :3]).max()
        st = _state_from_solve(study, lam_s, f"Buckling mode λ = {lam_s.lam:.1f} ({lam_s.key})",
                               phi / amp * 0.08 * np.ptp(x_mm[:, 2]))
        st["key"] = "buckle"
        st["info"] = f"first frame buckling mode of {lam_s.key}, arbitrary amplitude; forces are that solve's"
        states.append(st)
    tp = m.thrust_point * 1e3
    tri, pl = si.triangle, si.plate
    h, bw, sw = pl.base_half_height * 1e3, pl.base_width * 1e3, pl.stem_width * 1e3
    te, top = pl.stem_taper_end_v * 1e3, pl.top_edge_v * 1e3
    dims = {"tri_bolt": _r(tri.bolt_from_corner * 1e3), "tri_leg": _r(tri.bolt_from_corner * 1e3 + 12.7),
            "face": 25.4, "tri_t": 4.0, "plate_t": _r(pl.thickness * 1e3),
            "plate": [[-bw / 2, -h], [bw / 2, -h], [bw / 2, h], [sw / 2, te], [sw / 2, top], [-sw / 2, top],
                      [-sw / 2, te], [-bw / 2, h]]}
    gpts = [_vec(c.P * 1e3) for c in m.ground]
    bags = None
    if getattr(study, "bags", None) is not None:
        b = study.bags
        bags = {"kg": _r(b.kg_each), "pts": [_vec(q * 1e3) for q in b.points(m)],
                "L": [_r(L * 1e3) for _, _, L in b.stations],
                "dir": [_vec(m.members[mid].e) for mid, _, _ in b.stations]}
    return {
        "ground": gpts, "bags": bags,
        "dims": dims,
        "mode": m.mode, "x": [_vec(r, 5) for r in x_mm], "members": members, "brackets": brackets,
        "bearings": bearings, "joints": joints, "states": states,
        "thrust": {"at": _vec(tp), "N": _r(study.solves[0].loads.summary["thrust_factored_N"])},
        "targets": {"member": si.checks.SF_target_member, "joint": si.checks.SF_target_joint},
        "scale": _r(scale), "span": _r(float(np.ptp(x_mm, axis=0).max())),
        "caps": {"F_fric": _r(caps.F_fric), "F_pull": _r(caps.F_pull), "M_tilt": _r(caps.M_tilt),
                 "M_twist": _r(caps.M_twist)},
        "colors": {"crit": CRIT, "serious": SERIOUS, "safe_member": SAFE_MEMBER, "safe_joint": SAFE_JOINT,
                   "ink": INK, "ink2": INK2, "muted": MUTED, "hair": HAIR,
                   "ax": [SERIES[0], SERIES[2], SERIES[6]], "sel": SERIES[3]},
    }


# --------------------------------------------------------------------------- static tables
def _table(rows, cols, attrs=None) -> str:
    head = "".join(f"<th>{html.escape(c)}</th>" for c, _ in cols)
    body = []
    for r in rows:
        tds = []
        for _, f in cols:
            v, cls = f(r)
            tds.append(f'<td class="{cls}">{v}</td>')
        a = attrs(r) if attrs else ""
        body.append(f"<tr {a}>" + "".join(tds) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _sfcell(sf, target):
    if not np.isfinite(sf):
        return "–", "num"
    cls = "crit" if sf < 1 else "warn" if sf < target else "ok"
    return f"{sf:.2f}", f"num {cls}"


def _plotly_js(mode: str) -> str:
    if mode == "cdn":
        from plotly.offline import get_plotlyjs_version
        return f'<script src="https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js"></script>'
    from plotly.offline import get_plotlyjs
    return f"<script>{get_plotlyjs()}</script>"


def write_html(study: Study, env: Envelope, p, path: Path) -> Path:
    si = p.si
    m = study.model
    tm, tj = si.checks.SF_target_member, si.checks.SF_target_joint
    n = int(si.output.n_lowest)
    data = json.dumps(payload(study, env, p), separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    jmin = next(r for r in env.joints if np.isfinite(r["SF"]))
    mmin = env.members[0]
    th, sb = env.thrust, env.sandbag
    stats = [
        ("lowest joint SF", *_sfcell(jmin["SF"], tj), f"{jmin['joint']} · {TERM_LABEL.get(jmin['gov_term'], '')}"),
        ("lowest member SF", *_sfcell(mmin["SF"], tm), f"{mmin['id']} · {mmin['gov_check']}"),
        ("frame buckling λ", *_sfcell(env.lam[0], tm), env.lam[1]),
        ("thrust-point tilt", f"{th['tilt_deg']:.2f}°", "num warn" if th["tilt_flag"] else "num ok",
         f"limit {si.checks.tilt_limit:g}° · δ {np.linalg.norm(th['disp_mm']):.1f} mm"),
        ("sandbag mass", f"{sb['net_kg']:.0f} kg", "num", f"net uplift {sb['uplift_N']:.0f} N"),
    ]
    stat_html = "".join(f'<div class="stat"><div class="k">{k}</div><div class="v {c}">{v}</div>'
                        f'<div class="s">{html.escape(s)}</div></div>' for k, v, c, s in stats)
    spring_of = {(br.joint, br.index, br.copy): i for i, br in enumerate(m.brackets)}
    jt = _table([r for r in env.joints if np.isfinite(r["SF"])][:n], [
        ("SF", lambda r: _sfcell(r["SF"], tj)), ("joint", lambda r: (r["joint"], "")),
        ("bracket", lambda r: (f"{r['bracket']}{' copy ' + str(r['copy'] + 1) if r['copy'] else ''} {r['type']}", "")),
        ("leg", lambda r: (f"{r['leg']} on {r['member']}", "")),
        ("governs", lambda r: (TERM_LABEL.get(r["gov_term"], ""), "")),
        ("share", lambda r: (f"{100 * r[r['gov_term']] / r['U']:.0f} %", "num")),
        ("run/case", lambda r: (f"{r['gov_run']}/{r['gov_case']}", "muted"))],
        attrs=lambda r: f'class="pick" data-spring="{spring_of[(r["joint"], r["bracket"], r["copy"])]}"')
    mt = _table(env.members[:n], [
        ("SF", lambda r: _sfcell(r["SF"], tm)), ("member", lambda r: (f"{r['id']} {r['profile']}", "")),
        ("governs", lambda r: (r["gov_check"], "")), ("σ MPa", lambda r: (f"{r['sigma_MPa']:.1f}", "num")),
        ("N", lambda r: (f"{r['N_N']:.0f}", "num")), ("Mz N·m", lambda r: (f"{r['Mz_Nm']:.1f}", "num")),
        ("run/case", lambda r: (f"{r['gov_run']}/{r['gov_case']}", "muted"))],
        attrs=lambda r: f'class="pick" data-member="{r["id"][1:]}"')
    changes = ("".join(f"<li><code>{html.escape(c.key)}</code> {html.escape(str(c.default))} → "
                       f"<b>{html.escape(str(c.value))}</b></li>" for c in p.changes)
               or "<li>all parameters at defaults</li>")
    flags = "".join(f"<li><code>{q.key}</code> = {html.escape(p.display(q.key))} <span class='muted'>[{q.flag}]</span></li>"
                    for f in ("placeholder", "unverified") for q in p.flagged(f))
    notes = "".join(f"<li>{html.escape(x)}</li>" for x in m.notes)
    mech = (f"<li>run P invalid (mechanism) for {', '.join(study.mechanism_cases)} → run R used</li>"
            if study.mechanism_cases else "")
    page = (TEMPLATE
            .replace("%%TITLE%%", f"Mojave Sphinx test stand — safety factors ({m.mode.upper()})")
            .replace("%%SUB%%", f"{html.escape(p.path.name)} · thrust {si.loads.thrust:.0f} N × DF {si.loads.DF:g} · "
                                f"targets: member {tm:g}, joint {tj:g} · {len(study.solves)} solves + "
                                f"{len(study.sweep)} sweep")
            .replace("%%STATS%%", stat_html).replace("%%JT%%", jt).replace("%%MT%%", mt)
            .replace("%%CHANGES%%", changes).replace("%%FLAGS%%", flags)
            .replace("%%NOTES%%", mech + (notes or "<li>none</li>"))
            .replace("%%PLOTLY%%", _plotly_js(si.output.plotlyjs))
            .replace("%%DATA%%", data).replace("%%JS%%", JS))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page)
    return path


TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sphinx Stand SF</title>
<style>
:root { --ink:#0b0b0b; --ink2:#52514e; --muted:#8a8984; --hair:#e4e3df; --faint:#f6f5f2; --crit:#d03b3b; --warn:#b8501f; --ok:#3f3e3a; --sel:#eda100; }
* { box-sizing:border-box; }
body { margin:0; background:#fff; color:var(--ink); font:13px/1.45 Inter, "DejaVu Sans", system-ui, sans-serif; }
main { max-width:1680px; margin:0 auto; padding:14px 16px 40px; }
h1 { font-size:15px; margin:0 0 2px; } .sub { color:var(--muted); font-size:12px; margin-bottom:12px; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:1px; background:var(--hair);
  border:1px solid var(--hair); margin-bottom:10px; }
.stat { background:#fff; padding:8px 12px; } .stat .k { color:var(--ink2); font-size:11px; }
.stat .v { font-size:22px; font-weight:600; font-variant-numeric:tabular-nums; } .stat .s { color:var(--muted); font-size:11px; }
.crit { color:var(--crit); } .warn { color:var(--warn); } .ok { color:var(--ok); } .muted { color:var(--muted); }
.bar { display:flex; flex-wrap:wrap; gap:6px 14px; align-items:center; padding:6px 0; border-top:1px solid var(--hair); }
.bar select { font:inherit; padding:3px 4px; max-width:100%; }
.bar label { display:inline-flex; gap:4px; align-items:center; color:var(--ink2); cursor:pointer; }
.bar button, .insp button.lnk { font:inherit; font-size:12px; background:#fff; border:1px solid var(--hair); padding:2px 8px; cursor:pointer; color:var(--ink); }
.bar button:hover, .insp button.lnk:hover { border-color:var(--ink2); }
.bar .grp { display:inline-flex; gap:4px; }
#stateinfo { color:var(--muted); font-size:11.5px; width:100%; }
.view { display:flex; gap:14px; align-items:stretch; }
#plot { flex:1 1 auto; min-width:0; height:760px; }
.insp { flex:0 0 560px; height:760px; overflow:auto; border-left:1px solid var(--hair); padding:2px 0 0 14px; }
.insp h3 { font-size:13px; margin:0 0 2px; } .insp h4 { font-size:12px; margin:12px 0 2px; color:var(--ink2); font-weight:600; }
.insp .k { color:var(--muted); font-size:11.5px; }
.insp .legsf { font-size:18px; font-weight:600; font-variant-numeric:tabular-nums; }
.key { display:flex; flex-wrap:wrap; gap:4px 12px; font-size:11.5px; color:var(--ink2); margin:6px 0; }
.sw { display:inline-block; width:18px; height:0; border-top:3px solid; vertical-align:middle; margin-right:4px; }
.sw.d { border-top-style:dashed; }
.pill { background:#fdf0d5; border:1px solid var(--crit); border-radius:3px; padding:0 4px; font-weight:700; }
.nav { display:flex; justify-content:space-between; align-items:center; margin:0 0 6px; }
.nav button:disabled { opacity:.35; cursor:default; }
.leg { border-top:1px solid var(--hair); margin-top:10px; padding-top:2px; }
svg.fbd { width:100%; height:auto; display:block; margin:6px 0 4px; }
table.legt td.by { color:var(--muted); font-size:11px; white-space:normal; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); gap:24px; margin-top:16px; }
h2 { font-size:12px; color:var(--ink2); margin:0 0 6px; font-weight:600; }
table { border-collapse:collapse; width:100%; font-size:12px; }
th { text-align:left; color:var(--muted); font-weight:500; border-bottom:1px solid var(--hair); padding:3px 8px 3px 0; }
td { padding:3px 8px 3px 0; border-bottom:1px solid #f3f2ef; white-space:nowrap; }
td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
td.num.crit, td.num.warn { font-weight:600; }
tr.sub td { color:var(--ink2); } tr.chk td:first-child { padding-left:0; }
tr.gov td { background:#fdf3e1; }
tr.pick { cursor:pointer; } tr.pick:hover td { background:var(--faint); }
.grid th:first-child, .grid td:first-child { width:3.5em; }
ul { margin:4px 0 0; padding-left:18px; color:var(--ink2); } code { font-size:11.5px; }
.help { color:var(--muted); font-size:11.5px; margin-top:4px; }
@media (max-width:1100px) { .view { flex-direction:column; } .insp { flex:none; height:auto; max-height:none; border-left:0; border-top:1px solid var(--hair); padding:10px 0 0; } #plot { height:560px; } }
@media (max-width:600px) { .grid { grid-template-columns:1fr; } td { white-space:normal; } #plot { height:440px; } }
</style>
%%PLOTLY%%
</head><body><main>
<h1>%%TITLE%%</h1>
<div class="sub">%%SUB%%</div>
<div class="stats">%%STATS%%</div>
<div class="bar">
  <select id="state" aria-label="result state"></select>
  <label><input type="checkbox" id="deformed"> deformed</label>
  <label id="groundlab"><input type="checkbox" id="ground" checked> ground reaction</label>
  <span class="grp" id="cams"></span>
  <span class="grp"><button id="focus" title="zoom to the selection">focus</button><button id="clear">clear</button></span>
  <div id="stateinfo"></div>
</div>
<div class="view"><div id="plot"></div><div class="insp" id="insp"></div></div>
<div class="help">Click a member, a joint (ring) or a bracket (its outline). Colours: red SF &lt; 1, orange 1 ≤ SF &lt; target, grey ≥ target.
A bracket click opens its free-body diagram per leg in the panel. Camera icon saves a 3× PNG.</div>
<div class="grid"><div><h2>Lowest joint SFs (envelope) — click a row</h2>%%JT%%</div><div><h2>Lowest member SFs (envelope) — click a row</h2>%%MT%%</div></div>
<div class="grid"><div><h2>Parameters changed from defaults</h2><ul>%%CHANGES%%</ul>
<h2 style="margin-top:12px">Model notes</h2><ul>%%NOTES%%</ul></div>
<div><h2>Unverified inputs</h2><ul>%%FLAGS%%<li><code>plate_other</code> brackets: forces only, no capacity</li></ul></div></div>
</main>
<script id="payload" type="application/json">%%DATA%%</script>
<script>%%JS%%</script>
</body></html>"""


JS = r"""
(function () {
const D = JSON.parse(document.getElementById('payload').textContent);
const C = D.colors, X = D.x;
const plot = document.getElementById('plot'), insp = document.getElementById('insp');
const sel = { kind: null, id: null };
let S = D.states[0];
const ui = { deformed: false, ground: true };
// FBD palette (as the reference sketch): in-plane force orange, bolt-axis force green, moments purple
const FB = { fxy: '#e0622c', fz: '#16a06c', m: '#6b5fd3', plate: '#d9d7d1', plateEdge: '#77756f',
  ghost: '#efeeea', face: '#a9a7a1', ink: '#1d1c1a', muted: '#8a8984', gov: '#fdf0d5' };

// ------------------------------------------------------------------ vector helpers
const fin = v => v !== null && v !== undefined && isFinite(v);
const fmt = (v, d) => !fin(v) ? '–' : (Math.abs(v) >= 1000 ? v.toFixed(0) : v.toFixed(d === undefined ? 1 : d));
const sfTxt = v => !fin(v) ? '∞' : v >= 100 ? '>100' : v.toFixed(2);
const sfClass = (v, t) => !fin(v) ? 'ok' : v < 1 ? 'crit' : v < t ? 'warn' : 'ok';
const binOf = (v, t) => !fin(v) ? 2 : v < 1 ? 0 : v < t ? 1 : 2;
const add = (a, b, k = 1) => [a[0] + k * b[0], a[1] + k * b[1], a[2] + k * b[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = a => Math.hypot(a[0], a[1], a[2]);
const unit = a => mul(a, 1 / (norm(a) || 1));
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const legsOf = i => S.legs[i] || [];
function bracketSF(i) { let m = Infinity; for (const l of legsOf(i)) if (fin(l.SF)) m = Math.min(m, l.SF); return m; }
function optOf(i) { const b = D.brackets[i], ls = legsOf(i); return (ls.length && b.opts[ls[0].opt]) || Object.values(b.opts)[0]; }
function legGeom(i, l) { const o = D.brackets[i].opts[l.opt]; return o ? o.find(g => g.name === l.leg) : null; }

// ------------------------------------------------------------------ bracket shape in a local frame
// u = leg-a / member-a slot direction, v = leg-b direction made orthogonal, w = u x v.
// Triangle: L-angle inside the corner, plate a in (u,w) at v=0, plate b in (v,w) at u=0, two
// triangular gussets at the plate edges.  Plate: the brief's outline in (u,v), w = plate normal.
function shapeOf(i) {
  const b = D.brackets[i], opt = optOf(i);
  // plates: v = plate normal (plate lies flat, seen from above); triangles: v = leg b direction
  const u = unit(opt[0].frame[0]), eb = opt[1].frame[0];
  const v = b.type === 'triangle' ? unit(sub(eb, mul(u, dot(eb, u)))) : unit(opt[0].frame[2]), w = cross(u, v);
  const O = b.type === 'triangle' ? b.X : b.O;
  const toL = g => { const d = sub(g, O); return [dot(d, u), dot(d, v), dot(d, w)]; };
  const dirL = g => [dot(g, u), dot(g, v), dot(g, w)];
  const toG = l => add(add(add(O, u, l[0]), v, l[1]), w, l[2]);
  const polys = [], faces = [];
  const F = D.dims.face;
  if (b.type === 'triangle') {
    const ea = [1, 0, 0], ebl = unit(dirL(eb)), Lg = D.dims.tri_leg, h = F / 2;
    const P = (s, e, t) => add(mul(e, s), [0, 0, t]);
    polys.push({ leg: 'a', pts: [P(0, ea, -h), P(Lg, ea, -h), P(Lg, ea, h), P(0, ea, h)] });
    polys.push({ leg: 'b', pts: [P(0, ebl, -h), P(Lg, ebl, -h), P(Lg, ebl, h), P(0, ebl, h)] });
    for (const t of [-h, h]) polys.push({ leg: 'g', pts: [P(0, ea, t), P(0.8 * Lg, ea, t), P(0.8 * Lg, ebl, t)] });
    const Lf = 2.1 * Lg, hf = 0.62 * F;
    faces.push({ leg: 'a', pts: [P(-4, ea, -hf), P(Lf, ea, -hf), P(Lf, ea, hf), P(-4, ea, hf)], at: P(Lf, ea, hf) });
    faces.push({ leg: 'b', pts: [P(-4, ebl, -hf), P(Lf, ebl, -hf), P(Lf, ebl, hf), P(-4, ebl, hf)], at: P(Lf, ebl, -hf) });
  } else {
    const ebl = unit(dirL(eb));
    polys.push({ leg: 'p', pts: D.dims.plate.map(q => add(mul([1, 0, 0], q[0]), ebl, q[1])) });
    const bA = opt[0].bolts.map(toL), bB = opt[1].bolts.map(toL);
    const uMin = Math.min(...bA.map(q => q[0])) - 25, uMax = Math.max(...bA.map(q => q[0])) + 25;
    const vMax = Math.max(...bB.map(q => q[1])) + 25, h = F / 2;
    faces.push({ leg: 'A', pts: [[uMin, -h, -1], [uMax, -h, -1], [uMax, h, -1], [uMin, h, -1]], at: [uMax, -h, -1] });
    faces.push({ leg: 'B', pts: [[-h, h, -1], [h, h, -1], [h, vMax, -1], [-h, vMax, -1]], at: [h, vMax, -1] });
  }
  return { b, opt, u, v, w, O, toL, dirL, toG, polys, faces };
}

// ------------------------------------------------------------------ 3D traces
function memberTraces() {
  const names = ['SF < 1', `1 ≤ SF < ${D.targets.member}`, `SF ≥ ${D.targets.member}`];
  const cols = [C.crit, C.serious, C.safe_member];
  const out = [];
  for (let b = 0; b < 3; b++) {
    const x = [], y = [], z = [], t = [], cd = [];
    for (const m of D.members) {
      const r = S.members[m.id];
      if (binOf(r[0], D.targets.member) !== b) continue;
      const txt = `<b>M${m.id}</b> · ${m.profile}<br>SF <b>${sfTxt(r[0])}</b> (${r[1]})<br>σ ${fmt(r[2])} MPa · N ${fmt(r[3], 0)} N<br>My ${fmt(r[4])} · Mz ${fmt(r[5])} N·m<br>${r[9]}`;
      for (const n of m.nodes) { x.push(X[n][0]); y.push(X[n][1]); z.push(X[n][2]); t.push(txt); cd.push(['m', m.id]); }
      x.push(null); y.push(null); z.push(null); t.push(null); cd.push(null);
    }
    out.push({ type: 'scatter3d', mode: 'lines', x, y, z, hovertext: t, hoverinfo: 'text', customdata: cd,
      name: names[b], legendgroup: 'b' + b, line: { color: cols[b], width: b < 2 ? 7 : 5 } });
  }
  if (sel.kind === 'member' || sel.kind === 'bracket') {
    const ids = sel.kind === 'member' ? [sel.id] : legsOf(sel.id).map(l => l.member);
    const x = [], y = [], z = [];
    for (const id of ids) {
      const m = D.members.find(q => q.id === id); if (!m) continue;
      for (const n of m.nodes) { x.push(X[n][0]); y.push(X[n][1]); z.push(X[n][2]); }
      x.push(null); y.push(null); z.push(null);
    }
    out.push({ type: 'scatter3d', mode: 'lines', x, y, z, hoverinfo: 'skip', showlegend: false,
      line: { color: C.sel, width: 9 }, opacity: 0.3 });
  }
  return out;
}
function groundTraces() {
  if (!ui.ground || !D.ground.length) return [];
  const out = [];
  if (S.ground) {
    const qm = Math.max(...S.ground.map(q => q || 0)) || 1, L = 0.12 * D.span;
    const x = [], y = [], z = [], t = [], lx = [], ly = [], lz = [];
    D.ground.forEach((p, i) => {
      const q = S.ground[i] || 0;
      if (q <= 0) { lx.push(p[0]); ly.push(p[1]); lz.push(p[2]); return; }
      const d = L * q / qm;
      x.push(p[0], p[0], null); y.push(p[1], p[1], null); z.push(p[2] - d, p[2], null);
      const h = `ground pressure ${(q / 1000).toFixed(2)} kN/m`; t.push(h, h, null);
    });
    out.push({ type: 'scatter3d', mode: 'lines', x, y, z, hovertext: t, hoverinfo: 'text', name: 'ground pressure (length ∝ q)',
      line: { color: '#3987e5', width: 4 } });
    if (lx.length) out.push({ type: 'scatter3d', mode: 'markers', x: lx, y: ly, z: lz, hoverinfo: 'skip', name: 'lift-off',
      marker: { size: 2.5, color: C.crit } });
  }
  if (D.bags) {
    const x = [], y = [], z = [], t = [];
    D.bags.pts.forEach((p, k) => {
      const d = D.bags.dir[k], h = D.bags.L[k] / 2;
      x.push(p[0] - d[0] * h, p[0] + d[0] * h, null); y.push(p[1] - d[1] * h, p[1] + d[1] * h, null);
      z.push(p[2] + 30, p[2] + 30, null); const s = `sandbag ${D.bags.kg} kg`; t.push(s, s, null);
    });
    out.push({ type: 'scatter3d', mode: 'lines', x, y, z, hovertext: t, hoverinfo: 'text', name: `sandbags (${D.bags.kg} kg each)`,
      line: { color: '#c79a5b', width: 16 } });
  }
  return out;
}
function deformedTrace() {
  if (!ui.deformed || !S.dshape) return [];
  const x = [], y = [], z = [];
  for (const m of D.members) {
    for (const n of m.nodes) { const d = S.dshape[n]; x.push(X[n][0] + d[0]); y.push(X[n][1] + d[1]); z.push(X[n][2] + d[2]); }
    x.push(null); y.push(null); z.push(null);
  }
  const lab = S.key === 'buckle' ? 'buckling mode' : `deformed × ${D.scale.toFixed(0)}`;
  return [{ type: 'scatter3d', mode: 'lines', x, y, z, hoverinfo: 'skip', name: lab, line: { color: C.ink, width: 2.5 } }];
}
function jointTrace() {
  const x = [], y = [], z = [], c = [], s = [], t = [], cd = [];
  for (const j of D.joints) {
    let w = Infinity, wi = null;
    for (const i of j.br) { const v = bracketSF(i); if (v < w) { w = v; wi = i; } }
    const b = binOf(w, D.targets.joint);
    x.push(j.at[0]); y.push(j.at[1]); z.push(j.at[2]);
    c.push([C.crit, C.serious, C.safe_joint][b]); s.push(sel.kind === 'joint' && sel.id === j.id ? 22 : 15);
    t.push(`<b>${j.id}</b> · ${j.br.length} bracket(s), ${j.be.length} bearing(s)<br>worst bracket SF <b>${sfTxt(w)}</b>` +
      (wi !== null ? ` (${D.brackets[wi].label})` : ''));
    cd.push(['j', j.id]);
  }
  return { type: 'scatter3d', mode: 'markers', x, y, z, hovertext: t, hoverinfo: 'text', customdata: cd,
    name: 'joint (worst bracket)', marker: { symbol: 'circle-open', size: s, color: c, opacity: 0.7, line: { width: 2, color: c } } };
}
// each bracket drawn as its outline (triangle: L-angle side profile; plate: outline) + bolt dots
function bracketTraces() {
  const groups = [0, 1, 2, 3].map(() => ({ x: [], y: [], z: [], t: [], cd: [] }));
  const bolts = { x: [], y: [], z: [] };
  D.brackets.forEach((b, i) => {
    const sh = shapeOf(i), v = bracketSF(i), ls = legsOf(i);
    const g = groups[sel.kind === 'bracket' && sel.id === i ? 3 : binOf(v, D.targets.joint)];
    const off = b.copy ? mul(sh.w, 8 * b.copy) : [0, 0, 0];
    const txt = `<b>${b.label}</b> ${b.type} · M${b.a}–M${b.b}<br>SF <b>${sfTxt(v)}</b>` +
      ls.map(l => `<br>leg ${l.leg} on M${l.member}: SF ${sfTxt(l.SF)} · ${l.gov}`).join('') + '<br><i>click for its free-body diagram</i>';
    let loops;
    if (b.type === 'triangle') {   // the gusset triangle on the face side + both plates' outer edges
      const L = D.dims.tri_leg, ea = [1, 0, 0], ebl = unit(sh.dirL(sh.opt[1].frame[0]));
      loops = [[[0, 0, 0], mul(ea, L), mul(ebl, L), [0, 0, 0]]];
    } else loops = [sh.polys[0].pts.concat([sh.polys[0].pts[0]])];
    for (const lp of loops) {
      for (const q of lp) { const p = add(sh.toG(q), off); g.x.push(p[0]); g.y.push(p[1]); g.z.push(p[2]); g.t.push(txt); g.cd.push(['b', i]); }
      g.x.push(null); g.y.push(null); g.z.push(null); g.t.push(null); g.cd.push(null);
    }
    for (const leg of sh.opt) for (const p of (leg.bolts || [leg.P])) { const q = add(p, off); bolts.x.push(q[0]); bolts.y.push(q[1]); bolts.z.push(q[2]); }
  });
  const cols = [C.crit, C.serious, C.safe_joint, C.sel];
  const fills = [0, 1, 2, 3].map(() => ({ x: [], y: [], z: [], i: [], j: [], k: [] }));
  D.brackets.forEach((b, i) => {
    const sh = shapeOf(i), f = fills[sel.kind === 'bracket' && sel.id === i ? 3 : binOf(bracketSF(i), D.targets.joint)];
    const off = b.copy ? mul(sh.w, 8 * b.copy) : [0, 0, 0];
    const poly = b.type === 'triangle' ? [[0, 0, 0], [D.dims.tri_leg, 0, 0], mul(unit(sh.dirL(sh.opt[1].frame[0])), D.dims.tri_leg)] : sh.polys[0].pts;
    const n0 = f.x.length;
    for (const q of poly) { const p = add(sh.toG(q), off); f.x.push(p[0]); f.y.push(p[1]); f.z.push(p[2]); }
    for (let k = 1; k < poly.length - 1; k++) { f.i.push(n0); f.j.push(n0 + k); f.k.push(n0 + k + 1); }
  });
  const fcols = [C.crit, C.serious, C.safe_joint, C.sel];
  const meshes = fills.filter(f => f.x.length).map((f, k) => ({ type: 'mesh3d', ...f, color: fcols[fills.indexOf(f)], opacity: 0.45,
    flatshading: true, hoverinfo: 'skip', showlegend: false, lighting: { ambient: 1, diffuse: 0 } }));
  const out = meshes.concat(groups.map((g, k) => ({ type: 'scatter3d', mode: 'lines', x: g.x, y: g.y, z: g.z, hovertext: g.t, hoverinfo: 'text',
    customdata: g.cd, name: k === 3 ? 'selected bracket' : k === 0 ? 'bracket' : '', showlegend: k === 0,
    line: { color: cols[k], width: k === 3 ? 8 : 5 } })));
  out.push({ type: 'scatter3d', mode: 'markers', ...bolts, hoverinfo: 'skip', showlegend: false,
    marker: { size: 2, color: C.ink } });
  return out;
}
function thrustTrace() {
  const a = D.thrust.at, top = [a[0], a[1], a[2] + 0.12 * D.span];
  return [{ type: 'scatter3d', mode: 'lines', x: [a[0], top[0]], y: [a[1], top[1]], z: [a[2], top[2]],
    line: { color: C.ink, width: 4 }, hovertext: `thrust ${fmt(D.thrust.N, 0)} N (factored)`, hoverinfo: 'text', showlegend: false },
  { type: 'cone', x: [top[0]], y: [top[1]], z: [top[2]], u: [0], v: [0], w: [0.025 * D.span], sizemode: 'absolute', sizeref: 1,
    anchor: 'tip', showscale: false, colorscale: [[0, C.ink], [1, C.ink]], hoverinfo: 'skip', showlegend: false }];
}
function bearingTraces() {
  if (sel.kind !== 'joint') return [];
  const j = D.joints.find(q => q.id === sel.id); if (!j) return [];
  return j.be.map(k => {
    const be = D.bearings[k], f = S.bearing[k];
    return { type: 'scatter3d', mode: 'markers', x: [be.X[0]], y: [be.X[1]], z: [be.X[2]],
      marker: { size: 7, symbol: 'square', color: f[1] ? FB.fz : C.muted },
      hovertext: `${be.label}: ${f[1] ? fmt(f[0], 0) + ' N compression' : 'open'}`, hoverinfo: 'text', showlegend: false };
  });
}

// ------------------------------------------------------------------ SVG free-body diagram (one leg)
// Isometric view along (1,1,1) of the local frame: u -> right-down, v -> up, w -> left-down.
const K = 3.4;                                    // px per mm
const VIEW = unit([1, 1, 1]);                     // towards the viewer
const LIGHT = unit([0.35, 1, 0.55]);
const iso = l => [K * 0.866 * (l[0] - l[2]), K * (0.5 * (l[0] + l[2]) - l[1])];
const depth = l => l[0] + l[1] + l[2];            // larger = nearer
function shade(hex, n, k0 = 0.62) {
  const t = k0 + (1 - k0) * Math.max(0, dot(n, LIGHT));
  const c = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
  return '#' + c.map(v => Math.round(Math.min(255, v * t + (1 - t) * 40 * 0)).toString(16).padStart(2, '0')).join('');
}
// solids as face lists {pts (local 3D), n (outward), fill, stroke, op, deco}
function quadFaces(o, A, B, Cc, style) {
  const P = (a, b, c) => add(add(add(o, A, a), B, b), Cc, c);
  const cen = P(0.5, 0.5, 0.5), F = [];
  const q = [[P(0, 0, 0), P(1, 0, 0), P(1, 1, 0), P(0, 1, 0)], [P(0, 0, 1), P(1, 0, 1), P(1, 1, 1), P(0, 1, 1)],
    [P(0, 0, 0), P(1, 0, 0), P(1, 0, 1), P(0, 0, 1)], [P(0, 1, 0), P(1, 1, 0), P(1, 1, 1), P(0, 1, 1)],
    [P(0, 0, 0), P(0, 1, 0), P(0, 1, 1), P(0, 0, 1)], [P(1, 0, 0), P(1, 1, 0), P(1, 1, 1), P(1, 0, 1)]];
  for (const pts of q) {
    let n = unit(cross(sub(pts[1], pts[0]), sub(pts[3], pts[0])));
    const c = mul(pts.reduce((a, p) => add(a, p), [0, 0, 0]), 0.25);
    if (dot(n, sub(c, cen)) < 0) n = mul(n, -1);
    F.push({ pts, n, ...style });
  }
  return F;
}
function extrudeFaces(poly, h, style) {          // flat polygon + thickness vector h
  const top = poly.map(p => add(p, h)), F = [];
  const cen = add(mul(poly.reduce((a, p) => add(a, p), [0, 0, 0]), 1 / poly.length), h, 0.5);
  const nb = unit(mul(h, -1));
  F.push({ pts: poly, n: nb, ...style }, { pts: top, n: mul(nb, -1), ...style });
  for (let k = 0; k < poly.length; k++) {
    const a = poly[k], b = poly[(k + 1) % poly.length], pts = [a, b, add(b, h), add(a, h)];
    let n = unit(cross(sub(b, a), h)); const c = mul(add(a, add(b, h)), 0.5);
    if (dot(n, sub(c, cen)) < 0) n = mul(n, -1);
    F.push({ pts, n, ...style });
  }
  return F;
}
const ALU = '#d4d2cc', ALU_DARK = '#b9b7b0', BRK = '#e9e7e2';
function scene(i, legName) {
  const sh = shapeOf(i), b = sh.b, opt = sh.opt, F = D.dims.face, h = F / 2, faces = [], bolts = [], tags = [];
  const za = unit(sh.dirL(opt[0].frame[2])), zb = unit(sh.dirL(opt[1].frame[2]));
  const ea = [1, 0, 0], ebl = unit(sh.dirL(opt[1].frame[0])), w = [0, 0, 1];
  const mem = () => ({ fill: ALU, stroke: '#9d9b94', op: 1, layer: 0 });
  let headZ;
  if (b.type === 'triangle') {
    const Lg = D.dims.tri_leg, t = D.dims.tri_t, Lf = 1.75 * Lg;
    // extrusion stubs: member a runs through the corner, member b butts onto it
    const fa = quadFaces(add(add(mul(ea, -F), za, -F), w, -h), mul(ea, Lf + F), mul(za, F), mul(w, F), mem());
    const fb = quadFaces(add(mul(zb, -F), w, -h), mul(ebl, Lf), mul(zb, F), mul(w, F), mem());
    slotDeco(fa, za, ea, w, h); slotDeco(fb, zb, ebl, w, h);
    faces.push(...fa, ...fb);
    tags.push({ at: add(add(mul(ea, Lf), za, -F), w, h), text: `M${b.a}`, sub: 'leg a member' },
      { at: add(add(mul(ebl, Lf), zb, -F * 0.5), w, -h), text: `M${b.b}`, sub: 'leg b member' });
    // L-angle: two plates + two gussets
    const pa = { fill: BRK, stroke: legName === 'a' ? '#3d3c39' : '#8f8d87', op: 1, w: legName === 'a' ? 1.3 : 0.8, layer: 1 };
    const pb = { fill: BRK, stroke: legName === 'b' ? '#3d3c39' : '#8f8d87', op: 1, w: legName === 'b' ? 1.3 : 0.8, layer: 1 };
    faces.push(...quadFaces(add([0, 0, 0], w, -h), mul(ea, Lg), mul(za, t), mul(w, F), pa));
    faces.push(...quadFaces(add([0, 0, 0], w, -h), mul(ebl, Lg), mul(zb, t), mul(w, F), pb));
    for (const s of [-h, h - 2.5]) {
      const tri = [add(add(za, zb, 1).map(v => v * t), w, s), add(add(mul(ea, 0.82 * Lg), za, t), w, s), add(add(mul(ebl, 0.82 * Lg), zb, t), w, s)];
      faces.push(...extrudeFaces(tri, mul(w, 2.5), { fill: BRK, stroke: '#8f8d87', op: 1, w: 0.8, layer: 1 }));
    }
    for (const lg of opt) bolts.push({ c: add(sh.toL(lg.P), lg.name === 'a' ? za : zb, t), z: lg.name === 'a' ? za : zb, on: lg.name === legName });
    headZ = t;
  } else {
    const n = unit(sh.dirL(opt[0].frame[2])), t = D.dims.plate_t;
    const bA = opt[0].bolts.map(sh.toL), bB = opt[1].bolts.map(sh.toL);
    const uMin = Math.min(...bA.map(q => q[0])) - 22, uMax = Math.max(...bA.map(q => q[0])) + 22;
    const vMax = Math.max(...bB.map(q => dot(q, ebl))) + 22;
    const acA = unit(cross(n, ea)), acB = unit(cross(n, ebl));
    const fa = quadFaces(add(add(mul(ea, uMin), acA, -h), n, -F), mul(ea, uMax - uMin), mul(acA, F), mul(n, F), mem());
    const fb = quadFaces(add(add(mul(ebl, h), acB, -h), n, -F), mul(ebl, vMax - h), mul(acB, F), mul(n, F), mem());
    slotDeco(fa, n, ea, acA, h); slotDeco(fb, n, ebl, acB, h);
    faces.push(...fa, ...fb);
    tags.push({ at: add(add(mul(ea, uMax), acA, -h), n, -F), text: `M${b.a}`, sub: 'group A member' },
      { at: add(add(mul(ebl, vMax), acB, h), n, -F), text: `M${b.b}`, sub: 'group B member' });
    const outline = D.dims.plate.map(q => add(mul(ea, q[0]), ebl, q[1]));
    faces.push(...extrudeFaces(outline, mul(n, t), { fill: BRK, stroke: '#3d3c39', op: 1, w: 1.1, layer: 1 }));
    for (const lg of opt) for (const bp of lg.bolts) bolts.push({ c: add(sh.toL(bp), n, t), z: n, on: lg.name === legName });
    headZ = t;
  }
  return { sh, faces, bolts, tags, headZ };
}
function slotDeco(faces, nrm, along, across, h) {   // T-slot groove on every long face
  for (const f of faces) {
    if (Math.abs(dot(f.n, along)) > 0.5) continue;
    const c = mul(f.pts.reduce((a, p) => add(a, p), [0, 0, 0]), 0.25);
    const ax = unit(cross(f.n, along)), L = f.pts.map(p => dot(sub(p, c), along)), lo = Math.min(...L), hi = Math.max(...L);
    f.deco = [-1, 1].map(s => [add(add(c, along, lo + 1), ax, s * 3.2), add(add(c, along, hi - 1), ax, s * 3.2)]);
  }
}
function hull(P) {
  const p = P.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]), cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const q of p) { while (lo.length > 1 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  for (const q of p.slice().reverse()) { while (up.length > 1 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}
const pathOf = (ps, close = true) => ps.map((q, k) => (k ? 'L' : 'M') + q[0].toFixed(1) + ',' + q[1].toFixed(1)).join(' ') + (close ? ' Z' : '');
function boltSVG(bt) {   // socket-head cap screw: cylinder 2r x 0.8r high, hex socket
  const r = 4.6, hh = 3.8, z = bt.z;
  let e1 = unit(cross(z, Math.abs(z[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0])); const e2 = cross(z, e1);
  const ring = (c, rr, n = 28) => Array.from({ length: n }, (_, k) => { const a = 2 * Math.PI * k / n; return add(add(c, e1, rr * Math.cos(a)), e2, rr * Math.sin(a)); });
  const top = add(bt.c, z, hh), base2 = ring(bt.c, r).map(iso), top2 = ring(top, r).map(iso);
  const hex = ring(top, 1.9, 6).map(iso);
  const col = bt.on ? ['#4a4945', '#6d6b66', '#1f1e1c'] : ['#a7a59f', '#c4c2bc', '#8a8984'];
  return `<path d="${pathOf(hull(base2.concat(top2)))}" fill="${col[0]}"/><path d="${pathOf(top2)}" fill="${col[1]}" stroke="${col[0]}" stroke-width="0.6"/>` +
    `<path d="${pathOf(hex)}" fill="${col[2]}"/>`;
}
function arrowHead(tip, dir2, size, color) {
  const n = Math.hypot(dir2[0], dir2[1]) || 1, d = [dir2[0] / n, dir2[1] / n], p = [-d[1], d[0]];
  const b = [tip[0] - d[0] * size, tip[1] - d[1] * size], m = [tip[0] - d[0] * size * 0.72, tip[1] - d[1] * size * 0.72];
  return `<path d="M${tip[0].toFixed(1)},${tip[1].toFixed(1)} L${(b[0] + p[0] * size * 0.45).toFixed(1)},${(b[1] + p[1] * size * 0.45).toFixed(1)} ` +
    `L${m[0].toFixed(1)},${m[1].toFixed(1)} L${(b[0] - p[0] * size * 0.45).toFixed(1)},${(b[1] - p[1] * size * 0.45).toFixed(1)} Z" fill="${color}" stroke="#fff" stroke-width="1.2" paint-order="stroke" stroke-linejoin="round"/>`;
}
function fbdSVG(i, legIdx) {
  const ls = legsOf(i), l = ls[legIdx], g = legGeom(i, l);
  const { sh, faces, bolts, tags, headZ } = scene(i, l.leg);
  const el = [], top = [], labels = [], pts = [];
  const P2 = l3 => { const p = iso(l3); pts.push(p); return p; };
  // geometry: back faces culled, painter's order by face centroid depth
  const items = [];
  for (const f of faces) {
    if (dot(f.n, VIEW) <= 1e-6) continue;
    const c = mul(f.pts.reduce((a, p) => add(a, p), [0, 0, 0]), 1 / f.pts.length);
    const ps = f.pts.map(P2);
    let svg = `<path d="${pathOf(ps)}" fill="${shade(f.fill, f.n)}" fill-opacity="${f.op}" stroke="${f.stroke}" stroke-width="${f.w || 0.7}" stroke-linejoin="round"/>`;
    if (f.deco) svg += f.deco.map(s => { const a = iso(s[0]), b = iso(s[1]); return `<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="#8d8b84" stroke-width="0.9"/>`; }).join('');
    items.push({ d: depth(c) + 1e4 * (f.layer || 0), svg });
  }
  for (const bt of bolts) items.push({ d: depth(bt.c) + 2e4, svg: boltSVG(bt) });
  items.sort((a, b) => a.d - b.d).forEach(it => el.push(it.svg));
  for (const t of tags) { const p = P2(t.at); labels.push({ at: p, dir: [1, 0.2], text: t.text, val: t.sub, color: '#6f6d67', tag: true }); }

  // wrench at the bolt (plates: group centroid), drawn from the head
  const ax = g.frame.map(f => unit(sh.dirL(f)));
  const z = ax[2];
  const B = add(sh.toL(g.P), z, headZ + 3.8), B2 = iso(B);
  const Fm = Math.max(...l.F.map(Math.abs)), Mm = Math.max(...l.M.map(Math.abs));
  const govC = { U_shear: Math.abs(l.F[0]) >= Math.abs(l.F[1]) ? 'F0' : 'F1', U_pull: 'F2', U_Mx: 'M0', U_My: 'M1', U_Mz: 'M2',
    U_bend_line: 'M0' }[l.govk];
  const tiny = [];
  const halo = (svg) => svg;
  for (let c = 0; c < 3; c++) {
    const v = l.F[c];
    if (!fin(v) || Fm <= 0 || Math.abs(v) < 0.02 * Fm) { tiny.push('F' + 'xyz'[c]); continue; }
    const len = 20 + 30 * Math.sqrt(Math.abs(v) / Fm), d = mul(ax[c], Math.sign(v));
    const tip = P2(add(B, d, len)), dir2 = [tip[0] - B2[0], tip[1] - B2[1]];
    const col = c === 2 ? FB.fz : FB.fxy, nd = Math.hypot(...dir2) || 1;
    const se = [tip[0] - dir2[0] / nd * 10, tip[1] - dir2[1] / nd * 10];
    top.push(`<line x1="${B2[0]}" y1="${B2[1]}" x2="${se[0]}" y2="${se[1]}" stroke="#fff" stroke-width="6.5" stroke-linecap="round" opacity="0.9"/>` +
      `<line x1="${B2[0]}" y1="${B2[1]}" x2="${se[0]}" y2="${se[1]}" stroke="${col}" stroke-width="3" stroke-linecap="round"/>` + arrowHead(tip, dir2, 13, col));
    labels.push({ at: [tip[0] + dir2[0] / nd * 6, tip[1] + dir2[1] / nd * 6], dir: dir2, color: col, gov: govC === 'F' + c,
      text: `F${'xyz'[c]}`, val: `${fmt(Math.abs(v))} N` });
  }
  for (let c = 0; c < 3; c++) {
    const v = l.M[c];
    if (!fin(v) || Mm <= 0 || Math.abs(v) < 0.02 * Mm) { tiny.push('M' + 'xyz'[c]); continue; }
    const a = ax[c], sF = Math.abs(l.F[c]) >= 0.02 * Fm ? Math.sign(l.F[c]) : 1;
    const cen = add(B, a, sF * 30), r = 6.5;
    const e1 = unit(cross(a, Math.abs(a[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0])), e2 = cross(a, e1);
    const sg = Math.sign(v), n = 40, path = [];
    for (let k = 0; k <= n; k++) { const th = 0.6 + sg * 5.0 * k / n; path.push(P2(add(cen, add(mul(e1, r * Math.cos(th)), mul(e2, r * Math.sin(th)))))); }
    const cen2 = iso(cen), last = path[n], d2 = [last[0] - path[n - 3][0], last[1] - path[n - 3][1]];
    const arc = pathOf(path.slice(0, -2), false);
    top.push(`<line x1="${B2[0]}" y1="${B2[1]}" x2="${cen2[0]}" y2="${cen2[1]}" stroke="${FB.m}" stroke-width="1" stroke-dasharray="1.5 2.5" stroke-linecap="round" opacity="0.7"/>` +
      `<path d="${arc}" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" opacity="0.9"/>` +
      `<path d="${arc}" fill="none" stroke="${FB.m}" stroke-width="2.6" stroke-linecap="round"/>` + arrowHead(last, d2, 11, FB.m));
    const o2 = [cen2[0] - B2[0], cen2[1] - B2[1]], no = Math.hypot(...o2) || 1, rr = Math.max(...path.map(q => Math.hypot(q[0] - cen2[0], q[1] - cen2[1])));
    labels.push({ at: [cen2[0] + o2[0] / no * (rr + 5), cen2[1] + o2[1] / no * (rr + 5)], dir: o2, color: FB.m, gov: govC === 'M' + c,
      text: `M${'xyz'[c]}`, val: `${fmt(Math.abs(v))} N·m` });
  }
  top.push(`<circle cx="${B2[0]}" cy="${B2[1]}" r="2.6" fill="#1d1c1a" stroke="#fff" stroke-width="1.2"/>`);

  // labels: greedy, no overlaps; name in colour, value in ink
  const boxes = [], H = 19, txt = [];
  const hit = bx => boxes.some(o => bx[0] < o[2] && bx[2] > o[0] && bx[1] < o[3] && bx[3] > o[1]);
  for (const lb of labels.sort((p, q) => (q.tag ? 0 : 1) - (p.tag ? 0 : 1))) {
    const w = (lb.text.length * 8.4 + lb.val.length * 7.6) + 18;
    const d = lb.dir || [1, 0], dn = Math.hypot(...d) || 1, ux = d[0] / dn, uy = d[1] / dn;
    const base = [lb.at[0] + (ux >= -0.2 ? 0 : -w), lb.at[1] + (Math.abs(uy) > 0.55 ? (uy > 0 ? 1 : -H - 1) : -H / 2)];
    const cands = [[0, 0], [0, -H - 2], [0, H + 2], [ux >= 0 ? 12 : -12, 0], [0, -2 * H - 4], [0, 2 * H + 4], [w / 2, 0], [-w / 2, 0], [0, -3 * H], [0, 3 * H]];
    let bx = null;
    for (const c of cands) { const t = [base[0] + c[0], base[1] + c[1]], cand = [t[0], t[1], t[0] + w, t[1] + H]; if (!hit(cand)) { bx = cand; break; } }
    if (!bx) bx = [base[0], base[1], base[0] + w, base[1] + H];
    boxes.push(bx); pts.push([bx[0], bx[1]], [bx[2], bx[3]]);
    if (lb.tag) {
      txt.push(`<text x="${bx[0] + 4}" y="${bx[1] + H - 6}" font-size="12.5" font-weight="650" fill="${lb.color}">${esc(lb.text)}` +
        `<tspan dx="5" font-size="10.5" font-weight="400" fill="${FB.muted}">${esc(lb.val)}</tspan></text>`);
      continue;
    }
    const bg = lb.gov ? `fill="${FB.gov}" stroke="${C.crit}" stroke-width="1.2"` : `fill="#fff" fill-opacity="0.92" stroke="${C.hair}" stroke-width="0.8"`;
    txt.push(`<rect x="${bx[0]}" y="${bx[1]}" width="${w}" height="${H}" rx="9.5" ${bg}/>` +
      `<text x="${bx[0] + 7}" y="${bx[1] + H - 5.5}" font-size="13" font-weight="700" fill="${lb.color}">${esc(lb.text)}` +
      `<tspan dx="5" font-weight="${lb.gov ? 700 : 500}" fill="${lb.gov ? C.crit : '#2a2927'}">${esc(lb.val)}</tspan></text>`);
  }
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const pad = 12, x0 = Math.min(...xs) - pad, y0 = Math.min(...ys) - pad, x1 = Math.max(...xs) + pad, y1 = Math.max(...ys) + pad;
  // leg-frame key, lower-left
  const T0 = [x0 + 18, y1 + 14], tri = [];
  ax.forEach((a, c) => {
    const d = iso(a), n = Math.hypot(...d) || 1, L = 22 * Math.max(0.3, n / K), e = [T0[0] + d[0] / n * L, T0[1] + d[1] / n * L];
    tri.push(`<line x1="${T0[0]}" y1="${T0[1]}" x2="${e[0]}" y2="${e[1]}" stroke="#8a8984" stroke-width="1.3"/>` + arrowHead(e, [e[0] - T0[0], e[1] - T0[1]], 6, '#8a8984') +
      `<text x="${e[0] + (e[0] >= T0[0] ? 3 : -9)}" y="${e[1] + 4}" font-size="11" font-weight="600" fill="#6f6d67">${'xyz'[c]}</text>`);
  });
  const foot = `<text x="${T0[0] + 38}" y="${T0[1] + 4}" font-size="11" fill="#8a8984">leg ${l.leg} frame · x slot · y across · z bolt axis, + pull-off` +
    `${tiny.length ? ` · not drawn (≈ 0): ${tiny.join(', ')}` : ''}</text>`;
  const vb = [x0, y0, x1 - x0, (y1 - y0) + 30];
  return `<svg class="fbd" viewBox="${vb.map(v => v.toFixed(1)).join(' ')}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, DejaVu Sans, system-ui, sans-serif">` +
    `${el.join('')}${top.join('')}${tri.join('')}${foot}${txt.join('')}</svg>`;
}

// ------------------------------------------------------------------ inspector
function sfSpan(v, t) { return `<span class="${sfClass(v, t)}">${sfTxt(v)}</span>`; }
function legTable(l) {
  const Umax = Math.max(...l.items.map(q => fin(q[4]) ? q[4] : -1));
  const rows = l.items.map(([lab, v, u, cap, U, by]) => {
    const share = fin(U) && fin(l.U) && l.U > 0 ? (100 * U / l.U).toFixed(0) + ' %' : '';
    const alone = fin(U) ? (U > 0 ? sfSpan(1 / U, D.targets.joint) : '∞') : '';
    const gov = fin(U) && U > 0 && Math.abs(U - Umax) < 1e-12;
    return `<tr class="${fin(cap) ? 'chk' : 'sub'}${gov ? ' gov' : ''}"><td>${esc(lab)}</td><td class="num">${fmt(v)} ${u}</td>` +
      `<td class="num">${fin(cap) ? fmt(cap) + ' ' + u : ''}</td><td class="num">${share}</td><td class="num">${alone}</td><td class="by">${esc(by)}</td></tr>`;
  }).join('');
  return `<table class="legt"><thead><tr><th>load</th><th class="num">value</th><th class="num">capacity</th>` +
    `<th class="num">share of U</th><th class="num">SF alone</th><th>carried by</th></tr></thead><tbody>${rows}</tbody></table>`;
}
function ranked() {
  return D.brackets.map((b, i) => [bracketSF(i), i]).filter(q => legsOf(q[1]).length)
    .sort((p, q) => (fin(p[0]) ? p[0] : 1e9) - (fin(q[0]) ? q[0] : 1e9)).map(q => q[1]);
}
function showBracket(i) {
  const b = D.brackets[i], ls = legsOf(i), v = bracketSF(i), rk = ranked(), pos = rk.indexOf(i);
  let h = `<div class="nav"><button class="lnk" data-step="-1" ${pos <= 0 ? 'disabled' : ''}>◀ lower SF</button>` +
    `<span class="k">${pos + 1} of ${rk.length} by SF</span><button class="lnk" data-step="1" ${pos >= rk.length - 1 ? 'disabled' : ''}>higher SF ▶</button></div>` +
    `<h3>${b.label} · ${b.type === 'triangle' ? 'triangle bracket' : b.type}${b.copy ? ' (copy ' + (b.copy + 1) + ')' : ''} — SF ${sfSpan(v, D.targets.joint)}</h3>` +
    `<div class="k">joint <button class="lnk" data-joint="${b.joint}">${b.joint}</button> · leg a on M${b.a}, leg b on M${b.b} · face ${b.face}` +
    `${b.note ? ' · ' + esc(b.note) : ''}</div>` +
    `<div class="k">Each leg is drawn alone: the loads the bracket puts on that leg's member at its bolt (plates: bolt-group centre), ` +
    `in the leg's own x, y, z. Arrows point the way the load acts; values are magnitudes (signed values in the table). ` +
    `Legs act in series, so the bracket SF is the lower leg SF. U = Σ term utilisations, SF = 1/U.</div>`;
  h += `<div class="key"><span><span class="sw" style="border-color:${FB.fxy}"></span>Fx, Fy in the face</span>` +
    `<span><span class="sw" style="border-color:${FB.fz}"></span>Fz bolt axis</span><span><span class="sw" style="border-color:${FB.m}"></span>moment (curl, right-hand rule)</span>` +
    `<span><span class="pill">label</span> governs</span></div>`;
  ls.forEach((l, k) => {
    h += `<div class="leg"><h4>leg ${l.leg} on M${l.member} — SF <span class="legsf ${sfClass(l.SF, D.targets.joint)}">${sfTxt(l.SF)}</span>` +
      ` <span class="k">U ${fin(l.U) ? l.U.toFixed(2) : '–'} · governs ${esc(l.gov || '–')}</span></h4>` +
      `<div class="k">${esc(l.src)} · corner option ${esc(l.opt)}</div>` + fbdSVG(i, k) + legTable(l) + `</div>`;
  });
  if (!ls.length) h += '<p class="k">no result rows for this bracket</p>';
  if (S.key === 'envelope') h += `<p class="k">Envelope: each leg shows the solve that governs it, so legs can come from different solves.</p>`;
  insp.innerHTML = h;
}
function showJoint(id) {
  const j = D.joints.find(q => q.id === id);
  let h = `<h3>Joint ${j.id}</h3><div class="k">members ${j.members.map(m => `<button class="lnk" data-member="${m}">M${m}</button>`).join(' ')}` +
    ` · at (${j.at.map(q => q.toFixed(0)).join(', ')}) mm</div><h4>Brackets — click for the free-body diagram</h4>`;
  h += `<table><thead><tr><th>bracket</th><th>type</th><th>legs</th><th class="num">SF</th><th>governs</th><th>run/case</th></tr></thead><tbody>`;
  for (const i of j.br) {
    const b = D.brackets[i], ls = legsOf(i), v = bracketSF(i);
    const w = ls.reduce((a, l) => (!a || (fin(l.SF) && l.SF < a.SF)) ? l : a, null);
    h += `<tr class="pick" data-spring="${i}"><td>${b.label}</td><td>${b.type}</td><td>a M${b.a} · b M${b.b}</td>` +
      `<td class="num">${sfSpan(v, D.targets.joint)}</td><td>${w ? esc(w.leg + ': ' + w.gov) : ''}</td><td class="muted">${w ? esc(w.src) : ''}</td></tr>`;
  }
  h += `</tbody></table>`;
  if (j.be.length) {
    h += `<h4>Bearing (end of one member pressing on another; compression only)</h4><table><thead><tr><th>contact</th>` +
      `<th class="num">force</th><th>state</th><th>run/case</th></tr></thead><tbody>`;
    for (const k of j.be) {
      const be = D.bearings[k], f = S.bearing[k];
      h += `<tr><td>M${be.end_of} end → M${be.bears_on}</td><td class="num">${f[1] ? fmt(f[0], 0) + ' N' : '0'}</td>` +
        `<td>${f[1] ? 'closed' : 'open'}</td><td class="muted">${esc(f[2])}</td></tr>`;
    }
    h += `</tbody></table>`;
    if (S.key === 'envelope') h += `<p class="k">Envelope: largest compression over valid solves.</p>`;
  }
  insp.innerHTML = h;
}
function showMember(id) {
  const m = D.members.find(q => q.id === id), r = S.members[id], t = D.targets.member;
  const js = D.joints.filter(j => j.members.includes(id));
  insp.innerHTML = `<h3>M${id} · ${m.profile} · ${m.L.toFixed(0)} mm — SF ${sfSpan(r[0], t)}</h3>` +
    `<div class="k">governs: ${esc(r[1])} · ${esc(r[9])}</div>` +
    `<table><tbody><tr><td>yield SF</td><td class="num">${sfSpan(r[6], t)}</td></tr>` +
    `<tr><td>buckling SF</td><td class="num">${sfSpan(r[7], t)}</td></tr><tr><td>beam-column SF</td><td class="num">${sfSpan(r[8], t)}</td></tr>` +
    `<tr class="sub"><td>σ at yield-governing section</td><td class="num">${fmt(r[2])} MPa</td></tr>` +
    `<tr class="sub"><td>N (tension +)</td><td class="num">${fmt(r[3], 0)} N</td></tr>` +
    `<tr class="sub"><td>My / Mz</td><td class="num">${fmt(r[4])} / ${fmt(r[5])} N·m</td></tr></tbody></table>` +
    `<h4>Joints on this member</h4>${js.map(j => `<button class="lnk" data-joint="${j.id}">${j.id}</button>`).join(' ') || '<span class="k">none</span>'}`;
}
function showNothing() {
  const w = ranked()[0];
  insp.innerHTML = `<h3>Inspector</h3><p class="k">Click a bracket (its outline in the 3D view) for its free-body diagram, a joint (ring) for its brackets ` +
    `and bearing forces, or a member for its checks. The state menu switches between the design envelope and any single run/case.</p>` +
    (w !== undefined ? `<p><button class="lnk" data-spring="${w}">open the lowest-SF bracket (${D.brackets[w].label}, SF ${sfTxt(bracketSF(w))})</button></p>` : '') +
    `<p class="k">${D.brackets.length} brackets · ${D.joints.length} joints · ${D.members.length} members · ${D.bearings.length} bearing contacts.</p>`;
}
function inspect() {
  if (sel.kind === 'bracket') showBracket(sel.id);
  else if (sel.kind === 'joint') showJoint(sel.id);
  else if (sel.kind === 'member') showMember(sel.id);
  else showNothing();
}

// ------------------------------------------------------------------ plot
const axis = t => ({ title: { text: t, font: { size: 11, color: C.ink2 } }, showbackground: false, showgrid: false,
  zeroline: false, showspikes: false, tickfont: { size: 10, color: C.muted }, linecolor: C.hair, ticks: '' });
const ext = [0, 1, 2].map(c => { const v = X.map(p => p[c]); return [Math.min(...v), Math.max(...v)]; });
const pad = 0.1 * D.span;
const rng = ext.map(e => [e[0] - pad, e[1] + pad]);
const span = rng.map(r => r[1] - r[0]), smax = Math.max(...span);
const Z0 = 1.6, ar = span.map(s => Z0 * s / smax);
const CAMS = {
  iso: { eye: { x: 1.1, y: -1.1, z: 0.6 }, up: { x: 0, y: 0, z: 1 } },
  front: { eye: { x: 0, y: -1.6, z: 0 }, up: { x: 0, y: 0, z: 1 } },
  side: { eye: { x: 1.6, y: 0, z: 0 }, up: { x: 0, y: 0, z: 1 } },
  top: { eye: { x: 0, y: 0, z: 1.6 }, up: { x: 0, y: 1, z: 0 } },
};
const layout = {
  uirevision: 'keep', paper_bgcolor: '#fff', margin: { l: 0, r: 0, t: 8, b: 0 }, hoverlabel: { font: { size: 12 } },
  font: { family: 'Inter, DejaVu Sans, system-ui, sans-serif', color: C.ink },
  legend: { x: 0.01, y: 0.02, bgcolor: 'rgba(255,255,255,0.85)', font: { size: 11 } },
  scene: { aspectmode: 'manual', aspectratio: { x: ar[0], y: ar[1], z: ar[2] },
    xaxis: { ...axis('x (mm)'), range: rng[0] }, yaxis: { ...axis('y (mm)'), range: rng[1] }, zaxis: { ...axis('z (mm)'), range: rng[2] },
    camera: { ...CAMS.iso, projection: { type: 'orthographic' } } },
};
function render() {
  layout.showlegend = plot.clientWidth > 600;
  const fl = plot._fullLayout && plot._fullLayout.scene;
  if (fl) { layout.scene.camera = JSON.parse(JSON.stringify(fl.camera)); layout.scene.aspectratio = { ...fl.aspectratio }; }
  const tr = [...memberTraces(), ...deformedTrace(), ...groundTraces(), ...thrustTrace(), jointTrace(), ...bracketTraces(), ...bearingTraces()];
  Plotly.react(plot, tr, layout, { displaylogo: false, responsive: true,
    toImageButtonOptions: { format: 'png', scale: 3, filename: 'stand' } });
}
function toScene(p) { return { x: ((p[0] - rng[0][0]) / span[0] - 0.5) * ar[0], y: ((p[1] - rng[1][0]) / span[1] - 0.5) * ar[1], z: ((p[2] - rng[2][0]) / span[2] - 0.5) * ar[2] }; }
function focusPoint() {
  if (sel.kind === 'bracket') return D.brackets[sel.id].X;
  if (sel.kind === 'joint') return D.joints.find(q => q.id === sel.id).at;
  if (sel.kind === 'member') { const m = D.members.find(q => q.id === sel.id); return X[m.nodes[Math.floor(m.nodes.length / 2)]]; }
  return null;
}
function focus() {
  const p = focusPoint(); if (!p) return;
  const f = sel.kind === 'bracket' ? 4 : 2.5, c0 = toScene(p), c = { x: c0.x * f, y: c0.y * f, z: c0.z * f };
  const cam = plot._fullLayout.scene.camera, e = cam.eye, o = cam.center;
  const d = [e.x - o.x, e.y - o.y, e.z - o.z], n = norm(d) || 1;
  Plotly.relayout(plot, { 'scene.aspectratio': { x: ar[0] * f, y: ar[1] * f, z: ar[2] * f },
    'scene.camera': { center: c, eye: { x: c.x + d[0] * 1.8 / n, y: c.y + d[1] * 1.8 / n, z: c.z + d[2] * 1.8 / n },
      up: cam.up, projection: { type: 'orthographic' } } });
}

// ------------------------------------------------------------------ zoom to cursor
// Plotly zooms an orthographic scene by scaling scene.aspectratio about the scene ORIGIN and
// never touches camera.center, so its own wheel always pulls toward the middle of the stand.
// Take the wheel first (capture phase, ahead of plotly's listener on the gl canvas) and move
// the camera with the zoom: scaling the aspect ratio by s sends a scene point P to s*P, so the
// point Q under the pointer holds its place on screen iff the camera moves to c + (s-1)*Q.
// Ticks are accumulated in zState and flushed one relayout per frame -- reading the camera
// back out of _fullLayout per tick races the in-flight relayout and the zoom then slides.
const ZSTEP = 1.1, ZMIN = 0.25, ZMAX = 60;
let zState = null, zBusy = false, zDirty = false;
function cursorPoint(ev, st) {
  // Q: the scene point under the pointer, on the view plane through the camera centre. The
  // basis comes from the camera we are about to move, not from glplot's view matrix, which
  // eases toward its target over several frames and so lags mid-scroll. Only the projection
  // is read from glplot (orthographic: it carries the canvas aspect, nothing camera-bound).
  const gl = plot._fullLayout.scene._scene.glplot, r = gl.canvas.getBoundingClientRect();
  const P = gl.cameraParams.projection, c = [st.center.x, st.center.y, st.center.z];
  const fwd = unit(sub(c, [st.eye.x, st.eye.y, st.eye.z]));
  const rt = unit(cross(fwd, [st.up.x, st.up.y, st.up.z])), up = cross(rt, fwd);
  const vx = (2 * (ev.clientX - r.left) / r.width - 1) / P[0];      // pointer offset from the
  const vy = (1 - 2 * (ev.clientY - r.top) / r.height) / P[5];      // centre, in scene units
  return c.map((ci, i) => ci + rt[i] * vx + up[i] * vy);
}
function zFlush() {
  zDirty = false;
  Plotly.relayout(plot, { 'scene.aspectratio': zState.ar, 'scene.camera.center': zState.center,
    'scene.camera.eye': zState.eye })
    .then(() => { if (zDirty) requestAnimationFrame(zFlush); else { zBusy = false; zState = null; } });
}
function wheelZoom(ev) {
  const sc = plot._fullLayout.scene;
  if (!sc || !sc._scene || !sc._scene.glplot || !sc._scene.glplot.cameraParams) return;
  ev.preventDefault(); ev.stopPropagation();
  if (!zState) {                       // nothing in flight: the layout is authoritative again,
    const c = sc.camera;               // so pick up any rotate / pan / preset since last time
    zState = { ar: { ...sc.aspectratio }, center: { ...c.center }, eye: { ...c.eye }, up: { ...c.up } };
  }
  const unit_ = ev.deltaMode === 1 ? 16 : ev.deltaMode === 2 ? 400 : 1;   // lines / pages -> px
  const k = zState.ar.z / ar[2];                                         // zoom vs the base view
  const s = Math.min(Math.max(Math.pow(ZSTEP, -ev.deltaY * unit_ / 120), ZMIN / k), ZMAX / k);
  if (Math.abs(s - 1) < 1e-9) return;
  const q = cursorPoint(ev, zState), m = q.map(v => (s - 1) * v);
  zState = { up: zState.up, ar: { x: zState.ar.x * s, y: zState.ar.y * s, z: zState.ar.z * s },
    center: { x: zState.center.x + m[0], y: zState.center.y + m[1], z: zState.center.z + m[2] },
    eye: { x: zState.eye.x + m[0], y: zState.eye.y + m[1], z: zState.eye.z + m[2] } };
  if (zBusy) { zDirty = true; return; }
  zBusy = true; requestAnimationFrame(zFlush);
}
plot.addEventListener('wheel', wheelZoom, { capture: true, passive: false });

// ------------------------------------------------------------------ wiring
function select(kind, id) { sel.kind = kind; sel.id = id; render(); inspect(); insp.scrollTop = 0; }
const sSel = document.getElementById('state');
D.states.forEach((s, k) => { const o = document.createElement('option'); o.value = k; o.textContent = s.title; if (!s.valid) o.style.color = C.muted; sSel.appendChild(o); });
function setState(k) {
  S = D.states[k];
  document.getElementById('stateinfo').textContent = S.info || '';
  const dfm = document.getElementById('deformed');
  dfm.disabled = !S.dshape; if (S.key === 'buckle' && S.dshape) { dfm.checked = true; ui.deformed = true; }
  render(); inspect();
}
sSel.addEventListener('change', e => setState(+e.target.value));
document.getElementById('deformed').addEventListener('change', e => { ui.deformed = e.target.checked; render(); });
document.getElementById('ground').addEventListener('change', e => { ui.ground = e.target.checked; render(); });
if (!D.ground.length) document.getElementById('groundlab').style.display = 'none';
const cams = document.getElementById('cams');
for (const [k, v] of Object.entries(CAMS)) {
  const b = document.createElement('button'); b.textContent = k;
  b.onclick = () => Plotly.relayout(plot, { 'scene.aspectratio': { x: ar[0], y: ar[1], z: ar[2] },
    'scene.camera': { ...v, center: { x: 0, y: 0, z: 0 }, projection: { type: 'orthographic' } } });
  cams.appendChild(b);
}
document.getElementById('focus').onclick = focus;
document.getElementById('clear').onclick = () => select(null, null);
document.addEventListener('click', e => {
  const t = e.target.closest('[data-spring],[data-joint],[data-member],[data-step]'); if (!t || t.disabled) return;
  if (t.dataset.step !== undefined) { const rk = ranked(), k = rk.indexOf(sel.id) + (+t.dataset.step); if (rk[k] !== undefined) select('bracket', rk[k]); return; }
  if (t.dataset.spring !== undefined) select('bracket', +t.dataset.spring);
  else if (t.dataset.joint !== undefined) select('joint', t.dataset.joint);
  else select('member', +t.dataset.member);
  if (t.closest('.grid')) { document.querySelector('.view').scrollIntoView({ behavior: 'smooth', block: 'start' }); focus(); }
});
setState(0);
plot.on('plotly_click', ev => {
  const pt = ev.points && ev.points[0]; if (!pt || !pt.customdata) return;
  const [k, id] = pt.customdata;
  // defer: re-rendering inside plotly's own click handler recurses in its hover-label code
  setTimeout(() => select(k === 'b' ? 'bracket' : k === 'j' ? 'joint' : 'member', id), 0);
});
window.__stand = { D, select, setState, focus };
})();
"""
