#!/bin/bash
# Camp 2: run ddsim with photon gun
# Usage:
#   ./run_sim.sh          -> 10 test events
#   ./run_sim.sh 1000     -> 1000 events

N=${1:-10}
#command -v setupalma9 &>/dev/null && setupalma9   # optional: only runs if available
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh

# BASH_SOURCE[0] works whether the script is run (./run_sim.sh) or sourced (source run_sim.sh)
export CAMP2_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CAMP2_DIR"

echo "=== Camp 2 ddsim ==="
echo "  Geometry : geometry/CLD_o2_v07_500um/CLD_o2_v07.xml"
echo "  Particle : gamma, 10 GeV, direction (1,0,0)"
echo "  Events   : $N"
echo "  Output   : photon_10GeV_500um_SIM.edm4hep.root"
echo "======================================"

ddsim --steeringFile steering_files/steer_photon_gun_500um.py -N "$N"
