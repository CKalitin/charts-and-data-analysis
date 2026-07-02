# Launch vehicle economics: capex vs. opex

A cross-program scatter analysis of launch vehicle capital cost (development/program capex)
against operating cost (cost per launch and cost per kg to LEO), covering 40 vehicles from
the 1957 Atlas ICBM through the current global wave of new-space launch startups (Terran R,
Nova, Spectrum, Zhuque-3, and more — most still pre-first-flight as of this research).

## Why two capex charts and two opex bases

The brief for this analysis was explicit that **"total program cost"** and **"cost until
first launch"** are apples and oranges — a NASA/GAO DDT&E-style figure covering only R&D
through IOC is not the same quantity as a whole-program figure that can include decades of
production, launch-pad infrastructure, and (for military/NASA vehicles) procurement of dozens
of rounds. Rather than force one number per vehicle, both are recorded wherever the sources
distinguish them, in separate CSV columns, and plotted as **separate charts**:

- `results/capex_program_vs_opex_per_launch.png`
- `results/capex_first_launch_vs_opex_per_launch.png`
- `results/capex_program_vs_opex_per_kg.png`
- `results/capex_first_launch_vs_opex_per_kg.png`

**Every vehicle in the dataset appears on every chart it has any data for.** A vehicle is
never dropped just because one of its two coordinates is undocumented — e.g. Soyuz and
Proton have well-documented commercial launch prices but no public capex figure under either
basis (Soviet-era ruble accounting under a non-convertible currency makes any dollar figure
for their original development cost methodologically unreliable). Instead of silently
omitting them, a vehicle missing one coordinate is placed in a shaded, clearly-labeled "not
publicly disclosed" lane along that axis, at its real value on the other axis, separated from
the real log-scale data by a dashed boundary line. A vehicle is only absent from a chart if
**both** of its coordinates for that specific chart are undocumented — the script prints
exactly which vehicles (if any) that applies to, chart by chart, so nothing goes missing
silently. See "Data gaps" below.

The opex side has the same apples/oranges problem: a **marginal/incremental cost** (what it
actually costs the operator to fly one more mission), a **fully-loaded average cost**
(marginal cost plus its share of fixed overhead), and a **commercial or government contract
price** (which bakes in profit margin and, for military missions, mission-assurance
overhead) are three different economic concepts. All three are kept as separate CSV columns
(`opex_marginal_usd`, `opex_fully_loaded_usd`, `opex_price_usd`); the charts pick one **best
available** figure per vehicle using the priority **marginal → fully-loaded → price** (cost
concepts are preferred over price when available), and encode *which* concept was used via
marker shape (circle / square / triangle) so the mixing is visible rather than hidden.

Marker **color** encodes region of origin (USA, Russia/USSR, Japan, India, China, Europe —
individual European countries are grouped into one "Europe" swatch to keep the legend
readable; see `REGION_OF_COUNTRY` in the script for the country-level mapping). Marker
**fill** encodes flight status: solid = has flown at least once, hollow/open = pre-flight or
a predicted figure for a vehicle that hasn't launched yet (e.g. Neutron) — those numbers are
forward-looking by definition and are visually flagged as such everywhere they appear.

All dollar figures are converted to 2026 USD using the BLS CPI-U annual-average index
(`scripts/cpi.py`) purely so a 1959 Atlas program and a 2026 Neutron estimate sit on a
comparable axis. This is a blunt macroeconomic deflator, not a launch-industry-specific
index — real launch costs have arguably fallen far more than general CPI over this period,
so treat the resulting positions as roughly comparable, not as a precise "real cost" claim.

## Files

- `data/launch_vehicles.csv` — one row per vehicle, every sourced dollar figure kept in its
  original nominal/quoted-year form, with a `*_source` URL column next to every cost field.
  This is the record of "every bit of data possible" — nothing here is CPI-adjusted or
  cherry-picked; that happens only in the plotting script.
- `data/sources.md` — full per-vehicle citation notes (the prose behind every CSV cell),
  organized in the same order as the CSV, with direct links to NASA, GAO, NASA OIG, RAND,
  Lok Sabha replies, SEC filings, and trade press.
- `scripts/cpi.py` — BLS CPI-U lookup table and the nominal→2026-USD conversion function.
- `scripts/plot_launch_economics.py` — loads the CSV, applies the marginal→fully-loaded→
  price selection logic and CPI adjustment, and renders the four figures into `results/`.
  Run with `python3 scripts/plot_launch_economics.py` (needs `pandas` + `matplotlib`).
- `results/*.png` — the four scatter charts.

## Vehicles covered

**Established/historical (22):** Falcon 9 v1.0, Falcon 9 (reusable, Block 5), Falcon Heavy,
Starship (expendable, scoped to IFT-1), Antares, Space Shuttle, SLS, Saturn V, Titan IV,
Titan II GLV (Gemini), Original Atlas (SM-65/Atlas D), Atlas V, Delta IV (Medium & Heavy),
Neutron (Rocket Lab, pre-first-flight predictions), New Glenn, Soyuz, Proton, H-II/H-IIA, H3,
PSLV, GSLV Mk II, and — as a bonus, since it's far better documented than plain GSLV — GSLV
Mk III / LVM3.

**New-space startups (18, added in a second pass):** Terran R (Relativity Space, USA), Nova
(Stoke Space, USA), Firefly Alpha (USA), Eclipse/MLV (Firefly + Northrop Grumman, USA), RS1
(ABL Space Systems, USA — program terminated 2024), Spectrum (Isar Aerospace, Germany), RFA
ONE (Rocket Factory Augsburg, Germany), Miura 5 (PLD Space, Spain), Prime (Orbex, UK), Maia
(MaiaSpace, France), Agnibaan (Agnikul Cosmos, India), Vikram-1 (Skyroot Aerospace, India),
Kairos (Space One, Japan), Zhuque-2 (LandSpace, China), Zhuque-3 (LandSpace, China), Ceres-1
(Galactic Energy, China), Hyperbola-1 (i-Space, China), Tianlong-3 (Space Pioneer, China).
Almost all of these are pre-first-flight or have only flown sub-scale demonstrators — their
capex figures are company funding-raised totals (a looser proxy than a disclosed R&D budget)
and their opex figures, where they exist at all, are unproven target prices. See
`data/sources.md` for the "New-space startups" section with full caveats per vehicle.

## Data gaps (recorded and shown, never guessed or dropped)

Several vehicles have **no public total-program capex figure** at all (shown in the "capex
not publicly disclosed" lane on both capex-program charts, at their real $/launch or $/kg):
Soyuz, Proton, H3, PSLV, GSLV Mk II. For Soyuz and Proton this is a structural gap —
Soviet-era ruble accounting under a non-convertible currency makes any dollar figure for
their original 1950s–60s R&D methodologically suspect, so none is reported. For PSLV and
GSLV Mk II, extensive searching (including ISRO's own site and Lok Sabha replies) turned up
only production/operations-batch budgets, not original R&D capex — those budget figures are
recorded in `sources.md` but deliberately kept out of the capex columns since they aren't the
same quantity.

**Cost-through-first-launch** is even sparser (most historical programs' public accounting
only reports a whole-program total, not a first-launch cutoff): missing for Falcon 9 v1.0,
Starship, Saturn V, Titan IV, Original Atlas, Atlas V, Delta IV, New Glenn, plus the four
above — all likewise shown in the "capex not publicly disclosed" lane rather than omitted.

**Titan II GLV** has no chart-usable opex figure at all: the only per-flight economics found
is a whole-Gemini-program figure (booster + spacecraft bundled), which is a different
quantity than a launch-vehicle-only cost and was deliberately not substituted in — it's shown
in the "opex not publicly disclosed" lane at its real capex value instead.

**H3** and **GSLV Mk II** are missing $/kg: for H3, the only price we have (~$34-51M) applies
to the H3-30 config (~4,000 kg to SSO) while the only LEO payload figure we have (16,000 kg)
is for the different H3-24 config — blending them would be a bad ratio, so it's shown in the
$/kg N/A lane instead of a fabricated number.

The one case where a vehicle can still be absent from a specific chart: if **both** of its
coordinates for that chart are undocumented, there's genuinely nothing to plot (e.g. H3 has
no total-program capex *and* no valid $/kg, so it can't appear on the total-program-vs-$/kg
chart specifically — it does appear on the other three). `plot_launch_economics.py` prints
this list explicitly every time it runs; check that output rather than assuming.

Several figures are explicitly **estimates or pre-flight predictions**, flagged as such
throughout: Neutron (all figures are Rocket Lab's own pre-flight projections, since the
vehicle has not launched as of this analysis), Starship's capex/opex (SpaceX doesn't publish
true costs; the numbers used are third-party analyst estimates), and parts of New Glenn's
capex (Blue Origin's only official figure, $2.5B from 2017, is contested by third-party
estimates 4–6x higher).

## Regenerating the charts

```
cd launch-vehicle-economics/scripts
python3 plot_launch_economics.py
```

Prints the four output paths plus a report of which vehicles were excluded from which chart
and why (mirrors the "Data gaps" section above, computed live from the CSV).
