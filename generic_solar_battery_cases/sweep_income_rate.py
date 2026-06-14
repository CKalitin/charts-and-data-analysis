"""Sweep income rate (% of load capex per kWh served) across 5 log-spaced values.

For each income rate the physical dispatch frontier is shared (computed once),
and only the net-value calculation changes.

Outputs (output/):
    sweep_income_lines.png       -- 5 max-net-value lines vs $/kWh-yr load
    sweep_income_heatmaps.png    -- 5 net value heatmaps in a grid

Run:  python sweep_income_rate.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

import plotting
import solar_battery_core as sbc

# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
DATA_FILE = Path(__file__).with_name("nsrdb_data") / "nsrdb_836224_2024.csv"

LOAD_KW          = 1.0
GEN_PER_KW       = 100.0   # $ / kW solar
STORAGE_PER_KWH  = 100.0   # $ / kWh battery

# Physical dispatch grid (optimised over, not shown as axes)
KW_SOLAR    = sbc.arange_inclusive(0.0, 25.0, 0.25)
KWH_BATTERY = sbc.arange_inclusive(0.0, 25.0, 0.25)

# x-axis: load capex sweep, log-spaced
LOAD_PER_KW_VALS = np.logspace(1, 4, 60)   # $10 – $10,000

# y-axis: utilization levels for the heatmaps
N_UTIL_LEVELS = 200

# 5 income rate fractions, log-spaced from 0.01% to 1%
INCOME_RATE_FRACS = np.logspace(-4, -2, 5)   # [0.0001, ..., 0.01]


# --------------------------------------------------------------------------- #
# Core analysis (income-independent frontier, run once)
# --------------------------------------------------------------------------- #
def build_frontier(sweep: sbc.SweepResult):
    """Cheapest solar+battery config for every utilization level.

    Returns arrays of shape (N_UTIL_LEVELS,).
    """
    util_flat    = sweep.utilization.flatten()
    served_flat  = sweep.dispatch.served_kwh.flatten()
    kw_flat      = sweep.KW.flatten()
    kwh_flat     = sweep.KWH.flatten()
    sb_capex_flat = kw_flat * GEN_PER_KW + kwh_flat * STORAGE_PER_KWH

    max_util = float(util_flat.max())
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


def net_value_grid(
    min_sb_capex: np.ndarray,
    served_kwh: np.ndarray,
    income_rate_frac: float,
) -> np.ndarray:
    """Net value grid (n_util, n_load) for one income rate fraction."""
    income_rate = LOAD_PER_KW_VALS[np.newaxis, :] * income_rate_frac  # (1, n_load)
    income      = served_kwh[:, np.newaxis] * income_rate
    load_capex  = LOAD_KW * LOAD_PER_KW_VALS[np.newaxis, :]
    return income - min_sb_capex[:, np.newaxis] - load_capex


def max_net_value_per_x(net_val: np.ndarray) -> np.ndarray:
    """Max net value across all utilization levels for each $/kWh-yr load. Shape (n_load,)."""
    return np.nanmax(net_val, axis=0)


def optimal_util_per_x(net_val: np.ndarray, y_pct: np.ndarray) -> np.ndarray:
    """Utilization (%) that achieves max net value at each $/kWh-yr load. Shape (n_load,)."""
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


def _frac_label(frac: float) -> str:
    return f"{frac * 100:.3g}%"


def _param_lines(data: sbc.NsrdbData) -> list[str]:
    yearly, daily = sbc.solar_resource_kwh_m2(data)
    lo, hi = _frac_label(INCOME_RATE_FRACS[0]), _frac_label(INCOME_RATE_FRACS[-1])
    return [
        f"Site         : NSRDB {DATA_FILE.stem.split('_')[1]} ({data.timestamps[0].year})",
        f"Solar resource (kWh/m2): {yearly:,.0f} / year, {daily:.1f} / day",
        f"Load         : {LOAD_KW:g} kW constant",
        f"$/kW solar   : {GEN_PER_KW:,.0f}",
        f"$/kWh battery: {STORAGE_PER_KWH:,.0f}",
        f"Income rate  : {lo} to {hi} of load capex per kWh  (5 log steps)",
        f"$/kWh-yr load    : ${LOAD_PER_KW_VALS[0]:.0f} to ${LOAD_PER_KW_VALS[-1]:,.0f} (log sweep)",
    ]


# --------------------------------------------------------------------------- #
# Line chart
# --------------------------------------------------------------------------- #
def plot_lines(
    x_log: np.ndarray,
    y_pct: np.ndarray,
    net_val_list: list[np.ndarray],
    data: sbc.NsrdbData,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(11, 6))
    colors = _line_colors(len(INCOME_RATE_FRACS))

    for frac, net_val, color in zip(INCOME_RATE_FRACS, net_val_list, colors):
        opt_util = optimal_util_per_x(net_val, y_pct)
        ax.plot(x_log, opt_util, color=color, linewidth=2.0, label=_frac_label(frac))

    ax.set_xlabel(r"Load capex (\$/kWh-yr load, log scale)")
    ax.set_ylabel("Load utilization (%)")
    ax.set_title("Optimal Utilization vs Load Capex — Income Rate Sweep")
    ax.set_ylim(0, 100)
    _set_log_xticks(ax)
    ax.legend(title="Income rate\n(% of load capex/kWh)", fontsize=9, framealpha=0.7)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(data))
    return fig


# --------------------------------------------------------------------------- #
# Heatmap grid
# --------------------------------------------------------------------------- #
def _symlog_norm(net_val: np.ndarray) -> mcolors.SymLogNorm:
    vmin, vmax = float(np.nanmin(net_val)), float(np.nanmax(net_val))
    linthresh = max(abs(vmin), abs(vmax)) / 100.0
    return mcolors.SymLogNorm(linthresh=linthresh, vmin=vmin, vmax=vmax, base=10)


def plot_heatmaps(
    x_log: np.ndarray,
    y_pct: np.ndarray,
    net_val_list: list[np.ndarray],
    data: sbc.NsrdbData,
) -> plt.Figure:
    n = len(INCOME_RATE_FRACS)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 6), sharey=True)

    for ax, frac, net_val in zip(axes, INCOME_RATE_FRACS, net_val_list):
        norm = _symlog_norm(net_val)
        mesh = ax.pcolormesh(x_log, y_pct, net_val, shading="auto",
                             cmap="plasma", norm=norm)
        # breakeven contour
        if np.nanmin(net_val) < 0 < np.nanmax(net_val):
            ax.contour(x_log, y_pct, net_val, levels=[0.0],
                       colors="white", linewidths=1.2, alpha=0.85)
        # max-net-value trend line
        best_util = y_pct[np.nanargmax(net_val, axis=0)]
        ax.plot(x_log, best_util, color="white", linewidth=1.5,
                linestyle="--", alpha=0.85)
        fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.04).set_label(r"Net value (\$)")
        _set_log_xticks(ax)
        ax.set_xlabel(r"\$/kWh-yr load (log)")
        ax.set_ylabel("Load utilization (%)")
        ax.set_title(f"Income: {_frac_label(frac)} of load capex/kWh")
        plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(data), bottom_frac=0.13)
    return fig


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

    cost = sbc.CostParams(gen_per_kw=GEN_PER_KW, storage_per_kwh=STORAGE_PER_KWH)
    print(
        f"Running dispatch: {len(KW_SOLAR)} kW pts x {len(KWH_BATTERY)} kWh pts "
        f"= {len(KW_SOLAR) * len(KWH_BATTERY):,} configs ..."
    )
    sweep = sbc.sweep_solar_battery(data, KW_SOLAR, KWH_BATTERY, cost, LOAD_KW, verbose=True)

    print("Building frontier ...")
    util_levels, min_sb_capex, served_kwh = build_frontier(sweep)

    print(f"Computing net value for {len(INCOME_RATE_FRACS)} income rates ...")
    net_val_list = [net_value_grid(min_sb_capex, served_kwh, f) for f in INCOME_RATE_FRACS]

    for frac, nv in zip(INCOME_RATE_FRACS, net_val_list):
        mnv = max_net_value_per_x(nv)
        print(f"  {_frac_label(frac):>6s} : max net value ${mnv.max():,.0f}  "
              f"at ${LOAD_PER_KW_VALS[np.argmax(mnv)]:,.0f}/kWh-yr load")
    print()

    x_log = np.log10(LOAD_PER_KW_VALS)
    y_pct = util_levels * 100.0

    def _gt(arr, n):
        return f"{n}{arr[0]:g}-{arr[-1]:g}s{arr[1]-arr[0]:g}"

    tag = (f"{_gt(KW_SOLAR,'kw')}_{_gt(KWH_BATTERY,'kwh')}"
           f"_sol{GEN_PER_KW:g}_bat{STORAGE_PER_KWH:g}"
           f"_inc{INCOME_RATE_FRACS[0]*100:g}pct-{INCOME_RATE_FRACS[-1]*100:g}pct"
           f"_{len(INCOME_RATE_FRACS)}steps")

    for fig, name in [
        (plot_lines(x_log, y_pct, net_val_list, data),    f"{tag}_lines.png"),
        (plot_heatmaps(x_log, y_pct, net_val_list, data), f"{tag}_heatmaps.png"),
    ]:
        path = plotting.save_figure(fig, name, subdir="income_rate")
        print(f"Saved -> {path.relative_to(Path(__file__).parent)}")
        plt.close(fig)


if __name__ == "__main__":
    main()
