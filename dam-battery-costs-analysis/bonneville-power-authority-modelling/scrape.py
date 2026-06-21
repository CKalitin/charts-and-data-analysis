"""Scrape USACE Northwestern Division hourly project data → tidy CSVs.

Resumable, parallel scraper for BPA federal dams tracked by USACE NWD.

Usage:
  python scrape.py                   # all dams, 6 parallel workers
  python scrape.py chj               # single dam
  python scrape.py chj jda tda       # specific dams
  python scrape.py --workers 4       # override worker count
  python scrape.py --workers 1 chj   # sequential, single dam

Output:
  data/grand_coulee_hourly_2023.csv   (gcl - legacy path, config compat)
  data/bonneville_hourly_2023.csv     (bon - legacy path, config compat)
  data/bpa_dams/{slug}_hourly_2023.csv (all other dams)

Unit note:
  Large Columbia/Snake River dams report flow in kcfs.
  Small Oregon Willamette Valley USACE projects report in cfs.
  This scraper normalises everything to kcfs in the CSV output.

Power formula (already applied during scrape):
  power_mw = gen_flow_kcfs * 1000 * head_ft * 7.63e-5   (eta=0.90)

Not available in USACE NWD (Bureau of Reclamation dams):
  Palisades, Anderson Ranch, Minidoka

Non-BPA Columbia River dams also in NWD (not scraped here):
  prd=Priest Rapids, ris=Rock Island, rrh=Rocky Reach, wan=Wanapum, wel=Wells
"""

from __future__ import annotations

import csv
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

YEAR            = 2023
DATA_DIR        = Path(__file__).resolve().parent / "data"
BPA_DAM_DIR     = DATA_DIR / "bpa_dams"
BASE_URL        = "https://www.nwd-wc.usace.army.mil/dd/nwdp/project_hourly/webexec/rep"
REQUEST_DELAY_S = 1.0
POWER_K         = 7.63e-5   # MW per (cfs * ft) at eta=0.90
DEFAULT_WORKERS = 6
DAYS_IN_YEAR    = 365

# BPA federal dams available in USACE NWD.
# code -> (display name, slug, nameplate_mw, flow_unit)
# flow_unit: "kcfs" for large Columbia/Snake dams; "cfs" for small Oregon USACE projects.
# All output is normalised to kcfs regardless of source unit.
# fmt: off
DAMS: dict[str, tuple[str, str, int, str]] = {
    # --- Large Columbia/Snake River mainstem dams (kcfs) ---
    "gcl": ("Grand Coulee",     "grand_coulee",     7049, "kcfs"),
    "chj": ("Chief Joseph",     "chief_joseph",     2614, "kcfs"),
    "jda": ("John Day",         "john_day",         2484, "kcfs"),
    "tda": ("The Dalles",       "the_dalles",       2048, "kcfs"),
    "bon": ("Bonneville",       "bonneville",       1216, "kcfs"),
    "mcn": ("McNary",           "mcnary",           1127, "kcfs"),
    "lgs": ("Little Goose",     "little_goose",      930, "kcfs"),
    "lwg": ("Lower Granite",    "lower_granite",     930, "kcfs"),
    "lmn": ("Lower Monumental", "lower_monumental",  930, "kcfs"),
    "ihr": ("Ice Harbor",       "ice_harbor",        695, "kcfs"),
    "lib": ("Libby",            "libby",             605, "kcfs"),
    "dwr": ("Dworshak",         "dworshak",          460, "kcfs"),
    "hgh": ("Hungry Horse",     "hungry_horse",      428, "kcfs"),
    "alf": ("Albeni Falls",     "albeni_falls",       49, "kcfs"),
    # --- Small Oregon Willamette Valley USACE projects (cfs -> normalised to kcfs) ---
    "lop": ("Lookout Point",    "lookout_point",     138, "cfs"),
    "det": ("Detroit",          "detroit",           126, "cfs"),
    "gpr": ("Green Peter",      "green_peter",        92, "cfs"),
    "los": ("Lost Creek",       "lost_creek",         56, "cfs"),
    "hcr": ("Hills Creek",      "hills_creek",        34, "cfs"),
    "cgr": ("Cougar",           "cougar",             28, "cfs"),
    "fos": ("Foster",           "foster",             23, "cfs"),
    "bcl": ("Big Cliff",        "big_cliff",          23, "cfs"),
    "dex": ("Dexter",           "dexter",             17, "cfs"),
}
# fmt: on

_LEGACY_STEMS = {"gcl", "bon"}

CSV_COLUMNS = [
    "date", "hour", "datetime", "dam_code", "dam_name",
    "total_outflow_kcfs", "gen_flow_kcfs", "spill_kcfs",
    "forebay_elev_ft", "tailwater_elev_ft", "head_ft", "power_mw",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# --- Shared progress state (thread-safe) ------------------------------------------------
_lock = threading.Lock()
_progress: dict[str, dict] = {}


def _status_line(code: str) -> str:
    p = _progress[code]
    name, _, mw, _ = DAMS[code]
    pct = p["done"] / p["total"] * 100
    bar_len = 20
    filled = int(bar_len * p["done"] / p["total"])
    bar = "#" * filled + "." * (bar_len - filled)
    return f"  {code:4s} {name:<20} [{bar}] {p['done']:3d}/{p['total']} ({pct:5.1f}%)  {p['status']}"


def _print_progress() -> None:
    with _lock:
        print(f"\n--- Progress ({time.strftime('%H:%M:%S')}) ---")
        for code in _progress:
            print(_status_line(code))
        print()
        sys.stdout.flush()


# --- Parsing ----------------------------------------------------------------------------
def _to_float(text: str):
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def _normalise(value, unit: str):
    """Convert cfs to kcfs if needed; leave kcfs values unchanged."""
    if value is None:
        return None
    return value / 1000.0 if unit == "cfs" else value


def parse_day(html: str, day: date, code: str, name: str, unit: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        hour     = int(cells[0])
        gen_flow_raw = _to_float(cells[2])
        head         = _to_float(cells[6])
        gen_flow_kcfs = _normalise(gen_flow_raw, unit)
        power = (gen_flow_kcfs * 1000 * head * POWER_K
                 if gen_flow_kcfs is not None and head is not None else None)
        iso = f"{day.isoformat()}T{hour - 1:02d}:00"
        rows.append({
            "date": day.isoformat(), "hour": hour, "datetime": iso,
            "dam_code": code, "dam_name": name,
            "total_outflow_kcfs":  _normalise(_to_float(cells[1]), unit),
            "gen_flow_kcfs":       gen_flow_kcfs,
            "spill_kcfs":          _normalise(_to_float(cells[3]), unit),
            "forebay_elev_ft":     _to_float(cells[4]),
            "tailwater_elev_ft":   _to_float(cells[5]),
            "head_ft":             head,
            "power_mw":            round(power, 1) if power is not None else None,
        })
    return rows


# --- File helpers -----------------------------------------------------------------------
def _out_path(code: str, slug: str) -> Path:
    if code in _LEGACY_STEMS:
        return DATA_DIR / f"{slug}_hourly_{YEAR}.csv"
    return BPA_DAM_DIR / f"{slug}_hourly_{YEAR}.csv"


def _existing_dates(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="") as f:
        return {row["date"] for row in csv.DictReader(f) if row.get("date")}


# --- Per-dam scrape worker --------------------------------------------------------------
def scrape_dam(code: str) -> str:
    name, slug, _, unit = DAMS[code]
    out = _out_path(code, slug)
    out.parent.mkdir(parents=True, exist_ok=True)

    done_dates = _existing_dates(out)
    write_header = not out.exists() or out.stat().st_size == 0

    with _lock:
        _progress[code] = {
            "done":   len(done_dates),
            "total":  DAYS_IN_YEAR,
            "status": "resuming" if done_dates else "starting",
        }

    session = requests.Session()
    day, end = date(YEAR, 1, 1), date(YEAR, 12, 31)
    n_new = 0

    with out.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()

        while day <= end:
            if day.isoformat() in done_dates:
                day += timedelta(days=1)
                continue

            url_date = f"{day:%m/%d/%Y}"
            try:
                r = session.post(
                    BASE_URL,
                    data={"r": code, "date": url_date},
                    headers=HEADERS, timeout=30, verify=False,
                )
                r.raise_for_status()
                rows = parse_day(r.text, day, code, name, unit)
                if rows:
                    writer.writerows(rows)
                    f.flush()
                    n_new += 1
                    with _lock:
                        _progress[code]["done"] += 1
                        _progress[code]["status"] = f"last: {day}"
                else:
                    # Server returned form page or empty response — skip silently
                    with _lock:
                        _progress[code]["done"] += 1
                        _progress[code]["status"] = f"no data: {day}"
            except Exception as e:
                with _lock:
                    _progress[code]["status"] = f"ERR {day}: {e}"

            time.sleep(REQUEST_DELAY_S)
            day += timedelta(days=1)

    with _lock:
        _progress[code]["done"] = DAYS_IN_YEAR
        _progress[code]["status"] = f"done ({n_new} days with data)"

    return f"[{code}] {name} -- {n_new} days written to {out.name}"


# --- Orchestrator -----------------------------------------------------------------------
def main() -> None:
    args = sys.argv[1:]
    workers = DEFAULT_WORKERS
    if "--workers" in args:
        i = args.index("--workers")
        workers = int(args[i + 1])
        args = args[:i] + args[i + 2:]

    codes = args if args else list(DAMS)
    unknown = [c for c in codes if c not in DAMS]
    if unknown:
        print(f"Unknown codes: {unknown}")
        print(f"Valid codes: {list(DAMS)}")
        sys.exit(1)

    # Pre-populate progress
    for code in codes:
        done = len(_existing_dates(_out_path(code, DAMS[code][1])))
        _progress[code] = {"done": done, "total": DAYS_IN_YEAR, "status": "queued"}

    actual_workers = min(workers, len(codes))
    print(f"Scraping {len(codes)} dam(s) for {YEAR} with {actual_workers} worker(s)")
    print(f"Estimated time: ~{DAYS_IN_YEAR * len(codes) / actual_workers / 60:.0f} min")
    _print_progress()
    sys.stdout.flush()

    stop_event = threading.Event()
    def _status_loop():
        while not stop_event.is_set():
            time.sleep(30)
            if not stop_event.is_set():
                _print_progress()
    threading.Thread(target=_status_loop, daemon=True).start()

    with ThreadPoolExecutor(max_workers=actual_workers) as ex:
        futures = {ex.submit(scrape_dam, code): code for code in codes}
        for fut in as_completed(futures):
            code = futures[fut]
            try:
                msg = fut.result()
                with _lock:
                    print(f"\n  OK {msg}")
                    sys.stdout.flush()
            except Exception as e:
                with _lock:
                    print(f"\n  ERR [{code}] failed: {e}")
                    sys.stdout.flush()

    stop_event.set()
    _print_progress()
    print("All done.")


if __name__ == "__main__":
    main()
