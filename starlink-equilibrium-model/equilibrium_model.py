"""Phase 5: the core equilibrium model.

Mechanism (see CLAUDE.md): revenue per additional unit of capacity falls with
diminishing returns as cheaper capacity reaches progressively less valuable demand;
satellite cost + margin is flat. Where they cross is the equilibrium.

Adapted to the user's Phase 4 decision that cost is measured in $/Gbps, not
$/satellite: the x-axis here is CUMULATIVE GBPS OF CAPACITY DEPLOYED, not satellite
count directly -- because $/satellite differs by generation (a satellite is a
different amount of capacity in each generation), a single revenue-vs-satellite-count
curve would not mean the same thing across generations, while a revenue-vs-Gbps
curve does. Satellite count per generation is then `equilibrium_gbps /
gbps_per_satellite(generation)` -- reported alongside every equilibrium point, not
dropped.

Demand-side construction, per country:
  - ARPU proxy = the LOCAL incumbent monthly price for the dominant access mode
    (fixed broadband $/month, or mobile $/month if `cellular_dominant_market`) --
    what Starlink would need to approach to win share, and what it could plausibly
    capture per customer.
  - Addressable customers = min(coverage-corrected unconnected population,
    land_area_km2 x Phase 3's density ceiling). The density cap is REQUIRED per the
    user's explicit earlier instruction -- for high-population-density countries
    (India, Nigeria, China) this binds well below their raw unconnected population,
    which is the whole point of Phase 3's finding.
  - Coverage gate: countries whose capital latitude exceeds Gen1's max covered
    latitude (~82.4 deg) are excluded. In practice this excludes ~nothing (no
    populated country's capital sits that far poleward) -- included for
    completeness/correctness, not because it binds.

Countries are ranked by ARPU descending (highest-value demand served first, by
construction: whoever would pay the most is the most profitable to serve first, and
each additional satellite of capacity has to reach into progressively cheaper
markets to keep growing) and walked cumulatively to build a revenue-per-Gbps step
curve. See ASSUMPTIONS below for the specific numbers this depends on.

ASSUMPTIONS requiring user confirmation, clearly flagged, NOT silently chosen:
  - SATELLITE_LIFETIME_YEARS = 5: commonly cited Starlink design life. Needed to
    annualize the one-time cost-to-orbit ($/Gbps) so it's comparable to recurring
    monthly ARPU revenue. Changing this shifts every equilibrium point.
  - CUSTOMERS_PER_GBPS is derived from Phase 3's v2-Mini-specific density scenario
    (6,704 customers / 96 Gbps = ~69.8 customers/Gbps) and applied to EVERY
    generation, assuming beam/contention characteristics scale proportionally with
    raw capacity. Not verified for v1.0 or v3 specifically -- a real assumption.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

SATELLITE_LIFETIME_YEARS = 5.0  # ASSUMPTION -- see module docstring, confirm with user
ARPU_CAP_USD_MONTH = 100.0  # ASSUMPTION -- caps a handful of implausible outlier prices
# (e.g. Zimbabwe, Turkmenistan, Syria showing $150-440/mo from thin survey samples --
# already-documented "small sample size skews the average" limitation in
# telecom_market_by_country.md) at just above the US's own real $80/mo, the highest
# PLAUSIBLE price point in the dataset. Without this cap, 1-2 outlier countries with
# bad survey data would dominate the top of the revenue ranking and distort the whole
# equilibrium calculation. Flagged as a modeling choice, not a data correction.
DENSITY_CAP_PER_KM2 = 2.5726693638587732  # Phase 3: v2 Mini, 20:1 contention, upload-limited (see capacity_density_model.py)
CUSTOMERS_PER_GBPS = 6704 / 96.0  # Phase 3 v2-Mini ratio, applied to all generations -- ASSUMPTION
MAX_COVERAGE_LAT_DEG = 82.4  # Gen1 near-polar shell's max latitude (see starlink_shells.md)


@dataclass(frozen=True)
class CountryDemand:
    country: str
    iso3: str
    arpu_usd_month: float
    addressable_customers: float
    gbps_needed: float
    binding_constraint: str  # "population" or "density"
    arpu_capped: bool = False


def _load_land_area() -> dict[str, float]:
    d = json.load(open(DATA / "raw" / "wb_AG.LND.TOTL.K2.json", encoding="utf-8"))[1]
    return {r["countryiso3code"]: r["value"] for r in d if r["value"]}


def _load_capitals() -> dict[str, float]:
    out = {}
    for c in json.load(open(DATA / "raw" / "wb_countries.json", encoding="utf-8"))[1]:
        if c["region"]["id"] == "NA":
            continue
        if c.get("latitude"):
            out[c["id"]] = float(c["latitude"])
    return out


def build_country_demand(income_cap_pct: float | None = None, income_basis: str = "gni") -> list[CountryDemand]:
    """income_cap_pct=None (default): the original flat ARPU_CAP_USD_MONTH=100 cap.
    income_cap_pct=X: replaces the flat cap with a PER-COUNTRY cap of X% of that
    country's own monthly per-capita income (income_basis="gni" or "gdp") -- see
    charts/affordability.py, built to explore this as an alternative to the flat
    dollar cap flagged in ASSUMPTIONS.md #4 (which let a handful of countries with
    bad survey data rank at the very top of the ARPU ranking, ahead of every real
    high-income market). A country with no per-capita income figure available falls
    back to the flat ARPU_CAP_USD_MONTH cap rather than going uncapped."""
    land_area = _load_land_area()
    capitals = _load_capitals()

    rows = []
    with open(DATA / "telecom_market_by_country.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    out = []
    for r in rows:
        iso3 = r["iso3"]
        lat = capitals.get(iso3)
        if lat is None or abs(lat) > MAX_COVERAGE_LAT_DEG:
            continue  # coverage-gated (in practice, excludes ~nothing)

        try:
            unconnected = float(r["unconnected_population_est_coverage_corrected"])
        except (ValueError, KeyError):
            continue
        if unconnected <= 0:
            continue

        area = land_area.get(iso3)
        cellular_dominant = r["cellular_dominant_market"] == "True"
        bb_month = r["fixed_broadband_usd_per_month"]
        mob_month = r["mobile_usd_per_month_illustrative"]

        if cellular_dominant and mob_month:
            arpu = float(mob_month)
        elif bb_month:
            arpu = float(bb_month)
        elif mob_month:
            arpu = float(mob_month)
        else:
            continue  # no pricing data at all -- can't rank this country, skip
        if arpu <= 0:
            continue

        if income_cap_pct is None:
            cap = ARPU_CAP_USD_MONTH
        else:
            income_field = "gni_per_capita_ppp_usd" if income_basis == "gni" else "gdp_per_capita_ppp_usd"
            income_pc = r.get(income_field)
            cap = (income_cap_pct / 100.0) * (float(income_pc) / 12.0) if income_pc else ARPU_CAP_USD_MONTH
        capped = arpu > cap
        arpu = min(arpu, cap)

        if area:
            density_ceiling = area * DENSITY_CAP_PER_KM2
            if density_ceiling < unconnected:
                addressable = density_ceiling
                binding = "density"
            else:
                addressable = unconnected
                binding = "population"
        else:
            addressable = unconnected
            binding = "population_no_area_data"

        out.append(CountryDemand(
            country=r["country"], iso3=iso3, arpu_usd_month=arpu,
            addressable_customers=addressable,
            gbps_needed=addressable / CUSTOMERS_PER_GBPS,
            binding_constraint=binding, arpu_capped=capped,
        ))

    out.sort(key=lambda c: -c.arpu_usd_month)
    return out


def build_revenue_curve(demand: list[CountryDemand]):
    """Step curve: (cumulative_gbps, revenue_per_gbps_annual_usd) at each country's
    entry point, ranked by ARPU descending. revenue_per_gbps_annual_usd is that
    country's own ARPU-implied annual revenue rate per Gbps of capacity -- constant
    within a country's segment, stepping down at each new country."""
    cum_gbps = 0.0
    points = []  # (cum_gbps_start, cum_gbps_end, revenue_per_gbps_annual)
    for c in demand:
        revenue_per_gbps_annual = c.arpu_usd_month * 12 * CUSTOMERS_PER_GBPS
        points.append((cum_gbps, cum_gbps + c.gbps_needed, revenue_per_gbps_annual, c))
        cum_gbps += c.gbps_needed
    return points


def find_equilibrium(revenue_points, cost_per_gbps_annual: float):
    """Walk the step curve to find where revenue/Gbps drops to the cost/Gbps line.
    Returns (equilibrium_gbps, n_countries_served, last_country) or None if even the
    single highest-ARPU country's revenue never reaches the cost line."""
    if not revenue_points or revenue_points[0][2] < cost_per_gbps_annual:
        return None
    served = 0
    equilibrium_gbps = 0.0
    for start, end, rev, c in revenue_points:
        if rev < cost_per_gbps_annual:
            break
        equilibrium_gbps = end
        served += 1
    return equilibrium_gbps, served


def market_size_usd(revenue_points, equilibrium_gbps: float) -> float:
    """Total ANNUAL revenue captured by serving up to equilibrium_gbps of capacity."""
    total = 0.0
    for start, end, rev, c in revenue_points:
        if start >= equilibrium_gbps:
            break
        seg = min(end, equilibrium_gbps) - start
        total += seg * rev
    return total


def sweep_cost_curve(revenue_points, cost_values_annual):
    """Phase 6: the CONTINUOUS cost-vs-market-size curve -- run find_equilibrium() +
    market_size_usd() across a swept range of cost/Gbps/year values, not just the 4
    discrete generation points. Returns a list of (cost_annual, equilibrium_gbps,
    market_size_usd, n_countries) -- skips costs above the best available market
    (no equilibrium exists there)."""
    out = []
    for cost_annual in cost_values_annual:
        result = find_equilibrium(revenue_points, cost_annual)
        if result is None:
            continue
        eq_gbps, n = result
        market = market_size_usd(revenue_points, eq_gbps)
        out.append((cost_annual, eq_gbps, market, n))
    return out
