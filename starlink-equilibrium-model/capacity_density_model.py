"""Phase 3: satellite capacity & customer density constraints.

Reproduces the methodology in data/satellite_capacity.md (Meinrath, Grindal, Fishbine
& DeGidio, "Starlink Capacity Analysis v0.2," X-Lab/Penn State, July 2025) as
parameterized pure functions rather than a hand-derived one-off result, so a
different assumption set (beamwidth, altitude, contention ratio, min speed) can be
re-run instead of requiring new arithmetic.

Two DISTINCT, independent constraints, both required (per CLAUDE.md):
  1. Max customers per satellite -- a hard cap on total simultaneous subscribers a
     single satellite's beams can support.
  2. Max customer DENSITY -- a hard cap on subscribers per unit area within a single
     beam's footprint, independent of how many satellites are overhead (Phase 2's
     question). A latitude band can have plenty of satellite coverage (Phase 2) and
     still be locally oversaturated if population density exceeds this ceiling.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CapacityScenario:
    """One fully-specified assumption set. Every field is a documented, citable
    assumption (see data/satellite_capacity.md), not a physical constant."""
    label: str
    downlink_gbps_per_beam: float
    uplink_gbps_per_beam: float
    beams_per_satellite: int
    altitude_km: float
    beamwidth_deg: float
    contention_ratio: float          # e.g. 20 -> 20:1 oversubscription
    min_download_gbps: float         # regulatory/quality threshold, e.g. 0.1 = 100 Mbps
    min_upload_gbps: float           # e.g. 0.02 = 20 Mbps


# The only fully-derived scenario found in public research (v2 Mini, 550 km,
# 1.5 deg beamwidth, 20:1 contention, US BEAD 100/20 Mbps threshold).
V2_MINI_BEAD_SCENARIO = CapacityScenario(
    label="v2_mini_550km_1.5deg_20to1_100-20mbps",
    downlink_gbps_per_beam=6.0,
    uplink_gbps_per_beam=0.419,
    beams_per_satellite=16,
    altitude_km=550.0,
    beamwidth_deg=1.5,
    contention_ratio=20.0,
    min_download_gbps=0.1,
    min_upload_gbps=0.02,
)


def beam_footprint_area_km2(altitude_km: float, beamwidth_deg: float) -> float:
    """Circular nadir footprint area. A = pi * (tan(beamwidth/2) * altitude)^2."""
    half_angle = np.radians(beamwidth_deg / 2)
    radius_km = np.tan(half_angle) * altitude_km
    return np.pi * radius_km ** 2


def max_subscribers_per_beam(scenario: CapacityScenario, dedicated: bool = False):
    """Returns (download_limited, upload_limited, binding) subscriber counts per beam.

    dedicated=True: no contention (every subscriber gets a guaranteed allocation).
    dedicated=False (default): scenario.contention_ratio applied (industry-standard
    oversubscription assumption -- see data/satellite_capacity.md).
    """
    dl = scenario.downlink_gbps_per_beam / scenario.min_download_gbps
    ul = scenario.uplink_gbps_per_beam / scenario.min_upload_gbps
    mult = 1.0 if dedicated else scenario.contention_ratio
    dl, ul = dl * mult, ul * mult
    binding = "download" if dl < ul else "upload"
    return dl, ul, binding


def max_customer_density_per_km2(scenario: CapacityScenario, dedicated: bool = False) -> float:
    """Max subscribers per km^2 within one beam's footprint before saturation."""
    dl, ul, _ = max_subscribers_per_beam(scenario, dedicated=dedicated)
    binding_count = min(dl, ul)
    area = beam_footprint_area_km2(scenario.altitude_km, scenario.beamwidth_deg)
    return binding_count / area


def max_customers_per_satellite(scenario: CapacityScenario, dedicated: bool = False) -> float:
    dl, ul, _ = max_subscribers_per_beam(scenario, dedicated=dedicated)
    return min(dl, ul) * scenario.beams_per_satellite


def max_customers_per_shell(scenario: CapacityScenario, total_satellites: int, dedicated: bool = False) -> float:
    """Naive upper bound: per-satellite cap x satellite count. Ignores overlap between
    adjacent satellites' footprints (real coverage overlaps considerably at these
    altitudes/beamwidths) -- an UPPER bound, not a precise total."""
    return max_customers_per_satellite(scenario, dedicated=dedicated) * total_satellites
