# Solar + battery for generic use cases

A reframing of Casey Handmer's
[*Solar and batteries for generic use cases*](https://caseyhandmer.wordpress.com/2024/11/09/solar-and-batteries-for-generic-use-cases/).

## The reframing

Handmer plots **optimal utilization vs load capex ($/kW)**. But "optimal" means
*profit-maximizing*, and capex alone can't define profit — it says nothing about
what the delivered energy is *worth*. The well-posed independent variable is
**load income ($/kWh delivered)**: the revenue signal that actually decides how
much solar + battery it pays to build.

The optimization is therefore stated directly on profit:

```
profit_per_year(S, B) = income_per_kWh · served_kWh(S, B)      [income]
                      − solar_cost_ann   · S                    [$/(kW·yr) · kW]
                      − battery_cost_ann · B                    [$/(kWh·yr) · kWh]
```

- **Optimal build** = the (S = kW solar, B = kWh battery) that maximizes annual profit.
- **Optimal utilization** = that winning build's `served / demand`.
- **Costs are annualized:** capex ÷ amortization period → `$/(kW·yr)`, directly
  comparable to annual income. Raw capex (`= annualized × years`) appears on chart
  twin axes.
- **Load capex is excluded** from the profit (secondary — it shifts profit by a
  constant and changes neither the optimal build nor the utilization).

`served_kWh(S, B)` is **pure physics, independent of every price**, so it is
computed once over the build grid, cached, and reused; all economic results are
then a cheap `argmax` over that single grid.

## Architecture (leaf → root, no cycles)

| layer | file | responsibility |
|---|---|---|
| config | `config.py` | every tunable: paths, costs, amortization, income, grids, sweeps |
| labels | `labels.py` | single source of truth for axis labels/units |
| model | `model.py` | physics: NSRDB load, GHI→generation, dispatch, **steady-state warm-start** |
| derived | `derived.py` | cached served grid + the profit optimization (cost plane, income sweep) |
| viz | `viz/` | bundled render / plotting / info_box / axis_range helpers (Agg, no pyplot) |
| charts | `charts/` | one module per chart family; each draws onto a provided Axes |
| run | `run.py` | thin entry point + findings report |

## Charts (`outputs/`, by family)

- **`utilization_vs_income/`** — the flagship: optimal utilization % vs load income
  ($/kWh). Handmer's S-curve on the correct axis.
- **`cost_plane/`** — optimal utilization and optimal profit over the
  (solar $/(kW·yr) × battery $/(kWh·yr)) plane at fixed income; capex twin axes.
- **`build_plane/`** — the (kW × kWh) landscape the optimizer chooses among, with
  the profit-optimum marked.
- **`timeseries/`** — annual dispatch for one build (sanity view of the physics).

## Warm-start

Dispatch is iterated to a **periodic SOC fixed point** (year-end SOC == year-start
SOC) rather than started from an empty battery. This removes the Jan-1 cold-start
artifact, so utilization can reach >99.8% instead of being capped by the first day.

## Run

```bash
python run.py            # build + save all charts (served grid cached after first run)
python run.py --count    # list planned charts without rendering
python run.py --no-cache # force-rebuild the served grid
```

Data: NSRDB 10-minute point files in `nsrdb_data/` (fetch via
`download_nsrdb_dataset.py`). The configured site is 836224 (34.86, −118.17;
capacity factor ≈ 25%).
