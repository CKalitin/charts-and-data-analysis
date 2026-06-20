"""Heatmap charts for the dam + battery model sweep.

Four charts per dam:
  1. Served Load Fraction (SLF)   — fixed 0-100%, 5 evenly-spaced contours
  2. System Cost (total capex, $M)
  3. LCOE ($/MWh of served energy) — logarithmic colour scale, 5 log-spaced contours
  4. Total Spill (GWh/year)        — 5 evenly-spaced contours

X axis: battery capacity (MWh)  0 → nameplate × MWH_PER_MW
Y axis: installed turbine capacity (MW)  0 → nameplate
Colormap: inferno throughout.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import matplotlib.ticker as mticker
import numpy as np
from matplotlib.colors import LogNorm

import config as cfg
from charts import common
from model import config as mc
from viz import render


CMAP = "inferno"
N_CONTOURS = 5   # number of contour lines per chart


_SLF_CONTOUR_LEVELS = [50, 80, 90, 99, 99.9, 99.99]


def _draw_heatmap(
    ax, fig, Z, mw_vals, mwh_vals,
    title: str, cbar_label: str,
    fmt=None,
    source=cfg.SOURCE_USACE,
    vmin=None, vmax=None,
    log_scale: bool = False,
    add_contours: bool = False,
    slf_contours: bool = False,
    contour_color: str = "white",
    text_color: str = "0.15",
) -> None:
    """Draw one heatmap panel.

    log_scale=True uses LogNorm and log-spaced contour levels.
    add_contours=True draws N_CONTOURS white contour lines.
    vmin/vmax fix the colorbar range (linear only).
    """
    # ── Pcolormesh ────────────────────────────────────────────────────────────
    if log_scale:
        valid = Z[np.isfinite(Z) & (Z > 0)]
        norm  = LogNorm(vmin=valid.min() if len(valid) else 1,
                        vmax=valid.max() if len(valid) else 1e4)
        pcm = ax.pcolormesh(mwh_vals, mw_vals, Z, cmap=CMAP,
                            norm=norm, shading="nearest")
    else:
        pcm = ax.pcolormesh(mwh_vals, mw_vals, Z, cmap=CMAP,
                            vmin=vmin, vmax=vmax, shading="nearest")

    # Explicit axis limits — prevents matplotlib from defaulting to 0-1
    ax.set_xlim(mwh_vals[0], mwh_vals[-1])
    ax.set_ylim(mw_vals[0],  mw_vals[-1])

    # ── Colorbar ──────────────────────────────────────────────────────────────
    cb = fig.colorbar(pcm, ax=ax, pad=0.02)
    cb.set_label(cbar_label, fontsize=9)
    if fmt and not log_scale:
        cb.ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
    elif log_scale:
        cb.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: f"${v:,.0f}")
        )

    # ── Axis labels & tick formatters ─────────────────────────────────────────
    ax.set_xlabel("Battery capacity (MWh)", fontsize=9)
    ax.set_ylabel("Installed turbine capacity (MW)", fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

    # ── Contour lines ─────────────────────────────────────────────────────────
    if add_contours or slf_contours:
        X, Y = np.meshgrid(mwh_vals, mw_vals)
        if slf_contours:
            levels = _SLF_CONTOUR_LEVELS
            cs = ax.contour(X, Y, Z, levels=levels,
                            colors=contour_color, linewidths=0.7, alpha=0.65)
            ax.clabel(cs, fmt=lambda v: f"{v:g}%", fontsize=6.5, inline=True)
        elif log_scale:
            valid = Z[np.isfinite(Z) & (Z > 0)]
            if len(valid) >= 2:
                levels = np.logspace(
                    np.log10(valid.min()), np.log10(valid.max()),
                    N_CONTOURS + 2
                )[1:-1]   # N_CONTOURS interior levels, log-spaced
                cs = ax.contour(X, Y, Z, levels=levels,
                                colors=contour_color, linewidths=0.7, alpha=0.65)
                ax.clabel(cs, fmt=lambda v: f"${v:,.0f}", fontsize=6.5, inline=True)
        else:
            z_lo = vmin if vmin is not None else float(np.nanmin(Z))
            z_hi = vmax if vmax is not None else float(np.nanmax(Z))
            levels = np.linspace(z_lo, z_hi, N_CONTOURS + 2)[1:-1]
            cs = ax.contour(X, Y, Z, levels=levels,
                            colors=contour_color, linewidths=0.7, alpha=0.65)
            ax.clabel(cs, fmt=lambda v: f"{v:.1f}", fontsize=6.5, inline=True)

    common.add_source(ax, source, color=text_color)
    common.add_watermark(ax, color=text_color)


def _add_operating_point(ax, results: dict, target_mw: float, target_mwh: float) -> None:
    """Mark a (MW, MWh) operating point with a star and annotated values."""
    mw_vals  = results["mw_vals"]
    mwh_vals = results["mwh_vals"]

    i_mw  = int(np.argmin(np.abs(mw_vals  - target_mw)))
    i_mwh = int(np.argmin(np.abs(mwh_vals - target_mwh)))

    actual_mw  = mw_vals[i_mw]
    actual_mwh = mwh_vals[i_mwh]

    slf_pct   = results["slf"][i_mw, i_mwh] * 100
    cost_m    = results["system_cost"][i_mw, i_mwh] / 1e6
    lcoe_val  = results["lcoe"][i_mw, i_mwh]
    spill_pct = results["total_spill"][i_mw, i_mwh] / results["total_load_mwh"] * 100

    label = (f"SLF: {slf_pct:.1f}%\n"
             f"Cost: ${cost_m:,.0f}M\n"
             f"LCOE: ${lcoe_val:.1f}/MWh\n"
             f"Spill: {spill_pct:.1f}%")

    ax.plot(actual_mwh, actual_mw, "*", color="white", markersize=12, zorder=10,
            markeredgecolor="0.3", markeredgewidth=0.5)
    ax.annotate(
        label,
        xy=(actual_mwh, actual_mw),
        xytext=(8, -72), textcoords="offset points",
        fontsize=7, color="0.1",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.88,
                  edgecolor="0.5", linewidth=0.5),
        arrowprops=dict(arrowstyle="-", color="white", lw=0.8),
    )


def figures_heatmaps(results: dict, dam, operating_points: list | None = None) -> list:
    """Return plan entries for all four heatmaps for one dam."""
    mw_vals  = results["mw_vals"]
    mwh_vals = results["mwh_vals"]
    out_dir  = cfg.OUTPUT_DIR / "model" / dam.slug

    def _box(lines):
        return [
            f"Nameplate: {dam.nameplate_mw:,} MW",
            f"Battery eff: {mc.BATTERY_EFFICIENCY*100:.0f}%",
            f"Dam: $3M/MW, 50 yr",
            f"Battery: $200k/MWh, 20 yr",
        ] + lines

    plans = []

    op = operating_points or []  # list of (target_mw, target_mwh)

    # 1. Served Load Fraction — fixed 0-100%, contours
    def build_slf(r=results, dam=dam, out=out_dir, op=op):
        fig, ax = render.new_figure(figsize=(10, 7))
        _draw_heatmap(ax, fig, r["slf"] * 100, mw_vals, mwh_vals,
                      f"{dam.name} — Served Load Fraction (%)",
                      "Served load fraction (%)",
                      fmt=lambda v, _: f"{v:.0f}%",
                      vmin=0, vmax=100,
                      slf_contours=True,
                      contour_color="black",
                      text_color="white")
        for pt in op:
            _add_operating_point(ax, r, *pt)
        common.add_box(ax, fig, _box(["Higher = more load served"]))
        return fig, out / f"{dam.slug}_model_slf.png"
    plans.append((f"model_slf_{dam.code}", build_slf))

    # 2. System Cost — no contours
    def build_cost(r=results, dam=dam, out=out_dir, op=op):
        fig, ax = render.new_figure(figsize=(10, 7))
        Z_m = r["system_cost"] / 1e6
        _draw_heatmap(ax, fig, Z_m, mw_vals, mwh_vals,
                      f"{dam.name} — System Cost ($M capex)",
                      "Total capex ($M)",
                      fmt=lambda v, _: f"${v:,.0f}M",
                      add_contours=True,
                      text_color="white")
        for pt in op:
            _add_operating_point(ax, r, *pt)
        common.add_box(ax, fig, _box(["Total capital cost"]))
        return fig, out / f"{dam.slug}_model_cost.png"
    plans.append((f"model_cost_{dam.code}", build_cost))

    # 3. LCOE — log scale, contours
    def build_lcoe(r=results, dam=dam, out=out_dir, op=op):
        fig, ax = render.new_figure(figsize=(10, 7))
        _draw_heatmap(ax, fig, r["lcoe"], mw_vals, mwh_vals,
                      f"{dam.name} — LCOE ($/MWh served)",
                      "LCOE ($/MWh)",
                      log_scale=True,
                      add_contours=True)
        for pt in op:
            _add_operating_point(ax, r, *pt)
        common.add_box(ax, fig, _box(["Annualised cost ÷ served energy"]))
        return fig, out / f"{dam.slug}_model_lcoe.png"
    plans.append((f"model_lcoe_{dam.code}", build_lcoe))

    # 4. Total Spill — contours
    def build_spill(r=results, dam=dam, out=out_dir, op=op):
        fig, ax = render.new_figure(figsize=(10, 7))
        Z_gwh = r["total_spill"] / 1e3
        _draw_heatmap(ax, fig, Z_gwh, mw_vals, mwh_vals,
                      f"{dam.name} — Total Spill (GWh/year)",
                      "Spill (GWh/year)",
                      fmt=lambda v, _: f"{v:,.0f} GWh",
                      add_contours=True)
        for pt in op:
            _add_operating_point(ax, r, *pt)
        common.add_box(ax, fig, _box(["Capacity spill + battery overflow"]))
        return fig, out / f"{dam.slug}_model_spill.png"
    plans.append((f"model_spill_{dam.code}", build_spill))

    return plans
