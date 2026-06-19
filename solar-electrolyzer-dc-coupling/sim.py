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
from dataclasses import dataclass, field
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
    """Invert solar I(V) for V given I, by bisection on V in [0, V_oc_array]."""
    V_oc_array = cfg.V_oc * cfg.N_series
    if I <= 0:
        return V_oc_array
    if I >= array_iph(G, cfg):
        return 0.0
    return brentq(lambda V: solar_current(V, G, cfg) - I, 0.0, V_oc_array)


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
def _save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
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
    _save(fig, f'iv_overlay_G{int(G)}.png')
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
    _save(fig, f'pv_mpp_G{int(G)}.png')
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
    _save(fig, f'loss_breakdown_G{int(G)}.png')
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
    _save(fig, 'sweep_overview.png')
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
    _save(fig, 'op_trajectory.png')
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
    sim = SimConfig()
    print("Solar-Electrolyzer DC Coupling Simulator")
    print("=" * 60)
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
    report_sweep_summary(Gs, rows, sim)

    print(f"\nAll outputs saved to: {os.path.relpath(OUTPUT_DIR)}")


if __name__ == '__main__':
    main()
