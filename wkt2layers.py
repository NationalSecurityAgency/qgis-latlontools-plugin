# -*- coding: utf-8 -*-
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
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsWkbTypes

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterCrs,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink)

from .util import tr

# import traceback

class Wkt2LayersAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to import KML and KMZ files.
    """
    PrmInput = 'Input Layer'
    PrmField = 'Field'
    PrmInputCRS = 'InputCRS'
    PrmPointOutputLayer = 'PointOutputLayer'
    PrmLineOutputLayer = 'LineOutputLayer'
    PrmPolygonOutputLayer = 'PolygonOutputLayer'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInput,
                tr('Input vector layer or table'),
                [QgsProcessing.TypeVector])
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmField,
                tr('Select a WKT coordinate field'),
                parentLayerParameterName=self.PrmInput,
                type=QgsProcessingParameterField.String,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.PrmInputCRS,
                tr('WKT CRS (Usually EPSG:4326)'),
                'EPSG:4326',
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmPointOutputLayer,
                tr('Output point layer'),
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmLineOutputLayer,
                tr('Output line layer'),
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmPolygonOutputLayer,
                tr('Output polygon layer'),
                optional=True)
        )

    def processAlgorithm(self, parameters, context, feedback):
        self.parameters = parameters
        self.context = context
        field_name = self.parameterAsString(parameters, self.PrmField, context)
        if not field_name:
            raise QgsProcessingException(tr('A String attribute field needs to be selected'))
        source = self.parameterAsSource(parameters, self.PrmInput, context)
        self.input_crs = self.parameterAsCrs(parameters, self.PrmInputCRS, context)

        skipPt = True if self.PrmPointOutputLayer not in parameters or parameters[self.PrmPointOutputLayer] is None else False
        skipline = True if self.PrmLineOutputLayer not in parameters or parameters[self.PrmLineOutputLayer] is None else False
        skipPoly = True if self.PrmPolygonOutputLayer not in parameters or parameters[self.PrmPolygonOutputLayer] is None else False
        self.cntPt = 0
        self.cntLine = 0
        self.cntPoly = 0

        self.fields = source.fields()

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        failed = 0

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))
            try:
                wkt_str = feature[field_name].strip()
                if wkt_str.startswith("GEOMETRYCOLLECTION"):
                    failed += 1
                    continue
                geom = QgsGeometry.fromWkt(wkt_str)
                if geom.isEmpty() or geom.isNull():
                    failed += 1
                    continue
                    
                type = geom.type()
                if type == QgsWkbTypes.PointGeometry:
                    self.addpoint(feature, geom)
                elif type == QgsWkbTypes.LineGeometry:
                    self.addline(feature, geom)
                elif type == QgsWkbTypes.PolygonGeometry:
                    self.addpolygon(feature, geom)
                else:
                    failed += 1
                    continue
                
            except Exception:
                '''s = traceback.format_exc()
                feedback.pushInfo(s)'''
                failed += 1


        feedback.pushInfo('{} points extracted'.format(self.cntPt))
        feedback.pushInfo('{} lines extracted'.format(self.cntLine))
        feedback.pushInfo('{} polygons extracted'.format(self.cntPoly))

        r = {}
        if self.cntPt > 0:
            r[self.PrmPointOutputLayer] = self.dest_id_pt
        if self.cntLine > 0:
            r[self.PrmLineOutputLayer] = self.dest_id_line
        if self.cntPoly > 0:
            r[self.PrmPolygonOutputLayer] = self.dest_id_poly

        return (r)

    def addpoint(self, feature, geom):
        if self.cntPt == 0:
            (self.sinkPt, self.dest_id_pt) = self.parameterAsSink(
                self.parameters,
                self.PrmPointOutputLayer, self.context, self.fields,
                QgsWkbTypes.MultiPoint, self.input_crs)

        if geom.isSimple():
            geom = geom.convertToType(QgsWkbTypes.PointGeometry, True)
        feature.setGeometry(geom)
        self.cntPt += 1
        self.sinkPt.addFeature(feature)

    def addline(self, feature, geom):
        if self.cntLine == 0:
            (self.sinkLine, self.dest_id_line) = self.parameterAsSink(
                self.parameters,
                self.PrmLineOutputLayer, self.context, self.fields,
                QgsWkbTypes.MultiLineString, self.input_crs)

        if geom.isSimple():
            geom = geom.convertToType(QgsWkbTypes.LineGeometry, True)
        feature.setGeometry(geom)
        self.cntLine += 1
        self.sinkLine.addFeature(feature)

    def addpolygon(self, feature, geom):
        if self.cntPoly == 0:
            (self.sinkPoly, self.dest_id_poly) = self.parameterAsSink(
                self.parameters,
                self.PrmPolygonOutputLayer, self.context, self.fields,
                QgsWkbTypes.MultiPolygon, self.input_crs)
        if geom.isSimple():
            geom = geom.convertToType(QgsWkbTypes.PolygonGeometry, True)
        feature.setGeometry(geom)
        self.cntPoly += 1
        self.sinkPoly.addFeature(feature)

    def name(self):
        return 'wkt2layers'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/wkt2layers.svg')

    def displayName(self):
        return tr('WKT attribute to layers')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return Wkt2LayersAlgorithm()
