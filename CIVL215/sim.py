import pandas as pd
import matplotlib.pyplot as plt
import math

LENGTH = 731 * 1000 # m

VOLUME_FLOW_RATE = 1
DENSITY = 1000 # kg/m^3
G = 9.81 # m/s^2

MAX_PRESSURE = 200000 # Pa
MIN_PRESSURE = 30000 # Pa
PUMP_PRESSURE_HEAD_INCREASE = 100 # m
DIST_STEP = 1000 # m

DISPLAY = False
VERBOSE = False

FRICTION_FACTOR_VS_DIAMETER = {
    # diameter (m) : friction factor (dimensionless)
    0.6: 0.015,
    0.7: 0.015,
    0.8: 0.015,
    0.9: 0.015,
    1.0: 0.014,
    1.1: 0.014,
    1.2: 0.014,
    1.3: 0.014,
    1.4: 0.014,
}

# min pressure head is -7m trust me bro

def get_elevation(distance):
    return 1000 * 0.2 * (2 + (6 * distance / LENGTH) - (5 * ((distance / LENGTH) ** 2)))

def get_pipe_area(diameter):
    radius = diameter / 2
    return math.pi * (radius ** 2)

def pressure_head_to_pressure(pressure_head):
    return DENSITY * G * pressure_head

def pressure_to_pressure_head(pressure):
    return pressure / (DENSITY * G)

def sim_model(diameter_vs_distance_func):
    model_data = {}
    model_data['num_stations'] = 0
    model_data['pipe_cost'] = 0
    model_data['pumping_station_cost'] = 0
    model_data['total_cost'] = 0
    model_data['diameter'] = []
    model_data['distance'] = []
    model_data['elevation'] = []
    model_data['pressure_head'] = []
    model_data['pressure'] = []
    model_data['energy_grade_line'] = []
    model_data['hydraulic_grade_line'] = []
    
    for dist in range(0, LENGTH+1, DIST_STEP):
        elevation = get_elevation(dist)
        
        diameter = diameter_vs_distance_func(dist)

        velocity = VOLUME_FLOW_RATE / get_pipe_area(diameter)

        frictional_head_loss = FRICTION_FACTOR_VS_DIAMETER[diameter] * DIST_STEP * (velocity ** 2) / (2 * G * diameter)
        elevation_head_loss = elevation - model_data['elevation'][-1] if model_data['elevation'] else 0
        
        pressure_head = model_data['pressure_head'][-1] - frictional_head_loss - elevation_head_loss if model_data['pressure_head'] else 0
        pressure = pressure_head_to_pressure(pressure_head)

        if pressure < MIN_PRESSURE:
            # print previous model_Data
            pressure_head += PUMP_PRESSURE_HEAD_INCREASE
            pressure = pressure_head_to_pressure(pressure_head)

            num_stations = model_data['num_stations'] + 1 if model_data['num_stations'] else 1
        
        energy_grade_line = elevation + pressure_head
        hydraulic_grade_line = energy_grade_line - (velocity ** 2) / (2 * G)

        if VERBOSE and dist < 30000 and diameter == 0.9:
            print(f"Diameter: {diameter} m, Distance: {dist} m, Elevation: {elevation:.2f} m, Pressure Head: {pressure_head:.2f} m, Frictional Head Loss: {frictional_head_loss:.2f} m, Elevation Head Loss: {elevation_head_loss:.2f} m, Pressure: {pressure:.2f} Pa, Num Stations: {num_stations}")

        model_data['diameter'].append(diameter)
        model_data['distance'].append(dist)
        model_data['num_stations'] = num_stations
        model_data['elevation'].append(elevation)
        model_data['pressure_head'].append(pressure_head)
        model_data['pressure'].append(pressure)
        model_data['energy_grade_line'].append(energy_grade_line)
        model_data['hydraulic_grade_line'].append(hydraulic_grade_line)
    if DISPLAY:
        print(model_data['num_stations'])

    pipe_cost_vs_diameter = {
        # diameter (m) : cost ($/m)
        0.6: 80,
        0.7: 100,
        0.8: 120,
        0.9: 150,
        1.0: 200,
        1.1: 250,
        1.2: 300,
        1.3: 350,
        1.4: 400,
    }

    for diameter in model_data['diameter']:
        model_data['pipe_cost'] += pipe_cost_vs_diameter[diameter] * DIST_STEP
    model_data['pumping_station_cost'] = model_data['num_stations'] * 16000000
    model_data['total_cost'] = model_data['pipe_cost'] + model_data['pumping_station_cost']

    return model_data

def plot_model_data(model_data, file_name="", title=""):
    plt.figure(figsize=(10, 6))

    plt.plot(model_data['distance'], model_data['elevation'], label='Elevation (m)')
    plt.plot(model_data['distance'], model_data['energy_grade_line'], label='EGL (m)')
    plt.plot(model_data['distance'], model_data['hydraulic_grade_line'], label='HGL (m)')
    
    plt.xlabel('Distance (m)')
    plt.ylabel('Height (m)')
    
    plt.title(title)
    
    plt.legend()

    # Add a box showing number of pump stations and total cost
    textstr = f'Number of Pump Stations: {model_data["num_stations"]}\nPipe Cost: ${model_data["pipe_cost"]:,}\nPumping Station Cost: ${model_data["pumping_station_cost"]:,}\nTotal Cost: ${model_data["total_cost"]:,}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    plt.text(0.05, 0.95, textstr, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=props)

    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    plt.savefig(file_name)
    print(f"Saved plot: {file_name}")

    if DISPLAY:
        plt.show()

def plot_model_costs_vs_diameter(model_data):
    diameters_plot = []
    pipe_costs = []
    pumping_costs = []
    total_costs = []

    for m in model_data:
        diameters_plot.append(m['diameter'][-1])
        pipe_costs.append(m.get('pipe_cost', 0))
        pumping_costs.append(m.get('pumping_station_cost', 0))
        total_costs.append(m.get('total_cost', 0))

    if diameters_plot:
        plt.figure(figsize=(8, 6))
        plt.plot(diameters_plot, pipe_costs, marker='o', label='Pipe Cost ($)')
        plt.plot(diameters_plot, pumping_costs, marker='o', label='Pumping Station Cost ($)')
        plt.plot(diameters_plot, total_costs, marker='o', label='Total Cost ($)')

        plt.xlabel('Diameter (m)')
        plt.ylabel('Cost ($)')
        plt.title('Cost vs Diameter')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()

        fname = 'cost_vs_diameter.png'
        plt.savefig(fname)
        print(f"Saved plot: {fname}")

        if DISPLAY:
            plt.show()
