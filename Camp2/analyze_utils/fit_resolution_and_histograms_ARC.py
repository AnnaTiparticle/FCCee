"""
fit_resolution_and_histograms_ARC.py  ("ARC analysis plots")

Photon energy resolution measurement + fit, selectable analog/digital readout, with:
  - config-agnostic CLI (arbitrary number of --config LABEL FILE... entries)
  - selectable Gaussian-fit method per plotting round
  - per-histogram diagnostic plots (fit overlay + cut-window lines + chi2)
    combined into a single labeled sheet PNG
  - genuine 68%-containment uncertainty (bootstrap resampling)

Usage:
    python fit_resolution_and_histograms_ARC.py \
        --config baseline b_1GeV.root b_5GeV.root b_15GeV.root b_20GeV.root b_50GeV.root b_100GeV.root b_200GeV.root \
        --config ARC1     a_1GeV.root a_5GeV.root a_15GeV.root a_20GeV.root a_50GeV.root a_100GeV.root a_200GeV.root \
        --mode analog --fit-method original

Each --config's file list must be given in ENERGIES order below; missing
files (pass "" or just omit a shorter list) are skipped for that energy.
"""

import sys, os, argparse
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

_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ── config ────────────────────────────────────────────────────────────────────
ENERGIES  = [1, 5, 15, 20, 50, 100, 200]
THRESHOLD = 5e-5   # GeV — zero-suppression cut applied to summed hit energies

FIT_METHODS = ["original", "10simple", "20simple", "reduced", "fitamp"]
FIT_METHOD_LABELS = {
    "original": "original [0.5,99.5] iterative",
    "10simple": "10 simple gauss",
    "20simple": "20 simple gauss",
    "reduced":  "reduced [5,99.5] iterative",
    "fitamp":   "original [0.5,99.5] iterative, fitted amplitude",
}

COLOR_CYCLE  = ["black", "#9467bd", "#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#17becf", "#e377c2"]
MARKER_CYCLE = ["o", "P", "D", "^", "v", ".", "s", "*"]

# ── fit helpers ───────────────────────────────────────────────────────────────
def gaussian(x, A, mu, sigma):
    return A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

def fit_gaussian(values, method="original", nbins=80):
    """
    Returns mu, sigma, sigma_err, the final cut window [lo, hi] actually used
    for the reported fit, plus a WIDE display histogram (always the raw
    [0.5, 99.5] percentile of the full data, regardless of fit method) for
    plotting, and chi2/ndof computed against the actual fit window.
    """
    values = np.asarray(values)

    if method == "original":
        lo, hi = np.percentile(values, [0.5, 99.5])
        n_iter, iterative, use_counts_max = 2, True, True
    elif method == "reduced":
        lo, hi = np.percentile(values, [5, 99.5])
        n_iter, iterative, use_counts_max = 2, True, True
    elif method == "10simple":
        lo, hi = np.percentile(values, [10, 90])
        n_iter, iterative, use_counts_max = 1, False, False
    elif method == "20simple":
        lo, hi = np.percentile(values, [20, 80])
        n_iter, iterative, use_counts_max = 1, False, False
    elif method == "fitamp":
        lo, hi = np.percentile(values, [0.5, 99.5])
        n_iter, iterative, use_counts_max = 2, True, False
    else:
        raise ValueError(f"Unknown fit method: {method}")

    mu, sigma, sigma_err = np.mean(values), np.std(values), 0.0
    A_fit = None

    for i in range(n_iter):
        counts, edges = np.histogram(values, bins=nbins, range=(lo, hi))
        centers = 0.5 * (edges[:-1] + edges[1:])
        p0 = [counts.max(), centers[np.argmax(counts)], (hi - lo) / 6]
        try:
            popt, pcov = curve_fit(gaussian, centers, counts, p0=p0, maxfev=10000)
            A_fit = popt[0]
            mu, sigma = popt[1], abs(popt[2])
            sigma_err = np.sqrt(np.diag(pcov))[2]
            if iterative and i == 0:
                lo, hi = mu - 2 * sigma, mu + 2 * sigma
        except RuntimeError:
            break

    # final histogram at the window actually used, for chi2 computation
    counts, edges = np.histogram(values, bins=nbins, range=(lo, hi))
    centers = 0.5 * (edges[:-1] + edges[1:])

    mask = counts > 0
    if mask.sum() > 0 and sigma > 0:
        A_plot = counts.max() if (use_counts_max or A_fit is None) else A_fit
        expected = gaussian(centers, A_plot, mu, sigma)
        chi2 = float(np.sum(((counts[mask] - expected[mask]) ** 2) / counts[mask]))
        ndof = max(int(mask.sum()) - 3, 1)
    else:
        A_plot = counts.max() if A_fit is None else A_fit
        chi2, ndof = float("nan"), 1

    # separate, wider histogram for display: always the raw [0.5, 99.5] percentile
    # window of the full data, regardless of fit method/cut — so the plotted
    # histogram shows all the data, not just what survived the fit's cut window.
    disp_lo, disp_hi = np.percentile(values, [0.5, 99.5])
    disp_counts, disp_edges = np.histogram(values, bins=nbins, range=(disp_lo, disp_hi))
    disp_centers = 0.5 * (disp_edges[:-1] + disp_edges[1:])
    disp_bin_width = disp_edges[1] - disp_edges[0]
    fit_bin_width = edges[1] - edges[0]
    A_display = A_plot * (disp_bin_width / fit_bin_width) if fit_bin_width > 0 else A_plot

    return dict(mu=mu, sigma=sigma, sigma_err=sigma_err, lo=lo, hi=hi,
                A_fit=A_display, counts=disp_counts, edges=disp_edges, centers=disp_centers,
                chi2=chi2, ndof=ndof)

def resolution_model(E, a, c):
    return np.sqrt((a / np.sqrt(E)) ** 2 + c ** 2)

N_BOOTSTRAP = 500  # resamples used to estimate the SE of the 68% containment width

def bootstrap_contain68_se(values, n_boot=N_BOOTSTRAP, rng=None):
    """Nonparametric SE of (p84-p16)/2 via resampling with replacement."""
    if rng is None:
        rng = np.random.default_rng()
    values = np.asarray(values)
    n = len(values)
    if n == 0:
        return float("nan")
    boot_vals = np.empty(n_boot)
    for b in range(n_boot):
        resample = rng.choice(values, size=n, replace=True)
        p16, p84 = np.percentile(resample, [16, 84])
        boot_vals[b] = (p84 - p16) / 2
    return float(np.std(boot_vals, ddof=1))

# ── measurement ───────────────────────────────────────────────────────────────
def measure_resolution(fnames, E_true, mode="analog", fit_method="original"):
    """
    fnames: list of one or more ROOT file paths to pool (concatenate) for
    this energy point, e.g. multiple reps of the same config/energy.
    """
    raw_parts = []
    for fname in fnames:
        f    = uproot.open(fname)
        tree = f["events"]
        tree_keys = tree.keys()

        hits_barrel = tree["ECalBarrelCollection.energy"].array()
        n   = len(hits_barrel)
        raw = np.zeros(n)
        for i, evt in enumerate(hits_barrel):
            e = np.asarray(evt)
            raw[i] = np.sum(e) if mode == "analog" else float(np.sum(e > THRESHOLD))

        if "ECalEndcapCollection.energy" in tree_keys:
            hits_endcap = tree["ECalEndcapCollection.energy"].array()
            for i, evt in enumerate(hits_endcap):
                e = np.asarray(evt)
                raw[i] += np.sum(e) if mode == "analog" else float(np.sum(e > THRESHOLD))

        raw_parts.append(raw)

    raw = np.concatenate(raw_parts)

    calib  = E_true / np.mean(raw)
    E_reco = raw * calib

    fit = fit_gaussian(E_reco, method=fit_method)
    mu, sigma, sigma_err = fit["mu"], fit["sigma"], fit["sigma_err"]

    p16, p84 = np.percentile(E_reco, [16, 84])
    contain68 = (p84 - p16) / 2
    contain68_err = bootstrap_contain68_se(E_reco)

    return dict(
        res           = sigma / E_true * 100,
        res_err       = sigma_err / E_true * 100,
        contain68     = contain68 / E_true * 100,
        contain68_err = contain68_err / E_true * 100 if np.isfinite(contain68_err) else float("nan"),
        n             = len(raw),
        fit           = fit,
    )

# ── CLI ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="ARC analysis plots — analog photon energy resolution")
parser.add_argument("--config", nargs="+", action="append", required=True,
                     metavar="LABEL FILE...",
                     help="LABEL followed by one ROOT file per energy in ENERGIES order "
                          "(1,5,15,20,50,100,200 GeV). Repeatable.")
parser.add_argument("--mode", choices=["analog", "digital"], default="analog",
                     help="Readout mode for the whole run: analog sums deposited energy, "
                          "digital counts hits above THRESHOLD")
parser.add_argument("--fit-method", choices=FIT_METHODS, default="original",
                     help="Gaussian fit method for this plotting round")
parser.add_argument("--outdir", default=os.path.join(_BASE, "plots"),
                     help="Output directory for plots")
args = parser.parse_args()
os.makedirs(args.outdir, exist_ok=True)

CONFIGS = {}
for entry in args.config:
    label, files = entry[0], entry[1:]
    CONFIGS[label] = files

STYLE = {}
for i, label in enumerate(CONFIGS):
    STYLE[label] = dict(color=COLOR_CYCLE[i % len(COLOR_CYCLE)],
                         marker=MARKER_CYCLE[i % len(MARKER_CYCLE)])

config_list_str = "_".join(CONFIGS.keys())
title_str       = ", ".join(CONFIGS.keys())
fit_label       = FIT_METHOD_LABELS[args.fit_method]

# ── collect results ───────────────────────────────────────────────────────────
results   = {label: {"E": [], "res": [], "res_err": [], "contain68": [], "contain68_err": []}
             for label in CONFIGS}
hist_data = {}  # (label, E) -> fit dict, for diagnostic histogram sheet

print(f"\n{'Config':<15} {'E (GeV)':>8} {'N':>6} {'Gauss sigma/E':>13} {'68% cont':>9}")
print("-" * 58)

for label, files in CONFIGS.items():
    for E, fname_entry in zip(ENERGIES, files):
        if not fname_entry:
            print(f"  [skip] {label} {E}GeV: file not found ({fname_entry})")
            continue
        fnames = [p.strip() for p in fname_entry.split(",") if p.strip()]
        missing = [p for p in fnames if not os.path.exists(p)]
        fnames = [p for p in fnames if os.path.exists(p)]
        if missing:
            print(f"  [warn] {label} {E}GeV: skipping missing file(s): {missing}")
        if not fnames:
            print(f"  [skip] {label} {E}GeV: no valid files ({fname_entry})")
            continue
        try:
            r = measure_resolution(fnames, float(E), mode=args.mode, fit_method=args.fit_method)
        except Exception as exc:
            print(f"  [skip] {label} {E}GeV: unreadable/corrupted file ({fnames}) — {type(exc).__name__}: {exc}")
            continue
        results[label]["E"].append(E)
        results[label]["res"].append(r["res"])
        results[label]["res_err"].append(max(r["res_err"], 0.05))
        results[label]["contain68"].append(r["contain68"])
        results[label]["contain68_err"].append(
            r["contain68_err"] if np.isfinite(r["contain68_err"]) else 0.05)
        hist_data[(label, E)] = r["fit"]
        print(f"  {label:<15} {E:>8} {r['n']:>6} {r['res']:>12.2f}%  {r['contain68']:>8.2f}%")

# ── fit resolution curve ──────────────────────────────────────────────────────
fit_params = {}
print(f"\n{'Config':<15}  {'a (%sqrt(GeV))':>15}  {'c (%)':>7}")
print("-" * 42)
for label in CONFIGS:
    E_arr   = np.array(results[label]["E"],   dtype=float)
    res_arr = np.array(results[label]["res"],  dtype=float)
    err_arr = np.array(results[label]["res_err"], dtype=float)
    if len(E_arr) < 3:
        continue
    try:
        popt, pcov = curve_fit(resolution_model, E_arr, res_arr,
                               sigma=err_arr, p0=[15.0, 1.0],
                               bounds=([0, 0], [100, 20]))
        a, c = popt
        a_err, c_err = np.sqrt(np.diag(pcov))
        fit_params[label] = (a, c, a_err, c_err)
        print(f"  {label:<15}  {a:>13.2f} +/- {a_err:.2f}   {c:>5.2f} +/- {c_err:.2f}%")
    except RuntimeError:
        print(f"  {label:<15}  fit failed")

# ── plot: resolution curve ────────────────────────────────────────────────────
E_fine = np.logspace(np.log10(0.8), np.log10(250), 300)
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle(f"ARC analysis plots — {title_str} — mode: {args.mode} — fit: {fit_label}", fontsize=12)

for ax, metric, err_key, title in [
    (axes[0], "res",       "res_err",       "Gaussian sigma_E/E (fitted)"),
    (axes[1], "contain68", "contain68_err", "68% containment width / E"),
]:
    ax.set_title(title)
    for label in CONFIGS:
        E_arr = np.array(results[label]["E"], dtype=float)
        m_arr = np.array(results[label][metric], dtype=float)
        err   = np.array(results[label][err_key], dtype=float)
        if len(E_arr) == 0:
            continue
        style = STYLE[label]
        ax.errorbar(E_arr, m_arr, yerr=err,
                    fmt=style["marker"], color=style["color"], ms=7,
                    capsize=4, label=label, zorder=3, lw=1.2)
        if metric == "res" and label in fit_params:
            a, c, _, _ = fit_params[label]
            ax.plot(E_fine, resolution_model(E_fine, a, c),
                    color=style["color"], lw=1.2, ls="--", alpha=0.7)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("E (GeV)")
    ax.set_ylabel("sigma_E / E (%)")
    ax.set_xlim(0.8, 250)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    ax.set_xticks([1, 5, 10, 20, 50, 100, 200])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

plt.tight_layout()
outpng_curve = os.path.join(args.outdir, f"ARC_analysis_plots_resolution_curve_{config_list_str}_{args.mode}_{args.fit_method}.png")
plt.savefig(outpng_curve, dpi=150)
plt.close(fig)
print(f"\nResolution curve plot saved: {outpng_curve}")

# ── plot: resolution ratio to baseline ────────────────────────────────────────
if "baseline" in CONFIGS and len(results["baseline"]["E"]) > 0:
    fig_ratio, axes_ratio = plt.subplots(1, 2, figsize=(15, 6))
    fig_ratio.suptitle(f"ARC analysis plots (ratio to baseline) — {title_str} — mode: {args.mode} — fit: {fit_label}", fontsize=12)

    base_E = results["baseline"]["E"]

    for ax, metric, title in [
        (axes_ratio[0], "res",       "Gaussian sigma_E/E ratio (config / baseline)"),
        (axes_ratio[1], "contain68", "68% containment ratio (config / baseline)"),
    ]:
        ax.set_title(title)
        ax.axhline(1.0, color="gray", ls=":", lw=1, label="Baseline (ratio = 1)")
        for label in CONFIGS:
            if label == "baseline":
                continue
            style = STYLE[label]
            common_E, ratios = [], []
            for e, val in zip(results[label]["E"], results[label][metric]):
                if e in base_E:
                    base_val = results["baseline"][metric][base_E.index(e)]
                    if base_val != 0:
                        common_E.append(e)
                        ratios.append(val / base_val)
            if not common_E:
                continue
            ax.plot(common_E, ratios, marker=style["marker"], color=style["color"],
                    label=label, lw=1.2)

        ax.set_xscale("log")
        ax.set_xlabel("E (GeV)")
        ax.set_ylabel("Ratio to baseline")
        ax.set_xlim(0.8, 250)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8, loc="best")
        ax.set_xticks([1, 5, 10, 20, 50, 100, 200])
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

    plt.tight_layout()
    outpng_ratio = os.path.join(args.outdir, f"ARC_analysis_plots_resolution_ratio_{config_list_str}_{args.mode}_{args.fit_method}.png")
    plt.savefig(outpng_ratio, dpi=150)
    plt.close(fig_ratio)
    print(f"Resolution ratio-to-baseline plot saved: {outpng_ratio}")
else:
    print("Skipping ratio-to-baseline plot: no 'baseline' config present in this run.")

# ── plot: histogram diagnostic sheet ──────────────────────────────────────────
labels_with_data = [label for label in CONFIGS if any(E in results[label]["E"] for E in ENERGIES)]
n_rows = len(labels_with_data)
n_cols = len(ENERGIES)

if n_rows > 0:
    fig2, axes2 = plt.subplots(n_rows, n_cols, figsize=(3.2 * n_cols, 3.0 * n_rows), squeeze=False)
    fig2.suptitle(f"ARC analysis plots — histogram sheet — {title_str} — mode: {args.mode} — fit: {fit_label}", fontsize=12)

    for row, label in enumerate(labels_with_data):
        for col, E in enumerate(ENERGIES):
            ax = axes2[row][col]
            fit = hist_data.get((label, E))
            if fit is None:
                ax.axis("off")
                continue

            counts, edges, centers = fit["counts"], fit["edges"], fit["centers"]
            mu, sigma, lo, hi, A_fit = fit["mu"], fit["sigma"], fit["lo"], fit["hi"], fit["A_fit"]
            chi2, ndof = fit["chi2"], fit["ndof"]

            ax.bar(centers, counts, width=(edges[1] - edges[0]),
                   color="#7fb3d5", edgecolor="none", linewidth=0, alpha=0.9)
            if sigma > 0:
                x_fine = np.linspace(edges[0], edges[-1], 300)
                ax.plot(x_fine, gaussian(x_fine, A_fit, mu, sigma),
                        color="red", lw=1.3)
            ax.axvline(lo, color="blue", ls="--", lw=1)
            ax.axvline(hi, color="blue", ls="--", lw=1)

            chi2_txt = f"chi2/ndof={chi2/ndof:.2f}" if np.isfinite(chi2) else "chi2/ndof=n/a"
            ax.text(0.03, 0.95, chi2_txt, transform=ax.transAxes,
                    ha="left", va="top", fontsize=7)
            ax.set_title(f"{label}  {E} GeV", fontsize=9)
            ax.tick_params(labelsize=7)

    plt.tight_layout()
    outpng_hist = os.path.join(args.outdir, f"ARC_analysis_plots_histogram_sheet_{config_list_str}_{args.mode}_{args.fit_method}.png")
    plt.savefig(outpng_hist, dpi=150)
    plt.close(fig2)
    print(f"Histogram sheet saved: {outpng_hist}")

    # ── individual per-config sheets (one figure per config, all energies) ────
    n_e_cols = 4
    n_e_rows = int(np.ceil(len(ENERGIES) / n_e_cols))
    for label in labels_with_data:
        fig3, axes3 = plt.subplots(n_e_rows, n_e_cols, figsize=(4.0 * n_e_cols, 3.5 * n_e_rows), squeeze=False)
        fig3.suptitle(f"{label}: all energy points  —  fit: {fit_label}", fontsize=12)

        for idx, E in enumerate(ENERGIES):
            row, col = divmod(idx, n_e_cols)
            ax = axes3[row][col]
            fit = hist_data.get((label, E))
            if fit is None:
                ax.axis("off")
                continue

            counts, edges, centers = fit["counts"], fit["edges"], fit["centers"]
            mu, sigma, lo, hi, A_fit = fit["mu"], fit["sigma"], fit["lo"], fit["hi"], fit["A_fit"]
            chi2, ndof = fit["chi2"], fit["ndof"]

            ax.bar(centers, counts, width=(edges[1] - edges[0]),
                   color="#7fb3d5", edgecolor="none", linewidth=0, alpha=0.9)
            if sigma > 0:
                x_fine = np.linspace(edges[0], edges[-1], 300)
                ax.plot(x_fine, gaussian(x_fine, A_fit, mu, sigma),
                        color="red", lw=1.3)
            ax.axvline(lo, color="blue", ls="--", lw=1)
            ax.axvline(hi, color="blue", ls="--", lw=1)

            chi2_txt = f"chi2/ndof={chi2/ndof:.2f}" if np.isfinite(chi2) else "chi2/ndof=n/a"
            ax.text(0.03, 0.95, chi2_txt, transform=ax.transAxes,
                    ha="left", va="top", fontsize=8)
            ax.set_title(f"{E} GeV", fontsize=10)

        # blank out any unused trailing subplot cells
        for idx in range(len(ENERGIES), n_e_rows * n_e_cols):
            row, col = divmod(idx, n_e_cols)
            axes3[row][col].axis("off")

        plt.tight_layout()
        outpng_single = os.path.join(args.outdir, f"ARC_analysis_plots_histogram_single_{label}_{args.mode}_{args.fit_method}.png")
        plt.savefig(outpng_single, dpi=150)
        plt.close(fig3)
        print(f"Individual histogram sheet saved: {outpng_single}")

# ============================================================================
# Per-energy config overlays: for each energy point, one graph overlaying
# every config's Gaussian fit (peaks are aligned, since each config is
# calibrated to its own true energy in measure_resolution above).
# ============================================================================
_ov_dir = os.path.join(args.outdir, "config_overlays")
os.makedirs(_ov_dir, exist_ok=True)
for E in ENERGIES:
    _entries = [(label, hist_data[(label, E)]) for label in CONFIGS
                if (label, E) in hist_data]
    if len(_entries) < 2:
        continue
    _figov, _axov = plt.subplots(figsize=(8.5, 6))
    for label, fit in _entries:
        color = STYLE[label]["color"]
        counts, edges, centers = fit["counts"], fit["edges"], fit["centers"]
        mu, sigma, A_fit = fit["mu"], fit["sigma"], fit["A_fit"]
        peak = counts.max() if counts.max() > 0 else 1.0
        e_idx = results[label]["E"].index(E)
        res = results[label]["res"][e_idx]
        _axov.bar(centers, counts / peak, width=(edges[1] - edges[0]),
                  color=color, alpha=0.15, edgecolor="none", zorder=1)
        _axov.step(edges, np.append(counts, counts[-1]) / peak, where="post",
                   color=color, lw=1.2, zorder=2)
        if sigma > 0:
            x_fine = np.linspace(edges[0], edges[-1], 300)
            _axov.plot(x_fine, gaussian(x_fine, A_fit, mu, sigma) / peak,
                       color=color, lw=2.2, zorder=3,
                       label=f"{label}   mu={mu:.2f} GeV,  sigma/E={res:.2f}%")
        _axov.axvline(mu, color=color, ls="--", lw=1.0, alpha=0.4, zorder=2)
    _axov.set_xlabel("Reconstructed ECal energy [GeV]")
    _axov.set_ylabel("Normalized counts (peak = 1)")
    _axov.set_title(f"Config comparison @ {E} GeV - mode: {args.mode} - fit: {fit_label}")
    _axov.grid(True, ls=":", alpha=0.4)
    _axov.legend(fontsize=9, loc="best")
    plt.tight_layout()
    _outov = os.path.join(_ov_dir,
        f"ARC_config_overlay_{E}GeV_{config_list_str}_{args.mode}_{args.fit_method}.png")
    plt.savefig(_outov, dpi=150)
    plt.close(_figov)
    print(f"Config overlay ({E} GeV) saved: {_outov}")
