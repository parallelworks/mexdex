#!/bin/bash

outcsv=$1
outhtml=$2
rpath=$3
caseslistFile=$4
metrics_json=$5

if [ $# -lt 6 ]
then
	mexdexDir="."
else
	mexdexDir=$6
fi 

# For cases were png directory and case directory roots are not specified in the kpi.json file:
setRootDir=false
if [ $# -eq 9 ]
then
	pngOutDirRoot=$7
	caseDirRoot=$8   
	outputsList4DE=$9
	setRootDir=true
fi

colorby="stl"

echo $@

#
# Set the base directory and design explorer base directories
#
if [[ "$rpath" == *"/efs/job_working_directory"* ]];then
	basedir="$(echo /download$rpath | sed "s|/efs/job_working_directory||g" )"
	DEbase="/preview"  
else
	basedir="$(echo /download$rpath | sed "s|/export/galaxy-central/database/job_working_directory||g" )"
	DEbase="/preview"  
fi 

#
# Generate the design explorer csv file:
#
if [ "$setRootDir" = true ] ; then
	# If the root directories are provided as input to this script, set them when calling mexdex/writeDesignExplorerCsv.py 
	# Works with both python2 and python3 
	python   $mexdexDir/writeDesignExplorerCsv.py \
		--casesList_paramValueDelimiter "=" \
		--imagesDirectory $pngOutDirRoot{:d} \
		--includeOutputParamsFile $outputsList4DE \
		--MECsvPathTemplate  $caseDirRoot{:d}/metrics.csv \
		$caseslistFile $metrics_json $basedir $outcsv
else
	# Works with both python2 and python3 
	python  $mexdexDir/writeDesignExplorerCsv.py \
		--casesList_paramValueDelimiter  ":"   \
		$caseslistFile $metrics_json $basedir/ $outcsv
fi

#
# Generate the design explorer html file:
#
baseurl="$DEbase/DesignExplorer/index.html?datafile=$basedir/$outcsv&colorby=$colorby"
echo '<html style="overflow-y:hidden;background:white"><a style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px" href="'$baseurl'" target="_blank">Open in New Window</a><iframe width="100%" height="100%" src="'$baseurl'" frameborder="0"></iframe></html>' > $outhtml


