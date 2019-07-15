#!/bin/bash

outcsv=$1
outhtml=$2
rpath=$3
kpi=$4

caseslistFile="cases.list"
metrics_json=$kpi
pngOutDirRoot="results/case_"
caseDirRoot="results/case_"
outputsList4DE="mexdex/DEoutputParams.txt"

colorby="GISFC"

if [[ "$rpath" == *"/efs/job_working_directory"* ]];then
    basedir="$(echo /download$rpath | sed "s|/efs/job_working_directory||g" )"
    DEbase="/preview"
else
    # cloud 9 development
    #host=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    host="35.188.158.233"
    basedir="$(echo $rpath | sed 's|/core|http://'$host':8080/preview|g')"
    DEbase="http://$host:8080/preview/share"
fi

# Works with both python2 and python3 
python model/mexdex/writeDesignExplorerCsv.py \
	--casesList_paramValueDelimiter "," \
	--imagesDirectory $pngOutDirRoot{:d} \
	--includeOutputParamsFile $outputsList4DE \
	--MEXCsvPathTemplate "$caseDirRoot{:d}/metrics.txt" \
	$caseslistFile $metrics_json $basedir $outcsv

baseurl="$DEbase/DesignExplorer/index.html?datafile=$basedir/$outcsv&colorby=$colorby"
echo '<html style="overflow-y:hidden;background:white"><a style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px" href="'$baseurl'" target="_blank">Open in New Window</a><iframe width="100%" height="100%" src="'$baseurl'" frameborder="0"></iframe></html>' > $outhtml

