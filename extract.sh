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

paraviewPath=$1
resultsFile=$2
desiredMetricsFile=$3
pvOutputDir=$4
outputMetrics=$5

if [ $# -ge 6 ]
then
	caseNumber="--case_number $6"
else
	caseNumber=""
fi

conver2cellData=""
if [ $# -eq 7 ]
then
    if [ "$7" = true ] ; then
	convert2cellData="--convert_to_cell_data"
    fi
fi

xvfb-run -a --server-args="-screen 0 1024x768x24" $paraviewPath/pvpython  --mesa-llvm   extract.py  $resultsFile $desiredMetricsFile  $pvOutputDir $outputMetrics $caseNumber $convert2cellData 


