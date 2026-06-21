"""Monthly spill fraction bar chart — generic for any USACE dam."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import config as cfg
from config import DamConfig
import derived
from charts import common
from viz import render

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SPILL_COLOR = "#ff7f0e"


def draw(ax, fig, df, dam: DamConfig) -> None:
    sf = derived.monthly_spill_fraction(df).reindex(range(1, 13)) * 100
    xs = np.arange(1, 13)
    ax.bar(xs, sf.to_numpy(), color=SPILL_COLOR, width=0.7, alpha=0.85)

    ax.set_xticks(xs)
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlabel(cfg.axis_label("month"))
    ax.set_ylabel("Spill fraction (%)")
    ax.set_title(f"{dam.name} monthly spill fraction — {dam.year}")
    ax.set_ylim(bottom=0)


def figures(df, dam: DamConfig):
    def build():
        fig, ax = render.new_figure()
        draw(ax, fig, df, dam)
        sf = derived.monthly_spill_fraction(df) * 100
        valid = sf.dropna()
        peak_m = int(valid.idxmax()) if not valid.empty else 0
        max_month = MONTH_LABELS[peak_m - 1] if peak_m else "N/A"
        common.add_source(ax, cfg.SOURCE_USACE)
        common.add_watermark(ax)
        common.add_box(ax, fig, [f"Peak spill month: {max_month}", f"Year: {dam.year}"])
        path = dam.output_dir / f"{dam.slug}_spill_fraction_{dam.year}.png"
        return fig, path
    return [(f"spill_fraction_{dam.code}", build)]


if __name__ == "__main__":
    for dam in cfg.ALL_DAMS:
        df = derived.load_dam(dam.csv_path)
        for _, build in figures(df, dam):
            fig, path = build()
            print("wrote", render.save_fig(fig, path))
