import sys
import paramUtils


if len(sys.argv) < 3:
    print("Number of provided arguments: ", len(sys.argv) - 1)
    print("Usage: python preinputs.py  <sweep.run>  <output_casesListFile>")
    sys.exit()


paramsFile = sys.argv[1]
casesListFile = sys.argv[2]

cases = paramUtils.readCases(paramsFile, paramsdelimiter="|")[0]

print("Generated "+str(len(cases))+" Cases")

caselist = paramUtils.generate_caselist(cases, pnameValDelimiter=',')

casel = "\n".join(caselist)

f = open(casesListFile, "w")
f.write(casel)
f.close()
