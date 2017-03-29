from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import webbrowser

class ShowOnMapTool(QgsMapTool):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    def __init__(self, settings, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.settings = settings
        
    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        
    def canvasReleaseEvent(self, event):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard.'''
        pt = self.toMapCoordinates(event.pos())
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(canvasCRS, epsg4326)
        pt4326 = transform.transform(pt.x(), pt.y())
        lat = pt4326.y()
        lon = pt4326.x()
        mapprovider = self.settings.getMapProviderString(lat, lon)
        url = QUrl(mapprovider).toString()
        webbrowser.open(url, new=2)
        self.iface.messageBar().pushMessage("", "Viewing Coordinate %f,%f in external map" % (lat,lon), level=QgsMessageBar.INFO, duration=3)
