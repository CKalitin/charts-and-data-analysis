"""Chart E — LCOE and utilisation vs solar fraction (fixed total resource).

Parametrises ALL (S, B) builds by a single number α ∈ (0, 1]:
    S = α × T   [kW],   B = (1 − α) × T   [kWh]
where T is the total resource allocated ("1 kW/kWh budget").

KEY ASSUMPTION: this is meaningful as a cost-fraction axis only when
C_S [$/kW·yr] = C_B [$/kWh·yr].  When both cost the same per unit,
equal units = equal dollars and total annual cost = C × T = constant,
so LCOE = C·T / served and the curve is the inverse of utilisation.

At the extremes:
  α → 0  (pure battery, no solar): served → 0, LCOE → ∞.  The curve
          shoots off the top of the log LCOE axis — the correct visual.
  α = 1  (pure solar, no battery): serves only during daylight → ~50%
          utilisation, finite LCOE, but far from optimal.

The OPTIMAL α is NOT 0.5.  At our site (CF ≈ 25 %), it is ≈ 0.34 —
roughly 34 % solar / 66 % battery by unit count.  The mismatch traces
directly to the capacity factor: solar generates ~6 peak hours/day, so
you need ≈ 18/6 = 3× more storage than generation capacity (in kWh/kW)
to bridge overnight gaps.  With equal costs, the LCOE-optimal build is
battery-heavy even when components cost the same per unit.
"""

from __future__ import annotations

import sys
from pathlib import Path

if not __package__:  # running as a script — add project root to path
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

# Colour cycle for the T-curves (ordered: small → large total resource).
_COLOURS = ["#4393c3", "#2ca25f", "#e07b00", "#c51b7d"]

# Clamp LCOE display at this value to prevent the α→0 singularity from
# compressing the interesting part of the curve.
_LCOE_Y_MAX = 2.0  # $/kWh — everything above is "unviable", shown as dashed line


def _params(grid, sweeps: list[derived.SolarFractionSweep]) -> dict[str, str]:
    s = sweeps[0]
    d: dict[str, str] = {
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Load": f"{cfg.LOAD_KW:g} kW constant",
        "Solar cost": f"${s.solar_cost_ann:.3g}/kW·yr  (${s.solar_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kW)",
        "Battery cost": f"${s.batt_cost_ann:.3g}/kWh·yr  (${s.batt_cost_ann * cfg.AMORTIZATION_YEARS:.0f}/kWh)",
        "Amortization": f"{cfg.AMORTIZATION_YEARS:g} yr",
        "Round-trip eff.": f"{cfg.ROUND_TRIP_EFFICIENCY:.0%}",
    }
    return d


def draw(ax, sweeps: list[derived.SolarFractionSweep], grid) -> None:
    """Plot LCOE and utilisation vs solar fraction for several T values."""
    ax_lcoe = ax.twinx()

    alpha_opt_vals = []

    for sweep, color in zip(sweeps, _COLOURS):
        T = sweep.total_units
        alpha = sweep.alpha

        # ---- utilisation curve (left axis) --------------------------------
        ax.plot(alpha, sweep.utilization * 100.0,
                color=color, linewidth=2.0, label=f"Utilization  T={T:g}", zorder=3)

        # Optimal point marker on utilisation axis.
        if np.isfinite(sweep.opt_alpha):
            ax.scatter([sweep.opt_alpha], [sweep.opt_utilization * 100.0],
                       s=70, marker="*", color=color, edgecolors="black",
                       linewidth=0.7, zorder=5)
            alpha_opt_vals.append((sweep.opt_alpha, sweep.opt_utilization * 100.0,
                                   sweep.opt_lcoe, T, color))

        # ---- LCOE curve (right axis, log scale) ----------------------------
        lcoe_clipped = np.clip(sweep.lcoe, None, _LCOE_Y_MAX * 1.5)
        lcoe_visible = np.where(sweep.lcoe <= _LCOE_Y_MAX, sweep.lcoe, np.nan)
        lcoe_overflow = np.where(sweep.lcoe > _LCOE_Y_MAX, lcoe_clipped, np.nan)

        # Label only the visible portion so it appears in the legend.
        ax_lcoe.plot(alpha, lcoe_visible,
                     color=color, linewidth=1.4, linestyle="--", alpha=0.75,
                     label=f"LCOE  T={T:g}  (right axis)", zorder=2)
        ax_lcoe.plot(alpha, lcoe_overflow,
                     color=color, linewidth=1.0, linestyle=":", alpha=0.40, zorder=2)

    # ---- vertical line at the common asymptotic optimal fraction -----------
    if alpha_opt_vals:
        # Highlight the large-T optimum as the "asymptotic" correct split.
        best_T = max(alpha_opt_vals, key=lambda t: t[3])
        a_star = best_T[0]
        #ax.axvline(a_star, color="gray", linewidth=0.9, linestyle="--", alpha=0.6, zorder=1)
        #ax.text(a_star + 0.01, 5,
        #        f"α* ≈ {a_star:.2f}\n({a_star * 100:.0f}% solar)",
        #        fontsize=7.5, color="gray", va="bottom")

    # ---- axes config -------------------------------------------------------
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 103)
    ax.set_xlabel("Solar fraction  α = S / (S + B)   [← more battery  |  more solar →]")
    ax.set_ylabel(axis_label("utilization_pct"))
    ax.grid(True, which="major", linestyle="--", alpha=0.35)

    # x-axis tick labels: also show battery fraction beneath.
    ax.xaxis.set_major_locator(mticker.MultipleLocator(0.1))
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:.0%}")
    )

    # LCOE twin axis.
    ax_lcoe.set_yscale("log")
    ax_lcoe.set_ylim(0.001, _LCOE_Y_MAX)
    ax_lcoe.set_ylabel(axis_label("lcoe") + "  (dashed; dotted = above axis limit)")
    ax_lcoe.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: common._dollar_fmt(v))
    )
    ax_lcoe.yaxis.set_minor_formatter(mticker.NullFormatter())

    # Combined legend: handles from primary (utilization) + twin (LCOE) axes.
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax_lcoe.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2,
              loc="upper left", fontsize=7.5, framealpha=0.88, ncol=2,
              title="Solid = utilization (left)   |   Dashed = LCOE (right, log)",
              title_fontsize=7)
    ax.set_title(
        "Utilisation (solid) and LCOE (dashed) vs solar fraction  —  fixed total kW + kWh"
    )

    # Mark demand ceiling.
    ax.axhline(100, color="black", linewidth=0.7, linestyle=":", alpha=0.5)


def draw_util_only(ax, sweeps: list[derived.SolarFractionSweep], grid) -> None:
    """Plot utilisation vs solar fraction only (no LCOE lines)."""
    for sweep, color in zip(sweeps, _COLOURS):
        T = sweep.total_units
        alpha = sweep.alpha

        # ---- utilisation curve --------------------------------
        ax.plot(alpha, sweep.utilization * 100.0,
                color=color, linewidth=2.0, label=f"Utilization  T={T:g}", zorder=3)

        # Optimal point marker.
        if np.isfinite(sweep.opt_alpha):
            ax.scatter([sweep.opt_alpha], [sweep.opt_utilization * 100.0],
                       s=70, marker="*", color=color, edgecolors="black",
                       linewidth=0.7, zorder=5)

    # ---- axes config -------------------------------------------------------
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 103)
    ax.set_xlabel("Solar fraction  α = S / (S + B)   [← more battery  |  more solar →]")
    ax.set_ylabel(axis_label("utilization_pct"))
    ax.grid(True, which="major", linestyle="--", alpha=0.35)

    # x-axis tick labels.
    ax.xaxis.set_major_locator(mticker.MultipleLocator(0.1))
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:.0%}")
    )

    ax.legend(loc="upper left", fontsize=8, framealpha=0.88)
    ax.set_title("Utilisation vs solar fraction  —  fixed total kW + kWh")

    # Mark demand ceiling.
    ax.axhline(100, color="black", linewidth=0.7, linestyle=":", alpha=0.5)


def figures(sweeps: list[derived.SolarFractionSweep], grid):
    from viz import render

    params = _params(grid, sweeps)
    T_str = "+".join(f"{s.total_units:g}" for s in sweeps)
    suffix = common.param_suffix({
        "T": T_str,
        "sol": f"{sweeps[0].solar_cost_ann:.3g}",
        "bat": f"{sweeps[0].batt_cost_ann:.3g}",
        "amort": f"{cfg.AMORTIZATION_YEARS:g}yr",
    })

    def fig_fn():
        fig, ax = render.new_figure(figsize=(11, 6))
        draw(ax, sweeps, grid)
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_SOLAR_FRACTION / f"lcoe_vs_fraction_{suffix}.png"

    def fig_util_only():
        fig, ax = render.new_figure(figsize=(11, 6))
        draw_util_only(ax, sweeps, grid)
        common.info(ax, fig, params, mode="on")
        common.watermark(ax, fig)
        return fig, cfg.OUT_SOLAR_FRACTION / f"util_vs_fraction_{suffix}.png"

    return [("solar_fraction/lcoe_vs_fraction", fig_fn), ("solar_fraction/util_vs_fraction", fig_util_only)]


if __name__ == "__main__":
    import time

    import config as cfg
    import derived
    from viz import render

    t0 = time.time()
    grid = derived.load_served_grid()
    sf_sweeps = [derived.solar_fraction_sweep(grid, T) for T in cfg.SOLAR_FRACTION_TOTAL_UNITS]
    plan = figures(sf_sweeps, grid)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
