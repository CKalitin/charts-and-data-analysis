"""Time-series family: price vs year and annual production vs year."""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":   # runnable standalone: put the project root on the path first
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.ticker as mticker

import config as cfg
from charts import common
from viz import render

OUT = cfg.OUTPUT_ROOT / "timeseries"

SOURCE_PRICE = (
    "Sources: US Tariff Commission, Synthetic Organic Chemicals (1945-1984); ACS (1943); Goozner 2004 (1950); "
    "ISID WP239; Zhang & Bjerke 2023; Elander 2003; CCCMHPIE; United Laboratories; Southwest Securities. "
    f"Real = CPI-U deflated to {cfg.CPI_BASIS_YEAR}."
)
SOURCE_PROD = (
    "Sources: US Tariff Commission, Synthetic Organic Chemicals (US, 1945-1983); ACS/WPB (1943-44); "
    "world anchors: CIA 1954 (Soviet bloc 1953), CORDIS (1985), Elander 2003 (1995), Chinese industry reports (2019); "
    "world 1953-84 = US + rest-of-world interpolated between anchors; log-linear between anchors elsewhere."
)


def _year_log_axes(ax, yfmt) -> None:
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(mticker.LogLocator(base=10, numticks=15))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(yfmt))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.grid(True, which="major", ls="--", alpha=0.4)
    ax.set_xlim(1940, 2027)


def draw_price(ax, fig, pts, annual) -> None:
    _year_log_axes(ax, common.dollar_fmt)
    kinds = [common.series_key(r) for r in pts.itertuples()]
    pts = pts.assign(kind=kinds)
    for k in common.SERIES_ORDER:
        sel = pts[pts.kind == k]
        style = dict(common.MARKERS[k])
        ax.scatter(sel.year, sel.real, zorder=4, **style)
        nominal_style = {**style, "label": None, "alpha": 0.35}
        ax.scatter(sel.year, sel.nominal, zorder=3, **nominal_style)
    ax.plot([], [], ls="none", marker="o", color="0.6", alpha=0.35, label="Faded markers: nominal USD")
    ax.set_xlabel("Year")
    ax.set_ylabel(f"Price [USD per billion units; solid = real {cfg.CPI_BASIS_YEAR} USD]")
    ax.set_title("Penicillin Price vs Year")
    common.per_kg_right_axis(ax)
    ax.legend(loc="upper right", fontsize=7.8, framealpha=0.9)
    common.add_watermark(ax)
    common.add_source(fig, SOURCE_PRICE)


def draw_production(ax, fig, pts, annual) -> None:
    _year_log_axes(ax, common.count_fmt)
    a = annual
    ax.fill_between(a.year, a.world_BU_low, a.world_BU_high, color=cfg.COLORS["world_prod"],
                    alpha=0.15, lw=0, label="World, low-high anchor scenarios")
    ax.plot(a.year, a.world_BU_central, color=cfg.COLORS["world_prod"], lw=1.8,
            label="World, central estimate (interpolated between anchors)")
    us = a.dropna(subset=["us_BU"])
    us = us[us.year <= 1983]
    ax.plot(us.year, us.us_BU, color=cfg.COLORS["us_prod"], lw=1.4, marker="o", ms=3,
            label="United States (Tariff Commission; 1949-51 interpolated)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual production [billion units]")
    ax.set_title("Penicillin Production vs Year")
    sec = ax.secondary_yaxis("right", functions=(lambda b: b / cfg.BU_PER_TONNE,
                                                 lambda t: t * cfg.BU_PER_TONNE))
    sec.set_ylabel("Annual production [tonnes, K-salt equivalent]")
    sec.yaxis.set_major_formatter(mticker.FuncFormatter(common.count_fmt))
    sec.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.legend(loc="upper left", fontsize=7.8, framealpha=0.9)
    common.add_watermark(ax)
    common.add_source(fig, SOURCE_PROD)


def figures(pts, annual):
    def build(draw, name, size=(11, 6.5)):
        def _b():
            fig, ax = render.new_figure(figsize=size)
            fig.get_layout_engine().set(rect=(0, 0.045, 1, 0.955))
            draw(ax, fig, pts, annual)
            return fig, OUT / f"{name}.png"
        return name, _b
    return [build(draw_price, "price_vs_year"), build(draw_production, "production_vs_year")]


if __name__ == "__main__":
    import time

    import derived

    t0 = time.time()
    plan = figures(derived.price_points(), derived.annual_table())
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
