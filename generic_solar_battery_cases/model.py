"""Physics of a solar + battery system serving a constant load.

Pure, side-effect-free, plotting-free. The dependency flow is one direction:

    NSRDB CSV --load_nsrdb-->  NsrdbData (GHI series + timestep)
       GHI    --generation-->  generation time series (kW)
    generation --dispatch--->  served energy (kWh) per configuration

Everything is vectorized: one `simulate_dispatch` call advances an entire
(kW solar × kWh battery) grid through a single time loop by broadcasting the
config dimensions. The SOC recursion is sequential in time but simultaneous
across configs, so a year-long full-grid sweep costs one time loop.

The one expensive quantity, `served_kwh(S, B)`, depends only on physics — never
on prices — which is why it can be computed once and reused for every economic
optimization downstream.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

# Rows 0–1 of an NSRDB point CSV are metadata/units; row 2 is the real header.
_NSRDB_HEADER_ROW = 2


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
@dataclass
class NsrdbData:
    """A parsed NSRDB point file."""

    frame: pd.DataFrame
    ghi_w_m2: np.ndarray
    dt_hours: float
    latitude: float = float("nan")
    longitude: float = float("nan")

    @property
    def timestamps(self) -> pd.DatetimeIndex:
        return self.frame.index

    @property
    def n_steps(self) -> int:
        return self.ghi_w_m2.shape[0]

    @property
    def duration_hours(self) -> float:
        return self.n_steps * self.dt_hours

    @property
    def site_id(self) -> str:
        src = str(self.frame.attrs.get("source_path", ""))
        stem = Path(src).stem
        parts = stem.split("_")
        return parts[1] if len(parts) > 1 else stem

    @property
    def year(self) -> int:
        return int(self.timestamps[0].year)


def load_nsrdb(
    path: str | Path = cfg.DATA_FILE,
    irradiance_column: str = "GHI",
    resample: str | None = None,
) -> NsrdbData:
    """Load a single-point NSRDB CSV.

    ``resample`` (e.g. ``"1h"``) downsamples the irradiance series by mean —
    useful to speed up the one-time grid sweep; ``None`` keeps native resolution.
    """
    path = Path(path)
    lat, lon = read_coords(path)
    frame = pd.read_csv(path, skiprows=_NSRDB_HEADER_ROW).rename(columns=str.strip)
    timestamps = pd.to_datetime(frame[["Year", "Month", "Day", "Hour", "Minute"]])
    frame = frame.set_index(timestamps)
    frame.attrs["source_path"] = str(path)

    if resample is not None:
        ghi_series = frame[irradiance_column].resample(resample).mean()
        frame = frame.resample(resample).mean(numeric_only=True)
        frame.attrs["source_path"] = str(path)
        ghi = ghi_series.to_numpy(dtype=float)
    else:
        ghi = frame[irradiance_column].to_numpy(dtype=float)

    return NsrdbData(frame=frame, ghi_w_m2=ghi, dt_hours=_infer_timestep_hours(frame.index),
                     latitude=lat, longitude=lon)


def read_coords(path: str | Path) -> tuple[float, float]:
    """Read (latitude, longitude) from an NSRDB point file's metadata header.

    Row 0 is the metadata field names, row 1 the values; ``Latitude`` /
    ``Longitude`` live there (the data block below starts at row 2).
    """
    meta = pd.read_csv(path, nrows=1)
    try:
        return float(meta["Latitude"].iloc[0]), float(meta["Longitude"].iloc[0])
    except (KeyError, ValueError):
        return float("nan"), float("nan")


def _infer_timestep_hours(timestamps: pd.DatetimeIndex) -> float:
    if len(timestamps) < 2:
        raise ValueError("Need at least two samples to infer a timestep.")
    return (timestamps[1] - timestamps[0]) / pd.Timedelta(hours=1)


def solar_generation_kw(
    ghi_w_m2: np.ndarray,
    kw_solar_nameplate: float | np.ndarray,
    reference_irradiance_w_m2: float = cfg.REFERENCE_IRRADIANCE_W_M2,
) -> np.ndarray:
    """Linear-GHI generation: ``kW = nameplate · GHI / reference``. Broadcasts."""
    ghi = np.asarray(ghi_w_m2, dtype=float)
    return np.asarray(kw_solar_nameplate, dtype=float) * ghi / reference_irradiance_w_m2


def annual_capacity_factor(data: NsrdbData) -> float:
    """Mean GHI / reference — the capacity factor of a 1 kW flat array."""
    return float(np.mean(data.ghi_w_m2) / cfg.REFERENCE_IRRADIANCE_W_M2)


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
@dataclass
class DispatchResult:
    """Energy accounting for one or many configs (fields shaped like the grid).

    The ``*_ts`` time-series fields are populated only when ``record=True`` (a
    single, small config); otherwise they are ``None``.
    """

    demand_kwh: float
    served_kwh: np.ndarray
    curtailed_kwh: np.ndarray
    final_soc_kwh: np.ndarray
    # optional per-step series, shape (T, *cfg), present iff record=True
    soc_ts: np.ndarray | None = None
    served_ts: np.ndarray | None = None
    curtailed_ts: np.ndarray | None = None
    unmet_ts: np.ndarray | None = None

    @property
    def utilization(self) -> np.ndarray:
        with np.errstate(invalid="ignore", divide="ignore"):
            u = np.where(self.demand_kwh > 0, self.served_kwh / self.demand_kwh, 0.0)
        return np.clip(u, 0.0, 1.0)


def simulate_dispatch(
    gen_kw: np.ndarray,
    load_kw: float,
    battery_kwh: float | np.ndarray,
    dt_hours: float,
    round_trip_efficiency: float = cfg.ROUND_TRIP_EFFICIENCY,
    initial_soc_kwh: float | np.ndarray = 0.0,
    record: bool = False,
) -> DispatchResult:
    """Greedy "solar-first, battery-buffer" dispatch over a time series.

    Surplus generation charges the battery (excess curtailed); a load deficit is
    drawn from the battery (shortfall unmet). One time loop advances every config
    in a broadcast grid simultaneously.

    ``gen_kw`` has shape ``(T, *cfg)``: leading axis time, trailing axes index
    configurations. ``record=True`` stores full per-step series (use only for a
    single small config — it allocates ``(T, *cfg)`` arrays).
    """
    gen_kw = np.asarray(gen_kw, dtype=float)
    n_steps = gen_kw.shape[0]
    cfg_shape = np.broadcast_shapes(gen_kw.shape[1:], np.shape(battery_kwh))

    cap = np.broadcast_to(np.asarray(battery_kwh, dtype=float), cfg_shape)
    leg_eff = math.sqrt(round_trip_efficiency)

    soc = np.broadcast_to(np.asarray(initial_soc_kwh, dtype=float), cfg_shape).astype(float).copy()
    served_kwh = np.zeros(cfg_shape)
    curtailed_kwh = np.zeros(cfg_shape)

    if record:
        soc_ts = np.zeros((n_steps, *cfg_shape))
        served_ts = np.zeros((n_steps, *cfg_shape))
        curtailed_ts = np.zeros((n_steps, *cfg_shape))
        unmet_ts = np.zeros((n_steps, *cfg_shape))

    load_step_kwh = load_kw * dt_hours

    for t in range(n_steps):
        net_energy = (gen_kw[t] - load_kw) * dt_hours  # +surplus / −deficit (kWh)
        surplus = np.maximum(net_energy, 0.0)
        deficit = np.maximum(-net_energy, 0.0)

        # Charge: store as much surplus as fits; curtail the rest (load-side).
        room = cap - soc
        stored = np.minimum(surplus * leg_eff, room)
        curt = surplus - stored / leg_eff
        soc = soc + stored
        curtailed_kwh = curtailed_kwh + curt

        # Discharge: deliver as much of the deficit as the battery allows.
        deliverable = soc * leg_eff
        delivered = np.minimum(deficit, deliverable)
        soc = soc - delivered / leg_eff

        # Served = load met directly by generation + load met from the battery.
        direct = load_step_kwh - deficit          # generation covering load this step
        served = direct + delivered
        served_kwh = served_kwh + served

        if record:
            soc_ts[t] = soc
            served_ts[t] = served
            curtailed_ts[t] = curt
            unmet_ts[t] = load_step_kwh - served

    demand_kwh = float(load_step_kwh * n_steps)
    return DispatchResult(
        demand_kwh=demand_kwh,
        served_kwh=served_kwh,
        curtailed_kwh=curtailed_kwh,
        final_soc_kwh=soc,
        soc_ts=soc_ts if record else None,
        served_ts=served_ts if record else None,
        curtailed_ts=curtailed_ts if record else None,
        unmet_ts=unmet_ts if record else None,
    )


def steady_state_dispatch(
    gen_kw: np.ndarray,
    load_kw: float,
    battery_kwh: float | np.ndarray,
    dt_hours: float,
    round_trip_efficiency: float = cfg.ROUND_TRIP_EFFICIENCY,
    max_iters: int = cfg.WARMSTART_MAX_ITERS,
    tol: float = cfg.WARMSTART_TOL,
    record: bool = False,
    verbose: bool = False,
) -> tuple[DispatchResult, int]:
    """Run dispatch to a periodic (year-end SOC == year-start SOC) fixed point.

    Iterates the map ``soc0 -> final_soc(soc0)`` until the start and end states
    agree to within ``tol`` (relative to capacity). The returned result is
    therefore self-consistent steady-state operation, with no cold-start
    artifact — the reason utilization can reach >99.8% instead of being capped
    by an empty battery on the first day.

    Returns ``(result, n_iters)``.
    """
    cfg_shape = np.broadcast_shapes(gen_kw.shape[1:], np.shape(battery_kwh))
    cap = np.broadcast_to(np.asarray(battery_kwh, dtype=float), cfg_shape)
    soc0 = np.zeros(cfg_shape)

    res = None
    for it in range(1, max_iters + 1):
        # Record only on the final, converged pass to avoid storing T×grid arrays repeatedly.
        res = simulate_dispatch(
            gen_kw, load_kw, battery_kwh, dt_hours, round_trip_efficiency,
            initial_soc_kwh=soc0, record=False,
        )
        with np.errstate(invalid="ignore", divide="ignore"):
            rel = np.where(cap > 0, np.abs(res.final_soc_kwh - soc0) / cap, 0.0)
        max_rel = float(np.max(rel)) if rel.size else 0.0
        if verbose:
            print(f"  warm-start iter {it}: max |dSOC|/cap = {max_rel:.2e}", flush=True)
        if max_rel < tol:
            break
        soc0 = res.final_soc_kwh

    if record:
        res = simulate_dispatch(
            gen_kw, load_kw, battery_kwh, dt_hours, round_trip_efficiency,
            initial_soc_kwh=soc0, record=True,
        )
    return res, it


# --------------------------------------------------------------------------- #
# Served-energy grid — the single expensive, price-independent computation
# --------------------------------------------------------------------------- #
@dataclass
class ServedGrid:
    """``served_kwh[i, j]`` for solar ``kw_solar[i]`` × battery ``kwh_battery[j]``."""

    kw_solar: np.ndarray       # (nS,)
    kwh_battery: np.ndarray    # (nB,)
    served_kwh: np.ndarray     # (nS, nB)
    demand_kwh: float
    capacity_factor: float
    warmstart_iters: int

    @property
    def utilization(self) -> np.ndarray:
        return self.served_kwh / self.demand_kwh


def served_energy_grid(
    data: NsrdbData,
    kw_solar: np.ndarray = cfg.KW_SOLAR_GRID,
    kwh_battery: np.ndarray = cfg.KWH_BATTERY_GRID,
    load_kw: float = cfg.LOAD_KW,
    round_trip_efficiency: float = cfg.ROUND_TRIP_EFFICIENCY,
    verbose: bool = True,
) -> ServedGrid:
    """Energy delivered to the load for every (kW solar × kWh battery) config.

    gen depends only on the solar axis: shape ``(T, nS, 1)`` broadcasts against
    the ``(1, nB)`` capacity axis, so the whole grid rides one time loop, run to
    a steady-state SOC fixed point.
    """
    kw_solar = np.asarray(kw_solar, dtype=float)
    kwh_battery = np.asarray(kwh_battery, dtype=float)

    gen_kw = solar_generation_kw(data.ghi_w_m2[:, None, None], kw_solar[None, :, None])
    capacity = kwh_battery[None, :]

    res, iters = steady_state_dispatch(
        gen_kw, load_kw, capacity, data.dt_hours, round_trip_efficiency, verbose=verbose
    )
    served = np.broadcast_to(res.served_kwh, (kw_solar.size, kwh_battery.size)).copy()

    return ServedGrid(
        kw_solar=kw_solar,
        kwh_battery=kwh_battery,
        served_kwh=served,
        demand_kwh=res.demand_kwh,
        capacity_factor=annual_capacity_factor(data),
        warmstart_iters=iters,
    )
