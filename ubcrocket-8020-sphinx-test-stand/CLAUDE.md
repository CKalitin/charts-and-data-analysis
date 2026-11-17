# Sphinx stand model — handoff

Read this first; `ASSUMPTIONS.md` lists every unconfirmed number. The original brief is
`references/prompt/PROMPT.md` (+ geometry.json, brackets.json, burrard_validation.json).

## Layout

```
stand/params.py     SCHEMA = single source of every tunable (unit in key suffix, flags);
                    load() -> SI namespace + list of changes vs defaults
stand/geometry.py   JSON (mm) -> Member / Joint dataclasses (SI)
stand/fem.py        element k, geometric kg, consistent linear loads, springs w/ rigid arms,
                    Solver (cached inverse + iterative refinement), force recovery, eigen
stand/model.py      build(): stations, sub-elements, bracket + bearing springs, 2D variant,
                    3-2-1 restraint, relative_to_base()
stand/loads.py      load cases + sandbag base line load (exact 6x6 resultant balance)
stand/joints.py     leg/bolt-group geometry (prepare) and checks; capacities()
stand/members.py    yield, braced-length Euler/Johnson, beam-column, tau
stand/analysis.py   Engine: runs x cases, bearing active set, mechanism eig, buckling, sweep
stand/envelope.py   worst over valid solves -> rows for CSV/plots
stand/report.py     terminal tables, CSVs, summary.md (+ figures inline), results/README.md index
stand/charts/       one module per figure family (runnable alone from results/3d/.cache);
                    files numbered by _render.FIGURE_ORDER; PNG only unless output.svg
                    _render.py = the only matplotlib config (from the charting skill's
                    render.py) + palette, info box (skill's info_box.py), labels, views
stand/viz.py        stand.html: JSON payload + client-side plotly; click bracket -> free-body
                    diagram (6 wrench comps per leg, leg frame) + capacity table; click joint/member
tests/              validation suite (brief section 9 + unit checks)
```

## Status (2026-11-17)

Everything in the brief is implemented, plus 11 document figures; 18 tests pass (cantilever, UDL, Euler column,
Burrard truss incl. AB = −5.763P, pinned rectangle couple + mechanism, bolt group B
869 N, statics of the wrench transfer, global equilibrium + vanishing 3-2-1 reactions on
every stand run, sandbag 196.4 kg, compression-only bearing, 2D run). Full 3D run ≈ 40 s.

## Results layout

results/{3d,2d}/ {summary.md, viewer.html, figures/NN_*.png, tables/*.csv, params_used.yaml};
non-default runs -> results/variants/<mode>_<changes>[_case_...]/ (stand/__main__._out_dir).

## viewer.html (2026-11-17)

State <select> (envelope / any run-case / buckling mode), deformed overlay, forces/moments
toggles, focus (orthographic zoom = scene.aspectratio, not eye distance). Gotchas: re-render
from plotly_click must be deferred (setTimeout) or plotly's hover label recurses; render()
copies the live camera + aspectratio into the layout before Plotly.react. Envelope legs of one
bracket may come from different solves (each leg's own governing solve) — stated in the panel.

## Findings so far (defaults)

- Every triangle-bracket joint is SF < 1, governed by **twist about its single bolt**
  (Mz vs μF_i·r_f = 4.6 N·m). Worst are the base joints (SF ≈ 0.08–0.10), driven by the
  sandbag line load bending the base beams; the M17 end joints N29/N30 are ≈ 0.26.
  The brief's hand calc (N29/N30 ≈ 1.8) counted friction slip only; with the 20 mm bolt
  offset, the r × F twist dominates.
- Members: M18 1.76, M17 1.90, M32 1.93 (yield, Mz) — below target 2.
- Frame buckling λ ≈ 15 (k_θ = 1) to 43 (rigid): fine.
- Thrust-point tilt ≈ 1.0° (rigid) — 4× the 0.25° flag; comes from the 150 mm top
  cantilevers M14/M27 + M18/M32 bending.
- Run P is a mechanism in every case (pinned 3D frame); run R governs.

## Answered (2026-11-17) — see ASSUMPTIONS.md "Confirmed"

No anti-rotation key on triangles; plate = 80/20 aluminium (172 MPa); plate sections from
the brief's outline. Still open: a ground-contact base option (compression-only ground +
sandbag loads) instead of the brief's sandbag line load — not requested yet.

## Decisions worth knowing (why)

- Displacements are measured relative to a rigid fit of the base nodes: the free base
  flexes, and measuring against the 3-2-1 nodes reported 22 mm of fake y-drift.
- The 1 mm mechanism test applies to run P only; the sweep uses 5 × run R displacement,
  since run R itself moves ~12 mm.
- Buckling eigenproblem: Cholesky reduction to a standard symmetric problem
  (ARPACK's generalized LA mode needed ~1000 iterations/solve; 12-digit agreement with
  dense eigh verified).
- P-run solves are ~10 m "displacements": their reaction recovery is round-off
  limited (~1e-6 × thrust), so the strict restraint assertion applies to valid solves.
