#!/usr/bin/env python3
"""
fit_resolution_and_histograms.py

All-in-one ECal resolution analysis. For each config, pools the given
.root files per energy point, fits a Gaussian to the per-event
reconstructed energy (four selectable methods), and in one run saves:

  1. The resolution curve (sigma/E vs E, with a/c fit).
  2. One individual histogram PNG per (config, energy): display window is
     the raw data's 0.5-99.5 percentile (not the narrowed fit window),
     80 bins, overlay amplitude taken as the displayed histogram's peak
     count -- plus a chi2/ndof annotation (computed on the actual fit
     window/amplitude) and dashed lines marking the fit-window cut points.
  3. One combined "grid" PNG per config with every energy point's
     histogram on a single page, same per-panel styling as above.

Usage:
    python3 analyze_utils/fit_resolution_and_histograms.py \
        --config baseline scan_baseline_rep2/photon_*.root scan_baseline_rep3/photon_*.root \
        --config X0_0.05  scan_ARC2_x005/photon_*.root \
        --config X0_0.15  scan_ARC2_x015/photon_*.root \
        --config X0_0.30  scan_ARC2_x030/photon_*.root \
        --method original \
        --mode analog \
        --outdir plots

Notes:
    - Energy is inferred per-file from the filename pattern
      photon_{E}GeV_..._SIM.edm4hep.root. The config label is whatever
      you pass after --config.
    - Files sharing an energy within one --config group are pooled
      (concatenated) before both fitting and histogramming.
    - Outputs land in <outdir>/resolution_curve.png and
      <outdir>/histograms/{hist_<config>_<E>GeV.png, grid_<config>_all_energies.png}
"""
import os, re, sys, argparse
from collections import defaultdict
import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
try:
    import uproot
except ImportError:
    sys.exit("uproot not found.")
try:
    import awkward as ak
except ImportError:
    ak = None

THRESHOLD = 1e-6  # GeV = 1 keV, only used in digital mode

DEFAULT_COLORS = {"baseline": "black", "ARC1": "#9467bd"}
FALLBACK_COLORS = ["#d62728", "#2ca02c", "#1f77b4", "#ff7f0e", "#17becf", "#8c564b"]

ENERGY_RE = re.compile(r"(\d+)GeV")


# --------------------------------------------------------------------------
# Fitting
# --------------------------------------------------------------------------

def gaussian(x, A, mu, sigma):
    return A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def fit_gaussian(values, method="original", nbins=80):
    """
    Unified fit covering all four established methods:
        original  -- 0.5-99.5 percentile start, 2 iters, narrow to mu+-2sigma
        reduced   -- 5-95 percentile start, 3 iters, narrow to mu+-1.5sigma
        simple10  -- single-pass fixed 10-90 percentile window
        simple20  -- single-pass fixed 20-80 percentile window

    Returns A, mu, sigma, sigma_err, lo, hi -- the FIT window (used for
    chi2), which is intentionally separate from the wider window used
    for display in the plotting functions below.
    """
    if method == "original":
        lo, hi = np.percentile(values, [0.5, 99.5])
        n_iter, narrow = 2, 2.0
    elif method == "reduced":
        lo, hi = np.percentile(values, [5, 95])
        n_iter, narrow = 3, 1.5
    elif method == "simple10":
        lo, hi = np.percentile(values, [10, 90])
        n_iter, narrow = 1, None
    elif method == "simple20":
        lo, hi = np.percentile(values, [20, 80])
        n_iter, narrow = 1, None
    else:
        raise ValueError(f"Unknown method: {method}")

    A = mu = sigma = sigma_err = None
    for _ in range(n_iter):
        counts, edges = np.histogram(values, bins=nbins, range=(lo, hi))
        centers = 0.5 * (edges[:-1] + edges[1:])
        p0 = [counts.max(), centers[np.argmax(counts)], (hi - lo) / 6]
        try:
            popt, pcov = curve_fit(gaussian, centers, counts, p0=p0, maxfev=10000)
            A, mu, sigma = popt[0], popt[1], abs(popt[2])
            sigma_err = np.sqrt(np.diag(pcov))[2]
            if narrow is not None:
                lo, hi = mu - narrow * sigma, mu + narrow * sigma
        except RuntimeError:
            break
    if mu is None:
        raise RuntimeError("Gaussian fit never converged for this sample.")
    return A, mu, sigma, sigma_err, lo, hi


def chi_squared(values, A, mu, sigma, lo, hi, nbins=80):
    """Chi2/ndof of the Gaussian fit vs binned data in the FIT window [lo, hi]."""
    counts, edges = np.histogram(values, bins=nbins, range=(lo, hi))
    centers = 0.5 * (edges[:-1] + edges[1:])
    expected = gaussian(centers, A, mu, sigma)
    errs = np.sqrt(np.maximum(counts, 1))
    mask = counts > 0
    chi2 = np.sum(((counts[mask] - expected[mask]) / errs[mask]) ** 2)
    ndof = max(mask.sum() - 3, 1)  # 3 fit params: A, mu, sigma
    return chi2, ndof


def resolution_model(E, a, c):
    return np.sqrt((a / np.sqrt(E)) ** 2 + c ** 2)


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

def infer_energy(fname):
    m = ENERGY_RE.search(os.path.basename(fname))
    if not m:
        raise ValueError(f"Could not infer energy (no NGeV pattern) from {fname}")
    return int(m.group(1))


def _sum_collection(arr, mode):
    if mode == "analog":
        return ak.sum(arr, axis=1).to_numpy() if ak is not None \
            else np.array([np.sum(np.asarray(e)) for e in arr])
    return ak.sum(arr > THRESHOLD, axis=1).to_numpy() if ak is not None \
        else np.array([np.sum(np.asarray(e) > THRESHOLD) for e in arr])


def load_raw_energy(fnames, mode="analog"):
    """Pool per-event reconstructed ECal energy (barrel + endcap) across files."""
    raw_parts = []
    for fname in fnames:
        f = uproot.open(fname)
        tree = f["events"]
        raw = _sum_collection(tree["ECalBarrelCollection.energy"].array(), mode)

        if "ECalEndcapCollection.energy" in tree.keys():
            raw = raw + _sum_collection(tree["ECalEndcapCollection.energy"].array(), mode)

        raw_parts.append(np.asarray(raw, dtype=float))
    return np.concatenate(raw_parts)


# --------------------------------------------------------------------------
# Plotting -- matches histograms_of_energies.py's display style exactly:
# wide 0.5-99.5 percentile window on the RAW data (not the narrowed fit
# window), 80 bins, overlay amplitude = displayed histogram's peak count.
# Dashed black lines mark the actual FIT-window cut points, which depend
# on --method and can differ from the display window.
# --------------------------------------------------------------------------

def _display_window_and_amplitude(values, nbins=80):
    lo, hi = np.percentile(values, [0.5, 99.5])
    counts, _ = np.histogram(values, bins=nbins, range=(lo, hi))
    return lo, hi, counts.max()


def plot_single_histogram(values, mu, sigma, chi2, ndof, fit_lo, fit_hi, config, E_true, outdir):
    disp_lo, disp_hi, disp_amp = _display_window_and_amplitude(values)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(values, bins=80, range=(disp_lo, disp_hi), histtype="stepfilled", alpha=0.4,
            label=f"N={len(values)} events")
    xs = np.linspace(disp_lo, disp_hi, 400)
    ax.plot(xs, gaussian(xs, disp_amp, mu, sigma), "r-", lw=2,
            label=f"Gauss fit: \u03bc={mu:.2f}, \u03c3={sigma:.3f}")
    ax.axvline(fit_lo, color="black", linestyle="--", lw=1.2, alpha=0.7,
               label=f"fit cut [{fit_lo:.2f}, {fit_hi:.2f}]")
    ax.axvline(fit_hi, color="black", linestyle="--", lw=1.2, alpha=0.7)
    ax.set_xlabel("Reconstructed energy (GeV)")
    ax.set_ylabel("Events / bin")
    ax.set_title(f"{config}  (E_true = {E_true} GeV)")
    ax.text(0.02, 0.95, f"$\\chi^2$/ndof={chi2/ndof:.2f}", transform=ax.transAxes,
            ha="left", va="top", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", alpha=0.8))
    ax.legend()
    fig.tight_layout()
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"hist_{config}_{E_true}GeV.png")
    fig.savefig(outpath, dpi=120)
    plt.close(fig)
    return outpath


def plot_grid_for_config(per_energy_data, config, outdir):
    """per_energy_data: dict E_true -> (values, mu, sigma, chi2, ndof, fit_lo, fit_hi)"""
    energies = sorted(per_energy_data.keys())
    n = len(energies)
    ncols = 4 if n > 6 else 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.5 * ncols, 3.6 * nrows))
    axes = np.atleast_1d(axes).flatten()

    for i, E_true in enumerate(energies):
        values, mu, sigma, chi2, ndof, fit_lo, fit_hi = per_energy_data[E_true]
        disp_lo, disp_hi, disp_amp = _display_window_and_amplitude(values)
        ax = axes[i]
        ax.hist(values, bins=80, range=(disp_lo, disp_hi), histtype="stepfilled",
                alpha=0.4, color="#1f77b4")
        xs = np.linspace(disp_lo, disp_hi, 300)
        ax.plot(xs, gaussian(xs, disp_amp, mu, sigma), color="crimson", lw=1.5)
        ax.axvline(fit_lo, color="black", linestyle="--", lw=1.0, alpha=0.7)
        ax.axvline(fit_hi, color="black", linestyle="--", lw=1.0, alpha=0.7)
        ax.set_title(f"{E_true} GeV", fontsize=10)
        ax.text(0.95, 0.92, f"$\\chi^2$/ndof={chi2/ndof:.2f}", transform=ax.transAxes,
                ha="right", va="top", fontsize=8,
                bbox=dict(boxstyle="round", fc="white", alpha=0.8))
        ax.tick_params(labelsize=8)

    for j in range(n, len(axes)):
        axes[j].axis("off")

    fig.suptitle(f"{config}: all energy points", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"grid_{config}_all_energies.png")
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    return outpath


def plot_resolution_curve(results, outdir):
    """results: dict config -> list of (E, sigma_over_E, sigma_over_E_err)"""
    fig, ax = plt.subplots(figsize=(7, 5))
    fit_summary = {}

    for idx, (config, points) in enumerate(results.items()):
        points = sorted(points)
        E = np.array([p[0] for p in points], dtype=float)
        y = np.array([p[1] for p in points], dtype=float)
        yerr = np.array([p[2] for p in points], dtype=float)

        color = DEFAULT_COLORS.get(config, FALLBACK_COLORS[idx % len(FALLBACK_COLORS)])
        ax.errorbar(E, y * 100, yerr=yerr * 100, fmt="o", color=color, label=config, capsize=3)

        try:
            popt, pcov = curve_fit(resolution_model, E, y, p0=[0.15, 0.01],
                                    sigma=yerr if np.all(yerr > 0) else None, maxfev=10000)
            a, c = popt
            a_err, c_err = np.sqrt(np.diag(pcov))
            xs = np.linspace(E.min(), E.max(), 200)
            ax.plot(xs, resolution_model(xs, a, c) * 100, color=color, ls="--", alpha=0.7)
            fit_summary[config] = (a, a_err, c, c_err)
        except RuntimeError:
            fit_summary[config] = None

    ax.set_xlabel("Energy (GeV)")
    ax.set_ylabel(r"$\sigma_E / E$ (%)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "resolution_curve.png")
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    return outpath, fit_summary


# --------------------------------------------------------------------------
# CLI / driver
# --------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="All-in-one resolution curve + histogram generator.")
    p.add_argument("--config", nargs="+", action="append", required=True,
                   metavar=("LABEL", "FILES"),
                   help="LABEL followed by one or more ROOT files/globs. Repeatable.")
    p.add_argument("--method", choices=["original", "reduced", "simple10", "simple20"],
                   default="original")
    p.add_argument("--mode", choices=["analog", "digital"], default="analog")
    p.add_argument("--outdir", default="plots")
    return p.parse_args()


def main():
    args = parse_args()
    resolution_results = defaultdict(list)

    for group in args.config:
        config, fnames = group[0], group[1:]
        if not fnames:
            sys.exit(f"No files given for config '{config}'")

        by_energy = defaultdict(list)
        for fname in fnames:
            by_energy[infer_energy(fname)].append(fname)

        per_energy_hist_data = {}
        for E_true, files_for_E in sorted(by_energy.items()):
            values = load_raw_energy(files_for_E, mode=args.mode)
            A, mu, sigma, sigma_err, lo, hi = fit_gaussian(values, method=args.method)
            chi2, ndof = chi_squared(values, A, mu, sigma, lo, hi)

            plot_single_histogram(values, mu, sigma, chi2, ndof, lo, hi,
                                   config, E_true, os.path.join(args.outdir, "histograms"))
            per_energy_hist_data[E_true] = (values, mu, sigma, chi2, ndof, lo, hi)

            sigma_over_E = sigma / mu
            sigma_over_E_err = sigma_err / mu
            resolution_results[config].append((E_true, sigma_over_E, sigma_over_E_err))

            print(f"[{config}] {E_true} GeV: mu={mu:.4f} sigma={sigma:.4f} "
                  f"sigma/E={sigma_over_E*100:.2f}% chi2/ndof={chi2/ndof:.2f}")

        plot_grid_for_config(per_energy_hist_data, config, os.path.join(args.outdir, "histograms"))

    curve_path, fit_summary = plot_resolution_curve(resolution_results, args.outdir)

    print(f"\nSaved resolution curve: {curve_path}")
    for config, fit in fit_summary.items():
        if fit is None:
            print(f"  {config}: fit failed")
        else:
            a, a_err, c, c_err = fit
            print(f"  {config}: a={a*100:.2f}+-{a_err*100:.2f}%  c={c*100:.2f}+-{c_err*100:.2f}%")


if __name__ == "__main__":
    main()
