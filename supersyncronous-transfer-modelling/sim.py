import numpy as np
import matplotlib.pyplot as plt
import model
import os
import csv
from math import floor
from dataclasses import dataclass

def example_orbits():
    # Start at 400km circular LEO
    leo = model.Orbit(a=6771, e=0, i=28.5, Omega=90, omega=0, nu=0)

    # Raise apogee to 10,000km with a 0.2 km/s limit per pass
    transfer_steps = model.Maneuvers.multipass_altitude_change(leo, target_alt=10000, change_apogee=True, dv_limit=0.2)

    viz = model.OrbitVisualizer("Raising Apogee Multi-Pass")
    viz.add_earth()

    colors = plt.cm.viridis(np.linspace(0, 1, len(transfer_steps)))
    for i, orb in enumerate(transfer_steps):
        viz.add_orbit(orb, color=colors[i], alpha=0.6, label=f"Pass {i}" if i % 2 == 0 else "")

    viz.show()

    # make orbit with 60 000 km apogee, 400 km perigee
    high_elliptical = model.Orbit.from_apsides(apogee_alt=60000, perigee_alt=400, i=45, Omega=0, omega=0)

    transfer_steps, _ = model.Maneuvers.multipass_inclination_change_at_apogee(high_elliptical, target_inc=0, dv_limit=0.1)

    viz = model.OrbitVisualizer("Inclination Change Multi-Pass")
    viz.add_earth()

    colors = plt.cm.plasma(np.linspace(0, 1, len(transfer_steps)))
    for i, orb in enumerate(transfer_steps):
        viz.add_orbit(orb, color=colors[i], alpha=0.6, label=f"Pass {i}" if i % 2 == 0 else "")
        
    viz.show()

def geo_transfer(initial_apo_alt, initial_peri_alt, initial_inc, initial_Omega=0, initial_omega=0, dv_limit=0.2, title="GEO Transfer", show=False, max_apogee=None):
    geo_alt = 35786  # GEO altitude in km
    
    start_orbit = model.Orbit.from_apsides(apogee_alt=initial_apo_alt, perigee_alt=initial_peri_alt, i=initial_inc, Omega=initial_Omega, omega=initial_omega)
    
    steps = [start_orbit]
    total_dv = 0
    inc_dv_total = 0
    apo_dv_total = 0
    peri_dv_total = 0
    
    # Inclination change if needed
    if initial_inc != 0:
        inc_steps, inc_dv = model.Maneuvers.multipass_inclination_change_at_apogee(start_orbit, target_inc=0, dv_limit=dv_limit)
        steps.extend(inc_steps[1:])
        total_dv += inc_dv
        inc_dv_total = inc_dv
    
    current_orbit = steps[-1]
    
    # Perigee change if needed
    if current_orbit.r_perigee != geo_alt + 6371:
        peri_steps, peri_dv = model.Maneuvers.multipass_altitude_change(current_orbit, target_alt=geo_alt, change_apogee=False, dv_limit=dv_limit)
        steps.extend(peri_steps[1:])
        total_dv += peri_dv
        peri_dv_total = peri_dv
    
    current_orbit = steps[-1]
    
    # Apogee change if needed
    if current_orbit.r_apogee != geo_alt + 6371:
        apo_steps, apo_dv = model.Maneuvers.multipass_altitude_change(current_orbit, target_alt=geo_alt, change_apogee=True, dv_limit=dv_limit)
        steps.extend(apo_steps[1:])
        total_dv += apo_dv
        apo_dv_total = apo_dv
    
    # Calculate total time for all maneuvers
    total_time_seconds = sum(orb.period for orb in steps[1:])
    total_time_days = total_time_seconds / (3600 * 24)
    
    viz = model.OrbitVisualizer(title)
    viz.add_earth()
    
    # Limit legend to 6 entries: 0 and last, with 4 interpolated in between
    n = len(steps)
    legend_indices = [round(i * (n - 1) / 5) for i in range(6)]
    legend_indices = list(set(legend_indices))  # Remove duplicates if any
    
    colors = plt.cm.plasma(np.linspace(0, 0.9, len(steps)))
    for i, orb in enumerate(steps):
        label = f"Pass {i}" if i in legend_indices else ""
        viz.add_orbit(orb, color=colors[i], alpha=0.6, label=label)
    
    # Add DV information as text on the plot
    info_text = (f"Total ΔV: {total_dv:.3f} km/s\n"
                 f"Inclination ΔV: {inc_dv_total:.3f} km/s\n"
                 f"Apogee raise ΔV: {apo_dv_total:.3f} km/s\n"
                 f"Perigee raise ΔV: {peri_dv_total:.3f} km/s\n"
                 f"ΔV limit per maneuver: {dv_limit} km/s\n"
                 f"Total time: {total_time_days:.1f} days")
    
    viz.ax.text2D(0.98, 0.98, info_text, transform=viz.ax.transAxes, fontsize=10, 
                  verticalalignment='top', horizontalalignment='right', 
                  bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Build folder name with Mm apogee information if provided
    folder_base = f'geo_transfers_{int(dv_limit*1000)}ms_dV_lim_inc{int(initial_inc)}'
    if max_apogee is not None:
        folder_base += f'_{int(max_apogee/1000)}Mm'
    
    os.makedirs(folder_base, exist_ok=True)
    filename = folder_base + '/' + title.lower().replace(' ', '_') + '.png'
    viz.save(filename)
    
    # Save intermediary orbits to CSV
    os.makedirs(f'{folder_base}/orbit_data', exist_ok=True)
    filename_csv = f'{folder_base}/orbit_data/' + title.lower().replace(' ', '_') + '.csv'
    with open(filename_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['step', 'a_km', 'e', 'i_deg', 'Omega_deg', 'omega_deg', 'nu_deg', 'period_s', 'r_apogee_km', 'r_perigee_km'])
        for idx, orb in enumerate(steps):
            writer.writerow([idx, orb.a, orb.e, orb.i, orb.Omega, orb.omega, orb.nu, orb.period, orb.r_apogee, orb.r_perigee])
    
    if show:
        viz.show()
    
    plt.close(viz.fig)
        
    return {
        'steps': steps,
        'total_dv': total_dv,
        'inc_dv_total': inc_dv_total,
        'apo_dv_total': apo_dv_total,
        'peri_dv_total': peri_dv_total,
        'total_time_days': total_time_days
    }

def sweep_geo_transfer_apogees(min, max, step, dv_limit=0.2, inc=45):
    # Go from 35786 to 40000 to 200000 km apogee in steps of 5000 km
    apogees = [35786] + list(range(min, max, step)) #+ list(range(500000, 10000000, 500000))

    results = []
    for apo in apogees:
        result = geo_transfer(initial_apo_alt=apo, initial_peri_alt=400, initial_inc=inc, dv_limit=dv_limit, title=f"{apo} km Apogee Transfer to GEO", show=False, max_apogee=max)
        results.append((apo, result))
        print(f"Apogee: {apo} km, Total ΔV: {result['total_dv']:.3f} km/s, Total Time: {result['total_time_days']:.1f} days")

    # return apogees vs results
    return results

def plot_apogees_vs_dv_time(results, dv_limit, inc, file_suffix=""):
    apogees = [r[0] for r in results]
    total_dvs = [r[1]['total_dv'] for r in results]
    total_times = [r[1]['total_time_days'] for r in results]

    fig, ax1 = plt.subplots()

    color = 'tab:blue'
    ax1.set_xlabel('Insertion Apogee Altitude (km)')
    ax1.set_ylabel('Total ΔV (km/s)', color=color)
    ax1.plot(apogees, total_dvs, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  
    color = 'tab:red'
    ax2.set_ylabel('Total Time (days)', color=color)  
    ax2.plot(apogees, total_times, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('Initial Apogee vs Total ΔV and Time to GEO')
    
    # Add note about dV limit
    fig.text(0.5, 0.88,
             f"ΔV limit per maneuver: {dv_limit*1000:.0f} m/s", 
             ha='center', fontsize=9, style='italic')
    fig.text(0.5, 0.85,
             f"Inclination: {inc}°, Perigee: 400 km", 
             ha='center', fontsize=9, style='italic')
    
    fig.tight_layout()  
    plt.subplots_adjust(bottom=0.08)  # Make room for the note
    os.makedirs('results', exist_ok=True)
    plt.savefig(f'results/apogee_vs_dv_time{file_suffix}.png', bbox_inches='tight', dpi=300)
    #plt.show()
    plt.close(fig)

def plot_dv_components_vs_apogees(results, dv_limit, inc, file_suffix=""):
    apogees = [r[0] for r in results]
    inc_dvs = [r[1]['inc_dv_total'] for r in results]
    apo_dvs = [r[1]['apo_dv_total'] for r in results]
    peri_dvs = [r[1]['peri_dv_total'] for r in results]
    total_dvs = [r[1]['total_dv'] for r in results]

    fig, ax = plt.subplots()

    ax.plot(apogees, inc_dvs, color='tab:blue', label='Inclination Change ΔV', marker='o', markersize=3)
    ax.plot(apogees, apo_dvs, color='tab:red', label='Apogee Change ΔV', marker='s', markersize=3)
    ax.plot(apogees, peri_dvs, color='tab:green', label='Perigee Change ΔV', marker='^', markersize=3)
    ax.plot(apogees, total_dvs, color='tab:purple', label='Total ΔV', marker='d', markersize=3, linewidth=2)
    
    ax.set_xlabel('Insertion Apogee Altitude (km)')
    ax.set_ylabel('ΔV (km/s)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.title('ΔV Components vs Initial Apogee')
    
    # Add note about parameters in a box
    info_text = f"ΔV limit: {dv_limit*1000:.0f} m/s\nInclination: {inc}°\nPerigee: 400 km"
    ax.text(0.98, 0.98, info_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    fig.tight_layout()
    os.makedirs('results', exist_ok=True)
    plt.savefig(f'results/apogee_vs_dv_components{file_suffix}.png', bbox_inches='tight', dpi=300)
    plt.close(fig)

def plot_dv_rates_vs_apogees(results, dv_limit, inc, file_suffix=""):
    apogees = [r[0] for r in results]
    inc_dvs = [r[1]['inc_dv_total'] for r in results]
    apo_dvs = [r[1]['apo_dv_total'] for r in results]
    peri_dvs = [r[1]['peri_dv_total'] for r in results]
    
    # Calculate rates of change (derivatives) using finite differences
    # d(dV)/d(apogee)
    inc_dv_rates = []
    apo_dv_rates = []
    peri_dv_rates = []
    
    for i in range(len(apogees) - 1):
        d_apogee = apogees[i+1] - apogees[i]
        d_inc_dv = inc_dvs[i+1] - inc_dvs[i]
        d_apo_dv = apo_dvs[i+1] - apo_dvs[i]
        d_peri_dv = peri_dvs[i+1] - peri_dvs[i]
        
        inc_dv_rates.append(d_inc_dv / d_apogee)
        apo_dv_rates.append(d_apo_dv / d_apogee)
        peri_dv_rates.append(d_peri_dv / d_apogee)
    
    # Use apogees[:-1] to align with rates array
    fig, ax = plt.subplots()
    
    ax.plot(apogees[:-1], inc_dv_rates, color='tab:blue', label='d(Inc ΔV)/d(Apogee)', marker='o', markersize=3)
    ax.plot(apogees[:-1], apo_dv_rates, color='tab:red', label='d(Apo ΔV)/d(Apogee)', marker='s', markersize=3)
    ax.plot(apogees[:-1], peri_dv_rates, color='tab:green', label='d(Peri ΔV)/d(Apogee)', marker='^', markersize=3)
    
    ax.set_xlabel('Insertion Apogee Altitude (km)')
    ax.set_ylabel('Rate of Change (1/km)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.title('ΔV Component Rates vs Initial Apogee')
    
    # Add note about parameters in a box
    info_text = f"ΔV limit: {dv_limit*1000:.0f} m/s\nInclination: {inc}°\nPerigee: 400 km"
    ax.text(0.98, 0.98, info_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    fig.tight_layout()
    os.makedirs('results', exist_ok=True)
    plt.savefig(f'results/apogee_vs_dv_rates{file_suffix}.png', bbox_inches='tight', dpi=300)
    plt.close(fig)

def plot_combined_inclination_comparison(results_inc0, results_inc45, dv_limit, dV_limit_val, max_apogee=None):
    """Plot DV and Time comparison between two inclinations on the same graph."""
    apogees_0 = [r[0] for r in results_inc0]
    total_dvs_0 = [r[1]['total_dv'] for r in results_inc0]
    total_times_0 = [r[1]['total_time_days'] for r in results_inc0]
    
    apogees_45 = [r[0] for r in results_inc45]
    total_dvs_45 = [r[1]['total_dv'] for r in results_inc45]
    total_times_45 = [r[1]['total_time_days'] for r in results_inc45]

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot DV for both inclinations
    ax1.set_xlabel('Insertion Apogee Altitude (km)', fontsize=11)
    ax1.set_ylabel('Total ΔV (km/s)', fontsize=11)
    ax1.plot(apogees_0, total_dvs_0, color='tab:blue', label='Inc 0° ΔV', linewidth=2)
    ax1.plot(apogees_45, total_dvs_45, color='tab:cyan', label='Inc 45° ΔV', linewidth=2, linestyle='--')
    ax1.tick_params(axis='y')

    ax2 = ax1.twinx()  
    ax2.set_ylabel('Total Time (days)', fontsize=11)
    ax2.plot(apogees_0, total_times_0, color='tab:red', label='Inc 0° Time', linewidth=2, alpha=0.7)
    ax2.plot(apogees_45, total_times_45, color='tab:orange', label='Inc 45° Time', linewidth=2, linestyle='--', alpha=0.7)
    ax2.tick_params(axis='y')

    plt.title('Inclination Comparison: Initial Apogee vs Total ΔV and Time to GEO', fontsize=12, fontweight='bold')
    
    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    # Add note about parameters
    fig.text(0.5, 0.88,
             f"ΔV limit per maneuver: {dV_limit_val*1000:.0f} m/s | Perigee: 400 km", 
             ha='center', fontsize=9, style='italic')
    
    fig.tight_layout()  
    plt.subplots_adjust(bottom=0.08)
    os.makedirs('results', exist_ok=True)
    
    # Build filename based on parameters
    if max_apogee is not None:
        file_suffix = f"_{int(max_apogee/1000)}Mm_{int(dV_limit_val*1000)}ms_dV_lim_inc_comparison"
    else:
        file_suffix = f"_comparison"
    
    plt.savefig(f'results/apogee_vs_dv_time{file_suffix}.png', bbox_inches='tight', dpi=300)
    print(f"Combined comparison plot saved to results/apogee_vs_dv_time{file_suffix}.png")
    plt.close(fig)

@dataclass
class SweepParameters:
    min_apogee: int
    max_apogee: int
    step_apogee: int
    dv_limit: float
    inc: int

sweep_params =[
    SweepParameters(250000, 10000001, 250000, 100, 0),
    SweepParameters(40000, 200001, 10000, 100, 0),
    SweepParameters(40000, 200001, 10000, 0.001, 0),
    SweepParameters(40000, 200001, 10000, 0.2, 45),
    SweepParameters(250000, 10000001, 250000, 100, 45),
    SweepParameters(40000, 200001, 10000, 0.001, 45),
]

# Store results for comparison
results_inc0_10Mm_100ms = None
results_inc45_10Mm_100ms = None
results_inc0_200K_1ms = None
results_inc45_200K_1ms = None

for params in sweep_params:
    results = sweep_geo_transfer_apogees(params.min_apogee, params.max_apogee, params.step_apogee, dv_limit=params.dv_limit, inc=params.inc)
    file_suffix = f"_{int(params.max_apogee/1000)}Mm_{int(params.dv_limit*1000)}ms_dV_lim_inc{params.inc}"
    plot_apogees_vs_dv_time(results, params.dv_limit, params.inc, file_suffix)
    plot_dv_components_vs_apogees(results, params.dv_limit, params.inc, file_suffix)
    plot_dv_rates_vs_apogees(results, params.dv_limit, params.inc, file_suffix)
    
    # Store the 10000Mm 100ms results for both inclinations
    if params.max_apogee == 10000001 and params.dv_limit == 100 and params.inc == 0:
        results_inc0_10Mm_100ms = results
    elif params.max_apogee == 10000001 and params.dv_limit == 100 and params.inc == 45:
        results_inc45_10Mm_100ms = results
    
    # Store the 200K 1ms results for both inclinations
    if params.max_apogee == 200001 and params.dv_limit == 0.001 and params.inc == 0:
        results_inc0_200K_1ms = results
    elif params.max_apogee == 200001 and params.dv_limit == 0.001 and params.inc == 45:
        results_inc45_200K_1ms = results

# Create combined comparison plots
if results_inc0_10Mm_100ms is not None and results_inc45_10Mm_100ms is not None:
    plot_combined_inclination_comparison(results_inc0_10Mm_100ms, results_inc45_10Mm_100ms, dv_limit=100, dV_limit_val=100, max_apogee=10000001)

if results_inc0_200K_1ms is not None and results_inc45_200K_1ms is not None:
    plot_combined_inclination_comparison(results_inc0_200K_1ms, results_inc45_200K_1ms, dv_limit=0.001, dV_limit_val=0.001, max_apogee=200001)
