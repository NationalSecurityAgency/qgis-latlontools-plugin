import os

from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider

from .field2geom import Field2GeomAlgorithm
from .geom2field import Geom2FieldAlgorithm
from .mgrstogeom import MGRStoLayerlgorithm
from .pluscodes import PlusCodes2Layerlgorithm, ToPlusCodesAlgorithm
from .tomgrs import ToMGRSAlgorithm


class LatLonToolsProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(PlusCodes2Layerlgorithm())
        self.addAlgorithm(ToPlusCodesAlgorithm())
        self.addAlgorithm(MGRStoLayerlgorithm())
        self.addAlgorithm(ToMGRSAlgorithm())
        self.addAlgorithm(Geom2FieldAlgorithm())
        self.addAlgorithm(Field2GeomAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/copyicon.png')

    def id(self):
        return 'latlontools'

    def name(self):
        return 'Lat Lon tools'

    def longName(self):
        return self.name()
