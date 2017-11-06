#!/bin/bash

outcsv=$1
outhtml=$2
rpath=$3

caseslistFile=$4
metrics_json=$5
pngOutDirRoot=$6
caseDirRoot=$7

colorby="ClipUy"

echo $@

if [[ "$rpath" == *"/efs/job_working_directory"* ]];then
	basedir="$(echo /download$rpath | sed "s|/efs/job_working_directory||g" )"
	DEbase="/preview"  
else
	basedir="$(echo /download$rpath | sed "s|/export/galaxy-central/database/job_working_directory||g" )"
	DEbase="/preview"  
fi 

# Works with both python2 and python3 
python      mexdex/writeDesignExplorerCsv.py \
	--casesList_paramValueDelimiter "=" \
	--imagesDirectory $pngOutDirRoot{:d} \
	--MEXCsvPathTemplate  $caseDirRoot{:d}/metrics.csv \
	$caseslistFile $metrics_json $basedir $outcsv


baseurl="$DEbase/DesignExplorer/index.html?datafile=$basedir/$outcsv&colorby=$colorby"
echo '<html style="overflow-y:hidden;background:white"><a style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px" href="'$baseurl'" target="_blank">Open in New Window</a><iframe width="100%" height="100%" src="'$baseurl'" frameborder="0"></iframe></html>' > $outhtml


