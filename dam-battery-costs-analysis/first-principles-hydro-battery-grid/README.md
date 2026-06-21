# First-principles BPA hydro + battery grid sizing

Takes BPA's **2024 native control-area load** (5-minute resolution, exports excluded — the
`TOTAL BPA CONTROL AREA LOAD` column; NET INTERCHANGE is separate) and sizes a firm-hydro +
battery system to serve it.

## Model
- **Hydro** is firm/dispatchable: up to its MW rating at any instant, *no* energy limit.
- **Battery**: 87% round-trip (loss at charge), energy-capped only (power unconstrained),
  commissioned pre-charged.
- Each 5-min interval: hydro serves load up to its cap and charges the battery with spare
  capacity; if load exceeds the cap, the battery discharges 1:1 to cover the deficit.
- **Utilization** = served energy ÷ total load energy.
- Costs: hydro $3M/MW (50 yr), battery $200k/MWh (20 yr). LCOE = annualised cost ÷ served energy.

## Run
```
python run.py            # all charts -> outputs/
python run.py --count    # dry-run chart count
```
Each module is independently runnable (`python model/simulate.py`, `python charts/heatmaps.py`, …).

## 2024 load
Peak 11.44 GW · mean 6.63 GW · 58.2 TWh/yr · min 4.58 GW.

## Headline finding
The min-cost design serving ≥99.99% of load is **10.1 GW hydro + 8.1 GWh battery** ($31.9B,
LCOE $11.8/MWh). At $200k/MWh the optimum keeps hydro near *peak* load and buys almost no
battery: load exceeds the 10.1 GW hydro cap only **~40 hours/year** (mostly the Jan 13 cold
snap), so the battery cycles only **~2×/year** — it is cheap peak insurance, not a daily asset.
On the utilization heatmap this shows as near-horizontal contours: at the 0–200 GWh scale the
battery has almost no leverage; firm unlimited-energy hydro just needs roughly peak capacity.

## Outputs
- `outputs/heatmaps/` — utilization, system cost, LCOE, LCOE+utilization contours (design point starred)
- `outputs/timeseries/bpa_dispatch_daily_2024.png` — daily hydro generation + battery throughput
- `outputs/timeseries/quarter_days/` — first day of each quarter, 5-min
- `outputs/timeseries/months/` — each month, 5-min
