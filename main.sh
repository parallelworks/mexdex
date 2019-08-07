#!/bin/bash
work_dir=`pwd`
# Import general bash workflow functions
# . in bash is nearly the same as "source"
# This line will work as long as the utils
# directory is passed as a mapped list of
# files to the SWIFT app that calls this
# script.
. utils/general.sh
case_number=$1
metricsfile=$2
# DO NOT CHECK WHETHER THE METRICS FILE
# exists or not because it can be generated
# automatically below.
#check_file_exists ${metricsfile}

# The input file in this case is the output
# file of the simulation.
inputfile=$3
check_file_exists ${inputfile}

# Output directory for Paraview
outdir=$4

# File that defines all the values to extract
# is normally called kpi.json.
kpifile=$5
check_file_exists ${kpifile}

#=======================================
# OPTIONAL INPUTS
#
# $6 = the user can define the location
#      of the mexdex directory which is
#      where the metrics extractor and
#      Design Explorer code resides.
#      This is the same approach as in
#      postProcess.sh.
if [ $# -lt 6 ]
then
	mexdexDir="."
else
	mexdexDir=$6
fi 

#================================
# Check that the name of the metricsfile
# is listed in the kpi file.  This
# line will search for any resultFile naming
# lines in the kpi.json and verify that
# this name is present in an existing
# metrics file.  If there is no metrics
# file listed in the kpi file and if
# that file is not already present,
# then everything crashes.
#
# WARNING: Assumes all metrics go to same file!!
# In particular, this check assumes that there
# is only one file that is specified by the
# "resultFile" entries in the whole kpi.json.
# This is extremely limiting.
#
# (I don't know if this WARNING is strictly
# true, but it is correct that there are
# many assumptions at play here.)  Frankly,
# I don't see the value of this check and
# would opt to delete it completely.  It crashes
# the workflow if a given metrics file does
# not already exist.  If it were not to exist,
# it would be created automatically by extract.py
# (which is wrapped in extract.sh).
#metricsfile_kpi=$(cat ${kpifile} | grep -Po '"resultFile":.*?[^\\]",' | cut -d'"' -f4 | uniq | sed "s/{:d}/${case_number}/g")
# Check that metrics file specified in kpifile is the same as metricsfile:
#if [ ${metricsfile} != ${metricsfile_kpi} ]; then
#    echo "ERROR: Check resultFile key value in ${kpifile}"
#    exit 1
#fi

# Also, as far as I can tell, MEXDEX's extract.py
# and called subroutines do not provide the functionality
# as stated in the documentation that the metrics
# requested will be written to a particular file.
# Instead, as far as I can tell, MEXDEX simply
# dumps all metrics to the file name specified here.
# So, the best possible course of action is to
# rejig MEXDEX so that it creates output files
# associated with the kpi fields as is in the docs.
# The next best course of action would be to specify
# the output file as given in the kpi.json file.
# However, this would not deal with a variable-by-variable
# split of metrics, as implied is possible in
# MEXDEX.  So, I go the third route which is to
# manually specify the filename based on the
# input parameters of this script.

echo "Running mexdex in docker container"
run_command="docker run --rm  -i --user root -v `pwd`:/scratch -w /scratch docker.io/parallelworks/paraview:v5_4u_imgmagick_rootUser /bin/bash"
paraviewPath=/opt/ParaView-5.4.1-Qt5-OpenGL2-MPI-Linux-64bit/bin/

# Older line where the metrics file definition is
# replaced with dummy.
#sudo $run_command $mexdexDir/extract.sh ${paraviewPath} ${inputfile} ${kpifile} ${outdir} ${outdir}/dummy ${case_number} true

# Newer line where metrics file is automatically created.
sudo $run_command $mexdexDir/extract.sh ${paraviewPath} ${inputfile} ${kpifile} ${outdir} ${metricsfile} ${case_number} true
