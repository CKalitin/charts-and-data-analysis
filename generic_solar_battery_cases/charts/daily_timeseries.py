"""Weekly dispatch time series — 7-day window (±3 days) around special calendar dates.

Sub-hourly dispatch physics converted from UTC to US/Pacific local time
(pandas tz_convert handles PST/PDT automatically — DST in 2024 runs Mar 10 → Nov 3).

Three special periods:
  Summer solstice  Jun 21  PDT (UTC-7)  longest day
  Winter solstice  Dec 21  PST (UTC-8)  shortest day
  Spring equinox   Mar 20  PDT (UTC-7)  equal day/night; DST already active

Four build cases per date (12 files total):
  1 kW solar,  no battery
  2 kW solar,  no battery
  6 kW solar + 12 kWh battery
  25 kW solar + 50 kWh battery

No-battery builds get a 2-panel layout (solar + load); battery builds get 3-panel
(solar + SOC + load).
"""

from __future__ import annotations

import sys
from pathlib import Path

if not __package__:  # running as a script — add project root to path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, timedelta

import matplotlib.dates as mdates
import numpy as np

import config as cfg
import model

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]


_COLOR = {
    "used":         "#4a90d9",
    "curtailed":    "#e8a000",
    "soc":          "#7ed321",
    "from_solar":   "#417505",
    "from_battery": "#2ca25f",
    "unmet":        "#d0021b",
}

# (kw_solar, kwh_battery, filename slug, build description)
_BUILDS = [
    (1.0,   0.0,  "sol1kW_nobat",     "1 kW solar — no battery"),
    (2.0,   0.0,  "sol2kW_nobat",     "2 kW solar — no battery"),
    (6.0,  12.0,  "sol6kW_bat12kWh",  "6 kW solar + 12 kWh battery"),
    (25.0, 50.0,  "sol25kW_bat50kWh", "25 kW solar + 50 kWh battery"),
]

# (month, day, descriptive subtitle, filename slug)
_SPECIAL_WEEKS = [
    (6,  21, "Summer solstice",  "jun21"),
    (12, 21, "Winter solstice",  "dec21"),
    (3,  20, "Spring equinox",   "mar20"),
]

_WEEK_HALF = 3   # days either side of the center date → 7-day window total


def _run_dispatch(data: model.NsrdbData, kw_solar: float, kwh_battery: float):
    """Steady-state full-year dispatch for one build; returns (gen_kw, result)."""
    gen = model.solar_generation_kw(data.ghi_w_m2, kw_solar)
    res, _ = model.steady_state_dispatch(
        gen[:, None], cfg.LOAD_KW, np.array([kwh_battery]),
        data.dt_hours, record=True,
    )
    for f in ("soc_ts", "served_ts", "curtailed_ts", "unmet_ts"):
        setattr(res, f, np.asarray(getattr(res, f)).reshape(data.n_steps))
    return gen, res


def _extract_week(local_ts, gen_kw: np.ndarray, res, center: date, dt: float) -> dict:
    """Slice per-step arrays to the 7-day window centered on ``center``."""
    start = center - timedelta(days=_WEEK_HALF)
    end   = center + timedelta(days=_WEEK_HALF)
    local_dates = local_ts.date
    mask = np.array([(start <= d <= end) for d in local_dates])

    g         = gen_kw[mask]
    soc       = np.asarray(res.soc_ts)[mask]
    served    = np.asarray(res.served_ts)[mask]
    curtailed = np.asarray(res.curtailed_ts)[mask]
    unmet     = np.asarray(res.unmet_ts)[mask]

    curtailed_kw      = curtailed / dt
    served_total_kw   = served / dt
    used_kw           = np.maximum(g - curtailed_kw, 0.0)
    served_solar_kw   = np.minimum(g, cfg.LOAD_KW)
    served_battery_kw = np.maximum(served_total_kw - served_solar_kw, 0.0)

    return {
        "timestamps":        local_ts[mask],
        "gen_kw":            g,
        "used_kw":           used_kw,
        "curtailed_kw":      curtailed_kw,
        "soc_kwh":           soc,
        "served_solar_kw":   served_solar_kw,
        "served_battery_kw": served_battery_kw,
        "unmet_kw":          unmet / dt,
    }


def _setup_xaxis(ax) -> None:
    """Daily major ticks + 6-hourly minor ticks for the shared x-axis (weekly view)."""
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))
    ax.tick_params(axis="x", which="minor", length=3)


def _setup_xaxis_daily(ax) -> None:
    """3-hourly major ticks for a single-day view."""
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    ax.tick_params(axis="x", which="minor", length=3)


def _draw_solar_panel(ax, week: dict, title: str) -> None:
    ts = week["timestamps"]
    ax.fill_between(ts, week["gen_kw"], week["used_kw"],
                    color=_COLOR["curtailed"], alpha=0.85, label="Curtailed")
    ax.fill_between(ts, week["used_kw"],
                    color=_COLOR["used"], alpha=0.75, label="Used")
    ax.set_ylabel("Solar (kW)")
    ax.set_title(title)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.85)


def _draw_soc_panel(ax, week: dict, kwh_bat: float) -> None:
    ts = week["timestamps"]
    ax.fill_between(ts, week["soc_kwh"], color=_COLOR["soc"], alpha=0.75)
    ax.axhline(kwh_bat, color="gray", linewidth=0.9, linestyle="--",
               label=f"Capacity ({kwh_bat:g} kWh)")
    ax.set_ylim(0, kwh_bat * 1.12)
    ax.set_ylabel("Battery SOC (kWh)")
    ax.set_title(f"Battery state of charge ({kwh_bat:g} kWh capacity)")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.85)


def _draw_load_panel(ax, week: dict, has_battery: bool) -> None:
    ts = week["timestamps"]
    s = week["served_solar_kw"]
    b = week["served_battery_kw"]

    ax.fill_between(ts, s,        color=_COLOR["from_solar"],   alpha=0.85, label="Solar")
    if has_battery:
        ax.fill_between(ts, s, s + b, color=_COLOR["from_battery"], alpha=0.75, label="Battery")
    top = s + b if has_battery else s
    ax.fill_between(ts, top, cfg.LOAD_KW, color=_COLOR["unmet"], alpha=0.50, label="Unmet")
    ax.axhline(cfg.LOAD_KW, color="black", linewidth=0.7, linestyle=":", alpha=0.5)
    ax.set_ylim(0, cfg.LOAD_KW * 1.10)
    ax.set_ylabel("Load served (kW)")
    ax.set_title(f"Load energy served ({cfg.LOAD_KW:g} kW constant)")
    ncols = 3 if has_battery else 2
    ax.legend(loc="lower right", fontsize=8, framealpha=0.85, ncol=ncols)


def _draw(fig, week: dict, title: str, kwh_bat: float, params: dict[str, str]) -> None:
    has_battery = kwh_bat > 0.0
    n_panels = 3 if has_battery else 2
    axes = fig.subplots(n_panels, 1, sharex=True)
    if n_panels == 2:
        ax_sol, ax_load = axes
    else:
        ax_sol, ax_soc, ax_load = axes

    _draw_solar_panel(ax_sol, week, title)
    if has_battery:
        _draw_soc_panel(ax_soc, week, kwh_bat)
    _draw_load_panel(ax_load, week, has_battery)

    _setup_xaxis(ax_load)
    common.info(ax_sol, fig, params, mode="on")
    common.watermark(ax_sol, fig)


def _extract_day(local_ts, gen_kw: np.ndarray, res, center: date, dt: float) -> dict:
    """Slice per-step arrays to a single calendar day in local time."""
    local_dates = local_ts.date
    mask = np.array([d == center for d in local_dates])

    g         = gen_kw[mask]
    soc       = np.asarray(res.soc_ts)[mask]
    served    = np.asarray(res.served_ts)[mask]
    curtailed = np.asarray(res.curtailed_ts)[mask]
    unmet     = np.asarray(res.unmet_ts)[mask]

    curtailed_kw      = curtailed / dt
    served_total_kw   = served / dt
    used_kw           = np.maximum(g - curtailed_kw, 0.0)
    served_solar_kw   = np.minimum(g, cfg.LOAD_KW)
    served_battery_kw = np.maximum(served_total_kw - served_solar_kw, 0.0)

    return {
        "timestamps":        local_ts[mask],
        "gen_kw":            g,
        "used_kw":           used_kw,
        "curtailed_kw":      curtailed_kw,
        "soc_kwh":           soc,
        "served_solar_kw":   served_solar_kw,
        "served_battery_kw": served_battery_kw,
        "unmet_kw":          unmet / dt,
    }


def figures(data: model.NsrdbData, grid: model.ServedGrid):
    from viz import render

    # UTC → US/Pacific: pandas handles PST (UTC-8) / PDT (UTC-7) automatically.
    local_ts = data.timestamps.tz_localize("UTC").tz_convert("America/Los_Angeles")
    year = int(data.timestamps[0].year)

    result = []

    for kw_sol, kwh_bat, build_slug, build_label in _BUILDS:
        gen, res = _run_dispatch(data, kw_sol, kwh_bat)
        has_battery = kwh_bat > 0.0

        for month, day_num, subtitle, date_slug in _SPECIAL_WEEKS:
            center = date(year, month, day_num)
            week = _extract_week(local_ts, gen, res, center, data.dt_hours)

            c = center
            date_label = f"{c.strftime('%B')} {c.day}, {c.year}  (±{_WEEK_HALF} days)"
            title = f"{date_label}  —  {subtitle}\n{build_label}"

            params = {
                "Site":  common.site_label(),
                "Build": build_label,
                "Load":  f"{cfg.LOAD_KW:g} kW constant",
                "TZ":    "US/Pacific (PST/PDT)",
            }
            out_path = cfg.OUT_WEEKLY_TIMESERIES / f"weekly_{date_slug}_{build_slug}.png"
            figsize  = (13, 9) if has_battery else (13, 6)

            def make_fig(week=week, title=title, kwh_bat=kwh_bat,
                         params=params, out_path=out_path, figsize=figsize):
                fig = render.Figure(figsize=figsize, dpi=render.DPI)
                render.FigureCanvasAgg(fig)
                _draw(fig, week, title, kwh_bat, params)
                return fig, out_path

            result.append((f"weekly_timeseries/{date_slug}/{build_slug}", make_fig))

    return result


if __name__ == "__main__":
    import time

    import config as cfg
    import derived
    import model
    from viz import render

    t0 = time.time()
    grid = derived.load_served_grid()
    data = model.load_nsrdb(cfg.DATA_FILE, resample=None)
    plan = [*figures(data, grid), *figures_daily(data, grid)]
    for name, build in plan:
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"\nwrote {len(plan)} charts in {time.time() - t0:.1f}s")


def figures_daily(data: model.NsrdbData, grid: model.ServedGrid):
    """Single-day zoom for each build × special date (12 files, hourly x-axis)."""
    from viz import render

    local_ts = data.timestamps.tz_localize("UTC").tz_convert("America/Los_Angeles")
    year = int(data.timestamps[0].year)

    result = []

    for kw_sol, kwh_bat, build_slug, build_label in _BUILDS:
        gen, res = _run_dispatch(data, kw_sol, kwh_bat)
        has_battery = kwh_bat > 0.0

        for month, day_num, subtitle, date_slug in _SPECIAL_WEEKS:
            center = date(year, month, day_num)
            day = _extract_day(local_ts, gen, res, center, data.dt_hours)

            c = center
            date_label = f"{c.strftime('%B')} {c.day}, {c.year}"
            title = f"{date_label}  —  {subtitle}\n{build_label}"

            params = {
                "Site":  common.site_label(),
                "Build": build_label,
                "Load":  f"{cfg.LOAD_KW:g} kW constant",
                "TZ":    "US/Pacific (PST/PDT)",
            }
            out_path = cfg.OUT_DAILY_TIMESERIES / f"daily_{date_slug}_{build_slug}.png"
            figsize  = (11, 9) if has_battery else (11, 6)

            def make_fig(day=day, title=title, kwh_bat=kwh_bat,
                         params=params, out_path=out_path, figsize=figsize):
                fig = render.Figure(figsize=figsize, dpi=render.DPI)
                render.FigureCanvasAgg(fig)
                # Draw using shared panel helpers but with hourly x-axis
                has_bat = kwh_bat > 0.0
                n_panels = 3 if has_bat else 2
                axes = fig.subplots(n_panels, 1, sharex=True)
                if n_panels == 2:
                    ax_sol, ax_load = axes
                else:
                    ax_sol, ax_soc, ax_load = axes

                _draw_solar_panel(ax_sol, day, title)
                if has_bat:
                    _draw_soc_panel(ax_soc, day, kwh_bat)
                _draw_load_panel(ax_load, day, has_bat)

                _setup_xaxis_daily(ax_load)
                common.info(ax_sol, fig, params, mode="on")
                common.watermark(ax_sol, fig)
                return fig, out_path

            result.append((f"daily_timeseries/{date_slug}/{build_slug}", make_fig))

    return result
