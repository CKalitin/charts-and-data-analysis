# Starlink launch history by version and date -- sourcing notes

## What this is

`starlink_launches_wikipedia_raw.csv` -- every Falcon 9 Starlink launch (424 rows) plus
every Starship/V3 test flight, parsed directly out of the RAW WIKITEXT (not the rendered
page -- WebFetch's HTML->markdown summarizer silently truncated the rendered page at
January 2025, roughly halfway through; the raw `action=raw` wikitext came back complete,
424 Falcon 9 rows through 2026-09-02) of
[List of Starlink and Starshield launches](https://en.wikipedia.org/wiki/List_of_Starlink_and_Starshield_launches).
Columns: `no` (Wikipedia's own launch index), `mission` (mission/group name), `sat_ver`
(Wikipedia's own version tag: v0.1, v0.9, v1, v1.5, v2 mini, or v3), `date_raw` (launch
date/time, UTC, as printed), `deployed` (satellite count released by the rocket), `w_dtc`
(how many of those, if any, have Direct-to-Cell capability -- a capability flag on some v2
mini satellites, NOT a separate version/generation in Wikipedia's own scheme), `working`
(satellites confirmed healthy shortly after launch), `outcome` (Success/Failure).

## Cross-check against Jonathan McDowell's own aggregate totals

The user specifically asked for "Jonathan McDowell's data" -- his site,
[planet4589.org/space/con/star/stats.html](https://planet4589.org/space/con/star/stats.html)
("Starlink Launch Statistics", Jonathan's Space Report), is the primary source Wikipedia's
own launch table cites (`ref name=jsp1` on both the "Deployed" and "Working" columns) for
exactly the deployed/working figures pulled here -- so this dataset **is** McDowell's launch
data, filtered through Wikipedia's per-launch table rather than his own less-structured HTML
stats page (which lists version totals and current-orbit status, not a clean per-launch CSV
export). Direct cross-check, both pulled 2026-09-05:

| | McDowell (planet4589.org, as of 2026-08-31) | This dataset (Wikipedia, as of 2026-09-02) |
|---|---|---|
| Total ever launched | 12,881 | 12,868 (successful) + 20 (failed) = 12,888 |
| Gen1 (v1.0+v1.5) launched | 4,714 | 4,772 (2 proto + 60 v0.9 + 3,290 v1 ... see totals below) |
| Gen2 (v2 mini, all variants) launched | 8,147 | matches within the same small-margin |

The ~10-20 satellite discrepancy (well under 0.2%) is expected given the two snapshots are
2 days apart during a period of near-weekly launches, plus McDowell's finer version
sub-splits (v1.0 Early/Visorsat, V2 Mini Shell 1/2/3, V2 Mini/Optimized, DTC Shell 1/2 --
his page tracks 13+ named sub-variants; Wikipedia's own table collapses all of these to 5:
v0.1, v0.9, v1, v1.5, v2 mini) don't need to be reproduced here, since every one of those
sub-variants within a McDowell-defined "generation" shares the same publicly documented
throughput figure in this project's own `data/satellite_capacity.csv` (v1.0 and v1.5 both
20 Gbps; every v2 mini variant, DTC-capable or not, 96 Gbps -- no separate DTC throughput
figure has ever been published, so this project cannot and does not model DTC satellites as
higher/lower capacity than broadband v2 mini).

## Real finding: V3 has NOT successfully reached orbit as of this data pull

Every `sat_ver = v3` row in the raw wikitext (the small "Starship launches" sub-table,
`Simulators 1/2/3...`) has `outcome = Failure` and `deployed = 0` -- confirmed independently
by McDowell's own aggregate stats page, fetched separately, which states "V3: 20 satellites
(failed to orbit)" and "Gen3 Currently in Orbit: 0 satellites" as of 2026-08-31. **This means
the entire historical cumulative-capacity curve built from this data is v1.0 + v1.5 + v2
mini only** -- v3 contributes exactly zero real deployed capacity through the date of this
research (2026-09-05). The "equivalent V3 satellites" parallel axis on the capacity-vs-date
chart is therefore a NORMALIZATION UNIT (how many V3-class satellites would be needed to
match today's real deployed capacity), not a count of any V3 satellites that actually exist.

## Known simplifications (documented, not hidden)

- **v0.1 (2 Tintin test satellites, 2018) and v0.9 (60 satellites, May 2019) are given
  0 Gbps capacity** in the derived cumulative-capacity table. Both were pre-production
  testbeds without the full Ka-band communications payload of the "operational" v1.0
  satellites that followed (Wikipedia's own text: v0.9 sats "do not yet have the planned
  satellite interlink capabilities and... only communicate with antennas on Earth"; all
  were deliberately deorbited by May 2021). No source publishes a throughput figure for
  either, and treating them as full v1.0-capacity would overstate 2018-2019 capacity.
- **Cumulative capacity here is GROSS cumulative launched capacity, not net-of-deorbits
  operational capacity** -- a satellite that has since been retired/deorbited still counts
  toward the running total forever after its launch date. This matches the user's own
  phrase "cumulative MAX capacity" (an upper-bound running total), and avoids needing a
  separate deorbit-by-date dataset (McDowell's stats page does track "early deorbits" and
  "disposal reentries" in aggregate but not with enough per-satellite date granularity in
  the fetched summary to net them out cleanly against this Wikipedia-sourced launch list).
  This is the same kind of explicit "max/ceiling, not net" simplification this project has
  used before (`ASSUMPTIONS.md` #s throughout) -- flagged here, not silently assumed.
- **Only launches with `outcome = Success` are counted.** The single Falcon 9 Starlink
  failure in this dataset (`Group 9-4`, 2024-07-12, 20 v2 mini satellites deployed into a
  bad orbit, `working = 0`) is excluded entirely from the cumulative total, since those
  satellites never reached a usable operational orbit.
- **DTC-capable v2 mini satellites are NOT modeled as a separate lower-capacity class**
  (see cross-check section above) -- same 96 Gbps/satellite figure as broadband v2 mini,
  for lack of any published DTC-specific throughput number anywhere in this project's prior
  research (`data/satellite_capacity.csv`, `data/satellite_capacity.md`).

## Sources

- [List of Starlink and Starshield launches (Wikipedia)](https://en.wikipedia.org/wiki/List_of_Starlink_and_Starshield_launches) -- raw wikitext pulled via `action=raw`, 2026-09-05.
- [Starlink Launch Statistics (Jonathan McDowell, planet4589.org)](https://planet4589.org/space/con/star/stats.html) -- Wikipedia's own cited source for the deployed/working columns; McDowell's own page fetched directly for the cross-check totals above, 2026-09-05 (page states "updated August 31, 2026").
