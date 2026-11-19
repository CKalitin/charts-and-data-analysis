"""Member checks: yield, column buckling (Euler/Johnson), beam-column, shear/torsion.

Buckling about each local axis uses that axis's braced length: the member is
split at joints whose connected members have |cos| >= brace_cos_min with the
deflection direction.  A segment ending at a free (unjointed) end is a cantilever
(K = 2); otherwise K = checks.K_buckling.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import fem
from .model import StandModel


def critical_load(E, sigma_y, A, I, KL) -> tuple[float, str]:
    r = np.sqrt(I / A)
    slender = KL / r
    Cc = np.sqrt(2 * np.pi**2 * E / sigma_y)
    if slender > Cc:
        return np.pi**2 * E * I / KL**2, "Euler"
    return A * sigma_y * (1 - sigma_y * slender**2 / (4 * np.pi**2 * E)), "Johnson"


@dataclass
class Segment:
    s0: float
    s1: float
    K: float
    elements: list[int]

    @property
    def L(self) -> float:
        return self.s1 - self.s0


def braced_segments(model: StandModel, mid: int, p) -> dict[str, list[Segment]]:
    """Per local deflection axis ('y' uses Iz, 'z' uses Iy): segments between bracing joints."""
    m = model.members[mid]
    R = model.elements[model.member_elements[mid][0]].R
    tol = p.si.model.station_merge
    joint_s = []
    for j in model.geo.joints:                  # bracing from the full 3D geometry
        if mid not in j.members:
            continue
        s, _ = m.project(j.at)
        joint_s.append((s, [model.geo.members[o].e for o in j.members if o != mid]))
    out = {}
    for ax, d in (("y", R[1]), ("z", R[2])):
        cuts = sorted({round(s, 6) for s, es in joint_s if any(abs(e @ d) >= p.si.checks.brace_cos_min for e in es)})
        has_joint_at = lambda s0: any(abs(s - s0) <= max(tol, 0.05 * m.L) for s, _ in joint_s)  # noqa: E731
        bounds = sorted(set([0.0, m.L] + cuts))
        bounds = [b for i, b in enumerate(bounds) if i == 0 or b - bounds[i - 1] > tol]
        segs = []
        for s0, s1 in zip(bounds[:-1], bounds[1:]):
            free = (s0 == 0.0 and not has_joint_at(0.0)) or (s1 == bounds[-1] and not has_joint_at(m.L))
            els = [k for k in model.member_elements[mid]
                   if model.node_s[model.elements[k].n1] >= s0 - 1e-9 and model.node_s[model.elements[k].n2] <= s1 + 1e-9]
            segs.append(Segment(s0, s1, 2.0 if free else p.si.checks.K_buckling, els))
        out[ax] = segs
    return out


def check_member(model: StandModel, mid: int, internal: dict[int, np.ndarray], segs, p) -> dict:
    """internal: element -> (n_pts, 7) [x, N, Vy, Vz, T, My, Mz]."""
    E, fy = model.E, p.si.material.sigma_y
    sec = model.sections[mid]
    Sy, Sz = sec.Iy / sec.cz, sec.Iz / sec.cy
    best = {"sigma": -1.0}
    tau = 0.0
    for k in model.member_elements[mid]:
        r = internal[k]
        sig = np.abs(r[:, 1]) / sec.A + np.abs(r[:, 5]) / Sy + np.abs(r[:, 6]) / Sz
        i = int(np.argmax(sig))
        if sig[i] > best["sigma"]:
            best = {"sigma": float(sig[i]), "N": float(r[i, 1]), "My": float(r[i, 5]), "Mz": float(r[i, 6]),
                    "x_mm": (model.node_s[model.elements[k].n1] + r[i, 0]) * 1e3}
        c_max = max(sec.cy, sec.cz)
        t = np.abs(r[:, 4]) * c_max / sec.J + 1.5 * np.maximum(np.abs(r[:, 2]), np.abs(r[:, 3])) / sec.A
        tau = max(tau, float(t.max()))
    out = {"sigma": best["sigma"], "N": best["N"], "My": best["My"], "Mz": best["Mz"], "x_mm": best["x_mm"],
           "SF_yield": fy / best["sigma"] if best["sigma"] > 0 else np.inf, "tau": tau}

    # ---- buckling + beam-column, per axis segment
    I_ax = {"y": sec.Iz, "z": sec.Iy}               # deflection along local y bends about z
    S_ax = {"y": Sz, "z": Sy}
    M_col = {"y": 6, "z": 5}
    worst_b = {"SF_buckle": np.inf, "Pcr": np.nan, "Ncomp": 0.0, "buckle_axis": "", "buckle_type": "",
               "KL_mm": np.nan}
    pcr_seg = {}
    for ax in ("y", "z"):
        for sg in segs[ax]:
            rows = np.vstack([internal[k] for k in sg.elements]) if sg.elements else np.zeros((1, 7))
            Ncomp = max(0.0, float(-rows[:, 1].min()))
            Pcr, kind = critical_load(E, fy, sec.A, I_ax[ax], sg.K * sg.L)
            pcr_seg[(ax, sg.s0)] = (Pcr, sg, Ncomp)
            if Ncomp > 0:
                sf = Pcr / Ncomp
                if sf < worst_b["SF_buckle"]:
                    worst_b = {"SF_buckle": sf, "Pcr": Pcr, "Ncomp": Ncomp, "buckle_axis": ax,
                               "buckle_type": kind, "KL_mm": sg.K * sg.L * 1e3}
    out.update(worst_b)

    # beam-column on each element: N/Pcr,min + sum_axes M/(M_y (1 - N/Pcr,axis))
    bc = 0.0
    for k in model.member_elements[mid]:
        s_mid = model.node_s[model.elements[k].n1]
        pc = {}
        for ax in ("y", "z"):
            for sg in segs[ax]:
                if sg.s0 - 1e-9 <= s_mid <= sg.s1 + 1e-9:
                    pc[ax] = critical_load(E, fy, sec.A, I_ax[ax], sg.K * sg.L)[0]
                    break
        r = internal[k]
        Nc = max(0.0, float(-r[:, 1].min()))
        if Nc <= 0:
            continue
        ratio = Nc / min(pc.values())
        for ax in ("y", "z"):
            amp = 1 - Nc / pc[ax]
            Mmax = float(np.abs(r[:, M_col[ax]]).max())
            ratio += np.inf if amp <= 0 else Mmax / (fy * S_ax[ax] * amp)
        bc = max(bc, ratio)
    out["bc_ratio"] = bc
    out["SF_bc"] = 1.0 / bc if bc > 0 else np.inf
    sfs = {"yield": out["SF_yield"], "buckle": out["SF_buckle"], "beam-col": out["SF_bc"]}
    out["gov_check"] = min(sfs, key=sfs.get)
    out["SF"] = sfs[out["gov_check"]]
    return out
