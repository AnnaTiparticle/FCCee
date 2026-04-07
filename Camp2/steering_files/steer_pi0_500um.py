"""
Camp 2b steering file: pi0 gun, 500um MAPS geometry.
  - Shoots one pi0 per event; Geant4 decays it to gamma gamma
  - pi0 energy set by env var PI0_ENERGY_GEV (default 50)
  - Output: pi0scan/pi0_<E>GeV_500um_SIM.edm4hep.root

Expected gamma-gamma transverse separation at ECAL face (R=2150mm):
  d ~ R * 2*m_pi / E_pi  (average, isotropic decay in pi0 rest frame)
  20 GeV -> ~29 mm   50 GeV -> ~11.6 mm
  100 GeV -> ~5.8 mm  200 GeV -> ~2.9 mm
"""
import os
from DDSim.DD4hepSimulation import DD4hepSimulation
from g4units import mm, GeV, MeV, m

SIM = DD4hepSimulation()

SIM.compactFile = os.path.join(os.environ["CAMP2_DIR"], "geometry/CLD_o2_v07_500um/CLD_o2_v07.xml")

SIM.crossingAngleBoost     = 0.015
SIM.enableDetailedShowerMode = True
SIM.enableG4GPS = False
SIM.enableG4Gun = False
SIM.enableGun   = True

SIM.inputFiles  = []
SIM.macroFile   = ""
SIM.numberOfEvents = 10

_energy_gev = float(os.environ.get("PI0_ENERGY_GEV", "50"))
SIM.outputFile = f"Output/pi0scan/pi0_{int(_energy_gev)}GeV_500um_SIM.edm4hep.root"
SIM.printLevel = 3
SIM.runType    = "batch"
SIM.skipNEvents = 0
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

# --- pi0 gun ---
SIM.gun.particle     = "pi0"
SIM.gun.energy       = _energy_gev * GeV
SIM.gun.direction    = (1, 0, 0)   # +x: into barrel ECAL
SIM.gun.position     = (0.0, 0.0, 0.0)
SIM.gun.isotrop      = False
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

SIM.part.userParticleHandler   = "Geant4TVUserParticleHandler"
SIM.part.keepAllParticles      = False
SIM.part.minDistToParentVertex = 2.2e-14
SIM.part.minimalKineticEnergy  = 1.0*MeV
SIM.part.printEndTracking      = False
SIM.part.printStartTracking    = False
SIM.part.saveProcesses         = ['Decay']

# decays=True so Geant4 decays pi0 -> gamma gamma
SIM.physics.decays   = True
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
