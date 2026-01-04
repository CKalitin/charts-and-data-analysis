import scipy
import numpy as np
import matplotlib.pyplot as plt

# Choose whether to simulate sheath or bare wire
sheathed = True

m_1_sheath = 0.002 # kg
m_1_bare = 0.0001 # kg

a_1_sheath = 9.57e-4 # m^2
a_1_bare = 9.44e-5 # m^2

e_1 = 0.5 # emissivity

c_1 = 500 # J/kgK, specific heat capacity

boltzmann_constant = 5.67e-8 # W/m^2K^4

T_external_body = 1100 # K

T_initial = 300 # K, assumed ambient temperature

t_span = (0, 100) # seconds
t_points = np.linspace(t_span[0], t_span[1], 1000)

def evaluate_ode(m_1, a_1):
    def ode_system(t, T):
        # m_1 * c_1 * dT/dt = e_1 * a_1 * boltzmann_constant * (T^4 - T_0^4)
        dTdt = (e_1 * a_1 * boltzmann_constant * (T_external_body**4 - T**4)) / (m_1 * c_1)
        return dTdt

    solution = scipy.integrate.solve_ivp(
        fun=ode_system,
        t_span=t_span,
        y0=[T_initial],
        t_eval=t_points,
    )

    time = solution.t
    temperature_sheath = solution.y[0]

    # Equilibrium temperature is always T_external_body for this model

    return time, temperature_sheath

time_sheathed, temperature_sheath = evaluate_ode(m_1_sheath, a_1_sheath)
time_bare, temperature_bare = evaluate_ode(m_1_bare, a_1_bare)

plt.plot(time_sheathed, temperature_sheath, label='Sheathed Wire')
plt.plot(time_bare, temperature_bare, label='Bare Wire')
plt.xlabel('Time (s)')
plt.ylabel('Temperature (K)')

# Parameters textbox
params = (
    "Parameters:\n"
    f"m_1_sheath = {m_1_sheath} kg\n"
    f"m_1_bare = {m_1_bare} kg\n"
    f"a_1_sheath = {a_1_sheath:.3e} m^2\n"
    f"a_1_bare = {a_1_bare:.3e} m^2\n"
    f"e_1 = {e_1}\n"
    f"c_1 = {c_1} J/kgK\n"
    f"σ = {boltzmann_constant:.2e} W/m^2K^4\n"
    f"T_ext = {T_external_body} K\n"
    f"T_init = {T_initial} K\n"
    f"t_span = {t_span} s"
)
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

plt.text(
    0.98, 0.20, params,
    transform=plt.gca().transAxes,
    fontsize=9,
    verticalalignment='bottom',
    horizontalalignment='right',
    bbox=props
)

plt.legend()
plt.savefig('plot.png')
plt.show()
