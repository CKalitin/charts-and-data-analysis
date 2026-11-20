"""Ground reaction on the base (ground mode): where the gravel pushes back, and how hard.

ground_reaction  isometric view of the base: each base beam with its reaction drawn as a
                 'curtain' under it (depth = contact pressure q, N/m, upward arrows), lift-off
                 stretches marked, sandbags as blocks on the beams, the thrust line, the
                 tipping footprint on the ground.  Governing case (lowest base-joint SF).
ground_by_case   plan view per load case: beams coloured by q, lift-off dashed red.
"""
from __future__ import annotations

import numpy as np
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from . import _render as R

Q_CMAP = LinearSegmentedColormap.from_list("q", R.BLUE_RAMP)
BAG, BAG_EDGE = "#d9b98c", "#8a6a3e"
LIFT = R.CRIT


# ------------------------------------------------------------------ data
def contact_q(study, s):
    """Per base member: (s positions m, contact points (n,3) m, q N/m (+ = ground pushes up), closed?)."""
    m = study.model
    out = {}
    for i, c in enumerate(m.ground):
        d = out.setdefault(c.member, {"s": [], "P": [], "q": [], "on": []})
        d["s"].append(m.node_s[c.node])
        d["P"].append(c.P)
        d["q"].append(s.ground_F[i, 2] / c.trib if c.trib > 0 else 0.0)
        d["on"].append(bool(s.contact[i]))
    for d in out.values():
        o = np.argsort(d["s"])
        for k in d:
            d[k] = np.asarray(d[k])[o]
    return out


def base_joint_sf(study, s) -> float:
    base = set(study.model.geo.base_members)
    v = [r["SF"] for r in s.joint_rows
         if np.isfinite(r["SF"]) and (r["a"] in base or r["b"] in base)]
    return min(v) if v else np.inf


def governing(study):
    sols = [s for s in study.solves if s.valid and s.run.name == "R" and s.ground_F is not None]
    return min(sols, key=lambda s: base_joint_sf(study, s))


# ------------------------------------------------------------------ projection
VIEW = np.array([0.55, -1.0, 0.62])
VIEW = VIEW / np.linalg.norm(VIEW)                 # towards the viewer (front = -y, right = +x)
RIGHT = np.cross([0, 0, 1.0], VIEW)
RIGHT /= np.linalg.norm(RIGHT)
UP = np.cross(VIEW, RIGHT)


def proj(P):
    P = np.atleast_2d(P) * 1e3
    return np.c_[P @ RIGHT, P @ UP]


def depth(P):
    return float(np.mean(np.atleast_2d(P) @ VIEW))


def box(c, ex, ey, ez):
    """Faces (lists of 3D points) of an axis-aligned box centred at c, visible from VIEW."""
    h = np.array([ex, ey, ez]) / 2
    faces = []
    for ax in range(3):
        for sgn in (-1, 1):
            n = np.zeros(3)
            n[ax] = sgn
            if n @ VIEW <= 0:
                continue
            o = [a for a in range(3) if a != ax]
            pts = []
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = c.copy()
                p[ax] += sgn * h[ax]
                p[o[0]] += a * h[o[0]]
                p[o[1]] += b * h[o[1]]
                pts.append(p)
            faces.append((np.array(pts), n))
    return faces


def shade(rgb_hex, n, k0=0.68):
    light = np.array([0.3, -0.5, 1.0])
    light /= np.linalg.norm(light)
    t = k0 + (1 - k0) * max(0.0, float(n @ light))
    c = np.array([int(rgb_hex[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    return tuple(c * t)


# ------------------------------------------------------------------ hero figure
def build_hero(study, env, p):
    m = study.model
    s = governing(study)
    bags = study.bags
    g = p.si.model.g
    data = contact_q(study, s)
    qmax = max(float(d["q"].max()) for d in data.values())
    z0 = bags.z0
    depth_mm = 230.0                              # curtain depth at qmax
    k = depth_mm / qmax * 1e-3                    # m of curtain per N/m

    fig = R.new_figure(10.6, 7.2)
    fig.set_layout_engine("none")      # this figure places its own axes; constrained_layout
    ax = fig.add_axes([0.0, 0.06, 0.80, 0.86])     # finds no gridspec and warns otherwise
    ax.set_aspect("equal")
    ax.axis("off")
    items = []                                    # (depth, kind, artist-maker)

    # ground plane + footprint
    hull = bags.hull
    lo, hi = hull.min(0) - 0.12, hull.max(0) + 0.12
    gp = np.array([[lo[0], lo[1], z0], [hi[0], lo[1], z0], [hi[0], hi[1], z0], [lo[0], hi[1], z0]])
    ax.add_patch(_poly(proj(gp), fc="#f3f1ec", ec="none", z=0))
    fp = np.c_[hull, np.full(len(hull), z0)]
    ax.add_patch(_poly(proj(fp), fc="none", ec="#a9a7a1", lw=0.9, ls=(0, (4, 3)), z=0.5))

    # curtains (under the ground plane, drawn back to front), arrows, lift-off
    order = sorted(data, key=lambda mid: -depth(data[mid]["P"]))
    for zi, mid in enumerate(order):
        d = data[mid]
        P, q, on = d["P"], np.clip(d["q"], 0, None), d["on"]
        bot = P.copy()
        bot[:, 2] = z0 - k * q
        top2, bot2 = proj(P), proj(bot)
        col = Q_CMAP(0.35 + 0.65 * q / qmax)
        zc = 1 + zi * 0.01
        polys = [np.r_[top2[i:i + 2], bot2[i:i + 2][::-1]] for i in range(len(P) - 1)]
        cols = [Q_CMAP(0.25 + 0.75 * 0.5 * (q[i] + q[i + 1]) / qmax) for i in range(len(P) - 1)]
        ax.add_collection(PolyCollection(polys, facecolors=cols, edgecolors="none", alpha=0.85, zorder=zc))
        ax.plot(bot2[:, 0], bot2[:, 1], color=R.BLUE_RAMP[-1], lw=0.9, zorder=zc + 0.001)
        step = max(1, len(P) // max(2, int(np.ptp(d["s"]) / 0.06)))
        for i in range(0, len(P), step):
            if q[i] > 0.12 * qmax:
                a, b = bot2[i], top2[i]
                ax.annotate("", xy=b, xytext=a, zorder=zc + 0.002,
                            arrowprops=dict(arrowstyle="-|>,head_length=0.35,head_width=0.18",
                                            color="white", lw=0.9, shrinkA=0, shrinkB=1.5))
        # lift-off stretches: red under the beam
        off = ~on
        if off.any():
            e = P[-1] - P[0]
            e = e / np.linalg.norm(e)
            side = np.cross([0, 0, 1.0], e)
            side = side if side @ VIEW > 0 else -side            # the face towards the viewer
            edge = proj(P + side * 0.0127)
            seg = [edge[i:i + 2] for i in range(len(P) - 1) if off[i] and off[i + 1]]
            ax.add_collection(LineCollection(seg, colors=LIFT, lw=2.4, zorder=8.5, capstyle="round"))
    # beams (back to front) as shaded boxes
    beam_faces = []
    for mid in m.geo.base_members:
        if mid not in m.members:
            continue
        mem = m.members[mid]
        c = 0.5 * (mem.p0 + mem.p1)
        c = c.copy()
        c[2] = z0 + 0.0127
        e = np.abs(mem.p1 - mem.p0)
        ext = np.where(e > 1e-6, e, 0.0254)
        ext[2] = 0.0254
        for pts, n in box(c, *ext):
            beam_faces.append((depth(pts), pts, n, mid))
    for _, pts, n, _ in sorted(beam_faces, key=lambda t: t[0]):
        ax.add_patch(_poly(proj(pts), fc=shade("#cfcdc6", n), ec="#8f8d86", lw=0.5, z=7))
    # sandbags
    bag_faces = []
    for (mid, s0, L), P in zip(bags.stations, bags.points(m)):
        mem = m.members[mid]
        e = (mem.p1 - mem.p0) / mem.L
        ext = np.abs(e) * L + (1 - np.abs(e)) * 0.075
        ext[2] = 0.045
        c = P.copy()
        c[2] = z0 + 0.0254 + 0.0225
        for pts, n in box(c, *ext):
            bag_faces.append((depth(pts), pts, n))
        tp = proj(c + np.array([0, 0, 0.0225]))[0]
        ax.annotate(f"{bags.kg_each:.0f} kg", tp, xytext=(0, 9), textcoords="offset points", ha="center",
                    fontsize=R.FS_TEXT, color=BAG_EDGE, fontweight="bold", zorder=12, bbox=R.HALO)
    for _, pts, n in sorted(bag_faces, key=lambda t: t[0]):
        pp = _poly(proj(pts), fc=shade(BAG, n), ec=BAG_EDGE, lw=0.6, z=9)
        pp.set_alpha(0.82)
        ax.add_patch(pp)
    # thrust line (plan position), drawn from the ground up
    tp = m.thrust_point
    a, b = proj(np.array([tp[0], tp[1], z0])), proj(np.array([tp[0], tp[1], z0 + 0.42]))
    ax.plot([a[0, 0], b[0, 0]], [a[0, 1], b[0, 1]], color=R.INK, lw=1.0, ls=(0, (2, 2)), zorder=10)
    ax.annotate("", xy=b[0], xytext=b[0] - (b[0] - a[0]) * 0.25, zorder=10,
                arrowprops=dict(arrowstyle="-|>,head_length=0.6,head_width=0.3", color=R.INK, lw=1.4))
    ax.annotate(f"thrust line\n{s.loads.summary['thrust_factored_N']:.0f} N up, {tp[2] * 1e3:.0f} mm above",
                b[0], xytext=(6, 0), textcoords="offset points", fontsize=R.FS_SMALL, color=R.INK2,
                va="center", zorder=12)
    # member labels and peak q
    for mid, d in data.items():
        i = int(np.argmax(d["q"]))
        bot = d["P"][i].copy()
        bot[2] = z0 - k * max(d["q"][i], 0)
        if d["q"][i] > 0.25 * qmax:
            ax.annotate(f"{d['q'][i] / 1e3:.1f} kN/m", proj(bot)[0], xytext=(0, -3), textcoords="offset points",
                        ha="center", va="top", fontsize=R.FS_SMALL, color=R.BLUE_RAMP[-1], zorder=13, bbox=R.HALO)
        end = d["P"][-1] if (d["P"][-1] - d["P"][0]) @ RIGHT >= 0 else d["P"][0]
        ax.annotate(f"M{mid}", proj(end + np.array([0, 0, 0.03]))[0], xytext=(4, 2), textcoords="offset points",
                    fontsize=R.FS_SMALL, color=R.INK2, zorder=13)
    ax.autoscale_view()
    ax.margins(0.03)

    # side panel: numbers
    Fz = s.ground_F[:, 2]
    on = np.array(s.contact)
    H = np.hypot(s.ground_F[:, 0].sum(), s.ground_F[:, 1].sum())
    mu = p.si.ground.mu
    lines = [
        ("case", s.key),
        ("ground reaction", f"{Fz.sum():.0f} N up"),
        ("  = bags", f"{bags.total_kg * g:.0f} N ({len(bags.stations)} × {bags.kg_each:.0f} kg)"),
        ("  + stand & rocket", f"{-(s.loads.applied_resultant[2] - s.loads.summary['thrust_factored_N']):.0f} N"),
        ("  − thrust", f"{s.loads.summary['thrust_factored_N']:.0f} N"),
        ("peak pressure", f"{qmax / 1e3:.1f} kN/m"),
        ("beam in contact", f"{100 * on.mean():.0f} %"),
        ("sliding", f"H {H:.0f} N ≤ μN {mu * Fz.sum():.0f} N"),
        ("lowest base-joint SF", f"{base_joint_sf(study, s):.2f}"),
    ]
    tx = fig.add_axes([0.79, 0.30, 0.20, 0.58])
    tx.axis("off")
    for i, (k_, v) in enumerate(lines):
        y = 1 - i * 0.075
        tx.text(0, y, k_, fontsize=R.FS_TEXT, color=R.INK2, va="top", transform=tx.transAxes)
        tx.text(1, y, v, fontsize=R.FS_TEXT, color=R.INK, va="top", ha="right", transform=tx.transAxes,
                fontweight="bold" if i in (1, 5, 8) else "normal")
    # legend + pressure scale
    lg = fig.add_axes([0.79, 0.07, 0.20, 0.22])
    lg.axis("off")
    hs = [Patch(fc=Q_CMAP(0.8), ec="none", label="ground pressure q (depth ∝ q)"),
          Line2D([], [], color=LIFT, lw=3, label="lift-off (gap opens)"),
          Patch(fc=BAG, ec=BAG_EDGE, label="sandbag"),
          Line2D([], [], color="#a9a7a1", lw=1, ls=(0, (4, 3)), label="tipping footprint")]
    lg.legend(handles=hs, loc="upper left", frameon=False, fontsize=R.FS_SMALL)
    R.title(fig, "Ground Reaction on the Base")
    R.note(fig, f"Base on compression-only springs (k_s = {s.k_s / 1e6:.0f} MN/m³, compacted gravel, "
                f"{p.si.ground.contact_width * 1e3:.1f} mm contact width); "
                f"curtain depth under each beam = contact pressure; governing case = lowest base-joint SF.")
    return fig


def _poly(xy, fc, ec, lw=0.6, ls="-", z=1):
    from matplotlib.patches import Polygon
    return Polygon(xy, closed=True, facecolor=fc, edgecolor=ec, lw=lw, ls=ls, zorder=z, joinstyle="round")


# ------------------------------------------------------------------ small multiples
def build_cases(study, env, p):
    m = study.model
    bags = study.bags
    sols = [s for s in study.solves if s.valid and s.run.name == "R" and s.run.bearing and s.ground_F is not None]
    if not sols:
        sols = [s for s in study.solves if s.valid and s.ground_F is not None]
    allq = [contact_q(study, s) for s in sols]
    qmax = max(float(d["q"].max()) for dd in allq for d in dd.values())
    norm = Normalize(0, qmax)
    n = len(sols)
    cols = 3
    rows = int(np.ceil(n / cols))
    span = np.ptp(bags.hull, axis=0)
    pw = 10.6 * 0.86 / cols
    ph = pw * span[1] / span[0] * 1.12 + 0.35
    fig = R.new_figure(10.6, ph * rows + 1.1)
    gs = fig.add_gridspec(rows, cols)
    hull = bags.hull * 1e3
    bp = bags.points(m) * 1e3
    tp = m.thrust_point * 1e3
    for i, (s, data) in enumerate(zip(sols, allq)):
        ax = fig.add_subplot(gs[i // cols, i % cols])
        ax.set_aspect("equal")
        ax.axis("off")
        ax.fill(hull[:, 0], hull[:, 1], fc="#f3f1ec", ec="#a9a7a1", lw=0.7, ls=(0, (4, 3)), zorder=0)
        for (mid, s0, L), P in zip(bags.stations, bp):
            mem = m.members[mid]
            e = (mem.p1 - mem.p0) / mem.L
            ext = (np.abs(e) * L + (1 - np.abs(e)) * 0.12) * 1e3
            ax.add_patch(_poly(np.array([[P[0] - ext[0] / 2, P[1] - ext[1] / 2], [P[0] + ext[0] / 2, P[1] - ext[1] / 2],
                                         [P[0] + ext[0] / 2, P[1] + ext[1] / 2], [P[0] - ext[0] / 2, P[1] + ext[1] / 2]]),
                               fc=BAG, ec=BAG_EDGE, lw=0.5, z=1))
        for mid, d in data.items():
            xy = d["P"][:, :2] * 1e3
            segs = np.stack([xy[:-1], xy[1:]], axis=1)
            qq = 0.5 * (d["q"][:-1] + d["q"][1:])
            onn = d["on"][:-1] & d["on"][1:]
            ax.add_collection(LineCollection(segs[onn], colors=Q_CMAP(0.15 + 0.85 * norm(qq[onn])), lw=5.5,
                                             capstyle="butt", zorder=3))
            if (~onn).any():
                ax.add_collection(LineCollection(segs[~onn], colors=LIFT, lw=1.6, linestyles=(0, (2, 1.5)), zorder=3))
        ax.plot(tp[0], tp[1], marker="+", ms=9, mew=1.6, color=R.INK, zorder=5)
        on = np.array(s.contact)
        ax.set_title(f"{s.case}", fontsize=R.FS_LABEL, color=R.INK, loc="left", fontweight="bold")
        ax.text(1, 1.02, f"contact {100 * on.mean():.0f} % · peak {max(d['q'].max() for d in data.values()) / 1e3:.1f} kN/m"
                         f" · base-joint SF {base_joint_sf(study, s):.2f}", transform=ax.transAxes, ha="right",
                va="bottom", fontsize=R.FS_SMALL, color=R.INK2)
        ax.autoscale_view()
        ax.margins(0.04)
    from matplotlib.cm import ScalarMappable
    cb = fig.colorbar(ScalarMappable(norm=Normalize(0, qmax / 1e3), cmap=Q_CMAP), ax=fig.axes,
                      shrink=0.55, fraction=0.025, pad=0.01, aspect=22)
    cb.set_label("ground pressure q (kN/m)", fontsize=R.FS_SMALL)
    cb.outline.set_visible(False)
    R.title(fig, "Ground Reaction by Load Case (plan)")
    R.note(fig, f"Run {sols[0].run.label}; red dashed = lift-off; + = thrust line; tan = sandbags "
                f"({len(bags.stations)} × {bags.kg_each:.0f} kg); grey = tipping footprint.")
    return fig


def figures(study, env, p):
    if not study.model.ground_mode or study.bags is None:
        return []
    return [("ground_reaction", lambda: build_hero(study, env, p)),
            ("ground_by_case", lambda: build_cases(study, env, p))]


if __name__ == "__main__":
    R.main(figures)
