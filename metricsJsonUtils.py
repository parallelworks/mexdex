import data_IO
import json
import warnings

from collections import OrderedDict


def readKPIJsonFile(kpiFile):
    fp_jsonIn = data_IO.open_file(kpiFile)
    kpihash = json.load(fp_jsonIn, object_pairs_hook=OrderedDict)
    orderPreservedKeys = data_IO.byteify(list(kpihash.keys()))
    kpihash = data_IO.byteify(kpihash)
    fp_jsonIn.close()
    return kpihash, orderPreservedKeys

# def check_key_value(key, value):
#     """Raise exception if a key value doesn't belongs to a given set.
#     """
#     if value not in acceptable_vals:
#         raise ValueError("")


def set_extract_time_defaults(metrichash, kpi, timesteps_key, times_key):
    if not (timesteps_key in metrichash):
        metrichash[timesteps_key] = None
    if not (times_key in metrichash):
        metrichash[times_key] = None

    # Use metrichash[timesteps_key] if both timesteps_key and
    # times_key are given
    if (metrichash[timesteps_key] is not None) and (metrichash[times_key] is not None):
        warnings.warn("Only set one of \"extractStatsTimeSteps\" or "
                      "\"extractStatsTimes\" fields for " + kpi +
                      ". Using \"extractStatsTimeSteps\".")

        # If none of them is provided set to default (last time step)
    elif (metrichash[timesteps_key] is None) and (metrichash[times_key] is None):
            metrichash[timesteps_key] = 'last'


def setKPIFieldDefaults(metrichash, kpi, caseNumber=""):
    if not ('IsParaviewMetric' in metrichash):
        metrichash['IsParaviewMetric'] = 'True'

    # Do not continue if a multi-filter paraview Metric:
    if data_IO.str2bool(metrichash['IsParaviewMetric']):
        if not ('MultiFilter' in metrichash):
            metrichash['MultiFilter'] = 'False'
        if data_IO.str2bool(metrichash['MultiFilter']):
            return metrichash

    if not ('sense' in metrichash):
        metrichash['sense'] = None

    # Set component to "Magnitude" if not given for vector/tensor fields
    if not ('field' in metrichash):
        metrichash['field'] = 'None'
        metrichash['fieldComponent'] = 'None'


    if not ('DEXoutputFlag' in metrichash):
        if data_IO.str2bool(metrichash['IsParaviewMetric']):
            metrichash['DEXoutputFlag'] = 'all'
        else:
            metrichash['DEXoutputFlag'] = ''

    # If not a Paraview Metric, make sure the information for extracting
    # data/images from a generic file is provided.
    if not data_IO.str2bool(metrichash['IsParaviewMetric']):
        if metrichash['DEXoutputFlag'].lower() == "image":
            if not ('imageName' in metrichash):
                metrichash['imageName'] = "out_" + kpi + ".png"

        if metrichash['DEXoutputFlag'].lower() == "animation":
            if not ('animation' in metrichash):
                metrichash['animation'] = 'True'
            if not data_IO.str2bool(metrichash['animation']):
                warnings.warn('Setting {}.animation to True'.format(kpi))
                metrichash['animation'] = 'True'
            if not ('animationName' in metrichash):
                metrichash['animationName'] = "out_" + kpi + ".gif"
        else:
            metrichash['animation'] = 'False'

        if not(metrichash['DEXoutputFlag'].lower() in {"none", "image", "animation"}):
            if not ('resultFile' in metrichash):
                warningMsg = 'Please provide resultFile for {}. Setting ' \
                             '{}.DEXoutputFlag to "none".'.format(kpi, kpi)
                warnings.warn(warningMsg)
                metrichash['DEXoutputFlag'] = 'none'
            if not ("delimiter" in metrichash):
                metrichash["delimiter"] = ""
            if not ("locationInFile" in metrichash):
                metrichash["locationInFile"] = "1"
        return metrichash

    # Set default image properties
    if not ('image' in metrichash):
        metrichash['image'] = 'None'
        metrichash['imageName'] = 'None'
    if not ('bodyopacity' in metrichash):
        metrichash['bodyopacity'] = "0.3"
    if not ('min' in metrichash):
        metrichash['min'] = 'auto'
    if not ('max' in metrichash):
        metrichash['max'] = 'auto'
    if not ('discretecolors' in metrichash):
        metrichash['discretecolors'] = '20'
    if not ('colorscale' in metrichash):
        metrichash['colorscale'] = 'Blue to Red Rainbow'
    if not ('invertcolor' in metrichash):
        metrichash['invertcolor'] = 'False'
    if not ('opacity' in metrichash):
        metrichash['opacity'] = "1"
    if not ('representationType' in metrichash):
        metrichash['representationType'] = 'Surface'
    if not ('per-pass' in metrichash):
        metrichash['per-pass'] = "true"


    if not('image' == 'None'):
        # Set image time(s)
        set_extract_time_defaults(metrichash, kpi, "imageTimeSteps", "imageTimes")
        # Set image name
        if not ('imageName' in metrichash):
            if metrichash['image'] == "plot":
                metrichash['imageName'] = "plot_" + kpi + ".png"
            else:
                metrichash['imageName'] = "out_" + kpi + ".png"

    # Set default streamline properties
    if metrichash['type'] == "StreamLines":
        if not ('seedType' in metrichash):
            metrichash['seedType'] = 'Line'

    if not('extractStats' in metrichash):
        if metrichash['field'] == 'None':
            metrichash['extractStats'] = 'False'
        else:
            metrichash['extractStats'] = 'True'

    if not('temporalStats' in metrichash):
        metrichash['temporalStats'] = 'False'

    set_extract_time_defaults(metrichash, kpi,
                              "extractStatsTimeSteps", "extractStatsTimes")

    if not data_IO.str2bool(metrichash['extractStats']):
        metrichash['DEXoutputFlag'] = 'none'

    if not ('animation' in metrichash):
        metrichash['animation'] = 'False'

    if data_IO.str2bool(metrichash['animation']):
        if not ('animationName' in metrichash):
            metrichash['animationName'] = "out_" + kpi + ".gif"

    if not ('blender' in metrichash):
        metrichash['blender'] = 'False'
    else:
        try:
            metrichash['blendercontext'] = metrichash['blendercontext'].split(",")
        except:
            metrichash['blendercontext'] = []
        try:
            metrichash['blenderbody'] = metrichash['blenderbody'].split(",")
        except:
            metrichash['blenderbody'] = False

    if metrichash['type'] == "WarpByVector":
        metrichash['extractStats'] = 'False'
        if not ('scaleFactor' in metrichash):
            metrichash['scaleFactor'] = 1

    return metrichash
