"""Axis display-range policy — a small, logic-only value type.

A chart axis can pick its visible limits three ways:

  - full      show everything; let matplotlib autoscale (the default).
  - autoclip  clip to a percentile band of the plotted data (+ padding). This tames a cluster
              of outliers that would otherwise compress the region you care about into a
              sliver — a "soft focus" on the dense body. It is DATA-ADAPTIVE, which is the
              whole point: the *same* policy focuses a test that has a tight cluster + an
              outlier tail, yet shows the full spread for a test whose data is genuinely broad
              (the clip window then contains every point). One config entry, correct for both
              — no per-case rules.
  - manual    hard-coded limits; either side may be None to autoscale just that side.

This module knows NOTHING about which variable/chart a policy applies to. That mapping is
config (a small dict with precedence: BY_CHART > BY_VAR > DEFAULT — see SKILL.md). Keeping the
mapping out of here means config can import this leaf with no import cycle, and this stays a
pure, testable value type. The only behavior here is turning a policy + the plotted data into
concrete (lo, hi) limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

AxisMode = Literal["full", "autoclip", "manual"]


@dataclass(frozen=True)
class AxisRange:
    """How one axis chooses its limits. Construct via the classmethods, not the raw fields."""

    mode: AxisMode = "full"
    lo: float | None = None          # manual: lower limit (None -> autoscale this side)
    hi: float | None = None          # manual: upper limit (None -> autoscale this side)
    lo_pct: float = 1.0              # autoclip: lower percentile
    hi_pct: float = 99.0             # autoclip: upper percentile
    pad_frac: float = 0.05           # autoclip: pad each side by this fraction of the span

    # -- constructors (the readable, validated API) -------------------------------------

    @classmethod
    def full(cls) -> "AxisRange":
        """Show all data (matplotlib autoscale)."""
        return cls(mode="full")

    @classmethod
    def autoclip(cls, *, lo_pct: float = 1.0, hi_pct: float = 99.0,
                 pad_frac: float = 0.05) -> "AxisRange":
        """Clip to the [lo_pct, hi_pct] percentile band of the plotted data, padded.

        Set hi_pct=100 (or lo_pct=0) to leave that tail unclipped — useful when the region
        you care about sits at one extreme (e.g. high purity, where you want the top intact
        but the low-startup junk dropped).
        """
        if not 0.0 <= lo_pct < hi_pct <= 100.0:
            raise ValueError(
                f"autoclip needs 0 <= lo_pct < hi_pct <= 100; got lo_pct={lo_pct}, hi_pct={hi_pct}")
        if pad_frac < 0.0:
            raise ValueError(f"pad_frac must be >= 0; got {pad_frac}")
        return cls(mode="autoclip", lo_pct=lo_pct, hi_pct=hi_pct, pad_frac=pad_frac)

    @classmethod
    def manual(cls, lo: float | None = None, hi: float | None = None) -> "AxisRange":
        """Hard-coded limits. Pass only one side to clip that side and autoscale the other."""
        if lo is None and hi is None:
            raise ValueError("manual range needs at least one of lo/hi")
        if lo is not None and hi is not None and lo >= hi:
            raise ValueError(f"manual range needs lo < hi; got lo={lo} >= hi={hi}")
        return cls(mode="manual", lo=lo, hi=hi)

    # -- resolution ---------------------------------------------------------------------

    def limits(self, data) -> tuple[float | None, float | None]:
        """Resolve to concrete (lo, hi). None on a side = autoscale that side.

        Returns (None, None) — i.e. no clipping — for `full` and for any degenerate autoclip
        case (empty data, all-NaN, or a constant series), so a policy can never collapse an
        axis to a single point.
        """
        if self.mode == "full":
            return (None, None)
        if self.mode == "manual":
            return (self.lo, self.hi)

        # autoclip
        arr = np.asarray(data, dtype="float64")
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return (None, None)
        lo = float(np.percentile(arr, self.lo_pct))
        hi = float(np.percentile(arr, self.hi_pct))
        if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
            return (None, None)
        pad = (hi - lo) * self.pad_frac
        return (lo - pad, hi + pad)


def resolve(policy_table_by_chart: dict, policy_by_var: dict, default: "AxisRange",
            *, yvar: str, xvar: str, axis: str, var: str) -> "AxisRange":
    """Effective policy for one axis, with precedence BY_CHART > BY_VAR > DEFAULT.

    - policy_table_by_chart: {(yvar, xvar): {"x"|"y": AxisRange}}  (most specific)
    - policy_by_var:         {var: AxisRange}                       (intrinsic to a variable)
    - default:               AxisRange                              (fallback)
    """
    per_axis = policy_table_by_chart.get((yvar, xvar))
    if per_axis and axis in per_axis:
        return per_axis[axis]
    return policy_by_var.get(var, default)


def apply(ax, *, xvar: str, yvar: str, x, y,
          policy_table_by_chart: dict | None = None,
          policy_by_var: dict | None = None,
          default: "AxisRange" | None = None) -> None:
    """Apply x/y range policies for a paired (xvar, yvar) chart. Call AFTER plotting so the
    policy overrides matplotlib's autoscale. x/y are the actual plotted arrays (only consulted
    for autoclip percentiles)."""
    policy_table_by_chart = policy_table_by_chart or {}
    policy_by_var = policy_by_var or {}
    default = default or AxisRange.full()

    x_lo, x_hi = resolve(policy_table_by_chart, policy_by_var,
                         default, yvar=yvar, xvar=xvar, axis="x", var=xvar).limits(x)
    if x_lo is not None or x_hi is not None:
        ax.set_xlim(left=x_lo, right=x_hi)
    y_lo, y_hi = resolve(policy_table_by_chart, policy_by_var,
                         default, yvar=yvar, xvar=xvar, axis="y", var=yvar).limits(y)
    if y_lo is not None or y_hi is not None:
        ax.set_ylim(bottom=y_lo, top=y_hi)
