# Mojave Sphinx test stand — frame + joint safety model

## Cheat sheet (Ubuntu)

```bash
cd ~/Documents/git/charts-and-data-analysis/ubcrocket-8020-sphinx-test-stand
```

First time only (needs `sudo apt install python3-venv` if venv is missing):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Every session — activate, then everything is `python -m stand ...`:

```bash
source .venv/bin/activate
```

| do this | command |
|---|---|
| full 3D run → `results/3d/` | `python -m stand run` |
| 2D side frame → `results/2d/` | `python -m stand run --2d` |
| one load case → `results/variants/3d_case_px/` | `python -m stand run --case +x` |
| try a value without editing files → `results/variants/3d_DF2.5/` | `python -m stand run --set loads.DF=2.5` |
| re-draw figures only (no solve, ~10 s) | `python -m stand plots` |
| re-draw one chart family | `python -m stand.charts.joint_terms` |
| see every parameter / only changed ones | `python -m stand params` · `python -m stand params --changed` |
| how each joint was modelled | `python -m stand model` |
| validation tests | `python -m stand test` |
| open the interactive viewer | `xdg-open results/3d/viewer.html` |
| read the results | `results/3d/summary.md` (all figures inline) |
| restore params.yaml defaults | `python -m stand params --reset --yes` |

Edit `params.yaml` (units are in the key names); every run prints what differs from the
defaults at the top. A run with changed parameters writes to its own
`results/variants/<mode>_<changes>/` folder, so a variant never overwrites the baseline.

3D direct-stiffness frame solver (numpy; scipy only for eigenvalues) for UBC Rocket's
80/20 aluminium-extrusion engine test stand. Computes the factor of safety of every
member and every bolted bracket leg, frame buckling, thrust-point deflection/tilt and
the sandbag mass needed. A 2D side-frame mode reuses the same code.

## Outputs (`results/`)

See [`results/README.md`](results/README.md). `results/3d/` (design result) and `results/2d/`
share one layout: `summary.md` (with every figure inline), `viewer.html`, `figures/NN_*.png`,
`tables/{members,joints,ktheta_sweep}.csv`, `params_used.yaml`. Set `output.svg: true` for
editable SVGs next to the PNGs.

### Figures

| figure | shows |
|---|---|
| `01_stand_sf` | true-scale front / side / plan, members and joints coloured by SF |
| `02_sf_ranking` | lowest joint and member SFs, log scale |
| `03_joint_sf_terms` | joint SF (log) beside each failure term's share of the demand |
| `04_sf_by_case` | SF of the critical items in every load case |
| `05_thrust_by_case` | thrust-axis tilt and thrust-point displacement per case, vs the tilt limit |
| `06_axial_force` | load path: tension / compression, width ∝ \|N\| |
| `07_peak_stress` | peak combined stress per sub-element, vs σ_y/SF and σ_y |
| `08_deflection` | deflected shape of the worst-tilt case |
| `09_buckling_mode` | lowest frame buckling mode and λ |
| `10_sandbag_demand` | base line load in plan and the sandbag kg each base member needs |
| `11_ktheta_sweep` | SF vs joint rotational stiffness (the P/R bounding test) |

Colour is used by exception: red SF < 1, orange 1 ≤ SF < target, grey ≥ target. Each
chart's info box lists the inputs that move the result.

**Why SF on the axes but U in the joint maths:** the joint check is a linear interaction
sum, U = Σ demand/capacity over slip, pull, tilt, twist and plate bending, and SF = 1/U.
The terms add in U, not in SF, so `joints.csv` keeps every U term. Charts show SF on log
axes, and show the composition as each term's share of U.

## Model in one paragraph

Members are split at every joint / load point and into ≤125 mm Euler–Bernoulli
elements. Members never share nodes: each bracket is a zero-length 6-DOF spring at the
joint point with rigid arms to each member's centreline node; bearing (member end face
on another member) is a compression-only spring solved by active-set iteration. The
base is not fixed: the resultant of all applied loads is cancelled by a linear line
load on the base members (the sandbags), and a 3-2-1 restraint whose reactions are
checked to vanish removes rigid-body motion. Joint stiffness is bounded by run P
(k_θ = 1e-3·EI/L) and run R (1e3·EI/L), each with bearing ON/OFF, over six
misalignment cases, plus a 7-point k_θ sweep. Design value = worst over valid solves.
See `CLAUDE.md` for decisions and `ASSUMPTIONS.md` for every unconfirmed number.
