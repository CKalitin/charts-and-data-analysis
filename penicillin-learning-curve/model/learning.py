"""Experience-curve (Wright's law) fit.

    P(X) = P0 * (X / X0)^b          fitted as  log10 P = a + b log10 X   (OLS)

    P   real price                        [2025 USD per billion units, $/BU]
    X   cumulative production             [BU]
    b   experience exponent               [dimensionless, < 0 for learning]
    LR  learning rate = 1 - 2^b           [fraction of price lost per doubling of X]
    PR  progress ratio = 2^b = 1 - LR     [fraction of price retained per doubling]
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class FitResult:
    a: float            # log10 intercept at X = 1 BU
    b: float            # experience exponent
    se_b: float         # standard error of b
    r2: float
    n: int
    ci_level: float = 0.95

    @property
    def lr(self) -> float:
        return 1.0 - 2.0 ** self.b

    def _b_ci(self) -> tuple[float, float]:
        t = stats.t.ppf(0.5 + self.ci_level / 2, self.n - 2)
        return self.b - t * self.se_b, self.b + t * self.se_b

    @property
    def lr_ci(self) -> tuple[float, float]:
        b_lo, b_hi = self._b_ci()
        return 1.0 - 2.0 ** b_hi, 1.0 - 2.0 ** b_lo   # steeper b -> larger LR

    def predict(self, x: np.ndarray) -> np.ndarray:
        return 10.0 ** (self.a + self.b * np.log10(x))


def fit_power_law(x: np.ndarray, y: np.ndarray) -> FitResult:
    lx, ly = np.log10(np.asarray(x, float)), np.log10(np.asarray(y, float))
    res = stats.linregress(lx, ly)
    return FitResult(a=res.intercept, b=res.slope, se_b=res.stderr, r2=res.rvalue ** 2, n=len(lx))


def midyear_cumulative(annual: dict[int, float]) -> dict[int, float]:
    """X_t = sum_{s<t} q_s + q_t / 2  -- the experience base during year t (not at its end)."""
    out, running = {}, 0.0
    for year in sorted(annual):
        out[year] = running + annual[year] / 2.0
        running += annual[year]
    return out
