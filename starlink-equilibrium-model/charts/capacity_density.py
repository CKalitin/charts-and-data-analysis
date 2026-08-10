"""Phase 3: satellite capacity & customer density constraint charts.

Two charts:
  1. Sensitivity of the max customer DENSITY ceiling to its assumptions (dedicated
     vs. contended bandwidth, download- vs. upload-limited, and the paper's own
     "tighter overlapping beams" alternative scenario).
  2. Max theoretical customers servable by latitude band -- Phase 2's satellite
     density by latitude (Gen1 only) x Phase 3's per-satellite customer cap. This is
     a raw multiplicative UPPER BOUND (ignores footprint overlap between neighboring
     satellites' beams -- see capacity_density_model.py docstring), not a precise
     count.

Run: python charts/capacity_density.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.ticker as mticker
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import capacity_density_model as cdm
import orbital_geometry as og
from viz import render, info_box

# Matches charts/coverage_map.py's INCLINATION_COLORS -- same shells, same colors,
# so a reader can visually cross-reference the two charts.
INCLINATION_COLORS = {53.0: "#4575b4", 53.2: "#4575b4", 70.0: "#1a9850", 97.6: "#d73027"}

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "capacity"
SOURCE_NOTE = "Source: satellite_capacity.md"


# --------------------------------------------------------------------------------------
# Chart 1: density-ceiling sensitivity to assumptions
# --------------------------------------------------------------------------------------
KM2_PER_SQ_MI = 2.58999


def fig_density_sensitivity():
    s = cdm.V2_MINI_BEAD_SCENARIO
    alt_scenario_per_km2 = 30 / KM2_PER_SQ_MI  # source states this directly in subscribers/sq mi
    scenarios = [
        ("Dedicated bandwidth\n(no contention)", cdm.max_customer_density_per_km2(s, dedicated=True)),
        ("20:1 contention\n(industry-standard, binding=upload)", cdm.max_customer_density_per_km2(s, dedicated=False)),
        ("Tighter overlapping beams\n(paper's alt. scenario, ~30/sq mi)", alt_scenario_per_km2),
    ]

    fig, ax = render.new_figure(figsize=(9, 6.5))
    labels = [x[0] for x in scenarios]
    vals_km2 = [x[1] for x in scenarios]
    colors = ["#4575b4", "#d73027", "#999999"]
    bars = ax.bar(labels, vals_km2, color=colors)
    ax.set_ylim(0, max(vals_km2) * 1.22)
    for b, v in zip(bars, vals_km2):
        ax.annotate(f"{v:.2f}/km2\n({v * KM2_PER_SQ_MI:.1f}/sq mi)",
                    xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 6), textcoords="offset points", ha="center", fontsize=9)
    ax.tick_params(axis="x", labelsize=7.8)

    ax.set_ylabel("Max subscriber density, per km2 (before saturation)")
    ax.set_title("Max subscriber density vs. capacity-model scenario")
    info_box.add_info_box(
        ax, fig, "v2 Mini, 550km, 1.5deg beamwidth. " + SOURCE_NOTE,
        mode="off", off_side="top", off_frac=0.14,
    )
    return fig, OUT_ROOT / "density_ceiling_sensitivity.png"


# --------------------------------------------------------------------------------------
# Chart 2: max theoretical customers servable by latitude band
# --------------------------------------------------------------------------------------
def fig_max_customers_by_latitude(shells):
    centers, by_shell = og.expected_sats_by_latitude(shells, bin_width_deg=1.0)
    total_sats_by_lat = np.sum(list(by_shell.values()), axis=0)

    s = cdm.V2_MINI_BEAD_SCENARIO
    per_sat_cap = cdm.max_customers_per_satellite(s)
    max_customers = total_sats_by_lat * per_sat_cap

    fig, ax = render.new_figure(figsize=(12, 7))
    # step="mid" makes the 1-degree bins visually explicit as a fine staircase rather
    # than a smooth curve, so the chart reads as "one bar per degree of latitude."
    ax.fill_between(centers, 1, max_customers, step="mid", color="#4575b4", alpha=0.7,
                    linewidth=0)
    ax.plot(centers, max_customers, drawstyle="steps-mid", color="#2c5488", linewidth=0.6)

    # Mark each shell's max latitude -- this is exactly where/why the spikes occur.
    seen = set()
    for shell in shells:
        incl = round(shell.inclination_deg, 1)
        max_lat = og.max_latitude_deg(shell.inclination_deg)
        key = round(max_lat, 1)
        if key in seen:
            continue
        seen.add(key)
        color = INCLINATION_COLORS.get(incl, "#888888")
        for sign in (1, -1):
            x = sign * max_lat
            ax.axvline(x, color=color, linestyle="--", linewidth=1, alpha=0.7, zorder=4)
            # Offset a few points to the side of the line (screen space, immune to the
            # axis-flip direction) so rotated text doesn't render directly on top of
            # the dashed line it's labelling.
            ax.annotate(f"{incl}deg max lat {max_lat:.1f}deg",
                       xy=(x, 0.02), xycoords=("data", "axes fraction"),
                       xytext=(5, 0), textcoords="offset points",
                       ha="left", va="bottom", fontsize=6.8, color=color, rotation=90, zorder=5)

    # Orientation references so the reader isn't just looking at bare numbers.
    for lat, label in [(0, "Equator"), (66.5, "Arctic/Antarctic\ncircle")]:
        signs = (1,) if lat == 0 else (1, -1)
        for sign in signs:
            ax.axvline(sign * lat, color="0.5", linestyle=":", linewidth=0.8, alpha=0.6, zorder=1)
            ax.text(sign * lat, 0.99, label, transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=7, color="0.4")

    ax.set_xlabel("Latitude (degrees) -- each point is ONE 1-degree-wide ring circling the whole globe")
    ax.set_ylabel("Max customers servable in that ring, at once (upper bound, log scale)")
    ax.set_title("Max theoretical customers by latitude, Gen1 satellites x v2 Mini capacity cap")
    ax.set_yscale("log")
    ax.set_xlim(-90, 90)
    ax.invert_xaxis()  # north (positive) on the left, matching the project convention
    # Log scale needs a nonzero floor -- the true values approach 0 beyond each shell's
    # max latitude, which would need infinite vertical space to render on a log axis.
    # Cut off well above that (just under the smallest MEANINGFUL value, ~20.7K) so the
    # chart spends its space on the data that actually varies, not the empty tail.
    ax.set_ylim(1e4, max_customers.max() * 1.5)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(15))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

    info_box.add_info_box(
        ax, fig, "Upper bound.\nSource:\nsatellite_\ncapacity.md",
        mode="off", off_side="right", off_frac=0.12, fontsize=7.8,
    )
    return fig, OUT_ROOT / "max_customers_by_latitude.png"


def figures(shells):
    return [
        ("density_sensitivity", fig_density_sensitivity),
        ("max_customers_by_latitude", lambda: fig_max_customers_by_latitude(shells)),
    ]


def main():
    shells = og.load_shells_with_full_geometry()
    plan = figures(shells)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"wrote {len(plan)} charts")

    s = cdm.V2_MINI_BEAD_SCENARIO
    per_sat = cdm.max_customers_per_satellite(s)
    gen1_total_sats = sum(sh.total_sats for sh in shells)
    gen1_max = gen1_total_sats * per_sat
    current_total_sats = 10900  # see starlink_shells.md, all generations, 2026-08-06
    current_max = current_total_sats * per_sat

    import csv as _csv
    telecom_csv = Path(__file__).resolve().parent.parent / "data" / "telecom_market_by_country.csv"
    with open(telecom_csv, encoding="utf-8") as f:
        global_unconnected = sum(float(r["unconnected_population_est_coverage_corrected"])
                                 for r in _csv.DictReader(f)
                                 if r["unconnected_population_est_coverage_corrected"])
    gap_multiple = global_unconnected / current_max

    print(f"\nNOTE: at the v2-Mini-class capacity ceiling (~{per_sat:,.0f} customers/satellite, "
          f"20:1 contention, upload-limited to meet 100/20 Mbps), the Gen1 constellation alone "
          f"({gen1_total_sats:,} sats) caps out at ~{gen1_max/1e6:.1f}M customers GLOBALLY -- and "
          f"even naively scaling to the full current fleet (~{current_total_sats:,} sats, all "
          f"generations, ignoring that most don't have this confirmed capacity) caps out at "
          f"~{current_max/1e6:.1f}M. Phase 1 found ~{global_unconnected/1e9:.2f}B people unconnected "
          f"worldwide (coverage-gap corrected, see telecom_market_by_country.md). This is a "
          f"~{gap_multiple:.0f}x gap between theoretical max capacity and the addressable "
          f"unserved population -- capacity, not demand, may be the binding constraint on "
          f"Starlink's achievable market size, which matters directly for Phase 5's equilibrium "
          f"model. This upper bound also ignores beam-footprint overlap between satellites, which "
          f"would tighten it further.")


if __name__ == "__main__":
    main()
