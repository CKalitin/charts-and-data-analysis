"""Phase 4 (revised): total cost-to-orbit per Gbps of delivered capacity, per
Starlink generation. User's explicit decisions, recorded here so they aren't
re-litigated:

  - Cost metric: $/Gbps, not $/satellite ("$/Gbps. Hard stop.").
  - Launch cost pairing: F9 (SpaceX's own internal marginal cost, not the rideshare
    price external customers pay -- Starlink IS SpaceX) for the F9-launched
    generations (v1.0, v1.5, v2 Mini); Starship for v3, in TWO scenarios --
    "initial" (conservative near-term estimate) and "end-state" (SpaceX's
    aspirational target, not yet achieved).
  - Manufacturing cost: use the LATEST known figure per generation, not an average
    or a continuous model (v2 Mini therefore uses the 2026 ~$400K point, not the
    2024 $800K point -- see data/starlink_satellite_cost.md for why both exist).
  - Required margin: 20%.

v2_full is EXCLUDED throughout -- no published capacity (Gbps) figure was found for
it in any research pass, and $/Gbps cannot be computed without one. Not estimated,
not guessed; see data/starlink_satellite_cost.md.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
MARGIN = 0.20  # user decision, 2026-08-09


@dataclass(frozen=True)
class GenerationEconomics:
    generation: str
    label: str
    mfg_cost_usd: float
    mass_kg: float
    downlink_gbps: float
    launch_scenario: str
    launch_usd_per_kg: float

    @property
    def launch_cost_usd(self) -> float:
        return self.mass_kg * self.launch_usd_per_kg

    @property
    def total_cost_usd(self) -> float:
        return self.mfg_cost_usd + self.launch_cost_usd

    @property
    def cost_per_gbps_usd(self) -> float:
        return self.total_cost_usd / self.downlink_gbps

    @property
    def cost_per_gbps_with_margin_usd(self) -> float:
        return self.cost_per_gbps_usd * (1 + MARGIN)


def _load_latest_mfg_cost() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with open(DATA / "starlink_satellite_cost.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            gen = r["generation"]
            if gen not in rows or r["as_of_date"] > rows[gen]["as_of_date"]:
                rows[gen] = r
    return rows


def _load_capacity() -> dict[str, float]:
    out = {}
    with open(DATA / "satellite_capacity.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["downlink_gbps_total"]:
                out[r["generation"]] = float(r["downlink_gbps_total"])
    return out


def _load_launch_scenarios() -> dict[str, float]:
    out = {}
    with open(DATA / "launch_cost_scenarios.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["scenario"]] = float(r["usd_per_kg"])
    return out


def build_generation_economics() -> list[GenerationEconomics]:
    mfg = _load_latest_mfg_cost()
    cap = _load_capacity()
    launch = _load_launch_scenarios()

    # (generation key in cost CSV, generation key in capacity CSV, display label, launch scenario)
    # v1.5 excluded, same reason as v2_full: no independently-published capacity
    # figure exists for it -- it was reusing v1.0's 20 Gbps number, which made it
    # look more expensive per Gbps than v1.0 purely because its higher mass adds
    # launch cost with no corresponding capacity credit. That's a data-availability
    # artifact, not a real cost result, so don't compute or chart it at all.
    plan = [
        ("v1.0", "v1.0", "v1.0", "f9_internal_marginal"),
        ("v2_mini", "v2_mini", "v2 Mini", "f9_internal_marginal"),
        ("v3", "v3_broadband", "v3 (Starship initial)", "starship_initial"),
        ("v3", "v3_broadband", "v3 (Starship end-state)", "starship_endstate"),
    ]

    results = []
    for cost_key, cap_key, label, scenario in plan:
        if cap_key not in cap:
            continue  # v2_full has no capacity figure -- skip, don't estimate
        c = mfg[cost_key]
        results.append(GenerationEconomics(
            generation=cost_key, label=label,
            mfg_cost_usd=float(c["unit_cost_usd"]), mass_kg=float(c["mass_kg"]),
            downlink_gbps=cap[cap_key], launch_scenario=scenario,
            launch_usd_per_kg=launch[scenario],
        ))
    return results
