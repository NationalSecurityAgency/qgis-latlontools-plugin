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
import pyproj
from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    QgsFields, QgsField, QgsFeature, QgsWkbTypes, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsProject, QgsPoint, QgsGeometry)

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink)

from .util import tr

class LatLonToEcefAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to convert a point layer with altitude to an ECEF table.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    PrmInputLayer = 'InputLayer'
    PrmExtractFromZ = 'ExtractFromZ'
    PrmAltitudeField = 'AltitudeField'
    PrmXFieldName = 'XFieldName'
    PrmYFieldName = 'YFieldName'
    PrmZFieldName = 'ZFieldName'
    PrmDefaultAltitude = 'DefaultAltitude'
    PrmOutputLayer = 'OutputLayer'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInputLayer,
                tr('Input point vector layer'),
                [QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmExtractFromZ,
                tr('Extract altitude from Z geometry (must be meters) if available'),
                False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmAltitudeField,
                tr('Altitude attribute'),
                parentLayerParameterName=self.PrmInputLayer,
                type=QgsProcessingParameterField.Numeric,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmDefaultAltitude,
                tr('Default altitude in meters when not otherwise specified'),
                QgsProcessingParameterNumber.Double,
                defaultValue=0,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmXFieldName,
                tr('Output X attribute name'),
                defaultValue='X')
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmYFieldName,
                tr('Output Y attribute name'),
                defaultValue='Y')
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmZFieldName,
                tr('Output Z attribute name'),
                defaultValue='Z')
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                tr('Output layer'))
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        use_z_altitude = self.parameterAsBool(parameters, self.PrmExtractFromZ, context)
        if self.PrmAltitudeField not in parameters or parameters[self.PrmAltitudeField] is None:
            alt_field = None
        else:
            alt_field = self.parameterAsString(parameters, self.PrmAltitudeField, context)
        x_name = self.parameterAsString(parameters, self.PrmXFieldName, context).strip()
        y_name = self.parameterAsString(parameters, self.PrmYFieldName, context).strip()
        z_name = self.parameterAsString(parameters, self.PrmZFieldName, context).strip()
        default_altitude = self.parameterAsDouble(parameters, self.PrmDefaultAltitude, context)

        xyzfields = QgsFields()
        xyzfields.append(QgsField(x_name, QVariant.Double))
        xyzfields.append(QgsField(y_name, QVariant.Double))
        xyzfields.append(QgsField(z_name, QVariant.Double))
        for field in source.fields():
            xyzfields.append(field)

        layerCRS = source.sourceCrs()
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer, context, xyzfields,
            QgsWkbTypes.NoGeometry)

        # The input requires latitudes and longitudes
        # If the layer is not EPSG:4326 we need to convert it.
        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        if layerCRS != epsg4326:
            transform = QgsCoordinateTransform(layerCRS, epsg4326, QgsProject.instance())
        ecef = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
        lla = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
        
        hasz = QgsWkbTypes.hasZ(source.wkbType())

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            pt = feature.geometry().get()
            if use_z_altitude and hasz:
                alt = pt.z()
            elif alt_field:
                alt = float(feature[alt_field])
            else:
                alt = default_altitude
            if layerCRS != epsg4326:
                pt = transform.transform(pt)
            x,y,z = pyproj.transform(lla, ecef, pt.x(), pt.y(), alt, radians=False)
            f = QgsFeature()
            f.setAttributes([x,y,z] + feature.attributes())
            sink.addFeature(f)
            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'lla2ecef'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/ecef.png')

    def displayName(self):
        return tr('Lat, Lon, Altitude to ECEF')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    '''def shortHelpString(self):
        file = os.path.dirname(__file__) + '/doc/geom2mgrs.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help'''

    def createInstance(self):
        return LatLonToEcefAlgorithm()

class EcefLatLonToAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to convert a point layer with altitude to an ECEF table.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    PrmInputLayer = 'InputLayer'
    PrmXField = 'XField'
    PrmYField = 'YField'
    PrmZField = 'ZField'
    PrmAddZToAttributes = 'AddZToAttributes'
    PrmAltitudeFieldName = 'AltitudeFieldName'
    PrmOutputLayer = 'OutputLayer'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInputLayer,
                tr('Input layer'),
                [QgsProcessing.TypeVector])
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmXField,
                tr('ECEF X attribute (meters)'),
                parentLayerParameterName=self.PrmInputLayer,
                type=QgsProcessingParameterField.Numeric,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmYField,
                tr('ECEF Y attribute (meters)'),
                parentLayerParameterName=self.PrmInputLayer,
                type=QgsProcessingParameterField.Numeric,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmZField,
                tr('ECEF Z attribute (meters)'),
                parentLayerParameterName=self.PrmInputLayer,
                type=QgsProcessingParameterField.Numeric,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmAddZToAttributes,
                tr('Add altitude to the output attribute table'),
                False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmAltitudeFieldName,
                tr('Output altitude attribute name'),
                defaultValue='altitude',
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                tr('Output pointZ layer'))
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        x_field = self.parameterAsString(parameters, self.PrmXField, context)
        y_field = self.parameterAsString(parameters, self.PrmYField, context)
        z_field = self.parameterAsString(parameters, self.PrmZField, context)
        add_z = self.parameterAsBool(parameters, self.PrmAddZToAttributes, context)
        z_name = self.parameterAsString(parameters, self.PrmAltitudeFieldName, context).strip()

        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        fieldsout = QgsFields(source.fields())
        if add_z:
            if fieldsout.append(QgsField(z_name, QVariant.Double)) is False:
                raise QgsProcessingException(tr("Altitude attribute name must be unique"))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer, context, fieldsout,
            QgsWkbTypes.PointZ, epsg4326)

        ecef = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
        lla = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            x = float(feature[x_field])
            y = float(feature[y_field])
            z = float(feature[z_field])
            lon, lat, alt = pyproj.transform(ecef, lla, x, y, z, radians=False)
            pt = QgsPoint(lon, lat, alt, wkbType=QgsWkbTypes.PointZ)
            f = QgsFeature()
            if add_z:
                f.setAttributes(feature.attributes()+[alt])
            else:
                f.setAttributes(feature.attributes())
            f.setGeometry(QgsGeometry(pt))
            sink.addFeature(f)
            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'ecef2lla'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/ecef.png')

    def displayName(self):
        return tr('ECEF to Lat, Lon, Altitude')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    '''def shortHelpString(self):
        file = os.path.dirname(__file__) + '/doc/geom2mgrs.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help'''

    def createInstance(self):
        return EcefLatLonToAlgorithm()
