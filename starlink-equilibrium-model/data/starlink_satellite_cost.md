# Starlink satellite cost & manufacturing economics — sources & methodology

Companion to [`starlink_satellite_cost.csv`](starlink_satellite_cost.csv) and
[`starlink_cost_per_gbps.csv`](starlink_cost_per_gbps.csv). Phase 4 of the plan (see
`CLAUDE.md`).

**Seed data**: the user pointed directly at
`Reflect-Orbital/sso-land-proximity/data/reflect_orbital_sources.md` (+ the
identical `.xlsx` version) as the starting source for this phase — it already has a
well-organized Starlink mass & cost table for v1.0 through v3, built for the sibling
Reflect Orbital project. Read in full and used as the seed here, then cross-checked
and extended per the user's explicit instruction that it "might not be enough."

---

## What the seed file actually contains (verified 2026-08-09)

Traced every figure back to its primary article: **all five generations' cost
figures come from ONE source chain** — Caleb Henry (Director of Research, Quilty
Space), quoted in a single SpaceNews article dated **2024-05-09**
(https://spacenews.com/starlink-soars-spacexs-satellite-internet-surprises-analysts-with-6-6-billion-revenue-projection/).
Confirmed directly by fetching the article: "$200,000 each" (v1), "$800,000" (v2
Mini, "increased from 260 kg to 730 kg"), "roughly $1.2 million" (v3, 1,500 kg
projected). **v1.5 and v2 full are NOT in that article at all** — the seed file's
own notes already flag these as interpolated/estimated with no primary source,
which this research confirms is accurate self-assessment, not an oversight.

**This means the seed file has real thinness the user was right to flag**: one
analyst, one article, from a source that is now **over 2 years old** relative to
today (2026-08-09) — in a market where the seed file's own "5 satellites/day"
production-scale trend implies costs move fast. Two problems worth fixing:
1. Only one analyst's estimate, never cross-confirmed against an independent source.
2. Vintage — 2 years is a long time for a manufacturing-cost figure in a
   still-scaling production line.

## New finding: v2 Mini cost has likely fallen by roughly half since the seed data

**New Space Economy**, "The Satellite Manufacturing Market After Starlink"
(published 2026-04-13,
https://newspaceeconomy.ca/2026/04/13/the-satellite-manufacturing-market-after-starlink-how-mass-production-changed-the-economics-of-building-spacecraft/):
states SpaceX manufactures **~5 satellites/day** from its Hawthorne facility and
prices v2 Mini at **~$400,000/unit "at production volume"** — roughly HALF the
2024 Quilty Space figure for the same generation (730 kg, unchanged). **Confidence:
single source, and critically, this $400K figure is NOT attributed further upstream
to Quilty Space or any other named analyst in the article itself** — it may be that
publication's own estimate/synthesis, not an independently re-confirmed data point.
Treat as directional (real cost decline is very plausible given the stated 5/day
production rate and general LEO-constellation cost trends) but **do not present
$400K as equally well-sourced as the 2024 $800K figure** — it's one unconfirmed
data point suggesting a real trend, not a confirmed new baseline.

**What this means for Phase 5**: if the equilibrium model sweeps "cost per
satellite" from v1.0 through v3 to find equilibria at each cost point, this v2 Mini
data point is itself evidence that costs fall over time even WITHIN one generation
as production scales — the model's v1.0->v3 sweep is really conflating two
different cost-reduction mechanisms (across-generation capability increases AND
within-generation manufacturing-scale learning). Worth flagging to the user before
Phase 5 locks in a single cost figure per generation.

## Complementary, independent metric: cost per Gbps (Wright's Law framing)

Found while cross-checking: **Gale L. Pooley** (economics professor, Utah Tech
University; adjunct scholar, Cato Institute), "Starlink Is Riding Down the Wright's
Law Cost Curve" (humanprogress.org, fetched 2026-08-09), citing **ARK Invest**
newsletter Issue 445: satellite bandwidth cost fell from **$300,000,000/Gbps
(2004, pre-Starlink GEO baseline)** to **~$40,000/Gbps (current)**, a 7,500-fold
drop, with ARK's own Wright's Law fit implying **~$1,000/Gbps by 2028** (a 40-fold
further decline) at a stated learning rate of "45% decline per cumulative doubling
of Gbps deployed in orbit." **Confidence: independent of the Quilty Space chain (a
genuinely different source and methodology), but still a single analysis (ARK
Invest) or a secondary quote of it, not cross-confirmed by a second independent
source.** This is a fundamentally DIFFERENT metric than $/satellite — cost per unit
of DELIVERED CAPACITY, which folds in the capacity increases from Phase 3
(`satellite_capacity.md`: 20 Gbps v1.5 -> 96 Gbps v2 Mini -> 1,024 Gbps v3 design
target). **This may be the more decision-relevant metric for Phase 5** than raw
$/satellite, since the equilibrium model is ultimately about revenue vs. cost of
DELIVERING service, not just building hardware — worth discussing with the user
before choosing which cost metric drives the equilibrium chart's flat cost line.

## Launch cost (already in the seed file, not yet combined with satellite cost)

The seed file's Launch Cost section (F9 rideshare $6,000/kg, F9 internal marginal
~$857/kg, Starship aspirational $67/kg, Starship conservative-near-term ~$200/kg)
was NOT yet combined with satellite mass to get a per-satellite launch cost, or
added to manufacturing cost for a true "cost to orbit" figure. **This matters**:
manufacturing cost alone understates what SpaceX actually spends to get one
satellite operational. Left as an open task for whoever builds Phase 5 — see below.

---

## Recommended next steps before Phase 5 locks in a cost line

1. **Ask the user which cost metric to use**: $/satellite (simpler, matches the
   model's "x = satellite count" framing) or $/Gbps (arguably more economically
   correct, but changes the model's x-axis meaning). Don't pick unilaterally.
2. **Combine manufacturing + launch cost** into a true cost-to-orbit figure per
   generation, using each generation's mass and a chosen launch $/kg assumption
   (also needs a user decision: F9 rideshare rate vs. Starship target vs.
   Starship conservative — these differ by ~90x, per the seed file itself).
3. **Decide how to handle the v2 Mini within-generation cost decline** ($800K ->
   ~$400K) — average it, use the more recent figure, or model cost decline as a
   continuous function of cumulative production rather than a discrete per-
   generation step. The user's Phase 6 instruction (continuous curve, not discrete
   tiers) suggests the continuous approach may fit the project's existing design
   philosophy better.
4. **Try to find a second source for the $400K v2 Mini figure** and the ARK
   Invest $40K/Gbps figure — both are currently single-sourced in this research
   pass, a real gap flagged explicitly rather than presented as solid.
