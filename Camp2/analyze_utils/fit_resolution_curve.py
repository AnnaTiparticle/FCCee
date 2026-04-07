"""
fit_resolution_curve.py
Measure sigma_E/E at each energy for baseline + all MAPS pixel sizes, then fit:

    sigma_E/E = sqrt( (a/sqrt(E))^2 + c^2 )

Usage:
    python fit_resolution_curve.py
"""

import sys, os
_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
from scipy.optimize import curve_fit
import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import uproot
except ImportError:
    sys.exit("uproot not found.")

# ── config ────────────────────────────────────────────────────────────────────
SCAN_DIR        = os.path.join(_BASE, "Output", "scan")
SCAN_PASSIVE_SI = os.path.join(_BASE, "Output", "scan_passiveSi")
ENERGIES   = [1, 5, 15, 20, 50, 100, 200]
THRESHOLD  = 1e-6   # GeV = 1 keV

CONFIGS = {
    "baseline":     dict(mode="analog",  file_key="baseline", label="Baseline (5.1mm, 0.50mm Si)",          color="black",    marker="o", ls="-",  fillstyle="full"),
    "500um_analog": dict(mode="analog",  file_key="500um",    label="MAPS 500um analog  (0.50mm, 12um Si)", color="#9467bd", marker="P", ls=":",  fillstyle="full"),
    "500um":        dict(mode="digital", file_key="500um",    label="MAPS 500um digital (0.50mm, 12um Si)", color="#9467bd", marker="P", ls="--", fillstyle="none"),
    "200um":        dict(mode="digital", file_key="200um",    label="MAPS 200um (0.20mm,  12um Si)",        color="#1f77b4", marker="D", ls="--", fillstyle="none"),
    "100um":        dict(mode="digital", file_key="100um",    label="MAPS 100um (0.10mm,  12um Si)",        color="#2ca02c", marker="^", ls="--", fillstyle="none"),
    "50um":         dict(mode="digital", file_key="50um",     label="MAPS  50um (0.05mm,  12um Si)",        color="#ff7f0e", marker="v", ls="--", fillstyle="none"),
    "25um":         dict(mode="digital", file_key="25um",     label="MAPS  25um (0.025mm, 12um Si)",        color="#d62728", marker=".", ls="--", fillstyle="none"),

}

# ── helpers ───────────────────────────────────────────────────────────────────
def gaussian(x, A, mu, sigma):
    return A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

def fit_gaussian(values, nbins=80, n_iter=2):
    lo, hi = np.percentile(values, [0.5, 99.5])
    mu, sigma, sigma_err = np.mean(values), np.std(values), 0.0
    for _ in range(n_iter):
        counts, edges = np.histogram(values, bins=nbins, range=(lo, hi))
        centers = 0.5 * (edges[:-1] + edges[1:])
        p0 = [counts.max(), centers[np.argmax(counts)], (hi - lo) / 6]
        try:
            popt, pcov = curve_fit(gaussian, centers, counts, p0=p0, maxfev=10000)
            mu, sigma = popt[1], abs(popt[2])
            sigma_err = np.sqrt(np.diag(pcov))[2]
            lo, hi = mu - 2 * sigma, mu + 2 * sigma
        except RuntimeError:
            break
    return mu, sigma, sigma_err

def measure_resolution(fname, mode, E_true):
    f    = uproot.open(fname)
    tree = f["events"]
    tree_keys = tree.keys()

    # Barrel hits (always present)
    hits_barrel = tree["ECalBarrelCollection.energy"].array()
    n   = len(hits_barrel)
    raw = np.zeros(n)
    for i, evt in enumerate(hits_barrel):
        e = np.asarray(evt)
        raw[i] = np.sum(e) if mode == "analog" else float(np.sum(e > THRESHOLD))

    # Endcap hits (add when present — relevant for eta != 0)
    if "ECalEndcapCollection.energy" in tree_keys:
        hits_endcap = tree["ECalEndcapCollection.energy"].array()
        for i, evt in enumerate(hits_endcap):
            e = np.asarray(evt)
            raw[i] += np.sum(e) if mode == "analog" else float(np.sum(e > THRESHOLD))

    calib  = E_true / np.mean(raw)
    E_reco = raw * calib

    mu, sigma, sigma_err = fit_gaussian(E_reco)
    p16, p84 = np.percentile(E_reco, [16, 84])

    return dict(
        res       = sigma / E_true * 100,
        res_err   = sigma_err / E_true * 100,
        contain68 = (p84 - p16) / 2 / E_true * 100,
        n         = n,
    )

def resolution_model(E, a, c):
    return np.sqrt((a / np.sqrt(E))**2 + c**2)

# ── collect results ───────────────────────────────────────────────────────────
results = {cfg: {"E": [], "res": [], "res_err": [], "contain68": []}
           for cfg in CONFIGS}

print(f"\n{'Config':<12} {'E (GeV)':>8} {'N':>6} {'Gauss σ/E':>10} {'68% cont':>9}")
print("-" * 52)

for cfg, info in CONFIGS.items():
    for E in ENERGIES:
        fkey = info.get("file_key", cfg)
        if cfg == "baseline":
            fname = os.path.join(SCAN_DIR, f"photon_{E}GeV_{fkey}_SIM.edm4hep.root")
        else:
            fname = os.path.join(SCAN_PASSIVE_SI, f"photon_{E}GeV_{fkey}_SIM.edm4hep.root")
        if not os.path.exists(fname):
            continue
        r = measure_resolution(fname, info["mode"], float(E))
        results[cfg]["E"].append(E)
        results[cfg]["res"].append(r["res"])
        results[cfg]["res_err"].append(max(r["res_err"], 0.05))
        results[cfg]["contain68"].append(r["contain68"])
        print(f"  {cfg:<12} {E:>8} {r['n']:>6} {r['res']:>9.2f}%  {r['contain68']:>8.2f}%")

# ── fit resolution curve ──────────────────────────────────────────────────────
fit_params = {}
print(f"\n{'Config':<12}  {'a (%√GeV)':>10}  {'c (%)':>7}")
print("-" * 35)
for cfg in CONFIGS:
    E_arr   = np.array(results[cfg]["E"],       dtype=float)
    res_arr = np.array(results[cfg]["res"],      dtype=float)
    err_arr = np.array(results[cfg]["res_err"],  dtype=float)
    if len(E_arr) < 3:
        continue
    try:
        popt, pcov = curve_fit(resolution_model, E_arr, res_arr,
                               sigma=err_arr, p0=[15.0, 1.0],
                               bounds=([0, 0], [100, 20]))
        a, c = popt
        a_err, c_err = np.sqrt(np.diag(pcov))
        fit_params[cfg] = (a, c, a_err, c_err)
        print(f"  {cfg:<12}  {a:>8.2f} ± {a_err:.2f}   {c:>5.2f} ± {c_err:.2f}%")
    except RuntimeError:
        print(f"  {cfg:<12}  fit failed")

# ── plot ──────────────────────────────────────────────────────────────────────
E_fine = np.logspace(np.log10(0.8), np.log10(250), 300)
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle("Photon energy resolution: Baseline CLD vs MAPS pixel sizes", fontsize=13)

for ax, metric, title in [
    (axes[0], "res",       "Gaussian σ_E/E  (fitted)"),
    (axes[1], "contain68", "68% containment width / E  (robust)"),
]:
    ax.set_title(title)
    for cfg, info in CONFIGS.items():
        E_arr = np.array(results[cfg]["E"], dtype=float)
        m_arr = np.array(results[cfg][metric], dtype=float)
        err   = np.array(results[cfg]["res_err"], dtype=float)
        if len(E_arr) == 0:
            continue

        ax.errorbar(E_arr, m_arr, yerr=err,
                    fmt=info["marker"], color=info["color"], ms=7,
                    capsize=4, label=info["label"], zorder=3,
                    lw=1.2)

        if metric == "res" and cfg in fit_params:
            a, c, _, _ = fit_params[cfg]
            ax.plot(E_fine, resolution_model(E_fine, a, c),
                    color=info["color"], lw=1.2, ls=info["ls"], alpha=0.7)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("E (GeV)")
    ax.set_ylabel("σ_E / E  (%)")
    ax.set_xlim(0.8, 250)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    ax.set_xticks([1, 5, 10, 20, 50, 100, 200])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

plt.tight_layout()
outpng = os.path.join(_BASE, "plots", "resolution_curve.png")
plt.savefig(outpng, dpi=150)
print(f"\nPlot saved: {outpng}")
