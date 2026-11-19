# Mojave Sphinx stand — 2D safety summary

params: `params.yaml` · 12 solves + 7 sweep · targets: member SF ≥ 2, joint SF ≥ 2 (DF = 2 already in the loads)

> 2D: cross members kept as joint stubs (load path between front members): M26@N18, M20@N2, M35@N20, M36@N28, M3@N6, M22@N8

> 2D: thrust/rocket loads (x0.5) moved from M17 to M14 at N30

## Headline

| quantity | value | governing |
|---|---|---|
| lowest joint SF | **0.08** (N8 triangle leg a on M19, U_Mz) | R-bON/+x |
| lowest member SF | **1.95** (M32 yield) | k=1-bON/+x |
| frame buckling λ | **60.02** (pass vs 2) | k=1-bON/+x |
| thrust-point deflection | 15.38 mm (x -12.63, y +0.00, z +8.77) | k=1-bON/+x |
| thrust-point tilt | 1.968° **> 0.25° flag** | k=1-bON/+x |
| sandbag mass (net uplift / g, FS 1) | **98.2 kg** (963 N) | all cases |
| sandbag mass if spread uniformly on the base | 369 kg (overturning 681 N·m about the base centroid) | worst case |
| 3-2-1 restraint reactions | 3.3e-10 × thrust (ok) | all valid solves |

Displacements are relative to the best-fit rigid motion of the base nodes (i.e. to the ground).

**In this folder:** [figures](#figures) (below, and in `figures/`) · `viewer.html` (interactive 3D, click any bracket for its free-body diagram; download and open locally) · `tables/members.csv`, `tables/joints.csv`, `tables/ktheta_sweep.csv` · `params_used.yaml` (exact inputs of this run)

## Lowest 10 joint SFs

SF = 1/U with U = Σ term demand/capacity (linear interaction). *Share* = that term's part of U; *SF if alone* = the SF if only that term acted.

| SF | joint | bracket | type | leg | on | governs | share | SF if alone | run/case |
|---|---|---|---|---|---|---|---|---|---|
| 0.08 | N8 | 1 | triangle | a | M19 | twist Mz | 97 % | 0.08 | R-bON/+x |
| 0.08 | N2 | 1 | triangle | a | M23 | twist Mz | 98 % | 0.08 | R-bOFF/-x |
| 0.10 | N2 | 0 | triangle | a | M33 | twist Mz | 97 % | 0.10 | R-bOFF/-x |
| 0.11 | N8 | 0 | triangle | a | M31 | twist Mz | 96 % | 0.11 | R-bON/+x |
| 0.14 | N6 | 0 | triangle | a | M23 | twist Mz | 98 % | 0.14 | R-bOFF/-x |
| 0.17 | N6 | 1 | triangle | a | M31 | twist Mz | 98 % | 0.17 | k=1-bON/+x |
| 0.19 | N20 | 2 | triangle | a | M6 | twist Mz | 67 % | 0.28 | k=1-bON/+x |
| 0.20 | N20 | 2 | triangle | b | M35 | twist Mz | 69 % | 0.28 | k=1-bON/+x |
| 0.21 | N20 | 1 | triangle | a | M5 | twist Mz | 66 % | 0.31 | k=1-bON/+x |
| 0.22 | N20 | 1 | triangle | b | M35 | twist Mz | 68 % | 0.32 | k=1-bON/+x |

## Lowest 10 member SFs

| SF | member | profile | governs | σ (MPa) | N (N) | My (N·m) | Mz (N·m) | SF yield | SF buckle | SF beam-col | run/case |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.95 | M32 | 1010 | yield | 88.1 | 359 | -0.0 | -125.8 | 1.95 | 194588.64 | 77284.86 | k=1-bON/+x |
| 2.16 | M19 | 1010 | yield | 79.6 | 8 | 0.0 | -115.3 | 2.16 | 2750.78 | 2.36 | R-bON/-x |
| 2.69 | M23 | 1010 | beam-col | 63.9 | -11 | -0.0 | 92.5 | 2.69 | 3660.18 | 2.69 | R-bOFF/-x |
| 3.85 | M7 | 1010 | beam-col | 38.8 | -624 | -0.0 | 53.0 | 4.43 | 25.65 | 3.85 | R-bOFF/-x |
| 4.32 | M6 | 1010 | yield | 39.8 | 42 | -0.0 | 57.4 | 4.32 | 516.98 | 5.43 | k=1-bON/+x |
| 5.28 | M15 | 1010 | yield | 32.6 | 1648 | -0.0 | -38.8 | 5.28 | inf | inf | k=1-bON/+x |
| 5.38 | M33 | 1010 | beam-col | 32.0 | -8 | -0.0 | 46.3 | 5.38 | 4007.00 | 5.38 | R-bOFF/-x |
| 6.11 | M31 | 1010 | yield | 28.1 | 21 | 0.0 | -40.7 | 6.11 | inf | inf | R-bON/+x |
| 6.84 | M29 | 1010 | beam-col | 21.1 | -341 | -0.0 | -28.9 | 8.14 | 36.74 | 6.84 | R-bOFF/-x |
| 8.47 | M5 | 1010 | beam-col | 19.5 | -340 | -0.0 | 26.5 | 8.81 | 94.88 | 8.47 | R-bOFF/-x |

## Mechanism checks

- **Run P invalid** for cases none, +x, -x: a node moves more than 1 mm → *mechanism — pinned result invalid; joints carry moment*. Run R used for those cases.
- P-bON: lowest K eigenvalue / max diag = 4.73e-13 **(mechanism)**; softest mode dominated by node 87 (M33 s=0 mm) ry, node 88 (M33 s=100 mm) ry, node 89 (M33 s=200 mm) ry
- P-bOFF: lowest K eigenvalue / max diag = 1.49e-13 **(mechanism)**; softest mode dominated by node 86 (M32 s=980 mm) ux, node 94 (M36 s=250 mm) ux, node 33 (M14 s=150 mm) ux
- R-bON: lowest K eigenvalue / max diag = 5.73e-10; softest mode dominated by node 86 (M32 s=980 mm) ux, node 33 (M14 s=150 mm) ux, node 32 (M14 s=134 mm) ux
- R-bOFF: lowest K eigenvalue / max diag = 5.73e-10; softest mode dominated by node 86 (M32 s=980 mm) ux, node 33 (M14 s=150 mm) ux, node 32 (M14 s=134 mm) ux

## k_θ sweep (+x, bearing ON)

| k_θ / (EI/L) | max node δ (mm) | valid | λ | lowest SF |
|---|---|---|---|---|
| 0.001 | 1.66e+04 | no | 48.93 | 0.04 (N20#2.0:a) |
| 0.01 | 1.63e+03 | no | 49.25 | 0.04 (N20#2.0:a) |
| 0.1 | 140 | no | 51.55 | 0.05 (N20#2.0:a) |
| 1 | 15.8 | yes | 60.02 | 0.10 (N8#1.0:a) |
| 10 | 8.51 | yes | 85.87 | 0.09 (N8#1.0:a) |
| 100 | 7.88 | yes | 106.92 | 0.08 (N8#1.0:a) |
| 1000 | 7.81 | yes | 110.37 | 0.08 (N8#1.0:a) |

Items whose utilisation peaks at an interior k_θ (value used in the envelope):

- M19: U = 0.384 at k = 10 (ends 0.384 / 0.384)
- M29: U = 0.046 at k = 10 (ends 0.043 / 0.042)
- N12#0.0:a: U = 0.290 at k = 10 (ends 0.274 / 0.275)
- N12#0.0:b: U = 0.200 at k = 10 (ends 0.194 / 0.179)
- N14#0.0:a: U = 0.424 at k = 100 (ends 0.289 / 0.422)
- N14#0.0:b: U = 0.523 at k = 100 (ends 0.355 / 0.518)
- N2#0.0:a: U = 5.892 at k = 10 (ends 5.892 / 5.892)
- N2#0.0:b: U = 1.231 at k = 10 (ends 1.231 / 1.231)
- N2#1.0:a: U = 7.130 at k = 10 (ends 7.130 / 7.130)
- N2#1.0:b: U = 1.231 at k = 10 (ends 1.231 / 1.231)
- N28#0.0:b: U = 3.500 at k = 10 (ends 3.154 / 3.405)
- N28#1.0:b: U = 0.449 at k = 10 (ends 0.195 / 0.400)
- N28#2.0:a: U = 0.335 at k = 10 (ends 0.239 / 0.324)

## Joint capacities used

- friction per bolt μF_i = 1000 N, pull F_i = 5000 N, triangle tilt M = F_i·a = 63.5 N·m, twist μF_i·r_f = 4.63 N·m (r_f = 4.63 mm)
- T-plate sections (computed from the outline): A line b_net = 54.8 mm (brief 54.8); B line 49.2 mm (brief 36.5); B through lower hole 43.7 mm (brief 56.4); stem neck 76.2 mm (added check)

## Unverified inputs

| parameter | value | flag | meaning |
|---|---|---|---|
| `triangle.tilt_arm_mm` | 12.7 mm | placeholder | gap-opening arm a: Mx,max = My,max = F_i*a |
| `plate.thickness_mm` | 6.35 mm | placeholder | plate thickness t |
| `section_1010.J_mm4` | auto mm4 | unverified | torsion constant; auto = 0.5*(Iy+Iz) |
| `section_1020.J_mm4` | auto mm4 | unverified | torsion constant; auto = 0.5*(Iy+Iz) |
| `loads.misalign_x` | 0.03 - | assumption | horizontal x load as fraction of factored thrust |
| `loads.misalign_y` | 0.03 - | assumption | horizontal y load as fraction of factored thrust |
| `bolts.preload_N` | 5000 N | assumption | 1/4-20 bolt preload F_i |
| `bolts.mu` | 0.2 - | assumption | friction coefficient, one surface |
| `base.mode` | line | assumption | line = brief: sandbag line load that exactly balances the stand | ground = base on compression-only gravel springs + discrete sandbags (3D only; `run --ground`) |
| `ground.k_s_MN_per_m3` | 150 MN/m3 | assumption | modulus of subgrade reaction, compacted gravel (typical 100-200) |
| `ground.kh_ratio` | 0.5 - | assumption | horizontal / vertical contact stiffness (friction, sticking) |
| `ground.mu` | 0.5 - | assumption | aluminium on gravel friction, for the sliding check |
| `sandbags.stations` | [[19, 225, 300], [25, 225, 300], [22, 522.5, 155], [22, 77.5, 155]] | assumption | bags: [member, centre along member mm, length mm]; default = thrust-end outriggers M19/M25 under the thrust line + both stubs of cross beam M22 |
| `sandbags.FS_tip` | 1.5 - | assumption | stabilising / overturning moment about every footprint edge (and lift) |
| plate_other brackets | — | no capacity | forces reported only |

## Figures

### Safety factor by member and joint (front / side / plan)

![stand_sf](figures/01_stand_sf.png)

### Lowest safety factors

![sf_ranking](figures/02_sf_ranking.png)

### Joint SF and the share of each failure term

![joint_sf_terms](figures/03_joint_sf_terms.png)

### SF of the critical items in every load case

![sf_by_case](figures/04_sf_by_case.png)

### Thrust-point tilt and deflection by load case

![thrust_by_case](figures/05_thrust_by_case.png)

### Member axial force (load path)

![axial_force](figures/06_axial_force.png)

### Peak combined stress

![peak_stress](figures/07_peak_stress.png)

### Deflected shape (worst-tilt case)

![deflection](figures/08_deflection.png)

### Frame buckling mode

![buckling_mode](figures/09_buckling_mode.png)

### Sandbag demand on the base

![sandbag_demand](figures/10_sandbag_demand.png)

### SF vs joint rotational stiffness

![ktheta_sweep](figures/11_ktheta_sweep.png)

