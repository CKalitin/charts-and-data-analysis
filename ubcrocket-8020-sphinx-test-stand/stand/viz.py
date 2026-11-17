"""Interactive viewer: results/stand.html (plotly 3D + stat strip + lowest-SF tables).

One dropdown picks what is shown (design envelope, any run/case, the buckling
mode); camera buttons give iso / front / side / top orthographic views for clean
screenshots.  Colours match figures.py (status colours by exception).
"""
from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
import plotly.graph_objects as go

from .analysis import Solve, Study
from .envelope import Envelope
from .charts._render import CRIT, HAIR, INK, INK2, MUTED, SAFE_JOINT, SAFE_MEMBER, SERIOUS, TERM_LABEL, bracket_name, deform_scale

BIN_NAMES = ["SF < 1", "1 ≤ SF < target", "SF ≥ target"]
BIN_COLORS = [CRIT, SERIOUS, SAFE_MEMBER]


def _bin(sf, target):
    if not np.isfinite(sf):
        return 2
    return 0 if sf < 1 else 1 if sf < target else 2


def _member_rows_for(s: Solve | None, env: Envelope, study: Study):
    if s is None:
        return {int(r["id"][1:]): (r["SF"], r["gov_check"], r["sigma_MPa"], r["N_N"], r["My_Nm"], r["Mz_Nm"],
                                   f"{r['gov_run']}/{r['gov_case']}") for r in env.members}
    out = {}
    for mid, r in s.member_rows.items():
        out[mid] = (r["SF"], r["gov_check"], r["sigma"] / 1e6, r["N"], r["My"], r["Mz"], s.key)
    return out


def _joint_rows_for(s: Solve | None, env: Envelope):
    rows = env.joints if s is None else [
        {**r, "member": f"M{r['member']}", "gov_run": s.run.label, "gov_case": s.case} for r in s.joint_rows]
    out = {}
    for r in rows:
        if not np.isfinite(r["SF"]):
            continue
        if r["joint"] not in out or r["SF"] < out[r["joint"]]["SF"]:
            out[r["joint"]] = r
    return out


def _traces(study: Study, env: Envelope, p, s: Solve | None, scale: float, shape: np.ndarray | None,
            name: str) -> list[go.Scatter3d]:
    m = study.model
    tm, tj = p.si.checks.SF_target_member, p.si.checks.SF_target_joint
    mrows = _member_rows_for(s, env, study)
    disp = None
    if shape is not None:
        disp = shape.reshape(-1, 6)[:, :3]
    traces = []
    for b in range(3):
        X, Y, Z, T = [], [], [], []
        for mid, ns in m.member_nodes.items():
            sf, gov, sig, N, My, Mz, where = mrows[mid]
            if _bin(sf, tm) != b:
                continue
            P = m.x[ns] * 1e3
            if disp is not None:
                P = P + scale * disp[ns] * 1e3
            txt = (f"<b>M{mid}</b> · {m.members[mid].profile}<br>SF <b>{sf:.2f}</b> ({gov})<br>"
                   f"σ {sig:.1f} MPa · N {N:.0f} N<br>My {My:.1f} · Mz {Mz:.1f} N·m<br>{where}")
            X += list(P[:, 0]) + [None]
            Y += list(P[:, 1]) + [None]
            Z += list(P[:, 2]) + [None]
            T += [txt] * len(ns) + [None]
        traces.append(go.Scatter3d(
            x=X, y=Y, z=Z, mode="lines", name=BIN_NAMES[b].replace("target", f"{tm:g}"),
            line=dict(color=BIN_COLORS[b], width=7 if b < 2 else 5), hovertext=T, hoverinfo="text",
            legendgroup=f"b{b}", showlegend=(name == "envelope")))
    jrows = _joint_rows_for(s, env)
    jx, jy, jz, jc, jt, js = [], [], [], [], [], []
    for jt_ in m.joints:
        r = jrows.get(jt_.id)
        if r is None:
            continue
        P = jt_.at * 1e3
        if disp is not None:
            nds = [n for (jid, _), n in m.joint_node.items() if jid == jt_.id]
            P = P + scale * disp[nds].mean(0) * 1e3
        b = _bin(r["SF"], tj)
        jx.append(P[0]); jy.append(P[1]); jz.append(P[2])
        jc.append([CRIT, SERIOUS, SAFE_JOINT][b])
        js.append(10 if b < 2 else 5)
        jt.append(f"<b>{jt_.id}</b> · worst bracket SF <b>{r['SF']:.2f}</b><br>"
                  f"{r['type']}: {bracket_name(r).split(' ', 1)[1]}<br>"
                  f"governs: {TERM_LABEL.get(r['gov_term'], r['gov_term'])} ({100 * r[r['gov_term']] / r['U']:.0f} % of demand)<br>"
                  f"F ({r.get('Fx_N', r.get('Fx')):.0f}, {r.get('Fy_N', r.get('Fy')):.0f}, {r.get('Fz_N', r.get('Fz')):.0f}) N leg frame<br>"
                  f"{r['gov_run']}/{r['gov_case']}")
    traces.append(go.Scatter3d(x=jx, y=jy, z=jz, mode="markers", name="joints (worst bracket)",
                               marker=dict(color=jc, size=js, line=dict(color="white", width=1.5)),
                               hovertext=jt, hoverinfo="text", showlegend=(name == "envelope")))
    return traces


def build_figure(study: Study, env: Envelope, p) -> tuple[go.Figure, list[str]]:
    m = study.model
    scale = deform_scale(study, p)
    fig = go.Figure()
    # undeformed ghost (always on)
    X, Y, Z = [], [], []
    for ns in m.member_nodes.values():
        P = m.x[ns] * 1e3
        X += list(P[:, 0]) + [None]
        Y += list(P[:, 1]) + [None]
        Z += list(P[:, 2]) + [None]
    fig.add_trace(go.Scatter3d(x=X, y=Y, z=Z, mode="lines", line=dict(color=HAIR, width=3),
                               hoverinfo="skip", name="undeformed", showlegend=False))
    tp = m.thrust_point * 1e3
    fig.add_trace(go.Cone(x=[tp[0]], y=[tp[1]], z=[tp[2] + 120], u=[0], v=[0], w=[1], sizemode="absolute",
                          sizeref=90, anchor="tail", colorscale=[[0, INK], [1, INK]], showscale=False,
                          hovertext=f"thrust {study.solves[0].loads.summary['thrust_factored_N']:.0f} N (factored)",
                          hoverinfo="text", name="thrust"))
    states = [("envelope", "Design envelope (worst of all valid runs)", None, None)]
    lim = p.si.checks.mechanism_disp
    for s in study.solves:
        tag = "" if s.valid else "  — mechanism, invalid"
        states.append((s.key, f"{s.key}{tag}", s, s.ur if s.valid else None))
    lam_s = next((s for s in study.solves if s.key == env.lam[1]), None)
    if lam_s is not None and lam_s.phi is not None:
        from .model import relative_to_base
        phi = relative_to_base(m, lam_s.phi)
        amp = np.abs(phi.reshape(-1, 6)[:, :3]).max()
        states.append(("buckle", f"Buckling mode λ = {lam_s.lam:.1f} ({lam_s.key})", lam_s,
                       phi / amp * (0.08 * np.ptp(m.x[:, 2])) / max(scale, 1e-12)))
    n_fixed = len(fig.data)
    per = None
    titles = []
    for k, (key, title, s, shape) in enumerate(states):
        tr = _traces(study, env, p, s, scale, shape, key)
        per = len(tr)
        for t in tr:
            t.visible = (k == 0)
            fig.add_trace(t)
        sub = ""
        if s is not None and shape is not None and key != "buckle":
            sub = f" · deformed × {scale:.0f} · thrust δ {np.linalg.norm(s.thrust_disp) * 1e3:.2f} mm, tilt {s.thrust_tilt_deg:.2f}°"
        elif key == "buckle":
            sub = " · mode shape (arbitrary amplitude)"
        titles.append(title + sub)
    buttons = []
    for k, (key, title, s, shape) in enumerate(states):
        vis = [True] * n_fixed + [False] * (per * len(states))
        for i in range(per):
            vis[n_fixed + k * per + i] = True
        buttons.append(dict(label=title.split("  —")[0] if len(title) < 60 else title[:60],
                            method="update", args=[{"visible": vis}, {"title.text": titles[k]}]))
    span = np.ptp(m.x, axis=0)
    cams = {
        "iso": dict(eye=dict(x=1.6, y=-1.6, z=0.9), up=dict(x=0, y=0, z=1)),
        "front": dict(eye=dict(x=0, y=-2.5, z=0), up=dict(x=0, y=0, z=1)),
        "side": dict(eye=dict(x=2.5, y=0, z=0), up=dict(x=0, y=0, z=1)),
        "top": dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0)),
    }
    cam_buttons = [dict(label=k, method="relayout",
                        args=[{"scene.camera": {**v, "projection": {"type": "orthographic"}}}])
                   for k, v in cams.items()]
    axis = dict(showbackground=False, showgrid=False, zeroline=False, showspikes=False,
                tickfont=dict(size=10, color=MUTED), title=dict(font=dict(size=11, color=INK2)),
                linecolor=HAIR, ticks="")
    fig.update_layout(
        template="none", paper_bgcolor="white", plot_bgcolor="white", height=760,
        margin=dict(l=0, r=0, t=46, b=0),
        title=dict(text=titles[0], x=0.01, y=0.985, font=dict(size=14, color=INK)),
        font=dict(family="Inter, DejaVu Sans, system-ui, sans-serif", color=INK),
        legend=dict(x=0.01, y=0.04, bgcolor="rgba(255,255,255,0.8)", font=dict(size=11)),
        scene=dict(aspectmode="data", xaxis={**axis, "title": {"text": "x (mm)"}},
                   yaxis={**axis, "title": {"text": "y (mm)"}}, zaxis={**axis, "title": {"text": "z (mm)"}},
                   camera={**cams["iso"], "projection": {"type": "orthographic"}}),
        updatemenus=[
            dict(type="dropdown", buttons=buttons, x=0.99, xanchor="right", y=0.995, yanchor="top",
                 bgcolor="white", bordercolor=HAIR, font=dict(size=11), showactive=True),
            dict(type="buttons", direction="right", buttons=cam_buttons, x=0.99, xanchor="right", y=0.93,
                 yanchor="top", bgcolor="white", bordercolor=HAIR, font=dict(size=11), showactive=True),
        ],
    )
    return fig, titles


def _table(rows, cols) -> str:
    head = "".join(f"<th>{html.escape(c)}</th>" for c, _ in cols)
    body = []
    for r in rows:
        tds = []
        for _, f in cols:
            v, cls = f(r)
            tds.append(f'<td class="{cls}">{v}</td>')
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _sfcell(sf, target):
    if not np.isfinite(sf):
        return "–", "num"
    cls = "crit" if sf < 1 else "warn" if sf < target else "ok"
    return f"{sf:.2f}", f"num {cls}"


def write_html(study: Study, env: Envelope, p, path: Path) -> Path:
    fig, _ = build_figure(study, env, p)
    si = p.si
    tm, tj = si.checks.SF_target_member, si.checks.SF_target_joint
    n = int(si.output.n_lowest)
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
    jt = _table([r for r in env.joints if np.isfinite(r["SF"])][:n], [
        ("SF", lambda r: _sfcell(r["SF"], tj)), ("joint", lambda r: (r["joint"], "")),
        ("bracket", lambda r: (f"{r['bracket']}{' copy ' + str(r['copy'] + 1) if r['copy'] else ''} {r['type']}", "")),
        ("leg", lambda r: (f"{r['leg']} on {r['member']}", "")),
        ("governs", lambda r: (TERM_LABEL.get(r["gov_term"], ""), "")),
        ("share", lambda r: (f"{100 * r[r['gov_term']] / r['U']:.0f} %", "num")),
        ("run/case", lambda r: (f"{r['gov_run']}/{r['gov_case']}", "muted"))])
    mt = _table(env.members[:n], [
        ("SF", lambda r: _sfcell(r["SF"], tm)), ("member", lambda r: (f"{r['id']} {r['profile']}", "")),
        ("governs", lambda r: (r["gov_check"], "")), ("σ MPa", lambda r: (f"{r['sigma_MPa']:.1f}", "num")),
        ("N", lambda r: (f"{r['N_N']:.0f}", "num")), ("Mz N·m", lambda r: (f"{r['Mz_Nm']:.1f}", "num")),
        ("run/case", lambda r: (f"{r['gov_run']}/{r['gov_case']}", "muted"))])
    changes = ("".join(f"<li><code>{html.escape(c.key)}</code> {html.escape(str(c.default))} → "
                       f"<b>{html.escape(str(c.value))}</b></li>" for c in p.changes)
               or "<li>all parameters at defaults</li>")
    flags = "".join(f"<li><code>{q.key}</code> = {html.escape(p.display(q.key))} <span class='muted'>[{q.flag}]</span></li>"
                    for f in ("placeholder", "unverified") for q in p.flagged(f))
    notes = "".join(f"<li>{html.escape(x)}</li>" for x in study.model.notes)
    mech = (f"<li>run P invalid (mechanism) for {', '.join(study.mechanism_cases)} → run R used</li>"
            if study.mechanism_cases else "")
    plot = fig.to_html(full_html=False, include_plotlyjs=("cdn" if si.output.plotlyjs == "cdn" else True),
                       config={"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 3,
                                                                               "filename": "stand"}})
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sphinx Stand SF</title>
<style>
:root {{ --ink:{INK}; --ink2:{INK2}; --muted:{MUTED}; --hair:{HAIR}; --crit:{CRIT}; --warn:#b8501f; --ok:#3f3e3a; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#fff; color:var(--ink); font:13px/1.45 Inter, "DejaVu Sans", system-ui, sans-serif; }}
main {{ max-width:1500px; margin:0 auto; padding:14px 16px 40px; }}
h1 {{ font-size:15px; margin:0 0 2px; }} .sub {{ color:var(--muted); font-size:12px; margin-bottom:12px; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:1px; background:var(--hair);
  border:1px solid var(--hair); margin-bottom:8px; }}
.stat {{ background:#fff; padding:8px 12px; }} .stat .k {{ color:var(--ink2); font-size:11px; }}
.stat .v {{ font-size:22px; font-weight:600; font-variant-numeric:tabular-nums; }} .stat .s {{ color:var(--muted); font-size:11px; }}
.crit {{ color:var(--crit); }} .warn {{ color:var(--warn); }} .ok {{ color:var(--ok); }} .muted {{ color:var(--muted); }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); gap:24px; margin-top:12px; }}
h2 {{ font-size:12px; text-transform:none; color:var(--ink2); margin:0 0 6px; font-weight:600; }}
table {{ border-collapse:collapse; width:100%; font-size:12px; }}
th {{ text-align:left; color:var(--muted); font-weight:500; border-bottom:1px solid var(--hair); padding:3px 8px 3px 0; }}
td {{ padding:3px 8px 3px 0; border-bottom:1px solid #f3f2ef; white-space:nowrap; }}
td.num {{ text-align:right; font-variant-numeric:tabular-nums; }} th:first-child, td:first-child {{ width:3.5em; }}
td.num.crit, td.num.warn {{ font-weight:600; }}
ul {{ margin:4px 0 0; padding-left:18px; color:var(--ink2); }} code {{ font-size:11.5px; }}
.help {{ color:var(--muted); font-size:11.5px; margin-top:4px; }}
@media (max-width:600px) {{ .grid {{ grid-template-columns:1fr; }} td {{ white-space:normal; }} }}
</style></head><body><main>
<h1>Mojave Sphinx test stand — safety factors ({study.model.mode.upper()})</h1>
<div class="sub">{html.escape(p.path.name)} · thrust {si.loads.thrust:.0f} N × DF {si.loads.DF:g} · targets: member {tm:g}, joint {tj:g} ·
{len(study.solves)} solves + {len(study.sweep)} sweep</div>
<div class="stats">{stat_html}</div>
{plot}
<div class="help">Dropdown (top right): envelope, any run/case, buckling mode. Buttons: orthographic iso / front / side / top.
Hover a member or joint for numbers. Camera icon in the toolbar saves a 3× PNG. Grey = at or above target.</div>
<div class="grid"><div><h2>Lowest joint SFs</h2>{jt}</div><div><h2>Lowest member SFs</h2>{mt}</div></div>
<div class="grid"><div><h2>Parameters changed from defaults</h2><ul>{changes}</ul>
<h2 style="margin-top:12px">Model notes</h2><ul>{mech}{notes or '<li>none</li>'}</ul></div>
<div><h2>Unverified inputs</h2><ul>{flags}<li><code>plate_other</code> brackets: forces only, no capacity</li></ul></div></div>
</main></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page)
    return path
