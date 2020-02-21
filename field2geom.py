import os
import re

from qgis.PyQt.QtCore import QCoreApplication, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsFields, QgsFeature, QgsWkbTypes, QgsGeometry, QgsPointXY

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterCrs,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink)

from . import mgrs
from .util import epsg4326, parseDMSString
from . import olc
from . import geohash
from .utm import isUtm, utmString2Crs
from .maidenhead import maidenGridCenter
# import traceback


def tr(string):
    return QCoreApplication.translate('Processing', string)


class Field2GeomAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to convert a point layer to a Plus codes field.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    PrmInputLayer = 'InputLayer'
    PrmInputField1Type = 'InputField1Type'
    PrmField1 = 'Field1'
    PrmField2 = 'Field2'
    PrmInputCRS = 'InputCRS'
    PrmOutputLayer = 'OutputLayer'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInputLayer,
                tr('Input point vector layer or table'),
                [QgsProcessing.TypeVector])
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmInputField1Type,
                tr('Coordinate format found in the first field'),
                options=[
                    tr('Latitude (Y)'),
                    tr('Latitude (Y), Longitude (X)'),
                    tr('Longitude (X), Latitude (Y)'),
                    tr('MGRS'), tr('Plus Codes'), tr('Geohash'), tr('Standard UTM'), tr('Maidenhead grid locator')],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmField1,
                tr('Select the first field containing both coordinates or the Y (latitude) coordinate'),
                parentLayerParameterName=self.PrmInputLayer,
                type=QgsProcessingParameterField.String,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PrmField2,
                tr('Select the field containing the X or longitude coordinate if applicable'),
                parentLayerParameterName=self.PrmInputLayer,
                type=QgsProcessingParameterField.String,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.PrmInputCRS,
                tr('Input CRS - Not applicable to MGRS, Plus Codes, Geohash, UTM, & Maidenhead'),
                'EPSG:4326',
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                tr('Output layer'))
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        field_type = self.parameterAsInt(parameters, self.PrmInputField1Type, context)
        field1_name = self.parameterAsString(parameters, self.PrmField1, context).strip()
        field2_name = self.parameterAsString(parameters, self.PrmField2, context).strip()
        input_crs = self.parameterAsCrs(parameters, self.PrmInputCRS, context)

        if not field1_name:
            msg = tr('Select an attribute field containing a coordinate')
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

        if field_type == 0 and not field2_name:
            msg = tr('Select an attribute field containing an X or longitude coordinate')
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

        fieldsout = QgsFields(source.fields())

        if field_type >= 3:  # For MGRS, Plus Codes, UTM, Geohash and Maidenhead force the CRS to be 4326
            input_crs = epsg4326

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer,
            context, fieldsout, QgsWkbTypes.Point, input_crs)

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        failed = 0

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            try:
                attr1 = feature[field1_name].strip()
                if field_type == 0:  # Lat (y)
                    attr_x = feature[field2_name].strip()
                    if input_crs == epsg4326:
                        text = '{} {}'.format(attr1, attr_x)
                        lat, lon = parseDMSString(text, 0)
                    else:
                        lat = float(attr1)
                        lon = float(attr_x)
                elif field_type == 1:  # Lat (y), Lon (x)
                    if input_crs == epsg4326:
                        lat, lon = parseDMSString(attr1, 0)
                    else:
                        coords = re.split(r'[\s,;:]+', attr1, 1)
                        if len(coords) < 2:
                            raise ValueError('Invalid Coordinates')
                        lat = float(coords[0])
                        lon = float(coords[1])
                elif field_type == 2:  # Lon (x), Lat (y)
                    if input_crs == epsg4326:
                        lat, lon = parseDMSString(attr1, 1)
                    else:
                        coords = re.split(r'[\s,;:]+', attr1, 1)
                        if len(coords) < 2:
                            raise ValueError('Invalid Coordinates')
                        lon = float(coords[0])
                        lat = float(coords[1])
                elif field_type == 3:  # MGRS
                    m = re.sub(r'\s+', '', str(attr1))  # Remove all white space
                    lat, lon = mgrs.toWgs(m)
                elif field_type == 4:  # Plus codes
                    coord = olc.decode(attr1)
                    lat = coord.latitudeCenter
                    lon = coord.longitudeCenter
                elif field_type == 5:  # Geohash
                    (lat, lon) = geohash.decode(attr1)
                    lat = float(lat)
                    lon = float(lon)
                elif field_type == 6:  # UTM
                    pt = utmString2Crs(attr1)
                    lat = pt.y()
                    lon = pt.x()
                elif field_type == 7:  # Maidenhead Grid Locator
                    (lat, lon) = maidenGridCenter(attr1)
                    lat = float(lat)
                    lon = float(lon)

                f = QgsFeature()
                f.setAttributes(feature.attributes())
                f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
                sink.addFeature(f)
            except Exception:
                '''s = traceback.format_exc()
                feedback.pushInfo(s)'''
                failed += 1

            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))

        if failed > 0:
            msg = "{} out of {} features were invalid".format(failed, source.featureCount())
            feedback.pushInfo(msg)

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'field2geom'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/field2geom.png')

    def displayName(self):
        return 'Fields to point layer'

    def group(self):
        return 'Vector conversion'

    def groupId(self):
        return 'vectorconversion'

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def shortHelpString(self):
        file = os.path.dirname(__file__) + '/doc/field2geom.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return Field2GeomAlgorithm()
