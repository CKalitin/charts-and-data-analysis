import sim

 # Make sure this matches sim.py
DIST_STEP = 1000
LENGTH = 731 * 1000
LUT_DIST_STEP = 1000 * 200 # km

diameters = [0.9, 1.0, 1.1, 1.2, 1.3, 1.4]

best_diameters = {}

def update_diameter_LUT(existing_set, next_distance, step_size, next_diameter):
    for distance in range(next_distance, next_distance + step_size + 1, DIST_STEP):
        existing_set[distance] = next_diameter
    return existing_set

# init LUT
diameter_vs_distance_LUT = {}

# With each step it's updating the next 100 km with a given pipe diameter, seeing that to the next 1 km, then repeating
# Using 100 km LUT_DIST_STEP got $383.3M, 200 km gives $377.6M 
# Just going with 1.3m diameter gives $384M, negligible improvement
# Not a great search algorithm, but going one at a time does nothing because you just increase cost with a greater diamter, without decreasing number of pumping stations
for distance in range(0, LENGTH + 1, LUT_DIST_STEP):
    for minor_distance in range(0, LUT_DIST_STEP, DIST_STEP):
        if distance + minor_distance > LENGTH: continue
        diameter_vs_distance_LUT[distance + minor_distance] = 0.9

for distance in range(0, LENGTH + 1, DIST_STEP):
    if distance > LENGTH: continue
    models_data = []

    for diameter in diameters:
        temp_LUT = diameter_vs_distance_LUT.copy()
        temp_LUT = update_diameter_LUT(temp_LUT, distance, LUT_DIST_STEP, diameter)

        def diameter_vs_distance_func(dist):
            return temp_LUT[dist]

        model_data = sim.sim_model(diameter_vs_distance_func)
        models_data.append((diameter, model_data))

    lowest_cost = 999999999999999
    best_diameter = None
    for dia, m_data in models_data:
        if m_data['total_cost'] < lowest_cost:
            lowest_cost = m_data['total_cost']
            best_diameter = dia
    
    diameter_vs_distance_LUT = update_diameter_LUT(diameter_vs_distance_LUT, distance, LUT_DIST_STEP, best_diameter)
    print(f"At distance {distance}, best diameter is {best_diameter} with cost {lowest_cost}")

# Save diameter vs distance LUT to your favourite file type
with open('diameter_vs_distance_LUT.txt', 'w') as f:
    for dist in range(0, LENGTH + 1, DIST_STEP):
        f.write(f"{dist},{diameter_vs_distance_LUT[dist]}\n")

model_data = sim.sim_model(diameter_vs_distance_func)

sim.plot_model_data(model_data, file_name=f"elevation_egl_vs_distance_optimized_diamters.png", title=f"Elevation and EGL vs Distance (Optimized Diameters)")

"""
models_data = []
for diameter in diameters:
    models_data.append(sim.sim_model(diameter_vs_distance_func))

# After all simulations are completed, plot elevation and EGL vs distance for each model
for m in models_data:
    sim.plot_model_data(m, file_name=f"elevation_egl_vs_distance_d{m['diameter'][-1]}.png", title=f"Elevation and EGL vs Distance (diameter={m['diameter'][-1]} m)")

sim.plot_model_costs_vs_diameter(models_data)"""