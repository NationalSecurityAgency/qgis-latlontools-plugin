from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QApplication
from qgis.core import QgsCoordinateTransform, QgsPoint
from qgis.gui import QgsMapToolEmitPoint, QgsMessageBar

from .LatLon import LatLon
from .util import *
import mgrs

class CopyLatLonTool(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    capturesig = pyqtSignal(QgsPoint)
    
    def __init__(self, settings, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.settings = settings
        self.latlon = LatLon()
        self.capture4326 = False
        self.canvasClicked.connect(self.clicked)
        
    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        
    def formatCoord(self, pt, delimiter):
        '''Format the coordinate string according to the settings from
        the settings dialog.'''
        if self.settings.captureProjIsWgs84(): # ProjectionTypeWgs84
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326)
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
                    msg = 'POINT({} {})'.format(self.latlon.lon, self.latlon.lat)
                else: # decimal degrees
                    if self.settings.coordOrder == self.settings.OrderYX:
                        msg = '{}{}{}'.format(self.latlon.lat,delimiter,self.latlon.lon)
                    else:
                        msg = '{}{}{}'.format(self.latlon.lon,delimiter,self.latlon.lat)
            else:
                msg = None
        elif self.settings.captureProjIsProjectCRS():
            # Projection in the project CRS
            if self.settings.otherNumberFormat == 0: # Numerical
                if self.settings.coordOrder == self.settings.OrderYX:
                    msg = '{}{}{}'.format(pt.y(),delimiter,pt.x())
                else:
                    msg = '{}{}{}'.format(pt.x(),delimiter,pt.y())
            else:
                msg = 'POINT({} {})'.format(pt.x(), pt.y())
        elif self.settings.captureProjIsCustomCRS():
            # Projection is a custom CRS
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            customCRS = self.settings.captureCustomCRS()
            transform = QgsCoordinateTransform(canvasCRS, customCRS)
            pt = transform.transform(pt.x(), pt.y())
            if self.settings.otherNumberFormat == 0: # Numerical
                if self.settings.coordOrder == self.settings.OrderYX:
                    msg = '{}{}{}'.format(pt.y(),delimiter,pt.x())
                else:
                    msg = '{}{}{}'.format(pt.x(),delimiter,pt.y())
            else:
                msg = 'POINT({} {})'.format(pt.x(), pt.y())
        elif self.settings.captureProjIsMGRS():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326)
                pt4326 = transform.transform(pt.x(), pt.y())
            try:
                msg = mgrs.toMgrs(pt4326.y(), pt4326.x())
            except:
                msg = None

        return msg
        
    def canvasMoveEvent(self, event):
        '''Capture the coordinate as the user moves the mouse over
        the canvas. Show it in the status bar.'''
        try:
            pt = self.toMapCoordinates(event.pos())
            msg = self.formatCoord(pt, ', ')
            formatString = self.coordFormatString()
            if msg == None:
                self.iface.mainWindow().statusBar().showMessage("")
            else:
                self.iface.mainWindow().statusBar().showMessage("{} - {}".format(msg,formatString))
        except:
            self.iface.mainWindow().statusBar().showMessage("")

    def coordFormatString(self):
        if self.settings.captureProjIsWgs84():
            if self.settings.wgs84NumberFormat == self.settings.Wgs84TypeDecimal:
                if self.settings.coordOrder == self.settings.OrderYX:
                    s = 'Lat Lon'
                else:
                    s = 'Lon Lat'
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeWKT:
                s = 'WKT'
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
        try:
            if self.capture4326:
                canvasCRS = self.canvas.mapSettings().destinationCrs()
                transform = QgsCoordinateTransform(canvasCRS, epsg4326)
                pt4326 = transform.transform(pt.x(), pt.y())
                self.capturesig.emit(pt4326)
                return
            msg = self.formatCoord(pt, self.settings.delimiter)
            formatString = self.coordFormatString()
            if msg != None:
                clipboard = QApplication.clipboard()
                clipboard.setText(msg)
                self.iface.messageBar().pushMessage("", "{} coordinate {} copied to the clipboard".format(formatString, msg), level=QgsMessageBar.INFO, duration=4)
        except Exception as e:
            self.iface.messageBar().pushMessage("", "Invalid coordinate: {}".format(e), level=QgsMessageBar.WARNING, duration=4)