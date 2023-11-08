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

from qgis.PyQt.QtCore import QVariant, QCoreApplication, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsFields, QgsField, QgsFeature, QgsCoordinateTransform, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterString,
    QgsProcessingParameterNumber,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink)

from . import mgrs
from .util import epsg4326, convertDD2DMS, formatDmsString, tr
from .utm import latLon2Utm
from . import olc
from . import geohash
from .maidenhead import toMaiden
from .ups import latLon2Ups
from . import georef


class Geom2FieldAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm to convert a point layer to a Plus codes field.
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    PrmInputLayer = 'InputLayer'
    PrmOutputFormat = 'OutputFormat'
    PrmYFieldName = 'YFieldName'
    PrmXFieldName = 'XFieldName'
    PrmCoordinateOrder = 'CoordinateOrder'
    PrmCoordinateDelimiter = 'CoordinateDelimiter'
    PrmOutputCRSType = 'OutputCRSType'
    PrmCustomCRS = 'CustomCRS'
    PrmWgs84NumberFormat = 'Wgs84NumberFormat'
    PrmCoordinatePrecision = 'CoordinatePrecision'
    PrmDmsSecondPrecision = 'DMSSecondPrecision'
    PrmPlusCodesLength = 'PlusCodesLength'
    PrmGeohashPrecision = 'PrmGeohashPrecision'
    PrmOutputLayer = 'OutputLayer'
    PrmDmsAddSpace = 'DmsAddSpace'
    PrmDmsPadWithSpace = 'DmsPadWithSpace'
    PrmMaidenheadPrecision = 'MaidenheadPrecision'
    PrmUpsPrecision = 'UpsPrecision'
    PrmGeorefPrecision = 'GeorefPrecision'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PrmInputLayer,
                tr('Input point vector layer'),
                [QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmOutputFormat,
                tr('Output coordinate format'),
                options=[
                    tr('Coordinates in 2 fields'),
                    tr('Coordinates in 1 field'),
                    tr('GeoJSON'), tr('WKT'), tr('MGRS'),
                    tr('Plus Codes'), tr('Geohash'), tr('Standard UTM'),
                    tr('Maidenhead grid locator'), tr('UPS'), tr('GEOREF')],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmYFieldName,
                tr('Name for the field containing both coordinates, or the Y (latitude) coordinate'),
                defaultValue='y',
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmXFieldName,
                tr('Name of the field containing the X (longitude) portion of the coordinate'),
                defaultValue='x',
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmCoordinateOrder,
                tr('Coordinate order when using 1 field'),
                options=[tr('Lat,Lon (Y,X) - Google map order'), tr('Lon,Lat (X,Y) order')],
                defaultValue=0,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmCoordinateDelimiter,
                tr('Delimiter between coordinates when using 1 field'),
                defaultValue=',',
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmOutputCRSType,
                tr('Output CRS of coordinates added to a field'),
                options=[tr('WGS 84'), tr('Layer CRS'), tr('Project CRS'), tr('Custom CRS')],
                defaultValue=0,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.PrmCustomCRS,
                tr('Custom CRS for coordinates added to a field'),
                'EPSG:4326',
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmWgs84NumberFormat,
                tr('Select Decimal or DMS degrees for WGS 84 numbers'),
                options=[tr('Decimal degrees'), tr('D°M\'S"'), tr('D°M.MM\''), tr('DDMMSS')],
                defaultValue=0,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmDmsAddSpace,
                tr('Add space between D° M\' S" and D° M.MM\' numbers'),
                False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmDmsPadWithSpace,
                tr('Pad D°M\'S" and D°M.MM\' coordinates with leading zeros'),
                False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmCoordinatePrecision,
                tr('Decimal number precision'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=8,
                optional=True,
                minValue=0)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmDmsSecondPrecision,
                tr('DMS / Degrees Minutes / UTM precision'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=0,
                optional=True,
                minValue=0)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmPlusCodesLength,
                tr('Plus Codes length'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=11,
                optional=True,
                minValue=10,
                maxValue=20)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmGeohashPrecision,
                tr('Geohash precision'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=12,
                optional=True,
                minValue=1,
                maxValue=30)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmMaidenheadPrecision,
                tr('Maidenhead grid locator precision'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=3,
                optional=True,
                minValue=1,
                maxValue=4)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmUpsPrecision,
                tr('UPS precision'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=0,
                optional=True,
                minValue=0,
                maxValue=8)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmGeorefPrecision,
                tr('GEOREF precision'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=5,
                optional=True,
                minValue=0,
                maxValue=10)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                tr('Output layer'))
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        outputFormat = self.parameterAsInt(parameters, self.PrmOutputFormat, context)
        field1Name = self.parameterAsString(parameters, self.PrmYFieldName, context).strip()
        field2Name = self.parameterAsString(parameters, self.PrmXFieldName, context).strip()
        coordOrder = self.parameterAsInt(parameters, self.PrmCoordinateOrder, context)
        delimiter = self.parameterAsString(parameters, self.PrmCoordinateDelimiter, context)
        crsType = self.parameterAsInt(parameters, self.PrmOutputCRSType, context)
        crsOther = self.parameterAsCrs(parameters, self.PrmCustomCRS, context)
        wgs84Format = self.parameterAsInt(parameters, self.PrmWgs84NumberFormat, context)
        decimalPrecision = self.parameterAsInt(parameters, self.PrmCoordinatePrecision, context)
        dmsPrecision = self.parameterAsInt(parameters, self.PrmDmsSecondPrecision, context)
        plusCodesLength = self.parameterAsInt(parameters, self.PrmPlusCodesLength, context)
        geohashPrecision = self.parameterAsInt(parameters, self.PrmGeohashPrecision, context)
        maidenPrecision = self.parameterAsInt(parameters, self.PrmMaidenheadPrecision, context)
        upsPrecision = self.parameterAsInt(parameters, self.PrmUpsPrecision, context)
        georefPrecision = self.parameterAsInt(parameters, self.PrmGeorefPrecision, context)
        use_dms_space = self.parameterAsBool(parameters, self.PrmDmsAddSpace, context)
        dms_pad_with_space = self.parameterAsBool(parameters, self.PrmDmsPadWithSpace, context)

        layerCRS = source.sourceCrs()
        # For the first condition, the user has either EPSG:4326 selected or
        # or have chosen GeoJSON or WKT which will be 4326 as well
        if crsType == 0 or outputFormat >= 2:  # Forced WGS 84
            outCRS = epsg4326
        elif crsType == 1:  # Layer CRS
            outCRS = layerCRS
        elif crsType == 2:  # Project CRS
            outCRS = QgsProject.instance().crs()
        else:
            outCRS = crsOther

        fieldsout = QgsFields(source.fields())
        if fieldsout.append(QgsField(field1Name, QVariant.String)) is False:
            msg = "{} '{}'".format(tr('Field names must be unique. There is already a field named'), field1Name)
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        if outputFormat == 0:  # Two fields for coordinates
            if fieldsout.append(QgsField(field2Name, QVariant.String)) is False:
                msg = "{} '{}'".format(tr('Field names must be unique. There is already a field named'), field2Name)
                feedback.reportError(msg)
                raise QgsProcessingException(msg)

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutputLayer,
            context, fieldsout, source.wkbType(), layerCRS)

        if layerCRS != outCRS:
            transform = QgsCoordinateTransform(layerCRS, outCRS, QgsProject.instance())

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            try:
                pt = feature.geometry().asPoint()
                if layerCRS != outCRS:
                    pt = transform.transform(pt)
                if outputFormat == 0:  # Two fields for coordinates
                    if outCRS == epsg4326:
                        if wgs84Format == 0:  # Decimal Degrees
                            msg = '{:.{prec}f}'.format(pt.y(), prec=decimalPrecision)
                            msg2 = '{:.{prec}f}'.format(pt.x(), prec=decimalPrecision)
                        elif wgs84Format == 1:  # DMS
                            msg = convertDD2DMS(pt.y(), True, 0, dmsPrecision, use_dms_space, dms_pad_with_space)
                            msg2 = convertDD2DMS(pt.x(), False, 0, dmsPrecision, use_dms_space, dms_pad_with_space)
                        elif wgs84Format == 2:  # D M.MM
                            msg = convertDD2DMS(pt.y(), True, 2, dmsPrecision, use_dms_space, dms_pad_with_space)
                            msg2 = convertDD2DMS(pt.x(), False, 2, dmsPrecision, use_dms_space, dms_pad_with_space)
                        else:  # DDMMSS
                            msg = convertDD2DMS(pt.y(), True, 1, dmsPrecision, use_dms_space, dms_pad_with_space)
                            msg2 = convertDD2DMS(pt.x(), False, 1, dmsPrecision, use_dms_space, dms_pad_with_space)
                    else:
                        msg = '{:.{prec}f}'.format(pt.y(), prec=decimalPrecision)
                        msg2 = '{:.{prec}f}'.format(pt.x(), prec=decimalPrecision)
                elif outputFormat == 1:  # One field for coordinate
                    if outCRS == epsg4326:
                        if wgs84Format == 0:  # Decimal Degrees
                            if coordOrder == 0:
                                msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.y(), delimiter, pt.x(), prec=decimalPrecision)
                            else:
                                msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.x(), delimiter, pt.y(), prec=decimalPrecision)
                        elif wgs84Format == 1:  # DMS
                            msg = formatDmsString(pt.y(), pt.x(), 0, dmsPrecision, coordOrder, delimiter, use_dms_space, dms_pad_with_space)
                        elif wgs84Format == 2:  # D M.MM
                            msg = formatDmsString(pt.y(), pt.x(), 2, dmsPrecision, coordOrder, delimiter, use_dms_space, dms_pad_with_space)
                        else:  # DDMMSS
                            msg = formatDmsString(pt.y(), pt.x(), 1, dmsPrecision, coordOrder, delimiter, use_dms_space, dms_pad_with_space)
                    else:
                        if coordOrder == 0:
                            msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.y(), delimiter, pt.x(), prec=decimalPrecision)
                        else:
                            msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.x(), delimiter, pt.y(), prec=decimalPrecision)
                elif outputFormat == 2:  # GeoJSON
                    msg = '{{"type": "Point","coordinates": [{:.{prec}f},{:.{prec}f}]}}'.format(pt.x(), pt.y(), prec=decimalPrecision)
                elif outputFormat == 3:  # WKT
                    msg = 'POINT({:.{prec}f} {:.{prec}f})'.format(pt.x(), pt.y(), prec=decimalPrecision)
                elif outputFormat == 4:  # MGRS
                    msg = mgrs.toMgrs(pt.y(), pt.x(), 5)
                elif outputFormat == 5:  # Plus codes
                    msg = olc.encode(pt.y(), pt.x(), plusCodesLength)
                elif outputFormat == 6:  # Geohash
                    msg = geohash.encode(pt.y(), pt.x(), geohashPrecision)
                elif outputFormat == 7:  # WGS 84 UTM
                    msg = latLon2Utm(pt.y(), pt.x(), dmsPrecision)
                elif outputFormat == 8: # Maidenhead grid
                    msg = toMaiden(pt.y(), pt.x(), maidenPrecision)
                elif outputFormat == 9: # UPS
                    msg = latLon2Ups(pt.y(), pt.x(), upsPrecision, 0)
                else:  # GEOREF
                    msg = georef.encode(pt.y(), pt.x(), georefPrecision)
            except Exception:
                msg = ''
                msg2 = ''

            f = QgsFeature()
            f.setGeometry(feature.geometry())
            if outputFormat == 0:  # Two fields for coordinates
                f.setAttributes(feature.attributes() + [msg, msg2])
            else:
                f.setAttributes(feature.attributes() + [msg])
            sink.addFeature(f)

            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))

        return {self.PrmOutputLayer: dest_id}

    def name(self):
        return 'geom2field'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/geom2field.svg')

    def displayName(self):
        return tr('Point layer to fields')

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def shortHelpString(self):
        file = os.path.dirname(__file__) + '/doc/geom2fields.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return Geom2FieldAlgorithm()
