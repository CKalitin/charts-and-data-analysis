# Starlink current subscribers by geography — sources & extrapolation methodology

Companion to [`starlink_subscriber_milestones.csv`](starlink_subscriber_milestones.csv)
(raw, dated data points only) and [`../starlink_subscriber_trend.py`](../starlink_subscriber_trend.py)
(the extrapolation math, as reusable pure functions — not a one-off calculation).

**Revision history**: an earlier version of this file concluded only 2 countries
(US, Brazil) had any usable data and treated the rest as flatly undisclosed. The
user correctly pushed back: SpaceX posts frequent growth milestones (global AND,
via regulators/press, several individual countries), and those can be extrapolated
forward with a documented method instead of shrugging at the gap. This version does
that — **take the anchors seriously as data, extrapolate carefully, and write down
exactly how**, so the next session can audit or update the math rather than
re-deriving it.

---

## Raw anchors (every row in `starlink_subscriber_milestones.csv`, with confidence)

**Global** (12 real dated points, Dec 2022 -> June 2026, roughly monthly resolution
in 2025-2026): SpaceX/Musk public milestone announcements, widely reported and
internally consistent with each other (1M -> 2M -> ... -> 12M in order, no
contradictions). The two most authoritative: **10.3M as of 2026-03-31** (SpaceX's
own SEC S-1 filing — the single best-sourced figure in this whole file) and **12M as
of 2026-06-04** (Musk X post, also referenced in later S-1-adjacent reporting).
**Confidence: high** for the trajectory shape; the exact day-of-month for the
mid-series milestones (e.g. "Feb 2025: 5M") is approximate (aggregator sites report
the month but not always the exact date) — each was assigned the 15th of its
reported month as a reasonable midpoint, which introduces up to ~2 weeks of date
uncertainty per point. This barely affects the extrapolation since the two anchors
actually used (S-1's Mar 31 and the June 4 X post) both have exact dates.

**One row is a FORECAST, not a data point** and is excluded from all extrapolation
by default (`exclude_forecasts=True` in the trend model): Quilty Space's independent
projection of 16.8M by v2026-12-31. Kept in the CSV for context/future comparison
only, tagged `source_type=analyst_forecast_not_actual` so code doesn't accidentally
treat it as observed.

**US**: 2 dated points — 2.0M (2025-07-15, press-reported SpaceX milestone) and
2.7M (2026-05-14, New Street Research, an independent analyst firm — same
source/month pairing as their ~10M global estimate that month, so internally
consistent). **Confidence: press-reported milestone + one named analyst firm, not
SpaceX-official, but specific and dated.** A third, vaguer 2024 figure (~1.2M) was
found in early research and is deliberately EXCLUDED from the anchor set — it has no
precise date and would only add noise to a two-point trend line, though it's
directionally consistent (1.2M in 2024 -> 2.0M mid-2025 -> 2.7M mid-2026 all point
the same way).

**Brazil**: only **1** dated point — 662K (2026-02-15, press-reported, describing
Brazil as Starlink's #2 global market). **Not enough for its own trend line** — see
the relative-growth method below. A 2024 figure (~20K) was found and EXCLUDED as
before: 20K -> 662K would imply ~33x growth, which might be real (Brazil's
adoption curve could easily have been that explosive) but the 2024 figure's source
quality and exact date were never confirmed, and one bad early anchor would swing a
two-point extrapolation wildly. Better to extrapolate one solid point forward via a
documented assumption than build a trend on a shaky point.

**Nigeria**: 3 dated points, the first 2 from the **Nigerian Communications
Commission (NCC)** — a telecom regulator, the single best source TYPE in this file
after the S-1 (a government regulator has no incentive to inflate a foreign
satellite operator's numbers): 23,897 (2023-12-31) and 65,564 (2024-09-30). A third,
vaguer point — "approaching 100,000" as of ~2026-06 — is press-reported with hedge
language, not an exact figure; read as ~95,000, flagged `_imprecise` in the CSV.
**The extrapolation deliberately uses the 2nd and 3rd points (2024-09-30 ->
2026-06-15), NOT the 1st and 2nd** — see methodology note below on why early-market
hyper-growth rates shouldn't be extrapolated over long horizons.

**Kenya**: 2 dated points, both from **Communications Authority of Kenya (CA)** (via
Space in Africa's reporting) — same "regulator" confidence tier as Nigeria's best
points: 19,460 (2025-09-30) and 24,999 (2026-03-31).

**Checked for and NOT included** (same exclusions as the prior version of this
file, still valid): a paid proprietary country tracker exists (Idem Est Research &
Advisory, ~$800-15,600, not purchased); Ukraine's ~3M "Starlink Mobile via Kyivstar"
users are a Direct-to-Cell phone product, a different metric than terminal-based
"Starlink Subscribers" and would be a unit error to include; the S-1's geographic
REVENUE-by-domicile table (Ireland $1.8B etc.) is a corporate billing-entity
artifact, not a customer-location proxy, and stays unused. **Countries searched
without finding any usable dated figure**: Canada, UK, France, Germany, Australia,
Japan, Mexico, Philippines, Poland, India (not yet live as of this research).

---

## Extrapolation methodology (implemented in `starlink_subscriber_trend.py`)

**Method: constant daily geometric growth rate between the two most recent real
anchors for a scope**, projected forward to the target date (2026-08-09, "today" in
this session). This is the standard short-horizon approach for a growing-adoption
metric — NOT a full logistic/S-curve fit (which would need many more data points and
an assumed saturation ceiling to be meaningful; overkill for a ~2-3 month
extrapolation).

**Deliberate choice: use the two MOST RECENT anchors, never the earliest ones.**
Nigeria's first 9 months of NCC data (2023-12 -> 2024-09) implies ~11.6%/month
growth — a real number, but early-market hyper-growth from a tiny base. Extrapolating
that rate over the ~21 months since would produce an absurd figure (small markets
don't sustain their first-year percentage growth rate indefinitely). Using the more
recent 2024-09 -> 2026-06 pair instead gives a much more moderate, plausible
~1.8%/month — this is the number actually used.

**Brazil (only 1 real anchor) uses a different, weaker method**:
`estimate_via_global_relative_growth()` scales Brazil's single 662K point by the
GLOBAL relative growth between Brazil's anchor date and the target date (i.e.
assumes Brazil grows at the SAME RATE as the worldwide average from that point
forward). **This is a materially weaker assumption than the other countries' own
trend lines** — Brazil was almost certainly growing FASTER than the global average
around early 2026 (it had just become the #2 market), so this method likely
UNDERSTATES Brazil's true current count. Treat it as a floor, not a point estimate.

## Results as of 2026-08-09 (computed by `starlink_subscriber_trend.py`, not hand-calculated)

| Scope | Estimate | Anchors used | Implied growth |
|---|---|---|---|
| Global | ~14.0M | 10.3M (2026-03-31, S-1) -> 12.0M (2026-06-04) | ~0.235%/day (~7.3%/mo) |
| US | ~2.94M | 2.0M (2025-07-15) -> 2.7M (2026-05-14) | ~0.099%/day (~3.0%/mo) |
| Nigeria | ~98.2K | 65,564 (2024-09-30) -> ~95,000 (2026-06-15, imprecise) | ~0.060%/day (~1.8%/mo) |
| Kenya | ~29.9K | 19,460 (2025-09-30) -> 24,999 (2026-03-31) | ~0.138%/day (~4.2%/mo) |
| Brazil | ~927K | single anchor (662K, 2026-02-15) x global relative growth | (borrows global rate) |

**Known total: ~4.0M of ~14.0M global (~28.5%).** Adding Nigeria and Kenya barely
moved this share versus the earlier 2-country version (US+Brazil alone were ~28%) —
**both are real, regulator-sourced markets, but small in absolute terms.** The
~10M-subscriber gap is still dominated by unlisted-but-plausibly-large markets this
research did not find usable figures for: Canada, UK, France, Germany, Australia,
Japan, Mexico, Philippines, and ~155 others. **Do not read "4 countries now covered"
as "the picture is now mostly complete" — it isn't; it's modestly less incomplete.**

## Revision 2 (2026-08-09, same session): UK, Mexico, Canada added via Ookla market-share data

The user pushed back again, specifically naming UK and France as markets that
"must" have some findable data. They were right that more exists — the first pass
stopped after the US/Brazil/Nigeria/Kenya milestone search without trying a
fundamentally different source type: **Ookla's "2025 Global Satellite Broadband
Performance Report"** (published 2026-02-04, Q3 2025 data), which ranks countries
by **their share of Starlink's global Speedtest samples** — a different metric from
a subscriber-count milestone, but a real, named, dated, methodologically-described
one. New data, in [`starlink_ookla_market_share.csv`](starlink_ookla_market_share.csv):

| Country | Share of global Starlink Speedtest samples (Q3 2025) |
|---|---|
| US | 22.5% |
| Mexico | 5.7% |
| Canada | ~4.3% |
| UK | 3.5% (11th largest market) |

**France: genuinely searched again, including French-language sources (ARCEP
consultation documents, French tech press) — no subscriber or market-share figure
found anywhere.** ARCEP's public documents cover spectrum authorization, not
subscriber counts. This isn't a case of not trying; the data does not appear to be
public. Also checked and NOT found: Germany, Australia, Japan, Philippines,
Indonesia (ranked top-5 by two different secondary sources, but no country
specifically states its %).

**Important cross-check discrepancy, worth knowing before trusting these numbers**:
converting the US's 22.5% share to a subscriber count (22.5% x ~7M global
subscribers around Q3 2025) gives **~1.6M** — but the US's own DIRECT milestone
anchor for a very similar date (2.0M, dated 2025-07-15, a few weeks before Q3 2025)
is **~25% higher**. This means **"share of Speedtest samples" is NOT the same as
"share of subscribers"** — Starlink users in some countries apparently run
Speedtest at different rates per-subscriber than others (plausibly: an established,
mature market like the US tests less per-capita than a newer, more novelty-driven
market). **Direction and magnitude of this bias for Mexico/Canada/UK specifically is
unknown** — their share-based estimates could be too high or too low, and the US
comparison only proves the method is imperfect, not which way it's off for a
different country. Treat these 3 estimates as **directional (a defensible relative
ranking), not precise subscriber counts**, and weight them well below the
milestone-based countries (US, Brazil, Nigeria, Kenya) in confidence.

**Also found, and flagged as a separate unresolved inconsistency**: one source
described Canada as having "500,000+ active subscribers (~4.3% of worldwide
users)" at Q3 2025 — but 500,000 / 7,000,000 (global at that time) is actually
~7.1%, not 4.3%. The two numbers in that same sentence don't agree with each other
mathematically. Rather than silently pick one, both are logged here; the chart uses
the 4.3%-share-based estimate for consistency with Mexico/UK's same-metric figures,
not the 500K figure.

`estimate_via_ookla_share(share_pct, target_date)` in `starlink_subscriber_trend.py`
implements this: `share% x global_value_at(target_date)`, i.e. assumes the
country's share has stayed constant since the Q3 2025 report — another stacked
assumption on top of the sample-vs-subscriber gap above.

## Results as of 2026-08-09, revision 2 (7 countries total)

| Country | Estimate | Method | Confidence |
|---|---|---|---|
| US | ~2.94M | milestone extrapolation (2 direct anchors) | highest |
| Brazil | ~927K | 1 anchor x global relative growth | medium (likely underestimate) |
| Mexico | ~798K | Ookla share (5.7%) x global | lower (share-vs-subscriber gap unverified for this country) |
| Canada | ~602K | Ookla share (4.3%) x global | lower (same caveat; conflicts with a separate ~500K/7.1% figure) |
| UK | ~490K | Ookla share (3.5%) x global | lower (same caveat) |
| Nigeria | ~98K | milestone extrapolation (2 regulator anchors) | high (regulator-sourced) |
| Kenya | ~30K | milestone extrapolation (2 regulator anchors) | high (regulator-sourced) |

**Known total: ~5.9M of ~14.0M global (~42%)** — a real improvement from ~28.5% in
revision 1, driven mostly by the 3 large Ookla-share markets. **Still ~58%
undisclosed/unallocated**, across France, Germany, Australia, Japan, Philippines,
Indonesia (a confirmed top-5 market with no % found), and ~150 others.

## What a future session should do to improve this further

- Re-run `starlink_subscriber_trend.py` with fresh milestone data as new global
  figures or country regulatory reports appear — the anchors will go stale within
  weeks given the growth rate involved.
- Specifically worth searching for next: Ofcom (UK), ARCEP (France), Bundesnetzagentur
  (Germany), ACMA (Australia), CRTC (Canada) satellite-broadband subscriber reports —
  these are the same "telecom regulator" source type that worked well for
  Nigeria/Kenya, and these markets are large enough to matter for the known/unknown
  split.
- If budget allows, the Idem Est Research & Advisory country tracker (idemest.com)
  would likely close most of the remaining gap directly, at a cost.
