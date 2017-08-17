import math
import sys
import itertools as it
import data_IO
import json
from collections import OrderedDict

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def frange(a, b, inc):
    if isInt(a) and isInt(b) and isInt(inc):
        a = int(a)
        b = int(b)
        inc = int(inc)
    else:
        a = float(a)
        b = float(b)
        inc = float(inc)
    x = [a]
    for i in range(1, int(math.ceil(((b + inc) - a) / inc))):
        x.append(a + i * inc)
    return (str(e) for e in x)


def expandVars(v, RangeDelimiter = ':'):
    min = v.split(RangeDelimiter)[0]
    max = v.split(RangeDelimiter)[1]
    step = v.split(RangeDelimiter)[2]
    v = ','.join(frange(min, max, step))
    return v

def readCases(params, namesdelimiter=";", valsdelimiter="_",paramsdelimiter = "\n", withParamType = True):
    with open(params) as f:
        content = f.read().split(paramsdelimiter)
        if content[-1] == "\n":
            del content[-1]

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
                pval = expandVars(pval).split(",")
            else:
                pval = [pval]
            pvals[pname] = pval
            if withParamType:
                pTypes[pname] = pType

    varNames = sorted(pvals)
    cases = [[{varName: val} for varName, val in zip(varNames, prod)] for prod in
             it.product(*(pvals[varName] for varName in varNames))]
    return cases, varNames, pTypes


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


def readcasesfromcsv(casesFile,paramValDelim=','):
    f = open(casesFile, "r")
    cases = []
    for i, line in enumerate(f):
        data = [l.replace("\n", "") for l in line.split(",")]
        # Combine the parameter labels and their values, if "," is used as delimiter
        # between them also.
        span = 2
        if paramValDelim == ',':
            data = [",".join(data[i:i+span]) for i in range(0, len(data), span)]
        case = []
        for ii, v in enumerate(data):
            param = {v.split(paramValDelim)[0]: v.split(paramValDelim)[1]}
            case.append(param)
        cases.append(case)
    f.close()
    return cases


def readParamsFile(paramsFile, paramValDelim=','):
    paramsFileType = getParamTypeFromfileAddress(paramsFile)
    if paramsFileType == 'paramFile':
        cases = readCases(paramsFile)
    else:
        cases = readcasesfromcsv(paramsFile, paramValDelim)
    return cases


def generateHeader(inputParamNames, outParamTables, outImgList):
    num2statTable = {0:'ave', 1:'min', 2:'max'}
    header = []
    for varName in inputParamNames:
        header += "in:" + varName + ","
    header = "".join(header[:-1])
    for paramNameStat in outParamTables:
        outStr = ",out:" + paramNameStat[0]
        if paramNameStat[1] >= 0:
            outStr += "_" + num2statTable[paramNameStat[1]]
        header += outStr
    for pngFile in outImgList:
        header += ",img:" + pngFile
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


def getOutputParamsFromKPI(kpiFile):
    fp_jsonIn = data_IO.open_file(kpiFile)
    kpihash = json.load(fp_jsonIn, object_pairs_hook=OrderedDict)
    orderPreservedKeys = data_IO.byteify(list(kpihash.keys()))
    kpihash = data_IO.byteify(kpihash)
    fp_jsonIn.close()
    outputParams= []
    for kpi in orderPreservedKeys:
        metrichash = kpihash[kpi]
        kpitype = metrichash['type']

        if kpitype == "StreamLines":
            metrichash['extractStats'] = "False"

        if 'extractStats' in metrichash:
            extractStats = data_IO.str2bool(metrichash['extractStats'])
        else:
            extractStats = True

        if extractStats:
            outputParams.append(kpi)
    return outputParams


def getOutImgsFromKPI(kpiFile):
    fp_jsonIn = data_IO.open_file(kpiFile)
    kpihash = json.load(fp_jsonIn, object_pairs_hook=OrderedDict)
    orderPreservedKeys = data_IO.byteify(list(kpihash.keys()))
    kpihash = data_IO.byteify(kpihash)
    fp_jsonIn.close()
    outputPNGs= []
    outputPNG_types = []
    for kpi in orderPreservedKeys:
        metrichash = kpihash[kpi]
        if 'image' in metrichash:
            kpiimage = metrichash['image']
        else:
            kpiimage = "None"

        if kpiimage != "None" and kpiimage != "":
            outputPNGs.append(kpi)
            outputPNG_types.append(kpiimage)
    return outputPNGs,outputPNG_types


def getOutputParamsStatList(outputParamsFileAddress, outputParamNames, stats2include=['ave','min','max']):
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
        # pressure_drop;results/case_@@i@@_pressure_drop.txt;;" ";1
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


def genOutputLookupTable(outParamsList):
    lookupTable = []
    stat2numTable = {'ave': 0, 'min': 1, 'max': 2}
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


def writeOutputParamVals2caselist(cases, csvTemplateName, paramTable, caselist,
                                  outputParamsFileAddress ):
    # Read the desired metric from each output file
    for icase, case in enumerate(cases):
        # Read values from the Metrics Extraction file first
        if csvTemplateName:
            extractedFile = csvTemplateName.replace("@@i@@", str(icase))
            fcaseMetrics = data_IO.open_file(extractedFile, 'r')
            caseOutStr = ""

            for param in paramTable:
                if param[1] >=0:
                    param_icase = data_IO.read_float_from_file_pointer(fcaseMetrics, param[0],
                                                                   ',', param[1])
                    caseOutStr += "," + str(param_icase)
            caselist[icase] += caseOutStr
            fcaseMetrics.close()
        if outputParamsFileAddress:
            foutParams = data_IO.open_file(outputParamsFileAddress, 'r')
            allDesiredOutputs = foutParams.read()
            allDesiredOutputs = allDesiredOutputs.splitlines()
            # Read parameters from other files if provided
            # The format is:
            # outputName;outputFileNameTemplate;outputFlag;delimitor;locationInFile
            #
            # For example:
            # pressure_drop;results/case_@@i@@_pressure_drop.txt;;" ";1

            # outputName;outputFileNameTemplate;delimitor;locationInFile
            #
            # For example:
            # pressure_drop;results/case_@@i@@_pressure_drop.txt; ;1

            for param in paramTable:
                caseOutStr = ""
                if param[1] == -1:
                    outFile = data_IO.read_str_from_strList(allDesiredOutputs,param[0], ";", 0, 0)
                    outFile = outFile.replace("@@i@@", str(icase))
                    foutFile = data_IO.open_file(outFile,'r')
                    outFileParamFlag = data_IO.read_str_from_strList(allDesiredOutputs,param[0], ";", 1, 0)
                    outFileDelimiter = data_IO.read_str_from_strList(allDesiredOutputs,param[0], ";", 2, 0)[1]
                    locnInOutFile = int(data_IO.read_str_from_strList(allDesiredOutputs,param[0], ";", 3, 0))
                    param_icase = data_IO.read_float_from_file_pointer(foutFile, outFileParamFlag,
                                                                       outFileDelimiter, locnInOutFile)
                    caseOutStr += "," + str(param_icase)
            caselist[icase] += caseOutStr

    return caselist


def writeImgs2caselist(cases, outImgList, imgTypes, basePath, pngsDirRel2BasePath, caselist):
    for icase, case in enumerate(cases):
        caseOutStr = ""
        for iPng, pngFile in enumerate(outImgList):
            if imgTypes[iPng] == "plot":
                imgPrefix = "plot_"
            else:
                imgPrefix = "out_"

            caseOutStr += "," + basePath + "/" + pngsDirRel2BasePath + str(icase) + "/" + imgPrefix + pngFile + ".png"
        caselist[icase] += caseOutStr
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


def writeXMLPWfile(case, paramTypes, xmlFile, helpStr = 'Whitespace delimited or range/step (e.g. min:max:step)',
                   paramUnits=[]):
    """Write the input section of the xml file for generating input forms on the Parallel Works platform"""

    paramVals = convertListOfDicts2Dict(case)
    # sort the keys by parameter types:
    paramsBytype = {}
    paramsSortedBytype = sorted(paramTypes.items())
    paramsTypeVal = mergeParamTypesParamValsDict(paramTypes, paramVals)

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
                f.write("\t\t\t<param name=\'"+ paramName + "\' type=\'text\' value=\'" + str(pVal) +
                        "\' label=\'" + paramName + unitStr +"\' help=\'" + helpStr + "\' width=\'33.3%\' argument=\'"
                        + sectionName + "\'>\n")
                f.write("\t\t\t</param>\n")
        f.write("\t\t</section> \n")
    f.write("\t</inputs> \n")
    f.write("</tool> \n")
    f.close()
    return paramsBytype
