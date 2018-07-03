import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .tomgrs import ToMGRSAlgorithm
from .mgrstogeom import MGRStoLayerlgorithm

class LatLonToolsProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

        # Load algorithms
        self.alglist = [MGRStoLayerlgorithm(),ToMGRSAlgorithm()]

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        for alg in self.alglist:
            self.addAlgorithm( alg )

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/copyicon.png')
        
    def id(self):
        return 'latlontools'

    def name(self):
        return 'Lat Lon tools'

    def longName(self):
        return self.name()