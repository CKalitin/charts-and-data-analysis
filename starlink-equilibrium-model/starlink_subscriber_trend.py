"""Extrapolates Starlink subscriber counts to a target date from real, dated
milestone announcements (data/starlink_subscriber_milestones.csv), per generation
countries where SpaceX/regulators have published at least two dated data points.

Method: geometric (constant daily growth rate) interpolation/extrapolation between
the two most recent real anchors for a given scope. This is the standard way to
extrapolate a growing-adoption curve over a SHORT horizon (weeks to a few months)
without assuming a full logistic/S-curve model -- it will overstate growth if
extrapolated far past the anchors or through a genuine slowdown, so every result
carries the anchor dates and implied daily rate so a reader can judge how far the
extrapolation is being pushed.

NOT used: extrapolating a market's EARLY hyper-growth rate (e.g. Nigeria's first
9 months, 2023-12 to 2024-09, ~11.6%/month) over a multi-year horizon -- early-market
percentage growth from a tiny base is not sustained, and doing so would produce an
absurd result. Always prefer the two MOST RECENT anchors for a given scope, which
better reflect current (slower, more mature) growth than the earliest ones.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

MILESTONES_CSV = Path(__file__).resolve().parent / "data" / "starlink_subscriber_milestones.csv"


@dataclass(frozen=True)
class Milestone:
    scope: str
    iso3: str | None
    d: date
    value: float
    source: str
    source_type: str


def load_milestones(csv_path: Path = MILESTONES_CSV) -> list[Milestone]:
    out = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            y, m, d = map(int, r["date"].split("-"))
            out.append(Milestone(
                scope=r["scope"], iso3=r["iso3"] or None, d=date(y, m, d),
                value=float(r["value"]), source=r["source"], source_type=r["source_type"],
            ))
    return out


def daily_growth_rate(v0: float, d0: date, v1: float, d1: date) -> float:
    """Constant daily geometric growth rate implied by two anchors (v1 later than v0)."""
    days = (d1 - d0).days
    if days <= 0 or v0 <= 0:
        raise ValueError("anchors must be chronological with a positive starting value")
    return math.log(v1 / v0) / days


def extrapolate(v_anchor: float, d_anchor: date, daily_rate: float, target: date) -> float:
    days = (target - d_anchor).days
    return v_anchor * math.exp(daily_rate * days)


def estimate_current(scope: str, target: date, milestones: list[Milestone] | None = None,
                     exclude_forecasts: bool = True):
    """Extrapolate to `target` using the two most recent REAL (non-forecast) anchors
    for `scope`. Returns (estimate, anchor0, anchor1, daily_rate) so the caller can
    report the method alongside the number -- never return a bare float from this."""
    milestones = milestones or load_milestones()
    rows = [m for m in milestones if m.scope == scope]
    if exclude_forecasts:
        rows = [m for m in rows if m.source_type != "analyst_forecast_not_actual"]
    rows.sort(key=lambda m: m.d)
    if len(rows) < 2:
        raise ValueError(f"need >=2 real anchors for scope={scope!r}, found {len(rows)}")
    a0, a1 = rows[-2], rows[-1]
    rate = daily_growth_rate(a0.value, a0.d, a1.value, a1.d)
    est = extrapolate(a1.value, a1.d, rate, target)
    return est, a0, a1, rate


def global_value_at(target: date, milestones: list[Milestone] | None = None) -> float:
    """Global subscriber count at any date: geometrically INTERPOLATE between the two
    real anchors bracketing `target` if it falls within the anchor timeline (more
    accurate than extrapolating from the wrong end), or EXTRAPOLATE from the last two
    anchors if `target` is beyond all of them."""
    milestones = milestones or load_milestones()
    rows = sorted((m for m in milestones if m.scope == "global"
                  and m.source_type != "analyst_forecast_not_actual"), key=lambda m: m.d)
    before = [m for m in rows if m.d <= target]
    after = [m for m in rows if m.d >= target]
    if before and after and before[-1].d != after[0].d:
        a0, a1 = before[-1], after[0]
    elif before and after:  # exact match
        return before[-1].value
    else:
        a0, a1 = rows[-2], rows[-1]
    rate = daily_growth_rate(a0.value, a0.d, a1.value, a1.d)
    return extrapolate(a1.value, a1.d, rate, target)


def estimate_via_global_relative_growth(country_value: float, country_date: date,
                                        target: date, milestones: list[Milestone] | None = None):
    """For scopes with only ONE real anchor (e.g. Brazil): scale that single anchor
    by the GLOBAL relative growth between the anchor's date and the target date.
    This is a materially weaker assumption than estimate_current() -- it assumes the
    country tracks the average global growth rate, which may not hold (flag this to
    the reader; a fast-growing market like Brazil could easily be a floor, not a
    point estimate -- see data/starlink_subscribers.md)."""
    milestones = milestones or load_milestones()
    ratio = global_value_at(target, milestones) / global_value_at(country_date, milestones)
    return country_value * ratio


def estimate_via_ookla_share(share_pct: float, target: date, milestones: list[Milestone] | None = None) -> float:
    """For countries with only an Ookla 'share of Starlink's global Speedtest
    samples' figure (no direct subscriber count): share% x global subscribers at
    `target`. ASSUMES the country's share of samples has stayed constant since the
    report date AND that sample share approximates subscriber share -- the second
    assumption is checked (and found imperfect) against the US in
    data/starlink_subscribers.md; treat these estimates as directional, not precise."""
    milestones = milestones or load_milestones()
    return (share_pct / 100.0) * global_value_at(target, milestones)
