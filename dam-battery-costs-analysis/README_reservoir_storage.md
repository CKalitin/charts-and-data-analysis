# Columbia River Reservoir Storage — Energy Equivalent Methodology

## File

`columbia_reservoir_storage.csv` — 8 major BPA federal dams with reservoir storage
capacity, hydraulic head, and estimated electrical energy equivalent of active storage.

---

## The energy formula

Energy stored in a reservoir is gravitational potential energy, converted to electricity
through the turbines. Starting from first principles:

```
P = ρ * g * Q * h * η
```

Where:
- `ρ` = water density = 1000 kg/m³
- `g` = gravitational acceleration = 9.81 m/s²
- `Q` = volumetric flow rate (m³/s)
- `h` = net head (m)
- `η` = turbine-generator efficiency (~0.90 for modern Francis turbines)

Integrating over a volume `V` (m³) gives total energy in joules, then convert to MWh:

```
E (MWh) = ρ * g * η * V * h / (3.6 × 10⁹)
         = 1000 * 9.81 * 0.90 * V_m³ * h_m / 3,600,000,000
```

### Unit conversion: acre-feet and feet → MWh

US reservoir volumes are reported in acre-feet (AF). 1 acre-ft = 1,233.48 m³.
Head is reported in feet. 1 ft = 0.3048 m.

Substituting:

```
E (MWh) = 1000 * 9.81 * 0.90 * (V_AF * 1233.48) * (h_ft * 0.3048)
           / 3,600,000,000
         = V_AF * h_ft * 0.0001024
```

**The constant 0.0001024 MWh/(acre-ft · ft)** is the key number.
To get GWh, divide by 1000:

```
E (GWh) ≈ V_AF * h_ft * 1.024 × 10⁻⁷
```

### In code

```python
K = 0.0001024   # MWh per (acre-ft * ft), assuming η = 0.90

energy_mwh = active_storage_af * head_ft * K
energy_gwh  = energy_mwh / 1000
```

---

## Schema for `columbia_reservoir_storage.csv`

| Column | Units | Description |
|---|---|---|
| `name` | — | Dam name |
| `dam_type` | — | `storage` (dispatchable) or `run_of_river` (must-run) |
| `river` | — | River impounded |
| `state` | — | US state(s) |
| `capacity_mw` | MW | Installed nameplate generating capacity |
| `total_storage_af` | acre-feet | Total reservoir capacity |
| `active_storage_af` | acre-feet | Usable/active storage between min and max operating pool elevation |
| `head_ft` | feet | Hydraulic head used for calculation (typically maximum or rated head) |
| `energy_gwh_active` | GWh | **Estimated electrical energy equivalent of active storage** |
| `notes` | — | Caveats on active storage estimates, head assumptions |
| `source_url` | — | Primary source for capacity and storage figures |

---

## Results summary

| Dam | Type | Active Storage (AF) | Head (ft) | Energy Equiv (GWh) | Capacity (MW) |
|---|---|---|---|---|---|
| Libby | storage | 4,700,000 | 420 | **202 GWh** | 620 |
| Grand Coulee | storage | 5,185,400 | 380 | **202 GWh** | 6,809 |
| Hungry Horse | storage | 2,400,000 | 520 | **128 GWh** | 428 |
| Dworshak | storage | 2,016,000 | 560 | **116 GWh** | 400 |
| John Day | run-of-river | 80,000 | 105 | ~0.9 GWh | 2,484 |
| Bonneville | run-of-river | 54,000 | 60 | ~0.3 GWh | 1,242 |
| Chief Joseph | run-of-river | 20,000 | 130 | ~0.3 GWh | 2,614 |
| McNary | run-of-river | 22,000 | 85 | ~0.2 GWh | 954 |

**Total storage dams: ~648 GWh ≈ 0.65 TWh**

BPA annual generation ≈ 87 TWh, so total reservoir storage ≈ **0.7% of annual output**.
But that's misleading — the storage isn't used that way. See the interpretation below.

---

## What this means — and the critical caveat

### The right comparison is daily and weekly dispatch, not annual

The ~648 GWh across four major storage dams is most useful understood as:
- **Grand Coulee alone** (~202 GWh): at a typical output of 3,000 MW, that's ~67 hours
  of storage — nearly 3 days of continuous full output
- **All four storage dams combined** (~648 GWh): at 3,000 MW output, ~9 days of storage

This is not "battery storage" in the hourly sense — it's multi-day to multi-week
storage. The reservoirs fill over months (snowmelt season) and drain over months
(summer/fall). Daily dispatch varies the output by perhaps 1,000–4,000 MW within Grand
Coulee's 6,809 MW range, drawing down the reservoir by perhaps 1–3 feet per day, which
corresponds to perhaps 50–150 GWh per day of swing.

### Head varies with reservoir level

The `head_ft` in the CSV is the maximum/rated head. As the reservoir drains from full pool
to minimum pool, head decreases — typically by 10–15% for deep reservoirs like Libby and
Dworshak. The actual average head over a discharge cycle is lower than the maximum.
Energy calculations using max head overestimate by ~5–10%.

The correct calculation for a more accurate estimate:

```python
# Head scales linearly with reservoir level (approximately)
# If max head = h_max, min head = h_min:
h_avg = (h_max + h_min) / 2
energy_mwh = active_storage_af * h_avg * K
```

For Grand Coulee: max pool 1290 ft, min pool 1208 ft, dam base ~900 ft.
So h_max ≈ 390 ft, h_min ≈ 308 ft, h_avg ≈ 349 ft.
Revised estimate: 5,185,400 × 349 × 0.0001024 / 1000 ≈ **185 GWh** (vs 202 using max head).

### Run-of-river dams have effectively zero storage

The run-of-river dams (Bonneville, John Day, McNary, Chief Joseph) show <1 GWh of
equivalent storage despite having large generating capacities. This confirms that:
1. Their output is **constrained by river inflow** — they must pass what the river delivers
2. During high runoff, they **cannot reduce output** without spilling water over the dam
3. During low runoff, they **cannot increase output** beyond what the river provides
4. This is the mechanism behind the 2011 wind curtailment — spring runoff forced run-of-river
   dams to run at capacity, and there was nowhere for that power to go

### Comparison with BESS

For context, the ~648 GWh of Columbia River reservoir storage equivalent:
- At $125/kWh Ember all-in BESS cost: would cost **$81 billion** to replicate with batteries
- At $334/kWh NREL US cost: would cost **$216 billion**
- The actual construction cost of these four dams was ~$2–3 billion in nominal dollars
  (~$10–20 billion in 2025$)

This is the most important number for the blog post argument: reservoir storage is
extraordinarily cheap per GWh compared to BESS — because the water cycle is free and
the civil works were built 50–80 years ago. The question is whether you can get
*additional* storage flexibility by pairing BESS with a dam to shave peak output.

---

## Data sources

- Grand Coulee storage: [Wikipedia](https://en.wikipedia.org/wiki/Grand_Coulee_Dam);
  USACE NWD project page (`nwd-wc.usace.army.mil/dd/common/projects/www/gcl.html`)
- Libby Dam: [Wikipedia](https://en.wikipedia.org/wiki/Libby_Dam)
- Dworshak Dam: [Wikipedia](https://en.wikipedia.org/wiki/Dworshak_Dam)
- Hungry Horse Dam: [Wikipedia](https://en.wikipedia.org/wiki/Hungry_Horse_Dam)
- Bonneville Dam: [Wikipedia](https://en.wikipedia.org/wiki/Bonneville_Dam)
- John Day Dam: [Wikipedia](https://en.wikipedia.org/wiki/John_Day_Dam)
- McNary Dam: [Wikipedia](https://en.wikipedia.org/wiki/McNary_Dam)
- Chief Joseph Dam: [Wikipedia](https://en.wikipedia.org/wiki/Chief_Joseph_Dam)
- BPA system overview: [BPA.gov](https://www.bpa.gov/energy-and-services/power)
- FCRPS Hydrosystem: [Bureau of Reclamation](https://www.usbr.gov/pn/fcrps/hydro/index.html)

---

## How to get the actual generation profile data

### BPA 5-minute data (total hydro, not per-dam) — easiest

Annual Excel files with 5-minute resolution, 2007–present. Contains: Load, Wind,
Solar, **Hydro total**, Thermal, Nuclear, Net Interchange.

```
# Full year 2024:
https://transmission.bpa.gov/Business/Operations/Wind/OPITabularReports/WindGenTotalLoadYTD_2024.xlsx

# Full year 2025 (YTD):
https://transmission.bpa.gov/Business/Operations/Wind/OPITabularReports/WindGenTotalLoadYTD_2025.xlsx
```

~105,000 rows per year at 5-minute intervals. Hydro column is all 46 BPA plants combined.

### USACE NWD hourly per-dam data — Grand Coulee specifically

URL pattern (date-addressable, per-day HTML tables):
```
https://www.nwd-wc.usace.army.mil/dd/nwdp/project_hourly/webexec/rep?r=gcl&date=MM/DD/YYYY
```

Example for January 15, 2024:
```
https://www.nwd-wc.usace.army.mil/dd/nwdp/project_hourly/webexec/rep?r=gcl&date=1/15/2024
```

Data includes: forebay elevation, tailwater, inflow, outflow, powerhouse generation (MW),
spill (kcfs). **This is hourly per-dam generation for Grand Coulee specifically.**
It requires scraping one page per day (robots.txt disallows automated access, but
the data is public — check current status before scraping).

Other project codes:
- `bon` = Bonneville
- `tda` = The Dalles
- `jda` = John Day
- `mcn` = McNary
- `dwk` = Dworshak
- `lby` = Libby
- `hgn` = Hungry Horse

### EIA Electricity Data Browser — monthly per plant

EIA-923 monthly data, per plant, accessible via API:
```
https://api.eia.gov/v2/electricity/electric-power-operational-data/data/
  ?api_key=YOUR_KEY&facets[plantid][]=4012   # Grand Coulee EIA plant ID
  &frequency=monthly&data[]=generation
```

Grand Coulee EIA plant code: **4012**  
Bonneville: **9903** (approximate — verify via EIA plant search)

Monthly resolution only — not useful for intraday profile analysis.

### USBR Hydromet historical — reservoir levels, not power

Historical daily reservoir elevation and storage data (not power output):
```
https://www.usbr.gov/pn/hydromet/arcread.html
```

Use station codes like `GCAM` (Grand Coulee forebay). Useful for correlating reservoir
drawdown with generation patterns.
