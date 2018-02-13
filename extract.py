from paraview.simple import *
import argparse
import copy
import numpy
import os

import pvutils
import metricsJsonUtils
import data_IO

import sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
ccx_utils_dir = os.path.join(parentdir, "calculix")
sys.path.insert(0,ccx_utils_dir) 
print sys.path

import calculix_utils

# import sys
# To run from Paraview Python Shell
# from mexdex import pvutils
# from mexdex import metricsJsonUtils
# import data_IO
# import calculix_utils
# print(sys.argv)

parser = argparse.ArgumentParser(
    description='Extract metrics from all the calculix output files.')

# parser.add_argument("data_file_dir",
#                     help="The directory of the data files for extracting data from")
parser.add_argument("kpi_file_address",
                    help="The json file that specifies what image(s)/data to extract")
parser.add_argument("output_dir",
                    help="The directory for writing the extracted image(s)")
parser.add_argument("metrics_file",
                    help="The path of the csv file for writing extracted statistics")

parser.add_argument("--case_number", default="",
                    help='A number that can be used for naming output image files. '
                    'For example, if image name in the kpi file set to '
                    '"domain{:d}.png", and case_number is set to 1, the output image name'
                    'would be "domain1.png - default: ""')

parser.add_argument("--convert_to_cell_data", dest='convert2cellData', action='store_true',
                    help='If set, a filter will be applied to the data source to convert '
                    'the Cell Data variables to Point Data variables. This is needed if '
                    'the source data file uses the Cell Data structure (instead of Point '
                    'Data) - This conversion is not performed by default')
parser.set_defaults(convert2cellData=False)

parser.add_argument("--inp_file_path_template", default="./model_pass{:d}.inp",
                    help='The template for CalculiX input file. "{:d}" will be replaced '
                    'with 1, 2, ..., n, where n is the number of input files - default: '
                         '"./model_pass{:d}.inp"')

parser.add_argument("-n", "--num_input_files", type=int, default=-1,
                    help='The number of input files. If not given, the number of input '
                    'files will be read from pass_coordinates.out')

parser.add_argument("--pass_coordinates_file", default= "./pass_coordinates.out",
                    help='The file containing the weld pass coordinates. If the number '
                    'of CalculiX input files are not provided, they will be determined '
                    'from this file - default:"./pass_coordinates.out"')

args = parser.parse_args()
# dataFileAddress = args.data_file_dir
kpiFileAddress = args.kpi_file_address
outputDir = args.output_dir
outputDir = os.path.join(outputDir, '')
metricFile = args.metrics_file
caseNumber = args.case_number
convert2cellData = args.convert2cellData
inp_file_path_template = args.inp_file_path_template
max_passes = args.num_input_files


pass_coor_file_path = args.pass_coordinates_file
weld_passes = calculix_utils.WeldPasses(pass_coor_file_path)
num_passes = weld_passes.num_passes
if max_passes != -1:
    num_passes = min(max_passes, num_passes)
print("Processing {:d} passes".format(num_passes))

# Make a list of CalculiX input files
ccx_inputs = []
for ipass in range(num_passes):
    inp_file_path = inp_file_path_template.format(ipass+1)
    ccx_inputs.append(inp_file_path)

# Make a list of CalculiX result files:
# #####
# Note: The result files are assumed to be in the same directory as the CalculiX input
# files
# ####
ccx_results = []
for i, ccx_input_file in enumerate(ccx_inputs):
    if i == 0:
        ccx_results_dir = os.path.dirname(ccx_input_file)
        ccx_results.append(os.path.join(ccx_results_dir, 'analysis.exo'))
    else:
        ccx_result_file = os.path.splitext(ccx_input_file)[0] + '.exo'
        ccx_results.append(ccx_result_file)
print(ccx_results)

# Read time periods of the welding steps from CalculiX input files
t_step = []
for ipass in range(num_passes):
    t_step.extend(calculix_utils.read_uncoupled_step_time_from_inp(ccx_inputs[ipass]))
t_step_total = numpy.cumsum(t_step)
t_step_total = t_step_total.tolist()

image_settings = pvutils.ImageSettings()

# Read the desired outputs/metrics from the csv file:
kpihash_main = metricsJsonUtils.readKPIJsonFile(kpiFileAddress)[0]

# Set the default values for missing fields in the kpihash_main
for kpi in kpihash_main:
    kpihash_main[kpi] = metricsJsonUtils.setKPIFieldDefaults(kpihash_main[kpi], kpi)
print(kpihash_main)

fields2Read = pvutils.getfieldsfromkpihash(kpihash_main)

fp_csv_metrics = data_IO.open_file(metricFile, "w")
fp_csv_metrics.write(",".join(['metric', 'ave', 'min', 'max', 'sd', 'time']) + "\n")

for ipass, dataFileAddress in enumerate(ccx_results):
    kpihash = copy.deepcopy(kpihash_main)

    # Fix the image names and animation names for multi-pass kpi's:
    for kpi in kpihash:
        if data_IO.str2bool(kpihash[kpi]['per-pass']):
            if 'imageName' in kpihash[kpi]:
                kpihash[kpi]['imageName'] = 'pass{}_'.format(ipass) + \
                                            kpihash[kpi]['imageName']
            if 'animationName' in kpihash[kpi]:
                kpihash[kpi]['animationName'] = 'pass{}_'.format(ipass) + \
                                            kpihash[kpi]['animationName']

    # Change the image time and extractStat time to the end time of the heating step
    for kpi in kpihash:
        if data_IO.str2bool(kpihash[kpi]['per-pass']):
            heating_end_time = t_step_total[ipass * 3 + 1]
            if 'imageTimes' in kpihash[kpi]:
                if kpihash[kpi]['imageTimes'] is not None:
                    kpihash[kpi]['imageTimes'] = kpihash[kpi]['imageTimes'].format(
                        heating_end_time)
            if data_IO.str2bool(kpihash[kpi]['extractStats']):
                kpihash[kpi]['extractStatsTimes'] = str(heating_end_time)


    # Read data file
    dataReader = pvutils.readDataFile(dataFileAddress, fields2Read, convert2cellData)

    # Initialize renderView and display
    renderView1, readerDisplay = pvutils.initRenderView(dataReader, image_settings)

    print("Generating KPIs: "+" pass {}".format(ipass))

    for kpi in kpihash:
        if not (kpihash[kpi]['field'] == 'None'):
            kpihash[kpi] = pvutils.correctfieldcomponent(dataReader, kpihash[kpi])

    for kpi in kpihash:
        if not data_IO.str2bool(kpihash[kpi]['IsParaviewMetric']):
            continue

        metrichash = kpihash[kpi]
        kpitype = metrichash['type']
        kpiimage = metrichash['image']

        # Add a new key to metrichash to keep track of the frame numbers for multi-pass
        # data:
        if 'num_written_frames' not in kpihash_main[kpi] or data_IO.str2bool(
                metrichash['per-pass']):
            kpihash_main[kpi]['num_written_frames'] = 0

        HideAll()
        Show(dataReader, renderView1)
        if kpiimage != "None" and kpiimage != "plot":
            pvutils.adjustCamera(kpiimage, renderView1, metrichash)

        print(kpi)

        ave = []
        if kpitype == "Slice":
            pw_filter = pvutils.createSlice(metrichash, dataReader, readerDisplay)
        elif kpitype == "WarpByVector":
            pw_filter = pvutils.createWarpbyVector(metrichash, dataReader, readerDisplay)
        elif kpitype == "Clip":
            pw_filter = pvutils.createClip(metrichash, dataReader, readerDisplay)
        elif kpitype == "Probe":
            pw_filter = pvutils.createProbe(metrichash, dataReader)
        elif kpitype == "Line":
            pw_filter = pvutils.createLine(metrichash, dataReader, outputDir, caseNumber)
        elif kpitype == "StreamLines":
            pw_filter = pvutils.createStreamTracer(metrichash, dataReader, readerDisplay)
        elif kpitype == "Volume":
            pw_filter = pvutils.createVolume(metrichash, dataReader, readerDisplay)
        elif kpitype == "Basic":
            pw_filter = pvutils.createBasic(metrichash, dataReader, readerDisplay)
        elif kpitype == "FindData":
            pw_filter = pvutils.createFindData(metrichash, dataReader, readerDisplay)

        if data_IO.str2bool(metrichash['temporalStats']):
            pw_filter = pvutils.statsOverTime(metrichash, pw_filter, readerDisplay)

        extractStats = data_IO.str2bool(metrichash['extractStats'])

        if data_IO.str2bool(metrichash['per-pass']):
            stat_tag = kpi + '_pass{}'.format(ipass)
        else:
            stat_tag = kpi

        if extractStats:
            pvutils.extractStats(pw_filter, stat_tag, metrichash, fp_csv_metrics)

        if kpiimage != "None" and kpiimage != "plot":
            append_csv = not(data_IO.str2bool(metrichash['per-pass'])) and (ipass>0)
            _, image_numbers = pvutils.save_images(outputDir, metrichash,
                                                   image_settings.magnification,
                                                   renderView1, caseNumber,
                                                   kpihash_main[kpi]['num_written_frames'],
                                                   append_csv)
            if not data_IO.str2bool(metrichash['per-pass']):
                kpihash_main[kpi]['num_written_frames'] = \
                    kpihash_main[kpi]['num_written_frames'] + len(image_numbers)

        if data_IO.str2bool(metrichash['animation']):
            if data_IO.str2bool(kpihash[kpi]['per-pass']):
                pvutils.makeAnimation(outputDir, kpi, image_settings.magnification,
                                      metrichash['animationName'], 
                                      case_number=caseNumber)
            else:
                if ipass == (len(ccx_results) - 1):
                    frames_dir = os.path.dirname(os.path.join(outputDir,
                                                               metrichash["imageName"]))
                    image_base_name = os.path.basename(
                        metrichash["imageName"]).format("%d") + '[0-' + \
                        str(kpihash_main[kpi]['num_written_frames'] - 1) + ']'
                    pvutils.make_anim_from_frames(
                        frames_dir, image_base_name,
                        os.path.join(outputDir, metrichash['animationName']))

        export2Blender = data_IO.str2bool(metrichash['blender'])
        if export2Blender:
            blenderContext=metrichash['blendercontext']
            renderBody=metrichash['blenderbody']
            pvutils.exportx3d(outputDir, kpi, pw_filter, dataReader, renderBody,
                              blenderContext)

        # Remove the pw_filter
        if kpitype != 'Basic':
            Delete(pw_filter)
            del pw_filter

    Delete(dataReader)
    del dataReader

fp_csv_metrics.close()
