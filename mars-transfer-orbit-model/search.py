"""Grid search over the real 2020 Mars departure window for the minimum-C3
Type-1 (<180 deg transfer angle) Earth->Mars Lambert solution.

Restricted to the single window we deliberately chose (Jul 20 - Aug 11 2020
departure; see brainstorm decision to validate one real opportunity before
generalizing to a full porkchop sweep across multiple synodic windows).
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np

import config
import ephemeris
import frames
import lambert


@dataclass
class BaselineTransfer:
    dep_epoch: str
    arr_epoch: str
    tof_days: float
    r_earth_eq: np.ndarray
    v_earth_eq: np.ndarray
    r_mars_eq: np.ndarray
    v_mars_eq: np.ndarray
    v_transfer_dep_eq: np.ndarray  # transfer-orbit velocity at departure, equatorial frame
    v_transfer_arr_eq: np.ndarray
    v_inf_dep_eq: np.ndarray
    v_inf_arr_eq: np.ndarray
    C3: float
    prop_residual_km: float


def _date_range(start, end, step_days):
    d0 = datetime.strptime(start, "%Y-%m-%d")
    d1 = datetime.strptime(end, "%Y-%m-%d")
    out = []
    d = d0
    while d <= d1:
        out.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=step_days)
    return out


def find_minimum_c3_transfer(verbose=True):
    dep_dates = _date_range(config.DEPARTURE_WINDOW_START, config.DEPARTURE_WINDOW_END,
                             config.DEPARTURE_SEARCH_STEP_DAYS)
    arr_dates = _date_range(config.ARRIVAL_WINDOW_START, config.ARRIVAL_WINDOW_END,
                             config.ARRIVAL_SEARCH_STEP_DAYS)

    earth_states = {d: ephemeris.get_state("earth", d) for d in dep_dates}
    mars_states = {d: ephemeris.get_state("mars", d) for d in arr_dates}

    best = None
    for dep in dep_dates:
        dep_dt = datetime.strptime(dep, "%Y-%m-%d")
        es = earth_states[dep]
        for arr in arr_dates:
            arr_dt = datetime.strptime(arr, "%Y-%m-%d")
            tof_days = (arr_dt - dep_dt).days
            if tof_days <= 0:
                continue
            ms = mars_states[arr]
            tof_s = tof_days * 86400.0

            # Type-1 (<180 deg) check in the ecliptic plane before solving.
            r1_ecl = frames.eq_to_ecl(es.r)
            r2_ecl = frames.eq_to_ecl(ms.r)
            cos_dnu = np.dot(r1_ecl, r2_ecl) / (np.linalg.norm(r1_ecl) * np.linalg.norm(r2_ecl))
            cross_z = np.cross(r1_ecl, r2_ecl)[2]
            if cross_z <= 0:
                continue  # would be a >180 deg (Type 2) transfer; skip for this search

            try:
                sol = lambert.solve(es.r, ms.r, tof_s)
            except Exception:
                continue

            v_earth_ecl = frames.eq_to_ecl(es.v)
            v_inf_dep_ecl = sol.v1_ecl - v_earth_ecl
            C3 = np.linalg.norm(v_inf_dep_ecl) ** 2

            if best is None or C3 < best[0]:
                best = (C3, dep, arr, tof_days, sol, es, ms)

    C3, dep, arr, tof_days, sol, es, ms = best
    v_earth_ecl = frames.eq_to_ecl(es.v)
    v_mars_ecl = frames.eq_to_ecl(ms.v)
    v_inf_dep_ecl = sol.v1_ecl - v_earth_ecl
    v_inf_arr_ecl = sol.v2_ecl - v_mars_ecl

    result = BaselineTransfer(
        dep_epoch=dep, arr_epoch=arr, tof_days=tof_days,
        r_earth_eq=es.r, v_earth_eq=es.v, r_mars_eq=ms.r, v_mars_eq=ms.v,
        v_transfer_dep_eq=frames.ecl_to_eq(sol.v1_ecl),
        v_transfer_arr_eq=frames.ecl_to_eq(sol.v2_ecl),
        v_inf_dep_eq=frames.ecl_to_eq(v_inf_dep_ecl),
        v_inf_arr_eq=frames.ecl_to_eq(v_inf_arr_ecl),
        C3=C3,
        prop_residual_km=sol.prop_residual_km,
    )
    if verbose:
        print(f"Minimum-C3 Type-1 transfer in window: depart {dep}, arrive {arr} "
              f"({tof_days:.0f} days)")
        print(f"  C3 = {C3:.4f} km^2/s^2  ({np.sqrt(C3):.4f} km/s)")
        print(f"  arrival v_inf = {np.linalg.norm(v_inf_arr_ecl):.4f} km/s")
        print(f"  Lambert propagation residual = {sol.prop_residual_km:.2e} km")
    return result


if __name__ == "__main__":
    find_minimum_c3_transfer()
