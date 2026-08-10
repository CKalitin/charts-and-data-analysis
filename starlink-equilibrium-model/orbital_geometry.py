"""Pure orbital-mechanics functions for Starlink shell coverage (Phase 2).

Physics used (standard circular-orbit spherical trigonometry, no J2/perturbation
correction -- flagged as a simplification, adequate for a market-sizing model, not
for actual satellite operations):

  - Sub-satellite latitude as a function of argument of latitude u (0..2*pi per orbit):
        lat(u) = asin(sin(i) * sin(u))
    Max |lat| reached over one orbit = i for i <= 90 deg, else 180 - i (inclinations
    > 90 deg are retrograde/near-polar; the ground track still only reaches a max
    latitude of 180-i, not literally over the pole unless i == 90).

  - Longitude relative to the ascending node:
        lam(u) = atan2(cos(i) * sin(u), cos(u))
    This plus a subtraction for Earth's rotation during the elapsed time produces the
    familiar S-curve Starlink ground track on a world map.

  - Orbital period via Kepler's third law: T = 2*pi*sqrt(a^3 / mu).

  - Time-averaged latitude density: satellites moving at constant angular rate in u
    spend unequal TIME at different latitudes -- they linger longest near their max
    inclination (turning points) and move fastest through the equator crossing, the
    same effect as a pendulum lingering at the top of its swing. Computed here by
    dense numeric sampling of u (not a closed-form density, which has an integrable
    singularity at the turning points that's easy to get subtly wrong) and
    histogramming into latitude bins. This is what lets Phase 3 turn "N satellites in
    a shell" into "expected satellites overhead at latitude X at any instant."
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

EARTH_RADIUS_KM = 6378.137
EARTH_MU_KM3_S2 = 398600.4418          # standard gravitational parameter
SIDEREAL_DAY_S = 86164.0905

DATA_CSV = Path(__file__).resolve().parent / "data" / "starlink_shells.csv"


@dataclass(frozen=True)
class Shell:
    shell_id: str
    generation: str
    altitude_km: float
    inclination_deg: float
    orbital_planes: int
    sats_per_plane: int
    status: str

    @property
    def total_sats(self) -> int:
        return self.orbital_planes * self.sats_per_plane

    @property
    def semi_major_axis_km(self) -> float:
        return EARTH_RADIUS_KM + self.altitude_km

    @property
    def period_s(self) -> float:
        a = self.semi_major_axis_km
        return 2 * np.pi * np.sqrt(a ** 3 / EARTH_MU_KM3_S2)


def max_latitude_deg(inclination_deg: float) -> float:
    """Max |latitude| a ground track reaches for a given orbital inclination."""
    i = inclination_deg
    return i if i <= 90 else 180 - i


def load_shells_with_full_geometry(csv_path: Path = DATA_CSV) -> list[Shell]:
    """Load only rows with complete altitude/inclination/planes/sats_per_plane data.

    Many rows in starlink_shells.csv are altitude+inclination only (no public
    plane-count data -- see starlink_shells.md); those can't feed a density
    calculation and are skipped here, not zero-filled.
    """
    shells = []
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                shells.append(Shell(
                    shell_id=row["shell_id"],
                    generation=row["generation"],
                    altitude_km=float(row["altitude_km"]),
                    inclination_deg=float(row["inclination_deg"]),
                    orbital_planes=int(row["orbital_planes"]),
                    sats_per_plane=int(row["sats_per_plane"]),
                    status=row["status"],
                ))
            except (ValueError, KeyError):
                continue
    return shells


def ground_track(shell: Shell, n_points: int = 2000, lon0_deg: float = 0.0,
                 duration_s: float | None = None, points_per_orbit: int = 900):
    """A single satellite's ground track (lon, lat) in degrees, Earth-fixed frame.

    duration_s controls how much of the orbit is traced: None (default) traces
    exactly one orbital period. Pass duration_s=86400 to trace a full day -- since
    the orbital period (~95 min) doesn't evenly divide a day, successive passes
    are shifted westward by Earth's rotation and "walk" around the globe, which is
    the real reason a one-day ground track looks like a fan of parallel S-curves
    rather than one repeated line.

    lon0_deg is the arbitrary ascending-node longitude (a visualization choice, not a
    physical constant -- real Starlink planes are spread across many ascending nodes).
    n_points is used only when duration_s is None; otherwise point count scales with
    the number of orbits traced (points_per_orbit) so curve resolution stays constant.
    """
    i = np.radians(shell.inclination_deg)

    if duration_s is None:
        duration_s = shell.period_s
        n = n_points
    else:
        n_orbits = duration_s / shell.period_s
        n = max(int(points_per_orbit * n_orbits), n_points)

    t = np.linspace(0, duration_s, n)
    u = 2 * np.pi * (t / shell.period_s)

    lat = np.degrees(np.arcsin(np.sin(i) * np.sin(u)))
    lam = np.degrees(np.arctan2(np.cos(i) * np.sin(u), np.cos(u)))

    earth_rotation_deg = 360.0 * (t / SIDEREAL_DAY_S)

    lon = lon0_deg + lam - earth_rotation_deg
    lon = ((lon + 180) % 360) - 180  # wrap to [-180, 180]
    return lon, lat


def latitude_density(shell: Shell, n_samples: int = 400_000, bin_width_deg: float = 1.0):
    """Fraction of orbital period spent in each latitude bin (sums to ~1).

    Numeric (Monte Carlo-style dense sampling), not closed-form, to sidestep the
    integrable singularity in the analytic density at the turning points +/- max_lat.
    """
    i = np.radians(shell.inclination_deg)
    u = np.random.default_rng(42).uniform(0, 2 * np.pi, n_samples)
    lat = np.degrees(np.arcsin(np.sin(i) * np.sin(u)))

    edges = np.arange(-90, 90 + bin_width_deg, bin_width_deg)
    counts, _ = np.histogram(lat, bins=edges)
    fractions = counts / n_samples
    centers = (edges[:-1] + edges[1:]) / 2
    return centers, fractions


def expected_sats_by_latitude(shells: list[Shell], bin_width_deg: float = 1.0):
    """Expected instantaneous satellite count per latitude bin, per shell.

    Returns (bin_centers, {shell_id: expected_count_array}). Relies on the ergodic
    equivalence between "one satellite sampled over time" and "many evenly-phased
    satellites in a plane sampled at one instant" -- valid because Starlink planes
    space their satellites evenly in argument of latitude.
    """
    edges = np.arange(-90, 90 + bin_width_deg, bin_width_deg)
    centers = (edges[:-1] + edges[1:]) / 2
    result = {}
    for shell in shells:
        _, frac = latitude_density(shell, bin_width_deg=bin_width_deg)
        result[shell.shell_id] = frac * shell.total_sats
    return centers, result
