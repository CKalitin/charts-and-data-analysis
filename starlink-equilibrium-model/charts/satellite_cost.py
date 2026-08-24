"""Phase 4: Starlink cost-to-orbit per Gbps of delivered capacity, by generation --
the user's chosen cost metric ("$/Gbps. Hard stop."), combining manufacturing cost +
launch cost (see cost_per_gbps_model.py for the full methodology and the user's
explicit decisions this implements: launch-cost pairing, "latest" mfg cost only,
20% required margin). Also keeps the independent cost-per-Gbps industry trend
(ARK Invest / Wright's Law) as a second, cross-check chart.

Run: python charts/satellite_cost.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cost_per_gbps_model as cgm
from viz import render, info_box

DATA = Path(__file__).resolve().parent.parent / "data"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "cost"

GEN_COLORS = {"v1.0": "#4575b4", "v1.5": "#74add1", "v2_mini": "#fee090", "v3": "#d73027"}


def fig_cost_per_gbps_by_generation():
    econ = cgm.build_generation_economics()

    fig, ax = render.new_figure(figsize=(11, 6.5))
    labels = [g.label for g in econ]
    base = [g.cost_per_gbps_usd for g in econ]
    with_margin = [g.cost_per_gbps_with_margin_usd for g in econ]
    colors = [GEN_COLORS[g.generation] for g in econ]

    x = range(len(econ))
    ax.bar(x, base, color=colors, label="Cost to orbit per Gbps")
    for i, (b, m) in enumerate(zip(base, with_margin)):
        ax.plot([i - 0.4, i + 0.4], [m, m], color="black", linewidth=1.6, linestyle="--", zorder=5)
        ax.annotate(f"${b:,.0f}", xy=(i, b), xytext=(0, 5), textcoords="offset points",
                    ha="center", fontsize=8.5)
        # Explicit $ value on the margin line itself -- on a log axis, a constant
        # PERCENTAGE margin renders as a constant PIXEL gap above every bar (equal
        # ratios are equal log-distances), which looks identical to a constant
        # dollar offset even though it isn't. Label the actual number so it's
        # unambiguous rather than relying on the eye to read a log-scale gap.
        ax.annotate(f"${m:,.0f} (+20%)", xy=(i, m), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=7.5, color="0.25")
    ax.plot([], [], color="black", linewidth=1.6, linestyle="--", label="+ 20% required margin")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_yscale("log")
    ax.set_ylabel("Cost to orbit per Gbps, USD (log scale)")
    ax.set_title("Starlink cost-to-orbit per Gbps, by generation (mfg + launch cost)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.legend(loc="upper right", fontsize=9)

    info_box.add_info_box(
        ax, fig,
        "v1.5, v2 full excluded: no published capacity figure.\n"
        "Source: Quilty Space (SpaceNews); New Space Economy",
        mode="on",
    )
    return fig, OUT_ROOT / "cost_per_gbps_by_generation.png"


def load_gbps_trend_rows():
    with open(DATA / "starlink_cost_per_gbps.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fig_cost_per_gbps_trend(rows):
    fig, ax = render.new_figure(figsize=(9, 6))
    dates = [int(r["date"]) for r in rows]
    costs = [float(r["cost_usd_per_gbps"]) for r in rows]
    is_forecast = [r["confidence"] == "forecast_not_actual" for r in rows]

    real_x = [d for d, f in zip(dates, is_forecast) if not f]
    real_y = [c for c, f in zip(costs, is_forecast) if not f]
    ax.plot(real_x, real_y, "o-", color="#4575b4", linewidth=2, markersize=8, label="Observed")
    fc_x = [dates[-2], dates[-1]]
    fc_y = [costs[-2], costs[-1]]
    ax.plot(fc_x, fc_y, "o--", color="#d73027", linewidth=2, markersize=8, label="ARK Invest forecast (not actual)")

    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Satellite bandwidth cost, $/Gbps (log scale)")
    ax.set_title("Satellite bandwidth cost, $/Gbps vs. year")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.legend(loc="upper right", fontsize=9)

    for d, c in zip(dates, costs):
        ax.annotate(f"${c:,.0f}", xy=(d, c), xytext=(0, -14), textcoords="offset points",
                    ha="center", fontsize=8)

    info_box.add_info_box(
        ax, fig,
        "Industry-wide trend, not Starlink-specific. 2028 is a forecast.\n"
        "Source: Gale Pooley (Cato Institute); ARK Invest",
        mode="on",
    )
    return fig, OUT_ROOT / "satellite_cost_per_gbps_trend.png"


def figures():
    gbps_rows = load_gbps_trend_rows()
    return [
        ("cost_per_gbps_by_generation", fig_cost_per_gbps_by_generation),
        ("cost_per_gbps_trend", lambda: fig_cost_per_gbps_trend(gbps_rows)),
    ]


def main():
    plan = figures()
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")

    print("\nCost-to-orbit per Gbps by generation (latest mfg cost, 20% margin):")
    for g in cgm.build_generation_economics():
        print(f"  {g.label}: ${g.cost_per_gbps_usd:,.0f}/Gbps (${g.cost_per_gbps_with_margin_usd:,.0f} w/ margin)")


if __name__ == "__main__":
    main()
