"""Orchestrator — propagate the SSO ground track once, classify, render every chart.

  python run.py            # generate all charts
  python run.py --count    # dry-run: print the chart count
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as cfg
import derived
from model import OrbitParams, propagate_orbit
from charts.proximity_map import figures as proximity_figures
from charts.solar_proximity import figures as solar_figures
from charts.transmission_proximity import figures as transmission_figures

# The transmission chart is produced only for this one case.
_TRANSMISSION_CASE = (100.0, frozenset({"China"}))
from viz import render


def main() -> None:
    dry_run = "--count" in sys.argv
    t0 = time.time()

    params = OrbitParams(alt_km=cfg.ALT_KM, inc_deg=cfg.INC_DEG)
    period_min = params.period_s / 60.0
    print(f"Propagating {cfg.N_ORBITS} orbits  "
          f"({cfg.ALT_KM} km, {cfg.INC_DEG} deg, T={period_min:.1f} min, "
          f"{1440/period_min:.2f} orbits/day)...")
    lats, lons = propagate_orbit(params, cfg.N_ORBITS, cfg.N_PER_ORBIT)

    print("Classifying ground track + background raster...")
    assets = derived.load_land_assets()
    data = derived.compute(lats, lons, assets)
    lon_e, lat_e, grid = derived.classify_grid(assets)
    rings = derived.land_polygons(assets)

    print(f"  Over land     : {data.pct_land:5.1f}%")
    print(f"  Coastal water : {data.pct_near:5.1f}%  (within {cfg.THRESHOLD_MI} mi of a coast)")
    print(f"  Open ocean    : {data.pct_ocean:5.1f}%")
    print(f"  SURPRISE      : {data.pct_land + data.pct_near:.0f}% of orbit time is within "
          f"{cfg.THRESHOLD_MI} mi of land -- well above Earth's 29% land share, because the "
          f"polar track lingers over Eurasia, N. America and the Antarctic margins.")

    plan = [*proximity_figures(data, lon_e, lat_e, grid, rings, period_min)]

    for min_mw, excl in cfg.SOLAR_CASES:
        solar = derived.load_solar_assets(min_mw, excl)
        sdata = derived.compute_solar(lats, lons, solar)
        s_lon_e, s_lat_e, s_grid = derived.classify_solar_grid(solar)
        tag = f" >= {min_mw:g} MW" if min_mw > 0 else " (all sizes)"
        if excl:
            tag += f", excl. {', '.join(sorted(excl))}"
        print(f"\nSolar arrays{tag}:")
        print(f"  Arrays kept   : {solar.n:,}  ({solar.total_gw:,.0f} GW)")
        print(f"  Within {cfg.THRESHOLD_MI} mi   : {sdata.pct_near:5.1f}%  (of orbit time)")
        print(f"  Beyond range  : {sdata.pct_far:5.1f}%")
        plan += solar_figures(sdata, solar, s_lon_e, s_lat_e, s_grid, rings, period_min)

        if (min_mw, excl) == _TRANSMISSION_CASE:
            cloud  = derived.load_cloud_cover()
            teff   = derived.compute_teff(solar, cloud)
            print(f"  Cloud source  : {cloud.source}")
            print(f"  T_eff mean    : {teff.mean():.3f}  "
                  f"(range {teff.min():.3f}--{teff.max():.3f})")
            t_lon_e, t_lat_e, teff_raster = derived.classify_teff_grid(solar, teff)
            ot = derived.compute_orbit_transmission(sdata, solar, teff)
            print(f"  Net utility   : {ot.net_utility:.1f}%  "
                  f"({ot.pct_near:.1f}% in range x {ot.mean_teff:.3f} T_eff)")
            plan += transmission_figures(
                sdata, solar, t_lon_e, t_lat_e, teff_raster, rings,
                cloud, ot, period_min,
            )

    if dry_run:
        print(f"Would generate {len(plan)} charts.")
        return

    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")

    print(f"\nDone -- {len(plan)} charts in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
