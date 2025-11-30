import matplotlib.pyplot as plt

LAUNCH_COST = 10000000 # dollars
TRANSPORT_COST_DOWNRANGE = 1000000

LAUNCH_TIME = 5 # day
TRANSPORT_TIME_DOWNRANGE = 4

KG_PER_LAUNCH_DOWNRANGE = 10000 # kg
KG_PER_LAUNCH_RTLS = KG_PER_LAUNCH_DOWNRANGE * 0.7

# Take a range of refurb time values and transport cost values

# Independent variables: refurb + launch cost, transport cost, transport time downrange

def sim(type="rtls", transport_cost=TRANSPORT_COST_DOWNRANGE, transport_time=TRANSPORT_TIME_DOWNRANGE):
    if (type != "rtls" and type != "downrange"):
        raise ValueError("Invalid type. Choose 'rtls' or 'downrange'.")

    extra_cost = 0
    extra_time = 0
    kg_per_launch = KG_PER_LAUNCH_RTLS

    if type == "downrange":
        extra_cost = transport_cost
        extra_time = transport_time
        kg_per_launch = KG_PER_LAUNCH_DOWNRANGE

    cost = LAUNCH_COST + extra_cost
    days_per_launch = LAUNCH_TIME + extra_time

    launches_per_year = 365.0 / days_per_launch

    kg_per_year = kg_per_launch * launches_per_year
    cost_per_kg = cost / kg_per_launch

    return (cost, days_per_launch, kg_per_year, cost_per_kg)

def plot(launches_list_downrange, launches_list_rtls, plot_var_index=0, plot_var_index_2=-1, x_var_name="Variable"):
    # launches_list = [(x1, y1, y2), ... ]
    # plot_var_index = 0 for cost, 1 for time, 2 for kg/year, 3 for cost/kg

    x = [launch[0] for launch in launches_list_downrange]

    y_axis_titles = ['Cost', 'Time', 'Kg per Year', 'Cost per Kg']
    y_axis_1_title = y_axis_titles[plot_var_index]
    y_axis_2_title = y_axis_titles[plot_var_index_2]

    fig, ax1 = plt.subplots()
    # primary axis (plot_var_index)
    y_downrange_1 = [launch[1][plot_var_index] for launch in launches_list_downrange]
    y_rtls_1 = [launch[1][plot_var_index] for launch in launches_list_rtls]
    ax1.plot(x, y_downrange_1, marker='o', color='C0', label=f'Downrange ({y_axis_1_title})')
    ax1.plot(x, y_rtls_1, marker='s', color='C1', label=f'RTLS ({y_axis_1_title})')
    ax1.set_xlabel(x_var_name)
    ax1.set_ylabel(y_axis_1_title)
    ax1.grid(True)
    ax1.set_ylim(bottom=0)

    # show constants in a textbox on the plot
    info_text = (
        f"Launch cost: ${LAUNCH_COST:,}\n"
        f"Launch time: {LAUNCH_TIME} days\n"
        f"RTLS Payload: {int(KG_PER_LAUNCH_RTLS):,} kg\n"
        f"Downrange Payload: {int(KG_PER_LAUNCH_DOWNRANGE):,} kg"
    )
    bbox_props = dict(boxstyle='round', facecolor='white', alpha=0.8)
    ax1.text(0.02, 0.02, info_text, transform=ax1.transAxes, fontsize=9,
             verticalalignment='bottom', bbox=bbox_props)
    
    # secondary axis (plot_var_index_2)
    if plot_var_index_2 != -1:
        ax2 = ax1.twinx()
        y_downrange_2 = [launch[1][plot_var_index_2] for launch in launches_list_downrange]
        y_rtls_2 = [launch[1][plot_var_index_2] for launch in launches_list_rtls]
        ax2.plot(x, y_downrange_2, marker='^', linestyle='--', color='C2', label=f'Downrange ({y_axis_2_title})')
        ax2.plot(x, y_rtls_2, marker='v', linestyle='--', color='C3', label=f'RTLS ({y_axis_2_title})')
        ax2.set_ylabel(y_axis_2_title)
        ax2.set_ylim(bottom=0)

    if plot_var_index_2 == -1:
        lines1, labels1 = ax1.get_legend_handles_labels()
        ax1.legend(lines1, labels1, loc='best')
    else:
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')

    plt.title('RTLS vs Downrange Landing')
    fig.tight_layout()
    plt.show()


transport_times = [0,1,2,3,4,5,6,7,8,9,10]
transport_time_list_downrange = []
transport_time_list_rtls = []
for transport_time in transport_times:
    sim_data = sim(type="downrange", transport_time=transport_time)
    transport_time_list_downrange.append((transport_time, sim_data))

    sim_data = sim(type="rtls", transport_time=transport_time)
    transport_time_list_rtls.append((transport_time, sim_data))
plot(transport_time_list_downrange, transport_time_list_rtls, plot_var_index=2, x_var_name="Transport Time (days)")


transport_costs = [i * 500000 for i in [0,1,2,3,4,5,6,7,8,9,10]]
transport_costs_list_downrange = []
transport_costs_list_rtls = []
for transport_cost in transport_costs:
    sim_data = sim(type="downrange", transport_cost=transport_cost)
    transport_costs_list_downrange.append((transport_cost, sim_data))

    sim_data = sim(type="rtls", transport_cost=transport_cost)
    transport_costs_list_rtls.append((transport_cost, sim_data))
    print(sim_data)
plot(transport_costs_list_downrange, transport_costs_list_rtls, plot_var_index=3, x_var_name="Transport Cost")

# Assign a value to each kg, payload value. This can be maximized even given higher launch cost
# Same principle as load capex cost
