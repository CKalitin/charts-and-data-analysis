# Reflect Orbital Model — Sources

Claude does all my number scraping reserach for me, I'm not a shmuck.

---

## Launch Cost

**F9 dedicated list price: $74M, payload 22,800 kg → $3,246/kg**
What Reflect actually pays is the rideshare rate, not this. Useful as an upper bound and for deriving internal cost.
https://en.wikipedia.org/wiki/Falcon_9

**F9 rideshare (Transporter SSO): $6,000/kg**
This is what Reflect Orbital actually pays today. Confirmed by Monocle interview with Nowack quoting ~$6,500/kg.
https://en.wikipedia.org/wiki/Falcon_9
https://monocle.com/business/aviation/reflect-orbital-aerospace-startup/

**F9 internal marginal cost: ~$15M/launch → ~$857/kg**
SpaceX's actual cost, not what they charge. Sets floor on how cheap F9 could ever get for Reflect.
https://en.wikipedia.org/wiki/Falcon_9

**Starship aspirational: $10M/launch, 150,000 kg → $67/kg**
SpaceX stated target at high cadence. Not achieved. The number that makes Reflect's economics work.
https://spacenexus.us/blog/economics-satellite-launch-cost-per-kilogram

**Starship conservative near-term: ~$30M/launch → ~$200/kg**
More realistic early operational estimate from analysts.
https://spacenexus.us/blog/economics-satellite-launch-cost-per-kilogram

---

## Starlink Satellite Mass & Cost (benchmark for Reflect sat manufacturing cost)

**v1.0: 260 kg, $200k/unit → $769/kg**
First operational generation. Cost from Quilty Space analyst estimate via SpaceNews.
- Mass: https://space.skyrocket.de/doc_sdat/starlink-v1-0.htm
- Cost: https://spacenews.com/starlink-soars-spacexs-satellite-internet-surprises-analysts-with-6-6-billion-revenue-projection/

**v1.5: ~305 kg, ~$250k/unit (estimated) → ~$820/kg**
Added laser inter-satellite links. 305 kg figure from Teslarati citing FCC filing context. Cost interpolated — no primary source gives it directly.
- Mass: https://www.teslarati.com/spacex-unveils-next-gen-starlink-v2-mini-satellites-ahead-of-monday-launch/
- Mass (Wikipedia): https://en.wikipedia.org/wiki/Starlink ("Bus F9-1, 303 kg")
- Cost: interpolated from v1.0 and v2 Mini Quilty Space data

**v2 Mini: 800 kg, $800k/unit → $1,000/kg**
Current generation, launched on F9. Cost from Quilty Space via SpaceNews.
- Mass: https://en.wikipedia.org/wiki/Starlink
- Cost: https://spacenews.com/starlink-soars-spacexs-satellite-internet-surprises-analysts-with-6-6-billion-revenue-projection/

**v2 full (Starship-only): ~1,250 kg, ~$1M/unit (estimated) → ~$800/kg**
Too large for F9, not yet launched commercially. Mass from Musk statement. Cost estimated by scaling from v2 Mini — no primary source.
- Mass: https://www.teslarati.com/spacex-elon-musk-next-gen-starlink-satellite-details/
- Cost: estimate only

**v3 (projected): 1,500 kg, $1.2M/unit → $800/kg**
Future generation. Both figures from Quilty Space via SpaceNews.
https://spacenews.com/starlink-soars-spacexs-satellite-internet-surprises-analysts-with-6-6-billion-revenue-projection/

---

## Reflect Orbital Satellite Specs

**Eärendil-1 mirror mass: 16 kg**
Mirror only, not total satellite. Mylar film on deployable booms.
- https://en.wikipedia.org/wiki/Reflect_Orbital
- https://www.space.com/orbiting-mirror-boost-solar-power-production

**Eärendil-1 total satellite mass: 100 kg**
Full satellite including bus, propulsion, avionics. From Monocle interview with Nowack ("100kg satellite packed into a box the size of a microwave"). Bus mass implied: ~84 kg.
- https://monocle.com/business/aviation/reflect-orbital-aerospace-startup/
- https://orbitaltoday.com/2025/07/31/startup-plans-to-beam-sunlight-to-earth-using-space-mirrors/

**Eärendil-1 mirror area: 324 m² (18m × 18m)**
Derived. Sets current m²/kg = 324/16 = 20.3 m²/kg for mirror film alone; 324/100 = 3.24 m²/kg for whole satellite.
- https://en.wikipedia.org/wiki/Reflect_Orbital

**Future constellation mirror size: 54m × 55m (~2,916–3,025 m²)**
Stated goal for production satellites. ~9× more mirror area than Eärendil.
- https://payloadspace.com/reflect-orbital-raises-20m-series-a/
- https://www.livescience.com/space/space-exploration/controversial-startups-plan-to-sell-sunlight-using-giant-mirrors-in-space-would-be-catastrophic-and-horrifying-astronomers-warn

**Future constellation satellite total mass: NO PUBLIC DATA**
Not stated anywhere. Derivable estimate: mirror film scales to ~144 kg (9× Eärendil film), bus probably 200–400 kg given larger attitude control demands → total ~300–500 kg. Treat as unknown.

---

## Reflect Orbital Mission Parameters

**Orbit: SSO, 600–650 km altitude**
Sets ground track geometry and pass duration for your model.
https://en.wikipedia.org/wiki/Reflect_Orbital

**Beam diameter on ground: 5 km**
Set by sun's angular diameter (0.53°) projected from altitude. Not a design choice, a physics constraint.
https://en.wikipedia.org/wiki/Reflect_Orbital

**Target irradiance: 200 W/m²**
Reflect's stated goal for the full constellation. ~20% of midday sun, enough for meaningful solar generation.
https://monocle.com/business/aviation/reflect-orbital-aerospace-startup/

**Pricing: ~$5,000/hour per satellite**
Nowack's stated figure for lighting customers. Solar farm revenue-share model also discussed but no public rate.
https://futurism.com/space/fcc-huge-mirror-satellite

---

## Notes on Data Quality

- All Starlink cost figures are **analyst estimates** (Quilty Space), not SpaceX disclosures. Treat as ±30%.
- Starlink mass figures are **well-sourced** (FCC filings, NSF launch reports, Wikipedia citing primary sources).
- Reflect total satellite mass (100 kg) comes from **one interview** — treat as approximate.
- Future constellation satellite mass has **no source** and must be modeled or assumed.
- F9 rideshare pricing is **publicly listed** and reliable.
- Starship cost figures are **targets**, not achieved prices.
