# V2 stand (Onshape "Test Stand New", V2 Prototype) — inputs in progress

- `Assembly_1.step` — Onshape export (13 instances: 12 extrusions + load-cell plate M8).
- `extract/` — STEP reader (`parse.py`), member axes/profiles (`members.py`, `contacts.py`),
  CAD section properties (`sections.py`), contact detection (`contacts2.py`), tool data (`build_tool.py`).
- `joints_candidates.json` — members + 13 candidate joints + the user's bracket entries so far (`seed`),
  as loaded in the bracket tool https://claude.ai/artifact/Nsq6kQay9ChoT8JhyCZBR1.
  Change applied at the user's request: top 4040 pair M5 + M11 replaced by one 4080 (M5), depth along y.
- `cad_sections.json` — section properties from the CAD end faces (4040 A 1059 mm², I 15.1 cm⁴;
  4080 A 2388 mm², I 116/30.7 cm⁴; 8080 A 3539 mm², I 226 cm⁴). CAD 4040 is a simplified solid
  profile: replace with catalogue values (unverified until then).

Open before simulating: brackets for N6–N14, thrust point/direction, load-cell plate attachment,
40-series bolt size/preload and bracket types, sandbag plan.
