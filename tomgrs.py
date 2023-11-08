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

from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsFields, QgsField, QgsFeature, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink)

from . import mgrs
from .util import tr


class ToMGRSAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to convert a point layer to a MGRS field.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    PrmInputLayer = 'InputLayer'
    PrmMgrsFieldName = 'MgrsFieldName'
    PrmMgrsPrecision = 'MgrsPrecision'
    PrmOutputLayer = 'OutputLayer'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInputLayer,
                tr('Input point vector layer'),
                [QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmMgrsFieldName,
                tr('Output MGRS field name'),
                defaultValue='mgrs')
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmMgrsPrecision,
                tr('MGRS Precision'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=5,
                optional=False,
                minValue=0,
                maxValue=5)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                tr('Output layer'))
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        mgrs_name = self.parameterAsString(parameters, self.PrmMgrsFieldName, context).strip()
        precision = self.parameterAsInt(parameters, self.PrmMgrsPrecision, context)

        fieldsout = QgsFields(source.fields())

        if fieldsout.append(QgsField(mgrs_name, QVariant.String)) is False:
            msg = "{} '{}'".format(tr('MGRS Field Name must be unique. There is already a field named'), mgrs_name)
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

        layerCRS = source.sourceCrs()
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer,
            context, fieldsout, source.wkbType(), layerCRS)

        # The input to the mgrs conversions requires latitudes and longitudes
        # If the layer is not EPSG:4326 we need to convert it.
        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        if layerCRS != epsg4326:
            transform = QgsCoordinateTransform(layerCRS, epsg4326, QgsProject.instance())

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            pt = feature.geometry().asPoint()
            if layerCRS != epsg4326:
                pt = transform.transform(pt)
            try:
                msg = mgrs.toMgrs(pt.y(), pt.x(), precision)
            except Exception:
                msg = ''
            f = QgsFeature()
            f.setGeometry(feature.geometry())
            f.setAttributes(feature.attributes() + [msg])
            sink.addFeature(f)
            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'point2mgrs'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/point2mgrs.svg')

    def displayName(self):
        return tr('Point layer to MGRS')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def shortHelpString(self):
        file = os.path.dirname(__file__) + '/doc/geom2mgrs.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return ToMGRSAlgorithm()
