#!/bin/bash
# Pi0 two-photon separation scan — Camp 2b
#
# Shoots pi0 at 4 energies x 4 configs (baseline, 100um, 200um, 500um).
# Geant4 decays each pi0 -> gamma gamma. We then find two clusters
# in the SimHits to measure the minimum resolvable separation.
#
# Expected gamma-gamma separation at ECAL face (R=2150mm):
#   20 GeV  -> ~29 mm     50 GeV -> ~11.6 mm
#   100 GeV -> ~5.8 mm   200 GeV -> ~2.9 mm  (< 1 baseline cell)
#
# Run from inside the container at /srv/Camp2 with key4hep sourced:
#   cd /srv/Camp2
#   nohup bash run_pi0_scan.sh > Output/pi0scan/pi0_scan.log 2>&1 &

export CAMP2_DIR=/sdf/home/p/pbhattar/FCCee_home/FCCee/Camp2
echo "CWD: $(pwd)   CAMP2_DIR: $CAMP2_DIR"

N=500

# ── 20 GeV ──────────────────────────────────────────────────────────────────
PI0_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_pi0_baseline.py -N $N > Output/pi0scan/log_baseline_20GeV.txt  2>&1 && echo "done baseline 20GeV"  || echo "FAILED baseline 20GeV"
PI0_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_pi0_100um.py   -N $N > Output/pi0scan/log_100um_20GeV.txt    2>&1 && echo "done 100um   20GeV"  || echo "FAILED 100um   20GeV"
PI0_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_pi0_200um.py   -N $N > Output/pi0scan/log_200um_20GeV.txt    2>&1 && echo "done 200um   20GeV"  || echo "FAILED 200um   20GeV"
PI0_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_pi0_500um.py   -N $N > Output/pi0scan/log_500um_20GeV.txt    2>&1 && echo "done 500um   20GeV"  || echo "FAILED 500um   20GeV"

# ── 50 GeV ──────────────────────────────────────────────────────────────────
PI0_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_pi0_baseline.py -N $N > Output/pi0scan/log_baseline_50GeV.txt  2>&1 && echo "done baseline 50GeV"  || echo "FAILED baseline 50GeV"
PI0_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_pi0_100um.py   -N $N > Output/pi0scan/log_100um_50GeV.txt    2>&1 && echo "done 100um   50GeV"  || echo "FAILED 100um   50GeV"
PI0_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_pi0_200um.py   -N $N > Output/pi0scan/log_200um_50GeV.txt    2>&1 && echo "done 200um   50GeV"  || echo "FAILED 200um   50GeV"
PI0_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_pi0_500um.py   -N $N > Output/pi0scan/log_500um_50GeV.txt    2>&1 && echo "done 500um   50GeV"  || echo "FAILED 500um   50GeV"

# ── 100 GeV ─────────────────────────────────────────────────────────────────
PI0_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_pi0_baseline.py -N $N > Output/pi0scan/log_baseline_100GeV.txt  2>&1 && echo "done baseline 100GeV"  || echo "FAILED baseline 100GeV"
PI0_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_pi0_100um.py   -N $N > Output/pi0scan/log_100um_100GeV.txt    2>&1 && echo "done 100um   100GeV"  || echo "FAILED 100um   100GeV"
PI0_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_pi0_200um.py   -N $N > Output/pi0scan/log_200um_100GeV.txt    2>&1 && echo "done 200um   100GeV"  || echo "FAILED 200um   100GeV"
PI0_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_pi0_500um.py   -N $N > Output/pi0scan/log_500um_100GeV.txt    2>&1 && echo "done 500um   100GeV"  || echo "FAILED 500um   100GeV"

# ── 200 GeV ─────────────────────────────────────────────────────────────────
PI0_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_pi0_baseline.py -N $N > Output/pi0scan/log_baseline_200GeV.txt  2>&1 && echo "done baseline 200GeV"  || echo "FAILED baseline 200GeV"
PI0_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_pi0_100um.py   -N $N > Output/pi0scan/log_100um_200GeV.txt    2>&1 && echo "done 100um   200GeV"  || echo "FAILED 100um   200GeV"
PI0_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_pi0_200um.py   -N $N > Output/pi0scan/log_200um_200GeV.txt    2>&1 && echo "done 200um   200GeV"  || echo "FAILED 200um   200GeV"
PI0_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_pi0_500um.py   -N $N > Output/pi0scan/log_500um_200GeV.txt    2>&1 && echo "done 500um   200GeV"  || echo "FAILED 500um   200GeV"

echo "Pi0 scan complete."
