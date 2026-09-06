"""New market-ladder-style chart: AVG $/Gbps/year vs. cumulative capacity deployed,
derived from the TAM-vs-satellites sweeps (country_tam_model.py /
country_tam_full_model.py) rather than market_ladder.py's per-country ARPU staircase.
Same axis units and the same per-generation cost reference lines as market_ladder.py
(GEN_COST_COLORS, _draw_cost_lines, both reused directly, not re-implemented), so the
two chart families are directly comparable -- but this curve is one BLENDED average
price (TAM / total deployed capacity), not a per-country ladder.

Mechanism: for each swept satellite count N, TAM(N) is total addressable market in
USD/month (summed across every country -- see the two TAM model docstrings for the
full pricing mechanism). Capacity deployed at N is N x v3's 1,024 Gbps/satellite
(capacity_density_model.V3_SCENARIO, the same figure market_ladder.py's secondary
axis and every serviceable-customers chart's Tbps axis already use). Avg price =
TAM(N) x 12 (annualized, to match cost_per_gbps_model's $/Gbps/YEAR basis) / capacity
deployed at N.

Built for BOTH TAM models, per explicit user instruction (2026-08-23, "Both"):
  - unconnected-only (country_tam_model.py) -- narrower demand base, TAM itself peaks
    then declines with N (see country_tam_charts.py), so this avg-price curve falls
    especially fast at high N (shrinking numerator AND growing denominator).
  - full-capture (country_tam_full_model.py) -- Starlink takes ALL addressable
    population's business, not just the unconnected slice; TAM saturates rather than
    declining, so this avg-price curve falls smoothly toward an asymptote instead.

Each gets a log-log and a linear version (4 charts total), following this project's
standing log+linear precedent (charts/equilibrium.py, charts/market_ladder.py).

Run: python charts/avg_price_market_ladder.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import capacity_density_model as cdm
import cost_per_gbps_model as cgm
import tam_model as tm
import equilibrium_model as em
from market_ladder import _draw_cost_lines, _human
from viz import render

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "market_ladder"

GBPS_PER_SAT = cdm.V3_SCENARIO.downlink_gbps_per_beam * cdm.V3_SCENARIO.beams_per_satellite  # 1,024

SAT_COUNTS_LOG = np.geomspace(100, 2_000_000, 30)
SAT_COUNTS_LINEAR = np.linspace(1, 200_000, 60)

CURVE_COLOR = {"unconnected": "#2ca25f", "full": "#6a51a3"}
CURVE_LABEL = {
    "unconnected": "Avg $/Gbps/yr (Unconnected Addressable Market)",
    "full": "Avg $/Gbps/yr (Total Addressable Market)",
}
def _avg_price_per_gbps_yr(tam_usd_per_month: np.ndarray, sat_counts: np.ndarray) -> np.ndarray:
    capacity_gbps = sat_counts * GBPS_PER_SAT
    return (tam_usd_per_month * 12.0) / capacity_gbps


def _draw_avg_price_curve(ax, capacity_gbps, avg_price, model_key):
    color = CURVE_COLOR[model_key]
    ax.plot(capacity_gbps, avg_price, color=color, linewidth=2.2, zorder=3, label=CURVE_LABEL[model_key])
    ax.fill_between(capacity_gbps, 0, avg_price, color=color, alpha=0.08, zorder=1)


def _draw_chart(ax, capacity_gbps, avg_price, econ, model_key, *, log_scale: bool):
    _draw_avg_price_curve(ax, capacity_gbps, avg_price, model_key)

    if log_scale:
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(capacity_gbps[0] * 0.9, capacity_gbps[-1] * 1.1)
        y_all = np.concatenate([avg_price, [
            g.cost_per_gbps_with_margin_usd / em.SATELLITE_LIFETIME_YEARS for g in econ]])
        ax.set_ylim(y_all.min() * 0.6, y_all.max() * 1.5)
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())
        scale_word = "log scale"
    else:
        ax.set_xlim(0, capacity_gbps[-1] * 1.03)
        # avg_price is NOT assumed monotonic (the unconnected-only TAM itself is
        # non-monotonic in N -- see country_tam_charts.py) -- use the curve's actual
        # max, not its value at N's left edge, which at very low N can be near zero
        # (almost nobody servable yet, so TAM(N) approx 0 there too).
        ax.set_ylim(0, avg_price.max() * 1.08)
        scale_word = "linear scale"

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _human(v)))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.set_xlabel(f"Cumulative capacity deployed, Gbps ({scale_word})")
    ax.set_ylabel(f"Avg $/Gbps/year ({scale_word})")
    ax.set_title("Avg $/Gbps/year vs. cumulative capacity deployed")

    secax = ax.secondary_xaxis("top", functions=(lambda x: x / GBPS_PER_SAT, lambda s: s * GBPS_PER_SAT))
    secax.set_xlabel(f"Cumulative v3 satellites ({GBPS_PER_SAT:,.0f} Gbps/sat)")
    secax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.1f}" if v < 10 else f"{v:,.0f}"))
    secax.xaxis.set_minor_formatter(mticker.NullFormatter())

    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    # Drawn LAST, after every other axes element (legend/secondary axis) is in place --
    # cost-line label positions are computed from ax.get_ylim(), which is already final
    # by this point, but keeping this call last avoids re-litigating the draw-order
    # question this project already hit once (see CLAUDE.md).
    skip_labels = () if log_scale else ("v3 (Starship end-state)",)
    _draw_cost_lines(ax, econ, side="left", skip_labels=skip_labels)
    return ax.figure


def fig_avg_price_log(sat_counts, tam, econ, model_key):
    fig, ax = render.new_figure(figsize=(13, 8))
    capacity_gbps = sat_counts * GBPS_PER_SAT
    avg_price = _avg_price_per_gbps_yr(tam, sat_counts)
    _draw_chart(ax, capacity_gbps, avg_price, econ, model_key, log_scale=True)
    return fig, OUT_ROOT / f"avg_price_per_gbps_vs_capacity_{model_key}.png"


def fig_avg_price_linear(sat_counts, tam, econ, model_key):
    fig, ax = render.new_figure(figsize=(13, 8))
    capacity_gbps = sat_counts * GBPS_PER_SAT
    avg_price = _avg_price_per_gbps_yr(tam, sat_counts)
    _draw_chart(ax, capacity_gbps, avg_price, econ, model_key, log_scale=False)
    return fig, OUT_ROOT / f"avg_price_per_gbps_vs_capacity_{model_key}_linear.png"


def main():
    econ = cgm.build_generation_economics()
    telecom_rows, household_size, tile, demand, pop_by_tile = tm.load_inputs(verbose=True)
    args = (telecom_rows, household_size, pop_by_tile, tile, demand)

    n_written = 0
    for model_key in ("unconnected", "full"):
        tam_log = tm.total_tam(tm.sweep_country_tam(SAT_COUNTS_LOG, *args, mode=model_key, verbose=True))
        fig, path = fig_avg_price_log(SAT_COUNTS_LOG, tam_log, econ, model_key)
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
        n_written += 1

        tam_linear = tm.total_tam(tm.sweep_country_tam(SAT_COUNTS_LINEAR, *args, mode=model_key, verbose=True))
        fig, path = fig_avg_price_linear(SAT_COUNTS_LINEAR, tam_linear, econ, model_key)
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
        n_written += 1

        avg_price_log = _avg_price_per_gbps_yr(tam_log, SAT_COUNTS_LOG)
        i_min, i_max = np.argmin(avg_price_log), np.argmax(avg_price_log)
        print(f"  [{model_key}] avg $/Gbps/yr range: ${avg_price_log[i_min]:,.0f} (N={SAT_COUNTS_LOG[i_min]:,.0f}) "
              f"to ${avg_price_log[i_max]:,.0f} (N={SAT_COUNTS_LOG[i_max]:,.0f})")

    print(f"wrote {n_written} charts")


if __name__ == "__main__":
    main()
