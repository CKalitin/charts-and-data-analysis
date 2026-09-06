# Launch vehicle economics: capex vs. opex

A cross-program scatter analysis of launch vehicle economics: capital cost (development/
program capex), operating cost (cost per launch and cost per kg to LEO), and payload
capacity, plotted pairwise against each other. The underlying dataset
(`data/launch_vehicles.csv`) records 55 vehicles from the 1957 Atlas ICBM through the current
global wave of new-space launch startups, 45 of which have flown at least once. **The charts
themselves are stricter: only vehicles with real values on BOTH of a given chart's two axes
are plotted** (21–42 vehicles per chart, depending which two metrics) — see "Why two capex
charts and two opex bases" below for why capex in particular is split, and "Data gaps" for
exactly which vehicles get excluded from which chart and why. Real, flight-proven pricing
dominates what remains: decades of Arianespace, CGWIC/Long March, Sea Launch, and NSSL/ESA
contract history, plus Rocket Lab's SEC-disclosed unit economics for Electron. A handful of
pre-flight predictions (Neutron, hollow markers) are still shown, clearly flagged, where they
have both coordinates for a given chart.

## The seven charts

- `results/capex_program_vs_opex_per_launch.png` — total program cost vs. cost per launch
- `results/capex_first_launch_vs_opex_per_launch.png` — cost through first launch vs. cost per launch
- `results/capex_program_vs_opex_per_kg.png` — total program cost vs. $/kg to LEO
- `results/capex_first_launch_vs_opex_per_kg.png` — cost through first launch vs. $/kg to LEO
- `results/payload_vs_opex_per_kg.png` — payload capacity to LEO vs. $/kg to LEO
- `results/payload_vs_capex_program.png` — payload capacity to LEO vs. total program cost
- `results/payload_vs_capex_first_launch.png` — payload capacity to LEO vs. cost through first launch

The payload-capacity charts are the best-populated of the seven (42 and 41 vehicles,
respectively, vs. 21–30 for the capex-vs-opex charts) simply because payload capacity is
publicly disclosed for nearly every vehicle ever built, while capex and opex are each
independently spotty — so pairing payload with either one loses fewer vehicles than pairing
capex with opex.

## Why two capex charts and two opex bases

The brief for this analysis was explicit that **"total program cost"** and **"cost until
first launch"** are apples and oranges — a NASA/GAO DDT&E-style figure covering only R&D
through IOC is not the same quantity as a whole-program figure that can include decades of
production, launch-pad infrastructure, and (for military/NASA vehicles) procurement of dozens
of rounds. Rather than force one number per vehicle, both are recorded wherever the sources
distinguish them, in separate CSV columns, and plotted as **separate charts** — this is why
both the capex-vs-opex pair and the payload-vs-capex pair each come in two versions.

**A vehicle is only plotted on a chart if it has BOTH a real capex value (for that chart's
basis) and a real opex value.** Earlier drafts of this analysis placed vehicles missing one
coordinate into a shaded "not disclosed" sidebar so nothing was ever dropped — with 54
vehicles that added enough visual clutter (half the canvas given over to non-coordinate
placeholder positions) that it undermined the point of a scatter plot, which is to show a
trend in genuine paired data. Each chart now only shows vehicles with a real, comparable
(x, y) pair, so every point is a genuine data pair, not a partial record padded to a
placeholder position. This means: (a) the four charts have different, smaller vehicle counts
(21–30 vehicles per chart, down from all 54), and (b) some vehicles with real, well-sourced
data on ONE axis — e.g. Soyuz and Proton's real commercial launch prices, which have no
public capex figure under either basis — don't appear on any of the four charts at all. That
data isn't lost: it's still fully recorded in `data/launch_vehicles.csv` and cited in
`data/sources.md`, just not plotted. The script prints exactly which vehicles were excluded
from each chart, and why, every time it runs. See "Data gaps" below for the full list.

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
- `results/*.png` — the seven scatter charts (see "The seven charts" above).

## Vehicles covered

**Established/historical (22):** Falcon 9 v1.0, Falcon 9 (reusable, Block 5), Falcon Heavy,
Starship (expendable, scoped to IFT-1), Antares, Space Shuttle, SLS, Saturn V, Titan IV,
Titan II GLV (Gemini), Atlas D (SM-65D Atlas / Atlas LV-3B), Atlas V, Delta IV (Medium & Heavy),
Neutron (Rocket Lab, pre-first-flight predictions), New Glenn, Soyuz, Proton, H-II/H-IIA, H3,
PSLV, GSLV Mk II, and — as a bonus, since it's far better documented than plain GSLV — GSLV
Mk III / LVM3.

**Mature/flight-proven, added in a third pass to strengthen the real-data trend (14):**
Ariane 5, Ariane 6, Vega, Vega-C (ESA/Europe), Vulcan Centaur, Electron (USA), Long March 3B,
Long March 5, Long March 2D, Kuaizhou-1A (China), Angara A5, Zenit-3SL/Sea Launch (Russia/
Ukraine), Epsilon (Japan), SSLV (India). These were added specifically because the first
new-space-startup pass (below) skewed the dataset toward unprovable pre-flight predictions —
this batch is decades of real commercial/institutional launch history instead: the 1990s
CGWIC "dumping" dispute pricing for Long March (real $25–70M contract figures tied to actual
US-China trade filings), Arianespace's decades of disclosed Ariane 5 GTO pricing, ESA's own
itemized Ariane 6/Vega-C launch-service contract values, the 1995 Sea Launch/Hughes $100M×10
commercial contract, and Rocket Lab's SEC-filed (10-Q) Electron unit economics.

**New-space startups (18, added in a second pass):** Terran R (Relativity Space, USA), Nova
(Stoke Space, USA), Firefly Alpha (USA), Eclipse/MLV (Firefly + Northrop Grumman, USA), RS1
(ABL Space Systems, USA — program terminated 2024), Spectrum (Isar Aerospace, Germany), RFA
ONE (Rocket Factory Augsburg, Germany), Miura 5 (PLD Space, Spain), Prime (Orbex, UK), Maia
(MaiaSpace, France), Agnibaan (Agnikul Cosmos, India), Vikram-1 (Skyroot Aerospace, India),
Kairos (Space One, Japan), Zhuque-2 (LandSpace, China), Zhuque-3 (LandSpace, China), Ceres-1
(Galactic Energy, China), Hyperbola-1 (i-Space, China), Tianlong-3 (Space Pioneer, China).
Most are pre-first-flight or have only flown sub-scale demonstrators — their capex figures
are company funding-raised totals (a looser proxy than a disclosed R&D budget) and their
opex figures, where they exist at all, are unproven target prices. See `data/sources.md` for
full per-vehicle caveats.

**Also added on request (1):** Tundra (NordSpace, Canada) — a pre-first-flight small launcher
targeting 2028 IOC, in the same "predicted, not yet real" category as the startups above.
Opex is back-calculated from the company's stated ~$10,000/kg LEO cost target (not a
disclosed flat price) — a peer check against every other vehicle in Tundra's payload class
(500 kg) shows this is plausible: it lands between SSLV's real $7,800/kg and Ceres-1's real
$10,950/kg, both actually-flying vehicles, not an implausibly cheap outlier. **Capex is
deliberately left blank, not just flagged as uncertain:** NordSpace's only vehicle-specific
disclosure is a CA$8.33M Canadian government grant, which is far below every comparable
small-launcher peer (Electron and Firefly Alpha each needed ~$100M; RFA ONE has raised $33M
and still hasn't reached orbit; even SSLV — a heavily state-subsidized ISRO program reusing
existing PSLV/GSLV infrastructure — needed $20.4M). Plotting $8.33M as "capex" would imply an
unprecedented, implausible level of cost efficiency for a vehicle that hasn't flown, so Tundra
appears only on the payload-vs-$/kg chart, not the capex charts. (NordSpace separately holds
a much larger CA$715M Canadian Space Agency award, but that's for broader propulsion-
manufacturing capability, not Tundra-specific R&D, and wasn't a good substitute either.)
Canada is its own region/color on the charts (previously grouped countries only covered USA,
Russia/USSR, Japan, India, China, and Europe).

## A note on data quality (read this before trusting any single point)

Flown-vs-unflown (the marker fill) is a coarse proxy; the more important distinction is
**where the number actually comes from**, and it varies a lot even among "real" vehicles:

- **Best tier — a real, itemized, arm's-length contract or SEC filing.** Rocket Lab's Electron
  marginal cost ($5.68M, from an actual 10-Q segment breakdown), ESA's disclosed Ariane 6/
  Vega-C launch-service contract values (Sentinel-1C/1D), the 1995 Sea Launch/Hughes contract,
  and the 1990s CGWIC Long March pricing (tied to real US-China trade disputes) all belong here.
- **Good tier — a real government/institutional cost disclosure, but not a market price.**
  NASA/GAO/OIG figures (Shuttle, SLS, Titan IV), JAXA's Epsilon cost figures, India's Lok Sabha
  replies (PSLV/GSLV/SSLV), Angara's Roscosmos-adjacent cost estimates. These are genuine, but
  a state institution's internal cost isn't the same thing as a price a customer paid.
  China's Long March 5 price is explicitly flagged the other way — a secondary analyst
  estimate, NOT a disclosed contract, because CZ-5 has no commercial customer.
- **Weakest tier — a company's total funding raised, used as a capex proxy.** Almost every
  new-space startup in this dataset (both the pre-flight ones and several that have flown
  small demonstrators, e.g. Firefly Alpha, Zhuque-2/3, Ceres-1, Hyperbola-1) falls here: total
  money raised is not the same as money spent on R&D for one specific vehicle, especially for
  multi-program companies. These are flagged in both the CSV `notes` column and `sources.md`.

The `opex_used_basis` marker shape (circle/square/triangle) tells you the *economic concept*
(marginal cost vs. fully-loaded vs. price) but does NOT by itself tell you the *evidentiary
strength* above — check `sources.md` for that per vehicle.

## Data gaps (recorded in the CSV, but excluded from the charts)

A large fraction of the dataset never appears in any of the four charts, because a real
capex figure and a real opex figure for the SAME vehicle rarely both exist. This is not a
plotting bug — it's the honest shape of public launch-cost disclosure. The most notable
exclusions:

- **Soyuz, Proton** — real, well-documented commercial launch prices (Glavkosmos/ILS), but
  no public capex figure under either basis. Soviet-era ruble accounting under a
  non-convertible currency makes any dollar figure for their original development cost
  methodologically unreliable, so none is reported — these vehicles are absent from all four
  charts despite having genuinely strong opex data.
- **PSLV, GSLV Mk II, H3** — real opex data, but development capex was never disclosed (for
  PSLV/GSLV Mk II, only production/operations-batch budgets exist, which aren't the same
  quantity as R&D capex and were deliberately not substituted in).
- **Most new-space startups** (Terran R, Nova, Eclipse/MLV, RS1, Spectrum, Miura 5, Orbex
  Prime, MaiaSpace, Agnibaan, Vikram-1, Zhuque-2, Ceres-1, Hyperbola-1, Tianlong-3) — have a
  funding-raised capex proxy but no disclosed price, so they don't appear on the $/launch or
  $/kg charts. A few (Vulcan Centaur, Long March 3B/5/2D, Kuaizhou-1A) have the opposite gap:
  real opex data but no disclosed capex.
- **Titan II GLV** — has real capex (a 1962 NASA program-office estimate) but no vehicle-only
  opex figure exists (the only per-flight economics found bundles booster + spacecraft
  together, a different quantity, so it wasn't substituted in).

Several of the figures that DO make it onto the charts are still explicitly **estimates or
pre-flight predictions** rather than realized costs, flagged as such throughout: Neutron (all
figures are Rocket Lab's own pre-flight projections), Starship's capex/opex (SpaceX doesn't
publish true costs; third-party analyst estimates), and China's Long March 5 price (a
secondary analyst estimate, not a disclosed contract, since CZ-5 has no commercial customer).

## Regenerating the charts

```
cd launch-vehicle-economics/scripts
python3 plot_launch_economics.py
```

Prints, per chart: how many vehicles were plotted, and the full list of vehicles excluded
because they're missing capex, opex, or both for that chart's specific basis.
