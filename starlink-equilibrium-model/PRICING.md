# How pricing works in the TAM model

Companion to `tam_model.py`. Explains how every "Unconnected Addressable Market"
(UAM) and "Total Addressable Market" (TAM) figure in this project gets its price.

> **Rewritten 2026-09-05.** The previous version of this file documented
> `country_tam_model.py` and `country_tam_full_model.py` (two separate modules, both
> since deleted and merged into `tam_model.py`) and a `_country_price()` rule built
> around `SCARCITY_PRICE_MULTIPLIER_CEILING = 3.0`. None of that exists any more.
> Its revision history also argued *against* elasticity-derived pricing, which is
> what the model now uses — see "Why elasticity pricing is back" below, because the
> objection was real and the current design answers it rather than ignoring it.

---

## One model, two modes

`tam_model.py` covers both questions with a single `mode` argument:

| mode | question | addressable population |
|---|---|---|
| `"unconnected"` (UAM) | what market does Starlink *open up* among people with no connection today? | `min(unconnected_population, capacity)` |
| `"full"` (TAM) | what if Starlink also *displaces incumbents*, taking whatever its capacity reaches? | capacity serves the unconnected first, then whatever is left over serves connected people |

`capacity = servable_fraction(N) x population`, per country. Both modes share one
physical capacity constraint and one pricing rule; they differ only in how much of
the servable population is counted, and at what price.

---

## Where capacity comes from

`country_service_model.country_servable_fraction(N, ...)`, which since 2026-09-05
reads out of **`tile_capacity_model.py`'s 2D (latitude x longitude) allocation**.
Each satellite carries one customer budget shared only inside its ~940 km coverage
disk, so neighbouring countries genuinely compete for the same satellite. A
country's servable-% is its own population-weighted average over the 1-degree tiles
it occupies.

This replaced a per-latitude-band readout that pooled capacity around an entire
40,000 km ring — which let idle satellites over the mid-Pacific serve demand in
South Asia, and handed every country on a band the same answer. That overstated
servable customers by roughly 1.5x at realistic fleet sizes. See
`LONGITUDE_FOV_CAPACITY_REVIEW.md` and `MODEL_SPEC.md`.

`tam_model.py` itself does **no** capacity work: `compute_country_tam()` takes an
already-computed `{iso3: servable_fraction}` and does pure pricing and aggregation.

---

## The pricing rule

There is no ARPU cap, no scarcity multiplier, and no `<20%` / `>=20%` branch. Two
prices, both derived from one elasticity curve.

### The curve

`charts/served_population_vs_cost.py` holds the user-specified elasticity anchors,
and `tam_model` imports them rather than redefining them, so there is one source of
truth:

```
0.75% of monthly GNI/capita  <->    0% of the population priced out
  10% of monthly GNI/capita  <->  100% of the population priced out
                      linear in log10(cost %) between those anchors
```

`elasticity_cost_pct(pct_unconnected)` inverts it: given how much of a country is
unconnected *today*, what monthly cost (as a share of GNI/capita) does that imply?
`elasticity_price_usd_month()` turns that into dollars with the country's own GNI.

### Unconnected customers

```
price = elasticity_price_usd_month(country's real % unconnected, country's GNI/capita)
```

**One number per country, independent of N.** It is a demand-side statement — "this
is what a market with this much exclusion is telling us people can pay" — and
deliberately not anchored to what the local terrestrial market charges today.

### Connected customers (`mode="full"` only)

Already-connected people have a revealed price: what they pay now. As Starlink takes
more of them, the price it can charge converges on the elasticity curve's cheapest
point for that country:

```
t     = (that country's connected population served) / (its connected population)
price = existing_local_ARPU + t * (floor_price(GNI) - existing_local_ARPU)
```

At `t = 0` (nobody switched yet) the price is today's real incumbent price; at
`t = 1` (everyone switched) it is `floor_price_usd_month(GNI)`, the curve's 0%-
unconnected price. Unlike the unconnected price, this one *does* move with N,
because `t` depends on how much capacity exists.

### Subscriptions

```
subscriptions = addressable_population / household_size(country)
TAM ($/month)  = subscriptions x price
```

One subscription per household — Starlink sells one terminal per premise. Household
sizes are in `data/household_size_by_country.csv`; see
`results/population/household_size_by_country_ranked.png` for the spread (2.05 to
8.66 people per household).

Note that `tile_capacity_model` *also* converts people to connections internally,
using the same dataset attributed per tile. That is not double-counting: the tile
model returns `servable_fraction` as a fraction of **people**, and the conversion to
subscriptions happens once, here.

---

## Why elasticity pricing is back, when the old file argued against it

The 2026-08-23 objection was specific and correct: the old code fed
**`servable_fraction(N)`** into the elasticity curve as if it were a demand-side
"% priced out" quantity. That conflated a *physical supply constraint* (how many
satellites exist) with a *demand-side price signal*, so at low N — when capacity
reached almost nobody — the curve concluded the market must be desperate and India's
derived price came out at **$88.59/mo against a real local ARPU of $1.60**, a 55x
markup driven entirely by there not being enough satellites.

The current model does not do that. It feeds the country's **real, current
%unconnected** into the curve — a fixed property of the country, not of the
constellation. India's price is now $15.77/mo and does not move when N does.

The conflation is fixed. A **milder version of the divergence remains**, and it is a
modelling choice rather than a bug:

| country | % unconnected | real local price | derived price | ratio |
|---|---|---|---|---|
| Fiji | 25.3% | $0.88 | $18.49 | 21.0x |
| Sri Lanka | 45.4% | $2.49 | $33.94 | 13.6x |
| India | 30.0% | $1.60 | $15.77 | 9.9x |
| Pakistan | 42.7% | $1.24 | $12.16 | 9.8x |
| Nigeria | 58.8% | $3.94 | $26.45 | 6.7x |
| United States | 3.0% | $80.00 | $60.45 | 0.8x |

Across 200 priced countries the **median derived price is 1.04x the local price** —
19 countries land above 3x and 45 below 0.5x. The high-ratio tail is concentrated in
large, cheap, partly-connected markets, which is exactly where TAM is largest, so it
matters.

**This is intended and was confirmed with the user**: the curve expresses willingness
to pay for satellite service, and anchoring it to a $1.60 Indian mobile plan would
assume Starlink must compete on the incumbent's terms. The full picture is charted at
`results/market/derived_vs_real_price_by_country.png`
(`charts/derived_vs_real_price.py`) so the size of the assumption is visible rather
than buried here.

---

## Known limitations (flagged, not fixed)

- **Raw ARPU is uncapped for data-quality outliers.** The connected-segment price
  starts from `_raw_arpu()`, which inherits known-bad survey samples — Zimbabwe
  reports $437/mo, South Sudan and Syria similarly implausible figures. They show up
  on the derived-vs-real chart as the extreme low-ratio points. `ASSUMPTIONS.md` #4.
- **The elasticity anchors themselves** (0.75% and 10% of GNI/capita) are
  user-specified, not measured. Every price in the model scales with them.
- **`mode="full"` serves the unconnected first, then the connected**, per country and
  not per latitude band or tile — an explicit simplification over allocating within
  a country by who is actually reachable. `ASSUMPTIONS.md` #15.
- **One household size per country**, applied uniformly, though rural households are
  generally larger and Starlink's demand skews rural. `ASSUMPTIONS.md` #13.
- **Capacity is allocated revenue-blind.** `tile_capacity_model` maximises
  *connections served*, then TAM prices whatever got served. The stated intent is to
  serve the highest-revenue customers first within each tile's reachable set; that is
  a separate, not-yet-built step.

---

## What the 2026-09-05 capacity switch did to the numbers

Switching `country_servable_fraction()` from latitude bands to tiles bundles two
corrections with **opposite signs**, so the net is misleading on its own. At
N=10,900, TAM $B/month:

| stage | `unconnected` | `full` |
|---|---|---|
| latitude-pooled capacity, 1 person = 1 dish | 4.67 | 11.68 |
| + longitude fix (tiles) | 3.21 | 8.61 |
| + households fix (connections) — what ships | 6.60 | 20.19 |

The longitude fix alone cuts TAM ~31%; correcting people-vs-subscriptions more than
reverses it. More importantly the longitude fix **redistributes**: India's servable
fraction falls to 0.24x, Brazil 0.42x, Nigeria 0.43x, while the USA rises 2.10x and
Australia 1.19x. Ring-pooling had been crediting dense low-latitude countries with
capacity sitting over empty ocean at their latitude.
