"""Scrape USACE Northwestern Division hourly project data → tidy CSV.

Standalone, resumable scraper for the dam-vs-BESS blog analysis. Pulls one calendar
year of hourly records for any USACE NWD project (Grand Coulee `gcl`, Bonneville
`bon`, ...) and computes turbine power from generation flow and hydraulic head.

Power model (head is read directly from the page's "Average Head" column):

    power_mw = gen_flow_kcfs * 1000 (cfs/kcfs) * head_ft * K
    K = rho * g * eta / unit_conversions = 7.63e-5 MW per (cfs * ft), eta = 0.90

Robustness:
  - 1 s delay between requests (polite to the .gov server)
  - verify=False: the host serves a DoD CA chain not in the default trust store
  - incremental append + flush per day, so a killed run resumes where it left off
    (dates already present in the output file are skipped)

Run:  python scrape.py            # scrapes every dam in DAMS for YEAR
      python scrape.py gcl        # just Grand Coulee
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Config (single source of truth for the scrape) -----------------------------------
YEAR = 2023
DATA_DIR = Path(__file__).resolve().parent / "data"
BASE_URL = "https://www.nwd-wc.usace.army.mil/dd/nwdp/project_hourly/webexec/rep"
REQUEST_DELAY_S = 1.0
POWER_K = 7.63e-5          # MW per (cfs * ft) at eta = 0.90

DAMS = {                  # code -> (display name, output filename stem)
    "gcl": ("Grand Coulee", "grand_coulee_hourly_2023"),
    "bon": ("Bonneville", "bonneville_hourly_2023"),
}

CSV_COLUMNS = [
    "date", "hour", "datetime", "dam_code", "dam_name",
    "total_outflow_kcfs", "gen_flow_kcfs", "spill_kcfs",
    "forebay_elev_ft", "tailwater_elev_ft", "head_ft", "power_mw",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.nwd-wc.usace.army.mil/dd/common/projects/www/{code}.html",
}


def _to_float(text: str):
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def parse_day(html: str, day: date, code: str, name: str) -> list[dict]:
    """Parse one day's HTML table into hourly rows. Skips AVG/MAX/MIN summary rows."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        hour = int(cells[0])                      # 1..24, hour-ending
        gen_flow = _to_float(cells[2])
        head = _to_float(cells[6])
        power = (gen_flow * 1000 * head * POWER_K
                 if gen_flow is not None and head is not None else None)
        # Store datetime as hour-beginning (0..23) so pandas .dt.hour spans the full day
        # cleanly and hour-ending 24 does not become an invalid 24:00 timestamp.
        iso = f"{day.isoformat()}T{hour - 1:02d}:00"
        rows.append({
            "date": day.isoformat(), "hour": hour, "datetime": iso,
            "dam_code": code, "dam_name": name,
            "total_outflow_kcfs": _to_float(cells[1]),
            "gen_flow_kcfs": gen_flow,
            "spill_kcfs": _to_float(cells[3]),
            "forebay_elev_ft": _to_float(cells[4]),
            "tailwater_elev_ft": _to_float(cells[5]),
            "head_ft": head,
            "power_mw": round(power, 1) if power is not None else None,
        })
    return rows


def _existing_dates(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="") as f:
        return {row["date"] for row in csv.DictReader(f)}


def scrape_dam(code: str, name: str, stem: str) -> None:
    out_path = DATA_DIR / f"{stem}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = _existing_dates(out_path)
    write_header = not out_path.exists()

    session = requests.Session()
    headers = {**HEADERS, "Referer": HEADERS["Referer"].format(code=code)}

    day = date(YEAR, 1, 1)
    end = date(YEAR, 12, 31)
    n_new = 0
    with out_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        while day <= end:
            if day.isoformat() in done:
                day += timedelta(days=1)
                continue
            url = f"{BASE_URL}?r={code}&date={day:%m/%d/%Y}"
            try:
                r = session.get(url, headers=headers, timeout=30, verify=False)
                r.raise_for_status()
                rows = parse_day(r.text, day, code, name)
                writer.writerows(rows)
                f.flush()
                n_new += 1
                if n_new % 25 == 0:
                    print(f"  [{code}] {day} ({n_new} days, {len(rows)} rows last)")
            except Exception as e:                # keep going; a killed run resumes cleanly
                print(f"  [{code}] FAILED {day}: {e}")
            time.sleep(REQUEST_DELAY_S)
            day += timedelta(days=1)
    print(f"[{code}] done — {n_new} new days written to {out_path.name}")


def main() -> None:
    codes = sys.argv[1:] or list(DAMS)
    for code in codes:
        name, stem = DAMS[code]
        print(f"Scraping {name} ({code}) for {YEAR} ...")
        scrape_dam(code, name, stem)


if __name__ == "__main__":
    main()
