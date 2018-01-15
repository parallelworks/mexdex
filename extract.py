from paraview.simple import *
import json
import sys
import pvutils
import metricsJsonUtils
import data_IO
import os

print(sys.argv)
if len(sys.argv) < 5:
    print("Number of provided arguments: ", len(sys.argv) - 1)
    print("Usage: pvpython extract.py  <dataFile>  <desiredMetrics.json> <outputDir> "
          "<outputMetrics.csv> [caseNumber]  [cellData]")
    sys.exit()


dataFileAddress = sys.argv[1]
kpiFileAddress = sys.argv[2]
outputDir = sys.argv[3]
outputDir = os.path.join(outputDir, '')
metricFile = sys.argv[4]
caseNumber = data_IO.setOptionalSysArgs(sys.argv, "", 5)
convert2cellData = data_IO.str2bool(data_IO.setOptionalSysArgs(sys.argv, "False", 6))

# Image settings:
magnification, viewSize, backgroundColor = pvutils.setImageProps()

# Read the desired outputs/metrics from the csv file:
kpihash = metricsJsonUtils.readKPIJsonFile(kpiFileAddress)[0]

print(kpihash)

# disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# Read data file
fields2Read = pvutils.getfieldsfromkpihash(kpihash)
dataReader = pvutils.readDataFile(dataFileAddress, fields2Read, convert2cellData)

# Initialize renderView and display
renderView1, readerDisplay = pvutils.initRenderView(dataReader, viewSize,
                                                    backgroundColor)

print("Generating KPIs")

# Set the default values for missing fields in the kpihash
for kpi in kpihash:
    kpihash[kpi] = metricsJsonUtils.setKPIFieldDefaults(kpihash[kpi], kpi)
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
        if not (os.path.exists(outputDir)):
            if outputDir:
                os.makedirs(outputDir)
        if caseNumber:
            metrichash['imageName'] = metrichash['imageName'].format(int(caseNumber))
        SaveScreenshot(outputDir + metrichash['imageName'],
                       magnification=magnification, quality=100)

    makeAnim = data_IO.str2bool(metrichash['animation'])
    if makeAnim:
        animationName = metrichash['animationName']
        if caseNumber:
            animationName = animationName.format(int(caseNumber))

        pvutils.makeAnimation(outputDir, kpi, magnification, animationName)

    export2Blender = data_IO.str2bool(metrichash['blender'])
    if export2Blender:
        blenderContext=metrichash['blendercontext']
        renderBody=metrichash['blenderbody']
        pvutils.exportx3d(outputDir, kpi, pw_filter, dataReader, renderBody, blenderContext)

fp_csv_metrics.close()
