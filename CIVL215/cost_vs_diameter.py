import sim

diameters = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]

models_data = []
for diameter in diameters:
    def diameter_vs_distance_func(dist):
        return diameter

    models_data.append(sim.sim_model(diameter_vs_distance_func))

# After all simulations are completed, plot elevation and EGL vs distance for each model
for m in models_data:
    sim.plot_model_data(m, file_name=f"elevation_egl_vs_distance_d{m['diameter'][-1]}.png", title=f"Elevation and EGL vs Distance (diameter={m['diameter'][-1]} m)")

sim.plot_model_costs_vs_diameter(models_data)