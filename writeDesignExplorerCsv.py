import sys
import data_IO
import paramUtils

# Generate a csv file for Design Explorer (DE) from the input parameters and output metrics.
# - The individual extracted values from each case (e.g., metrics.csv files) are assumed to be in
#     *i* 
#   format, where i is the case number. For example, results/metrics/case_0.csv where i=0. 
#   The ResultsDirRoot would need to be set to results/metrics/case_@@i@@.csv in this case.


# Example output csv file for Design Explorer
"""
in:Inlet Velocity,in:Jet Velocity,in:Pannel Height,out:PMV (person ave),out:PMV (room ave),out:T (person ave),out:T (room ave),out:DR (person ave),out:DR (room ave),out:U (person ave),out:U (room ave),img:T_jetSection.png,img:T_personSection.png,img:U_jetSection.png,img:U_personSection.png
5,0,0.04,-0.74,-0.803,297.381,297.19,72.27,74.74,0.15,0.042,../pngs/0/out_sliceT_jet.png,../pngs/0/out_sliceT_person.png,../pngs/0/out_sliceUMag_jet.png,../pngs/0/out_sliceUMag_person.png
5,0,0.5,-0.693,-0.682,297.258,297.30,67.95,67.45,0.18,0.022,../pngs/1/out_sliceT_jet.png,../pngs/1/out_sliceT_person.png,../pngs/1/out_sliceUMag_jet.png,../pngs/1/out_sliceUMag_person.png
5,20,0.04,-0.7,-0.807,297.437,297.32,71.66,70.22,0.14,0.040,../pngs/2/out_sliceT_jet.png,../pngs/2/out_sliceT_person.png,../pngs/2/out_sliceUMag_jet.png,../pngs/2/out_sliceUMag_person.png
5,20,0.5,0.381,0.326,297.851,297.737,61.59,67.84,0.20,0.024,../pngs/3/out_sliceT_jet.png,../pngs/3/out_sliceT_person.png,../pngs/3/out_sliceUMag_jet.png,../pngs/3/out_sliceUMag_person.png
"""

# Parse function inputs

print(sys.argv)
if len(sys.argv) < 5:
    print("Number of provided arguments: ", len(sys.argv) - 1)
    print("Usage: pvpython writeDesignExplorerCsv <cases.list File> "
          "<desiredMetrics.json> <basepath> <designExplorer.csv> \n"
          "[ImageDirRoot=\"outputs/png\"] [metricsFilesNameTemplate=\"outputs/case@@i@@/metrics.csv\"] "
          "[outputParamsDesiredStatsFile] [params2ignore]")

    sys.exit()

paramsFile =sys.argv[1]
kpiFile = sys.argv[2]
basepath=sys.argv[3]
deCSVFile = sys.argv[4]
imagesdir = data_IO.setOptionalSysArgs(sys.argv, "outputs/png", 5)
metricsFilesNameTemplate = data_IO.setOptionalSysArgs(sys.argv, "outputs/case@@i@@/metrics.csv", 6)
outputParamStatsFile = data_IO.setOptionalSysArgs(sys.argv, '', 7)
ignoreList_default = []
ignoreList_default = ",".join(ignoreList_default)
ignoreList = data_IO.setOptionalSysArgs(sys.argv, ignoreList_default, 8)
ignoreSet = set(ignoreList.split(","))


# Read the input parameters from the cases.list file (also works with a sweep.run file but
# make sure the order is the same as cases.list files used for running the cases)
cases = paramUtils.readParamsFile(paramsFile, paramValDelim=":")
print(" Read " + str(len(cases)) + " Cases")

# Get the list of input parameters from the first case
inputVarNames = paramUtils.getParamNamesFromCase(cases[0])
inputVarNames = list(set(inputVarNames)-ignoreSet)

# Add the values of input parameters for each case to caselist
caselist = paramUtils.writeInputParamVals2caselist(cases, inputVarNames)

# Read the desired output metrics
outputParamNames = paramUtils.getOutputParamsFromKPI(kpiFile)
outputParamNames = list(set(outputParamNames)-ignoreSet)
outputParamList = paramUtils.getOutputParamsStatList(
    outputParamStatsFile, outputParamNames,['ave', 'min', 'max'])

outParamTable = paramUtils.genOutputLookupTable(outputParamList)

# Read the desired metric from each output file and add them to caselist
caselist = paramUtils.writeOutputParamVals2caselist(
    cases, metricsFilesNameTemplate, outParamTable, caselist, outputParamStatsFile)

# Get the list of desired images
imgList, imgTypes = paramUtils.getOutImgsFromKPI(kpiFile)

caselist = paramUtils.writeImgs2caselist(cases, imgList, imgTypes, basepath, imagesdir, caselist)

# Write the header of the DE csv file
header = paramUtils.generateHeader(inputVarNames, outParamTable, imgList)

# Write the Design Explorer csv file:
paramUtils.writeDesignExplorerCSVfile(deCSVFile, header, caselist)
