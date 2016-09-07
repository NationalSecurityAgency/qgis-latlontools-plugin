from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from LatLon import LatLon
import mgrs

class CopyLatLonTool(QgsMapTool):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    def __init__(self, settings, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.settings = settings
        self.latlon = LatLon()
        
    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        
    def formatCoord(self, pt, delimiter, outputFormat, order):
        '''Format the coordinate according to the settings from
        the settings dialog.'''
        if outputFormat == 'native':
            # Formatin in the native CRS
            if order == 0:
                msg = str(pt.y()) + delimiter + str(pt.x())
            else:
                msg = str(pt.x()) + delimiter + str(pt.y())
        elif outputFormat == 'mgrs':
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapRenderer().destinationCrs()
            epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(canvasCRS, epsg4326)
            pt4326 = transform.transform(pt.x(), pt.y())
            try:
                msg = mgrs.toMgrs(pt4326.y(), pt4326.x())
            except:
                msg = None
        else:
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapRenderer().destinationCrs()
            epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(canvasCRS, epsg4326)
            pt4326 = transform.transform(pt.x(), pt.y())
            self.latlon.setCoord(pt4326.y(), pt4326.x())
            self.latlon.setPrecision(self.settings.dmsPrecision)
            if self.latlon.isValid():
                if outputFormat == 'dms':
                    if order == 0:
                        msg = self.latlon.getDMS(delimiter)
                    else:
                        msg = self.latlon.getDMSLonLatOrder(delimiter)
                elif outputFormat == 'ddmmss':
                    if order == 0:
                        msg = self.latlon.getDDMMSS(delimiter)
                    else:
                        msg = self.latlon.getDDMMSSLonLatOrder(delimiter)
                else: # decimal degrees
                    if order == 0:
                        msg = str(self.latlon.lat)+ delimiter +str(self.latlon.lon)
                    else:
                        msg = str(self.latlon.lon)+ delimiter +str(self.latlon.lat)
            else:
                msg = None
        return msg
        
    def canvasMoveEvent(self, event):
        '''Capture the coordinate as the user moves the mouse over
        the canvas. Show it in the status bar.'''
        outputFormat = self.settings.outputFormat
        order = self.settings.coordOrder
        pt = self.toMapCoordinates(event.pos())
        msg = self.formatCoord(pt, ', ', outputFormat, order)
        if outputFormat == 'native' or msg == None:
            self.iface.mainWindow().statusBar().showMessage("")
        elif outputFormat == 'dms' or outputFormat == 'ddmmss':
            self.iface.mainWindow().statusBar().showMessage("DMS: " + msg)
        elif outputFormat == 'mgrs':
            self.iface.mainWindow().statusBar().showMessage("MGRS Coordinate: " + msg)
        else:
            if order == 0:
                self.iface.mainWindow().statusBar().showMessage("Lat Lon: " + msg)
            else: 
                self.iface.mainWindow().statusBar().showMessage("Lon Lat: " + msg)

    def canvasReleaseEvent(self, event):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard.'''
        pt = self.toMapCoordinates(event.pos())
        msg = self.formatCoord(pt, self.settings.delimiter,
            self.settings.outputFormat, self.settings.coordOrder)
        if msg != None:
            clipboard = QApplication.clipboard()
            clipboard.setText(msg)
            self.iface.messageBar().pushMessage("", "Coordinate '%s' copied to the clipboard" % msg, level=QgsMessageBar.INFO, duration=3)
