"""Annual dispatch time series for one build — a sanity view of the physics.

Native-resolution dispatch (run to the steady-state SOC fixed point, same as the
sweep) aggregated to daily values for a clean year-at-a-glance:

  1. GHI                     (kWh/m²/day)
  2. Solar production        (kWh/day, curtailed vs used)
  3. Battery state of charge (daily-mean kWh)
  4. Load energy served      (kWh/day, unmet shaded)
"""

from __future__ import annotations

import matplotlib.dates as mdates
import numpy as np
import pandas as pd

import config as cfg
import model

from . import common

_COLOR = {
    "ghi": "#f5a623", "used": "#4a90d9", "curtailed": "#e8a000",
    "soc": "#7ed321", "served": "#417505", "unmet": "#d0021b",
}


def _daily(data: model.NsrdbData, res: model.DispatchResult) -> pd.DataFrame:
    dt = data.dt_hours
    df = pd.DataFrame(
        {
            "ghi_kwh_m2": data.ghi_w_m2 * dt / 1000.0,
            "gen_kwh": model.solar_generation_kw(data.ghi_w_m2, cfg.TS_KW_SOLAR) * dt,
            "curtailed_kwh": res.curtailed_ts,
            "served_kwh": res.served_ts,
            "unmet_kwh": res.unmet_ts,
            "load_kwh": np.full(data.n_steps, cfg.LOAD_KW * dt),
            "soc_kwh": res.soc_ts,
        },
        index=data.timestamps,
    )
    agg = {c: ("mean" if c == "soc_kwh" else "sum") for c in df.columns}
    daily = df.resample("D").agg(agg)
    return daily[df["ghi_kwh_m2"].resample("D").count() > 0]


def _date_axis(ax) -> None:
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.grid(axis="y", linestyle="--", alpha=0.3)


def figures(data: model.NsrdbData, grid: model.ServedGrid):
    from viz import render

    gen = model.solar_generation_kw(data.ghi_w_m2, cfg.TS_KW_SOLAR)
    res, _ = model.steady_state_dispatch(
        gen[:, None], cfg.LOAD_KW, np.array([cfg.TS_KWH_BATTERY]),
        data.dt_hours, record=True,
    )
    # record path used a length-1 config axis; squeeze it back to time series.
    for f in ("soc_ts", "served_ts", "curtailed_ts", "unmet_ts"):
        setattr(res, f, np.asarray(getattr(res, f)).reshape(data.n_steps))
    util = float(res.served_kwh.reshape(-1)[0] / res.demand_kwh)
    daily = _daily(data, res)

    params = {
        "Site": common.site_label(),
        "Capacity factor": f"{grid.capacity_factor:.0%}",
        "Build": f"{cfg.TS_KW_SOLAR:g} kW solar + {cfg.TS_KWH_BATTERY:g} kWh battery",
        "Load": f"{cfg.LOAD_KW:g} kW constant",
        "Utilization": f"{util:.1%}",
    }
    suffix = common.param_suffix({"sol": f"{cfg.TS_KW_SOLAR:g}kW",
                                  "bat": f"{cfg.TS_KWH_BATTERY:g}kWh"})

    def combined():
        fig = render.Figure(figsize=(13, 11), dpi=render.DPI)
        render.FigureCanvasAgg(fig)
        axes = fig.subplots(4, 1, sharex=True)
        ax_ghi, ax_sol, ax_soc, ax_load = axes

        ax_ghi.fill_between(daily.index, daily["ghi_kwh_m2"], color=_COLOR["ghi"], alpha=0.75)
        ax_ghi.set_ylabel("GHI\n(kWh/m²/day)")
        ax_ghi.set_title("Global horizontal irradiance")

        used = daily["gen_kwh"] - daily["curtailed_kwh"]
        ax_sol.fill_between(daily.index, daily["gen_kwh"], used, color=_COLOR["curtailed"],
                            alpha=0.85, label="Curtailed (battery full)")
        ax_sol.fill_between(daily.index, used, color=_COLOR["used"], alpha=0.75,
                            label="Used (load + charge)")
        ax_sol.legend(loc="upper right", fontsize=8)
        ax_sol.set_ylabel("Production\n(kWh/day)")
        ax_sol.set_title(f"Solar production ({cfg.TS_KW_SOLAR:g} kW)")

        ax_soc.fill_between(daily.index, daily["soc_kwh"], color=_COLOR["soc"], alpha=0.75)
        ax_soc.axhline(cfg.TS_KWH_BATTERY, color="gray", linewidth=0.8, linestyle="--",
                       label=f"Capacity ({cfg.TS_KWH_BATTERY:g} kWh)")
        ax_soc.set_ylabel("SOC\n(kWh)")
        ax_soc.set_title("Battery state of charge (daily mean)")
        ax_soc.legend(loc="upper right", fontsize=8)

        ax_load.fill_between(daily.index, daily["load_kwh"], color=_COLOR["unmet"],
                             alpha=0.4, label="Unmet")
        ax_load.fill_between(daily.index, daily["served_kwh"], color=_COLOR["served"],
                             alpha=0.85, label="Served")
        ax_load.set_ylabel("Load\n(kWh/day)")
        ax_load.set_title(f"Load energy served ({cfg.LOAD_KW:g} kW constant)")
        ax_load.legend(loc="lower right", fontsize=8)

        for ax in axes:
            _date_axis(ax)
        common.info(ax_ghi, fig, params, mode="on")
        common.watermark(ax_ghi, fig)
        return fig, cfg.OUT_TIMESERIES / f"dispatch_{suffix}.png"

    return [("timeseries", combined)]
