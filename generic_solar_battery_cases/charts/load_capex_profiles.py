"""Load capex profiles — 3-panel line charts over load capex at a fixed income level.

One figure per income level; each figure has three panels:
  1. LVOE-optimal utilization (%) — LCOE-minimizing build, masked to LVOE > 0
  2. LVOE ($/kWh) — income minus min LCOE; crosses 0 at the breakeven load capex
  3. Min LCOE ($/kWh) vs load capex, with a horizontal line at this income level

x-axis (bottom): load capex ($/kW raw)  /  top twin: $/kW·yr annualized
"""

from __future__ import annotations

import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.ticker as mticker
import numpy as np

import config as cfg
import derived
from labels import axis_label

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]

_INCOME_SLICES = [0.01, 0.1, 1.0]   # $/kWh


def _nearest_idx(arr: np.ndarray, value: float) -> int:
    return int(np.argmin(np.abs(arr - value)))


def draw_slice(axes, plane: derived.LoadPlane, income: float) -> None:
    """Fill three Axes with LVOE-util / LVOE / min-LCOE profiles for one income level."""
    ax_util, ax_lvoe, ax_cost = axes

    x_raw = plane.load_capex_raw           # $/kW  (display x)
    amort = plane.load_amortization_years

    i = _nearest_idx(plane.income_per_kwh, income)
    lvoe = plane.lvoe[i, :]
    util = plane.lcoe_utilization[i, :] * 100.0

    # ── panel 1: LVOE-optimal utilization, masked to viable region ───────────
    ax_util.plot(x_raw, np.where(lvoe > 0, util, np.nan),
                 color="#4a90d9", linewidth=2.0)
    ax_util.set_ylabel("Utilization (%)")
    ax_util.set_ylim(0, 105)
    ax_util.set_title("LVOE-optimal utilization")

    # ── panel 2: LVOE ────────────────────────────────────────────────────────
    ax_lvoe.plot(x_raw, lvoe, color="#7b2fbe", linewidth=2.0)
    ax_lvoe.axhline(0, color="black", linewidth=0.8, linestyle=":")
    ax_lvoe.set_ylabel("LVOE  ($/kWh)")
    ax_lvoe.set_title("Levelized Value of Energy  (income − min LCOE)")
    ax_lvoe.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"${v:.3g}")
    )

    # ── panel 3: min LCOE + income reference line ─────────────────────────────
    ax_cost.plot(x_raw, plane.lcoe_min, color="#333333", linewidth=2.0, label="Min LCOE")
    ax_cost.axhline(income, color="#e07b00", linewidth=1.5, linestyle="--",
                    label=f"Income  ${income:.3g}/kWh")
    ax_cost.set_ylabel("$/kWh")
    ax_cost.set_yscale("log")
    ax_cost.set_title("Min LCOE vs load capex")
    ax_cost.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
    )
    ax_cost.legend(fontsize=8, framealpha=0.85)

    # ── shared x-axis setup ───────────────────────────────────────────────────
    for ax in axes:
        ax.set_xscale("log")
        ax.set_xlim(x_raw.min(), x_raw.max())
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
        )
        ax.set_xlabel(f"Load capex  ($/kW, {amort:g}-yr amort)")
        ax.grid(True, which="major", alpha=0.35)
        ax.grid(True, which="minor", alpha=0.12)
        ax.text(0.02, 0.02, cfg.WATERMARK_TEXT, transform=ax.transAxes,
                ha="left", va="bottom", fontsize=9.0, color="#888888", alpha=0.9)

    # Annualized $/kW·yr twin on top of the first panel only.
    sec = ax_util.secondary_xaxis(
        "top", functions=(lambda v: v / amort, lambda v: v * amort)
    )
    sec.set_xlabel("Annualized load capex  ($/kW·yr)")
    sec.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
    )


def figures(plane: derived.LoadPlane, grid):
    from viz import render

    amort = plane.load_amortization_years
    params = {
        "Site":            common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load":            f"{cfg.LOAD_KW:g} kW constant",
        "Solar cost":      f"${plane.solar_cost_ann:.3g}/kW·yr",
        "Battery cost":    f"${plane.batt_cost_ann:.3g}/kWh·yr",
        "Load amort":      f"{amort:g} yr",
    }
    suffix = common.param_suffix({
        "sol":    f"{plane.solar_cost_ann:.3g}",
        "bat":    f"{plane.batt_cost_ann:.3g}",
        "lamort": f"{amort:g}yr",
    })

    result = []

    for income in _INCOME_SLICES:
        slug = f"{income:g}".replace(".", "p")
        slice_params = {**params, "Income": f"${income:.3g}/kWh"}

        def make_fig(income=income, slug=slug, slice_params=slice_params):
            fig = render.Figure(figsize=(17, 5), dpi=render.DPI)
            render.FigureCanvasAgg(fig)
            axes = fig.subplots(1, 3)

            draw_slice(axes, plane, income)

            fig.suptitle(
                f"Load capex profiles — income = ${income:.3g}/kWh",
                fontsize=13,
            )
            fig.subplots_adjust(wspace=0.45, top=0.88)
            common.info(axes[2], fig, slice_params, mode="on")

            out = cfg.OUT_LOAD_CAPEX_PROFILES / f"load_capex_profiles_{slug}perkwh_{suffix}.png"
            return fig, out

        result.append((f"load_capex_profiles/{slug}perkwh", make_fig))

    return result


if __name__ == "__main__":
    import time
    from viz import render

    t0 = time.time()
    g = derived.load_served_grid()
    lplane = derived.load_plane(g)
    plan = figures(lplane, g)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
