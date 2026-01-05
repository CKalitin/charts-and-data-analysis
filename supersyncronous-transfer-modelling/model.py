import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

MU_EARTH = 398600  # km^3/s^2, derived from GM, G = 6.67430e-20 km^3/kg/s^2, M_earth = 5.972e24 kg
R_EARTH = 6371 # km

@dataclass
class Orbit:
    a: float      # Semi-major axis in km
    e: float      # Eccentricity
    i: float      # Inclination in degrees
    Omega: float  # Right Ascension of Ascending Node in degrees
    omega: float  # Argument of Perigee in degrees
    nu: float     # True Anomaly in degrees
    mu: float = MU_EARTH  # Gravitational parameter, default to Earth, GM, G = 6.67430e-20 km^3/kg/s^2, M_earth = 5.972e24 kg
    
    @property
    def r_apogee(self): return self.a * (1 + self.e)
    
    @property
    def r_perigee(self): return self.a * (1 - self.e)

    @property
    def v_perigee(self):
        return np.sqrt(self.mu * (2/self.r_perigee - 1/self.a))

    @property
    def v_apogee(self):
        return np.sqrt(self.mu * (2/self.r_apogee - 1/self.a))

    @property
    def period(self):
        """Orbital period in seconds"""
        return 2 * np.pi * np.sqrt(self.a**3 / self.mu)

    @classmethod
    def from_apsides(cls, apogee_alt, perigee_alt, i=0, Omega=0, omega=0, nu=0, R_earth=6371):
        """Creates an Orbit object from altitudes."""
        ra = apogee_alt + R_earth
        rp = perigee_alt + R_earth
        a = (ra + rp) / 2
        e = (ra - rp) / (ra + rp)
        return cls(a, e, i, Omega, omega, nu) # Note we use "cls" because it's a classmethod, referring to the class itself, not an instance

    def get_points(self, num_points=500):
        """Generates the 3D path of the orbit."""
        nu = np.linspace(0, 2 * np.pi, num_points)
        r = self.a * (1 - self.e**2) / (1 + self.e * np.cos(nu))
        
        # Orbital plane coordinates
        x_p, y_p = r * np.cos(nu), r * np.sin(nu)
        
        # Rotation to ECI frame
        i_r, Om_r, om_r = np.radians([self.i, self.Omega, self.omega])
        
        X = (x_p * (np.cos(Om_r)*np.cos(om_r) - np.sin(Om_r)*np.sin(om_r)*np.cos(i_r)) -
             y_p * (np.cos(Om_r)*np.sin(om_r) + np.sin(Om_r)*np.cos(om_r)*np.cos(i_r)))
        Y = (x_p * (np.sin(Om_r)*np.cos(om_r) + np.cos(Om_r)*np.sin(om_r)*np.cos(i_r)) -
             y_p * (np.sin(Om_r)*np.sin(om_r) - np.cos(Om_r)*np.cos(om_r)*np.cos(i_r)))
        Z = (x_p * (np.sin(om_r)*np.sin(i_r)) + y_p * (np.cos(om_r)*np.sin(i_r)))
        
        return X, Y, Z

class Maneuvers:
    @staticmethod
    def multipass_inclination_change_at_apogee(start_orbit, target_inc, dv_limit):
        """
        Returns a list of Orbit objects representing the transition.
        Executes burns at Apogee for maximum efficiency.
        """
        print(f"\n--- Inclination Change ---")
        print(f"From {start_orbit.i:.2f}° to {target_inc:.2f}°")
        
        current_orbit = start_orbit
        history = [current_orbit]
        
        # Speed at apogee (where we burn)
        v_burn = current_orbit.v_apogee
        
        # Max angle change per pass
        # dv = 2 * v * sin(di/2) -> di = 2 * asin(dv / 2v)
        ratio = min(dv_limit / (2 * v_burn), 1.0)  # Cap at 1 to avoid NaN
        max_di = 2 * np.degrees(np.arcsin(ratio))
        
        total_change_needed = abs(target_inc - start_orbit.i)
        num_passes = int(np.ceil(total_change_needed / max_di))
        actual_di_per_pass = (target_inc - start_orbit.i) / num_passes
        
        print(f"Planning {num_passes} passes at {actual_di_per_pass:.2f}° each.")
        
        # Calculate actual dV per pass
        di_radians = np.radians(actual_di_per_pass)
        dv_per_pass = abs(2 * v_burn * np.sin(di_radians / 2))
        total_dv = dv_per_pass * num_passes
        print(f"Total dV: {total_dv:.4f} km/s | Passes: {num_passes}")
        
        # Print initial orbit
        print(f"Initial: Inclination = {start_orbit.i:.2f}°, dV limit = {dv_limit:.4f} km/s")
        
        for _ in range(num_passes):
            # Create a NEW orbit object based on the previous one
            new_inc = current_orbit.i + actual_di_per_pass
            # Calculate actual dV required for this angle change
            di_radians = np.radians(actual_di_per_pass)
            dv_required = abs(2 * v_burn * np.sin(di_radians / 2))
            current_orbit = Orbit(
                a=current_orbit.a, 
                e=current_orbit.e, 
                i=new_inc, 
                Omega=current_orbit.Omega, 
                omega=current_orbit.omega,
                nu=current_orbit.nu
            )
            history.append(current_orbit)
            print(f"Pass {_+1}: Inclination = {new_inc:.2f}°, dV = {dv_required:.4f} km/s")
            
        return history, total_dv

    @staticmethod
    def multipass_altitude_change(start_orbit: Orbit, target_alt: float, change_apogee=True, dv_limit=0.1):
        """
        Raises or lowers apogee (by burning at perigee) or perigee (by burning at apogee).
        """
        print(f"\n--- Altitude Change ---")
        current_alt = start_orbit.r_apogee - 6371 if change_apogee else start_orbit.r_perigee - 6371
        alt_type = "Apogee" if change_apogee else "Perigee"
        print(f"Changing {alt_type} from {current_alt:.1f} km to {target_alt:.1f} km")
        
        history = [start_orbit]
        r_target = target_alt + 6371
        
        # 1. Determine where we are burning and what the final a and e will be
        r_fixed = start_orbit.r_perigee if change_apogee else start_orbit.r_apogee
        v_current = start_orbit.v_perigee if change_apogee else start_orbit.v_apogee
        
        a_final = (r_fixed + r_target) / 2
        v_final_req = np.sqrt(start_orbit.mu * (2/r_fixed - 1/a_final))
        
        total_dv_needed = v_final_req - v_current
        abs_dv_needed = abs(total_dv_needed)
        num_passes = int(np.ceil(abs_dv_needed / dv_limit))
        sign = np.sign(total_dv_needed) if total_dv_needed != 0 else 1
        dv_per_pass = sign * dv_limit
        
        print(f"Total dV: {abs_dv_needed:.4f} km/s | Passes: {num_passes}")

        # Print initial orbit
        initial_apogee = (start_orbit.r_apogee - 6371)
        initial_perigee = (start_orbit.r_perigee - 6371)
        print(f"Initial: Apogee = {initial_apogee:.1f} km, Perigee = {initial_perigee:.1f} km, dV limit = {dv_limit:.4f} km/s")

        # 2. Iteratively create intermediate orbits
        current_v = v_current
        for i in range(num_passes):
            dv_step = dv_per_pass if i < num_passes - 1 else sign * (abs_dv_needed - (num_passes - 1) * dv_limit)
            current_v += dv_step
            # New semi-major axis based on new velocity at the same r_fixed
            # Solve Vis-viva for a: a = 1 / (2/r - v^2/mu)
            a_new = 1 / (2/r_fixed - current_v**2 / start_orbit.mu)
            # New eccentricity: e = |ra - rp| / (ra + rp) -> a(1+e) = r_max
            # Or simpler: e = 1 - (r_perigee / a) if we burn at perigee
            if change_apogee:
                e_new = 1 - (r_fixed / a_new)
            else:
                e_new = (r_fixed / a_new) - 1
                
            new_orb = Orbit(a=a_new, e=abs(e_new), i=start_orbit.i, 
                            Omega=start_orbit.Omega, omega=start_orbit.omega, nu=0)
            history.append(new_orb)
            apogee_alt = (new_orb.r_apogee - 6371)
            perigee_alt = (new_orb.r_perigee - 6371)
            print(f"Pass {i+1}: Apogee = {apogee_alt:.1f} km, Perigee = {perigee_alt:.1f} km, dV = {dv_step:.4f} km/s")            
        return history, abs(total_dv_needed)

class OrbitVisualizer:
    def __init__(self, title="Orbital Transfer Visualization"):
        self.fig = plt.figure(figsize=(8, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_title(title)
        plt.subplots_adjust(top=1)
        self.ax.set_xlabel("X (km)", labelpad=15)
        self.ax.set_ylabel("Y (km)", labelpad=15)
        self.ax.set_zlabel("Z (km)", labelpad=15)
        # Initialize bounds tracking
        self.xmin = float('inf')
        self.xmax = float('-inf')
        self.ymin = float('inf')
        self.ymax = float('-inf')
        self.zmin = float('inf')
        self.zmax = float('-inf')

    def add_earth(self, radius=6371):
        # Update bounds for Earth
        self.xmin = min(self.xmin, -radius)
        self.xmax = max(self.xmax, radius)
        self.ymin = min(self.ymin, -radius)
        self.ymax = max(self.ymax, radius)
        self.zmin = min(self.zmin, -radius)
        self.zmax = max(self.zmax, radius)
        u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
        x = radius * np.cos(u) * np.sin(v)
        y = radius * np.sin(u) * np.sin(v)
        z = radius * np.cos(v)
        self.ax.plot_surface(x, y, z, color='royalblue', alpha=0.1, edgecolors='w', linewidth=0.1)

    def add_orbit(self, orbit: Orbit, label=None, color=None, alpha=1.0, lw=1.5):
        X, Y, Z = orbit.get_points()
        # Update bounds
        self.xmin = min(self.xmin, min(X))
        self.xmax = max(self.xmax, max(X))
        self.ymin = min(self.ymin, min(Y))
        self.ymax = max(self.ymax, max(Y))
        self.zmin = min(self.zmin, min(Z))
        self.zmax = max(self.zmax, max(Z))
        self.ax.plot(X, Y, Z, label=label, color=color, alpha=alpha, linewidth=lw)

    def _set_axes_equal(self):
        # We unfortunately are forced to have a good amount of wasted space for highly elliptical orbits to keep it aspect equal
        
        # Find the overall min/max across all axes for equal scaling
        overall_min = min(self.xmin, self.ymin, self.zmin)
        overall_max = max(self.xmax, self.ymax, self.zmax)
        # Set all axes to the same range for equal scales
        self.ax.set_xlim(overall_min, overall_max)
        self.ax.set_ylim(overall_min, overall_max)
        self.ax.set_zlim(overall_min, overall_max)
        # Keeps the 3D plot box cubic
        self.ax.set_box_aspect([1, 1, 1])

    def show(self):
        self.ax.legend(bbox_to_anchor=(0.02, 0.98), loc='upper left', fontsize='small')
        self._set_axes_equal()
        plt.show()

    def save(self, filename):
        self.ax.legend(bbox_to_anchor=(0.02, 0.98), loc='upper left', fontsize='small')
        self._set_axes_equal()
        plt.savefig(filename, bbox_inches='tight', dpi=200)
