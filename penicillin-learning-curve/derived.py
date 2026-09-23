"""The one place derived quantities are computed: annual production (US, world scenarios),
price points on a common $/BU real basis, mid-year cumulative production, and the fits."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

import config as cfg
from model import econ
from model.learning import FitResult, fit_power_law, midyear_cumulative

FIRST_YEAR, LAST_YEAR = 1943, 2025


# --------------------------------------------------------------------------- production ----
def us_production() -> dict[int, float]:
    """US annual penicillin production [BU], 1943-1984 (1984 assumed = 1983, see README)."""
    df = pd.read_csv(cfg.US_PRODUCTION_CSV)
    q: dict[int, float] = {}
    for r in df.itertuples():
        if pd.isna(r.production):
            continue
        q[r.year] = r.production * (cfg.BU_PER_KLB_PRODUCTION if r.unit == "klb" else 1.0)
    # 1949-1951: geometric interpolation between the reported 1948 and 1952 values
    g = (q[1952] / q[1948]) ** (1 / 4)
    for k, year in enumerate((1949, 1950, 1951), start=1):
        q[year] = q[1948] * g ** k
    q[1984] = q[1983]   # 1984 production withheld by the Tariff Commission
    return dict(sorted(q.items()))


def _log_interp(x0, y0, x1, y1, x):
    return math.exp(math.log(y0) + (math.log(y1) - math.log(y0)) * (x - x0) / (x1 - x0))


def world_production(scenario: str = "central") -> dict[int, float]:
    """World annual penicillin (G + V) production [BU] for one anchor scenario.

    1943-1952: US x (world/US ratio), ratio log-interpolated between the 1946 and 1953 anchors.
    1953-1984: reported US + rest of world (RoW), RoW log-interpolated between its 1953 value and
               its 1985 value (1985 world anchor minus US output, US 1985 taken = 1984 = 1983).
               Keeping the reported US series inside the world total guarantees world >= US.
    1985-2025: log-linear interpolation between absolute world anchors (1985, 1995, 2019, 2025).
    """
    col = {"central": "value", "low": "low", "high": "high"}[scenario]
    anchors = pd.read_csv(cfg.WORLD_ANCHORS_CSV).set_index("year")
    us = us_production()
    r46, r53 = anchors.loc[1946, col], anchors.loc[1953, col]

    q: dict[int, float] = {}
    for year in range(FIRST_YEAR, 1953):
        ratio = r46 if year <= 1946 else _log_interp(1946, r46, 1953, r53, year)
        q[year] = us[year] * ratio

    abs_pts = {year: row[col] * cfg.BU_PER_TONNE
               for year, row in anchors.iterrows() if row["unit"] == "t"}
    row53 = us[1953] * (r53 - 1.0)
    row85 = abs_pts[1985] - us[1984]
    for year in range(1953, 1985):
        q[year] = us[year] + _log_interp(1953, row53, 1985, row85, year)

    years = sorted(abs_pts)
    for y0, y1 in zip(years[:-1], years[1:]):
        for year in range(y0, y1 + 1):
            q[year] = _log_interp(y0, abs_pts[y0], y1, abs_pts[y1], year)
    return {y: q[y] for y in range(FIRST_YEAR, LAST_YEAR + 1)}


# ------------------------------------------------------------------------------- prices ----
def _us_price_points() -> pd.DataFrame:
    df = pd.read_csv(cfg.US_PRICES_CSV)
    rows = []
    for r in df.itertuples():
        if r.basis == "quoted":
            if r.quoted_unit == "USD/100k_units":
                nominal = r.quoted_price * 1e9 / 1e5
            elif r.quoted_unit == "USD/lb":
                nominal = r.quoted_price / cfg.BU_PER_LB_1948
            else:
                raise ValueError(r.quoted_unit)
        else:
            qty_bu = r.sales_qty * (cfg.BU_PER_KLB_SALES if r.qty_unit == "klb" else 1.0)
            nominal = r.sales_value_kusd * 1e3 / qty_bu
        in_fit = r.basis != "all_forms" or r.year <= cfg.ALL_FORMS_FIT_CUTOFF_YEAR
        rows.append(dict(year=r.year, region="US", basis=r.basis, nominal=nominal,
                         source=r.source, note=r.note, in_fit=in_fit))
    return pd.DataFrame(rows)


def _world_price_points() -> pd.DataFrame:
    df = pd.read_csv(cfg.WORLD_PRICES_CSV)
    rows = []
    for r in df.itertuples():
        if r.unit == "USD/BOU":
            nominal = r.price
        elif r.unit == "USD/kg":
            nominal = r.price / cfg.BU_PER_KG_K_SALT
        elif r.unit == "CNY/BOU":
            nominal = econ.cny_to_usd(r.price, r.year)
        else:
            raise ValueError(r.unit)
        rows.append(dict(year=r.year, region="World", basis=r.kind, nominal=nominal,
                         source=r.source, note=r.note, in_fit=True))
    return pd.DataFrame(rows)


def price_points() -> pd.DataFrame:
    """Every price observation with real $/BU and the matching mid-year cumulative volumes."""
    df = pd.concat([_us_price_points(), _world_price_points()], ignore_index=True)
    df["real"] = [econ.to_real(p, y, cfg.CPI_BASIS_YEAR) for p, y in zip(df.nominal, df.year)]
    cum_us = midyear_cumulative(us_production())
    df["cum_us"] = df.year.map(cum_us)
    for s in cfg.SCENARIOS:
        df[f"cum_world_{s}"] = df.year.map(midyear_cumulative(world_production(s)))
    return df.sort_values(["year", "region", "basis"]).reset_index(drop=True)


# --------------------------------------------------------------------------------- fits ----
def fits(pts: pd.DataFrame) -> dict[str, FitResult]:
    fit_pts = pts[pts.in_fit]
    us = fit_pts[fit_pts.region == "US"]
    out = {"US price vs US cumulative (1943-1984)": fit_power_law(us.cum_us, us.real)}
    for s in cfg.SCENARIOS:
        out[f"World cumulative, {s} (1943-2024)"] = fit_power_law(
            fit_pts[f"cum_world_{s}"], fit_pts.real)
    for name, (y0, y1) in cfg.ERAS.items():
        seg = fit_pts[(fit_pts.year >= y0) & (fit_pts.year <= y1)]
        out[f"Era: {name}"] = fit_power_law(seg.cum_world_central, seg.real)

    # Robustness: each variant changes ONE choice relative to the central world fit.
    x = "cum_world_central"
    no43 = fit_pts[fit_pts.year != 1943]
    out["Robustness: drop 1943 quote"] = fit_power_law(no43[x], no43.real)
    noq = fit_pts[fit_pts.basis != "quoted"]
    out["Robustness: drop 1943 + 1950 quotes"] = fit_power_law(noq[x], noq.real)
    allf = pts[pts.in_fit | (pts.basis == "all_forms")]
    out["Robustness: include 1952-64 dosage-form values"] = fit_power_law(allf[x], allf.real)
    end_cum = end_of_year_cumulative(world_production("central"))
    out["Robustness: end-of-year cumulative"] = fit_power_law(
        fit_pts.year.map(end_cum), fit_pts.real)
    af = pts[(pts.basis == "all_forms")]
    out["Check: dosage-form series alone (1945-1964, US cum.)"] = fit_power_law(af.cum_us, af.real)
    return out


def end_of_year_cumulative(annual: dict[int, float]) -> dict[int, float]:
    return dict(zip(sorted(annual), np.cumsum([annual[y] for y in sorted(annual)])))


def fit_table(fit_map: dict[str, FitResult]) -> pd.DataFrame:
    rows = []
    for name, f in fit_map.items():
        lo, hi = f.lr_ci
        rows.append(dict(fit=name, n=f.n, b=round(f.b, 4), se_b=round(f.se_b, 4),
                         learning_rate_pct=round(100 * f.lr, 1),
                         lr_ci95_lo_pct=round(100 * lo, 1), lr_ci95_hi_pct=round(100 * hi, 1),
                         r2=round(f.r2, 3)))
    return pd.DataFrame(rows)


def annual_table() -> pd.DataFrame:
    us = us_production()
    world = {s: world_production(s) for s in cfg.SCENARIOS}
    cum = {s: midyear_cumulative(world[s]) for s in cfg.SCENARIOS}
    rows = []
    for y in range(FIRST_YEAR, LAST_YEAR + 1):
        rows.append(dict(year=y, us_BU=us.get(y, np.nan),
                         world_BU_central=world["central"][y], world_BU_low=world["low"][y],
                         world_BU_high=world["high"][y],
                         world_t_central=world["central"][y] / cfg.BU_PER_TONNE,
                         cum_world_mid_BU_central=cum["central"][y]))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.width", 200, "display.max_columns", 20, "display.max_rows", 200)
    pts = price_points()
    print(pts[["year", "region", "basis", "nominal", "real", "cum_us", "cum_world_central",
               "in_fit"]].round(2).to_string())
    print(fit_table(fits(pts)).to_string())
    ann = annual_table()
    for y in (1945, 1953, 1970, 1985, 1995, 2020, 2025):
        tot = ann[ann.year <= y].world_t_central.sum()
        print(f"cumulative world production through {y}: {tot:,.0f} t")
