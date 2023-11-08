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
import os
import re

from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QDockWidget, QApplication, QMenu
from qgis.PyQt.QtCore import QTextCodec
from qgis.gui import QgsRubberBand, QgsProjectionSelectionDialog
from qgis.core import Qgis, QgsJsonUtils, QgsWkbTypes, QgsPointXY, QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsRectangle
from .util import epsg4326, parseDMSString, tr
from .settings import settings, CoordOrder, H3_INSTALLED
from .utm import isUtm, utm2Point
from .ups import isUps, ups2Point
import traceback

from . import mgrs
from . import olc
from . import geohash
from .maidenhead import maidenGrid
from . import georef
if H3_INSTALLED:
    import h3

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/zoomToLatLon.ui'))


class ZoomToLatLon(QDockWidget, FORM_CLASS):

    def __init__(self, lltools, iface, parent):
        super(ZoomToLatLon, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()
        self.clipboard = QApplication.clipboard()
        self.zoomToolButton.setIcon(QIcon(':/images/themes/default/mActionZoomIn.svg'))
        self.clearToolButton.setIcon(QIcon(':/images/themes/default/mIconClearText.svg'))
        self.pasteButton.setIcon(QIcon(':/images/themes/default/mActionEditPaste.svg'))
        self.zoomToolButton.clicked.connect(self.zoomToPressed)
        self.clearToolButton.clicked.connect(self.removeMarker)
        self.pasteButton.clicked.connect(self.pasteCoordinate)
        self.optionsButton.setIcon(QIcon(':/images/themes/default/mActionOptions.svg'))
        self.optionsButton.clicked.connect(self.showSettings)
        self.xyIcon = QIcon(os.path.dirname(__file__) + '/images/xy.svg')
        self.yxIcon = QIcon(os.path.dirname(__file__) + '/images/yx.svg')
        self.xyButton.setIcon(self.yxIcon)
        self.xyButton.clicked.connect(self.xyButtonClicked)
        self.crsButton.setIcon(QIcon(':/images/themes/default/mIconProjectionEnabled.svg'))
        self.crsmenu = QMenu()
        a = self.crsmenu.addAction(tr("WGS 84"))
        a.setData('wgs84')
        a = self.crsmenu.addAction(tr("Project CRS"))
        a.setData('project')
        a = self.crsmenu.addAction(tr("Custom CRS"))
        a.setData('custom')
        a = self.crsmenu.addAction(tr("MGRS"))
        a.setData('mgrs')
        a = self.crsmenu.addAction(tr("Plus Codes"))
        a.setData('pluscode')
        a = self.crsmenu.addAction(tr("Standard UTM"))
        a.setData('utm')
        a = self.crsmenu.addAction(tr("Geohash"))
        a.setData('geohash')
        a = self.crsmenu.addAction(tr("Maidenhead Grid"))
        a.setData('ham')
        if H3_INSTALLED:
            a = self.crsmenu.addAction(tr("H3"))
            a.setData('h3')
        self.crsButton.setMenu(self.crsmenu)
        self.crsButton.triggered.connect(self.crsTriggered)
        self.lltools = lltools
        self.settings = lltools.settingsDialog
        self.iface = iface
        self.coordTxt.returnPressed.connect(self.zoomToPressed)
        self.canvas.destinationCrsChanged.connect(self.crsChanged)
        
        self.marker = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.marker.setColor(settings.markerColor)
        self.marker.setStrokeColor(settings.markerColor)
        self.marker.setWidth(settings.markerWidth)
        self.marker.setIconSize(settings.markerSize)
        self.marker.setIcon(QgsRubberBand.ICON_CROSS)
        
        self.line_marker = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.line_marker.setWidth(settings.gridWidth)
        self.line_marker.setColor(settings.gridColor)
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
            self.label.setText(tr("Enter MGRS Coordinate"))
        elif self.settings.zoomToProjIsPlusCodes():
            self.label.setText(tr("Enter Plus Codes"))
        elif self.settings.zoomToProjIsGeohash():
            self.label.setText(tr("Enter Geohash"))
        elif self.settings.zoomToProjIsH3():
            self.label.setText(tr("Enter H3 geohash"))
        elif self.settings.zoomToProjIsStandardUtm():
            self.label.setText(tr("Enter Standard UTM"))
        elif self.settings.zoomToProjIsMaidenhead():
            self.label.setText(tr("Enter Maidenhead Grid"))
        elif self.settings.zoomToProjIsWgs84():
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText(tr("Enter 'Latitude, Longitude'"))
            else:
                self.label.setText(tr("Enter 'Longitude, Latitude'"))
        elif self.settings.zoomToProjIsProjectCRS():
            crsID = self.canvas.mapSettings().destinationCrs().authid()
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("{} {} Y,X".format(tr('Enter'), crsID))
            else:
                self.label.setText("{} {} X,Y".format(tr('Enter'), crsID))
        else:  # Default to custom CRS
            crsID = self.settings.zoomToCustomCrsId()
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("{} {} Y,X".format(tr('Enter'), crsID))
            else:
                self.label.setText("{} {} X,Y".format(tr('Enter'), crsID))
        if self.settings.zoomToCoordOrder == 0:
            self.xyButton.setIcon(self.yxIcon)
        else:
            self.xyButton.setIcon(self.xyIcon)

    def convertCoordinate(self, text):
        try:
            if self.settings.zoomToProjIsMGRS():
                # An MGRS coordinate only format has been specified. This will result in an exception
                # if it is not a valid MGRS coordinate
                text2 = re.sub(r'\s+', '', str(text))  # Remove all white space
                lat, lon = mgrs.toWgs(text2)
                return(lat, lon, None, epsg4326)

            if self.settings.zoomToProjIsPlusCodes():
                # A Plus Codes coordinate has been selected. This will result in an exception
                # if it is not a valid plus codes coordinate.
                coord = olc.decode(text)
                lat = coord.latitudeCenter
                lon = coord.longitudeCenter
                rect = QgsRectangle(coord.longitudeLo, coord.latitudeLo, coord.longitudeHi, coord.latitudeHi)
                geom = QgsGeometry.fromRect(rect)
                return(lat, lon, geom, epsg4326)

            if self.settings.zoomToProjIsStandardUtm():
                # A Standard UTM coordinate has been selected. This will result in an exception
                # if it is not a valid utm coordinate.
                pt = utm2Point(text)
                return(pt.y(), pt.x(), None, epsg4326)

            if self.settings.zoomToProjIsGeohash():
                # A Geohash coordinate has been selected. This will result in an exception
                # if it is not a valid Geohash coordinate.
                (lat1, lat2, lon1, lon2) = geohash.decode_extent(text)
                lat = (lat1 + lat2) / 2
                lon = (lon1 + lon2) / 2
                rect = QgsRectangle(lon1, lat1, lon2, lat2)
                geom = QgsGeometry.fromRect(rect)
                return(lat, lon, geom, epsg4326)

            if self.settings.zoomToProjIsH3():
                # An H3 coordinate has been selected. 
                if not h3.h3_is_valid(text):
                    raise ValueError(tr('Invalid H3 Coordinate'))
                (lat, lon) = h3.h3_to_geo(text)
                coords = h3.h3_to_geo_boundary(text)
                pts = []
                for p in coords:
                    pt = QgsPointXY(p[1], p[0])
                    pts.append(pt)
                pts.append(pts[0])  # Close the polygon
                geom = QgsGeometry.fromPolylineXY(pts)
                return(lat, lon, geom, epsg4326)

            if self.settings.zoomToProjIsMaidenhead():
                # A Maidenhead grid coordinate has been selected. This will result in an exception
                # if it is not a valid maidenhead coordinate.
                (lat, lon, lat1, lon1, lat2, lon2) = maidenGrid(text)
                rect = QgsRectangle(lon1, lat1, lon2, lat2)
                geom = QgsGeometry.fromRect(rect)
                return(float(lat), float(lon), geom, epsg4326)

            # Check for other formats
            if text[0] == '{':  # This may be a GeoJSON point
                codec = QTextCodec.codecForName("UTF-8")
                fields = QgsJsonUtils.stringToFields(text, codec)
                fet = QgsJsonUtils.stringToFeatureList(text, fields, codec)
                if (len(fet) == 0) or not fet[0].isValid():
                    raise ValueError(tr('Invalid Coordinates'))

                geom = fet[0].geometry()
                if geom.isEmpty() or (geom.wkbType() != QgsWkbTypes.Point):
                    raise ValueError(tr('Invalid GeoJSON Geometry'))
                pt = geom.asPoint()
                return(pt.y(), pt.x(), None, epsg4326)

            # Check to see if it is standard UTM
            if isUtm(text):
                pt = utm2Point(text)
                return(pt.y(), pt.x(), None, epsg4326)

            # Check to see if it is a UPS coordinate
            if isUps(text):
                pt = ups2Point(text)
                return(pt.y(), pt.x(), None, epsg4326)

            # Check to see if it is a Georef coordinate
            try:
                (lat, lon, prec) = georef.decode(text, False)
                return(lat, lon, None, epsg4326)
            except Exception:
                pass

            # Check to see if it is an MGRS coordinate
            try:
                text2 = re.sub(r'\s+', '', str(text))
                lat, lon = mgrs.toWgs(text2)
                return(lat, lon, None, epsg4326)
            except Exception:
                pass

            # Check to see if it is a plus codes string
            try:
                coord = olc.decode(text)
                lat = coord.latitudeCenter
                lon = coord.longitudeCenter
                return(lat, lon, None, epsg4326)
            except Exception:
                pass

            # Check to see if it is a geohash string
            try:
                (lat, lon, lat_err, lon_err) = geohash.decode_exactly(text)
                return(lat, lon, None, epsg4326)
            except Exception:
                pass

            # Check to see if it is a WKT POINT format
            if re.search(r'POINT\(', text) is not None:
                m = re.findall(r'POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                if len(m) != 1:
                    raise ValueError(tr('Invalid Coordinates'))
                lon = float(m[0][0])
                lat = float(m[0][1])
                if self.settings.zoomToProjIsWgs84():
                    srcCrs = epsg4326
                elif self.settings.zoomToProjIsProjectCRS():
                    srcCrs = self.canvas.mapSettings().destinationCrs()
                else:
                    srcCrs = self.settings.zoomToCustomCRS()
                return(lat, lon, None, srcCrs)

            # We are left with either DMS or decimal degrees in one of the projections
            if self.settings.zoomToProjIsWgs84():
                lat, lon = parseDMSString(text, self.settings.zoomToCoordOrder)
                return(lat, lon, None, epsg4326)

            # We are left with a non WGS 84 decimal projection
            coords = re.split(r'[\s,;:]+', text, 1)
            if len(coords) < 2:
                raise ValueError(tr('Invalid Coordinates'))
            if self.settings.zoomToCoordOrder == CoordOrder.OrderYX:
                lat = float(coords[0])
                lon = float(coords[1])
            else:
                lon = float(coords[0])
                lat = float(coords[1])
            if self.settings.zoomToProjIsProjectCRS():
                srcCrs = self.canvas.mapSettings().destinationCrs()
            else:
                srcCrs = self.settings.zoomToCustomCRS()
            return(lat, lon, None, srcCrs)

        except Exception:
            traceback.print_exc()
            raise ValueError(tr('Invalid Coordinates'))
        
    def zoomToPressed(self):
        try:
            text = self.coordTxt.text().strip()
            (lat, lon, bounds, srcCrs) = self.convertCoordinate(text)
            pt = self.lltools.zoomTo(srcCrs, lat, lon)
            self.marker.reset(QgsWkbTypes.PointGeometry)
            self.marker.setWidth(settings.markerWidth)
            self.marker.setIconSize(settings.markerSize)
            self.marker.setColor(settings.markerColor)
            if self.settings.persistentMarker:
                self.marker.addPoint(pt)
            self.line_marker.reset(QgsWkbTypes.LineGeometry)
            self.line_marker.setWidth(settings.gridWidth)
            self.line_marker.setColor(settings.gridColor)
            if bounds and self.settings.showGrid:
                canvas_crs = self.canvas.mapSettings().destinationCrs()
                if srcCrs != canvas_crs:
                    trans = QgsCoordinateTransform(srcCrs, canvas_crs, QgsProject.instance())
                    bounds.transform(trans)
                self.line_marker.addGeometry(bounds, None)
        except Exception:
            traceback.print_exc()
            self.iface.messageBar().pushMessage("", tr("Invalid Coordinate"), level=Qgis.Warning, duration=2)
            return

    def pasteCoordinate(self):
        text = self.clipboard.text().strip()
        self.coordTxt.clear()
        self.coordTxt.setText(text)
        
    def removeMarker(self):
        self.marker.reset(QgsWkbTypes.PointGeometry)
        self.line_marker.reset(QgsWkbTypes.LineGeometry)
        self.coordTxt.clear()

    def showSettings(self):
        self.settings.showTab(1)

    def xyButtonClicked(self):
        if self.settings.zoomToCoordOrder == 0:
            self.settings.setZoomToCoordOrder(1)
        else:
            self.settings.setZoomToCoordOrder(0)
        self.configure()

    def crsTriggered(self, action):
        selection_id = action.data()
        crs = None
        if selection_id == 'custom':
            selector = QgsProjectionSelectionDialog()
            selector.setCrs(QgsCoordinateReferenceSystem(self.settings.zoomToCustomCRS()))
            if selector.exec():
                crs = selector.crs()
        self.settings.setZoomToMode(selection_id, crs)
        self.configure()

