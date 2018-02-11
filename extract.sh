#!/bin/bash
#
# This script provides examples for running extract.py via pvpython. To get help on the arguments for
# running extract.py, run: 
#
#   ParaviewPath/bin/pvpython  extract.py -h
#
# USAGE:
# - CalculiX (exo file):
#    ./extract.sh /opt/paraview530/bin solve.exo beadOnPlateKPI.json example_outputs outputs/metrics.csv 
# - openFOAM:
#    ./extract.sh /opt/paraview530/bin elbow-test/system/controlDict elbowKPI.json outputs/  outputs/metrics.csv 0

#paraviewPath=$1
model_step_files=$1
resultsFile=$2
kpi_file_address=$3
pvOutputDir=$4
metrics_file=$5
pass_coordinates_file=$6

if [[ $# -lt 7 ]]; then
 	maxPasses2Run=-1
else
	maxPasses2Run=$7
fi 

tar -xf $resultsFile
tar -xf $model_step_files

xvfb-run -a --server-args="-screen 0 1024x768x24" $PARAVIEWPATH/pvpython  --mesa-llvm utils/mexdex/extract.py $kpi_file_address $pvOutputDir $metrics_file  --inp_file_path_template model_step{:d}.inp -n $maxPasses2Run  --pass_coordinates_file $pass_coordinates_file
