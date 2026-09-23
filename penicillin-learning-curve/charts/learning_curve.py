"""Learning-curve family: real price vs cumulative production (world, US, eras)."""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":   # runnable standalone: put the project root on the path first
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import config as cfg
from charts import common
from viz import info_box, render

OUT = cfg.OUTPUT_ROOT / "learning_curve"
Y_LABEL = f"Real price [{cfg.CPI_BASIS_YEAR} USD per billion units]"
X_WORLD = "Cumulative world production [billion units, mid-year]"
X_US = "Cumulative US production [billion units, mid-year]"

SOURCE_WORLD = (
    "Sources: US Tariff Commission, Synthetic Organic Chemicals (1945-1984); ACS National Historic "
    "Chemical Landmark (1943 price, 1943-44 output); Goozner 2004 (1950); CIA 1954; CORDIS; Elander 2003; "
    "ISID WP239; Zhang & Bjerke 2023; CCCMHPIE; United Laboratories; Southwest Securities. "
    f"CPI-U deflated to {cfg.CPI_BASIS_YEAR}. 1 billion units = 0.627 kg K-salt."
)
SOURCE_US = (
    "Sources: US Tariff Commission, Synthetic Organic Chemicals (1945-1984); ACS National Historic "
    f"Chemical Landmark (1943); Goozner 2004 (1950). CPI-U deflated to {cfg.CPI_BASIS_YEAR}."
)

# per-year label offsets (dx, dy, ha, va) where the default (6, 6) collides
OFFSETS = {
    1943: (8, -2, "left", "center"),
    1945: (8, 2, "left", "bottom"),
    1952: (7, 3, "left", "bottom"),
    1962: (-6, -6, "right", "top"),
    1964: (0, 9, "center", "bottom"),
    1984: (-4, -8, "right", "top"),
    1985: (6, 6, "left", "bottom"),
    2003: (-6, -6, "right", "top"),
    2013: (-4, 7, "right", "bottom"),
    2024: (6, 2, "left", "bottom"),
}


def _fit_line(ax, fit, x_lo, x_hi, **kw):
    xs = np.logspace(np.log10(x_lo), np.log10(x_hi), 100)
    ax.plot(xs, fit.predict(xs), zorder=3, **kw)


def _fit_text(fit, label: str) -> str:
    lo, hi = fit.lr_ci
    return (f"{label}\nLearning rate {100 * fit.lr:.1f}% per doubling\n"
            f"95% CI {100 * lo:.1f}-{100 * hi:.1f}%   b = {fit.b:.3f}\n"
            f"R² = {fit.r2:.3f}   n = {fit.n}")


def _layout_for_source(fig) -> None:
    fig.get_layout_engine().set(rect=(0, 0.045, 1, 0.955))


def draw_world(ax, fig, pts, fits) -> None:
    fit = fits["World cumulative, central (1943-2024)"]
    lo_fit, hi_fit = fits["World cumulative, low (1943-2024)"], fits["World cumulative, high (1943-2024)"]
    x = "cum_world_central"
    common.log_axes(ax)
    common.scatter_points(ax, pts, x)
    _fit_line(ax, fit, pts[x].min() * 0.7, pts[x].max() * 1.4, color=cfg.COLORS["fit"], lw=1.6,
              label=f"Fit, 1943-2024: {100 * fit.lr:.1f}% learning rate")
    common.label_years(ax, pts, x, offsets=OFFSETS)
    ax.set_xlabel(X_WORLD)
    ax.set_ylabel(Y_LABEL)
    ax.set_title("Penicillin Price vs Cumulative World Production")
    common.tonnes_top_axis(ax)
    common.per_kg_right_axis(ax)
    ax.legend(loc="lower left", fontsize=7.8, framealpha=0.9)
    common.add_watermark(ax)
    common.add_source(fig, SOURCE_WORLD)
    info = (_fit_text(fit, "log P = a + b log X (OLS)") +
            f"\nWorld-volume scenarios: LR {100 * lo_fit.lr:.1f}% (low) / {100 * hi_fit.lr:.1f}% (high)"
            "\nExcluded: 1952-64 bulk+dosage-form values")
    info_box.add_info_box(ax, fig, info, mode="on", fontsize=8)


def draw_us(ax, fig, pts, fits) -> None:
    fit = fits["US price vs US cumulative (1943-1984)"]
    us = pts[pts.region == "US"]
    x = "cum_us"
    common.log_axes(ax)
    common.scatter_points(ax, us, x, keys=("quoted", "all_forms_fit", "all_forms_excluded", "us_bulk"))
    _fit_line(ax, fit, us[x].min() * 0.7, us[x].max() * 1.4, color=cfg.COLORS["fit"], lw=1.6,
              label=f"Fit, 1943-1984: {100 * fit.lr:.1f}% learning rate")
    common.label_years(ax, us, x, years=cfg.LABEL_YEARS | {1946, 1947, 1956, 1964, 1975},
                       offsets=OFFSETS)
    ax.set_xlabel(X_US)
    ax.set_ylabel(Y_LABEL)
    ax.set_title("US Penicillin Price vs Cumulative US Production")
    common.per_kg_right_axis(ax)
    ax.legend(loc="lower left", fontsize=7.8, framealpha=0.9)
    common.add_watermark(ax)
    common.add_source(fig, SOURCE_US)
    info_box.add_info_box(ax, fig, _fit_text(fit, "log P = a + b log X (OLS)") +
                          "\nExcluded: 1952-64 bulk+dosage-form values", mode="on", fontsize=8)


def draw_eras(ax, fig, pts, fits) -> None:
    x = "cum_world_central"
    fit_pts = pts[pts.in_fit]
    common.log_axes(ax)
    whole = fits["World cumulative, central (1943-2024)"]
    _fit_line(ax, whole, pts[x].min() * 0.7, pts[x].max() * 1.4, color="0.55", lw=1.2, ls="--",
              label=f"All years: {100 * whole.lr:.1f}%")
    lines = []
    for color, (name, (y0, y1)) in zip(cfg.ERA_COLORS, cfg.ERAS.items()):
        seg = fit_pts[(fit_pts.year >= y0) & (fit_pts.year <= y1)]
        f = fits[f"Era: {name}"]
        lo, hi = f.lr_ci
        ax.scatter(seg[x], seg.real, s=34, color=color, edgecolor="k", linewidth=0.5, zorder=4)
        _fit_line(ax, f, seg[x].min() / 1.5, seg[x].max() * 1.5, color=color, lw=2.0,
                  label=f"{name}: {100 * f.lr:.0f}% (95% CI {100 * lo:.0f}-{100 * hi:.0f}%, n={f.n})")
        lines.append(f)
    gap = pts[(pts.basis == "all_forms") & ~pts.in_fit]
    ax.scatter(gap[x], gap.real, s=30, facecolor="none", edgecolor="0.5", linewidth=0.9, zorder=3,
               label="1952-64 bulk + dosage forms (not fitted)")
    common.label_years(ax, fit_pts, x, years={1943, 1950, 1962, 1984, 1985, 2024}, offsets=OFFSETS)
    ax.set_xlabel(X_WORLD)
    ax.set_ylabel(Y_LABEL)
    ax.set_title("Penicillin Learning Rate by Era")
    common.tonnes_top_axis(ax)
    ax.legend(loc="lower left", fontsize=7.8, framealpha=0.9)
    common.add_watermark(ax)
    common.add_source(fig, SOURCE_WORLD)


def figures(pts, fits):
    def build(draw, name, size=(11, 7)):
        def _b():
            fig, ax = render.new_figure(figsize=size)
            _layout_for_source(fig)
            draw(ax, fig, pts, fits)
            return fig, OUT / f"{name}.png"
        return name, _b
    return [build(draw_world, "price_vs_cumulative_world"),
            build(draw_us, "price_vs_cumulative_us"),
            build(draw_eras, "learning_rate_by_era")]


if __name__ == "__main__":
    import time

    import derived

    t0 = time.time()
    pts = derived.price_points()
    fits = derived.fits(pts)
    plan = figures(pts, fits)
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")
