"""
Camp 2 baseline steering file: single photon gun, original CLD geometry.
  - Cell size : 5.1 mm  (baseline)
  - Si thick  : 0.50 mm (baseline)
  - Geometry  : $K4GEO/FCCee/CLD/compact/CLD_o2_v07/CLD_o2_v07.xml (unmodified)

Everything else identical to steer_photon_gun_500um.py.
"""
import os

from DDSim.DD4hepSimulation import DD4hepSimulation
from g4units import mm, GeV, MeV, m, deg

SIM = DD4hepSimulation()

# --- Geometry: original CLD from K4GEO (no local copy needed) ---
SIM.compactFile = os.path.join(os.environ["K4GEO"], "FCCee/CLD/compact/CLD_o2_v07/CLD_o2_v07.xml")

SIM.crossingAngleBoost = 0.015
SIM.enableDetailedShowerMode = True
SIM.enableG4GPS = False
SIM.enableG4Gun = False
SIM.enableGun = True

SIM.inputFiles = []
SIM.macroFile = ""
SIM.numberOfEvents = 10
# Energy scan: read from env var (set by run_energy_scan.sh), default 10 GeV
_energy_gev = float(os.environ.get("PHOTON_ENERGY_GEV", "10"))
SIM.outputFile = f"Output/scan_passiveSi_eta03/photon_{int(_energy_gev)}GeV_baseline_SIM.edm4hep.root"
SIM.printLevel = 3
SIM.runType = "batch"
SIM.skipNEvents = 0
SIM.steeringFile = None
SIM.vertexOffset = [0.0, 0.0, 0.0, 0.0]
SIM.vertexSigma  = [0.0, 0.0, 0.0, 0.0]

SIM.action.tracker = "Geant4TrackerWeightedAction"
SIM.action.calo    = "Geant4ScintillatorCalorimeterAction"
SIM.action.mapActions = {}

SIM.field.delta_chord        = 0.25*mm
SIM.field.delta_intersection = 0.001*mm
SIM.field.delta_one_step     = 0.01*mm
SIM.field.eps_max            = 0.001*mm
SIM.field.eps_min            = 5e-05*mm
SIM.field.equation           = "Mag_UsualEqRhs"
SIM.field.largest_step       = 10.0*m
SIM.field.min_chord_step     = 0.01*mm
SIM.field.stepper            = "ClassicalRK4"

SIM.filter.calo = "edep0"
SIM.filter.filters = {
    'edep0':   {'parameter': {'Cut': 0.0},   'name': 'EnergyDepositMinimumCut/Cut0'},
    'geantino':{'parameter': {},             'name': 'GeantinoRejectFilter/GeantinoRejector'},
    'edep1kev':{'parameter': {'Cut': 0.001}, 'name': 'EnergyDepositMinimumCut'},
}
SIM.filter.mapDetFilter = {}
SIM.filter.tracker = "edep1kev"

SIM.gun.particle   = "gamma"
SIM.gun.energy     = _energy_gev * GeV
SIM.gun.direction  = (0.956, 0, 0.292)   # eta = 0.3
SIM.gun.position   = (0.0, 0.0, 0.0)
SIM.gun.isotrop    = False
SIM.gun.multiplicity = 1
SIM.gun.distribution = None
SIM.gun.phiMin = None
SIM.gun.phiMax = None
SIM.gun.thetaMin = None
SIM.gun.thetaMax = None

SIM.output.inputStage = 3
SIM.output.kernel     = 3
SIM.output.part       = 3
SIM.output.random     = 6

SIM.part.userParticleHandler    = "Geant4TVUserParticleHandler"
SIM.part.keepAllParticles       = False
SIM.part.minDistToParentVertex  = 2.2e-14
SIM.part.minimalKineticEnergy   = 1.0*MeV
SIM.part.printEndTracking       = False
SIM.part.printStartTracking     = False
SIM.part.saveProcesses          = ['Decay']

SIM.physics.decays   = False
SIM.physics.list     = "FTFP_BERT"
SIM.physics.pdgfile  = os.path.join(os.environ.get("DD4hepINSTALL"), "examples/DDG4/examples/particle.tbl")
SIM.physics.rangecut = 0.7*mm
SIM.physics.rejectPDGs = {1,2,3,4,5,6,21,23,24,25}

SIM.random.enableEventSeed = True
SIM.random.file            = None
SIM.random.luxury          = 1
SIM.random.replace_gRandom = True
SIM.random.seed            = None
SIM.random.type            = None
