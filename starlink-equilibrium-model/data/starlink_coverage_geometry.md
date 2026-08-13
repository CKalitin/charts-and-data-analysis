# Starlink ground-coverage radius & minimum elevation angle — sources & methodology

Companion to `orbital_geometry.py`'s coverage-radius functions
(`off_nadir_angle_deg()`, `ground_range_angular_radius_deg()`, `ground_range_km()`,
`expected_sats_reaching_latitude()`) and `ASSUMPTIONS.md` #11. Follows the same
citation convention as `starlink_shells.md` and `satellite_capacity.md`: every
figure cited with a confidence note, including how far the citation chain was
actually traced (not just the first source that repeats a number).

Researched 2026-08-11, citation chain dug deeper 2026-08-13 after the user pushed
back on the initial sourcing ("that 25 degree number is not official from Huston,
unless it cites a source but I can't see one") — **and traced all the way to the
actual FCC order text** the same day, after a follow-up question ("what number do
we use... has SpaceX through FCC released anything to suggest something?").

---

## What "minimum elevation angle" actually means (a real point of confusion)

**It's the ground terminal's (the user's dish's) angle, not the satellite's.**
Elevation angle is measured AT the dish, between the local horizontal (the
terminal's own horizon) and the line of sight up to the satellite — 0° is a
satellite sitting right on the horizon, 90° is a satellite directly overhead.
"Minimum elevation angle" is the lowest the dish will let a satellite get before
it stops using it (signal degrades near the horizon from atmospheric attenuation,
obstructions, and multipath).

This is NOT the same thing as the satellite's own **off-nadir angle** (how far the
satellite has to point its beam away from straight-down to reach that same ground
point) — a different, related quantity computed by `off_nadir_angle_deg()` in this
project, measured at the satellite's end of the same line of sight. The two angles
sum with the 90°-elevation triangle's angles to 180° (law of sines on the
Earth-center/satellite/ground-station triangle) — see `ground_range_angular_radius_deg()`'s
docstring for the actual computation.

**Two pieces of direct evidence this is a ground-terminal quantity, not a
satellite one**, found while re-checking Geoff Huston's slides (see below):
- The slide stating "Starlink tracks satellites with a minimum elevation of 25°"
  is titled **"Looking Up"** — the ground terminal's perspective, looking up at
  the sky.
- A later slide shows live output from Starlink's own dish diagnostic tool
  (`starlink-grpc-tools/dish_grpc_text.py status`), which reports a field literally
  named `direction_elevation` (64.6° in that sample) — elevation is something
  **the dish itself measures and reports**, not a satellite-side spec.

---

## The 25° figure — full citation chain, traced as far as practical

**Where it's used**: `orbital_geometry.py`, `MIN_ELEVATION_DEG = 25.0`.

**Level 1 — where this project found it repeated, without a visible source**:
Geoff Huston (APNIC Chief Scientist), *"Starlink Protocol Performance"*, IETF/IEPG
118 slides (2026):
https://www.ietf.org/slides/slides-iepg-starlink-protocol-performance-00.pdf /
https://datatracker.ietf.org/meeting/118/materials/slides-118-iepg-sessa-starlink-protocol-performance-00
— slide 5 ("Looking Up"): *"Starlink tracks satellites with a minimum elevation of
25°. There are between 30–50 visible Starlink satellites at any point on the
surface between latitudes 56° north and south."* **No citation or footnote on that
slide** — extracted and re-checked the raw PDF text directly (not just a summary)
to confirm this. Huston's slide 3 also states the *"~900km radius"* coverage
footprint at 550km this project cross-validated its own geometry against — same
situation, stated as fact, no visible source on the slide.

**Level 2 — where the user found an actual citation** (re-researched 2026-08-13):
Shkelzen Cakaj, *"The Parameters Comparison of the 'Starlink' LEO Satellites
Constellation for Different Orbital Shells,"* Frontiers in Communications and
Networks, vol. 2, article 643095 (2021):
https://www.frontiersin.org/journals/communications-and-networks/articles/10.3389/frcmn.2021.643095/full
— an actual peer-reviewed academic paper (unlike Huston's slides, which are a
conference talk). States explicitly: *"Starlink has submitted the request to FCC
... for the lower users' elevation angle of 25° rather than the 40°, in order to
improve the reception"* and, for the original figure, *"Starlink, for the first
shell (layer at the altitude of 550 km), applies an elevation angle for the
designed horizon plane at 40° for users."* **This paper's own citation for both
numbers is "Starlink (2020)" / "Starlink Satellite Missions (2020)"** — i.e. it
traces the figure to SpaceX's own public statements / FCC filing materials from
2020, not an independent academic derivation or measurement.

**Level 3 — the actual FCC order, opened and read directly (2026-08-13)**: pulled
the raw PDF and extracted its text with `pypdf` (WebFetch's own PDF reader choked
on it, returning "no relevant content found" — worth knowing for future FCC-filing
research in this project: pull the PDF and extract text locally instead of relying
on WebFetch's summary for these). This resolved the chain completely:

`docs.fcc.gov/public/attachments/fcc-21-48a1.pdf` — **FCC Order FCC 21-48**,
approving SpaceX's *"Third Modification Application"* (IBFS File No.
SAT-MOD-20200417-00037, **filed April 17, 2020** — this is almost certainly what
the Frontiers paper's "Starlink (2020)" citation refers to). Footnote 3 of the
order states, verbatim:

> *"Specifically, SpaceX is authorized to operate with earth station elevation
> angles as low as 25 degrees for user terminals and gateways, and for gateways
> in the polar regions it is authorized to operate with earth station elevation
> angles as low as five degrees."*

And from the order's body text: *"SpaceX states that to maintain coverage with
the satellites at the lower altitudes, SpaceX would use a minimum elevation angle
as low as 25 degrees for user beams..."* — directly tying the 25° figure to the
SAME altitude change (1,100-1,300km → 540-570km) that produced this project's real
Gen1 shells. **This is a primary source**: an actual FCC regulatory order text,
not a summary, not a secondary source repeating a number — read and confirmed
directly.

**This also fully reconciles an apparent contradiction found along the way**: the
APNIC blog *"Navigating Starlink's FCC paper trail"*
(https://blog.apnic.net/2024/06/26/navigating-starlinks-fcc-paper-trail/) states
that Starlink's ORIGINAL 2016 filing (`SAT-LOA-20161115-00118`) specified a 40°
minimum elevation, "to protect terrestrial microwave links" — a genuinely
different figure, from a genuinely different (earlier) filing, for a genuinely
different reason (interference protection, not reception quality). Both are real:
**40° was the original 2016 figure; SpaceX's 2020 Third Modification Application
requested — and the FCC's 2021 order (21-48) granted — lowering it to 25°**,
paired with lowering the satellite altitude to 540-570km. Not two competing claims
about the same thing; two different points in the same regulatory timeline.

**Confidence: now directly confirmed from FCC order text**, not just "well-
attested, traced to an unopened filing" as this doc said as of a few hours
earlier. 25° is the actual FCC-authorized minimum elevation angle for Gen1 user
terminals, current as of the 2021 order (superseded only for shells below 500km by
the 2026 STA already documented above, which doesn't reach Gen1's real 540-570km
shells).

**Sequence, now confirmed rather than inferred**: 2016 original license, 40°
(interference protection) → SpaceX's 2020 Third Modification Application requests
540-570km altitude + 25° elevation ("to maintain coverage... improve customer
experience") → FCC Order 21-48 (2021) grants it → STA-20220516-00051 (2022)
further extends a 5° minimum specifically to polar-region operations (buildout of
the near-polar shell) → 2026 STA lowers minimums further, but only below 500km
(doesn't reach Gen1). `MIN_ELEVATION_DEG=25` is the applicable, FCC-confirmed
figure for this project's real shells; `ALT_MIN_ELEVATION_DEG=40` is correctly
the ORIGINAL (now-superseded) figure, kept only for the cross-validation below —
see `ASSUMPTIONS.md` #11 for the corrected framing.

---

## What do the tracker websites use? (checked 2026-08-13)

Checked two live Starlink trackers directly for their stated methodology:
- **starlink.sx** (https://starlink.sx/): has a user-adjustable **"Minimum
  elevation"** setting in its own UI — i.e. no single fixed number, the viewer
  picks it. Separately mentions a "40° visibility line" drawn "at zero tilt," but
  this describes the Dishy hardware's own physical steering/field-of-view limit
  (a phased-array antenna's electronic steering range), a DIFFERENT concept from
  the link-quality minimum elevation angle this project's model uses — coincidentally
  the same numeral as the original 2016 FCC figure, not the same thing.
- **orbitalradar.com** (https://orbitalradar.com/starlink-tracker/): displays
  live "Max elevation" / "Avg elevation" as computed RESULTS for a viewer's chosen
  location, but doesn't publish what elevation cutoff it uses to draw coverage
  circles.

**Neither tracker site documents a single fixed radius/angle as "the" number** —
both treat it as either user-configurable or an unpublished implementation detail.
This is consistent with 25° being the right MODELING choice for this project (the
FCC-authorized, currently-applicable figure) even though public trackers don't
converge on displaying one canonical value.

---

## Coverage-radius cross-validation figures

**~900 km at 25°, 550 km altitude**: Huston's slide 3, stated directly (*"no more
than ~900Km radius, or 2M K²"*) — same slide deck as the 25° figure above, so this
isn't an independent second source for the elevation angle itself, but it IS an
independent number this project's own `ground_range_km()` computation could be
checked against: this project computed **940.7 km**, a ~4% difference, close
enough to confirm the geometry (law of sines on the Earth-center/satellite/
ground-station triangle) is implemented correctly, not exactly matching because
Huston's figure is a rounded, standalone claim without its own shown derivation.

**~580 km at 40°**: the Frontiers paper above computes this altitude/elevation
combination directly. This project's own `ground_range_km()` computed **573.5
km** for the same inputs — a closer match (~1% difference), consistent with the
Frontiers paper showing its actual formula (this project's independent derivation
converges on nearly the same number via the same standard geometry) rather than a
rounded claim.

---

## What this means for the model

`MIN_ELEVATION_DEG = 25.0` is the applicable figure for every real Gen1 shell in
this project (540-570 km) — the 2026 FCC ruling that further lowers the minimum
(to 10-20°) only applies below 500 km, so it doesn't reach any of Gen1's real
shells; see `ASSUMPTIONS.md` #11 for that check. `ALT_MIN_ELEVATION_DEG = 40.0` is
kept as a documented alternative specific to the 550 km shell's original design
figure, used only for the cross-validation above, not as a live model input
anywhere.

**Only `charts/satellite_range_coverage.py`'s two figures depend on this
constant** (`satellite_density_by_latitude_with_range.png`,
`satellite_range_vs_population_by_latitude.png`) plus, downstream, the
range-extended density-cap term in `serviceable_customers_model.py`
(`sats_reaching_latitude()`, `effective_density_cap_by_latitude()`) — everything
else in this project (shell geometry, capacity/density scenario, orbital period)
is independent of the elevation-angle question entirely.
