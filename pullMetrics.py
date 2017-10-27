
import sys
import paramUtils
import metricsJsonUtils

kpiFile=sys.argv[1]
out=sys.argv[2]

# Read the desired output metrics
# Read the kpihash and set the default values for missing fields
[kpihash, orderPreservedKeys] = metricsJsonUtils.readKPIJsonFile(kpiFile)
for kpi in kpihash:
    kpihash[kpi] = metricsJsonUtils.setKPIFieldDefaults(kpihash[kpi], kpi)

# Read the desired output metrics
outputParamNames = paramUtils.getOutputParamsFromKPI(kpihash, orderPreservedKeys, [])

outParams=[]
for i in outputParamNames:
    try:
        loc=kpihash[i[0]]['resultFile'].replace("{:d}","0")
        index=int(kpihash[i[0]]['locationInFile'])-1
        f = open(loc,'r')
        outParams.append(f.read().split()[index])
    except:
        pass

"""
outputParamNames = list(set(outputParamNames))
outputParamList = paramUtils.getOutputParamsStatList(outputParamStatsFile, outputParamNames,['ave', 'min', 'max'])
outParamTable = paramUtils.genOutputLookupTable(outputParamList)

outParams=[]
f = open(metricLocation,'r')
metrics = f.read().splitlines()
for metric in metrics:
    m=metric.split(",")
    for o in outParamTable:
        if o[0] == m[0]:
            outParams.append(m[o[1]+1])
f.close()
"""

f = open(out,'w')
f.write("\n".join(outParams))
f.write("\n")
f.close()
