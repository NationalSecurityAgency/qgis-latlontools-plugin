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
from qgis.core import (
    QgsFields, QgsField,
    QgsFeature, QgsGeometry, QgsPointXY,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsProject, QgsWkbTypes)

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingParameterNumber,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink)

from . import olc
from .util import tr


class ToPlusCodesAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to convert a point layer to a Plus codes field.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    PrmInputLayer = 'InputLayer'
    PrmPlusCodesFieldName = 'PlusCodesFieldName'
    PrmPlusCodesLength = 'PlusCodesLength'
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
                self.PrmPlusCodesFieldName,
                tr('Plus Codes field name'),
                defaultValue='pluscodes')
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmPlusCodesLength,
                tr('Plus Codes length'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=11,
                optional=False,
                minValue=10,
                maxValue=olc.MAX_DIGIT_COUNT_)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                tr('Output layer'))
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        field_name = self.parameterAsString(parameters, self.PrmPlusCodesFieldName, context).strip()
        plusCodesLength = self.parameterAsInt(parameters, self.PrmPlusCodesLength, context)

        fieldsout = QgsFields(source.fields())

        if fieldsout.append(QgsField(field_name, QVariant.String)) is False:
            msg = "{} '{}'".format(tr('Plus Codes Field Name must be unique. There is already a field named'), field_name)
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

        layerCRS = source.sourceCrs()
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer,
            context, fieldsout, source.wkbType(), layerCRS)

        # The input to the plus codes conversions requires latitudes and longitudes
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
                msg = olc.encode(pt.y(), pt.x(), plusCodesLength)
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
        return 'point2pluscodes'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/pluscodes.svg')

    def displayName(self):
        return tr('Point layer to Plus Codes')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def shortHelpString(self):
        file = os.path.dirname(__file__) + '/doc/geom2pluscodes.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return ToPlusCodesAlgorithm()


class PlusCodes2Layerlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to convert a layer with a Plus Codes field into a point layer.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    PrmInputLayer = 'InputLayer'
    PrmPlusCodesField = 'PlusCodesField'
    PrmOutputLayer = 'OutputLayer'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInputLayer,
                tr('Input vector layer or table'),
                [QgsProcessing.TypeVector])
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmPlusCodesField,
                tr('Field containing Plus Code coordinate'),
                defaultValue='pluscodes',
                parentLayerParameterName=self.PrmInputLayer,
                type=QgsProcessingParameterField.String)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                tr('Output layer'))
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        pluscodesfieldname = self.parameterAsString(parameters, self.PrmPlusCodesField, context)
        if not pluscodesfieldname:
            msg = tr('Select a Plus Codes field to process')
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer,
            context, source.fields(), QgsWkbTypes.Point, epsg4326)

        featureCount = source.featureCount()
        total = 100.0 / featureCount if featureCount else 0
        badFeatures = 0

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            m = feature[pluscodesfieldname].strip()
            try:
                coord = olc.decode(m)
                lat = coord.latitudeCenter
                lon = coord.longitudeCenter
            except Exception:
                # traceback.print_exc()
                badFeatures += 1
                continue
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            f.setAttributes(feature.attributes())
            sink.addFeature(f)

            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))

        if badFeatures > 0:
            msg = "{} {} {} {}".format(featureCount - badFeatures, tr('out of'), featureCount, tr('features contained Plus Codes coordinates'))
            feedback.pushInfo(msg)

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'pluscodes2point'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/pluscodes.svg')

    def displayName(self):
        return tr('Plus Codes to point layer')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def shortHelpString(self):
        file = os.path.dirname(__file__) + '/doc/pluscodes2point.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return PlusCodes2Layerlgorithm()
