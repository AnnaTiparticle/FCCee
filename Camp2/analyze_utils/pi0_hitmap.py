"""
pi0_hitmap.py
Simple 2D hit position plots (y vs z) for pi0 -> gamma gamma events.
Shows summed hit map across all events for each (config, energy).
Run: python pi0_hitmap.py
"""
import sys, os
_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import uproot
except ImportError:
    sys.exit("uproot not found")

PI0_DIR  = os.path.join(_BASE, "Output", "pi0scan")
ENERGIES = [20, 50, 100, 200]
CONFIGS  = {
    "baseline": dict(label="Baseline 5.1mm", mode="analog"),
    "100um":    dict(label="MAPS 100μm",      mode="digital"),
    "200um":    dict(label="MAPS 200μm",      mode="digital"),
    "500um":    dict(label="MAPS 500μm",      mode="digital"),
}
THRESHOLD = 1e-6   # GeV = 1 keV

# ── one figure: rows = energy, cols = config ──────────────────────────────────
nrows = len(ENERGIES)
ncols = len(CONFIGS)
fig, axes = plt.subplots(nrows, ncols, figsize=(4*ncols, 3.5*nrows))
fig.suptitle("π⁰ → γγ  ECAL hit map (y vs z, summed over all events)", fontsize=13)

for row, E in enumerate(ENERGIES):
    for col, (cfg, info) in enumerate(CONFIGS.items()):
        ax = axes[row][col]
        fname = os.path.join(PI0_DIR, f"pi0_{E}GeV_{cfg}_SIM.edm4hep.root")

        if not os.path.exists(fname):
            ax.text(0.5, 0.5, "missing", transform=ax.transAxes, ha="center")
            continue

        f    = uproot.open(fname)
        tree = f["events"]
        ys   = tree["ECalBarrelCollection.position.y"].array()
        zs   = tree["ECalBarrelCollection.position.z"].array()
        es   = tree["ECalBarrelCollection.energy"].array()

        # flatten across all events
        y_all = np.concatenate([np.asarray(a) for a in ys])
        z_all = np.concatenate([np.asarray(a) for a in zs])
        e_all = np.concatenate([np.asarray(a) for a in es])

        if info["mode"] == "digital":
            mask  = e_all > THRESHOLD
            y_all, z_all, w_all = y_all[mask], z_all[mask], np.ones(mask.sum())
        else:
            w_all = e_all

        h = ax.hist2d(y_all, z_all, bins=80, weights=w_all,
                      cmap="hot", norm=matplotlib.colors.LogNorm())
        fig.colorbar(h[3], ax=ax, label="energy (GeV)" if info["mode"]=="analog" else "hits")

        ax.set_xlabel("y (mm)")
        ax.set_ylabel("z (mm)")
        ax.set_title(f"{info['label']}  |  E_π⁰ = {E} GeV", fontsize=9)

plt.tight_layout()
out = "pi0plot.png"
plt.savefig(out, dpi=130)
print(f"Saved {out}")
