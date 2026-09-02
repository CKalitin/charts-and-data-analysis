"""Heliocentric state vectors for Earth and Mars.

Primary source: JPL Horizons API (DE441 numerical integration), fetched live
and cached to disk. Falls back to astropy's built-in analytic ephemeris
(ERFA, JPL-heritage) if the network is unavailable.

VALIDATION (done once, 2026-08-28 session, see scratch notes): the fallback
method (astropy `get_body_barycentric_posvel` for the body and the Sun, ICRS
frame, direct subtraction) was cross-checked against this same Horizons
DE441 API at two epochs (2020-07-30 for Earth, 2021-02-18 for Mars). Result:
Earth position/velocity match Horizons to ~4 km / ~1 mm/s; Mars matches to
~4 km / ~1.8 m/s. Both are far smaller than the psi-driven delta-v effects
(tens-hundreds of m/s) this model studies, so either source is adequate;
Horizons is preferred whenever reachable since it costs nothing extra and
removes the question entirely.

All epochs in this module are plain 'YYYY-MM-DD' (or full ISO) strings
interpreted as TDB (matches how Horizons labeled its own output in the
validation run -- see frames.py docstring). All returned vectors are in the
equatorial ICRS/J2000 frame (heliocentric), km and km/s. Use frames.eq_to_ecl
to convert to ecliptic-of-J2000 for plotting.
"""
import json
import subprocess
from dataclasses import dataclass

import numpy as np

import config

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

# Horizons body codes.
BODY_CODES = {"earth": "399", "mars": "499", "sun": "10"}


@dataclass
class State:
    r: np.ndarray  # km, heliocentric, ICRS/J2000 equatorial frame
    v: np.ndarray  # km/s, same frame
    source: str  # "horizons" or "astropy_fallback"


def _cache_path(body, epoch):
    safe_epoch = epoch.replace(":", "").replace(" ", "_")
    return config.CACHE_DIR / f"horizons_{body}_{safe_epoch}.json"


def _fetch_horizons(body, epoch):
    """Fetch a heliocentric ICRS state vector from JPL Horizons at `epoch` (TDB)."""
    code = BODY_CODES[body]
    # Horizons needs a stop time distinct from the start; take a 1-day window
    # and read the first (start-time) row.
    start = epoch
    from datetime import datetime, timedelta

    dt = datetime.fromisoformat(epoch) if len(epoch) > 10 else datetime.strptime(epoch, "%Y-%m-%d")
    stop = (dt + timedelta(days=1)).strftime("%Y-%m-%d")

    args = [
        "curl", "-sS", "-G", HORIZONS_URL,
        "--data-urlencode", "format=text",
        "--data-urlencode", f"COMMAND={code}",
        "--data-urlencode", "OBJ_DATA=NO",
        "--data-urlencode", "MAKE_EPHEM=YES",
        "--data-urlencode", "EPHEM_TYPE=VECTORS",
        "--data-urlencode", "CENTER=500@10",
        "--data-urlencode", f"START_TIME={start}",
        "--data-urlencode", f"STOP_TIME={stop}",
        "--data-urlencode", "STEP_SIZE=1d",
        "--data-urlencode", "REF_PLANE=FRAME",
        "--data-urlencode", "OUT_UNITS=KM-S",
    ]
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    text = result.stdout
    if "$$SOE" not in text or "$$EOE" not in text:
        raise RuntimeError(f"Horizons response missing vector block for {body}@{epoch}")

    block = text.split("$$SOE")[1].split("$$EOE")[0]
    lines = [ln for ln in block.splitlines() if ln.strip()]
    # First 2 non-empty lines after $$SOE are the first epoch's record:
    #   "<JD> = <calendar date> TDB"
    #   " X = ... Y = ... Z = ..."
    #   " VX= ... VY= ... VZ= ..."
    x_line = lines[1]
    v_line = lines[2]

    def parse_triplet(line, keys):
        import re
        vals = []
        for key in keys:
            m = re.search(rf"{key}\s*=\s*([-+0-9.eE]+)", line)
            if m is None:
                raise RuntimeError(f"could not parse {key!r} from Horizons line: {line!r}")
            vals.append(float(m.group(1)))
        return vals

    x, y, z = parse_triplet(x_line, ["X", "Y", "Z"])
    vx, vy, vz = parse_triplet(v_line, ["VX", "VY", "VZ"])
    return np.array([x, y, z]), np.array([vx, vy, vz])


def _fetch_astropy(body, epoch):
    """Fallback: astropy builtin analytic ephemeris, ICRS frame, heliocentric."""
    from astropy.time import Time
    from astropy.coordinates import get_body_barycentric_posvel
    import astropy.units as u

    t = Time(epoch, scale="tdb")
    pos_b, vel_b = get_body_barycentric_posvel(body, t)
    pos_s, vel_s = get_body_barycentric_posvel("sun", t)
    r = (pos_b - pos_s).xyz.to(u.km).value
    v = (vel_b - vel_s).xyz.to(u.km / u.s).value
    return r, v


def get_state(body, epoch, use_cache=True):
    """Heliocentric ICRS state of `body` ('earth'|'mars') at `epoch` (TDB date string)."""
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(body, epoch)
    if use_cache and cache_file.exists():
        data = json.loads(cache_file.read_text())
        return State(np.array(data["r"]), np.array(data["v"]), data["source"])

    try:
        r, v = _fetch_horizons(body, epoch)
        source = "horizons"
    except Exception as exc:  # network down, API change, etc.
        print(f"  [ephemeris] Horizons fetch failed for {body}@{epoch} ({exc}); "
              f"falling back to astropy builtin ephemeris.")
        r, v = _fetch_astropy(body, epoch)
        source = "astropy_fallback"

    if use_cache:
        cache_file.write_text(json.dumps({"r": r.tolist(), "v": v.tolist(), "source": source}))
    return State(r, v, source)
