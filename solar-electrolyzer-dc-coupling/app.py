"""
Streamlit web UI for the Solar-Electrolyzer DC Coupling Simulator.

Run with:    streamlit run app.py

All physics is imported from sim.py — this file is purely the UI layer
(sliders, layout, Plotly figures). Edit physics in sim.py.
"""

import json
from pathlib import Path

import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

# ─── Persistent settings ─────────────────────────────────────────────────────
# Slider values are saved to app_state.json next to this file and reloaded on
# every launch. Reset button in sidebar wipes the file and restores defaults.
STATE_FILE = Path(__file__).parent / 'app_state.json'

DEFAULTS = {
    'I_sc': 10.0, 'V_oc': 500.0, 'N_series': 1, 'N_parallel': 1,
    'G_ref': 1000.0, 'T_cell_C': 35.0, 'n_ideality': 1.3, 'V_oc_per_cell': 0.62,
    'N_cells_series': 200, 'electrode_area_cm2': 100.0, 'M_strings': 10,
    'V_onset_cell': 1.48, 'R_ohmic_area': 0.2, 'A_tafel': 0.06,
    'j0_mA': 1.0, 'j_lim_mA': 800, 'B_mt': 0.05, 'faradaic_eff': 1.0,
    'G_single': 800, 'G_min': 0, 'G_max': 1000, 'G_steps': 101,
}

def _load_state():
    if STATE_FILE.exists():
        try:
            with STATE_FILE.open(encoding='utf-8') as f:
                saved = json.load(f)
            merged = {**DEFAULTS, **{k: v for k, v in saved.items() if k in DEFAULTS}}
            return merged
        except Exception:
            pass
    return dict(DEFAULTS)

def _save_state(values: dict):
    try:
        with STATE_FILE.open('w', encoding='utf-8') as f:
            json.dump(values, f, indent=2)
    except Exception:
        pass

S = _load_state()

from sim import (
    SolarConfig, ElectrolyzerConfig, SweepConfig, SimConfig,
    solar_current, array_iph, cell_voltage, cell_overpotentials,
    operating_point, best_operating_point, mpp, evaluate, run_sweep,
    V_REVERSIBLE, V_THERMONEUTRAL,
)

st.set_page_config(page_title='Solar-Electrolyzer DC Coupling',
                   page_icon='⚡', layout='wide')

# ─── Theme detection — pick a Plotly template that matches Streamlit ─────────
# Streamlit's theme is set in .streamlit/config.toml or the UI; fall back to
# 'auto' which we treat as dark (the user's screenshot uses dark).
def _is_dark():
    try:
        base = st.get_option('theme.base')
        if base in ('dark', 'light'):
            return base == 'dark'
    except Exception:
        pass
    return True   # default to dark — works on both

DARK = _is_dark()
TEMPLATE   = 'plotly_dark' if DARK else 'plotly_white'
ACCENT_HI  = '#f6e58d' if DARK else '#222222'   # MPP marker / dashed locus
ACCENT_OP  = '#ff6b6b'                          # DC op point — same on both
SOLAR_LINE = '#74b9ff' if DARK else '#1f4e8c'   # solar I(V) curve
NEUTRAL    = '#cccccc' if DARK else '#444444'   # MPP locus, family lines
GRID_FAMILY = '#888888'                          # grey family in trajectory


# ─── Sidebar: all parameters as live controls ────────────────────────────────
st.sidebar.title("Parameters")
st.sidebar.caption("Drag any slider — plots update live. Settings auto-save to disk.")

if st.sidebar.button("↺ Reset to defaults"):
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    st.rerun()

with st.sidebar.expander("☀️ Solar array", expanded=True):
    I_sc       = st.slider("I_sc per module (A)",        0.5, 200.0, float(S['I_sc']), 0.5)
    V_oc       = st.slider("V_oc per module (V)",        10.0, 1000.0, float(S['V_oc']), 10.0)
    N_series   = st.slider("Modules in series",          1, 20, int(S['N_series']))
    N_parallel = st.slider("Modules in parallel",        1, 50, int(S['N_parallel']))
    G_ref      = st.slider("Reference irradiance (W/m²)", 500.0, 1200.0, float(S['G_ref']), 50.0)
    T_cell_C   = st.slider("Cell temperature (°C)",      0.0, 80.0, float(S['T_cell_C']), 1.0)
    n_ideality = st.slider("Diode ideality n",           1.0, 2.0, float(S['n_ideality']), 0.05)
    V_oc_per_cell = st.slider("V_oc per cell (V) — sets thermal-voltage scaling",
                              0.4, 0.8, float(S['V_oc_per_cell']), 0.01)

with st.sidebar.expander("⚡ Electrolyzer stack", expanded=True):
    N_cells_series     = st.slider("Cells in series per stack",  10, 1000, int(S['N_cells_series']), 10)
    electrode_area_cm2 = st.slider("Electrode area (cm²)",      10.0, 1000.0, float(S['electrode_area_cm2']), 10.0)
    M_strings          = st.slider("Total parallel stacks (strings)", 1, 30, int(S['M_strings']))
    V_onset_cell       = st.slider("Onset voltage per cell (V)", 1.23, 1.6, float(S['V_onset_cell']), 0.01)
    R_ohmic_area       = st.slider("R_ohmic·area per cell (Ω·cm²)", 0.05, 1.0, float(S['R_ohmic_area']), 0.05)
    A_tafel            = st.slider("Tafel slope A (V)",          0.02, 0.15, float(S['A_tafel']), 0.01)
    j0_mA              = st.slider("Exchange current density j₀ (mA/cm²)",
                                   0.01, 10.0, float(S['j0_mA']), 0.05)
    j_lim_mA           = st.slider("Limiting current density j_lim (mA/cm²)",
                                   100, 2000, int(S['j_lim_mA']), 50)
    B_mt               = st.slider("Mass-transport prefactor B (V)",
                                   0.0, 0.2, float(S['B_mt']), 0.01)
    faradaic_eff       = st.slider("Faradaic efficiency (assumption)",
                                   0.7, 1.0, float(S['faradaic_eff']), 0.01)

with st.sidebar.expander("📊 Single-G analysis", expanded=True):
    G_single = st.slider("Irradiance for I-V / loss plots (W/m²)",
                         0, 1200, int(S['G_single']), 25)

with st.sidebar.expander("🔄 Sweep", expanded=False):
    G_min   = st.slider("G min (W/m²)",   0,    500,  int(S['G_min']),   25)
    G_max   = st.slider("G max (W/m²)",   500,  1200, int(S['G_max']), 25)
    G_steps = st.slider("Sweep points",   21,   301,  int(S['G_steps']),  10)

# Persist current values (only writes if anything changed).
_current_state = {
    'I_sc': I_sc, 'V_oc': V_oc, 'N_series': N_series, 'N_parallel': N_parallel,
    'G_ref': G_ref, 'T_cell_C': T_cell_C, 'n_ideality': n_ideality,
    'V_oc_per_cell': V_oc_per_cell, 'N_cells_series': N_cells_series,
    'electrode_area_cm2': electrode_area_cm2, 'M_strings': M_strings,
    'V_onset_cell': V_onset_cell, 'R_ohmic_area': R_ohmic_area,
    'A_tafel': A_tafel, 'j0_mA': j0_mA, 'j_lim_mA': j_lim_mA,
    'B_mt': B_mt, 'faradaic_eff': faradaic_eff,
    'G_single': G_single, 'G_min': G_min, 'G_max': G_max, 'G_steps': G_steps,
}
if _current_state != {k: S.get(k) for k in _current_state}:
    _save_state(_current_state)

# ─── Build config from sidebar values ────────────────────────────────────────
sim = SimConfig(
    solar=SolarConfig(
        I_sc=I_sc, V_oc=V_oc, N_series=N_series, N_parallel=N_parallel,
        G_ref=G_ref, T_cell=T_cell_C + 273.15, n_ideality=n_ideality,
        V_oc_per_cell=V_oc_per_cell,
    ),
    elec=ElectrolyzerConfig(
        N_cells_series=N_cells_series, electrode_area_cm2=electrode_area_cm2,
        M_strings=M_strings, V_onset=V_onset_cell, R_ohmic_area=R_ohmic_area,
        A_tafel=A_tafel, j0=j0_mA / 1000.0, j_lim=j_lim_mA / 1000.0,
        B_mt=B_mt, faradaic_eff=faradaic_eff,
    ),
    sweep=SweepConfig(G_min=G_min, G_max=G_max, G_steps=G_steps),
    G_single=G_single,
)

# ─── Header + key numbers ────────────────────────────────────────────────────
st.title("⚡ Solar-Electrolyzer Direct DC Coupling Simulator")
st.caption(
    f"Array: {sim.solar.cells_per_module} cells/module × "
    f"{sim.solar.N_series}s × {sim.solar.N_parallel}p · "
    f"V_oc_array = {sim.solar.V_oc * sim.solar.N_series:.0f} V · "
    f"I_sc_array = {sim.solar.I_sc * sim.solar.N_parallel:.1f} A    |    "
    f"Bank: {sim.elec.N_cells_series} cells × {sim.elec.M_strings} strings · "
    f"area {sim.elec.electrode_area_cm2:.0f} cm² · "
    f"V_min_bank ≈ {sim.elec.N_cells_series * sim.elec.V_onset:.0f} V"
)

r = evaluate(G_single, sim)
op, mp = r['op'], r['mpp']

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("MPP power (kW)", f"{mp['P']/1000:.2f}")
c2.metric("DC-coupled power (kW)", f"{op['P']/1000:.2f}",
          f"-{r['mpp_gap_pct']:.1f}% gap")
c3.metric("Active stacks", f"{op['n_active']} / {sim.elec.M_strings}")
c4.metric("Cell j (mA/cm²)", f"{op['j']*1000:.0f}",
          f"of j_lim {sim.elec.j_lim*1000:.0f}")
c5.metric("H₂ rate (g/hr)", f"{r['m_h2_g_hr']:.1f}")

# Sizing hint — flag when array is current-starved or current-flooded.
J_TARGET = 0.3   # A/cm² — typical alkaline operating point
I_demand_target = J_TARGET * sim.elec.electrode_area_cm2 * max(op['n_active'], 1)
I_avail = array_iph(G_single, sim.solar)
if I_avail > 0 and op['feasible']:
    ratio = I_avail / I_demand_target
    if ratio < 0.7:
        st.caption(f"💡 **Array is current-starved for j≈300 mA/cm² target.** Available "
                   f"I_ph = {I_avail:.1f} A; demand at j=300 mA/cm² with n={op['n_active']} = "
                   f"{I_demand_target:.0f} A. Increase N_parallel by ≈{I_demand_target/I_avail:.1f}× "
                   f"or shrink electrode area by the same factor to land in the 200–400 mA/cm² band.")
    elif ratio > 2.0:
        st.caption(f"💡 **Array is current-flooded vs j≈300 mA/cm² target.** Available "
                   f"I_ph = {I_avail:.1f} A; demand at j=300 mA/cm² = {I_demand_target:.0f} A. "
                   f"Increase electrode area or activate more stacks to absorb the current.")

# Surprises / observations bar.
notes = []
if not op['feasible']:
    notes.append("⚠️ **Operating point not feasible** — array V_oc is below stack onset; "
                 "no current flows.")
if op['feasible']:
    overs = sorted([('kinetic η_act', r['eta_act']),
                    ('ohmic η_ohm', r['eta_ohm']),
                    ('transport η_mt', r['eta_mt'])],
                   key=lambda x: -x[1])
    notes.append(f"🔍 **Dominant loss:** {overs[0][0]} ({overs[0][1]*1000:.0f} mV/cell). "
                 f"V_cell = {r['V_cell']:.3f} V (onset {sim.elec.V_onset:.2f} + "
                 f"η_act {r['eta_act']:.3f} + η_ohm {r['eta_ohm']:.3f} + η_mt {r['eta_mt']:.3f}).")
    if r['eta_mt'] > 0.5 * (r['eta_act'] + r['eta_ohm']):
        notes.append("⚠️ Mass-transport loss is comparable to kinetic+ohmic — j approaching j_lim.")
    if r['mpp_gap_pct'] > 15:
        notes.append(f"⚠️ MPP gap > 15% at this G — switching granularity is hurting.")
    V_min_bank = sim.elec.N_cells_series * sim.elec.V_onset
    if V_min_bank > mp['V']:
        notes.append(f"⚠️ Bank V_min ({V_min_bank:.0f} V) > MPP V ({mp['V']:.0f} V) — "
                     "stack switching can't help; reduce cells/string or array voltage.")
    # Stacks-underutilized design hint: if optimum sits at one extreme of the
    # M_strings range, the bank is mismatched to the array. Suggest a target
    # cells/string that lands V_min_bank ≈ MPP V (so all stacks engage at G_max).
    if op['n_active'] <= max(1, sim.elec.M_strings // 4) and sim.elec.M_strings >= 4:
        N_target = max(10, round(mp['V'] / sim.elec.V_onset))
        notes.append(
            f"⚠️ Only **{op['n_active']} of {sim.elec.M_strings}** stacks active — "
            f"bank is over-built or array is under-sized. With these defaults the "
            f"other stacks sit idle. To make switching meaningful, set "
            f"`N_cells_series ≈ {N_target}` so V_min_bank ≈ V_mpp ({mp['V']:.0f} V). "
            "All stacks then engage at peak G; switch off as G drops."
        )
    elif op['n_active'] >= sim.elec.M_strings and sim.elec.M_strings >= 2:
        notes.append(
            f"⚠️ All {sim.elec.M_strings} stacks active — bank may be under-built; "
            "no switching headroom remains. Consider more cells/string or more strings."
        )
for n in notes:
    st.markdown(n)

st.divider()

# Pre-compute curves used by I-V and P-V tabs.
V_oc_array = sim.solar.V_oc * sim.solar.N_series
V_grid = np.linspace(0, V_oc_array, 600)
I_grid = np.array([solar_current(V, G_single, sim.solar) for V in V_grid])


def _styled(fig, height=520):
    """Apply theme + sane legend/margins for every chart."""
    fig.update_layout(
        template=TEMPLATE,
        height=height,
        margin=dict(l=60, r=30, t=50, b=50),
        legend=dict(orientation='h', yanchor='bottom', y=1.02,
                    xanchor='left', x=0),
        hovermode='closest',
    )
    return fig


# ─── 1. I-V overlay ──────────────────────────────────────────────────────────
st.subheader("I-V overlay — solar curve vs. stack family")
fig = go.Figure()
fig.add_trace(go.Scatter(x=V_grid, y=I_grid, mode='lines',
                         line=dict(color=SOLAR_LINE, width=3),
                         name=f'Solar @ {G_single} W/m²'))
fig.add_trace(go.Scatter(x=[mp['V']], y=[mp['I']], mode='markers',
                         marker=dict(symbol='star', size=18,
                                     color=ACCENT_HI,
                                     line=dict(color=NEUTRAL, width=1)),
                         name=f"MPP ({mp['P']/1000:.2f} kW)"))

I_string_arr = np.linspace(1e-4,
                           sim.elec.j_lim * sim.elec.electrode_area_cm2 * 0.999, 300)
V_stack_string = np.array([
    sim.elec.N_cells_series * cell_voltage(I/sim.elec.electrode_area_cm2, sim.elec)
    for I in I_string_arr
])
# Viridis-like family, brightened so it stays readable on dark.
# Stack family is suppressed from the legend (too many entries crowd the plot);
# instead we annotate each curve with its n value at the top of the curve.
I_max_y = max(array_iph(G_single, sim.solar) * 1.1, 1)
for n in range(1, sim.elec.M_strings + 1):
    t = (n - 1) / max(sim.elec.M_strings - 1, 1)
    rgb = (
        int(np.clip(70 + 180*t, 0, 255)),
        int(np.clip(180 - 50*t, 0, 255)),
        int(np.clip(220 - 120*t, 0, 255)),
    )
    color = f'rgb{rgb}'
    Y = I_string_arr * n
    fig.add_trace(go.Scatter(
        x=V_stack_string, y=Y, mode='lines',
        line=dict(width=1.3, color=color),
        name=f'{n} stack' + ('s' if n > 1 else ''),
        showlegend=False,
        hovertemplate=f'n={n}<br>V=%{{x:.1f}} V<br>I=%{{y:.2f}} A<extra></extra>',
    ))
    # Label the curve where it exits the visible y-range (or at its top).
    above = np.where(Y >= I_max_y * 0.97)[0]
    if len(above):
        idx = int(above[0])
    else:
        idx = int(np.argmax(Y))
    fig.add_annotation(
        x=V_stack_string[idx], y=Y[idx], text=f'n={n}',
        showarrow=False, xanchor='left', yanchor='bottom',
        xshift=2, yshift=2, font=dict(size=9, color=color),
    )

if op['feasible']:
    fig.add_trace(go.Scatter(
        x=[op['V']], y=[op['I']], mode='markers',
        marker=dict(symbol='circle', size=15, color=ACCENT_OP,
                    line=dict(color='white' if DARK else 'black', width=1.5)),
        name=f"Op point ({op['P']/1000:.2f} kW, n={op['n_active']})",
    ))

fig.update_xaxes(range=[0, V_oc_array * 1.02], title='Terminal Voltage (V)')
fig.update_yaxes(range=[0, I_max_y], title='Current (A)')
# Override _styled defaults: vertical legend on right, no top legend overlap.
fig.update_layout(
    template=TEMPLATE,
    height=560,
    margin=dict(l=60, r=170, t=30, b=50),
    legend=dict(orientation='v', x=1.02, y=1.0,
                xanchor='left', yanchor='top'),
    hovermode='closest',
)
st.plotly_chart(fig, use_container_width=True)


# ─── 2. P-V with MPP and DC op point ─────────────────────────────────────────
st.subheader("P-V curve with MPP and DC op point")
P_grid = V_grid * I_grid / 1000
fig = go.Figure()
fig.add_trace(go.Scatter(x=V_grid, y=P_grid, mode='lines',
                         line=dict(color=SOLAR_LINE, width=2.5), name='P(V)'))
fig.add_trace(go.Scatter(x=[mp['V']], y=[mp['P']/1000], mode='markers',
                         marker=dict(symbol='star', size=18, color=ACCENT_HI,
                                     line=dict(color=NEUTRAL, width=1)),
                         name=f"MPP {mp['P']/1000:.2f} kW @ {mp['V']:.0f} V"))
if op['feasible']:
    fig.add_trace(go.Scatter(
        x=[op['V']], y=[op['P']/1000], mode='markers',
        marker=dict(symbol='circle', size=15, color=ACCENT_OP),
        name=f"DC-coupled {op['P']/1000:.2f} kW @ {op['V']:.0f} V "
             f"(gap {r['mpp_gap_pct']:.1f}%)",
    ))
fig.update_xaxes(title='Terminal Voltage (V)')
fig.update_yaxes(title='Array Power (kW)')
st.plotly_chart(_styled(fig, height=480), use_container_width=True)


# ─── 2b. Solar I-V and P-V at varying G (illustration) ──────────────────────
st.subheader("Solar I-V and P-V at varying irradiance")
st.caption("Family of solar curves at fixed cell temperature. Stars mark MPP at each G. "
           "Note: V_oc shifts only slightly (logarithmically with I_ph), while I_sc scales linearly.")
G_family = np.array([100, 250, 500, 750, 1000, 1200])
G_family = G_family[G_family <= G_max if G_max >= 100 else G_max]
fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.10,
                    subplot_titles=('I-V family', 'P-V family'))
import plotly.express as _px
fam_colors = _px.colors.sequential.Plasma
for i, G in enumerate(G_family):
    color = fam_colors[int((i / max(len(G_family)-1, 1)) * (len(fam_colors)-1))]
    I_arr = np.array([solar_current(V, float(G), sim.solar) for V in V_grid])
    P_arr = V_grid * I_arr / 1000
    mp_G = mpp(float(G), sim.solar)
    fig.add_trace(go.Scatter(x=V_grid, y=I_arr, mode='lines',
                             line=dict(color=color, width=2),
                             name=f'G={G:.0f} W/m²',
                             legendgroup=f'g{i}'), 1, 1)
    fig.add_trace(go.Scatter(x=[mp_G['V']], y=[mp_G['I']], mode='markers',
                             marker=dict(symbol='star', size=12, color=color,
                                         line=dict(color=NEUTRAL, width=1)),
                             showlegend=False, legendgroup=f'g{i}',
                             hovertemplate=f'MPP @ G={G}<br>V=%{{x:.1f}}<br>I=%{{y:.2f}}<extra></extra>'),
                  1, 1)
    fig.add_trace(go.Scatter(x=V_grid, y=P_arr, mode='lines',
                             line=dict(color=color, width=2),
                             showlegend=False, legendgroup=f'g{i}'), 1, 2)
    fig.add_trace(go.Scatter(x=[mp_G['V']], y=[mp_G['P']/1000], mode='markers',
                             marker=dict(symbol='star', size=12, color=color,
                                         line=dict(color=NEUTRAL, width=1)),
                             showlegend=False, legendgroup=f'g{i}',
                             hovertemplate=f'MPP @ G={G}<br>V=%{{x:.1f}}<br>P=%{{y:.2f}} kW<extra></extra>'),
                  1, 2)
fig.update_xaxes(title_text='Terminal Voltage (V)', row=1, col=1)
fig.update_xaxes(title_text='Terminal Voltage (V)', row=1, col=2)
fig.update_yaxes(title_text='Current (A)', row=1, col=1)
fig.update_yaxes(title_text='Power (kW)', row=1, col=2)
fig.update_layout(template=TEMPLATE, height=500,
                  margin=dict(l=60, r=30, t=70, b=50),
                  legend=dict(orientation='h', yanchor='bottom', y=1.10,
                              xanchor='left', x=0))
st.plotly_chart(fig, use_container_width=True)


# ─── 3. Loss breakdown ───────────────────────────────────────────────────────
st.subheader("Cell voltage breakdown at the operating point")
if not op['feasible']:
    st.warning("Operating point not feasible — nothing to break down.")
else:
    labels = ['V_onset (thermo.)', 'η_activation (kinetics)',
              'η_ohmic', 'η_mass-transport']
    values = [sim.elec.V_onset, r['eta_act'], r['eta_ohm'], r['eta_mt']]
    colors = ['#7f7f7f', '#e67e22', '#27ae60', '#9b59b6']
    text = [f'{v:.3f} V<br>({100*v/r["V_cell"]:.0f}%)' for v in values]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors,
                           text=text, textposition='outside'))
    fig.add_hline(y=V_REVERSIBLE, line_dash='dot',
                  line_color='#27ae60' if DARK else '#15803d',
                  annotation_text='V_reversible (1.23 V)',
                  annotation_position='top right')
    fig.add_hline(y=V_THERMONEUTRAL, line_dash='dot',
                  line_color='#f39c12',
                  annotation_text='V_thermoneutral (1.48 V)',
                  annotation_position='bottom right')
    fig.update_yaxes(title='Voltage per cell (V)')
    fig.update_layout(title=f'V_cell = {r["V_cell"]:.3f} V · '
                            f'j = {op["j"]*1000:.0f} mA/cm² · G = {G_single} W/m²')
    st.plotly_chart(_styled(fig, height=480), use_container_width=True)


# ─── Sweep computation (cached on parameter tuple) ───────────────────────────
@st.cache_data(show_spinner=False)
def cached_sweep(_sim_key, G_min, G_max, G_steps,
                 I_sc, V_oc, N_series, N_parallel, G_ref, T_K, n_ideality,
                 V_oc_per_cell, N_cells_series, area, M_strings,
                 V_onset_cell, R_ohmic_area, A_tafel, j0, j_lim, B_mt, F_eff):
    s = SimConfig(
        solar=SolarConfig(I_sc=I_sc, V_oc=V_oc, N_series=N_series, N_parallel=N_parallel,
                          G_ref=G_ref, T_cell=T_K, n_ideality=n_ideality,
                          V_oc_per_cell=V_oc_per_cell),
        elec=ElectrolyzerConfig(N_cells_series=N_cells_series, electrode_area_cm2=area,
                                M_strings=M_strings, V_onset=V_onset_cell,
                                R_ohmic_area=R_ohmic_area, A_tafel=A_tafel,
                                j0=j0, j_lim=j_lim, B_mt=B_mt, faradaic_eff=F_eff),
        sweep=SweepConfig(G_min=G_min, G_max=G_max, G_steps=G_steps),
    )
    return run_sweep(s)

cache_args = (
    'v2-arcsinh', G_min, G_max, G_steps,
    I_sc, V_oc, N_series, N_parallel, G_ref, T_cell_C + 273.15, n_ideality,
    V_oc_per_cell, N_cells_series, electrode_area_cm2, M_strings,
    V_onset_cell, R_ohmic_area, A_tafel, j0_mA/1000, j_lim_mA/1000, B_mt, faradaic_eff,
)
Gs, rows = cached_sweep(*cache_args)

P_op   = np.array([rr['op']['P']  for rr in rows]) / 1000
P_mp   = np.array([rr['mpp']['P'] for rr in rows]) / 1000
gap    = np.array([rr['mpp_gap_pct'] for rr in rows])
n_act  = np.array([rr['op']['n_active'] for rr in rows])
V_op   = np.array([rr['op']['V']  for rr in rows])
I_op   = np.array([rr['op']['I']  for rr in rows])
j_arr  = np.array([rr['op']['j']  for rr in rows]) * 1000
h2     = np.array([rr['m_h2_g_hr'] for rr in rows])
Q_kW   = np.array([rr['Q_total_W'] for rr in rows]) / 1000
eta_a  = np.array([rr['eta_act']  for rr in rows])
eta_o  = np.array([rr['eta_ohm']  for rr in rows])
eta_m  = np.array([rr['eta_mt']   for rr in rows])
over_t = np.where(eta_a + eta_o + eta_m > 1e-6, eta_a + eta_o + eta_m, 1.0)


# ─── 4. Irradiance sweep — 3×3 panel grid ────────────────────────────────────
st.subheader("Irradiance sweep — full output grid")
fig = make_subplots(rows=3, cols=3, shared_xaxes=False,
                    vertical_spacing=0.13, horizontal_spacing=0.10,
                    subplot_titles=(
                        'Power: DC-coupled vs MPP', 'MPP gap',
                        f'Active stacks (M={M_strings})',
                        'Operating voltage', 'Operating current',
                        'Per-cell current density',
                        'H₂ production rate', 'Stack heat generation',
                        'Loss share',
                    ))
fig.add_trace(go.Scatter(x=Gs, y=P_op, name='DC-coupled',
                         line=dict(color=SOLAR_LINE, width=2)), 1, 1)
fig.add_trace(go.Scatter(x=Gs, y=P_mp, name='MPP (ideal)',
                         line=dict(color=NEUTRAL, dash='dash', width=2)), 1, 1)
fig.add_trace(go.Scatter(x=Gs, y=gap, line=dict(color='#ff6b6b', width=2),
                         showlegend=False), 1, 2)
fig.add_trace(go.Scatter(x=Gs, y=n_act,
                         line=dict(color='#a29bfe', shape='hv', width=2),
                         showlegend=False), 1, 3)
fig.add_trace(go.Scatter(x=Gs, y=V_op,
                         line=dict(color='#55efc4', width=2), showlegend=False), 2, 1)
fig.add_trace(go.Scatter(x=Gs, y=I_op,
                         line=dict(color='#55efc4', width=2), showlegend=False), 2, 2)
fig.add_trace(go.Scatter(x=Gs, y=j_arr,
                         line=dict(color='#fdcb6e', width=2), showlegend=False), 2, 3)
fig.add_hline(y=j_lim_mA, line_dash='dot', line_color='#ff6b6b', row=2, col=3)
fig.add_trace(go.Scatter(x=Gs, y=h2,
                         line=dict(color=SOLAR_LINE, width=2), showlegend=False), 3, 1)
fig.add_trace(go.Scatter(x=Gs, y=Q_kW,
                         line=dict(color='#e17055', width=2), showlegend=False), 3, 2)
fig.add_trace(go.Scatter(x=Gs, y=100*eta_a/over_t, name='η_act',
                         line=dict(color='#e67e22', width=2)), 3, 3)
fig.add_trace(go.Scatter(x=Gs, y=100*eta_o/over_t, name='η_ohm',
                         line=dict(color='#27ae60', width=2)), 3, 3)
fig.add_trace(go.Scatter(x=Gs, y=100*eta_m/over_t, name='η_mt',
                         line=dict(color='#9b59b6', width=2)), 3, 3)
# X-axis label on every subplot, Y-axis label with units on every subplot.
y_titles = [
    ['Power (kW)',          'Gap (%)',          'Active stacks (#)'],
    ['Voltage (V)',         'Current (A)',      'j (mA/cm²)'],
    ['H₂ rate (g/hr)',      'Heat (kW)',        '% of overpotential'],
]
for r in (1, 2, 3):
    for c in (1, 2, 3):
        fig.update_xaxes(title_text='G (W/m²)', row=r, col=c)
        fig.update_yaxes(title_text=y_titles[r-1][c-1], row=r, col=c)

fig.update_layout(template=TEMPLATE, height=900, hovermode='x unified',
                  margin=dict(l=60, r=30, t=70, b=50),
                  legend=dict(orientation='h', yanchor='bottom', y=1.04,
                              xanchor='left', x=0))
st.plotly_chart(fig, use_container_width=True)

# Sweep summary numbers.
energy_op  = float(np.trapezoid(P_op,  Gs))
energy_mpp = float(np.trapezoid(P_mp,  Gs))
energy_gap = 100*(energy_mpp - energy_op)/max(energy_mpp, 1e-9)
weights = P_mp / max(P_mp.sum(), 1e-9)
gap_w = float((gap * weights).sum())
switches = int(np.sum(np.diff(n_act) != 0))

s1, s2, s3, s4 = st.columns(4)
s1.metric("Mean MPP gap", f"{gap.mean():.2f} %")
s2.metric("Power-weighted MPP gap", f"{gap_w:.2f} %",
          help="Proxy for the day-integrated energy loss vs. MPPT.")
s3.metric("∫P dG energy lost", f"{energy_gap:.2f} %")
s4.metric("Stack switches across sweep", f"{switches}",
          help=f"Granularity = 1/{M_strings} = {100/M_strings:.0f}%.")

if switches == 0 and len(n_act):
    V_min_bank_arr = N_cells_series * V_onset_cell
    rel = 'below' if V_min_bank_arr < rows[-1]['mpp']['V'] else 'above'
    st.info(
        f"**Optimizer never switches** (n_active = {int(n_act[-1])} for all G). "
        f"Bank V_min ≈ {V_min_bank_arr:.0f} V is already {rel} the MPP voltage "
        f"({rows[-1]['mpp']['V']:.0f} V at G_max). To make switching useful, change "
        "cells/string or array voltage so the bank I-V curve straddles MPP V as G varies."
    )


# ─── 5. Op-point trajectory ──────────────────────────────────────────────────
st.subheader("Op-point trajectory across the irradiance sweep")
st.caption("Each colored dot is the DC-coupled operating point at one G. "
           "Dashed line = MPP locus. Grey curves are solar I-V at sample G values.")
fig = go.Figure()

G_levels = np.linspace(max(G_min, 50), G_max, 6)
for k, G in enumerate(G_levels):
    I_arr = np.array([solar_current(V, G, sim.solar) for V in V_grid])
    fig.add_trace(go.Scatter(
        x=V_grid, y=I_arr, mode='lines',
        line=dict(color=GRID_FAMILY, width=1, dash='solid'),
        opacity=0.35,
        name=f'Solar I-V @ G={G:.0f}',
        showlegend=False,           # too many → suppress; annotate endpoints instead
        hoverinfo='skip',
    ))
    # Annotate G value at right end of each curve, in muted color.
    fig.add_annotation(
        x=V_oc_array * 0.995, y=float(I_arr[-1]),
        text=f"G={G:.0f}",
        showarrow=False, xanchor='right', yanchor='bottom',
        font=dict(size=10, color=GRID_FAMILY),
    )

V_op_arr = np.array([rr['op']['V'] for rr in rows])
I_op_arr = np.array([rr['op']['I'] for rr in rows])
V_mp_arr = np.array([rr['mpp']['V'] for rr in rows])
I_mp_arr = np.array([rr['mpp']['I'] for rr in rows])
fig.add_trace(go.Scatter(
    x=V_op_arr, y=I_op_arr, mode='markers',
    marker=dict(color=Gs, colorscale='Plasma', size=8,
                colorbar=dict(title='G (W/m²)', x=1.02, len=0.85, y=0.5)),
    name='DC-coupled op point',
    hovertemplate='G=%{marker.color:.0f}<br>V=%{x:.1f} V<br>I=%{y:.2f} A<extra></extra>',
))
fig.add_trace(go.Scatter(
    x=V_mp_arr, y=I_mp_arr, mode='lines',
    line=dict(color=ACCENT_HI, dash='dash', width=2),
    name='MPP locus',
))
fig.update_xaxes(range=[0, V_oc_array * 1.02], title='Terminal Voltage (V)')
fig.update_yaxes(title='Current (A)')
fig.update_layout(
    template=TEMPLATE,
    height=620,
    margin=dict(l=60, r=110, t=70, b=50),  # extra right margin for colorbar
    legend=dict(orientation='h', yanchor='bottom', y=1.04,
                xanchor='left', x=0),
)
st.plotly_chart(fig, use_container_width=True)

# ─── 6. Equivalent resistance vs n_active ────────────────────────────────────
st.subheader("Bank equivalent resistance vs. number of active stacks")
st.caption(
    "Switching IN more stacks LOWERS the bank's effective resistance — that's "
    "why more stacks pulls V_op DOWN at a given total current. Left: full "
    "polarization curves V(I) for each n. Right: chord resistance "
    "R_eq = (V_stack − V_min_bank) / I_total at three representative current levels."
)

n_axis = np.arange(1, sim.elec.M_strings + 1)
I_max_bank = sim.elec.j_lim * sim.elec.electrode_area_cm2 * sim.elec.M_strings * 0.999
I_curve = np.linspace(1e-3, I_max_bank, 250)
V_min_bank = sim.elec.N_cells_series * sim.elec.V_onset

fig = make_subplots(
    rows=1, cols=2, horizontal_spacing=0.12,
    subplot_titles=(
        'Stack polarization V(I) for each n',
        'Effective bank resistance vs n',
    ),
)

# Left panel: V_stack vs I_total for each n_active.
I_avail_full = array_iph(G_single, sim.solar)
for n in n_axis:
    t = (n - 1) / max(sim.elec.M_strings - 1, 1)
    rgb = (
        int(np.clip(70 + 180*t, 0, 255)),
        int(np.clip(180 - 50*t, 0, 255)),
        int(np.clip(220 - 120*t, 0, 255)),
    )
    color = f'rgb{rgb}'
    I_lim_n = sim.elec.j_lim * sim.elec.electrode_area_cm2 * n * 0.999
    I_n = I_curve[I_curve <= I_lim_n]
    V_n = np.array([
        sim.elec.N_cells_series * cell_voltage(I/(n*sim.elec.electrode_area_cm2), sim.elec)
        for I in I_n
    ])
    fig.add_trace(go.Scatter(x=I_n, y=V_n, mode='lines',
                             line=dict(color=color, width=1.6),
                             name=f'n={n}', showlegend=False,
                             hovertemplate=f'n={n}<br>I=%{{x:.1f}} A<br>V=%{{y:.1f}} V<extra></extra>'),
                  1, 1)
    # Annotate at the right end of each curve.
    if len(I_n):
        fig.add_annotation(
            x=I_n[-1], y=V_n[-1], text=f'n={n}',
            showarrow=False, xanchor='left', yanchor='middle', xshift=4,
            font=dict(size=9, color=color), row=1, col=1,
        )
fig.add_hline(y=V_min_bank, line_dash='dot',
              line_color='#f6e58d' if DARK else '#b07c00',
              annotation_text=f'V_min_bank = {V_min_bank:.0f} V',
              annotation_position='bottom right', row=1, col=1)
# Vertical line at currently available array current at G_single.
if I_avail_full > 0:
    fig.add_vline(x=I_avail_full, line_dash='dot',
                  line_color=SOLAR_LINE,
                  annotation_text=f'I_ph @ {G_single} W/m² = {I_avail_full:.1f} A',
                  annotation_position='top right', row=1, col=1)

# Right panel: chord resistance vs n at fixed I_total levels.
# Scale levels to whatever current the bank can actually accept across n=1..M:
# R_eq depends on j = I/(n*area), so pick I_total values that are feasible for all n.
I_levels_max_for_all_n = sim.elec.j_lim * sim.elec.electrode_area_cm2 * 1 * 0.95  # n=1
I_levels = [0.25, 0.5, 0.75]
I_levels = [lvl * I_levels_max_for_all_n for lvl in I_levels]
level_colors = ['#74b9ff', '#fdcb6e', '#ff6b6b']
for I_total, lc in zip(I_levels, level_colors):
    R_arr = []
    for n in n_axis:
        j = I_total / (n * sim.elec.electrode_area_cm2)
        if j >= sim.elec.j_lim:
            R_arr.append(np.nan)
            continue
        V_stack = sim.elec.N_cells_series * cell_voltage(j, sim.elec)
        R = (V_stack - V_min_bank) / I_total
        R_arr.append(R)
    fig.add_trace(go.Scatter(
        x=n_axis, y=R_arr, mode='lines+markers',
        line=dict(color=lc, width=2),
        marker=dict(size=8, color=lc),
        name=f'I_total = {I_total:.1f} A '
             f'(j₁ = {1000*I_total/sim.elec.electrode_area_cm2:.0f} mA/cm² @ n=1)',
    ), 1, 2)

fig.update_xaxes(title_text='Total current I_total (A)', row=1, col=1)
fig.update_xaxes(title_text='Number of active stacks (n)', row=1, col=2,
                 tick0=1, dtick=1)
fig.update_yaxes(title_text='Bank terminal voltage (V)', row=1, col=1)
fig.update_yaxes(title_text='R_eq = (V_stack − V_min) / I  (Ω)', row=1, col=2)
fig.update_layout(template=TEMPLATE, height=520,
                  margin=dict(l=60, r=30, t=80, b=50),
                  legend=dict(orientation='h', yanchor='bottom', y=1.10,
                              xanchor='left', x=0))
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "**Reading this:** at n=1 each amp pushes through one string at high j → steep V "
    "rise and high R_eq. At n=10 each amp splits 10 ways → low j per cell → flat V "
    "rise and low R_eq. The blue/yellow/red lines show R_eq drops roughly as 1/n at "
    "moderate currents, with deviations from pure 1/n coming from the Tafel and "
    "mass-transport terms."
)

st.caption("Physics in `sim.py`. UI in `app.py`. Run with `streamlit run app.py`.")
