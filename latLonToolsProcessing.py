from qgis.core import QgsApplication

from .latLonFunctions import InitLatLonFunctions, UnloadLatLonFunctions
from .settings import settings
from .provider import LatLonToolsProvider


class LatLonTools:

    def __init__(self):
        self.provider = None

    def initProcessing(self):
        self.provider = LatLonToolsProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)
        InitLatLonFunctions()

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        UnloadLatLonFunctions()
