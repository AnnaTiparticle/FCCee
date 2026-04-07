"""
pi0_ellipse.py
--------------
For pi0 -> gamma gamma events, fit an ellipse to the hit pattern in the (y, z)
plane using the 2D weighted covariance matrix. Compute eccentricity at two depths:
  - First ECAL layer  (least shower spread, clearest two-photon imprint)
  - Shower maximum    (layer with most deposited energy/hits)

Eccentricity = sqrt(1 - lambda_min / lambda_max), range [0, 1]:
  0 = circular blob (single photon or fully merged)
  1 = line (two clearly separated photons)

No truth-matched clustering needed — works on the raw merged hit blob.

Output: plots/ellipse_eccentricity.png
"""

import numpy as np
import uproot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import os

_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

PI0_DIR           = os.path.join(_BASE, "Output", "pi0scan")
R_ECAL            = 2150.0  # mm, ECAL inner radius
M_PI0             = 0.135   # GeV
R_M               = 9.2     # mm, Moliere radius
STAVE_WINDOW_MM   = 400.0   # transverse hit window around +x stave
FIRST_LAYER_DMAX  = 4.0     # mm — x range above x_min defining "first layer"
MIN_HITS          = 3       # minimum hits to attempt ellipse fit
DIGITAL_THRESHOLD = 1e-6   # GeV = 1 keV
D_TRUTH_MAX       = 2 * 9.2  # mm — only events where showers are merged (d_truth < 2*R_M)

# ── method switch ──────────────────────────────────────────────────────────────
# "covariance"  : weighted 2D covariance matrix (moment-of-inertia ellipse)
# "fitzgibbon"  : direct algebraic least-squares fit (Fitzgibbon 1996)
METHOD = "fitzgibbon"# or "covariance"

# Shower-max parametric constants (CLD ECAL W absorber)
X0_W          = 3.5    # mm, radiation length of W
W_PER_LAYER   = 1.90   # mm of W per layer
L_LAYER       = 5.05   # mm, total layer thickness
X0_PER_LAYER  = W_PER_LAYER / X0_W   # ≈ 0.543 X0 per layer
E_C_GEV       = 0.008  # GeV, critical energy in W

ENERGIES = [20, 50, 100, 200]

CONFIGS = {
    "baseline": dict(color="black",   label="Baseline (5.1mm pad)", mode="analog",  ls="-",  marker="o"),
    "100um":    dict(color="#2ca02c", label="MAPS 100μm",           mode="digital", ls="--", marker="^"),
    "200um":    dict(color="#1f77b4", label="MAPS 200μm",           mode="digital", ls="--", marker="D"),
    "500um":    dict(color="#9467bd", label="MAPS 500μm",           mode="digital", ls="--", marker="P"),
}


# ── helpers ───────────────────────────────────────────────────────────────────

def get_truth_sep(tree, iev):
    """Returns truth gamma-gamma separation at ECAL face (mm), or None."""
    def rd(b):
        return np.array(tree[b].array(entry_start=iev, entry_stop=iev+1)[0])

    pdg     = rd('MCParticles/MCParticles.PDG')
    px_arr  = rd('MCParticles/MCParticles.momentum.x')
    py_arr  = rd('MCParticles/MCParticles.momentum.y')
    pz_arr  = rd('MCParticles/MCParticles.momentum.z')
    dau_beg = rd('MCParticles/MCParticles.daughters_begin').astype(int)
    dau_end = rd('MCParticles/MCParticles.daughters_end').astype(int)
    dau_idx = rd('_MCParticles_daughters/_MCParticles_daughters.index').astype(int)

    g_idxs = []
    for i, pid in enumerate(pdg):
        if pid == 111:
            for d in range(dau_beg[i], dau_end[i]):
                j = dau_idx[d]
                if pdg[j] == 22:
                    g_idxs.append(j)
            break
    if len(g_idxs) != 2:
        return None

    pts = []
    for gi in g_idxs:
        px, py, pz = px_arr[gi], py_arr[gi], pz_arr[gi]
        if px <= 0:
            return None
        t = R_ECAL / px
        pts.append(np.array([py * t, pz * t]))

    return float(np.linalg.norm(pts[1] - pts[0]))


def fitzgibbon_ellipse(y, z, w):
    """
    Fitzgibbon direct least-squares algebraic ellipse fit.
    Fits: A*y² + B*y*z + C*z² + D*y + E*z + F = 0
    Constraint: 4AC - B² = 1  (guarantees ellipse, not hyperbola/parabola).
    Returns eccentricity in [0, 1], or None if fit fails.
    Requires >= 6 weighted points.
    """
    n = len(y)
    if n < 6:
        return None
    w_sum = np.sum(w)
    if w_sum == 0:
        return None

    # scale rows by sqrt(w) for weighted least squares
    sw = np.sqrt(w / w_sum) * n
    D = np.column_stack([
        y**2 * sw, y*z * sw, z**2 * sw, y * sw, z * sw, sw
    ])
    S = D.T @ D   # 6x6 scatter matrix

    # constraint matrix C_mat: encodes 4AC - B² = 1
    C_mat = np.zeros((6, 6))
    C_mat[0, 2] = 2.0
    C_mat[2, 0] = 2.0
    C_mat[1, 1] = -1.0

    try:
        eigenvalues, eigenvectors = np.linalg.eig(np.linalg.inv(S) @ C_mat)
    except np.linalg.LinAlgError:
        return None

    # keep only real, positive eigenvalues — these correspond to ellipse solutions
    real_pos = np.isreal(eigenvalues) & (eigenvalues.real > 1e-10)
    if not np.any(real_pos):
        return None

    # pick the eigenvector with the smallest positive eigenvalue
    idx = np.where(real_pos)[0][np.argmin(eigenvalues.real[real_pos])]
    coeffs = eigenvectors[:, idx].real
    A, B, C = coeffs[0], coeffs[1], coeffs[2]

    # verify it's an ellipse: B² - 4AC < 0
    if B**2 - 4*A*C >= 0:
        return None

    # eccentricity from shape matrix eigenvalues
    # shape matrix: [[A, B/2], [B/2, C]], eigenvalues λ_min ≤ λ_max (both > 0)
    # semi-axes ∝ 1/√λ → major axis along λ_min → e = √(1 - λ_min/λ_max)
    lam = np.linalg.eigvalsh([[A, B/2], [B/2, C]])
    if lam[0] <= 0 or lam[1] <= 0:
        return None

    return float(np.sqrt(max(1.0 - lam[0] / lam[1], 0.0)))


def covariance_ellipse(y, z, w):
    """
    Compute eccentricity from 2D weighted covariance of (y, z) hits.
    Returns eccentricity in [0, 1], or None if not enough hits.
    """
    if len(y) < MIN_HITS:
        return None
    w_sum = np.sum(w)
    if w_sum == 0:
        return None
    yw = np.sum(w * y) / w_sum
    zw = np.sum(w * z) / w_sum
    dy, dz = y - yw, z - zw
    Cyy = np.sum(w * dy**2) / w_sum
    Czz = np.sum(w * dz**2) / w_sum
    Cyz = np.sum(w * dy * dz) / w_sum
    eigenvalues = np.linalg.eigvalsh([[Cyy, Cyz], [Cyz, Czz]])  # ascending
    lam_min, lam_max = eigenvalues[0], eigenvalues[1]
    if lam_max <= 0:
        return None
    return float(np.sqrt(max(1.0 - lam_min / lam_max, 0.0)))


def get_stave_hits(tree, iev, mode):
    """Returns (x, y, z, w) arrays for hits passing the stave filter, or None."""
    def rd(b):
        return np.array(tree[b].array(entry_start=iev, entry_stop=iev+1)[0])

    hit_x = rd('ECalBarrelCollection/ECalBarrelCollection.position.x')
    hit_y = rd('ECalBarrelCollection/ECalBarrelCollection.position.y')
    hit_z = rd('ECalBarrelCollection/ECalBarrelCollection.position.z')
    hit_e = rd('ECalBarrelCollection/ECalBarrelCollection.energy')

    mask = (hit_x > 0) & (np.abs(hit_y) < STAVE_WINDOW_MM) & (np.abs(hit_z) < STAVE_WINDOW_MM)
    if not np.any(mask):
        return None

    x, y, z, e = hit_x[mask], hit_y[mask], hit_z[mask], hit_e[mask]
    w = e if mode == "analog" else (e > DIGITAL_THRESHOLD).astype(float)
    return x, y, z, w


def eccentricity_first_layer(x, y, z, w):
    """Eccentricity using hits in the first ECAL layer only."""
    x_first_max = np.min(x) + FIRST_LAYER_DMAX
    sel = (x <= x_first_max)
    if np.sum(sel) < MIN_HITS:
        return None
    _fit = fitzgibbon_ellipse if METHOD == "fitzgibbon" else covariance_ellipse
    return _fit(y[sel], z[sel], w[sel])


def shower_max_x(E_pi0_gev):
    """
    Parametric x position (mm) of EM shower maximum for a pi0 of given energy.
    Assumes E_gamma = E_pi0 / 2 (average symmetric decay).
    Formula: t_max = ln(E_gamma / E_c) - 0.5  [in radiation lengths]
    """
    E_gamma = E_pi0_gev / 2.0
    t_max_X0 = np.log(E_gamma / E_C_GEV) - 0.5
    depth_mm = t_max_X0 * L_LAYER / X0_PER_LAYER
    return R_ECAL + depth_mm


def eccentricity_shower_max(x, y, z, w, x_smax):
    """
    Eccentricity using hits in the Si layer closest to x_smax.
    Snaps to the nearest actual hit layer (all Si hits at the same x).
    """
    unique_x = np.unique(x)
    nearest_x = unique_x[np.argmin(np.abs(unique_x - x_smax))]
    sel = np.abs(x - nearest_x) < 0.5   # 0.5 mm tolerance — same Si slice
    if np.sum(sel) < MIN_HITS:
        return None
    _fit = fitzgibbon_ellipse if METHOD == "fitzgibbon" else covariance_ellipse
    return _fit(y[sel], z[sel], w[sel])


# ── collect results ────────────────────────────────────────────────────────────

# data[cfg][E] = {"d_truth": [], "ecc_first": [], "ecc_smax": []}
data = {cfg: {E: {"d_truth": [], "ecc_first": [], "ecc_smax": []}
              for E in ENERGIES}
        for cfg in CONFIGS}

for cfg, info in CONFIGS.items():
    for E in ENERGIES:
        fname = os.path.join(PI0_DIR, f"pi0_{E}GeV_{cfg}_SIM.edm4hep.root")
        if not os.path.exists(fname):
            print(f"  missing: {fname}")
            continue
        tree  = uproot.open(fname)["events"]
        x_smax = shower_max_x(E)   # parametric shower max for this energy
        print(f"  {cfg:<12}  {E:>4} GeV:  shower max x = {x_smax:.1f} mm "
              f"(layer ~{(x_smax - R_ECAL) / L_LAYER:.1f})")
        n_first, n_smax = 0, 0
        for iev in range(tree.num_entries):
            d_truth = get_truth_sep(tree, iev)
            if d_truth is None or d_truth > D_TRUTH_MAX:
                continue
            hits = get_stave_hits(tree, iev, info["mode"])
            if hits is None:
                continue
            x, y, z, w = hits

            ecc_f = eccentricity_first_layer(x, y, z, w)
            ecc_s = eccentricity_shower_max(x, y, z, w, x_smax)

            if ecc_f is not None:
                data[cfg][E]["ecc_first"].append(ecc_f)
                n_first += 1
            if ecc_s is not None:
                data[cfg][E]["ecc_smax"].append(ecc_s)
                data[cfg][E]["d_truth"].append(d_truth)
                n_smax += 1

        ecc_f_arr = np.array(data[cfg][E]["ecc_first"])
        ecc_s_arr = np.array(data[cfg][E]["ecc_smax"])
        print(f"  {cfg:<12}  {E:>4} GeV:  "
              f"first={n_first:>4} events (med ecc={np.median(ecc_f_arr):.3f})  "
              f"smax={n_smax:>4} events (med ecc={np.median(ecc_s_arr):.3f})"
              if n_first > 0 and n_smax > 0 else
              f"  {cfg:<12}  {E:>4} GeV:  no valid events")


# ── Plot: median eccentricity vs energy, first layer vs shower max ─────────────

fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
fig.suptitle(r"Ellipse eccentricity vs $\pi^0$ energy  (first ECAL layer vs shower max)",
             fontsize=12)

titles   = ["First ECAL layer", "Shower maximum layer"]
ecc_keys = ["ecc_first", "ecc_smax"]
ylims    = [(0.8, 1.0), (0.0, 1.0)]

for ax, key, title, ylim in zip(axes, ecc_keys, titles, ylims):
    for cfg, info in CONFIGS.items():
        E_arr, med_ecc, p16, p84 = [], [], [], []
        for E in ENERGIES:
            arr = np.array(data[cfg][E][key])
            if len(arr) < 5:
                continue
            E_arr.append(E)
            med_ecc.append(np.median(arr))
            p16.append(np.percentile(arr, 16))
            p84.append(np.percentile(arr, 84))

        if len(E_arr) == 0:
            continue
        E_arr   = np.array(E_arr,   dtype=float)
        med_ecc = np.array(med_ecc)
        p16     = np.array(p16)
        p84     = np.array(p84)

        ax.plot(E_arr, med_ecc, info["marker"] + info["ls"],
                color=info["color"], lw=2, ms=7, label=info["label"])
        ax.fill_between(E_arr, p16, p84, color=info["color"], alpha=0.12)

    ax.set_xscale("log")
    ax.set_xlim(40, 250)
    ax.set_ylim(0.8,1.1)
    ax.set_xticks([20, 50, 100, 200])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel(r"$E_{\pi^0}$ (GeV)", fontsize=11)
    ax.set_ylabel("Median eccentricity  (0=circle, 1=line)", fontsize=11)
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=9, loc="lower left")
    ax.grid(True, which="both", alpha=0.3)

plt.tight_layout()
outf = os.path.join(_BASE, "plots", "ellipse_eccentricity_fit.png")
plt.savefig(outf, dpi=150)
plt.close()
print(f"\nSaved: {outf}")
