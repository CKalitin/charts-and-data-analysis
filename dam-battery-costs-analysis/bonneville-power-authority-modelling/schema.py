"""Raw → canonical column naming. The one place messy source columns are renamed.

USACE dam CSVs are already tidy (the scraper writes the canonical schema), so they only
need date parsing. The BPA 5-minute file has long SCADA-tagged headers and a junk title
row; we select it positionally and rename to short canonical names here, so no downstream
code ever touches a raw "TOTAL HYDRO GENERATION (MW; SCADA 79682)" string.
"""

from __future__ import annotations

import pandas as pd

# BPA raw columns are selected by POSITION (the header text carries volatile SCADA ids).
# index -> canonical name.  See config / the raw file header for the full positional map.
_BPA_POS_TO_CANON = {
    0: "datetime",
    4: "wind_mw",
    5: "load_mw",
    6: "hydro_mw",
    7: "fossil_mw",
    8: "nuclear_mw",
    9: "net_interchange_mw",
    12: "solar_mw",
}


def load_usace(path) -> pd.DataFrame:
    """Load a scraped dam CSV with datetime parsed."""
    df = pd.read_csv(path, parse_dates=["datetime"])
    return df


def load_bpa(path) -> pd.DataFrame:
    """Load the BPA 5-minute file into a canonical tidy frame.

    Returns columns: datetime, load_mw, wind_mw, hydro_mw, fossil_mw, nuclear_mw,
    solar_mw, net_interchange_mw — all numeric MW, datetime parsed.
    """
    # Row 0 is a title banner; the real header is row 1 → header=1. Read raw, pick by pos.
    raw = pd.read_csv(path, header=1, dtype=str)
    out = pd.DataFrame()
    for pos, canon in _BPA_POS_TO_CANON.items():
        out[canon] = raw.iloc[:, pos]
    out["datetime"] = pd.to_datetime(out["datetime"], format="%m/%d/%y %H:%M",
                                     errors="coerce")
    for col in out.columns:
        if col != "datetime":
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.dropna(subset=["datetime"]).reset_index(drop=True)
