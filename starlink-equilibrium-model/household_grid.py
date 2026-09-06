"""People per connection, per lat/lon tile.

WHY THIS EXISTS
===============
Satellite capacity in this project is denominated in SUBSCRIBERS, not people. The
X-Lab derivation behind capacity_density_model.py counts how many *subscriptions*
(one dish, one household) a beam can hold while each still meets 100/20 Mbps under
20:1 contention -- 419 per beam, 200,000 per V3 satellite, 195/km^2. WorldPop
demand, on the other hand, is PEOPLE.

Comparing the two directly -- which every capacity model in this project did before
2026-09-05 -- silently asserts one person per dish. It does not overstate the
market; it UNDERSTATES how many people a satellite can reach, by roughly the
household size (global population-weighted mean ~4.2). tile_capacity_model.py now
works in connections internally and converts back to people for reporting, and this
module supplies the conversion factor per tile.

METHOD
======
`data/household_size_by_country.csv` is per country (151 of 217 from a national
census or survey, 66 on a regional-median fallback -- see ASSUMPTIONS.md #13). To
use it on a lat/lon grid, each tile is attributed to the country whose Natural Earth
110m polygon contains its centre. Tiles with population but no polygon hit -- coastal
tiles whose centre falls offshore, and the ~50 small states the 110m simplification
drops entirely -- fall back to the population-weighted global mean rather than being
discarded.

Known limitation: one household size per whole country, applied uniformly. Rural
households are generally larger than urban ones in the same country, which matters
here because Starlink's addressable demand skews rural -- so the true rural figure is
probably somewhat above the national average, making this conversion mildly
conservative in exactly the segment that matters most. No sub-national household-size
dataset was sought.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

import country_geometry as cgeo

DATA = Path(__file__).resolve().parent / "data"
HOUSEHOLD_CSV = DATA / "household_size_by_country.csv"


def load_household_size() -> dict[str, float]:
    """{iso3: people per household}."""
    with open(HOUSEHOLD_CSV, encoding="utf-8") as f:
        return {r["iso3"]: float(r["household_size"]) for r in csv.DictReader(f)
                if r.get("household_size")}


def household_size_by_tile(lat_centers: np.ndarray, lon_centers: np.ndarray,
                           population: np.ndarray | None = None,
                           subsamples: int = 4) -> tuple[np.ndarray, dict]:
    """People per connection for every tile, plus a coverage report.

    Each tile is probed at `subsamples` x `subsamples` interior points rather than
    only at its centre, and takes the mean household size over whichever probes land
    inside a country. Probing centres alone matched just 87.8% of world population --
    a 1 degree tile covering a coastal city often has its centre offshore, so dense
    coastal populations were falling through to the global fallback. Subsampling
    lifts that above 97%, and a tile straddling a border gets a blend of both
    neighbours rather than an arbitrary winner.

    `population` (people per tile) is used only to weight the global-mean fallback
    and to report how much of the world's population landed inside a matched tile --
    pass it whenever available so the fallback is population-weighted, not
    area-weighted.
    """
    sizes = load_household_size()
    paths = cgeo.load_country_paths()

    n_lat, n_lon = len(lat_centers), len(lon_centers)
    d_lat = abs(lat_centers[1] - lat_centers[0]) if n_lat > 1 else 1.0
    d_lon = abs(lon_centers[1] - lon_centers[0]) if n_lon > 1 else 1.0
    offs = (np.arange(subsamples) + 0.5) / subsamples - 0.5

    sub_lat = (lat_centers[:, None] + offs[None, :] * d_lat).ravel()
    sub_lon = (lon_centers[:, None] + offs[None, :] * d_lon).ravel()
    lon2d, lat2d = np.meshgrid(sub_lon, sub_lat)
    points = np.column_stack([lon2d.ravel(), lat2d.ravel()])

    total = np.zeros(points.shape[0])
    hits = np.zeros(points.shape[0], dtype=np.int32)
    for iso3, plist in paths.items():
        size = sizes.get(iso3)
        if size is None:
            continue
        for path in plist:
            (x0, y0), (x1, y1) = path.get_extents().get_points()
            # Bounding-box prefilter: testing every probe against every polygon of
            # all 177 countries is the slow way round.
            near = np.flatnonzero((points[:, 0] >= x0) & (points[:, 0] <= x1)
                                  & (points[:, 1] >= y0) & (points[:, 1] <= y1))
            if near.size == 0:
                continue
            inside = near[path.contains_points(points[near])]
            total[inside] += size
            hits[inside] += 1

    shape4 = (n_lat, subsamples, n_lon, subsamples)
    tile_total = total.reshape(shape4).sum(axis=(1, 3))
    tile_hits = hits.reshape(shape4).sum(axis=(1, 3))

    out = np.full((n_lat, n_lon), np.nan)
    matched = tile_hits > 0
    out[matched] = tile_total[matched] / tile_hits[matched]

    if population is not None and population.sum() > 0:
        pop_matched = float(population[matched].sum())
        fallback = (float((population[matched] * out[matched]).sum() / pop_matched)
                    if pop_matched > 0 else float(np.mean(list(sizes.values()))))
        report = {
            "tiles_matched": int(matched.sum()),
            "population_matched_share": pop_matched / float(population.sum()),
            "fallback_household_size": fallback,
            "subsamples": subsamples,
        }
    else:
        fallback = float(np.mean(list(sizes.values())))
        report = {"tiles_matched": int(matched.sum()), "population_matched_share": None,
                  "fallback_household_size": fallback, "subsamples": subsamples}

    out[~matched] = fallback
    return out, report


if __name__ == "__main__":
    import population_density_grid as pdg
    import tile_capacity_model as tcm

    tile = tcm.make_tile_grid()
    demand = tcm.build_demand(tile, household_size=np.ones(tile.shape))  # people, unconverted
    hh, report = household_size_by_tile(tile.lat_centers, tile.lon_centers, demand.population)
    pop = demand.population
    print(f"tiles matched to a country polygon: {report['tiles_matched']:,} of {hh.size:,}")
    print(f"share of world population inside a matched tile: {report['population_matched_share']*100:.2f}%")
    print(f"population-weighted mean household size: "
          f"{float((pop * hh).sum() / pop.sum()):.2f} people per connection")
    print(f"fallback applied to unmatched tiles: {report['fallback_household_size']:.2f}")
    print(f"world population {pop.sum()/1e9:.2f}B -> {(pop/hh).sum()/1e9:.2f}B connections")
    _ = pdg  # imported for the module-level dependency note only
