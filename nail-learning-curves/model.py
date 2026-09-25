"""Nail learning curves: real price vs cumulative production, by production technology.

Pipeline (all pure functions of the CSVs in data/):
  real_prices()          -> year, tech, cents_per_lb_2012 (== 2012 $ per 100-lb keg)
  annual_output_kegs()   -> year, tech, kegs  (US cut & wire; scenario-dependent where estimated)
  learning_table()       -> prices joined to cumulative output, per tech & scenario
  fit_learning_rate()    -> Wright's-law fit  P = a * Q^b,  LR = 1 - 2^b

Units: price  P  [2012 US$ / kg];  cumulative output  Q  [Mt = 1e9 kg];  LR  [fraction].
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

import config as cfg


# ---------------------------------------------------------------------------- prices
def nails_per_lb(year, tech):
    """2-inch nails per pound (Sichel 2022, appendix Table A2)."""
    if tech != "wire":
        return 85.0
    if year <= 1941:
        return 150.0
    if year <= 1944:
        return 181.0
    return 168.0


def _sichel():
    real = pd.read_csv(cfg.DATA / "sichel_fig3_real.csv")
    nom = pd.read_csv(cfg.DATA / "sichel_fig2_nominal.csv")
    return real, nom


def deflator_to_2012():
    """2012 $ per nominal $ by year, implied by Sichel's own real / nominal series."""
    real, nom = _sichel()
    m = real.merge(nom, on=["year", "series"])
    m = m[~((m.series == "cut") & (m.year == 1890))]   # Sichel's cut->wire link vertex, not a price
    return (m.cents_per_lb_2012usd / m.cents_per_lb_nominal).groupby(m.year).median()


def real_prices():
    real, _ = _sichel()
    tech_of = {"early_uk": "hand_forged", "mixed": "mixed", "cut": "cut", "wire": "wire"}
    df = real.assign(tech=real.series.map(tech_of), source="Sichel (2022)")[
        ["year", "tech", "cents_per_lb_2012usd", "source"]]
    df = df[(df.tech != "mixed") | (df.year >= cfg.CUT_START_YEAR)]
    df = df[~((df.tech == "cut") & (df.year == 1890))]  # link vertex; replaced by HSUS 1890 below

    # cut nails after 1890 (Sichel switches to wire): AISA Philadelphia, deflated with his index
    nom = pd.read_csv(cfg.DATA / "nail_prices_nominal_usd_per_keg.csv")
    cut = pd.concat([nom[(nom.series == "hsus_e131_mixed_cut") & (nom.year == 1890)],
                     nom[nom.series == "cut_philadelphia"]])
    d = deflator_to_2012()
    cut["cents_per_lb_2012usd"] = cut.usd_per_100lb_nominal * cut.year.map(d)
    cut = cut.assign(tech="cut", source=np.where(cut.year == 1890, "HSUS E-131", "AISA (Philadelphia)"))[df.columns]
    df = pd.concat([df, cut], ignore_index=True)
    df = df[df.year <= cfg.LAST_YEAR]
    df["usd_per_kg_2012"] = df.cents_per_lb_2012usd / 100.0 / cfg.KG_PER_LB
    df["cents_per_nail_2012"] = df.cents_per_lb_2012usd / [nails_per_lb(y, t) for y, t in zip(df.year, df.tech)]
    return df.sort_values(["tech", "year"]).reset_index(drop=True)


# ---------------------------------------------------------------------------- output
def _loglin(years, anchors):
    """Log-linear interpolation of a positive series through {year: value} anchors."""
    ay = np.array(sorted(anchors))
    av = np.log(np.array([anchors[y] for y in ay], dtype=float))
    return np.exp(np.interp(years, ay, av))


def _production():
    p = pd.read_csv(cfg.DATA / "us_nail_production_kegs.csv")
    return {t: g.set_index("year").kegs_100lb for t, g in p.groupby("technology")}


def cut_output_kegs(scenario="central", lesley=None):
    prod = _production()["cut"]
    years = np.arange(cfg.CUT_START_YEAR, 1921)
    anchors = {y: prod[y] for y in prod.index}            # 1810, 1856 benchmarks + 1872-1920 AISA
    anchors[1856] *= cfg.CUT_1856_SCALE[lesley or scenario]
    kegs = _loglin(years, anchors)
    g = cfg.CUT_PRE1810_GROWTH[scenario]
    pre = years < 1810
    kegs[pre] = prod[1810] * np.exp(-g * (1810 - years[pre]))
    quality = np.where(np.isin(years, prod.index), "tabulated", "interpolated")
    quality[pre] = "extrapolated"
    return pd.DataFrame({"year": years, "tech": "cut", "kegs": kegs, "quality": quality})


def wire_consumption_benchmarks():
    """Wire-nail US consumption & production (kegs) at Sichel's post-1920 benchmark years."""
    ab = pd.read_csv(cfg.DATA / "sichel_figA1_absorption.csv").set_index("year").absorption_musd_2012
    real, _ = _sichel()
    wp = real[real.series == "wire"].set_index("year").cents_per_lb_2012usd
    imp = pd.read_csv(cfg.DATA / "sichel_figA3_import_share.csv").set_index("year").import_share_pct / 100
    yrs = [y for y in ab.index if 1920 < y <= cfg.LAST_YEAR + 2]
    lbs = np.array([ab[y] * 1e6 / (wp[y] / 100.0) for y in yrs])
    share = np.interp(yrs, [1920] + list(imp.index), [0.0] + list(imp.values))
    return pd.DataFrame({"year": yrs, "consumption_kegs": lbs / cfg.LB_PER_KEG,
                         "import_share": share,
                         "production_kegs": lbs / cfg.LB_PER_KEG * (1 - share)})


def wire_output_kegs(basis=cfg.WIRE_X_BASIS):
    prod = _production()["wire"]
    bm = wire_consumption_benchmarks()
    col = "production_kegs" if basis == "us_production" else "consumption_kegs"
    anchors = {**{y: prod[y] for y in prod.index}, **dict(zip(bm.year, bm[col]))}
    years = np.arange(prod.index.min(), cfg.LAST_YEAR + 1)
    kegs = _loglin(years, anchors)
    quality = np.where(np.isin(years, prod.index), "tabulated",
                       np.where(np.isin(years, bm.year), "benchmark (absorption/price)", "interpolated"))
    return pd.DataFrame({"year": years, "tech": "wire", "kegs": kegs, "quality": quality})


WIRE_STOCK_BEFORE_1886_KEGS = 0.5e6   # small-size wire brads & cigar-box nails, 1875-1885 (estimate)


def cumulative_mt(out, stock_kegs=0.0):
    kg = (out.kegs.cumsum() + stock_kegs) * cfg.LB_PER_KEG * cfg.KG_PER_LB
    return kg / 1e9


def hand_forged_cumulative(years, scenario="central"):
    """England: Q(t) = O(t)/g with O(t) = O_1800 exp(g (t-1800)); returns Mt."""
    o1800_kt, g = cfg.HAND_FORGED_SCENARIOS[scenario]
    return o1800_kt * np.exp(g * (np.asarray(years) - 1800)) / g / 1e3


# ---------------------------------------------------------------------------- joining
def learning_table(scenario="central", wire_basis=cfg.WIRE_X_BASIS):
    pr = real_prices()
    cut = cut_output_kegs(scenario)
    cut["cum_mt"] = cumulative_mt(cut)
    wire = wire_output_kegs(wire_basis)
    wire["cum_mt"] = cumulative_mt(wire, WIRE_STOCK_BEFORE_1886_KEGS)
    cum = {"cut": cut.set_index("year").cum_mt, "mixed": cut.set_index("year").cum_mt,
           "wire": wire.set_index("year").cum_mt}
    rows = []
    for tech, g in pr.groupby("tech"):
        if tech == "hand_forged":
            q = hand_forged_cumulative(g.year, scenario)
        else:
            q = g.year.map(cum[tech]).values
        rows.append(g.assign(cum_mt=q))
    df = pd.concat(rows, ignore_index=True).dropna(subset=["cum_mt"])
    return df


@dataclass(frozen=True)
class Fit:
    tech: str
    y0: int
    y1: int
    b: float          # log-log slope  d ln P / d ln Q   [-]
    b_se: float
    a_usd_per_kg: float
    n: int
    doublings: float  # log2(Q_end / Q_start) over the window

    @property
    def lr(self):             # fractional price drop per doubling of cumulative output
        return 1 - 2 ** self.b

    @property
    def lr_ci95(self):
        return (1 - 2 ** (self.b + 1.96 * self.b_se), 1 - 2 ** (self.b - 1.96 * self.b_se))


def fit_learning_rate(df, tech, y0, y1):
    s = df[(df.tech == tech) & df.year.between(y0, y1)]
    x, y = np.log(s.cum_mt.values), np.log(s.usd_per_kg_2012.values)
    (b, a), cov = np.polyfit(x, y, 1, cov=True)
    return Fit(tech, y0, y1, b, float(np.sqrt(cov[0, 0])), float(np.exp(a)), len(s),
               float(np.log2(s.cum_mt.max() / s.cum_mt.min())))


def all_fits(df):
    fits = {t: fit_learning_rate(df, t, *w) for t, w in cfg.FIT_WINDOWS.items()}
    for name, (t, y0, y1) in cfg.SECONDARY_WINDOWS.items():
        fits[name] = fit_learning_rate(df, t, y0, y1)
    return fits


if __name__ == "__main__":
    for sc in ("low", "central", "high"):
        df = learning_table(sc)
        print(f"--- scenario {sc}")
        for k, f in all_fits(df).items():
            lo, hi = f.lr_ci95
            print(f"{k:13s} {f.y0}-{f.y1}  n={f.n:3d}  doublings={f.doublings:4.1f}  "
                  f"b={f.b:+.3f}  LR={f.lr:+.1%}  (95% CI {lo:+.1%} .. {hi:+.1%})")
    print("--- cut LR sensitivity: pre-1810 growth x 1856 anchor scale")
    for g in cfg.CUT_PRE1810_GROWTH:
        for l in cfg.CUT_1856_SCALE:
            cut = cut_output_kegs(g, l)
            cut["cum_mt"] = cumulative_mt(cut)
            df = real_prices().query("tech == 'cut'")
            df = df.assign(cum_mt=df.year.map(cut.set_index("year").cum_mt))
            f = fit_learning_rate(df, "cut", *cfg.FIT_WINDOWS["cut"])
            print(f"  growth={g:8s} lesley={l:8s} LR={f.lr:.1%}")
    print(wire_consumption_benchmarks().round(0).to_string())
