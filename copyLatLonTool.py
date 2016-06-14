from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from LatLon import LatLon

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
        
    def formatCoord(self, pt, delimiter, outputFormat):
        '''Format the coordinate according to the settings from
        the settings dialog.'''
        if outputFormat == 'native':
            # Formatin in the native CRS
            msg = str(pt.y()) + delimiter + str(pt.x())
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
                    msg = self.latlon.getDMS(delimiter)
                elif outputFormat == 'ddmmss':
                    msg = self.latlon.getDDMMSS(delimiter)
                else:
                    msg = str(self.latlon.lat)+ delimiter +str(self.latlon.lon)
            else:
                msg = None
        return msg
        
    def canvasMoveEvent(self, event):
        '''Capture the coordinate as the user moves the mouse over
        the canvas. Show it in the status bar.'''
        outputFormat = self.settings.outputFormat
        pt = self.toMapCoordinates(event.pos())
        msg = self.formatCoord(pt, ', ', outputFormat)
        if outputFormat == 'native' or msg == None:
            self.iface.mainWindow().statusBar().showMessage("")
        elif outputFormat == 'dms' or outputFormat == 'ddmmss':
            self.iface.mainWindow().statusBar().showMessage("DMS: " + msg)
        else:
            self.iface.mainWindow().statusBar().showMessage("Lat Lon: " + msg)


    def canvasReleaseEvent(self, event):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard.'''
        pt = self.toMapCoordinates(event.pos())
        msg = self.formatCoord(pt, self.settings.delimiter,
            self.settings.outputFormat)
        if msg != None:
            clipboard = QApplication.clipboard()
            clipboard.setText(msg)
            self.iface.messageBar().pushMessage("", "Coordinate %s copied to the clipboard" % msg, level=QgsMessageBar.INFO, duration=3)
