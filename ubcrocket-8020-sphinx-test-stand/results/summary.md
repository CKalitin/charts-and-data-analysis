# Mojave Sphinx stand — 3D safety summary

params: `params.yaml` · 24 solves + 7 sweep · targets: member SF ≥ 2, joint SF ≥ 2 (DF = 2 already in the loads)

## Headline

| quantity | value | governing |
|---|---|---|
| lowest joint SF | **0.08** (N5 triangle leg a on M34, U_Mz) | k=1-bOFF/+x+y |
| lowest member SF | **1.76** (M18 yield) | k=1-bOFF/+x+y |
| frame buckling λ | **14.94** (pass vs 2) | k=1-bOFF/+x+y |
| thrust-point deflection | 36.83 mm (x -14.71, y +32.46, z +9.31) | k=1-bOFF/+x+y |
| thrust-point tilt | 1.926° **> 0.25° flag** | k=1-bOFF/+x+y |
| sandbag mass (net uplift / g) | **196.4 kg** (1926 N) | all cases |
| sandbag mass if spread uniformly on the base | 911 kg (overturning 1368 N·m about the base centroid) | worst case |
| 3-2-1 restraint reactions | 3.1e-09 × thrust (ok) | all valid solves |

Displacements are relative to the best-fit rigid motion of the base nodes (i.e. to the ground).

## Lowest 10 joint SFs

SF = 1/U with U = Σ term demand/capacity (linear interaction). *Share* = that term's part of U; *SF if alone* = the SF if only that term acted.

| SF | joint | bracket | type | leg | on | governs | share | SF if alone | run/case |
|---|---|---|---|---|---|---|---|---|---|
| 0.08 | N5 | 1 | triangle | a | M34 | twist Mz | 98 % | 0.09 | k=1-bOFF/+x+y |
| 0.09 | N7 | 1 | triangle | b | M25 | twist Mz | 91 % | 0.09 | R-bOFF/+x+y |
| 0.09 | N5 | 0 | triangle | a | M28 | twist Mz | 99 % | 0.09 | R-bOFF/-x |
| 0.09 | N6 | 0 | triangle | a | M23 | twist Mz | 99 % | 0.09 | R-bOFF/-x |
| 0.09 | N2 | 1 | triangle | a | M23 | twist Mz | 97 % | 0.09 | R-bOFF/-x |
| 0.09 | N1 | 1 | triangle | b | M28 | twist Mz | 97 % | 0.09 | R-bOFF/-x |
| 0.09 | N6 | 1 | triangle | a | M31 | twist Mz | 97 % | 0.09 | R-bOFF/-y |
| 0.09 | N8 | 1 | triangle | a | M19 | twist Mz | 90 % | 0.10 | R-bOFF/-y |
| 0.10 | N2 | 0 | triangle | a | M33 | twist Mz | 97 % | 0.11 | R-bOFF/+y |
| 0.10 | N1 | 0 | triangle | b | M16 | twist Mz | 97 % | 0.11 | R-bOFF/-y |

## Lowest 10 member SFs

| SF | member | profile | governs | σ (MPa) | N (N) | My (N·m) | Mz (N·m) | SF yield | SF buckle | SF beam-col | run/case |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.76 | M18 | 1010 | yield | 97.5 | 336 | 14.2 | -125.4 | 1.76 | 194588.64 | 77284.86 | k=1-bOFF/+x+y |
| 1.90 | M17 | 1010 | yield | 90.3 | 78 | 0.8 | -129.7 | 1.90 | 2535.07 | 2.08 | k=1-bOFF/+x+y |
| 1.93 | M32 | 1010 | yield | 89.3 | 389 | -1.4 | -126.1 | 1.93 | 194588.64 | 77284.86 | k=1-bOFF/+x+y |
| 2.02 | M19 | 1010 | yield | 85.0 | 58 | -4.6 | -118.3 | 2.02 | 4700.15 | 2.88 | R-bOFF/-y |
| 2.02 | M25 | 1010 | yield | 85.0 | 58 | 4.5 | -118.3 | 2.02 | 3114.86 | 2.88 | R-bOFF/+y |
| 2.41 | M23 | 1010 | beam-col | 71.2 | -19 | 0.0 | 103.0 | 2.42 | 2153.30 | 2.41 | R-bON/+y |
| 2.41 | M28 | 1010 | beam-col | 71.2 | -19 | -0.0 | 103.0 | 2.42 | 2154.61 | 2.41 | R-bON/-y |
| 3.27 | M9 | 1010 | beam-col | 48.3 | -423 | -13.3 | 54.5 | 3.56 | 23.90 | 3.27 | R-bON/+y |
| 3.27 | M7 | 1010 | beam-col | 48.3 | -423 | 13.2 | 54.5 | 3.56 | 23.92 | 3.27 | R-bON/-y |
| 3.94 | M6 | 1010 | yield | 43.7 | 4 | 0.9 | 62.4 | 3.94 | 524.04 | 4.92 | k=1-bOFF/+x+y |

## Mechanism checks

- **Run P invalid** for cases none, +x, -x, +y, -y, +x+y: a node moves more than 1 mm → *mechanism — pinned result invalid; joints carry moment*. Run R used for those cases.
- P-bON: lowest K eigenvalue / max diag = 2.49e-13 **(mechanism)**; softest mode dominated by node 105 (M14 s=150 mm) uy, node 184 (M27 s=150 mm) uy, node 85 (M10 s=210 mm) uy
- P-bOFF: lowest K eigenvalue / max diag = 8.67e-14 **(mechanism)**; softest mode dominated by node 64 (M7 s=667 mm) rz, node 65 (M7 s=778 mm) rz, node 80 (M9 s=667 mm) rz
- R-bON: lowest K eigenvalue / max diag = 1.76e-10; softest mode dominated by node 79 (M9 s=556 mm) rz, node 63 (M7 s=556 mm) rz, node 78 (M9 s=444 mm) rz
- R-bOFF: lowest K eigenvalue / max diag = 1.78e-10; softest mode dominated by node 63 (M7 s=556 mm) rz, node 79 (M9 s=556 mm) rz, node 62 (M7 s=444 mm) rz

## k_θ sweep (+x+y, bearing OFF)

| k_θ / (EI/L) | max node δ (mm) | valid | λ | lowest SF |
|---|---|---|---|---|
| 0.001 | 2.18e+04 | no | 0.03 | 0.08 (N6#0.0:a) |
| 0.01 | 2.19e+03 | no | 0.34 | 0.08 (N6#0.0:a) |
| 0.1 | 237 | no | 2.85 | 0.08 (N5#1.0:a) |
| 1 | 37.6 | yes | 14.94 | 0.08 (N5#1.0:a) |
| 10 | 15.4 | yes | 34.34 | 0.09 (N5#1.0:a) |
| 100 | 12.8 | yes | 42.02 | 0.09 (N7#1.0:b) |
| 1000 | 12.5 | yes | 43.24 | 0.09 (N7#1.0:b) |

Items whose utilisation peaks at an interior k_θ (value used in the envelope):

- M14: U = 0.123 at k = 10 (ends 0.122 / 0.085)
- M16: U = 0.066 at k = 100 (ends 0.066 / 0.066)
- M20: U = 0.028 at k = 100 (ends 0.028 / 0.028)
- N1#0.0:a: U = 0.700 at k = 10 (ends 0.700 / 0.700)
- N10#0.0:a: U = 3.004 at k = 10 (ends 2.757 / 2.987)
- N10#0.0:b: U = 2.008 at k = 10 (ends 1.994 / 1.932)
- N11#0.0:b: U = 2.384 at k = 10 (ends 2.310 / 2.355)
- N12#0.0:b: U = 2.430 at k = 100 (ends 2.333 / 2.427)
- N13#1.0:a: U = 0.441 at k = 10 (ends 0.345 / 0.429)
- N13#1.0:b: U = 0.629 at k = 10 (ends 0.619 / 0.590)
- N14#0.0:a: U = 0.433 at k = 100 (ends 0.279 / 0.433)
- N14#1.0:a: U = 0.604 at k = 10 (ends 0.603 / 0.581)
- N14#1.0:b: U = 0.437 at k = 10 (ends 0.369 / 0.401)
- N15#0.0:a: U = 0.687 at k = 100 (ends 0.420 / 0.683)
- N24#0.0:a: U = 0.502 at k = 100 (ends 0.357 / 0.496)
- N27#0.0:b: U = 3.575 at k = 100 (ends 3.036 / 3.533)
- N28#0.0:b: U = 3.750 at k = 10 (ends 3.494 / 3.581)

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
| plate_other brackets | — | no capacity | forces reported only |
