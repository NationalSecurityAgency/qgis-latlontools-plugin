from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMapToolEmitPoint, QgsMessageBar
from .util import *
import webbrowser

class ShowOnMapTool(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    def __init__(self, settings, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.settings = settings
        self.canvasClicked.connect(self.clicked)
        
    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        
    def clicked(self, pt, b):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard.'''
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
        pt4326 = transform.transform(pt.x(), pt.y())
        lat = pt4326.y()
        lon = pt4326.x()
        mapprovider = self.settings.getMapProviderString(lat, lon)
        url = QUrl(mapprovider).toString()
        webbrowser.open(url, new=2)
        self.iface.messageBar().pushMessage("", "Viewing Coordinate %f,%f in external map" % (lat,lon), level=QgsMessageBar.INFO, duration=3)
