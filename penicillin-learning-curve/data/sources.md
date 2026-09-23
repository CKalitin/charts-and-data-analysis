# Sources

Every number in `data/*.csv` traces to one of the entries below. "SOC-YYYY" in the CSVs is
the US Tariff Commission (later USITC) annual report *Synthetic Organic Chemicals: United
States Production and Sales, YYYY*. The OCR text and page scans come from the Internet
Archive copies (`syntheticorganicYYYYunit`). The 1949–1951, 1980 and 1986 volumes are not on
the Internet Archive, and USITC's own copies return HTTP 403 to automated fetches.

## US production and prices, 1943–1984

| Tag | Citation | What it supplies |
|---|---|---|
| SOC-1945 … SOC-1984 | US Tariff Commission, *Synthetic Organic Chemicals, US Production and Sales* (annual). E.g. https://archive.org/details/syntheticorganic1970unit | US penicillin production, sales quantity and sales value. 1945–1964: narrative text + medicinal-chemicals table. 1965–1975: antibiotic tabulation in billions of units (BU), read from the page scans. 1976–1984: main table in pounds. |
| ACS-NHCL | American Chemical Society, National Historic Chemical Landmark, "Discovery and Development of Penicillin" (1999). https://www.acs.org/education/whatischemistry/landmarks/flemingpenicillin.html | US output of 21 BU (1943), 1,663 BU (1944), more than 6.8 trillion units (1945). Price of $20 per 100,000 units in 1943, under $0.10 by 1949. |
| Goozner-2004 | M. Goozner, *The $800 Million Pill* (Univ. of California Press, 2004), quoted in the review at https://pmc.ncbi.nlm.nih.gov/articles/PMC1395782/ | "Between 1945 and 1950, the price of penicillin plunged from $3,955 to $282 a pound." The 1945 value matches SOC-1945 at 0.597 BU/lb ($3,955/lb vs SOC $3,865/lb), which supports using the same factor for 1950. |
| CIA-1954 | CIA Office of Research and Reports, *The Antibiotics Industry in the Soviet Bloc*, CIA/RR PR-80, 15 Nov 1954 (released 1999). https://archive.org/details/cia-readingroom-document-cia-rdp79-01093a000700020008-2 | 1953 Soviet-bloc output of 113,100 BU (USSR 92,200; European satellites 19,700; China 1,200). 1953 US output of 370,000 BU, a cross-check on SOC's 372,000. |

Key basis notes from the SOC tables themselves:
- SOC-1948 footnote and SOC-1964 table header: pre-1965 antibiotic sales include **bulk and
  dosage forms** ("Sales (bulk and dosage forms)"). SOC-1965 onward are bulk only. SOC-1976
  adds that "in previous years a significant quantity of an antibiotic in dosage form was
  reported incorrectly as sales."
- SOC-1960 and SOC-1961 footnotes add feed-grade penicillin (~92 and ~112 trillion units)
  that the human/veterinary headline excludes. SOC-1962 onward reports "for all uses".
- SOC unit conversions: procaine penicillin G 458 M units/lb, potassium penicillin G 723 M
  units/lb, penicillin V salts 769 M units/lb (SOC-1964 onward).

## World production anchors

| Tag | Citation | Value |
|---|---|---|
| CORDIS BAP-0395 | EU CORDIS project BAP*0395 (1989–1990). https://cordis.europa.eu/project/id/BAP*0395/de | "Worldwide penicillin production in 1985 was 11,000 tons, 40% of which was used for the manufacture of … semisynthetic penicillin" |
| Elander-2003 | R. P. Elander, "Industrial production of β-lactam antibiotics", *Appl. Microbiol. Biotechnol.* 61:385–392 (2003). https://doi.org/10.1007/s00253-003-1274-y | 1995: 26,400 t penicillin G + 9,980 t penicillin V, a $1.06 billion market. Harvest titers of 40–50 g/L. |
| chyxx-2019 | 智研咨询 (Zhiyan Consulting), "2019年以来中国青霉素工业盐行业发展情况分析" https://www.chyxx.com/industry/201912/821393.html | China makes 75% of world output (2013). ShiYao capacity 18,000 t. |
| gelonghui | 格隆汇 industry reports on 青霉素工业盐, e.g. https://m.gelonghui.com/p/2005212 | China capacity ~100 kt/yr against world demand of 50–60 kt/yr. Another report gives 60–70 kt/yr. |
| Bio Based Press | "Chemistry vs. bacteria #36: Amoxicillin, the factory" (2021). https://www.biobasedpress.eu/2021/11/chemistry-vs-bacteria-36-amoxicillin-the-factory/ | Cross-check only: penicillin G cumulative production of about 2 million tons through 2020. |

## World prices, 1985–2024

| Tag | Citation | Value |
|---|---|---|
| ISID-WP239 | R. K. Joseph & R. A. Kumar, ISID Working Paper 239 (Dec 2021), case study based on Bart, Aggarwal & Singh (2013). https://isid.org.in/pdf/WP239.pdf | "the price of Pen-G crashed to $6/BU as compared to $24/BU during the period between 1985 and 2003". China Pen-G capacity: 5,000–6,000 MMU (1990) → 160,000 MMU (2012). |
| Zhang & Bjerke 2023 | "Antibiotics 'dumped': Negotiating Pharmaceutical Identities…", *Medical Anthropology Quarterly* 37(2):148–163. https://doi.org/10.1111/maq.12757 | About USD 18/BOU in the early 1990s, USD 6.27/BOU in the early 2000s. Chinese export floor of USD 6.3/BOU. |
| CCCMHPIE | China Chamber of Commerce for Import & Export of Medicines & Health Products, "2012年青霉素工业盐出口情况分析" https://www.cccmhpie.org.cn/Pub/4989/80637.shtml (figures as quoted in search results; the page returned HTTP 503 when fetched directly) | 2012: 6,207 t exported, $74.92 M, $12.07/kg, down 13.1% YoY. 2013: 8,454 t, $152 M, ~$18/kg. |
| chyxx 2017 | 智研咨询, "2017年中国抗生素市场概况及价格走势分析" https://www.chyxx.com/industry/201708/550654.html | July 2016 record low of 45 CNY/BOU. May 2017 average of 65 CNY/BOU. |
| biodiscover 2017 | 生物探索, "青霉素工业盐75元/BOU" https://biodiscover.com/industry/33519.html | Sep 2017: 75 CNY/BOU |
| hanghangcha (via search) | 行行查 Q&A on 青霉素工业盐 price trend (login-walled; figures as surfaced by search) | 2008: 60→130→55 CNY/BOU. 2009: 55–70. 2010: 55→72. **Lowest-confidence price source.** |
| BusinessToday 2020 | "Coronavirus fallout: China controlled Penicillin G sees over 50% price rise", 5 Mar 2020. https://www.businesstoday.in/industry/pharma/story/coronavirus-fallout-china-penicillin-g-over-50-price-rise-251463-2020-03-05 | $6/BOU (Nov–Dec 2019), $9.5/BOU (Mar 2020). "Roughly, 1.6 BOU is equivalent to 1 kilogram." |
| United Laboratories | The United Laboratories International Holdings (3933.HK) annual-results presentations, FY2021 (https://doc.irasia.com/listco/hk/unitedlab/cpresent/cpre220324.pdf) and FY2022 (cpre230322.pdf) | Average external selling price of penicillin G potassium industrial salt, ex-VAT: 53.4 (2020), 66.3 (2021), 89.4 (2022) CNY/BOU. "每BOU相等于0.63公斤" (1 BOU = 0.63 kg). |
| Southwest Securities 2024-05 | 西南证券, "原料药板块2024M1-4跟踪报告" https://pdf.dfcfw.com/pdf/H3_AP202405241634546405_1.pdf | April 2024 penicillin industrial salt quote of 130 CNY/BOU, −23.53% YoY, which implies ~170 in April 2023. Wind market quotes. |

## Deflators and FX

- CPI-U annual averages: BLS (https://www.bls.gov/cpi/). 1957–2025 values are copied from `launch-vehicle-economics/scripts/cpi.py` in this repo.
- CNY/USD annual averages: Federal Reserve H.10 / IMF IFS.

## Sources checked but not used

- FTC, *Economic Report on Antibiotics Manufacture* (1958). This is the authoritative 1940s–50s
  bulk-price source, but the Internet Archive copy (`b32172357`) is lending-restricted and
  HathiTrust blocks automated access. It is the #1 source to add, because it would fill the
  1949–1961 bulk-price gap.
- R. Neushul, "Science, Government, and the Mass Production of Penicillin", *J. Hist. Med.* 48:371 (1993): paywalled.
