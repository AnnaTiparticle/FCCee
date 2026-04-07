"""
Generic MAPS steering file — reads pixel size and energy from env vars.

  MAPS_CELL_UM      : pixel size in um (25, 50, 100, 200, 500). Default: 500
  PHOTON_ENERGY_GEV : photon energy in GeV.                      Default: 10
  CAMP2_DIR         : absolute path to Camp2/ dir (set by run_energy_scan.sh)

Output: scan/photon_{E}GeV_{SIZE}um_SIM.edm4hep.root
"""
import os

from DDSim.DD4hepSimulation import DD4hepSimulation
from g4units import mm, GeV, MeV, m

SIM = DD4hepSimulation()

_cell_um    = int(os.environ.get("MAPS_CELL_UM",       "500"))
_energy_gev = float(os.environ.get("PHOTON_ENERGY_GEV", "10"))

SIM.compactFile = os.path.join(
    os.environ["CAMP2_DIR"],
    f"geometry/CLD_o2_v07_{_cell_um}um/CLD_o2_v07.xml"
)
SIM.outputFile = f"scan/photon_{int(_energy_gev)}GeV_{_cell_um}um_SIM.edm4hep.root"

SIM.crossingAngleBoost    = 0.015
SIM.enableDetailedShowerMode = True
SIM.enableG4GPS = False
SIM.enableG4Gun = False
SIM.enableGun   = True
SIM.inputFiles  = []
SIM.macroFile   = ""
SIM.numberOfEvents = 10   # override with -N
SIM.printLevel  = 3
SIM.runType     = "batch"
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

SIM.gun.particle     = "gamma"
SIM.gun.energy       = _energy_gev * GeV
SIM.gun.direction    = (1, 0, 0)
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

SIM.physics.decays   = False
SIM.physics.list     = "FTFP_BERT"
SIM.physics.pdgfile  = os.path.join(os.environ.get("DD4hepINSTALL"),
                                    "examples/DDG4/examples/particle.tbl")
SIM.physics.rangecut = 0.7*mm
SIM.physics.rejectPDGs = {1,2,3,4,5,6,21,23,24,25}

SIM.random.enableEventSeed = True
SIM.random.file            = None
SIM.random.luxury          = 1
SIM.random.replace_gRandom = True
SIM.random.seed            = None
SIM.random.type            = None

# Workaround: addParametersToRunHeader returns a Python dict that cppyy cannot
# convert to std::map<string,string> in the March 9-13 key4hep nightlies.
# Monkey-patch _configureEDM4HEP to skip the broken RunHeader assignment.
import types as _types, logging as _logging

def _fixed_configureEDM4HEP(self, dds, geant4):
    _logging.getLogger("DDSim.Helper.OutputConfig").info(
        "++++ Setting up EDM4hep ROOT::TTree Output ++++")
    e4Out = geant4.setupEDM4hepOutput('EDM4hepOutput', dds.outputFile)
    e4Out.RNTuple = self.useRNTuple
    eventPars = dds.meta.parseMetaParameters()
    # e4Out.RunHeader = ...  ← skipped: cppyy dict→std::map conversion bug
    e4Out.EventParametersString, e4Out.EventParametersInt, e4Out.EventParametersFloat = eventPars
    runPars = dds.meta.parseMetaParameters(parameterType="run")
    e4Out.RunParametersString, e4Out.RunParametersInt, e4Out.RunParametersFloat = runPars
    e4Out.RunNumberOffset  = dds.meta.runNumberOffset  if dds.meta.runNumberOffset  > 0 else 0
    e4Out.EventNumberOffset = dds.meta.eventNumberOffset if dds.meta.eventNumberOffset > 0 else 0

SIM.outputConfig._configureEDM4HEP = _types.MethodType(_fixed_configureEDM4HEP, SIM.outputConfig)
