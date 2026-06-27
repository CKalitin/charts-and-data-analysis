# SSO Ground-Track Land Proximity

How much of a sun-synchronous satellite's orbit time is spent over land, over
coastal water (within 300 mi of a coast), or over open ocean?

A circular SSO ground track (550 km, 97.6°) is propagated for a full sidereal
day (16 orbits), every sample carrying equal time weight. Each sample — and each
cell of a background raster covering the globe — is classified against Natural
Earth 110m land:

- **on land** (exact `shapely.contains_xy` polygon test), else
- **distance to nearest coast** via a 3D unit-vector KD-tree over coastline
  vertices (chord → great-circle), then thresholded at 300 mi / 483 km.

## Result

| Region | Orbit-time fraction |
|---|---|
| Over land | ~32% |
| Coastal water (< 300 mi) | ~24% |
| Open ocean | ~44% |

**~57% of orbit time is within 300 mi of land** — well above Earth's 29% land
share, because the near-polar track lingers over Eurasia, North America, and the
Antarctic margins. The figure is insensitive to inclination (85–98.5°: ±2%) and
altitude (400–700 km: ±2%).

### Proximity to solar arrays

The same track is also classified against the **operating utility-scale arrays
(1 MW+)** in the *Global Solar Power Tracker* (Global Energy Monitor, Feb 2026) —
81,377 sites, ~1,268 GW. A KD-tree over the array sites gives distance to the
nearest array; the threshold is the same 300 mi.

One chart is rendered per minimum-capacity floor in `SOLAR_MIN_MW_CASES`
(`config.py`, default `[0, 100]`):

| Min array size | Sites kept | Capacity | Within 300 mi |
|---|---|---|---|
| all operating | 81,377 | 1,268 GW | **28.7%** |
| ≥ 100 MW | 3,379 | 699 GW | **13.2%** |

The all-sizes fraction is nearly as high as the land fraction (~32%): a 300 mi
buffer merges the dense clusters (China, India, Europe, US Southwest) into broad
coverage corridors. **The 100 MW floor is the surprise** — it keeps only 4% of
sites but 55% of the gigawatts, yet in-range orbit time *more than halves*. Large
plants are geographically concentrated, so the coverage corridors collapse even
though most of the capacity remains.

Filter status via `SOLAR_STATUS` (defaults to `operating`); arrays with unknown
capacity are dropped when a size floor is set. Parsed sites are cached to
`data/solar_arrays.npz`; outputs are `sso_solar_proximity.png` and
`sso_solar_proximity_min100MW.png`.

## Layout

```
config.py   — orbital params, threshold, raster resolution, light-mode colors
model.py    — pure SSO ground-track propagator (no I/O)
derived.py  — land + solar geometry, KD-trees, classifiers for track + background raster
charts/     — proximity_map.py   (land:  classified world map + SSO track + donut)
              solar_proximity.py (solar: array sites + coverage raster + SSO track + donut)
viz/        — bundled render / plotting / info_box helpers
run.py      — orchestrator (renders both charts)
```

## Run

```
pip install -r requirements.txt
python run.py                 # -> outputs/sso_land_proximity.png
python charts/proximity_map.py   # just this chart family
```

Land data is fetched once from GitHub and cached locally (`ne_110m_land.geojson`).
