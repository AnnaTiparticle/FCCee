#!/bin/bash
# Flat scan — one ddsim command per (size, energy) point.
# Run from inside the container at /srv/Camp2 with key4hep sourced:
#   cd /srv/Camp2
#   nohup bash run_scan_flat.sh > Output/scan_passiveSi/scan_flat.log 2>&1 &

export CAMP2_DIR=/sdf/home/p/pbhattar/FCCee_home/FCCee/Camp2
echo "CWD: $(pwd)   CAMP2_DIR: $CAMP2_DIR"

N=1000

# --- 1 GeV ---
# PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_25um.py  -N $N > Output/scan_passiveSi/log_25um_1GeV.txt  2>&1 && echo "done 25um  1GeV"  || echo "FAILED 25um  1GeV"
# PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_50um.py  -N $N > Output/scan_passiveSi/log_50um_1GeV.txt  2>&1 && echo "done 50um  1GeV"  || echo "FAILED 50um  1GeV"
# PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_100um.py -N $N > Output/scan_passiveSi/log_100um_1GeV.txt 2>&1 && echo "done 100um 1GeV"  || echo "FAILED 100um 1GeV"
# PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_200um.py -N $N > Output/scan_passiveSi/log_200um_1GeV.txt 2>&1 && echo "done 200um 1GeV"  || echo "FAILED 200um 1GeV"
#PHOTON_ENERGY_GEV=1 ddsim --steeringFile steering_files/steer_photon_gun_500um.py -N $N > Output/scan_passiveSi500/log_500um_1GeV.txt 2>&1 && echo "done 500um 1GeV"  || echo "FAILED 500um 1GeV"

# --- 5 GeV ---
# PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_25um.py  -N $N > Output/scan_passiveSi/log_25um_5GeV.txt  2>&1 && echo "done 25um  5GeV"  || echo "FAILED 25um  5GeV"
# PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_50um.py  -N $N > Output/scan_passiveSi/log_50um_5GeV.txt  2>&1 && echo "done 50um  5GeV"  || echo "FAILED 50um  5GeV"
# PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_100um.py -N $N > Output/scan_passiveSi/log_100um_5GeV.txt 2>&1 && echo "done 100um 5GeV"  || echo "FAILED 100um 5GeV"
# PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_200um.py -N $N > Output/scan_passiveSi/log_200um_5GeV.txt 2>&1 && echo "done 200um 5GeV"  || echo "FAILED 200um 5GeV"
#PHOTON_ENERGY_GEV=5 ddsim --steeringFile steering_files/steer_photon_gun_500um.py -N $N > Output/scan_passiveSi500/log_500um_5GeV.txt 2>&1 && echo "done 500um 5GeV"  || echo "FAILED 500um 5GeV"

# # --- 15 GeV ---
# PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_25um.py  -N $N > Output/scan_passiveSi/log_25um_15GeV.txt  2>&1 && echo "done 25um  15GeV" || echo "FAILED 25um  15GeV"
# PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_50um.py  -N $N > Output/scan_passiveSi/log_50um_15GeV.txt  2>&1 && echo "done 50um  15GeV" || echo "FAILED 50um  15GeV"
# PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_100um.py -N $N > Output/scan_passiveSi/log_100um_15GeV.txt 2>&1 && echo "done 100um 15GeV" || echo "FAILED 100um 15GeV"
# PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_200um.py -N $N > Output/scan_passiveSi/log_200um_15GeV.txt 2>&1 && echo "done 200um 15GeV" || echo "FAILED 200um 15GeV"
#PHOTON_ENERGY_GEV=15 ddsim --steeringFile steering_files/steer_photon_gun_500um.py -N $N > Output/scan_passiveSi500/log_500um_15GeV.txt 2>&1 && echo "done 500um 15GeV" || echo "FAILED 500um 15GeV"

# --- 20 GeV ---
# PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_25um.py  -N $N > Output/scan_passiveSi/log_25um_20GeV.txt  2>&1 && echo "done 25um  20GeV" || echo "FAILED 25um  20GeV"
# PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_50um.py  -N $N > Output/scan_passiveSi/log_50um_20GeV.txt  2>&1 && echo "done 50um  20GeV" || echo "FAILED 50um  20GeV"
# PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_100um.py -N $N > Output/scan_passiveSi/log_100um_20GeV.txt 2>&1 && echo "done 100um 20GeV" || echo "FAILED 100um 20GeV"
# PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_200um.py -N $N > Output/scan_passiveSi/log_200um_20GeV.txt 2>&1 && echo "done 200um 20GeV" || echo "FAILED 200um 20GeV"
#PHOTON_ENERGY_GEV=20 ddsim --steeringFile steering_files/steer_photon_gun_500um.py -N $N > Output/scan_passiveSi500/log_500um_20GeV.txt 2>&1 && echo "done 500um 20GeV" || echo "FAILED 500um 20GeV"

# --- 50 GeV ---
# PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_25um.py  -N $N > Output/scan_passiveSi/log_25um_50GeV.txt  2>&1 && echo "done 25um  50GeV" || echo "FAILED 25um  50GeV"
# PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_50um.py  -N $N > Output/scan_passiveSi/log_50um_50GeV.txt  2>&1 && echo "done 50um  50GeV" || echo "FAILED 50um  50GeV"
# PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_100um.py -N $N > Output/scan_passiveSi/log_100um_50GeV.txt 2>&1 && echo "done 100um 50GeV" || echo "FAILED 100um 50GeV"
# PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_200um.py -N $N > Output/scan_passiveSi/log_200um_50GeV.txt 2>&1 && echo "done 200um 50GeV" || echo "FAILED 200um 50GeV"
#PHOTON_ENERGY_GEV=50 ddsim --steeringFile steering_files/steer_photon_gun_500um.py -N $N > Output/scan_passiveSi500/log_500um_50GeV.txt 2>&1 && echo "done 500um 50GeV" || echo "FAILED 500um 50GeV"

# --- 100 GeV ---
# PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_25um.py  -N $N > Output/scan_passiveSi/log_25um_100GeV.txt  2>&1 && echo "done 25um  100GeV" || echo "FAILED 25um  100GeV"
# PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_50um.py  -N $N > Output/scan_passiveSi/log_50um_100GeV.txt  2>&1 && echo "done 50um  100GeV" || echo "FAILED 50um  100GeV"
# PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_100um.py -N $N > Output/scan_passiveSi/log_100um_100GeV.txt 2>&1 && echo "done 100um 100GeV" || echo "FAILED 100um 100GeV"
# PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_200um.py -N $N > Output/scan_passiveSi/log_200um_100GeV.txt 2>&1 && echo "done 200um 100GeV" || echo "FAILED 200um 100GeV"
PHOTON_ENERGY_GEV=100 ddsim --steeringFile steering_files/steer_photon_gun_500um.py -N $N > Output/scan_passiveSi500/log_500um_100GeV.txt 2>&1 && echo "done 500um 100GeV" || echo "FAILED 500um 100GeV"

# --- 200 GeV ---
# PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_25um.py  -N $N > Output/scan_passiveSi/log_25um_200GeV.txt  2>&1 && echo "done 25um  200GeV" || echo "FAILED 25um  200GeV"
# PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_50um.py  -N $N > Output/scan_passiveSi/log_50um_200GeV.txt  2>&1 && echo "done 50um  200GeV" || echo "FAILED 50um  200GeV"
# PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_100um.py -N $N > Output/scan_passiveSi/log_100um_200GeV.txt 2>&1 && echo "done 100um 200GeV" || echo "FAILED 100um 200GeV"
# PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_200um.py -N $N > Output/scan_passiveSi/log_200um_200GeV.txt 2>&1 && echo "done 200um 200GeV" || echo "FAILED 200um 200GeV"
#PHOTON_ENERGY_GEV=200 ddsim --steeringFile steering_files/steer_photon_gun_500um.py -N $N > Output/scan_passiveSi500/log_500um_200GeV.txt 2>&1 && echo "done 500um 200GeV" || echo "FAILED 500um 200GeV"

echo "All done."
