#!/bin/bash
#=======================================
# This script will create the .html and
# .csv files read by Design Explorer to
# display the results of a parameter sweep.
#
# The .html file is basically a wrapper
# for launching Design Explorer.  The
# .csv file lists parameter values and
# names associated with the parameter
# sweep (i.e. the metadata) necessary
# for graphical display.
#
# A previous version treated $7, $8,
# and $9 as a series of optional inputs,
# but here I require them as it appears
# they are necessary.
#=======================================
# BASIC INPUTS
#
# $1 = the name of the OUTPUT .csv file
# $2 = the name of the OUTPUT .html file
# $3 = the user's working directory on
#      the PW system, which is then used
#      to build paths in the .html file.
# $4 = an explicit list of cases in the
#      parameter sweep with each line
#      being a list of param_name,param_value,...
# $5 = the kpi.json file that defines what
#      metrics and images are made by
#      the metrics extrator (MEX).
#=======================================
outcsv=$1
outhtml=$2
rpath=$3
caseslistFile=$4
metrics_json=$5

#=======================================
# MEXDEX CODE PATH
#
# $6 = the user can define the location
#      of the mexdex directory which is
#      where the metrics extractor and
#      Design Explorer code resides.
mexdexDir=$6

#======================================
# PATHS FOR DATA TO DISPLAY
#
# An integer, associated with the
# run count, is added to the end of
# the pngOutDirRoot ($7)
# and to caseDirRoot ($8) but not to
# outputsList4DE ($9).
pngOutDirRoot=$7
caseDirRoot=$8
metricsFileName=$9

# Frankly, I have no evidence that the
# path specified in the .json file actually
# makes its way into MEXDEX - it appears
# NOT to, so this option is actually REQUIRED
# if you have output in results/case_{:d}.
# This needs to be tracked down, documented,
# and cleaned up.  I also cannot find any
# evidence that outputsList4DE is used by
# MEXDEX.

#=======================================
# I don't know what this means yet.
colorby="stl"

# Print out all the options for running
# this script for debugging.
echo $@

#=======================================
# Set the base directory and design explorer
# base directories
#=======================================
if [[ "$rpath" == *"/efs/job_working_directory"* ]];then
	basedir="$(echo /download$rpath | sed "s|/efs/job_working_directory||g" )"
	DEbase="/preview"  
else
	basedir="$(echo /download$rpath | sed "s|/export/galaxy-central/database/job_working_directory||g" )"
	DEbase="/preview"  
fi 

#=======================================
# Generate the design explorer csv file:
#=======================================

# Works with both python2 and python3 
python   $mexdexDir/writeDesignExplorerCsv.py \
	 --casesList_paramValueDelimiter "," \
	 --imagesDirectory $pngOutDirRoot{:d} \
	 --MEXCsvPathTemplate  $caseDirRoot{:d}/$metricsFileName \
	 $caseslistFile $metrics_json $basedir/ $outcsv

#========================================
# Generate the design explorer html file:
#========================================
baseurl="$DEbase/DesignExplorer/index.html?datafile=$basedir/$outcsv&colorby=$colorby"
echo '<html style="overflow-y:hidden;background:white"><a style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px" href="'$baseurl'" target="_blank">Open in New Window</a><iframe width="100%" height="100%" src="'$baseurl'" frameborder="0"></iframe></html>' > $outhtml


