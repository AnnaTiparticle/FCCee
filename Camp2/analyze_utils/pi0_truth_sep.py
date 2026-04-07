"""
pi0_truth_sep.py
-----------------
For baseline and 200um, across all pi0 energies (20, 50, 100, 200 GeV):
  - Compute the true gamma-gamma separation at ECAL face from MCParticle truth
  - Plot distributions with delta_X_min = 2*m_pi*R/E and R_M marked

delta_X = 2 * m_pi * R_ECAL / E_pi0   is the minimum possible separation
          (symmetric decay, both photons equal energy)
The actual truth separation per event is always >= delta_X.
"""

import numpy as np
import uproot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

PI0_DIR  = os.path.join(_BASE, "Output", "pi0scan")
R_ECAL   = 2150.0   # mm
M_PI0    = 0.135    # GeV
R_M      = 9.2      # mm, Moliere radius in CLD ECAL (W dominated)

ENERGIES = [20, 50, 100, 200]

CONFIGS = {
    "baseline": dict(color="black",   label="Baseline (5.1mm pad)"),
    "100um":    dict(color="#2ca02c", label="MAPS 100μm"),
    "200um":    dict(color="#1f77b4", label="MAPS 200μm"),
}


def get_truth_sep(tree, iev):
    """
    Returns the true gamma-gamma transverse separation at ECAL face (mm).
    Projects each decay photon momentum from origin to the cylinder R=R_ECAL.
    Returns None if event doesn't have exactly 2 photons from pi0.
    """
    pdg     = np.array(tree["MCParticles/MCParticles.PDG"].array(entry_start=iev, entry_stop=iev+1)[0])
    px_arr  = np.array(tree["MCParticles/MCParticles.momentum.x"].array(entry_start=iev, entry_stop=iev+1)[0])
    py_arr  = np.array(tree["MCParticles/MCParticles.momentum.y"].array(entry_start=iev, entry_stop=iev+1)[0])
    pz_arr  = np.array(tree["MCParticles/MCParticles.momentum.z"].array(entry_start=iev, entry_stop=iev+1)[0])
    dau_beg = np.array(tree["MCParticles/MCParticles.daughters_begin"].array(entry_start=iev, entry_stop=iev+1)[0])
    dau_end = np.array(tree["MCParticles/MCParticles.daughters_end"].array(entry_start=iev, entry_stop=iev+1)[0])
    dau_idx = np.array(tree["_MCParticles_daughters/_MCParticles_daughters.index"].array(entry_start=iev, entry_stop=iev+1)[0])

    photons = []
    for i, pid in enumerate(pdg):
        if pid == 111:  # pi0
            for d in range(dau_beg[i], dau_end[i]):
                j = dau_idx[d]
                if pdg[j] == 22:  # gamma
                    photons.append((px_arr[j], py_arr[j], pz_arr[j]))

    if len(photons) != 2:
        return None

    pts = []
    for (px, py, pz) in photons:
        if px <= 0:
            return None
        t = R_ECAL / px          # project to x = R_ECAL (pi0 shot along +x)
        pts.append((py * t, pz * t))

    dy = pts[0][0] - pts[1][0]
    dz = pts[0][1] - pts[1][1]
    return np.sqrt(dy**2 + dz**2)


# ── collect truth separations ────────────────────────────────────────────────

data = {cfg: {E: [] for E in ENERGIES} for cfg in CONFIGS}

for cfg in CONFIGS:
    for E in ENERGIES:
        fname = os.path.join(PI0_DIR, f"pi0_{E}GeV_{cfg}_SIM.edm4hep.root")
        if not os.path.exists(fname):
            print(f"  missing: {fname}")
            continue
        f    = uproot.open(fname)
        tree = f["events"]
        N    = tree.num_entries
        for iev in range(N):
            sep = get_truth_sep(tree, iev)
            if sep is not None:
                data[cfg][E].append(sep)
        n = len(data[cfg][E])
        arr = np.array(data[cfg][E])
        dmin = 2 * M_PI0 * R_ECAL / E
        print(f"  {cfg:12s}  {E:>4} GeV:  {n:>4} events  "
              f"d_min={dmin:.1f}mm  median={np.median(arr):.1f}mm  "
              f"frac<RM={np.mean(arr < R_M)*100:.1f}%  "
              f"frac<2RM={np.mean(arr < 2*R_M)*100:.1f}%")


# ── plot: one panel per energy, both configs overlaid ───────────────────────

fig, axes = plt.subplots(1, 4, figsize=(16, 5), sharey=False)
fig.suptitle(r"Truth $\gamma\gamma$ separation at ECAL face  ($\pi^0 \to \gamma\gamma$, both configs)",
             fontsize=13)

for ax, E in zip(axes, ENERGIES):
    dmin = 2 * M_PI0 * R_ECAL / E

    # choose x range: from 0 to max(4*dmin, 3*R_M, some headroom)
    xmax = max(4 * dmin, 4 * R_M, 10)
    bins = np.linspace(0, xmax, 60)

    for cfg, info in CONFIGS.items():
        arr = np.array(data[cfg][E])
        if len(arr) == 0:
            continue
        med = np.median(arr)
        ax.hist(arr, bins=bins, histtype="step", lw=2,
                color=info["color"], label=f"{info['label']} (median={med:.1f}mm)", density=True)
        ax.axvline(med, color=info["color"], lw=1.5, ls="-",
                   alpha=0.8)

    # reference lines
    ax.axvline(dmin, color="red",  lw=1.5, ls="--",
               label=fr"$\delta X_{{min}}$ = {dmin:.1f} mm")
    ax.axvline(R_M,  color="gray", lw=1.5, ls=":",
               label=fr"$R_M$ ≈ {R_M:.0f} mm")
    ax.axvline(2*R_M, color="gray", lw=1.0, ls="-.", alpha=0.6,
               label=fr"$2R_M$ ≈ {2*R_M:.0f} mm")

    ax.set_title(f"$E_{{\\pi^0}}$ = {E} GeV", fontsize=11)
    ax.set_xlabel("Truth $\\gamma\\gamma$ separation (mm)", fontsize=9)
    ax.set_ylabel("Density" if E == 20 else "", fontsize=9)
    ax.legend(fontsize=7, loc="upper right")
    ax.set_xlim(0, xmax)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
outf = os.path.join(_BASE, "plots", "truth_sep_all_energies.png")
plt.savefig(outf, dpi=150)
print(f"\nSaved: {outf}")


# ── summary plot: median + percentiles vs energy ─────────────────────────────

fig2, ax2 = plt.subplots(figsize=(8, 5))
ax2.set_title(r"Truth $\gamma\gamma$ separation vs $\pi^0$ energy", fontsize=12)

E_fine = np.linspace(10, 220, 300)
d_fine = 2 * M_PI0 * R_ECAL / E_fine
ax2.plot(E_fine, d_fine, "r--", lw=1.5, label=r"$\delta X_{min} = 2m_\pi R / E$")
ax2.axhline(R_M,   color="gray", lw=1.5, ls=":",  label=fr"$R_M$ ≈ {R_M:.0f} mm")
ax2.axhline(2*R_M, color="gray", lw=1.0, ls="-.", alpha=0.7, label=fr"$2R_M$ ≈ {2*R_M:.0f} mm")

for cfg, info in CONFIGS.items():
    E_arr      = []
    med_arr    = []
    p16_arr    = []
    p84_arr    = []
    for E in ENERGIES:
        arr = np.array(data[cfg][E])
        if len(arr) == 0:
            continue
        E_arr.append(E)
        med_arr.append(np.median(arr))
        p16_arr.append(np.percentile(arr, 16))
        p84_arr.append(np.percentile(arr, 84))
    E_arr   = np.array(E_arr)
    med_arr = np.array(med_arr)
    p16_arr = np.array(p16_arr)
    p84_arr = np.array(p84_arr)
    ax2.plot(E_arr, med_arr, "o-", color=info["color"], lw=2, ms=7, label=f"{info['label']} median")
    ax2.fill_between(E_arr, p16_arr, p84_arr, color=info["color"], alpha=0.15, label=f"{info['label']} 16–84%")

ax2.set_xlabel(r"$E_{\pi^0}$ (GeV)", fontsize=11)
ax2.set_ylabel("$\\gamma\\gamma$ separation at ECAL face (mm)", fontsize=11)
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlim(10, 250)
ax2.set_ylim(1, 200)
ax2.set_xticks([20, 50, 100, 200])
ax2.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
import matplotlib.ticker
ax2.grid(True, which="both", alpha=0.3)
ax2.legend(fontsize=8, loc="upper right")

plt.tight_layout()
outf2 = os.path.join(_BASE, "plots", "truth_sep_vs_energy.png")
plt.savefig(outf2, dpi=150)
print(f"Saved: {outf2}")
