"""Digitize Sichel (2021, NBER w29617) vector figures straight from the PDF drawing paths.

The figures in the working paper and appendix are native vector graphics (Excel export), so
each polyline vertex is an exact plotted value -- no pixel picking. Outputs:

  data/sichel_fig2_nominal.csv   year, series, cents_per_lb_nominal
  data/sichel_fig3_real.csv      year, series, cents_per_nail_2012usd, cents_per_lb_2012usd
  data/sichel_figA1_absorption.csv  year, absorption_musd_2012

Axis calibration uses the gridline / tick-label positions read from the same page.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pymupdf

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
WP = RAW / "sichel_2021_w29617.pdf"
APPX = RAW / "sichel_2021_appendix.pdf"

# rgb stroke colour -> (series name, first year); the year of each vertex comes from its x.
SERIES = {
    (0.57, 0.82, 0.31): ("early_uk", 1695),   # Beveridge, Greenwich Hospital, hand-forged
    (0.0, 0.44, 0.75): ("mixed", 1784),       # Cole, Philadelphia, forged + cut
    (1.0, 0.0, 0.0): ("cut", 1814),           # HSUS E-131 cut nails
    (0.0, 0.0, 0.0): ("wire", 1890),          # HSUS / BLS PPI wire nails
}

# Sichel appendix Table A2: 2" nails per pound, by period.
def nails_per_lb(year):
    if year <= 1889:
        return 85.0
    if year <= 1941:
        return 150.0
    if year <= 1944:
        return 181.0
    return 168.0


def _rgb(c):
    return tuple(round(v, 2) for v in c) if c else None


def _polyline(d):
    pts = [d["items"][0][1]] + [it[2] for it in d["items"] if it[0] == "l"]
    return np.array([(p.x, p.y) for p in pts])


def _series_lines(page, min_items=20, max_y=None):
    out = {}
    for d in page.get_drawings():
        col = _rgb(d.get("color"))
        if d.get("type") != "s" or col not in SERIES or len(d["items"]) < min_items:
            continue
        if not all(it[0] == "l" for it in d["items"]):
            continue
        out[SERIES[col][0]] = _polyline(d)
    return out


def _log2_axis(y_top, v_top, y_bot, v_bot):
    """Return f(y_pt) -> value for a log-scaled y axis."""
    slope = (np.log2(v_top) - np.log2(v_bot)) / (y_top - y_bot)
    return lambda y: 2.0 ** (np.log2(v_bot) + (y - y_bot) * slope)


def _x_to_year(page_x_1695, page_x_2015):
    """Linear category axis: tick-label centres for 1695 and 2015 give the year of any vertex."""
    return lambda x: np.rint(1695 + (x - page_x_1695) * (2015 - 1695) / (page_x_2015 - page_x_1695)).astype(int)


def fig2_nominal():
    page = pymupdf.open(WP)[37]
    ymap = _log2_axis(172.3, 256.0, 435.4, 1.0)   # gridlines: 256 at top, 1 at axis
    year_of = _x_to_year((122.5 + 150.9) / 2, (482.5 + 510.9) / 2)
    rows = []
    for name, pts in _series_lines(page).items():
        for yr, y in zip(year_of(pts[:, 0]), pts[:, 1]):
            rows.append((yr, name, ymap(y)))
    return pd.DataFrame(rows, columns=["year", "series", "cents_per_lb_nominal"])


def fig3_real():
    page = pymupdf.open(WP)[38]
    ymap = _log2_axis(174.2, 8.0, 398.5, 0.125)   # right axis, cents/nail
    year_of = _x_to_year((119.3 + 147.7) / 2, (483.8 + 512.2) / 2)
    rows = []
    for name, pts in _series_lines(page).items():
        for yr, y in zip(year_of(pts[:, 0]), pts[:, 1]):
            cpn = ymap(y)
            rows.append((yr, name, cpn, cpn * nails_per_lb(yr)))
    return pd.DataFrame(rows, columns=["year", "series", "cents_per_nail_2012usd", "cents_per_lb_2012usd"])


def figA1_absorption():
    """Orange markers = domestic absorption, millions of 2012 $, log2 left axis; date x-axis."""
    page = pymupdf.open(APPX)[21]
    ymap = _log2_axis(148.5, 1024.0, 328.9, 16.0)
    # x: tick-label centres 1810 -> 120.95, 1992 -> 464.7 (linear date axis)
    x_of = lambda yr: 120.95 + (yr - 1810) * (464.7 - 120.95) / (1992 - 1810)
    yr_of = lambda x: 1810 + (x - 120.95) * (1992 - 1810) / (464.7 - 120.95)
    rows = []
    for d in page.get_drawings():
        if d.get("type") == "f" and _rgb(d.get("fill")) == (0.93, 0.49, 0.19) and len(d["items"]) == 4:
            r = d["rect"]
            if r.y0 > 340:            # legend marker
                continue
            cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
            rows.append((yr_of(cx), ymap(cy)))
    df = pd.DataFrame(rows, columns=["year_float", "absorption_musd_2012"]).sort_values("year_float")
    df["year"] = df["year_float"].round().astype(int)
    return df


def figA3_import_share():
    """Blue solid line = import share of US domestic absorption of nails (%), 1947-2002.

    Category axis with 15 benchmark years; each vertex sits on one category, in order.
    """
    page = pymupdf.open(APPX)[23]
    years = [1947, 1950, 1954, 1958, 1963, 1967, 1972, 1977, 1982, 1987, 1992, 2002]
    for d in page.get_drawings():
        if d.get("type") == "s" and _rgb(d.get("color")) == (0.0, 0.44, 0.75) and len(d["items"]) > 1:
            pts = _polyline(d)
    assert len(pts) == len(years)
    pct = (342.1 - pts[:, 1]) * 80.0 / (342.1 - 188.1)   # 0 % gridline at 342.1, 80 % at 188.1
    return pd.DataFrame({"year": years, "import_share_pct": pct})


if __name__ == "__main__":
    out = ROOT / "data"
    f2, f3, fa = fig2_nominal(), fig3_real(), figA1_absorption()
    f2.to_csv(out / "sichel_fig2_nominal.csv", index=False, float_format="%.4f")
    f3.to_csv(out / "sichel_fig3_real.csv", index=False, float_format="%.5f")
    fa.to_csv(out / "sichel_figA1_absorption.csv", index=False, float_format="%.3f")
    f_imp = figA3_import_share()
    f_imp.to_csv(out / "sichel_figA3_import_share.csv", index=False, float_format="%.2f")
    print(f_imp.to_string())
    print(f2.groupby("series").year.agg(["min", "max", "count"]))
    print(f3.groupby("series").year.agg(["min", "max", "count"]))
    print(fa.to_string())
