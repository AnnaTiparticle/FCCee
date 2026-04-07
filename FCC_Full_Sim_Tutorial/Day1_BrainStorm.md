# Day 1 Brainstorm: MAPS-Based ECAL for FCC-ee
**Date:** 2026-02-24
**Goal:** Evaluate whether MAPS-based electromagnetic calorimetry (inspired by SiD) can deliver improved physics performance at FCC-ee, and whether it is technically feasible given the cooling constraints.

---

## 1. The Core Question

> *If we replace the CLD silicon-pad ECAL with MAPS-based sensors at FCC-ee, do we gain physics performance? Is it feasible given that power pulsing is not possible at a circular collider?*

The key tension:
- **Linear collider (ILC/C³):** ~0.03–0.48% duty cycle → power pulsing → passive cooling → MAPS works
- **FCC-ee (circular):** essentially continuous operation → no power pulsing → active cooling required → material penalty

---

## 2. Key Papers Read

### Brau et al., CALOR 2024 — *Monolithic Active Pixel Sensors for the Linear Collider ECal*
`/sdf/home/p/pbhattar/FCCee_home/epjconf_calor2024_00005.pdf`

**MAPS design (NAPA-p1 based):**
- Pixel pitch: 25 μm × 100 μm (2500 μm² area); future: 25×25 or 25×50 μm²
- Sensitive epitaxial layer: **12 μm thick**
- Detection threshold: ~1 keV (~1/4 MIP)
- Technology: Tower Semiconductor 65 nm CMOS imaging
- Wafer-scale goal: 5 cm × 20 cm

**SiD ECal structure (unchanged longitudinally):**
- 30 layers: 20 × (2.5 mm W + 1.25 mm gap) + 10 × (5 mm W + 1.25 mm gap)
- Total: 26 radiation lengths
- Total Si area: ~1290 m² (barrel + endcap ECal)

**Performance (Figure 6, gamma showers, B=5T):**

| Method | Energy Resolution |
|--------|-----------------|
| TDR analog baseline | 17%/√E ⊕ 1.0% |
| Hits (no optimization) | 16.4%/√E ⊕ 2.0% |
| Weighted clusters (best) | **12.2%/√E ⊕ 1.4%** |
| MIP active pixels | 9.8%/√E ⊕ 1.1% |
| ALL MIPs (ideal) | 8.8%/√E ⊕ 0.2% |

**Two-shower separation:** resolved to **mm scale** (demonstrated for π⁰→γγ, 10 mm separation)

**Cooling strategy (linear collider only):**
- Power pulsing reduces power by **>100×**
- Passive conduction through W to cold plate at module edge
- Temperature rise: 16 K at far corner (ILC, 0.48% duty cycle)
- For FCC-ee (100% duty cycle): would be ~3200 K → **passive cooling impossible**

---

### Habib et al., JINST 2024 — *NAPA-p1: monolithic nanosecond timing pixel*
`/sdf/home/p/pbhattar/FCCee_home/Habib_2024_J._Inst._19_C04033.pdf`

**THE KEY NUMBER:**

| Condition | Power density |
|-----------|--------------|
| Peak (always-on) | **115 mW/cm²** |
| Average at <1% duty cycle | **< 1.15 mW/cm²** |
| Target spec (initial estimate) | < 20 mW/cm² |

**State-of-the-art MAPS comparison (Table 1):**

| Chip | Technology | Pixel pitch | Timing | Power |
|------|-----------|------------|--------|-------|
| ALPIDE | Tower 180 nm | 28 μm | <2000 ns | 5 mW/cm² |
| DPTS | Tower 65 nm | 15 μm | 6.3 ns | 53 mW/cm² |
| NAPA-p1 target | Tower 65 nm | 25 μm | 1 ns | <20 mW/cm² |

**Critical statement from paper:**
> *"These timing structures are quite different from the continuous machines resulting from a circular collider (i.e. FCC or LHC)"*

NAPA-p1 is explicitly NOT designed for FCC-ee. A chip redesign is required.

**Prototype details:**
- 24×24 pixel array, 1.5 mm × 1.5 mm
- ENC: 13 e-rms at C_sensor = 2 fF
- Jitter: < 400 ps-rms
- Pixel current: 600 nA (analog front-end)
- Power pulsing reduces power by factor >100

---

## 3. CLD Baseline Geometry

**Source:** `$K4GEO/FCCee/CLD/compact/CLD_o2_v07/ECalBarrel_o2_v01_03.xml`
(external package — k4geo, not in CLDConfig repo)

### ECAL Barrel Parameters

| Parameter | Value |
|-----------|-------|
| **Cell size (x,y)** | **5.1 × 5.1 mm²** |
| Silicon sensor thickness | 0.50 mm |
| Tungsten absorber/layer | 1.90 mm |
| Number of layers | 40 |
| Inner radius | 2150 mm |
| Outer radius | 2352 mm |
| Total depth | 202 mm |

### Per-layer material stack
```
Tungsten (absorber):   1.90 mm
G10 support:           0.15 mm
Air gap:               0.10 mm
PCB mix:               1.30 mm  ← active layer lives here
Silicon sensor:        0.50 mm  ← replaced by MAPS (12 μm epitaxial)
Ground/HV layer:       0.10 mm
G10 support:           0.75 mm
Air gap:               0.25 mm
─────────────────────────────
Total:                 ~5.05 mm/layer × 40 = 202 mm
```

**Key insight:** MAPS sensor is 12 μm vs current 0.50 mm Si → frees **~0.49 mm per layer** which partially compensates for cooling plate material. More room than initially expected.

---

## 4. The CLD Simulation Chain

```
[1] EVENT GENERATION
    Pythia8 / particle gun → .hepmc file

[2] FULL SIMULATION
    ddsim --steeringFile cld_steer.py
    reads:  $K4GEO/FCCee/CLD/compact/CLD_o2_v07/CLD_o2_v07.xml
    runs:   Geant4 FTFP_BERT, range cut 0.7 mm
    writes: SimCalorimeterHits (ECalBarrelCollection, ECalEndcapCollection)
    output: CLD_SIM.edm4hep.root

[3] DIGITIZATION
    k4run CLDReconstruction.py → CaloDigi.py → DDCaloDigi
    threshold:   50 keV  (5e-05 GeV)
    mode:        ANALOG  (IfDigitalEcal = 0)  ← change to 1 for MAPS
    calibration: CalibrECAL = 37.5227
    timing:      10 ns window
    writes: CalorimeterHits (ECALBarrel, ECALEndcap)

[4] PARTICLE FLOW
    MarlinPandora (Pandora.py)
    reads:  CalorimeterHits + SiTracks_Refitted
    does:   cluster + track matching → PFOs
    writes: PandoraClusters, PandoraPFOs

[5] HIGH-LEVEL RECO
    PFO selection, jet clustering, vertexing, b-tagging
    writes: TightSelectedPandoraPFOs  ← used in plotHiggsMassRecoil.py
```

### What changes for MAPS (file-by-file)

| File | Change needed |
|------|--------------|
| `ECalBarrel_o2_v01_03.xml` (k4geo) | cell size 5.1mm → 25–200 μm; Si 0.50mm → 0.012mm; add cooling layer |
| `CaloDigi.py` | `IfDigitalEcal: 0 → 1`; threshold 50 keV → 1 keV |
| `Pandora.py` + settings | recalibrate for digital hit counting |

---

## 5. Why Current CLD Si Sensors Don't Need Cooling (and Why MAPS Changes Everything)

This is a subtle but critical point that reframes the entire cooling challenge.

### Current CLD Si pad sensor = passive device

A silicon pad sensor is just a **reverse-biased diode**. In steady state it draws only leakage current (~nA/cm²). The sensor itself generates **essentially zero heat**.

The readout ASIC (e.g. SKIROC or similar) sits **at the module edge on a PCB, outside the tungsten-silicon stack**, connected via wire bonds or flex cables:

```
[W absorber][Si pad sensor] ---wire bond--- [ASIC on PCB at module edge]
                                                         ↑
                                               heat generated HERE
                                               outside sensitive volume
                                               cooled at the module rim
```

Heat is removed at the **periphery** of the module — no material needed inside the sensitive volume.

### MAPS = sensor + ASIC integrated everywhere

With MAPS the "monolithic" design means readout electronics are **embedded in the sensor itself**, distributed across the full silicon area:

```
[W absorber][MAPS: sensor + full front-end everywhere]
                           ↑
                  115 mW/cm² generated
                  UNIFORMLY across 2400 m²
                  INSIDE the sensitive volume
                  → cooling needed everywhere
```

### The fundamental difference

| | Current CLD Si pads | MAPS |
|--|---|---|
| Sensor power | ~0 (passive diode) | 115 mW/cm² peak |
| Heat location | Module edge (outside volume) | Everywhere inside volume |
| Cooling needed | Minimal, at periphery | Active, throughout calorimeter |
| Material impact inside detector | **None** | Cooling plates between layers |

**The current CLD ECAL has essentially no cooling inside the calorimeter.** We wouldn't be improving existing cooling — we'd be adding something fundamentally new.

> ⚠️ **Flag:** The specific ASIC model and its exact power/cooling scheme for FCC-ee CLD should be verified against the CLD CDR or detector note. The above reflects general Si-W ECAL design practice.

---

## 6. Power & Feasibility Analysis

### Power density vs pixel size (CLD barrel, 2400 m² total)

| Pixel size | Power density | Total barrel heat | Feasibility |
|-----------|--------------|-------------------|-------------|
| 25 × 25 μm² | 115 mW/cm² | ~2.8 MW | ❌ impossible |
| 50 × 50 μm² | ~29 mW/cm² | ~700 kW | ❌ very hard |
| **100 × 100 μm²** | **~7 mW/cm²** | **~170 kW** | ⚠️ hard but HGCAL-scale |
| 200 × 200 μm² | ~1.8 mW/cm² | ~43 kW | ✅ manageable |

*Power scales as 1/pixel_area (each pixel consumes ~600 nA)*
*CMS HGCAL for reference: designed for ~160 kW*

### Feasibility window: **100–200 μm pixels**
- Still 650–2600× finer than current 5.1 mm cells
- ~100 pixels across Molière radius at 100 μm → negligible pileup
- HGCAL-style CO₂ cooling likely sufficient

### Cooling material estimate
HGCAL-style cooling plate (~0.5 mm Al per layer):
- X₀(Al) = 88.97 mm
- 0.5 mm Al = ~0.56% X₀ per layer
- 40 layers: ~22% X₀ extra (partially offset by thinner MAPS sensor)

---

## 7. The Core Physics Arguments

**Why MAPS gives better energy resolution:**
- Digital hit counting: count shower particles (Poisson statistics) vs measure charge (Landau fluctuations)
- Less susceptible to shower-to-shower fluctuations
- Pixel pileup (saturation) in shower core is the limiting factor → addressed by cluster weighting

**Where MAPS wins most:**
1. **π⁰ → γγ separation** (mm scale vs cm scale) — biggest unique gain, robust to cooling material
2. **Energy resolution** (~28% better stochastic term) — partially degraded by cooling material
3. **Shower position resolution** — useful for photon pointing, π⁰ mass

**The cooling tradeoff:**
- Dead material between sensor and absorber → more showering in gap
- Slight increase in effective absorber per sampling layer
- Estimate: 12.2%/√E (ideal MAPS) → ~13–14%/√E (with 0.5mm Al cooling) — still better than 17%/√E baseline

---

## 8. Performance Metrics for the Study

### Tier 1 — Start here (cleanest)
- **Single photon energy resolution:** σ_E/E = a/√E ⊕ c
  Scan energies: 1, 5, 10, 20, 50 GeV
  Directly comparable to Brau Figure 6

### Tier 2 — The unique MAPS advantage
- **π⁰ → γγ two-photon separation efficiency** vs minimum separation distance
  Run at various π⁰ energies

### Tier 3 — Full physics figure of merit
- **Jet energy resolution:** σ(E_jet)/E_jet for light quark jets
  The ultimate test — does better ECAL translate to better jets?

### Comparison matrix to fill in

```
Metric            | Baseline CLD  | MAPS ideal    | MAPS + cooling
                  | 5.1mm analog  | 100μm, no mat | 100μm + 0.5mm Al
──────────────────────────────────────────────────────────────────
Stochastic term a |     a₀        |      a₁       |      a₂
Constant term c   |     c₀        |      c₁       |      c₂
π⁰ sep. distance  |     d₀        |      d₁       |      d₂
Jet energy res.   |     j₀        |      j₁       |      j₂
```

---

## 8. The Roadmap (4 Base Camps)

### ✅ Base Camp 1 — Understand the Baseline (DONE)
- [x] Understand MAPS technology (NAPA-p1)
- [x] Understand physics case (Brau CALOR 2024)
- [x] Identify core R&D question and feasibility window
- [x] Find CLD ECAL cell size (5.1 mm)
- [x] Understand full simulation chain

### 🔲 Base Camp 2 — Physics Performance Scan (no cooling)
- Modify CLD ECAL segmentation in DD4hep: 5.1mm → 25, 50, 100, 200, 500 μm
- Modify digitization: analog → digital, threshold 50 keV → 1 keV
- Run single photon gun: measure energy resolution vs pixel size
- Run π⁰ gun: measure two-photon separation vs pixel size
- **Result:** performance vs granularity curve (upper bound, no cooling penalty)

### 🔲 Base Camp 3 — Add Cooling Material Penalty
- Add parametric dead material layer per ECAL layer (0.3, 0.5, 1.0 mm Al)
- Re-run same performance metrics
- Find crossover: at what cooling thickness do MAPS gains disappear?
- **Result:** optimal pixel size + cooling material combination

### 🔲 Base Camp 4 — Feasibility & Cost
- Use optimal power density to estimate total heat load
- Compare to HGCAL cooling as engineering reference
- Rough cost estimate (silicon area + cooling infrastructure)
- **Result:** is this detector buildable?

### 🏔️ Summit — The Paper
> *"Can a MAPS-based ECAL at FCC-ee deliver improved physics performance, and is it technically feasible?"*

---

## 9. Open Questions

1. What is the achievable power density of a redesigned NAPA chip for continuous (non-pulsed) operation? The CDS architecture needs rethinking for FCC-ee.
2. Can CO₂ cooling channels fit within the ~0.5 mm freed by the thinner MAPS sensor?
3. At what pixel size does pileup in the shower core start degrading digital performance?
4. Does Pandora PFA need fundamental algorithm changes for ultra-high-granularity input, or just recalibration?
5. Simulation practicality: 100 μm pixels → ~2.4×10¹¹ cells in barrel alone. Need fast digitization or coarser effective granularity approach.

---

## 10. Key Files Reference

| File | Location | Purpose |
|------|----------|---------|
| `ECalBarrel_o2_v01_03.xml` | k4geo (external) | CLD ECAL geometry — cell size lives here |
| `cld_steer.py` | `CLDConfig/CLDConfig/` | DDSim steering — Geant4 simulation |
| `CLDReconstruction.py` | `CLDConfig/CLDConfig/` | Reconstruction steering — runs full chain |
| `CaloDigi.py` | `CLDConfig/CLDConfig/CaloDigi/` | ECAL digitization — threshold, analog/digital mode |
| `Pandora.py` | `CLDConfig/CLDConfig/ParticleFlow/` | PFA — calibration constants |
| `plotHiggsMassRecoil.py` | `FCCee_home/` | Example analysis — uses TightSelectedPandoraPFOs |
| `epjconf_calor2024_00005.pdf` | `FCCee_home/` | Brau CALOR 2024 — MAPS ECal performance |
| `Habib_2024_J._Inst._19_C04033.pdf` | `FCCee_home/` | NAPA-p1 — sensor specs, power numbers |
