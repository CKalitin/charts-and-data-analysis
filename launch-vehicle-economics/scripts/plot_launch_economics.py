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
one axis would be comparing apples to oranges.

EVERY vehicle that has at least one of the two coordinates for a given chart is plotted on
that chart -- a vehicle is never dropped just because one axis is undocumented (e.g. Soyuz
and Proton have well-documented commercial launch prices but no public capex figure at all,
for either basis: Soviet-era ruble accounting under a non-convertible currency makes any
dollar figure for their original development cost methodologically unreliable). Vehicles
missing one coordinate are placed in a shaded "not publicly disclosed" lane along the
relevant axis, clearly separated from the real log-scale data by a dashed boundary and an
axis-label callout, rather than being silently omitted. A vehicle is only absent from a
chart if BOTH of its coordinates for that chart are undocumented (nothing to plot) -- see
the console gap report / README for exactly which vehicles that applies to, chart by chart.

All dollar figures are converted to 2026 USD via the BLS CPI-U annual-average index
(cpi.py) SOLELY so that a 1959 Atlas program and a 2026 Neutron estimate sit on a
comparable axis; this is a blunt macro deflator, not a space-cost-specific index -- treat
the resulting values as illustrative, not authoritative "real cost" figures.

Marker SHAPE encodes which cost concept the $/launch (and derived $/kg) figure represents,
since that is itself a second apples/oranges axis (marginal/incremental cost to the
operator vs. a fully-loaded average cost vs. a commercial/contract price including margin
and, for government vehicles, mission-assurance overhead). Marker COLOR encodes country/
region of origin. Marker FILL encodes flight status: filled = has flown at least once,
hollow (open) = pre-flight / predicted (forward-looking figures only -- see notes column).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from cpi import to_2026_usd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_CSV = PROJECT_DIR / "data" / "launch_vehicles.csv"
OUT_DIR = PROJECT_DIR / "results"

SOURCE_NOTE = (
    "Sources: NASA, GAO, NASA OIG, company/SEC filings, Lok Sabha replies, RAND, trade press "
    "(SpaceNews, Ars Technica, Payload Research, The Planetary Society, Spaceflight Now) -- "
    "full citation per data point in data/sources.md. Dollar figures inflated to 2026 USD via "
    "BLS CPI-U (a blunt macro deflator, not a launch-cost-specific index). Hollow markers = "
    "pre-flight / predicted figures. Shaded lanes = that axis is not publicly documented for "
    "this vehicle; the vehicle is still shown at its real value on the other axis."
)

# Fixed categorical color order (colorblind-checked qualitative set, Tableau10-derived),
# assigned by region of origin. Region (not raw country) keeps the legend to a manageable
# number of swatches once individual European startups (Germany, UK, Spain, France, ...)
# are added -- see REGION_OF_COUNTRY below.
REGION_COLORS = {
    "USA":            "#1f77b4",
    "Russia/USSR":    "#d62728",
    "Japan":          "#2ca02c",
    "India":          "#ff7f0e",
    "China":          "#9467bd",
    "Europe":         "#17becf",
}
REGION_ORDER = ["USA", "Russia/USSR", "Japan", "India", "China", "Europe"]

REGION_OF_COUNTRY = {
    "USA": "USA",
    "Russia/USSR": "Russia/USSR",
    "Russia": "Russia/USSR",
    "USSR": "Russia/USSR",
    "Japan": "Japan",
    "India": "India",
    "China": "China",
    "Germany": "Europe", "UK": "Europe", "Spain": "Europe", "France": "Europe",
}

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
# These are approximations -- see their data/sources.md caveats. Keyed by (vehicle, field).
YEAR_OVERRIDES = {
    ("Space Shuttle (STS)", "capex_first_launch_year"): 1978,
    ("SLS (Space Launch System)", "capex_program_year"): 2022,
    ("SLS (Space Launch System)", "capex_first_launch_year"): 2022,
    ("Saturn V", "capex_program_year"): 1966,
    ("Titan IV", "capex_program_year"): 1990,
    ("Titan II GLV (Gemini Launch Vehicle)", "capex_program_year"): 1964,
    ("Titan II GLV (Gemini Launch Vehicle)", "capex_first_launch_year"): 1962,
}

# Manual per-point label offsets (dx, dy in points, ha, va) to de-collide crowded clusters.
# Anything not listed gets a small default offset.
_DEFAULT_OFFSET = (6, 6, "left", "bottom")
_LABEL_OFFSETS = {
    "Falcon 9 (reusable, Block 5)":      (6, 6, "left", "bottom"),
    "Falcon Heavy":                      (6, -8, "left", "top"),
    "Starship (expendable)":             (-8, 6, "right", "bottom"),
    "Antares":                           (6, 6, "left", "bottom"),
    "Space Shuttle":                     (6, 6, "left", "bottom"),
    "SLS":                               (6, -8, "left", "top"),
    "Saturn V":                          (-8, 6, "right", "bottom"),
    "Titan IV":                          (6, 16, "left", "bottom"),
    "Titan II GLV":                      (-8, -8, "right", "top"),
    "Original Atlas":                    (6, 6, "left", "bottom"),
    "Atlas V":                           (6, -8, "left", "top"),
    "Delta IV Heavy":                    (-8, -14, "right", "top"),
    "Neutron (predicted)":               (10, -14, "left", "top"),
    "New Glenn":                         (10, -18, "left", "top"),
    "Soyuz":                             (14, 10, "left", "bottom"),
    "Proton":                            (6, 10, "left", "bottom"),
    "H-II/H-IIA":                        (6, 6, "left", "bottom"),
    "H3":                                (6, -8, "left", "top"),
    "PSLV":                              (-8, 6, "right", "bottom"),
    "GSLV Mk II":                        (6, -24, "left", "top"),
    "GSLV Mk III / LVM3":                (-10, -18, "right", "top"),
    "Falcon 9 v1.0":                     (8, -14, "left", "top"),
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

    df["region"] = df["country"].map(REGION_OF_COUNTRY)
    unmapped = df.loc[df["region"].isna(), "country"].unique().tolist()
    if unmapped:
        raise ValueError(
            f"REGION_OF_COUNTRY is missing an entry for: {unmapped} -- add it rather than "
            "letting these vehicles silently default to the wrong region color."
        )
    df["is_preflight"] = df["num_flights"].fillna(0).astype(float) <= 0

    return df


def _dollar_fmt(v, _pos=None):
    if v <= 0:
        return ""
    if v >= 1e9:
        return f"${v/1e9:.0f}B"
    if v >= 1e6:
        return f"${v/1e6:.0f}M"
    if v >= 1e3:
        return f"${v/1e3:.0f}k"
    return f"${v:.0f}"


def _new_fig():
    fig, ax = plt.subplots(figsize=(16, 9.5))
    return fig, ax


def _bounded_dollar_formatter(threshold):
    """A $-formatter that blanks any tick below `threshold` -- used so the shaded
    'not publicly disclosed' lane never shows a real-looking dollar gridline."""
    def fmt(v, pos=None):
        if v < threshold * 0.999:
            return ""
        return _dollar_fmt(v, pos)
    return fmt


def _plot_group(ax, sub, x, y, hollow: bool):
    for region in REGION_ORDER:
        for basis in BASIS_ORDER:
            grp = sub[(sub["region"] == region) & (sub["opex_used_basis"] == basis)]
            if grp.empty:
                continue
            color = REGION_COLORS[region]
            ax.scatter(
                grp[x], grp[y], marker=BASIS_MARKERS[basis], s=95, zorder=4,
                facecolor=("none" if hollow else color),
                edgecolor=color, linewidth=(1.6 if hollow else 0.6),
            )


def _scatter_with_na_lanes(ax, df: pd.DataFrame, xcol: str, ycol: str, xlabel_short: str, ylabel_short: str):
    """Plot every vehicle with at least one real coordinate. Vehicles missing xcol (but
    with a real ycol) go in a shaded vertical lane left of the real data; vehicles missing
    ycol (but with a real xcol) go in a shaded horizontal lane below the real data. Returns
    the combined frame (with resolved plot_x/plot_y columns) used for label placement, plus
    the list of vehicles that had neither coordinate (and so could not be shown at all)."""
    both = df.dropna(subset=[xcol, ycol]).copy()
    x_missing = df[df[xcol].isna() & df[ycol].notna()].copy()
    y_missing = df[df[ycol].isna() & df[xcol].notna()].copy()
    neither = df[df[xcol].isna() & df[ycol].isna()]["vehicle"].tolist()

    xmin, xmax = both[xcol].min(), both[xcol].max()
    ymin, ymax = both[ycol].min(), both[ycol].max()
    if not x_missing.empty:
        ymin = min(ymin, x_missing[ycol].min())
        ymax = max(ymax, x_missing[ycol].max())
    if not y_missing.empty:
        xmin = min(xmin, y_missing[xcol].min())
        xmax = max(xmax, y_missing[xcol].max())

    x_lane = xmin / 9.0
    y_lane = ymin / 9.0
    x_boundary = xmin / 2.6
    y_boundary = ymin / 2.6
    x_lo = x_lane / 2.4
    y_lo = y_lane / 2.4
    x_hi = xmax * 1.55
    y_hi = ymax * 1.55

    both["plot_x"], both["plot_y"] = both[xcol], both[ycol]

    # Vehicles sharing a lane would otherwise all land on exactly the same x (or y) and
    # stack directly on top of each other -- stagger them across a handful of sub-columns
    # (log-spaced within the lane band), cycling by rank on the OTHER coordinate so
    # points close together on that axis end up visually separated.
    N_STAGGER = 4
    x_cols = np.geomspace(x_lo * 1.6, x_boundary / 1.4, N_STAGGER)
    y_rows = np.geomspace(y_lo * 1.6, y_boundary / 1.4, N_STAGGER)

    x_missing = x_missing.sort_values(ycol, ascending=False).reset_index(drop=True)
    x_missing["plot_x"] = [x_cols[i % N_STAGGER] for i in range(len(x_missing))]
    x_missing["plot_y"] = x_missing[ycol]

    y_missing = y_missing.sort_values(xcol, ascending=False).reset_index(drop=True)
    y_missing["plot_y"] = [y_rows[i % N_STAGGER] for i in range(len(y_missing))]
    y_missing["plot_x"] = y_missing[xcol]

    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)

    # Shaded "not publicly disclosed" lanes + boundary lines, drawn before the data points.
    ax.axvspan(x_lo, x_boundary, color="0.90", zorder=0)
    ax.axhspan(y_lo, y_boundary, color="0.90", zorder=0)
    ax.axvline(x_boundary, color="0.6", linestyle="--", linewidth=0.8, zorder=1)
    ax.axhline(y_boundary, color="0.6", linestyle="--", linewidth=0.8, zorder=1)
    x_band_center = (x_lo * x_boundary) ** 0.5
    y_band_center = (y_lo * y_boundary) ** 0.5
    ax.text(x_band_center, y_hi / 1.15, f"{xlabel_short}\nnot publicly\ndisclosed", fontsize=6.5,
            color="0.4", ha="center", va="top", style="italic", zorder=2)
    ax.text(x_hi / 1.12, y_band_center, f"{ylabel_short} not publicly disclosed", fontsize=6.5,
            color="0.4", ha="right", va="center", style="italic", zorder=2, rotation=0)

    for sub in (both, x_missing, y_missing):
        _plot_group(ax, sub[~sub["is_preflight"]], "plot_x", "plot_y", hollow=False)
        _plot_group(ax, sub[sub["is_preflight"]], "plot_x", "plot_y", hollow=True)

    combined = pd.concat([both, x_missing, y_missing], ignore_index=True)
    for _, row in combined.iterrows():
        label = _short(row["vehicle"])
        suffix = ""
        if row["vehicle"] in x_missing["vehicle"].values:
            suffix = " (capex n/a)"
        elif row["vehicle"] in y_missing["vehicle"].values:
            suffix = " (opex n/a)"
        dx, dy, ha, va = _LABEL_OFFSETS.get(label, _DEFAULT_OFFSET)
        ax.annotate(
            label + suffix, xy=(row["plot_x"], row["plot_y"]), xytext=(dx, dy),
            textcoords="offset points", fontsize=7,
            color=REGION_COLORS.get(row["region"], "grey"), ha=ha, va=va,
        )

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_bounded_dollar_formatter(xmin)))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_bounded_dollar_formatter(ymin)))

    return combined, neither


def _legend(ax):
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker="o", linestyle="", color=REGION_COLORS[c], markersize=8, label=c)
        for c in REGION_ORDER
    ] + [
        Line2D([0], [0], marker=BASIS_MARKERS[b], linestyle="", color="0.35", markersize=8, label=b)
        for b in BASIS_ORDER
    ] + [
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor="0.35", markeredgecolor="0.35",
               markersize=8, label="has flown"),
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor="none", markeredgecolor="0.35",
               markeredgewidth=1.6, markersize=8, label="pre-flight / predicted"),
    ]
    # Placed OUTSIDE the axes (to the right) so it never overlaps a data point or label,
    # regardless of which corner of a given chart happens to be crowded.
    ax.legend(handles=handles, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0),
              ncol=1, framealpha=0.9, borderaxespad=0,
              title="Color = region\nShape = opex cost basis\nFill = flight status", title_fontsize=8)


def _finish(fig, ax, xlabel, ylabel, title, out_name):
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="major", alpha=0.3, linewidth=0.5)
    ax.grid(True, which="minor", alpha=0.12, linewidth=0.4)
    _legend(ax)
    # Manually wrapped (rather than relying on matplotlib's `wrap=True`, which measures
    # against the full figure canvas and had been overflowing past the axes+legend) to a
    # fixed character width tuned to this figure's size, so it never runs wider than the
    # plot area it sits under.
    wrapped = "\n".join(textwrap.wrap(SOURCE_NOTE, width=145))
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=6.8, color="0.35")
    n_lines = wrapped.count("\n") + 1
    bottom_margin = 0.03 + 0.014 * n_lines
    fig.tight_layout(rect=(0, bottom_margin, 0.84, 1))
    out = OUT_DIR / out_name
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"wrote {out}")


def figure_capex_program_vs_opex_per_launch(df):
    fig, ax = _new_fig()
    _, neither = _scatter_with_na_lanes(ax, df, "capex_program_2026usd", "opex_used_2026usd",
                                         "total program capex", "cost per launch")
    _finish(
        fig, ax,
        "Total program capex (2026 USD, log)", "Cost per launch (2026 USD, log)",
        "Launch vehicle economics: total program cost vs. cost per launch",
        "capex_program_vs_opex_per_launch.png",
    )
    return neither


def figure_capex_first_launch_vs_opex_per_launch(df):
    fig, ax = _new_fig()
    _, neither = _scatter_with_na_lanes(ax, df, "capex_first_launch_2026usd", "opex_used_2026usd",
                                         "capex through first launch", "cost per launch")
    _finish(
        fig, ax,
        "Capex through first launch (2026 USD, log)", "Cost per launch (2026 USD, log)",
        "Launch vehicle economics: development cost through first launch vs. cost per launch",
        "capex_first_launch_vs_opex_per_launch.png",
    )
    return neither


def figure_capex_program_vs_opex_per_kg(df):
    fig, ax = _new_fig()
    _, neither = _scatter_with_na_lanes(ax, df, "capex_program_2026usd", "opex_per_kg_2026usd",
                                         "total program capex", "cost per kg to LEO")
    _finish(
        fig, ax,
        "Total program capex (2026 USD, log)", "Cost per kg to LEO (2026 USD, log)",
        "Launch vehicle economics: total program cost vs. $/kg to LEO",
        "capex_program_vs_opex_per_kg.png",
    )
    return neither


def figure_capex_first_launch_vs_opex_per_kg(df):
    fig, ax = _new_fig()
    _, neither = _scatter_with_na_lanes(ax, df, "capex_first_launch_2026usd", "opex_per_kg_2026usd",
                                         "capex through first launch", "cost per kg to LEO")
    _finish(
        fig, ax,
        "Capex through first launch (2026 USD, log)", "Cost per kg to LEO (2026 USD, log)",
        "Launch vehicle economics: development cost through first launch vs. $/kg to LEO",
        "capex_first_launch_vs_opex_per_kg.png",
    )
    return neither


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()
    print(f"Total vehicles in dataset: {len(data)}")
    results = {
        "capex_program_vs_opex_per_launch.png": figure_capex_program_vs_opex_per_launch(data),
        "capex_first_launch_vs_opex_per_launch.png": figure_capex_first_launch_vs_opex_per_launch(data),
        "capex_program_vs_opex_per_kg.png": figure_capex_program_vs_opex_per_kg(data),
        "capex_first_launch_vs_opex_per_kg.png": figure_capex_first_launch_vs_opex_per_kg(data),
    }
    for name, neither in results.items():
        if neither:
            print(f"\n{name}: vehicles absent (BOTH coordinates undocumented, nothing to plot):")
            for v in neither:
                print(f"  - {v}")
        else:
            print(f"\n{name}: every vehicle in the dataset is shown (real point or N/A lane).")
