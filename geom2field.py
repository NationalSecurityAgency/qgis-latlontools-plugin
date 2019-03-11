import os

from qgis.PyQt.QtCore import QVariant, QCoreApplication, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsFields, QgsField, QgsFeature, QgsCoordinateTransform, QgsProject

from qgis.core import (QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterString,
    QgsProcessingParameterNumber,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink)

from . import mgrs
from .LatLon import LatLon
from .util import epsg4326
from . import olc

def tr(string):
    return QCoreApplication.translate('Processing', string)
        
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
    PrmOtherDelimiter = 'OtherDelimiter'
    PrmOutputCRSType = 'OutputCRSType'
    PrmCustomCRS = 'CustomCRS'
    PrmWgs84NumberFormat = 'Wgs84NumberFormat'
    PrmCoordinatePrecision = 'CoordinatePrecision'
    PrmDMSSecondPrecision = 'DMSSecondPrecision'
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
            QgsProcessingParameterEnum(
                self.PrmOutputFormat,
                tr('Output format'),
                options=[tr('Coordinates in 2 fields'),
                    tr('Coordinates in 1 field'),
                    'GeoJSON','WKT','MGRS','Plus Codes'],
                defaultValue=0,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmYFieldName,
                tr('Latitude (Y), GeoJSON, WKT, MGRS, or Plus Codes field name'),
                defaultValue='y',
                optional=True)
            )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmXFieldName,
                tr('Longitude (X) field name'),
                defaultValue='x',
                optional=True)
            )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmCoordinateOrder,
                tr('Coordinate order when using 1 field'),
                options=[tr('Lat,Lon (Y,X) - Google map order'),tr('Lon,Lat (X,Y) order')],
                defaultValue=0,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmCoordinateDelimiter,
                tr('Coordinate delimiter when using 1 field'),
                options=[tr('Comma'),tr('Space'),tr('Tab'),tr('Other')],
                defaultValue=0,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PrmOtherDelimiter,
                tr('Other delimiter when using 1 field'),
                defaultValue='',
                optional=True)
            )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmOutputCRSType,
                tr('Output CRS of coordinates added to a field'),
                options=[tr('WGS 84'),tr('Layer CRS'),tr('Project CRS'),tr('Custom CRS')],
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
                tr('Select Decimal or DMS degress for WGS 84 numbers'),
                options=[tr('Decimal degrees'),tr('DMS'),tr('DDMMSS')],
                defaultValue=0,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmCoordinatePrecision,
                tr('Decimal number precision'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=8,
                optional=True,
                minValue=0
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmDMSSecondPrecision,
                tr('DMS second precision'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=0,
                optional=True,
                minValue=0
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmPlusCodesLength,
                'Plus Codes length',
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=11,
                optional=False,
                minValue=10,
                maxValue=20
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PrmOutputLayer,
                'Output layer')
            )
    
    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInputLayer, context)
        outputFormat = self.parameterAsInt(parameters, self.PrmOutputFormat, context)
        field1Name = self.parameterAsString(parameters, self.PrmYFieldName, context).strip()
        field2Name = self.parameterAsString(parameters, self.PrmXFieldName, context).strip()
        coordOrder = self.parameterAsInt(parameters, self.PrmCoordinateOrder, context)
        delimType = self.parameterAsInt(parameters, self.PrmCoordinateDelimiter, context)
        otherDelim = self.parameterAsString(parameters, self.PrmOtherDelimiter, context).strip()
        crsType = self.parameterAsInt(parameters, self.PrmOutputCRSType, context)
        crsOther = self.parameterAsCrs(parameters, self.PrmCustomCRS, context)
        wgs84Format = self.parameterAsInt(parameters, self.PrmWgs84NumberFormat, context)
        decimalPrecision = self.parameterAsInt(parameters, self.PrmCoordinatePrecision, context)
        dmsPrecision = self.parameterAsInt(parameters, self.PrmDMSSecondPrecision, context)
        plusCodesLength = self.parameterAsInt(parameters, self.PrmPlusCodesLength, context)
        
        if delimType == 0:
            delimiter = ','
        elif delimType == 1:
            delimiter = ' '
        elif delimType == 2:
            delimiter = '\t'
        else:
            delimiter = otherDelim
            
        layerCRS = source.sourceCrs()
        # For the first condition, the user has either EPSG:4326 selected or
        # or have chosen GeoJSON or WKT which will be 4326 as well
        if crsType == 0 or outputFormat >= 2: # Forced WGS 84
            outCRS = epsg4326
        elif crsType == 1: # Layer CRS
            outCRS = layerCRS
        elif crsType == 2: # Project CRS
            outCRS = QgsProject.instance().crs()
        else:
            outCRS = crsOther
            
        fieldsout = QgsFields(source.fields())
        
        if fieldsout.append(QgsField(field1Name, QVariant.String)) == False:
            msg = "Field names must be unique. There is already a field named '{}'".format(field1Name)
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        if outputFormat == 0: # Two fields for coordinates
            if fieldsout.append(QgsField(field2Name, QVariant.String)) == False:
                msg = "Field names must be unique. There is already a field named '{}'".format(field2Name)
                feedback.reportError(msg)
                raise QgsProcessingException(msg)
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.PrmOutputLayer,
                context, fieldsout, source.wkbType(), layerCRS)
                
        if layerCRS != outCRS:
            transform = QgsCoordinateTransform(layerCRS, outCRS, QgsProject.instance())
        
        latlon = LatLon()
        latlon.setPrecision(dmsPrecision)

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            pt = feature.geometry().asPoint()
            if layerCRS != outCRS:
                pt = transform.transform(pt)
            try:
                if outputFormat == 0: # Two fields for coordinates
                    if outCRS == epsg4326:
                        if wgs84Format == 0: # Decimal Degrees
                            msg = '{:.{prec}f}'.format(pt.y(),prec=decimalPrecision)
                            msg2 = '{:.{prec}f}'.format(pt.x(),prec=decimalPrecision)
                        elif wgs84Format == 1: # DMS
                            latlon.setCoord(pt.y(), pt.x())
                            msg = latlon.convertDD2DMS(pt.y(), True, True)
                            msg2 = latlon.convertDD2DMS(pt.x(), False, True)
                        else: #DDMMSS
                            latlon.setCoord(pt.y(), pt.x())
                            msg = latlon.convertDD2DMS(pt.y(), True, False)
                            msg2 = latlon.convertDD2DMS(pt.x(), False, False)
                    else:
                        msg = '{:.{prec}f}'.format(pt.y(),prec=decimalPrecision)
                        msg2 = '{:.{prec}f}'.format(pt.x(),prec=decimalPrecision)
                elif outputFormat == 1: # One field for coordinate
                    if outCRS == epsg4326:
                        if wgs84Format == 0: # Decimal Degrees
                            if coordOrder == 0:
                                msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.y(),delimiter,pt.x(),prec=decimalPrecision)
                            else:
                                msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.x(),delimiter,pt.y(),prec=decimalPrecision)
                        elif wgs84Format == 1: # DMS
                            latlon.setCoord(pt.y(), pt.x())
                            if coordOrder == 0:
                                msg = latlon.getDMS(delimiter)
                            else:
                                msg = latlon.getDMSLonLatOrder(delimiter)
                        else: #DDMMSS
                            latlon.setCoord(pt.y(), pt.x())
                            if coordOrder == 0:
                                msg = latlon.getDDMMSS(delimiter)
                            else:
                                msg = latlon.getDDMMSSLonLatOrder(delimiter)
                    else:
                        if coordOrder == 0:
                            msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.y(),delimiter,pt.x(),prec=decimalPrecision)
                        else:
                            msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.x(),delimiter,pt.y(),prec=decimalPrecision)
                elif outputFormat == 2: # GeoJSON
                    msg = '{{"type": "Point","coordinates": [{:.{prec}f},{:.{prec}f}]}}'.format(pt.x(), pt.y(),prec=decimalPrecision)
                elif outputFormat == 3: # WKT
                    msg = 'POINT({:.{prec}f} {:.{prec}f})'.format(pt.x(), pt.y(),prec=decimalPrecision)
                elif outputFormat == 4: # MGRS
                    msg = mgrs.toMgrs(pt.y(), pt.x(), 5)
                else: # Plus codes
                    msg = olc.encode(pt.y(), pt.x(), plusCodesLength)
            except:
                msg = ''

            f = QgsFeature()
            f.setGeometry(feature.geometry())
            if outputFormat == 0: # Two fields for coordinates
                f.setAttributes(feature.attributes()+[msg, msg2])
            else:
                f.setAttributes(feature.attributes()+[msg])
            sink.addFeature(f)
            
            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total))
            
        return {self.PrmOutputLayer: dest_id}
        
    def name(self):
        return 'geom2field'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/geom2field.png')
    
    def displayName(self):
        return 'Point layer to fields'
    
    def group(self):
        return 'Vector conversion'
        
    def groupId(self):
        return 'vectorconversion'
        
    def helpUrl(self):
        file = os.path.dirname(__file__)+'/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)
    
    def shortHelpString(self):
        file = os.path.dirname(__file__)+'/doc/geom2fields.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help=helpf.read()
        return help
        
    def createInstance(self):
        return Geom2FieldAlgorithm()
