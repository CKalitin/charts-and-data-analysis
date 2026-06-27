"""Derived quantities: land geometry + distance classification.

Key design choices
------------------
- Land boundary vertices -> a 3D unit-vector KD-tree for fast great-circle
  distance-to-nearest-coast. For a ~483 km threshold the vertex-sampling error
  from the 110m Natural Earth resolution is < 2%.
- shapely.contains_xy for on-land detection (exact polygon test); KD-tree for the
  distance to the nearest coast (approximate, but the threshold is large).
- One classifier (``_classify``) serves BOTH the ground track and the map
  background raster, so a point and the region it sits in can never disagree.

Category codes are the config single source of truth: CAT_LAND / CAT_NEAR / CAT_OCEAN.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
import requests
import shapely
from scipy.interpolate import RegularGridInterpolator
from scipy.spatial import cKDTree
from shapely.geometry import shape
from shapely.ops import unary_union

import config as cfg
from model import R_EARTH

# Module-level cache so the (expensive) land union + KD-tree are built once even
# when both the track classification and the background raster need them.
_ASSETS: "LandAssets | None" = None
_SOLAR: "dict[float, SolarAssets]" = {}   # keyed by the min-capacity filter (MW)


@dataclass
class LandAssets:
    land_geom:         object   # classification geometry — Antarctica excluded
    tree:              cKDTree  # KD-tree over coastline vertices — Antarctica excluded
    land_geom_display: object   # full geometry including Antarctica (coastline drawing)
    land_geom_excl:    object   # Antarctica only — stamped as CAT_LAND_EXCL on the raster


@dataclass
class ProximityData:
    lats:     np.ndarray     # sub-satellite latitudes, degrees
    lons:     np.ndarray     # sub-satellite longitudes, degrees
    dists_km: np.ndarray     # great-circle distance to nearest land, km (0 = on land)
    codes:    np.ndarray     # int category per point: CAT_LAND / CAT_NEAR / CAT_OCEAN

    def _frac(self, code: int) -> float:
        return float((self.codes == code).mean())

    @property
    def pct_land(self)  -> float: return 100 * self._frac(cfg.CAT_LAND)
    @property
    def pct_near(self)  -> float: return 100 * self._frac(cfg.CAT_NEAR)
    @property
    def pct_ocean(self) -> float: return 100 * self._frac(cfg.CAT_OCEAN)


@dataclass
class SolarAssets:
    lats:             np.ndarray   # array latitudes, degrees
    lons:             np.ndarray   # array longitudes, degrees
    mw:               np.ndarray   # nameplate capacity, MW
    tree:             cKDTree      # KD-tree over array sites in 3D unit-sphere coords
    min_mw:           float = 0.0
    exclude_countries: frozenset = frozenset()

    @property
    def n(self) -> int:        return self.lats.size
    @property
    def total_gw(self) -> float: return float(np.nansum(self.mw)) / 1e3


@dataclass
class SolarProximityData:
    lats:     np.ndarray     # sub-satellite latitudes, degrees
    lons:     np.ndarray     # sub-satellite longitudes, degrees
    dists_km: np.ndarray     # great-circle distance to nearest solar array, km
    codes:    np.ndarray     # CAT_SOLAR_NEAR / CAT_SOLAR_FAR

    @property
    def pct_near(self) -> float:
        return 100 * float((self.codes == cfg.CAT_SOLAR_NEAR).mean())

    @property
    def pct_far(self) -> float:
        return 100 * float((self.codes == cfg.CAT_SOLAR_FAR).mean())


# ── Land data loading ────────────────────────────────────────────────────────────────
def _load_land_geojson() -> dict:
    if cfg.LAND_CACHE.exists():
        with open(cfg.LAND_CACHE) as f:
            return json.load(f)
    print(f"Downloading land data from {cfg.LAND_GEOJSON_URL} ...")
    r = requests.get(cfg.LAND_GEOJSON_URL, timeout=30)
    r.raise_for_status()
    data = r.json()
    with open(cfg.LAND_CACHE, "w") as f:
        json.dump(data, f)
    print(f"Cached to {cfg.LAND_CACHE.name}")
    return data


def load_land_assets() -> LandAssets:
    """Build (and cache) the land union geometry + coastline-vertex KD-tree."""
    global _ASSETS
    if _ASSETS is not None:
        return _ASSETS

    gj = _load_land_geojson()
    all_geoms = [shape(f["geometry"]) for f in gj["features"]]
    land_geom_display = unary_union(all_geoms)

    # Split into operational (non-Antarctic) and excluded (Antarctic) geometries.
    calc_geoms = [g for g in all_geoms if g.centroid.y >= cfg.ANTARCTICA_LAT_CUTOFF]
    excl_geoms = [g for g in all_geoms if g.centroid.y <  cfg.ANTARCTICA_LAT_CUTOFF]
    land_geom      = unary_union(calc_geoms)
    land_geom_excl = unary_union(excl_geoms)

    # KD-tree built from the classification geometry's coastline vertices only.
    pts: list = []
    def _extract(geom):
        if geom.geom_type == "Polygon":
            pts.extend(geom.exterior.coords)
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                pts.extend(poly.exterior.coords)
    _extract(land_geom)

    land_arr = np.asarray(pts)                       # (M, 2): lon, lat
    land_xyz = _to_xyz(land_arr[:, 1], land_arr[:, 0])
    _ASSETS = LandAssets(land_geom, cKDTree(land_xyz), land_geom_display, land_geom_excl)
    return _ASSETS


def land_polygons(assets: LandAssets) -> list[np.ndarray]:
    """Exterior rings of every land polygon as (N, 2) lon/lat arrays (for map drawing).

    Uses the full display geometry so Antarctica appears on the map even though it is
    excluded from proximity classification.
    """
    rings: list[np.ndarray] = []
    geom = assets.land_geom_display
    if geom.geom_type == "Polygon":
        rings.append(np.asarray(geom.exterior.coords))
    elif geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            rings.append(np.asarray(poly.exterior.coords))
    return rings


# ── Classification ───────────────────────────────────────────────────────────────────
def _to_xyz(lat_deg: np.ndarray, lon_deg: np.ndarray) -> np.ndarray:
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)
    return np.column_stack([
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat),
    ])


def _classify(lats: np.ndarray, lons: np.ndarray,
              assets: LandAssets) -> tuple[np.ndarray, np.ndarray]:
    """Return (dists_km, codes) for flat lat/lon arrays.

    codes: CAT_LAND where on land, CAT_NEAR within the threshold of a coast,
    CAT_OCEAN beyond it.
    """
    on_land = shapely.contains_xy(assets.land_geom, lons, lats)

    chord, _ = assets.tree.query(_to_xyz(lats, lons), k=1)
    dists_km = 2 * np.arcsin(np.clip(chord / 2, 0, 1)) * R_EARTH
    dists_km = np.where(on_land, 0.0, dists_km)

    codes = np.full(lats.shape, cfg.CAT_OCEAN, dtype=np.int8)
    codes[(~on_land) & (dists_km <= cfg.THRESHOLD_KM)] = cfg.CAT_NEAR
    codes[on_land] = cfg.CAT_LAND
    return dists_km, codes


def compute(lats: np.ndarray, lons: np.ndarray,
            assets: LandAssets | None = None) -> ProximityData:
    """Classify ground-track points into land / coastal-water / open-ocean."""
    assets = assets or load_land_assets()
    dists_km, codes = _classify(lats, lons, assets)
    return ProximityData(lats, lons, dists_km, codes)


def classify_grid(assets: LandAssets | None = None,
                  nlon: int | None = None,
                  nlat: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Classify a regular lon/lat grid covering the globe, for the map background.

    Returns
    -------
    lon_edges : (nlon+1,) cell edges, degrees  (for pcolormesh)
    lat_edges : (nlat+1,) cell edges, degrees
    codes     : (nlat, nlon) int category per cell
    """
    assets = assets or load_land_assets()
    nlon = nlon or cfg.MAP_NLON
    nlat = nlat or cfg.MAP_NLAT

    lon_edges = np.linspace(-180, 180, nlon + 1)
    lat_edges = np.linspace(-90, 90, nlat + 1)
    lon_c = 0.5 * (lon_edges[:-1] + lon_edges[1:])
    lat_c = 0.5 * (lat_edges[:-1] + lat_edges[1:])

    LON, LAT = np.meshgrid(lon_c, lat_c)             # (nlat, nlon)

    # Classify with the operational geometry (no Antarctica).
    _, codes = _classify(LAT.ravel(), LON.ravel(), assets)
    codes = codes.reshape(LAT.shape)

    # Stamp Antarctic cells as CAT_LAND_EXCL so they render grey on the map,
    # making it visually clear they are excluded from the analysis.
    excl_mask = shapely.contains_xy(assets.land_geom_excl,
                                    LON.ravel(), LAT.ravel()).reshape(LAT.shape)
    codes[excl_mask] = cfg.CAT_LAND_EXCL

    return lon_edges, lat_edges, codes


# ── Solar arrays (Global Solar Power Tracker) ──────────────────────────────────────────
def _read_solar_xlsx() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Parse the tracker sheet -> (lat, lon, MW, country) for the configured statuses.

    Cached to an .npz keyed by the status filter so reruns skip the (slow) parse.
    Country is stored as a bytes array (object arrays can't go in npz).
    """
    status_key = "_".join(sorted(cfg.SOLAR_STATUS))
    if cfg.SOLAR_CACHE.exists():
        z = np.load(cfg.SOLAR_CACHE, allow_pickle=True)
        if str(z.get("status_key")) == status_key and "country" in z:
            return z["lats"], z["lons"], z["mw"], z["country"]

    import openpyxl
    print(f"Parsing {cfg.SOLAR_XLSX.name} (status: {sorted(cfg.SOLAR_STATUS)})...")
    wb = openpyxl.load_workbook(cfg.SOLAR_XLSX, read_only=True, data_only=True)
    ws = wb[cfg.SOLAR_SHEET]

    lats, lons, mw, countries = [], [], [], []
    for r in ws.iter_rows(min_row=2, values_only=True):
        country, cap, status, lat, lon = r[1], r[6], r[9], r[18], r[19]
        if status not in cfg.SOLAR_STATUS:
            continue
        try:
            la, lo = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        if not (-90 <= la <= 90 and -180 <= lo <= 180):
            continue
        lats.append(la)
        lons.append(lo)
        mw.append(float(cap) if isinstance(cap, (int, float)) else np.nan)
        countries.append(str(country) if country else "")
    wb.close()

    lats    = np.asarray(lats)
    lons    = np.asarray(lons)
    mw      = np.asarray(mw)
    country = np.asarray(countries)
    np.savez(cfg.SOLAR_CACHE, lats=lats, lons=lons, mw=mw, country=country,
             status_key=np.array(status_key))
    print(f"  {lats.size:,} arrays, {np.nansum(mw)/1e3:,.0f} GW total")
    return lats, lons, mw, country


def load_solar_assets(min_mw: float = 0.0,
                      exclude_countries: frozenset = frozenset()) -> SolarAssets:
    """Load solar array sites, applying capacity floor and country exclusions.

    Results are cached per (min_mw, exclude_countries) key. Arrays with unknown
    capacity (NaN) are dropped when min_mw > 0.
    """
    key = (min_mw, exclude_countries)
    if key in _SOLAR:
        return _SOLAR[key]
    lats, lons, mw, country = _read_solar_xlsx()
    keep = np.ones(lats.size, dtype=bool)
    if min_mw > 0:
        keep &= np.nan_to_num(mw, nan=0.0) >= min_mw
    for c in exclude_countries:
        keep &= (country != c)
    lats, lons, mw = lats[keep], lons[keep], mw[keep]
    _SOLAR[key] = SolarAssets(lats, lons, mw, cKDTree(_to_xyz(lats, lons)),
                              min_mw, exclude_countries)
    return _SOLAR[key]


def _classify_solar(lats: np.ndarray, lons: np.ndarray,
                    solar: SolarAssets) -> tuple[np.ndarray, np.ndarray]:
    """Return (dists_km, codes) — distance to nearest array, NEAR/FAR at the threshold."""
    chord, _ = solar.tree.query(_to_xyz(lats, lons), k=1)
    dists_km = 2 * np.arcsin(np.clip(chord / 2, 0, 1)) * R_EARTH
    codes = np.where(dists_km <= cfg.THRESHOLD_KM, cfg.CAT_SOLAR_NEAR, cfg.CAT_SOLAR_FAR)
    return dists_km, codes.astype(np.int8)


def compute_solar(lats: np.ndarray, lons: np.ndarray,
                  solar: SolarAssets | None = None) -> SolarProximityData:
    """Classify ground-track points by proximity to the nearest solar array."""
    solar = solar or load_solar_assets()
    dists_km, codes = _classify_solar(lats, lons, solar)
    return SolarProximityData(lats, lons, dists_km, codes)


def classify_solar_grid(solar: SolarAssets,
                        nlon: int | None = None,
                        nlat: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Classify a regular lon/lat grid by solar proximity, for the map background."""
    solar = solar or load_solar_assets()
    nlon = nlon or cfg.MAP_NLON
    nlat = nlat or cfg.MAP_NLAT

    lon_edges = np.linspace(-180, 180, nlon + 1)
    lat_edges = np.linspace(-90, 90, nlat + 1)
    lon_c = 0.5 * (lon_edges[:-1] + lon_edges[1:])
    lat_c = 0.5 * (lat_edges[:-1] + lat_edges[1:])

    LON, LAT = np.meshgrid(lon_c, lat_c)
    _, codes = _classify_solar(LAT.ravel(), LON.ravel(), solar)
    return lon_edges, lat_edges, codes.reshape(LAT.shape)


def classify_teff_grid(solar: SolarAssets, teff: np.ndarray,
                       nlon: int | None = None,
                       nlat: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Background raster for the transmission chart.

    Each pixel in the 'near' zone gets the T_eff of its nearest solar array;
    far-zone pixels are masked so the axes facecolor (slate) shows through.

    Returns (lon_edges, lat_edges, teff_masked).
    """
    nlon = nlon or cfg.MAP_NLON
    nlat = nlat or cfg.MAP_NLAT

    lon_edges = np.linspace(-180, 180, nlon + 1)
    lat_edges = np.linspace(-90, 90, nlat + 1)
    lon_c = 0.5 * (lon_edges[:-1] + lon_edges[1:])
    lat_c = 0.5 * (lat_edges[:-1] + lat_edges[1:])

    LON, LAT = np.meshgrid(lon_c, lat_c)
    pts = _to_xyz(LAT.ravel(), LON.ravel())

    chord, idx = solar.tree.query(pts, k=1)
    dists_km = 2 * np.arcsin(np.clip(chord / 2, 0, 1)) * R_EARTH
    near = (dists_km <= cfg.THRESHOLD_KM).reshape(LAT.shape)

    teff_grid = teff[idx].reshape(LAT.shape)
    return lon_edges, lat_edges, np.ma.masked_where(~near, teff_grid)


# ── Cloud cover + effective transmission ───────────────────────────────────────────────

class CloudCover:
    """Climatological cloud fraction field, queryable at arbitrary (lat, lon) pairs."""

    def __init__(self, source: str, fn):
        self.source = source   # human-readable description for chart labels
        self._fn = fn          # callable: (lats_arr, lons_arr) -> f_cloud in [0, 1]

    def at(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        return np.clip(self._fn(np.asarray(lats, float), np.asarray(lons, float)), 0.0, 1.0)


def _synthetic_fn(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """Latitude-only climatological model as fallback when ERA5 is unavailable."""
    c_itcz  = 0.55 * np.exp(-0.5 * (lats /  9.0) ** 2)
    c_storm = 0.45 * (np.exp(-0.5 * ((lats - 55) / 13.0) ** 2)
                    + np.exp(-0.5 * ((lats + 55) / 13.0) ** 2))
    return 0.22 + c_itcz + c_storm


def _load_era5_cloud() -> CloudCover:
    import netCDF4 as nc
    print(f"Loading ERA5 cloud cover from {cfg.ERA5_NC.name}...")
    ds = nc.Dataset(cfg.ERA5_NC)
    raw_lats = np.array(ds.variables["latitude"][:])   # (721,) descending 90→-90
    raw_lons = np.array(ds.variables["longitude"][:])  # (1440,) 0→359.75
    tcc = np.array(ds.variables["tcc"][:]).mean(axis=0)  # (721, 1440) time-average
    ds.close()

    # RegularGridInterpolator requires strictly ascending axes.
    lats_asc = raw_lats[::-1].copy()
    tcc_asc  = tcc[::-1].copy()

    # Convert ERA5 0→360 longitudes to -180→180.
    lons_180 = np.where(raw_lons > 180, raw_lons - 360, raw_lons)
    idx = np.argsort(lons_180)
    lons_180 = lons_180[idx]
    tcc_asc  = tcc_asc[:, idx]

    interp = RegularGridInterpolator(
        (lats_asc, lons_180), tcc_asc,
        method="linear", bounds_error=False, fill_value=None,
    )

    def era5_fn(lats, lons):
        return interp(np.column_stack([lats, lons]))

    return CloudCover("ERA5 (2018-2023 monthly climatological mean)", era5_fn)


_CLOUD: "CloudCover | None" = None


def load_cloud_cover() -> CloudCover:
    """Return the cloud fraction interpolator; ERA5 if available, synthetic otherwise."""
    global _CLOUD
    if _CLOUD is not None:
        return _CLOUD
    if cfg.ERA5_NC.exists():
        _CLOUD = _load_era5_cloud()
    else:
        print(f"ERA5 not found at {cfg.ERA5_NC}.\n"
              f"  Using synthetic latitude model.  Run: python scripts/download_era5.py")
        _CLOUD = CloudCover("Synthetic latitude model", _synthetic_fn)
    return _CLOUD


def compute_teff(solar: SolarAssets, cloud: CloudCover) -> np.ndarray:
    """T_eff per array: linear blend of T_CLEAR / T_OVERCAST by cloud fraction."""
    f = cloud.at(solar.lats, solar.lons)
    return f * cfg.T_OVERCAST + (1.0 - f) * cfg.T_CLEAR


@dataclass
class GriddedSolar:
    """Solar arrays binned into SOLAR_GRID_CELL_DEG cells for dot-per-cell plotting."""
    lons:     np.ndarray   # cell-centre longitudes, deg
    lats:     np.ndarray   # cell-centre latitudes, deg
    teff:     np.ndarray   # capacity-weighted mean T_eff per cell
    gw:       np.ndarray   # total capacity in cell, GW
    cell_deg: float

    @property
    def n_cells(self) -> int:
        return int(self.lons.size)

    @property
    def total_gw(self) -> float:
        return float(self.gw.sum())


@dataclass
class OrbitTransmission:
    """T_eff statistics along the SSO orbit for in-range orbit points."""
    pct_near:      float         # orbit time within range, %
    mean_teff:     float         # mean T_eff across in-range orbit points (time-weighted)
    net_utility:   float         # pct_near * mean_teff  (% of orbit time, combined)
    teff_in_range: np.ndarray    # T_eff at every in-range orbit point — for histogram


def compute_orbit_transmission(data: SolarProximityData, solar: SolarAssets,
                               teff_per_array: np.ndarray) -> OrbitTransmission:
    """Assign T_eff of nearest array to each in-range orbit point, then aggregate."""
    in_range = data.codes == cfg.CAT_SOLAR_NEAR
    if not in_range.any():
        return OrbitTransmission(0.0, 0.0, 0.0, np.array([]))

    chord, idx = solar.tree.query(_to_xyz(data.lats[in_range], data.lons[in_range]), k=1)
    teff_ir = teff_per_array[idx]

    pct  = float(in_range.mean() * 100)
    mean = float(teff_ir.mean())
    return OrbitTransmission(
        pct_near=pct,
        mean_teff=mean,
        net_utility=pct * mean,   # (%) * (dimensionless) = (%)
        teff_in_range=teff_ir,
    )


def aggregate_to_grid(solar: SolarAssets, teff: np.ndarray,
                      cell_deg: float = cfg.SOLAR_GRID_CELL_DEG) -> GriddedSolar:
    """Bin arrays into cell_deg x cell_deg cells; capacity-weighted mean T_eff + total GW."""
    i_lon = np.floor((solar.lons + 180.0) / cell_deg).astype(int)
    i_lat = np.floor((solar.lats +  90.0) / cell_deg).astype(int)
    mw    = np.nan_to_num(solar.mw, nan=100.0)

    # Unique int key per cell; grid is at most 720 x 360, so i_lat < 1000 is safe.
    keys = i_lon * 1000 + i_lat
    unique_keys, inv = np.unique(keys, return_inverse=True)

    n = len(unique_keys)
    wt_sum = np.bincount(inv, weights=mw * teff,  minlength=n).astype(float)
    w_sum  = np.bincount(inv, weights=mw,          minlength=n).astype(float)
    gw_sum = np.bincount(inv, weights=mw / 1e3,   minlength=n).astype(float)

    il = unique_keys // 1000
    ij = unique_keys  % 1000
    return GriddedSolar(
        lons     = -180.0 + (il + 0.5) * cell_deg,
        lats     =  -90.0 + (ij + 0.5) * cell_deg,
        teff     = wt_sum / w_sum,
        gw       = gw_sum,
        cell_deg = cell_deg,
    )
