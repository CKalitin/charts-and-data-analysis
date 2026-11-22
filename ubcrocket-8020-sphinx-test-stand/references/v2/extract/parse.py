import re, sys, json
import numpy as np
txt = open(sys.argv[1]).read()
data = txt[txt.index("DATA;")+5: txt.index("ENDSEC;", txt.index("DATA;"))]
ents = {}
for m in re.finditer(r"#(\d+)\s*=\s*(.*?);\s*(?=#\d+\s*=|$)", data, re.S):
    ents[int(m.group(1))] = " ".join(m.group(2).split())
refs = lambda s: [int(x) for x in re.findall(r"#(\d+)", s)]
def nums(s): return [float(x) for x in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)]
def point(i):
    s = ents[i]; return np.array(nums(s[s.index("("):])[-3:])
def direction(i):
    s = ents[i]; return np.array(nums(s[s.index(",")+1:])[-3:])
def axis(i):
    r = refs(ents[i]); o = point(r[0]); z = direction(r[1]); x = direction(r[2])
    z /= np.linalg.norm(z); x = x - (x@z)*z; x /= np.linalg.norm(x); y = np.cross(z, x)
    return o, np.vstack([x, y, z]).T     # columns = local axes in parent
# brep vertex clouds: collect VERTEX_POINT reachable from each MANIFOLD_SOLID_BREP
def reach(i, seen):
    stack=[i]
    while stack:
        k=stack.pop()
        if k in seen: continue
        seen.add(k); stack += refs(ents[k])
breps = {i for i,s in ents.items() if s.startswith("MANIFOLD_SOLID_BREP")}
cloud = {}
for b in breps:
    seen=set(); reach(b, seen)
    cloud[b] = np.array([point(refs(ents[k])[0]) for k in seen if ents[k].startswith("VERTEX_POINT")])
# part shape rep -> brep  (SRR(partrep, advbrep))
adv = {i: refs(s)[0] for i,s in ents.items() if s.startswith("ADVANCED_BREP_SHAPE_REPRESENTATION")}
rep2brep = {}
for i,s in ents.items():
    if s.startswith("SHAPE_REPRESENTATION_RELATIONSHIP("):
        r = refs(s)
        if r[1] in adv: rep2brep[r[0]] = adv[r[1]]
out = []
for i,s in ents.items():
    if s.startswith("( REPRESENTATION_RELATIONSHIP") or s.startswith("(REPRESENTATION_RELATIONSHIP"):
        r = refs(s); child, parent, tr = r[0], r[1], r[2]
        idt = refs(ents[tr]); o1,R1 = axis(idt[0]); o2,R2 = axis(idt[1])
        P = cloud[rep2brep[child]]
        # child local -> parent: p = o2 + R2 (R1^T (p - o1))
        W = o2 + (R2 @ (R1.T @ (P - o1).T)).T
        out.append({"rel": i, "brep": rep2brep[child], "pts": W.tolist()})
json.dump(out, open("instances.json","w"))
print(len(out), "instances; vertices per:", [len(o["pts"]) for o in out])
