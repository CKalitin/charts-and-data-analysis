"""Build data/household_size_by_country.csv -- average household size (people per
household), the missing input for converting a population count into a subscription
count for the TAM model (see CLAUDE.md's TAM-model section, user request 2026-08-14).

Source: Wikipedia's "List of countries by number of households" (fetched 2026-08-14),
itself a compilation of national census/survey figures -- NOT a single bulk
machine-readable download (no such thing was found for this specific indicator; the
UN Population Division's own "Household Size and Composition" database is an
interactive portal, not a bulk CSV, and WebFetch could not reliably extract a full
table from its JS-rendered UI when tried). 152 of 217 countries in
telecom_market_by_country.csv are directly covered. The other 65 (mostly small
island states / territories not in Wikipedia's table) get a REGIONAL MEDIAN fallback,
computed from the covered countries in the SAME `region` column already used
throughout this project (telecom_market_by_country.csv) -- flagged with
confidence="regional_median_fallback" per row, never silently blended with the
real per-country figures.

Run: python build_household_size_dataset.py
"""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

# Country name (as it appears in the Wikipedia table) -> (avg household size, year).
# Extracted 2026-08-14 from https://en.wikipedia.org/wiki/List_of_countries_by_number_of_households
WIKI_HOUSEHOLD_SIZE = {
    "China": (2.80, 2023), "India": (4.57, 2015), "United States": (2.49, 2020),
    "Indonesia": (3.86, 2017), "Brazil": (3.31, 2010), "Russia": (2.58, 2010),
    "Japan": (2.26, 2020), "Nigeria": (4.90, 2015), "Germany": (2.05, 2011),
    "Bangladesh": (4.47, 2014), "Mexico": (3.74, 2015), "Pakistan": (6.80, 2013),
    "France": (2.22, 2015), "United Kingdom": (2.27, 2011), "Turkey": (3.14, 2023),
    "Philippines": (4.23, 2017), "Vietnam": (3.78, 2009), "Italy": (2.40, 2011),
    "Egypt": (4.13, 2014), "Iran": (3.49, 2016), "South Korea": (2.18, 2022),
    "Ethiopia": (4.61, 2016), "DR Congo": (5.30, 2013), "Thailand": (3.69, 2010),
    "South Africa": (3.36, 2016), "Spain": (2.69, 2011), "Ukraine": (2.46, 2007),
    "Canada": (2.45, 2016), "Colombia": (3.53, 2015), "Argentina": (3.26, 2010),
    "Poland": (2.81, 2011), "Kenya": (3.64, 2015), "Myanmar": (4.22, 2016),
    "Tanzania": (4.85, 2015), "Australia": (2.50, 2011), "Uganda": (4.53, 2016),
    "Ghana": (3.49, 2014), "Peru": (3.75, 2012), "Netherlands": (2.23, 2011),
    "Sudan": (5.59, 2008), "Malaysia": (4.56, 2000), "Nepal": (4.24, 2016),
    "Morocco": (5.24, 2004), "Mozambique": (4.37, 2011), "Romania": (2.88, 2011),
    "Uzbekistan": (5.24, 1996), "Venezuela": (4.33, 2001), "North Korea": (3.93, 2008),
    "Angola": (4.82, 2016), "Chile": (3.58, 2002), "Kazakhstan": (3.50, 2009),
    "Madagascar": (4.95, 2011), "Iraq": (7.70, 1997), "Ivory Coast": (5.09, 2012),
    "Belgium": (2.36, 2011), "Cameroon": (4.99, 2011), "Sweden": (2.17, 2020),
    "Ecuador": (3.78, 2010), "Yemen": (6.67, 2013), "Czech Republic": (2.40, 2011),
    "Greece": (2.44, 2011), "Afghanistan": (8.04, 2015), "Malawi": (4.51, 2015),
    "Austria": (2.27, 2011), "Niger": (5.92, 2012), "Switzerland": (2.21, 2000),
    "Portugal": (2.66, 2011), "Zimbabwe": (4.08, 2015), "Belarus": (2.48, 2009),
    "Hungary": (2.60, 2011), "Burkina Faso": (5.92, 2014), "Cuba": (3.14, 2002),
    "Guatemala": (4.81, 2015), "Zambia": (5.13, 2013), "Mali": (5.81, 2018),
    "Cambodia": (4.61, 2014), "Bolivia": (3.53, 2012), "Dominican Republic": (3.48, 2013),
    "Bulgaria": (2.34, 2011), "Rwanda": (4.26, 2015), "Israel": (3.14, 2008),
    "Chad": (5.78, 2015), "Haiti": (4.29, 2017), "Finland": (2.07, 2010),
    "Hong Kong": (2.83, 2016), "Burundi": (4.83, 2016), "Norway": (2.22, 2011),
    "Serbia": (2.88, 2011), "Benin": (5.19, 2018), "Jordan": (4.72, 2017),
    "South Sudan": (5.95, 2008), "Azerbaijan": (4.55, 2009), "Honduras": (4.47, 2012),
    "Guinea": (6.25, 2012), "Slovakia": (2.80, 2011), "Senegal": (8.66, 2017),
    "New Zealand": (2.67, 2013), "Ireland": (2.77, 2011), "Singapore": (3.29, 2010),
    "Togo": (4.55, 2014), "El Salvador": (4.07, 2007), "Papua New Guinea": (5.43, 2000),
    "Paraguay": (4.63, 2002), "Kyrgyzstan": (4.21, 2012), "Tajikistan": (6.27, 2012),
    "Costa Rica": (3.46, 2011), "Croatia": (2.80, 2011), "Sierra Leone": (5.90, 2013),
    "Nicaragua": (4.92, 2005), "Congo": (4.31, 2011), "Uruguay": (2.78, 2011),
    "Laos": (5.77, 2005), "Lithuania": (2.32, 2011), "Puerto Rico": (2.67, 2010),
    "Panama": (3.67, 2010), "Central African Republic": (4.91, 1994), "Georgia": (3.34, 2014),
    "Liberia": (4.95, 2013), "Moldova": (2.89, 2014), "Jamaica": (3.06, 2011),
    "Albania": (3.30, 2017), "Slovenia": (2.47, 2015), "Armenia": (3.54, 2016),
    "Mongolia": (4.32, 2000), "Latvia": (2.58, 2011), "Botswana": (3.52, 2011),
    "Lesotho": (3.34, 2014), "Namibia": (4.24, 2013), "Estonia": (2.30, 2011),
    "Oman": (8.02, 2003), "Gabon": (4.10, 2012), "Trinidad and Tobago": (3.29, 2011),
    "Mauritius": (3.48, 2011), "Cyprus": (2.75, 2011), "Gambia": (8.23, 2013),
    "Luxembourg": (2.41, 2011), "East Timor": (5.27, 2016), "Swaziland": (4.74, 2007),
    "China, Macao SAR": (3.07, 2016), "Guyana": (3.80, 2009), "Fiji": (4.57, 2014),
    "Montenegro": (3.21, 2011), "Malta": (2.85, 2011), "Guadeloupe": (2.30, 2015),
    "Suriname": (3.94, 2004), "Comoros": (5.37, 2012), "Bahamas": (3.40, 2010),
    "Maldives": (5.40, 2017), "Aruba": (2.89, 2010), "Isle of Man": (2.28, 2016),
    "Samoa": (6.75, 2016), "Bermuda": (2.26, 2016), "Liechtenstein": (2.32, 2010),
}

# Wikipedia name -> this project's World Bank-style country name (telecom_market_by_country.csv).
# Only needed where the two differ; identity mapping is assumed otherwise.
NAME_OVERRIDES = {
    "Russia": "Russian Federation", "Ivory Coast": "Cote d'Ivoire", "DR Congo": "Congo, Dem. Rep.",
    "Congo": "Congo, Rep.", "North Korea": "Korea, Dem. People's Rep.", "South Korea": "Korea, Rep.",
    "Czech Republic": "Czechia", "Swaziland": "Eswatini", "East Timor": "Timor-Leste",
    "China, Macao SAR": "Macao SAR, China", "Hong Kong": "Hong Kong SAR, China",
    "Slovakia": "Slovak Republic", "Egypt": "Egypt, Arab Rep.", "Iran": "Iran, Islamic Rep.",
    "Venezuela": "Venezuela, RB", "Yemen": "Yemen, Rep.", "Gambia": "Gambia, The",
    "Bahamas": "Bahamas, The", "Kyrgyzstan": "Kyrgyz Republic", "Laos": "Lao PDR",
    "Turkey": "Turkiye", "Vietnam": "Viet Nam",
}


def main():
    with open(DATA / "telecom_market_by_country.csv", encoding="utf-8") as f:
        countries = list(csv.DictReader(f))
    name_to_iso3 = {r["country"]: r["iso3"] for r in countries}
    iso3_to_region = {r["iso3"]: r["region"] for r in countries}

    direct: dict[str, tuple[float, int]] = {}  # iso3 -> (size, year)
    unmatched = []
    for wiki_name, (size, year) in WIKI_HOUSEHOLD_SIZE.items():
        project_name = NAME_OVERRIDES.get(wiki_name, wiki_name)
        iso3 = name_to_iso3.get(project_name)
        if iso3 is None:
            unmatched.append(wiki_name)
            continue
        direct[iso3] = (size, year)

    if unmatched:
        print(f"WARNING: {len(unmatched)} Wikipedia rows did not match a project country: {unmatched}")

    # Regional median fallback for every country NOT directly covered.
    region_sizes: dict[str, list[float]] = {}
    for iso3, (size, _year) in direct.items():
        region_sizes.setdefault(iso3_to_region[iso3], []).append(size)
    region_median = {region: statistics.median(sizes) for region, sizes in region_sizes.items()}
    global_median = statistics.median([s for sizes in region_sizes.values() for s in sizes])

    out_rows = []
    n_direct, n_regional, n_global = 0, 0, 0
    for r in countries:
        iso3 = r["iso3"]
        if iso3 in direct:
            size, year = direct[iso3]
            out_rows.append({"iso3": iso3, "country": r["country"], "household_size": round(size, 2),
                              "source_year": year, "confidence": "direct_national_census_or_survey"})
            n_direct += 1
        elif r["region"] in region_median:
            out_rows.append({"iso3": iso3, "country": r["country"],
                              "household_size": round(region_median[r["region"]], 2),
                              "source_year": "", "confidence": "regional_median_fallback"})
            n_regional += 1
        else:
            out_rows.append({"iso3": iso3, "country": r["country"], "household_size": round(global_median, 2),
                              "source_year": "", "confidence": "global_median_fallback"})
            n_global += 1

    out_path = DATA / "household_size_by_country.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["iso3", "country", "household_size", "source_year", "confidence"])
        w.writeheader()
        w.writerows(out_rows)

    print(f"wrote {out_path} -- {len(out_rows)} countries "
          f"({n_direct} direct, {n_regional} regional median, {n_global} global median)")
    print(f"global median household size (fallback of last resort): {global_median:.2f}")
    for region, sizes in sorted(region_sizes.items()):
        print(f"  {region}: n={len(sizes)}, median={statistics.median(sizes):.2f}")


if __name__ == "__main__":
    main()
