import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .tomgrs import ToMGRSAlgorithm
from .mgrstogeom import MGRStoLayerlgorithm

class LatLonToolsProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(MGRStoLayerlgorithm())
        self.addAlgorithm(ToMGRSAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/copyicon.png')
        
    def id(self):
        return 'latlontools'

    def name(self):
        return 'Lat Lon tools'

    def longName(self):
        return self.name()
