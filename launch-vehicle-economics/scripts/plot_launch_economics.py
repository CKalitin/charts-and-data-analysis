"""Launch vehicle capex vs opex scatter plots.

Reads data/launch_vehicles.csv (one row per vehicle, every sourced dollar figure kept in
its original nominal/quoted-year form -- see data/sources.md for full citations) and
produces four log-log scatter figures into results/:

  1. capex_program_vs_opex_per_launch.png   -- total program cost        vs $/launch
  2. capex_first_launch_vs_opex_per_launch.png -- cost through first launch vs $/launch
  3. capex_program_vs_opex_per_kg.png       -- total program cost        vs $/kg to LEO
  4. capex_first_launch_vs_opex_per_kg.png  -- cost through first launch vs $/kg to LEO

Two capex figures exist per opex metric because "total program cost" and "cost through
first launch" are NOT the same quantity (a NASA/GAO/DDT&E-style figure vs. a whole-program
figure that can include decades of production and infrastructure spend) -- mixing them on
one axis would be comparing apples to oranges. Vehicles lacking a given capex figure are
simply absent from that particular chart (see console output / README for the list).

All dollar figures are converted to 2026 USD via the BLS CPI-U annual-average index
(cpi.py) SOLELY so that a 1959 Atlas program and a 2026 Neutron estimate sit on a
comparable axis; this is a blunt macro deflator, not a space-cost-specific index -- treat
the resulting values as illustrative, not authoritative "real cost" figures.

Marker SHAPE encodes which cost concept the $/launch (and derived $/kg) figure represents,
since that is itself a second apples/oranges axis (marginal/incremental cost to the
operator vs. a fully-loaded average cost vs. a commercial/contract price including margin
and, for government vehicles, mission-assurance overhead). Marker COLOR encodes country/
program origin.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from cpi import to_2026_usd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_CSV = PROJECT_DIR / "data" / "launch_vehicles.csv"
OUT_DIR = PROJECT_DIR / "results"

SOURCE_NOTE = (
    "Sources: NASA, GAO, NASA OIG, company/SEC filings, Lok Sabha replies, RAND, trade "
    "press (SpaceNews, Ars Technica, Payload Research, The Planetary Society, Spaceflight "
    "Now) -- full citation per data point in data/sources.md. Dollar figures inflated to "
    "2026 USD via BLS CPI-U (blunt macro deflator, not a launch-cost-specific index)."
)

# Fixed categorical color order (colorblind-checked qualitative set), assigned by country.
COUNTRY_COLORS = {
    "USA":            "#1f77b4",
    "Russia/USSR":    "#d62728",
    "Japan":          "#2ca02c",
    "India":          "#ff7f0e",
}
COUNTRY_ORDER = ["USA", "Russia/USSR", "Japan", "India"]

# Marker shape encodes which cost CONCEPT the opex figure represents -- picked in this
# priority order per vehicle (see _pick_opex below): marginal/incremental cost is the
# closest analog to "opex" in a fixed-vs-variable-cost sense, so it's preferred when
# available; a fully-loaded average is the next best "true cost" concept; a commercial
# or government contract PRICE (which bakes in margin / mission-assurance overhead) is
# used only when no cost-basis figure exists.
BASIS_MARKERS = {
    "marginal cost":       "o",
    "fully-loaded cost":   "s",
    "commercial/contract price": "^",
}
BASIS_ORDER = ["marginal cost", "fully-loaded cost", "commercial/contract price"]

# Representative single year for CPI conversion where the CSV's *_year field is a range
# or textual description (e.g. "then-year, summed FY1972-1984") rather than one integer.
# These are approximations -- seetheir data/sources.md caveats. Keyed by (vehicle, field).
YEAR_OVERRIDES = {
    ("Space Shuttle (STS)", "capex_first_launch_year"): 1978,
    ("SLS (Space Launch System)", "capex_program_year"): 2022,
    ("SLS (Space Launch System)", "capex_first_launch_year"): 2022,
    ("Saturn V", "capex_program_year"): 1966,
    ("Titan IV", "capex_program_year"): 1990,
    ("Titan II GLV (Gemini Launch Vehicle)", "capex_program_year"): 1964,
    ("Titan II GLV (Gemini Launch Vehicle)", "capex_first_launch_year"): 1962,
}

# Manual per-point label offsets (dx, dy in points, ha, va) to de-collide the crowded
# clusters. Anything not listed gets a small default offset.
_DEFAULT_OFFSET = (6, 6, "left", "bottom")
_LABEL_OFFSETS = {
    "Falcon 9 (reusable, Block 5)":      (6, 6, "left", "bottom"),
    "Falcon Heavy":                      (6, -8, "left", "top"),
    "Starship (expendable)":             (-8, 6, "right", "bottom"),
    "Antares":                           (6, 6, "left", "bottom"),
    "Space Shuttle":                     (6, 6, "left", "bottom"),
    "SLS":                               (6, -8, "left", "top"),
    "Saturn V":                          (-8, 6, "right", "bottom"),
    "Titan IV":                          (6, 6, "left", "bottom"),
    "Titan II GLV":                      (-8, -8, "right", "top"),
    "Original Atlas":                    (6, 6, "left", "bottom"),
    "Atlas V":                           (6, -8, "left", "top"),
    "Delta IV Heavy":                    (-8, 6, "right", "bottom"),
    "Neutron (predicted)":               (10, -14, "left", "top"),
    "New Glenn":                         (6, -8, "left", "top"),
    "Soyuz":                             (6, 6, "left", "bottom"),
    "Proton":                            (-8, -8, "right", "top"),
    "H-II/H-IIA":                        (6, 6, "left", "bottom"),
    "H3":                                (6, -8, "left", "top"),
    "PSLV":                              (-8, 6, "right", "bottom"),
    "GSLV Mk II":                        (6, 6, "left", "bottom"),
    "GSLV Mk III / LVM3":                (-10, -18, "right", "top"),
    "Falcon 9 v1.0":                     (10, 10, "left", "bottom"),
}

_SHORT = {
    "Starship (expendable, pre-IFT-1 scope)": "Starship (expendable)",
    "Titan II GLV (Gemini Launch Vehicle)": "Titan II GLV",
    "Original Atlas (SM-65 / Atlas D, Mercury-Atlas era)": "Original Atlas",
    "Delta IV (Medium & Heavy)": "Delta IV Heavy",
    "Neutron (Rocket Lab, PRE-FIRST-FLIGHT / predicted)": "Neutron (predicted)",
    "New Glenn": "New Glenn",
    "Space Shuttle (STS)": "Space Shuttle",
    "SLS (Space Launch System)": "SLS",
    "H-II / H-IIA": "H-II/H-IIA",
    "GSLV Mk III / LVM3 (bonus: better-documented sibling of GSLV)": "GSLV Mk III / LVM3",
}


def _short(name: str) -> str:
    return _SHORT.get(name, name)


def _year_for(row: pd.Series, field: str):
    override = YEAR_OVERRIDES.get((row["vehicle"], field))
    if override is not None:
        return override
    val = row[field]
    if pd.isna(val):
        return None
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def _pick_opex(row: pd.Series):
    """Return (nominal_usd, year, basis_label) using the marginal > fully-loaded >
    price priority described in the module docstring, or (None, None, None)."""
    if pd.notna(row["opex_marginal_usd"]):
        return row["opex_marginal_usd"], _year_for(row, "opex_marginal_year"), "marginal cost"
    if pd.notna(row["opex_fully_loaded_usd"]):
        return row["opex_fully_loaded_usd"], _year_for(row, "opex_fully_loaded_year"), "fully-loaded cost"
    if pd.notna(row["opex_price_usd"]):
        return row["opex_price_usd"], _year_for(row, "opex_price_year"), "commercial/contract price"
    return None, None, None


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_CSV)

    opex_vals, opex_years, opex_basis = [], [], []
    for _, r in df.iterrows():
        v, y, b = _pick_opex(r)
        opex_vals.append(v)
        opex_years.append(y)
        opex_basis.append(b)
    df["opex_used_usd"] = opex_vals
    df["opex_used_year"] = opex_years
    df["opex_used_basis"] = opex_basis
    df["opex_used_2026usd"] = [
        to_2026_usd(v, y) if v is not None and y is not None else None
        for v, y in zip(opex_vals, opex_years)
    ]

    df["capex_program_2026usd"] = [
        to_2026_usd(r["capex_program_usd"], _year_for(r, "capex_program_year"))
        if pd.notna(r["capex_program_usd"]) else None
        for _, r in df.iterrows()
    ]
    df["capex_first_launch_2026usd"] = [
        to_2026_usd(r["capex_first_launch_usd"], _year_for(r, "capex_first_launch_year"))
        if pd.notna(r["capex_first_launch_usd"]) else None
        for _, r in df.iterrows()
    ]

    # $/kg re-derived from the CPI-adjusted opex figure (rather than CPI-adjusting the
    # already-nominal $/kg column) so the same inflation basis applies consistently.
    df["opex_per_kg_2026usd"] = [
        (row["opex_used_2026usd"] / row["payload_leo_kg"])
        if row["opex_used_2026usd"] is not None and pd.notna(row["payload_leo_kg"])
        else None
        for _, row in df.iterrows()
    ]

    return df


def _dollar_fmt(v, _pos=None):
    if v >= 1e9:
        return f"${v/1e9:.0f}B"
    if v >= 1e6:
        return f"${v/1e6:.0f}M"
    if v >= 1e3:
        return f"${v/1e3:.0f}k"
    return f"${v:.0f}"


def _new_fig():
    fig, ax = plt.subplots(figsize=(15, 9))
    return fig, ax


def _scatter(ax, df: pd.DataFrame, xcol: str, ycol: str, label_key: dict):
    plotted = df.dropna(subset=[xcol, ycol]).copy()
    for country in COUNTRY_ORDER:
        for basis in BASIS_ORDER:
            sub = plotted[(plotted["country"] == country) & (plotted["opex_used_basis"] == basis)]
            if sub.empty:
                continue
            ax.scatter(
                sub[xcol], sub[ycol],
                color=COUNTRY_COLORS[country], marker=BASIS_MARKERS[basis],
                s=90, zorder=4, edgecolor="white", linewidth=0.6,
                label=None,
            )
    for _, row in plotted.iterrows():
        label = _short(row["vehicle"])
        dx, dy, ha, va = _LABEL_OFFSETS.get(label, _DEFAULT_OFFSET)
        ax.annotate(
            label, xy=(row[xcol], row[ycol]), xytext=(dx, dy), textcoords="offset points",
            fontsize=7, color=COUNTRY_COLORS.get(row["country"], "grey"), ha=ha, va=va,
        )
    return plotted


def _legend(ax):
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker="o", linestyle="", color=COUNTRY_COLORS[c], markersize=8, label=c)
        for c in COUNTRY_ORDER
    ] + [
        Line2D([0], [0], marker=BASIS_MARKERS[b], linestyle="", color="0.35", markersize=8, label=b)
        for b in BASIS_ORDER
    ]
    # Placed OUTSIDE the axes (to the right) so it never overlaps a data point or label,
    # regardless of which corner of a given chart happens to be crowded.
    ax.legend(handles=handles, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0),
              ncol=1, framealpha=0.9, borderaxespad=0,
              title="Color = country/program\nShape = opex cost basis", title_fontsize=8)


def _expand_log_limits(ax, factor=1.35):
    """Pad autoscaled log-log limits so edge/extreme points aren't clipped by the axes
    border and their labels have room to render inside the figure."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    ax.set_xlim(x0 / factor, x1 * factor)
    ax.set_ylim(y0 / factor, y1 * factor)


def _finish(fig, ax, xlabel, ylabel, title, out_name):
    ax.set_xscale("log")
    ax.set_yscale("log")
    _expand_log_limits(ax)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_dollar_fmt))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_dollar_fmt))
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="major", alpha=0.3, linewidth=0.5)
    ax.grid(True, which="minor", alpha=0.12, linewidth=0.4)
    _legend(ax)
    fig.text(0.5, 0.01, SOURCE_NOTE, ha="center", va="bottom", fontsize=7, color="0.35", wrap=True)
    fig.tight_layout(rect=(0, 0.035, 0.85, 1))
    out = OUT_DIR / out_name
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"wrote {out}")


def figure_capex_program_vs_opex_per_launch(df):
    fig, ax = _new_fig()
    _scatter(ax, df, "capex_program_2026usd", "opex_used_2026usd", _LABEL_OFFSETS)
    _finish(
        fig, ax,
        "Total program capex (2026 USD, log)", "Cost per launch (2026 USD, log)",
        "Launch vehicle economics: total program cost vs. cost per launch",
        "capex_program_vs_opex_per_launch.png",
    )


def figure_capex_first_launch_vs_opex_per_launch(df):
    fig, ax = _new_fig()
    _scatter(ax, df, "capex_first_launch_2026usd", "opex_used_2026usd", _LABEL_OFFSETS)
    _finish(
        fig, ax,
        "Capex through first launch (2026 USD, log)", "Cost per launch (2026 USD, log)",
        "Launch vehicle economics: development cost through first launch vs. cost per launch",
        "capex_first_launch_vs_opex_per_launch.png",
    )


def figure_capex_program_vs_opex_per_kg(df):
    fig, ax = _new_fig()
    _scatter(ax, df, "capex_program_2026usd", "opex_per_kg_2026usd", _LABEL_OFFSETS)
    _finish(
        fig, ax,
        "Total program capex (2026 USD, log)", "Cost per kg to LEO (2026 USD, log)",
        "Launch vehicle economics: total program cost vs. $/kg to LEO",
        "capex_program_vs_opex_per_kg.png",
    )


def figure_capex_first_launch_vs_opex_per_kg(df):
    fig, ax = _new_fig()
    _scatter(ax, df, "capex_first_launch_2026usd", "opex_per_kg_2026usd", _LABEL_OFFSETS)
    _finish(
        fig, ax,
        "Capex through first launch (2026 USD, log)", "Cost per kg to LEO (2026 USD, log)",
        "Launch vehicle economics: development cost through first launch vs. $/kg to LEO",
        "capex_first_launch_vs_opex_per_kg.png",
    )


def _report_gaps(df):
    no_program = df.loc[df["capex_program_usd"].isna(), "vehicle"].tolist()
    no_first = df.loc[df["capex_first_launch_usd"].isna(), "vehicle"].tolist()
    no_opex = df.loc[df["opex_used_usd"].isna(), "vehicle"].tolist()
    no_kg = df.loc[df["opex_per_kg_2026usd"].isna(), "vehicle"].tolist()
    print("\nVehicles missing total-program capex (excluded from those charts):")
    for v in no_program:
        print(f"  - {v}")
    print("\nVehicles missing to-first-launch capex (excluded from those charts):")
    for v in no_first:
        print(f"  - {v}")
    if no_opex:
        print("\nVehicles missing ANY opex figure (excluded from all charts):")
        for v in no_opex:
            print(f"  - {v}")
    if no_kg:
        print("\nVehicles missing $/kg (excluded from $/kg charts):")
        for v in no_kg:
            print(f"  - {v}")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()
    figure_capex_program_vs_opex_per_launch(data)
    figure_capex_first_launch_vs_opex_per_launch(data)
    figure_capex_program_vs_opex_per_kg(data)
    figure_capex_first_launch_vs_opex_per_kg(data)
    _report_gaps(data)
