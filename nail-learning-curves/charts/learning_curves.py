"""Charts: nail real price vs cumulative production by technology, and annual production.

Each draw_* function draws onto a provided Axes. figures() returns [(name, build)] pairs.
"""
import numpy as np
import pandas as pd
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


KT_PER_KEG = cfg.LB_PER_KEG * cfg.KG_PER_LB / 1e6


def output_all():
    """Every annual-output value used anywhere in the analysis, one row per year x series [kt/yr]."""
    rows = []
    yrs = np.arange(1695, 1801)
    for sc, (o1800, g) in cfg.HAND_FORGED_SCENARIOS.items():
        rows.append(pd.DataFrame({"year": yrs, "series": f"hand_forged_england_{sc}",
                                  "kt_per_yr": o1800 * np.exp(g * (yrs - 1800)),
                                  "quality": "assumed (scenario)"}))
    cut = model.cut_output_kegs()
    wire = model.wire_output_kegs()
    rows.append(cut.assign(series="cut_us", kt_per_yr=cut.kegs * KT_PER_KEG)[["year", "series", "kt_per_yr", "quality"]])
    wq = wire.quality.where(~wire.year.between(1886, 1889), "trade estimate")
    rows.append(wire.assign(series="wire_us", kt_per_yr=wire.kegs * KT_PER_KEG, quality=wq)[["year", "series", "kt_per_yr", "quality"]])
    bm = model.wire_consumption_benchmarks()
    bm = bm[bm.year <= cfg.LAST_YEAR + 2]
    rows.append(pd.DataFrame({"year": bm.year, "series": "wire_us_implied_production",
                              "kt_per_yr": bm.production_kegs * KT_PER_KEG,
                              "quality": "derived (consumption x (1 - import share))"}))
    return pd.concat(rows, ignore_index=True)


def _masked(s, ok):
    return s.where(ok)


def draw_annual_output(ax, out):
    hf = {sc: out[out.series == f"hand_forged_england_{sc}"].set_index("year").kt_per_yr
          for sc in cfg.HAND_FORGED_SCENARIOS}
    c = cfg.TECH_STYLE["hand_forged"]["color"]
    ax.fill_between(hf["low"].index, hf["low"], hf["high"], color=c, alpha=0.15, lw=0,
                    label="Hand-forged, England: assumed range (20 kt @1.5%/yr to 80 kt @0.5%/yr)")
    ax.plot(hf["central"].index, hf["central"], color=c, lw=1.6, ls="--",
            label="Hand-forged, England: central assumption (40 kt/yr in 1800, +1%/yr)")

    for series, tech in (("cut_us", "cut"), ("wire_us", "wire")):
        st = cfg.TECH_STYLE[tech]
        d = out[out.series == series].set_index("year")
        ax.plot(d.index, d.kt_per_yr, color=st["color"], lw=1.0, ls=":", alpha=0.9)   # interpolation
        tab = d.quality == "tabulated"
        ax.plot(d.index, _masked(d.kt_per_yr, tab), color=st["color"], lw=1.6,
                label=f"{st['label']}: tabulated annual (AISA)")
        ax.scatter(d.index[tab], d.kt_per_yr[tab], s=9, color=st["color"], zorder=3)

    cc = cfg.TECH_STYLE["cut"]["color"]
    p = model._production()["cut"]
    ax.scatter([1810, 1856], [p[1810] * KT_PER_KEG, p[1856] * KT_PER_KEG], s=70, marker="*",
               color=cc, zorder=5, label="Cut, US: benchmark (Gallatin 1810, Lesley 1856)")
    wc = cfg.TECH_STYLE["wire"]["color"]
    w = out[(out.series == "wire_us") & (out.quality == "trade estimate")]
    ax.scatter(w.year, w.kt_per_yr, s=26, marker="^", facecolor="none", edgecolor=wc, zorder=5,
               label="Wire, US: trade estimate (AISA / Swank, 1886-89)")
    bm = model.wire_consumption_benchmarks()
    bm = bm[bm.year <= cfg.LAST_YEAR + 2]
    ax.scatter(bm.year, bm.consumption_kegs * KT_PER_KEG, s=30, marker="D", facecolor="none",
               edgecolor=wc, zorder=5, label="Wire, US consumption: benchmark (Sichel absorption / price)")
    ip = out[out.series == "wire_us_implied_production"]
    ax.scatter(ip.year, ip.kt_per_yr, s=20, marker="x", color="0.35", zorder=5,
               label="Wire, implied US production (consumption x (1 - import share))")
    ax.plot([], [], color="0.4", lw=1.0, ls=":", label="Dotted = interpolated / extrapolated")

    ax.set_yscale("log")
    ax.set_xlim(1690, 2005)
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual output [kt / yr]  (1 kt = 22,046 100-lb kegs)")
    ax.set_title("Nail Output by Technology")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}")
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.legend(loc="upper left", fontsize=7.5, framealpha=0.9)


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
        out = output_all()
        (cfg.OUTPUT_ROOT / "production").mkdir(parents=True, exist_ok=True)
        out.to_csv(cfg.OUTPUT_ROOT / "production" / "nail_output_by_technology.csv", index=False,
                   float_format="%.4g")
        fig, ax = render.new_figure(figsize=(12, 6.5))
        fig.get_layout_engine().set(rect=(0, 0.03, 1, 0.97))
        draw_annual_output(ax, out)
        fig.text(0.01, 0.005, cfg.SOURCE_NOTE, fontsize=6.5, color="0.35", ha="left", va="bottom")
        return fig, cfg.OUTPUT_ROOT / "production" / "nail_output_by_technology.png"

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
