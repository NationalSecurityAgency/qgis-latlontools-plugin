"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .tomgrs import ToMGRSAlgorithm
from .mgrstogeom import MGRStoLayerlgorithm
from .pluscodes import ToPlusCodesAlgorithm, PlusCodes2Layerlgorithm
from .geom2field import Geom2FieldAlgorithm
from .field2geom import Field2GeomAlgorithm
from .geom2wkt import Geom2WktAlgorithm
from .wkt2layers import Wkt2LayersAlgorithm
from .ecef import LatLonToEcefAlgorithm, EcefLatLonToAlgorithm


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
        self.addAlgorithm(Geom2WktAlgorithm())
        self.addAlgorithm(Wkt2LayersAlgorithm())
        self.addAlgorithm(LatLonToEcefAlgorithm())
        self.addAlgorithm(EcefLatLonToAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/copyicon.svg')

    def id(self):
        return 'latlontools'

    def name(self):
        return 'Lat Lon tools'

    def longName(self):
        return self.name()
