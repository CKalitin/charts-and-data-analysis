"""
Solar-Electrolyzer Direct DC Coupling Simulator
================================================

Models a PV array directly wired to an alkaline electrolyzer stack (no MPPT,
no DC-DC converter). The operating point is the intersection of the solar
single-diode I-V curve and the stack polarization curve. A discrete number of
parallel stack strings can be switched in to coarsely "track" the array.

The simulator answers four questions:

  1. How much power does direct coupling leave on the table vs. an MPPT?
  2. How well does discrete stack switching (M parallel strings) approximate
     continuous MPP tracking?
  3. Which loss term (kinetic, ohmic, mass-transport) dominates at the
     operating current density, and how does that shift with irradiance?
  4. Where on the I-V curve does the operating point spend most of the day?

Author: Christopher Kalitin, 2026 (well, Claude)
"""

import os
import sys
from dataclasses import dataclass, field, replace as _dc_replace
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq, minimize_scalar

# Windows consoles default to cp1252 and choke on Ω, η, ², etc.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ─── Physical constants ──────────────────────────────────────────────────────
Q_E   = 1.602176634e-19      # C, electron charge
K_B   = 1.380649e-23         # J/K, Boltzmann
F_FAR = 96485.33212          # C/mol, Faraday
V_THERMONEUTRAL = 1.48       # V/cell, thermoneutral (matches default V_onset)
V_REVERSIBLE    = 1.23       # V/cell, reversible water splitting at 25°C

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─── Configuration ───────────────────────────────────────────────────────────
@dataclass
class SolarConfig:
    """Single-diode array model parameters.

    I_sc, V_oc are the rated short-circuit current and open-circuit voltage of
    one module at G_ref. N_series and N_parallel scale to the full array.
    n_ideality is the diode quality factor (1.0 ideal, 1.3 typical c-Si).

    The thermal voltage in the diode equation must scale with the number of
    cells in series, otherwise V_oc >> n*kT/q produces a degenerate (square)
    I-V curve. cells_per_module is auto-inferred from V_oc assuming
    V_oc_per_cell = 0.62 V (typical c-Si) when left as None.
    """
    I_sc: float       = 10.0      # A, per module at G_ref
    V_oc: float       = 500.0     # V, per module at G_ref
    N_series: int     = 1
    N_parallel: int   = 1
    G_ref: float      = 1000.0    # W/m^2
    T_cell: float     = 308.0     # K (35 °C, desert)
    n_ideality: float = 1.3
    cells_per_module: Optional[int] = None
    V_oc_per_cell:    float = 0.62  # V, used to infer cells_per_module

    def __post_init__(self):
        if self.cells_per_module is None:
            self.cells_per_module = max(1, round(self.V_oc / self.V_oc_per_cell))


@dataclass
class ElectrolyzerConfig:
    """Per-cell alkaline polarization parameters and stack topology.

    A "stack" here = one parallel string of N_cells_series cells in series.
    M_strings is the total number of stacks; n_active (0..M_strings) is set
    by stack switching to match the array operating point.

    R_ohmic_area is in Ω·cm² per cell; per-cell ohmic resistance is
    R_ohmic_area / electrode_area_cm².
    """
    N_cells_series:     int   = 200
    electrode_area_cm2: float = 100.0
    M_strings:          int   = 10
    V_onset:            float = 1.48     # V/cell
    R_ohmic_area:       float = 0.2      # Ω·cm²/cell
    A_tafel:            float = 0.06     # V, Butler-Volmer slope
    j0:                 float = 1e-3     # A/cm², exchange current density
    j_lim:              float = 0.8      # A/cm², limiting current density
    B_mt:               float = 0.05     # V, mass-transport prefactor
    faradaic_eff:       float = 1.0      # assumption — flag in outputs


@dataclass
class SweepConfig:
    G_min: float = 0.0
    G_max: float = 1000.0
    G_steps: int = 101


@dataclass
class SimConfig:
    solar:  SolarConfig         = field(default_factory=SolarConfig)
    elec:   ElectrolyzerConfig  = field(default_factory=ElectrolyzerConfig)
    sweep:  SweepConfig         = field(default_factory=SweepConfig)
    G_single: float = 800.0     # W/m^2 used for single-G analysis plots


# ─── Config ↔ flat-dict bridge (shared with the Streamlit app) ───────────────
# app.py's sliders / app_state.json use this same flat key set. Centralized
# here so the raw->SimConfig field mapping (unit conversions included) is
# defined once, not duplicated between the UI and standalone chart scripts.
APP_STATE_FILE = os.path.join(os.path.dirname(__file__), 'app_state.json')


def sim_config_from_dict(d: dict) -> SimConfig:
    """Build a SimConfig from the flat parameter dict used by app.py / app_state.json."""
    return SimConfig(
        solar=SolarConfig(
            I_sc=d['I_sc'], V_oc=d['V_oc'], N_series=d['N_series'], N_parallel=d['N_parallel'],
            G_ref=d['G_ref'], T_cell=d['T_cell_C'] + 273.15, n_ideality=d['n_ideality'],
            V_oc_per_cell=d['V_oc_per_cell'],
        ),
        elec=ElectrolyzerConfig(
            N_cells_series=d['N_cells_series'], electrode_area_cm2=d['electrode_area_cm2'],
            M_strings=d['M_strings'], V_onset=d['V_onset_cell'], R_ohmic_area=d['R_ohmic_area'],
            A_tafel=d['A_tafel'], j0=d['j0_mA'] / 1000.0, j_lim=d['j_lim_mA'] / 1000.0,
            B_mt=d['B_mt'], faradaic_eff=d['faradaic_eff'],
        ),
        sweep=SweepConfig(G_min=d['G_min'], G_max=d['G_max'], G_steps=d['G_steps']),
        G_single=d['G_single'],
    )


def load_website_config(path: str = APP_STATE_FILE) -> SimConfig:
    """Load the Streamlit app's persisted parameter state as a SimConfig.

    Keeps standalone charts in sync with "whatever the website is currently
    configured to" instead of drifting from sim.py's own SimConfig() defaults.
    Falls back to SimConfig() if app_state.json is missing.
    """
    if not os.path.exists(path):
        return SimConfig()
    import json
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    return sim_config_from_dict(d)


# ─── Solar physics (single-diode model) ──────────────────────────────────────
def thermal_voltage(cfg: SolarConfig) -> float:
    """Effective array thermal voltage V_T_eff [V].

    V_T per cell is n*kT/q; the array has cells_per_module*N_series cells in
    series, so the diode-equation voltage scale is V_T_eff = N_cells * V_T.
    """
    n_cells_total = cfg.cells_per_module * cfg.N_series
    return cfg.n_ideality * K_B * cfg.T_cell / Q_E * n_cells_total


def array_iph(G: float, cfg: SolarConfig) -> float:
    """Photocurrent I_ph [A] at irradiance G [W/m^2]."""
    return cfg.I_sc * cfg.N_parallel * (G / cfg.G_ref)


def array_idark(cfg: SolarConfig) -> float:
    """Dark saturation current I_0 [A] derived from V_oc condition.

    At G_ref, V=V_oc_array, I=0  =>  I_ph = I_0 * (exp(V_oc/V_T) - 1)
    """
    V_oc_array = cfg.V_oc * cfg.N_series
    I_ph_ref   = cfg.I_sc * cfg.N_parallel
    return I_ph_ref / (np.exp(V_oc_array / thermal_voltage(cfg)) - 1.0)


def solar_current(V: float, G: float, cfg: SolarConfig) -> float:
    """Array terminal current [A] at terminal voltage V [V] and irradiance G."""
    I_ph = array_iph(G, cfg)
    I_0  = array_idark(cfg)
    V_T  = thermal_voltage(cfg)
    # Clip exponent to avoid overflow far above V_oc (physically I < 0 there).
    exponent = np.clip(V / V_T, -50.0, 50.0)
    return I_ph - I_0 * (np.exp(exponent) - 1.0)


def solar_voltage_for_current(I: float, G: float, cfg: SolarConfig) -> float:
    """Invert solar I(V) for V given I, by bisection on V in [0, V_oc_exact(G)].

    V_oc_exact is the analytic root of solar_current(V, G, cfg) = 0, i.e.
    V_T * ln(I_ph/I_0 + 1). This is used as the upper bracket instead of the
    nameplate V_oc (rated at G_ref) because for G > G_ref the true open-circuit
    voltage rises slightly above nameplate — using the flat nameplate bound
    then leaves no root in [0, V_oc_array] and brentq raises a sign-mismatch
    error. Real irradiance data routinely exceeds G_ref around solar noon.
    """
    I_ph = array_iph(G, cfg)
    I_0  = array_idark(cfg)
    V_T  = thermal_voltage(cfg)
    V_oc_exact = V_T * np.log(I_ph / I_0 + 1.0) if I_ph > 0 else 0.0
    if I <= 0:
        return V_oc_exact
    if I >= I_ph:
        return 0.0
    return brentq(lambda V: solar_current(V, G, cfg) - I, 0.0, V_oc_exact)


# ─── Electrolyzer physics (per-cell polarization) ────────────────────────────
def cell_overpotentials(j: float, cfg: ElectrolyzerConfig):
    """Return (eta_act, eta_ohm, eta_mt) in volts at current density j [A/cm^2].

    eta_act = A * arcsinh(j / (2*j0))   Butler-Volmer (smooth through j=0)
                                        Reduces to A*j/(2*j0) for j << j0
                                        and to A*ln(j/j0) for j >> j0 (Tafel)
    eta_ohm = j * R_ohmic_area          ohmic in cell + electrolyte
    eta_mt  = -B * ln(1 - j / j_lim)    classical mass-transport divergence
    """
    eta_act = cfg.A_tafel * np.arcsinh(max(j, 0.0) / (2.0 * cfg.j0))
    eta_ohm = j * cfg.R_ohmic_area
    if j >= cfg.j_lim:
        eta_mt = 5.0   # cap to keep solver bounded
    else:
        eta_mt = -cfg.B_mt * np.log(1.0 - j / cfg.j_lim)
    return eta_act, eta_ohm, eta_mt


def cell_voltage(j: float, cfg: ElectrolyzerConfig) -> float:
    """Per-cell terminal voltage [V] at current density j [A/cm^2]."""
    eta_act, eta_ohm, eta_mt = cell_overpotentials(j, cfg)
    return cfg.V_onset + eta_act + eta_ohm + eta_mt


def stack_voltage(I_total: float, n_active: int, cfg: ElectrolyzerConfig) -> float:
    """Terminal voltage [V] of the bank with n_active parallel strings drawing I_total.

    Returns +infinity if n_active == 0 (open circuit — no current can flow).
    """
    if n_active <= 0:
        return np.inf
    I_string = I_total / n_active
    j = I_string / cfg.electrode_area_cm2
    return cfg.N_cells_series * cell_voltage(j, cfg)


# ─── Operating-point solver ──────────────────────────────────────────────────
def operating_point(G: float, n_active: int, sim: SimConfig):
    """Find DC-coupled operating point for n_active parallel stacks.

    Solves f(I_total) = V_solar(I_total) - V_stack(I_total, n_active) = 0
    by bisection on I_total in [eps, I_max].

    Returns dict with V, I, P, j_per_cell (current density per cell).
    Returns zero-power dict if no positive-power intersection exists
    (e.g. n_active=0, or array can't push past V_onset of the bank).
    """
    if n_active <= 0:
        return {'V': 0.0, 'I': 0.0, 'P': 0.0, 'j': 0.0, 'feasible': False}

    I_ph = array_iph(G, sim.solar)
    if I_ph <= 0:
        return {'V': 0.0, 'I': 0.0, 'P': 0.0, 'j': 0.0, 'feasible': False}

    # Upper bound on current is the smaller of array I_sc and stack I_lim sum.
    I_max_stack = sim.elec.j_lim * sim.elec.electrode_area_cm2 * n_active * 0.999
    I_hi = min(I_ph * 0.999, I_max_stack)

    def f(I):
        return solar_voltage_for_current(I, G, sim.solar) - stack_voltage(I, n_active, sim.elec)

    # f(0+) = V_oc_array - N_cells*V_onset; positive if array can push the bank.
    # f(I_hi) is large negative (stack voltage diverges near j_lim or V_solar -> 0).
    eps = 1e-6
    f_lo = f(eps)
    f_hi = f(I_hi)
    if f_lo <= 0:
        # Array open-circuit voltage is below stack onset → no current flows.
        return {'V': sim.solar.V_oc * sim.solar.N_series, 'I': 0.0, 'P': 0.0,
                'j': 0.0, 'feasible': False}
    if f_hi >= 0:
        # Stack voltage never catches up — operating point is at I_hi (clipped).
        I_op = I_hi
    else:
        I_op = brentq(f, eps, I_hi)

    V_op = solar_voltage_for_current(I_op, G, sim.solar)
    j    = (I_op / n_active) / sim.elec.electrode_area_cm2
    return {'V': V_op, 'I': I_op, 'P': V_op * I_op, 'j': j, 'feasible': True}


def best_operating_point(G: float, sim: SimConfig):
    """Sweep n_active = 1..M_strings; pick the count that maximizes power."""
    best = {'V': 0.0, 'I': 0.0, 'P': -1.0, 'j': 0.0, 'n_active': 0, 'feasible': False}
    for n in range(1, sim.elec.M_strings + 1):
        op = operating_point(G, n, sim)
        if op['P'] > best['P']:
            best = {**op, 'n_active': n}
    if best['P'] < 0:
        best['P'] = 0.0
    return best


def mpp(G: float, cfg: SolarConfig):
    """Maximum power point of solar array at irradiance G."""
    V_oc_array = cfg.V_oc * cfg.N_series
    if G <= 0:
        return {'V': 0.0, 'I': 0.0, 'P': 0.0}
    res = minimize_scalar(
        lambda V: -V * solar_current(V, G, cfg),
        bounds=(1e-6, V_oc_array * 0.9999),
        method='bounded',
        options={'xatol': 1e-4},
    )
    V_mpp = float(res.x)
    I_mpp = float(solar_current(V_mpp, G, cfg))
    return {'V': V_mpp, 'I': I_mpp, 'P': V_mpp * I_mpp}


# ─── Outputs at an operating point ───────────────────────────────────────────
def evaluate(G: float, sim: SimConfig):
    """Compute everything we report at one irradiance."""
    op   = best_operating_point(G, sim)
    mp   = mpp(G, sim.solar)

    # Per-cell quantities at the operating point.
    j = op['j']
    if op['feasible'] and op['I'] > 0:
        eta_act, eta_ohm, eta_mt = cell_overpotentials(j, sim.elec)
        V_cell = sim.elec.V_onset + eta_act + eta_ohm + eta_mt
        I_string = op['I'] / op['n_active']
    else:
        eta_act = eta_ohm = eta_mt = 0.0
        V_cell  = 0.0
        I_string = 0.0

    # H2 production: one mole H2 per 2 e- per cell. Total e-/s = I_string/Q_E
    # per cell; multiply by N_cells_series (series) and n_active (parallel)
    # cells producing H2. Series cells share the same current → each produces
    # H2 at the same rate; total cells contributing = N_cells_series * n_active.
    n_cells_total = sim.elec.N_cells_series * op['n_active']
    n_h2_mol_s = (I_string / (2.0 * F_FAR)) * n_cells_total * sim.elec.faradaic_eff
    m_h2_g_hr  = n_h2_mol_s * 2.016 * 3600.0  # H2 molar mass 2.016 g/mol

    # Heat: any cell voltage above the thermoneutral 1.48 V is dissipated as
    # heat (above 1.23 V is "extra electrical work that becomes heat"; >1.48 V
    # is net heat generation including the entropy term). Spec asks for
    # (V_cell - V_reversible) * I_cell summed over all cells — we honor that.
    Q_per_cell_W = max(V_cell - V_REVERSIBLE, 0.0) * I_string
    Q_total_W    = Q_per_cell_W * n_cells_total

    mpp_gap_pct = 100.0 * (mp['P'] - op['P']) / mp['P'] if mp['P'] > 0 else 0.0

    return {
        'G': G,
        'op': op,
        'mpp': mp,
        'V_cell': V_cell,
        'eta_act': eta_act,
        'eta_ohm': eta_ohm,
        'eta_mt':  eta_mt,
        'I_string': I_string,
        'n_h2_mol_s': n_h2_mol_s,
        'm_h2_g_hr':  m_h2_g_hr,
        'Q_total_W':  Q_total_W,
        'mpp_gap_pct': mpp_gap_pct,
    }


# ─── Plotting ────────────────────────────────────────────────────────────────
def _save(fig, name, subdir: str = ''):
    """Save under OUTPUT_DIR/<subdir>/<name> — subdir groups charts by type so
    results/ stays navigable as the number of chart families grows.
    """
    out_dir = os.path.join(OUTPUT_DIR, subdir) if subdir else OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    fig.savefig(path, dpi=140, bbox_inches='tight')
    print(f"  saved {os.path.relpath(path)}")


def plot_iv_overlay(G: float, sim: SimConfig):
    """Solar I-V at G, plus stack I-V curves for each n_active, with op point."""
    V_oc_array = sim.solar.V_oc * sim.solar.N_series
    V_arr = np.linspace(0, V_oc_array, 600)
    I_arr = np.array([solar_current(V, G, sim.solar) for V in V_arr])

    # Stack I-V: parameterize by per-string current.
    I_string_arr = np.linspace(1e-4,
                               sim.elec.j_lim * sim.elec.electrode_area_cm2 * 0.999,
                               400)
    V_stack_string = np.array([
        sim.elec.N_cells_series * cell_voltage(I/sim.elec.electrode_area_cm2, sim.elec)
        for I in I_string_arr
    ])

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(V_arr, I_arr, 'k-', lw=2.2, label=f'Solar array @ {G:.0f} W/m²')

    # Mark MPP.
    mp = mpp(G, sim.solar)
    ax.plot(mp['V'], mp['I'], 'k*', ms=14, label=f"MPP ({mp['P']/1000:.2f} kW)")

    cmap = plt.get_cmap('viridis')
    for n in range(1, sim.elec.M_strings + 1):
        I_total = I_string_arr * n
        ax.plot(V_stack_string, I_total, color=cmap(n / sim.elec.M_strings),
                lw=1.2, alpha=0.85,
                label=f'{n} stack' + ('s' if n > 1 else ''))

    best = best_operating_point(G, sim)
    if best['feasible']:
        ax.plot(best['V'], best['I'], 'ro', ms=11,
                label=f"Operating point ({best['P']/1000:.2f} kW, n={best['n_active']})")

    ax.set_xlabel('Terminal Voltage (V)')
    ax.set_ylabel('Current (A)')
    ax.set_title(f'Solar + Electrolyzer I-V curves at G = {G:.0f} W/m²')
    ax.set_xlim(0, V_oc_array * 1.02)
    ax.set_ylim(0, max(array_iph(G, sim.solar) * 1.1, 1))
    ax.grid(alpha=0.3)
    ax.legend(loc='lower left', fontsize=8, ncol=2)
    fig.tight_layout()
    _save(fig, f'iv_overlay_G{int(G)}.png', subdir='general')
    plt.close(fig)


def plot_pv_with_mpp(G: float, sim: SimConfig):
    """Solar P-V curve with MPP and DC-coupled operating point marked."""
    V_oc_array = sim.solar.V_oc * sim.solar.N_series
    V_arr = np.linspace(0, V_oc_array, 800)
    I_arr = np.array([solar_current(V, G, sim.solar) for V in V_arr])
    P_arr = V_arr * I_arr

    mp   = mpp(G, sim.solar)
    best = best_operating_point(G, sim)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(V_arr, P_arr/1000, 'b-', lw=2)
    ax.plot(mp['V'], mp['P']/1000, 'k*', ms=14,
            label=f"MPP: {mp['P']/1000:.2f} kW @ {mp['V']:.0f} V")
    if best['feasible']:
        gap = 100*(mp['P'] - best['P'])/mp['P']
        ax.plot(best['V'], best['P']/1000, 'ro', ms=11,
                label=f"DC-coupled: {best['P']/1000:.2f} kW @ {best['V']:.0f} V "
                      f"(gap {gap:.1f}%)")
    ax.set_xlabel('Terminal Voltage (V)')
    ax.set_ylabel('Array Power (kW)')
    ax.set_title(f'Solar P-V curve at G = {G:.0f} W/m²')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=10)
    fig.tight_layout()
    _save(fig, f'pv_mpp_G{int(G)}.png', subdir='general')
    plt.close(fig)


def plot_loss_breakdown(G: float, sim: SimConfig):
    """Stacked-bar voltage breakdown per cell at the operating point."""
    r = evaluate(G, sim)
    if not r['op']['feasible']:
        print("  loss breakdown skipped (operating point not feasible)")
        return

    parts  = [sim.elec.V_onset, r['eta_act'], r['eta_ohm'], r['eta_mt']]
    labels = ['V_onset\n(thermo.)', 'η_activation\n(kinetics)',
              'η_ohmic\n(R)', 'η_mass_transport\n(transport)']
    colors = ['#888', '#d95f02', '#1b9e77', '#7570b3']

    fig, ax = plt.subplots(figsize=(8, 5.5))
    bars = ax.bar(labels, parts, color=colors, edgecolor='k')
    for b, v in zip(bars, parts):
        ax.text(b.get_x() + b.get_width()/2, v + 0.005,
                f'{v:.3f} V\n({v/r["V_cell"]*100:.0f}%)',
                ha='center', va='bottom', fontsize=9)
    ax.set_ylabel('Voltage contribution per cell (V)')
    ax.set_title(
        f'Cell voltage breakdown at G = {G:.0f} W/m²\n'
        f'V_cell = {r["V_cell"]:.3f} V, j = {r["op"]["j"]*1000:.0f} mA/cm² '
        f'(j_lim = {sim.elec.j_lim*1000:.0f}), n_active = {r["op"]["n_active"]}'
    )
    ax.set_ylim(0, max(parts) * 1.25)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    _save(fig, f'loss_breakdown_G{int(G)}.png', subdir='general')
    plt.close(fig)


def run_sweep(sim: SimConfig):
    """Evaluate over G_min..G_max and return arrays for plotting."""
    Gs = np.linspace(sim.sweep.G_min, sim.sweep.G_max, sim.sweep.G_steps)
    rows = [evaluate(G, sim) for G in Gs]
    return Gs, rows


def plot_sweep(sim: SimConfig):
    Gs, rows = run_sweep(sim)
    V        = np.array([r['op']['V']        for r in rows])
    I        = np.array([r['op']['I']        for r in rows])
    P        = np.array([r['op']['P']        for r in rows]) / 1000  # kW
    P_mpp    = np.array([r['mpp']['P']       for r in rows]) / 1000
    n_act    = np.array([r['op']['n_active'] for r in rows])
    gap      = np.array([r['mpp_gap_pct']    for r in rows])
    h2_g_hr  = np.array([r['m_h2_g_hr']      for r in rows])
    Q_kW     = np.array([r['Q_total_W']      for r in rows]) / 1000
    j        = np.array([r['op']['j']*1000   for r in rows])  # mA/cm²

    fig, axes = plt.subplots(3, 3, figsize=(16, 11))

    ax = axes[0,0]
    ax.plot(Gs, P,     'b-', lw=2, label='DC-coupled')
    ax.plot(Gs, P_mpp, 'k--', lw=1.5, label='MPP (ideal)')
    ax.set_ylabel('Power (kW)'); ax.set_title('Power: DC-coupled vs MPP')
    ax.legend(); ax.grid(alpha=0.3)

    ax = axes[0,1]
    ax.plot(Gs, gap, 'r-', lw=2)
    ax.set_ylabel('MPP gap (%)'); ax.set_title('Energy left on the table')
    ax.grid(alpha=0.3)

    ax = axes[0,2]
    ax.step(Gs, n_act, where='post', color='purple', lw=2)
    ax.set_ylabel('Active stacks (#)')
    ax.set_title(f'Stack switching (M={sim.elec.M_strings})')
    ax.set_yticks(range(0, sim.elec.M_strings + 1))
    ax.grid(alpha=0.3)

    ax = axes[1,0]
    ax.plot(Gs, V, 'g-', lw=2)
    ax.set_ylabel('Terminal V (V)'); ax.set_title('Operating voltage')
    ax.grid(alpha=0.3)

    ax = axes[1,1]
    ax.plot(Gs, I, 'g-', lw=2)
    ax.set_ylabel('Terminal I (A)'); ax.set_title('Operating current')
    ax.grid(alpha=0.3)

    ax = axes[1,2]
    ax.plot(Gs, j, color='darkorange', lw=2)
    ax.axhline(sim.elec.j_lim*1000, color='r', ls=':', label='j_lim')
    ax.set_ylabel('Cell j (mA/cm²)'); ax.set_title('Per-cell current density')
    ax.legend(); ax.grid(alpha=0.3)

    ax = axes[2,0]
    ax.plot(Gs, h2_g_hr, 'b-', lw=2)
    ax.set_ylabel('H₂ (g/hr)'); ax.set_xlabel('G (W/m²)')
    ax.set_title('Hydrogen production rate')
    ax.grid(alpha=0.3)

    ax = axes[2,1]
    ax.plot(Gs, Q_kW, color='firebrick', lw=2)
    ax.set_ylabel('Heat (kW)'); ax.set_xlabel('G (W/m²)')
    ax.set_title('Stack heat generation')
    ax.grid(alpha=0.3)

    # Loss-fraction trajectory — which loss dominates as G varies.
    ax = axes[2,2]
    eta_act_arr = np.array([r['eta_act'] for r in rows])
    eta_ohm_arr = np.array([r['eta_ohm'] for r in rows])
    eta_mt_arr  = np.array([r['eta_mt']  for r in rows])
    over_total  = eta_act_arr + eta_ohm_arr + eta_mt_arr
    safe = np.where(over_total > 1e-6, over_total, 1.0)
    ax.plot(Gs, 100*eta_act_arr/safe, label='η_act',  color='#d95f02', lw=2)
    ax.plot(Gs, 100*eta_ohm_arr/safe, label='η_ohm',  color='#1b9e77', lw=2)
    ax.plot(Gs, 100*eta_mt_arr/safe,  label='η_mt',   color='#7570b3', lw=2)
    ax.set_ylabel('% of overpotential'); ax.set_xlabel('G (W/m²)')
    ax.set_title('Which loss dominates?')
    ax.legend(); ax.grid(alpha=0.3)

    for ax in axes[:2].flat:
        ax.set_xlabel('G (W/m²)')

    fig.suptitle('Solar-Electrolyzer DC Coupling — Irradiance Sweep',
                 fontsize=14, y=1.00)
    fig.tight_layout()
    _save(fig, 'sweep_overview.png', subdir='general')
    plt.close(fig)

    return Gs, rows


def plot_op_trajectory(Gs, rows, sim: SimConfig):
    """Trace the operating point across the family of solar I-V curves.

    Shows where the op point lives across the day and how stack-switching
    discontinuities push it back toward MPP.
    """
    V_oc_array = sim.solar.V_oc * sim.solar.N_series
    V_arr = np.linspace(0, V_oc_array, 400)

    fig, ax = plt.subplots(figsize=(10, 6.5))
    G_levels = np.linspace(100, sim.solar.G_ref, 6)
    cmap_iv = plt.get_cmap('Greys')
    for k, G in enumerate(G_levels):
        I_arr = np.array([solar_current(V, G, sim.solar) for V in V_arr])
        ax.plot(V_arr, I_arr, color=cmap_iv(0.3 + 0.6*k/len(G_levels)),
                lw=1, alpha=0.7,
                label=f'I-V @ G={G:.0f}' if k in (0, len(G_levels)-1) else None)

    V_op = np.array([r['op']['V'] for r in rows])
    I_op = np.array([r['op']['I'] for r in rows])
    V_mp = np.array([r['mpp']['V'] for r in rows])
    I_mp = np.array([r['mpp']['I'] for r in rows])

    sc = ax.scatter(V_op, I_op, c=Gs, cmap='plasma', s=18,
                    label='DC-coupled op point', zorder=5)
    ax.plot(V_mp, I_mp, 'k--', lw=1.2, alpha=0.7, label='MPP locus')
    plt.colorbar(sc, ax=ax, label='G (W/m²)')

    ax.set_xlabel('Terminal Voltage (V)')
    ax.set_ylabel('Current (A)')
    ax.set_title('Operating-point trajectory across irradiance sweep')
    ax.set_xlim(0, V_oc_array * 1.02)
    ax.set_ylim(0, max(I_op.max(), I_mp.max()) * 1.15)
    ax.grid(alpha=0.3); ax.legend(loc='lower left', fontsize=9)
    fig.tight_layout()
    _save(fig, 'op_trajectory.png', subdir='general')
    plt.close(fig)


def _draw_control_dashboard(x, xlabel, rows, sim: SimConfig, suptitle: str,
                             sub2_note: str = ""):
    """Shared three-panel control-algorithm dashboard, parameterized by x-axis.

    (1) DC-coupled operating point: Power / Voltage / Current on a triple y-axis.
    (2) Active-stack count — the control decision (stack switching).
    (3) MPP-tracking efficiency: raw (P_op/P_mpp, %) vs current-weighted
        (I_op * P_op/P_mpp, A) — the latter collapses toward zero whenever
        current is low even when raw tracking is excellent, since it's
        dominated by the shrinking current term rather than tracking quality.

    Used both for the synthetic G-sweep (x = irradiance) and for a measured
    diurnal irradiance profile (x = time of day) — same physics, same
    figure-of-merit, different independent variable.

    Returns (fig, eta_pct, cw_eff) so callers can add their own intuition prints.
    """
    P     = np.array([r['op']['P'] for r in rows]) / 1000.0  # kW
    V     = np.array([r['op']['V'] for r in rows])
    I     = np.array([r['op']['I'] for r in rows])
    n_act = np.array([r['op']['n_active'] for r in rows])
    P_op_w = np.array([r['op']['P']  for r in rows])
    P_mpp  = np.array([r['mpp']['P'] for r in rows])

    eta_frac = np.divide(P_op_w, P_mpp, out=np.zeros_like(P_op_w), where=P_mpp > 1e-9)
    eta_pct  = eta_frac * 100.0
    cw_eff   = I * eta_frac  # A

    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

    # Panel 1: P, V, I triple-axis.
    ax1 = axes[0]
    ax2 = ax1.twinx()
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))

    l1, = ax1.plot(x, P, color='tab:blue',   lw=2, label='Power (kW)')
    l2, = ax2.plot(x, V, color='tab:green',  lw=2, label='Voltage (V)')
    l3, = ax3.plot(x, I, color='tab:orange', lw=2, label='Current (A)')

    ax1.set_ylabel('Power (kW)',   color='tab:blue')
    ax2.set_ylabel('Voltage (V)',  color='tab:green')
    ax3.set_ylabel('Current (A)',  color='tab:orange')
    ax1.tick_params(axis='y', colors='tab:blue')
    ax2.tick_params(axis='y', colors='tab:green')
    ax3.tick_params(axis='y', colors='tab:orange')
    ax1.set_title('DC-coupled operating point: Power / Voltage / Current')
    ax1.grid(alpha=0.3)
    ax1.legend([l1, l2, l3], [l.get_label() for l in (l1, l2, l3)],
               loc='upper left', fontsize=9)

    # Panel 2: active stacks — the control decision.
    ax = axes[1]
    ax.step(x, n_act, where='post', color='purple', lw=2)
    ax.set_ylabel('Active stacks (#)')
    title2 = f'Stack-switching control decision (M = {sim.elec.M_strings})'
    ax.set_title(title2 + (f' — {sub2_note}' if sub2_note else ''))
    ax.set_yticks(range(0, sim.elec.M_strings + 1))
    ax.grid(alpha=0.3)

    # Panel 3: raw vs current-weighted efficiency.
    ax  = axes[2]
    axb = ax.twinx()
    l1, = ax.plot(x, eta_pct, color='black',   lw=2, ls='--',
                  label='Raw MPP efficiency (%)')
    l2, = axb.plot(x, cw_eff, color='crimson', lw=2,
                   label='Current-weighted efficiency (A) = I × P/P_mpp')
    ax.set_ylabel('Raw MPP efficiency (%)')
    axb.set_ylabel('Current-weighted efficiency (A)', color='crimson')
    axb.tick_params(axis='y', colors='crimson')
    ax.set_ylim(0, 105)
    ax.set_xlabel(xlabel)
    ax.set_title('MPP-tracking efficiency: raw vs current-weighted')
    ax.grid(alpha=0.3)
    h1, lab1 = ax.get_legend_handles_labels()
    h2, lab2 = axb.get_legend_handles_labels()
    ax.legend(h1 + h2, lab1 + lab2, loc='lower right', fontsize=9)

    fig.suptitle(suptitle, fontsize=14, y=1.00)
    fig.tight_layout()

    return fig, eta_pct, cw_eff


def _report_cw_eff_collapse(x, x_fmt, eta_pct, cw_eff):
    """Print a note if current-weighted efficiency collapses despite good raw tracking."""
    mid = eta_pct > 50.0
    if mid.any() and cw_eff[mid].min() < 0.05 * cw_eff.max():
        x_at_min = x[mid][np.argmin(cw_eff[mid])]
        print(f"  >> Note: current-weighted efficiency drops near-zero at {x_fmt(x_at_min)} "
              f"even though raw MPP efficiency stays >50% there — it's tracking current, not "
              f"tracking quality.")


def plot_control_dashboard(Gs, rows, sim: SimConfig):
    """Control-algorithm dashboard across the synthetic irradiance sweep."""
    fig, eta_pct, cw_eff = _draw_control_dashboard(
        Gs, 'Irradiance G (W/m²)', rows, sim,
        'Solar-Electrolyzer DC Coupling — Control Algorithm Overview')
    _save(fig, 'control_dashboard.png', subdir='control_dashboard')
    plt.close(fig)
    _report_cw_eff_collapse(Gs, lambda g: f"G≈{g:.0f} W/m²", eta_pct, cw_eff)


def load_irradiance_profile(csv_path: str):
    """Load a measured diurnal profile: columns time_hours, G_W_m2, T_amb_C."""
    data = np.genfromtxt(csv_path, delimiter=',', names=True)
    return data['time_hours'], data['G_W_m2'], data['T_amb_C']


def plot_control_dashboard_timeseries(csv_path: str, sim: SimConfig):
    """Control-algorithm dashboard driven by a measured G(t) irradiance profile.

    Ambient temperature from the CSV is loaded but not fed into the model —
    sim.py's solar/electrolyzer physics run at the configured fixed T_cell,
    so this is irradiance-only fidelity, not a full thermal simulation.
    """
    t_hr, G_arr, T_amb = load_irradiance_profile(csv_path)
    rows = [evaluate(float(G), sim) for G in G_arr]

    csv_name = os.path.basename(csv_path)
    fig, eta_pct, cw_eff = _draw_control_dashboard(
        t_hr, 'Time of day (hr)', rows, sim,
        f'Solar-Electrolyzer DC Coupling — Control Algorithm vs. Time of Day\n'
        f'({csv_name}, G_peak={G_arr.max():.0f} W/m², T_amb {T_amb.min():.0f}–{T_amb.max():.0f} °C)',
        sub2_note='vs. time of day')
    _save(fig, f'control_dashboard_timeseries_{os.path.splitext(csv_name)[0]}.png',
          subdir='control_dashboard')
    plt.close(fig)
    _report_cw_eff_collapse(t_hr, lambda h: f"t≈{h:.1f} hr", eta_pct, cw_eff)


def plot_iv_trajectory_timeseries(csv_path: str, sim: SimConfig, M_strings: int = 1000):
    """Operating-point trajectory across a time-of-day irradiance profile, laid
    over the family of solar I-V curves — the time-driven counterpart to
    plot_op_trajectory. Run through the auto-switching control algorithm with
    an oversized bank (M_strings) so the controller has fine-grained room to
    track MPP across the whole profile.
    """
    t_hr, G_arr, _T_amb = load_irradiance_profile(csv_path)
    sim_big = _dc_replace(sim, elec=_dc_replace(sim.elec, M_strings=M_strings))
    rows = [evaluate(float(G), sim_big) for G in G_arr]

    V_oc_array = sim.solar.V_oc * sim.solar.N_series
    V_arr = np.linspace(0, V_oc_array, 400)

    fig, ax = plt.subplots(figsize=(10, 6.5))
    G_levels = np.linspace(max(G_arr.max() * 0.1, 1.0), G_arr.max(), 6)
    cmap_iv = plt.get_cmap('Greys')
    for k, G in enumerate(G_levels):
        I_arr = np.array([solar_current(V, G, sim.solar) for V in V_arr])
        ax.plot(V_arr, I_arr, color=cmap_iv(0.3 + 0.6 * k / len(G_levels)),
                lw=1, alpha=0.7,
                label=f'I-V @ G={G:.0f}' if k in (0, len(G_levels) - 1) else None)

    V_op = np.array([r['op']['V'] for r in rows])
    I_op = np.array([r['op']['I'] for r in rows])
    V_mp = np.array([r['mpp']['V'] for r in rows])
    I_mp = np.array([r['mpp']['I'] for r in rows])
    P_op = np.array([r['op']['P'] for r in rows])
    P_mp = np.array([r['mpp']['P'] for r in rows])

    # Hard voltage floor set by cells IN SERIES — no number of parallel strings
    # can push the bank below this, since per-string voltage only approaches it
    # (never crosses below) as current density -> 0. Whenever the array's true
    # MPP voltage sits below this floor, the coupled system clamps here instead
    # and loses real power, regardless of M_strings.
    V_floor = sim.elec.N_cells_series * sim.elec.V_onset

    sc = ax.scatter(V_op, I_op, c=t_hr, cmap='plasma', s=18,
                    label=f'Op point (control algo, M_strings={M_strings})', zorder=5)
    ax.plot(V_mp, I_mp, 'k--', lw=1.2, alpha=0.7, label='MPP locus')
    ax.axvline(V_floor, color='crimson', ls=':', lw=1.5,
               label=f'Bank onset floor ({V_floor:.0f} V = {sim.elec.N_cells_series} cells × '
                     f'{sim.elec.V_onset:.2f} V)')
    plt.colorbar(sc, ax=ax, label='Time of day (hr)')

    csv_name = os.path.basename(csv_path)
    ax.set_xlabel('Terminal Voltage (V)')
    ax.set_ylabel('Current (A)')
    ax.set_title(f'Operating-point trajectory vs. time of day ({csv_name})\n'
                 f'control algorithm, n = {M_strings} (auto-switching)')
    ax.set_xlim(0, V_oc_array * 1.02)
    ax.set_ylim(0, max(I_op.max(), I_mp.max()) * 1.15)
    ax.grid(alpha=0.3); ax.legend(loc='lower left', fontsize=8)
    fig.tight_layout()
    stem = os.path.splitext(csv_name)[0]
    _save(fig, f'iv_trajectory_vs_time_n{M_strings}_{stem}.png', subdir='sweeps')
    plt.close(fig)

    # Surface the floor-clamping loss even though it's visible on the chart —
    # printed numbers are what actually get noticed (see other _report_* calls).
    clamped = (V_mp < V_floor) & (P_mp > 1e-9)
    if clamped.any():
        loss_pct = 100.0 * (P_mp[clamped] - P_op[clamped]) / P_mp[clamped]
        g_clamped = G_arr[clamped]
        worst = np.argmax(loss_pct)
        print(f"  >> Note: for G below ~{g_clamped.max():.0f} W/m² the array's true MPP voltage "
              f"sits below the bank's {V_floor:.0f} V onset floor ({sim.elec.N_cells_series} "
              f"cells/string × {sim.elec.V_onset:.2f} V) — the coupled system clamps there instead "
              f"of tracking MPP, losing up to {loss_pct[worst]:.0f}% of available power at "
              f"G={g_clamped[worst]:.0f} W/m². Adding strings (even up to M_strings={M_strings}) "
              f"cannot fix this — the floor is set by cells in series, not parallel count.")


def plot_efficiency_vs_current(Gs, rows, sim: SimConfig):
    """Raw MPP-tracking efficiency vs. operating current for the auto-switching
    control algorithm (the case we have — best_operating_point picks n_active).
    """
    I      = np.array([r['op']['I']  for r in rows])
    P_op   = np.array([r['op']['P']  for r in rows])
    P_mpp  = np.array([r['mpp']['P'] for r in rows])
    eta_pct = np.divide(P_op, P_mpp, out=np.zeros_like(P_op), where=P_mpp > 1e-9) * 100.0

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(I, eta_pct, '-', color='gray', lw=1, alpha=0.6, zorder=1)
    sc = ax.scatter(I, eta_pct, c=Gs, cmap='plasma', s=22, zorder=2)
    plt.colorbar(sc, ax=ax, label='G (W/m²)')
    ax.set_xlabel('Current I (A)')
    ax.set_ylabel('Raw MPP efficiency (%)')
    ax.set_title('MPP-tracking efficiency vs. operating current\n'
                 f'DC-coupled control algorithm ({sim.elec.M_strings} electrolyzers, auto-switching)')
    ax.set_ylim(0, 105)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    _save(fig, 'efficiency_vs_current.png', subdir='sweeps')
    plt.close(fig)


def _op_for_n(G: float, n: int, sim: SimConfig, control_algo: bool):
    """Operating point at n electrolyzers: FIXED (no switching, n always active)
    unless control_algo=True, in which case n is the bank size M_strings and
    the auto-switching algorithm picks how many of those n to activate.
    """
    if control_algo:
        sim_n = _dc_replace(sim, elec=_dc_replace(sim.elec, M_strings=n))
        return best_operating_point(G, sim_n)
    return operating_point(G, n, sim)


def run_constant_n_sweep(n_values, sim: SimConfig, control_algo_n=()):
    """Sweep G for each n in n_values.

    n in control_algo_n is treated as a bank SIZE run through the auto-switching
    control algorithm (best_operating_point); every other n is held FIXED with
    no switching (operating_point directly). Returns {n: {'G','I','eta_pct','cw_eff'}}.
    """
    Gs = np.linspace(sim.sweep.G_min, sim.sweep.G_max, sim.sweep.G_steps)
    out = {}
    for n in n_values:
        is_control = n in control_algo_n
        I, eta_pct, cw_eff = [], [], []
        for G in Gs:
            op = _op_for_n(G, n, sim, is_control)
            mp = mpp(G, sim.solar)
            eta_frac = op['P'] / mp['P'] if mp['P'] > 1e-9 else 0.0
            I.append(op['I'])
            eta_pct.append(eta_frac * 100.0)
            cw_eff.append(op['I'] * eta_frac)
        out[n] = {'G': Gs, 'I': np.array(I), 'eta_pct': np.array(eta_pct),
                   'cw_eff': np.array(cw_eff), 'control_algo': is_control}
    return out


def _n_family_split(data_by_n: dict):
    """Split n's into (fixed_ns, control_ns) using each entry's control_algo flag
    (set by run_constant_n_sweep/timeseries) — not a magnitude heuristic, so it
    stays correct regardless of how wide the fixed-n range grows.
    """
    ns = sorted(data_by_n.keys(), reverse=True)
    fixed_ns   = sorted([n for n in ns if not data_by_n[n]['control_algo']], reverse=True)
    control_ns = sorted([n for n in ns if data_by_n[n]['control_algo']], reverse=True)
    return ns, fixed_ns, control_ns


def _n_family_style(data_by_n: dict):
    """Assign each n a plot style. Fixed (no-switching) n's get a viridis
    gradient by n magnitude (so equal n-gaps read as equal color-gaps even with
    a variable step schedule); control-algo n's get a fixed high-contrast
    dashed style so they don't fight the gradient for color slots.
    """
    ns, fixed_ns, control_ns = _n_family_split(data_by_n)
    cmap = plt.get_cmap('viridis')
    norm = plt.Normalize(vmin=min(fixed_ns), vmax=max(fixed_ns)) if fixed_ns else None
    styles = {}
    for n in fixed_ns:
        styles[n] = dict(color=cmap(norm(n)), ls='-', lw=1.6)
    for n in control_ns:
        styles[n] = dict(color='black', ls='--', lw=2.2)
    return ns, styles


def _n_family_legend_set(data_by_n: dict, max_fixed_labels: int = 10):
    """Which n's get a legend entry. A wide variable-step family can have 50+
    fixed-n lines — label only ~max_fixed_labels evenly-spaced ones (by rank)
    plus every control-algo n, matching the rest of the codebase's legend-
    subsampling convention for swept families.
    """
    ns, fixed_ns, control_ns = _n_family_split(data_by_n)
    k = min(max_fixed_labels, len(fixed_ns))
    if k <= 1:
        keep = set(fixed_ns[:1])
    else:
        keep_idx = {round(i * (len(fixed_ns) - 1) / (k - 1)) for i in range(k)}
        keep = {fixed_ns[i] for i in keep_idx}
    return keep | set(control_ns)


def _n_family_title(data_by_n: dict):
    ns, fixed_ns, control_ns = _n_family_split(data_by_n)
    label = f'n = {min(fixed_ns)}→{max(fixed_ns)} fixed (variable step)' if fixed_ns else ''
    if control_ns:
        label += (' + ' if label else '') + 'n = ' + ', '.join(str(n) for n in control_ns) + ' (control algo)'
    return label


def _n_family_fname(data_by_n: dict):
    ns, fixed_ns, control_ns = _n_family_split(data_by_n)
    stem = f'n{min(fixed_ns)}to{max(fixed_ns)}' if fixed_ns else ''
    if control_ns:
        stem += ('_' if stem else '') + 'plusctrl' + '_'.join(str(n) for n in control_ns)
    return stem


def plot_cw_efficiency_by_n(data_by_n: dict, sim: SimConfig, log_x: bool = False):
    """Current-weighted efficiency vs. G, one series per constant electrolyzer count."""
    ns, styles = _n_family_style(data_by_n)
    legend_ns = _n_family_legend_set(data_by_n)
    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    for n in ns:
        d = data_by_n[n]
        G, cw = d['G'], d['cw_eff']
        if log_x:
            mask = G > 0
            G, cw = G[mask], cw[mask]
        label = _n_label(n, d) if n in legend_ns else None
        ax.plot(G, cw, label=label, **styles[n])
    if log_x:
        ax.set_xscale('log')
    ax.set_xlabel('Irradiance G (W/m²)')
    ax.set_ylabel('Current-weighted efficiency (A) = I × P/P_mpp')
    ax.set_title(f'Current-weighted efficiency vs. G{" (log)" if log_x else ""}\n'
                 f'{_n_family_title(data_by_n)}')
    ax.legend(fontsize=7.5, ncol=2, loc='upper left')
    ax.grid(alpha=0.3, which='both' if log_x else 'major')
    fig.tight_layout()
    suffix = '_log' if log_x else ''
    _save(fig, f'cw_efficiency_vs_G_{_n_family_fname(data_by_n)}{suffix}.png', subdir='sweeps')
    plt.close(fig)


def plot_mpp_efficiency_vs_current_by_n(data_by_n: dict, sim: SimConfig, log_x: bool = False):
    """Raw MPP efficiency vs. current, one series per constant electrolyzer count."""
    ns, styles = _n_family_style(data_by_n)
    legend_ns = _n_family_legend_set(data_by_n)
    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    for n in ns:
        d = data_by_n[n]
        order = np.argsort(d['I'])
        I, eta = d['I'][order], d['eta_pct'][order]
        if log_x:
            mask = I > 0
            I, eta = I[mask], eta[mask]
        label = _n_label(n, d) if n in legend_ns else None
        ax.plot(I, eta, label=label, **styles[n])
    if log_x:
        ax.set_xscale('log')
    ax.set_xlabel('Current I (A)')
    ax.set_ylabel('Raw MPP efficiency (%)')
    ax.set_title(f'MPP-tracking efficiency vs. current{" (log)" if log_x else ""}\n'
                 f'{_n_family_title(data_by_n)}')
    ax.set_ylim(0, 105)
    ax.legend(fontsize=7.5, ncol=2, loc='lower right')
    ax.grid(alpha=0.3, which='both' if log_x else 'major')
    fig.tight_layout()
    suffix = '_log' if log_x else ''
    _save(fig, f'mpp_efficiency_vs_current_{_n_family_fname(data_by_n)}{suffix}.png',
          subdir='sweeps')
    plt.close(fig)


def run_constant_n_timeseries(n_values, t_hr, G_arr, sim: SimConfig, control_algo_n=()):
    """Like run_constant_n_sweep, but driven by a measured G(t) profile instead
    of a synthetic G sweep. Returns {n: {'t', 'I', 'eta_pct', 'cw_eff'}}.
    """
    out = {}
    for n in n_values:
        is_control = n in control_algo_n
        I, eta_pct, cw_eff = [], [], []
        for G in G_arr:
            op = _op_for_n(float(G), n, sim, is_control)
            mp = mpp(float(G), sim.solar)
            eta_frac = op['P'] / mp['P'] if mp['P'] > 1e-9 else 0.0
            I.append(op['I'])
            eta_pct.append(eta_frac * 100.0)
            cw_eff.append(op['I'] * eta_frac)
        out[n] = {'t': t_hr, 'I': np.array(I), 'eta_pct': np.array(eta_pct),
                   'cw_eff': np.array(cw_eff), 'control_algo': is_control}
    return out


def _n_label(n: int, d: dict) -> str:
    return f'n = {n} (control algo)' if d.get('control_algo') else f'n = {n}'


def plot_cw_efficiency_by_n_timeseries(data_by_n: dict, csv_name: str):
    """Current-weighted efficiency vs. time of day, one series per constant
    electrolyzer count — the time-of-day counterpart to plot_cw_efficiency_by_n.
    """
    ns, styles = _n_family_style(data_by_n)
    legend_ns = _n_family_legend_set(data_by_n)
    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    for n in ns:
        d = data_by_n[n]
        label = _n_label(n, d) if n in legend_ns else None
        ax.plot(d['t'], d['cw_eff'], label=label, **styles[n])
    ax.set_xlabel('Time of day (hr)')
    ax.set_ylabel('Current-weighted efficiency (A) = I × P/P_mpp')
    ax.set_title(f'Current-weighted efficiency vs. time of day ({csv_name})\n'
                 f'{_n_family_title(data_by_n)}')
    ax.legend(fontsize=7.5, ncol=2, loc='upper left')
    ax.grid(alpha=0.3)
    fig.tight_layout()
    stem = os.path.splitext(csv_name)[0]
    _save(fig, f'cw_efficiency_vs_time_{_n_family_fname(data_by_n)}_{stem}.png',
          subdir='sweeps')
    plt.close(fig)


# ─── Intuition prints ────────────────────────────────────────────────────────
def report_single_point(G: float, sim: SimConfig):
    r = evaluate(G, sim)
    op, mp = r['op'], r['mpp']
    print(f"\n── Single-point analysis at G = {G:.0f} W/m² ──")
    if not op['feasible']:
        print("  NO FEASIBLE OPERATING POINT — array can't push the bank above onset.")
        print(f"  V_oc_array = {sim.solar.V_oc*sim.solar.N_series:.1f} V; "
              f"stack onset = {sim.elec.N_cells_series*sim.elec.V_onset:.1f} V")
        return
    print(f"  MPP (ideal MPPT):    V={mp['V']:.1f} V  I={mp['I']:.2f} A  P={mp['P']/1000:.2f} kW")
    print(f"  DC-coupled op:       V={op['V']:.1f} V  I={op['I']:.2f} A  P={op['P']/1000:.2f} kW")
    print(f"    n_active stacks  = {op['n_active']} of {sim.elec.M_strings}")
    print(f"    cell j           = {op['j']*1000:.1f} mA/cm² (j_lim = {sim.elec.j_lim*1000:.0f})")
    print(f"    cell V           = {r['V_cell']:.3f} V "
          f"(onset {sim.elec.V_onset:.2f} + η_act {r['eta_act']:.3f} "
          f"+ η_ohm {r['eta_ohm']:.3f} + η_mt {r['eta_mt']:.3f})")
    print(f"    H2 production    = {r['m_h2_g_hr']:.1f} g/hr "
          f"({r['n_h2_mol_s']*1000:.2f} mmol/s)  [F_eff assumed {sim.elec.faradaic_eff*100:.0f}%]")
    print(f"    Stack heat       = {r['Q_total_W']/1000:.2f} kW")
    print(f"    MPP gap          = {r['mpp_gap_pct']:.2f} %")

    # Surprises / observations.
    overs = [('kinetic (η_act)', r['eta_act']),
             ('ohmic (η_ohm)',   r['eta_ohm']),
             ('transport (η_mt)', r['eta_mt'])]
    overs.sort(key=lambda x: -x[1])
    print(f"  >> Dominant loss term: {overs[0][0]} at {overs[0][1]*1000:.0f} mV/cell")
    if r['eta_mt'] > 0.5 * (r['eta_act'] + r['eta_ohm']):
        print("  >> WARNING: mass-transport loss is nontrivial — j is approaching j_lim.")
    if r['mpp_gap_pct'] > 10:
        print(f"  >> Note: MPP gap > 10% — switching granularity may be hurting at this G.")


def report_sweep_summary(Gs, rows, sim: SimConfig):
    P_op  = np.array([r['op']['P']  for r in rows])
    P_mpp = np.array([r['mpp']['P'] for r in rows])
    gap   = np.array([r['mpp_gap_pct'] for r in rows])

    # Energy-weighted gap — the only number that really matters for a day.
    # Weight by MPP power (proxy for time-of-day energy distribution at uniform
    # G sampling; for true diurnal weighting the user should sample G(t)).
    weights = P_mpp / np.maximum(P_mpp.sum(), 1e-9)
    gap_weighted = float((gap * weights).sum())

    energy_op  = float(np.trapezoid(P_op,  Gs))
    energy_mpp = float(np.trapezoid(P_mpp, Gs))
    energy_gap_pct = 100.0 * (energy_mpp - energy_op) / max(energy_mpp, 1e-9)

    print("\n── Sweep summary ──")
    print(f"  Irradiance range:        {sim.sweep.G_min:.0f}–{sim.sweep.G_max:.0f} W/m²")
    print(f"  Mean MPP gap:            {gap.mean():.2f} %")
    print(f"  Power-weighted MPP gap:  {gap_weighted:.2f} %  "
          f"(this is the '∫ over a day' figure of merit)")
    print(f"  ∫P dG  DC-coupled:       {energy_op:.0f} (kW·W/m²)")
    print(f"  ∫P dG  MPP ideal:        {energy_mpp:.0f}")
    print(f"  Energy lost vs MPP:      {energy_gap_pct:.2f} %")

    n_active_arr = np.array([r['op']['n_active'] for r in rows])
    switches = int(np.sum(np.diff(n_active_arr) != 0))
    print(f"  Stack switches across sweep: {switches} (granularity = "
          f"1/{sim.elec.M_strings} = {100/sim.elec.M_strings:.0f}%)")

    if switches == 0:
        n_used = int(n_active_arr[-1])
        V_min_bank = sim.elec.N_cells_series * sim.elec.V_onset
        V_mpp_high = rows[-1]['mpp']['V']
        print(f"  >> SURPRISE: optimizer never switches (n_active = {n_used} for all G).")
        print(f"     Bank's minimum voltage ({V_min_bank:.0f} V = N_cells × V_onset) is")
        print(f"     already below MPP voltage (~{V_mpp_high:.0f} V at G_max). Adding more")
        print(f"     parallel strings would only drop V_op further below MPP. To make")
        print(f"     switching useful you need either more cells per string (raises bank V)")
        print(f"     or a lower-voltage array (lowers MPP V).")


# ─── Entry point ─────────────────────────────────────────────────────────────
def main():
    sim = load_website_config()
    print("Solar-Electrolyzer DC Coupling Simulator")
    print("=" * 60)
    print(f"(config: {'website (app_state.json)' if os.path.exists(APP_STATE_FILE) else 'sim.py built-in defaults'})")
    print(f"Array:   I_sc={sim.solar.I_sc} A · V_oc={sim.solar.V_oc} V "
          f"· N_s={sim.solar.N_series} · N_p={sim.solar.N_parallel} "
          f"· T={sim.solar.T_cell} K")
    print(f"         (auto-inferred {sim.solar.cells_per_module} cells/module "
          f"@ {sim.solar.V_oc_per_cell} V/cell for thermal-voltage scaling)")
    print(f"Bank:    {sim.elec.N_cells_series} cells/string × "
          f"{sim.elec.M_strings} strings, {sim.elec.electrode_area_cm2} cm²/cell")
    print(f"         onset {sim.elec.V_onset} V, R={sim.elec.R_ohmic_area} Ω·cm², "
          f"j_lim {sim.elec.j_lim*1000:.0f} mA/cm²")

    print("\nGenerating single-point plots @ "
          f"G = {sim.G_single:.0f} W/m² ...")
    plot_iv_overlay(sim.G_single, sim)
    plot_pv_with_mpp(sim.G_single, sim)
    plot_loss_breakdown(sim.G_single, sim)
    report_single_point(sim.G_single, sim)

    # Cross-reference at low G to expose dominant-loss shifts and granularity pain.
    report_single_point(200.0, sim)

    print("\nRunning irradiance sweep ...")
    Gs, rows = plot_sweep(sim)
    plot_op_trajectory(Gs, rows, sim)
    plot_control_dashboard(Gs, rows, sim)
    report_sweep_summary(Gs, rows, sim)
    plot_efficiency_vs_current(Gs, rows, sim)

    # Fixed (no-switching) electrolyzer counts, variable step so the range can
    # reach 1000 without 490 lines: step 2 up to 50, step 10 up to 200, step 20
    # up to 400, step 40 up to (but excluding) 1000 — 1000 itself is reserved
    # for the control-algo reference case below.
    n_core = (list(range(20, 51, 2)) + list(range(60, 201, 10)) +
              list(range(220, 401, 20)) + list(range(440, 1000, 40)))
    print(f"\nRunning constant-electrolyzer-count sweep "
          f"(n = {n_core[0]}→{n_core[-1]} fixed/no switching, variable step, "
          f"+ n=1000 control-algo reference) ...")
    n_values      = n_core + [1000]
    control_algo_n = {1000}   # n=1000 = bank size for the auto-switching algorithm, not a fixed count
    data_by_n = run_constant_n_sweep(n_values, sim, control_algo_n=control_algo_n)
    plot_cw_efficiency_by_n(data_by_n, sim)
    plot_cw_efficiency_by_n(data_by_n, sim, log_x=True)
    plot_mpp_efficiency_vs_current_by_n(data_by_n, sim)
    plot_mpp_efficiency_vs_current_by_n(data_by_n, sim, log_x=True)
    eta_hi = data_by_n[max(n_core)]['eta_pct'][-1]
    eta_lo = data_by_n[min(n_core)]['eta_pct'][-1]
    if eta_hi - eta_lo < 2.0:
        print(f"  >> Note: n = {min(n_core)}..{max(n_core)} barely separates at G_max — raw MPP "
              f"efficiency only spans {eta_lo:.2f}–{eta_hi:.2f}% there. At this bank voltage "
              f"({sim.elec.N_cells_series} cells/string), the array sits close enough to every "
              f"n's I-V curve that electrolyzer count stops mattering much in this range; the "
              f"switching algorithm's real payoff is at low G, not high G.")

    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if os.path.isdir(data_dir):
        for fname in sorted(os.listdir(data_dir)):
            if fname.endswith('.csv'):
                print(f"\nRunning time-of-day profile: {fname} ...")
                csv_path = os.path.join(data_dir, fname)
                plot_control_dashboard_timeseries(csv_path, sim)
                t_hr, G_arr, _T_amb = load_irradiance_profile(csv_path)
                data_by_n_t = run_constant_n_timeseries(n_values, t_hr, G_arr, sim,
                                                         control_algo_n=control_algo_n)
                plot_cw_efficiency_by_n_timeseries(data_by_n_t, fname)
                plot_iv_trajectory_timeseries(csv_path, sim, M_strings=1000)

    print(f"\nAll outputs saved to: {os.path.relpath(OUTPUT_DIR)}")


if __name__ == '__main__':
    main()
