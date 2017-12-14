#!/bin/bash

# USAGE:
# - CalculiX (exo file):
#    ./extract.sh /opt/paraview530/bin solve.exo beadOnPlateKPI.json example_outputs outputs/metrics.csv 
# - openFOAM:
#    ./extract.sh /opt/paraview530/bin elbow-test/system/controlDict elbowKPI.json outputs/  outputs/metrics.csv 

paraviewPath=$1
resultsFile=$2
desiredMetricsFile=$3
pvOutputDir=$4
outputMetrics=$5
caseNumber=$6

if [ $# -eq 7 ]
then
	isCellData=$7
else
	isCellData=""
fi

xvfb-run -a --server-args="-screen 0 1024x768x24" $paraviewPath/pvpython  --mesa-llvm   extract.py  $resultsFile $desiredMetricsFile  $pvOutputDir $outputMetrics $caseNumber $isCellData


