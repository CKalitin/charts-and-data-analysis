import numpy as np
import matplotlib.pyplot as plt
import model
import os
import csv
from math import floor

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

def geo_transfer(initial_apo_alt, initial_peri_alt, initial_inc, initial_Omega=0, initial_omega=0, dv_limit=0.2, title="GEO Transfer", show=False):
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
    
    os.makedirs(f'geo_transfers_{int(dv_limit*1000)}ms_dV_lim', exist_ok=True)
    filename = f'geo_transfers_{int(dv_limit*1000)}ms_dV_lim/' + title.lower().replace(' ', '_') + '.png'
    viz.save(filename)
    
    # Save intermediary orbits to CSV
    os.makedirs(f'geo_transfers_{int(dv_limit*1000)}ms_dV_lim/orbit_data', exist_ok=True)
    filename_csv = f'geo_transfers_{int(dv_limit*1000)}ms_dV_lim/orbit_data/' + title.lower().replace(' ', '_') + '.csv'
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

def sweep_geo_transfer_apogees(min, max, step, dv_limit=0.2):
    # Go from 35786 to 40000 to 200000 km apogee in steps of 5000 km
    apogees = [35786] + list(range(min, max, step)) #+ list(range(500000, 10000000, 500000))

    results = []
    for apo in apogees:
        result = geo_transfer(initial_apo_alt=apo, initial_peri_alt=400, initial_inc=45, dv_limit=dv_limit, title=f"{apo} km Apogee Transfer to GEO", show=False)
        results.append((apo, result))
        print(f"Apogee: {apo} km, Total ΔV: {result['total_dv']:.3f} km/s, Total Time: {result['total_time_days']:.1f} days")

    # return apogees vs results
    return results

def plot_apogees_vs_dv_time(results, dv_limit, file_suffix=""):
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
             f"Inclination: 45°, Perigee: 400 km", 
             ha='center', fontsize=9, style='italic')
    
    fig.tight_layout()  
    plt.subplots_adjust(bottom=0.08)  # Make room for the note
    plt.savefig(f'apogee_vs_dv_time{file_suffix}.png', bbox_inches='tight', dpi=300)
    #plt.show()
    plt.close(fig)

"""dv_limit = 0.2
results = sweep_geo_transfer_apogees(40000, 200001, 10000, dv_limit=dv_limit)
plot_apogees_vs_dv_time(results, dv_limit, f"_200Mm_{int(dv_limit*1000)}ms_dV_lim") # Mm = mega meter, 1000 * km
"""
dv_limit = 100
results = sweep_geo_transfer_apogees(500000, 10000001, 100000, dv_limit=dv_limit)
plot_apogees_vs_dv_time(results, dv_limit, f"_10000Mm_{int(dv_limit*1000)}ms_dV_lim")

"""dv_limit = 0.001
results = sweep_geo_transfer_apogees(40000, 200001, 10000, dv_limit=dv_limit)
plot_apogees_vs_dv_time(results, dv_limit, f"_200Mm_{int(dv_limit*1000)}ms_dV_lim")"""