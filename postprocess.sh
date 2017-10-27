#!/bin/bash

outcsv=$1
outhtml=$2
rpath=$3

echo "rpath is: " $rpath

caseslistFile="cases.list"
desiredMetricsFile="models/mexdex/kpi.json"

colorby="avg_fluid_T"

echo $@

if [[ "$rpath" == *"/efs/job_working_directory"* ]];then
	basedir="$(echo /download$rpath | sed "s|/efs/job_working_directory||g" )"
	DEbase="/preview"  
else
	basedir="$(echo /download$rpath | sed "s|/export/galaxy-central/database/job_working_directory||g" )"
	DEbase="/preview"  
fi 


# if [[ "$rpath" == *"/efs/job_working_directory"* ]];then
#     basedir="$(echo /download$rpath | sed "s|/efs/job_working_directory||g" )"
#     DEbase="/preview"
# else
#     # cloud 9 development
#     host=$(wget -O - -q http://169.254.169.254/latest/meta-data/public-ipv4)
#     #host="dev.parallel.works"
#     basedir="$(echo $rpath | sed 's|/core|http://'$host':8080/preview|g')"
#     DEbase="http://$host:8080/preview/share"
# fi

echo "basedir is:" $basedir

# Works with both python2 and python3 
python  models/mexdex/writeDesignExplorerCsv.py \
        --casesList_paramValueDelimiter ","   \
	--imagesDirectory "results/case_{:d}/openfoam/png" \
	$caseslistFile $desiredMetricsFile  $basedir output.csv
mv output.csv $outcsv

baseurl="$DEbase/DesignExplorer/index.html?datafile=$basedir/$outcsv&colorby=$colorby"
echo '<html style="overflow-y:hidden;background:white"><a style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px" href="'$baseurl'" target="_blank">Open in New Window</a><iframe width="100%" height="100%" src="'$baseurl'" frameborder="0"></iframe></html>' > $outhtml
