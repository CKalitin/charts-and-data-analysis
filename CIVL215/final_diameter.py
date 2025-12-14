"""
Manually specify the pipe diameters at every point along the path for this simulation.

Specify as a list of tuples:
	(dist 1, diameter 1),
	(dist 2, diameter 2),
	(dist 3, diameter 3),
where diameter 1 starts at dist 1 and continues until dist 2, etc.
"""

import sim

# Example: user-specified diameter segments (edit as needed)

# $318.9 M
"""manual_diameters = [
	(0, 1.1),
	(270_000, 1.4),
	(510_000, 1.3),
	(550_000, 1.2),
	(590_000, 1.1),
    (690_000, 1.0),
]"""

# $302.4 M
manual_diameters = [
	(0, 1.1),
	(350_000, 1.2),
    (540_000, 1.1),
    (690_000, 1.0),
    (731_000, 1.0),
]

# $304.9 M
"""manual_diameters = [
	(0, 1.1),
	(350_000, 1.3),
    (470_000, 1.1),
    (690_000, 1.0),
    (731_000, 1.0),
]"""

def diameter_vs_distance_func(dist):
	# Assumes manual_diameters is sorted by distance ascending
	for i in range(len(manual_diameters) - 1):
		start_dist, dia = manual_diameters[i]
		next_start_dist, _ = manual_diameters[i + 1]
		if start_dist <= dist < next_start_dist:
			return dia
	# If at or beyond last segment, use last diameter
	return manual_diameters[-1][1]

model_data = sim.sim_model(diameter_vs_distance_func)

sim.plot_model_data(model_data, file_name="elevation_egl_vs_distance_manual_diameters.png", title="Elevation and EGL vs Distance (Manual Diameters)")

print(manual_diameters)
print(f"Total cost: ${model_data['total_cost']:,}")