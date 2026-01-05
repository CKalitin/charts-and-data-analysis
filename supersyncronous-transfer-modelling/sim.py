import numpy as np
import matplotlib.pyplot as plt
import model

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
