import os
import re

from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.PyQt.QtCore import pyqtSignal, QTextCodec
from qgis.gui import QgsVertexMarker
from qgis.core import Qgis, QgsJsonUtils, QgsWkbTypes
from .util import epsg4326, parseDMSString
from .utm import isUtm, utmString2Crs
#import traceback

from . import mgrs
from . import olc

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/zoomToLatLon.ui'))


class ZoomToLatLon(QDockWidget, FORM_CLASS):

    def __init__(self, lltools, iface, parent):
        super(ZoomToLatLon, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()
        self.marker = None
        self.zoomToolButton.setIcon(QIcon(':/images/themes/default/mActionZoomIn.svg'))
        self.clearToolButton.setIcon(QIcon(':/images/themes/default/mIconClearText.svg'))
        self.zoomToolButton.clicked.connect(self.zoomToPressed)
        self.clearToolButton.clicked.connect(self.removeMarker)
        self.lltools = lltools
        self.settings = lltools.settingsDialog
        self.iface = iface
        self.coordTxt.returnPressed.connect(self.zoomToPressed)
        self.canvas.destinationCrsChanged.connect(self.crsChanged)
        self.configure()

    def showEvent(self, e):
        self.configure()
        
    def closeEvent(self, event):
        self.removeMarker()
        event.accept()
        
    def crsChanged(self):
        if self.isVisible():
            self.configure()
        
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def configure(self):
        self.coordTxt.setText("")
        
        if self.settings.zoomToProjIsMGRS():
            # This is an MGRS coordinate
            self.label.setText("Enter MGRS Coordinate")
        elif self.settings.zoomToProjIsPlusCodes():
            self.label.setText("Enter Plus Codes")
        elif self.settings.zoomToProjIsWgs84():
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("Enter 'Latitude, Longitude'")
            else:
                self.label.setText("Enter 'Longitude, Latitude'")
        elif self.settings.zoomToProjIsProjectCRS():
            crsID = self.canvas.mapSettings().destinationCrs().authid()
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("Enter {} Y,X".format(crsID))
            else:
                self.label.setText("Enter {} X,Y".format(crsID))
        else: # Default to custom CRS
            crsID = self.settings.zoomToCustomCrsId()
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("Enter {} Y,X".format(crsID))
            else:
                self.label.setText("Enter {} X,Y".format(crsID))

    def zoomToPressed(self):
        try:
            text = self.coordTxt.text().strip()
            if text[0] == '{': # This may be a GeoJSON point
                codec = QTextCodec.codecForName("UTF-8")
                fields = QgsJsonUtils.stringToFields(text, codec)
                fet = QgsJsonUtils.stringToFeatureList(text, fields, codec)
                if (len(fet) == 0) or not fet[0].isValid():
                    raise ValueError('Invalid Coordinates')
                
                geom = fet[0].geometry()
                if geom.isEmpty() or (geom.wkbType() != QgsWkbTypes.Point):
                    raise ValueError('Invalid GeoJSON Geometry')
                pt = geom.asPoint()
                lat = pt.y()
                lon = pt.x()
                srcCrs = epsg4326
            elif isUtm(text):
                pt = utmString2Crs(text)
                srcCrs = epsg4326
                lon = pt.x()
                lat = pt.y()
            elif self.settings.zoomToProjIsWgs84():
                if re.search(r'POINT\(', text) == None:
                    lat, lon = parseDMSString(text, self.settings.zoomToCoordOrder)
                else:
                    m = re.findall(r'POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                    if len(m) != 1:
                        raise ValueError('Invalid Coordinates')
                    lon = float(m[0][0])
                    lat = float(m[0][1])
                srcCrs = epsg4326
            elif self.settings.zoomToProjIsPlusCodes() and olc.isValid(text):
                # This looks like a Plus Codes coordinate
                coord = olc.decode(text)
                srcCrs = epsg4326
                lat = coord.latitudeCenter
                lon = coord.longitudeCenter
            elif self.settings.zoomToProjIsMGRS():
                # This is an MGRS coordinate
                text = re.sub(r'\s+', '', str(text)) # Remove all white space
                lat, lon = mgrs.toWgs(text)
                srcCrs = epsg4326
            else: # Is either the project or custom CRS
                if re.search(r'POINT\(', text) == None:
                    coords = re.split(r'[\s,;:]+', text, 1)
                    if len(coords) < 2:
                        raise ValueError('Invalid Coordinates')
                    if self.settings.zoomToCoordOrder == self.settings.OrderYX:
                        lat = float(coords[0])
                        lon = float(coords[1])
                    else:
                        lon = float(coords[0])
                        lat = float(coords[1])
                else:
                    m = re.findall(r'POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                    if len(m) != 1:
                        raise ValueError('Invalid Coordinates')
                    lon = float(m[0][0])
                    lat = float(m[0][1])
                if self.settings.zoomToProjIsProjectCRS():
                    srcCrs = self.canvas.mapSettings().destinationCrs()
                else:
                    srcCrs = self.settings.zoomToCustomCRS()
                    
            pt = self.lltools.zoomTo(srcCrs, lat, lon)
            if self.settings.persistentMarker:
                if self.marker is None:
                    self.marker = QgsVertexMarker(self.canvas)
                self.marker.setCenter(pt)
                self.marker.setIconSize(18)
                self.marker.setPenWidth(2)
                self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            elif self.marker is not None:
                self.removeMarker();
        except:
            #traceback.print_exc()
            self.iface.messageBar().pushMessage("", "Invalid Coordinate" , level=Qgis.Warning, duration=2)
            return

    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None
            self.coordTxt.clear()
