from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import Qgis, QgsCoordinateTransform, QgsPointXY, QgsProject
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker

from .settings import settings
from .LatLon import LatLon
from .util import *
from . import mgrs
from . import olc
#import traceback

class CopyLatLonTool(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    capturesig = pyqtSignal(QgsPointXY)
    
    def __init__(self, settings, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.settings = settings
        self.latlon = LatLon()
        self.capture4326 = False
        self.canvasClicked.connect(self.clicked)
        self.marker = None
        
    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
    
    def deactivate(self):
        self.removeMarker()
        
    def formatCoord(self, pt, delimiter):
        '''Format the coordinate string according to the settings from
        the settings dialog.'''
        if self.settings.captureProjIsWgs84(): # ProjectionTypeWgs84
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            self.latlon.setCoord(pt4326.y(), pt4326.x())
            self.latlon.setPrecision(self.settings.dmsPrecision)
            if self.latlon.isValid():
                if self.settings.wgs84NumberFormat == self.settings.Wgs84TypeDMS: # DMS
                    if self.settings.coordOrder == self.settings.OrderYX:
                        msg = self.latlon.getDMS(delimiter)
                    else:
                        msg = self.latlon.getDMSLonLatOrder(delimiter)
                elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeDDMMSS: # DDMMSS
                    if self.settings.coordOrder == self.settings.OrderYX:
                        msg = self.latlon.getDDMMSS(delimiter)
                    else:
                        msg = self.latlon.getDDMMSSLonLatOrder(delimiter)
                elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeWKT: # WKT
                    msg = 'POINT({:.{prec}f} {:.{prec}f})'.format(self.latlon.lon, self.latlon.lat, prec=self.settings.decimalDigits)
                elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeGeoJSON: # GeoJSON
                    msg = '{{"type": "Point","coordinates": [{:.{prec}f},{:.{prec}f}]}}'.format(self.latlon.lon, self.latlon.lat, prec=self.settings.decimalDigits)
                else: # decimal degrees
                    if self.settings.coordOrder == self.settings.OrderYX:
                        msg = '{:.{prec}f}{}{:.{prec}f}'.format(self.latlon.lat,delimiter,self.latlon.lon,prec=self.settings.decimalDigits)
                    else:
                        msg = '{:.{prec}f}{}{:.{prec}f}'.format(self.latlon.lon,delimiter,self.latlon.lat,prec=self.settings.decimalDigits)
            else:
                msg = None
        elif self.settings.captureProjIsProjectCRS():
            # Projection in the project CRS
            if self.settings.otherNumberFormat == 0: # Numerical
                if self.settings.coordOrder == self.settings.OrderYX:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.y(),delimiter,pt.x(),prec=self.settings.decimalDigits)
                else:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.x(),delimiter,pt.y(),prec=self.settings.decimalDigits)
            else:
                msg = 'POINT({:.{prec}f} {:.{prec}f})'.format(pt.x(), pt.y(),prec=self.settings.decimalDigits)
        elif self.settings.captureProjIsCustomCRS():
            # Projection is a custom CRS
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            customCRS = self.settings.captureCustomCRS()
            transform = QgsCoordinateTransform(canvasCRS, customCRS, QgsProject.instance())
            pt = transform.transform(pt.x(), pt.y())
            if self.settings.otherNumberFormat == 0: # Numerical
                if self.settings.coordOrder == self.settings.OrderYX:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.y(),delimiter,pt.x(),prec=self.settings.decimalDigits)
                else:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.x(),delimiter,pt.y(),prec=self.settings.decimalDigits)
            else:
                msg = 'POINT({:.{prec}f} {:.{prec}f})'.format(pt.x(), pt.y(),prec=self.settings.decimalDigits)
        elif self.settings.captureProjIsMGRS():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            try:
                msg = mgrs.toMgrs(pt4326.y(), pt4326.x())
            except:
                msg = None
        elif self.settings.captureProjIsPlusCodes():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            try:
                msg = olc.encode(pt4326.y(), pt4326.x(), self.settings.plusCodesLength)
            except:
                msg = None
        
        msg = '{}{}{}'.format(self.settings.capturePrefix, msg, self.settings.captureSuffix)
        return msg
        
    def canvasMoveEvent(self, event):
        '''Capture the coordinate as the user moves the mouse over
        the canvas. Show it in the status bar.'''
        try:
            pt = self.toMapCoordinates(event.pos())
            msg = self.formatCoord(pt, ', ')
            formatString = self.coordFormatString()
            if msg == None:
                self.iface.statusBarIface().showMessage("")
            else:
                self.iface.statusBarIface().showMessage("{} - {}".format(msg,formatString),4000)
        except:
            self.iface.statusBarIface().showMessage("")

    def coordFormatString(self):
        if self.settings.captureProjIsWgs84():
            if self.settings.wgs84NumberFormat == self.settings.Wgs84TypeDecimal:
                if self.settings.coordOrder == self.settings.OrderYX:
                    s = 'Lat Lon'
                else:
                    s = 'Lon Lat'
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeWKT:
                s = 'WKT'
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeGeoJSON:
                s = 'GeoJSON'
            else:
                s = 'DMS'
        elif self.settings.captureProjIsProjectCRS():
            crsID = self.canvas.mapSettings().destinationCrs().authid()
            if self.settings.otherNumberFormat == 0: # Numerical
                if self.settings.coordOrder == self.settings.OrderYX:
                    s = '{} - Y,X'.format(crsID)
                else:
                    s = '{} - X,Y'.format(crsID)
            else: # WKT
                s = 'WKT'
        elif self.settings.captureProjIsMGRS():
            s = 'MGRS'
        elif self.settings.captureProjIsPlusCodes():
            s = 'Plus Codes'
        elif self.settings.captureProjIsCustomCRS():
            if self.settings.otherNumberFormat == 0: # Numerical
                if self.settings.coordOrder == self.settings.OrderYX:
                    s = '{} - Y,X'.format(self.settings.captureCustomCRSID())
                else:
                    s = '{} - X,Y'.format(self.settings.captureCustomCRSID())
            else: # WKT
                s = 'WKT'
        else: # Should never happen
            s = ''
        return s
    
    def clicked(self, pt, b):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard.'''
        if settings.captureShowLocation:
            if self.marker is None:
                self.marker = QgsVertexMarker(self.canvas)
                self.marker.setIconSize(18)
                self.marker.setPenWidth(2)
                self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            self.marker.setCenter(pt)
        else:
            self.removeMarker();
        
        try:
            if self.capture4326:
                canvasCRS = self.canvas.mapSettings().destinationCrs()
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
                self.capturesig.emit(pt4326)
                return
            msg = self.formatCoord(pt, self.settings.delimiter)
            formatString = self.coordFormatString()
            if msg != None:
                clipboard = QApplication.clipboard()
                clipboard.setText(msg)
                self.iface.messageBar().pushMessage("", "{} coordinate {} copied to the clipboard".format(formatString, msg), level=Qgis.Info, duration=4)
        except Exception as e:
            self.iface.messageBar().pushMessage("", "Invalid coordinate: {}".format(e), level=Qgis.Warning, duration=4)
    
    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None
