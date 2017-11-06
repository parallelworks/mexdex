import sys
import data_IO
import paramUtils

# Input arguments:

if len(sys.argv) < 4:
    print("Number of provided arguments: ", len(sys.argv) - 1)
    print("Usage: python writeSimParamFiles <cases.list> <simFilesDir> <simFileRootName>")
    sys.exit()


caseListFileName = sys.argv[1]
simFilesDir = sys.argv[2]
simFileRootName = sys.argv[3]

cases = paramUtils.readParamsFile(caseListFileName)

for i, caseParams in enumerate(cases):
    line = ''
    for iParamValDict in caseParams:
        print(iParamValDict)
        line += (list(iParamValDict.keys())[0] + ' ' +
                  list(iParamValDict.values())[0] + '\n')
    print(type(caseParams))
    print(caseParams)
    simFileAddress = simFilesDir + "/" + simFileRootName + str(i) + ".in"
    simf = data_IO.open_file(simFileAddress, "w")
    simf.write(line)
    simf.write("\n")
    simf.close()

