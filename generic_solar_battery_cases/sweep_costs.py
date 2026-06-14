"""Sweep solar and battery costs to show effect on optimal load utilization.

Three panels, 5 lines each (cost steps $100 -> $20 in $20 increments):
  Left   : solar cost sweep      (battery held at $100/kWh)
  Centre : battery cost sweep    (solar held at $100/kW)
  Right  : both swept together

x-axis : load capex ($/kWh-yr load, log-spaced $10 - $10,000)
y-axis : load utilization at max net value (%)
Income : 0.03% of load capex per kWh served (proportional)

Output: output/sweep_costs.png
Run:    python sweep_costs.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotting
import solar_battery_core as sbc

# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
DATA_FILE = Path(__file__).with_name("nsrdb_data") / "nsrdb_836224_2024.csv"

LOAD_KW          = 1.0
INCOME_RATE_FRAC = 0.0003   # 0.03% of load capex per kWh served

# Physical dispatch grid (run once — costs don't change dispatch physics)
KW_SOLAR    = sbc.arange_inclusive(0.0, 20.0, 0.1)
KWH_BATTERY = sbc.arange_inclusive(0.0, 20.0, 0.1)

# x-axis
LOAD_PER_KW_VALS = np.logspace(1, 4, 60)   # $10 - $10,000
N_UTIL_LEVELS    = 200

# Cost steps: $100 -> $20 in $20 decrements
COST_STEPS = np.arange(100, 0, -20, dtype=float)   # [100, 80, 60, 40, 20]
BASE_COST  = 100.0                                   # baseline ($/kW or $/kWh)


# --------------------------------------------------------------------------- #
# Core analysis
# --------------------------------------------------------------------------- #
def build_frontier(sweep: sbc.SweepResult, gen_per_kw: float, storage_per_kwh: float):
    """Min solar+battery capex frontier for given cost params.

    Returns util_levels, min_sb_capex, served_kwh — all shape (N_UTIL_LEVELS,).
    """
    util_flat     = sweep.utilization.flatten()
    served_flat   = sweep.dispatch.served_kwh.flatten()
    kw_flat       = sweep.KW.flatten()
    kwh_flat      = sweep.KWH.flatten()
    sb_capex_flat = kw_flat * gen_per_kw + kwh_flat * storage_per_kwh

    max_util    = float(util_flat.max())
    util_levels = np.linspace(0.0, max_util * 0.9995, N_UTIL_LEVELS)
    min_sb_capex = np.full(N_UTIL_LEVELS, np.nan)
    served_kwh   = np.zeros(N_UTIL_LEVELS)

    for i, u in enumerate(util_levels):
        feasible = util_flat >= u
        if feasible.any():
            masked = np.where(feasible, sb_capex_flat, np.inf)
            idx = int(np.argmin(masked))
            min_sb_capex[i] = sb_capex_flat[idx]
            served_kwh[i]   = served_flat[idx]

    return util_levels, min_sb_capex, served_kwh


def net_value_grid(min_sb_capex: np.ndarray, served_kwh: np.ndarray) -> np.ndarray:
    """Net value grid (n_util, n_load) for fixed proportional income rate."""
    income_rate = LOAD_PER_KW_VALS[np.newaxis, :] * INCOME_RATE_FRAC
    income      = served_kwh[:, np.newaxis] * income_rate
    load_capex  = LOAD_KW * LOAD_PER_KW_VALS[np.newaxis, :]
    return income - min_sb_capex[:, np.newaxis] - load_capex


def optimal_util_per_x(net_val: np.ndarray, y_pct: np.ndarray) -> np.ndarray:
    """Utilization (%) that maximises net value at each $/kWh-yr load. Shape (n_load,)."""
    return y_pct[np.nanargmax(net_val, axis=0)]


# --------------------------------------------------------------------------- #
# Plotting helpers
# --------------------------------------------------------------------------- #
def _set_log_xticks(ax) -> None:
    decades = np.arange(
        int(np.floor(np.log10(LOAD_PER_KW_VALS[0]))),
        int(np.ceil(np.log10(LOAD_PER_KW_VALS[-1]))) + 1,
    )
    ax.set_xticks(decades)
    ax.set_xticklabels([f"${10**d:,.0f}" for d in decades])


def _line_colors(n: int):
    return plt.cm.plasma(np.linspace(0.15, 0.85, n))


def _draw_panel(ax, x_log, frontiers, labels, title: str, show_ylabel: bool) -> None:
    colors = _line_colors(len(frontiers))
    for (util_levels, min_sb_capex, served_kwh), label, color in zip(frontiers, labels, colors):
        y_pct    = util_levels * 100.0
        net_val  = net_value_grid(min_sb_capex, served_kwh)
        opt_util = optimal_util_per_x(net_val, y_pct)
        ax.plot(x_log, opt_util, color=color, linewidth=2.0, label=label)

    if show_ylabel:
        ax.set_ylabel("Load utilization (%)")
    ax.set_xlabel(r"Load capex ($/kWh-yr load, log scale)")
    ax.set_title(title)
    ax.set_ylim(0, 100)
    _set_log_xticks(ax)
    ax.legend(fontsize=8, framealpha=0.7)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plotting.add_watermark(ax)


def _param_lines(data: sbc.NsrdbData) -> list[str]:
    yearly, daily = sbc.solar_resource_kwh_m2(data)
    return [
        f"Site         : NSRDB {DATA_FILE.stem.split('_')[1]} ({data.timestamps[0].year})",
        f"Solar resource (kWh/m2): {yearly:,.0f} / year, {daily:.1f} / day",
        f"Load         : {LOAD_KW:g} kW constant",
        f"Income rate  : {INCOME_RATE_FRAC * 100:.3g}% of load capex per kWh served",
        f"Cost steps   : ${COST_STEPS[0]:.0f} to ${COST_STEPS[-1]:.0f} /kW or /kWh in $20 steps",
        f"$/kWh-yr load    : ${LOAD_PER_KW_VALS[0]:.0f} to ${LOAD_PER_KW_VALS[-1]:,.0f} (log sweep)",
    ]


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    data = sbc.load_nsrdb_csv(DATA_FILE)
    yearly, daily = sbc.solar_resource_kwh_m2(data)
    print(
        f"Loaded {DATA_FILE.name}: {data.n_steps} samples  |  "
        f"solar {yearly:.0f} kWh/m2/yr, {daily:.1f} kWh/m2/day\n"
    )

    cost = sbc.CostParams(gen_per_kw=BASE_COST, storage_per_kwh=BASE_COST)
    print(
        f"Running dispatch: {len(KW_SOLAR)} kW pts x {len(KWH_BATTERY)} kWh pts "
        f"= {len(KW_SOLAR) * len(KWH_BATTERY):,} configs ..."
    )
    sweep = sbc.sweep_solar_battery(data, KW_SOLAR, KWH_BATTERY, cost, LOAD_KW, verbose=True)

    x_log = np.log10(LOAD_PER_KW_VALS)

    print("Building solar cost frontiers ...")
    solar_frontiers = [
        build_frontier(sweep, gen_per_kw=c, storage_per_kwh=BASE_COST)
        for c in COST_STEPS
    ]
    solar_labels = [f"${c:.0f}/kW solar" for c in COST_STEPS]

    print("Building battery cost frontiers ...")
    batt_frontiers = [
        build_frontier(sweep, gen_per_kw=BASE_COST, storage_per_kwh=c)
        for c in COST_STEPS
    ]
    batt_labels = [f"${c:.0f}/kWh battery" for c in COST_STEPS]

    print("Building combined cost frontiers ...")
    comb_frontiers = [
        build_frontier(sweep, gen_per_kw=c, storage_per_kwh=c)
        for c in COST_STEPS
    ]
    comb_labels = [f"${c:.0f}/kW + ${c:.0f}/kWh" for c in COST_STEPS]

    print("Plotting ...")
    fig, axes = plt.subplots(1, 3, figsize=(19, 6), sharey=True)
    fig.subplots_adjust(wspace=0.08)

    _draw_panel(axes[0], x_log, solar_frontiers, solar_labels,
                "Solar Cost Sweep\n(battery = $100/kWh)", show_ylabel=True)
    _draw_panel(axes[1], x_log, batt_frontiers, batt_labels,
                "Battery Cost Sweep\n(solar = $100/kW)", show_ylabel=False)
    _draw_panel(axes[2], x_log, comb_frontiers, comb_labels,
                "Combined Cost Sweep\n(solar + battery together)", show_ylabel=False)

    plotting.add_param_box_below(fig, _param_lines(data))

    def _gt(arr, n):
        return f"{n}{arr[0]:g}-{arr[-1]:g}s{arr[1]-arr[0]:g}"

    tag = (f"{_gt(KW_SOLAR,'kw')}_{_gt(KWH_BATTERY,'kwh')}"
           f"_cost{COST_STEPS[-1]:.0f}-{COST_STEPS[0]:.0f}"
           f"_inc{INCOME_RATE_FRAC*100:g}pct")

    path = plotting.save_figure(fig, f"{tag}_combined.png", subdir="costs")
    print(f"Saved -> {path.relative_to(Path(__file__).parent)}")
    plt.close(fig)


if __name__ == "__main__":
    main()
