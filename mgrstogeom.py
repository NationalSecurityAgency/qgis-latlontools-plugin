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
import re

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsCoordinateReferenceSystem, QgsWkbTypes
# import traceback

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink)

from . import mgrs
from .util import tr


class MGRStoLayerlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to convert a layer with an MGRS field into a point layer.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    PrmInputLayer = 'InputLayer'
    PrmMgrsField = 'MgrsField'
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
                self.PrmMgrsField,
                tr('Field containing MGRS coordinate'),
                defaultValue='mgrs',
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
        mgrsfieldname = self.parameterAsString(parameters, self.PrmMgrsField, context)
        if not mgrsfieldname:
            msg = tr('Select an MGRS field to process')
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
            m = feature[mgrsfieldname]
            try:
                m = re.sub(r'\s+', '', str(m))  # Remove all white space
                lat, lon = mgrs.toWgs(m)
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
            msg = "{} {} {} {}".format(featureCount - badFeatures, tr('out of'), featureCount, tr('features contained MGRS coordinates'))
            feedback.pushInfo(msg)

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'mgrs2point'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/mgrs2point.svg')

    def displayName(self):
        return tr('MGRS to point layer')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def shortHelpString(self):
        file = os.path.dirname(__file__) + '/doc/mgrs2point.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return MGRStoLayerlgorithm()
