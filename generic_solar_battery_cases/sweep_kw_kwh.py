"""Sweep kW solar x kWh battery and plot net value and utilization heatmaps.

    y-axis : kW solar       (0 -> 10, 0.5 kW steps)
    x-axis : kWh battery    (0 -> 50, 1 kWh steps)

Outputs (all to output/):
    sweep_kw_kwh_net_value.png    -- income minus capex ($)
    sweep_kw_kwh_utilization.png  -- fraction of annual load served (%)
    sweep_kw_kwh_combined.png     -- both side by side

Run:  python sweep_kw_kwh.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

import plotting
import solar_battery_core as sbc

# --------------------------------------------------------------------------- #
# Inputs -- edit freely.
# --------------------------------------------------------------------------- #
DATA_FILE = Path(__file__).with_name("nsrdb_data") / "nsrdb_836224_2024.csv"

LOAD_KW = 1.0

COST = sbc.CostParams(
    gen_per_kw=100.0,            # $ / kW solar
    storage_per_kwh=100.0,       # $ / kWh battery
    load_per_kw=100.0,          # $ / kW load (one-time capex)
    load_value_per_kwh=10.0,     # $ / kWh delivered to load (income)
)

KW_SOLAR = sbc.arange_inclusive(0.0, 150.0, 1)   # y-axis
KWH_BATTERY = sbc.arange_inclusive(0.0, 150.0, 1)  # x-axis

REPORT_UTILIZATION_TARGETS = (0.90, 0.95, 0.99, 0.999)


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _param_lines(data: sbc.NsrdbData, cost: sbc.CostParams) -> list[str]:
    yearly, daily = sbc.solar_resource_kwh_m2(data)
    return [
        f"Site         : NSRDB {DATA_FILE.stem.split('_')[1]} ({data.timestamps[0].year})",
        f"Solar resource (kWh/m²): {yearly:,.0f} / year, {daily:.1f} / day",
        f"Load         : {LOAD_KW:g} kW constant",
        f"$/kW solar   : {cost.gen_per_kw:,.0f}",
        f"$/kWh battery: {cost.storage_per_kwh:,.0f}",
        f"$/kWh-yr load: {cost.load_per_kw:,.0f}",
        f"$/kWh income : {cost.load_value_per_kwh:.2f}",
    ]


def _mesh_kwargs(z: np.ndarray, cmap: str) -> dict:
    return dict(shading="auto", cmap=cmap, vmin=z.min(), vmax=z.max())


def _add_contours(ax, x, y, z, fmt: str, n: int = 5) -> None:
    levels = sbc.nice_contour_levels(float(z.min()), float(z.max()), target_count=n)
    if levels.size == 0:
        return
    cs = ax.contour(x, y, z, levels=levels, colors="black", linewidths=0.8, alpha=0.75)
    ax.clabel(cs, fmt=fmt, fontsize=8, inline=True)


def _style_axes(ax, title: str) -> None:
    ax.set_xlabel("Battery storage (kWh)")
    ax.set_ylabel("Solar generation (kW)")
    ax.set_title(title)


# --------------------------------------------------------------------------- #
# Draw primitives (work on any Axes, no fig creation)
# --------------------------------------------------------------------------- #
def _draw_net_value(ax, sweep: sbc.SweepResult) -> plt.cm.ScalarMappable:
    mesh = ax.pcolormesh(
        sweep.kwh_battery, sweep.kw_solar, sweep.net_value,
        **_mesh_kwargs(sweep.net_value, "plasma"),
    )
    _add_contours(ax, sweep.kwh_battery, sweep.kw_solar, sweep.net_value, fmt=r"\$%.0f")
    _style_axes(ax, "Net Value (Income − Capex)")
    return mesh


def _draw_utilization(ax, sweep: sbc.SweepResult) -> plt.cm.ScalarMappable:
    util_pct = sweep.utilization * 100.0
    mesh = ax.pcolormesh(
        sweep.kwh_battery, sweep.kw_solar, util_pct,
        shading="auto", cmap="plasma", vmin=0, vmax=100,
    )
    # Log-spaced contour lines give detail at both low and high utilization
    levels = np.array([10, 20, 40, 60, 80, 90, 95, 99, 99.9, 99.99], dtype=float)
    levels = levels[(levels > util_pct.min()) & (levels < util_pct.max())]
    if levels.size:
        cs = ax.contour(sweep.kwh_battery, sweep.kw_solar, util_pct,
                        levels=levels, colors="black", linewidths=0.8, alpha=0.75)
        ax.clabel(cs, fmt=lambda x: f"{x:.3f}".rstrip("0").rstrip(".") + "%",
                  fontsize=8, inline=True)
    _style_axes(ax, "Load Utilization")
    return mesh


# --------------------------------------------------------------------------- #
# Individual figures
# --------------------------------------------------------------------------- #
def plot_net_value_heatmap(sweep: sbc.SweepResult, data: sbc.NsrdbData) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 7))
    mesh = _draw_net_value(ax, sweep)
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label(r"Net value (\$)")
    plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(data, COST))
    return fig


def plot_utilization_heatmap(sweep: sbc.SweepResult, data: sbc.NsrdbData) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 7))
    mesh = _draw_utilization(ax, sweep)
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label("Load utilization (%)")
    plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(data, COST))
    return fig


def plot_combined(sweep: sbc.SweepResult, data: sbc.NsrdbData) -> plt.Figure:
    fig, (ax_nv, ax_ut) = plt.subplots(1, 2, figsize=(18, 7))

    mesh_nv = _draw_net_value(ax_nv, sweep)
    cb_nv = fig.colorbar(mesh_nv, ax=ax_nv, fraction=0.046, pad=0.04)
    cb_nv.set_label(r"Net value (\$)")

    mesh_ut = _draw_utilization(ax_ut, sweep)
    cb_ut = fig.colorbar(mesh_ut, ax=ax_ut, fraction=0.046, pad=0.04)
    cb_ut.set_label("Load utilization (%)")

    plotting.add_watermark(ax_nv)
    plotting.add_watermark(ax_ut)
    plotting.add_param_box_below(fig, _param_lines(data, COST))
    return fig


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def report_findings(sweep: sbc.SweepResult) -> None:
    util = sweep.utilization
    nv = sweep.net_value
    print(
        f"Grid: {sweep.kw_solar.size} kW pts x {sweep.kwh_battery.size} kWh pts"
        f"  ({util.size} configs)"
    )
    print(f"Utilization: {util.min():.1%} -> {util.max():.1%}")
    print(f"Net value  : ${nv.min():,.0f} -> ${nv.max():,.0f}\n")

    print("Cheapest config meeting each utilization target:")
    for target in REPORT_UTILIZATION_TARGETS:
        best = sweep.lowest_cost_meeting(target)
        if best is None:
            print(f"  >= {target:.0%}: not reachable on this grid")
        else:
            # net value at that config
            i = np.searchsorted(sweep.kw_solar, best["kw_solar"])
            j = np.searchsorted(sweep.kwh_battery, best["kwh_battery"])
            nv_best = float(sweep.net_value[i, j])
            print(
                f"  >= {target:.0%}: {best['kw_solar']:.1f} kW + "
                f"{best['kwh_battery']:.0f} kWh  "
                f"capex ${best['cost']:,.0f}  "
                f"net value ${nv_best:,.0f}  "
                f"(util {best['utilization']:.1%})"
            )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    data = sbc.load_nsrdb_csv(DATA_FILE)
    print(
        f"Loaded {DATA_FILE.name}: {data.n_steps} samples @ {data.dt_hours:.4g} h "
        f"({data.duration_hours:.0f} h total)\n"
    )

    sweep = sbc.sweep_solar_battery(
        data=data,
        kw_solar=KW_SOLAR,
        kwh_battery=KWH_BATTERY,
        cost=COST,
        load_kw=LOAD_KW,
        verbose=True,
    )

    report_findings(sweep)

    def _gt(arr, n):  # grid tag: name{min}-{max}s{step}
        return f"{n}{arr[0]:g}-{arr[-1]:g}s{arr[1]-arr[0]:g}"

    tag = (f"{_gt(KW_SOLAR,'kw')}_{_gt(KWH_BATTERY,'kwh')}"
           f"_sol{COST.gen_per_kw:g}_bat{COST.storage_per_kwh:g}"
           f"_inc{COST.load_value_per_kwh:g}")

    for fig, name in [
        (plot_net_value_heatmap(sweep, data),   f"{tag}_net_value.png"),
        (plot_utilization_heatmap(sweep, data), f"{tag}_utilization.png"),
        (plot_combined(sweep, data),            f"{tag}_combined.png"),
    ]:
        path = plotting.save_figure(fig, name, subdir="kw_kwh")
        print(f"Saved -> {path.relative_to(Path(__file__).parent)}")
        plt.close(fig)


if __name__ == "__main__":
    main()
