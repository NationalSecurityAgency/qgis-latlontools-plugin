import os
import re

from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.PyQt.QtCore import QTextCodec
from qgis.gui import QgsVertexMarker
from qgis.core import Qgis, QgsJsonUtils, QgsWkbTypes
from .util import epsg4326, parseDMSString
from .utm import isUtm, utmString2Crs
# import traceback

from . import mgrs
from . import olc
from . import geohash
from .maidenhead import maidenGridCenter

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
        self.optionsButton.setIcon(QIcon(':/images/themes/default/mActionOptions.svg'))
        self.optionsButton.clicked.connect(self.showSettings)
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
        self.removeMarker()

        if self.settings.zoomToProjIsMGRS():
            # This is an MGRS coordinate
            self.label.setText("Enter MGRS Coordinate")
        elif self.settings.zoomToProjIsPlusCodes():
            self.label.setText("Enter Plus Codes")
        elif self.settings.zoomToProjIsGeohash():
            self.label.setText("Enter Geohash")
        elif self.settings.zoomToProjIsStandardUtm():
            self.label.setText("Enter Standard UTM")
        elif self.settings.zoomToProjIsMaidenhead():
            self.label.setText("Enter Maidenhead Grid")
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
        else:  # Default to custom CRS
            crsID = self.settings.zoomToCustomCrsId()
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("Enter {} Y,X".format(crsID))
            else:
                self.label.setText("Enter {} X,Y".format(crsID))

    def convertCoordinate(self, text):
        try:
            if self.settings.zoomToProjIsMGRS():
                # An MGRS coordinate only format has been specified. This will result in an exception
                # if it is not a valid MGRS coordinate
                text2 = re.sub(r'\s+', '', str(text))  # Remove all white space
                lat, lon = mgrs.toWgs(text2)
                return(lat, lon, epsg4326)

            if self.settings.zoomToProjIsPlusCodes():
                # A Plus Codes coordinate has been selected. This will result in an exception
                # if it is not a valid plus codes coordinate.
                coord = olc.decode(text)
                lat = coord.latitudeCenter
                lon = coord.longitudeCenter
                return(lat, lon, epsg4326)

            if self.settings.zoomToProjIsStandardUtm():
                # A Standard UTM coordinate has been selected. This will result in an exception
                # if it is not a valid utm coordinate.
                pt = utmString2Crs(text)
                return(pt.y(), pt.x(), epsg4326)

            if self.settings.zoomToProjIsGeohash():
                # A Geohash coordinate has been selected. This will result in an exception
                # if it is not a valid Geohash coordinate.
                (lat, lon) = geohash.decode(text)
                return(float(lat), float(lon), epsg4326)

            if self.settings.zoomToProjIsMaidenhead():
                # A Maidenhead grid coordinate has been selected. This will result in an exception
                # if it is not a valid maidenhead coordinate.
                (lat, lon) = maidenGridCenter(text)
                return(float(lat), float(lon), epsg4326)

            # Check for other formats
            if text[0] == '{':  # This may be a GeoJSON point
                codec = QTextCodec.codecForName("UTF-8")
                fields = QgsJsonUtils.stringToFields(text, codec)
                fet = QgsJsonUtils.stringToFeatureList(text, fields, codec)
                if (len(fet) == 0) or not fet[0].isValid():
                    raise ValueError('Invalid Coordinates')

                geom = fet[0].geometry()
                if geom.isEmpty() or (geom.wkbType() != QgsWkbTypes.Point):
                    raise ValueError('Invalid GeoJSON Geometry')
                pt = geom.asPoint()
                return(pt.y(), pt.x(), epsg4326)

            # Check to see if it is standard UTM
            if isUtm(text):
                pt = utmString2Crs(text)
                return(pt.y(), pt.x(), epsg4326)

            # Check to see if it is an MGRS coordinate
            try:
                text2 = re.sub(r'\s+', '', str(text))
                lat, lon = mgrs.toWgs(text2)
                return(lat, lon, epsg4326)
            except Exception:
                pass

            # Check to see if it is a plus codes string
            try:
                coord = olc.decode(text)
                lat = coord.latitudeCenter
                lon = coord.longitudeCenter
                return(lat, lon, epsg4326)
            except Exception:
                pass

            # Check to see if it is a WKT POINT format
            if re.search(r'POINT\(', text) is not None:
                m = re.findall(r'POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                if len(m) != 1:
                    raise ValueError('Invalid Coordinates')
                lon = float(m[0][0])
                lat = float(m[0][1])
                if self.settings.zoomToProjIsWgs84():
                    srcCrs = epsg4326
                elif self.settings.zoomToProjIsProjectCRS():
                    srcCrs = self.canvas.mapSettings().destinationCrs()
                else:
                    srcCrs = self.settings.zoomToCustomCRS()
                return(lat, lon, srcCrs)

            # We are left with either DMS or decimal degrees in one of the projections
            if self.settings.zoomToProjIsWgs84():
                lat, lon = parseDMSString(text, self.settings.zoomToCoordOrder)
                return(lat, lon, epsg4326)

            # We are left with a non WGS 84 decimal projection
            coords = re.split(r'[\s,;:]+', text, 1)
            if len(coords) < 2:
                raise ValueError('Invalid Coordinates')
            if self.settings.zoomToCoordOrder == self.settings.OrderYX:
                lat = float(coords[0])
                lon = float(coords[1])
            else:
                lon = float(coords[0])
                lat = float(coords[1])
            if self.settings.zoomToProjIsProjectCRS():
                srcCrs = self.canvas.mapSettings().destinationCrs()
            else:
                srcCrs = self.settings.zoomToCustomCRS()
            return(lat, lon, srcCrs)

        except Exception:
            raise ValueError('Invalid Coordinates')
        
    def zoomToPressed(self):
        try:
            text = self.coordTxt.text().strip()
            (lat, lon, srcCrs) = self.convertCoordinate(text)
            pt = self.lltools.zoomTo(srcCrs, lat, lon)
            if self.settings.persistentMarker:
                if self.marker is None:
                    self.marker = QgsVertexMarker(self.canvas)
                self.marker.setCenter(pt)
                self.marker.setIconSize(18)
                self.marker.setPenWidth(2)
                self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            elif self.marker is not None:
                self.removeMarker()
        except Exception:
            # traceback.print_exc()
            self.iface.messageBar().pushMessage("", "Invalid Coordinate", level=Qgis.Warning, duration=2)
            return

    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None
            self.coordTxt.clear()

    def showSettings(self):
        self.settings.showTab(1)
