"""Cross-city comparison charts: overlaid house-price-index trajectories, and a decoupling-gap
ranking bar chart -- the two charts that actually answer "where do Canadian cities sit?"."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config as cfg
from viz import render
from viz.info_box import add_info_box
from viz.plotting import SeriesSpec, draw


def figures_overlay(indexed):
    def build():
        fig, ax = render.new_figure()
        series = []
        for city_key in cfg.CA_CITIES + cfg.US_CITIES:
            city = cfg.CITIES[city_key]
            sub = indexed[indexed["city"] == city_key].sort_values("year")
            series.append(SeriesSpec(sub["year"], sub["house_price_index"],
                                     label=city["label"], color=city["color"], linewidth=2.0))
        draw(ax, series, xlabel="Year", ylabel=cfg.axis_label("house_price_index"),
             title=f"Real house-price growth by city ({cfg.START_YEAR} = 100)")
        add_info_box(ax, fig,
                     "Deflated by each country's own CPI\n"
                     "CA: StatCan New Housing Price Index (new construction)\n"
                     "US: Zillow ZHVI (all-homes tier)", mode="on")
        return fig, cfg.OUTPUT_DIR / "ranking" / "house_price_index_overlay.png"

    return [("house_price_overlay", build)]


def figures_decoupling_ranking(ranking_df):
    def build():
        fig, ax = render.new_figure()
        df = ranking_df.sort_values("decoupling_gap_pp")
        colors = [cfg.CITIES[c]["color"] for c in df["city"]]
        labels = [cfg.CITIES[c]["label"] for c in df["city"]]
        ax.barh(labels, df["decoupling_gap_pp"], color=colors)
        ax.axvline(0, color="0.3", linewidth=1)
        ax.set_xlabel(cfg.axis_label("decoupling_gap_pp"))
        year = int(df["year"].iloc[0])
        ax.set_title(f"House-price growth minus wage growth, cumulative "
                      f"{cfg.START_YEAR}-{year} (real terms)")
        add_info_box(ax, fig,
                     "Positive = house prices outran wages over the window\n"
                     "Negative = wages outran house prices", mode="on")
        return fig, cfg.OUTPUT_DIR / "ranking" / "decoupling_gap_ranking.png"

    return [("decoupling_ranking", build)]


if __name__ == "__main__":
    import time

    import data_load
    import model.derived as derived

    t0 = time.time()
    panel = data_load.load_panel()
    indexed = derived.add_indices(panel)
    ranking = derived.latest_year_ranking(indexed)
    plan = [*figures_overlay(indexed), *figures_decoupling_ranking(ranking)]
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
