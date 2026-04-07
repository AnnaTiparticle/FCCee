"""
pi0_last_layer.py
------------------
For each (config, energy): look ONLY at the last ECAL layer (x > 2320mm).

For each event:
  - Project last-layer hits onto the truth photon separation axis
  - Count hits in three regions: core0 | between | core1
  - "Between" = 10%-90% of the way between the two truth positions

Key output: median N_between in last layer vs energy, per config.
This tells you directly: at the shower tail, how many cells are shared
between the two showers — and how that scales with pixel size.
"""

import numpy as np, uproot, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
from collections import deque
import os
_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

PI0_DIR   = os.path.join(_BASE, "Output", "pi0scan")
LAST_LAYER_XMIN = 2320.0   # mm — last ~2 layers
ENERGIES  = [20, 50, 100, 200]
CONFIGS   = {
    "baseline": dict(color="black",   label="Baseline (5.1mm, 500μm Si)", mode="analog",  marker="o", ls="-",  cell_mm=5.10),
    "500um":    dict(color="#9467bd", label="MAPS 500μm",                  mode="digital", marker="P", ls="--", cell_mm=0.50),
    "200um":    dict(color="#1f77b4", label="MAPS 200μm",                  mode="digital", marker="D", ls="--", cell_mm=0.20),
    "100um":    dict(color="#2ca02c", label="MAPS 100μm",                  mode="digital", marker="s", ls="--", cell_mm=0.10),
}
DIGITAL_THRESHOLD = 1e-6


def process_event(tree, iev, mode):
    def rd(b): return np.array(tree[b].array(entry_start=iev, entry_stop=iev+1)[0])

    pdg    = rd('MCParticles/MCParticles.PDG')
    px_arr = rd('MCParticles/MCParticles.momentum.x')
    py_arr = rd('MCParticles/MCParticles.momentum.y')
    pz_arr = rd('MCParticles/MCParticles.momentum.z')
    dau_beg= rd('MCParticles/MCParticles.daughters_begin').astype(int)
    dau_end= rd('MCParticles/MCParticles.daughters_end').astype(int)
    dau_idx= rd('_MCParticles_daughters/_MCParticles_daughters.index').astype(int)

    g_idxs = []
    for i, pid in enumerate(pdg):
        if pid == 111:
            for d in range(dau_beg[i], dau_end[i]):
                j = dau_idx[d]
                if pdg[j] == 22: g_idxs.append(j)
            break
    if len(g_idxs) != 2: return None

    g_mom = []
    for gi in g_idxs:
        px, py, pz = px_arr[gi], py_arr[gi], pz_arr[gi]
        if px <= 0: return None
        g_mom.append((px, py, pz))

    hit_x = rd('ECalBarrelCollection/ECalBarrelCollection.position.x')
    hit_y = rd('ECalBarrelCollection/ECalBarrelCollection.position.y')
    hit_z = rd('ECalBarrelCollection/ECalBarrelCollection.position.z')
    hit_e = rd('ECalBarrelCollection/ECalBarrelCollection.energy')
    hit_cb= rd('ECalBarrelCollection/ECalBarrelCollection.contributions_begin').astype(int)
    hit_ce= rd('ECalBarrelCollection/ECalBarrelCollection.contributions_end').astype(int)
    contrib_e  = rd('ECalBarrelCollectionContributions/ECalBarrelCollectionContributions.energy')
    contrib_par= rd('_ECalBarrelCollectionContributions_particle/_ECalBarrelCollectionContributions_particle.index').astype(int)

    photon_label = np.full(len(pdg), -1, dtype=int)
    photon_label[g_idxs[0]] = 0; photon_label[g_idxs[1]] = 1
    q = deque(g_idxs)
    while q:
        i = q.popleft()
        for d in range(dau_beg[i], dau_end[i]):
            j = dau_idx[d]
            if photon_label[j] == -1:
                photon_label[j] = photon_label[i]; q.append(j)

    # ── get energy-weighted depth for truth projection ────────────────────────
    stave_all = (hit_x > 0) & (np.abs(hit_y) < 400) & (np.abs(hit_z) < 400)
    acc = np.zeros((2, 4))
    for ihit in range(len(hit_x)):
        if not stave_all[ihit]: continue
        ep = np.zeros(2)
        for k in range(hit_cb[ihit], hit_ce[ihit]):
            par = contrib_par[k]
            if par < len(photon_label) and photon_label[par] in (0,1):
                ep[photon_label[par]] += contrib_e[k]
        asgn = np.argmax(ep)
        if ep[asgn] == 0: continue
        w = hit_e[ihit] if mode=='analog' else (1.0 if hit_e[ihit]>DIGITAL_THRESHOLD else 0.0)
        if w == 0: continue
        acc[asgn,0]+=hit_x[ihit]*w; acc[asgn,1]+=hit_y[ihit]*w
        acc[asgn,2]+=hit_z[ihit]*w; acc[asgn,3]+=w

    if acc[0,3]==0 or acc[1,3]==0: return None
    mx0 = acc[0,0]/acc[0,3]; mx1 = acc[1,0]/acc[1,3]

    # truth positions at shower depth
    px0,py0,pz0 = g_mom[0]; px1,py1,pz1 = g_mom[1]
    t0 = np.array([py0/px0*mx0, pz0/px0*mx0])
    t1 = np.array([py1/px1*mx1, pz1/px1*mx1])
    axis = t1 - t0
    d_truth = np.linalg.norm(axis)
    if d_truth < 0.1: return None
    axis_hat = axis / d_truth

    # ── reco centroids projected onto truth axis ─────────────────────────────
    c0 = np.array([acc[0,1]/acc[0,3], acc[0,2]/acc[0,3]])
    c1 = np.array([acc[1,1]/acc[1,3], acc[1,2]/acc[1,3]])
    s_reco_0 = (c0[0]-t0[0])*axis_hat[0] + (c0[1]-t0[1])*axis_hat[1]
    s_reco_1 = (c1[0]-t0[0])*axis_hat[0] + (c1[1]-t0[1])*axis_hat[1]

    # ── all-layer hits projected onto truth axis (for profile plot) ───────────
    hy_a = hit_y[stave_all]; hz_a = hit_z[stave_all]; he_a = hit_e[stave_all]
    w_a  = he_a if mode=='analog' else (he_a > DIGITAL_THRESHOLD).astype(float)
    s_all = (hy_a - t0[0]) * axis_hat[0] + (hz_a - t0[1]) * axis_hat[1]

    # ── last-layer hits only ──────────────────────────────────────────────────
    last = stave_all & (hit_x > LAST_LAYER_XMIN)

    hy_l = hit_y[last]; hz_l = hit_z[last]; he_l = hit_e[last]
    w_l  = he_l if mode=='analog' else (he_l > DIGITAL_THRESHOLD).astype(float)

    # project onto truth axis
    s = (hy_l - t0[0]) * axis_hat[0] + (hz_l - t0[1]) * axis_hat[1]

    n_total   = int(w_l.sum())
    n_between = int(w_l[(s > 0.1*d_truth) & (s < 0.9*d_truth)].sum())
    n_core0   = int(w_l[s < -0.2*d_truth].sum())
    n_core1   = int(w_l[s >  1.2*d_truth].sum())

    return dict(
        d_truth   = d_truth,
        n_total   = n_total,
        n_between = n_between,
        n_core0   = n_core0,
        n_core1   = n_core1,
        s_vals    = s,        # last-layer projected positions
        w_vals    = w_l,
        s_vals_all = s_all,   # all-layer projected positions (for profile)
        w_vals_all = w_a,
        s_reco_0  = s_reco_0, # reco centroid of photon 0 on truth axis
        s_reco_1  = s_reco_1, # reco centroid of photon 1 on truth axis
    )


# ── collect ──────────────────────────────────────────────────────────────────

results = {cfg: {E: [] for E in ENERGIES} for cfg in CONFIGS}

print(f"\n{'Config':<12} {'E':>5}   {'N_ev':>5}  {'N_last_total':>13}  {'N_between':>10}  {'N_core0':>8}  {'N_core1':>8}  {'N_between/cell':>14}")
print("-"*90)

for cfg, info in CONFIGS.items():
    for E in ENERGIES:
        fname = os.path.join(PI0_DIR, f"pi0_{E}GeV_{cfg}_SIM.edm4hep.root")
        if not os.path.exists(fname): continue
        f    = uproot.open(fname)
        tree = f['events']
        evs  = []
        for iev in range(tree.num_entries):
            r = process_event(tree, iev, info['mode'])
            if r: evs.append(r)
        results[cfg][E] = evs

        nt  = np.median([e['n_total']   for e in evs])
        nb  = np.median([e['n_between'] for e in evs])
        nc0 = np.median([e['n_core0']   for e in evs])
        nc1 = np.median([e['n_core1']   for e in evs])
        # hits per cell: for digital this equals N_hits; for analog normalize by typical cell area
        # cell area in mm^2; d_truth window length in between region ~ 0.8 * median d_truth
        d_med = np.median([e['d_truth'] for e in evs])
        between_length = 0.8 * d_med   # mm
        cell = info['cell_mm']
        n_cells_in_gap = between_length / cell   # 1D estimate
        hits_per_cell  = nb / n_cells_in_gap if n_cells_in_gap > 0 else 0

        print(f"  {cfg:<12} {E:>5}   {len(evs):>5}  {nt:>13.1f}  {nb:>10.1f}  {nc0:>8.1f}  {nc1:>8.1f}  {hits_per_cell:>14.2f}")
    print()


# ── Plot 1: N_between in last layer vs energy ─────────────────────────────────

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle(r"Last ECAL layer ($x > 2320$ mm): hits between shower cores", fontsize=12)

ax_nb   = axes[0]
ax_hpc  = axes[1]

for cfg, info in CONFIGS.items():
    E_arr, nb_med, nb_lo, nb_hi = [], [], [], []
    hpc_med, hpc_lo, hpc_hi    = [], [], []
    for E in ENERGIES:
        evs = results[cfg][E]
        if len(evs) < 5: continue
        nb   = np.array([e['n_between'] for e in evs])
        dmed = np.median([e['d_truth']  for e in evs])
        between_len = 0.8 * dmed
        hpc = nb / (between_len / info['cell_mm'])

        E_arr.append(E)
        nb_med.append(np.median(nb)); nb_lo.append(np.percentile(nb,16)); nb_hi.append(np.percentile(nb,84))
        hpc_med.append(np.median(hpc)); hpc_lo.append(np.percentile(hpc,16)); hpc_hi.append(np.percentile(hpc,84))

    E_arr   = np.array(E_arr, dtype=float)
    nb_med  = np.array(nb_med)
    hpc_med = np.array(hpc_med)

    ax_nb.plot(E_arr, nb_med, color=info['color'], marker=info['marker'],
               ls=info['ls'], lw=2, ms=7, label=info['label'])
    ax_nb.fill_between(E_arr, nb_lo, nb_hi, color=info['color'], alpha=0.12)

    ax_hpc.plot(E_arr, hpc_med, color=info['color'], marker=info['marker'],
                ls=info['ls'], lw=2, ms=7, label=info['label'])
    ax_hpc.fill_between(E_arr, hpc_lo, hpc_hi, color=info['color'], alpha=0.12)

for ax, ylabel, title in [
    (ax_nb,  "Median N hits between cores (last layer)",
             "Raw hit count between cores\n(last layer only)"),
    (ax_hpc, "Median hits per cell in gap\n(N_between / N_cells_in_gap)",
             "Occupancy between cores per cell\n(hits per cell in gap, last layer)"),
]:
    ax.set_xlabel(r"$E_{\pi^0}$ (GeV)", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.set_xscale('log'); ax.set_xlim(10, 250)
    ax.set_xticks([20, 50, 100, 200])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.legend(fontsize=8); ax.grid(True, which='both', alpha=0.3)

plt.tight_layout()
outf = os.path.join(_BASE, "plots", "last_layer_between.png")
plt.savefig(outf, dpi=140)
print(f"Saved: {outf}")


# ── Plot 2: 1D hit profile (all layers) along truth axis with reco centroids ──
# One panel per energy, baseline vs 100um overlaid

fig2, axes2 = plt.subplots(1, 4, figsize=(16, 4), sharey=False)
fig2.suptitle(r"1D hit profile along $\gamma\gamma$ axis — all ECAL layers", fontsize=12)

show_cfgs = ["baseline", "100um"]

for col, E in enumerate(ENERGIES):
    ax = axes2[col]
    ref_evs = results['baseline'][E] or results['100um'][E]
    d_med = np.median([e['d_truth'] for e in ref_evs]) if ref_evs else 30.0
    bins  = np.linspace(-1.5*d_med, 2.5*d_med, 60)

    for cfg in show_cfgs:
        info = CONFIGS[cfg]
        evs  = results[cfg][E]
        if not evs: continue
        n_ev  = len(evs)

        # hit profile: all layers
        all_s = np.concatenate([e['s_vals_all'] for e in evs])
        all_w = np.concatenate([e['w_vals_all'] for e in evs])
        ax.hist(all_s, bins=bins, weights=all_w/n_ev,
                histtype='step', lw=2, color=info['color'], label=info['label'])

        # reco centroid lines (median over events)
        sr0 = np.median([e['s_reco_0'] for e in evs])
        sr1 = np.median([e['s_reco_1'] for e in evs])
        # draw at the smaller s first for consistency
        s_lo, s_hi = (sr0, sr1) if sr0 < sr1 else (sr1, sr0)
        ax.axvline(s_lo, color=info['color'], lw=1.5, ls=':', alpha=0.85)
        ax.axvline(s_hi, color=info['color'], lw=1.5, ls=':',  alpha=0.85,
                   label=f'reco centroids ({cfg})')

    # truth reference lines
    ax.axvline(0,      color='gray', lw=1, ls='--', label='truth γ1')
    ax.axvline(d_med,  color='gray', lw=1, ls=':',  label='truth γ2')
    ax.axvspan(0.1*d_med, 0.9*d_med, color='yellow', alpha=0.15, label='between region')
    ax.set_title(f"$E_{{\\pi^0}}$ = {E} GeV\n(d_truth ~ {d_med:.1f} mm)", fontsize=9)
    ax.set_xlabel("s along γγ axis (mm)", fontsize=8)
    ax.set_ylabel("hits / event" if col==0 else "", fontsize=8)
    ax.legend(fontsize=6, loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=7)

plt.tight_layout()
outf2 = os.path.join(_BASE, "plots", "last_layer_profile.png")
plt.savefig(outf2, dpi=140)
print(f"Saved: {outf2}")
