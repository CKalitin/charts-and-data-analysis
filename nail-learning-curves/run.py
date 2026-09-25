"""Regenerate everything: digitize Sichel figures, write the tidy learning table + fits, draw charts."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import config as cfg  # noqa: E402
import model  # noqa: E402
from charts import learning_curves  # noqa: E402
from viz import render  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "digitize_sichel.py")], check=True,
                   stdout=subprocess.DEVNULL)
    df = model.learning_table("central")
    df.to_csv(cfg.OUTPUT_ROOT / "nail_learning_table.csv", index=False, float_format="%.5g")
    rows = []
    for sc in ("low", "central", "high"):
        for k, f in model.all_fits(model.learning_table(sc)).items():
            lo, hi = f.lr_ci95
            rows.append(dict(scenario=sc, fit=k, years=f"{f.y0}-{f.y1}", n=f.n,
                             doublings=round(f.doublings, 2), b=round(f.b, 4),
                             learning_rate=round(f.lr, 4), lr_ci95_lo=round(lo, 4), lr_ci95_hi=round(hi, 4)))
    import pandas as pd
    pd.DataFrame(rows).to_csv(cfg.OUTPUT_ROOT / "learning_rate_fits.csv", index=False)
    for name, build in learning_curves.figures():
        fig, path = build()
        render.save_fig(fig, path, dpi=cfg.DPI)
        print(f"  wrote {path.relative_to(cfg.PROJECT_DIR)}")
    print(f"done in {time.time() - t0:.1f}s")
