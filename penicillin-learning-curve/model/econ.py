"""Deflators and exchange rates.

CPI-U (all items, US city average, 1982-84 = 100), BLS annual averages. 1957-2025 values are
copied from launch-vehicle-economics/scripts/cpi.py in this repo; 1943-1956 are the standard
BLS historical annual averages (https://www.bls.gov/cpi/).

CNY per USD: annual averages (Federal Reserve H.10 / IMF IFS), used only to put Chinese
yuan-per-BOU quotes on a dollar basis.
"""

from __future__ import annotations

CPI_U = {
    1943: 17.3, 1944: 17.6, 1945: 18.0, 1946: 19.5, 1947: 22.3, 1948: 24.1, 1949: 23.8,
    1950: 24.1, 1951: 26.0, 1952: 26.5, 1953: 26.7, 1954: 26.9, 1955: 26.8, 1956: 27.2,
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
}

CNY_PER_USD = {
    2009: 6.831, 2016: 6.644, 2017: 6.752, 2020: 6.900, 2021: 6.452, 2022: 6.730,
    2023: 7.084, 2024: 7.197,
}


def to_real(amount: float, year: int, basis_year: int) -> float:
    """Nominal `amount` in `year` dollars -> `basis_year` dollars (CPI-U)."""
    return amount * CPI_U[basis_year] / CPI_U[year]


def cny_to_usd(amount: float, year: int) -> float:
    return amount / CNY_PER_USD[year]
