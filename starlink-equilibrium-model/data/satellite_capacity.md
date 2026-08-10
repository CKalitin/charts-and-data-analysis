# Satellite capacity & customer density — sources & methodology

Companion to [`satellite_capacity.csv`](satellite_capacity.csv). Follows the same
citation convention as the rest of this project: every figure cited with a
confidence note. SpaceX does not publish detailed per-satellite capacity specs, so
**every number in this file is a third-party analyst estimate, not an official
SpaceX disclosure** — treat with wider error bars than the Phase 1/2 data.

Researched 2026-08-09.

---

## Per-satellite throughput, by generation

**v1.0**: not separately published anywhere found in this research session. Left
blank in the CSV, not estimated.

**v1.5**: ~17-23 Gbps total downlink capacity (analyst estimate, midpoint ~20 used in
the CSV). Derived from FCC-filing-based analysis: 4 phased-array antennas (1 uplink,
3 downlink), each capable of 8 beams x 2 polarizations = 48 downlink beams, 16 uplink
beams total. Uplink total capacity not found. **Confidence: analyst estimate from FCC
filing analysis, single source found, not cross-confirmed.**

**v2 Mini**: **96 Gbps downlink, 6.7 Gbps uplink** (roughly 14:1 down:up ratio), 16
beams per satellite, ~6 Gbps downlink / ~0.419 Gbps uplink per beam. **Confidence:
cross-confirmed by two independent sources** — davidveksler.com's Starlink engineering
specs summary (96 Gbps) and Meinrath/Grindal/Fishbine/DeGidio, "Starlink Capacity
Analysis v0.2," X-Lab/Penn State working paper, July 18 2025 (96 Gbps down / 6.7 Gbps
up / 16 beams) — both land on the same number independently, which is the strongest
cross-check available for any figure in this file. Roughly 4x v1.5's capacity per the
same sources, attributed to larger phased arrays and E-band backhaul.

**v3 Broadband**: 1,024 Gbps downlink / 200+ Gbps uplink design target. **Confidence:
company-stated target for an unbuilt/not-yet-operational generation, not a measured
or FCC-filing-derived figure — treat as aspirational, same caveat as the Starship
launch-cost targets in the Reflect Orbital sourcing file.** No operational V3
deployment existed as of the source's July 2026 writing.

---

## Max customers per satellite / max customer density — full methodology reproduced

This is the **required** density constraint (see `CLAUDE.md`), and the best public
source found is a complete, transparent, reproducible derivation: Meinrath, Grindal,
Fishbine & DeGidio, "Starlink Capacity Analysis v0.2," X-Lab working paper, Penn
State University, July 18 2025
(https://thexlab.org/wp-content/uploads/2025/07/Starlink_Analysis_Working_Paper_v0.2.pdf).
**Confidence: single source for the density derivation itself (the underlying beam
capacity numbers it uses are the cross-confirmed v2 Mini figures above), explicit
about every assumption, built for a specific regulatory purpose (BEAD/NTIA broadband
funding eligibility) — read the assumptions before reusing the headline number.**

### Assumptions (all explicit in the source)
- Beam footprint: 1.5° beamwidth (a "reasonable midpoint" assumption per the paper,
  not a disclosed spec), 550 km altitude (Starlink's original planned shell — see
  `starlink_shells.md` for why current altitudes are somewhat lower; the paper notes
  this explicitly as a simplification).
- Beam footprint area formula: `A = pi * (tan(beamwidth/2) * altitude)^2` → **162.86
  km² (~62.9 sq mi)** circular footprint at nadir.
- Contention ratio: 20:1 (industry-standard oversubscription assumption for consumer
  broadband — i.e., only 1 in 20 subscribers is actively using capacity at any
  instant).
- Minimum qualifying broadband speed: 100 Mbps down / 20 Mbps up (US NTIA/BEAD
  program definition — a regulatory threshold, not a physical constant; a different
  minimum-speed assumption changes the density number directly and proportionally).

### Derivation
- Per-beam capacity: 6 Gbps down, 0.419 Gbps up (96/16 and 6.7/16).
- Per-beam max subscriber count, dedicated bandwidth (no contention): download-limited
  = 6 / 0.1 = 60; upload-limited = 0.419 / 0.02 ≈ 21. **Upload is the binding
  constraint** (matches real-world Starlink upload being the weaker side, 14:1
  down:up ratio).
- Per-beam max subscriber count, with 20:1 contention: 21 x 20 ≈ **419 subscribers per
  beam** (upload-limited, the binding case).
- **Max customer density: 419 subscribers / 62.9 sq mi = 6.66 subscribers per square
  mile ≈ 2.57 subscribers per km²**, beyond which Starlink cannot sustain the 100/20
  Mbps minimum for all subscribers in that beam's footprint.
- **Max customers per satellite (16 beams x 419, contended): ~6,704.** Not stated as
  a headline number in the source (the source's own focus is the density threshold,
  not a per-satellite total) — this is a straightforward multiplication of the
  source's own per-beam figure by beam count, computed here, not an extra assumption.

### Sensitivity noted by the source itself
- With two overlapping 1° beams (tighter beamwidth, deliberate overlap), the source
  estimates density could rise to **~30 subscribers per square mile** before
  saturation — a ~4.5x looser constraint, entirely dependent on how aggressively
  Starlink overlaps beams in practice (not something this research confirmed either
  way for current operations).
- The source explicitly excludes topography, weather attenuation, self-interference,
  and hand-off/micro-outage effects — all of which would tighten (lower) the real
  density limit further. **Treat 6.66/sq mi as an optimistic upper bound, not a
  typical real-world figure.**
- The source cites real-world corroboration: as of June 2025, only ~17% of US Ookla
  speedtest users on Starlink met the 100/20 Mbps threshold at all — consistent with
  (though not proof of) the constellation already operating near or above this
  density ceiling in parts of the US.

---

## What this means for Phase 3/5

- The 6.66 BSL/sq mi (2.57/km²) density ceiling and ~6,704 customers/satellite figure
  are both **v2 Mini, 550 km, 1.5° beamwidth, 20:1 contention, 100/20 Mbps threshold**
  specific. Changing any assumption changes the number proportionally — these are not
  physical constants, they're a specific, well-documented scenario. `capacity_density_model.py`
  keeps the derivation as parameterized pure functions (not hardcoded results) so a
  different assumption set can be re-run rather than requiring new hand arithmetic.
- This density constraint is about **local oversubscription within one beam's
  footprint**, independent of the latitude-band satellite-count question Phase 2
  answered. A latitude band can have plenty of satellites overhead (Phase 2) while
  still being locally oversaturated if population density within a single beam's
  ~163 km² footprint exceeds ~2.57/km² (this section). Phase 5 needs BOTH constraints,
  not just one.
- v1.0/v1.5 density figures were NOT derived (no beam-count/footprint data found for
  those generations) — only v2 Mini has a full derivation. If the equilibrium model
  needs a v1.5-specific density limit, that's an open gap, not silently filled here.
