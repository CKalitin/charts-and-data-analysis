"""Household size by country, ranked.

People per household is the conversion between the two units this project mixes:
WorldPop demand is PEOPLE, satellite capacity is SUBSCRIBERS (one dish, one
household). `tile_capacity_model.py` divides by it to get connection demand, so the
spread shown here propagates roughly linearly into every "people served" figure.

The 66 countries on a regional-median fallback rather than a national census are
drawn hatched. That distinction is load-bearing and must not be dropped in a later
edit -- a fallback country's household size is an inference from its neighbours, not
a measurement, and several of them sit at the extremes of this ranking.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import household_grid as hhg          # noqa: E402
from regions import REGION_COLORS, REGION_SHORT   # noqa: E402
from viz import render                # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "population"

FALLBACK = "regional_median_fallback"
SOURCE_NOTE = ("Sources: national censuses and household surveys, compiled via Wikipedia's "
               "list of countries by number of households; regions and population from World Bank.")

#: Countries called out by name: the two endpoints, plus the four most populous --
#: which is where a household-size error moves the model most, and none of which
#: would otherwise be identifiable among 217 bars. Only well-separated ranks get a
#: callout; labelling the top 4 and bottom 4 put rotated text on adjacent bars ~0.05
#: inch apart, which simply overlapped. The extremes are listed in the footer instead.
LABEL_ALWAYS = {"CHN", "IND", "USA", "IDN"}


def _load():
    hh = {r["iso3"]: r for r in csv.DictReader(open(DATA / "household_size_by_country.csv", encoding="utf-8"))}
    tel = {r["iso3"]: r for r in csv.DictReader(open(DATA / "telecom_market_by_country.csv", encoding="utf-8"))}
    rows = []
    for iso3, r in hh.items():
        t = tel.get(iso3, {})
        rows.append({
            "iso3": iso3,
            "country": r["country"],
            "size": float(r["household_size"]),
            "fallback": r["confidence"] == FALLBACK,
            "region": t.get("region") or "",
            "population": float(t["population"]) if t.get("population") else 0.0,
        })
    rows.sort(key=lambda r: -r["size"])
    return rows


def draw(ax, rows):
    x = np.arange(1, len(rows) + 1)
    colors = [REGION_COLORS.get(r["region"], "#999999") for r in rows]
    ax.bar(x, [r["size"] for r in rows], width=1.0, color=colors, linewidth=0.0, zorder=2)
    # Second pass for the fallback bars only: hatching over a per-bar color list is
    # cleaner applied as its own overlay than by trying to vary hatch per bar.
    fb = [i for i, r in enumerate(rows) if r["fallback"]]
    if fb:
        ax.bar(x[fb], [rows[i]["size"] for i in fb], width=1.0, facecolor="none",
               edgecolor="#333333", hatch="////", linewidth=0.0, zorder=3)

    pop = np.array([r["population"] for r in rows])
    size = np.array([r["size"] for r in rows])
    weighted = float((pop * size).sum() / pop.sum())
    ax.axhline(weighted, color="#111111", lw=1.3, ls="--", zorder=4,
               label=f"Population-weighted mean, {weighted:.2f}")
    ax.axhline(float(np.median(size)), color="#111111", lw=1.0, ls=":", zorder=4,
               label=f"Median country, {np.median(size):.2f}")

    idx = {0, len(rows) - 1} | {i for i, r in enumerate(rows) if r["iso3"] in LABEL_ALWAYS}
    for i in sorted(idx):
        r = rows[i]
        ax.annotate(f"{r['country']} {r['size']:.2f}", xy=(x[i], r["size"]),
                    xytext=(0, 22), textcoords="offset points",
                    fontsize=7.5, rotation=90, ha="center", va="bottom", color="#222222",
                    arrowprops=dict(arrowstyle="-", color="#666666", lw=0.5))

    ax.set_xlim(0.5, len(rows) + 0.5)
    ax.set_ylim(0, max(size) * 1.30)   # headroom for the rotated callouts
    ax.set_xlabel(f"Country rank, largest household first (n={len(rows)})")
    ax.set_ylabel("People per household")
    ax.set_title("People per household vs country")

    present = [reg for reg in REGION_COLORS if any(r["region"] == reg for r in rows)]
    handles = [Patch(facecolor=REGION_COLORS[reg], label=REGION_SHORT[reg]) for reg in present]
    handles.append(Patch(facecolor="white", edgecolor="#333333", hatch="////",
                         label=f"Regional-median fallback, not a national survey ({len(fb)})"))
    handles += ax.get_legend_handles_labels()[0]
    ax.legend(handles=handles, loc="upper right", fontsize=8, framealpha=0.95)
    return weighted


def fig_household_size_ranked():
    rows = _load()
    fig, ax = render.new_figure(figsize=(13, 8.0))
    # constrained_layout does not reserve space for figure-level text, so the footer
    # lands on the x-axis label. Shrink the layout engine's rect instead of calling
    # subplots_adjust -- set_layout_engine("none") leaves a placeholder engine that
    # still refuses subplots_adjust, so that route only produces a warning.
    fig.get_layout_engine().set(rect=(0.0, 0.145, 1.0, 0.855))

    weighted = draw(ax, rows)
    n_fb = sum(r["fallback"] for r in rows)
    top = ", ".join(f"{r['country']} {r['size']:.2f}" for r in rows[:3])
    bottom = ", ".join(f"{r['country']} {r['size']:.2f}" for r in rows[-3:][::-1])
    fig.text(0.055, 0.012,
             f"{len(rows)} countries. Largest: {top}.  Smallest: {bottom}.\n"
             f"{n_fb} countries have no national survey and take their region's median, drawn "
             f"hatched -- they are the flat plateaus, where a whole region shares one inferred value.\n"
             f"The model's own figure is {_model_mean():.2f}, a little below the "
             f"{weighted:.2f} shown here: it weights by WorldPop's gridded population rather than "
             f"World Bank country totals, and 2.4% of population falls outside a matched country polygon.\n"
             f"{SOURCE_NOTE}",
             fontsize=7, color="#555555", va="bottom", ha="left", linespacing=1.5)
    return fig, OUT_ROOT / "household_size_by_country_ranked.png"


def _model_mean() -> float:
    """The population-weighted mean the capacity model actually applies, taken from
    the model's own code path rather than recomputed here -- the two differ slightly
    and quoting the country-level number as "what the model uses" would be wrong."""
    import tile_capacity_model as tcm

    tile = tcm.make_tile_grid()
    demand = tcm.build_demand(tile)
    return float((demand.population * demand.household_size).sum() / demand.population.sum())


def figures():
    return [("household_size_by_country_ranked", fig_household_size_ranked)]


if __name__ == "__main__":
    for name, build in figures():
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(OUT_ROOT.parent.parent)}")

    rows = _load()
    tiles_hh = hhg.load_household_size()
    print(f"\n{len(rows)} countries, {sum(r['fallback'] for r in rows)} on a regional fallback")
    print(f"largest:  " + ", ".join(f"{r['country']} {r['size']:.2f}" for r in rows[:5]))
    print(f"smallest: " + ", ".join(f"{r['country']} {r['size']:.2f}" for r in rows[-5:]))
    print(f"model uses {len(tiles_hh)} of these when attributing tiles")
