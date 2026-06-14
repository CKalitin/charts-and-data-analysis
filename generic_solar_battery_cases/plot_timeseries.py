"""Annual time series for a specific solar + battery configuration.

Aggregates the 10-minute NSRDB dispatch to daily values for a clean
year-at-a-glance view.

Plots (individual PNGs + combined 4-panel):
  1. GHI                       (kWh/m²/day)
  2. Solar array production    (kWh/day)
  3. Battery state of charge   (mean kWh over each day)
  4. Load energy served        (kWh/day, unmet shaded)

Outputs (output/):
    ts_ghi.png
    ts_solar_production.png
    ts_battery_soc.png
    ts_load_served.png
    ts_combined.png

Run:  python plot_timeseries.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import plotting
import solar_battery_core as sbc

# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
DATA_FILE = Path(__file__).with_name("nsrdb_data") / "nsrdb_836224_2024.csv"

LOAD_KW = 1.0
KW_SOLAR = 50       # solar array size to simulate
KWH_BATTERY = 50.0   # battery capacity to simulate


# --------------------------------------------------------------------------- #
# Daily aggregation
# --------------------------------------------------------------------------- #
def _daily(ts: sbc.TimeseriesResult) -> pd.DataFrame:
    """Return a DataFrame with daily aggregated columns, indexed by date."""
    idx = ts.timestamps

    ghi_kwh_m2 = ts.ghi_w_m2 * ts.dt_hours / 1000.0   # W/m² → kWh/m² per step

    df = pd.DataFrame(
        {
            "ghi":       ghi_kwh_m2,
            "gen":       ts.gen_kw * ts.dt_hours,          # kWh per step
            "curtailed": ts.curtailed_kwh,
            "served":    ts.served_kwh,
            "unmet":     ts.unmet_kwh,
            "load":      ts.load_kwh,
            "soc":       ts.soc_kwh,
        },
        index=idx,
    )

    has_data = df.resample("D").count()["ghi"] > 0
    return pd.DataFrame(
        {
            "ghi_kwh_m2":     df["ghi"].resample("D").sum(),
            "gen_kwh":        df["gen"].resample("D").sum(),
            "curtailed_kwh":  df["curtailed"].resample("D").sum(),
            "soc_kwh_mean":   df["soc"].resample("D").mean(),
            "served_kwh":     df["served"].resample("D").sum(),
            "unmet_kwh":      df["unmet"].resample("D").sum(),
            "load_kwh":       df["load"].resample("D").sum(),
        }
    )[has_data]


# --------------------------------------------------------------------------- #
# Chart style helpers
# --------------------------------------------------------------------------- #
_MONTH_FMT = mdates.DateFormatter("%b")
_MONTH_LOC = mdates.MonthLocator()

_COLOR_GHI        = "#f5a623"
_COLOR_SOLAR      = "#4a90d9"
_COLOR_CURTAILED  = "#e8a000"
_COLOR_SOC        = "#7ed321"
_COLOR_SERVED     = "#417505"
_COLOR_UNMET      = "#d0021b"


def _format_date_axis(ax) -> None:
    ax.xaxis.set_major_locator(_MONTH_LOC)
    ax.xaxis.set_major_formatter(_MONTH_FMT)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.grid(axis="y", linestyle="--", alpha=0.3)


def _param_lines(ts: sbc.TimeseriesResult, data: sbc.NsrdbData) -> list[str]:
    yearly, daily = sbc.solar_resource_kwh_m2(data)
    total_served = ts.served_kwh.sum()
    total_load = ts.load_kwh.sum()
    util = total_served / total_load if total_load > 0 else 0.0
    return [
        f"Site   : NSRDB {DATA_FILE.stem.split('_')[1]} ({data.timestamps[0].year})",
        f"Solar resource (kWh/m²): {yearly:,.0f} / year, {daily:.1f} / day",
        f"Config : {ts.kw_solar:g} kW solar + {ts.kwh_battery_capacity:g} kWh battery",
        f"Load   : {ts.load_kw:g} kW constant  |  Utilization: {util:.1%}",
    ]


# --------------------------------------------------------------------------- #
# Individual chart functions
# --------------------------------------------------------------------------- #
def plot_ghi(daily: pd.DataFrame, data: sbc.NsrdbData, ts: sbc.TimeseriesResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.fill_between(daily.index, daily["ghi_kwh_m2"], color=_COLOR_GHI, alpha=0.7)
    ax.set_ylabel("GHI (kWh/m²/day)")
    ax.set_title("Global Horizontal Irradiance")
    _format_date_axis(ax)
    plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(ts, data), bottom_frac=0.22)
    return fig


def plot_solar_production(daily: pd.DataFrame, data: sbc.NsrdbData, ts: sbc.TimeseriesResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    useful = daily["gen_kwh"] - daily["curtailed_kwh"]
    ax.fill_between(daily.index, daily["gen_kwh"], useful,
                    color=_COLOR_CURTAILED, alpha=0.8, label="Curtailed (battery full)")
    ax.fill_between(daily.index, useful,
                    color=_COLOR_SOLAR, alpha=0.7, label="Used (load + battery charge)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_ylabel("Energy (kWh/day)")
    ax.set_title(f"Solar Array Production  ({ts.kw_solar:g} kW)")
    _format_date_axis(ax)
    plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(ts, data), bottom_frac=0.22)
    return fig


def plot_battery_soc(daily: pd.DataFrame, data: sbc.NsrdbData, ts: sbc.TimeseriesResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.fill_between(daily.index, daily["soc_kwh_mean"], color=_COLOR_SOC, alpha=0.7)
    ax.axhline(ts.kwh_battery_capacity, color="gray", linewidth=0.8,
               linestyle="--", label=f"Capacity ({ts.kwh_battery_capacity:g} kWh)")
    ax.set_ylabel("SOC (kWh)")
    ax.set_title(f"Battery State of Charge  ({ts.kwh_battery_capacity:g} kWh capacity, daily mean)")
    ax.legend(loc="upper right", fontsize=8)
    _format_date_axis(ax)
    plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(ts, data), bottom_frac=0.22)
    return fig


def plot_load_served(daily: pd.DataFrame, data: sbc.NsrdbData, ts: sbc.TimeseriesResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.fill_between(daily.index, daily["load_kwh"],
                    color=_COLOR_UNMET, alpha=0.4, label="Unmet demand")
    ax.fill_between(daily.index, daily["served_kwh"],
                    color=_COLOR_SERVED, alpha=0.8, label="Served")
    ax.set_ylabel("Energy (kWh/day)")
    ax.set_title(f"Load Energy Served  ({ts.load_kw:g} kW constant demand)")
    ax.legend(loc="lower right", fontsize=8)
    _format_date_axis(ax)
    plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(ts, data), bottom_frac=0.22)
    return fig


# --------------------------------------------------------------------------- #
# Combined 4-panel
# --------------------------------------------------------------------------- #
def plot_combined(daily: pd.DataFrame, data: sbc.NsrdbData, ts: sbc.TimeseriesResult) -> plt.Figure:
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    ax_ghi, ax_sol, ax_soc, ax_load = axes

    ax_ghi.fill_between(daily.index, daily["ghi_kwh_m2"], color=_COLOR_GHI, alpha=0.7)
    ax_ghi.set_ylabel("GHI\n(kWh/m²/day)")
    ax_ghi.set_title("Global Horizontal Irradiance")

    _useful = daily["gen_kwh"] - daily["curtailed_kwh"]
    ax_sol.fill_between(daily.index, daily["gen_kwh"], _useful,
                        color=_COLOR_CURTAILED, alpha=0.8, label="Curtailed")
    ax_sol.fill_between(daily.index, _useful,
                        color=_COLOR_SOLAR, alpha=0.7, label="Used")
    ax_sol.legend(loc="upper right", fontsize=8)
    ax_sol.set_ylabel("Production\n(kWh/day)")
    ax_sol.set_title(f"Solar Array Production  ({ts.kw_solar:g} kW)")

    ax_soc.fill_between(daily.index, daily["soc_kwh_mean"], color=_COLOR_SOC, alpha=0.7)
    ax_soc.axhline(ts.kwh_battery_capacity, color="gray", linewidth=0.8, linestyle="--",
                   label=f"Capacity ({ts.kwh_battery_capacity:g} kWh)")
    ax_soc.set_ylabel("SOC\n(kWh)")
    ax_soc.set_title(f"Battery State of Charge  ({ts.kwh_battery_capacity:g} kWh, daily mean)")
    ax_soc.legend(loc="upper right", fontsize=8)

    ax_load.fill_between(daily.index, daily["load_kwh"],
                         color=_COLOR_UNMET, alpha=0.4, label="Unmet demand")
    ax_load.fill_between(daily.index, daily["served_kwh"],
                         color=_COLOR_SERVED, alpha=0.8, label="Served")
    ax_load.set_ylabel("Load\n(kWh/day)")
    ax_load.set_title(f"Load Energy Served  ({ts.load_kw:g} kW constant demand)")
    ax_load.legend(loc="lower right", fontsize=8)

    for ax in axes:
        _format_date_axis(ax)
        plotting.add_watermark(ax)

    plotting.add_param_box_below(fig, _param_lines(ts, data), bottom_frac=0.08)
    return fig


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    data = sbc.load_nsrdb_csv(DATA_FILE)
    yearly, daily_res = sbc.solar_resource_kwh_m2(data)
    print(
        f"Loaded {DATA_FILE.name}: {data.n_steps} samples  |  "
        f"solar {yearly:.0f} kWh/m²/yr, {daily_res:.1f} kWh/m²/day\n"
    )

    print(f"Running dispatch: {KW_SOLAR} kW solar + {KWH_BATTERY} kWh battery ...")
    ts = sbc.dispatch_timeseries(data, KW_SOLAR, KWH_BATTERY, LOAD_KW)
    util = ts.served_kwh.sum() / ts.load_kwh.sum()
    print(f"Annual utilization: {util:.1%}\n")

    daily = _daily(ts)

    tag = f"sol{KW_SOLAR:g}kW_bat{KWH_BATTERY:g}kWh_load{LOAD_KW:g}kW"

    charts = [
        (plot_ghi(daily, data, ts),              f"{tag}_ghi.png"),
        (plot_solar_production(daily, data, ts), f"{tag}_solar_production.png"),
        (plot_battery_soc(daily, data, ts),      f"{tag}_battery_soc.png"),
        (plot_load_served(daily, data, ts),      f"{tag}_load_served.png"),
        (plot_combined(daily, data, ts),         f"{tag}_combined.png"),
    ]
    for fig, name in charts:
        path = plotting.save_figure(fig, name, subdir="timeseries")
        print(f"Saved -> {path.relative_to(Path(__file__).parent)}")
        plt.close(fig)


if __name__ == "__main__":
    main()
