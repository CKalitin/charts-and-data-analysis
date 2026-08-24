# How pricing works in the TAM models

Companion to `country_tam_model.py` and `country_tam_full_model.py`. Explains the
actual pricing mechanism behind every "Unconnected Addressable Market" (UAM) and
"Total Addressable Market" (TAM) chart in this project, since the two models answer
genuinely different questions and price things differently under the hood.

---

## The two models, in one paragraph each

**Unconnected Addressable Market (UAM)** — `country_tam_model.py`,
`charts/country_tam_charts.py`. Sizes the market Starlink opens up among people who
are **currently unconnected**. Addressable population per country is capped at
however many unconnected people actually exist there. This is the narrower,
"fills the gap" question.

**Total Addressable Market (TAM)** — `country_tam_full_model.py`,
`charts/country_tam_full_charts.py`. Sizes the market assuming Starlink **takes
100% of whatever population its capacity can reach**, connected and unconnected
alike — i.e. it also displaces existing incumbent telecom revenue, not just fills
the unconnected gap. This is the wider, "just takes share as it expands" question.

Both models share the same physical capacity constraint
(`country_service_model.country_servable_fraction(N)` — how much of a country's
population Starlink's satellites can physically reach at N satellites) and the same
per-country pricing rule (`country_tam_model._country_price()`, described below).
They differ only in **how much of the servable population gets counted, and at
what price**.

---

## The pricing rule (`_country_price()`, in `country_tam_model.py`)

Every priced customer, in both models, is priced by the same two-branch rule,
evaluated per country:

```
arpu = _raw_arpu(country)          # real local price today (mobile or fixed
                                     # broadband, whichever is the dominant
                                     # access mode in that country)

if pct_unconnected < 20%:
    price = arpu                    # well-served market -> trust the real price

else:  # >= 20% unconnected
    frac = servable_fraction(N)     # capacity-constrained, changes with N
    multiplier = 3.0 - 2.0 * frac   # 3x at frac=0, 1x at frac=1, linear between
    price = arpu * multiplier
```

- **<20% unconnected**: price is just today's real local ARPU, unmodified. If a
  country is already mostly served, its existing market price is a reliable signal
  — no adjustment needed.
- **>=20% unconnected**: price is the same local ARPU, multiplied by a **scarcity
  premium** bounded between 1x and `SCARCITY_PRICE_MULTIPLIER_CEILING` (currently
  **3.0**, a picked-not-confirmed default — see Known limitations below). At low N
  (capacity barely reaches anyone), the premium is at its ceiling; as N grows and
  `servable_fraction` approaches 1 (capacity reaches everyone), the premium relaxes
  back to 1x — full coverage should mean the real market price, not a markup.

This scarcity-premium formula replaced an earlier (broken) mechanism on
2026-08-23 — see "Revision history" below for why.

---

## How the two models differ in addressable population

This is the part that actually causes the two models' numbers to diverge, and it
surprised us when South Asia showed up earning *more* in the UAM chart than in the
TAM chart at some satellite counts — worth understanding precisely.

**UAM** (`country_tam_model.compute_country_tam`):
```
addressable_population = min(unconnected_population, servable_fraction(N) * total_population)
```
All of a country's servable capacity is treated as going to unconnected people
first, capped only by how many unconnected people actually exist.

**TAM** (`country_tam_full_model.compute_country_tam_full`):
```
connected_population   = total_population - unconnected_population
addressable_connected   = servable_fraction(N) * connected_population    # "incumbent" segment, priced at arpu (no premium)
addressable_unconnected = servable_fraction(N) * unconnected_population  # "new" segment, priced via _country_price()
```
Servable capacity is split **proportionally** across connected and unconnected
people, in the same ratio as the country's real population — not all funneled to
the unconnected segment. `TAM = incumbent-segment revenue + new-segment revenue`.

**Why this makes UAM revenue larger than TAM revenue below full saturation**: UAM
effectively values *all* servable capacity (including the slice that "belongs" to
already-connected people) at the >=20%-branch's scarcity-premium price. TAM instead
prices that same slice at the real, lower incumbent ARPU. Algebraically, for a
country in the >=20% branch with no population capping in play:

```
UAM − TAM = servable_fraction(N) * connected_population * (price_premium − price_incumbent)
```

Since the premium price is always >= the incumbent price by construction, UAM is
always >= TAM's corresponding contribution until `servable_fraction` reaches 1 (full
saturation), at which point the premium relaxes to 1x and the two formulas converge
exactly. This is expected, structural behavior, not a bug — the two models are
deliberately answering different questions ("what if all capacity serves the
unconnected specifically" vs. "what if capacity is shared proportionally").

---

## Household conversion and totals

Both models convert priced population to subscriptions the same way:
```
subscriptions = addressable_population / household_size(country)   # data/household_size_by_country.csv
TAM ($/month) = subscriptions * price
```
One subscription per household, not per person (Starlink sells one terminal per
premise). Summed across all countries for the totals shown in
`tam_vs_satellites.png` / `tam_full_vs_satellites.png`.

---

## Known limitations (flagged, not fixed)

- **`SCARCITY_PRICE_MULTIPLIER_CEILING = 3.0`** is a reasonable starting default,
  not a user-confirmed number. Tune this one constant in `country_tam_model.py` if
  a different scarcity-premium magnitude is wanted — everything downstream (both
  models, `avg_price_market_ladder.py`) reads from the same constant.
- **Raw ARPU is not capped for data-quality outliers** in either model's price
  formula (e.g. a country with a thin, unreliable survey sample could still report
  an implausible incumbent price, which both `price = arpu` and
  `price = arpu * multiplier` would inherit uncorrected). This is a pre-existing,
  already-documented gap (`ASSUMPTIONS.md` #4, e.g. Zimbabwe's raw pre-cap ARPU),
  not something introduced by the 2026-08-23 pricing revision.
- **The connected/unconnected proportional split** in the TAM model (servable
  capacity divided in the country's overall population ratio) is an explicit
  simplifying assumption — no sub-national data exists to know which specific
  people within a density bin are already connected (`ASSUMPTIONS.md` #15).

---

## Revision history

**2026-08-23**: The `>=20% unconnected` branch previously derived price by
inverting a cross-country elasticity curve (`served_population_vs_cost.py`'s
0.75%–10%-of-GNI/month anchors) using `servable_fraction(N)` as if it were a
demand-side "% priced out" quantity. That conflated a **physical supply
constraint** (how many satellites exist) with a **demand-side price signal**,
producing absurd results at low N — e.g. India's derived price was $88.59/mo
against a real local ARPU of $1.60/mo, a 55x markup driven entirely by capacity
being scarce, which has nothing to do with what the market would actually bear.
Replaced with the local-ARPU-anchored, bounded scarcity-premium formula described
above (one of two options presented to the user; the other was dropping
capacity-dependent pricing entirely). The `<20%` branch was already local-ARPU-only
and unaffected by this change. `cost_pct_from_pct_unconnected()` (the old inversion
function) was deleted from `served_population_vs_cost.py` as dead code; its forward
counterpart `pct_unconnected_from_cost_pct()` is unaffected and still used by that
file's own scatter chart trend line, unrelated to TAM pricing.
