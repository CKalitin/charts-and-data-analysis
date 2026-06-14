"""Core simulator for a solar + battery system serving a fixed load.

This module is deliberately plotting-free and side-effect-free so that any
analysis script can import the physics and economics primitives and build on
top of them.  The pieces compose like this:

    NSRDB CSV  --load_nsrdb_csv-->  NsrdbData (GHI time series + timestep)
        GHI    --solar_generation_kw-->  generation time series (kW)
    generation --simulate_dispatch-->  DispatchResult (utilization, energy)
    geometry   --capital_cost------->  system capex
    grid sweep --sweep_solar_battery->  SweepResult (2D utilization + cost)

Everything downstream of `simulate_dispatch` is fully vectorized: a single call
can evaluate an entire (kW solar x kWh battery) grid at once by broadcasting the
config dimensions, so a year-long, full-grid sweep runs in a couple of seconds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Irradiance at which a panel produces its nameplate rating (standard test
# conditions).  Generation is modeled as linear in GHI up to and beyond this.
REFERENCE_IRRADIANCE_W_M2 = 1000.0

# Rows 0-1 of an NSRDB point CSV are metadata/units; row 2 is the real header.
_NSRDB_HEADER_ROW = 2


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
@dataclass
class NsrdbData:
    """A parsed NSRDB point file.

    Attributes
    ----------
    frame : pd.DataFrame
        The full record, indexed by timestamp, with the original columns.
    ghi_w_m2 : np.ndarray
        Global Horizontal Irradiance time series (W/m^2), shape ``(T,)``.
    dt_hours : float
        Spacing between samples in hours (e.g. ``1/6`` for 10-minute data).
    """

    frame: pd.DataFrame
    ghi_w_m2: np.ndarray
    dt_hours: float

    @property
    def timestamps(self) -> pd.DatetimeIndex:
        return self.frame.index

    @property
    def n_steps(self) -> int:
        return self.ghi_w_m2.shape[0]

    @property
    def duration_hours(self) -> float:
        return self.n_steps * self.dt_hours


def load_nsrdb_csv(path: str | Path, irradiance_column: str = "GHI") -> NsrdbData:
    """Load a single-point NSRDB CSV into an :class:`NsrdbData`.

    Parameters
    ----------
    path : str or Path
        Path to an ``nsrdb_<id>_<year>.csv`` file.
    irradiance_column : str
        Which irradiance column drives generation.  ``"GHI"`` (measured global
        horizontal irradiance) is the right default for a fixed flat array.
    """
    path = Path(path)
    frame = pd.read_csv(path, skiprows=_NSRDB_HEADER_ROW)
    frame = frame.rename(columns=str.strip)

    timestamps = pd.to_datetime(
        frame[["Year", "Month", "Day", "Hour", "Minute"]]
    )
    frame = frame.set_index(timestamps)

    dt_hours = _infer_timestep_hours(timestamps)
    ghi = frame[irradiance_column].to_numpy(dtype=float)
    return NsrdbData(frame=frame, ghi_w_m2=ghi, dt_hours=dt_hours)


def _infer_timestep_hours(timestamps: pd.DatetimeIndex) -> float:
    """Infer a uniform sample spacing (hours) from the first two timestamps."""
    if len(timestamps) < 2:
        raise ValueError("Need at least two samples to infer a timestep.")
    delta = timestamps[1] - timestamps[0]
    return delta / pd.Timedelta(hours=1)


# --------------------------------------------------------------------------- #
# Generation model
# --------------------------------------------------------------------------- #
def solar_generation_kw(
    ghi_w_m2: np.ndarray,
    kw_solar_nameplate: float | np.ndarray,
    reference_irradiance_w_m2: float = REFERENCE_IRRADIANCE_W_M2,
) -> np.ndarray:
    """Linear-GHI generation model: ``kW = nameplate * GHI / reference``.

    Broadcasts, so a ``(T,)`` irradiance series times a ``(n_kw,)`` vector of
    nameplate sizes (shaped ``(1, n_kw)``) yields a ``(T, n_kw)`` field.
    """
    ghi = np.asarray(ghi_w_m2, dtype=float)
    return np.asarray(kw_solar_nameplate, dtype=float) * ghi / reference_irradiance_w_m2


# --------------------------------------------------------------------------- #
# Dispatch simulation
# --------------------------------------------------------------------------- #
@dataclass
class DispatchResult:
    """Annual energy accounting for one or many configurations.

    Scalar inputs give scalar (0-d array) fields; a broadcast config grid gives
    fields shaped like that grid.

    Attributes
    ----------
    demand_kwh : float
        Total load energy demanded over the horizon.
    served_kwh, unmet_kwh, curtailed_kwh : np.ndarray
        Energy delivered to the load, energy the system failed to deliver, and
        surplus generation that could not be stored (all kWh, load-side).
    utilization : np.ndarray
        ``served / demand`` in ``[0, 1]`` -- the fraction of load met.
    final_soc_kwh : np.ndarray
        Battery state of charge at the end of the horizon.
    """

    demand_kwh: float
    served_kwh: np.ndarray
    unmet_kwh: np.ndarray
    curtailed_kwh: np.ndarray
    utilization: np.ndarray
    final_soc_kwh: np.ndarray


def simulate_dispatch(
    gen_kw: np.ndarray,
    load_kw: float | np.ndarray,
    battery_kwh: float | np.ndarray,
    dt_hours: float,
    round_trip_efficiency: float = 1.0,
    verbose: bool = True,
    initial_soc_kwh: float | np.ndarray = 0.0,
) -> DispatchResult:
    """Greedy "solar-first, battery-buffer" dispatch over a time series.

    At each step surplus generation charges the battery (excess is curtailed)
    and any load deficit is drawn from the battery (shortfall is unmet).  The
    state-of-charge recursion is inherently sequential in time, but every
    configuration in a broadcast grid is advanced simultaneously, so sweeping
    thousands of (kW, kWh) points costs the same as a single time loop.

    Parameters
    ----------
    gen_kw : np.ndarray
        Generation time series, shape ``(T, *cfg)``.  The leading axis is time;
        any trailing axes index configurations (e.g. different solar sizes).
    load_kw : float or np.ndarray
        Constant load (scalar) or a per-step load series of shape ``(T,)``.
    battery_kwh : float or np.ndarray
        Usable battery capacity, broadcastable to ``cfg``.
    dt_hours : float
        Timestep length in hours.
    round_trip_efficiency : float
        Battery round-trip efficiency in ``(0, 1]``; split symmetrically into
        charge and discharge legs.  ``1.0`` is lossless.

    Returns
    -------
    DispatchResult
        Energy totals and utilization shaped like the config grid ``cfg``.
    """
    gen_kw = np.asarray(gen_kw, dtype=float)
    n_steps = gen_kw.shape[0]
    cfg_shape = np.broadcast_shapes(gen_kw.shape[1:], np.shape(battery_kwh))

    cap = np.broadcast_to(np.asarray(battery_kwh, dtype=float), cfg_shape)
    leg_efficiency = math.sqrt(round_trip_efficiency)

    load = np.asarray(load_kw, dtype=float)
    load_is_series = load.ndim > 0
    if load_is_series:
        if load.shape[0] != n_steps:
            raise ValueError("Load series length must match the time axis.")
        load = load.reshape((n_steps,) + (1,) * len(cfg_shape))

    soc = np.broadcast_to(np.asarray(initial_soc_kwh, dtype=float), cfg_shape).copy()
    unmet_kwh = np.zeros(cfg_shape)
    curtailed_kwh = np.zeros(cfg_shape)

    milestones = {int(n_steps * p / 10) for p in range(1, 11)} if verbose else set()

    for t in range(n_steps):
        if verbose and t in milestones:
            print(f"  Dispatch {t / n_steps:>4.0%} ({t:,}/{n_steps:,} steps)", flush=True)
        load_t = load[t] if load_is_series else load
        net_energy = (gen_kw[t] - load_t) * dt_hours  # +surplus / -deficit, kWh

        surplus = np.maximum(net_energy, 0.0)
        deficit = np.maximum(-net_energy, 0.0)

        # Charge: store as much surplus as fits; curtail the rest (load-side).
        room = cap - soc
        stored = np.minimum(surplus * leg_efficiency, room)
        curtailed_kwh = curtailed_kwh + (surplus - stored / leg_efficiency)
        soc = soc + stored

        # Discharge: deliver as much of the deficit as the battery allows.
        deliverable = soc * leg_efficiency
        delivered = np.minimum(deficit, deliverable)
        unmet_kwh = unmet_kwh + (deficit - delivered)
        soc = soc - delivered / leg_efficiency

    total_load_kwh = float(np.sum(load) * dt_hours) if load_is_series else float(
        load * dt_hours * n_steps
    )
    served_kwh = total_load_kwh - unmet_kwh
    with np.errstate(invalid="ignore", divide="ignore"):
        utilization = np.where(total_load_kwh > 0, served_kwh / total_load_kwh, 0.0)
    utilization = np.clip(utilization, 0.0, 1.0)  # guard float noise at the edges

    return DispatchResult(
        demand_kwh=total_load_kwh,
        served_kwh=served_kwh,
        unmet_kwh=unmet_kwh,
        curtailed_kwh=curtailed_kwh,
        utilization=utilization,
        final_soc_kwh=soc,
    )


# --------------------------------------------------------------------------- #
# Economics
# --------------------------------------------------------------------------- #
@dataclass
class CostParams:
    """Unit prices for the system components.

    ``load_per_kw``        one-time capex for the load equipment ($ / kW).
    ``load_value_per_kwh`` revenue earned per kWh actually delivered to the load
                           ($ / kWh).  Used to compute net value = income - capex.
    """

    gen_per_kw: float
    storage_per_kwh: float
    load_per_kw: float = 0.0
    load_value_per_kwh: float = 0.0


def capital_cost(
    kw_solar: float | np.ndarray,
    battery_kwh: float | np.ndarray,
    cost: CostParams,
    load_kw: float | np.ndarray = 1.0,
) -> np.ndarray:
    """Total capital cost of a configuration (broadcasts over arrays)."""
    return (
        np.asarray(kw_solar, dtype=float) * cost.gen_per_kw
        + np.asarray(battery_kwh, dtype=float) * cost.storage_per_kwh
        + np.asarray(load_kw, dtype=float) * cost.load_per_kw
    )


# --------------------------------------------------------------------------- #
# Grid sweep
# --------------------------------------------------------------------------- #
@dataclass
class SweepResult:
    """Results of a (kW solar x kWh battery) sweep on a regular grid.

    ``utilization`` and ``cost`` are 2D arrays indexed ``[i_kw, j_kwh]``.  The
    ``KW`` / ``KWH`` meshgrids (``indexing="ij"``) align with them element-wise,
    which is what ``contour``/``pcolormesh`` want.
    """

    kw_solar: np.ndarray      # (n_kw,)
    kwh_battery: np.ndarray   # (n_kwh,)
    KW: np.ndarray            # (n_kw, n_kwh)
    KWH: np.ndarray           # (n_kw, n_kwh)
    utilization: np.ndarray   # (n_kw, n_kwh)  fraction in [0, 1]
    cost: np.ndarray          # (n_kw, n_kwh)  system capex ($)
    net_value: np.ndarray     # (n_kw, n_kwh)  income - capex ($)
    dispatch: DispatchResult  # full energy accounting on the grid

    def lowest_cost_meeting(self, min_utilization: float) -> dict | None:
        """Cheapest grid point whose utilization is at least ``min_utilization``.

        Returns ``None`` if no configuration on the grid clears the threshold.
        """
        feasible = self.utilization >= min_utilization
        if not feasible.any():
            return None
        masked_cost = np.where(feasible, self.cost, np.inf)
        i, j = np.unravel_index(np.argmin(masked_cost), masked_cost.shape)
        return {
            "kw_solar": float(self.kw_solar[i]),
            "kwh_battery": float(self.kwh_battery[j]),
            "cost": float(self.cost[i, j]),
            "utilization": float(self.utilization[i, j]),
        }


def sweep_solar_battery(
    data: NsrdbData,
    kw_solar: np.ndarray,
    kwh_battery: np.ndarray,
    cost: CostParams,
    load_kw: float = 1.0,
    round_trip_efficiency: float = 1.0,
    verbose: bool = True,
) -> SweepResult:
    """Evaluate utilization and cost over a full kW x kWh grid in one pass.

    Generation depends only on the solar axis and load is constant, so the
    per-step net energy is shaped ``(n_kw, 1)`` and broadcasts against the
    ``(1, n_kwh)`` capacity axis -- the whole grid rides through a single time
    loop inside :func:`simulate_dispatch`.

    Circular warm-up: the simulation is run twice. The first pass starts with
    an empty battery (cold start) and records the year-end SOC for every config.
    The second pass uses those SOC values as the initial condition, approximating
    steady-state operation and eliminating the artificial unmet-demand spike on
    Jan 1 that occurs when the battery starts empty.
    """
    kw_solar = np.asarray(kw_solar, dtype=float)
    kwh_battery = np.asarray(kwh_battery, dtype=float)

    # gen_kw shape (T, n_kw, 1); capacity shape (1, n_kwh) -> grid (n_kw, n_kwh).
    gen_kw = solar_generation_kw(data.ghi_w_m2[:, None, None], kw_solar[None, :, None])
    capacity = kwh_battery[None, :]

    _dispatch_kwargs = dict(
        gen_kw=gen_kw,
        load_kw=load_kw,
        battery_kwh=capacity,
        dt_hours=data.dt_hours,
        round_trip_efficiency=round_trip_efficiency,
        verbose=verbose,
    )

    if verbose:
        print("  Pass 1/2 (cold start) ...")
    cold = simulate_dispatch(**_dispatch_kwargs)

    if verbose:
        print("  Pass 2/2 (warm start) ...")
    dispatch = simulate_dispatch(**_dispatch_kwargs, initial_soc_kwh=cold.final_soc_kwh)

    KW, KWH = np.meshgrid(kw_solar, kwh_battery, indexing="ij")
    cost_grid = capital_cost(KW, KWH, cost, load_kw=load_kw)
    util_grid = np.broadcast_to(dispatch.utilization, KW.shape).copy()

    # served_kwh has shape (n_kw, n_kwh) via the dispatch broadcast.
    served_grid = np.broadcast_to(dispatch.served_kwh, KW.shape).copy()
    net_value_grid = served_grid * cost.load_value_per_kwh - cost_grid

    return SweepResult(
        kw_solar=kw_solar,
        kwh_battery=kwh_battery,
        KW=KW,
        KWH=KWH,
        utilization=util_grid,
        cost=cost_grid,
        net_value=net_value_grid,
        dispatch=dispatch,
    )


@dataclass
class TimeseriesResult:
    """Per-timestep dispatch output for a single (kW solar, kWh battery) config.

    All ``*_kwh`` arrays are energy in the timestep (kWh per step), not power.
    ``soc_kwh`` is the battery state of charge at the *end* of each step.
    """

    timestamps: pd.DatetimeIndex
    ghi_w_m2: np.ndarray
    gen_kw: np.ndarray
    soc_kwh: np.ndarray
    served_kwh: np.ndarray
    unmet_kwh: np.ndarray
    curtailed_kwh: np.ndarray
    load_kwh: np.ndarray
    dt_hours: float
    kw_solar: float
    kwh_battery_capacity: float
    load_kw: float


def dispatch_timeseries(
    data: NsrdbData,
    kw_solar: float,
    kwh_battery: float,
    load_kw: float = 1.0,
    round_trip_efficiency: float = 1.0,
) -> TimeseriesResult:
    """Greedy dispatch for a single config, recording the full state time series.

    Identical physics to :func:`simulate_dispatch` but operates on scalars so
    the loop can store SoC and energy flows at every timestep.
    """
    gen = solar_generation_kw(data.ghi_w_m2, float(kw_solar))
    n = len(gen)
    dt = data.dt_hours
    leg_eff = math.sqrt(round_trip_efficiency)
    cap = float(kwh_battery)

    # Circular warm-up: run once from SOC=0 to get year-end SOC, then re-run
    # using that as the starting condition.  This eliminates the artificial
    # unmet-demand spike on Jan 1 caused by starting with an empty battery.
    def _run_loop(initial_soc: float):
        soc_ts = np.zeros(n)
        served_ts = np.zeros(n)
        unmet_ts = np.zeros(n)
        curtailed_ts = np.zeros(n)
        soc = initial_soc
        for t in range(n):
            net = (gen[t] - load_kw) * dt  # +surplus / -deficit kWh
            if net >= 0:
                stored = min(net * leg_eff, cap - soc)
                curtailed_ts[t] = net - stored / leg_eff
                soc += stored
            else:
                deficit = -net
                delivered = min(deficit, soc * leg_eff)
                soc -= delivered / leg_eff
                unmet_ts[t] = deficit - delivered
            served_ts[t] = max(0.0, load_kw * dt - unmet_ts[t])
            soc_ts[t] = soc
        return soc_ts, served_ts, unmet_ts, curtailed_ts

    cold_soc_ts, _, _, _ = _run_loop(0.0)                                    # pass 1: cold start
    soc_ts, served_ts, unmet_ts, curtailed_ts = _run_loop(cold_soc_ts[-1])  # pass 2: warm start

    return TimeseriesResult(
        timestamps=data.timestamps,
        ghi_w_m2=data.ghi_w_m2.copy(),
        gen_kw=gen,
        soc_kwh=soc_ts,
        served_kwh=served_ts,
        unmet_kwh=unmet_ts,
        curtailed_kwh=curtailed_ts,
        load_kwh=np.full(n, load_kw * dt),
        dt_hours=dt,
        kw_solar=float(kw_solar),
        kwh_battery_capacity=float(kwh_battery),
        load_kw=float(load_kw),
    )


def solar_resource_kwh_m2(data: NsrdbData) -> tuple[float, float]:
    """Total and daily-average GHI irradiation for the dataset period.

    Returns
    -------
    yearly : float
        Cumulative irradiation over the full dataset (kWh / m²).
    daily : float
        Average daily irradiation (kWh / m² / day), i.e. yearly / n_days.
    """
    yearly = float(np.sum(data.ghi_w_m2) * data.dt_hours / 1000.0)
    n_days = data.duration_hours / 24.0
    daily = yearly / n_days
    return yearly, daily


def arange_inclusive(start: float, stop: float, step: float) -> np.ndarray:
    """Like ``np.arange`` but reliably includes ``stop`` (within float tol)."""
    n = int(round((stop - start) / step))
    return start + step * np.arange(n + 1)


# --------------------------------------------------------------------------- #
# Contour level helper
# --------------------------------------------------------------------------- #
def nice_contour_levels(
    vmin: float, vmax: float, target_count: int = 5
) -> np.ndarray:
    """Pick ~``target_count`` round contour levels spanning ``[vmin, vmax]``.

    The step is ``(vmax - vmin) / target_count`` snapped up to the nearest
    "nice" multiple (1, 2, 2.5, 5 x 10^k), so levels land on human-friendly
    numbers without any value being hard-coded for a particular dataset.
    """
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
        return np.array([])

    raw_step = (vmax - vmin) / target_count
    magnitude = 10.0 ** math.floor(math.log10(raw_step))
    for multiple in (1.0, 2.0, 2.5, 5.0, 10.0):
        if raw_step <= multiple * magnitude:
            step = multiple * magnitude
            break

    first = math.ceil(vmin / step) * step
    return np.arange(first, vmax + 0.5 * step, step)
