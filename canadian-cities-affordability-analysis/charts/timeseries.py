"""House-price-index vs wage-index small multiples, one panel per city, CA cities first."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config as cfg
from viz import render
from viz.plotting import SeriesSpec, draw


def figures_city_panels(indexed):
    plan = []
    city_order = cfg.CA_CITIES + cfg.US_CITIES
    for city_key in city_order:
        city = cfg.CITIES[city_key]
        sub = indexed[indexed["city"] == city_key].sort_values("year")

        def build(sub=sub, city=city, city_key=city_key):
            fig, ax = render.new_figure()
            draw(
                ax,
                [
                    SeriesSpec(sub["year"], sub["house_price_index"],
                               label="House price (real)", color=city["color"], linewidth=2.2),
                    SeriesSpec(sub["year"], sub["wage_index"],
                               label="Wage income (real)", color="0.35",
                               linestyle="--", linewidth=1.6),
                ],
                xlabel="Year",
                ylabel=cfg.axis_label("house_price_index"),
                title=f"{city['label']} -- real house price vs. real wage growth "
                      f"({cfg.START_YEAR} = 100)",
            )
            return fig, cfg.OUTPUT_DIR / "timeseries" / f"{city_key}.png"

        plan.append((f"timeseries_{city_key}", build))
    return plan


if __name__ == "__main__":
    import time

    import data_load
    import model.derived as derived

    t0 = time.time()
    panel = data_load.load_panel()
    indexed = derived.add_indices(panel)
    plan = figures_city_panels(indexed)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
