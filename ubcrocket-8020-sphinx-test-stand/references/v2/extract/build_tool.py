import json, re, numpy as np
C = json.load(open("contacts.json"))
mem = {m["i"]: m for m in C["members"]}
members = []
for i, m in mem.items():
    c, e = np.array(m["c"]), np.array(m["e"])
    p0, p1 = c - e * m["L"] / 2, c + e * m["L"] / 2
    d = {"id": i, "p0": p0.round(1).tolist(), "p1": p1.round(1).tolist(), "L": round(m["L"], 1), "prof": m["profile"]}
    if m["profile"] == "4080":     # depth (80) direction
        d["depth"] = (np.array(m["u"]) if m["wu"] == 80 else np.array(m["v"])).round(4).tolist()
    members.append(d)
# cluster contacts (plate excluded: it is not a frame member) into joints
pairs = [p for p in C["pairs"] if mem[p["a"]]["profile"] != "plate" and mem[p["b"]]["profile"] != "plate"]
groups = []
for p in pairs:
    at = np.array(p["at"])
    side_side = p["wa"].startswith("side") and p["wb"].startswith("side")
    g = None if side_side else next((g for g in groups if not g["ss"] and min(np.linalg.norm(at - np.array(q["at"])) for q in g["p"]) < 50), None)
    if g is None:
        groups.append({"p": [p], "ss": side_side})
    else:
        g["p"].append(p)
def order_key(g):
    c = np.mean([q["at"] for q in g["p"]], 0)
    return (round(c[2] / 100), c[0], c[1])
groups.sort(key=order_key)
nodes = []
for k, g in enumerate(groups, 1):
    c = np.mean([q["at"] for q in g["p"]], 0)
    ms = sorted({q["a"] for q in g["p"]} | {q["b"] for q in g["p"]})
    contacts = []
    for q in g["p"]:
        ea, eb = q["wa"].startswith("end"), q["wb"].startswith("end")
        if ea and eb:
            contacts += [{"a": q["a"], "b": q["b"], "kind": "end-end", "end_of": q["a"]},
                         {"a": q["a"], "b": q["b"], "kind": "end-end", "end_of": q["b"]}]
        elif ea or eb:
            contacts.append({"a": q["a"], "b": q["b"], "kind": "end-to-side", "end_of": q["a"] if ea else q["b"]})
        else:
            contacts.append({"a": q["a"], "b": q["b"], "kind": "side-side", "end_of": q["a"]})
    nodes.append({"id": f"N{k}", "c": c.round(1).tolist(), "members": ms, "contacts": contacts})
plate = mem[8]
pc, pe, pu = np.array(plate["c"]), np.array(plate["e"]), np.array(plate["u"])
corners = [(pc + pe * a * plate["L"] / 2 + pu * b * plate["wu"] / 2).round(1).tolist() for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
DATA = {"members": members, "nodes": nodes, "plate": corners}
json.dump(DATA, open("tool_data.json", "w"), indent=1)
for n in nodes:
    print(n["id"], n["c"], ["M%d" % x for x in n["members"]], [(c["kind"], "M%d" % c["end_of"]) for c in n["contacts"]])
