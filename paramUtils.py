import math
import sys
import itertools as it
import data_IO
import warnings
import re
import os

from collections import OrderedDict


def readCases(paramsFile, namesdelimiter=";", valsdelimiter="_",paramsdelimiter = "\n", withParamType = True):
    with open(paramsFile) as f:
        content = f.read().split(paramsdelimiter)
        if content[-1] == "\n":
            del content[-1]
        # Replace non-ascii characters with space
        content = data_IO.remove_non_ascii_list(content)

    pvals = {}
    pTypes = {}
    for x in content:
        if "null" not in x and x != "":
            pname = x.split(namesdelimiter)[0]
            if withParamType:
                pType = x.split(namesdelimiter)[1]
                pval = x.split(namesdelimiter)[2]
            else:
                pval = x.split(namesdelimiter)[1]
            if valsdelimiter in pval:
                pval = pval.split(valsdelimiter)
            elif ":" in pval:
                pval = data_IO.expandVars(pval).split(",")
            else:
                pval = [pval]
            pvals[pname] = pval
            if withParamType:
                pTypes[pname] = pType

    varNames = sorted(pvals)
    cases = [[{varName: val} for varName, val in zip(varNames, prod)] for prod in
             it.product(*(pvals[varName] for varName in varNames))]
    return cases, varNames, pTypes


def correct_input_variable_names(cases):
    all_cases_corrected = []
    for case in cases:
        corrected_case = []
        for param_val_pair in case:
            param_name = next(iter(param_val_pair))
            param_name_corrected = param_name.replace(',', '_')
            param_name_corrected = param_name_corrected.replace('(', '_')
            param_name_corrected = param_name_corrected.replace(')', '_')
            param_name_corrected = param_name_corrected.replace('[', '_')
            param_name_corrected = param_name_corrected.replace(']', '_')
            param_name_corrected = param_name_corrected.replace(':', '')
            param_name_corrected = param_name_corrected.replace('/', '_div_')
            param_val_pair[param_name_corrected] = param_val_pair.pop(param_name)
            corrected_case.append(param_val_pair)
        all_cases_corrected.append(corrected_case)
    return all_cases_corrected


def generate_caselist(cases, pnameValDelimiter='='):

    caselist = []
    for c in cases:
        case = ""
        for p in c:
            pname = list(p.keys())[0]
            pval = p[pname]
            case += pname + pnameValDelimiter + pval + ","
        caselist.append(case[:-1])
    return caselist


def getParamTypeFromfileAddress(dataFileAddress):
    if dataFileAddress.endswith('.run'):
        paramsType = 'paramFile'
    elif dataFileAddress.endswith('.list'):
        paramsType = 'listFile'
    else:
        print('Error: parameter/case type cannot be set. Please provide .list or .run file. ')
        sys.exit(1)

    return paramsType


def readcasesfromcsv(casesFile,paramValDelim=',', paramPairDelim = ','):
    f = open(casesFile, "r")
    cases = []
    for i, line in enumerate(f):
        # First split all the parameters and values:
        data = []
        for paramValPair in line.split(paramPairDelim):
            data.extend(l.replace("\n", "") for l in paramValPair.split(paramValDelim))
        # Combine the parameter labels and their values:
        span = 2
        data = [paramValDelim.join(data[i:i+span]) for i in range(0, len(data), span)]
        case = []
        for ii, v in enumerate(data):
            param = {v.split(paramValDelim)[0]: v.split(paramValDelim)[1]}
            case.append(param)
        cases.append(case)
    f.close()
    return cases


def readParamsFile(paramsFile, paramValDelim=',', paramPairDelim=','):
    paramsFileType = getParamTypeFromfileAddress(paramsFile)
    if paramsFileType == 'paramFile':
        cases = readCases(paramsFile)
    else:
        cases = readcasesfromcsv(paramsFile, paramValDelim, paramPairDelim)
    return cases


def generateHeader(inputParamNames, outParamTables, outImgList):
    num2statTable = {0:'ave', 1:'min', 2:'max', 3:'sd'}
    header = []
    for varName in inputParamNames:
        header += "in:" + varName + ","
    header = "".join(header[:-1])
    for paramNameStat in outParamTables:
        outStr = ",out:" + paramNameStat[0]
        if paramNameStat[1] >= 0:
            outStr += "_" + num2statTable[paramNameStat[1]]
        header += outStr
    for imgName in outImgList:
        header += ",img:" + imgName
    return header


def convertListOfDicts2Dict(listOfDicts):
    """
    Convert the list of dictionaries (per parameter/value pair) from a case"
    into a single dictionary
    """
    result = {}
    for d in listOfDicts:
        result.update(d)
    return result


def getParamNamesFromCase(case):
    result = convertListOfDicts2Dict(case)
    inputVarNames = sorted(result)
    return inputVarNames


def writeInputParamVals2caselist(cases, inputVarNames):
    """
    Add the values of input parameters for each case to caselist
    """
    caselist = []
    for c in cases:
        case = ""
        cDict = convertListOfDicts2Dict(c)
        for pname in inputVarNames:
            pval = cDict[pname]
            case += pval + ","
        caselist.append(case[:-1])
    return caselist


def genOutputLookupTable(outParamsList):
    lookupTable = []
    stat2numTable = {'ave': 0, 'min': 1, 'max': 2, 'sd': 3}
    for param in outParamsList:
        if param.find("(") > 0:
            paramName = param[:param.find("(")]
            paramName = paramName.lstrip()
            statStr = param[param.find("(")+1:param.find(")")]
            statKey = stat2numTable[statStr.lower()]
            lookupTable.append([paramName, statKey])
        else:
            lookupTable.append([param, -1])
    return lookupTable


def parseOutputType(statStr, isParaviewMetric):
    statList = []
    statStrList = [x.strip().lower() for x in statStr.split(",")]
    stat2numTable = OrderedDict([('ave', 0), ('min', 1), ('max', 2), ('sd', 3)])
    if statStrList[0].lower() in {"none", "image"}:
        return statList
    elif statStrList[0] == "all":
        statStrList = list(stat2numTable.keys())
    for statStr in statStrList:
        if isParaviewMetric:
            if statStr in stat2numTable:
                statList.append(stat2numTable[statStr])
            else:
                warningMsg = 'Please check the format of stat flag ' \
                             '("{}" is not acceptable for Paraview metrics). ' \
                             'Accepted values are: "none", "image", "all", "{}". ' \
                             'Setting stat flag to "none". ' \
                    .format(statStr, '", "'.join(list(stat2numTable.keys())))
                warnings.warn(warningMsg)
        else:
            statList.append(-1)
    return statList


def getOutputParamsFromKPI(kpihash, orderPreservedKeys, ignoreSet):
    outputParams= []
    lookupTable = []
    for kpi in orderPreservedKeys:
        if kpi not in ignoreSet:
            metrichash = kpihash[kpi]
            if data_IO.str2bool(metrichash['IsParaviewMetric']):
                if not data_IO.str2bool(metrichash['extractStats']):
                    continue
            outputTypeList = parseOutputType(metrichash['DEXoutputFlag'],
                                             data_IO.str2bool(metrichash['IsParaviewMetric']))
            for outputType in outputTypeList:
                outputParams.append(kpi)
                lookupTable.append([kpi, outputType])
    return lookupTable


def getOutImgsFromKPI(kpihash, orderPreservedKeys):
    imgTitles= []
    imgNames = []
    for kpi in orderPreservedKeys:
        metrichash = kpihash[kpi]
        isParaviewMetric = data_IO.str2bool(metrichash["IsParaviewMetric"])
        if not (isParaviewMetric or metrichash['DEXoutputFlag'].lower() == "image"):
            continue
        imageName = metrichash['imageName']
        if imageName != "None":
            imgTitles.append(kpi)
            imgNames.append(imageName)
        animation = data_IO.str2bool(metrichash['animation'])
        if animation:
            imgTitles.append(kpi+'_animation')
            imgNames.append(metrichash['animationName'])

    return imgTitles, imgNames


def getOutputParamsStatListOld(outputParamsFileAddress, outputParamNames,
                            stats2include=['ave', 'min', 'max']):
    # If the outputParamsFileAddress exists, read the output variables and their desired stats from file
    if outputParamsFileAddress:
        foutParams = data_IO.open_file(outputParamsFileAddress, 'r')
        allDesiredOutputs = foutParams.read()
        allDesiredOutputs = allDesiredOutputs.splitlines()

        # First get the name of parameters to read from metric extraction csv files
        outParamsFromCSV = allDesiredOutputs[0]
        outParamsFromCSV = outParamsFromCSV.split(',')
        # Make sure all the varialbes in outputParamsList exist in outputParamNames:
        outParamsList_existIncsv = []
        for param in outParamsFromCSV:
            paramName = param[:param.find("(")]
            if paramName in outputParamNames:
                outParamsList_existIncsv.append(param)
        outParamsList = outParamsList_existIncsv

        # Read parameters from other files if provided
        # The format is:
        # outputName;outputFileNameTemplate;outputFlag;delimitor;locationInFile
        #
        # For example:
        # pressure_drop;results/case_{:d}_pressure_drop.txt;;" ";1
        #
        outParamsFromOtherFiles = []
        for line in allDesiredOutputs[1:]:
            if line:
                outputReadParams = line.split(";")
                outParamsFromOtherFiles.append(outputReadParams[0])
        outParamsList.extend(outParamsFromOtherFiles)

    else:
        outParamsList =[]
        for paramName in outputParamNames:
            for stat in stats2include:
                outParamsList.append(paramName+"("+stat+")")
    return outParamsList


def readOutParamsForCase(paramTable, csvTemplateName, caseNumber, zoneNumber, kpihash):

    outParamsList = []

    # Read values from the Metrics Extraction file first
    readMEXCSVFile = False

    if any(param[1] >= 0 for param in paramTable):
        readMEXCSVFile = True

    if readMEXCSVFile:
        PVcsvAddress = csvTemplateName.format(caseNumber, zoneNumber)
        fPVcsv = data_IO.open_file(PVcsvAddress, 'r')

    for param in paramTable:
        if param[1] >= 0: # Read the parameters from a Mex (Paraview) .csv file
            param_icase = data_IO.read_float_from_file_pointer(
                fPVcsv, param[0], ',', param[1])
        else:  # Read parameters from other files if provided
            metrichash = kpihash[param[0]]
            dataFile = metrichash['resultFile'].format(caseNumber, zoneNumber)
            dataFileParamFlag = metrichash['DEXoutputFlag']
            dataFileDelimiter = metrichash['delimiter']
            if not dataFileDelimiter:
                dataFileDelimiter = None
            locnInOutFile = int(metrichash['locationInFile']) - 1  # Start from 0
            fdataFile = data_IO.open_file(dataFile, 'r')
            param_icase = data_IO.read_float_from_file_pointer(
                fdataFile, dataFileParamFlag, dataFileDelimiter, locnInOutFile)
            fdataFile.close()
        outParamsList.append(str(param_icase))

    if readMEXCSVFile:
        fPVcsv.close()
    return outParamsList


def writeOutParamVals2caselist(cases, zone_cases, csvTemplateName, paramTable, caselist,
                               kpihash):

    # Read the desired metric from output file(s) for each case and each zone
    case_count = 0
    for icase, izone in it.product(range(len(cases)), range(len(zone_cases))):
        outparamList = readOutParamsForCase(paramTable, csvTemplateName, icase,
                                            izone, kpihash)
        caselist[case_count] += "," + ",".join(outparamList)
        case_count = case_count + 1


    return caselist


def writeImgs2caselist(cases, zone_cases, imgNames, basePath, pngsDirRel2BasePath,
                       caselist):
    # for icase, case in enumerate(cases):
    case_count = 0
    for icase, izone in it.product(range(len(cases)), range(len(zone_cases))):

        caseOutStr = ""
        for imageNameTemplate in imgNames:
            imageName = imageNameTemplate.format(icase, izone)

            caseOutStr += "," + os.path.join(basePath, pngsDirRel2BasePath.format(icase),
                                             imageName)
        caselist[case_count] += caseOutStr
        case_count = case_count + 1
    return caselist


def writeDesignExplorerCSVfile(deCSVFile, header, caselist):
    f = open(deCSVFile, "w")
    f.write(header + '\n')
    casel = "\n".join(caselist)
    f.write(casel + '\n')
    f.close()


def mergeParamTypesParamValsDict(paramTypes, paramVals):
    paramsTypeVal = {}
    for param in paramTypes:
        paramsTypeVal[param] = {'value':paramVals[param], 'type':paramTypes[param]}
    return paramsTypeVal


def merge_cases(case_1, case_2):
    merged_cases = []
    for i in it.product(case_1,case_2):
        merged_cases.append(i[0]+i[1])
    return merged_cases


def writeXMLPWfile(case, paramTypes, xmlFile, helpStr = 'Whitespace delimited or range/step (e.g. min:max:step)',
                   paramUnits=[]):
    """Write the input section of the xml file for generating input forms on the Parallel Works platform"""

    paramVals = convertListOfDicts2Dict(case)
    # sort the keys by parameter types:
    paramsBytype = {}
    paramsSortedBytype = sorted(paramTypes.items())
    paramsTypeVal = mergeParamTypesParamValsDict(paramTypes, paramVals)
    paramsTypeVal = OrderedDict(sorted(paramsTypeVal.items()))

    print(list(paramVals.keys()))
    unitStr = ""
    f = data_IO.open_file(xmlFile, "w")

    # Write the xml file header:
    f.write("<tool id=\'test_params_forms\' name=\'test_params_forms\'>  \n"
            "\t<command interpreter=\'swift\'>main.swift</command>     \n"
            "\t<inputs>  \n")

    paramTypes = set(paramTypes.values())
    # Write the parameters of each type under a section
    expanded = 'true'
    for sectionName in paramTypes:
        # Write the section header
        # e.g.    <section name='design_space' type='section' title='Cyclone Geometry Parameter Space' expanded='true'>
        f.write("\t\t<section name=\'" + sectionName + "\' type=\'section\' title='" +
                sectionName.capitalize() +" Parameters\' expanded=\'" + expanded + "\'> \n")
        expanded = 'false'
        for paramName in paramsTypeVal:
            paramDict = paramsTypeVal[paramName]
            if paramUnits:
                if paramUnits[paramName]:
                    unitStr = " (" + paramUnits[paramName] + ")"
                else:
                    unitStr = ""
            if paramDict['type'] == sectionName:
                pVal = paramDict['value']
                paramLabel = re.sub(r"(\w)([A-Z])", r"\1 \2", paramName)
                paramLabel = data_IO.upperfirst(paramLabel)
                f.write("\t\t\t<param name=\'"+ paramName + "\' type=\'text\' value=\'" + str(pVal) +
                        "\' label=\'" + paramLabel + unitStr +"\' help=\'" + helpStr + "\' width=\'33.3%\' argument=\'"
                        + sectionName + "\'>\n")
                f.write("\t\t\t</param>\n")
        f.write("\t\t</section> \n")
    f.write("\t</inputs> \n")
    f.write("</tool> \n")
    f.close()
    return paramsBytype
