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

## Original Atlas (SM-65 / Atlas D, Mercury-Atlas era)

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
