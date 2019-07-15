#!/bin/bash
apps_dir=$(dirname $0)
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
if [ $# -eq 7 ]; then
    if [ "$7" = true ] ; then
	convert2cellData="--convert_to_cell_data"
    fi
fi
convert2cellData="--convert_to_cell_data"

xvfb-run -a --server-args="-screen 0 1024x768x24" $paraviewPath/pvpython  --mesa-llvm ${apps_dir}/extract.py  $resultsFile $desiredMetricsFile  $pvOutputDir $outputMetrics $caseNumber $convert2cellData 
