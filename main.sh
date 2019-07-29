#!/bin/bash
work_dir=`pwd`
# Import general bash workflow functions
# . in bash is nearly the same as "source"
. utils/general.sh
case_number=$1
metricsfile=$2
check_file_exists ${metricsfile}

# The input file in this case is the output
# file of the simulation.
inputfile=$3
check_file_exists ${inputfile}

# Output directory for Paraview
outdir=$4
kpifile=$5
check_file_exists ${kpifile}

# WARNING: Assumes all metrics go to same file!!
metricsfile_kpi=$(cat ${kpifile} | grep -Po '"resultFile":.*?[^\\]",' | cut -d'"' -f4 | uniq | sed "s/{:d}/${case_number}/g")
# Check that metrics file specified in kpifile is the same as metricsfile:
if [ ${metricsfile} != ${metricsfile_kpi} ]; then
    echo "ERROR: Check resultFile key value in ${kpifile}"
    exit 1
fi


echo "Running mexdex in docker container"
run_command="docker run --rm  -i --user root -v `pwd`:/scratch -w /scratch docker.io/parallelworks/paraview:v5_4u_imgmagick_rootUser /bin/bash"
paraviewPath=/opt/ParaView-5.4.1-Qt5-OpenGL2-MPI-Linux-64bit/bin/
sudo $run_command mexdex/extract.sh ${paraviewPath} ${inputfile} ${kpifile} ${outdir} ${outdir}/dummy
