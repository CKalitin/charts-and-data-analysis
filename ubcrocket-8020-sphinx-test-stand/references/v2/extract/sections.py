import re, json, numpy as np
exec(open("parse.py").read().split("# brep vertex clouds")[0].replace("sys.argv[1]", "'a.step'"))
def loop_pts(loop):
    """Ordered vertex coords of an EDGE_LOOP (straight edges)."""
    pts = []
    for oe in refs(ents[loop]):
        r = refs(ents[oe]); ec = r[-1]; s = ents[oe]
        fwd = s.strip().endswith(".T.)")
        v = refs(ents[ec])[:2]
        a, b = (v[0], v[1]) if fwd else (v[1], v[0])
        pts.append(point(refs(ents[a])[0]))
    return np.array(pts)
def poly_props(P):   # P (n,2) closed polygon, signed
    x, y = P[:, 0], P[:, 1]; x1, y1 = np.roll(x, -1), np.roll(y, -1); c = x * y1 - x1 * y
    A = c.sum() / 2; Cx = ((x + x1) * c).sum() / (6 * A); Cy = ((y + y1) * c).sum() / (6 * A)
    Ixx = ((y**2 + y * y1 + y1**2) * c).sum() / 12; Iyy = ((x**2 + x * x1 + x1**2) * c).sum() / 12
    return A, A * Cx, A * Cy, Ixx, Iyy
breps = sorted(i for i, s in ents.items() if s.startswith("MANIFOLD_SOLID_BREP"))
res = {}
for b in breps:
    shell = refs(ents[b])[0]
    faces = refs(ents[shell])
    best = None
    for f in faces:
        s = ents[f]
        if not s.startswith("ADVANCED_FACE"): continue
        r = refs(s); surf = r[-1]
        if not ents[surf].startswith("PLANE"): continue
        o, R = axis(refs(ents[surf])[0])
        bounds = r[:-1]
        loops = [loop_pts(refs(ents[fb])[0]) for fb in bounds]
        n = sum(len(l) for l in loops)
        if best is None or n > best[0]: best = (n, o, R, loops)   # end face = the face with most vertices
    n, o, R, loops = best
    A = Sx = Sy = Ixx = Iyy = 0.0
    for L in loops:
        q = (L - o) @ R[:, :2]                       # in-plane coords (m)
        a, sx, sy, ixx, iyy = poly_props(q)
        # outer loop positive, holes negative: force sign by area magnitude ordering later
        A += a; Sx += sx; Sy += sy; Ixx += ixx; Iyy += iyy
    if A < 0: A, Sx, Sy, Ixx, Iyy = -A, -Sx, -Sy, -Ixx, -Iyy
    cx, cy = Sx / A, Sy / A
    Ixc, Iyc = Ixx - A * cy**2, Iyy - A * cx**2
    allq = np.vstack([(L - o) @ R[:, :2] for L in loops])
    w = np.ptp(allq, 0)
    res[b] = dict(loops=len(loops), nverts=n, A_mm2=A * 1e6, Ix_cm4=Ixc * 1e8, Iy_cm4=Iyc * 1e8,
                  bbox_mm=(w * 1e3).round(2).tolist())
for b, r in res.items():
    print(b, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
json.dump(res, open("sections.json", "w"), indent=1)
