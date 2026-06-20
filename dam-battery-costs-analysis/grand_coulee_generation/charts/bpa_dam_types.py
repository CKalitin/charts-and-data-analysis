"""BPA federal dam classification: storage vs run-of-river.

Chart products:
  figures_all_dams()          — bar chart sorted by MW, coloured by type
  figures_totals_mw()         — two-bar: total MW storage vs RoR
  figures_reservoir_af()      — bar chart sorted by reservoir AF
  figures_totals_af()         — two-bar: total AF storage vs RoR
  figures_energy_storage_gwh()— bar chart sorted by energy storage (GWh)

Reservoir storage data sourced from individual Wikipedia articles.
Classification: "ror" if Wikipedia explicitly labels run-of-river;
"storage" if the dam holds a substantial reservoir used for seasonal dispatch.

Energy storage formula:
  E_GWh = active_AF * mean_head_ft * 9.23e-7    (eta = 0.90)
  Derivation: 1 AF*ft = 0.9226 kWh at eta=0.90

  active_AF  — usable storage (total minus dead pool below intake)
               sourced from USACE/BoR coordinated operations agreements
  mean_head  — GCL, BON: 2023 USACE NWD hourly mean (scraped)
               all others: design head or published operational average

Run:  python charts/bpa_dam_types.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import matplotlib.ticker as mticker
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Patch

import config as cfg
import derived
from charts import common
from viz import render

STORAGE_COLOR = "#d62728"
ROR_COLOR     = "#1f77b4"
GEN_COLOR     = "#1f77b4"
SPILL_COLOR   = "#ff7f0e"
ENERGY_K      = 9.23e-7        # GWh per (AF * ft)  at eta=0.90
_KCFS_TO_MAF_YR = 1983 * 365 / 1e6  # ≈ 0.7238 MAF/year per kcfs

# fmt: off
# Fields: name, cap_mw, reservoir_af, dam_type, source_url, active_af, mean_head_ft
#
# active_af  = usable storage (excludes dead pool)
#   Sources: USACE Columbia River Coordinated Operations Agreement (GCL, CHJ, JDA, TDA, BON, MCN,
#            Snake River dams, Libby, Dworshak, Hungry Horse, Albeni Falls);
#            BoR Snake River Basin Operational Studies (Palisades, Anderson Ranch, Minidoka);
#            USACE Willamette Valley Dam Regulation Manuals (Lookout Point, Detroit, Green Peter,
#            Lost Creek, Hills Creek, Cougar, Foster, Big Cliff, Dexter);
#            estimates (~70% of total) for Green Springs and small diversion dams.
#
# mean_head_ft = hydraulic head at turbine
#   GCL: 2023 USACE NWD hourly mean (forebay 1274 ft, tailwater 959 ft) — pool ran ~16 ft below
#        full (1290 ft max); mean-head-at-full-drawdown would be ~290 ft.
#   BON: 2023 USACE NWD hourly mean.
#   All others: design head or published USACE/BoR operational average.
_DAMS = [
    # name                    cap_mw  reservoir_af  type      wiki_url                                               active_af  mean_head_ft
    ("Grand Coulee",           7049,   9_562_000, "storage", "https://en.wikipedia.org/wiki/Grand_Coulee_Dam",       5_185_200,  315),
    ("Chief Joseph",           2614,     516_000, "ror",     "https://en.wikipedia.org/wiki/Chief_Joseph_Dam",          35_000,  175),
    ("John Day",               2484,   2_530_000, "ror",     "https://en.wikipedia.org/wiki/John_Day_Dam",             400_000,  100),
    ("The Dalles",             2048,     330_000, "ror",     "https://en.wikipedia.org/wiki/The_Dalles_Dam",            200_000,   88),
    ("Bonneville",             1216,     537_000, "ror",     "https://en.wikipedia.org/wiki/Bonneville_Dam",             37_000,   61),
    ("McNary",                 1127,   1_350_000, "ror",     "https://en.wikipedia.org/wiki/McNary_Dam",                750_000,   72),
    ("Little Goose",            930,     516_300, "ror",     "https://en.wikipedia.org/wiki/Little_Goose_Dam",          100_000,   97),
    ("Lower Granite",           930,     440_200, "ror",     "https://en.wikipedia.org/wiki/Lower_Granite_Dam",         100_000,   97),
    ("Lower Monumental",        930,     432_000, "ror",     "https://en.wikipedia.org/wiki/Lower_Monumental_Dam",      100_000,   97),
    ("Ice Harbor",              695,     249_000, "ror",     "https://en.wikipedia.org/wiki/Ice_Harbor_Dam",            100_000,   97),
    ("Libby",                   605,   6_027_000, "storage", "https://en.wikipedia.org/wiki/Libby_Dam",              5_013_400,  255),
    ("Dworshak",                460,   3_468_000, "storage", "https://en.wikipedia.org/wiki/Dworshak_Dam",           2_018_200,  640),
    ("Hungry Horse",            428,   3_467_179, "storage", "https://en.wikipedia.org/wiki/Hungry_Horse_Dam",       2_068_600,  430),
    ("Palisades",               176,   1_200_000, "storage", "https://en.wikipedia.org/wiki/Palisades_Dam",            720_000,  215),
    ("Lookout Point",           138,     477_700, "storage", "https://en.wikipedia.org/wiki/Lookout_Point_Dam",        300_000,  305),
    ("Detroit",                 126,     455_000, "storage", "https://en.wikipedia.org/wiki/Detroit_Dam",              230_000,  375),
    ("Green Peter",              92,     312_500, "storage", "https://en.wikipedia.org/wiki/Green_Peter_Dam",          220_000,  300),
    ("Lost Creek",               56,     315_000, "storage", "https://en.wikipedia.org/wiki/Lost_Creek_Lake",          210_000,  325),
    ("Albeni Falls",             49,   1_155_000, "storage", "https://en.wikipedia.org/wiki/Albeni_Falls_Dam",          64_000,   38),
    ("Anderson Ranch",           40,     503_500, "storage", "https://en.wikipedia.org/wiki/Anderson_Ranch_Dam",       480_000,  390),
    ("Hills Creek",              34,     355_500, "storage", "https://en.wikipedia.org/wiki/Hills_Creek_Dam",          140_000,  305),
    ("Minidoka",                 28,     210_200, "storage", "https://en.wikipedia.org/wiki/Minidoka_Dam",             140_000,   65),
    ("Cougar",                   28,     219_000, "storage", "https://en.wikipedia.org/wiki/Cougar_Dam",               130_000,  355),
    ("Foster",                   23,      28_300, "ror",     "https://en.wikipedia.org/wiki/Foster_Dam",                25_000,  195),  # 6.4 d
    ("Big Cliff",                23,       6_450, "ror",     "https://en.wikipedia.org/wiki/Big_Cliff_Dam",              3_600,  335),  # 1.5 d
    ("Dexter",                   17,      29_900, "ror",     "https://en.wikipedia.org/wiki/Dexter_Dam",                20_000,   75),  # 6.0 d
    ("Green Springs",            17,     200_000, "storage", "https://en.wikipedia.org/wiki/Green_Springs_Powerplant", 150_000,  225),
    ("Chandler",                 12,       5_000, "ror",     "https://en.wikipedia.org/wiki/Chandler_Dam",               3_000,   60),
    ("Roza",                     13,       1_000, "ror",     "https://en.wikipedia.org/wiki/Roza_Dam",                     500,   50),
    ("Black Canyon Diversion",   10,      31_200, "ror",     "https://en.wikipedia.org/wiki/Black_Canyon_Diversion_Dam",20_000,   65),
    ("Boise River Diversion",     3,       1_200, "ror",     "https://en.wikipedia.org/wiki/Boise_River_Diversion_Dam",    600,   40),
]
# fmt: on

_COLS = ["name", "capacity_mw", "reservoir_af", "dam_type", "source_url", "active_af", "mean_head_ft"]

# Classification note — our definition, not Wikipedia's:
# dam_type = "ror"     if reservoir / avg_annual_flow < 10 days
# dam_type = "storage" if reservoir / avg_annual_flow >= 10 days
# Big Cliff, Dexter, Foster: Wikipedia says "storage" but they are re-regulating pondages
# with < 10 days of reservoir-to-flow ratio — reclassified as "ror" here.


def _load(sort_by: str = "capacity_mw") -> pd.DataFrame:
    df = pd.DataFrame(_DAMS, columns=_COLS)
    df["energy_gwh"] = df["active_af"] * df["mean_head_ft"] * ENERGY_K
    return df.sort_values(sort_by, ascending=False).reset_index(drop=True)


def _bar_chart(df, y_col, ylabel, title, path, source_text="Source: USACE / Bureau of Reclamation; Wikipedia"):
    fig = Figure(figsize=(14, 6), dpi=render.DPI)
    FigureCanvasAgg(fig)
    fig.set_constrained_layout(True)
    ax = fig.add_subplot(1, 1, 1)

    colors = [STORAGE_COLOR if t == "storage" else ROR_COLOR for t in df["dam_type"]]
    ax.bar(np.arange(len(df)), df[y_col], color=colors, width=0.75, alpha=0.88)
    ax.set_xticks(np.arange(len(df)))
    ax.set_xticklabels(df["name"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.legend(handles=[
        Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
        Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
    ], loc="upper right", fontsize=9)
    common.add_source(ax, source_text)
    common.add_watermark(ax)
    return fig, path


def _totals_chart(df, y_col, ylabel, title, path):
    totals = df.groupby("dam_type")[y_col].sum()
    counts = df.groupby("dam_type").size()
    values = [totals.get("storage", 0), totals.get("ror", 0)]
    labels = [
        f"Storage\n({counts.get('storage', 0)} dams)",
        f"Run-of-River\n({counts.get('ror', 0)} dams)",
    ]

    fig = Figure(figsize=(6, 5), dpi=render.DPI)
    FigureCanvasAgg(fig)
    fig.set_constrained_layout(True)
    ax = fig.add_subplot(1, 1, 1)

    bars = ax.bar(np.arange(2), values, color=[STORAGE_COLOR, ROR_COLOR],
                  width=0.5, alpha=0.88)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v * 1.01,
                f"{v:,.0f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xticks([0, 1])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_ylim(0, max(values) * 1.18)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    common.add_source(ax, "Source: USACE / Bureau of Reclamation; Wikipedia")
    common.add_watermark(ax)
    return fig, path


def figures_all_dams():
    def build():
        return _bar_chart(
            _load("capacity_mw"),
            "capacity_mw", "Nameplate capacity (MW)",
            "BPA federal dams — nameplate capacity by type",
            cfg.BPA_OUTPUT_DIR / "bpa_dams_by_capacity.png",
        )
    return [("bpa_dams_by_capacity", build)]


def figures_totals_mw():
    def build():
        return _totals_chart(
            _load(),
            "capacity_mw", "Total nameplate capacity (MW)",
            "BPA federal dams — total capacity by type",
            cfg.BPA_OUTPUT_DIR / "bpa_dams_totals_mw.png",
        )
    return [("bpa_dams_totals_mw", build)]


def figures_reservoir_af():
    def build():
        return _bar_chart(
            _load("reservoir_af"),
            "reservoir_af", "Reservoir capacity (acre-feet)",
            "BPA federal dams — reservoir storage by type",
            cfg.BPA_OUTPUT_DIR / "bpa_dams_by_reservoir_af.png",
        )
    return [("bpa_dams_by_reservoir_af", build)]


def figures_totals_af():
    def build():
        return _totals_chart(
            _load(),
            "reservoir_af", "Total reservoir capacity (acre-feet)",
            "BPA federal dams — total reservoir storage by type",
            cfg.BPA_OUTPUT_DIR / "bpa_dams_totals_af.png",
        )
    return [("bpa_dams_totals_af", build)]


def figures_energy_storage_gwh():
    """Bar chart: reservoir energy storage capacity (GWh) per dam, sorted largest-first."""
    def build():
        df = _load("energy_gwh")
        source = "Source: USACE / Bureau of Reclamation; eta = 90%"
        return _bar_chart(
            df,
            "energy_gwh", "Energy storage capacity (GWh)",
            "BPA federal dams — reservoir energy storage capacity",
            cfg.BPA_OUTPUT_DIR / "bpa_dams_energy_storage_gwh.png",
            source_text=source,
        )
    return [("bpa_dams_energy_storage_gwh", build)]


def figures_scatter_mw_vs_gwh():
    """Log-log scatter: nameplate GW vs energy storage GWh, with iso-duration lines."""
    def build():
        from collections import defaultdict

        df = _load()
        df = df[df["energy_gwh"] > 0.01].copy()
        df["capacity_gw"] = df["capacity_mw"] / 1000.0

        fig = Figure(figsize=(11, 7.5), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)

        # Axis limits — set early so iso-line labels can be placed at edges
        x_min, x_max = 0.015, 3000.0
        y_min, y_max = 0.002, 12.0
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        # Iso-duration lines: GWh = GW * hours  →  GW = GWh / hours
        gwh_arr = np.logspace(np.log10(x_min), np.log10(x_max), 300)
        iso_specs = [(1, "1 hr"), (10, "10 hr"), (100, "100 hr"), (1000, "1,000 hr")]
        for hours, iso_label in iso_specs:
            gw_arr = gwh_arr / hours
            ax.plot(gwh_arr, gw_arr, "--", color="0.72", lw=0.9, zorder=0)
            x_at_top = y_max * hours   # GWh where line exits top
            if x_min < x_at_top < x_max:
                ax.text(x_at_top * 0.88, y_max * 0.92, iso_label,
                        color="0.50", fontsize=7.5, ha="right", va="top", rotation=0)
            else:
                y_at_right = x_max / hours
                if y_min < y_at_right < y_max:
                    ax.text(x_max * 0.92, y_at_right * 1.05, iso_label,
                            color="0.50", fontsize=7.5, ha="right", va="bottom")

        # Scatter points
        for dam_type, color, legend_label in [
            ("storage", STORAGE_COLOR, "Storage"),
            ("ror",     ROR_COLOR,     "Run-of-River"),
        ]:
            sub = df[df["dam_type"] == dam_type]
            ax.scatter(sub["energy_gwh"], sub["capacity_gw"],
                       c=color, alpha=0.88, s=45, zorder=3, label=legend_label)

        # Stagger labels for dams at the same point (Snake River lower dams overlap)
        pos_groups: dict = defaultdict(list)
        for _, row in df.iterrows():
            key = (round(row["energy_gwh"], 1), round(row["capacity_gw"], 4))
            pos_groups[key].append(row["name"])

        label_y_off: dict[str, float] = {}
        for key, names in pos_groups.items():
            n = len(names)
            for i, name in enumerate(sorted(names)):
                label_y_off[name] = (i - (n - 1) / 2) * 11

        for _, row in df.iterrows():
            y_off = label_y_off.get(row["name"], 4)
            ax.annotate(
                row["name"],
                (row["energy_gwh"], row["capacity_gw"]),
                xytext=(5, y_off), textcoords="offset points",
                fontsize=6.2, va="center", color="0.15",
            )

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_xlabel("Energy storage capacity (GWh)")
        ax.set_ylabel("Nameplate capacity (GW)")
        ax.set_title("BPA federal dams — generation capacity vs energy storage")
        ax.grid(True, which="both", ls="--", alpha=0.35, zorder=0)
        ax.legend(handles=[
            Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
            Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
        ], loc="lower right", fontsize=9)
        common.add_source(ax, "Source: USACE / Bureau of Reclamation; eta = 90%")
        common.add_watermark(ax, loc="top_left")
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_scatter_gw_vs_gwh.png"
    return [("bpa_dams_scatter_gw_vs_gwh", build)]


_KCFS_PER_MAF_PER_DAY = 1e6 / 1983.0   # 1 MAF / 1 day ≈ 504.3 kcfs

# Manually entered average outflow estimates for dams NOT in the USACE NWD hourly system.
# Source: USGS long-term mean annual streamflow statistics (approximate, ±30%).
_MANUAL_FLOW_KCFS = {
    "Black Canyon Diversion": 3.2,   # Boise River near Emmett, ID (USGS ~3200 cfs mean)
}


def _add_flow(df: pd.DataFrame, dfs: dict) -> pd.DataFrame:
    """Join avg total_outflow_kcfs from 2023 scraped data onto a _DAMS dataframe.

    Falls back to _MANUAL_FLOW_KCFS for dams not in the USACE NWD hourly system.
    """
    flow = {}
    for dam in cfg.ALL_DAMS:
        d = dfs.get(dam.code)
        if d is not None and not d.empty and "total_outflow_kcfs" in d.columns:
            v = d["total_outflow_kcfs"].mean()
            if not pd.isna(v):
                flow[dam.name] = v
    for name, val in _MANUAL_FLOW_KCFS.items():
        if name not in flow:
            flow[name] = val
    out = df.copy()
    out["avg_flow_kcfs"] = out["name"].map(flow)
    return out


def figures_avg_flow_bar(dfs: dict):
    """Bar chart: average daily total outflow (kcfs) per dam, 2023 data."""
    def build():
        df = _add_flow(_load("capacity_mw"), dfs)
        df = (df[df["avg_flow_kcfs"].notna()]
              .sort_values("avg_flow_kcfs", ascending=False)
              .reset_index(drop=True))
        return _bar_chart(
            df,
            "avg_flow_kcfs", "Average total outflow (kcfs)",
            "BPA federal dams — average daily flow (2023)",
            cfg.BPA_OUTPUT_DIR / "bpa_dams_avg_flow_kcfs.png",
            source_text=cfg.SOURCE_USACE,
        )
    return [("bpa_dams_avg_flow_bar", build)]


def figures_scatter_flow_vs_storage(dfs: dict):
    """Log-log scatter: avg daily flow vs reservoir capacity, with iso-days-of-storage lines.

    Cleanly separates storage dams (high reservoir / low flow) from run-of-river
    (low reservoir / high flow). Iso-lines show constant days_of_storage where
    days = reservoir_MAF * 1e6 / (avg_flow_kcfs * 1983 AF/kcfs/day).
    """
    def build():
        from collections import defaultdict

        df = _add_flow(_load("reservoir_af"), dfs)
        df = df[df["avg_flow_kcfs"].notna() & (df["reservoir_af"] > 0)].copy()
        df["reservoir_maf"] = df["reservoir_af"] / 1e6

        fig = Figure(figsize=(11, 7.5), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)

        x_min, x_max = 0.003, 20.0    # MAF
        y_min, y_max = 0.3,  300.0    # kcfs
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        # Iso-days lines: avg_flow_kcfs = reservoir_maf * K / days
        maf_arr = np.logspace(np.log10(x_min), np.log10(x_max), 300)
        for ndays, iso_label in [(1, "1 d"), (10, "10 d"), (100, "100 d"), (1000, "1,000 d")]:
            kcfs_arr = maf_arr * _KCFS_PER_MAF_PER_DAY / ndays
            ax.plot(maf_arr, kcfs_arr, "--", color="0.72", lw=0.9, zorder=0)
            x_at_top = y_max * ndays / _KCFS_PER_MAF_PER_DAY
            if x_min < x_at_top < x_max:
                ax.text(x_at_top * 0.88, y_max * 0.92, iso_label,
                        color="0.50", fontsize=7.5, ha="right", va="top")
            else:
                y_at_right = x_max * _KCFS_PER_MAF_PER_DAY / ndays
                if y_min < y_at_right < y_max:
                    ax.text(x_max * 0.92, y_at_right * 1.05, iso_label,
                            color="0.50", fontsize=7.5, ha="right", va="bottom")

        # Scatter points
        for dam_type, color, leg_label in [
            ("storage", STORAGE_COLOR, "Storage"),
            ("ror",     ROR_COLOR,     "Run-of-River"),
        ]:
            sub = df[df["dam_type"] == dam_type]
            ax.scatter(sub["reservoir_maf"], sub["avg_flow_kcfs"],
                       c=color, alpha=0.88, s=45, zorder=3, label=leg_label)

        # Label stagger: group dams within 0.12 log-units on both axes
        pos_groups: dict = defaultdict(list)
        for _, row in df.iterrows():
            lx = round(np.log10(max(row["reservoir_maf"], 1e-9)) / 0.12) * 0.12
            ly = round(np.log10(max(row["avg_flow_kcfs"],  1e-9)) / 0.12) * 0.12
            pos_groups[(lx, ly)].append(row["name"])

        label_y_off: dict[str, float] = {}
        for key, names in pos_groups.items():
            n = len(names)
            for i, name in enumerate(sorted(names)):
                label_y_off[name] = (i - (n - 1) / 2) * 11

        for _, row in df.iterrows():
            y_off = label_y_off.get(row["name"], 4)
            ax.annotate(
                row["name"],
                (row["reservoir_maf"], row["avg_flow_kcfs"]),
                xytext=(5, y_off), textcoords="offset points",
                fontsize=6.2, va="center", color="0.15",
            )

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_xlabel("Reservoir capacity (MAF)")
        ax.set_ylabel("Average total outflow (kcfs, 2023)")
        ax.set_title("BPA federal dams — average daily flow vs reservoir storage")
        ax.grid(True, which="both", ls="--", alpha=0.35, zorder=0)
        ax.legend(handles=[
            Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
            Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
        ], loc="lower right", fontsize=9)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax, loc="top_left")

        # Print days-of-storage for each dam (surprises flagged)
        print("\n--- Days of storage (reservoir_AF / daily_flow_kcfs / 1983) ---")
        for _, row in df.sort_values("avg_flow_kcfs", ascending=False).iterrows():
            days = row["reservoir_maf"] * 1e6 / (row["avg_flow_kcfs"] * 1983)
            flag = "  <-- NOTE: < 2 d (pondage)" if days < 2 else ""
            print(f"  {row['name']:<22} {days:7.1f} d  "
                  f"({row['reservoir_maf']:.3f} MAF, {row['avg_flow_kcfs']:.1f} kcfs, "
                  f"{row['dam_type']}){flag}")

        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_scatter_flow_vs_storage.png"
    return [("bpa_dams_scatter_flow_vs_storage", build)]


def _cf_df(dfs: dict) -> pd.DataFrame:
    """Per-dam capacity factor from 2023 scraped data, sorted by CF descending."""
    _type_map = {row[0]: row[3] for row in _DAMS}
    _cap_map  = {row[0]: row[1] for row in _DAMS}
    rows = []
    for dam in cfg.ALL_DAMS:
        df = dfs.get(dam.code)
        if df is None or df.empty:
            continue
        avg_power  = df["power_mw"].mean()
        peak_power = df["power_mw"].max()
        cap_mw     = _cap_map.get(dam.name, dam.nameplate_mw)
        rows.append({
            "name":                dam.name,
            "dam_type":            _type_map.get(dam.name, "ror"),
            "nameplate_mw":        cap_mw,
            "avg_power_mw":        avg_power,
            "capacity_factor_pct": avg_power  / cap_mw * 100,
            "peak_cf_pct":         peak_power / cap_mw * 100,
            "load_factor_pct":     avg_power  / peak_power * 100 if peak_power > 0 else float("nan"),
        })
    return (pd.DataFrame(rows)
            .sort_values("capacity_factor_pct", ascending=False)
            .reset_index(drop=True))


def figures_cf_bar(dfs: dict):
    """Bar chart: 2023 annual capacity factor per dam, sorted by CF descending."""
    def build():
        df = _cf_df(dfs)
        colors = [STORAGE_COLOR if t == "storage" else ROR_COLOR for t in df["dam_type"]]
        x = np.arange(len(df))

        fig = Figure(figsize=(14, 6), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)

        ax.bar(x, df["capacity_factor_pct"], color=colors, width=0.75, alpha=0.88, linewidth=0)
        ax.set_xticks(x)
        ax.set_xticklabels(df["name"], rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("Capacity factor (%)")
        ax.set_title("BPA federal dams — annual capacity factor (2023)")
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.legend(handles=[
            Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
            Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
        ], loc="upper right", fontsize=9)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_capacity_factor.png"
    return [("bpa_dams_cf_bar", build)]


def figures_cf_vs_capacity_scatter(dfs: dict):
    """Scatter: 2023 capacity factor (%) vs installed capacity (MW), log x scale."""
    def build():
        from collections import defaultdict

        df = _cf_df(dfs)

        fig = Figure(figsize=(11, 7.5), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)

        for dam_type, color, leg_label in [
            ("storage", STORAGE_COLOR, "Storage"),
            ("ror",     ROR_COLOR,     "Run-of-River"),
        ]:
            sub = df[df["dam_type"] == dam_type]
            ax.scatter(sub["nameplate_mw"], sub["capacity_factor_pct"],
                       c=color, alpha=0.88, s=45, zorder=3, label=leg_label)

        # Stagger labels within 0.12 log-units on x, 2 pct-points on y
        pos_groups: dict = defaultdict(list)
        for _, row in df.iterrows():
            lx = round(np.log10(max(row["nameplate_mw"], 1)) / 0.12) * 0.12
            ly = round(row["capacity_factor_pct"] / 2) * 2
            pos_groups[(lx, ly)].append(row["name"])

        label_y_off: dict[str, float] = {}
        for key, names in pos_groups.items():
            n = len(names)
            for i, name in enumerate(sorted(names)):
                label_y_off[name] = (i - (n - 1) / 2) * 11

        for _, row in df.iterrows():
            ax.annotate(
                row["name"],
                (row["nameplate_mw"], row["capacity_factor_pct"]),
                xytext=(5, label_y_off.get(row["name"], 4)),
                textcoords="offset points",
                fontsize=6.2, va="center", color="0.15",
            )

        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.set_xlabel("Installed capacity (MW)")
        ax.set_ylabel("Capacity factor, 2023 (%)")
        ax.set_title("BPA federal dams — capacity factor vs installed capacity (2023)")
        ax.set_ylim(0, 100)
        ax.grid(True, which="both", ls="--", alpha=0.35, zorder=0)
        ax.legend(handles=[
            Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
            Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
        ], loc="upper right", fontsize=9)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax, loc="top_left")
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_cf_vs_capacity.png"
    return [("bpa_dams_cf_vs_capacity_scatter", build)]


def figures_peak_cf_bar(dfs: dict):
    """Bar chart: 2023 peak (max hourly) capacity factor per dam, sorted descending."""
    def build():
        df = (_cf_df(dfs)
              .sort_values("peak_cf_pct", ascending=False)
              .reset_index(drop=True))
        colors = [STORAGE_COLOR if t == "storage" else ROR_COLOR for t in df["dam_type"]]
        x = np.arange(len(df))

        fig = Figure(figsize=(14, 6), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)

        ax.bar(x, df["peak_cf_pct"], color=colors, width=0.75, alpha=0.88, linewidth=0)
        ax.set_xticks(x)
        ax.set_xticklabels(df["name"], rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("Peak capacity factor (%)")
        ax.set_title("BPA federal dams — peak hourly capacity factor (2023)")
        ax.set_ylim(0, 110)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.legend(handles=[
            Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
            Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
        ], loc="upper right", fontsize=9)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_peak_cf.png"
    return [("bpa_dams_peak_cf_bar", build)]


def figures_peak_cf_vs_capacity_scatter(dfs: dict):
    """Scatter: 2023 peak CF (%) vs installed capacity (MW), log x scale."""
    def build():
        from collections import defaultdict

        df = _cf_df(dfs)

        fig = Figure(figsize=(11, 7.5), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)

        for dam_type, color, leg_label in [
            ("storage", STORAGE_COLOR, "Storage"),
            ("ror",     ROR_COLOR,     "Run-of-River"),
        ]:
            sub = df[df["dam_type"] == dam_type]
            ax.scatter(sub["nameplate_mw"], sub["peak_cf_pct"],
                       c=color, alpha=0.88, s=45, zorder=3, label=leg_label)

        pos_groups: dict = defaultdict(list)
        for _, row in df.iterrows():
            lx = round(np.log10(max(row["nameplate_mw"], 1)) / 0.12) * 0.12
            ly = round(row["peak_cf_pct"] / 2) * 2
            pos_groups[(lx, ly)].append(row["name"])

        label_y_off: dict[str, float] = {}
        for key, names in pos_groups.items():
            n = len(names)
            for i, name in enumerate(sorted(names)):
                label_y_off[name] = (i - (n - 1) / 2) * 11

        for _, row in df.iterrows():
            ax.annotate(
                row["name"],
                (row["nameplate_mw"], row["peak_cf_pct"]),
                xytext=(5, label_y_off.get(row["name"], 4)),
                textcoords="offset points",
                fontsize=6.2, va="center", color="0.15",
            )

        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.set_xlabel("Installed capacity (MW)")
        ax.set_ylabel("Peak capacity factor, 2023 (%)")
        ax.set_title("BPA federal dams — peak capacity factor vs installed capacity (2023)")
        ax.set_ylim(0, 110)
        ax.grid(True, which="both", ls="--", alpha=0.35, zorder=0)
        ax.legend(handles=[
            Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
            Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
        ], loc="upper right", fontsize=9)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax, loc="top_left")
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_peak_cf_vs_capacity.png"
    return [("bpa_dams_peak_cf_vs_capacity_scatter", build)]


def figures_load_factor_bar(dfs: dict):
    """Bar chart: 2023 load factor (avg / peak output) per dam, sorted descending.

    Load factor = avg_power / max_observed_power.  Unlike capacity factor it uses the
    actual peak achieved rather than nameplate, so it measures dispatch pattern (how
    steadily the dam is run) rather than hardware utilisation.
    """
    def build():
        df = (_cf_df(dfs)
              .sort_values("load_factor_pct", ascending=False)
              .reset_index(drop=True))
        colors = [STORAGE_COLOR if t == "storage" else ROR_COLOR for t in df["dam_type"]]
        x = np.arange(len(df))

        fig = Figure(figsize=(14, 6), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)

        ax.bar(x, df["load_factor_pct"], color=colors, width=0.75, alpha=0.88, linewidth=0)
        ax.set_xticks(x)
        ax.set_xticklabels(df["name"], rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("Load factor (%)")
        ax.set_title("BPA federal dams — load factor: avg / peak output (2023)")
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.legend(handles=[
            Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
            Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
        ], loc="upper right", fontsize=9)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_load_factor.png"
    return [("bpa_dams_load_factor_bar", build)]


def figures_scatter_flow_vs_active_storage(dfs: dict):
    """Log-log scatter: avg daily flow vs *active* reservoir storage (usable storage only).

    Identical to figures_scatter_flow_vs_storage but uses active_af (excludes dead pool)
    so iso-lines show days of *usable* storage rather than total reservoir days.
    """
    def build():
        from collections import defaultdict

        df = _add_flow(_load("active_af"), dfs)
        df = df[df["avg_flow_kcfs"].notna() & (df["active_af"] > 0)].copy()
        df["active_maf"] = df["active_af"] / 1e6

        fig = Figure(figsize=(11, 7.5), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)

        x_min, x_max = 0.001, 10.0    # MAF (active is smaller than total)
        y_min, y_max = 0.3,  300.0    # kcfs
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        # Iso-days lines: avg_flow_kcfs = active_maf * K / days
        maf_arr = np.logspace(np.log10(x_min), np.log10(x_max), 300)
        for ndays, iso_label in [(1, "1 d"), (10, "10 d"), (100, "100 d"), (1000, "1,000 d")]:
            kcfs_arr = maf_arr * _KCFS_PER_MAF_PER_DAY / ndays
            ax.plot(maf_arr, kcfs_arr, "--", color="0.72", lw=0.9, zorder=0)
            x_at_top = y_max * ndays / _KCFS_PER_MAF_PER_DAY
            if x_min < x_at_top < x_max:
                ax.text(x_at_top * 0.88, y_max * 0.92, iso_label,
                        color="0.50", fontsize=7.5, ha="right", va="top")
            else:
                y_at_right = x_max * _KCFS_PER_MAF_PER_DAY / ndays
                if y_min < y_at_right < y_max:
                    ax.text(x_max * 0.92, y_at_right * 1.05, iso_label,
                            color="0.50", fontsize=7.5, ha="right", va="bottom")

        for dam_type, color, leg_label in [
            ("storage", STORAGE_COLOR, "Storage"),
            ("ror",     ROR_COLOR,     "Run-of-River"),
        ]:
            sub = df[df["dam_type"] == dam_type]
            ax.scatter(sub["active_maf"], sub["avg_flow_kcfs"],
                       c=color, alpha=0.88, s=45, zorder=3, label=leg_label)

        pos_groups: dict = defaultdict(list)
        for _, row in df.iterrows():
            lx = round(np.log10(max(row["active_maf"],     1e-9)) / 0.12) * 0.12
            ly = round(np.log10(max(row["avg_flow_kcfs"],  1e-9)) / 0.12) * 0.12
            pos_groups[(lx, ly)].append(row["name"])

        label_y_off: dict[str, float] = {}
        for key, names in pos_groups.items():
            n = len(names)
            for i, name in enumerate(sorted(names)):
                label_y_off[name] = (i - (n - 1) / 2) * 11

        for _, row in df.iterrows():
            ax.annotate(
                row["name"],
                (row["active_maf"], row["avg_flow_kcfs"]),
                xytext=(5, label_y_off.get(row["name"], 4)),
                textcoords="offset points",
                fontsize=6.2, va="center", color="0.15",
            )

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_xlabel("Active reservoir storage (MAF)")
        ax.set_ylabel("Average total outflow (kcfs, 2023)")
        ax.set_title("BPA federal dams — average daily flow vs active reservoir storage")
        ax.grid(True, which="both", ls="--", alpha=0.35, zorder=0)
        ax.legend(handles=[
            Patch(facecolor=STORAGE_COLOR, alpha=0.88, label="Storage"),
            Patch(facecolor=ROR_COLOR,     alpha=0.88, label="Run-of-River"),
        ], loc="lower right", fontsize=9)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax, loc="top_left")

        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_scatter_flow_vs_active_storage.png"
    return [("bpa_dams_scatter_flow_vs_active_storage", build)]


def _spill_df(dfs: dict) -> pd.DataFrame:
    """Per-dam gen vs spill table from 2023 scraped data, sorted by spill fraction desc."""
    _type_map = {row[0]: row[3] for row in _DAMS}  # name -> dam_type
    rows = []
    for dam in cfg.ALL_DAMS:
        df = dfs.get(dam.code)
        if df is None or df.empty:
            continue
        gen   = df["gen_flow_kcfs"].mean()
        spill = df["spill_kcfs"].mean()
        total = df["total_outflow_kcfs"].mean()
        if pd.isna(total) or total == 0:
            continue
        rows.append({
            "name":       dam.name,
            "dam_type":   _type_map.get(dam.name, "ror"),
            "gen_kcfs":   gen,
            "spill_kcfs": spill,
            "total_kcfs": total,
            "spill_frac": spill / total,
        })
    return (pd.DataFrame(rows)
            .sort_values("spill_frac", ascending=False)
            .reset_index(drop=True))


def _spill_energy_df(dfs: dict) -> pd.DataFrame:
    """Per-dam generated GWh vs spilled potential GWh, sorted by spill energy fraction desc.

    Spill potential = spill_kcfs * 1000 * avg_head_ft * 7.62e-5  (same power formula as gen,
    η=0.90 baked in) — what would have been generated had spill passed through turbines.
    """
    _type_map = {row[0]: row[3] for row in _DAMS}
    rows = []
    for dam in cfg.ALL_DAMS:
        df = dfs.get(dam.code)
        if df is None or df.empty:
            continue
        gen_mw    = df["power_mw"].mean()
        head_ft   = df["head_ft"].mean()
        spill_mw  = df["spill_kcfs"].mean() * 1000 * head_ft * 7.62e-5
        total_mw  = gen_mw + spill_mw
        if total_mw == 0 or pd.isna(total_mw):
            continue
        rows.append({
            "name":       dam.name,
            "dam_type":   _type_map.get(dam.name, "ror"),
            "gen_gwh":    gen_mw   * 8760 / 1000,
            "spill_gwh":  spill_mw * 8760 / 1000,
            "total_gwh":  total_mw * 8760 / 1000,
            "spill_frac": spill_mw / total_mw,
        })
    return (pd.DataFrame(rows)
            .sort_values("spill_frac", ascending=False)
            .reset_index(drop=True))


def figures_spill_energy_bars(dfs: dict):
    """Stacked bar charts: generated GWh vs spilled potential GWh.

    Product 1 (volume):   gen + spill in GWh/year, sorted by total GWh
    Product 2 (fraction): gen% + spill% of total potential, sorted by spill fraction
    """
    def _axes_base(title, ylabel):
        fig = Figure(figsize=(14, 6), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        return fig, ax

    def _finish(ax, df, x):
        ax.set_xticks(x)
        ax.set_xticklabels(df["name"], rotation=45, ha="right", fontsize=8)
        ax.set_ylim(bottom=0)
        ax.legend(loc="upper right", fontsize=9)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)

    def build_volume():
        df = (_spill_energy_df(dfs)
              .sort_values("total_gwh", ascending=False)
              .reset_index(drop=True))
        x = np.arange(len(df))

        fig, ax = _axes_base(
            "BPA federal dams — generated vs spilled energy (2023), sorted by total",
            "Annual energy (GWh/year)",
        )
        ax.bar(x, df["gen_gwh"],   width=0.75, color=GEN_COLOR,   alpha=0.88,
               linewidth=0, label="Generated")
        ax.bar(x, df["spill_gwh"], width=0.75, color=SPILL_COLOR, alpha=0.88,
               linewidth=0, label="Spill potential", bottom=df["gen_gwh"])
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        _finish(ax, df, x)
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_spill_energy_volume.png"

    def build_fraction():
        df = _spill_energy_df(dfs)
        x         = np.arange(len(df))
        gen_pct   = (1 - df["spill_frac"]) * 100
        spill_pct = df["spill_frac"] * 100

        fig, ax = _axes_base(
            "BPA federal dams — generated vs spilled energy fraction (2023), sorted by spill fraction",
            "Fraction of total potential energy (%)",
        )
        ax.bar(x, gen_pct,   width=0.75, color=GEN_COLOR,   alpha=0.88,
               linewidth=0, label="Generated")
        ax.bar(x, spill_pct, width=0.75, color=SPILL_COLOR, alpha=0.88,
               linewidth=0, label="Spill potential", bottom=gen_pct)
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        _finish(ax, df, x)
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_spill_energy_fraction_pct.png"

    return [
        ("bpa_dams_spill_energy_volume",   build_volume),
        ("bpa_dams_spill_energy_fraction", build_fraction),
    ]


def figures_spill_bars(dfs: dict):
    """Stacked bar charts: generation flow vs spill, all dams sorted by spill fraction.

    Product 1 (volume):   gen + spill in MAF/year
    Product 2 (fraction): gen% + spill% of total outflow
    """
    def _axes_base(title, ylabel):
        fig = Figure(figsize=(14, 6), dpi=render.DPI)
        FigureCanvasAgg(fig)
        fig.set_constrained_layout(True)
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        return fig, ax

    def _finish(ax, df, x):
        ax.set_xticks(x)
        ax.set_xticklabels(df["name"], rotation=45, ha="right", fontsize=8)
        ax.set_ylim(bottom=0)
        ax.legend(loc="upper right", fontsize=9)
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)

    def build_volume():
        df = (_spill_df(dfs)
              .sort_values("total_kcfs", ascending=False)
              .reset_index(drop=True))
        x         = np.arange(len(df))
        gen_maf   = df["gen_kcfs"]   * _KCFS_TO_MAF_YR
        spill_maf = df["spill_kcfs"] * _KCFS_TO_MAF_YR

        fig, ax = _axes_base(
            "BPA federal dams — generation vs spill volume (2023), sorted by total flow",
            "Annual flow volume (MAF/year)",
        )
        ax.bar(x, gen_maf,   width=0.75, color=GEN_COLOR,   alpha=0.88,
               linewidth=0, label="Generation flow")
        ax.bar(x, spill_maf, width=0.75, color=SPILL_COLOR, alpha=0.88,
               linewidth=0, label="Spill", bottom=gen_maf)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.1f}"))
        _finish(ax, df, x)
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_spill_volume.png"

    def build_fraction():
        df = _spill_df(dfs)
        x         = np.arange(len(df))
        gen_pct   = (1 - df["spill_frac"]) * 100
        spill_pct = df["spill_frac"] * 100

        fig, ax = _axes_base(
            "BPA federal dams — generation vs spill fraction (2023), sorted by spill fraction",
            "Fraction of total outflow (%)",
        )
        ax.bar(x, gen_pct,   width=0.75, color=GEN_COLOR,   alpha=0.88,
               linewidth=0, label="Generation flow")
        ax.bar(x, spill_pct, width=0.75, color=SPILL_COLOR, alpha=0.88,
               linewidth=0, label="Spill", bottom=gen_pct)
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        _finish(ax, df, x)
        return fig, cfg.BPA_OUTPUT_DIR / "bpa_dams_spill_fraction_pct.png"

    return [
        ("bpa_dams_spill_volume",   build_volume),
        ("bpa_dams_spill_fraction", build_fraction),
    ]


if __name__ == "__main__":
    cfg.BPA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dfs = {dam.code: derived.load_dam(dam.csv_path) for dam in cfg.ALL_DAMS}
    plans = [
        *figures_all_dams(), *figures_totals_mw(),
        *figures_reservoir_af(), *figures_totals_af(),
        *figures_energy_storage_gwh(),
        *figures_scatter_mw_vs_gwh(),
        *figures_avg_flow_bar(dfs),
        *figures_cf_bar(dfs),
        *figures_cf_vs_capacity_scatter(dfs),
        *figures_peak_cf_bar(dfs),
        *figures_peak_cf_vs_capacity_scatter(dfs),
        *figures_load_factor_bar(dfs),
        *figures_scatter_flow_vs_storage(dfs),
        *figures_scatter_flow_vs_active_storage(dfs),
        *figures_spill_bars(dfs),
        *figures_spill_energy_bars(dfs),
    ]
    for name, build in plans:
        fig, path = build()
        print("wrote", render.save_fig(fig, path))

    df = _load("energy_gwh")
    print("\n--- Energy storage by dam (GWh) ---")
    for _, r in df.iterrows():
        marker = "<-- NOTE" if r["name"] == "Dworshak" else ""
        print(f"  {r['name']:<25} {r['energy_gwh']:7.1f} GWh  "
              f"(active={r['active_af']:>9,.0f} AF, head={r['mean_head_ft']:>4.0f} ft, "
              f"{r['dam_type']})  {marker}")

    # Flag counterintuitive findings
    gcl = df[df["name"] == "Grand Coulee"]["energy_gwh"].iloc[0]
    dwk = df[df["name"] == "Dworshak"]["energy_gwh"].iloc[0]
    lib = df[df["name"] == "Libby"]["energy_gwh"].iloc[0]
    print(f"\n*** Dworshak energy storage ({dwk:.0f} GWh) is {dwk/gcl*100:.0f}% of Grand Coulee ({gcl:.0f} GWh)")
    print(f"    despite having only {2_018_200/5_185_200*100:.0f}% of GCL's active storage (2.0M vs 5.2M AF)")
    print(f"    High head (640 ft vs 315 ft) compensates. Same story for Libby ({lib:.0f} GWh).")
