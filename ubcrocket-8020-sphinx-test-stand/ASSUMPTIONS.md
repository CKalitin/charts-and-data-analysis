# Assumptions

Every number or modelling choice not confirmed by the user. Move an entry to
**Confirmed** when it is answered. Parameter keys refer to `params.yaml`.

## Open — inputs (placeholders, from the brief)

| key | value | status |
|---|---|---|
| `triangle.tilt_arm_mm` | 12.7 mm | placeholder: Mx,max = My,max = F_i·a |
| `plate.thickness_mm` | 6.35 mm | placeholder |
| `section_*.J_mm4` | 0.5·(Iy+Iz) | not published by 80/20; affects torsion and stiffness only |
| `bolts.preload_N`, `bolts.mu` | 5 kN, 0.2 | brief assumption |
| `loads.misalign_x/_y` | 0.03 | brief assumption |
| `plate_other` brackets | — | no capacity model (none in the current brackets.json) |

## Open — modelling choices made by Claude

1. **Spring stiffness basis.** Bracket k_t = 1e3·min(EA/L) and k_θ = factor·min(EI_weak/L)
   over the two connected members, L = full member length; rotational spring isotropic.
2. **Triangle corner side.** When a member continues through the joint, the bracket
   could sit in either corner; every feasible corner is evaluated and the worst used
   (`corner` and `n_corner_options` columns in joints.csv). Bolt = joint point + 20 mm
   along each member; corner taken as the joint point `at`.
3. **Wrench transfer sign.** Implemented as statics, M_P = M_X + (X − P) × F. The brief's
   "M + r × F with r = joint → bolt" has the opposite sign for that r; magnitudes differ
   unless one term vanishes. (`test_wrench_transfer_statics`.)
4. **Stem neck check added** (76.2 mm wide where the stem meets the base, no hole);
   stem bending = max(lower hole, neck).
5. **Bearing contact** at the end-face node of the bearing member, zero initial gap,
   k = 1e3·EA/L of that member.
6. **Displacements, tilt and the 1 mm mechanism test** are measured relative to the
   least-squares rigid motion of the base nodes (the ground), not to the 3-2-1 nodes —
   otherwise base flexure swings the whole stand and reports ~20 mm of fake drift.
7. **3-2-1 restraint** placed only on base joint nodes (never a cantilever tip).
8. **Sweep validity.** A k_θ sweep point counts as "mechanism-dominated" (excluded) when
   its max displacement exceeds `checks.sweep_mech_ratio` (5) × run R's and 1 mm. Plain
   "> 1 mm" cannot be used: run R itself moves 9–15 mm.
9. **Buckling braced length.** A joint braces a local axis if a member there has
   |cos| ≥ 0.5 with it; a segment ending at a free end uses K = 2.
10. **2D mode.** Geometry flattened onto y = −20 mm; removed cross members kept as
    zero-length stubs where they bracket ≥ 2 front members together at one joint
    (otherwise the M21/M32 splice through M26 and the base continuity are lost and the
    upper truss hangs off one 1010 column). Half of each cross member's weight is lumped
    at its front-frame joints. Out-of-plane cases are skipped.
11. **Sandbag line load** (brief): linear in plan position; besides the brief's
    net-uplift mass the report also gives the mass if bags are spread uniformly (must
    cover the most-downward demand).

## Confirmed

| item | answer (2026-11-17) |
|---|---|
| triangle bracket anti-rotation key | **none** → twist capacity is friction only, μF_i·r_f = 4.6 N·m |
| plate material | **80/20 aluminium** → `plate.fy_MPa` = 172 MPa, same as the extrusions |
| T-plate section widths | **use the plate diagram/outline** in the brief (computed): A line 54.8 mm, B line 49.2 mm, B through lower hole 43.7 mm. The brief's hand values (36.5 / 56.4 mm) imply a different outline; with them the worst plate leg moves SF 0.60 → 0.65 (slip governs either way) |
