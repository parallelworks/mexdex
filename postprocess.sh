#!/bin/bash

outcsv=$1
outhtml=$2
rpath=$3


caseslistFile="cases.list"
desiredMetricsFile="mexdex/kpi.json"
pngOutDirRoot="results/case_"
metricsFilesNameTemplate="results/metrics/case_@@i@@.csv"
outputs4DE="mexdex/DEoutputParams.txt"
extractedFileName=".csv"

colorby="stl"

echo $@

# this should be the main run path
#if [ -d "/core/matthew" ];then

basedir="$(echo $rpath | sed 's|/core||g')"
DEbase="/share"

#elif [[ "$rpath" == *"/efs/job_working_directory"* ]];then
#    # adjust this for pw download path
#    basedir="$(echo /download$rpath | sed "s|/efs/job_working_directory||g" )"
#    DEbase="/preview"
#else
#    basedir="$rpath"
#    DEbase="/"
#fi

# Works with both python2 and python3 
python mexdex/writeDesignExplorerCsv.py $caseslistFile $desiredMetricsFile $basedir output.csv $pngOutDirRoot $metricsFilesNameTemplate $outputs4DE 
mv output.csv $outcsv

baseurl="$DEbase/DesignExplorer/index.html?datafile=$basedir/$outcsv&colorby=$colorby"
echo '<html style="overflow-y:hidden;background:white"><a style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px" href="'$baseurl'" target="_blank">Open in New Window</a><iframe width="100%" height="100%" src="'$baseurl'" frameborder="0"></iframe></html>' > $outhtml

