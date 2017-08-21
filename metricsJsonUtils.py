import data_IO


def setKPIFieldDefaults(metrichash):

    # Set component to "Magnitude" if not given for vector/tensor fields
    if not ('field' in metrichash):
        metrichash['field'] = 'None'
        metrichash['fieldComponent'] = 'None'

    if not ('IsParaviewMetric' in metrichash):
        metrichash['IsParaviewMetric'] = 'True'
    # If not a Paraview Metric, don't need to do anything
    if not data_IO.str2bool(metrichash['IsParaviewMetric']):
        return metrichash

    # Set default image properties
    if not ('image' in metrichash):
        metrichash['image'] = 'None'
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

    # Set default streamline properties
    if metrichash['type'] == "StreamLines":
        if not ('seedType' in metrichash):
            metrichash['seedType'] = 'Line'

    if not('extractStats' in metrichash):
        if metrichash['field'] == 'None':
            metrichash['extractStats'] = 'False'
        else:
            metrichash['extractStats'] = 'True'

    if not ('animation' in metrichash):
        metrichash['animation'] = 'False'

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

    return metrichash
