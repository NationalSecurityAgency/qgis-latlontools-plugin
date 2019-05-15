from qgis.PyQt.QtCore import Qt, QUrl
from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker
from .util import epsg4326
from .settings import settings
import os
import webbrowser
import tempfile
import platform


class ShowOnMapTool(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    def __init__(self, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.canvasClicked.connect(self.clicked)
        self.marker = None
        
    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
    
    def deactivate(self):
        self.removeMarker()
    
    def clicked(self, pt, b):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard.'''
        if settings.externalMapShowLocation:
            if self.marker is None:
                self.marker = QgsVertexMarker(self.canvas)
                self.marker.setIconSize(18)
                self.marker.setPenWidth(2)
                self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            self.marker.setCenter(pt)
        else:
            self.removeMarker();
            
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
        pt4326 = transform.transform(pt.x(), pt.y())
        lat = pt4326.y()
        lon = pt4326.x()
        if settings.googleEarthMapProvider():
            f = tempfile.NamedTemporaryFile(mode='w', suffix=".kml", delete=False)
            f.write('<?xml version="1.0" encoding="UTF-8"?>')
            f.write('<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">')
            f.write('<Document>')
            f.write('   <name>QGIS Location</name>')
            f.write('   <description>{:.8f}, {:.8f}</description>'.format(lon, lat))
            f.write('   <Placemark>')
            f.write('       <name>QGIS Location</name>')
            f.write('       <Point>')
            f.write('           <coordinates>{:.8f},{:.8f},0</coordinates>'.format(lon, lat))
            f.write('       </Point>')
            f.write('   </Placemark>')
            f.write('</Document>')
            f.write('</kml>')
            f.close()
            if platform.system() == 'Windows':
                os.startfile(f.name)
            else:
                webbrowser.open(f.name)
            self.iface.messageBar().pushMessage("", "Viewing Coordinate %f,%f in Google Earth" % (lat, lon), level=Qgis.Info, duration=3)
        else:
            mapprovider = settings.getMapProviderString(lat, lon)
            url = QUrl(mapprovider).toString()
            webbrowser.open(url, new=2)
            self.iface.messageBar().pushMessage("", "Viewing Coordinate %f,%f in external map" % (lat, lon), level=Qgis.Info, duration=3)
    
    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None
