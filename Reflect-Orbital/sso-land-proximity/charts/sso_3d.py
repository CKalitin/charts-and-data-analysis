"""Chart: 3D view of a dawn-dusk Sun-Synchronous Orbit (light theme).

Tells one story: the satellite rides the day/night terminator in *continuous
sunlight*, and reflects a beam of that sunlight down to a point on the day/night
line — light delivered to the edge of darkness.

Geometry is physically honest:
  - orbit ring is the model's exact SSO plane (P, Q basis), radius R_EARTH + ALT_KM
  - the Sun is offset from the orbit-plane normal by SUN_ORBIT_OFFSET_DEG. That same
    angle is the tilt between the orbit ring and the terminator great circle, so a
    small offset makes the orbit hug the day/night line. Below ~23 deg the ring never
    enters Earth's shadow cylinder (continuous sunlight) — the dawn-dusk regime.

The matplotlib-3D z-ordering problem (whole-artist depth sort -> curves clip through
the globe) is solved by an *occlusion split*: for the fixed camera we compute, per
curve point, whether the opaque sphere hides it, then draw visible segments
solid/bright and hidden segments faint/dashed. On-surface curves (terminator,
graticule) use a robust hemisphere test (outward normal faces camera) so they don't
flicker at the silhouette; off-surface curves (orbit, beam, rays) use the cylinder
test. Nothing relies on matplotlib's own sorting.

Independently runnable:  python charts/sso_3d.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

import config as cfg
from model import R_EARTH
from viz import render

# ── Palette (light theme — pure white page) ────────────────────────────────────────────
COL_BG         = "#FFFFFF"   # page background
COL_EARTH_LIT  = np.array([175, 205, 235]) / 255   # sunlit hemisphere (sky blue)
COL_EARTH_DARK = np.array([23, 34, 56]) / 255       # night hemisphere (deep navy)
COL_LIMB       = "#7F92AE"   # silhouette ring separating the globe from white
COL_TERM       = "#10A8CB"   # terminator great circle (bright cyan — reads day & night)
COL_ORBIT_SUN  = "#E8930C"   # sunlit arc of the orbit (amber — reads on white)
COL_ORBIT_SHAD = "#6A7488"   # shadowed / occluded arc of the orbit (slate)
COL_SUNRAY     = "#E8A53A"   # parallel sunlight rays (warm gold)
COL_BEAM       = "#149E52"   # reflected beam to the terminator target (green)
COL_SAT_FILL   = "#FFC400"   # satellite marker fill
COL_SAT_EDGE   = "#7A5200"   # satellite marker edge
COL_GRAT       = "#9FB2CC"   # graticule

COL_TITLE      = "#1B2231"
COL_SUB        = "#5A6884"
COL_LEGEND     = "#2A3344"
COL_WATERMARK  = "#9AA6BB"

A_ORBIT = R_EARTH + cfg.ALT_KM   # orbit radius, km
SURFACE_LIFT = 1.006             # lift on-surface curves above the sphere (anti z-fight)


# ── Vector helpers ─────────────────────────────────────────────────────────────────────
def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def _camera_vector(elev_deg: float, azim_deg: float) -> np.ndarray:
    """Unit vector pointing from the scene origin toward the matplotlib camera."""
    e, a = np.radians(elev_deg), np.radians(azim_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def _elev_azim(v: np.ndarray) -> dict:
    """Inverse of _camera_vector: a view direction -> matplotlib (elev, azim) degrees."""
    v = _unit(v)
    return dict(elev=float(np.degrees(np.arcsin(np.clip(v[2], -1, 1)))),
                azim=float(np.degrees(np.arctan2(v[1], v[0]))))


def _cam_basis(view: np.ndarray):
    """Camera right / up screen axes for the given view direction."""
    up = np.array([0, 0, 1.0])
    cam_right = _unit(np.cross(up, view))
    cam_up = _unit(np.cross(view, cam_right))
    return cam_right, cam_up


def _occluded(pts: np.ndarray, view: np.ndarray, radius: float,
              surface: bool = False) -> np.ndarray:
    """Boolean mask: True where the opaque sphere (radius, at origin) hides the point.

    surface=False (off-surface curves: orbit, beam, rays): a point is hidden iff its
    sightline passes within the silhouette (perp < R) AND it sits behind the sphere's
    near surface along the view axis.

    surface=True (on-surface curves: terminator, graticule): the point lies exactly at
    radius R, right on the boundary of the cylinder test, so that test flickers. Use the
    robust hemisphere test instead — a surface point is visible iff its outward normal
    faces the camera (p . view > 0).
    """
    if surface:
        return (pts @ view) <= 0
    s = pts @ view                                  # depth toward camera
    perp = np.linalg.norm(pts - np.outer(s, view), axis=1)
    inside = perp < radius
    near_surface = np.sqrt(np.clip(radius**2 - perp**2, 0, None))
    return inside & (s < near_surface)


def _split_draw(ax, pts, view, *, color, lw, zorder, hide_color=None,
                hide_alpha=0.30, alpha=1.0, surface=False, label=None):
    """Plot a polyline, solid where visible and faint-dashed where the globe hides it.

    This is the z-ordering fix: visible and occluded runs are drawn as separate
    artists so neither can punch incorrectly through the sphere.
    """
    occ = _occluded(pts, view, R_EARTH, surface=surface)
    hide_color = hide_color or color
    start = 0
    first_vis = True
    for i in range(1, len(pts) + 1):
        if i == len(pts) or occ[i] != occ[start]:
            seg = pts[start:i + 1] if i < len(pts) else pts[start:i]
            if len(seg) >= 2:
                if occ[start]:
                    ax.plot(*seg.T, color=hide_color, lw=lw * 0.7, ls=(0, (4, 4)),
                            alpha=hide_alpha, zorder=zorder - 5,
                            solid_capstyle="round")
                else:
                    ax.plot(*seg.T, color=color, lw=lw, alpha=alpha, zorder=zorder,
                            solid_capstyle="round",
                            label=label if first_vis else None)
                    first_vis = False
            start = i


def _callout(ax, point, text, view, *, color, direction=None, extra=0.42, fontsize=9.0):
    """Label a 3D point with a leader line out to the white margin beyond the limb.

    The label is pushed along its screen-radial direction (away from the globe centre)
    to clear the disk, or along an explicit `direction=(dx, dy)` in screen axes when two
    nearby points would otherwise send their labels the same way. A thin leader connects
    marker to text.
    """
    cam_right, cam_up = _cam_basis(view)
    pr, pu = point @ cam_right, point @ cam_up
    rad = np.hypot(pr, pu) + 1e-9
    if direction is None:
        ox, oy = pr / rad, pu / rad
    else:
        ox, oy = direction
    norm = np.hypot(ox, oy);  ox, oy = ox / norm, oy / norm
    out_r = max(rad, R_EARTH) + extra * R_EARTH      # land beyond the limb
    depth = point @ view
    anchor = ox * out_r * cam_right + oy * out_r * cam_up + depth * view
    ax.plot(*np.column_stack([point, anchor]).reshape(3, -1), color=color, lw=0.9,
            alpha=0.75, zorder=20, solid_capstyle="round")
    ha = "left" if ox >= 0 else "right"
    tip = anchor + np.sign(ox) * 0.04 * R_EARTH * cam_right
    ax.text(*tip, text, color=color, fontsize=fontsize, ha=ha, va="center",
            zorder=25, fontweight="bold")


# ── Scene construction ─────────────────────────────────────────────────────────────────
def _build_scene():
    """View-independent geometry in inertial km coordinates."""
    inc = np.radians(cfg.INC_DEG)
    P = np.array([1.0, 0.0, 0.0])
    Q = np.array([0.0, np.cos(inc), np.sin(inc)])
    n = _unit(np.cross(P, Q))                       # orbit-plane normal

    # Sun: offset from the orbit normal by the dawn-dusk angle, about a "seasonal" axis.
    off = np.radians(cfg.SUN_ORBIT_OFFSET_DEG)
    w = _unit(np.cross(np.array([0, 0, 1.0]), n))   # in-equatorial offset direction
    sun = _unit(n * np.cos(off) + w * np.sin(off))

    # Orbit ring.
    u = np.linspace(0, 2 * np.pi, 600)
    r_unit = np.cos(u)[:, None] * P + np.sin(u)[:, None] * Q
    orbit = A_ORBIT * r_unit

    # Sunlit vs shadowed: a point is in Earth's umbra (cylindrical-shadow model) iff
    # it is on the anti-sun side AND its distance from the shadow axis is < R_EARTH.
    s_along = r_unit @ sun
    perp = A_ORBIT * np.sqrt(np.clip(1 - s_along**2, 0, None))
    in_shadow = (s_along < 0) & (perp < R_EARTH)
    lit = ~in_shadow

    # Terminator great circle (plane perpendicular to the Sun). Lifted just above the
    # surface so mplot3d's facet depth-sort can't hide the line behind the sphere.
    e1 = _unit(np.cross(sun, np.array([0, 0, 1.0])))
    e2 = _unit(np.cross(sun, e1))
    tu = np.linspace(0, 2 * np.pi, 400)
    term = R_EARTH * SURFACE_LIFT * (np.cos(tu)[:, None] * e1 + np.sin(tu)[:, None] * e2)

    return dict(sun=sun, orbit=orbit, r_unit=r_unit, lit=lit,
                any_shadow=bool(in_shadow.any()), u=u, term=term, e1=e1, e2=e2)


def _place_sat_target(scene, view):
    """With a zero dawn-dusk offset the whole orbit lies on the terminator, so every point
    reflects sunlight straight down at exactly 90 deg. Choose a satellite well onto the
    near face (clearly visible, not at the limb) and as far to one side as possible — so it
    reads as 'off to the side we can see', with a short nadir beam to the day/night line."""
    orbit, r_unit = scene["orbit"], scene["r_unit"]
    cam_right, cam_up = _cam_basis(view)

    dep = orbit @ view
    side = np.abs(orbit @ cam_right)
    on_face = (dep > 0.30 * A_ORBIT) & (np.abs(orbit @ cam_up) < 0.55 * A_ORBIT)
    i_sat = int(np.argmax(np.where(on_face, side, -np.inf)))
    sat, sat_hat = orbit[i_sat], r_unit[i_sat]

    # Nadir beam: straight down to the surface point directly below (on the terminator).
    target = R_EARTH * SURFACE_LIFT * sat_hat
    return dict(sat=sat, sat_hat=sat_hat, target=target)


def _earth_surface(sun: np.ndarray, nu: int = 120, nv: int = 120):
    """Sphere mesh + per-vertex RGBA facecolors (smooth cosine day/night shading)."""
    phi = np.linspace(0, np.pi, nu)
    th = np.linspace(0, 2 * np.pi, nv)
    PH, TH = np.meshgrid(phi, th, indexing="ij")
    x = np.sin(PH) * np.cos(TH)
    y = np.sin(PH) * np.sin(TH)
    z = np.cos(PH)
    normals = np.stack([x, y, z], axis=-1)
    cosang = np.clip(normals @ sun, -1, 1)
    ambient = 0.12
    m = ambient + (1 - ambient) * np.clip(cosang, 0, 1)   # 0=night .. 1=subsolar
    colors = (COL_EARTH_DARK[None, None, :] * (1 - m[..., None])
              + COL_EARTH_LIT[None, None, :] * m[..., None])
    rgba = np.concatenate([colors, np.ones((*m.shape, 1))], axis=-1)
    return R_EARTH * x, R_EARTH * y, R_EARTH * z, rgba


def _limb_ring(view: np.ndarray):
    """The sphere silhouette for this camera: a circle of radius R perpendicular to view."""
    cam_right, cam_up = _cam_basis(view)
    t = np.linspace(0, 2 * np.pi, 240)
    return R_EARTH * (np.cos(t)[:, None] * cam_right + np.sin(t)[:, None] * cam_up)


def _graticule():
    """Faint lat/long lines, returned as a list of (N,3) arrays (drawn split)."""
    lines = []
    rad = R_EARTH * SURFACE_LIFT
    for lat in np.radians(np.arange(-60, 61, 30)):
        t = np.linspace(0, 2 * np.pi, 200)
        r = rad * np.cos(lat)
        lines.append(np.column_stack([r * np.cos(t), r * np.sin(t),
                                      np.full_like(t, rad * np.sin(lat))]))
    for lon in np.radians(np.arange(0, 360, 30)):
        t = np.linspace(-np.pi / 2, np.pi / 2, 120)
        lines.append(rad * np.column_stack([
            np.cos(t) * np.cos(lon), np.cos(t) * np.sin(lon), np.sin(t)]))
    return lines


# ── Drawing ────────────────────────────────────────────────────────────────────────────
def draw(ax, scene, view, *, elev, azim):
    sun = scene["sun"]
    place = _place_sat_target(scene, view)
    sat, target = place["sat"], place["target"]

    ax.set_axis_off()
    ax.set_facecolor(COL_BG)

    # Earth.
    xs, ys, zs, rgba = _earth_surface(sun)
    ax.plot_surface(xs, ys, zs, facecolors=rgba, rstride=1, cstride=1,
                    linewidth=0, antialiased=False, shade=False, zorder=0)

    # Silhouette ring (separates the globe from the white page).
    ring = _limb_ring(view)
    ax.plot(*ring.T, color=COL_LIMB, lw=1.3, zorder=1, alpha=0.9)

    # Graticule (subtle, hemisphere-split so it never flickers at the limb).
    for ln in _graticule():
        _split_draw(ax, ln, view, color=COL_GRAT, lw=0.5, zorder=2,
                    hide_alpha=0.0, surface=True)

    # Sunlight: parallel rays sampling the orbit in time (~one per 5 min), one at the sat.
    _draw_sun_rays(ax, scene, view, sat)

    # Terminator great circle (teal — the day/night line on the surface).
    _split_draw(ax, scene["term"], view, color=COL_TERM, lw=2.6, zorder=4,
                hide_alpha=0.22, surface=True)

    # Orbit ring — split sunlit vs shadowed arcs, each further split by occlusion.
    _draw_orbit(ax, scene["orbit"], scene["lit"], view)

    # Reflected beam: satellite straight down (nadir) to the terminator target.
    beam = np.linspace(sat, target, 60)
    _split_draw(ax, beam, view, color=COL_BEAM, lw=3.2, zorder=11, hide_alpha=0.30)
    ax.scatter(*target, s=70, color=COL_BEAM, edgecolor="white", linewidth=0.8,
               zorder=12, depthshade=False)

    # Right-angle marker: incoming sunlight (toward the Sun) ⟂ the straight-down beam.
    sat_hat = place["sat_hat"]
    e_in, e_out = sun, -sat_hat                       # perpendicular at the terminator
    ra = 0.14 * A_ORBIT
    corner = np.column_stack([sat + e_in * ra, sat + (e_in + e_out) * ra, sat + e_out * ra])
    ax.plot(*corner, color="#3a4252", lw=1.4, zorder=14, solid_capstyle="round")
    lbl = sat + (e_in + e_out) * (ra * 1.7)
    ax.text(*lbl, "90°", color="#3a4252", fontsize=9, fontweight="bold",
            ha="center", va="center", zorder=25)

    # Satellite: a crisp dot on the orbit (with a soft halo so it reads on any backdrop).
    ax.scatter(*sat, s=460, marker="o", color="#FFF1B8", alpha=0.50,
               zorder=12, depthshade=False)
    ax.scatter(*sat, s=150, marker="o", color=COL_SAT_FILL, edgecolor=COL_SAT_EDGE,
               linewidth=1.6, zorder=13, depthshade=False)

    side = 1.0 if (sat @ _cam_basis(view)[0]) >= 0 else -1.0   # which side the satellite is on
    _callout(ax, sat, "Satellite\n(in sunlight)", view, color=COL_TITLE,
             direction=(side * 0.9, 0.55))               # outward + up, into the sky
    _callout(ax, target, "Beam lands on\nthe day/night line", view,
             color="#0C6E3A", direction=(side * 0.9, -0.55))   # outward + down

    _annotate(ax, scene)

    # Camera + equal aspect (skill rule: equal span on all axes + locked box).
    # A little extra margin so the top-of-frame satellite + callout clear the title.
    lim = A_ORBIT * 1.4
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-lim, lim)
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=elev, azim=azim)


def _draw_orbit(ax, orbit, lit, view):
    """Draw the ring as sunlit (amber) and shadowed (slate) arcs, occlusion-split."""
    start = 0
    for i in range(1, len(orbit) + 1):
        if i == len(orbit) or lit[i] != lit[start]:
            seg = orbit[start:i + 1] if i < len(orbit) else orbit[start:i]
            if len(seg) >= 2:
                col = COL_ORBIT_SUN if lit[start] else COL_ORBIT_SHAD
                lw = 3.0 if lit[start] else 2.0
                _split_draw(ax, seg, view, color=col, lw=lw, zorder=9, hide_alpha=0.30)
            start = i


def _draw_sun_rays(ax, scene, view, sat):
    """Parallel sunlight rays sampling the orbit in *time* — about one ray per 5 minutes
    of the ~95-minute orbit — each arriving at a satellite position from the Sun. Together
    they show the orbit is bathed in sunlight all the way around (it never enters shadow).
    The ray reaching the highlighted satellite is emphasized and reflects straight down.
    """
    sun, orbit = scene["sun"], scene["orbit"]
    n_rays = 18                                       # ~ one ray per 5 min of a ~95 min orbit
    L = A_ORBIT * 0.5
    for k in np.linspace(0, len(orbit), n_rays, endpoint=False).astype(int):
        p = orbit[k]
        seg = np.linspace(p + sun * L, p, 24)
        _split_draw(ax, seg, view, color=COL_SUNRAY, lw=1.2, zorder=8,
                    alpha=0.9, hide_alpha=0.12)

    # Highlighted ray arriving at the satellite (continues as the reflected beam below).
    seg = np.linspace(sat + sun * (A_ORBIT * 0.62), sat, 24)
    _split_draw(ax, seg, view, color=COL_SUNRAY, lw=2.8, zorder=10, hide_alpha=0.30)


def _annotate(ax, scene):
    """Fixed-position callouts (text2D is immune to 3D rotation — skill rule)."""
    ax.text2D(0.5, 0.965, "Dawn-Dusk Sun-Synchronous Orbit",
              transform=ax.transAxes, ha="center", va="top",
              color=COL_TITLE, fontsize=15, fontweight="bold")
    ax.text2D(0.5, 0.918,
              f"Continuous sunlight, reflected to the day/night line  ·  "
              f"{cfg.ALT_KM} km  ·  {cfg.INC_DEG}° inclination",
              transform=ax.transAxes, ha="center", va="top",
              color=COL_SUB, fontsize=9.5)

    legend = [
        (COL_ORBIT_SUN, "SSO orbit — fully sunlit (never enters shadow)"),
        (COL_SUNRAY, "Sunlight (one ray per ~5 min of orbit)"),
        (COL_BEAM, "Reflected beam to the day/night line"),
        (COL_TERM, "Terminator (day/night line)"),
    ]
    if scene["any_shadow"]:
        legend.insert(1, (COL_ORBIT_SHAD, "SSO orbit — in Earth's shadow"))

    y = 0.20
    for col, lab in legend:
        ax.text2D(0.035, y, "—", transform=ax.transAxes, color=col,
                  fontsize=15, fontweight="bold", va="center")
        ax.text2D(0.075, y, lab, transform=ax.transAxes, color=COL_LEGEND,
                  fontsize=8.5, va="center")
        y -= 0.038

    ax.text2D(0.985, 0.02, cfg.WATERMARK, transform=ax.transAxes, ha="right",
              va="bottom", color=COL_WATERMARK, fontsize=8, style="italic")


# ── Figure assembly ────────────────────────────────────────────────────────────────────
def _new_3d_figure(figsize=(11, 9)):
    fig = Figure(figsize=figsize, dpi=cfg.OUTPUT_DPI)
    FigureCanvasAgg(fig)
    fig.set_facecolor(COL_BG)
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    return fig, ax


def _camera_views(scene) -> list[tuple[str, dict]]:
    """Day-side 3/4 views (Sun toward the camera) where the satellite sits well onto the
    near face and off to one side, its nadir beam is unobscured, and the orbit sun-rays
    point toward the camera so none are hidden by the globe. Two azimuths frame the
    satellite to the left and to the right for variety.
    """
    return [
        ("terminator", dict(elev=-5, azim=232)),   # satellite on the left, near the equator
        ("polar",      dict(elev=10, azim=304)),   # satellite on the right, slightly higher
    ]


def figures():
    """Return [(name, build_fn)] — one figure per camera viewpoint."""
    scene = _build_scene()
    plan = []
    for name, cam in _camera_views(scene):
        def build(name=name, cam=cam):
            fig, ax = _new_3d_figure()
            view = _camera_vector(cam["elev"], cam["azim"])
            draw(ax, scene, view, **cam)
            return fig, cfg.OUTPUT_DIR / f"sso_3d_{name}.png"
        plan.append((f"sso_3d_{name}", build))
    return plan


# ── Standalone entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import time
    t0 = time.time()
    for name, build in figures():
        fig, path = build()
        render.save_fig(fig, path, dpi=cfg.OUTPUT_DPI)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}  ({time.time()-t0:.1f}s)")
