import json, numpy as np
inst = json.load(open("instances.json"))
rows = []
for k, o in enumerate(inst):
    P = np.array(o["pts"]) * 1e3          # mm
    c = P.mean(0)
    # principal axes: snap to the box of the cloud along PCA directions
    U, S, Vt = np.linalg.svd(P - c, full_matrices=False)
    ax = Vt
    proj = (P - c) @ ax.T
    lo, hi = proj.min(0), proj.max(0)
    ext = hi - lo
    o_ = np.argsort(-ext)
    e = ax[o_[0]] * np.sign(ax[o_[0]][np.argmax(np.abs(ax[o_[0]]))])
    mid = c + ax.T @ ((lo + hi) / 2)
    L = ext[o_[0]]
    p0, p1 = mid - e * L / 2, mid + e * L / 2
    w = sorted(ext[o_[1:]].round(2))
    rows.append(dict(i=k, brep=o["brep"], nv=len(P), L=round(L, 2), sec=w, dir=e.round(4).tolist(),
                     p0=p0.round(2).tolist(), p1=p1.round(2).tolist(),
                     ax2=ax[o_[1]].round(3).tolist(), ax3=ax[o_[2]].round(3).tolist()))
for r in rows:
    print(f"#{r['i']:2d} brep{r['brep']} nv{r['nv']:4d} L={r['L']:8.2f} sec={r['sec']} dir={r['dir']}\n      p0={r['p0']} p1={r['p1']}  ax2={r['ax2']} ax3={r['ax3']}")
json.dump(rows, open("members.json", "w"), indent=1)
