# Battery Energy Storage System (BESS) Costs — Dataset

Companion to `dam_costs.csv`. Covers BESS prices from 2010–2025 across vendors,
geographies, and cost-stack layers, intended for comparison with hydroelectric dam $/MW
costs to evaluate dam + BESS optimization.

## File

| File | Rows | Description |
|---|---|---|
| `bess_costs.csv` | 26 | BESS cost data points: market benchmarks, vendor list prices, and research benchmarks. Sorted by year. |

---

## Schema

| Column | Type | Description |
|---|---|---|
| `name` | str | Descriptive name for this data point |
| `vendor` | str | Company or research organization |
| `country` | str | Vendor HQ country, or `Global` / `Ex-China-US` for benchmarks |
| `year` | int | Year the price applies to (not year published) |
| `cost_usd_per_kwh` | float\|empty | Cost in USD per kWh of storage capacity. Empty = price not publicly disclosed |
| `cost_type` | str | One of four levels (see below) |
| `chemistry` | str | `LFP`, `NMC`, `Zn-Br`, `Li-ion_mixed` |
| `duration_hr` | int\|empty | Storage duration in hours. Empty for cell/pack benchmarks not tied to a duration |
| `market` | str | `China`, `US`, `Global`, `Ex-China-US` |
| `scale` | str | `utility`, `C&I`, `residential`, `cell_market` |
| `notes` | str | Caveats, context, what is and isn't included |
| `source_url` | str | Primary source |

---

## Cost type definitions — critical for apples-to-apples comparison

This is the single most important thing to understand about BESS pricing. The gap between
the cell price you read about in headlines and the all-in project capex you actually pay
can be 3–5×. Every number in this dataset is tagged with one of four levels:

```
cell              Raw cells ex-factory. No pack assembly, no inverter, no BOS.
                  BYD $44/kWh, CATL $56/kWh (2024).

pack              Cells + module/pack assembly. No inverter, no enclosure, no civil.
                  BNEF global avg: $108/kWh (2025).

turnkey_system    Complete DC or AC block: cells + BMS + PCS + enclosure + thermal mgmt.
                  Ships to site. Excludes civil works, grid connection, EPC.
                  Tesla Megapack list price: $266/kWh (Jul 2024), hardware only.
                  BNEF global avg turnkey: $110/kWh (2025).
                  China domestic tender: $66/kWh (2025).

all_in_installed  Full project capex: turnkey system + EPC + civil + grid connection.
                  This is what goes into a financial model.
                  NREL US benchmark: $334/kWh (2024 USD).
                  Ember (ex-CN, ex-US): $125/kWh (Oct 2025).
                  Tesla Megapack installed (Q2 2025): ~$290/kWh.
```

The BNEF $70/kWh pack price and the NREL $334/kWh all-in installed price are for the
**same year and chemistry** — they just measure different things. Both are correct.

---

## Quick start

```python
import pandas as pd

df = pd.read_csv("bess_costs.csv")

# Filter to comparable all-in-installed costs only
installed = df[df["cost_type"] == "all_in_installed"].copy()

# Tesla Megapack price history (hardware only, turnkey_system)
tesla = df[(df["vendor"] == "Tesla") & (df["cost_type"] == "turnkey_system")]
print(tesla[["year", "cost_usd_per_kwh", "notes"]])

# Compare to dam costs
dams = pd.read_csv("dam_costs.csv")
dams_costed = dams[dams["has_cost_data"]]
print(f"Dam range: ${dams_costed['usd_per_mw_2025'].min():,.0f} – ${dams_costed['usd_per_mw_2025'].max():,.0f} /MW")
# Note: dam $/MW vs BESS $/MWh — need to account for duration to compare
```

---

## Key observations

### The cost stack gap
China domestic tender price in 2025: **$66/kWh** (all-in for 2025–2026 systems).
NREL US all-in benchmark: **$334/kWh** (2024).
The 5× gap is real: US has higher labor, permitting, grid interconnection, and fire code costs.
The BNEF global average **$117/kWh turnkey** sits in between because it averages all markets.

### Tesla Megapack price trajectory
| Year | $/kWh | Note |
|---|---|---|
| 2021 | $280 | First public pricing, 100-unit discount, NMC, Nevada factory |
| 2022 | $412–475 | Price hike during supply crunch; then LFP Lathrop factory opens |
| 2023 | $482 | Peak |
| 2024 | $266 | -44% from 2023 peak; Shanghai factory online |
| 2025 | ~$290 | Installed cost (incl. labor); hardware-only likely ~$220–240 |

Tesla list prices are hardware-only. Adding installation typically adds $150–250/kWh,
bringing the true all-in project cost to $400–550/kWh in the US for a utility project.

### China dominance
- BYD cell price: **$44/kWh** (2024) — lowest globally
- CATL cell price: **$56/kWh** (2024)
- China domestic BESS tender (16 GWh, 2025): **avg $66/kWh** all-in including 20-yr maintenance
- BNEF stationary LFP pack: **$70/kWh** (2025 global avg but driven by Chinese producers)

Chinese manufacturers benefit from: vertically integrated supply chains (Li mining →
cathode → cell → pack), lower labor, energy, and permitting costs, and production
overcapacity that compresses margins aggressively.

### EOS Energy (Znyth zinc-bromine)
Long-duration energy storage (LDES) play; 3–12 hour discharge. Aqueous zinc-bromine —
non-flammable, no thermal runaway risk. Originally targeted $200–250/kWh in 2014 with a
path to $160/kWh. Current pricing not publicly disclosed; company is pre-profitability
with $682M backlog (~2.6 GWh) as of end-2024. Relevant as an alternative to Li-ion for
applications where fire safety or cycle life matters more than energy density.

### BYD Haohan $0.014/kWh
This is **LCOS (levelized cost of storage)**, not capex — BYD's claimed lifetime cost per
kWh cycled over 10,000+ cycles. Do not compare to $/kWh capex figures. Included because
it illustrates the direction of the market: at 10,000 cycles over 20 years, even a
$200/kWh capex system can reach <$0.03/kWh LCOS.

### Dam comparison note
Dam $/MW (power capacity) vs BESS $/MWh (energy capacity) require duration to bridge:
- A 4-hour BESS at $125/kWh all-in = **$500,000/MW** of discharge power
- A 8-hour BESS at $125/kWh all-in = **$1,000,000/MW** of discharge power
- Site C dam: **$13.6M/MW** (2025$)

So a 4-hour BESS is ~27× cheaper per MW than Site C — but provides only 4 hours of
storage vs. a dam that can dispatch continuously. The optimization question in the blog
post is: at what ratio of dam downsizing + BESS addition does total system cost minimize
while matching the original energy delivery profile?

---

## Sources

| Source | What it covers | URL |
|---|---|---|
| BloombergNEF ESSC Survey 2025 | Global avg turnkey BESS $117/kWh; 4-hr $110/kWh | https://www.energy-storage.news/battery-storage-system-prices-continue-to-fall-sharply-bnef-and-ember-reports-find/ |
| BloombergNEF Li-ion Price Survey 2025 | Pack price $108/kWh; LFP stationary $70/kWh | https://about.bnef.com/insights/clean-transport/lithium-ion-battery-pack-prices-fall-to-108-per-kilowatt-hour-despite-rising-metal-prices-bloombergnef/ |
| Ember "How cheap is battery storage?" Oct 2025 | All-in $125/kWh ex-US/China; LCOS $65/MWh | https://ember-energy.org/latest-insights/how-cheap-is-battery-storage/ |
| NREL Cost Projections 2025 Update | US utility-scale 4-hr: $334/kWh | https://research-hub.nrel.gov/en/publications/cost-projections-for-utility-scale-battery-storage-2025-update/ |
| pv-magazine — Tesla pricing Jul 2024 | Megapack $266/kWh after 44% drop | https://pv-magazine-usa.com/2024/07/03/tesla-battery-deployment-up-157-megapack-pricing-down-44/ |
| Electrek — Tesla 2021 pricing | First public Megapack prices $280–333/kWh | https://electrek.co/2021/07/26/tesla-reveals-megapack-prices/ |
| Medium/Barnard — China $66/kWh tender | 16 GWh China Power Construction bid avg | https://medium.com/the-future-is-electric/grid-storage-at-66-kwh-the-world-just-changed-c2f39f42f09f |
| CleanTechnica — BYD Haohan | 14.5 MWh unit, LCOS $0.014/kWh | https://cleantechnica.com/2025/09/23/byds-new-14-5-mwh-haohan-bess-pushing-energy-storage-performance-cost-past-tipping-points/ |
| BSLBATT — 2025 market overview | BYD $44/kWh cell; BEV pack trends | https://bslbatt.com/blogs/current-average-energy-storage-cost-2025/ |
| Utility Dive — EOS 2013 pricing | EOS $200–250/kWh target (2014) | https://www.utilitydive.com/news/eos-battery-storage-will-be-cost-competitive-in-18-months/207750/ |
| energy-storage.news — EOS 2024/2025 | EOS backlog, DOE loan, no public pricing | https://www.energy-storage.news/us-zinc-bess-manufacturer-eos-guides-for-tenfold-revenue-increase-year-on-year/ |
| Solar Power World — Sungrow PowerTitan 3.0 | 6.9 MWh/20-ft, specs, no public price | https://www.solarpowerworldonline.com/2025/09/sungrow-powertitan-3-0-bess-reaches-6-9-mwh-in-20-ft-container/ |
