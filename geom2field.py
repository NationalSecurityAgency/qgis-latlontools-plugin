import os

from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtCore import QVariant
from qgis.core import Qgis, QgsMapLayerProxyModel, QgsVectorLayer, QgsFields, QgsField, QgsFeature, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsProject

from . import mgrs
from .LatLon import LatLon
from .util import *

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/geom2field.ui'))


class Geom2FieldWidget(QDialog, FORM_CLASS):
    '''ToMGRS Dialog box.'''
    def __init__(self, iface, parent):
        super(Geom2FieldWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.mapLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.mapLayerComboBox.activated.connect(self.enableWidgets)
        self.outputFormatComboBox.addItems(["Coordinates in 2 fields", "Coordinates in 1 field", "GeoJSON","WKT","MGRS"])
        self.outputFormatComboBox.activated.connect(self.enableWidgets)
        self.coordOrderComboBox.addItems(['Lat, Lon (Y,X) - Google Map Order','Lon, Lat (X,Y) Order'])
        self.delimComboBox.addItems(['Comma', 'Space', 'Tab', 'Other'])
        self.delimComboBox.activated.connect(self.enableWidgets)
        self.outputCrsComboBox.addItems(['WGS 84', 'Layer CRS', 'Project CRS', 'Custom CRS'])
        self.outputCrsComboBox.activated.connect(self.enableWidgets)
        self.wgs84NumberFormatComboBox.addItems(['Decimal Degrees', 'DMS', 'DDMMSS'])
        self.wgs84NumberFormatComboBox.activated.connect(self.enableWidgets)
        self.crsSelectionWidget.setCrs(epsg4326)

    def showEvent(self, e):
        self.enableWidgets()
        
        
    def enableWidgets(self):
        layer = self.mapLayerComboBox.currentLayer()
        field1Line = False
        field2Line = False
        coordOrder = False
        delim = False
        otherDelim = False
        outCrs = False
        crsSelection = False
        wgs84NumberFormat = False
        precision = False
        
        formatIndex = int(self.outputFormatComboBox.currentIndex())
        if formatIndex == 0: # Two coordinates
            field1Name = 'Latitude (Y) field name'
        elif formatIndex == 1: # Coordinates in 1 field
            if int(self.coordOrderComboBox.currentIndex()) == 0:
                field1Name = 'Lat, Lon (Y,X) field name'
            else:
                field1Name = 'Lon, Lat (X,Y) field name'
        elif formatIndex == 2: # GeoJSON
            field1Name = 'GeoJSON field name'
        elif formatIndex == 3: # WKT
            field1Name = 'WKT field name'
        else: # MGRS
            field1Name = 'MGRS field name'
        
        if layer:
            field1Line = True
            if formatIndex == 0: # Two coordinates
                field2Line = True
            if formatIndex <= 1: 
                wgs84NumberFormat = True
                if int(self.wgs84NumberFormatComboBox.currentIndex()) >= 1:
                    precision = True
            if formatIndex == 1: # Coordinates in 1 field
                coordOrder = True
                delim = True
                if int(self.delimComboBox.currentIndex()) == 3:
                    otherDelim = True
            if formatIndex == 2: # GeoJSON
                self.outputCrsComboBox.setCurrentIndex(0)
            if formatIndex <= 1 or formatIndex == 3:
                outCrs = True
            if int(self.outputCrsComboBox.currentIndex()) == 3:
                crsSelection = True
            
        self.field1Label.setText(field1Name)
        self.field1LineEdit.setEnabled(field1Line)
        self.field2LineEdit.setEnabled(field2Line)
        self.coordOrderComboBox.setEnabled(coordOrder)
        self.delimComboBox.setEnabled(delim)
        self.otherDelimLineEdit.setEnabled(otherDelim)
        self.outputCrsComboBox.setEnabled(outCrs)
        self.crsSelectionWidget.setEnabled(crsSelection)
        self.wgs84NumberFormatComboBox.setEnabled(wgs84NumberFormat)
        self.precisionSpinBox.setEnabled(precision)
        
    def isWgs84(self):
        wgs = int(self.outputCrsComboBox.currentIndex())
        layer = self.mapLayerComboBox.currentLayer()
        
        if wgs == 0: # Forced WGS 84
            return (True)
        elif wgs == 1: # Check the layer CRS
            if not layer:
                return (False)
            if layer.sourceCrs() == epsg4326:
                return (True)
        elif wgs == 2: # Check the project CRS
            if self.canvas.mapSettings().destinationCrs() == epsg4326:
                return (True)
        else:
            if self.crsSelectionWidget.crs() == epsg4326:
                return (True)
        return(False)
                
    def outputCrs(self):
        layer = self.mapLayerComboBox.currentLayer()
        outputFormat = int(self.outputFormatComboBox.currentIndex())
        # This shouldn't be called if there is not a layer, but if so just
        # return 4326.
        if outputFormat == 2 or outputFormat == 4 or not layer:
            return (epsg4326)
        outCRS = int(self.outputCrsComboBox.currentIndex())
        
        if outCRS == 0: # Forced WGS 84
            return (epsg4326)
        elif outCRS == 1: # Check the layer CRS
            return (layer.sourceCrs())
        elif outCRS == 2: # Check the project CRS
            return (self.canvas.mapSettings().destinationCrs())
        
        #other CRS
        return (self.crsSelectionWidget.crs())
                
    def accept(self):
        layer = self.mapLayerComboBox.currentLayer()
        if not layer:
            self.iface.messageBar().pushMessage("", "No Valid Layer", level=Qgis.Warning, duration=4)
            return
        layer_name = self.outputLayerLineEdit.text()
        outputFormat = int(self.outputFormatComboBox.currentIndex())
        field1Name = self.field1LineEdit.text()
        field2Name = self.field2LineEdit.text()
        coordOrder = int(self.coordOrderComboBox.currentIndex())
        delimType = int(self.delimComboBox.currentIndex())
        if delimType == 0:
            delimiter = ','
        elif delimType == 1:
            delimiter = ' '
        elif delimType == 2:
            delimiter = '\t'
        else:
            delimiter = self.otherDelimLineEdit.text()
        crsType = int(self.outputCrsComboBox.currentIndex())
        crsOther = self.crsSelectionWidget.crs()
        wgs84Format = int(self.wgs84NumberFormatComboBox.currentIndex())
        precision = self.precisionSpinBox.value()
        
        fields = layer.fields()
        fieldsout = QgsFields(fields)
        
        # We need to add the mgrs field at the end
        if fieldsout.append(QgsField(field1Name, QVariant.String)) == False:
            self.iface.messageBar().pushMessage("", "Coordinate Field Names must be unique", level=Qgis.Warning, duration=4)
            return
        if outputFormat == 0: # Two fields for coordinates
            if fieldsout.append(QgsField(field2Name, QVariant.String)) == False:
                self.iface.messageBar().pushMessage("", "Coordinate Field Names must be unique", level=Qgis.Warning, duration=4)
                return
        layerCRS = layer.crs()
        pointLayer = QgsVectorLayer("Point?crs={}".format(layerCRS.authid()), layer_name, "memory")
        ppoint = pointLayer.dataProvider()
        ppoint.addAttributes(fieldsout)
        pointLayer.updateFields()

        # The input to the mgrs conversions requires latitudes and longitudes
        # If the layer is not EPSG:4326 we need to convert it.
        outCRS = self.outputCrs()
        if layerCRS != outCRS:
            transform = QgsCoordinateTransform(layerCRS, outCRS, QgsProject.instance())

        iter = layer.getFeatures()
        latlon = LatLon()
        latlon.setPrecision(precision)

        msg2 = ''
        for feature in iter:
            pt = feature.geometry().asPoint()
            if layerCRS != outCRS:
                pt = transform.transform(pt)
            try:
                if outputFormat == 0: # Two fields for coordinates
                    if self.isWgs84():
                        if wgs84Format == 0: # Decimal Degrees
                            msg = '{}'.format(pt.y())
                            msg2 = '{}'.format(pt.x())
                        elif wgs84Format == 1: # DMS
                            latlon.setCoord(pt.y(), pt.x())
                            msg = latlon.convertDD2DMS(pt.y(), True, True)
                            msg2 = latlon.convertDD2DMS(pt.x(), False, True)
                        else: #DDMMSS
                            latlon.setCoord(pt.y(), pt.x())
                            msg = latlon.convertDD2DMS(pt.y(), True, False)
                            msg2 = latlon.convertDD2DMS(pt.x(), False, False)
                    else:
                        msg = '{}'.format(pt.y())
                        msg2 = '{}'.format(pt.x())
                elif outputFormat == 1: # One field for coordinate
                    if self.isWgs84():
                        if wgs84Format == 0: # Decimal Degrees
                            if coordOrder == 0:
                                msg = '{}{}{}'.format(pt.y(),delimiter,pt.x())
                            else:
                                msg = '{}{}{}'.format(pt.x(),delimiter,pt.y())
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
                            msg = '{}{}{}'.format(pt.y(),delimiter,pt.x())
                        else:
                            msg = '{}{}{}'.format(pt.x(),delimiter,pt.y())
                elif outputFormat == 2: # GeoJSON
                    msg = '{{"type": "Point","coordinates": [{},{}]}}'.format(pt.x(), pt.y())
                elif outputFormat == 3: # WKT
                    msg = 'POINT({} {})'.format(pt.x(), pt.y())
                else: # MGRS
                    msg = mgrs.toMgrs(pt.y(), pt.x(), 5)
            except:
                msg = ''
            f = QgsFeature()
            f.setGeometry(feature.geometry())
            if outputFormat == 0: # Two fields for coordinates
                f.setAttributes(feature.attributes()+[msg, msg2])
            else:
                f.setAttributes(feature.attributes()+[msg])
            ppoint.addFeatures([f])
            
        pointLayer.updateExtents()
        QgsProject.instance().addMapLayer(pointLayer)
        self.close()
        
        