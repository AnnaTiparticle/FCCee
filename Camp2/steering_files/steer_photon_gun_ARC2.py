#!/usr/bin/env python3
"""
Camp2 steering file: single photon gun, ARC2 CLD geometry with the
Plexiglass insert filled to a specified fraction of a radiation length (X0),
inside the fixed 200mm TrackerECalGap envelope.

Requires (in addition to the usual CAMP2_DIR / PHOTON_ENERGY_GEV):
    ARC2_GEOM_NAME  e.g. "CLD_o2_v07_ARC2_X0_0.25"
                    (produced by generate_arc_x0_variant.py -- run that
                    first, this file does not generate geometry itself)
"""
import os

from DDSim.DD4hepSimulation import DD4hepSimulation
from g4units import mm, GeV, MeV, m, deg

SIM = DD4hepSimulation()

# --- Geometry: ARC2 X0-scan variant ---
geom_name = os.environ.get("ARC2_GEOM_NAME")
if not geom_name:
    raise RuntimeError(
        "ARC2_GEOM_NAME not set. Run generate_arc_x0_variant.py first, then "
        "export ARC2_GEOM_NAME=CLD_o2_v07_ARC2_X0_<fraction> before calling ddsim."
    )
SIM.compactFile = os.path.join(os.environ["CAMP2_DIR"], "geometry", geom_name, "CLD_o2_v07.xml")

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
SIM.outputFile = f"Output/scan_{geom_name}/photon_{int(_energy_gev)}GeV_{geom_name}_SIM.edm4hep.root"
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
SIM.field.eps_max             = 0.001
SIM.field.eps_min             = 0.00005
SIM.field.largest_step       = 10.0*m
SIM.field.min_chord_step     = 0.01*mm
SIM.field.stepper            = "ClassicalRK4"

SIM.filter.calo = "edep0"
SIM.filter.filters = {
     'edep0':   {'parameter': {'Cut': 0.0},   'name': 'EnergyDepositMinimumCut/Cut0'},
     'edep1kev':{'parameter': {'Cut': 1.0*MeV/1000}, 'name': 'EnergyDepositMinimumCut/Cut1'},
}
SIM.filter.mapDetFilter = {}
SIM.filter.tracker = "edep1kev"

SIM.gun.particle   = "gamma"
SIM.gun.energy     = _energy_gev * GeV
SIM.gun.direction  = (1, 0, 0)   # +x: perpendicular to beam, into barrel ECAL
SIM.gun.position   = (0.0, 0.0, 0.0)
SIM.gun.isotrop    = False
SIM.gun.multiplicity = 1
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
SIM.part.printEndTracking       = False
SIM.part.printStartTracking     = False
SIM.part.saveProcesses          = ['Decay']

SIM.physics.decays  = False
SIM.physics.list    = "FTFP_BERT"
SIM.physics.pdgfile = os.path.join(os.environ.get("DD4hepINSTALL"), "examples/DDG4/examples/particle.tbl")
SIM.physics.rangecut = 0.7*mm
SIM.physics.rejectPDGs = {1,2,3,4,5,6,21,23,24,25}

SIM.random.enableEventSeed = True
SIM.random.file            = None
SIM.random.luxury          = 1
