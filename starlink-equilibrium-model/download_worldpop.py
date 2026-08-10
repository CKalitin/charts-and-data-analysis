"""Download WorldPop 1km gridded population density GeoTIFFs, one per country.

Deferred from the Phase 3/5 density-modeling discussion (see ASSUMPTIONS.md #6):
the equilibrium model currently spreads each country's density cap over its WHOLE
land area, which overstates addressable customers for countries with concentrated
population (e.g. Egypt, ~95% of people on ~5% of the land). Gridded population data
is the agreed fix -- this script fetches the raw input for that, it does NOT change
equilibrium_model.py yet (that's a separate integration step).

Source: WorldPop "Unconstrained individual countries 2000-2020 (1km resolution)"
population density dataset, via the no-login REST API at hub.worldpop.org. Pulls the
most recent year (2020) per ISO3 code found in telecom_market_by_country.csv.
~42MB/country (1km resolution) -- the 100m-native version was tried first and found
impractical (~4.1GB/country).

Idempotent / resumable: skips any .tif already present in data/raw/worldpop/. Safe to
re-run after an interruption. Writes data/raw/worldpop/_manifest.csv logging
success/failure per country so a partial run can be audited without re-downloading.

Run: python download_worldpop.py
"""
from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
OUT_DIR = DATA / "raw" / "worldpop"
API = "https://hub.worldpop.org/rest/data/pop_density/pd_ic_1km"
TARGET_YEAR = "2020"


def load_iso3_list() -> list[str]:
    out = []
    with open(DATA / "telecom_market_by_country.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["iso3"]:
                out.append(r["iso3"])
    return out


def fetch_tif_url(iso3: str) -> str | None:
    req = urllib.request.Request(f"{API}?iso3={iso3}", headers={"User-Agent": "starlink-equilibrium-model/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    entries = payload.get("data", [])
    for e in entries:
        if e.get("popyear") == TARGET_YEAR:
            for f in e.get("files", []):
                if f.endswith(".tif"):
                    return f
    # fall back to the latest available year if 2020 isn't present for this country
    entries_sorted = sorted(entries, key=lambda e: e.get("popyear", ""), reverse=True)
    for e in entries_sorted:
        for f in e.get("files", []):
            if f.endswith(".tif"):
                return f
    return None


def download(url: str, dest: Path) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": "starlink-equilibrium-model/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as out:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
    return dest.stat().st_size


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    iso3_list = load_iso3_list()
    manifest_path = OUT_DIR / "_manifest.csv"
    results = []

    for i, iso3 in enumerate(iso3_list, 1):
        dest = OUT_DIR / f"{iso3.lower()}_pd_1km.tif"
        if dest.exists() and dest.stat().st_size > 0:
            print(f"[{i}/{len(iso3_list)}] {iso3}: already downloaded, skipping")
            results.append((iso3, "already_present", dest.stat().st_size, ""))
            continue
        try:
            tif_url = fetch_tif_url(iso3)
            if tif_url is None:
                print(f"[{i}/{len(iso3_list)}] {iso3}: NO DATA on WorldPop")
                results.append((iso3, "no_data", 0, ""))
                continue
            size = download(tif_url, dest)
            print(f"[{i}/{len(iso3_list)}] {iso3}: downloaded {size / 1e6:.1f}MB")
            results.append((iso3, "ok", size, tif_url))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"[{i}/{len(iso3_list)}] {iso3}: FAILED -- {e}")
            results.append((iso3, "error", 0, str(e)))
        time.sleep(0.3)  # be polite to the free public API

    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["iso3", "status", "bytes", "detail"])
        w.writerows(results)

    ok = sum(1 for r in results if r[1] in ("ok", "already_present"))
    total_bytes = sum(r[2] for r in results)
    print(f"\nDone: {ok}/{len(iso3_list)} countries downloaded ({total_bytes / 1e9:.2f}GB total)")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
