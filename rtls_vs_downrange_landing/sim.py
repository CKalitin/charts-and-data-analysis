import matplotlib.pyplot as plt

LAUNCH_COST = 10000000 # dollars
REFURB_COST = 1000000
TRANSPORT_COST_DOWNRANGE = 1000000

LAUNCH_TIME = 1 # day
REFURB_TIME = 1
TRANSPORT_TIME_DOWNRANGE = 4

KG_PER_LAUNCH_DOWNRANGE = 10000 # kg
KG_PER_LAUNCH_RTLS = KG_PER_LAUNCH_DOWNRANGE * 0.7

# Take a range of refurb time values and transport cost values

# Independent variables: refurb + launch cost, transport cost, transport time downrange

def sim(type="rtls", refurb_cost=REFURB_COST, refurb_time=REFURB_TIME, transport_cost=TRANSPORT_COST_DOWNRANGE, transport_time=TRANSPORT_TIME_DOWNRANGE):
    if (type != "rtls" and type != "downrange"):
        raise ValueError("Invalid type. Choose 'rtls' or 'downrange'.")

    extra_cost = 0
    extra_time = 0
    kg_per_launch = KG_PER_LAUNCH_RTLS

    if type == "downrange":
        extra_cost = transport_cost
        extra_time = transport_time
        kg_per_launch = KG_PER_LAUNCH_DOWNRANGE

    cost = LAUNCH_COST + refurb_cost + extra_cost
    days_per_launch = LAUNCH_TIME + refurb_time + extra_time

    launches_per_year = 365.0 / days_per_launch

    kg_per_year = kg_per_launch * launches_per_year
    cost_per_kg = cost / kg_per_launch

    print(type, launches_per_year, kg_per_year, cost_per_kg)

    return (cost, days_per_launch, kg_per_year, cost_per_kg)

def plot(launches_list_downrange, launches_list_rtls, plot_var_index=0, x_var_name="Variable"):
    # launches_list = [(x1, y1, y2), ... ]
    # plot_var_index = 0 for cost, 1 for time, 2 for kg/year, 3 for cost/kg

    x = [launch[0] for launch in launches_list_downrange]
    y_downrange = [launch[1][plot_var_index] for launch in launches_list_downrange]
    y_rtls = [launch[1][plot_var_index] for launch in launches_list_rtls]

    y_axis_titles = ['Cost', 'Time', 'Kg per Year']
    y_axis_title = y_axis_titles[plot_var_index]

    # TODO:
    # TODO:
    # TODO:
    # TODO:
    # TODO:
    # Add two lines to the same plot with legend, configurable through function parameters, another plot var index parameter

    plt.plot(x, y_downrange, marker='o', label='Downrange')
    plt.plot(x, y_rtls, marker='o', label='RTLS')
    plt.xlabel(x_var_name)
    plt.ylabel(y_axis_title)
    plt.title('RTLS vs Downrange Landing')
    plt.grid()
    plt.legend(loc='best')
    plt.show()

transport_times = [1,2,3,4,5,6,7,8,9,10]
transport_time_list_downrange = []
transport_time_list_rtls = []
for transport_time in transport_times:
    sim_data = sim(type="downrange", transport_time=transport_time)
    transport_time_list_downrange.append((transport_time, sim_data))

    sim_data = sim(type="rtls", transport_time=transport_time)
    transport_time_list_rtls.append((transport_time, sim_data))
plot(transport_time_list_downrange, transport_time_list_rtls, plot_var_index=2, x_var_name="Transport Time (days)")
