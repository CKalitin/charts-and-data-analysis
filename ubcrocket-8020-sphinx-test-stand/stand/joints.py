"""Bracket (joint) checks: transfer each spring wrench to every leg / bolt group.

Wrench transfer is plain statics: a force F acting at the joint point X with
moment M_X has, about a bolt point P,  M_P = M_X + (X - P) x F.

Leg frame: x along that member's slot, y across the slot in the face plane,
z = bolt axis out of the face (+z = pull-off, i.e. the bracket pulls the member
towards itself).

Triangle (L) bracket, one bolt per leg (allowables per leg)
    shear  sqrt(Fx^2+Fy^2) <= mu*F_i          pull  Fz <= F_i
    Mx, My <= F_i*a  (gap opening)            Mz <= mu*F_i*r_f  (twist about the bolt)
T plate (plate_t5): rigid-plate bolt groups (A: 3 bolts on a, B: 2 bolts on b)
    in-plane bolt force   f_i = F/n + M_n (n x r_i)/sum r^2      <= mu*F_i
    out-of-plane          F_z,i = F_z/n + ((n x M).r_i)/sum r^2  <= F_i
    plate bending         M <= sigma_y,p * b_net * t^2 / 6 per section
U = linear sum of the term utilisations; SF = 1/U.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np

from .geometry import face_vector
from .model import BracketSpring, StandModel

U_TERMS = ["U_shear", "U_pull", "U_Mx", "U_My", "U_Mz", "U_bend_line", "U_bend_stem"]


# --------------------------------------------------------------------------- capacities
@dataclass
class Caps:
    F_fric: float
    F_pull: float
    M_tilt: float           # triangle Mx,max = My,max
    M_twist: float          # triangle Mz,max
    r_f: float
    plate_M_line_A: float
    plate_M_line_B: float
    plate_M_lower_hole: float
    plate_M_neck: float
    v_neck: float
    sections: dict = field(default_factory=dict)   # b_net values, for the report


def plate_width(v: float, pl) -> float:
    """Plate outline width (along u) at height v."""
    h = pl.base_half_height
    if abs(v) <= h + 1e-12:
        return pl.base_width
    if v <= pl.stem_taper_end_v:
        f = (v - h) / (pl.stem_taper_end_v - h)
        return pl.base_width + f * (pl.stem_width - pl.base_width)
    return pl.stem_width


def capacities(p) -> Caps:
    b, tri, pl = p.si.bolts, p.si.triangle, p.si.plate
    ri, ro = b.hole_radius, b.head_radius
    r_f = 2 / 3 * (ro**3 - ri**3) / (ro**2 - ri**2)
    d = 2 * ri
    fy_t2_6 = pl.fy * pl.thickness**2 / 6             # N·m per metre of section width
    bA = pl.base_width - len(pl.groupA_u) * d         # along bolt line A
    bB = (pl.top_edge_v - pl.base_half_height) - len(pl.groupB_v) * d   # along bolt line B (stem)
    b_low = plate_width(min(pl.groupB_v), pl) - d     # across the stem through the lower hole
    b_neck = plate_width(pl.base_half_height, pl)     # across the stem where it meets the base
    return Caps(
        F_fric=b.mu * b.preload, F_pull=b.preload,
        M_tilt=b.preload * tri.tilt_arm,
        M_twist=b.M_twist if b.M_twist > 0 else b.mu * b.preload * r_f, r_f=r_f,
        plate_M_line_A=fy_t2_6 * bA, plate_M_line_B=fy_t2_6 * bB,
        plate_M_lower_hole=fy_t2_6 * b_low, plate_M_neck=fy_t2_6 * b_neck,
        v_neck=pl.base_half_height,
        sections={"b_net_A_line": bA, "b_net_B_line": bB, "b_net_B_lower_hole": b_low,
                  "b_neck": b_neck, "hole_dia": d},
    )


# hand values quoted in the brief, shown next to the computed ones in the report
SPEC_QUOTED_SECTIONS = {"b_net_A_line": 76.2e-3 - 3 * 7.14e-3, "b_net_B_line": 36.5e-3,
                        "b_net_B_lower_hole": 56.4e-3}


# --------------------------------------------------------------------------- leg geometry
@dataclass
class Leg:
    """One leg (triangle) or bolt group (plate) of one bracket, for one corner option."""
    name: str               # "a" | "b" | "A" | "B"
    member: int
    on_side_b: bool         # wrench on this member = +W_b (else -W_b)
    P: np.ndarray           # bolt point / group centroid
    frame: np.ndarray       # rows: x (slot), y, z (bolt axis, +pull)
    bolts: np.ndarray | None = None     # (n, 3) plate bolt points
    stem_v: np.ndarray | None = None    # plate group B: bolt v coords along e_b
    e_b: np.ndarray | None = None


@dataclass
class LegOption:
    desc: str
    legs: list[Leg]


def _dirs(model: StandModel, mid: int, node: int, ext: float) -> list[np.ndarray]:
    m = model.geom(mid)
    s = model.node_s[node]
    out = []
    if m.L - s >= ext:
        out.append(m.e)
    if s >= ext:
        out.append(-m.e)
    return out or [m.e, -m.e]


def _perp(v, axis):
    w = v - (v @ axis) * axis
    return w / np.linalg.norm(w)


def _closest_on_line_a(pa, ea, pb, eb) -> np.ndarray:
    """Point on line a closest to line b."""
    w = pa - pb
    a, b, c, d, e = ea @ ea, ea @ eb, eb @ eb, ea @ w, eb @ w
    den = a * c - b * b
    if abs(den) < 1e-12:
        return pa
    s = (b * e - c * d) / den
    return pa + s * ea


def _sgn(v: np.ndarray) -> str:
    k = int(np.argmax(np.abs(v)))
    return ("+" if v[k] > 0 else "-") + "xyz"[k]


def prepare(model: StandModel, p) -> None:
    """Attach leg geometry options to every bracket spring (once per model)."""
    tri, pl = p.si.triangle, p.si.plate
    for br in model.brackets:
        ma, mb = model.geom(br.a), model.geom(br.b)
        da = _dirs(model, br.a, br.na, tri.min_leg_extent)
        db = _dirs(model, br.b, br.nb, tri.min_leg_extent)
        opts = []
        if br.type == "triangle":
            for ea, eb in product(da, db):
                if abs(ea @ eb) > 0.95:
                    continue
                Pa, Pb = br.X + tri.bolt_from_corner * ea, br.X + tri.bolt_from_corner * eb
                za, zb = _perp(eb, ma.e), _perp(ea, mb.e)
                Fa = np.vstack([ea, np.cross(za, ea), za])
                Fb = np.vstack([eb, np.cross(zb, eb), zb])
                opts.append(LegOption(f"a{_sgn(ea)}/b{_sgn(eb)}",
                                      [Leg("a", br.a, False, Pa, Fa), Leg("b", br.b, True, Pb, Fb)]))
        elif br.type in ("plate_t5", "plate_other"):
            n = face_vector(br.face)
            if abs(n @ ma.e) > 0.2 or abs(n @ mb.e) > 0.2:
                raise ValueError(f"{br.label}: plate face {br.face} is not normal to the plane of "
                                 f"M{br.a} and M{br.b}")
            O = _closest_on_line_a(ma.p0, ma.e, mb.p0, mb.e)
            for eb in db:
                eu = ma.e
                boltsA = np.array([O + u * eu for u in pl.groupA_u])
                vB = np.array(pl.groupB_v)
                boltsB = np.array([O + v * eb for v in vB])
                GA, GB = boltsA.mean(0), boltsB.mean(0)
                FA = np.vstack([eu, np.cross(n, eu), n])
                FB = np.vstack([eb, np.cross(n, eb), n])
                opts.append(LegOption(f"b{_sgn(eb)}", [
                    Leg("A", br.a, False, GA, FA, boltsA),
                    Leg("B", br.b, True, GB, FB, boltsB, vB, eb)]))
        br.legs = opts


# --------------------------------------------------------------------------- checks
def bolt_group(F: np.ndarray, M: np.ndarray, bolts: np.ndarray, n: np.ndarray, e_slot: np.ndarray):
    """Rigid-plate bolt group, wrench (F, M) at the group centroid.

    Returns (max |f_i| in-plane, max along-slot |f_i . e_slot|, per-bolt out-of-plane F_z,i).
    """
    G = bolts.mean(0)
    r = bolts - G
    nb = len(bolts)
    r2 = float((r**2).sum())
    F_ip = F - (F @ n) * n
    Mn = M @ n
    f = F_ip / nb + (Mn / r2) * np.cross(n, r) if r2 > 0 else np.tile(F_ip / nb, (nb, 1))
    Fz = (F @ n) / nb + (r @ np.cross(n, M)) / r2 if r2 > 0 else np.full(nb, (F @ n) / nb)
    return float(np.linalg.norm(f, axis=1).max()), float(np.abs(f @ e_slot).max()), Fz


def leg_wrench(br: BracketSpring, leg: Leg, W_b: np.ndarray):
    """Wrench on the leg's member, about the leg point, in leg frame -> (F_loc, M_loc)."""
    F = W_b[:3] if leg.on_side_b else -W_b[:3]
    M = W_b[3:] if leg.on_side_b else -W_b[3:]
    MP = M + np.cross(br.X - leg.P, F)
    return F, MP, leg.frame @ F, leg.frame @ MP


def check_leg(br: BracketSpring, leg: Leg, W_b: np.ndarray, caps: Caps) -> dict:
    F, MP, Fl, Ml = leg_wrench(br, leg, W_b)
    row = {"Fx": Fl[0], "Fy": Fl[1], "Fz": Fl[2], "Mx": Ml[0], "My": Ml[1], "Mz": Ml[2]}
    U = dict.fromkeys(U_TERMS, 0.0)
    if br.type == "triangle":
        U["U_shear"] = np.hypot(Fl[0], Fl[1]) / caps.F_fric
        U["U_pull"] = max(Fl[2], 0.0) / caps.F_pull
        U["U_Mx"] = abs(Ml[0]) / caps.M_tilt
        U["U_My"] = abs(Ml[1]) / caps.M_tilt
        U["U_Mz"] = abs(Ml[2]) / caps.M_twist
    elif br.type == "plate_t5":
        n = leg.frame[2]
        e_line = leg.frame[0]
        fmax, fslot, Fz = bolt_group(F, MP, leg.bolts, n, e_line)
        row["f_bolt_max"] = fmax
        row["f_bolt_slot_max"] = fslot
        row["Fz_bolt_max"] = float(Fz.max())
        U["U_shear"] = max(fmax, fslot) / caps.F_fric
        U["U_pull"] = max(float(Fz.max()), 0.0) / caps.F_pull
        M_line = abs(MP @ e_line)
        if leg.name == "A":
            U["U_bend_line"] = M_line / caps.plate_M_line_A
        else:
            U["U_bend_line"] = M_line / caps.plate_M_line_B
            # stem bending, from the out-of-plane bolt forces beyond each section
            v = leg.stem_v
            v_low = v.min()
            M_low = abs(sum(Fz[i] * (v[i] - v_low) for i in range(len(v)) if v[i] > v_low))
            M_neck = abs(sum(Fz[i] * (v[i] - caps.v_neck) for i in range(len(v))))
            row["M_stem_lower_hole"] = M_low
            row["M_stem_neck"] = M_neck
            U["U_bend_stem"] = max(M_low / caps.plate_M_lower_hole, M_neck / caps.plate_M_neck)
    else:   # plate_other: forces only
        U = {k: np.nan for k in U_TERMS}
    row.update(U)
    row["U"] = float(np.nansum([U[k] for k in U_TERMS])) if br.type != "plate_other" else np.nan
    row["SF"] = 1.0 / row["U"] if row["U"] and np.isfinite(row["U"]) and row["U"] > 0 else np.inf
    if br.type == "plate_other":
        row["SF"] = np.nan
    vals = {k: U[k] for k in U_TERMS if np.isfinite(U[k])}
    row["gov_term"] = max(vals, key=vals.get) if vals else ""
    return row


def check_bracket(br: BracketSpring, W_b: np.ndarray, caps: Caps) -> tuple[str, list[dict], int]:
    """Worst corner option -> (option desc, leg rows, number of options)."""
    best = None
    for opt in br.legs:
        rows = [dict(leg=leg.name, member=leg.member, **check_leg(br, leg, W_b, caps)) for leg in opt.legs]
        u = max((r["U"] for r in rows if np.isfinite(r["U"])), default=-1.0)
        if best is None or u > best[0]:
            best = (u, opt.desc, rows)
    return best[1], best[2], len(br.legs)
