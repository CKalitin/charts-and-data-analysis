import json, numpy as np
exec(open("contacts.py").read().split("tol = 1.5")[0])
tol = 1.0
def aabb(m):
    h = np.abs(m["e"]) * m["L"] / 2 + np.abs(m["u"]) * m["wu"] / 2 + np.abs(m["v"]) * m["wv"] / 2
    return m["c"] - h, m["c"] + h
aligned = lambda m: np.isclose(np.abs(m["e"]).max(), 1)
pairs = []
for i in range(len(mem)):
    for j in range(i + 1, len(mem)):
        A, B = mem[i], mem[j]
        if aligned(A) and aligned(B):
            a0, a1 = aabb(A); b0, b1 = aabb(B)
            lo, hi = np.maximum(a0, b0), np.minimum(a1, b1)
            if (hi - lo < -tol).any(): continue
            reg = np.vstack([lo, hi])
        else:
            dA, _ = sdist_box(A["P"], B); dB, _ = sdist_box(B["P"], A)
            pts = np.vstack([A["P"][dA <= 1.5], B["P"][dB <= 1.5]])
            if not len(pts): continue
            reg = np.vstack([pts.min(0), pts.max(0)])
        cpt = reg.mean(0)
        def where(m):
            s = (reg - m["c"]) @ m["e"]; lo_, hi_ = s.min(), s.max(); h = m["L"] / 2; w = max(m["wu"], m["wv"])
            e1, e0 = hi_ >= h - 1 and lo_ > h - 2 * w - 1, lo_ <= -h + 1 and hi_ < -h + 2 * w + 1
            if e1: return "end1"
            if e0: return "end0"
            return f"side@{(lo_ + hi_) / 2 + h:.0f}"
        pairs.append(dict(a=i, b=j, at=cpt.round(1).tolist(), wa=where(A), wb=where(B)))
for p in pairs: print(f"M{p['a']:2d}-M{p['b']:2d}  at {p['at']}  {p['wa']:10s} {p['wb']:10s}")
json.dump(dict(members=[{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in m.items() if k != "P"} for m in mem],
               pairs=pairs), open("contacts.json", "w"), indent=1)
