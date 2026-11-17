"""Parameter schema: the single source of truth for every tunable number.

`params.yaml` is the user's working copy, generated from SCHEMA (`python -m stand
params --reset`). Keys carry their display unit as a suffix (`_mm`, `_MPa`, ...);
`load()` converts everything to SI and records which values differ from the
schema defaults so every run can print exactly what was changed.

Flags:
  placeholder  value is a stand-in; must be measured/confirmed before trusting SFs
  unverified   published value not found; engineering estimate
  assumption   modelling choice from the brief, worth a second look
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import yaml

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PARAMS_PATH = PROJECT_DIR / "params.yaml"

# display unit -> factor to SI
UNIT_SI = {
    "mm": 1e-3, "mm2": 1e-6, "mm4": 1e-12, "m": 1.0,
    "N": 1.0, "N/m": 1.0, "MPa": 1e6, "GPa": 1e9,
    "m/s2": 1.0, "deg": 1.0, "-": 1.0, "": 1.0,
}


@dataclass(frozen=True)
class Param:
    key: str            # dotted path, e.g. "material.E_GPa"
    default: object
    unit: str = "-"
    help: str = ""
    flag: str = ""      # placeholder | unverified | assumption | ""


S = Param
SCHEMA: list[Param] = [
    # --- inputs ----------------------------------------------------------------
    S("inputs.geometry", "references/prompt/geometry.json", "", "member centrelines (mm)"),
    S("inputs.brackets", "references/prompt/brackets.json", "", "joints / brackets / bearing (mm)"),
    S("inputs.burrard", "references/prompt/burrard_validation.json", "", "truss validation case"),

    # --- material: 6063-T6 (80/20 published) ------------------------------------
    S("material.E_GPa", 68.9, "GPa", "Young's modulus"),
    S("material.G_GPa", 26.5, "GPa", "shear modulus"),
    S("material.sigma_y_MPa", 172.0, "MPa", "yield strength, 6063-T6"),

    # --- sections (80/20 published) ---------------------------------------------
    S("section_1010.A_mm2", 281.9, "mm2", "0.437 in^2"),
    S("section_1010.I_strong_mm4", 18400.0, "mm4", "0.0442 in^4 (square: both axes)"),
    S("section_1010.I_weak_mm4", 18400.0, "mm4", "0.0442 in^4"),
    S("section_1010.c_strong_mm", 12.7, "mm", "outer fibre"),
    S("section_1010.c_weak_mm", 12.7, "mm", "outer fibre"),
    S("section_1010.J_mm4", "auto", "mm4", "torsion constant; auto = 0.5*(Iy+Iz)", "unverified"),
    S("section_1010.weight_N_per_m", 7.43, "N/m", "0.0424 lb/in"),

    S("section_1020.A_mm2", 507.7, "mm2", "0.787 in^2"),
    S("section_1020.I_strong_mm4", 128100.0, "mm4", "0.3078 in^4, depth along strong_axis_depth_along"),
    S("section_1020.I_weak_mm4", 34670.0, "mm4", "0.0833 in^4"),
    S("section_1020.c_strong_mm", 25.4, "mm", "outer fibre, strong-axis bending"),
    S("section_1020.c_weak_mm", 12.7, "mm", "outer fibre, weak-axis bending"),
    S("section_1020.J_mm4", "auto", "mm4", "torsion constant; auto = 0.5*(Iy+Iz)", "unverified"),
    S("section_1020.weight_N_per_m", 13.45, "N/m", "0.0768 lb/in"),

    # --- loads ------------------------------------------------------------------
    S("loads.thrust_N", 1112.0, "N", "static thrust, 250 lbf, +z at thrust_point"),
    S("loads.DF", 2.0, "-", "dynamic factor on thrust (and on misalignment)"),
    S("loads.rocket_weight_N", 133.0, "N", "30 lb wet, -z at thrust_point, unfactored"),
    S("loads.self_weight", True, "", "distributed member self-weight on/off"),
    S("loads.misalign_x", 0.03, "-", "horizontal x load as fraction of factored thrust", "assumption"),
    S("loads.misalign_y", 0.03, "-", "horizontal y load as fraction of factored thrust", "assumption"),
    S("loads.cases", ["none", "+x", "-x", "+y", "-y", "+x+y"], "",
      "misalignment load cases (names parsed as signs on x/y)"),

    # --- joint springs ----------------------------------------------------------
    S("springs.k_t_factor", 1e3, "-", "bracket translational k = factor * EA/L (min of the two members)"),
    S("springs.k_theta_pinned", 1e-3, "-", "run P: rotational k = factor * EI/L (solver stability only)"),
    S("springs.k_theta_rigid", 1e3, "-", "run R: rotational k = factor * EI/L"),
    S("springs.k_theta_sweep", [1e-3, 1e-2, 1e-1, 1.0, 1e1, 1e2, 1e3], "-",
      "assumption test: k_theta factors swept on the governing case"),
    S("springs.k_bearing_factor", 1e3, "-", "bearing (compression-only) k = factor * EA/L of the bearing member"),
    S("springs.snap_tol_mm", 70.0, "mm", "a joint/load point lies on a member if within this of its centreline"),

    # --- bolts / brackets -------------------------------------------------------
    S("bolts.preload_N", 5000.0, "N", "1/4-20 bolt preload F_i", "assumption"),
    S("bolts.mu", 0.2, "-", "friction coefficient, one surface", "assumption"),
    S("bolts.hole_radius_mm", 3.57, "mm", "r_i (hole)"),
    S("bolts.head_radius_mm", 5.55, "mm", "r_o (head bearing)"),

    S("triangle.tilt_arm_mm", 12.7, "mm", "gap-opening arm a: Mx,max = My,max = F_i*a", "placeholder"),
    S("triangle.bolt_from_corner_mm", 20.0, "mm", "bolt distance from the corner along each member"),
    S("triangle.min_leg_extent_mm", 12.7, "mm",
      "a leg can lie along a member direction only if the member extends this far past the joint"),

    S("plate.fy_MPa", 172.0, "MPa", "plate yield strength (80/20 aluminium, as the extrusions; user-confirmed)"),
    S("plate.thickness_mm", 6.35, "mm", "plate thickness t", "placeholder"),
    S("plate.groupA_u_mm", [-25.4, 0.0, 25.4], "mm", "bolt positions on member a (u along a, v = 0)"),
    S("plate.groupB_v_mm", [38.1, 63.5], "mm", "bolt positions on member b (u = 0, v along b)"),
    S("plate.base_width_mm", 76.2, "mm", "outline (brief's plate diagram; user: use the diagram): base width along u"),
    S("plate.base_half_height_mm", 12.7, "mm", "outline: base spans v = -12.7..+12.7"),
    S("plate.stem_taper_end_v_mm", 63.5, "mm", "outline: tapers from base_width at v=+12.7 to stem_width here"),
    S("plate.stem_width_mm", 25.4, "mm", "outline: stem width from taper end to top edge"),
    S("plate.top_edge_v_mm", 76.2, "mm", "outline: top edge"),

    # --- checks -----------------------------------------------------------------
    S("checks.SF_target_member", 2.0, "-", "member target SF (DF already in loads)"),
    S("checks.SF_target_joint", 2.0, "-", "joint target SF (DF already in loads)"),
    S("checks.K_buckling", 1.0, "-", "effective length factor between bracing joints"),
    S("checks.brace_cos_min", 0.5, "-",
      "a joint braces a member axis if a connected member's axis has |cos| >= this with it"),
    S("checks.mechanism_disp_mm", 1.0, "mm", "run P invalid (mechanism) if any node moves more than this"),
    S("checks.sweep_mech_ratio", 5.0, "-",
      "k_theta sweep point is mechanism-dominated if max displacement > this x run R (and > mechanism_disp)"),
    S("checks.tilt_limit_deg", 0.25, "deg", "serviceability flag for thrust-point tilt"),
    S("checks.restraint_tol_rel", 1e-6, "-", "3-2-1 restraint reactions must be below this * factored thrust"),
    S("checks.mech_eig_rel_tol", 1e-12, "-", "K eigenvalue / max diag below this = mechanism"),

    # --- model ------------------------------------------------------------------
    S("model.max_subelement_mm", 125.0, "mm", "members are split so no sub-element is longer than this"),
    S("model.station_merge_mm", 2.0, "mm", "nodes on a member closer than this are merged"),
    S("model.g_m_s2", 9.80665, "m/s2", "gravity, for sandbag mass"),
    S("model.front_frame_y_mm", -20.0, "mm", "2D mode: side frame kept"),
    S("model.front_frame_tol_mm", 5.0, "mm", "2D mode: |y - front_frame_y| tolerance"),

    # --- output -----------------------------------------------------------------
    S("output.dir", "results", "", "results root: <dir>/3d, <dir>/2d, <dir>/variants/<name>"),
    S("output.svg", False, "", "also write editable SVG next to every PNG figure"),
    S("output.deform_frac", 0.06, "-", "plot: max deformed displacement as a fraction of stand height"),
    S("output.plotlyjs", "inline", "", "inline (offline, ~4.5 MB) | cdn"),
    S("output.n_lowest", 10, "-", "rows in the lowest-SF tables"),
]
del S

SCHEMA_BY_KEY = {p.key: p for p in SCHEMA}


def _unit_of(key: str) -> str:
    return SCHEMA_BY_KEY[key].unit


def _to_si(key: str, value):
    unit = _unit_of(key)
    f = UNIT_SI.get(unit, 1.0)
    if isinstance(value, bool) or isinstance(value, str) or value is None:
        return value
    if isinstance(value, list):
        return [v * f if isinstance(v, (int, float)) and not isinstance(v, bool) else v for v in value]
    return value * f


def _flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, key + "."))
        else:
            out[key] = v
    return out


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, list):
        return "[" + ", ".join(_fmt(x) for x in v) + "]"
    return str(v)


@dataclass
class Change:
    key: str
    default: object
    value: object
    source: str     # "params.yaml" | "--set"

    def __str__(self):
        unit = _unit_of(self.key)
        return f"{self.key:34s} {_fmt(self.default)} -> {_fmt(self.value)} {unit}  ({self.source})"


@dataclass
class Params:
    raw: dict                       # flat key -> display-unit value
    si: SimpleNamespace             # nested, SI
    path: Path
    changes: list[Change] = field(default_factory=list)

    def flagged(self, flag: str) -> list[Param]:
        return [p for p in SCHEMA if p.flag == flag]

    def display(self, key: str) -> str:
        return f"{_fmt(self.raw[key])} {_unit_of(key)}".strip()


def _nest(flat_si: dict) -> SimpleNamespace:
    root: dict = {}
    for key, v in flat_si.items():
        parts = key.split(".")
        d = root
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        # strip the unit suffix for the SI attribute name: E_GPa -> E, weight_N_per_m -> weight
        leaf = parts[-1]
        suffix = "_" + _unit_of(key).replace("/", "_per_").replace("m/s2", "m_s2")
        suffix = suffix.replace("_per_s2", "_s2")
        d[leaf[: -len(suffix)] if len(suffix) > 1 and leaf.endswith(suffix) else leaf] = v
    def to_ns(d):
        return SimpleNamespace(**{k: to_ns(v) if isinstance(v, dict) else v for k, v in d.items()})
    return to_ns(root)


def parse_set(items: list[str] | None) -> dict:
    """`--set loads.DF=2.5` -> {"loads.DF": 2.5} (value parsed as YAML)."""
    out = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--set expects key=value, got {item!r}")
        k, v = item.split("=", 1)
        k = k.strip()
        if k not in SCHEMA_BY_KEY:
            raise SystemExit(f"--set: unknown parameter {k!r}. Try `python -m stand params`.")
        out[k] = yaml.safe_load(v)
    return out


def load(path: Path | str | None = None, overrides: dict | None = None) -> Params:
    path = Path(path) if path else DEFAULT_PARAMS_PATH
    if not path.exists():
        write_defaults(path)
        print(f"params: {path} did not exist; wrote defaults")
    with open(path) as fh:
        user = _flatten(yaml.safe_load(fh) or {})
    unknown = sorted(set(user) - set(SCHEMA_BY_KEY))
    if unknown:
        raise SystemExit(f"params: unknown keys in {path}: {unknown}  (typo? see `python -m stand params`)")
    raw, changes = {}, []
    for p in SCHEMA:
        v = user.get(p.key, p.default)
        if isinstance(p.default, float) and isinstance(v, int) and not isinstance(v, bool):
            v = float(v)
        raw[p.key] = v
        if v != p.default:
            changes.append(Change(p.key, p.default, v, path.name))
    for k, v in (overrides or {}).items():
        prev = raw[k]
        raw[k] = v
        changes = [c for c in changes if c.key != k]
        if v != SCHEMA_BY_KEY[k].default or prev != v:
            changes.append(Change(k, SCHEMA_BY_KEY[k].default, v, "--set"))
    flat_si = {k: _to_si(k, v) for k, v in raw.items()}
    for prof in ("1010", "1020"):           # J = auto -> 0.5 (Iy + Iz)
        kj = f"section_{prof}.J_mm4"
        if flat_si[kj] == "auto":
            flat_si[kj] = 0.5 * (flat_si[f"section_{prof}.I_strong_mm4"] + flat_si[f"section_{prof}.I_weak_mm4"])
    return Params(raw=raw, si=_nest(flat_si), path=path, changes=changes)


def defaults_yaml() -> str:
    """params.yaml text generated from SCHEMA, grouped with unit/flag comments."""
    lines = [
        "# Mojave Sphinx test stand — model parameters (all editable).",
        "# Generated from stand/params.py:SCHEMA.  Units are in the key suffix.",
        "# Every run prints the values that differ from these defaults.",
        "# Flags: [placeholder] must be confirmed, [unverified] estimate, [assumption] modelling choice.",
        "",
    ]
    group = None
    for p in SCHEMA:
        g, leaf = p.key.split(".", 1)
        if g != group:
            if group is not None:
                lines.append("")
            lines.append(f"{g}:")
            group = g
        val = yaml.safe_dump(p.default, default_flow_style=True).strip()
        if val.endswith("\n..."):
            val = val[:-4].strip()
        val = val.removesuffix("...").strip()
        note = p.help + (f"  [{p.flag}]" if p.flag else "")
        lines.append(f"  {leaf + ':':30s} {val:28s} # {note}")
    return "\n".join(lines) + "\n"


def write_defaults(path: Path | str = DEFAULT_PARAMS_PATH) -> Path:
    path = Path(path)
    path.write_text(defaults_yaml())
    return path
