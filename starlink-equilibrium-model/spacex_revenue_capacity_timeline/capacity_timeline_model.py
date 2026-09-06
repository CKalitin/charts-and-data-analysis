"""Cumulative max Starlink capacity vs. date, from real launch history.

Reads data/starlink_launches_wikipedia_raw.csv (parsed from Wikipedia's "List of
Starlink and Starshield launches", itself sourced from Jonathan McDowell's launch
statistics -- see data/starlink_launch_history.md for the full provenance and
cross-check against McDowell's own aggregate totals).

Only counts satellites from launches with outcome == "Success". Capacity per
satellite is looked up by generation from the main project's own
../data/satellite_capacity.csv (downlink_gbps_total), NOT re-guessed here:
    v1.0, v1.5  -> 20 Gbps
    v2 mini     -> 96 Gbps  (used for every v2-mini variant, DTC-capable or not --
                              no separate DTC throughput figure has ever been
                              published, see starlink_launch_history.md)
    v0.1, v0.9  -> 0 Gbps   (pre-production testbeds, no comms payload; see .md)
    v3          -> 1024 Gbps (defined for completeness -- ZERO v3 satellites have
                              actually reached orbit as of this data pull, so v3
                              never contributes to the historical curve; it exists
                              here only as the conversion factor for the parallel
                              "equivalent V3 satellites" axis)

"Cumulative max capacity" = a running total of launched capacity, NOT net of
deorbits/retirements -- a documented simplification (see .md). Run this file
directly to (re)generate data/cumulative_capacity_vs_date.csv.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
RAW_LAUNCHES_CSV = DATA_DIR / "starlink_launches_wikipedia_raw.csv"
OUT_CSV = DATA_DIR / "cumulative_capacity_vs_date.csv"

# downlink_gbps_total per generation, taken directly from the main project's own
# data/satellite_capacity.csv (not re-derived here).
GBPS_PER_SAT = {
    "v0.1": 0.0,
    "v0.9": 0.0,
    "v1.0": 20.0,
    "v1.5": 20.0,
    "v2_mini": 96.0,
    "v3": 1024.0,
}

V3_GBPS_PER_SAT = GBPS_PER_SAT["v3"]

_SAT_VER_TO_GENERATION = {
    "v0.1": "v0.1",
    "v0.9": "v0.9",
    "v1": "v1.0",
    "v1.5": "v1.5",
    "v2 mini": "v2_mini",
    "v3": "v3",
}


@dataclass
class LaunchEvent:
    launch_date: date
    generation: str
    deployed: int
    capacity_gbps: float


def _parse_date(date_raw: str) -> date:
    # e.g. "22 February 2018, 14:17" or "2 September 2026, 09:35" or "7 January 2020, 02:19:21"
    m = re.match(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", date_raw.strip())
    if not m:
        raise ValueError(f"Unparseable date: {date_raw!r}")
    day, month_name, year = m.groups()
    dt = datetime.strptime(f"{day} {month_name} {year}", "%d %B %Y")
    return dt.date()


def load_launch_events(path: Path = RAW_LAUNCHES_CSV) -> list[LaunchEvent]:
    events: list[LaunchEvent] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["outcome"].strip() != "Success":
                continue
            sat_ver = row["sat_ver"].strip()
            generation = _SAT_VER_TO_GENERATION.get(sat_ver)
            if generation is None:
                raise ValueError(f"Unknown sat_ver: {sat_ver!r}")
            deployed = int(row["deployed"])
            if deployed <= 0:
                continue
            launch_date = _parse_date(row["date_raw"])
            capacity = deployed * GBPS_PER_SAT[generation]
            events.append(LaunchEvent(launch_date, generation, deployed, capacity))
    events.sort(key=lambda e: e.launch_date)
    return events


def build_cumulative_table(events: list[LaunchEvent]) -> list[dict]:
    """One row per launch DATE (same-day launches merged), running cumulative
    totals by generation, total capacity, and the equivalent-V3-satellites
    parallel-axis value (total_capacity_gbps / V3_GBPS_PER_SAT)."""
    by_date: dict[date, list[LaunchEvent]] = {}
    for e in events:
        by_date.setdefault(e.launch_date, []).append(e)

    cum_sats = {gen: 0 for gen in GBPS_PER_SAT}
    cum_capacity_gbps = 0.0
    rows = []
    for d in sorted(by_date):
        for e in by_date[d]:
            cum_sats[e.generation] += e.deployed
            cum_capacity_gbps += e.capacity_gbps
        rows.append({
            "date": d.isoformat(),
            "cum_sats_v0.1": cum_sats["v0.1"],
            "cum_sats_v0.9": cum_sats["v0.9"],
            "cum_sats_v1.0": cum_sats["v1.0"],
            "cum_sats_v1.5": cum_sats["v1.5"],
            "cum_sats_v2_mini": cum_sats["v2_mini"],
            "cum_sats_v3": cum_sats["v3"],
            "cum_sats_total": sum(cum_sats.values()),
            "cum_capacity_gbps": round(cum_capacity_gbps, 1),
            "equivalent_v3_satellites": round(cum_capacity_gbps / V3_GBPS_PER_SAT, 2),
        })
    return rows


def capacity_tbps_at_or_before(rows: list[dict], target: date) -> float:
    """Cumulative max capacity (Tbps) as of the last launch date <= target.
    `rows` is build_cumulative_table()'s output (dates ascending)."""
    best = None
    for r in rows:
        if date.fromisoformat(r["date"]) <= target:
            best = r
        else:
            break
    if best is None:
        return 0.0
    return best["cum_capacity_gbps"] / 1000.0


def write_cumulative_csv(rows: list[dict], path: Path = OUT_CSV) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    events = load_launch_events()
    rows = build_cumulative_table(events)
    write_cumulative_csv(rows)
    last = rows[-1]
    print(f"{len(events)} successful launch-events, {len(rows)} distinct launch dates")
    print(f"Latest ({last['date']}): {last['cum_sats_total']:,} satellites, "
          f"{last['cum_capacity_gbps']:,.0f} Gbps cumulative capacity "
          f"= {last['equivalent_v3_satellites']:,.0f} equivalent V3 satellites")
    print(f"Wrote {path if (path := OUT_CSV) else OUT_CSV}")
