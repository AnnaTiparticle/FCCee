#!/bin/bash
# Run ddsim photon gun scan over energies and MAPS pixel sizes.
# Outputs go into Camp2/scan/
#
# Usage:
#   nohup bash run_energy_scan.sh 1000 > Output/scan/scan.log 2>&1 &   (full run)
#   source run_energy_scan.sh 50                                 (quick test)

N=${1:-1000}
ENERGIES=(1 5 15 20 50 100 200)
MAPS_SIZES=(25 50 100 200)   # um

# key4hep must already be sourced in your shell before running this script.
# Do NOT source it here — re-sourcing bloats the environment past kernel limits.
echo "================================================"
echo "  Camp 2 full energy + pixel-size scan"
echo "  Energies   : ${ENERGIES[*]} GeV"
echo "  MAPS sizes : ${MAPS_SIZES[*]} um"
echo "  Events     : $N per point"
echo "  Output     : scan/"
echo "================================================"

# --- create MAPS geometries if not already done ---
python setup_maps_geometries.py

FAILED=()
TOTAL=$(( (${#MAPS_SIZES[@]} + 1) * ${#ENERGIES[@]} ))
COUNT=0

for E in "${ENERGIES[@]}"; do

    echo ""
    echo ">>> E = ${E} GeV <<<"

    # baseline
    OUTFILE="/sdf/home/p/pbhattar/FCCee_home/Camp2/scan_PassiveSi/photon_${E}GeV_baseline_SIM.edm4hep.root"
    COUNT=$((COUNT + 1))
    if [ -f "$OUTFILE" ]; then
        echo "  [$COUNT/$TOTAL] baseline: exists, skipping"
    else
        echo "  [$COUNT/$TOTAL] baseline: running..."
        PHOTON_ENERGY_GEV=$E ddsim --steeringFile steering_files/steer_photon_gun_baseline.py -N "$N" \
            > "scan/log_baseline_${E}GeV.txt" 2>&1
        if [ $? -ne 0 ]; then
            echo "  FAILED — see scan/log_baseline_${E}GeV.txt"
            FAILED+=("baseline_${E}GeV")
        else
            echo "  done -> $OUTFILE"
        fi
    fi

    # MAPS sizes
    for SIZE in "${MAPS_SIZES[@]}"; do
        OUTFILE="/sdf/home/p/pbhattar/FCCee_home/Camp2/scan/photon_${E}GeV_${SIZE}um_SIM.edm4hep.root"
        COUNT=$((COUNT + 1))
        if [ -f "$OUTFILE" ]; then
            echo "  [$COUNT/$TOTAL] ${SIZE}um: exists, skipping"
        else
            echo "  [$COUNT/$TOTAL] ${SIZE}um: running..."
            PHOTON_ENERGY_GEV=$E MAPS_CELL_UM=$SIZE \
                ddsim --steeringFile steering_files/steer_photon_gun_maps.py -N "$N" \
                > "scan/log_${SIZE}um_${E}GeV.txt" 2>&1
            if [ $? -ne 0 ]; then
                echo "  FAILED — see scan/log_${SIZE}um_${E}GeV.txt"
                FAILED+=("${SIZE}um_${E}GeV")
            else
                echo "  done -> $OUTFILE"
            fi
        fi
    done

done

echo ""
echo "================================================"
echo "  Scan complete.  ($((COUNT)) jobs)"
if [ ${#FAILED[@]} -gt 0 ]; then
    echo "  FAILED: ${FAILED[*]}"
else
    echo "  All jobs succeeded."
fi
echo "  Next: python fit_resolution_curve.py"
echo "================================================"
