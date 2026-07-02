"""US CPI-U (all items, U.S. city average, 1982-84=100) annual-average index, used to
convert nominal-dollar cost figures quoted in different years onto a common 2025-USD
basis so capex/opex figures spanning 1957-2026 can be compared on one chart.

Values for 2015-2025 were pulled directly from BLS's published annual-average table
(https://www.bls.gov/regions/mid-atlantic/data/consumerpriceindexannualandsemiannual_table.htm)
during this analysis (July 2026). The 2026 value is the most recent single-month index
(May 2026, https://www.bls.gov/news.release/cpi.t01.htm), used as a stand-in for a full
2026 annual average since one is not yet published. Pre-2015 values are BLS's standard,
widely-republished historical CPI-U annual averages (same series, https://www.bls.gov/cpi/).

This is a standard macro deflator, not a space-industry-specific index -- it captures
general purchasing power, not launch-industry cost inflation (which has arguably fallen
in real terms even as CPI rose). Used here only to put nominal figures on a roughly
comparable footing, not as a claim about "real" launch cost trends.
"""

from __future__ import annotations

CPI_U_ANNUAL_AVERAGE: dict[int, float] = {
    1957: 28.1, 1958: 28.9, 1959: 29.1, 1960: 29.6, 1961: 29.9, 1962: 30.2,
    1963: 30.6, 1964: 31.0, 1965: 31.5, 1966: 32.4, 1967: 33.4, 1968: 34.8,
    1969: 36.7, 1970: 38.8, 1971: 40.5, 1972: 41.8, 1973: 44.4, 1974: 49.3,
    1975: 53.8, 1976: 56.9, 1977: 60.6, 1978: 65.2, 1979: 72.6, 1980: 82.4,
    1981: 90.9, 1982: 96.5, 1983: 99.6, 1984: 103.9, 1985: 107.6, 1986: 109.6,
    1987: 113.6, 1988: 118.3, 1989: 124.0, 1990: 130.7, 1991: 136.2, 1992: 140.3,
    1993: 144.5, 1994: 148.2, 1995: 152.4, 1996: 156.9, 1997: 160.5, 1998: 163.0,
    1999: 166.6, 2000: 172.2, 2001: 177.1, 2002: 179.9, 2003: 184.0, 2004: 188.9,
    2005: 195.3, 2006: 201.6, 2007: 207.3, 2008: 215.3, 2009: 214.5, 2010: 218.056,
    2011: 224.939, 2012: 229.594, 2013: 232.957, 2014: 236.736, 2015: 237.017,
    2016: 240.007, 2017: 245.120, 2018: 251.107, 2019: 255.657, 2020: 258.811,
    2021: 270.970, 2022: 292.655, 2023: 304.702, 2024: 313.689, 2025: 321.943,
    2026: 335.123,  # May 2026 index, not yet a full annual average
}

BASIS_YEAR = 2026
_BASIS_INDEX = CPI_U_ANNUAL_AVERAGE[BASIS_YEAR]


def to_2026_usd(amount: float, year: int) -> float | None:
    """Inflate/deflate a nominal-dollar `amount` quoted in `year` to 2026 USD."""
    if amount is None or year is None:
        return None
    year = int(year)
    if year not in CPI_U_ANNUAL_AVERAGE:
        return None
    return amount * _BASIS_INDEX / CPI_U_ANNUAL_AVERAGE[year]
