# Sphinx stand model — handoff

Read this first, then `SESSION_SUMMARY.md` (what was asked/found/open, the user's mental model);
`ASSUMPTIONS.md` lists every unconfirmed number. The original brief is
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
stand/loads.py      load cases + sandbag base line load (exact 6x6 resultant balance);
                    ground mode: size_sandbags (rigid-body tipping/lift statics) + bag loads
stand/joints.py     leg/bolt-group geometry (prepare) and checks; capacities()
stand/burrard.py    Burrard half-truss back test solve (shared by the pytest check and figures)
stand/members.py    yield, braced-length Euler/Johnson, beam-column, tau
stand/analysis.py   Engine: runs x cases, bearing active set, mechanism eig, buckling, sweep
stand/envelope.py   worst over valid solves -> rows for CSV/plots
stand/report.py     terminal tables, CSVs, summary.md (+ figures inline), results/README.md index
stand/charts/       one module per figure family (runnable alone from results/3d/.cache);
                    layout.py = the node/member key every other figure is read against;
                    files numbered by _render.FIGURE_ORDER; PNG only unless output.svg
                    _render.py = the only matplotlib config (from the charting skill's
                    render.py) + palette, info box (skill's info_box.py), labels, views
stand/viz.py        viewer.html: JSON payload + client-side plotly 3D; click bracket -> isometric SVG
                    free-body diagram per leg (styled on the user's sketch) + capacity table
tests/              validation suite (brief section 9 + unit checks)
```

## Status (2026-11-18)

Everything in the brief is implemented, plus the document figures (ground mode swaps sandbag_demand
for two ground-reaction figures); 20 tests pass (cantilever, UDL, Euler column,
Burrard truss incl. AB = −5.763P, pinned rectangle couple + mechanism, bolt group B
869 N, statics of the wrench transfer, global equilibrium + vanishing 3-2-1 reactions on
every stand run, sandbag 196.4 kg, compression-only bearing, 2D run, ground-mode equilibrium +
compression-only contact, bag FS). Full 3D run ≈ 40 s; ground run ≈ 3 min.

## Results layout

results/{3d,3d_ground,2d}/ {summary.md, viewer.html, figures/NN_*.png, tables/*.csv, params_used.yaml};
non-default runs -> results/variants/<mode>_<changes>[_case_...]/ (stand/__main__._out_dir).

## viewer.html (2026-11-17)

State <select> (envelope / any run-case / buckling mode), deformed overlay, bracket stepping by
SF, FBD drawn in SVG (not in the 3D scene: overlapping 3D arrows were unreadable), focus (orthographic zoom = scene.aspectratio, not eye distance). Gotchas: re-render
from plotly_click must be deferred (setTimeout) or plotly's hover label recurses; render()
copies the live camera + aspectratio into the layout before Plotly.react. Envelope legs of one
bracket may come from different solves (each leg's own governing solve) — stated in the panel.

## Ground mode (2026-11-17, `run --ground`)

base.mode = ground: compression-only Winkler springs per base node (model.GroundContact,
Engine.K_for/contact_gap/ground_forces), no 3-2-1 restraint, bags sized by
loads.size_sandbags. Memory: every contact pattern is a dense ~2200-DOF inverse, so
buckling runs inside solve() and contact solvers are dropped (else OOM). charts/ground.py
draws the reaction (iso "curtains" + plan per case); viewer shows q under the base.

## Joint Mz capacity override (2026-11-18)

`bolts.M_twist_Nm` (0 = computed μ·F_i·r_f ≈ 4.6 N·m) models a fix that resists twist — a
second bolt, a key, a pinned bracket. Runs at 36 N·m are in
`results/variants/{2d,3d}_M_twist_Nm36/`. **36 N·m is not enough**: the worst twist demand is
54.4 N·m (3D) / 56.7 N·m (2D), and even with twist free the SF ceiling is 0.47 (3D) / 0.31 (2D)
because **shear slip** (F_fric = μ·F_i = 1000 N) takes over as the governing term. Fixing twist
alone cannot reach SF 1; the bolt preload / friction area has to go up too.

## Burrard back test (2026-11-18)

`python -m stand burrard` -> `results/validation/`: summary.md (the comparison tables),
tables/members.csv, one figure (the truss coloured by member force).

- **Forces:** all 19 members match the notes to 3 decimals, every digit they print.
- **Safety factors:** the notes' table prints yield AND buckling for every member
  (`burrard.NOTES_TABLE`, transcribed from the scan in the user's FBD doc, "Model Validation").
  Every buckling SF reproduces, and so does every `P_crit` (142.03 / 213.69 / 223.96 / 230.62 /
  232.92 / 5.84 / 2.63 MN).
- **The three rows that differ, and why:** AB 3.82 vs 3.88 and 16.43 vs 16.69 — their row is
  computed from the transposed T = −8.51 MN; over the corrected 8.644 MN their own P_crit gives
  16.43, which is ours and matches the correction they state (16.4). HK 9.48 vs 9.47 and
  HI 16.55 vs 16.53 — ~0.15 %, their σ rounded in the intermediate step.
- **IK's yield cell is not legible in the scan** — left as None, not guessed. Our 3.17.

The numeric comparison is a **table, not a chart**: 19 values against 19 reference values is
tabular data, and a chart of it only ever says "they match" (tried; rejected). `N/P` is the
notes' convention — axial force ÷ the unit load P = 1.5 MN — and must be spelled out wherever
it appears. `stand/burrard.py` holds the solve so the pytest check and the report share it;
`charts/burrard.py` is outside `charts.FAMILIES` because it takes no study.

## Node/member key + label placement (2026-11-18)

`charts/layout.py` -> figure 01 in every run: every member labelled along its own line, every
joint at its node, on the same true-scale front/side/plan views. Items projecting onto one spot
share a label ("M7/M9"); the other views separate them.

`_render.place_point_labels` is the shared greedy placer behind it (candidate offsets around
each point, first one clearing all boxes already placed wins). Three traps, all hit:
- Place labels only once the figure geometry is **final** — after `finish_view` sets equal
  aspect and after the legend/title. Placing earlier solves against a different data->display
  mapping and the result is meaningless.
- `fig.canvas.draw()` re-runs constrained_layout and **moves the axes**, invalidating every
  box measured before it. Draw once, then `set_layout_engine("none")`, then measure extents
  straight off the renderer with no further draws (also ~5x faster).
- One call per chart, not one per label — `placed` has to accumulate across all of them.
  Pass the most constrained labels first (a member id may only slide to either side of its
  own line; a node id can go anywhere).

## V2 stand (2026-11-22): 40-series, `--params params_v2.yaml`

Onshape "Test Stand New" (V2 Prototype). Inputs in `references/v2/` (STEP, extraction scripts,
geometry.json, brackets.json from the bracket tool https://claude.ai/artifact/Nsq6kQay9ChoT8JhyCZBR1).
`params_v2.yaml` holds only V2 overrides (40-series bolts/brackets/plate placeholders, sandbag
stations, 80 mm ground contact, output.dir results_v2). Results: `results_v2/{3d,3d_ground}` (no 2D).
Code generalised for it: section_4040/4080/8080 params (CAD-derived, unverified), depth direction
may be a vector (tilted braces), `thrust_patches` (rigid load-cell plate M8 spreads stand loads
equally over M1/M4/M9/M12; thrust kinematics = mean of patch nodes), params-file baseline (only
--set/--case make variants). User merged the two top 4040s into one 4080 (M5).
Findings: corner-bracket joints SF 0.23–0.45 (twist about one bolt), worst N6 (frame to column)
and N2 (column foot); T-plate brace joints 0.7–2.4 (bolt slip); members SF ≥ 4.6; run R tilt
≈ 0.5° (> 0.25°); 4 × 125 kg bags on the gravel base.

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
the brief's outline. Ground-contact base: built (`run --ground`); base-joint failures persist
(lowest 0.10 vs 0.08) -> real, not a line-load artifact. Next offered: joint-slip model.

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
