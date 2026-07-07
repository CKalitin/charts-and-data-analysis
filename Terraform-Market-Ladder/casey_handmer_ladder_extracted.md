# Extracted data points — Casey Handmer / Terraform Industries market-ladder charts

**Source: two chart images supplied directly by the user in this conversation** (methanol ladder
and methane ladder, attributed to "Casey Handmer's analysis"). This is a **manual transcription of
labeled data points from those images**, not an independently sourced or verified dataset.

> ⚠️ **Provenance flag.** The original research task in this repo
> ([`methane_methanol_market_ladder.csv`](methane_methanol_market_ladder.csv) /
> [`.md`](methane_methanol_market_ladder.md)) explicitly excluded Terraform Industries' blog and
> Casey Handmer's writing as sources, and was independently sourced from EIA/IEA/IGU/S&P
> Global/etc. **This file is the opposite: it is extracted verbatim from Casey Handmer/Terraform
> chart images the user pasted in**, per an explicit follow-up request. Treat the two files as
> separate, non-comparable datasets — do not merge them into one "verified" table, and do not
> cite this file's numbers as independently confirmed. Values below reflect what is printed on the
> source charts; I have not re-derived or checked them against primary data.

**Companion data file:** [`casey_handmer_ladder_extracted.csv`](casey_handmer_ladder_extracted.csv)

---

## Chart 1 — Methanol ladder

**Title (as printed):** "Methanol ladder: packaged-solvent beachhead, descending to fuels;
blue=AA, green=purified, purple=MTX"

- **Y-axis:** Max methanol synthesis cost / sale price ($/tonne) — must FALL (log scale)
- **X-axis:** Cumulative production deployed (units = Terraformers, ~87 t methanol/yr each) (log scale)
- **Series/legend color coding:**
  - dark blue — product sold as-is (packaged, marine fuel, bulk AA)
  - green — requires additional purification beyond AA
  - purple — requires MTX conversion (fuels / petrochem)
  - red — aggregate cost path (learning-rate-driven cost decline)
  - red dot — "tier saturation corner" (price/volume kink where one tier's demand is fully served)
  - teal square — cumulative market size to this point ($/yr)
  - tan/orange shaded region — "beachhead" (full retail price at small scale)

### Tier data points (descending price, left to right on chart)

| # | Segment | Price ceiling | Cumulative market size ($/yr) | Category (chart color) |
|---|---------|---------------|-------------------------------|-------------------------|
| 1 | Packaged consumer solvent (**BEACHHEAD**) | ≤ $3,000/t | $90M/yr | sold as-is (blue) |
| 2 | Semiconductor / electronic grade | ≤ $2,000/t | $190M/yr | requires purification (green) |
| 3 | HPLC / LC-MS analytical grade | ≤ $1,300/t | $216M/yr | requires purification (green) |
| 4 | USP / pharma grade | ≤ $700/t | $426M/yr | requires purification (green) |
| 5 | Grade AA methanol (bulk) | ≤ $450/t | $45B/yr | sold as-is (blue) |
| 6 | MTX aromatics / olefins | ≤ $267/t | $462B/yr | requires MTX conversion (purple) |
| 7 | Direct methanol marine fuel | ≤ $250/t | $615B/yr | sold as-is (blue) |
| 8 | MTG gasoline | ≤ $223/t | $1.26T/yr | requires MTX conversion (purple) |
| 9 | MTX diesel | ≤ $190/t | $2.11T/yr | requires MTX conversion (purple) |
| 10 | MTX jet / Jet-A | ≤ $167/t | $2.31T/yr | requires MTX conversion (purple) |

**Note on "cumulative market size":** per the chart's own legend (teal square = "cumulative market
size to this point"), these $/yr figures are **cumulative**, i.e. the total addressable market
unlocked by the time cost has fallen to that tier's price ceiling — not each tier's standalone
incremental size. This differs from the incremental-per-tier framing used in
[`methane_methanol_market_ladder.csv`](methane_methanol_market_ladder.csv).

### Additional annotations on the chart

- **Starting synthesis cost (small scale):** $800/t — orange star/arrow marker, labeled "start $800/t"
- **Aggregate cost path:** labeled "aggregate cost path (LR=6.5%, 25% end margin)" — a learning-rate
  (Wright's law) curve with **LR = 6.5%**, ending at **$134/t = 25% margin on jet fuel netback**
  (i.e. the terminal synthesis cost the curve converges to, priced at a 25% margin under the jet
  tier's netback value)

---

## Chart 2 — Methane ladder

**Title (as printed):** "Methane ladder: CP-methane beachhead at top, descending to Henry Hub bulk"

- **Y-axis:** Max methane synthesis cost / sale price ($/MMBtu-equiv) — must FALL (log scale)
- **X-axis:** Cumulative production deployed (units = Terraformers, ~2.4 MMcf CH4/yr each) (log scale)
- **Series/legend color coding:**
  - dark blue — Terraform CP methane sold as-is (packaged, fuel, bulk)
  - red — aggregate cost path (learning-rate-driven cost decline)
  - red dot — "tier saturation corner"
  - teal square — cumulative market size to this point ($/yr)
  - tan/orange shaded region — "beachhead" (full retail price at small scale)

### Tier data points (descending price, left to right on chart)

| # | Segment | Price ceiling | Cumulative market size ($/yr) | Category (chart color) |
|---|---------|---------------|-------------------------------|-------------------------|
| 1 | CP methane (99.5%) packaged (**BEACHHEAD**) | $495/MMBtu | $180M/yr | sold as-is (blue) |
| 2 | Strategic / remote (diesel displacement) | $45/MMBtu | $23B/yr | sold as-is (blue) |
| 3 | RNG western US (D3 RIN + LCFS) | $35/MMBtu | $94B/yr | sold as-is (blue) |
| 4 | Asian LNG spot (JKM) | $18.9/MMBtu | $208B/yr | sold as-is (blue) |
| 5 | European (TTF) | $15.5/MMBtu | $271B/yr | sold as-is (blue) |
| 6 | Global bulk (Henry Hub) | $3.0/MMBtu | $698B/yr | sold as-is (blue) — bulk floor |

### Additional annotations on the chart

- **Starting synthesis cost (small scale):** $30/Mcf ($29.7/MMBtu) — orange star/arrow marker,
  labeled "start $30/MCF ($29.7/MMBtu)"
- **Aggregate cost path:** labeled "aggregate cost path (LR=10.7%, 25% end margin)" — a
  learning-rate (Wright's law) curve with **LR = 10.7%**, ending at **$2.4/MMBtu = 25% margin on
  Henry Hub** (terminal synthesis cost at a 25% margin under the Henry Hub bulk price)

---

## Cross-chart structural notes

- Both charts share the same layout grammar: log-log axes, a "beachhead" shaded region at top-left
  (full retail price, tiny volume), a staircase of tiers descending in price as cumulative
  Terraformer deployment grows, red dots marking "tier saturation corners," and a red learning-rate
  cost-path line showing the modeled synthesis-cost decline overlaid on the same axes.
- The **learning rate (LR)** figures (6.5% for methanol, 10.7% for methane) and their **terminal
  25%-margin prices** ($134/t methanol; $2.4/MMBtu methane) are read directly off the chart
  annotations — no calculation was performed to verify them against the plotted curve.
- Units: 1 Terraformer = 87 t methanol/yr (methanol chart) or 2.4 MMcf CH4/yr (methane chart) —
  identical unit definitions to the ones used in this repo's independent ladder and its companion
  chart script ([`terraformer_market_ladder.py`](terraformer_market_ladder.py)).
