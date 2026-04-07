"""
pi0_reco_sep.py
----------------
Truth-matched SimHit clustering for pi0 -> gamma gamma.

For each SimHit cell, use the Geant4 contribution->MCParticle link to assign
the hit to photon 1 or photon 2 (whichever deposited more energy in that cell).
Then compute the energy-weighted centroid of each photon's cluster and measure
the reconstructed centroid separation.

This is the upper bound on what any real clustering algorithm can achieve —
it's perfect truth-matched clustering at the SimHit level.

Configs: baseline, 100um, 200um, 500um
Energies: 20, 50, 100, 200 GeV
Output: pi0scan/reco_sep_all_energies.png
         pi0scan/reco_sep_vs_energy.png
"""

import numpy as np
import uproot
from collections import deque
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import os
_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

PI0_DIR  = os.path.join(_BASE, "Output", "pi0scan")
R_ECAL   = 2150.0   # mm
M_PI0    = 0.135    # GeV
R_M      = 9.2      # mm, Moliere radius in CLD ECAL

ENERGIES = [20, 50, 100, 200]

CONFIGS = {
    "baseline": dict(color="black",   label="Baseline (5.1mm pad)", mode="analog",  ls="-"),
    "100um":    dict(color="#2ca02c", label="MAPS 100μm",           mode="digital", ls="--"),
    "200um":    dict(color="#1f77b4", label="MAPS 200μm",           mode="digital", ls="--"),
    "500um":    dict(color="#9467bd", label="MAPS 500μm",           mode="digital", ls="--"),
}

DIGITAL_THRESHOLD = 1e-6   # GeV = 1 keV
STAVE_WINDOW_MM   = 400.0  # keep only hits within this box around +x direction


def process_event(tree, iev, mode):
    """
    Returns (d_truth, d_reco) for one event, or (None, None) if unusable.

    d_truth: true gamma-gamma separation at ECAL face from MCParticle momenta
    d_reco:  energy-weighted centroid separation from truth-assigned SimHits
    """
    def rd(branch):
        return np.array(tree[branch].array(entry_start=iev, entry_stop=iev+1)[0])

    # ── MCParticles ───────────────────────────────────────────────────────────
    pdg     = rd('MCParticles/MCParticles.PDG')
    px_arr  = rd('MCParticles/MCParticles.momentum.x')
    py_arr  = rd('MCParticles/MCParticles.momentum.y')
    pz_arr  = rd('MCParticles/MCParticles.momentum.z')
    dau_beg = rd('MCParticles/MCParticles.daughters_begin').astype(int)
    dau_end = rd('MCParticles/MCParticles.daughters_end').astype(int)
    dau_idx = rd('_MCParticles_daughters/_MCParticles_daughters.index').astype(int)

    # find pi0 and its two photon daughters
    g_idxs = []
    for i, pid in enumerate(pdg):
        if pid == 111:
            for d in range(dau_beg[i], dau_end[i]):
                j = dau_idx[d]
                if pdg[j] == 22:
                    g_idxs.append(j)
            break  # only one pi0

    if len(g_idxs) != 2:
        return None, None

    # store photon momenta for truth-at-depth projection later
    g_mom = []
    for gi in g_idxs:
        px, py, pz = px_arr[gi], py_arr[gi], pz_arr[gi]
        if px <= 0:
            return None, None
        g_mom.append((px, py, pz))

    # truth separation at ECAL face (kept for reference only)
    pts_face = [(py/px * R_ECAL, pz/px * R_ECAL) for px, py, pz in g_mom]
    d_truth_face = np.sqrt((pts_face[0][0]-pts_face[1][0])**2 + (pts_face[0][1]-pts_face[1][1])**2)

    # photon label for each MCParticle (propagate through daughters)
    # In practice keepAllParticles=False so only pi0+2 photons exist,
    # but we propagate correctly anyway for generality
    photon_label = np.full(len(pdg), -1, dtype=int)
    photon_label[g_idxs[0]] = 0
    photon_label[g_idxs[1]] = 1
    q = deque(g_idxs)
    while q:
        i = q.popleft()
        for d in range(dau_beg[i], dau_end[i]):
            j = dau_idx[d]
            if photon_label[j] == -1:
                photon_label[j] = photon_label[i]
                q.append(j)

    # ── SimHits and contributions ─────────────────────────────────────────────
    hit_x  = rd('ECalBarrelCollection/ECalBarrelCollection.position.x')
    hit_y  = rd('ECalBarrelCollection/ECalBarrelCollection.position.y')
    hit_z  = rd('ECalBarrelCollection/ECalBarrelCollection.position.z')
    hit_e  = rd('ECalBarrelCollection/ECalBarrelCollection.energy')
    hit_cb = rd('ECalBarrelCollection/ECalBarrelCollection.contributions_begin').astype(int)
    hit_ce = rd('ECalBarrelCollection/ECalBarrelCollection.contributions_end').astype(int)

    contrib_e   = rd('ECalBarrelCollectionContributions/ECalBarrelCollectionContributions.energy')
    contrib_par = rd('_ECalBarrelCollectionContributions_particle/_ECalBarrelCollectionContributions_particle.index').astype(int)

    # stave filter: only hits in +x hemisphere within transverse window
    stave_mask = (hit_x > 0) & (np.abs(hit_y) < STAVE_WINDOW_MM) & (np.abs(hit_z) < STAVE_WINDOW_MM)

    # ── assign each hit to a photon ───────────────────────────────────────────
    # accumulators: [xw, yw, zw, w] per photon  (x = radial depth)
    acc = np.zeros((2, 4), dtype=float)

    for ihit in range(len(hit_x)):
        if not stave_mask[ihit]:
            continue

        # sum contribution energy per photon for this hit
        e_per_photon = np.zeros(2, dtype=float)
        cb, ce = hit_cb[ihit], hit_ce[ihit]
        for k in range(cb, ce):
            par = contrib_par[k]
            if par < len(photon_label):
                lbl = photon_label[par]
                if lbl in (0, 1):
                    e_per_photon[lbl] += contrib_e[k]

        assigned = np.argmax(e_per_photon)
        if e_per_photon[assigned] == 0:
            continue  # no photon contribution to this hit (background)

        # weight for centroid
        if mode == "analog":
            w = hit_e[ihit]
        else:
            w = 1.0 if hit_e[ihit] > DIGITAL_THRESHOLD else 0.0
        if w == 0:
            continue

        acc[assigned, 0] += hit_x[ihit] * w   # radial depth
        acc[assigned, 1] += hit_y[ihit] * w
        acc[assigned, 2] += hit_z[ihit] * w
        acc[assigned, 3] += w

    # require both photons have hits
    if acc[0, 3] == 0 or acc[1, 3] == 0:
        return d_truth_face, None

    # energy-weighted mean depth per photon
    mean_x0 = acc[0, 0] / acc[0, 3]
    mean_x1 = acc[1, 0] / acc[1, 3]

    # truth projected to actual shower depth (apples-to-apples with reco centroid)
    px0, py0, pz0 = g_mom[0]
    px1, py1, pz1 = g_mom[1]
    y0d = py0 / px0 * mean_x0;  z0d = pz0 / px0 * mean_x0
    y1d = py1 / px1 * mean_x1;  z1d = pz1 / px1 * mean_x1
    d_truth_depth = np.sqrt((y0d - y1d)**2 + (z0d - z1d)**2)

    c0 = acc[0, 1:3] / acc[0, 3]   # centroid (y,z) of photon 0
    c1 = acc[1, 1:3] / acc[1, 3]   # centroid (y,z) of photon 1
    d_reco = np.sqrt((c0[0]-c1[0])**2 + (c0[1]-c1[1])**2)

    return d_truth_depth, d_reco


# ── collect results ────────────────────────────────────────────────────────────

data = {cfg: {E: {"truth": [], "reco": []} for E in ENERGIES} for cfg in CONFIGS}

for cfg, info in CONFIGS.items():
    for E in ENERGIES:
        fname = os.path.join(PI0_DIR, f"pi0_{E}GeV_{cfg}_SIM.edm4hep.root")
        if not os.path.exists(fname):
            print(f"  missing: {fname}")
            continue
        f    = uproot.open(fname)
        tree = f["events"]
        n_ok = 0
        for iev in range(tree.num_entries):
            d_t, d_r = process_event(tree, iev, info["mode"])
            if d_t is not None:
                data[cfg][E]["truth"].append(d_t)
            if d_t is not None and d_r is not None:
                data[cfg][E]["reco"].append((d_t, d_r))
                n_ok += 1

        arr_t = np.array(data[cfg][E]["truth"])
        pairs = np.array(data[cfg][E]["reco"])
        if len(pairs):
            arr_r = pairs[:, 1]
            dmin = 2 * M_PI0 * R_ECAL / E
            print(f"  {cfg:<12}  {E:>4} GeV:  {n_ok:>4} events  "
                  f"d_truth median={np.median(arr_t):.1f}mm  "
                  f"d_reco  median={np.median(arr_r):.1f}mm  "
                  f"ratio={np.median(arr_r)/np.median(arr_t):.3f}")


# ── Plot 1: distributions per energy, truth vs reco overlaid ─────────────────

fig, axes = plt.subplots(len(CONFIGS), 4, figsize=(16, 3.5*len(CONFIGS)), sharey=False)
fig.suptitle(r"Truth-matched SimHit clustering: truth (at shower depth) vs reco $\gamma\gamma$ separation",
             fontsize=13)

for row, (cfg, info) in enumerate(CONFIGS.items()):
    for col, E in enumerate(ENERGIES):
        ax = axes[row, col]
        dmin = 2 * M_PI0 * R_ECAL / E
        xmax = max(5 * dmin, 5 * R_M, 15)
        bins = np.linspace(0, xmax, 55)

        pairs = np.array(data[cfg][E]["reco"])
        arr_t = np.array(data[cfg][E]["truth"])

        if len(arr_t):
            ax.hist(arr_t, bins=bins, histtype="step", lw=1.5,
                    color="gray", ls="-", density=True, label="truth", alpha=0.8)
            ax.axvline(np.median(arr_t), color="gray", lw=1.0, ls="-")

        if len(pairs):
            arr_r = pairs[:, 1]
            med_r = np.median(arr_r)
            ax.hist(arr_r, bins=bins, histtype="step", lw=2.0,
                    color=info["color"], density=True,
                    label=f"reco (med={med_r:.1f}mm)")
            ax.axvline(med_r, color=info["color"], lw=1.5, ls="-")

        ax.axvline(dmin, color="red",  lw=1.2, ls="--", label=f"δX_min={dmin:.1f}mm")
        ax.axvline(R_M,  color="black", lw=1.0, ls=":",  label=f"R_M={R_M:.0f}mm")

        if row == 0:
            ax.set_title(f"$E_{{\\pi^0}}$ = {E} GeV", fontsize=10)
        if col == 0:
            ax.set_ylabel(info["label"], fontsize=8)
        ax.set_xlabel("separation (mm)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=6, loc="upper right")
        ax.set_xlim(0, xmax)
        ax.grid(True, alpha=0.25)

plt.tight_layout()
outf1 = os.path.join(PI0_DIR, "reco_sep_all_energies.png")
plt.savefig(outf1, dpi=140)
plt.close()
print(f"\nSaved: {outf1}")


# ── Plot 2: reco median + truth median vs energy, all configs ─────────────────

fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))
fig2.suptitle(r"Reconstructed $\gamma\gamma$ centroid separation vs $\pi^0$ energy  (truth at shower depth)", fontsize=12)

ax_med  = axes2[0]
ax_pull = axes2[1]

E_fine = np.linspace(10, 250, 300)
d_fine = 2 * M_PI0 * R_ECAL / E_fine
ax_med.plot(E_fine, d_fine, "r--", lw=1.5, label=r"$\delta X_{min}$ = $2m_\pi R/E$")
ax_med.axhline(R_M,   color="gray", lw=1.2, ls=":", label=f"$R_M$ ≈ {R_M:.0f} mm")
ax_med.axhline(2*R_M, color="gray", lw=0.8, ls="-.", alpha=0.6, label=f"$2R_M$")

ax_pull.axhline(1.0, color="gray", lw=1.2, ls="--", label="reco = truth")
ax_pull.axhline(0.0, color="black", lw=0.5)

for cfg, info in CONFIGS.items():
    E_arr, med_t, med_r, p16_r, p84_r = [], [], [], [], []
    for E in ENERGIES:
        pairs = np.array(data[cfg][E]["reco"])
        arr_t = np.array(data[cfg][E]["truth"])
        if len(pairs) < 10:
            continue
        arr_r = pairs[:, 1]
        E_arr.append(E)
        med_t.append(np.median(arr_t))
        med_r.append(np.median(arr_r))
        p16_r.append(np.percentile(arr_r, 16))
        p84_r.append(np.percentile(arr_r, 84))

    E_arr  = np.array(E_arr,  dtype=float)
    med_t  = np.array(med_t)
    med_r  = np.array(med_r)
    p16_r  = np.array(p16_r)
    p84_r  = np.array(p84_r)

    # left panel: reco median + band
    ax_med.plot(E_arr, med_r, "o", color=info["color"], ls=info["ls"],
                lw=2, ms=7, label=f"{info['label']} reco")
    ax_med.fill_between(E_arr, p16_r, p84_r, color=info["color"], alpha=0.12)

    # right panel: ratio reco/truth
    ratio = med_r / med_t
    ax_pull.plot(E_arr, ratio, "o-", color=info["color"], lw=2, ms=7,
                 label=info["label"])

# also plot truth medians (same for all — use baseline)
pairs_bl = {E: np.array(data["baseline"][E]["truth"]) for E in ENERGIES}
E_t = np.array([E for E in ENERGIES if len(pairs_bl[E])>0], dtype=float)
med_truth = np.array([np.median(pairs_bl[E]) for E in ENERGIES if len(pairs_bl[E])>0])
ax_med.plot(E_t, med_truth, "k-", lw=1.5, alpha=0.5, label="truth median")

ax_med.set_xscale("log"); ax_med.set_yscale("log")
ax_med.set_xlim(10, 250); ax_med.set_ylim(1, 200)
ax_med.set_xticks([20, 50, 100, 200])
ax_med.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax_med.set_xlabel(r"$E_{\pi^0}$ (GeV)", fontsize=11)
ax_med.set_ylabel(r"Median centroid separation (mm)", fontsize=11)
ax_med.legend(fontsize=7, loc="upper right")
ax_med.grid(True, which="both", alpha=0.3)
ax_med.set_title("Reco median vs truth median", fontsize=11)

ax_pull.set_xscale("log")
ax_pull.set_xlim(10, 250)
ax_pull.set_xticks([20, 50, 100, 200])
ax_pull.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax_pull.set_xlabel(r"$E_{\pi^0}$ (GeV)", fontsize=11)
ax_pull.set_ylabel("Median reco / median truth", fontsize=11)
ax_pull.legend(fontsize=7)
ax_pull.grid(True, which="both", alpha=0.3)
ax_pull.set_title("Centroid bias: reco/truth ratio", fontsize=11)

plt.tight_layout()
outf2 = os.path.join(PI0_DIR, "reco_sep_vs_energy.png")
plt.savefig(outf2, dpi=140)
plt.close()
print(f"Saved: {outf2}")
