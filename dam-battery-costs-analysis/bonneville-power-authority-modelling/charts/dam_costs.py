"""$/MW (2025 USD) vs year for all dams with cost data in dam_costs.csv."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.ticker as mticker
import pandas as pd

import config as cfg
from charts import common
from viz import render
from viz.label_overlay import LabelPoint, place_labels_2d

SOURCE = "Source: Wikipedia / public records; CPI-adjusted to 2025 USD"

_REGION_COLORS = {
    "US":            "#1f77b4",
    "Canada":        "#d62728",
    "China":         "#2ca02c",
    "International": "#9467bd",
}
_REGION_ORDER = ["US", "Canada", "China", "International"]

_SHORT = {
    "Robert-Bourassa LG-2":    "LG-2",
    "Site C John Horgan Dam":  "Site C",
    "Grand Coulee Dam orig":   "Grand Coulee\n(orig)",
    "Grand Coulee 3rd PH":     "Grand Coulee\n(3rd PH)",
    "Bonneville Dam Ph1":      "Bonneville Ph1",
    "Bonneville Dam Ph2":      "Bonneville Ph2",
    "Robert Moses Niagara":    "R. Moses Niagara",
    "WAC Bennett Dam":         "WAC Bennett",
    "Churchill Falls GS":      "Churchill Falls",
    "Muskrat Falls GS":        "Muskrat Falls",
}

# Per-dam annotate offsets in points (dx, dy) from the dot.
# Positive dy = above; negative dy = below.  ha/va can also be overridden.
_OFFSETS: dict[str, tuple] = {
    # Right-edge Canadian — shift left
    "Muskrat Falls GS":        (-8,   6,  "right", "bottom"),
    "Site C John Horgan Dam":  (-8,  -8,  "right", "top"),
    "Keeyask GS":              (-8,   6,  "right", "bottom"),

    # Chinese 2010-2025 cluster — stagger around the dots
    "Three Gorges Dam":        (-8,   6,  "right", "bottom"),
    "Xiluodu Dam":             ( 6,  -8,  "left",  "top"),
    "Liyuan Dam":              ( 6,   6,  "left",  "bottom"),
    "Changheba Dam":           (-8,  -8,  "right", "top"),
    "Wudongde Dam":            (-8,   6,  "right", "bottom"),
    "Baihetan Dam":            ( 6,   6,  "left",  "bottom"),
    "Xiaolangdi Dam":          ( 6,   6,  "left",  "bottom"),

    # Early left-side dams that overlap each other
    "Hoover Dam":              ( 6,   8,  "left",  "bottom"),
    "Bonneville Dam Ph1":      (-8,   6,  "right", "bottom"),
    "Grand Coulee Dam orig":   ( 6,   6,  "left",  "bottom"),
    "Shasta Dam":              ( 6,  -8,  "left",  "top"),
    "Churchill Falls GS":      (-8,  -8,  "right", "top"),
    "Noxon Rapids Dam":        ( 6,  -8,  "left",  "top"),
    "Wanapum Dam":             ( 6,   6,  "left",  "bottom"),
    "Twin Falls GS":           ( 6,   6,  "left",  "bottom"),
    "WAC Bennett Dam":         ( 6,  -8,  "left",  "top"),
    "Robert Moses Niagara":    (-8,   6,  "right", "bottom"),

    # 1980s
    "Bonneville Dam Ph2":      ( 6,  10,  "left",  "bottom"),
    "Robert-Bourassa LG-2":    ( 6,  -8,  "left",  "top"),
    "Itaipu Dam":              (-8, -14,  "right", "top"),
}


def figure_cost_per_mw() -> tuple:
    data_path = cfg.PROJECT_DIR / "data" / "dam_costs.csv"
    df = pd.read_csv(data_path)
    df = df[df["has_cost_data"].astype(str).str.lower() == "true"].copy()
    df = df.sort_values("year_complete")

    fig, ax = render.new_figure(figsize=(15, 8))

    for region in _REGION_ORDER:
        sub = df[df["region_group"] == region]
        if sub.empty:
            continue
        ax.scatter(sub["year_complete"], sub["usd_per_mw_2025"],
                   color=_REGION_COLORS[region], marker="o", s=60,
                   zorder=4, label=region)

    for _, row in df.iterrows():
        label = _SHORT.get(row["name"], row["name"])
        color = _REGION_COLORS.get(row["region_group"], "grey")
        dx, dy, ha, va = _OFFSETS.get(row["name"], (6, 6, "left", "bottom"))
        ax.annotate(
            label,
            xy=(row["year_complete"], row["usd_per_mw_2025"]),
            xytext=(dx, dy), textcoords="offset points",
            fontsize=6.5, color=color, ha=ha, va=va,
            arrowprops=dict(arrowstyle="-", color=color, lw=0.5, alpha=0.5)
            if abs(dx) > 6 or abs(dy) > 6 else None,
        )

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda v, _: f"${v/1e6:.1f}M" if v >= 1e6
                         else f"${v/1e3:.0f}k" if v >= 1e3
                         else f"${v:.0f}"
        )
    )
    ax.set_xlabel("Year completed")
    ax.set_ylabel("Cost per MW (2025 USD)")
    ax.set_title("Hydroelectric dam construction cost per MW — 2025 USD")

    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, which="major", axis="y", alpha=0.3, linewidth=0.5)
    ax.grid(True, which="major", axis="x", alpha=0.2, linewidth=0.5)

    common.add_source(ax, SOURCE)
    common.add_watermark(ax)

    out = cfg.OUTPUT_DIR / "dam_costs_per_mw.png"
    return fig, out


def _short(name: str) -> str:
    """Short display name with any embedded newline flattened to a space."""
    return _SHORT.get(name, name).replace("\n", " ")


def figure_cost_per_mw_vs_capacity() -> tuple:
    """Scatter: cost per MW (2025 USD, log) vs installed capacity (MW, log).
    Each point labelled 'Name, year' with automatic de-collision."""
    data_path = cfg.PROJECT_DIR / "data" / "dam_costs.csv"
    df = pd.read_csv(data_path)
    df = df[df["has_cost_data"].astype(str).str.lower() == "true"].copy()
    df = df.sort_values("capacity_mw")

    fig, ax = render.new_figure(figsize=(15, 8))

    for region in _REGION_ORDER:
        sub = df[df["region_group"] == region]
        if sub.empty:
            continue
        ax.scatter(sub["capacity_mw"], sub["usd_per_mw_2025"],
                   color=_REGION_COLORS[region], marker="o", s=60,
                   zorder=4, label=region)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda v, _: f"${v/1e6:.1f}M" if v >= 1e6
                         else f"${v/1e3:.0f}k" if v >= 1e3
                         else f"${v:.0f}"
        )
    )
    ax.set_xlabel("Installed capacity (MW)")
    ax.set_ylabel("Cost per MW (2025 USD)")
    ax.set_title("Hydroelectric dam cost per MW vs installed capacity — 2025 USD")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, which="major", alpha=0.3, linewidth=0.5)
    ax.grid(True, which="minor", alpha=0.15, linewidth=0.4)

    common.add_source(ax, SOURCE)
    common.add_watermark(ax)

    # Labels: 'Name, year', coloured by region, auto-de-collided with leader lines.
    points = [
        LabelPoint(x=row["capacity_mw"], y=row["usd_per_mw_2025"],
                   text=f"{_short(row['name'])}, {int(row['year_complete'])}",
                   text_color=_REGION_COLORS.get(row["region_group"], "grey"))
        for _, row in df.iterrows()
    ]
    # High-capacity dams sit near the right edge → start their labels to the left.
    initial_offsets = {
        "Three":    (-0.07, 0.0),   # Three Gorges
        "Baihetan": (-0.06, 0.0),
        "Itaipu":   (-0.05, 0.0),
        "Xiluodu":  (-0.06, 0.0),
        "Wudongde": (-0.06, 0.0),
    }
    place_labels_2d(fig, ax, points, fontsize=6.5, initial_offsets=initial_offsets)

    out = cfg.OUTPUT_DIR / "dam_cost_per_mw_vs_capacity.png"
    return fig, out


if __name__ == "__main__":
    for build in (figure_cost_per_mw, figure_cost_per_mw_vs_capacity):
        fig, path = build()
        render.save_fig(fig, path)
        print(f"wrote {path}")
