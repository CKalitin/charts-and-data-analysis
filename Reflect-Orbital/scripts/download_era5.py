"""Download ERA5 monthly-mean total cloud cover and save to data/era5_tcc.nc.

Requires ~/.cdsapirc to be configured with valid CDS credentials.
Run once:  python scripts/download_era5.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg

import cdsapi

cfg.DATA_DIR.mkdir(exist_ok=True)
out = cfg.ERA5_NC

if out.exists():
    print(f"Already exists: {out}  (delete it to re-download)")
    sys.exit(0)

client = cdsapi.Client()
client.retrieve(
    "reanalysis-era5-single-levels-monthly-means",
    {
        "product_type": "monthly_averaged_reanalysis",
        "variable": "total_cloud_cover",
        "year": [str(y) for y in range(2018, 2024)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "time": "00:00",
        "format": "netcdf",
    },
    str(out),
)
print(f"Saved to {out}")
