"""Load geometry.json / brackets.json (mm) into SI dataclasses."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .params import PROJECT_DIR

MM = 1e-3
AXES = {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}


def face_vector(face: str) -> np.ndarray:
    sign = -1.0 if face.startswith("-") else 1.0
    return sign * AXES[face[-1]]


@dataclass
class Member:
    id: int
    p0: np.ndarray
    p1: np.ndarray
    profile: str
    depth_along: object = None        # rectangular profiles: global axis letter or a vector (depth dir)

    @property
    def L(self) -> float:
        return float(np.linalg.norm(self.p1 - self.p0))

    @property
    def e(self) -> np.ndarray:
        return (self.p1 - self.p0) / self.L

    def project(self, x: np.ndarray) -> tuple[float, float]:
        """(station s along member clamped to [0, L], distance from x to that point)."""
        s = float(np.clip((x - self.p0) @ self.e, 0.0, self.L))
        return s, float(np.linalg.norm(self.p0 + s * self.e - x))

    def point(self, s: float) -> np.ndarray:
        return self.p0 + s * self.e

    @property
    def name(self) -> str:
        return f"M{self.id}"


@dataclass
class BracketSpec:
    type: str
    a: int
    b: int
    face: str
    count: int = 1
    note: str = ""


@dataclass
class Bearing:
    end_of: int
    bears_on: int


@dataclass
class Joint:
    id: str
    at: np.ndarray
    members: list[int]
    bearing: list[Bearing] = field(default_factory=list)
    brackets: list[BracketSpec] = field(default_factory=list)


@dataclass
class Geometry:
    members: dict[int, Member]
    joints: list[Joint]
    base_members: list[int]
    thrust_point: np.ndarray
    thrust_member: int
    thrust_patches: list = field(default_factory=list)   # [(member, s0, s1)] SI: rigid plate spreads loads


def _resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_DIR / p


def load(geometry_path, brackets_path) -> Geometry:
    g = json.loads(_resolve(geometry_path).read_text())
    b = json.loads(_resolve(brackets_path).read_text())
    assert g.get("units", "mm") == "mm" and b.get("units", "mm") == "mm"
    members = {
        m["id"]: Member(m["id"], np.array(m["p0"], float) * MM, np.array(m["p1"], float) * MM,
                        str(m["profile"]), m.get("strong_axis_depth_along"))
        for m in g["members"]
    }
    joints = []
    for j in b["joints"]:
        joints.append(Joint(
            j["id"], np.array(j["at"], float) * MM, list(j["members"]),
            [Bearing(x["end_of"], x["bears_on"]) for x in j.get("bearing", [])],
            [BracketSpec(x["type"], x["a"], x["b"], x.get("face", "+y"), int(x.get("count", 1)),
                         x.get("note", "")) for x in j.get("brackets", [])],
        ))
    patches = [(int(t["member"]), float(t["s0"]) * MM, float(t["s1"]) * MM) for t in g.get("thrust_patches", [])]
    return Geometry(members, joints, list(g["base_members"]),
                    np.array(g["thrust_point"], float) * MM, int(g["thrust_member"]), patches)
