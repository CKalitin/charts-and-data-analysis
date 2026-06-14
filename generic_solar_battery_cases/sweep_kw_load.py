"""Net value + solar/battery sizing heatmaps: load utilization vs load capex.

For each achievable utilization level, finds the cheapest solar + battery
configuration that reaches it, then sweeps load capex to compute net value.

    x-axis : load capex         ($/kWh-yr load, log-spaced $10 – $10 000)
    y-axis : load utilization   (0 – max achievable %)
    color  : net value          (left chart)  income − solar/batt capex − load capex
             kW solar / kWh battery ratio of the optimal config (right chart)

Outputs (output/):
    sweep_kw_load_net_value.png
    sweep_kw_load_ratio.png
    sweep_kw_load_combined.png

Run:  python sweep_kw_load.py
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

LOAD_KW = 1.0
GEN_PER_KW = 50.0        # $ / kW solar
STORAGE_PER_KWH = 100.0   # $ / kWh battery

# --------------------------------------------------------------------------- #
# Income mode — set INCOME_MODE to switch between the two.
#
#   "constant"     : fixed $/kWh regardless of load capex
#                    → set LOAD_VALUE_PER_KWH
#
#   "proportional" : income scales with load capex
#                    → set INCOME_RATE_FRAC ($/kWh = frac × $/kWh-yr load)
# --------------------------------------------------------------------------- #
INCOME_MODE = "proportional"

LOAD_VALUE_PER_KWH = 0.20   # used when INCOME_MODE == "constant"
INCOME_RATE_FRAC   = 0.001 # used when INCOME_MODE == "proportional"

# Physical dispatch grid (optimised over, not shown as axes)
KW_SOLAR = sbc.arange_inclusive(0.0, 25.0, 0.1)
KWH_BATTERY = sbc.arange_inclusive(0.0, 25.0, 0.1)

# x-axis: load capex sweep, log-spaced
LOAD_PER_KW_VALS = np.logspace(1, 4, 60)   # $10 – $10 000, 60 points

# y-axis: utilization levels to evaluate
N_UTIL_LEVELS = 200


# --------------------------------------------------------------------------- #
# Core analysis
# --------------------------------------------------------------------------- #
def min_capex_frontier(sweep: sbc.SweepResult):
    """For each utilization level, find the min solar+battery capex config.

    Returns
    -------
    util_levels    : (N,)  target utilization fractions
    min_sb_capex   : (N,)  cheapest solar+battery capex achieving each
    served_kwh     : (N,)  kWh served by that cheapest config
    opt_kw_solar   : (N,)  optimal solar nameplate (kW)
    opt_kwh_battery: (N,)  optimal battery capacity (kWh)
    """
    util_flat    = sweep.utilization.flatten()
    served_flat  = sweep.dispatch.served_kwh.flatten()
    kw_flat      = sweep.KW.flatten()
    kwh_flat     = sweep.KWH.flatten()

    sb_capex_flat = kw_flat * GEN_PER_KW + kwh_flat * STORAGE_PER_KWH

    max_util = float(util_flat.max())
    util_levels = np.linspace(0.0, max_util * 0.9995, N_UTIL_LEVELS)

    min_sb_capex    = np.full(N_UTIL_LEVELS, np.nan)
    served_kwh      = np.zeros(N_UTIL_LEVELS)
    opt_kw_solar    = np.zeros(N_UTIL_LEVELS)
    opt_kwh_battery = np.zeros(N_UTIL_LEVELS)

    for i, u in enumerate(util_levels):
        feasible = util_flat >= u
        if feasible.any():
            masked = np.where(feasible, sb_capex_flat, np.inf)
            idx = int(np.argmin(masked))
            min_sb_capex[i]    = sb_capex_flat[idx]
            served_kwh[i]      = served_flat[idx]
            opt_kw_solar[i]    = kw_flat[idx]
            opt_kwh_battery[i] = kwh_flat[idx]

    return util_levels, min_sb_capex, served_kwh, opt_kw_solar, opt_kwh_battery


def net_value_grid(
    util_levels: np.ndarray,
    min_sb_capex: np.ndarray,
    served_kwh: np.ndarray,
    load_per_kw_vals: np.ndarray,
) -> np.ndarray:
    """Net value for every (utilization, $/kWh-yr load) cell. Shape: (n_util, n_load).

    Income depends on INCOME_MODE:
      "constant"     : LOAD_VALUE_PER_KWH per kWh, same across all x-axis columns
      "proportional" : INCOME_RATE_FRAC × ($/kWh-yr load) per kWh, scales with load capex
    """
    if INCOME_MODE == "constant":
        income_rate = LOAD_VALUE_PER_KWH                                # scalar
    elif INCOME_MODE == "proportional":
        income_rate = load_per_kw_vals[np.newaxis, :] * INCOME_RATE_FRAC  # (1, n_load)
    else:
        raise ValueError(f"Unknown INCOME_MODE {INCOME_MODE!r}. Use 'constant' or 'proportional'.")
    income     = served_kwh[:, np.newaxis] * income_rate
    load_capex = LOAD_KW * load_per_kw_vals[np.newaxis, :]
    return income - min_sb_capex[:, np.newaxis] - load_capex


def pct_solar_grid(
    opt_kw_solar: np.ndarray,
    opt_kwh_battery: np.ndarray,
    n_load: int,
    smooth_window: int = 9,
) -> np.ndarray:
    """Fraction of total system capex going to solar, as a percentage [0, 100].

    pct_solar = solar_capex / (solar_capex + battery_capex) × 100

    100% = solar only (no battery), ~50% = equal capex split.
    A median filter (window = smooth_window utilization steps) is applied before
    computing the fraction to suppress the argmin-jumping noise at the
    solar-to-battery transition zone where many configs are nearly cost-tied.
    Shape: (n_util, n_load).
    """
    from scipy.ndimage import median_filter
    kw  = median_filter(opt_kw_solar,    size=smooth_window)
    kwh = median_filter(opt_kwh_battery, size=smooth_window)

    solar_capex = kw  * GEN_PER_KW
    batt_capex  = kwh * STORAGE_PER_KWH
    total = solar_capex + batt_capex
    with np.errstate(invalid="ignore", divide="ignore"):
        pct = np.where(total > 0, solar_capex / total * 100.0, 50.0)

    return np.tile(pct[:, np.newaxis], (1, n_load))


# --------------------------------------------------------------------------- #
# Plotting helpers
# --------------------------------------------------------------------------- #
def _set_log_xticks(ax, vals: np.ndarray) -> None:
    decades = np.arange(
        int(np.floor(np.log10(vals[0]))),
        int(np.ceil(np.log10(vals[-1]))) + 1,
    )
    ax.set_xticks(decades)
    ax.set_xticklabels([f"${10**d:,.0f}" for d in decades])


def _param_lines(data: sbc.NsrdbData) -> list[str]:
    yearly, daily = sbc.solar_resource_kwh_m2(data)
    return [
        f"Site         : NSRDB {DATA_FILE.stem.split('_')[1]} ({data.timestamps[0].year})",
        f"Solar resource (kWh/m²): {yearly:,.0f} / year, {daily:.1f} / day",
        f"Load         : {LOAD_KW:g} kW constant",
        f"$/kW solar   : {GEN_PER_KW:,.0f}",
        f"$/kWh battery: {STORAGE_PER_KWH:,.0f}",
        *(
            [f"$/kWh income : {LOAD_VALUE_PER_KWH:.4f} (constant)"]
            if INCOME_MODE == "constant" else
            [f"Income rate  : {INCOME_RATE_FRAC*100:.4f}% of load capex per kWh served"]
        ),
        f"$/kWh-yr load    : ${LOAD_PER_KW_VALS[0]:.0f} – ${LOAD_PER_KW_VALS[-1]:,.0f} (log sweep)",
    ]


def _symlog_contour_levels(vmin: float, vmax: float, linthresh: float) -> np.ndarray:
    """Log-spaced contour levels suited to a SymLog colour scale.

    Generates ~3 negative decade levels, zero, and ~3 positive decade levels,
    filtered to the actual data range.
    """
    decades = np.arange(-5, 6)
    pos = linthresh * (10.0 ** decades[decades >= 0])
    neg = -linthresh * (10.0 ** decades[decades >= 0][::-1])
    levels = np.concatenate([neg, [0.0], pos])
    return levels[(levels >= vmin) & (levels <= vmax)]


def _draw_net_value(ax, x_log, y_pct, net_val) -> plt.cm.ScalarMappable:
    from matplotlib.colors import SymLogNorm
    vmin, vmax = float(np.nanmin(net_val)), float(np.nanmax(net_val))
    linthresh = max(abs(vmin), abs(vmax)) / 100.0   # linear region = ±1% of range
    norm = SymLogNorm(linthresh=linthresh, vmin=vmin, vmax=vmax, base=10)
    mesh = ax.pcolormesh(x_log, y_pct, net_val, shading="auto", cmap="plasma", norm=norm)
    levels = _symlog_contour_levels(vmin, vmax, linthresh)
    if levels.size:
        cs = ax.contour(x_log, y_pct, net_val, levels=levels,
                        colors="black", linewidths=0.8, alpha=0.75)
        ax.clabel(cs, fmt=r"\$%.0f", fontsize=8, inline=True)

    # Trend line: utilization that maximises net value at each $/kWh-yr load
    best_util = y_pct[np.nanargmax(net_val, axis=0)]
    ax.plot(x_log, best_util, color="white", linewidth=2.0, linestyle="--",
            alpha=0.9, label="Max net value")
    ax.legend(loc="lower right", fontsize=8, framealpha=0.6)

    _set_log_xticks(ax, LOAD_PER_KW_VALS)
    ax.set_xlabel(r"Load capex (\$/kWh-yr load, log scale)")
    ax.set_ylabel("Load utilization (%)")
    ax.set_title("Net Value vs Load Capex and Utilization")
    return mesh


def _draw_pct_solar(ax, x_log, y_pct, pct_solar) -> plt.cm.ScalarMappable:
    mesh = ax.pcolormesh(x_log, y_pct, pct_solar, shading="auto", cmap="plasma",
                         vmin=0, vmax=100)
    levels = sbc.nice_contour_levels(float(pct_solar.min()), float(pct_solar.max()), target_count=5)
    if levels.size:
        cs = ax.contour(x_log, y_pct, pct_solar, levels=levels,
                        colors="black", linewidths=0.8, alpha=0.75)
        ax.clabel(cs, fmt="%.0f%%", fontsize=8, inline=True)
    _set_log_xticks(ax, LOAD_PER_KW_VALS)
    ax.set_xlabel(r"Load capex (\$/kWh-yr load, log scale)")
    ax.set_ylabel("Load utilization (%)")
    ax.set_title("Optimal Config: % of Capex in Solar")
    return mesh


# --------------------------------------------------------------------------- #
# Figure builders
# --------------------------------------------------------------------------- #
def plot_net_value(x_log, y_pct, net_val, data: sbc.NsrdbData) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 7))
    mesh = _draw_net_value(ax, x_log, y_pct, net_val)
    fig.colorbar(mesh, ax=ax).set_label(r"Net value (\$)")
    plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(data))
    return fig


def plot_pct_solar(x_log, y_pct, pct_solar, data: sbc.NsrdbData) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 7))
    mesh = _draw_pct_solar(ax, x_log, y_pct, pct_solar)
    fig.colorbar(mesh, ax=ax).set_label("Solar capex fraction (%)")
    plotting.add_watermark(ax)
    plotting.add_param_box_below(fig, _param_lines(data))
    return fig


def plot_combined(x_log, y_pct, net_val, pct_solar, data: sbc.NsrdbData) -> plt.Figure:
    fig, (ax_nv, ax_rt) = plt.subplots(1, 2, figsize=(20, 7))

    mesh_nv = _draw_net_value(ax_nv, x_log, y_pct, net_val)
    fig.colorbar(mesh_nv, ax=ax_nv, fraction=0.046, pad=0.04).set_label(r"Net value (\$)")

    mesh_rt = _draw_pct_solar(ax_rt, x_log, y_pct, pct_solar)
    fig.colorbar(mesh_rt, ax=ax_rt, fraction=0.046, pad=0.04).set_label("Solar capex fraction (%)")

    plotting.add_watermark(ax_nv)
    plotting.add_watermark(ax_rt)
    plotting.add_param_box_below(fig, _param_lines(data))
    return fig


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    data = sbc.load_nsrdb_csv(DATA_FILE)
    yearly, daily = sbc.solar_resource_kwh_m2(data)
    print(
        f"Loaded {DATA_FILE.name}: {data.n_steps} samples  |  "
        f"solar {yearly:.0f} kWh/m²/yr, {daily:.1f} kWh/m²/day\n"
    )

    cost = sbc.CostParams(gen_per_kw=GEN_PER_KW, storage_per_kwh=STORAGE_PER_KWH)
    print(
        f"Running dispatch: {len(KW_SOLAR)} kW pts × {len(KWH_BATTERY)} kWh pts "
        f"= {len(KW_SOLAR) * len(KWH_BATTERY):,} configs ..."
    )
    sweep = sbc.sweep_solar_battery(data, KW_SOLAR, KWH_BATTERY, cost, LOAD_KW, verbose=True)

    print("Computing min-capex frontier ...")
    util_levels, min_sb_capex, served_kwh, opt_kw, opt_kwh = min_capex_frontier(sweep)

    net_val   = net_value_grid(util_levels, min_sb_capex, served_kwh, LOAD_PER_KW_VALS)
    pct_solar = pct_solar_grid(opt_kw, opt_kwh, len(LOAD_PER_KW_VALS))

    print(
        f"Net value range  : ${np.nanmin(net_val):,.0f} – ${np.nanmax(net_val):,.0f}\n"
        f"% solar range    : {pct_solar.min():.1f}% – {pct_solar.max():.1f}%\n"
        f"Utilization range: {util_levels[0]:.1%} – {util_levels[-1]:.1%}\n"
    )

    x_log = np.log10(LOAD_PER_KW_VALS)
    y_pct = util_levels * 100.0

    def _gt(arr, n):
        return f"{n}{arr[0]:g}-{arr[-1]:g}s{arr[1]-arr[0]:g}"

    income_tag = (f"prop{INCOME_RATE_FRAC*100:g}pct" if INCOME_MODE == "proportional"
                  else f"const{LOAD_VALUE_PER_KWH:g}")
    load_tag = f"load${LOAD_PER_KW_VALS[0]:.0f}-${LOAD_PER_KW_VALS[-1]:.0f}"
    tag = (f"{_gt(KW_SOLAR,'kw')}_{_gt(KWH_BATTERY,'kwh')}"
           f"_sol{GEN_PER_KW:g}_bat{STORAGE_PER_KWH:g}"
           f"_{income_tag}_{load_tag}")

    for fig, name in [
        (plot_net_value(x_log, y_pct, net_val, data),           f"{tag}_net_value.png"),
        (plot_pct_solar(x_log, y_pct, pct_solar, data),         f"{tag}_pct_solar.png"),
        (plot_combined(x_log, y_pct, net_val, pct_solar, data), f"{tag}_combined.png"),
    ]:
        path = plotting.save_figure(fig, name, subdir="kw_load")
        print(f"Saved -> {path.relative_to(Path(__file__).parent)}")
        plt.close(fig)


if __name__ == "__main__":
    main()
