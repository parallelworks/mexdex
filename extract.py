from paraview.simple import *
import argparse

import pvutils
import metricsJsonUtils
import data_IO
import os

parser = argparse.ArgumentParser(
    description='Extract metrics from all the calculix output files.')

parser.add_argument("data_file_address",
                    help="The path to the data file to extract data from")
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

parser.add_argument("--convert_to_cell_data", dest='convert2cellData',
                    action='store_true',
                    help='If set, a filter will be applied to the data source to convert '
                    'the Cell Data variables to Point Data variables. This is needed if '
                    'the source data file uses the Cell Data structure (instead of Point '
                    'Data) - This conversion is not performed by default')
parser.set_defaults(convert2cellData=False)

args = parser.parse_args()
dataFileAddress = args.data_file_address
kpiFileAddress = args.kpi_file_address
outputDir = args.output_dir
outputDir = os.path.join(outputDir, '')
metricFile = args.metrics_file
caseNumber = args.case_number
convert2cellData = args.convert2cellData

image_settings = pvutils.ImageSettings()

# Read the desired outputs/metrics from the csv file:
kpihash = metricsJsonUtils.readKPIJsonFile(kpiFileAddress)[0]

# Set the default values for missing fields in the kpihash
for kpi in kpihash:
    kpihash[kpi] = metricsJsonUtils.setKPIFieldDefaults(kpihash[kpi], kpi)
print(kpihash)

# Read data file
fields2Read = pvutils.getfieldsfromkpihash(kpihash)
dataReader = pvutils.readDataFile(dataFileAddress, fields2Read, convert2cellData)

# Initialize renderView and display
renderView1, readerDisplay = pvutils.initRenderView(dataReader, image_settings)

print("Generating KPIs")

for kpi in kpihash:
    if not (kpihash[kpi]['field'] == 'None'):
        kpihash[kpi] = pvutils.correctfieldcomponent(dataReader, kpihash[kpi])

fp_csv_metrics = data_IO.open_file(metricFile, "w")
fp_csv_metrics.write(",".join(['metric','ave','min','max','sd','time'])+"\n")

#pw_filters = []
for kpi in kpihash:
    if not data_IO.str2bool(kpihash[kpi]['IsParaviewMetric']):
        continue
    metrichash = kpihash[kpi]
    kpitype = metrichash['type']
    kpiimage = metrichash['image']

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
    if extractStats:
        pvutils.extractStats(pw_filter, kpi, metrichash, fp_csv_metrics)

    if kpiimage != "None" and kpiimage != "plot":
        pvutils.save_images(outputDir, metrichash, image_settings.magnification,
                            renderView1, caseNumber)

    makeAnim = data_IO.str2bool(metrichash['animation'])
    if makeAnim:
        animationName = metrichash['animationName']
        if caseNumber:
            animationName = animationName.format(int(caseNumber))
        pvutils.makeAnimation(outputDir, kpi, image_settings.magnification, animationName)

    export2Blender = data_IO.str2bool(metrichash['blender'])
    if export2Blender:
        blenderContext=metrichash['blendercontext']
        renderBody=metrichash['blenderbody']
        pvutils.exportx3d(outputDir, kpi, pw_filter, dataReader, renderBody, blenderContext)

fp_csv_metrics.close()
