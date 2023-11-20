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

from qgis.core import (
    QgsPointXY, QgsGeometry, QgsField,
    QgsProject, QgsWkbTypes, QgsPropertyDefinition)

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameters,
    QgsProcessingFeatureBasedAlgorithm,
    QgsProcessingParameterEnum)

from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.PyQt.QtGui import QIcon
from .util import tr


class Geom2WktAlgorithm(QgsProcessingFeatureBasedAlgorithm):
    """
    Algorithm to create a circle shape.
    """

    wkt_type = 0 # WKT
    PrmFormat = 'Format'

    def createInstance(self):
        return Geom2WktAlgorithm()

    def name(self):
        return 'geom2wkt'

    def displayName(self):
        return tr('Geometry to WKT/JSON')

    def outputName(self):
        return tr('Output layer')

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/geom2wkt.svg')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def shortHelpString(self):
        file = os.path.dirname(__file__) + '/doc/geom2wkt.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help

    def inputLayerTypes(self):
        return [QgsProcessing.TypeVectorAnyGeometry]

    def outputWkbType(self, input_wkb_type):
        return (input_wkb_type)

    def outputFields(self, input_fields):
        if self.wkt_type == 0:
            str = '_wkt'
        elif self.wkt_type == 1:
            str = '_ewkt'
        else:
            str = '_json'
            
        input_fields.append(QgsField(str, QVariant.String))
        return(input_fields)

    def  supportInPlaceEdit(self, layer):
        return False

    def initParameters(self, config=None):
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmFormat,
                tr('Output format type'),
                options=['WKT', 'EWKT', 'JSON'],
                defaultValue=0,
                optional=False)
        )

    def prepareAlgorithm(self, parameters, context, feedback):
        self.wkt_type = self.parameterAsInt(parameters, self.PrmFormat, context)
        source = self.parameterAsSource(parameters, 'INPUT', context)
        try:
            crs = source.sourceCrs()
            authid = crs.authid()
            self.auth, self.srid = authid.split(':')
            if self.auth != 'EPSG':
                self.srid = -1
        except Exception:
            self.sring = -1
        return True

    def processFeature(self, feature, context, feedback):
        if self.wkt_type == 0:
            str = feature.geometry().asWkt()
        elif self.wkt_type == 1:
            str = feature.geometry().asWkt()
            str = 'SRID={};{}'.format(self.srid, str)
        else:
            str = feature.geometry().asJson()
        attr = feature.attributes()
        attr.append(str)
        feature.setAttributes(attr)
        return [feature]
