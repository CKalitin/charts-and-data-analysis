"""Extract the four channel traces from photographs of a Tektronix TBS1104 screen.

Pipeline (per photo)
  1. Find the graticule: auto-detect the dark waveform rectangle for an initial quad,
     detect the 0.2-div graticule dots and fit a homography  pixel -> (u, v) divisions
     (u: 0..10 left->right, v: 0..8 top->bottom) by robust least squares on the dot lattice.
  2. Rectify the photo to 100 px/div, which removes perspective and rotation.
  3. Classify trace pixels by hue (CH1 yellow, CH2 cyan, CH3 magenta, CH4 green).
  4. "De-rasterise" each class onto the scope's own LCD grid (250 x 200 px for 10 x 8 div,
     0.04 div / px) and read one vertical stroke per LCD column.
  5. Convert to volts / seconds using the on-screen readouts (metadata below).

Run:  python tools/scope_extract.py            (from scope-images/)
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = ROOT / "Raw_images"
OUT = ROOT / "output"

# ---------------------------------------------------------------- on-screen readouts
# Read off each photo by eye (V/div per channel, timebase, M Pos, trigger).
META = {
    "image6": dict(vdiv=dict(CH1=2.0, CH2=5.0, CH3=1.0, CH4=2.0), tb=50e-3, mpos=7.6e-3,
                   trig_ch="CH1", trig_level=1.28, stamp="10-Oct-26 16:46",
                   quad=[(210, 248), (1365, 248), (1310, 1108), (232, 1105)]),  # bezel merges with screen -> manual quad
    "image7": dict(vdiv=dict(CH1=2.0, CH2=5.0, CH3=1.0, CH4=2.0), tb=25e-3, mpos=60e-6,
                   trig_ch="CH1", trig_level=1.44, stamp="10-Oct-26 17:08"),
    # only CH1 is displayed on this one (other channels off, so no data and no series for them)
    "image10": dict(vdiv=dict(CH1=0.5), channels=["CH1"], tb=10e-3, mpos=0.0,
                    trig_ch="CH1", trig_level=2.40, stamp="10-Oct-26 14:04",
                    trig_arrow=False),     # level arrow not visible on screen (menu overlay)
    "image9": dict(vdiv=dict(CH1=2.0, CH2=5.0, CH3=1.0, CH4=0.2), tb=25e-3, mpos=0.0,
                   trig_ch="CH1", trig_level=2.96, stamp="10-Oct-26 16:38"),
}
CHANNELS = ["CH1", "CH2", "CH3", "CH4"]


def shown(meta):
    """Channels actually displayed in this photo."""
    return meta.get("channels", CHANNELS)
ZERO_V = 7.0            # all four ground markers sit 3 div below centre (v = 4 + 3)
LCD = 0.04              # div per LCD pixel (25 px/div)
NCOL, NROW = 251, 201   # LCD pixel centres along u (0..10) and v (0..8)
SC, MG = 100, 100       # rectified px/div and margin (px)
F = 1500.0              # focal-ish scale for conditioning the fit

SIGNAL = {"CH1": "12V", "CH2": "V_gate_supp", "CH3": "Int_Vcc"}


def signal_name(meta, ch):
    """Probe-point names. CH4 depends on the setup: 200 mV/div -> SUPP_UVR, 2 V/div -> 12V_Supp_in."""
    if ch == "CH4":
        return "SUPP_UVR" if abs(meta["vdiv"]["CH4"] - 0.2) < 1e-9 else "12V_Supp_in"
    return SIGNAL[ch]


# hue (OpenCV 0..180) ranges of the trace colours as photographed
HUE = {"CH1": (25, 47), "CH4": (47, 77), "CH2": (77, 106), "CH3": (106, 160)}


# ---------------------------------------------------------------- 1. graticule geometry
def detect_dots(im):
    """Sub-pixel centres of bright, neutral-coloured blobs (graticule dots)."""
    mn = im.min(axis=2)
    bg = cv2.medianBlur(mn, 15).astype(np.float32)
    th = cv2.GaussianBlur(mn.astype(np.float32) - bg, (0, 0), 1.0)
    pk = (th == cv2.dilate(th, np.ones((5, 5)))) & (th > 25)
    ys, xs = np.nonzero(pk)
    out = []
    yy, xx = np.mgrid[-2:3, -2:3]
    for x, y in zip(xs, ys):
        w = th[y - 2:y + 3, x - 2:x + 3].clip(0)
        if w.shape != (5, 5) or w.sum() == 0:
            out.append((x, y))
        else:
            out.append((x + (w * xx).sum() / w.sum(), y + (w * yy).sum() / w.sum()))
    return np.array(out, float)


def init_quad(im):
    """Dark waveform rectangle -> 4 corners (TL, TR, BR, BL)."""
    d = ((im < 75).all(axis=2)).astype(np.uint8)
    d = cv2.morphologyEx(d, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    d = cv2.morphologyEx(d, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(d)
    best = max(range(1, n), key=lambda i: st[i, 4])
    cs, _ = cv2.findContours((lab == best).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(max(cs, key=cv2.contourArea))
    for eps in np.linspace(0.005, 0.1, 60):
        ap = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
        if len(ap) <= 4:
            break
    return order_quad(ap.reshape(-1, 2))


def order_quad(q):
    q = np.asarray(q, float)
    c = q.mean(0)
    q = q[np.argsort(np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]))]
    return np.roll(q, -np.argmin(q.sum(1)), 0)


def nearest_lattice(uv):
    """Nearest graticule dot: dots sit every 0.2 div on each integer division line."""
    u, v = uv[:, 0], uv[:, 1]
    A = np.c_[np.round(u), np.round(v * 5) / 5]
    B = np.c_[np.round(u * 5) / 5, np.round(v)]
    dA, dB = np.hypot(*(uv - A).T), np.hypot(*(uv - B).T)
    return np.where((dA < dB)[:, None], A, B), np.minimum(dA, dB)


def fit_homography(im, quad):
    """Return h (3x3, normalised px -> div), centre c, inlier pixel pts, RMS in div."""
    h_, w_ = im.shape[:2]
    c = np.array([w_ / 2, h_ / 2])
    pts = detect_dots(im)
    n_ = lambda p: (p - c) / F
    H, _ = cv2.findHomography(n_(np.float32(quad)), np.float32([[0, 0], [10, 0], [10, 8], [0, 8]]))
    project = lambda H_, p: cv2.perspectiveTransform(n_(p).reshape(-1, 1, 2).astype(np.float32), H_).reshape(-1, 2)
    # stage A: coarse-to-fine plain least squares on every dot that matches the lattice
    for tol in (0.3, 0.2, 0.15, 0.1, 0.08, 0.06, 0.05, 0.05, 0.05, 0.05):
        uv = project(H, pts)
        M, d = nearest_lattice(uv)
        sel = (d < tol) & (M[:, 0] >= 0) & (M[:, 0] <= 10) & (M[:, 1] >= 0) & (M[:, 1] <= 8)   # bound the lattice point, not the (still biased) dot
        H, _ = cv2.findHomography(n_(pts[sel]).astype(np.float32), M[sel].astype(np.float32), 0)
    # stage B: robust fit on interior dots only (the frame ticks are not lattice dots)
    for tol in (0.1, 0.08, 0.07, 0.06, 0.05, 0.04, 0.04):
        uv = project(H, pts)
        M, d = nearest_lattice(uv)
        sel = ((d < tol) & (uv[:, 0] > .25) & (uv[:, 0] < 9.75) & (uv[:, 1] > .25) & (uv[:, 1] < 7.75))
        P, Mm = n_(pts[sel]), M[sel]

        def fun(q):
            h = np.append(q, 1).reshape(3, 3)
            r = np.c_[P, np.ones(len(P))] @ h.T
            return (r[:, :2] / r[:, 2:3] - Mm).ravel()
        q = least_squares(fun, (H / H[2, 2]).ravel()[:8], loss="soft_l1", f_scale=0.02).x
        H = np.append(q, 1).reshape(3, 3)
        rms = np.sqrt((fun(q) ** 2).reshape(-1, 2).sum(1).mean())
    return H, c, pts[sel], rms


def rectify(im, H, c):
    T1 = np.array([[1 / F, 0, -c[0] / F], [0, 1 / F, -c[1] / F], [0, 0, 1]])
    T2 = np.array([[SC, 0, MG], [0, SC, MG], [0, 0, 1]])
    Hpx = T2 @ H @ T1                       # photo px -> rectified px
    rect = cv2.warpPerspective(im, Hpx, (10 * SC + 2 * MG, 8 * SC + 2 * MG), flags=cv2.INTER_CUBIC)
    return rect, Hpx


# ---------------------------------------------------------------- 2. colour classification
def class_masks(rect, min_area=40):
    hsv = cv2.cvtColor(rect, cv2.COLOR_BGR2HSV).astype(int)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    colourful = (s > 60) & (v > 130)
    out = {}
    for ch, (a, b) in HUE.items():
        m = (colourful & (h >= a) & (h < b)).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        keep = np.zeros(n, bool)
        keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_area       # drops graticule-dot speckle
        out[ch] = keep[lab]
    return out


def marker_exclusions(meta, mpos_div):
    """Rectified-px boxes (x0, x1, y0, y1) holding scope overlay glyphs, not traces."""
    u_trig = 5 - mpos_div
    ex = {ch: [] for ch in CHANNELS}
    box = lambda u0, u1, v0, v1: (MG + u0 * SC, MG + u1 * SC, MG + v0 * SC, MG + v1 * SC)
    for ch in shown(meta):                                # trigger-position arrow at top edge
        ex[ch].append(box(u_trig - .3, u_trig + .3, 0, .42))
    if meta.get("trig_arrow", True):
        tv = ZERO_V - meta["trig_level"] / meta["vdiv"][meta["trig_ch"]]
        ex[meta["trig_ch"]].append(box(9.62, 10.05, tv - .32, tv + .32))   # trigger-level arrow
    return ex


# ---------------------------------------------------------------- 3. trace read-out
def lcd_coverage(mask, excl):
    """Fraction of each 4x4 rectified block (one LCD pixel) covered by the class mask."""
    m = mask.astype(np.float32).copy()
    m[:MG + 5], m[MG + 8 * SC - 5:] = 0, 0                 # frame ticks / blue bezel colour leak at top & bottom edge
    m[:, :MG + 2], m[:, MG + 10 * SC - 2:] = 0, 0          # ... and left & right edge
    for x0, x1, y0, y1 in excl:
        m[int(y0):int(y1), int(x0):int(x1)] = 0
    ks = np.arange(NCOL)
    js = np.arange(NROW)
    cov = np.zeros((NROW, NCOL), np.float32)
    ii = cv2.integral(m)
    half = int(round(LCD * SC / 2))                      # 2 px
    xs0 = MG + (ks * LCD * SC).round().astype(int) - half
    ys0 = MG + (js * LCD * SC).round().astype(int) - half
    xs0 = np.clip(xs0, 0, m.shape[1] - 2 * half)
    ys0 = np.clip(ys0, 0, m.shape[0] - 2 * half)
    X0, Y0 = np.meshgrid(xs0, ys0)
    s = 2 * half
    cov = (ii[Y0 + s, X0 + s] - ii[Y0, X0 + s] - ii[Y0 + s, X0] + ii[Y0, X0]) / (s * s)
    return cov


def lit_bitmap(cov, thr=0.40, min_px=6):
    """Binary LCD bitmap of one channel. Components of < min_px LCD pixels (graticule dots / axis ticks
    that leaked into the colour class) are dropped; real strokes are connected and much larger."""
    lit = (cov >= thr).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(lit, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_px
    return keep[lab]


def read_columns(cov, thr=0.40):
    """Per LCD column: (lo, hi, centroid) in row units, or NaN when the channel is not visible."""
    lo = np.full(NCOL, np.nan)
    hi = np.full(NCOL, np.nan)
    cen = np.full(NCOL, np.nan)
    lit = lit_bitmap(cov, thr)
    for k in range(NCOL):
        rows = np.nonzero(lit[:, k])[0]
        if rows.size == 0:
            continue
        lo[k], hi[k] = rows.min(), rows.max()
        w = cov[rows, k]
        cen[k] = (rows * w).sum() / w.sum()
    return lo, hi, cen


def follow_path(lo, hi, cen, mid_rows=8):
    """Sample value per column. The scope joins consecutive samples with a vertical line, so a column
    holds a stroke from the previous sample to this one. Flat / moderately steep (<= mid_rows): the
    stroke midpoint (centroid when flat). Tall one-column spikes: the stroke end farther from the
    previous sample."""
    val = np.full(NCOL, np.nan)
    prev = np.nan
    for k in range(NCOL):
        if np.isnan(lo[k]):
            continue
        span = hi[k] - lo[k]
        if span <= 3:
            val[k] = cen[k]
        elif span <= mid_rows or np.isnan(prev):
            val[k] = 0.5 * (lo[k] + hi[k])
        else:
            val[k] = hi[k] if abs(hi[k] - prev) > abs(lo[k] - prev) else lo[k]
        prev = val[k]
    return val


def drop_islands(x, max_len=2, min_gap=3):
    """Remove 1-2 column 'visible' islands sitting inside long invisible stretches (colour-fringe false hits)."""
    ok = ~np.isnan(x)
    out = x.copy()
    k = 0
    while k < len(x):
        if ok[k]:
            j = k
            while j + 1 < len(x) and ok[j + 1]:
                j += 1
            left = k - 1 >= 0 and not ok[max(k - min_gap, 0):k].any() and k >= min_gap
            right = j + min_gap < len(x) and not ok[j + 1:j + 1 + min_gap].any()
            if j - k + 1 <= max_len and left and right:
                out[k:j + 1] = np.nan
            k = j + 1
        else:
            k += 1
    return out


def fill_gaps(x):
    """Linear interpolation across invisible columns; edge values held. Returns (filled, was_filled)."""
    idx = np.arange(len(x))
    ok = ~np.isnan(x)
    filled = np.interp(idx, idx[ok], x[ok])
    return filled, ~ok


def extract_image(name, verbose=True):
    meta = META[name]
    im = cv2.imread(str(RAW / f"{name}.jpg"))
    quad = order_quad(meta["quad"]) if "quad" in meta else init_quad(im)
    H, c, dots, rms = fit_homography(im, quad)
    rect, Hpx = rectify(im, H, c)
    mpos_div = meta["mpos"] / meta["tb"]
    masks = class_masks(rect)
    excl = marker_exclusions(meta, mpos_div)
    u = np.arange(NCOL) * LCD
    t = (u - 5) * meta["tb"] + meta["mpos"]            # seconds, t = 0 at trigger point
    res = {"t": t, "u": u, "rect": rect, "Hpx": Hpx, "rms_div": rms, "n_dots": len(dots), "ch": {}}
    for ch in shown(meta):
        cov = lcd_coverage(masks[ch], excl[ch])
        lo, hi, cen = read_columns(cov)
        val = drop_islands(follow_path(lo, hi, cen))
        valf, filled = fill_gaps(val)
        vd = meta["vdiv"][ch]
        to_volts = lambda row: (ZERO_V - row * LCD) * vd           # row index -> volts
        res["ch"][ch] = dict(v=to_volts(valf), vmax=to_volts(np.where(np.isnan(lo), valf, lo)),   # smaller row = higher V
                             vmin=to_volts(np.where(np.isnan(hi), valf, hi)), filled=filled,
                             raw_rows=val, cov=cov)
        if verbose:
            print(f"  {name} {ch}: visible {int((~filled).sum())}/{NCOL} columns")
    if verbose:
        print(f"  {name}: {len(dots)} dots, graticule fit RMS {rms:.4f} div")
    return res


# ---------------------------------------------------------------- outputs
def write_csv(name, r):
    import pandas as pd
    df = pd.DataFrame({"time_s": r["t"], "time_ms": r["t"] * 1e3})
    for ch in shown(META[name]):
        d = r["ch"][ch]
        n = signal_name(META[name], ch)
        df[f"{n}_V"] = d["v"]
        df[f"{n}_Vmin"] = d["vmin"]
        df[f"{n}_Vmax"] = d["vmax"]
        df[f"{n}_inferred"] = d["filled"].astype(int)
    path = OUT / f"{name}_traces.csv"
    df.to_csv(path, index=False, float_format="%.6g")
    return df


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    results = {}
    for nm in META:
        r = extract_image(nm)
        cv2.imwrite(str(OUT / f"{nm}_rectified.png"), r["rect"])
        write_csv(nm, r)
        results[nm] = r
    import render
    render.make_all(results, META)
