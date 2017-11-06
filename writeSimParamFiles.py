import sys
import data_IO

# Input arguments:

if len(sys.argv) < 4:
    print("Number of provided arguments: ", len(sys.argv) - 1)
    print("Usage: python writeSimParamFiles <cases.list> <simFilesDir> <simFileRootName>")
    sys.exit()


caseListFileName = sys.argv[1]
simFilesDir = sys.argv[2]
simFileRootName = sys.argv[3]


cl_fp = data_IO.open_file(caseListFileName)
for i, line in enumerate(cl_fp):
    line = line.replace(",", "\n")
    line = line.replace("=", "  ")
    simFileAddress = simFilesDir + "/" + simFileRootName + str(i) + ".in"
    simf = data_IO.open_file(simFileAddress, "w")
    simf.write(line)
    simf.write("\n")
    simf.close()

cl_fp.close()
