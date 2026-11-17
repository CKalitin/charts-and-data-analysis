# Claude Code prompt — Mojave Sphinx test stand frame + joint safety model

Paste everything below this line into Claude Code, in a folder that contains
`geometry.json`, `brackets.json` and `burrard_validation.json`.

---

## Goal

Build a Python tool that computes the **factor of safety of every member and every
bolted joint** of an 80/20 aluminium-extrusion rocket-engine test stand, using a
3D direct-stiffness frame solver written from scratch in numpy (no FE libraries;
scipy only for eigenvalues). A 2D mode (one side frame, x–z plane) must reuse the
same code. Output CSV tables, a markdown summary and an interactive plotly HTML.

Write the validation tests (section 9) **first** and keep them passing.

## 1. Inputs (provided)

- `geometry.json` — 36 members: `id`, centreline endpoints `p0`,`p1` (mm),
  `length`, `profile` (`1010` or `1020`), and for 1020 members
  `strong_axis_depth_along` (global axis of the 2-inch depth). Also
  `base_members`, `thrust_point`, `thrust_member` (M17).
- `brackets.json` — 30 joints. Each: `id`, `at` (joint centre, mm), `members`,
  `bearing` (list of `{end_of, bears_on}`: that member's end face pushes on the
  other member, compression only), `brackets` (list of
  `{type: triangle|plate_t5|plate_other|none, a, b, face: ±x|±y|±z, count}`).
  Duplicate entries = separate physical brackets (e.g. one each side).
- `burrard_validation.json` — truss validation case with expected answers.

Create `params.yaml` with every number below as an editable default.

## 2. Units and conventions

SI internally (m, N, Pa); inputs in mm are converted on load. Global z is up.
Member local x runs p0→p1. Report every quantity with units.

## 3. Materials and sections (80/20 published values; 6063-T6)

| | 1010 (1×1 in) | 1020 (1×2 in) |
|---|---|---|
| A | 0.437 in² = 281.9 mm² | 0.787 in² = 507.7 mm² |
| I (each axis) | 0.0442 in⁴ = 1.840e-8 m⁴ | strong 0.3078 in⁴ = 1.281e-7 m⁴; weak 0.0833 in⁴ = 3.467e-8 m⁴ |
| c (outer fibre) | 12.7 mm | strong 25.4 mm; weak 12.7 mm |
| weight | 0.0424 lb/in = 7.43 N/m | 0.0768 lb/in = 13.45 N/m |

E = 68.9 GPa, G = 26.5 GPa, σ_y = 172 MPa. Torsion constant J is not published:
parameter `J_1010`, `J_1020`, default 0.5·(Iy+Iz) and flag it as unverified.
The 1020 strong axis is the one whose depth runs along `strong_axis_depth_along`.

## 4. Loads (all inputs in params.yaml)

- Thrust F = 1112 N (250 lbf) × dynamic factor `DF = 2` → +z at `thrust_point`
  (midpoint of M17; split M17 with a node there).
- Rocket wet weight 30 lb = 133 N, −z at the same point, unfactored.
- Self-weight: distributed along every member from the table above.
- Misalignment: `misalign_x`, `misalign_y` (default 0.03 each) as fractions of
  the factored thrust, applied horizontally at the thrust point.
  Load cases: (+x), (−x), (+y), (−y), and (+x,+y) combined; plus a no-misalignment case.
- **Base = sandbags.** Do not fix the base. Sum all applied loads, then apply the
  equal-and-opposite resultant (force and moment) as a distributed line load over
  the `base_members` (uniform per metre; solve for a linear distribution if a
  moment needs balancing). Remove rigid-body motion with a statically determinate
  3-2-1 restraint on three base nodes, and **assert its reactions are ≈ 0**
  (< 1e-6 of thrust). Report the sandbag mass needed = net uplift / g.

## 5. Structural model

- 3D Euler–Bernoulli frame elements, 12 DOF, with orientation from a reference
  vector. Split members at every joint centre / load point lying on them
  (closest point on the centreline within 70 mm).
- **Each bracket is its own element** between the two members it connects, at
  the joint: a zero-length 6-DOF spring between the node on member `a` and the
  node on member `b` (both at the closest point on each centreline to `at`;
  if the centrelines are offset, connect through a rigid link — e.g. M32 sits on
  the outer half of M21 with a 20 mm offset). `count` > 1 or duplicate entries →
  that many springs in parallel. Joints with members but no bracket and no
  bearing are a modelling error: stop and report.
- Spring stiffness: translations k_t = 1e3·EA/L; rotations by run (section 6).
- **Bearing** pairs: compression-only spring along the bearing member's axis.
  Solve iteratively: deactivate any bearing spring in tension and resolve until
  the active set is stable.
- Mechanism check: eigenvalues of K; if near-zero, print the mode shape and the
  DOFs involved.

## 6. Runs (bounding the unknown joint stiffness)

| Run | Rotational spring k_θ |
|---|---|
| P (pinned) | 1e-3 · EI/L (soft: solver stability only) |
| R (rigid) | 1e3 · EI/L |

× bearing ON / OFF (OFF = all force through brackets) × every load case.
- Run P: if any node displacement > 1 mm, flag that load case "mechanism — pinned
  result invalid; joints carry moment" and use run R for it.
- For each member/joint item, the design value = worst over all runs and cases.
- Assumption test: sweep k_θ ∈ {1e-3 … 1e3}·EI/L (7 values) for the governing
  load case; confirm every utilisation peaks at an end of the sweep, else report
  the interior maximum and use it.

## 7. Joint (bracket) checks

Assumptions (params): bolt preload F_i = 5 kN, μ = 0.2 (one friction surface),
¼-20 bolts: hole radius r_i = 3.57 mm, head radius r_o = 5.55 mm, plate yield
172 MPa (placeholder), plate thickness t = 6.35 mm (placeholder), triangle tilt
arm a = 12.7 mm (placeholder). Flag all placeholders in the output.

Take each bracket spring's force/moment (F, M) at the joint and transfer it to
each leg / bolt group: **M_leg = M + r × F** (r = joint point → bolt or group
centroid). Rotate into the leg frame: x along that member's slot, y across the
slot in the face plane, z = bolt axis (out of the face, +z = pull-off).

**Triangle (L) bracket** — one bolt per leg; leg on member a bolts to a's face
that faces member b (z = direction toward b, made ⟂ to a); leg on b likewise.
Bolt sits 20 mm from the corner along each member.
Allowables per leg: Fx (along slot, friction only) = μF_i; Fy = μF_i;
F_z pull = F_i (push: not limiting); M_x = M_y = F_i·a (gap opening);
M_z = μF_i·r_f with r_f = ⅔(r_o³−r_i³)/(r_o²−r_i²) ≈ 4.6 mm.

**T plate (plate_t5)** — plate in the plane of members a and b, on the given
`face`. Local plate coords (u along a, v along b, origin at a's centreline at the
joint): group A (3 bolts on a) at u = −25.4, 0, +25.4 mm, v = 0; group B (2 bolts
on b) at u = 0, v = 38.1 and 63.5 mm. Plate outline: base 76.2 × 25.4 mm, taper
to 25.4 mm wide at v = 63.5 (+12.7 to the top edge). Per group, in-plane bolt
force: **f_i = F/n + M·(ẑ × r_i)/Σr²** (rigid plate; r_i from group centroid).
Check every bolt |f_i| ≤ μF_i and its along-slot component ≤ μF_i.
Out of plane: F_z,i = F_z/n ± M·r_i/Σr² against F_i, and plate bending
σ_y·b_net·t²/6 (group A: b_net = 76.2 − 3·7.14 mm; group B: 36.5 mm along the
line, 56.4 mm through the lower hole). Compute these in code from the formulas.

**plate_other**: report forces only, no capacity (flag).

Combined utilisation per leg / group: linear sum
U = √(Fx²+Fy²)/F_fric + F_z,pull/F_pull + |Mx|/Mx,max + |My|/My,max + |Mz|/Mz,max.
Joint SF = 1/U (demand already includes DF = 2). Target joint SF ≥ 2.

## 8. Member checks (target SF ≥ 2 with DF = 2 in the loads, i.e. 4 on static thrust)

- Yield: σ = |N|/A + |M_y|/S_y + |M_z|/S_z ≤ σ_y/SF (use the larger along each sub-element).
- Buckling (compression): K = 1.0 between joints, each axis with its own braced
  length; Euler P_cr = π²EI/(KL)² if KL/r > C_c = √(2π²E/σ_y) ≈ 89, else Johnson
  P_cr = Aσ_y[1 − σ_y(KL/r)²/(4π²E)]. Pass if N ≤ P_cr/SF.
- Beam-column (compression + bending): N/P_cr + M/(M_y(1 − N/P_cr)) ≤ 1/SF.
- Frame stability: linear buckling eigenproblem (K_e + λK_g)φ = 0 with K_g from
  member axial forces; report the lowest positive λ (pass if λ ≥ SF) and plot φ.
- Serviceability: deflection and tilt at the thrust point (report; flag tilt > 0.25°).
- Shear, torsion: report peak τ as a sanity check only.

## 9. Validation tests (pytest, write first)

1. Cantilever tip load: δ = PL³/(3EI), root moment PL.
2. `burrard_validation.json`: 2D pin-jointed truss (A, I per member, E, loads,
   supports given). Member forces must match `expected_force_in_P` to 0.5 %, min
   yield SF 2.71 (BE), min Euler buckling SF 4.52 (DE). Note AB = −5.763P (the
   course notes print 5.673P — a typo); the solver must reproduce 5.763P.
3. Pinned rectangle (two columns, width w, height h) under a vertical couple from
   load F at offset e from the right column: N_right = F(1 + e/w), N_left = −F·e/w.
4. Same pinned rectangle under a horizontal load → mechanism flag.
5. Bolt group B (2 bolts, r = ±12.7 mm): V = 100 N ⟂ to the line, M = 20.8 N·m →
   worst bolt 869 N.
6. Global equilibrium on every stand run (loads + base line load + restraint = 0).
7. Base restraint reactions ≈ 0.

## 10. Outputs

- `results/members.csv`: id, profile, governing run/case, N, My, Mz, σ, SF_yield,
  P_cr, SF_buckle, beam-column ratio.
- `results/joints.csv`: joint, bracket index, type, leg/group, member, the six
  leg-frame components, each allowable, U, SF, governing run/case, placeholder flags.
- `results/summary.md`: lowest 10 SFs (members and joints), frame λ, thrust-point
  deflection/tilt, sandbag mass required, mechanism flags, k_θ sweep result,
  list of unverified placeholders.
- `results/stand.html` (plotly 3D): undeformed + scaled deformed shape, members
  coloured by SF, brackets drawn at joints coloured by SF, hover with numbers;
  dropdown for run / load case.
- CLI: `python -m stand run [--2d] [--case NAME]`, `python -m stand test`.

## 11. Expected sanity checks (from hand calcs — investigate if far off)

- M17 end connections (N29, N30): two triangle brackets per end, 1112 N vertical
  per end vs 2 × 1 kN friction → joint SF ≈ 1.8 (expect this to govern).
- M18/M32 → M1/M21 splice goes through M26 brackets only (tension under thrust).
- Net uplift ≈ 2224 − 133 − 165 ≈ 1.93 kN → ≥ 196 kg of sandbags.
- 2D mode: front frame members only (y ≈ −20 mm), half of every stand load,
  cross members removed, out-of-plane DOFs fixed.
