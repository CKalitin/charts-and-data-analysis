# Starlink orbital shells — sources & methodology

Companion to [`starlink_shells.csv`](starlink_shells.csv). Follows the citation
convention from `Reflect-Orbital/sso-land-proximity/data/reflect_orbital_sources.md`
and `telecom_market_by_country.md`: every figure is cited with a confidence note.

Researched 2026-08-09 via web search — no bulk machine-readable source exists for
this (unlike the Phase 1 telecom data), so this is a hand-compiled table from
several converging public sources, not a single authoritative download.

---

## Rows with FULL geometry (altitude, inclination, planes, sats/plane) — well-sourced

**`gen1_shell1` through `gen1_shell4b`** — the original "Phase 1" / Gen1 constellation
as modified by the FCC's 2021 authorization order (lowering the original 1,100-1,300
km "upper shell" to 540-570 km). This is the most consistently-cited Starlink shell
table across independent sources (Wikipedia historically, eoPortal, and an academic
paper modeling Starlink's constellation parameters) and the numbers agree across all
of them:

| Shell | Altitude | Inclination | Planes x sats/plane | Total |
|---|---|---|---|---|
| 1 | 550 km | 53.0° | 72 x 22 | 1,584 |
| 2 | 540 km | 53.2° | 72 x 22 | 1,584 |
| 3 | 570 km | 70.0° | 36 x 20 | 720 |
| 4a | 560 km | 97.6° | 6 x 58 | 348 |
| 4b | 560 km | 97.6° | 4 x 43 | 172 |

**Total: 4,408 satellites** — matches the widely-cited "4,408" Phase 1 authorization
figure exactly (1584+1584+720+348+172 = 4408), which is a strong internal consistency
check that these five rows are correct together, even though no single source in this
search session returned the full table in one place. Shell 4 splits into two
sub-groups (4a/4b) at the same altitude/inclination but different plane counts — both
serve the 97.6° near-polar coverage band, just at different orbital-plane
granularity.

**Confidence: well-sourced**, cross-checked against 3+ independent sources, exact
total matches the public "4,408" figure. Search queries and sources (accessed via web
search, 2026-08-09): FCC modification orders (docs.fcc.gov, various FCC-XX-XX
dockets), eoPortal Starlink satellite mission page
(https://www.eoportal.org/satellite-missions/starlink), and cross-referenced against
a general web search aggregating Wikipedia/FCC-derived shell tables. **Caveat: I did
not open and read the primary FCC PDF filings directly in this session** — these
figures are as reported by secondary sources describing those filings, which is a
step short of full primary-source verification. If exact regulatory precision is ever
needed (not needed for this model's purpose), pull the FCC docket directly, e.g.
`docs.fcc.gov/public/attachments/FCC-22-91A1.pdf` and related orders.

---

## Rows with altitude + inclination only — no plane/sat-per-plane data found

**`gen2_shellA/B/C`** — Gen2 ("v2 Mini") shells as FCC-authorized: 525/530/535 km at
53/43/33 degrees respectively (7,500-satellite partial Gen2 authorization, 2022).
**Confidence: altitude/inclination well-sourced (FCC authorization, reported via
DataCenterDynamics and SpaceNews coverage of the FCC order); plane/satellite-per-plane
breakdown NOT FOUND in this research session** — left blank in the CSV, not
estimated. `gen2_shellC` (33°) is flagged `fcc_authorized_unconfirmed_deployed`
because this research did not confirm satellites are actually flying in that specific
sub-shell as opposed to just being authorized.

**`lowered_2026_a/b/c/d`** — the CURRENT (as of 2026) relocation SpaceX is actively
executing: lowering existing Gen1+Gen2 broadband satellites to 463-485 km across the
53°/43°/70°/97.3° inclinations. **Confidence: high for altitude/inclination** — this
came directly from SpaceX's own official space-safety documentation
(https://space-safety.starlink.com/docs/space-safety-articles/constellation_altitudes/),
which states this is happening "by end of 2026" for improved deorbit safety (">80%
reduction in ballistic decay time"). **Plane/satellite counts not given by the source
at all** — this describes a relocation of existing satellites, not a new
authorization, so per-shell counts are a moving target during 2026 and not usefully
tabulated as a static number right now.

**`dtc_2026_a/b`** — Direct-to-Cell shells at 360/358.5 km, 53°/43°. Same source as
above (SpaceX official). These are physically smaller/lower and serve phone-direct
connectivity, not the fixed/mobile broadband terminals this model is about — included
for completeness but likely **out of scope for the equilibrium model** (different
customer/revenue model entirely). Flag this explicitly for Phase 3/5: don't include
DTC shells in the broadband capacity/coverage math without a deliberate decision.

**`v3_broadband`** — next-generation Starship-launched satellites, 330-360 km
(midpoint 345 km used as placeholder), **inclination not stated by any source found —
left blank/TBD, do not assume a value**. Confidence: low, this is a forward-looking
placeholder for a shell that doesn't fully exist operationally yet.

---

## Constellation-wide total (context, not a per-shell figure)

**~10,900 Starlink satellites in orbit as of 2026-08-06** (10,920 launched, 10,904
working, per one tracking aggregator's report citing multiple independent tracking
sources converging on the same order of magnitude: 10,764-10,920). This is
meaningfully larger than the 4,408 Gen1 authorization total above — the gap is Gen2
("v2 Mini") satellites launched under the 7,500-satellite partial Gen2 authorization
plus continued Gen1 replenishment. **Confidence: satellite-tracker consensus, not a
single authoritative figure** — different trackers (KeepTrack, orbitalnodes,
HighSpeedInternet.com aggregating from Jonathan McDowell-style catalogs) report
numbers within ~1.5% of each other, treat ~10,900 as accurate to within a few hundred.

---

## What this means for the Phase 2 coverage model

The model uses the **Gen1 5-sub-shell table** (full geometry, well-sourced) as the
primary input for computing latitude coverage bands and per-shell satellite density —
it's the only rows with complete plane x sat/plane data needed for a density
calculation. The lowered-2026 and Gen2 rows are kept in the CSV for context and
future refinement but are NOT geometrically complete enough to feed the coverage-band
calculation yet. **This likely underestimates real current coverage/capacity**, since
it excludes ~6,500 Gen2 satellites that don't have public plane-count data — flag this
gap explicitly in any output, don't silently present Gen1-only results as "current
Starlink."

Do not conflate inclination changes over time: the classic 5-shell table's
inclinations (53.0°, 53.2°, 70.0°, 97.6°) are NOT identical to the 2026-relocation
altitudes' inclinations (53°, 43°, 70°, 97.3°) — very close but not the same
authorization, and the 43° shell in particular is new relative to the original Gen1
design (which had no 43° shell in this table). This matches the user's own dictated
note about "polar orbits... roughly forty-five degrees... sixty degree planes" being
an approximation of a real 43°/53°/70°/97.6° structure — the dictation was in the
right neighborhood but not exact, consistent with Phase 2's task to replace it with
real numbers.
