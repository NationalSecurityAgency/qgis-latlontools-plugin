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
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QColor
from qgis.core import Qgis, QgsCoordinateTransform, QgsProject, QgsSettings
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker
from .util import epsg4326, tr
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
        self.marker = None
        self.vertex = None

    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        self.snapcolor = QgsSettings().value( "/qgis/digitizing/snap_color" , QColor( Qt.magenta ) )

    def deactivate(self):
        self.removeMarker()
        self.removeVertexMarker()

    def canvasPressEvent(self, event):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard.'''
        pt = self.snappoint(event.originalPixelPoint())
        self.removeVertexMarker()
        if settings.externalMapShowLocation:
            if self.marker is None:
                self.marker = QgsVertexMarker(self.canvas)
                self.marker.setIconSize(18)
                self.marker.setPenWidth(2)
                self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            self.marker.setCenter(pt)
        else:
            self.removeMarker()

        button = event.button()

        canvasCRS = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
        pt4326 = transform.transform(pt.x(), pt.y())
        lat = pt4326.y()
        lon = pt4326.x()
        if settings.googleEarthMapProvider(button):
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
            self.iface.messageBar().pushMessage("", "{} {:.8f},{:.8f} {}".format(tr("Viewing Coordinate"), lat, lon, tr("in Google Earth")), level=Qgis.Info, duration=3)
        else:
            mapprovider = settings.getMapProviderString(lat, lon, button)
            url = QUrl(mapprovider).toString()
            webbrowser.open(url, new=2)
            self.iface.messageBar().pushMessage("", "{} {:.8f},{:.8f} {}".format(tr("Viewing Coordinate"), lat, lon, tr("in external map")), level=Qgis.Info, duration=3)

    def canvasMoveEvent(self, event):
        '''Show when the user mouses over a vector vertex in snapping mode.'''
        self.snappoint(event.originalPixelPoint()) # input is QPoint

    def snappoint(self, qpoint):
        match = self.canvas.snappingUtils().snapToMap(qpoint)
        if match.isValid():
            if self.vertex is None:
                self.vertex = QgsVertexMarker(self.canvas)
                self.vertex.setIconSize(12)
                self.vertex.setPenWidth(2)
                self.vertex.setColor(self.snapcolor)
                self.vertex.setIconType(QgsVertexMarker.ICON_BOX)
            self.vertex.setCenter(match.point())
            return (match.point()) # Returns QgsPointXY
        else:
            self.removeVertexMarker()
            return self.toMapCoordinates(qpoint) # QPoint input, returns QgsPointXY

    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None

    def removeVertexMarker(self):
        if self.vertex is not None:
            self.canvas.scene().removeItem(self.vertex)
            self.vertex = None
