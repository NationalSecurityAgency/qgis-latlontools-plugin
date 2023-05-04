def classFactory(iface):
    if iface:
        from .latLonTools import LatLonTools
        return LatLonTools(iface)
    else:
        from .latLonToolsProcessing import LatLonTools
        return LatLonTools()
