import json, numpy as np
inst = json.load(open("instances.json"))
G = np.eye(3)
def snap(v):
    k = np.argmax(np.abs(v)); 
    return (np.sign(v[k]) * G[k]) if abs(v[k]) > 0.999 else v / np.linalg.norm(v)
mem = []
for k, o in enumerate(inst):
    P = np.array(o["pts"]) * 1e3
    c = P.mean(0)
    _, _, Vt = np.linalg.svd(P - c, full_matrices=False)
    pr = (P - c) @ Vt.T; ext = np.ptp(pr, 0); order = np.argsort(-ext)
    e = snap(Vt[order[0]]); e = e * (1 if e[np.argmax(np.abs(e))] > 0 else -1)
    # cross axes: global axes perpendicular to e if possible
    cand = [g for g in G if abs(g @ e) < 1e-3]
    u = cand[0] if cand else snap(Vt[order[1]])
    v = np.cross(e, u)
    s = (P - c) @ e; a = (P - c) @ u; b = (P - c) @ v
    mid = c + e * (s.min() + s.max()) / 2 + u * (a.min() + a.max()) / 2 + v * (b.min() + b.max()) / 2
    L = np.ptp(s); wu, wv = np.ptp(a), np.ptp(b)
    if k == 8: kind = "plate"
    else: kind = "extrusion"
    mem.append(dict(i=k, P=P, c=mid, e=e, u=u, v=v, L=L, wu=wu, wv=wv, kind=kind))
def nom(w): return 40 if w < 60 else 80
for m in mem:
    if m["kind"] == "extrusion":
        # diagonal braces: mitred ends inflate the in-plane width; snap to 40/80
        m["wu"], m["wv"] = nom(m["wu"]), nom(m["wv"])
        m["profile"] = {(40, 40): "4040", (40, 80): "4080", (80, 40): "4080", (80, 80): "8080"}[(m["wu"], m["wv"])]
    else:
        m["profile"] = "plate"
def sdist_box(Pts, m):
    d = Pts - m["c"]
    q = np.c_[d @ m["e"], d @ m["u"], d @ m["v"]]
    h = np.array([m["L"] / 2, m["wu"] / 2, m["wv"] / 2])
    out = np.maximum(np.abs(q) - h, 0)
    return np.linalg.norm(out, axis=1), q
tol = 1.5
pairs = []
for i in range(len(mem)):
    for j in range(i + 1, len(mem)):
        A, B = mem[i], mem[j]
        dA, _ = sdist_box(A["P"], B); dB, _ = sdist_box(B["P"], A)
        ta, tb = A["P"][dA <= tol], B["P"][dB <= tol]
        if len(ta) + len(tb) == 0: continue
        pts = np.vstack([ta, tb]); cpt = pts.mean(0)
        def where(m, pts):
            s = (pts - m["c"]) @ m["e"]; h = m["L"] / 2; ww = max(m["wu"], m["wv"])
            lo, hi = s.min(), s.max()
            if hi > h - ww - 1 and lo > h - 2 * ww: return "end1"
            if lo < -h + ww + 1 and hi < -h + 2 * ww: return "end0"
            return f"side@{(lo + hi) / 2 + h:.0f}"
        pairs.append(dict(a=i, b=j, at=cpt.round(1).tolist(), wa=where(A, pts), wb=where(B, pts), n=len(pts)))
for m in mem:
    p0 = m["c"] - m["e"] * m["L"] / 2; p1 = m["c"] + m["e"] * m["L"] / 2
    print(f"M{m['i']:2d} {m['profile']:6s} L={m['L']:7.1f}  p0={p0.round(1)}  p1={p1.round(1)}  depth_u={m['wu']:.0f} along {m['u'].round(3)}")
print()
for p in pairs: print(f"M{p['a']:2d}-M{p['b']:2d}  at {p['at']}  {p['wa']:10s} {p['wb']:10s} n={p['n']}")
json.dump(dict(members=[{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in m.items() if k != "P"} for m in mem],
               pairs=pairs), open("contacts.json", "w"), indent=1)
