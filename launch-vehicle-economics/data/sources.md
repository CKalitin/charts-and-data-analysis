# Launch vehicle economics — full source notes

This file is the detailed, per-vehicle citation record behind `launch_vehicles.csv`. Every
dollar figure in the CSV traces to a specific source cited here (or directly in the CSV's
own `*_source` columns, which duplicate the most load-bearing URL per field). Research was
carried out via live web search in July 2026; all "active"/"as of" framing in this file
reflects that date.

**How to read this file.** For each vehicle: development/program capex (total program cost,
and — where distinguishable — cost through first launch only), then opex (marginal/
incremental cost to the operator, a fully-loaded average cost, and/or commercial or
government contract price — these are different economic concepts and are labeled as such),
then payload/$-per-kg, then status. Gaps are stated explicitly as gaps, not filled with
guesses.

---

## Falcon 9 v1.0 (original expendable, 2010–2013)

**Capex.** SpaceX's own stated development cost was ~$300 million (2011 dollars), a figure
NASA says it independently verified; NASA's cited combined figure including Falcon 1
heritage work is $390 million. Documented in NASA's [*Falcon 9 Launch Vehicle NAFCOM Cost
Estimates*](https://www.nasa.gov/wp-content/uploads/2015/01/586023main_8-3-11_NAFCOM.pdf)
(Aug 2011) — source of NASA's internal cost-model comparison: NASA's NAFCOM model predicted
Falcon 9 would have cost ~$4.0B (FY2010$, NASA-culture cost-plus assumptions) or ~$1.7B
(commercial-style assumptions) to develop in-house — a 4–11x gap vs. SpaceX's actual spend,
also discussed in [Zapata (NASA/AIAA, 2017)](https://ntrs.nasa.gov/api/citations/20170008895/downloads/20170008895.pdf).
NASA's COTS Space Act Agreement funding ($278M at 2006 signing, rising to $396M by 2011,
bundled with Dragon demo flights) is NASA's contribution only, not SpaceX's total spend —
not directly comparable. No source isolates cost through the first flight (June 2010) alone.

**Opex.** [Musk's May 2011 statement](https://nss.org/statement-from-spacex-ceo-elon-musk/):
$54M (2011$) commercial price. No marginal/incremental cost figure is publicly available.

**Payload/$-per-kg.** [SpaceX Falcon 9 Payload User's Guide, Rev 1 (2009)](https://www.spaceflightnow.com/falcon9/001/f9guide.pdf):
10,454 kg to 200km/28.5° LEO, expendable (Block 2 config, flew as v1.0). $54M ÷ 10,454 kg ≈
$5,167/kg (derived, not published; uses rated capacity, not actual payload flown).

**Status.** Expendable. 5 flights, June 2010 – March 2013. Retired.

---

## Falcon 9 (reusable, Block 5)

**Capex.** No official figure isolates Block 5 development (first flight May 11, 2018).
[Payload Research](https://payloadspace.com/rocket-development-costs-by-vehicle-payload-research/)
(ESTIMATE) models cumulative Falcon-family development (Falcon 1 → F9 expendable → F9
reusable) at ~$1.4B nominal / ~$1.9B in 2024$. Musk's March 2017 statement: SpaceX had spent
"over $1 billion" on reusable-rocket tech, self-funded ([SpaceNews](https://spacenews.com/spacex-demonstrates-rocket-reusability-with-ses-10-launch-and-booster-landing/)).

**Opex.** Marginal: Musk to Aviation Week (May 2020), ~$15M for a reused F9 ([ElonX.net](https://www.elonx.net/how-much-does-it-cost-to-launch-a-reused-falcon-9-elon-musk-explains-why-reusability-is-worth-it/)).
SpaceX's Christopher Couluris separately said "$28M with everything" (2020 briefing). Price:
$62M → $67M (Mar 2022, [Space.com](https://www.space.com/spacex-raises-prices-launch-starlink-inflation))
→ $69.75M (2024) → $74M (Feb 2026, [SatBase](https://satbase.com/articles/spacex-falcon-9-price-increase-2026)).
NSSL task orders run ~$102–105M (FY2024/25, [Spaceflight Now](https://spaceflightnow.com/2025/04/05/u-s-space-force-awards-13-7-billion-in-new-national-security-launch-contracts-to-blue-origin-spacex-and-ula/)).

**Payload/$-per-kg.** 22,800 kg expendable vs. ~17,400–18,500 kg with booster recovery
(typical operational mode). ~$70M ÷ 17,400 kg ≈ $4,000/kg (derived).

**Status.** Partial reuse. ~658 total Falcon 9 launches (all variants) as of mid-2026;
record booster ~34–35 flights. Cadence: 91 (2023), 132 (2024), 165 (2025) —
[Space.com](https://www.space.com/space-exploration/private-spaceflight/spacex-shatters-its-rocket-launch-record-yet-again-167-orbital-flights-in-2025). Active.

---

## Falcon Heavy

**Capex.** Musk: "over half a billion dollars, or more," self-funded, stated right after
the Feb 6 2018 debut flight ([SpaceNews](https://spacenews.com/spacex-successfully-launches-falcon-heavy/);
[GeekWire](https://www.geekwire.com/2018/spacexs-elon-musk-marvels-surreal-falcon-heavy-success-looks-ahead-bigger-spaceship/)) —
no government funding, leveraged existing F9 tooling. Payload Research (ESTIMATE)
corroborates an FH-specific increment of ~$500M over reusable F9.

**Opex.** List price $90M (2018–2021) → $97M (2022) ([Wikipedia](https://en.wikipedia.org/wiki/Falcon_Heavy);
[CNBC](https://www.cnbc.com/2022/03/23/spacex-raises-prices-for-launches-and-starlink-due-to-inflation.html)).
Musk separately quoted $150M "at most" fully expendable ([CNBC](https://www.cnbc.com/2018/02/12/elon-musk-spacex-falcon-heavy-costs-150-million-at-most.html)).
USSF/NSSL awards run higher and include non-recurring infrastructure (USSF-67 = $316M,
[SpaceNews](https://spacenews.com/spacex-explains-why-the-u-s-space-force-is-paying-316-million-for-a-single-launch/));
NASA Psyche = $117M ([NASA](https://www.nasa.gov/news-release/nasa-awards-launch-services-contract-for-the-psyche-mission/)).
No marginal-cost figure exists.

**Payload/$-per-kg.** 63,800 kg fully expendable vs. ~57,000 kg (side boosters recovered,
center core expended, most-flown config). $97M ÷ 63,800 kg ≈ $1,521/kg (mixed basis — see
CSV note); on the internally-consistent $150M expendable price, ~$2,350/kg.

**Status.** Partial reuse. 12 flights through Apr 2026, 100% success. Active, low cadence.

---

## Starship (expendable mode, scoped to IFT-1, April 2023)

**Capex.** No document quantifies SpaceX's total self-investment as of April 2023
specifically. NASA's HLS Option A contract ($2.89B, Apr 2021, [NASA](https://www.nasa.gov/news-release/as-artemis-moves-forward-nasa-picks-spacex-to-land-next-americans-on-moon/))
funds lunar-lander work only, not total Starship program cost. SpaceX CFO Bret Johnsen's
sworn declaration (~May 19 2023, ~1 month after IFT-1): SpaceX invested "more than $3
billion" in Starbase + Starship/Super Heavy, July 2014 through that date ([CNBC](https://www.cnbc.com/2023/05/22/spacex-joining-faa-to-fight-environmental-lawsuit-over-starship.html)) —
best available cumulative figure, blends facility construction with vehicle R&D, slightly
postdates IFT-1. Musk (Apr 29 2023): SpaceX would spend "~$2 billion" on Starship in
calendar 2023; long-term total R&D projected at $5–10B ([CNBC](https://www.cnbc.com/2023/04/29/elon-musk-spacexs-starship-costing-about-2-billion-this-year.html)) — forward-looking.

**Opex (expendable).** No expendable Starship has flown commercially. Musk's $2M marginal
target is explicitly for a fully-reusable, high-cadence vehicle — NOT used here. [Payload
Research](https://payloadspace.com/payload-research-detailing-artemis-vehicle-rd-costs/)
(ESTIMATE, ~2024) puts ~$100M to "build and expend" a stack.

**Payload/$-per-kg.** SpaceX-cited ~250,000 kg expendable capacity ([Wikipedia](https://en.wikipedia.org/wiki/SpaceX_Starship)).
$100M ÷ 250,000 kg ≈ $400/kg — derived, speculative.

**Status.** IFT-1 (Apr 20 2023) destroyed via FTS ~4 min into flight; 1 flight; development.

---

## Antares

**Capex.** SEC filings via [FlightGlobal](https://www.flightglobal.com/space/orbital-sciences-development-costs-increase/105078.article):
Orbital's estimated total Antares/Cygnus development cost reached $472M by 2012 (up from
$458M Q4 2011), against NASA's COTS milestone payments of $288M (NASA's contribution only).
Bundles Antares rocket + Cygnus spacecraft development, not cleanly separable. Reported ~1
year before the April 2013 debut — best available "cost to first launch" proxy.

**Opex.** No pure launch-only marginal cost is public. [Planetary Society's 2017
analysis](https://www.planetary.org/articles/201705011-data-orbital-spacex) of NASA CRS-1
contract data: Cygnus missions averaged ~$339M/flight (vs. ~$182M for SpaceX Dragon over
the same period) — bundles launch + Cygnus production + NASA overhead; 1.86x Dragon's cost.

**Payload/$-per-kg.** Antares 230/230+ rated LEO capacity 8,000 kg; average actual cargo
delivered only ~2,600 kg (Cygnus itself is usually the limiting factor). $339M ÷ 8,000 kg ≈
$42,375/kg (rated); ÷ 2,600 kg ≈ $130,385/kg (actual delivered).

**Status.** Expendable. 18 launches (17 success, 1 failure — Oct 2014 Orb-3 pad explosion)
through the final 230+ flight (Aug 2023). 200-series retired Aug 2023 (lost Russian RD-181
supply); Cygnus has since flown on Falcon 9. Antares 330 (Firefly-built first stage) targets
NET 2026. [Wikipedia](https://en.wikipedia.org/wiki/Antares_(rocket)).

---

## Space Shuttle (STS)

**Capex.** NASA's own end-of-program estimate: $209B total life-cycle cost, 1971–2011
(2010$) ([Space.com](https://www.space.com/12166-space-shuttle-program-cost-promises-209-billion.html)).
Alternates: $192B (2010$) per economist Roger Pielke Jr.'s reconstruction ([blog](http://rogerpielkejr.blogspot.com/2011/04/space-shuttle-costs-1971-2011.html));
$254.521B (2024$) per a 2013 peer-reviewed AIAA/JSR retrospective ([DOI](https://arc.aiaa.org/doi/10.2514/1.A36428)),
split $52.621B DDT&E + $201.9B operations & sustainment. DDT&E-only reconstruction from
actual NASA budget obligations FY1972–1984: $10.162B then-year ([Planetary Society](https://www.planetary.org/space-policy/sts-program-development-cost)),
$10.606B incl. facilities.

**Opex.** Marginal: GAO's FY1993 figure, $44.4M then-year, covering only consumables/
personnel that scale with flight rate, excluding ~90% fixed institutional overhead ([GAO
NSIAD-93-115](https://www.gao.gov/assets/nsiad-93-115.pdf)). Same report: FY1993 "average
cost per flight" $413.5M (still excludes ~$30.2B sunk development cost through 1992). NASA
publicly cited ~$450M/mission (nominal, 2011) near program end. Fully-loaded: ~$1.5B/flight
(2010$) per Pielke; $1,697M (2018$) per a NASA Ames peer-reviewed paper citing Pielke &
Byerly's 2011 *Nature* piece ([Jones, NASA ICES-2018-81](https://ntrs.nasa.gov/api/citations/20200001093/downloads/20200001093.pdf)).

**Payload/$-per-kg.** 27,500 kg (204km/28.5°); 16,050 kg to ISS orbit. $1,697M ÷ 27,500 kg ≈
$61,720/kg (2018$); to ISS orbit ≈ $105,800/kg.

**Status.** Partial reuse (orbiter + SRBs; tank expended). 135 flights, 2 losses (Challenger
1986, Columbia 2003). Retired 2011.

---

## SLS (Space Launch System)

**Capex.** Cumulative SLS-rocket-only obligations, program inception (~2011) through first
flight (Nov 2022): $23.8B nominal; combined with Orion ($20.4B) + Exploration Ground
Systems ($5.7B), total Artemis vehicle-side cost through 2022 = $49.9B ([Planetary
Society](https://www.planetary.org/space-policy/cost-of-sls-and-orion)). NASA's own
narrower "cost to develop the initial SLS capability": $11.8B ($2.7B formulation/design +
$9.1B development), per [GAO-23-105609](https://www.gao.gov/products/gao-23-105609).

**Opex.** Marginal/production-only: NASA OIG found a single SLS rocket costs ~$2.2B to
produce ([IG-22-003](https://oig.nasa.gov/docs/IG-22-003.pdf)). Fully loaded: same report —
SLS + Orion + European Service Module + Exploration Ground Systems averages $4.1B/launch
for Artemis I–IV, which OIG called "unsustainable."

**Payload/$-per-kg.** SLS Block 1 ≈ 95,000 kg to LEO (NASA typically quotes TLI mass >27t
instead, [fact sheet](https://www.nasa.gov/wp-content/uploads/2020/02/sls_lift_capabilities_and_configurations_508_08202018_0.pdf)).
$4.1B ÷ 95,000 kg ≈ $43,158/kg (derived, not officially published).

**Status.** Expendable. 2 flights: Artemis I (Nov 2022, uncrewed), Artemis II (Apr 2026,
crewed lunar flyby). Active.

---

## Saturn V

**Capex.** $6.6B then-year 1960s (Saturn V specifically, of a $9.4B total Saturn-family
spend incl. Saturn I/IB/engines), peer-reviewed reconstruction from NASA Historical
Reference Collection budget documents ([Planetary Society](https://www.planetary.org/space-policy/cost-of-apollo));
≈$80B in 2025$. Alternate: $6.417B (1964–1973 nominal appropriations) per NASA/Wikipedia.
No source isolates cost through first launch (Apollo 4, Nov 1967) from the whole ~15-vehicle
program total.

**Opex.** No formal marginal-vs-fully-loaded split exists (each vehicle built to a fixed
contract, not mass-produced). Standard figure: $185M (1969$), the Saturn V's notional share
of Apollo 11's $355M total mission cost. [Jones, NASA ICES-2018-81](https://ntrs.nasa.gov/api/citations/20200001093/downloads/20200001093.pdf)
inflation-adjusts this to $728M (2018$).

**Payload/$-per-kg.** 140,000 kg (uprated Block II, Apollo 15–17/Skylab; earlier ~118,000
kg). $728M ÷ 140,000 kg = $5,200/kg (2018$).

**Status.** Expendable. 13 launches, Nov 1967 – May 1973. Retired.

---

## Titan IV

**Capex.** USAF's Dec 1990 Selected Acquisition Report ESTIMATE: $18.3B nominal (~1990$)
for 65–66 vehicles over 16 years, via [GAO NSIAD-91-271](https://www.gao.gov/assets/nsiad-91-271.pdf)
(program estimate, not closed-out actual). No cost-to-first-launch figure isolated.

**Opex.** From the 1997 NASA Cassini/Titan-IV-Centaur launch ([GAO NSIAD-95-141BR](https://www.gao.gov/assets/nsiad-95-141br.pdf)):
$253.4M (FY1996$) = direct NASA payment to USAF for booster+Centaur+launch services
(marginal proxy); $451.7M (FY1996$) = total NASA-side mission cost incl. integration
contract and reserves (fully-loaded, this specific NASA/Centaur config is pricier than a
bare USAF Titan IV-B). A widely repeated $432M figure traces only to a secondary Astronautix
essay, not a primary source.

**Payload/$-per-kg.** 21,680 kg (Titan IV-B). [Jones, NASA ICES-2018-81](https://ntrs.nasa.gov/api/citations/20200001093/downloads/20200001093.pdf)
(citing Wertz & Larson, *Reducing Space Mission Cost*, 1996): $24,700/kg (2018$, basis
year 1989).

**Status.** Expendable. 39 launches (22 IV-A + 17 IV-B). Retired 2005 (cost, toxic
hypergolic propellants; replaced by EELV).

---

## Titan II GLV (Gemini Launch Vehicle)

**Capex.** NASA's Jan 1969 report to Congress: total Project Gemini program cost (spacecraft
$797.4M + launch vehicles $409.8M + support $76.2M), then-year 1962–1967 ([NASA SP-4002](https://www.nasa.gov/history/SP-4002/p1b.htm)) —
the $409.8M "launch vehicles" line bundles Titan II GLV boosters AND Atlas-Agena target
vehicles, not separable further. Vehicle-specific proxy: NASA's Gemini Program Office cost
tracking shows the "Titan II" line item rising from $113.0M to $161.8M as of May 1962 (~2
years before the April 1964 first launch) — a pre-launch estimate, not a final actual cost.

**Opex.** No reliable vehicle-specific marginal or fully-loaded figure exists. The only
per-flight economics available is whole-program (booster+spacecraft, NOT launch-vehicle-
only): Claude Lafleur's cost-comparison analysis puts total Gemini spending at $1.3B (1967$)
≈ $9.31B (2024$), ≈$723M/crewed flight (2010$) across 10 crewed missions ([The Space
Review, 2010](https://www.thespacereview.com/article/1579/1)) — not used as this vehicle's
opex figure since it isn't launch-vehicle-only.

**Payload/$-per-kg.** 3,600 kg (Gemini spacecraft mass). [Jones, NASA ICES-2018-81](https://ntrs.nasa.gov/api/citations/20200001093/downloads/20200001093.pdf):
$31,000/kg (2018$, basis year 1962) — likely reflects the generic Titan II space-launcher
config rather than the specifically man-rated GLV variant; caution flagged.

**Status.** Expendable. 12 launches (2 uncrewed, 10 crewed), 100% success. Retired 1966.

---

## Atlas D (SM-65D Atlas / Atlas LV-3B)

Real designation, since "Original Atlas" was a placeholder label: the missile family is
SM-65 Atlas; the D-model (redesignated CGM-16D in 1962) is "Atlas D"; the specific orbital
configuration flown for Mercury (with the Mercury capsule replacing the reentry vehicle) was
called **Atlas LV-3B**. The capex figure below covers the WHOLE SM-65 program (all A–F
variants), while the opex/payload figures are specific to the D-model/LV-3B configuration —
a real mismatch in scope, flagged here and in the CSV notes, not something the rename fixes.

**Capex.** Full Atlas ICBM crash-program cost: ~$8B (1959$) — missile R&D, production of
~350 missiles, and construction of 129 launch complexes; ~$2B (roughly a quarter) went to
design/development ([Air & Space Forces Magazine](https://www.airandspaceforces.com/article/1009atlas/)).
Cold War crash program under Eisenhower's highest-national-priority designation
(1955–56); comparable in scale to the Manhattan Project (~$2B). No figure isolates R&D cost
through first flight (June 1957) alone.

**Opex.** LOW CONFIDENCE — only traced to Encyclopedia Astronautica/astronautix.com
(site returned HTTP 503 during re-verification): early estimate $3.5M/booster, later unit
price $8.309M (1965$). NASA's Project Mercury (Redstone + Atlas combined) cost $384.1M total
(1963 accounting); the $82.9M "launch vehicles" line spans ~20 missions across both booster
types and can't be isolated to per-Atlas-launch cost ([Wikipedia: Project Mercury](https://en.wikipedia.org/wiki/Project_Mercury),
citing NASA SP-4201).

**Payload/$-per-kg.** Atlas D/LV-3B: 1,360 kg (Mercury capsule mass) ([Wikipedia: Atlas
LV-3B](https://en.wikipedia.org/wiki/Atlas_LV-3B)). ~$6,103/kg using the $8.3M/1965 price —
flagged low-confidence throughout.

**Status.** Expendable. SM-65 retired from ICBM service by 1965; ~24 Atlas A/B/C/D orbital-
relevant flights tallied here (350 missiles built across the full family, mostly deployed
ICBMs never launched). [Wikipedia: SM-65 Atlas](https://en.wikipedia.org/wiki/SM-65_Atlas).

---

## Atlas V

**Capex.** No Atlas-V-specific breakout exists; all figures found are combined EELV program
(Atlas V + Delta IV). GAO: ~$8.2B invested through FY2008 ([GAO-08-1039](https://www.gao.gov/assets/a281772.html));
by 2012, after a Nunn-McCurdy breach, the whole EELV program (FY1998–2030) had grown to an
estimated $70B ([SpacePolicyOnline](https://spacepolicyonline.com/news/gao-eelv-program-to-cost-70-billion-through-2030/);
[EveryCRSReport R44498](https://www.everycrsreport.com/reports/R44498.html)).

**Opex.** 2016 ULA RocketBuilder list prices: $109M (Atlas V 401), $153M (551), +~$6.8M per
extra SRB ([Wikipedia](https://en.wikipedia.org/wiki/Atlas_V)). Government contracts: $187M
(2010 NASA MAVEN), $164M (2013 USAF block buy, 401), $132.4M (2015 NASA TDRS-M). No
marginal-cost figure is disclosed.

**Payload/$-per-kg.** 9,800 kg (401 config) to LEO. $109M ÷ 9,800 kg ≈ $11,122/kg.

**Status.** Expendable. ~100–109 launches depending on tally date; 100% mission success.
First flight Aug 2002. Production ended 2024; retiring in favor of Vulcan Centaur.

---

## Delta IV (Medium & Heavy)

**Capex.** Same combined-EELV caveat as Atlas V — no Delta-IV-specific breakout exists.

**Opex.** ULA CEO Tory Bruno cited $350M standard for Delta IV Heavy; NRO missions up to
$440M (Wikipedia infobox); NASA's 2015 Parker Solar Probe contract = $389.1M. By ~2018 an
industry source told SpaceNews ULA had brought the price below $300M (exact figure withheld —
["the real price is a secret"](https://spacenews.com/cost-of-delta-4-heavy-launches-is-down-but-the-real-price-is-a-secret/)).
A $149M contract modification for one NROL Heavy mission (2019) and a $1.18B five-year NRO
ops-support contract (5 missions) also exist but bundle production/ops support.

**Payload/$-per-kg.** Delta IV Heavy: 28,370 kg to LEO. $350M ÷ 28,370 kg ≈ $12,336/kg.
(Delta IV Medium payload ≈8,510 kg, no matching price found.)

**Status.** Expendable. 45 family launches (16 Heavy: 15 success, 1 partial failure on its
2004 maiden flight). Retired — final Heavy flight April 2024 (NROL-70).

---

## Neutron (Rocket Lab) — PRE-FIRST-FLIGHT, all figures are company projections

**Capex.** Original estimate (2021–22, around announcement/2022 Investor Day): $250–300M
([Payload Research](https://payloadspace.com/rocket-development-costs-by-vehicle-payload-research/);
[Rocket Lab 2022 Investor Day](https://www.businesswire.com/news/home/20220921005916/en/Rocket-Lab-Hosts-Investor-Day-and-Neutron-Development-Update)).
Updated (Q3/Q4 2025): CFO Adam Spice stated cumulative spend through end of 2025 would
reach ~$360M ([SpaceNews](https://spacenews.com/rocket-lab-delays-first-neutron-launch-to-2026/);
[Spaceflight Now](https://spaceflightnow.com/2025/11/11/rocket-lab-delays-debut-of-neutron-rocket-to-2026/)).
All figures are company self-reported via earnings calls/investor days, not audited.

**Opex.** $50M target list price, announced March 2023 ([CNBC](https://www.cnbc.com/2023/03/24/rocket-lab-neutron-launch-price-challenges-spacex.html));
more recent reporting cites $50–55M. No confirmed marginal cost (vehicle hasn't flown).

**Payload/$-per-kg.** 13,000 kg (partial reuse, downrange landing); 15,000 kg fully
expendable; 8,500 kg RTLS ([Wikipedia: Rocket Lab Neutron](https://en.wikipedia.org/wiki/Rocket_Lab_Neutron)).
$50M ÷ 13,000 kg ≈ $3,846/kg (predicted).

**Status.** Has not flown. Target first launch Q4 2026 NET (already delayed from 2024).

---

## New Glenn

**Capex.** Official Blue Origin figure: $2.5B, Jeff Bezos, April 2017 ([NASA Watch, citing
GeekWire](https://nasawatch.com/commercialization/blue-origin-reveals-some-cost-numbers/)) —
likely stale given years of subsequent delays. Third-party ESTIMATES (not confirmed by Blue
Origin): ~$10B per an anonymous former employee ([Forbes, Jan 2025](https://www.forbes.com/sites/jeremybogaisky/2025/01/11/new-glenn-bezos-blue-origin-musk-spacex/));
~$14B per Space Capital's Chad Anderson — but that figure is for ALL of Blue Origin's
spending, not New Glenn specifically ([IBTimes UK](https://www.ibtimes.co.uk/jeff-bezos-sells-1635m-amazon-shares-worth-241b-blue-origin-gears-new-glenn-launch-1729673)).
Blue Origin separately spent >$1B rebuilding Launch Complex 36 (completed 2021) and received
~$500M in USAF NSSL Phase 2 cost-share funding.

**Opex.** Commercial estimate $68–110M (analyst estimates; no official Blue Origin list
price). NASA's ESCAPADE (NG-2) was priced at only ~$20M under NASA's VADR program — an
atypical discount, not representative ([SpaceNews](https://spacenews.com/blue-origin-wins-first-nasa-business-for-new-glenn/)).
USSF NSSL Phase 3 Lane 2 (Apr 2025): ~7 flights for $2.4B total (~$343M/mission avg) —
national-security mission-assurance pricing ([Spaceflight Now](https://spaceflightnow.com/2025/04/05/u-s-space-force-awards-13-7-billion-in-new-national-security-launch-contracts-to-blue-origin-spacex-and-ula/)).

**Payload/$-per-kg.** 45,000 kg (operational 7×2 config; [Wikipedia](https://en.wikipedia.org/wiki/New_Glenn)).
$68M ÷ 45,000 kg ≈ $1,511/kg.

**Status.** Partial reuse. 3 launches: NG-1 (Jan 2025, success, booster landing failed),
NG-2 (Nov 2025, success, first successful booster landing, NASA ESCAPADE), NG-3 (Apr 2026,
upper-stage malfunction stranded payload though the reused booster landed — first New Glenn
booster reuse). May 28 2026: a first stage exploded during a pre-launch static-fire test at
LC-36, damaging the pad; return-to-flight expected before end of 2026 ([SpaceNews](https://spacenews.com/new-glenn-rocket-explodes-on-cape-canaveral-pad/)).

---

## Soyuz (R-7-derived family)

**Capex.** No reliable public total-program or to-first-launch figure exists in dollar or
even ruble terms. Original R-7/Soyuz-era development (1950s–60s, Korolev's OKB-1) was never
disclosed with an auditable budget; Soviet-era ruble accounting under a non-convertible
currency makes dollar conversion methodologically suspect. A genuine, expected gap.

**Opex.** Glavkosmos Launch Services (Roscosmos's commercial arm) stated at the 2018 IAC:
$48.5M with Fregat upper stage, $35M without ([TASS](https://tass.com/science/1024055)).
Earlier Starsem-era pricing (late 1990s–2000s): $35–52M ([GlobalSecurity.org](https://www.globalsecurity.org/space/world/russia/launch_services_cost_study.htm)).

**Payload/$-per-kg.** Soyuz-2.1b from Baikonur: 8,300–8,670 kg cited by secondary sources
([rocketlaunch.org](https://rocketlaunch.org/launch-providers/progress-rocket-space-center/soyuz-21b));
no single authoritative LEO number exists across the whole family. $48.5M ÷ 8,300 kg ≈
$5,843/kg.

**Status.** Expendable. Flight count is inconsistent across sources (Wikipedia's variant
table sums ~1,100+; prose text cites "more than 1,700 flights" for the broader lineage) —
reflects genuinely poor consolidated bookkeeping, not a research gap. Active, declining
cadence; successor Soyuz-5 conducted a suborbital test in 2026.

---

## Proton (UR-500/Proton-K/Proton-M)

**Capex.** No reliable dollar figure for the original Soviet UR-500/Proton development
program (Chelomei design bureau, first flight 1965) exists publicly. Astronautix cites
~100 million rubles/launch as an internal Soviet OPERATING-cost figure (not development
capex, not reliably dollar-convertible).

**Opex.** ILS commercial price: ~$28–35M (late 1990s) → ~$65–85M (2000s) → $95M (2014)
reduced to $69–70M (Apr 2015), per Roscosmos chief Igor Komarov ([TASS](https://tass.com/non-political/789170)).
Current Wikipedia infobox: $65M. Roscosmos later floated matching Falcon 9 pricing without
a further specific figure ([TASS](https://tass.com/science/1050342)).

**Payload/$-per-kg.** 23,000 kg (Proton-M, 180km/51.5° from Baikonur, [Wikipedia](https://en.wikipedia.org/wiki/Proton-M)).
$70M ÷ 23,000 kg ≈ $3,043/kg.

**Status.** Expendable. 431 family launches since 1965 (383 successful, 88.9%); Proton-M
alone 116 launches as of Feb 2026. Active, being phased out for Angara A5.

---

## H-II / H-IIA

**Capex.** RAND Corporation's 2005 report: Japan invested "over 320 billion yen" in the
combined H-2 and H-2A launcher development through spring 2004 ([RAND TR-184](https://www.rand.org/pubs/technical_reports/TR184.html)) —
≈$2.9B nominal at ~110 JPY/USD (2004 basis); combined-family figure. Predecessor H-II alone
reportedly had per-launch OPERATING costs of 14–19.5 billion yen (~$190M) — an opex, not
capex, figure, and a major driver for developing the cheaper H-IIA ([Wikipedia: H-II](https://en.wikipedia.org/wiki/H-II)).

**Opex.** ~$90M per H-IIA launch ([Wikipedia: H-IIA](https://en.wikipedia.org/wiki/H-IIA)).

**Payload/$-per-kg.** 10,000–15,000 kg depending on config (202/204); midpoint 12,500 kg
used. $90M ÷ 12,500 kg ≈ $7,200/kg.

**Status.** Expendable. 50 launches, 49 successful (98%), incl. 44 consecutive successes
2003–2025. Operated by MHI under JAXA oversight since 2007. Retired — final flight (GOSAT-GW)
28 June 2025.

---

## H3

**Capex.** ~200 billion yen (~$1.5B), per Spaceflight Now trade-press reporting around the
first (failed) launch attempt, Feb/Mar 2023 ([article 1](https://spaceflightnow.com/2023/03/07/japans-flagship-h3-rocket-fails-on-first-test-flight/);
[article 2](https://spaceflightnow.com/2023/02/17/first-launch-of-japans-h3-rocket-aborted-moments-before-liftoff/)) —
best-documented, most consistently repeated figure; reported at first-flight time so likely
functions as both total-program and to-first-launch cost, though later fixes and the H3-30
variant's development aren't separately broken out.

**Opex.** MHI's target ~¥5 billion for the H3-30 (no-SRB) config — roughly half an H-IIA
flight. Reported dollar values range $33–51M depending on source/year/exchange rate: $33.9M
([Wikipedia](https://en.wikipedia.org/wiki/H3_(rocket)), 2024 rate), $33M ([Al Jazeera](https://www.aljazeera.com/news/2024/2/17/japan-successfully-launches-h3-rocket-after-back-to-back-failures)),
$50M (Spaceflight Now, 2023).

**Payload/$-per-kg.** H3-24 (2-SRB) config: 16,000 kg to ISS-type orbit — a DIFFERENT
configuration than the one the ~$34–51M price applies to (H3-30, ~4,000 kg to SSO). This
mismatch means $/kg cannot be honestly computed across configs; left blank rather than
blended in the CSV.

**Status.** Expendable. F1 failed (7 Mar 2023, 2nd-stage ignition failure), 5 straight
successes, F8 failed (22 Dec 2025, payload-adapter delamination destroyed QZS-5, [Spaceflight
Now](https://spaceflightnow.com/2025/12/22/h3-rocket-suffers-upper-stage-anomaly-fails-to-correctly-deploy-navigation-satellite/);
[SpaceNews](https://spacenews.com/h3-failure-linked-to-payload-fairing-separation-anomaly/)),
F9 succeeded (12 Jun 2026, first H3-30 flight, return-to-flight). Net: 9 launches, 7
successes, 2 failures. Active, stabilizing reliability.

---

## PSLV (Polar Satellite Launch Vehicle)

**Capex.** No reliable original PSLV development-cost figure (1980s program through first
1993 flight) could be located in Wikipedia, ISRO's own site, or any Lok Sabha reply found —
a genuine gap. The oft-cited ₹6,131 crore (2018 Cabinet approval, ~$750M 2023 basis) is a
bulk-procurement/OPERATIONS budget for 30 flights 2019–2024, not development capex, and is
deliberately excluded from the capex fields ([Wikipedia](https://en.wikipedia.org/wiki/Polar_Satellite_Launch_Vehicle)).

**Opex.** Commonly cited $15–31M depending on payload/variant; PSLV-C37 (104-satellite
rideshare) ~$15M. Marginal/production proxy: NSIL's $104M contract for 5 industry-built
PSLV-XL rockets (~$20.8M/unit, [Payload Space](https://payloadspace.com/oneweb-launch-shows-isros-budding-commercial-opportunities/)).

**Payload/$-per-kg.** PSLV-XL: 3,800 kg to 200km/30° LEO ([Wikipedia](https://en.wikipedia.org/wiki/Polar_Satellite_Launch_Vehicle));
ISRO's own site instead emphasizes 1,750 kg to 600km SSO, its more typical actual mission
profile ([ISRO PSLV page](https://www.isro.gov.in/PSLV_CON.html)) — both reported since not
interchangeable. $20M ÷ 3,800 kg ≈ $5,470/kg.

**Status.** Expendable. 64 flights as of Jan 2026 (58 success, 4 failure, 1 partial, 1
pending classification). Two consecutive failures (PSLV-C61 May 2025, PSLV-C62 Jan 2026)
linked to third-stage anomalies prompted an ISRO expert review ([SpaceNews](https://spacenews.com/indias-pslv-launch-fails-during-ascent-16-satellites-lost/);
[Spaceflight Now](https://spaceflightnow.com/2026/01/12/indias-pslv-suffers-second-consecutive-launch-failure-16-satellites-lost/)).

---

## GSLV Mk II

**Capex.** No development-cost figure could be independently verified against a reliable
primary or trade-press source; a commonly circulated "$500M" figure could not be confirmed
against any cited reference and was excluded rather than reported. Documented instead:
production/procurement batch approvals — ₹945 crore (Apr 2003, F01–F03 + long-lead items)
and ₹1,325 crore (Dec 2006, F04–F10) — not R&D capex ([Wikipedia: GSLV](https://en.wikipedia.org/wiki/Geosynchronous_Satellite_Launch_Vehicle)).

**Opex.** ~$47M per launch.

**Payload/$-per-kg.** 6,000 kg to LEO (GTO 2,500 kg, SSO 3,000 kg — GSLV's typical actual
missions are GTO, not LEO). $47M ÷ 6,000 kg ≈ $7,833/kg.

**Status.** Expendable. 18 flights through July 2025 (12 success, 4 failure, 2 partial
failure). ISRO has stopped selling/producing new Mk II vehicles (as of Oct 2024) though it
remains active for its remaining manifest (NVS, IDRSS, NISAR).

---

## GSLV Mk III / LVM3 (bonus row)

Not one of the originally requested 20 vehicles (which asked for "GSLV" generically,
mapped to GSLV Mk II above) — included as a bonus row because LVM3's development cost is
far better documented via a primary parliamentary source, and it usefully anchors the India
cluster with real capex data (unlike PSLV/GSLV Mk II, which have none).

**Capex.** ₹2,962.78 crore (~$470M, 2023 basis) total development cost, per **Government of
India, Department of Space, Lok Sabha Unstarred Question no. 3713 ("GSLV MK-III"), dated 12
August 2015** — a genuine primary parliamentary source, the best-documented development-cost
figure in this entire dataset ([cited via Wikipedia: LVM3](https://en.wikipedia.org/wiki/LVM3)).
Separately, ₹4,338 crore was approved June 2018 for a 10-rocket production batch (~₹433.8
crore/~$52M per unit) — a marginal/production-cost proxy, not R&D capex.

**Opex.** NSIL secured two OneWeb LVM3 launch contracts at $60M/launch (vs. $67M for a
contemporaneous dedicated Falcon 9), signed March 2022, flown Oct 2022 and Mar 2023
([Payload Space](https://payloadspace.com/oneweb-launch-shows-isros-budding-commercial-opportunities/)).

**Payload/$-per-kg.** ISRO's own site states 8,000 kg to 600km LEO; Wikipedia's infobox
instead states 10,000 kg — a genuine discrepancy between the two best sources, both
reported ([ISRO LVM3 page](https://www.isro.gov.in/GSLVmk3_CON.html); [Wikipedia](https://en.wikipedia.org/wiki/LVM3)).
$60M ÷ 8,000 kg ≈ $7,500/kg.

**Status.** Expendable. First suborbital test 18 Dec 2014; first orbital flight 5 June
2017. 9 launches, all successful, as of Dec 2025. Active.

---

# New-space startups (added in a second research pass)

The vehicles below were added to answer a follow-up request to cover the current wave of
new-space launch startups globally. **Almost every figure in this section is a company
funding-raised total used as a capex PROXY, not a disclosed vehicle-specific development
cost** — none of these companies publish an audited R&D figure the way NASA/GAO do, and
several are also multi-program companies (e.g. Firefly also builds lunar landers; Relativity
previously built and retired Terran 1) so their total raised capital is a looser proxy than
for a single-vehicle company. Where a company hasn't reached orbit yet, both capex fields
necessarily hold the same "total raised to date" number, since there's no way yet to isolate
spending "through first launch" from ongoing spending. All commercial/target prices for
pre-flight vehicles are explicitly predictions, not realized revenue.

## Terran R (Relativity Space, USA)

Relativity has raised $1.34B total across 8 rounds (largest: $650M Series E, June 2021) —
[Tracxn](https://tracxn.com/d/companies/relativity-space/__h5W7c_vzbvwpDtWeLA8Isw89aMethLWmokUCXAaA3Yk/funding-and-investors).
No standalone Terran-R capex figure is disclosed; this capital also funded the earlier
Terran 1 (flew once, March 2023, reached space but not orbit, since retired). Payload:
23,500 kg to LEO (reusable, downrange landing) / 33,500 kg expendable
([Wikipedia: Terran R](https://en.wikipedia.org/wiki/Terran_R)). No commercial price is
disclosed; company reports a $2.9B launch-services backlog (bookings, not a cost figure),
including an expanded SES multi-launch deal (Nov 2025,
[SES press release](https://www.ses.com/press-release/ses-relativity-space-expand-multi-launch-agreement-terran-r)).
First launch targeted late 2026 from LC-16, Cape Canaveral
([NASASpaceFlight.com](https://www.nasaspaceflight.com/2026/06/relativity-update-0626/)). Not yet flown.

## Nova (Stoke Space, USA)

$1.34B raised to date as of a Feb 2026 Series D extension (to $860M, from an initial $510M
in Oct 2025) — [GeekWire](https://www.geekwire.com/2026/stoke-space-350m-added-funding/);
[Stoke Space press release](https://www.stokespace.com/stoke-space-technologies-extends-previously-announced-series-d-financing-to-860-million/).
An earlier (2024) Payload Research estimate cited only ~$175M raised at that time — funding
scaled rapidly since. Payload: 3,000 kg to LEO with full reuse (both stages + fairing
recovered — Stoke's design targets FULL reusability, unlike the partial reuse of Falcon 9,
New Glenn, or Neutron) / 7,000 kg fully expendable
([Wikipedia: Stoke Space Nova](https://en.wikipedia.org/wiki/Stoke_Space_Nova)). No price
disclosed. Funding is activating Launch Complex 14 at Cape Canaveral. Not yet flown.

## Firefly Alpha (Firefly Aerospace, USA)

Firefly's own 2018 estimate: ~$100M Alpha-specific development cost
([CompositesWorld](https://www.compositesworld.com/articles/the-alpha-launch-vehicle-designing-performance-in-cost-out)).
A secondary Payload Research estimate instead treats Firefly's total raised capital (~$483M)
as a rough proxy, but Firefly is a multi-program company (Blue Ghost lunar landers,
Eclipse/MLV) so that figure likely overstates Alpha-specific spend
([Payload Research](https://payloadspace.com/rocket-development-costs-by-vehicle-payload-research/)).
Price: originally $15M advertised, now $19M
([Wikipedia: Firefly Alpha](https://en.wikipedia.org/wiki/Firefly_Alpha)) — exact year of the
increase not confirmed in this research. Payload: 1,030 kg to LEO (300km) / 630 kg to 500km
SSO. First flight Sept 2, 2021; ~7 flights through mid-2026 (approximate tally, not
independently reconfirmed flight-by-flight). Active — the only operational US 1-ton-class
small launcher.

## Eclipse / MLV (Firefly Aerospace + Northrop Grumman, USA)

Northrop Grumman's own stated co-development investment: $50M
([Firefly press release](https://fireflyspace.com/news/northrop-grumman-invests-50-million-in-firefly-aerospace-to-advance-medium-launch-vehicle-named-eclipse/)) —
likely UNDERSTATES the true total program cost since it excludes Firefly's own R&D spend
(undisclosed) as the other co-developer. Payload: 16,300 kg to LEO / 3,200 kg to GTO
([Wikipedia: Eclipse (rocket)](https://en.wikipedia.org/wiki/Eclipse_(rocket))). No price
disclosed. Designed as a successor to Antares (Northrop's legacy vehicle, elsewhere in this
dataset), shares first-stage design and Miranda engines with the planned Antares 330. First
flight targeted 2027. Not yet flown.

## RS1 (ABL Space Systems, USA) — program terminated

Included as a cautionary data point, not a going-concern vehicle. Total funding raised
before the program ended: ~$461M ("nearly half a billion dollars" —
[TechCrunch](https://techcrunch.com/2024/11/15/after-raising-nearly-half-a-billion-dollars-abl-space-pivots-from-launch-vehicles-to-missiles/)).
Only launch attempt (Jan 10, 2023, Kodiak Island, Alaska) fell back onto the pad and
exploded; the second built vehicle was destroyed during preflight ground testing in July
2024, before a second attempt could be made. ABL ended orbital launch plans in Nov 2024
(citing a tough launch market and supply-chain disruption from the Russian invasion of
Ukraine) and pivoted to missile-defense/hypersonic test technology, rebranding as "Long
Wall" in Feb 2025 ([Space.com](https://www.space.com/space-exploration/launches-spacecraft/rocket-startup-abl-space-systems-ends-orbital-launch-plans-pivots-to-missile-defense)).
No commercial price ever established; payload rating not independently verified in this
research and left blank rather than guessed.

## Spectrum (Isar Aerospace, Germany)

Total funding raised: ~€870M (~$950M), including a €270M Series D round
([SpaceNews](https://spacenews.com/isar-aerospace-raises-270-million-euros-for-global-launch-expansion/)).
Payload: 1,000 kg to LEO. Price: no flat per-launch price disclosed; the company's stated
TARGET was €10,000/kg (~$11,700/kg) — the CSV's opex figure is back-calculated from that
per-kg target times full payload, NOT a demonstrated commercial price, since Spectrum hasn't
reached orbit. Maiden flight March 30, 2025, from Andøya Space, Norway — lost attitude
control ~30s after liftoff (a vent-valve issue) and was terminated; the first orbital-class
launch attempt from Continental Europe by a commercial company
([Isar Aerospace press release](https://isaraerospace.com/press/isar-aerospace-lifts-off-successfully-during-first-test-flight-of-orbital-launch-vehicle)).
A second flight attempt followed in 2026 per ESA and Astronomy.com coverage; exact date/
detailed outcome not independently reconfirmed beyond "also fell short of orbit."

## RFA ONE (Rocket Factory Augsburg, Germany)

€30M (~$33M) KKR convertible-debt investment plus an €11M DLR grant
([RFA press release](https://www.rfa.space/rfa-secures-30m-investment-from-kkr/)) — likely
UNDERSTATES total spend since RFA (an OHB SE subsidiary) also draws on undisclosed
parent-company resources. Payload: 1,350 kg to polar orbit / 1,500 kg to 700km SSO. Target
price: €3M (~$3.3M) per launch, one of the most aggressive price targets in this dataset
([RFA press release](https://www.rfa.space/german-microlauncher-start-up-rocket-factory-announces-unrivalled-low-price-of-eur-3-million-per-rocket-launch/));
a more recent framing cites $3,000–4,000/kg for payloads up to 1,300 kg instead. The first
stage was destroyed in an Aug 2024 static-fire test explosion at SaxaVord Spaceport,
Shetland — not yet flown.

## Miura 5 (PLD Space, Spain)

Total funding raised: >€350M (~$407M), including a €180M Series C round and a €30M EIB
venture-debt loan (April 2026) —
[Spaceflight Now](https://spaceflightnow.com/2026/03/05/spanish-launch-startup-pld-space-raises-209-million-to-scale-its-rocket-production/).
Also received €169M in Spanish-government-backed launch commitments via ESA's European
Launcher Challenge (a revenue commitment, not a cost figure). Payload: 1,000 kg to LEO / 540
kg to SSO. No price disclosed. PLD's earlier Miura 1 (a much smaller suborbital technology
demonstrator) flew successfully in Oct 2023. Miura 5 targeted for a late-2026 debut from
Kourou, French Guiana; not yet flown.

## Prime (Orbex, UK)

Total funding raised: >£100M (~$124.5M) across rounds from a 2018 £30M raise through a 2024
Series D (~$20.7M) and 2025 UK government funding (~$25M) —
[TechCrunch](https://techcrunch.com/2024/04/18/orbexs-new-funding-may-accelerate-its-prime-microlauncher-into-orbit/).
Payload: 180 kg to LEO / 150 kg to SSO. No price disclosed. Designed to launch from
Sutherland Spaceport, Scotland; partially reusable (first-stage recovery planned).
Preselected (July 2025) for ESA's European Launcher Challenge (up to €169M available, a
revenue/support commitment, not a cost figure). Not yet flown.

## Maia (MaiaSpace, France)

ArianeGroup's (parent company) cumulative equity investment, raised in stages to €125M
(~$137M) by 2025, plus warrants that could add another €40M if exercised —
[European Spaceflight](https://europeanspaceflight.com/arianegroup-to-increase-maiaspace-investment-to-e125m/).
MaiaSpace separately reported €180M in customer advances/down-payments in 2024 filings —
prepayments on future launch contracts, not a development-cost figure, so not used as capex
here. Payload: 500 kg to LEO with first-stage recovery / 1,500 kg fully expendable. No price
disclosed. Positioned as Europe's push into reusability; also proposed as a future
booster-recovery upgrade path for Ariane 6 itself. Originally targeted a 2025 debut, since
delayed; not yet flown.

## Agnibaan (Agnikul Cosmos, India)

Funding raised: ~$40M through an Oct 2023 Series B, plus a further ~$17M round at a $500M
valuation ([Inc42](https://inc42.com/buzz/update-agnikul-raises-17-mn-at-500-mn-valuation/)).
Payload (orbital-class configuration): 100 kg to a 700km orbit standard / 500 kg to 700km SSO
fully expendable. No price disclosed. The one flight to date (May 30, 2024, "Agnibaan
SOrTeD") was a SUBORBITAL single-stage technology demonstrator using a 3D-printed
semi-cryogenic engine (Agnilet) — not the full multi-stage orbital configuration this
dataset's capacity figures describe; treated as a company milestone rather than a true
orbital first flight. Orbital Agnibaan debut still pending as of this research.

## Vikram-1 (Skyroot Aerospace, India)

Total funding raised: ~$160M, including a $60M round in May 2026 that valued the company
above $1B — India's first space-tech unicorn
([SpaceNews](https://spacenews.com/skyroot-raises-60-million-ahead-of-first-orbital-launch-attempt/)).
Payload: 350 kg to LEO (three solid stages + a liquid-fuel kick stage). No price disclosed.
The one flight to date (Nov 18, 2022, "Vikram-S") was a SUBORBITAL single-stage
demonstrator — India's first privately-developed rocket to fly — not the orbital Vikram-1;
treated as a milestone rather than a true orbital first flight. Orbital debut still pending
as of this research (mid-2026).

## Kairos (Space One, Japan)

Cumulative fundraising of ¥20 billion (~$130M) per an Oct 2024 company press release
([Space One](https://www.space-one.co.jp/news/news_20241009_02_e.html)), plus a separate
¥8.5 billion (~$55M) Japan Ministry of Defense contract for upper-stage enhancements (a
government contract, distinct from the equity total). Payload: 250 kg to LEO / 150 kg to SSO.
Space One does not officially disclose pricing; a reported/estimated figure is $9M per launch,
with a company executive describing it only as "competitive" against Rocket Lab's ~$7M
Electron price
([NASASpaceFlight.com](https://www.nasaspaceflight.com/2024/03/space-one-kairos/)). All 3
launch attempts to date have failed (March 2024, exploded seconds after liftoff; Dec 2024;
and a third 2025 attempt) — Kairos has not yet reached orbit.

## Zhuque-2 (LandSpace, China)

A Series C+ round raised $175M for Zhuque-2-series development specifically, led by Sequoia
Capital China, Country Garden Venture Capital, Matrix Partners China, and Cornerstone Capital
([SpaceNews](https://spacenews.com/chinas-landspace-raises-175-million-for-zhuque-2-launch-vehicles/)).
Payload: 6,000 kg to 200km LEO / 4,000 kg to SSO. No commercial price was found — a genuine
gap typical of Chinese commercial space pricing transparency. World's first liquid-methane
rocket to reach orbit (2nd attempt, July 2023, after a Dec 2022 failure); ~10 flights through
mid-2026 (approximate tally). Active.

## Zhuque-3 (LandSpace, China)

RMB900M (~$123M) from China's state-backed National Manufacturing Transformation and
Upgrading Fund, earmarked for the Zhuque reusable methalox vehicles
([SpaceNews](https://spacenews.com/chinas-landspace-secures-state-backed-funding-for-reusable-rockets/)) —
in addition to (not summed with, since the split isn't disclosed) the earlier $175M Zhuque-2
round. Payload: 18,300 kg to LEO with downrange first-stage recovery / 21,000 kg expendable /
12,500 kg with return-to-launch-site recovery. Launch cost reported at $21M per flight, per a
July 2026 Pandaily analysis of LandSpace's IPO filing on China's STAR Market — the same
filing disclosed the company loses ~$240M/year, a rare window into a Chinese commercial
launch company's real financials
([Pandaily](https://pandaily.com/landspace-ipo-zhuque-3-rocket-reusable-analysis-jul2026)).
Maiden flight Dec 3, 2025, reached orbit but the first-stage recovery attempt was
unsuccessful. Comparable in ambition to Falcon 9 (stainless-steel, partially reusable,
methalox, two-stage medium-to-heavy).

## Ceres-1 (Galactic Energy, China)

No funding/development-cost figure was found — a genuine gap. Payload: 400 kg to LEO / 300
kg to 500km SSO. Current flat price: $4.38M
([nextspaceflight.com](https://nextspaceflight.com/rockets/225/)); company has separately
stated a longer-term target of under $10,000/kg. Solid-fuel small launcher with a real,
established multi-year flight record (first flight Nov 2020) rather than a pre-flight
prediction — one of the most active and reliable Chinese commercial launchers; ~20 flights
through mid-2026 (approximate tally). Active.

## Hyperbola-1 (i-Space / Beijing Interstellar Glory, China)

No vehicle-specific development-cost figure was found; the company separately raised a $99M
Series C at an unspecified date for its broader launch-vehicle program (not isolated to
Hyperbola-1) — not used here as a vehicle-specific figure
([Payload Space](https://payloadspace.com/chinese-launch-startup-ispace-raises-99m-series-c/)).
Payload: 300 kg to LEO (solid-fuel, four stages). Price: ~$5M
([Wikipedia: Hyperbola-1](https://en.wikipedia.org/wiki/Hyperbola-1)). China's first
privately-developed rocket to reach orbit (July 25, 2019); mixed reliability record since;
~10 flights through mid-2026 (approximate tally). i-Space is separately developing the
larger, partially-reusable Hyperbola-3 (methalox, Falcon-9-class) — not included as a
distinct row given limited public cost data specific to it as of this research.

## Tianlong-3 (Space Pioneer, China)

Two disclosed funding rounds specifically tied to Tianlong-3 development: ~$414M cumulative
through a July 2023 C-round, plus a further RMB2.5B (~$351M) pre-D/D round in Oct 2025 —
reported as two separate raises rather than one verified cumulative total, so the ~$765M sum
used in the CSV should be treated as approximate
([SpaceNews](https://spacenews.com/space-pioneer-raises-350-million-as-chinas-commercial-launch-boom-accelerates/)).
Payload: 17,000 kg to LEO / 14,000 kg to 500km SSO — explicitly positioned by the company and
press as China's closest Falcon-9 analog (two-stage kerolox, reusable first stage). No price
disclosed. A first-stage vehicle was destroyed in an accidental ignition/crash during a June
2024 ground static-fire test, prior to any real flight attempt. The company's earlier,
smaller Tianlong-2 flew successfully in 2023 (not included as a separate row). Had not
achieved a successful orbital flight as of this research.

---

# Mature, flight-proven vehicles (added in a third research pass)

This section was added after feedback that the new-space-startup section above skewed the
dataset toward unprovable pre-flight predictions, muddling the real trend the underlying
(mostly historical/established) data shows. These 14 vehicles were specifically chosen for
having decades of REAL flight and pricing history — several are the strongest data points in
the entire dataset (actual SEC filings, actual ESA/USAF contract disclosures, actual 1990s
trade-dispute pricing records), not proxies or predictions.

## Ariane 5 (ESA/ArianeGroup, France — retired)

Development cost: ~$7B (nominal, 1987 program approval through 1996 first flight) is the
widely-repeated secondary-source consensus figure
([Design News](https://www.designnews.com/aerospace/ariane-5-europe-s-heavy-lifter)); not a
single official ESA line-item total, but corroborated indirectly by [ESA Bulletin
93](https://www.esa.int/esapub/bulletin/bullet93/b93carr.htm) (ground facilities alone were
~1B ECU = 20% of total development cost, implying ~5B ECU total in period currency). REAL
commercial pricing across the vehicle's life, all sourced to [Wikipedia: Ariane
5](https://en.wikipedia.org/wiki/Ariane_5) (itself citing contemporary reporting): ~€90M
(2013, heavy satellite/upper position), ~€50M (2014, midsize/lower position), ~€150M total
dual-launch (Jan 2015, used in the CSV), ~€150–200M (2016), rising toward ~€200M in the
vehicle's final years. Payload: 21,000 kg LEO (ES variant, real ATV cargo missions) / 10,865–
11,115 kg GTO (ECA variant, the actual commercial-market configuration — nearly all pricing
applies here, not to the LEO figure). 117 launches, 112 full successes (95.7%), retired July
2023 after an 82-mission consecutive-success streak (2003–2017).

## Ariane 6 (ESA/ArianeGroup, France — active)

Development cost: ~€4B (~$4.3–4.5B) as of the July 2024 first flight, risen in stages from an
initial €2.4B 2014 industrial contract ([Al Jazeera](https://www.aljazeera.com/news/2024/7/9/europes-ariane-6-ready-to-blast-off-from-spaceport-in-kourou);
[Wikipedia: Ariane 6](https://en.wikipedia.org/wiki/Ariane_6)). **REAL, itemized institutional
contract:** ESA disclosed it paid €82,070,773 (~$96M) to Arianespace to launch the Sentinel-1D
satellite on an Ariane 62 in Nov 2025 — ESA is unusual among launch customers in publishing
itemized launch-service procurement values
([European Spaceflight](https://europeanspaceflight.com/esa-spent-e82-million-to-launch-sentinel-1d-satellite-on-ariane-6/),
corroborated by [Behind The Black](https://behindtheblack.com/behind-the-black/points-of-information/esa-paid-arianespace-about-96-million-for-an-ariane-6-launch/),
which notes SpaceX charged ESA ~$90M for a comparable Sentinel launch). The Amazon Kuiper deal
(18 launches) was never officially priced; Quilty Space's ESTIMATE of $2.5–3B total (~$139–
167M/launch) is explicitly not used as the primary figure. ESA member states additionally
subsidize ArianeGroup operations directly at up to €340M/year (through ~2031) to bridge real
cost and competitive pricing. Payload: 21,650 kg LEO / 11,500 kg GTO (A64). 8 flights, 7
successes, 1 partial failure (upper-stage deorbit-burn anomaly, July 2024).

## Vega (ESA/Avio, Italy — retired)

Development cost: €710M (~$910M), per [SpaceNews via Wikipedia: Vega
(rocket)](https://en.wikipedia.org/wiki/Vega_(rocket)); a separate €400M ESA VERTA
contribution sponsored 5 post-qualification proving flights (2012–2014) and is excluded
(subsidized early ops, not pure R&D). Price: $37M official infobox figure (a real reported
average market price, not one named contract); more granular 2012 SpaceNews reporting gave
~€32M including Arianespace markup, ~€25M for the rocket alone at 2 flights/year. Payload:
~1,450 kg to 400km SSO. 22 launches, 20 successes, 2 failures (2019, 2020); retired Sept 2024.

## Vega-C (ESA/Avio, Italy — active)

Development cost: €395M (~$430M) ESA/ELV contract (2015); program officials separately
reported actual spend of only ~$300M, under the original budget — both figures reported
([Via Satellite](https://www.satellitetoday.com/finance/2015/08/12/esa-signs-contracts-for-ariane-6-vega-c-launchers/)).
**REAL, itemized institutional contract:** ESA's Sentinel-1C launch contract was €48.62M
(awarded Apr 2022), rising to a final €51.65M (~$54M) for the Dec 2024 return-to-flight
mission — the actual satellite (~2,284 kg) was close to full rated capacity, making this an
unusually clean real $/kg data point
([European Spaceflight](https://europeanspaceflight.com/esa-paid-e51-65-million-to-launch-sentinel-1c-on-vega-c-return-to-flight/)).
Payload: 2,300 kg to 700km SSO. 7 flights, 6 successes, 1 failure (Dec 2022, Zefiro-40 nozzle
erosion, grounded the vehicle for 2 years).

## Vulcan Centaur (United Launch Alliance, USA — active, paused)

No total program cost has ever been disclosed by ULA/Boeing/Lockheed — a genuine gap despite
searching (left blank rather than assembling Bruno's various public order-of-magnitude quotes
into a fabricated precise total). **REAL, disclosed figure used for cost-to-first-launch:** a
$967M USAF Other Transaction Agreement (Launch Service Agreement), Oct 2018
([official DoD contract announcement](https://www.war.gov/News/Contracts/Contract/Article/1658771/)) —
government cost-share only; Bruno stated Vulcan was "75% privately funded" as of March 2018,
implying the true total was materially higher. **REAL, disclosed opex:** derived from a $337M
FY2022 NSSL Phase 2 task order for 2 missions (Aug 2020 award,
[Spaceflight Now](https://spaceflightnow.com/2020/08/07/ula-spacex-win-landmark-launch-agreements-with-pentagon/)) —
a blended Atlas V/Vulcan-era task order, not a confirmed single-mission Vulcan-only price, but
a real government contract figure nonetheless. NSSL Phase 3 Lane 2 (Apr 2025) separately gave
ULA a ~$5.3B ceiling for 19 missions (~$279M/mission average, but a ceiling, not a firm price).
Payload: 27,200 kg to LEO (VC6). 4 flights since Jan 2024; paused for NSSL missions since a
Feb 2026 SRB nozzle anomaly on USSF-87 (the second such SRB issue after Cert-2 in Oct 2024).

## Electron (Rocket Lab, USA — active)

**The strongest real-data point in the new-space cohort.** Development cost: Peter Beck's
on-the-record 2020 statement, "it took us $100m to get to orbit" (Payload Research compiles
this as $100M nominal/$123M inflation-adjusted — the same source already used elsewhere in
this dataset). **REAL, SEC-filed marginal cost:** Rocket Lab's Form 10-Q for Q1 2025 breaks
out the Launch Services segment as $35.592M revenue / $28.375M cost of revenue across 5
confirmed Electron missions that quarter — average marginal cost of $5.68M/launch, an actual
disclosed operating-cost figure, not an estimate
([SEC EDGAR](https://www.sec.gov/Archives/edgar/data/0001819994/000162828025023857/rklb-20250331.htm)).
Price: $8.5M current backlog ASP (Q1 2026 earnings call), up from $5–6M at 2018 market entry
and $7.5M for years prior to 2023. Payload: 300 kg to LEO. 91 orbital launches (87 success/4
failure, ~95.6%) as of late June 2026 — the most-flown new-space small launcher in history;
publicly traded (NASDAQ: RKLB).

## Long March 3B (CASC, China — active)

**The best-documented historical commercial-pricing case in this entire dataset.** No
official development-cost figure exists (genuine gap after searching Cox Report chapters, CRS
reports, Chinese state media). But real 1990s prices, tied to actual US-China trade disputes,
are well documented: $25M offered for Arabsat (1990, triggered Arianespace/US government
pushback over "dumping," per [CRS Report
98-575](https://www.everycrsreport.com/reports/98-575.html)); ~$30M for AsiaSat 1 (1990,
China's first commercial launch for a foreign customer); $56M for Intelsat 708 (1992 contract;
the Feb 1996 launch failure destroyed the satellite and killed people on the ground at
Xichang). A 1995 US-China bilateral agreement required Chinese prices to stay within 15% of
Western prices or trigger a US pricing review; in 1997 USTR found China had violated this on
the Agila-2/Loral launch. CGWIC's standing commercial rate was reaffirmed at **$70M in 2012–
2013**, explicitly backed by a "96% success record over 181 flights"
([SpaceNews](https://spacenews.com/37366china-great-wall-reaffirms-commitment-to-70-million-long-march-launches/)) —
a genuine disclosed rate card, used in the CSV — and reportedly cut to $50M by 2019 amid
SpaceX competition. Payload: 5,100–5,500 kg GTO (real commercial market) / 11,500 kg LEO
(rarely flown). ~116 flights, ~96.5% success.

## Long March 5 (CASC, China — active)

No development-cost figure disclosed (only adjacent, non-equivalent launch-site/manufacturing
capex exists — not used). Unlike 3B/2D, CZ-5 has **no confirmed real commercial contract
price** — it's overwhelmingly a state-mission vehicle (space station, lunar sample return,
Mars). The ~$160M figure used is a secondary analyst estimate ([Wikipedia: Long March
5](https://en.wikipedia.org/wiki/Long_March_5)), explicitly flagged as NOT a real contract
price, unlike the other Long March entries. Payload: 25,000 kg LEO (CZ-5B variant). 18
flights, 17 successes (94.4%), including a 2017 failure that caused a 28-month hiatus.

## Long March 2D (CASC, China — active)

No development-cost figure disclosed. **REAL, disclosed modern commercial price:** repeat
customer Changguang Satellite Technology (Jilin-1 constellation) procured CZ-2D launches at
112.9–113 million yuan (~$15.7–16M) per mission for 2022-era contracts
([china-in-space.com](https://www.china-in-space.com/p/what-is-the-cost-of-a-long-march)) — a
genuine repeat-customer procurement price, distinct from a higher $30M nominal dedicated-
mission price also cited. Payload: 3,500 kg LEO. China's most-flown active workhorse (100th
mission passed 2025), ~99% success over 105 flights.

## Kuaizhou-1A (CASIC/ExPace, China — active)

No development-cost figure disclosed. **REAL, operator-disclosed pricing:** ExPace publicly
advertised $10,000–$20,000/kg (goal of $5,000/kg) starting ~2016
([Space.com](https://www.space.com/34840-chinese-expace-commercial-launch-company.html));
individual missions commonly listed at $5.8M per complete launch service
([RocketLaunch.org](https://rocketlaunch.org/launch-providers/expace/kuaizhou-1a)). Payload:
~300 kg LEO (varies by source/orbit, 200–400 kg range). 16 dedicated KZ-1A flights through Dec
2024 (14 successes, 2 failures, ~87.5%); an upgraded KZ-1A-Pro variant added further flights
through 2025 (4 Kuaizhou-series missions that year, 3 successes).

## Angara A5 (Roscosmos/Khrunichev, Russia — operational)

Development cost: $5.33B cumulative through 2012, per then-Roscosmos chief Vladimir
Popovkin's public estimate — the textbook case of Russian launcher cost/schedule overruns
(development began 1995, targeted 2005, didn't fly until Dec 2014)
([Pravda](https://english.pravda.ru/news/science/145395-angara/)). Opex: Salyut Design Bureau
chief designer Sergey Kuznetsov stated in 2021 costs run "between $50 million and $100
million," closer to the upper bound during low-rate production
([TASS](https://tass.com/defense/1239497)) — a real government/designer cost disclosure, NOT
a market-tested price (Angara has no Western commercial customers). Unit production cost
separately reported at 7 billion rubles (2019) vs. Proton-M's ~2.3B rubles. Payload: 24,500 kg
LEO. 5 flights through June 2025, 4 successes, 1 partial failure (Dec 2021).

## Zenit-3SL / Sea Launch (international consortium: Boeing/USA, Energia/Russia,
Yuzhnoye-Yuzhmash/Ukraine, Aker/Norway — indefinitely suspended)

**One of the strongest real-market-pricing cases in the entire dataset for a Russian/
Ukrainian-heritage vehicle.** Total consortium investment: ~$950M (platform + program through
the 1999 debut, [RussianSpaceWeb](https://www.russianspaceweb.com/sealaunch.html)), up from an
initial $583M 1996 budget. **REAL, arm's-length commercial contract:** Hughes Space and
Communications' Dec 1995 deal for 10 firm launches at $1 billion total ($100M/launch) — the
deal that made Sea Launch "a real business" per its general manager at the time
([Spokesman-Review, Dec 19 1995](https://www.spokesman.com/stories/1995/dec/19/boeing-launch-platform-gets-first-customer-hughes/)).
Prices later rose toward $110–120M/launch by the early 2010s. Payload: 6,000–6,160 kg GTO
(real operational missions); 7,000 kg LEO is a nominal, never-operationally-used figure.
36 launches 1999–2014 (32 successes, 3 failures, 1 partial). Filed Chapter 11 bankruptcy 2009
(~$2B in creditor claims); S7 Group (Russian airline) bought the assets in 2016, relocated to
Vladivostok; dormant since Russia's 2022 invasion of Ukraine severed the Russia-Ukraine
cooperation the Ukrainian-built Zenit depends on.

## Epsilon (JAXA/IHI Aerospace, Japan — active, transitioning)

Development cost: ~$325M combined (Phase 1 ~$200M through the 2013 debut + Phase 2 ~$100–150M
through the 2016 upgrade), per JAXA figures reported by
[SpaceNews](https://spacenews.com/japan-take-incremental-approach-new-epsilon-launcher/).
Opex: first (2013) launch cost ~3.8 billion yen (~$38–44.5M), explicitly targeted at roughly
half the ~$70M cost of the retired M-V solid rocket it replaced — a real JAXA institutional
cost figure, not a commercial market price (Epsilon primarily launches Japanese government/
JAXA science payloads). Payload: 1,200 kg to a 250×500km orbit. 6 flights: successes in 2013,
2016, 2018, 2019, 2021; failure Oct 2022 (attitude-control fault).

## SSLV (ISRO, India — development complete, transitioning to HAL/NSIL)

Development cost: ₹169.07 crore (~$20.4M) total sanctioned cost covering development,
qualification, and all 3 developmental flights, per a genuine primary source — Indian
Parliament (Rajya Sabha) written reply, Minister of State Dr. Jitendra Singh, 16 Dec 2021
([devdiscourse](https://www.devdiscourse.com/article/technology/1849929-sslv-to-provide-payload-capability-of-500-kg-to-a-500-km-planar-orbit-dr-jitendra-singh)).
Opex: ₹30–35 crore (~$3.6–4.2M) government/NSIL manufacturing-cost target — not yet a fully
disclosed real commercial contract, though NSIL has signed BlackSky Global as a commercial
customer (contract price undisclosed; market reporting cites $5–7M/launch as the 2025
commercial rate). Payload: 500 kg to a 500km planar orbit. 3 flights: SSLV-D1 (Aug 2022)
failed (software fault), SSLV-D2 and D3 both succeeded. In Sept 2025, HAL signed a ₹511 crore
(~$59M) tech-transfer deal to become SSLV's commercial manufacturer/operator.

---

## General methodology notes

- **Research conducted:** July 2026, via live web search across NASA, GAO/CBO, NASA OIG,
  RAND, company SEC filings/press releases/investor materials, Indian parliamentary (Lok
  Sabha) replies, and trade press (SpaceNews, Ars Technica, Payload Research, The Planetary
  Society, Spaceflight Now, TASS, FlightGlobal). Wikipedia was used as a starting point in
  many cases but the underlying primary source was traced and cited wherever possible.
- **Total program cost vs. cost through first launch** are genuinely different quantities
  (see `plot_launch_economics.py`'s docstring and `README.md`) and are kept in separate CSV
  columns / separate charts rather than blended.
- **Marginal cost vs. fully-loaded average cost vs. commercial/contract price** are three
  different economic concepts, also kept distinct in the CSV (`opex_marginal_usd`,
  `opex_fully_loaded_usd`, `opex_price_usd`) and encoded by marker shape in the charts.
- Figures marked **ESTIMATE** or **predicted/projected** throughout (Neutron pre-flight,
  Starship, some New Glenn and Payload Research figures) are explicitly flagged as such in
  both this file and the CSV `notes` column — they are not flight-proven, audited costs.
  Treat them with more skepticism than the GAO/NASA OIG/Lok Sabha figures.
