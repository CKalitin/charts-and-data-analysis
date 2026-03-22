import matplotlib.pyplot as plt

# Handmer data (red line)
handmer_x = [48.362195, 48.609146, 49.053659, 49.564024, 50.304878,
             51.753659, 53.597561, 54.354878, 55.968293, 61.220122, 64.2, 72.810366]
handmer_y = [1882.917466, 1641.074856, 1389.635317, 1207.293666, 1086.372361,
             923.224568, 796.545106, 767.754319, 621.880998, 414.587332, 355.086372, 230.326296]

# Stack points: (kWh/kgH2, $/kW, label, xytext offset, ha)
stack_points = [
    (48.9, 353, 'US DOE Est Alkaline (stack)', (10, -4), 'left'),
    (80,   100, 'Terraform (stack)',            (-10,  -4), 'right'),
    (46,   200, 'Verdagy AEM *Goal* (stack)',  (10,  -4), 'left'),
]

# Full plant points: (kWh/kgH2, $/kW, label, xytext offset, ha)
plant_points = [
    (53.7, 610,  'US DOE Est Alkaline (plant)',  (-10, -4), 'right'),
    (50,   775,  'Verdagy Alkaline (plant)',      (-10, -4), 'right'),
    (54.5, 850,  'EH2 PEM (plant)',               (10, -4), 'left'),
    (40,   2500, 'AEM / SOEC estimate (plant)',   ( 10, -4), 'left'),
]

fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(handmer_x, handmer_y, color='red', linewidth=2, label='Handmer 2024')

for x, y, label, offset, ha in stack_points:
    ax.scatter(x, y, marker='o', color='orange', s=80, zorder=5)
    ax.annotate(label, (x, y), textcoords='offset points', xytext=offset, fontsize=8, ha=ha)

for x, y, label, offset, ha in plant_points:
    ax.scatter(x, y, marker='^', color='blue', s=80, zorder=5)
    ax.annotate(label, (x, y), textcoords='offset points', xytext=offset, fontsize=8, ha=ha)

# Legend entries for categories
ax.scatter([], [], marker='o', color='orange', label='Electrolyzer stack')
ax.scatter([], [], marker='^', color='blue', label='Full plant')

ax.set_xlabel('Efficiency (kWh/kgH\u2082)')
ax.set_ylabel('Cost ($/kW)')
ax.set_title('Electrolyzer Cost vs Efficiency')
ax.legend()
ax.grid(True, linestyle='--', alpha=0.4)

ax.text(0.5, 0.95, 'Christopher Kalitin 2026', transform=ax.transAxes,
        fontsize=12, color='black', alpha=1.0, ha='center', va='top')

plt.tight_layout()
plt.savefig('electrolyzer_cost_vs_eff.png', dpi=150)
plt.show()
