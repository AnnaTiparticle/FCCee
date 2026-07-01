# FCCee MAPS ECAL Study

A physics performance study exploring the addition of an ARC-like structure to the baseline CLD ECAL. The goal is to study the loss in photon energy resolution and π⁰ → γγ separation with the addition of a possible ARC.

---

## Roadmap

### Camp 2 — Physics performance scan *(in progress)*
- [x] Replace baseline analog 5×5 mm² Si pads with digital MAPS sensors at pixel pitches of 25, 50, 100, 200, and 500 μm
- [x] Single photon energy resolution scan: σ_E/E = a/√E ⊕ c over 1–200 GeV
- [x] π⁰ → γγ two-photon separation study at truth and reco level
- [x] Shower shape eccentricity analysis for merged showers

### Camp 3 — Cooling material penalty *(future)*
- [ ] Add active cooling layers to the ECAL geometry and repeat the Camp 2 studies

### Camp 4 — Full PFA study *(future)*
- [ ] Full simulation with Pandora PFA to evaluate jet energy resolution improvement

---

## Repository Structure

```
FCCee/
├── Camp2/
│   ├── steering_files/       # ddsim steering files for photon gun and π⁰ gun
│   ├── analyze_utils/        # analysis scripts (energy resolution, π⁰ separation, ellipse)
│   ├── geometry/             # modified CLD ECAL geometry XMLs per pixel size
│   ├── run_scan_flat.sh      # run photon energy scan (eta=0)
│   ├── run_scan_eta03.sh     # run photon energy scan (eta=0.3)
│   ├── run_pi0_scan.sh       # run π⁰ scan
│   └── plots/                # output HTML plots (served via GitHub Pages)
└── FCC_Full_Sim_Tutorial/
    ├── fcc-tutorials/        # submodule: HEP-FCC/fcc-tutorials
    ├── CLDConfig/            # submodule: key4hep/CLDConfig
    └── Day1_BrainStorm.md
```

---

## Setup

### 1. Clone the repository
```bash
git clone --recurse-submodules https://github.com/AnnaTiparticle/FCCee.git
cd FCCee
```

### 2. Start the AlmaLinux 9 container (on SDF/SLAC)
```bash
setupalma9
```
Or manually:
```bash
apptainer exec -B /sdf,/fs /cvmfs/atlas.cern.ch/repo/containers/fs/singularity/x86_64-almalinux9 bash
```

### 3. Source the key4hep software stack
```bash
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh 
```

### 4. Set the Camp2 directory variable
```bash
export CAMP2_DIR=/path/to/FCCee/Camp2
```

You should now be able to run simulations and analysis scripts.

---

## Running Simulations

### Photon energy scan (η = 0, baseline + all MAPS configs)
```bash
cd $CAMP2_DIR
bash run_scan_flat.sh
```

### Photon energy scan at η = 0.3
```bash
bash run_scan_eta03.sh
```

### π⁰ → γγ scan
```bash
bash run_pi0_scan.sh
```

Simulation output (EDM4hep ROOT files) is written to `Camp2/Output/` (a symlink to the data storage area).

---

## Analysis Scripts

All scripts are in `Camp2/analyze_utils/` and can be run from anywhere:

| Script | Description |
|---|---|
| `fit_resolution_curve.py` | Fit σ_E/E = a/√E ⊕ c for all configs and plot resolution curves |
| `pi0_truth_sep.py` | Truth γγ separation at ECAL face from MCParticle momenta |
| `pi0_reco_sep.py` | Truth-matched SimHit clustering; reconstructed centroid separation |
| `pi0_hitmap.py` | 2D hit maps for π⁰ events |
| `pi0_interactive.py` | Interactive Plotly hit maps (saved as HTML) |
| `pi0_ellipse.py` | Shower shape eccentricity for merged showers (first layer + shower max) |
| `pi0_last_layer.py` | Hit profile along the γγ axis in the last ECAL layer |

---

## Interactive Plots

HTML plots are served via GitHub Pages and can be linked directly in presentations:

**[Camp 2 plots index](https://pbhattarai1s.github.io/FCCee/Camp2/plots/)**

To update plots after regenerating them locally:
```bash
git add Camp2/plots/*.html
git commit -m "update interactive plots"
git push
```
