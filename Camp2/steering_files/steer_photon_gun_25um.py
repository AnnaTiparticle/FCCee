"""
Camp 2 steering file: single photon gun, 50 um MAPS ECAL geometry.

Changes from cld_steer.py baseline:
  - SIM.compactFile  : local geometry with 50 um cells, 12 um Si
  - SIM.enableGun    : True  (particle gun on)
  - SIM.gun.particle : gamma (was mu-)
  - SIM.gun.energy   : 10 GeV
  - SIM.gun.direction: (1,0,0) -> perpendicular to beam, into barrel ECAL
  - SIM.numberOfEvents: set on command line with -N, default 10 for test
"""
import os

from DDSim.DD4hepSimulation import DD4hepSimulation
from g4units import mm, GeV, MeV, m, deg

SIM = DD4hepSimulation()

# --- Geometry: local copy with 500 um cells and 12 um Si ---
# CAMP2_DIR is exported by run_sim.sh (avoids __file__ which is undefined in ddsim exec())
SIM.compactFile = os.path.join(os.environ["CAMP2_DIR"], "geometry/CLD_o2_v07_25um/CLD_o2_v07.xml")

SIM.crossingAngleBoost = 0.015
SIM.enableDetailedShowerMode = True
SIM.enableG4GPS = False
SIM.enableG4Gun = False
SIM.enableGun = True          # particle gun ON

SIM.inputFiles = []
SIM.macroFile = ""
SIM.numberOfEvents = 10       # override with -N on command line
# Energy scan: read from env var (set by run_energy_scan.sh), default 10 GeV
_energy_gev = float(os.environ.get("PHOTON_ENERGY_GEV", "10"))
SIM.outputFile = f"Output/scan_passiveSi/photon_{int(_energy_gev)}GeV_25um_SIM.edm4hep.root"
SIM.printLevel = 3
SIM.runType = "batch"
SIM.skipNEvents = 0
SIM.steeringFile = None
SIM.vertexOffset = [0.0, 0.0, 0.0, 0.0]
SIM.vertexSigma  = [0.0, 0.0, 0.0, 0.0]

# --- Sensitive detector actions (unchanged) ---
SIM.action.tracker = "Geant4TrackerWeightedAction"
SIM.action.calo    = "Geant4ScintillatorCalorimeterAction"
SIM.action.mapActions = {}

# --- Magnetic field (unchanged) ---
SIM.field.delta_chord        = 0.25*mm
SIM.field.delta_intersection = 0.001*mm
SIM.field.delta_one_step     = 0.01*mm
SIM.field.eps_max            = 0.001*mm
SIM.field.eps_min            = 5e-05*mm
SIM.field.equation           = "Mag_UsualEqRhs"
SIM.field.largest_step       = 10.0*m
SIM.field.min_chord_step     = 0.01*mm
SIM.field.stepper            = "ClassicalRK4"

# --- Filters: keep all ECAL deposits (threshold applied in analysis) ---
SIM.filter.calo = "edep0"
SIM.filter.filters = {
    'edep0':   {'parameter': {'Cut': 0.0},   'name': 'EnergyDepositMinimumCut/Cut0'},
    'geantino':{'parameter': {},             'name': 'GeantinoRejectFilter/GeantinoRejector'},
    'edep1kev':{'parameter': {'Cut': 0.001}, 'name': 'EnergyDepositMinimumCut'},
}
SIM.filter.mapDetFilter = {}
SIM.filter.tracker = "edep1kev"

# --- Particle gun ---
SIM.gun.particle   = "gamma"
SIM.gun.energy     = _energy_gev * GeV
SIM.gun.direction  = (1, 0, 0)   # +x: perpendicular to beam, into barrel ECAL
SIM.gun.position   = (0.0, 0.0, 0.0)
SIM.gun.isotrop    = False
SIM.gun.multiplicity = 1
SIM.gun.distribution = None
SIM.gun.phiMin = None
SIM.gun.phiMax = None
SIM.gun.thetaMin = None
SIM.gun.thetaMax = None

# --- Output levels (unchanged) ---
SIM.output.inputStage = 3
SIM.output.kernel     = 3
SIM.output.part       = 3
SIM.output.random     = 6

# --- Particle handler (unchanged) ---
SIM.part.userParticleHandler    = "Geant4TVUserParticleHandler"
SIM.part.keepAllParticles       = False
SIM.part.minDistToParentVertex  = 2.2e-14
SIM.part.minimalKineticEnergy   = 1.0*MeV
SIM.part.printEndTracking       = False
SIM.part.printStartTracking     = False
SIM.part.saveProcesses          = ['Decay']

# --- Physics (unchanged) ---
SIM.physics.decays  = False
SIM.physics.list    = "FTFP_BERT"
SIM.physics.pdgfile = os.path.join(os.environ.get("DD4hepINSTALL"), "examples/DDG4/examples/particle.tbl")
SIM.physics.rangecut = 0.7*mm
SIM.physics.rejectPDGs = {1,2,3,4,5,6,21,23,24,25}

# --- Random (unchanged) ---
SIM.random.enableEventSeed = True
SIM.random.file            = None
SIM.random.luxury          = 1
SIM.random.replace_gRandom = True
SIM.random.seed            = None
SIM.random.type            = None
