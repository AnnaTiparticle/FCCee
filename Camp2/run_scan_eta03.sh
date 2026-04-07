#!/bin/bash
# MAPS photon scan at eta=0.3 (direction 0.956, 0, 0.292).
# All pixel sizes: 25, 50, 100, 200, 500 um.
# Energies: 1, 5, 15, 20, 50, 100, 200 GeV — 1000 events each.
#
# Run from inside the container at Camp2 root with key4hep sourced:
#   nohup bash run_scan_eta03.sh > Output/scan_passiveSi_eta03/scan.log 2>&1 &

export CAMP2_DIR=/sdf/home/p/pbhattar/FCCee_home/FCCee/Camp2
echo "CWD: $(pwd)   CAMP2_DIR: $CAMP2_DIR"

N=1000

# --- 1 GeV ---
PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_baseline_eta03.py -N $N > Output/scan_passiveSi_eta03/log_baseline_1GeV.txt 2>&1 && echo "done baseline 1GeV"  || echo "FAILED baseline 1GeV"
PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_25um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_25um_1GeV.txt  2>&1 && echo "done 25um  1GeV"  || echo "FAILED 25um  1GeV"
PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_50um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_50um_1GeV.txt  2>&1 && echo "done 50um  1GeV"  || echo "FAILED 50um  1GeV"
PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_100um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_100um_1GeV.txt 2>&1 && echo "done 100um 1GeV"  || echo "FAILED 100um 1GeV"
PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_200um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_200um_1GeV.txt 2>&1 && echo "done 200um 1GeV"  || echo "FAILED 200um 1GeV"
PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_500um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_500um_1GeV.txt 2>&1 && echo "done 500um 1GeV"  || echo "FAILED 500um 1GeV"

# --- 5 GeV ---
PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_baseline_eta03.py -N $N > Output/scan_passiveSi_eta03/log_baseline_5GeV.txt 2>&1 && echo "done baseline 5GeV"  || echo "FAILED baseline 5GeV"
PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_25um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_25um_5GeV.txt  2>&1 && echo "done 25um  5GeV"  || echo "FAILED 25um  5GeV"
PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_50um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_50um_5GeV.txt  2>&1 && echo "done 50um  5GeV"  || echo "FAILED 50um  5GeV"
PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_100um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_100um_5GeV.txt 2>&1 && echo "done 100um 5GeV"  || echo "FAILED 100um 5GeV"
PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_200um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_200um_5GeV.txt 2>&1 && echo "done 200um 5GeV"  || echo "FAILED 200um 5GeV"
PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_500um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_500um_5GeV.txt 2>&1 && echo "done 500um 5GeV"  || echo "FAILED 500um 5GeV"

# --- 15 GeV ---
PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_baseline_eta03.py -N $N > Output/scan_passiveSi_eta03/log_baseline_15GeV.txt 2>&1 && echo "done baseline 15GeV" || echo "FAILED baseline 15GeV"
PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_25um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_25um_15GeV.txt  2>&1 && echo "done 25um  15GeV" || echo "FAILED 25um  15GeV"
PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_50um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_50um_15GeV.txt  2>&1 && echo "done 50um  15GeV" || echo "FAILED 50um  15GeV"
PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_100um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_100um_15GeV.txt 2>&1 && echo "done 100um 15GeV" || echo "FAILED 100um 15GeV"
PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_200um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_200um_15GeV.txt 2>&1 && echo "done 200um 15GeV" || echo "FAILED 200um 15GeV"
PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_500um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_500um_15GeV.txt 2>&1 && echo "done 500um 15GeV" || echo "FAILED 500um 15GeV"

# --- 20 GeV ---
PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_baseline_eta03.py -N $N > Output/scan_passiveSi_eta03/log_baseline_20GeV.txt 2>&1 && echo "done baseline 20GeV" || echo "FAILED baseline 20GeV"
PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_25um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_25um_20GeV.txt  2>&1 && echo "done 25um  20GeV" || echo "FAILED 25um  20GeV"
PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_50um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_50um_20GeV.txt  2>&1 && echo "done 50um  20GeV" || echo "FAILED 50um  20GeV"
PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_100um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_100um_20GeV.txt 2>&1 && echo "done 100um 20GeV" || echo "FAILED 100um 20GeV"
PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_200um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_200um_20GeV.txt 2>&1 && echo "done 200um 20GeV" || echo "FAILED 200um 20GeV"
PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_500um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_500um_20GeV.txt 2>&1 && echo "done 500um 20GeV" || echo "FAILED 500um 20GeV"

# --- 50 GeV ---
PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_baseline_eta03.py -N $N > Output/scan_passiveSi_eta03/log_baseline_50GeV.txt 2>&1 && echo "done baseline 50GeV" || echo "FAILED baseline 50GeV"
PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_25um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_25um_50GeV.txt  2>&1 && echo "done 25um  50GeV" || echo "FAILED 25um  50GeV"
PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_50um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_50um_50GeV.txt  2>&1 && echo "done 50um  50GeV" || echo "FAILED 50um  50GeV"
PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_100um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_100um_50GeV.txt 2>&1 && echo "done 100um 50GeV" || echo "FAILED 100um 50GeV"
PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_200um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_200um_50GeV.txt 2>&1 && echo "done 200um 50GeV" || echo "FAILED 200um 50GeV"
PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_500um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_500um_50GeV.txt 2>&1 && echo "done 500um 50GeV" || echo "FAILED 500um 50GeV"

# --- 100 GeV ---
PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_baseline_eta03.py -N $N > Output/scan_passiveSi_eta03/log_baseline_100GeV.txt 2>&1 && echo "done baseline 100GeV" || echo "FAILED baseline 100GeV"
PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_25um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_25um_100GeV.txt  2>&1 && echo "done 25um  100GeV" || echo "FAILED 25um  100GeV"
PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_50um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_50um_100GeV.txt  2>&1 && echo "done 50um  100GeV" || echo "FAILED 50um  100GeV"
PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_100um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_100um_100GeV.txt 2>&1 && echo "done 100um 100GeV" || echo "FAILED 100um 100GeV"
PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_200um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_200um_100GeV.txt 2>&1 && echo "done 200um 100GeV" || echo "FAILED 200um 100GeV"
PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_500um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_500um_100GeV.txt 2>&1 && echo "done 500um 100GeV" || echo "FAILED 500um 100GeV"

# --- 200 GeV ---
PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_baseline_eta03.py -N $N > Output/scan_passiveSi_eta03/log_baseline_200GeV.txt 2>&1 && echo "done baseline 200GeV" || echo "FAILED baseline 200GeV"
PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_25um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_25um_200GeV.txt  2>&1 && echo "done 25um  200GeV" || echo "FAILED 25um  200GeV"
PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_50um_eta03.py  -N $N > Output/scan_passiveSi_eta03/log_50um_200GeV.txt  2>&1 && echo "done 50um  200GeV" || echo "FAILED 50um  200GeV"
PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_100um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_100um_200GeV.txt 2>&1 && echo "done 100um 200GeV" || echo "FAILED 100um 200GeV"
PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_200um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_200um_200GeV.txt 2>&1 && echo "done 200um 200GeV" || echo "FAILED 200um 200GeV"
PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_500um_eta03.py -N $N > Output/scan_passiveSi_eta03/log_500um_200GeV.txt 2>&1 && echo "done 500um 200GeV" || echo "FAILED 500um 200GeV"

echo "All done."
