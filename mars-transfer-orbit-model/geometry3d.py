"""Parametric 3D geometry helpers for the departure-geometry illustrations.

Kept separate from patched_conic.py (which solves for the physics) so the
"how do I turn this state into points to plot" concern stays isolated.
"""
import numpy as np


def sphere_surface(radius, n=40):
    u, v = np.mgrid[0:2 * np.pi:n * 1j, 0:np.pi:(n // 2) * 1j]
    x = radius * np.cos(u) * np.sin(v)
    y = radius * np.sin(u) * np.sin(v)
    z = radius * np.cos(v)
    return x, y, z


def circle_points(basis1_hat, basis2_hat, radius, center=np.zeros(3), n=200):
    """Circle of given radius in the plane spanned by two orthonormal vectors."""
    theta = np.linspace(0, 2 * np.pi, n)
    return center + radius * (np.outer(np.cos(theta), basis1_hat)
                               + np.outer(np.sin(theta), basis2_hat))


def plane_patch(basis1_hat, basis2_hat, half_extent, center=np.zeros(3), n=2):
    """A flat square patch spanning [-half_extent, half_extent] in each basis
    direction -- used to visually show a plane contains a given vector."""
    s = np.linspace(-half_extent, half_extent, n)
    S1, S2 = np.meshgrid(s, s)
    X = center[0] + S1 * basis1_hat[0] + S2 * basis2_hat[0]
    Y = center[1] + S1 * basis1_hat[1] + S2 * basis2_hat[1]
    Z = center[2] + S1 * basis1_hat[2] + S2 * basis2_hat[2]
    return X, Y, Z


def peri_direction(r_hat, n_hat, nu):
    """Reconstruct the periapsis-direction unit vector given a known point's
    direction r_hat at true anomaly nu (measured from periapsis, in the
    positive sense about n_hat)."""
    return r_hat * np.cos(nu) - np.cross(n_hat, r_hat) * np.sin(nu)


def conic_points(peri_hat, n_hat, e, p, nu_min, nu_max, n=200):
    """Points along a conic (ellipse e<1 or hyperbola e>1) between true
    anomalies nu_min and nu_max (radians), measured from peri_hat."""
    nu = np.linspace(nu_min, nu_max, n)
    dirs = (np.outer(np.cos(nu), peri_hat) + np.outer(np.sin(nu), np.cross(n_hat, peri_hat)))
    r = p / (1 + e * np.cos(nu))
    return dirs * r[:, None]


def set_axes_equal_box(ax, half_extent, center=(0, 0, 0)):
    cx, cy, cz = center
    ax.set_xlim(cx - half_extent, cx + half_extent)
    ax.set_ylim(cy - half_extent, cy + half_extent)
    ax.set_zlim(cz - half_extent, cz + half_extent)
    ax.set_box_aspect([1, 1, 1])
