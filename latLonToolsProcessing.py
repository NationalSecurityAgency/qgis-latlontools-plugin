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
