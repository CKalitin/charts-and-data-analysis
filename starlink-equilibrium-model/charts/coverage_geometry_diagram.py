"""The coverage triangle: Earth's centre, one satellite, and the furthest ground
point that satellite can serve.

Three different angles get called a "field of view" in this project, and they are
angles at three different vertices of ONE triangle -- which is why "25 deg" and
"~8 deg" both describe the same geometry without contradicting each other:

    at the user terminal   elevation above its local horizon   25.0 deg  (the input)
    at the satellite       off-nadir look angle                56.6 deg
    at Earth's centre      sub-satellite point to disk edge     8.5 deg  (the output)

    (90 + 25) + 56.6 + 8.5 = 180, exactly.

Everything is drawn TRUE TO SCALE, including Earth's curvature -- no exaggerated
altitude. That matters here: the whole reason the servable disk is only ~8.5 deg
wide is that 550 km is a small fraction of Earth's 6,378 km radius, and a diagram
with the altitude stretched would make the geometry look far more generous than it is.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import orbital_geometry as og   # noqa: E402
from viz import render          # noqa: E402

OUT_ROOT = Path(__file__).resolve().parent.parent / "results" / "coverage"

RE = og.EARTH_RADIUS_KM
ALT_KM = 550.0                      # Gen1's main shell; the others span 540-570 km
EPS = og.MIN_ELEVATION_DEG          # 25 deg, FCC Order 21-48

EARTH_FILL = "#dbe7f3"
EARTH_EDGE = "#7d9ec0"
RAY = "#1f3d63"
ANGLE = "#c1440e"
CAP = "#f2b705"


def _geometry():
    eta = og.off_nadir_angle_deg(ALT_KM, EPS)               # at the satellite
    r_deg = og.ground_range_angular_radius_deg(ALT_KM, EPS)  # at Earth's centre
    arc_km = og.ground_range_km(ALT_KM, EPS)                 # along the ground
    # Slant range by the law of sines on the same triangle (angle at G = 90 + eps).
    slant = (RE + ALT_KM) * np.sin(np.radians(r_deg)) / np.sin(np.radians(90 + EPS))
    return eta, r_deg, arc_km, slant


def _angle_between(vertex, p1, p2) -> float:
    a, b = np.asarray(p1) - vertex, np.asarray(p2) - vertex
    return float(np.degrees(np.arccos(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))))


def _verify_drawn_angles(O, S, G, H_near, eta, r_deg, tol=0.05):
    """Measure the three angles from the COORDINATES actually plotted, not from the
    formulas that produced them. A diagram whose labels are computed separately from
    its geometry can disagree with itself silently; this makes that impossible."""
    measured = {
        "elevation at the user terminal": (_angle_between(G, H_near, S), EPS),
        "off-nadir at the satellite": (_angle_between(S, O, G), eta),
        "at Earth's centre": (_angle_between(O, S, G), r_deg),
    }
    for name, (got, want) in measured.items():
        if abs(got - want) > tol:
            raise AssertionError(f"drawn {name} is {got:.3f} deg but the label says {want:.3f} deg")
    total = sum(got for got, _ in measured.values()) + 90.0
    if abs(total - 180.0) > tol:
        raise AssertionError(f"drawn angles sum to {total:.3f} deg, not 180")
    return measured


def _arc(ax, centre, radius, a0_deg, a1_deg, **kw):
    t = np.radians(np.linspace(a0_deg, a1_deg, 200))
    ax.plot(centre[0] + radius * np.cos(t), centre[1] + radius * np.sin(t), **kw)


def _angle_arc(ax, vertex, p1, p2, radius, label, label_pad=1.35, label_xy=None, **kw):
    """Mark the angle at `vertex` between the rays to p1 and p2, and label it just
    outside the arc along the bisector."""
    a1 = np.degrees(np.arctan2(p1[1] - vertex[1], p1[0] - vertex[0]))
    a2 = np.degrees(np.arctan2(p2[1] - vertex[1], p2[0] - vertex[0]))
    if (a2 - a1) % 360 > 180:
        a1, a2 = a2, a1
    _arc(ax, vertex, radius, a1, a2 if a2 > a1 else a2 + 360, color=ANGLE, lw=1.4)
    if label_xy is None:
        mid = np.radians((a1 + (a2 if a2 > a1 else a2 + 360)) / 2)
        label_xy = (vertex[0] + label_pad * radius * np.cos(mid),
                    vertex[1] + label_pad * radius * np.sin(mid))
    ax.text(label_xy[0], label_xy[1], label, color=ANGLE,
            ha=kw.pop("ha", "center"), va=kw.pop("va", "center"), fontsize=9, **kw)


def draw(ax_full, ax_zoom):
    eta, r_deg, arc_km, slant = _geometry()
    O = np.array([0.0, 0.0])
    P = np.array([0.0, RE])                       # sub-satellite point
    S = np.array([0.0, RE + ALT_KM])              # satellite
    g = np.radians(r_deg)
    G = np.array([RE * np.sin(g), RE * np.cos(g)])        # furthest servable point
    Gm = np.array([-G[0], G[1]])                          # and its mirror

    # ---------------- left: whole Earth, angle at Earth's centre ----------------
    ax = ax_full
    t = np.linspace(0, 2 * np.pi, 721)
    ax.fill(RE * np.cos(t), RE * np.sin(t), color=EARTH_FILL, zorder=0)
    ax.plot(RE * np.cos(t), RE * np.sin(t), color=EARTH_EDGE, lw=1.0, zorder=1)

    # the servable cap, drawn on the surface
    tc = np.radians(np.linspace(90 - r_deg, 90 + r_deg, 200))
    ax.plot(RE * np.cos(tc), RE * np.sin(tc), color=CAP, lw=4.0, solid_capstyle="butt", zorder=3)

    for X in (G, Gm):
        ax.plot([O[0], X[0]], [O[1], X[1]], color=RAY, lw=1.0, ls=":", zorder=2)
        ax.plot([S[0], X[0]], [S[1], X[1]], color=RAY, lw=1.4, zorder=2)
    ax.plot([O[0], S[0]], [O[1], S[1]], color=RAY, lw=1.0, ls=":", zorder=2)

    ax.plot(*S, marker="o", ms=7, color=RAY, zorder=4)
    ax.plot(*O, marker="+", ms=9, color=RAY, zorder=4)
    ax.text(S[0] + 260, S[1] + 220, "satellite", fontsize=9, color=RAY)
    ax.text(180, 130, "Earth's centre", fontsize=9, color=RAY)

    _angle_arc(ax, O, P, G, 2200, f"{r_deg:.1f} deg", label_pad=1.28)
    ax.annotate(f"Earth radius {RE:,.0f} km", xy=(0, -RE / 2), xytext=(0, -RE / 2),
                fontsize=9, color=RAY, ha="center")
    ax.plot([0, 0], [0, -RE], color=RAY, lw=0.8, ls=":", zorder=2)

    lim = RE * 1.22
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim * 1.02)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Angle at Earth's centre", fontsize=10)

    # ---------------- right: zoom on the satellite and the ground point ----------
    ax = ax_zoom
    tz = np.radians(np.linspace(90 - 1.6 * r_deg, 90 + 1.6 * r_deg, 400))
    ax.fill(np.concatenate([RE * np.cos(tz), [RE * np.cos(tz[-1]), RE * np.cos(tz[0])]]),
            np.concatenate([RE * np.sin(tz), [0, 0]]), color=EARTH_FILL, zorder=0)
    ax.plot(RE * np.cos(tz), RE * np.sin(tz), color=EARTH_EDGE, lw=1.2, zorder=1)
    ax.plot(RE * np.cos(np.radians(np.linspace(90 - r_deg, 90 + r_deg, 300))),
            RE * np.sin(np.radians(np.linspace(90 - r_deg, 90 + r_deg, 300))),
            color=CAP, lw=5.0, solid_capstyle="butt", zorder=3,
            label=f"servable ground spot, radius {arc_km:,.0f} km")

    for X in (G, Gm):
        ax.plot([S[0], X[0]], [S[1], X[1]], color=RAY, lw=1.5, zorder=4)
    ax.plot([S[0], O[0]], [S[1], O[1]], color=RAY, lw=1.0, ls=":", zorder=4)
    ax.plot(*S, marker="o", ms=8, color=RAY, zorder=6)
    ax.plot(*G, marker="o", ms=6, color=RAY, zorder=6)

    # local horizon at G: tangent to the sphere, i.e. perpendicular to OG
    tang = np.array([np.cos(g), -np.sin(g)])   # points away from the satellite
    horizon_len = 700.0
    H_far = G + tang * horizon_len * 0.75      # for the label
    H_near = G - tang * horizon_len            # toward the satellite -- the elevation reference
    ax.plot([H_near[0], H_far[0]], [H_near[1], H_far[1]], color="#666666", lw=1.1,
            ls="--", zorder=4)
    # Anchored to the RIGHT of the horizon line's far end, which is the only region
    # of this panel with nothing else in it -- left of here runs into the ground-spot
    # dimension line, above into the user-terminal label. "at the user terminal" is
    # dropped: the terminal is drawn at the other end of the same line.
    ax.text(H_far[0] + 55, H_far[1], "local horizon",
            fontsize=8, color="#666666", va="center", ha="left")

    # Elevation is the angle UP FROM THE HORIZON on the satellite's side, so the
    # reference ray is H_near. Using the far end instead measures 180 - eps.
    # Both angle labels are placed explicitly: the off-nadir bisector lands on the
    # yellow ground-spot arc, and the elevation's two rays both point leftward, so
    # its bisector would put the label inside the triangle rather than by its arc.
    _angle_arc(ax, S, O, G, 380, f"{eta:.1f} deg off-nadir", label_pad=1.0,
               label_xy=(255, S[1] - 95), ha="left")
    _angle_arc(ax, G, H_near, S, 300, f"{EPS:.0f} deg\nelevation", label_pad=1.0,
               label_xy=(G[0] + 115, G[1] + 315), ha="left")

    _verify_drawn_angles(O, S, G, H_near, eta, r_deg)

    # altitude
    ax.annotate("", xy=(S[0] - 210, S[1]), xytext=(P[0] - 210, P[1]),
                arrowprops=dict(arrowstyle="<->", color=RAY, lw=1.1))
    ax.text(-250, RE + ALT_KM / 2, f"altitude\n{ALT_KM:,.0f} km", fontsize=9,
            color=RAY, ha="right", va="center")
    ax.plot([P[0] - 260, P[0] + 60], [P[1], P[1]], color=RAY, lw=0.8, ls=":", zorder=2)

    # ground spot radius, measured along the surface. Both ends share one y so the
    # dimension line is horizontal -- an earlier version anchored one end at G's own
    # (lower) latitude and the other at P's, drawing it visibly tilted.
    y_dim = P[1] - 300
    ax.annotate("", xy=(G[0], y_dim), xytext=(P[0], y_dim),
                arrowprops=dict(arrowstyle="<->", color="#b8860b", lw=1.2))
    ax.text(G[0] / 2, y_dim - 70, f"ground spot radius {arc_km:,.0f} km",
            fontsize=9, color="#8a6508", ha="center", va="top")

    ax.text(S[0], S[1] + 95, "satellite", fontsize=9, color=RAY, ha="center")
    ax.text(G[0] + 55, G[1] - 95, "user terminal", fontsize=9, color=RAY,
            ha="left", va="top")

    ax.set_xlim(-arc_km * 1.85, arc_km * 2.25)
    ax.set_ylim(RE - 560, RE + ALT_KM + 320)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Angles at the satellite and the user terminal", fontsize=10)


def fig_coverage_geometry():
    eta, r_deg, arc_km, slant = _geometry()
    # render.new_figure() returns (fig, ax) with an Axes already attached. Taking
    # only the fig and calling add_subplot again leaves that first Axes orphaned,
    # rendering as a stray 0-1 tick/grid frame behind the diagram -- a documented
    # trap in this project's charting notes. Drop it explicitly.
    fig, stray = render.new_figure(figsize=(13.5, 7.4))
    stray.remove()
    ax_full = fig.add_subplot(1, 2, 1)
    ax_zoom = fig.add_subplot(1, 2, 2)
    draw(ax_full, ax_zoom)

    fig.suptitle("Satellite ground coverage geometry", fontsize=13)
    fig.text(0.5, 0.055,
             f"User FOV {EPS:.0f} deg (elevation at the dish)    "
             f"Sat FOV at equator ~{r_deg:.0f} deg (at Earth's centre)    "
             f"off-nadir {eta:.1f} deg at the satellite",
             fontsize=10, ha="center", va="bottom", color="#111111", fontweight="bold")
    fig.text(0.5, 0.012,
             f"The three angles are one triangle: (90 + {EPS:.0f}) + {eta:.1f} + {r_deg:.2f} = 180 deg exactly.  "
             f"Drawn true to scale, altitude not exaggerated.  "
             f"Altitude shown is Gen1's 550 km shell; the other shells span 540-570 km, "
             f"giving ground spot radii of 927-968 km.\n"
             f"Minimum elevation angle from FCC Order 21-48; shell altitudes from FCC filings/Celestrak.",
             fontsize=7.6, ha="center", va="bottom", color="#555555", linespacing=1.5)
    return fig, OUT_ROOT / "coverage_geometry.png"


def figures():
    return [("coverage_geometry", fig_coverage_geometry)]


if __name__ == "__main__":
    for name, build in figures():
        fig, path = build()
        render.save_fig(fig, path)
        print(f"  wrote {path.relative_to(OUT_ROOT.parent.parent)}")
