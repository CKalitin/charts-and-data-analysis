"""Correct front/behind rendering for 3D lines that pass around a solid body.

WHAT PROBLEM THIS SOLVES
========================
mplot3d has no depth buffer. It paints one whole artist at a time, ordered by a
single depth number per artist, so a curve that is *partly* in front of and
*partly* behind a surface can only ever be painted entirely in front of, or
entirely behind, it. An orbit around a planet is the canonical case: the near
half must occlude the planet, the far half must be occluded by it -- one artist
cannot do both.

And it is worse than a coin-flip. With the default ``computed_zorder=True``,
``Axes3D.draw`` depth-sorts only *Collections and Patches*. ``ax.plot`` on a 3D
axes makes a ``Line3D``, which subclasses ``Line2D`` -- not a Collection -- so it
never enters that sort and keeps the default line zorder of 2, while every
surface is re-assigned a zorder above it (2.5 and up). The outcome is therefore
deterministic and independent of geometry:

    **a 3D line is ALWAYS painted behind EVERY surface.**

That is why an orbit drawn around a translucent planet reads as if the entire
orbit were behind the planet -- including the half that is unambiguously in
front of it.

THE FIX
=======
Three steps, all of them in ``apply_depth_order`` (the only call a chart needs):

1. Switch the axes to ``computed_zorder=False`` and re-assign the surfaces'
   zorders explicitly, in matplotlib's own back-to-front depth order. Nothing
   about the surfaces changes visually; the ordering is just now *ours*, so
   explicit zorders stick instead of being overwritten on every draw.
2. Split every 3D line where it crosses the silhouette of an occluding body,
   inserting the exact crossing point (found by bisection) into both pieces so
   they meet with no gap.
3. Paint each piece at a zorder just above the occluders it is in front of, or
   just below the one that hides it.

THE OCCLUSION TEST
==================
A point is hidden by a body exactly when the straight segment from the point to
the *camera centre* passes through that body. Projection is a projective map, so
the set of points that land on one screen pixel is exactly a line through the
camera centre -- which means this test can be done in DATA coordinates and is
still exact under non-equal axis limits, a non-cubic ``set_box_aspect``, roll,
and perspective. See ``camera_from_axes`` for how the camera is recovered from
``ax.get_proj()`` alone (no matplotlib internals, no re-deriving the view
matrix, so it cannot drift out of sync with the axes).

USAGE
=====
    import depth3d

    surf = ax.plot_surface(x, y, z, color="C0", alpha=0.55)   # keep the artist
    ax.plot(orbit[:, 0], orbit[:, 1], orbit[:, 2], color="C1")
    ...
    ax.set_xlim(...); ax.set_ylim(...); ax.set_zlim(...)      # limits + view MUST
    ax.set_box_aspect([1, 1, 1]); ax.view_init(elev, azim)    # be final first

    earth = depth3d.Occluder(depth3d.Sphere(center=(0, 0, 0), radius=R), artist=surf)
    depth3d.apply_depth_order(ax, [earth])                    # then legend, etc.

Call it AFTER every artist is drawn and the view is final (it reads
``ax.get_proj()``), and BEFORE ``ax.legend()`` so the legend picks up the split
pieces. It is idempotent: pieces it created are marked and never re-split.

Bodies that are not spheres use ``Mesh.from_surface(X, Y, Z)`` -- pass the very
arrays you handed to ``plot_surface`` and the occlusion matches the drawn facets
exactly. ``Sphere`` is the analytic (and much faster) special case.

WHAT IS AND IS NOT HANDLED
==========================
- ``ax.plot`` lines (``Line3D``): split automatically. This is the main event.
- ``ax.scatter`` (``Path3DCollection``): zorder set from the occlusion test when
  all of its points agree (the usual single-marker case); a scatter that
  straddles a silhouette warns and is left to the depth sort -- draw those as
  two scatter calls.
- ``ax.quiver`` / other Line3DCollections and all surfaces: left to the
  back-to-front depth sort, which is what matplotlib itself does. A surface that
  intersects another surface still cannot be resolved by a painter's algorithm
  -- that is a property of mplot3d, not of this module.
- Log-scaled 3D axes are not supported (a sphere is not a sphere on a log axis).
- Each piece keeps the caller's ``solid_capstyle``. matplotlib's default,
  'projecting', makes every piece overhang the crossing by half a linewidth, so
  the near-side piece paints ~1 px past the true limb. Harmless at normal line
  widths; pass ``solid_capstyle="butt"`` if you want the split pixel-exact.

VERIFYING
=========
``depth3d_selftest.py`` (shipped alongside this module in the charting-and-modeling
skill) checks the camera against matplotlib's own projection and then reads back
RENDERED PIXELS over 72 view/projection/limit combinations, with a control run
that confirms the same checks fail when the fix is switched off. Run it after any
edit here.

TUNING
======
ZORDER_BASE / ZORDER_STEP   the band the surfaces are packed into. Kept below the
                            default Line2D zorder of 2 so unmanaged artists, the
                            3D text labels (3) and the legend (5) stay on top.
BISECT_ITERS                halvings used to place a silhouette crossing.
MESH_CHUNK                  points per ray/triangle batch (caps peak memory).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np

# --- Tunables (sensible defaults; override via the function kwargs) --------------------
ZORDER_BASE = 1.0     # zorder of the farthest surface
ZORDER_STEP = 0.1     # gap between consecutive surfaces in the depth sort
BISECT_ITERS = 40     # 40 halvings of a segment == exact to float64 for any real chart
MESH_CHUNK = 256      # points per ray/triangle batch (caps peak memory at N*T*3 floats)


# ============================== the camera ============================================

@dataclass(frozen=True)
class Camera:
    """The camera centre in DATA coordinates, as a homogeneous point (x, y, z, w).

    w != 0 -> a finite eye at vec[:3]/w   (perspective; mplot3d's default)
    w == 0 -> a direction at infinity     (orthographic, ``proj_type='ortho'``)

    ``direction_from(p)`` returns a vector from p toward the eye that is correct
    for both cases, so nothing downstream ever branches on the projection type.
    """

    vec: np.ndarray

    def direction_from(self, points) -> np.ndarray:
        p = np.asarray(points, dtype=float)
        return self.vec[:3] - self.vec[3] * p


def camera_from_axes(ax) -> Camera:
    """Recover the camera from the axes' own projection matrix ``ax.get_proj()``.

    The camera centre C is the one point whose image is undefined: every viewing
    ray runs through it, so its projected x, y and w all vanish. C therefore
    spans the null space of rows 0, 1 and 3 of the 4x4 projection matrix -- true
    for BOTH projection types (for 'ortho' it comes out as the direction at
    infinity, w = 0). Deriving it from the matrix the axes actually projects
    with means axis ranges, box aspect, elev/azim/roll and the perspective focal
    length are all accounted for by construction, and nothing here can drift out
    of sync with a future matplotlib.
    """
    M = np.asarray(ax.get_proj(), dtype=float)
    if M.shape != (4, 4):
        raise ValueError(f"expected a 4x4 projection matrix, got {M.shape}")
    vec = np.linalg.svd(M[[0, 1, 3], :])[2][-1]

    # The SVD fixes the sign arbitrarily, and the sign is what says which way is
    # "toward the camera". Take it from the depth gradient along the viewing ray,
    # in closed form: a point at parameter t is the homogeneous combination
    # (1 - t*w_C) * X + t * C of the point X = [p, 1] and the camera C, and since
    # row 3 of M annihilates C the depth works out to
    #     tz(t) = tz(0) + (t / (1 - t*w_C)) * (M[2] @ C) / (M[3] @ X),
    # whose derivative at t = 0 is (M[2] @ C) / (M[3] @ X). M[3] @ X is positive
    # for anything in front of the camera, so depth (larger == farther) decreases
    # toward the camera exactly when M[2] @ C is negative.
    if M[2] @ vec > 0:
        vec = -vec
    return Camera(vec=vec)


# ============================== shapes ================================================

def _as_points(points) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    if p.ndim == 1:
        p = p[None, :]
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError(f"expected (N, 3) points, got shape {np.shape(points)}")
    return p


@dataclass(frozen=True)
class Sphere:
    """A solid ball. The analytic (and fastest) occluder -- exact, no faceting."""

    center: tuple = (0.0, 0.0, 0.0)
    radius: float = 1.0

    def hidden(self, points, camera: Camera) -> np.ndarray:
        """True where the segment from the point toward the camera enters the ball."""
        p = _as_points(points)
        d = camera.direction_from(p)
        r = p - np.asarray(self.center, dtype=float)
        a = np.einsum("ij,ij->i", d, d)
        b = 2.0 * np.einsum("ij,ij->i", r, d)
        c = np.einsum("ij,ij->i", r, r) - float(self.radius) ** 2
        disc = b * b - 4.0 * a * c
        ok = (disc > 0.0) & (a > 0.0)
        with np.errstate(divide="ignore", invalid="ignore"):
            t_far = (-b + np.sqrt(np.where(ok, disc, 0.0))) / (2.0 * a)
            # A point *inside* the ball has t_far > 0 too, and is indeed hidden.
            # The length guard only rejects a grazing self-hit for a curve lying
            # exactly on the surface.
            reach = t_far * np.sqrt(a)
        return ok & (reach > 1e-9 * float(self.radius))


@dataclass
class Mesh:
    """An arbitrary triangle-soup occluder, (T, 3, 3): T triangles x 3 vertices x xyz.

    Build it from the same arrays you passed to ``plot_surface`` and the occlusion
    matches the facets that are actually painted, exactly. Prefer ``Sphere`` for a
    ball -- it is analytic and about an order of magnitude cheaper.
    """

    triangles: np.ndarray

    def __post_init__(self):
        tri = np.asarray(self.triangles, dtype=float).reshape(-1, 3, 3)
        self.triangles = tri
        self._v0 = tri[:, 0]
        self._e1 = tri[:, 1] - tri[:, 0]
        self._e2 = tri[:, 2] - tri[:, 0]
        flat = tri.reshape(-1, 3) if tri.size else np.zeros((1, 3))
        lo, hi = flat.min(axis=0), flat.max(axis=0)
        # Bounding sphere, for a cheap conservative reject; and a length scale for
        # the "don't count a hit at zero distance" guard.
        mid = 0.5 * (lo + hi)
        radius = float(np.linalg.norm(flat - mid, axis=1).max()) * (1.0 + 1e-9)
        self._bound = Sphere(tuple(mid), radius)
        self._eps_len = 1e-9 * (float(np.linalg.norm(hi - lo)) or 1.0)

    @classmethod
    def from_surface(cls, X, Y, Z) -> "Mesh":
        """Triangulate a plot_surface-style (n, m) coordinate grid."""
        P = np.stack([np.asarray(X, float), np.asarray(Y, float), np.asarray(Z, float)], axis=-1)
        if P.ndim != 3:
            raise ValueError("X, Y, Z must be 2D grids of the same shape")
        a, b, c, d = P[:-1, :-1], P[1:, :-1], P[1:, 1:], P[:-1, 1:]
        tris = np.concatenate([np.stack([a, b, c], axis=-2).reshape(-1, 3, 3),
                               np.stack([a, c, d], axis=-2).reshape(-1, 3, 3)])
        return cls(triangles=tris)

    def hidden(self, points, camera: Camera) -> np.ndarray:
        """True where the segment from the point toward the camera hits a triangle
        (Moller-Trumbore, batched over points to cap memory)."""
        p = _as_points(points)
        out = np.zeros(len(p), dtype=bool)
        if self.triangles.size == 0:
            return out

        # A ray that misses the bounding sphere cannot hit a triangle. For the usual
        # case -- a curve looping around a body -- that rejects most points up front
        # and changes no answer.
        maybe = np.flatnonzero(self._bound.hidden(p, camera))
        v0, e1, e2 = self._v0, self._e1, self._e2
        for s in range(0, len(maybe), MESH_CHUNK):
            idx = maybe[s:s + MESH_CHUNK]
            q = p[idx]
            d = camera.direction_from(q)                          # (n, 3)
            h = np.cross(d[:, None, :], e2[None, :, :])           # (n, T, 3)
            det = np.einsum("ntk,tk->nt", h, e1)
            sv = q[:, None, :] - v0[None, :, :]                   # (n, T, 3)
            qv = np.cross(sv, e1[None, :, :])
            with np.errstate(divide="ignore", invalid="ignore"):
                inv = 1.0 / det                                   # parallel -> inf/nan,
                u = inv * np.einsum("ntk,ntk->nt", sv, h)         # every test below then
                v = inv * np.einsum("ntk,nk->nt", qv, d)          # fails, which is right
                t = inv * np.einsum("ntk,tk->nt", qv, e2)
                reach = t * np.linalg.norm(d, axis=1)[:, None]
                hit = (u >= 0.0) & (u <= 1.0) & (v >= 0.0) & (u + v <= 1.0) \
                    & (reach > self._eps_len)
            out[idx] = hit.any(axis=1)
        return out


@dataclass
class Occluder:
    """A solid body plus the artist that draws it.

    The artist is what ties the geometry to a zorder: pieces of curve hidden by
    this body are painted just under ``artist``, the rest just over it. Pass an
    explicit ``zorder`` instead if the body has no single artist.
    """

    shape: object
    artist: object = None
    zorder: float | None = None

    def resolved_zorder(self) -> float:
        if self.zorder is not None:
            return float(self.zorder)
        if self.artist is not None:
            return float(self.artist.get_zorder())
        raise ValueError("Occluder needs either an artist or an explicit zorder")


# ============================== zorder assignment =====================================

def _front_zorder(occluders, front_zorder, step) -> float:
    if front_zorder is not None:
        return float(front_zorder)
    if not occluders:
        return 2.0
    return max(o.resolved_zorder() for o in occluders) + step / 2.0


def zorders_for_points(points, occluders, camera, front_zorder=None, step=ZORDER_STEP):
    """Per-point zorder: just above every occluder for a visible point, just below
    the frontmost body that hides it otherwise."""
    p = _as_points(points)
    front = _front_zorder(occluders, front_zorder, step)
    z = np.full(len(p), front, dtype=float)
    if not occluders:
        return z
    masks = np.array([o.shape.hidden(p, camera) for o in occluders])          # (K, N)
    zocc = np.array([o.resolved_zorder() for o in occluders], dtype=float)
    blocked = masks.any(axis=0)
    behind = np.where(masks, zocc[:, None], np.inf).min(axis=0) - step / 2.0
    z[blocked] = behind[blocked]
    return z


# ============================== splitting =============================================

@dataclass
class Segment:
    """One run of a polyline that can be painted as a single artist."""

    points: np.ndarray
    zorder: float
    hidden: bool
    real: np.ndarray = field(repr=False)   # False where a vertex is an inserted crossing


def densify(points, factor: int) -> np.ndarray:
    """Linearly subdivide each span `factor` ways. Only needed when a polyline is
    sampled so coarsely that it could duck behind a body and back out again
    between two consecutive vertices."""
    p = _as_points(points)
    if factor <= 1 or len(p) < 2:
        return p
    t = np.linspace(0.0, 1.0, factor + 1)[:-1]
    mid = p[:-1, None, :] + t[None, :, None] * (p[1:] - p[:-1])[:, None, :]
    return np.vstack([mid.reshape(-1, 3), p[-1]])


def split_polyline(points, occluders, camera, *, front_zorder=None, step=ZORDER_STEP,
                   densify_factor=1, bisect_iters=BISECT_ITERS):
    """Split a polyline into runs of constant zorder, with the silhouette crossings
    inserted so consecutive runs share an endpoint (no visible gap)."""
    p = densify(points, densify_factor)
    front = _front_zorder(occluders, front_zorder, step)
    z = zorders_for_points(p, occluders, camera, front, step)
    if len(p) < 2:
        return [Segment(p, float(z[0]) if len(z) else front,
                        bool(len(z) and z[0] != front), np.ones(len(p), bool))]

    cuts = np.flatnonzero(z[:-1] != z[1:])
    # One crossing point per cut, shared by the runs on both sides of it, so the
    # two pieces meet exactly and the curve shows no gap at the silhouette.
    crossings = [_crossing(p[i], p[i + 1], z[i], z[i + 1], occluders, camera, front, step,
                           bisect_iters) for i in cuts]
    bounds = [0, *(cuts + 1), len(p)]
    segments = []
    for k in range(len(bounds) - 1):
        i0, i1 = bounds[k], bounds[k + 1]
        block, real = [p[i0:i1]], [np.ones(i1 - i0, dtype=bool)]
        if k > 0:                                   # crossing shared with the previous run
            block.insert(0, crossings[k - 1][None, :])
            real.insert(0, np.zeros(1, dtype=bool))
        if k < len(bounds) - 2:                     # crossing shared with the next run
            block.append(crossings[k][None, :])
            real.append(np.zeros(1, dtype=bool))
        segments.append(Segment(np.vstack(block), float(z[i0]), bool(z[i0] != front),
                                np.concatenate(real)))
    return segments


def _crossing(p_lo, p_hi, z_lo, z_hi, occluders, camera, front, step, iters):
    """Bisect the span p_lo..p_hi (whose ends have different zorders) for the point
    where the zorder changes. Assumes ONE change in the span, which is why a very
    coarsely sampled polyline wants ``densify_factor``."""
    lo, hi = 0.0, 1.0
    delta = np.asarray(p_hi, float) - np.asarray(p_lo, float)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        z_mid = zorders_for_points(p_lo + mid * delta, occluders, camera, front, step)[0]
        if z_mid == z_lo:
            lo = mid
        elif z_mid == z_hi:
            hi = mid
        else:                    # a third state in between: keep bisecting the lo side
            hi = mid
    return p_lo + 0.5 * (lo + hi) * delta


# ============================== drawing ===============================================

_LINE_PROPS = ("color", "linewidth", "linestyle", "alpha", "marker", "markersize",
               "markerfacecolor", "markeredgecolor", "markeredgewidth", "drawstyle",
               "solid_capstyle", "solid_joinstyle", "dash_capstyle", "dash_joinstyle",
               "antialiased", "label")


def _has_marker(style) -> bool:
    return style.get("marker") not in (None, "None", "none", "", " ")


def plot_occluded(ax, points, occluders, *, camera=None, hidden_kwargs=None,
                  front_zorder=None, step=ZORDER_STEP, densify_factor=1, **kwargs):
    """``ax.plot`` for a 3D polyline, split so the parts in front of the occluding
    bodies are painted over them and the parts behind are painted under them.

    ``hidden_kwargs`` restyles only the hidden pieces (e.g.
    ``dict(alpha=0.35, linestyle=":")``); by default they keep the same style and
    are simply painted in the right place.
    """
    camera = camera if camera is not None else camera_from_axes(ax)
    segments = split_polyline(points, occluders, camera, front_zorder=front_zorder,
                              step=step, densify_factor=densify_factor)
    label = kwargs.pop("label", None)
    # One legend entry for the whole curve: put it on the first visible piece.
    label_at = next((i for i, s in enumerate(segments) if not s.hidden), 0)

    lines = []
    for i, seg in enumerate(segments):
        kw = dict(kwargs)
        if seg.hidden and hidden_kwargs:
            kw.update(hidden_kwargs)
        kw["zorder"] = seg.zorder
        kw["label"] = label if i == label_at else None
        if _has_marker(kw):
            # Inserted crossing points are not data: don't put a marker on them.
            kw["markevery"] = list(np.flatnonzero(seg.real))
        line, = ax.plot(seg.points[:, 0], seg.points[:, 1], seg.points[:, 2], **kw)
        line._depth3d_split = True
        lines.append(line)
    return lines


def _axes_children(ax):
    try:
        return list(ax._children)          # what Axes3D.draw itself iterates
    except AttributeError:                 # very old matplotlib
        return [*ax.lines, *ax.collections, *ax.patches]


def split_lines(ax, occluders, *, camera=None, hidden_kwargs=None, front_zorder=None,
                step=ZORDER_STEP, densify_factor=1, skip=()):
    """Re-draw every Line3D already on `ax` as occlusion-split pieces.

    Automatic so that a chart cannot forget a curve. Idempotent: pieces this
    created are marked and never re-split. Style, label and markers are carried
    over (markers stay on real vertices only).
    """
    from mpl_toolkits.mplot3d.art3d import Line3D

    camera = camera if camera is not None else camera_from_axes(ax)
    skip = set(map(id, skip))
    targets = [a for a in _axes_children(ax)
               if isinstance(a, Line3D) and a.get_visible()
               and not getattr(a, "_depth3d_split", False) and id(a) not in skip]

    out = []
    for line in targets:
        verts = np.asarray(line._verts3d, dtype=float).T
        if len(verts) == 0:
            continue                      # empty line: nothing to place
        style = {k: getattr(line, "get_" + k)() for k in _LINE_PROPS}
        line.remove()
        out.extend(plot_occluded(ax, verts, occluders, camera=camera,
                                 hidden_kwargs=hidden_kwargs, front_zorder=front_zorder,
                                 step=step, densify_factor=densify_factor, **style))
    return out


def sort_scene(ax, base=ZORDER_BASE, step=ZORDER_STEP):
    """Freeze matplotlib's own back-to-front ordering of the surfaces into explicit
    zorders, and turn ``computed_zorder`` off so they stick.

    Nothing about the surfaces changes visually -- this only moves the decision
    from matplotlib's per-draw sort (which overwrites any zorder we set) to ours.
    Returns the artists, farthest first.
    """
    from matplotlib.collections import Collection
    from matplotlib.patches import Patch

    ax.computed_zorder = False
    ax.M = ax.get_proj()
    try:
        ax.invM = np.linalg.inv(ax.M)
    except np.linalg.LinAlgError:
        pass

    items = [a for a in _axes_children(ax)
             if isinstance(a, (Collection, Patch)) and a.get_visible()
             and hasattr(a, "do_3d_projection")]
    depths = []
    for a in items:
        try:
            d = a.do_3d_projection()
        except TypeError:                     # matplotlib < 3.5 took the matrix
            d = a.do_3d_projection(ax.M)
        depths.append(float(d) if np.isfinite(d) else np.inf)
    order = np.argsort(-np.asarray(depths), kind="stable")     # farthest painted first
    for k, i in enumerate(order):
        items[i].set_zorder(base + k * step)
    return [items[i] for i in order]


def _fix_scatter_zorders(ax, occluders, camera, step):
    from mpl_toolkits.mplot3d.art3d import Path3DCollection

    for coll in _axes_children(ax):
        if not isinstance(coll, Path3DCollection) or not coll.get_visible():
            continue
        offsets = getattr(coll, "_offsets3d", None)
        if offsets is None:
            continue
        pts = np.asarray(offsets, dtype=float).T
        if len(pts) == 0:
            continue
        z = zorders_for_points(pts, occluders, camera, step=step)
        if np.all(z == z[0]):
            coll.set_zorder(float(z[0]))
        else:
            warnings.warn(
                "depth3d: a 3D scatter straddles a body's silhouette; one collection "
                "can only have one zorder. Draw the hidden and visible points as two "
                "separate ax.scatter calls to place both correctly.", stacklevel=3)


def apply_depth_order(ax, occluders, *, hidden_kwargs=None, base=ZORDER_BASE,
                      step=ZORDER_STEP, densify_factor=1, sort=True, scatter=True,
                      skip=()):
    """The one call a 3D chart makes. Run it after every artist is drawn and the
    limits / box aspect / view angle are final, and before ``ax.legend()``.

    Returns the Line3D pieces that replaced the original curves.
    """
    if sort:
        sort_scene(ax, base=base, step=step)
    camera = camera_from_axes(ax)
    lines = split_lines(ax, occluders, camera=camera, hidden_kwargs=hidden_kwargs,
                        step=step, densify_factor=densify_factor, skip=skip)
    if scatter:
        _fix_scatter_zorders(ax, occluders, camera, step)
    return lines
