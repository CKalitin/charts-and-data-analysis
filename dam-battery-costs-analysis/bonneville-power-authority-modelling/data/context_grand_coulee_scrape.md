# Task: Scrape Grand Coulee Dam Hourly Generation & Build Generation Profile

## What this is for

Blog post analysis comparing hydroelectric dam costs vs. battery storage (BESS).
The goal of this specific task is to **prove empirically that storage dams (Grand Coulee)
behave as peakers** — ramping output 2–3× between overnight and evening demand peaks —
while run-of-river dams (Bonneville, John Day) hold flat output driven by river flow.

This diurnal peaking pattern is central to the blog post argument: a storage dam already
provides temporal load-shifting. BESS paired with a dam adds a second layer of flexibility
on top of that. Understanding the existing profile is required before modeling the
dam + BESS optimization.

---

## Step 1: Scrape the data

### Source

USACE Northwestern Division hourly project data:
```
https://www.nwd-wc.usace.army.mil/dd/nwdp/project_hourly/webexec/rep?r=gcl&date=MM/DD/YYYY
```

The page returns an HTML table with 24 rows (one per hour) plus AVG/MAX/MIN summary rows.

**Columns on the page:**
| Column | Units | Description |
|---|---|---|
| Hour | 1–24 | Hour of day (local Pacific time) |
| Total Outflow | kcfs | All water leaving dam |
| Generation Flow | kcfs | Water through turbines (generates power) |
| Spill | kcfs | Water over spillway (wasted — no power) |
| Forebay Elevation | ft | Reservoir water surface elevation |
| Tailwater Elevation | ft | Elevation below dam |
| Average Head | ft | Forebay minus tailwater = hydraulic head |

**Power is NOT directly on the page.** Compute it:
```python
# K = ρ * g * η / unit_conversions = 7.63e-5 MW per (cfs * ft)
# η = 0.90 (turbine efficiency), 1 kcfs = 1000 cfs
power_mw = gen_flow_kcfs * 1000 * head_ft * 7.63e-5
```

### Project codes for other dams
| Code | Dam | Type |
|---|---|---|
| `gcl` | Grand Coulee | Storage / peaker |
| `dwk` | Dworshak | Storage / peaker |
| `bon` | Bonneville | Run-of-river |
| `jda` | John Day | Run-of-river |
| `mcn` | McNary | Run-of-river |
| `lby` | Libby | Storage |

### Scraping instructions

- Use `requests` + `BeautifulSoup`
- Set a **1-second delay** between requests (polite scraping of a gov server)
- Use a browser-like User-Agent header
- Set `Referer: https://www.nwd-wc.usace.army.mil/dd/common/projects/www/gcl.html`
- Scrape **full calendar year 2023** for Grand Coulee (`gcl`)
- Also scrape **full calendar year 2023** for Bonneville (`bon`) for comparison
- Write incrementally (flush after each day) so partial runs are recoverable
- Skip AVG/MAX/MIN rows — only keep rows where `cells[0].isdigit()`

### Output CSV schema

```
date, hour, datetime, dam_code, dam_name,
total_outflow_kcfs, gen_flow_kcfs, spill_kcfs,
forebay_elev_ft, tailwater_elev_ft, head_ft,
power_mw
```

- `datetime` = ISO format `YYYY-MM-DDTHH:00` for easy pandas parsing
- Save as `grand_coulee_hourly_2023.csv` and `bonneville_hourly_2023.csv`
- ~8,760 rows per file (365 days × 24 hours)

A working scraper is in `scrape_grand_coulee.py` — use it as the base.

---

## Step 2: Also download BPA 5-minute total system data

This gives total hydro MW for the entire BPA system at 5-minute resolution — useful for
context around Grand Coulee's individual contribution.

NOTE: This has already been completed by the user with the bpa_5min_2024.csv file, some more data processing and column renaming may be required.

**Direct download (Excel, no scraping needed):**
```
https://transmission.bpa.gov/Business/Operations/Wind/OPITabularReports/WindGenTotalLoadYTD_2023.xlsx
```

Columns in this file (2022+ format):
- DateTime (5-minute intervals)
- Load (MW)
- Wind Generation (MW)
- Wind Forecast (MW)
- Hydro (MW)   ← total of all 46 BPA hydro plants
- Thermal (MW)
- Nuclear (MW)
- Net Interchange (MW)

Save the hydro column as `bpa_5min_2023.csv` with columns `datetime, hydro_mw, load_mw`.
~105,000 rows for a full year.

---

## Step 3: Analysis and plots

Load both datasets and produce the following plots. Save all to `outputs/` directory.

### Plot 1: Grand Coulee average diurnal profile by season

**What to show:** Average hourly power output (MW) by hour of day, split into 4 seasons.
Overlay on a single chart with seasonal labels.

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("grand_coulee_hourly_2023.csv", parse_dates=["datetime"])
df["hour"] = df["datetime"].dt.hour
df["month"] = df["datetime"].dt.month
df["season"] = df["month"].map({
    12:"Winter", 1:"Winter", 2:"Winter",
    3:"Spring",  4:"Spring",  5:"Spring",
    6:"Summer",  7:"Summer",  8:"Summer",
    9:"Fall",   10:"Fall",   11:"Fall",
})

diurnal = df.groupby(["season", "hour"])["power_mw"].mean().unstack(level=0)
# Plot diurnal — x=hour, y=MW, one line per season
```

**Expected pattern:** Summer and Fall should show clear peaking behavior (low overnight,
high evening). Spring may show suppressed output due to spill. Winter should show moderate
consistent output.

**Filename:** `outputs/grand_coulee_diurnal_by_season_2023.png`

### Plot 2: Grand Coulee vs Bonneville — diurnal comparison

**What to show:** Annual average hourly profile for Grand Coulee vs Bonneville on the
same axes. This is the key chart proving storage dam = peaker, run-of-river = flat.

- Grand Coulee should show a clear morning ramp and evening peak, with output dropping
  overnight to perhaps 40–50% of peak
- Bonneville should show a nearly flat line — perhaps ±10% variation driven by grid
  load-following rather than water storage decisions

**Filename:** `outputs/storage_vs_runofriver_diurnal_2023.png`

### Plot 3: Full year time series — Grand Coulee power MW

**What to show:** Daily average power (MW) across all of 2023. Overlay the nameplate
capacity (6,809 MW) as a horizontal reference line.

Add annotations for:
- Spring runoff season (April–June) — typically high generation, possible spill
- Summer peak season (July–August) — peak demand, typically high dispatch
- Low water season (October–December) — reservoir drawdown

**Filename:** `outputs/grand_coulee_annual_timeseries_2023.png`

### Plot 4: Capacity factor by month

**What to show:** Bar chart of monthly capacity factor = avg_power_mw / 6809.

Grand Coulee nameplate = **6,809 MW**. Annual average CF ≈ 35%.

**Filename:** `outputs/grand_coulee_cf_by_month_2023.png`

### Plot 5: Spill fraction by month

**What to show:** Monthly average spill as % of total outflow.
`spill_fraction = spill_kcfs / total_outflow_kcfs`

Spring months should show highest spill. This is the 2011 wind curtailment mechanism —
when spill is high, the dam is at capacity and cannot reduce output. Annotate with note.

**Filename:** `outputs/grand_coulee_spill_fraction_2023.png`

### Plot 5: Spill fraction by month

Hello Claude, I am the user! Christopher Kalitin.

I also want the see the generation by type and load/exports side by side on a chart (these are two charts on the same image). I want this for the first day of every calendar quarter for the BPA grid.

Furthermore, I want a line graph showing the net generation and load+export for every day listed above (4). This way we have 4 series on each chart side by side on one image.

Name the file accordingly.

---

## Step 4: Key numbers to extract and print

After building the charts, print these to stdout (for inclusion in the blog post):

```python
# Annual average
print(f"Annual avg power: {df['power_mw'].mean():.0f} MW")
print(f"Annual CF: {df['power_mw'].mean()/6809*100:.1f}%")

# Peak vs trough diurnal (annual average)
hourly_avg = df.groupby("hour")["power_mw"].mean()
print(f"Avg overnight min (hr 2-5): {hourly_avg[2:6].mean():.0f} MW")
print(f"Avg evening peak (hr 17-20): {hourly_avg[17:21].mean():.0f} MW")
print(f"Daily swing ratio: {hourly_avg[17:21].mean() / hourly_avg[2:6].mean():.2f}x")

# Spill stats
spill_frac = df["spill_kcfs"] / df["total_outflow_kcfs"]
print(f"Hours with any spill: {(df['spill_kcfs']>0).sum()} / {len(df)}")
print(f"Max spill fraction month: ...")
```

---

## Context for the blog post argument

The core claim being supported by this data:

> Storage dams already do temporal load-shifting. Grand Coulee ramps from ~1,500 MW
> overnight to ~4,000 MW at evening peak — a 2.5× swing — acting as the Pacific
> Northwest's largest "peaker plant." Run-of-river dams (Bonneville, John Day) cannot
> do this and must run at whatever flow the river provides.
>
> Adding BESS to a storage dam system adds a *second* layer of flexibility on top of
> existing peaking behavior, enabling the dam to be downsized while maintaining or
> improving the generation profile match to demand.

The diurnal profile charts (Plots 1 and 2) are the empirical proof. If the data shows
Grand Coulee with a flat profile, the argument weakens significantly. If it shows a
strong diurnal swing, the argument is confirmed.

---

## Charting style

- Use matplotlib, professional style (no seaborn default colors)
- Use `plasma` or `tab10` colormap for seasonal lines
- Annotate key data points directly on the chart (don't rely on legend alone)
- Include a small info box with: data source, year, dam nameplate capacity
- Log-y axis is NOT appropriate here (MW values are all positive and same order)
- Save at 150 dpi minimum
- All charts must be readable standalone — include title, axis labels with units,
  and a source credit (`Source: USACE Northwestern Division, 2023`)
