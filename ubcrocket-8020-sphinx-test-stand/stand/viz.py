"""Interactive viewer: results/stand.html — 3D model + free-body inspector.

Everything is drawn client-side from one embedded JSON payload:
  - members (undeformed, coloured by SF; optional deformed overlay),
  - joint markers (ring, worst bracket SF) and one marker per bracket (diamond),
  - a state <select>: design envelope, every run/case, the buckling mode.
Click a member, joint or bracket.  A bracket click draws its free-body diagram:
for each leg / bolt group the 6 wrench components acting ON THAT LEG'S MEMBER,
about the bolt point (group centroid for plates), in the leg frame
(x along the slot, y across, z = bolt axis, + = pull-off) — forces solid with one
arrowhead, moments dashed with two — and a table: value, capacity, share of the
leg utilisation U, SF if that term acted alone, leg SF, governing run/case.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

import numpy as np

from .analysis import Solve, Study
from .envelope import Envelope
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
    """Rows [label, value, unit, capacity|None, U_term|None] for one leg row."""
    F = [r["Fx"], r["Fy"], r["Fz"]]
    M = [r["Mx"], r["My"], r["Mz"]]
    if br.type == "triangle":
        return [
            ["Fx (along slot)", F[0], "N", None, None],
            ["Fy (across slot)", F[1], "N", None, None],
            ["shear √(Fx²+Fy²) vs μF_i", math.hypot(F[0], F[1]), "N", caps.F_fric, r["U_shear"]],
            ["Fz (+ pull-off) vs F_i", F[2], "N", caps.F_pull, r["U_pull"]],
            ["Mx tilt vs F_i·a", M[0], "N·m", caps.M_tilt, r["U_Mx"]],
            ["My tilt vs F_i·a", M[1], "N·m", caps.M_tilt, r["U_My"]],
            ["Mz twist vs μF_i·r_f", M[2], "N·m", caps.M_twist, r["U_Mz"]],
        ]
    items = [[f"F{c}", F[i], "N", None, None] for i, c in enumerate("xyz")]
    items += [[f"M{c}", M[i], "N·m", None, None] for i, c in enumerate("xyz")]
    if br.type == "plate_t5":
        items += [
            ["max bolt shear vs μF_i", max(r["f_bolt_max"], r["f_bolt_slot_max"]), "N", caps.F_fric,
             r["U_shear"]],
            ["max bolt pull vs F_i", r["Fz_bolt_max"], "N", caps.F_pull, r["U_pull"]],
            ["plate bend at bolt line (|Mx|)", abs(M[0]), "N·m",
             caps.plate_M_line_A if r["leg"] == "A" else caps.plate_M_line_B, r["U_bend_line"]],
        ]
        if r["leg"] == "B":
            lo = r["M_stem_lower_hole"] / caps.plate_M_lower_hole
            ne = r["M_stem_neck"] / caps.plate_M_neck
            if lo >= ne:
                items.append(["stem bend at lower hole", r["M_stem_lower_hole"], "N·m",
                              caps.plate_M_lower_hole, r["U_bend_stem"]])
            else:
                items.append(["stem bend at neck", r["M_stem_neck"], "N·m", caps.plate_M_neck,
                              r["U_bend_stem"]])
    return items


def _leg_json(br, r, caps, src: str) -> dict:
    return {
        "leg": r["leg"], "member": int(r["member"]), "opt": r["option"], "src": src,
        "F": _vec([r["Fx"], r["Fy"], r["Fz"]]), "M": _vec([r["Mx"], r["My"], r["Mz"]]),
        "U": _r(r["U"]), "SF": _r(r["SF"]), "gov": TERM_LABEL.get(r["gov_term"], r["gov_term"]),
        "items": [[lab, _r(v), u, _r(c), _r(U)] for lab, v, u, c, U in _leg_items(br, r, caps)],
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
        brackets.append({"i": i, "label": br.label, "joint": br.joint, "index": br.index, "copy": br.copy,
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
    return {
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
.insp { flex:0 0 470px; height:760px; overflow:auto; border-left:1px solid var(--hair); padding:2px 0 0 14px; }
.insp h3 { font-size:13px; margin:0 0 2px; } .insp h4 { font-size:12px; margin:12px 0 2px; color:var(--ink2); font-weight:600; }
.insp .k { color:var(--muted); font-size:11.5px; }
.insp .legsf { font-size:18px; font-weight:600; font-variant-numeric:tabular-nums; }
.key { display:flex; flex-wrap:wrap; gap:4px 12px; font-size:11.5px; color:var(--ink2); margin:6px 0; }
.sw { display:inline-block; width:18px; height:0; border-top:3px solid; vertical-align:middle; margin-right:4px; }
.sw.d { border-top-style:dashed; }
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
  <label><input type="checkbox" id="showF" checked> forces</label>
  <label><input type="checkbox" id="showM" checked> moments</label>
  <label><input type="checkbox" id="showBr" checked> bracket markers</label>
  <span class="grp" id="cams"></span>
  <span class="grp"><button id="focus" title="zoom to the selection">focus</button><button id="clear">clear</button></span>
  <div id="stateinfo"></div>
</div>
<div class="view"><div id="plot"></div><div class="insp" id="insp"></div></div>
<div class="help">Click a member, a joint (ring) or a bracket (diamond). Colours: red SF &lt; 1, orange 1 ≤ SF &lt; target, grey ≥ target.
Bracket arrows are the wrench acting on each leg's member, about its bolt point, in the leg frame. Camera icon saves a 3× PNG.</div>
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
const ui = { deformed: false, F: true, M: true, br: true };
const AX = ['x', 'y', 'z'];

// ------------------------------------------------------------------ helpers
const fin = v => v !== null && v !== undefined && isFinite(v);
const fmt = (v, d) => !fin(v) ? '–' : (Math.abs(v) >= 1000 ? v.toFixed(0) : v.toFixed(d === undefined ? 1 : d));
const sfTxt = v => !fin(v) ? '∞' : v >= 100 ? '>100' : v.toFixed(2);
function sfClass(v, t) { return !fin(v) ? 'ok' : v < 1 ? 'crit' : v < t ? 'warn' : 'ok'; }
function binOf(v, t) { return !fin(v) ? 2 : v < 1 ? 0 : v < t ? 1 : 2; }
const add = (a, b, k) => [a[0] + k * b[0], a[1] + k * b[1], a[2] + k * b[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const norm = a => Math.hypot(a[0], a[1], a[2]);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function legsOf(i) { return S.legs[i] || []; }
function bracketSF(i) {
  let m = Infinity; for (const l of legsOf(i)) if (fin(l.SF)) m = Math.min(m, l.SF); return m;
}
function legGeom(i, l) {
  const o = D.brackets[i].opts[l.opt]; return o ? o.find(g => g.name === l.leg) : null;
}
function bracketPos(i) {
  const b = D.brackets[i], ls = legsOf(i);
  const opt = ls.length ? b.opts[ls[0].opt] : Object.values(b.opts)[0];
  if (!opt) return b.X;
  const c = [0, 0, 0]; opt.forEach(g => { c[0] += g.P[0] / opt.length; c[1] += g.P[1] / opt.length; c[2] += g.P[2] / opt.length; });
  let p = add(b.X, sub(c, b.X), 0.55);
  if (b.copy) p = add(p, opt[0].frame[2], 6 * b.copy);
  return p;
}

// ------------------------------------------------------------------ traces
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
    c.push([C.crit, C.serious, C.safe_joint][b]); s.push(sel.kind === 'joint' && sel.id === j.id ? 20 : b < 2 ? 13 : 9);
    t.push(`<b>${j.id}</b> · ${j.br.length} bracket(s), ${j.be.length} bearing(s)<br>worst bracket SF <b>${sfTxt(w)}</b>` +
      (wi !== null ? ` (${D.brackets[wi].label})` : ''));
    cd.push(['j', j.id]);
  }
  return { type: 'scatter3d', mode: 'markers', x, y, z, hovertext: t, hoverinfo: 'text', customdata: cd,
    name: 'joint (worst bracket)', marker: { symbol: 'circle-open', size: s, color: c, line: { width: 3, color: c } } };
}
function bracketTrace() {
  if (!ui.br) return [];
  const x = [], y = [], z = [], c = [], s = [], t = [], cd = [];
  D.brackets.forEach((b, i) => {
    const p = bracketPos(i), v = bracketSF(i), k = binOf(v, D.targets.joint), ls = legsOf(i);
    x.push(p[0]); y.push(p[1]); z.push(p[2]);
    c.push(sel.kind === 'bracket' && sel.id === i ? C.sel : [C.crit, C.serious, C.safe_joint][k]);
    s.push(sel.kind === 'bracket' && sel.id === i ? 9 : 5);
    t.push(`<b>${b.label}</b> ${b.type} · M${b.a}–M${b.b}<br>SF <b>${sfTxt(v)}</b>` +
      ls.map(l => `<br>leg ${l.leg} on M${l.member}: SF ${sfTxt(l.SF)} · ${l.gov}`).join(''));
    cd.push(['b', i]);
  });
  return [{ type: 'scatter3d', mode: 'markers', x, y, z, hovertext: t, hoverinfo: 'text', customdata: cd,
    name: 'bracket', marker: { symbol: 'diamond', size: s, color: c, line: { width: 0.5, color: '#fff' } } }];
}
function thrustTrace() {
  const a = D.thrust.at;
  return [{ type: 'scatter3d', mode: 'lines', x: [a[0], a[0]], y: [a[1], a[1]], z: [a[2], a[2] + 0.12 * D.span],
      line: { color: C.ink, width: 4 }, hoverinfo: 'skip', showlegend: false },
    cone([[a[0], a[1], a[2] + 0.12 * D.span]], [[0, 0, 1]], C.ink, 0.025 * D.span, `thrust ${fmt(D.thrust.N, 0)} N (factored)`)];
}
function cone(pts, dirs, color, size, hover) {
  return { type: 'cone', x: pts.map(p => p[0]), y: pts.map(p => p[1]), z: pts.map(p => p[2]),
    u: dirs.map(d => d[0] * size), v: dirs.map(d => d[1] * size), w: dirs.map(d => d[2] * size),
    sizemode: 'absolute', sizeref: 1, anchor: 'tip', showscale: false, colorscale: [[0, color], [1, color]],
    hovertext: hover, hoverinfo: hover ? 'text' : 'skip', showlegend: false, lighting: { ambient: 0.9 } };
}

// free-body diagram of the selected bracket
function fbdTraces() {
  if (sel.kind !== 'bracket') return [];
  const i = sel.id, b = D.brackets[i], ls = legsOf(i), out = [];
  const L = 0.035 * D.span, head = 0.004 * D.span;
  let Fref = 0, Mref = 0;
  for (const l of ls) for (let c = 0; c < 3; c++) { Fref = Math.max(Fref, Math.abs(l.F[c] || 0)); Mref = Math.max(Mref, Math.abs(l.M[c] || 0)); }
  // bracket body: corner -> each bolt point, bolts
  for (const l of ls) {
    const g = legGeom(i, l); if (!g) continue;
    out.push({ type: 'scatter3d', mode: 'lines', x: [b.X[0], g.P[0]], y: [b.X[1], g.P[1]], z: [b.X[2], g.P[2]],
      line: { color: C.ink2, width: 9 }, hoverinfo: 'skip', showlegend: false });
    const bolts = g.bolts || [g.P];
    out.push({ type: 'scatter3d', mode: 'markers', x: bolts.map(q => q[0]), y: bolts.map(q => q[1]), z: bolts.map(q => q[2]),
      marker: { size: 4, color: C.ink, symbol: 'circle' }, hovertext: `leg ${l.leg} bolt${bolts.length > 1 ? 's' : ''} on M${l.member}`,
      hoverinfo: 'text', showlegend: false });
  }
  out.push({ type: 'scatter3d', mode: 'markers', x: [b.X[0]], y: [b.X[1]], z: [b.X[2]], hovertext: `${b.label} corner X`,
    hoverinfo: 'text', marker: { size: 4, color: C.sel, symbol: 'square' }, showlegend: false });
  const tx = [], ty = [], tz = [], tt = [], tc = [];
  const cones = [[], [], []].map(() => ({ p: [], d: [], h: [] }));
  for (const l of ls) {
    const g = legGeom(i, l); if (!g) continue;
    for (const kind of ['F', 'M']) {
      if ((kind === 'F' && !ui.F) || (kind === 'M' && !ui.M)) continue;
      const ref = kind === 'F' ? Fref : Mref, unit = kind === 'F' ? 'N' : 'N·m';
      for (let c = 0; c < 3; c++) {
        const v = l[kind][c]; if (!fin(v) || ref <= 0 || Math.abs(v) < 0.03 * ref) continue;
        const len = Math.max(L * Math.abs(v) / ref, 2.2 * head), dir = g.frame[c].map(q => q * Math.sign(v));
        const tip = add(g.P, dir, len);
        const hov = `leg ${l.leg} on M${l.member}: ${kind}${AX[c]} = ${fmt(v)} ${unit}`;
        out.push({ type: 'scatter3d', mode: 'lines', x: [g.P[0], tip[0]], y: [g.P[1], tip[1]], z: [g.P[2], tip[2]],
          line: { color: C.ax[c], width: kind === 'F' ? 7 : 6, dash: kind === 'F' ? 'solid' : 'dash' },
          hovertext: [hov, hov], hoverinfo: 'text', showlegend: false });
        cones[c].p.push(tip); cones[c].d.push(dir); cones[c].h.push(hov);
        if (kind === 'M') { const t2 = add(tip, dir, -1.6 * head); cones[c].p.push(t2); cones[c].d.push(dir); cones[c].h.push(hov); }
        if (Math.abs(v) < 0.1 * ref) continue;
        const lp = add(tip, dir, 1.5 * head);
        tx.push(lp[0]); ty.push(lp[1]); tz.push(lp[2]); tt.push(`${kind}${AX[c]}${l.leg} ${fmt(v)}`); tc.push(C.ax[c]);
      }
    }
  }
  cones.forEach((q, c) => { if (q.p.length) out.push(cone(q.p, q.d, C.ax[c], head, q.h)); });
  if (tt.length) out.push({ type: 'scatter3d', mode: 'text', x: tx, y: ty, z: tz, text: tt, hoverinfo: 'skip',
    textfont: { size: 11, color: tc }, showlegend: false });
  return out;
}
function bearingTraces() {
  if (sel.kind !== 'joint') return [];
  const j = D.joints.find(q => q.id === sel.id); if (!j) return [];
  return j.be.map(k => {
    const be = D.bearings[k], f = S.bearing[k];
    return { type: 'scatter3d', mode: 'markers', x: [be.X[0]], y: [be.X[1]], z: [be.X[2]],
      marker: { size: 7, symbol: 'square', color: f[1] ? C.ax[0] : C.muted },
      hovertext: `${be.label}: ${f[1] ? fmt(f[0], 0) + ' N compression' : 'open'}`, hoverinfo: 'text', showlegend: false };
  });
}

// ------------------------------------------------------------------ inspector
function sfSpan(v, t) { return `<span class="${sfClass(v, t)}">${sfTxt(v)}</span>`; }
function legTable(l, b) {
  const rows = l.items.map(([lab, v, u, cap, U]) => {
    const share = fin(U) && fin(l.U) && l.U > 0 ? (100 * U / l.U).toFixed(0) + ' %' : '';
    const alone = fin(U) ? (U > 0 ? sfSpan(1 / U, D.targets.joint) : '∞') : '';
    const gov = fin(U) && fin(l.U) && l.U > 0 && Math.abs(U - Math.max(...l.items.map(q => fin(q[4]) ? q[4] : -1))) < 1e-12;
    return `<tr class="${fin(cap) ? 'chk' : 'sub'}${gov ? ' gov' : ''}"><td>${esc(lab)}</td><td class="num">${fmt(v)} ${u}</td>` +
      `<td class="num">${fin(cap) ? fmt(cap) + ' ' + u : ''}</td><td class="num">${share}</td><td class="num">${alone}</td></tr>`;
  }).join('');
  return `<table><thead><tr><th>component / check</th><th class="num">value</th><th class="num">capacity</th>` +
    `<th class="num">share of U</th><th class="num">SF alone</th></tr></thead><tbody>${rows}</tbody></table>`;
}
function showBracket(i) {
  const b = D.brackets[i], ls = legsOf(i), v = bracketSF(i);
  const j = D.joints.find(q => q.id === b.joint);
  let h = `<h3>${b.label} · ${b.type}${b.copy ? ' (copy ' + (b.copy + 1) + ')' : ''} — SF ${sfSpan(v, D.targets.joint)}</h3>` +
    `<div class="k">joint <button class="lnk" data-joint="${b.joint}">${b.joint}</button> · legs a on M${b.a}, b on M${b.b} · face ${b.face}` +
    `${b.note ? ' · ' + esc(b.note) : ''}</div>`;
  h += `<div class="key"><span><span class="sw" style="border-color:${C.ax[0]}"></span>x slot</span>` +
    `<span><span class="sw" style="border-color:${C.ax[1]}"></span>y across</span>` +
    `<span><span class="sw" style="border-color:${C.ax[2]}"></span>z bolt axis (+ pull-off)</span>` +
    `<span><span class="sw"></span>force</span><span><span class="sw d"></span>moment (double head)</span></div>`;
  h += `<div class="k">Wrench acting on each leg's member, about the bolt point (plates: group centroid), in that leg's frame. ` +
    `Legs act in series: bracket SF = min over legs. U = Σ term utilisations (linear interaction), SF = 1/U.</div>`;
  for (const l of ls) {
    const g = legGeom(i, l);
    const off = g ? norm(sub(g.P, b.X)).toFixed(1) : '?';
    h += `<h4>leg ${l.leg} on M${l.member} — SF <span class="legsf ${sfClass(l.SF, D.targets.joint)}">${sfTxt(l.SF)}</span>` +
      ` <span class="k">U ${fin(l.U) ? l.U.toFixed(2) : '–'} · governs ${esc(l.gov || '–')}</span></h4>` +
      `<div class="k">${esc(l.src)} · corner option ${esc(l.opt)} · bolt point ${off} mm from corner X` +
      `${g && g.bolts ? ' · ' + g.bolts.length + ' bolts' : ''}</div>` + legTable(l, b);
  }
  if (!ls.length) h += '<p class="k">no result rows for this bracket</p>';
  if (S.key === 'envelope') h += `<p class="k">Envelope: each leg shows the solve that governs it, so legs can come from different solves.</p>`;
  insp.innerHTML = h;
}
function showJoint(id) {
  const j = D.joints.find(q => q.id === id);
  let h = `<h3>Joint ${j.id}</h3><div class="k">members ${j.members.map(m => `<button class="lnk" data-member="${m}">M${m}</button>`).join(' ')}` +
    ` · at (${j.at.map(q => q.toFixed(0)).join(', ')}) mm</div><h4>Brackets</h4>`;
  h += `<table><thead><tr><th>bracket</th><th>type</th><th>legs</th><th class="num">SF</th><th>governs</th><th>run/case</th></tr></thead><tbody>`;
  for (const i of j.br) {
    const b = D.brackets[i], ls = legsOf(i), v = bracketSF(i);
    const w = ls.reduce((a, l) => (!a || (fin(l.SF) && l.SF < a.SF)) ? l : a, null);
    h += `<tr class="pick" data-spring="${i}"><td>${b.label}</td><td>${b.type}</td><td>a M${b.a} · b M${b.b}</td>` +
      `<td class="num">${sfSpan(v, D.targets.joint)}</td><td>${w ? esc(w.leg + ': ' + w.gov) : ''}</td><td class="muted">${w ? esc(w.src) : ''}</td></tr>`;
  }
  h += `</tbody></table>`;
  if (j.be.length) {
    h += `<h4>Bearing (compression-only, along the bearing member's axis)</h4><table><thead><tr><th>contact</th>` +
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
  insp.innerHTML = `<h3>Inspector</h3><p class="k">Click a bracket (diamond) for its free-body diagram, a joint (ring) for its brackets ` +
    `and bearing forces, or a member for its checks. The state menu switches between the design envelope and any single run/case.</p>` +
    `<p class="k">${D.brackets.length} bracket springs · ${D.joints.length} joints · ${D.members.length} members · ${D.bearings.length} bearing contacts.</p>`;
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
  const tr = [...memberTraces(), ...deformedTrace(), ...thrustTrace(), jointTrace(), ...bracketTrace(),
    ...bearingTraces(), ...fbdTraces()];
  Plotly.react(plot, tr, layout, { displaylogo: false, responsive: true,
    toImageButtonOptions: { format: 'png', scale: 3, filename: 'stand' } });
}
// scene normalised coordinates of a data point (aspectmode manual: box spans ±ar/2)
function toScene(p) { return { x: ((p[0] - rng[0][0]) / span[0] - 0.5) * ar[0], y: ((p[1] - rng[1][0]) / span[1] - 0.5) * ar[1], z: ((p[2] - rng[2][0]) / span[2] - 0.5) * ar[2] }; }
function focusPoint() {
  if (sel.kind === 'bracket') return D.brackets[sel.id].X;
  if (sel.kind === 'joint') return D.joints.find(q => q.id === sel.id).at;
  if (sel.kind === 'member') { const m = D.members.find(q => q.id === sel.id); return X[m.nodes[Math.floor(m.nodes.length / 2)]]; }
  return null;
}
function focus() {
  const p = focusPoint(); if (!p) return;
  const f = sel.kind === 'bracket' ? 10 : 2.5, c0 = toScene(p), c = { x: c0.x * f, y: c0.y * f, z: c0.z * f };
  const cam = plot._fullLayout.scene.camera, e = cam.eye, o = cam.center;
  const d = [e.x - o.x, e.y - o.y, e.z - o.z], n = norm(d) || 1;
  Plotly.relayout(plot, { 'scene.aspectratio': { x: ar[0] * f, y: ar[1] * f, z: ar[2] * f },
    'scene.camera': { center: c, eye: { x: c.x + d[0] * 1.8 / n, y: c.y + d[1] * 1.8 / n, z: c.z + d[2] * 1.8 / n },
      up: cam.up, projection: { type: 'orthographic' } } });
}
// ------------------------------------------------------------------ wiring
function select(kind, id) { sel.kind = kind; sel.id = id; render(); inspect(); }
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
for (const [id, key] of [['deformed', 'deformed'], ['showF', 'F'], ['showM', 'M'], ['showBr', 'br']])
  document.getElementById(id).addEventListener('change', e => { ui[key] = e.target.checked; render(); });
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
  const t = e.target.closest('[data-spring],[data-joint],[data-member]'); if (!t) return;
  if (t.dataset.spring !== undefined) select('bracket', +t.dataset.spring);
  else if (t.dataset.joint !== undefined) select('joint', t.dataset.joint);
  else select('member', +t.dataset.member);
  if (t.closest('.grid')) { plot.scrollIntoView({ behavior: 'smooth', block: 'center' }); focus(); }
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
