#!/bin/bash 
sweepParams=$1
casesListFile=$2
simFilesDir=$3
caseParamFileRootName=$4

python mexdex/prepinputs.py   $sweepParams $casesListFile 

python "mexdex/writeSimParamFiles.py" $casesListFile $simFilesDir $caseParamFileRootName
