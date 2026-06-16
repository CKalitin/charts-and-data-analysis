"""Terraform Electrolyzer — LCOE vs solar nameplate kW, no battery.

Shows the levelised cost of electricity (LCOE) as a function of solar array
size for Terraform's hydrogen electrolyzer load case:

    LCOE(S) = (solar_cost_ann × S  +  load_cost_ann × L)
              ─────────────────────────────────────────────
                      served_kWh_per_year(S, battery=0)

Parameters:
  Load:       1 kW constant hydrogen electrolyzer  (cfg.LOAD_KW)
  Load capex: $50/kW, 5-yr amort  →  $10/(kW·yr)
  Income:     $0.0125/kWh  (hydrogen production economics)
  Battery:    0 kWh  (pure solar, no storage)
  Solar:      $200/kW capex, 20-yr amort  →  $10/(kW·yr)

The minimum LCOE marks the hardware build that minimises delivered-electricity
cost regardless of the income signal. A horizontal line at Terraform's income
($0.0125/kWh) shows the "profitable zone" — solar sizes where LCOE < income.
"""

from __future__ import annotations

import sys
from pathlib import Path

if not __package__:  # running as a script — add project root to path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import config as cfg
import model

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]

# ── Terraform Electrolyzer parameters (mirrors cfg.LOAD_CASES) ──────────────
_TF_INCOME       = 0.0125   # $/kWh
_TF_CAPEX_PER_KW = 50.0    # $/kW  one-time
_TF_AMORT        = 5        # years
_TF_COST_ANN     = _TF_CAPEX_PER_KW / _TF_AMORT   # $10/(kW·yr)

# ── Sweep range ──────────────────────────────────────────────────────────────
_KW_MAX  = 5.0
_KW_STEP = 0.05   # fine enough for a smooth curve (201 points)


def _compute(data: model.NsrdbData) -> tuple[np.ndarray, np.ndarray]:
    """Run the vectorised no-battery sweep; return (kw_sweep, lcoe)."""
    kw_sweep = np.arange(0.0, _KW_MAX + _KW_STEP / 2, _KW_STEP)

    # Shape (T, nS) — all solar sizes in one pass, no time loop per config.
    gen = model.solar_generation_kw(data.ghi_w_m2[:, None], kw_sweep[None, :])

    # battery_kwh=0 → SOC stays 0 throughout; served = min(gen, load) per step.
    res = model.simulate_dispatch(gen, cfg.LOAD_KW, 0.0, data.dt_hours)
    served = res.served_kwh  # shape (nS,)

    solar_cost = cfg.SOLAR_COST_ANN * kw_sweep          # $/yr
    load_cost  = _TF_COST_ANN * cfg.LOAD_KW             # $/yr (constant)
    total_cost = solar_cost + load_cost                  # $/yr

    with np.errstate(divide="ignore", invalid="ignore"):
        lcoe = np.where(served > 0, total_cost / served, np.inf)

    lcoe[0] = np.inf   # S = 0 → nothing served → LCOE undefined

    return kw_sweep, lcoe


def draw(ax, kw_sweep: np.ndarray, lcoe: np.ndarray) -> None:
    """LCOE ($/kWh) vs solar nameplate (kW) with income threshold and optimum."""
    finite = np.isfinite(lcoe)

    # Clip y-axis at P90 of finite values so the steep near-zero tail doesn't
    # crush the interesting minimum region into an illegible sliver.
    y_max = float(np.nanpercentile(lcoe[finite], 90)) * 1.15

    lcoe_plot = np.where(lcoe <= y_max, lcoe, np.nan)
    ax.plot(kw_sweep, lcoe_plot, color="#2166ac", linewidth=2.0,
            label="LCOE  ($/kWh)")

    # ── Minimum LCOE point ───────────────────────────────────────────────────
    opt_idx  = int(np.nanargmin(lcoe))
    opt_kw   = float(kw_sweep[opt_idx])
    opt_lcoe = float(lcoe[opt_idx])
    ax.scatter([opt_kw], [opt_lcoe], s=100, marker="*", color="#2166ac",
               edgecolors="black", linewidth=0.8, zorder=5,
               label=f"Min LCOE: {common._dollar_fmt(opt_lcoe)}/kWh  at {opt_kw:g} kW")

    # ── Terraform income threshold ────────────────────────────────────────────
    ax.axhline(_TF_INCOME, color="#d6604d", linewidth=1.5, linestyle="--",
               label=f"Terraform income: {common._dollar_fmt(_TF_INCOME)}/kWh")

    # ── Shade profitable zone (LCOE < income) ────────────────────────────────
    lcoe_safe = np.where(finite, lcoe, np.inf)
    profitable = lcoe_safe < _TF_INCOME
    if profitable.any():
        ax.fill_between(kw_sweep, 0.0, _TF_INCOME,
                        where=profitable, color="#4dac26", alpha=0.18,
                        label="Profitable  (LCOE < income)")

    ax.set_xlabel("Solar nameplate  (kW)")
    ax.set_ylabel("LCOE  ($/kWh)")
    ax.set_xlim(0.0, _KW_MAX)
    ax.set_ylim(0.0, y_max)
    ax.set_title(
        "LCOE vs solar array size  —  Terraform Electrolyzer, no battery\n"
        "LCOE = (solar capex cost + electrolyzer capex cost) / kWh served"
    )
    ax.legend(loc="upper right", fontsize=9, framealpha=0.90)
    ax.yaxis.set_major_formatter(
        __import__("matplotlib.ticker", fromlist=["FuncFormatter"])
        .FuncFormatter(lambda v, _: f"${v:.4g}")
    )


def figures(data: model.NsrdbData, grid: model.ServedGrid):
    from viz import render

    kw_sweep, lcoe = _compute(data)

    opt_idx  = int(np.nanargmin(lcoe))
    opt_kw   = float(kw_sweep[opt_idx])
    opt_lcoe = float(lcoe[opt_idx])

    params = {
        "Site":          common.site_label(),
        "Load":          f"{cfg.LOAD_KW:g} kW constant (Terraform H₂ electrolyzer)",
        "Solar capex":   f"${cfg.SOLAR_CAPEX_PER_KW:.0f}/kW, {cfg.AMORTIZATION_YEARS:g}-yr amort"
                         f"  →  ${cfg.SOLAR_COST_ANN:.3g}/(kW·yr)",
        "Elec. capex":   f"${_TF_CAPEX_PER_KW:.0f}/kW, {_TF_AMORT}-yr amort"
                         f"  →  ${_TF_COST_ANN:.3g}/(kW·yr)",
        "Income":        f"{common._dollar_fmt(_TF_INCOME)}/kWh  (H₂ economics)",
        "Battery":       "none",
        "Optimal build": f"{opt_kw:g} kW solar  →  LCOE {common._dollar_fmt(opt_lcoe)}/kWh",
    }

    suffix_params = {
        "sol": f"0-{_KW_MAX:g}kW",
        "step": f"{_KW_STEP:g}kW",
        "load": f"{cfg.LOAD_KW:g}kW",
        "nobat": "",
        "terraform": "",
    }
    suffix = common.param_suffix(suffix_params)
    out_path = cfg.OUT_BUILD_PLANE / f"lcoe_vs_solar_terraform_{suffix}.png"

    def make_fig(kw_sweep=kw_sweep, lcoe=lcoe, params=params, out_path=out_path):
        fig, ax = render.new_figure(figsize=(10, 6))
        draw(ax, kw_sweep, lcoe)
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, out_path

    return [("terraform/lcoe_vs_solar", make_fig)]


if __name__ == "__main__":
    import time

    import config as cfg
    import derived
    import model
    from viz import render

    t0 = time.time()
    grid = derived.load_served_grid()
    data = model.load_nsrdb(cfg.DATA_FILE, resample=None)
    plan = figures(data, grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
