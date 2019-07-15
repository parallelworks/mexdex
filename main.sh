#!/bin/bash
kpi_file=$1
results_file=$2
mexdex_out_dir=$3
echo "Extracting metrics"
echo "Running mexdex in docker container"
run_command="docker run --rm  -i --user root -v `pwd`:/scratch -w /scratch docker.io/parallelworks/paraview:v5_4u_imgmagick_rootUser /bin/bash"
paraviewPath=/opt/ParaView-5.4.1-Qt5-OpenGL2-MPI-Linux-64bit/bin/
mkdir -p out
sudo $run_command mexdex/extract.sh ${paraviewPath} ${results_file} ${kpi_file} ${mexdex_out_dir} ${mexdex_out_dir}/dummy
