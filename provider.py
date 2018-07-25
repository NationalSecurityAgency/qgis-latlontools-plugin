import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .tomgrs import ToMGRSAlgorithm
from .mgrstogeom import MGRStoLayerlgorithm
from .pluscodes import ToPlusCodesAlgorithm, PlusCodes2Layerlgorithm

class LatLonToolsProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(PlusCodes2Layerlgorithm())
        self.addAlgorithm(ToPlusCodesAlgorithm())
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
