import sys
import data_IO
import json
import paramUtils

if len(sys.argv) < 3:
    print("Number of provided arguments: ", len(sys.argv) - 1)
    print("Usage: python writeParams2xml.py  <sweep.run>  <xmlFile> "
          "[paramUnits.json]")
    sys.exit()


paramsFile = sys.argv[1]
xmlFile = sys.argv[2]

paramUnitsFile = data_IO.setOptionalSysArgs(sys.argv, [], 3)

cases, _, paramTypes = paramUtils.readCases(paramsFile, paramsdelimiter="|")

print("Generated " + str(len(cases)) + " Cases")
print(paramTypes)

# Read the parameters units from the paramUnitsFile file:
paramUnits = []
if paramUnitsFile:
    fp_jsonIn = data_IO.open_file(paramUnitsFile)
    paramUnits = json.load(fp_jsonIn)
    fp_jsonIn.close()
    print(paramUnits)

paramUtils.writeXMLPWfile(cases[0],paramTypes, xmlFile, paramUnits=paramUnits)

