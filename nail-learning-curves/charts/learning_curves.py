"""Charts: nail real price vs cumulative production by technology, and annual production.

Each draw_* function draws onto a provided Axes. figures() returns [(name, build)] pairs.
"""
import numpy as np
from matplotlib.ticker import NullFormatter

import config as cfg
import model

YEAR_LABELS = {  # (tech, year): (dx_pts, dy_pts, ha, va)
    ("hand_forged", 1695): (-8, 0, "right", "center"),
    ("hand_forged", 1792): (6, 8, "left", "bottom"),
    ("mixed", 1795): (-6, 6, "right", "bottom"),
    ("cut", 1814): (-6, 8, "right", "bottom"),
    ("cut", 1850): (6, 8, "left", "bottom"),
    ("cut", 1886): (-4, -12, "right", "top"),
    ("cut", 1920): (6, 6, "left", "bottom"),
    ("wire", 1890): (6, 8, "left", "bottom"),
    ("wire", 1920): (-6, -10, "right", "top"),
    ("wire", 1940): (-4, -12, "center", "top"),
    ("wire", 1970): (-8, 8, "right", "bottom"),
    ("wire", 2000): (6, 0, "left", "center"),
}


def _fit_label(f):
    lo, hi = f.lr_ci95
    return f"LR {f.lr:.0%} per doubling ({lo:.0%} to {hi:.0%}), {f.y0}-{f.y1}"


def draw_learning(ax, df, fits, hf_band):
    for tech in ("hand_forged", "mixed", "cut", "wire"):
        st = cfg.TECH_STYLE[tech]
        s = df[df.tech == tech].sort_values("year")
        win = cfg.FIT_WINDOWS.get(tech)
        in_fit = s.year.between(*win) if win else np.zeros(len(s), bool)
        ax.plot(s.cum_mt, s.usd_per_kg_2012, color=st["color"], lw=0.8, alpha=0.45, zorder=2)
        label = st["label"] + (f"\n{_fit_label(fits[tech])}" if tech in fits else " (not fitted)")
        ax.scatter(s.cum_mt[in_fit], s.usd_per_kg_2012[in_fit], s=16, marker=st["marker"],
                   color=st["color"], edgecolor="white", linewidth=0.4, zorder=4, label=label)
        ax.scatter(s.cum_mt[~in_fit], s.usd_per_kg_2012[~in_fit], s=16, marker=st["marker"],
                   facecolor="none", edgecolor=st["color"], linewidth=0.8, zorder=3)
        if tech in fits:
            f = fits[tech]
            q = np.geomspace(s.cum_mt[in_fit].min(), s.cum_mt[in_fit].max(), 50)
            ax.plot(q, f.a_usd_per_kg * q ** f.b, color=st["color"], lw=2.2, zorder=5)
        for (t, yr), (dx, dy, ha, va) in YEAR_LABELS.items():
            if t == tech and yr in set(s.year):
                r = s[s.year == yr].iloc[0]
                ax.annotate(str(yr), (r.cum_mt, r.usd_per_kg_2012), xytext=(dx, dy),
                            textcoords="offset points", fontsize=7.5, color="0.25", ha=ha, va=va)

    # hand-forged x-uncertainty: low/high production scenarios bracket the central points
    lo, hi = hf_band
    ax.hlines(lo.usd_per_kg_2012, lo.cum_mt, hi.cum_mt, color=cfg.TECH_STYLE["hand_forged"]["color"],
              alpha=0.12, lw=1.0, zorder=1, label="Hand-forged volume range (England, estimated)")

    pw = fits["wire_postwar"]
    ax.plot([], [], " ", label=f"Hollow = outside fit window; wire {pw.y0}-{pw.y1}: "
                               f"LR {pw.lr:.0%} (price rose)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Cumulative production of that technology [Mt]  (1 Mt = 22 million 100-lb kegs)")
    ax.set_ylabel("Real price [2012 US$ / kg]")
    ax.set_title("Nail Real Price vs Cumulative Production, by Technology")
    ax.set_yticks([0.5, 1, 2, 3, 5])
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:g}")
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([0.01, 0.1, 1, 10, 100])
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:g}")
    ax.legend(loc="lower left", fontsize=7.5, framealpha=0.9)


def draw_annual_output(ax):
    cut = model.cut_output_kegs()
    wire = model.wire_output_kegs()
    for out, tech in ((cut, "cut"), (wire, "wire")):
        st = cfg.TECH_STYLE[tech]
        t = out.quality == "tabulated"
        ax.plot(out.year, out.kegs / 1e6, color=st["color"], lw=1.2, label=f"{st['label']}")
        ax.scatter(out.year[t], out.kegs[t] / 1e6, s=10, color=st["color"], zorder=3)
    b = model.wire_consumption_benchmarks()
    b = b[b.year <= cfg.LAST_YEAR + 2]
    ax.scatter(b.year, b.consumption_kegs / 1e6, s=28, marker="D", facecolor="none",
               edgecolor=cfg.TECH_STYLE["wire"]["color"], zorder=4,
               label="Wire, US consumption benchmark (Sichel absorption / price)")
    ax.scatter(b.year, b.production_kegs / 1e6, s=18, marker="x", color="0.35", zorder=4,
               label="Wire, implied US production (consumption x (1 - import share))")
    p = model._production()["cut"]
    for y in (1810, 1856):
        ax.scatter([y], [p[y] / 1e6], s=40, marker="*", color=cfg.TECH_STYLE["cut"]["color"], zorder=5)
    ax.plot([], [], "*", color=cfg.TECH_STYLE["cut"]["color"], label="Cut, benchmark (Gallatin 1810, Lesley 1856)")
    ax.plot([], [], "o", ms=3, color="0.3", label="Dots = tabulated annual (AISA); lines between = interpolated")
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("US output [million 100-lb kegs / yr]")
    ax.set_title("US Nail Output by Technology")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}")
    ax.legend(loc="lower right", fontsize=7.5)


def figures():
    from viz import info_box, render

    def learning():
        df = model.learning_table("central")
        fits = model.all_fits(df)
        hf = [model.learning_table(sc).query("tech == 'hand_forged'").sort_values("year")
              for sc in ("low", "high")]
        fig, ax = render.new_figure(figsize=(11, 7))
        fig.get_layout_engine().set(rect=(0, 0.025, 1, 0.975))
        draw_learning(ax, df, fits, hf)
        fig.text(0.01, 0.005, cfg.SOURCE_NOTE, fontsize=6.5, color="0.35", ha="left", va="bottom")
        o, g = cfg.HAND_FORGED_SCENARIOS["central"]
        info = ("Price: wholesale, deflated to 2012 US$ (Sichel CPI/PCE index)\n"
                f"England hand-forged volume: O(1800) = {o:.0f} kt/yr, growth {g:.1%}/yr\n"
                "  (band: 20 kt @1.5% to 80 kt @0.5%)\n"
                "US cut: AISA 1872-1920; 1795-1871 from 1810/1856 benchmarks\n"
                "US wire: AISA 1886-1920; after 1920 US consumption benchmarks\n"
                "LR = 1 - 2^b,  P = a Q^b;  95% CI from OLS slope s.e.")
        info_box.add_info_box(ax, fig, info, fontsize=7.5)
        return fig, cfg.OUTPUT_ROOT / "learning_curves" / "nail_price_vs_cumulative_production.png"

    def output():
        fig, ax = render.new_figure(figsize=(11, 6))
        fig.get_layout_engine().set(rect=(0, 0.03, 1, 0.97))
        draw_annual_output(ax)
        fig.text(0.01, 0.005, cfg.SOURCE_NOTE, fontsize=6.5, color="0.35", ha="left", va="bottom")
        return fig, cfg.OUTPUT_ROOT / "production" / "us_nail_output_by_technology.png"

    return [("learning", learning), ("output", output)]


if __name__ == "__main__":
    import sys
    import time
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from viz import render

    t0 = time.time()
    plan = figures()
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path, dpi=cfg.DPI)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"wrote {len(plan)} charts in {time.time() - t0:.1f}s")
