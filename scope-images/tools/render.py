"""Matplotlib renders of the extracted scope traces (light theme, one set of images per photo)."""
from __future__ import annotations

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import scope_extract as se

# scope hues, darkened so they read on white
COLORS = {"CH1": "#c79a00", "CH2": "#0b9bbd", "CH3": "#7b3fe4", "CH4": "#1f9d3a"}
FG, GRID, BG = "#1f2430", "#cfd4de", "#ffffff"


def _style():
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "axes.edgecolor": "#9aa1b0", "axes.labelcolor": FG, "text.color": FG,
        "xtick.color": FG, "ytick.color": FG, "grid.color": GRID, "grid.linestyle": ":",
        "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    })


def _label(m, ch):
    return f"{ch[-1]}: {se.signal_name(m, ch)}  ({m['vdiv'][ch]:g} V/div)"


def _plot_trace(ax, x, y, inferred, color, lw=1.4):
    """Solid where measured, dashed where inferred (hidden behind another trace)."""
    ax.plot(x, np.where(inferred, np.nan, y), color=color, lw=lw, drawstyle="steps-mid")
    seg = inferred.copy()
    seg[1:] |= inferred[:-1]
    seg[:-1] |= inferred[1:]
    ax.plot(x, np.where(seg, y, np.nan), color=color, lw=lw * 0.8, ls=(0, (3, 2)), alpha=.8, drawstyle="steps-mid")


def volts(nm, r, m, path):
    _style()
    chs = se.shown(m)
    fig, axs = plt.subplots(len(chs), 1, figsize=(9, 2.4 * len(chs) + 0.3 if len(chs) > 1 else 4), sharex=True, squeeze=False)
    axs = axs[:, 0]
    t = r["t"] * 1e3
    for ax, ch in zip(axs, chs):
        d = r["ch"][ch]
        ax.fill_between(t, d["vmin"], d["vmax"], step="mid", color=COLORS[ch], alpha=.22, lw=0)
        _plot_trace(ax, t, d["v"], d["filled"], COLORS[ch])
        ax.axvline(0, color=FG, lw=.6, alpha=.4)
        ax.grid(True)
        ax.set_xlim(t[0], t[-1])
        ax.set_ylabel("V")
        ax.set_title(_label(m, ch), loc="left", color=COLORS[ch], fontsize=11)
    axs[-1].set_xlabel("time relative to trigger (ms)")
    fig.suptitle(f"{nm}  -  {m['tb'] * 1e3:g} ms/div, {m['stamp']}   (dashed = hidden behind another trace, inferred)",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def overlay(nm, r, m, path):
    """All four channels on one chart, in volts. A channel whose full scale is >20x smaller than the
    largest one (image 9 SUPP_UVR, 200 mV/div) goes on a right-hand axis so it stays readable."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 6))
    t = r["t"] * 1e3
    peak = {ch: np.nanmax(np.abs(r["ch"][ch]["v"])) for ch in se.shown(m)}
    ax2 = None
    handles = []
    for ch in se.shown(m):
        d = r["ch"][ch]
        small = m["vdiv"][ch] * 20 < max(m["vdiv"].values())
        a = ax
        if small:
            ax2 = ax2 or ax.twinx()
            a = ax2
        a.fill_between(t, d["vmin"], d["vmax"], step="mid", color=COLORS[ch], alpha=.18, lw=0)
        _plot_trace(a, t, d["v"], d["filled"], COLORS[ch], lw=1.6)
        lab = f"{ch[-1]}: {se.signal_name(m, ch)}" + ("  (right axis)" if small else "")
        handles.append(plt.Line2D([], [], color=COLORS[ch], lw=2, label=lab))
    ax.axvline(0, color=FG, lw=.7, alpha=.4)
    ax.grid(True)
    ax.set_xlim(t[0], t[-1])
    ax.set_xlabel("time relative to trigger (ms)")
    ax.set_ylabel("V")
    if ax2:
        ax2.set_ylabel("V  (" + se.signal_name(m, "CH4") + ")", color=COLORS["CH4"])
        ax2.tick_params(axis="y", colors=COLORS["CH4"])
        lo, hi = ax.get_ylim()
        k = np.nanmax(r["ch"]["CH4"]["vmax"]) * 1.05 / max(peak.values())     # right-axis units per left-axis unit
        ax2.set_ylim(lo * k, hi * k)                                          # keeps both zeros level
    ax.set_title(f"{nm}  -  {m['tb'] * 1e3:g} ms/div, {m['stamp']}   (dashed = hidden behind another trace, inferred)", loc="left")
    ax.legend(handles=handles, loc="upper left", frameon=True, facecolor="white", edgecolor=GRID, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def screen(nm, r, m, path):
    """Redraw the screen: 10x8 graticule, traces in screen divisions (zero at -3 div)."""
    _style()
    fig, ax = plt.subplots(figsize=(9, 7.4))
    for ch in se.shown(m):
        d = r["ch"][ch]
        _plot_trace(ax, r["u"], d["v"] / m["vdiv"][ch] - 3, d["filled"], COLORS[ch], lw=1.4)
        ax.plot([], [], color=COLORS[ch], label=_label(m, ch))
    ax.set_xlim(0, 10)
    ax.set_ylim(-4, 4)
    ax.set_xticks(np.arange(11))
    ax.set_yticks(np.arange(-4, 5))
    ax.set_xticklabels([f"{(x - 5) * m['tb'] * 1e3 + m['mpos'] * 1e3:g}" for x in range(11)])
    ax.set_yticklabels([])
    ax.grid(True)
    ax.set_aspect(1.0)
    ax.axvline(5 - m["mpos"] / m["tb"], color=FG, lw=.8, alpha=.5)
    ax.set_xlabel("ms from trigger")
    ax.set_title(f"{nm}  -  {m['tb'] * 1e3:g} ms/div, trigger {m['trig_ch']} rising {m['trig_level']:g} V", loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.09), frameon=False, ncol=2, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def qa_overlay(nm, r, m, path):
    """Rectified photo with extracted samples drawn on top (check of the extraction itself)."""
    _style()
    fig, ax = plt.subplots(figsize=(9.5, 7.8))
    ax.imshow(cv2.cvtColor(r["rect"], cv2.COLOR_BGR2RGB), extent=(-1, 11, 9, -1))
    for ch in se.shown(m):
        d = r["ch"][ch]
        row = d["raw_rows"]
        ok = ~np.isnan(row)
        ax.plot(r["u"][ok], row[ok] * se.LCD, ".", ms=3, color="white", mec="#111", mew=.4)
        f = d["filled"]
        ax.plot(r["u"][f], se.ZERO_V - d["v"][f] / m["vdiv"][ch], "x", ms=3, color="#ff5a00")
    ax.set_xlim(0, 10)
    ax.set_ylim(8, 0)
    ax.set_title(f"{nm}: rectified photo + extracted samples (white dots; orange x = inferred)", loc="left")
    ax.set_xlabel("u (div)")
    ax.set_ylabel("v (div)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def make_all(results, meta):
    for nm, r in results.items():
        m = meta[nm]
        overlay(nm, r, m, se.OUT / f"{nm}_traces_overlay.png")
        volts(nm, r, m, se.OUT / f"{nm}_traces_volts.png")
        screen(nm, r, m, se.OUT / f"{nm}_traces_screen.png")
        qa_overlay(nm, r, m, se.OUT / f"{nm}_qa_overlay.png")
    print("wrote renders to", se.OUT)
