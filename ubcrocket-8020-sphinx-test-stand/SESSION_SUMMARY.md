# Session summary — Sphinx stand SF model (cloud sessions, 2026-11-17 → 19)

Handoff for the next Claude. Read `CLAUDE.md` (code layout + gotchas) and `ASSUMPTIONS.md`
(every unconfirmed number) too; this file is the *story*: what was asked, what was built,
what was found, what the user understands, and what is open.

## The user

Christopher Kalitin, ME intern (Terraform Industries), working on UBC Rocket's Mojave Sphinx
engine test stand (80/20 1010/1020 aluminium extrusion). Wants terse, direct answers, first
principles, units defined for every equation variable, honest criticism. Values clarity,
testability, a utilitarian CLI, intuitive folders, and *beautiful* visuals. Wants to build
intuition, not just numbers — explain mechanisms (series vs parallel load paths, etc.).

## What exists (all on branch `sphinx-stand-model-edarp6`, merged to `master` by the user)

Python tool `ubcrocket-8020-sphinx-test-stand/`: 3D direct-stiffness frame solver (numpy;
scipy for eigen/hull only), member splitting at joints, zero-length bracket springs,
compression-only bearing contacts, load cases, member + bolted-joint SF checks, buckling,
k_θ sweep, 2D side-frame mode, CLI, CSV/markdown/figures/interactive viewer. 20 pytest tests.

```
python -m stand run            # 3D, brief's base model          -> results/3d/        (~40 s)
python -m stand run --ground   # base on gravel springs + bags    -> results/3d_ground/ (~3 min, >2 GB RAM)
python -m stand run --2d       # side frame                       -> results/2d/
python -m stand plots [--ground|--2d]   # re-render figures + viewer from cache (no solve)
python -m stand test           # 20 tests
python -m stand params [--changed]      # params.yaml is the editable input (units in key names)
```

Results layout (user asked for it to be "very intuitive"): `results/README.md` index (generated);
each run folder has `summary.md` (all figures inline, GitHub-readable), `viewer.html`,
`figures/NN_*.png` (numbered reading order, PNG only; `output.svg: true` adds SVG),
`tables/{members,joints,ktheta_sweep}.csv`, `params_used.yaml`. Non-default runs go to
`results/variants/<mode>_<changes>/`.

## Work done this session, in order

1. **Viewer v1** (`stand/viz.py`, `viewer.html`): replaced plotly updatemenus with an HTML
   state `<select>` (envelope / every run-case / buckling mode); everything rendered client-side
   from an embedded JSON payload; click members, joints, brackets; inspector panel.
2. **Results folder cleanup**: user saw stale/duplicated images on GitHub (they were looking
   at the old branch `sphinx-stand-model`; also png+svg duplicates and 2d nested under 3d).
   Reorganised to the layout above; `stand.html` → `viewer.html`.
3. **Viewer v2 → v3 (free-body diagrams)**: user rejected overlapping 3D arrows ("not how we
   draw FBDs") and supplied a sketch: an L-shaped triangle bracket with two bolted legs,
   Fx/Fy (orange, in the face), Fz (green, bolt axis), Mx/My/Mz (purple curls), plus a
   "load / direction / carried by" table. Now: clicking a bracket draws **one isometric SVG
   FBD per leg** — shaded 1010 extrusion stubs with T-slots, solid L-angle with gussets (or
   the brief's T-plate outline), socket-head bolts (active leg dark), haloed arrows, curls,
   pill labels, governing load boxed in red, leg-frame triad, "not drawn (≈0): …" footnote
   (components < 2 % of the leg's largest force/moment are omitted from the drawing, always
   in the table). Table per leg: value, capacity, share of U, SF alone, carried by. Prev/next
   stepping through all brackets by SF. 3D scene shows brackets as filled triangles/plates.
   User reaction: "Beautiful!! Great work!" — keep this quality bar.
4. **Ground-contact base mode** (`base.mode: ground`, `run --ground`): see below.

## Engineering findings (what to tell / build on)

- **Joints are the problem.** Every triangle-bracket joint has SF < 1, governed by **twist
  about its single bolt**: Mz vs μF_i·r_f = 0.2 × 5000 N × ~4.6 mm ≈ 4.6 N·m. No anti-rotation
  key (user confirmed). Worst N5#1 leg a: Mz = 54.4 N·m (98 % of U).
- **Members:** M32/M18/M17 ≈ 1.7–1.9 (yield, Mz) < target 2. Buckling λ 10.7–15: fine.
  Thrust-point tilt 1.3–1.9° ≫ 0.25° flag (top cantilevers bending).
- **Base models compared** (lowest SF):

  | joint | brief line load (`3d`) | gravel springs (`3d_ground`) |
  |---|---|---|
  | N5, N6 | 0.08–0.09 | 0.35 |
  | N1, N2 | 0.09 | 0.75–0.77 |
  | N7, N8 (M22, by the bags) | 0.09 | 0.10 |
  | N9, N10 | 0.23 | 0.14 |

  Joints with SF < 1: 28 → 24. Insensitive to gravel stiffness (k_s 50/150/500 MN/m³ →
  0.09/0.10/0.10). **Conclusion: base-joint failures are real, not an artifact of the brief's
  assumed base load; the joints need a design change (2 bolts per leg ≈ μF_i·d ≈ 20 N·m, or
  keyed brackets), not different bags.**
- **Sandbags (ground mode):** 4 × 100 kg = 400 kg (vs brief's 196 kg = net uplift at FS 1),
  sized by FS 1.5 against **sideways tipping** — thrust line is only 300 mm from the long
  footprint edge, so bag lever arms ≈ thrust lever arm. Placement (Claude's choice, user
  delegated it): M19/M25 outriggers under the thrust line + both stubs of cross beam M22
  (`sandbags.stations`). Contact 64–80 % of base length; −x rail ends lift off; peak
  4.0 kN/m; sliding FS ≥ 10.6 (μ 0.5).

## Concepts the user has worked through (don't re-explain from scratch; build on them)

- **Bracket legs are in series, not parallel.** The rigid L passes the *same* moment through
  both legs; each leg sees it in its own frame (N5: twist 54.4 N·m on leg a ≡ tilt −58.6 N·m on
  leg b; the 4.2 N·m difference = r × F = 0.020 m × 208.7 N). Slip at the weak leg doesn't
  hand load to the other leg — the bracket stops carrying that moment and the *frame*
  redistributes (that's the indeterminate part). User initially had a parallel mental model;
  corrected and accepted.
- **Ground springs vs sandbag mass:** two separate questions. Bag mass = rigid-body statics
  (tipping/lift, determinate, depends on placement). How the base beams bend = where the
  ground pushes back = indeterminate → needs stiffness → Winkler springs (k = k_s·b·L_trib),
  compression-only active set. Characteristic length 1/λ = (4EI/k)^¼ ≈ 0.2–0.4 m on sand/gravel
  for 1010 (EI = 1268 N·m²) → 200–600 mm base beams act ~rigid on gravel.
- **"Fix every joint rigid, no brackets"** = run R; valid as an upper bound on joint demand,
  not as a verdict (rigid assumption contradicts SF ≪ 1). Run P (pinned) is a mechanism.

## Open / next steps (offered, not yet requested)

1. **Joint-slip model** (top candidate): per-bracket rotational spring elastic up to its
   friction limit, then slipping at constant moment; iterate like the bearing/ground active
   sets. Answers: does the stand settle stably after slip, how far does the thrust axis move,
   which joints really need fixing.
2. Uneven-ground bound (contact only near beam ends) for ground mode.
3. Design-fix runs: 2-bolt legs / keyed brackets as a capacity option, then re-check.
4. Cosmetic: 2D viewer arrowheads in 3D scene slightly oversized (minor).

## Gotchas (also in CLAUDE.md)

- Ground mode: each contact pattern is a dense ~2200-DOF inverse (~100 MB) → buckling is done
  inside `solve()` and contact-specific solvers are dropped, else OOM.
- Param keys: the unit suffix is stripped for the SI attribute (`round_to_kg` → `round_to`;
  a key named `round_kg` would become `round`).
- Viewer: defer re-render out of `plotly_click` (setTimeout) or plotly recurses; orthographic
  zoom = `scene.aspectratio`; FBD painter order = members, then bracket, then bolts (layers).
- Rerunning on another machine changes CSVs by round-off (bON/bOFF ties) — not real changes.
- Old `results/.cache` pickles from before a schema change break `plots`; just re-run.
