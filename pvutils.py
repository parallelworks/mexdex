from paraview.simple import *
import sys
import data_IO
import os
import subprocess
import shutil
import csv
import re
import numpy as np

# For saving plots as pngs
import matplotlib

import numpy as np
import warnings

def getParaviewVersion():
    """ Return paraview version as a double number: e.g. 5.4"""
    PVversionMajor = paraview.servermanager.vtkSMProxyManager.GetVersionMajor() 
    PVversionMinor = paraview.servermanager.vtkSMProxyManager.GetVersionMinor()
    PVversion = PVversionMajor + PVversionMinor/100.0
    return PVversion


def planeNormalFromName(planeName):
    if planeName.lower() == "x":
        normal = [1.0, 0.0, 0.0]
    if planeName.lower() == "y":
        normal = [0.0, 1.0, 0.0]
    if planeName.lower() == "z":
        normal = [0.0, 0.0, 1.0]
    return normal


def setviewposition(position_key, camera):
    center = position_key.split()
    nPoints = len(center)/3
    positionXYZ = []
    for iPoint in range(nPoints):
        positionXYZ.extend(list(camera.GetFocalPoint()))
        for i in range(iPoint*3, 3+iPoint*3):
            if center[i] != "center":
                positionXYZ[i] = float(center[i])
    return positionXYZ


def read_csv(f):
    kpihash = {}
    cols = [l.replace("\n", "") for l in f.readline().split(",")]
    for i, line in enumerate(f):
        data = [l.replace("\n", "") for l in line.split(",")]
        kpihash[data[0]] = {}
        for ii, v in enumerate(data):
            if ii != 0:
                kpihash[data[0]][cols[ii]] = v
    return kpihash


def getfieldsfromkpihash(kpihash):
    cellsarrays = []
    for kpi in kpihash:
        if 'field' in kpihash[kpi]:
            cellsarrays.append(kpihash[kpi]['field'])
        if 'colorByField' in kpihash[kpi]:
            cellsarrays.append(kpihash[kpi]['colorByField'])

    ca = set(cellsarrays)
    cellsarrays = list(ca)
    return cellsarrays


def isfldScalar(arrayInfo):
    numComps = arrayInfo.GetNumberOfComponents()
    if numComps == 1:
        return True
    else:
        return False


def getfldComponentMap(arrayInfo):
    compName2num = {}
    numComps = arrayInfo.GetNumberOfComponents()
    if numComps>1:
        for iComp in range(-1,numComps):
            compName2num[arrayInfo.GetComponentName(iComp)] = iComp
    return compName2num


def getfldCompNumber(arrayInfo, kpiComp):
    compNumberMap = getfldComponentMap(arrayInfo)
    if not kpiComp:
        compNum = 0
    else:
        compNum = compNumberMap[kpiComp]
    return compNum


def getdatarange(datasource, kpifld, kpifldcomp):
    arrayInfo = datasource.PointData[kpifld]
    compNumber = getfldCompNumber(arrayInfo, kpifldcomp)
    datarange = arrayInfo.GetRange(compNumber)
    return datarange


def extractStatsOld(d, kpi, kpifield, kpiComp, kpitype, fp_csv_metrics, ave=[]):
    datarange = getdatarange(d, kpifield, kpiComp)
    if kpitype == "Probe":
        average=(datarange[0]+datarange[1])/2
    elif kpitype == "Line":
        average=ave
    elif kpitype == "Slice":
        # get kpi field value and area - average = value/area
        integrateVariables = IntegrateVariables(Input=d)
        average = getdatarange(integrateVariables, kpifield, kpiComp)[0]\
                 / integrateVariables.CellData['Area'].GetRange()[0]
    elif kpitype == "Volume" or kpitype == "Clip":
        integrateVariables = IntegrateVariables(Input=d)
        average = getdatarange(integrateVariables, kpifield, kpiComp)[0]\
                  / integrateVariables.CellData['Volume'].GetRange()[0]

    fp_csv_metrics.write(",".join([kpi, str(average), str(datarange[0]),str(datarange[1])]) + "\n")


def writeCurrentStepStats(numStats, dStatsStatsInfo, fp_csv_metrics, statsTag, simTime,
                          isNegField=False):
    anim = GetAnimationScene()
    for iStat in range(numStats):
        statName = dStatsStatsInfo.GetArrayInformation(iStat).GetName()

        statValue = dStatsStatsInfo.GetArrayInformation(iStat).GetComponentRange(0)[0]
        if statName == 'Maximum':
            if isNegField:
                minimum = -statValue
            else:
                maximum = statValue

        elif statName == 'Minimum':
            if isNegField:
                maximum = -statValue
            else:
                minimum = statValue
        elif statName == 'Mean':
            average = statValue
            if isNegField:
                average = -average
        elif statName == 'Standard Deviation':
            stanDev = statValue
    fp_csv_metrics.write(
        ",".join([statsTag, str(average), str(minimum), str(maximum), str(stanDev),
                  "{:f}".format(simTime)]) + "\n")



def statsOverTime(metrichash, dataSource, dataDisplay):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    opacity=float(metrichash['opacity'])
    bodyopacity=float(metrichash['bodyopacity'])
    dataDisplay.Opacity = bodyopacity
    dataDisplay.ColorArrayName = ['POINTS', '']

    # create a new 'Temporal Statistics'
    temp_stat = TemporalStatistics(Input=dataSource)

    temp_stat_disp = Show(temp_stat, renderView1)
    Hide(dataSource, renderView1)

    temp_stat_disp.ColorArrayName = [None, '']
    temp_stat_disp.SetRepresentationType(metrichash['representationType'])
    temp_stat_disp.DiffuseColor = [0.0, 1.0, 0.0]
    temp_stat_disp.Specular = 0
    temp_stat_disp.Opacity = opacity

    fieldOrig = metrichash['field']
    metrichash['field'] = metrichash['field'] + '_' + metrichash['colorByField']

    metrichash = correctfieldcomponent(temp_stat, metrichash)
    colorMetric(temp_stat, metrichash)
    try:
        if metrichash['image'].split("_")[1] == "solo":
            Hide(data_reader, renderView1)
    except:
        pass

    # # Set 'field' to its original value
    # metrichash['field'] = fieldOrig
    return temp_stat


def extractStats(dataSource, statTag, metrichash, fp_csv_metrics):

    # Get view before adding the spreadsheets to get back to it afterwards.
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    # If kpifield is a vector, add a calculator on top and extract the component of the vector
    # as a scalar. Also, add a calculator for scalar data since this resolves a ParaView
    # bug/problem with extracting data directly from exo files

    kpifield = metrichash['field']
    kpiComp = metrichash['fieldComponent']

    arrayInfo = dataSource.PointData[kpifield]

    # create a new 'Calculator'
    if isfldScalar(arrayInfo):
        statVarName = kpifield
    else:
        statVarName = kpifield + '_' + kpiComp
    calc1 = Calculator(Input=dataSource)

    resultVarName = statVarName+'_s'
    calc1.ResultArrayName = resultVarName

    # ############################################################################
    # Values are multiplied by "-1" and then stats are corrected in
    # writeCurrentStepStats to get around an error with extracting values from some
    # exo files
    # ############################################################################
    isNegField = True
    if isNegField:
        multiplier = '-1*'
    else:
        multiplier = ''

    if kpiComp == 'Magnitude':
        calc1.Function = multiplier+'mag('+kpifield+')'
    else:
        calc1.Function = multiplier+statVarName
    UpdatePipeline()
    dataSource = calc1

    # create a new 'Descriptive Statistics'
    dStats = DescriptiveStatistics(Input=dataSource, ModelInput=None)
    
    dStats.VariablesofInterest = [resultVarName]

    ########################################################
    # Add another layout for viewing the spreadsheets. This is for updating the results
    # when switching to different time points at the end.

    CreateLayout('Layout #2')
    SetActiveView(None)
    spreadSheetView1 = CreateView('SpreadSheetView')
    spreadSheetView1.ColumnToSort = ''
    spreadSheetView1.BlockSize = 1024L
    layout2 = GetLayout()
    layout2.AssignView(0, spreadSheetView1)
    dStatsDisplay = Show(dStats, spreadSheetView1)
    spreadSheetView2 = CreateView('SpreadSheetView')
    spreadSheetView2.ColumnToSort = ''
    spreadSheetView2.BlockSize = 1024L
    layout2.AssignView(2, spreadSheetView2)
    dStatsDisplay_1 = Show(OutputPort(dStats, 1), spreadSheetView2)
    SetActiveView(spreadSheetView1)
    SetActiveSource(dStats)
    ########################################################

    UpdatePipeline()

    Times = get_extract_times(metrichash["extractStatsTimeSteps"],
                                  metrichash["extractStatsTimes"])

    anim = GetAnimationScene()

    anim.PlayMode = 'Real Time'

    for t in Times:
        spreadSheetView1.ViewTime = t
        spreadSheetView2.ViewTime = t
        anim.AnimationTime = t
        Render()
        RenderAllViews()
        UpdatePipeline()

        dStatsDataInfo = dStats.GetDataInformation()
        dStatsStatsInfo = dStatsDataInfo.GetRowDataInformation()
        numStats = dStatsDataInfo.GetRowDataInformation().GetNumberOfArrays()
        writeCurrentStepStats(numStats, dStatsStatsInfo, fp_csv_metrics, statTag, t,
                              isNegField)


    ########################################################
    # Set view back to the last view
    SetActiveView(renderView1)
    renderView1 = setFrame2latestTime(renderView1)

    # Delete the second layout after writing all the statistics
    Delete(spreadSheetView1)
    del spreadSheetView1
    Delete(spreadSheetView2)
    del spreadSheetView2
    RemoveLayout(layout2)


def correctfieldcomponent(datasource, metrichash):
    """
    Set "fieldComponent" to "Magnitude" if the component of vector/tensor fields is
    not given. For scalar fields set "fieldComponent" to an empty string.
    """
    kpifld = metrichash['field']
    arrayInfo = datasource.PointData[kpifld]
    #if type(arrayInfo) is type(None):
    #    metrichash['fieldComponent'] = ''
    
    if isfldScalar(arrayInfo):
        metrichash['fieldComponent'] = ''
    else:
        if not 'fieldComponent' in metrichash:
            metrichash['fieldComponent'] = 'Magnitude'
    return metrichash


def getReaderTypeFromfileAddress(dataFileAddress):
    if dataFileAddress.endswith('system/controlDict'):
        readerType = 'openFOAM'
    else:
        try:
            filename, file_extension = os.path.splitext(dataFileAddress)
            readerType = file_extension.replace('.', '')
        except:
            print('Error: Reader type cannot be set. Please check data file address')
            sys.exit(1)

    return readerType


def readDataFile(dataFileAddress, dataarray, convert2cellData=False):

    readerType = getReaderTypeFromfileAddress(dataFileAddress)
    if readerType == 'exo':
        # Read the results file : create a new 'ExodusIIReader'
        dataReader = ExodusIIReader(FileName=dataFileAddress)

        dataReader.ElementBlocks = ['PNT', 'C3D20 C3D20R', 'COMPOSITE LAYER C3D20', 'Beam B32 B32R',
                                    'CPS8 CPE8 CAX8 S8 S8R', 'C3D8 C3D8R', 'TRUSS2', 'TRUSS2',
                                    'CPS4R CPE4R S4 S4R', 'CPS4I CPE4I', 'C3D10', 'C3D4', 'C3D15',
                                    'CPS6 CPE6 S6', 'C3D6', 'CPS3 CPE3 S3',
                                    '2-node 1d network entry elem', '2-node 1d network exit elem',
                                    '2-node 1d genuine network elem']

        # only load the data that is needed
        dataReader.PointVariables = dataarray
    elif readerType == 'pvd':
        dataReader = PVDReader(FileName=[dataFileAddress])
    elif readerType == 'nek5000':
        dataReader = VisItNek5000Reader(FileName=dataFileAddress)
        #dataReader.Meshes = ['mesh']
        dataReader.PointArrays =  dataarray
    elif readerType == 'h5':
        dataReader = VisItPFLOTRANReader(FileName=dataFileAddress)
        #dataReader.Meshes = ['mesh']
        dataReader.CellArrays = dataarray
    elif readerType == 'openFOAM':
        # create a new 'OpenFOAMReader'
        dataReader = OpenFOAMReader(FileName=dataFileAddress)

        dataReader.MeshRegions = ['internalMesh']

        dataReader.CellArrays = dataarray

    elif readerType == 'vtk':
        dataReader = LegacyVTKReader(FileNames=[dataFileAddress])
        
    elif readerType == 'stl':
        dataReader = STLReader(FileNames=[dataFileAddress])

    if convert2cellData:
        # create a new 'Cell Data to Point Data'
        print("*** Converting all Cell Data to Point Data ***")
        dataReaderPointData = CellDatatoPointData(Input=dataReader)
        return dataReaderPointData
        
    return dataReader


def get_source_time_steps():
    # get animation scene
    animationScene1 = GetAnimationScene()

    # update animation scene based on data timesteps
    animationScene1.UpdateAnimationUsingDataTimeSteps()

    timeSteps = []
    if type(animationScene1.TimeKeeper.TimestepValues)== int or type(animationScene1.TimeKeeper.TimestepValues)== float:
        timeSteps.append(animationScene1.TimeKeeper.TimestepValues)
    elif len(animationScene1.TimeKeeper.TimestepValues) == 0:
        timeSteps = [0]
    else:
        timeSteps = list(animationScene1.TimeKeeper.TimestepValues)

    return timeSteps


def correctTimeSteps(timeSteps,times):
    timesLen = len(times)
    timeStepsCorrected = [x for x in timeSteps if 0 <= x < timesLen]
    subdiffMain = data_IO.difflists(timeSteps, timeStepsCorrected)
    if len(subdiffMain) > 0:
        warnings.warn("Excluding time point (s) " +str(data_IO.list2string(subdiffMain)))
        timeSteps = timeStepsCorrected
    return timeSteps


def getTimeStepsSubSet(times, timeStepsStr):
    if (timeStepsStr == 'last') or (timeStepsStr == "latest") or (timeStepsStr == "-1"):
        timesSubSet = [times[-1]]
    elif timeStepsStr == 'first' or (timeStepsStr == "0"):
        timesSubSet = [times[0]]
    elif timeStepsStr == "all":
        timesSubSet = times
    elif ":" in timeStepsStr:
        timeSlice = data_IO.str2slice(timeStepsStr)
        timesSubSet = times[timeSlice]
    elif "," in timeStepsStr:
        timeStepsSubSet = data_IO.read_ints_from_string(timeStepsStr, ",")
        timeStepsSubSet = correctTimeSteps(timeStepsSubSet, times)
        timesSubSet = [times[index] for index in timeStepsSubSet]
    else:
        timesSubSet = [times[int(timeStepsStr)]]
    return timesSubSet


def get_extract_times(extract_timesteps_key=None, extract_times_key=None):
    times = get_source_time_steps()
    if extract_timesteps_key is not None:
        times = getTimeStepsSubSet(times, extract_timesteps_key)
    else:
        try:
            times = data_IO.str2numList(extract_times_key)
        except:
            times = getTimeStepsSubSet(times, extract_times_key)
    return times


def setFrame2latestTime(renderView1, verbose=False):

    TimeSteps = get_source_time_steps()

    latesttime = TimeSteps[-1]
    if verbose:
        print("Setting view to latest Time: " + str(latesttime))

    renderView1.ViewTime = latesttime
    return renderView1


class ImageSettings:
    """ ImageSettings holds image settings and properties"""
    def __init__(self, magnification=2, view_size=[700,600],
                 background_color = [1,1,1], show_axis=0):
        """ Set image magnification, view_size and background_color"""
        self.magnification = magnification
        self.view_size = view_size
        self.background_color = background_color
        self.show_axis = show_axis


def initRenderView (dataReader, imageSettings):
    # disable automatic camera reset on 'Show'
    paraview.simple._DisableFirstRenderCameraReset()

    # get active view
    renderView1 = GetActiveViewOrCreate('RenderView')

    try:
        renderView1 = setFrame2latestTime(renderView1)
    except:
        pass

    # set the view size
    renderView1.ViewSize = imageSettings.view_size
    renderView1.Background = imageSettings.background_color

    # show data in view
    readerDisplay = Show(dataReader, renderView1)

    # reset view to fit data
    renderView1.ResetCamera()

    renderView1.InteractionMode = '2D'
    renderView1.OrientationAxesVisibility = imageSettings.show_axis

    return renderView1, readerDisplay


def get_colorbar_range(ctl):
    """ Return the range of a color transfer function (ctl) as a list = [min, max]

    I am sure there is a better way of doing this, but for now I am getting the minimum
    and maximum values from the ctl.RGBPoints.
    """
    rgbPoints = ctl.RGBPoints
    min = rgbPoints[0]
    max = rgbPoints[-4]
    return [min, max]


def get_colorbar_custom_labels(metricash, ctl):
    """ Return a list of paraview colorbar labels

    Set/Get colorbar labels either by
    - Reading the customLables directly from the metrichash, or
    - Set the labels based on the color transfer function (ctl) and number of labels
    provided by the user
    """

   # Set labels to custom labels if provided by the user:
    if 'customLabel' in metricash:
        labels = data_IO.read_floats_from_string(metricash['customLabel'],',')

    # if not, set the labels based on number of labels provided by the user
    else:
        color_range = get_colorbar_range(ctl)
        num_labels = float(metricash['NumberOfLabels'])
        labels = np.linspace(color_range[0],color_range[1],num_labels).tolist()

    return labels


def setColorBarRange(metrichash, ctf, dataSource):
    kpifld = metrichash['field']
    kpifldcomp = metrichash['fieldComponent']
    try:
        ctf.ApplyPreset(metrichash["colorscale"], True)
    except:
        pass
    try:
        if data_IO.str2bool(metrichash["invertcolor"]):
            ctf.InvertTransferFunction()
    except:
        pass

    try:
        datarange = getdatarange(dataSource, kpifld, kpifldcomp)
        min = datarange[0]
        max = datarange[1]
        if metrichash["min"] != "auto":
             min = float(metrichash["min"])
        if metrichash["max"] != "auto":
             max = float(metrichash["max"])
        ctf.RescaleTransferFunction(min, max)
        if int(metrichash["discretecolors"]) > 0:
            ctf.Discretize = 1
            ctf.NumberOfTableValues = int(metrichash["discretecolors"])
        else:
            ctf.Discretize = 0
    except:
        pass



def colorMetric(d, metrichash):
    display = GetDisplayProperties(d)
    kpifld = metrichash['field']
    kpifldcomp = metrichash['fieldComponent']
    ColorBy(display, ('POINTS', kpifld, kpifldcomp))

    Render()
    UpdateScalarBars()
    ctf = GetColorTransferFunction(kpifld)
    setColorBarRange(metrichash, ctf, d)
    # try:
    #     ctf.ApplyPreset(metrichash["colorscale"], True)
    # except:
    #     pass
    # try:
    #     if data_IO.str2bool(metrichash["invertcolor"]):
    #         ctf.InvertTransferFunction()
    # except:
    #     pass
    #
    # try:
    #     datarange = getdatarange(d, kpifld, kpifldcomp)
    #     min = datarange[0]
    #     max = datarange[1]
    #     if metrichash["min"] != "auto":
    #          min = float(metrichash["min"])
    #     if metrichash["max"] != "auto":
    #          max = float(metrichash["max"])
    #     ctf.RescaleTransferFunction(min, max)
    #     if int(metrichash["discretecolors"]) > 0:
    #         ctf.Discretize = 1
    #         ctf.NumberOfTableValues = int(metrichash["discretecolors"])
    #     else:
    #         ctf.Discretize = 0
    # except:
    #     pass

    renderView1 = GetActiveViewOrCreate('RenderView')
    ctfColorBar = GetScalarBar(ctf, renderView1)

    ctfColorBar.Orientation = "Horizontal"

    # Properties modified on uLUTColorBar
    if 'barTitle' in metrichash:
        ctfColorBar.Title = metrichash["barTitle"]
    if 'ComponentTitle' in metrichash:
        ctfColorBar.ComponentTitle = metrichash["ComponentTitle"]
    if 'FontColor' in metrichash:
        ctfColorBar.TitleColor = data_IO.read_floats_from_string(metrichash["FontColor"])
        ctfColorBar.LabelColor = data_IO.read_floats_from_string(metrichash["FontColor"])
    else:
        ctfColorBar.TitleColor = [0, 0, 0]
        ctfColorBar.LabelColor = [0, 0, 0]
    if 'FontSize' in metrichash:
        ctfColorBar.TitleFontSize = int(metrichash["FontSize"])
        ctfColorBar.LabelFontSize = int(metrichash["FontSize"])
    if 'LabelFormat' in metrichash:
        ctfColorBar.LabelFormat = metrichash["LabelFormat"]
        ctfColorBar.RangeLabelFormat = metrichash["LabelFormat"]

    PVversion = getParaviewVersion()

    if PVversion < 5.04:
        if 'NumberOfLabels' in metrichash:
            ctfColorBar.NumberOfLabels = int(metrichash["NumberOfLabels"])
    else:   # Use custom labels instead for paraview versions 5.4 and above:
        if ('NumberOfLabels' in metrichash) | ('customLabel' in metrichash):
            labels = get_colorbar_custom_labels(metrichash, ctf)
            ctfColorBar.UseCustomLabels = 1
            ctfColorBar.CustomLabels = labels


    if 'DrawTickMarks' in metrichash:
        ctfColorBar.DrawTickMarks = int(data_IO.str2bool(metrichash["DrawTickMarks"]))
    if PVversion < 5.04:
        if 'DrawSubTickMarks' in metrichash:
            ctfColorBar.DrawSubTickMarks = int(data_IO.str2bool(metrichash["DrawSubTickMarks"]))
    if 'ColorBarAnnotations' in metrichash:
        ctf.Annotations = data_IO.string2list(metrichash["ColorBarAnnotations"])
        ctfColorBar.DrawAnnotations = 1

    imgtype=metrichash['image'].split("_")[0]

    if (imgtype!="iso"):
        # center
        if PVversion < 5.04:
            ctfColorBar.Position = [0.25,0.05]
            ctfColorBar.Position2 = [0.5,0] # no such property in PV 5.04
        else:
            ctfColorBar.WindowLocation = 'LowerCenter'
            ctfColorBar.ScalarBarLength = 0.5
    else:
        # left
        if PVversion < 5.04:
            ctfColorBar.Position = [0.05,0.025]
            ctfColorBar.Position2 = [0.4,0] # no such property in PV 5.04
        else:
            ctfColorBar.WindowLocation = 'LowerLeftCorner'
            ctfColorBar.ScalarBarLength = 0.4

    #if individualImages == False:
    #    display.SetScalarBarVisibility(renderView1, False)


def createSlice(metrichash, dataReader, dataDisplay):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    opacity=float(metrichash['opacity'])
    bodyopacity=float(metrichash['bodyopacity'])
    dataDisplay.Opacity = bodyopacity
    dataDisplay.ColorArrayName = ['POINTS', '']
    slicetype = "Plane"
    plane = metrichash['plane']

    s = Slice(Input=dataReader)
    s.SliceType = slicetype
    s.SliceType.Origin = setviewposition(metrichash['position'], camera)
    s.SliceType.Normal = planeNormalFromName(plane)
    sDisplay = Show(s, renderView1)
    sDisplay.ColorArrayName = [None, '']
    sDisplay.SetRepresentationType(metrichash['representationType']) 
    sDisplay.DiffuseColor = [0.0, 1.0, 0.0]
    sDisplay.Specular = 0
    sDisplay.Opacity = opacity
    colorMetric(s, metrichash)
    return s


def createStreamTracer(metrichash, data_reader, data_display):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    opacity = float(metrichash['opacity'])
    bodyopacity = float(metrichash['bodyopacity'])
    data_display.Opacity = bodyopacity
    data_display.ColorArrayName = ['POINTS', '']

    seedPosition = setviewposition(metrichash['position'], camera)
    if metrichash['seedType'].lower() == 'line':
        streamTracer = StreamTracer(Input=data_reader,
                                    SeedType='High Resolution Line Source')
        streamTracer.SeedType.Point1 = seedPosition[0:3]
        streamTracer.SeedType.Point2 = seedPosition[3:6]
        streamTracer.SeedType.Resolution = int(metrichash['resolution'])

    elif metrichash['seedType'].lower() == 'plane':
        # create a new 'Point Plane Interpolator' for seeding the stream lines
        pointPlaneInterpolator = PointPlaneInterpolator(Input=data_reader, Source='Bounded Plane')
        pointPlaneInterpolator.Source.Center = setviewposition(metrichash['center'], camera)
        pointPlaneInterpolator.Source.BoundingBox = seedPosition
        pointPlaneInterpolator.Source.Normal = planeNormalFromName(metrichash['plane'])
        pointPlaneInterpolator.Source.Resolution = int(metrichash['resolution'])
        UpdatePipeline()
        streamTracer = StreamTracerWithCustomSource(Input=data_reader,
                                                    SeedSource=pointPlaneInterpolator)


    kpifld = metrichash['field'] #!!!!!!!
    streamTracer.Vectors = ['POINTS', kpifld]
    
    streamTracer.IntegrationDirection = metrichash['integralDirection'] # 'BACKWARD', 'FORWARD' or  'BOTH'
    streamTracer.IntegratorType = 'Runge-Kutta 4'
    # To do : Add a default value based on domain size ?
    streamTracer.MaximumStreamlineLength = float(metrichash['maxStreamLength'])


    ##
    # create a new 'Tube'
    tube = Tube(Input=streamTracer)
    tube.Radius = float(metrichash['tubeRadius'])
    # show data in view
    tubeDisplay = Show(tube, renderView1)
    # trace defaults for the display properties.
    tubeDisplay.Representation = metrichash['representationType'] 
    tubeDisplay.ColorArrayName = [None, '']
    tubeDisplay.EdgeColor = [0.0, 0.0, 0.0]
    tubeDisplay.DiffuseColor = [0.0, 1.0, 0.0]
    tubeDisplay.Specular = 0
    tubeDisplay.Opacity = opacity


    fieldOrig = metrichash['field']
    if 'fieldComponent' in metrichash:
        fieldComponentOrig = metrichash['fieldComponent']

    metrichash['field'] = metrichash['colorByField']
    if 'colorByFieldComponent' in metrichash:
        metrichash['fieldComponent'] = metrichash['colorByFieldComponent']
    metrichash = correctfieldcomponent(streamTracer, metrichash)
    colorMetric(tube, metrichash)
    try:
        if metrichash['image'].split("_")[1] == "solo":
            Hide(data_reader, renderView1)
    except:
        pass

    # Set 'field' and 'fieldComponent' to their original values
    metrichash['field'] = fieldOrig
    if 'colorByFieldComponent' in metrichash:
        metrichash['fieldComponent'] = fieldComponentOrig

    return tube


def createWarpbyVector(metrichash, data_reader, data_display):
    # The field should be a vector
    kpifld = metrichash['field']
    arrayInfo = data_reader.PointData[kpifld]
    if isfldScalar(arrayInfo):
        print('Error: The field for warpByVector type should be a vector. '
              'Please check kpi file.')
        sys.exit(1)

    renderView1 = GetActiveViewOrCreate('RenderView')

    opacity = float(metrichash['opacity'])
    bodyopacity = float(metrichash['bodyopacity'])
    data_display.Opacity = bodyopacity
    data_display.ColorArrayName = ['POINTS', '']

    # create a new 'Warp By Vector'
    s = WarpByVector(Input=data_reader)
    s.Vectors = ['POINTS', kpifld]
    s.ScaleFactor = float(metrichash['scaleFactor'])

    sDisplay = Show(s, renderView1)
    sDisplay.Representation = metrichash['representationType']
    sDisplay.ColorArrayName = [None, '']
    sDisplay.EdgeColor = [0.0, 0.0, 0.0]
    sDisplay.Opacity = opacity

    if 'colorByField' in metrichash:
        metrichash['field'] = metrichash['colorByField']
        if 'colorByFieldComponent' in metrichash:
            metrichash['fieldComponent'] = metrichash['colorByFieldComponent']
        metrichash = correctfieldcomponent(data_reader, metrichash)
    colorMetric(s, metrichash)


def createClip(metrichash, data_reader, data_display):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    opacity = float(metrichash['opacity'])
    bodyopacity = float(metrichash['bodyopacity'])
    data_display.Opacity = bodyopacity
    data_display.ColorArrayName = ['POINTS', '']
    cliptype = "Plane"
    plane = metrichash['plane']
    if 'invert' in metrichash.keys():
        invert = data_IO.str2bool(metrichash['invert'])
    else:
        invert = 0

    s = Clip(Input=data_reader)
    s.ClipType = cliptype
    s.ClipType.Origin = camera.GetFocalPoint()

    PVversion = getParaviewVersion()

    if PVversion < 5.05:
        s.InsideOut = invert
    else:
        s.Invert = invert

    s.ClipType.Origin = setviewposition(metrichash['position'],camera)
    s.ClipType.Normal = planeNormalFromName(plane)
    sDisplay = Show(s, renderView1)
    sDisplay.ColorArrayName = [None, '']
    sDisplay.SetRepresentationType(metrichash['representationType']) 
    sDisplay.DiffuseColor = [0.0, 1.0, 0.0]
    sDisplay.Specular = 0
    sDisplay.Opacity = opacity
    colorMetric(s, metrichash)
    try:
        if metrichash['image'].split("_")[1] == "solo":
            Hide(data_reader, renderView1)
    except:
        pass
    return s


def createProbe(metrichash, data_reader):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    p = ProbeLocation(Input=data_reader, ProbeType='Fixed Radius Point Source')
    p.PassFieldArrays = 1
    #p.ProbeType.Center = [1.2176899909973145, 1.2191989705897868, 1.5207239668816328]
    p.ProbeType.Center = setviewposition(metrichash['position'], camera)
    p.ProbeType.NumberOfPoints = 1
    p.ProbeType.Radius = 0.0
    ps = Sphere(Radius=0.025, ThetaResolution=32)
    ps.Center = setviewposition(metrichash['position'], camera)
    psDisplay = Show(ps, renderView1)
    psDisplay.DiffuseColor = [1.0, 0.0, 0.0]
    psDisplay.Opacity = 0.8
    return p


def createVolume(metrichash, data_reader, data_display):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    bounds = [float(x) for x in metrichash['position'].split(" ")]
    opacity = float(metrichash['opacity'])
    bodyopacity = float(metrichash['bodyopacity'])

    data_display.Opacity = bodyopacity
    data_display.ColorArrayName = ['POINTS', '']
    c = Clip(Input=data_reader)
    c.ClipType = 'Box'
    # (xmin,xmax,ymin,ymax,zmin,zmax)
    #c.ClipType.Bounds = [0.1, 3, 0.1, 2.3, 0.15, 2.3]
    c.ClipType.Bounds = bounds

    PVversion = getParaviewVersion()

    if PVversion < 5.05:
        c.InsideOut = 1
    else:
        c.Invert = 1

    cDisplay = Show(c, renderView1)
    cDisplay.ColorArrayName = ['Points', metrichash['field']]
    cDisplay.SetRepresentationType(metrichash['representationType']) 
    cDisplay.DiffuseColor = [1.0, 1.0, 0.0]
    cDisplay.Specular = 0
    cDisplay.Opacity = opacity 
    colorMetric(c, metrichash)
    return c

def createBasic(metrichash, dataReader, dataDisplay):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')
    bodyopacity=float(metrichash['bodyopacity'])
    dataDisplay.Opacity = bodyopacity
    dataDisplay.SetRepresentationType(metrichash['representationType'])

    if not (metrichash['field'] == 'None'):
        colorMetric(dataReader, metrichash)
    else:
        ColorBy(dataDisplay, ('POINTS', ''))
    return dataReader


def genQuery(queryField, queryList):
    query = ''
    elemList = data_IO.read_ints_from_string(queryList, ',')
    for elem in elemList:
        query = query + '({:s} == {:d}) | '.format(queryField, elem)
    # Remove the last "\" from query
    query = query[:-2]
    return query


def createFindData(metrichash, dataReader, dataDisplay):
    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    opacity = float(metrichash['opacity'])
    bodyopacity = float(metrichash['bodyopacity'])
    dataDisplay.Opacity = bodyopacity
    dataDisplay.ColorArrayName = ['POINTS', '']

    # create the extractSelection object
    extract = ExtractSelection(Input = dataReader)
    query = genQuery(metrichash['queryField'],metrichash['queryList'])
    ########
    ######## Don't get this from user, write a function to determine field type
    #########
    queryFieldType = metrichash['queryFieldType']
    sqs = SelectionQuerySource(FieldType=queryFieldType, QueryString= query)
    extract.Selection = sqs
    eDisplay = Show(extract, renderView1)

    eDisplay.ColorArrayName = [None, '']
    eDisplay.SetRepresentationType(metrichash['representationType'])
    eDisplay.DiffuseColor = [0.0, 1.0, 0.0]
    eDisplay.Specular = 0
    eDisplay.Opacity = opacity
    colorMetric(extract, metrichash)

    return  extract


def plotLine(infile, imageName) :
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    warnings.filterwarnings('ignore')

    header = np.genfromtxt(infile, delimiter=',', names=True).dtype.names
    data = np.genfromtxt(infile, delimiter=',', skip_header=1)

    x = data[:, 0]
    y = data[:, 1]

    plt.figure(figsize=(10, 6))
    plt.plot(x, y)

    locs, labels = plt.yticks()
    plt.yticks(locs, map(lambda x: "%g" % x, locs))

    plt.xlabel('Point')
    plt.ylabel(header[1])
    # plt.title(infile.replace(".csv", "").replace("plot_", "") + ' Plot')
    plt.grid(True)
    plt.savefig(imageName)


def createLine(metrichash, data_reader, outputDir=".", caseNumber=""):
    resolution = int(metrichash['resolution'])
    try:
        image = metrichash['image']
    except:
        image = None

    point = [x for x in metrichash['position'].split()]

    camera = GetActiveCamera()
    renderView1 = GetActiveViewOrCreate('RenderView')

    if point[0] == "center":
        point[0] = camera.GetFocalPoint()[0]
    if point[3] == "center":
        point[3] = camera.GetFocalPoint()[0]
    if point[1] == "center":
        point[1] = camera.GetFocalPoint()[1]
    if point[4] == "center":
        point[4] = camera.GetFocalPoint()[1]
    if point[2] == "center":
        point[2] = camera.GetFocalPoint()[2]
    if point[5] == "center":
        point[5] = camera.GetFocalPoint()[2]
    
    point1=[float(point[0]),float(point[1]),float(point[2])]
    point2=[float(point[3]),float(point[4]),float(point[5])]
    l = PlotOverLine(Input=data_reader, Source='High Resolution Line Source')
    l.PassPartialArrays = 1
    l.Source.Point1 = point1
    l.Source.Point2 = point2
    l.Source.Resolution = resolution
    lDisplay = Show(l, renderView1)
    lDisplay.DiffuseColor = [1.0, 0.0, 0.0]
    lDisplay.Specular = 0
    lDisplay.Opacity = 1

    # Get the line data
    pl = servermanager.Fetch(l)

    kpifld = metrichash['field']
    kpiComp = metrichash['fieldComponent']
    if (image == "plot"):
        if not (os.path.exists(outputDir)):
            if outputDir:
                os.makedirs(outputDir)
        if caseNumber:
            metrichash['imageName'] = metrichash['imageName'].format(int(caseNumber))
        imageFullPath = outputDir + metrichash['imageName']
        imageName, imageExtension = os.path.splitext(imageFullPath)
        csvFileName = imageName + ".csv"
        f=open(csvFileName,"w")
        f.write("point,"+kpifld)
        if kpiComp:
            f.write("_" + kpiComp)
        f.write("\n")

    METRIC_INDEX=0
    for a in range(0,pl.GetPointData().GetNumberOfArrays()):
        if kpifld == pl.GetPointData().GetArrayName(a):
            METRIC_INDEX = a
    sum=0
    num=pl.GetPointData().GetArray(METRIC_INDEX).GetNumberOfTuples()
    # Get the component numbers from the input of line filter (data_reader) (?)
    compNumber = getfldCompNumber(data_reader.PointData[kpifld], kpiComp)
    for t in range(0,num):
        dataPoint = pl.GetPointData().GetArray(METRIC_INDEX).GetTuple(t)[compNumber]
        if str(float(dataPoint)).lower() != "nan":
            sum += dataPoint
        if image == "plot":
            f.write(",".join([str(t), str(dataPoint)])+"\n")
    if image == "plot":
        f.close()
        plotLine(csvFileName, imageFullPath)
    ave = sum/pl.GetPointData().GetArray(METRIC_INDEX).GetNumberOfTuples()
    return l


def adjustCamera(view, renderView1, metrichash):
    camera=GetActiveCamera()
    if view == "iso-TN":
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,0,1)
        camera.SetViewUp(0, 1.0, 0)
        renderView1.ResetCamera()
        camera.Azimuth(45)
        camera.Elevation(45)
    elif view == 'iso-SE':
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,-1,0)
        camera.SetViewUp(0, 0, 1.0)
        renderView1.ResetCamera()
        camera.Azimuth(-45)
        camera.Elevation(45)
    elif view == 'iso-NE' or view == 'iso':
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,-1,0)
        camera.SetViewUp(0, 0, 1.0)
        renderView1.ResetCamera()
        camera.Azimuth(45)
        camera.Elevation(45)
    elif view == 'iso-NW':
        camera.SetFocalPoint(0, 0, 0)
        camera.SetPosition(0, -1, 0)
        camera.SetViewUp(0, 0, 1.0)
        renderView1.ResetCamera()
        camera.Azimuth(135)
        camera.Elevation(45)
    elif view == 'iso-SW' or view == 'iso-flipped':
        camera.SetFocalPoint(0, 0, 0)
        camera.SetPosition(0, -1, 0)
        camera.SetViewUp(0, 0, 1.0)
        renderView1.ResetCamera()
        camera.Azimuth(-135)
        camera.Elevation(45)
    # old iso
    # elif view.startswith("iso"):
    #     camera.SetFocalPoint(0, 0, 0)
    #     if (view == "iso-flipped"):
    #         camera.SetPosition(0, 1, 0)
    #     else:
    #         camera.SetPosition(0, -1, 0)
    #     renderView1.ResetCamera()
    #     # adjust for scale margin
    #     camera.SetFocalPoint(camera.GetFocalPoint()[0],camera.GetFocalPoint()[1],camera.GetFocalPoint()[2]-0.25)
    #     camera.SetPosition(camera.GetPosition()[0],camera.GetPosition()[1],camera.GetPosition()[2]-1)
    #     camera.Elevation(45)
    #     camera.Azimuth(45)
    elif view == "+X" or view == "+x" or view == "back": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(1, 0, 0)
        camera.SetViewUp(0, 0, 1)
        renderView1.ResetCamera()
    elif view == "-X" or view == "-x" or view == "front": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(-1,0,0)
        camera.SetViewUp(0, 0, 1)
        renderView1.ResetCamera()
    elif view == "+Y" or view == "+y" or view == "right": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,1,0)
        camera.SetViewUp(0, 0, 1)
        renderView1.ResetCamera()
    elif view == "-Y" or view == "-y" or view == "left": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,-1,0)
        camera.SetViewUp(0, 0, 1)
        renderView1.ResetCamera()
    elif view == "+Z" or view == "+z" or view == "top": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,0,1)
        camera.SetViewUp(0, 1, 0)
        renderView1.ResetCamera()
        #        camera.Roll(90)
    elif view == "-Z" or view == "-z" or view == "bottom": 
        camera.SetFocalPoint(0,0,0)
        camera.SetPosition(0,0,-1)
        camera.SetViewUp(0, 1, 0)
        renderView1.ResetCamera()
        #       camera.Roll(-90)
    elif view == "customize":
        renderView1.InteractionMode = '3D'
        renderView1.CameraPosition   = data_IO.read_floats_from_string(metrichash["CameraPosition"])
        renderView1.CameraFocalPoint = data_IO.read_floats_from_string(metrichash["CameraFocalPoint"])
        renderView1.CameraViewUp = data_IO.read_floats_from_string(metrichash["CameraViewUp"])
        renderView1.CameraParallelScale = float(metrichash["CameraParallelScale"])
        renderView1.CameraParallelProjection = int(metrichash["CameraParallelProjection"])


def write_image_times(csv_file_name, times, image_numbers, append_csv=False):
    if append_csv:
        fcsv = data_IO.open_file(csv_file_name,'a')
    else:
        fcsv = data_IO.open_file(csv_file_name, 'w')

    csv_writer = csv.writer(fcsv)
    if not append_csv:
        csv_writer.writerow(["number","time"])
    for i,t in enumerate(times):
        csv_writer.writerow([image_numbers[i],t])
    fcsv.close()


def save_images(outputDir, metrichash, magnification, renderView, pw_filter,
                case_number=None, write_image_from=0,append_csv=False):

    times = get_extract_times(metrichash["imageTimeSteps"], metrichash["imageTimes"])

    imageName = os.path.join(outputDir, metrichash["imageName"])
    outDir = os.path.dirname(imageName)
    if not (os.path.exists(outDir)):
        if outDir:
            os.makedirs(outDir)

    # write output times to a csv file
    csv_file_name = re.sub('{.*?}','',imageName)
    csv_file_name = os.path.splitext(csv_file_name)[0] + "_times.csv"

    anim = GetAnimationScene()
    anim.PlayMode = 'Real Time'

    image_numbers = []
    kpifld = metrichash['field']
    ctf = GetColorTransferFunction(kpifld)

    for i,t in enumerate(times):
        renderView.ViewTime = t
        anim.AnimationTime = t
        setColorBarRange(metrichash, ctf, pw_filter)
        file_image_number = i + write_image_from
        if case_number:
            imageName_i = imageName.format(int(case_number), file_image_number)
        else:
            imageName_i = imageName.format(file_image_number)
        image_numbers.append(file_image_number)
        Render()
        SaveScreenshot(imageName_i, magnification=magnification, quality=100)

    write_image_times(csv_file_name, times, image_numbers, append_csv=append_csv)
    # Set animation mode back to snap to time steps
    anim.PlayMode = 'Snap To TimeSteps'
    return times, image_numbers


def write_anim_frames(frames_dir, frame_names, magnification):

    if not (os.path.exists(frames_dir)):
        os.makedirs(frames_dir)

    WriteAnimation(os.path.join(frames_dir, frame_names),
                   Magnification=magnification, FrameRate=15.0,
                   Compression=False)


def make_anim_from_frames(animation_frames_dir, frames_name_pattern, anim_file,
                          delete_frames=True):
    subprocess.call(["convert", "-delay", "15",  "-loop",  "0",
                     os.path.join(animation_frames_dir, frames_name_pattern),
                     anim_file])

    if delete_frames:
        shutil.rmtree(animation_frames_dir)


def makeAnimation(outputDir, kpi, magnification, animationName, delete_frames=True,
                  case_number=None):
    if case_number:
        animationName = animationName.format(int(case_number))

    print(animationName)

    frames_dir = os.path.join(outputDir, 'animFrames')

    write_anim_frames(frames_dir, "out_" + kpi + ".png", magnification)

    make_anim_from_frames(frames_dir, "out_" + kpi + ".*.png",
                          os.path.join(outputDir, animationName), delete_frames)


def exportx3d(outputDir,kpi, metricObj, dataReader, renderBody, blenderContext):

    blenderFramesDir = outputDir + kpi + '_blender'
    blenderFramesDir = os.path.join(blenderFramesDir, '')
    if not (os.path.exists(blenderFramesDir)):
        os.makedirs(blenderFramesDir)

    try:
        TimeSteps = get_source_time_steps()
        firstTimeStep = TimeSteps[0]
        renderView1 = GetActiveViewOrCreate('RenderView')
        renderView1.ViewTime = firstTimeStep
        for num, time in enumerate(TimeSteps):
            name_solo = blenderFramesDir + str(num) + '_solo.x3d'
            Show(metricObj, renderView1)
            Hide(dataReader, renderView1)
            ExportView(name_solo, view=renderView1)
            if renderBody == "true":
                name_body = blenderFramesDir + str(num) + '_body.x3d'
                Show(dataReader, renderView1)
                Hide(metricObj, renderView1)
                ExportView(name_body, view=renderView1)
            animationScene1 = GetAnimationScene()
            animationScene1.GoToNext()
    except:
        renderView1 = GetActiveViewOrCreate('RenderView')
        name_body = blenderFramesDir + 'body.x3d'
        Show(dataReader, renderView1)
        ExportView(name_body, view=renderView1)
        
    if blenderContext != None and len(blenderContext) > 0:
        for i in blenderContext:
            dataReaderTmp = readDataFile(i, None)
            renderViewTmp = CreateView('RenderView')
            readerDisplayTmp = Show(dataReaderTmp, renderViewTmp)
            name_body = blenderFramesDir + os.path.splitext(os.path.basename(i))[0] + '.x3d'
            ExportView(name_body, view=renderViewTmp)

    # tar the directory
    data_IO.tarDirectory(os.path.dirname(blenderFramesDir) + ".tar",
                         os.path.dirname(blenderFramesDir))
    shutil.rmtree(blenderFramesDir)

def saveSTLfile(renderView,filename,magnification,quality):
    adjustCamera("iso", renderView, None, "false")
    SaveScreenshot(filename, magnification=magnification, quality=quality)
    
