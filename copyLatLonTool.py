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
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import Qgis, QgsCoordinateTransform, QgsPointXY, QgsProject, QgsSettings
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker

from .settings import settings, CoordOrder, H3_INSTALLED
from .util import epsg4326, formatDmsString, formatMgrsString, tr
from .utm import latLon2Utm
from .ups import latLon2Ups
from . import mgrs
from . import olc
from . import geohash
from . import maidenhead
from . import georef
if H3_INSTALLED:
    import h3

# import traceback

class CopyLatLonTool(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    captureStopped = pyqtSignal()

    def __init__(self, settings, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.settings = settings
        self.marker = None
        self.vertex = None

    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        self.snapcolor = QgsSettings().value( "/qgis/digitizing/snap_color" , QColor( Qt.magenta ) )

    def deactivate(self):
        self.removeMarker()
        self.removeVertexMarker()
        self.captureStopped.emit()

    def formatCoord(self, pt, delimiter):
        '''Format the coordinate string according to the settings from
        the settings dialog.'''
        if self.settings.captureProjIsWgs84():  # ProjectionTypeWgs84
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            lat = pt4326.y()
            lon = pt4326.x()
            if self.settings.wgs84NumberFormat == self.settings.Wgs84TypeDMS:  # DMS
                msg = formatDmsString(lat, lon, 0, self.settings.dmsPrecision, self.settings.coordOrder, delimiter, settings.captureAddDmsSpace, settings.capturePadZeroes)
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeDDMMSS:  # DDMMSS
                msg = formatDmsString(lat, lon, 1, self.settings.dmsPrecision, self.settings.coordOrder, delimiter, settings.captureAddDmsSpace, settings.capturePadZeroes)
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeDMM:  # DM.MM
                msg = formatDmsString(lat, lon, 2, settings.captureDmmPrecision, self.settings.coordOrder, delimiter, settings.captureAddDmsSpace, settings.capturePadZeroes)
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeWKT:  # WKT
                msg = 'POINT({:.{prec}f} {:.{prec}f})'.format(pt4326.x(), pt4326.y(), prec=self.settings.decimalDigits)
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeGeoJSON:  # GeoJSON
                msg = '{{"type": "Point","coordinates": [{:.{prec}f},{:.{prec}f}]}}'.format(pt4326.x(), pt4326.y(), prec=self.settings.decimalDigits)
            else:  # decimal degrees
                if self.settings.coordOrder == CoordOrder.OrderYX:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt4326.y(), delimiter, pt4326.x(), prec=self.settings.decimalDigits)
                else:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt4326.x(), delimiter, pt4326.y(), prec=self.settings.decimalDigits)
        elif self.settings.captureProjIsProjectCRS():
            # Projection in the project CRS
            if self.settings.otherNumberFormat == 0:  # Numerical
                if self.settings.coordOrder == CoordOrder.OrderYX:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.y(), delimiter, pt.x(), prec=self.settings.decimalDigits)
                else:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.x(), delimiter, pt.y(), prec=self.settings.decimalDigits)
            else:
                msg = 'POINT({:.{prec}f} {:.{prec}f})'.format(pt.x(), pt.y(), prec=self.settings.decimalDigits)
        elif self.settings.captureProjIsCustomCRS():
            # Projection is a custom CRS
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            customCRS = self.settings.captureCustomCRS()
            transform = QgsCoordinateTransform(canvasCRS, customCRS, QgsProject.instance())
            pt = transform.transform(pt.x(), pt.y())
            if self.settings.otherNumberFormat == 0:  # Numerical
                if self.settings.coordOrder == CoordOrder.OrderYX:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.y(), delimiter, pt.x(), prec=self.settings.decimalDigits)
                else:
                    msg = '{:.{prec}f}{}{:.{prec}f}'.format(pt.x(), delimiter, pt.y(), prec=self.settings.decimalDigits)
            else:
                msg = 'POINT({:.{prec}f} {:.{prec}f})'.format(pt.x(), pt.y(), prec=self.settings.decimalDigits)
        elif self.settings.captureProjIsMGRS():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            try:
                msg = mgrs.toMgrs(pt4326.y(), pt4326.x(), settings.captureMgrsPrec)
                msg = formatMgrsString(msg, settings.captureMgrsAddSpacesCheckBox)
            except Exception:
                # traceback.print_exc()
                msg = None
        elif self.settings.captureProjIsPlusCodes():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            try:
                msg = olc.encode(pt4326.y(), pt4326.x(), self.settings.plusCodesLength)
            except Exception:
                msg = None
        elif self.settings.captureProjIsUTM():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            msg = latLon2Utm(pt4326.y(), pt4326.x(), settings.captureUtmPrecision, settings.captureUtmFormat)
            if msg == '':
                msg = None
        elif self.settings.captureProjIsUPS():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            msg = latLon2Ups(pt4326.y(), pt4326.x(), settings.captureUpsPrecision, settings.captureUpsFormat)
            if msg == '':
                msg = None
        elif self.settings.captureProjIsGeohash():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            msg = geohash.encode(pt4326.y(), pt4326.x(), settings.captureGeohashPrecision)
            if msg == '':
                msg = None
        elif self.settings.captureProjIsH3():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            if H3_INSTALLED:
                msg = h3.geo_to_h3(pt4326.y(), pt4326.x(), settings.captureH3Precision)
                if msg == 0:
                    msg = None
            else:
                msg = None
        elif self.settings.captureProjIsMaidenhead():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            try:
                msg = maidenhead.toMaiden(pt4326.y(), pt4326.x(), precision=settings.captureMaidenheadPrecision)
            except Exception:
                msg = None
        elif self.settings.captureProjIsGEOREF():
            # Make sure the coordinate is transformed to EPSG:4326
            canvasCRS = self.canvas.mapSettings().destinationCrs()
            if canvasCRS == epsg4326:
                pt4326 = pt
            else:
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
            try:
                msg = georef.encode(pt4326.y(), pt4326.x(), settings.captureGeorefPrecision)
            except Exception:
                msg = None

        if msg is None:
            return(None)
        else:
            msg = '{}{}{}'.format(self.settings.capturePrefix, msg, self.settings.captureSuffix)
        return msg

    def canvasMoveEvent(self, event):
        '''Capture the coordinate as the user moves the mouse over
        the canvas. Show it in the status bar.'''
        pt = self.snappoint(event.originalPixelPoint()) # input is QPoint
        try:
            msg = self.formatCoord(pt, ', ')
            formatString = self.coordFormatString()
            if msg is None:
                self.iface.statusBarIface().showMessage("{} - {}".format(formatString, tr('Out of bounds')), 4000)
            else:
                self.iface.statusBarIface().showMessage("{} - {}".format(msg, formatString), 4000)
        except Exception:
            self.iface.statusBarIface().showMessage("")

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

    def coordFormatString(self):
        if self.settings.captureProjIsWgs84():
            if self.settings.wgs84NumberFormat == self.settings.Wgs84TypeDecimal:
                if self.settings.coordOrder == CoordOrder.OrderYX:
                    s = 'Lat Lon'
                else:
                    s = 'Lon Lat'
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeWKT:
                s = 'WKT'
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeGeoJSON:
                s = 'GeoJSON'
            elif self.settings.wgs84NumberFormat == self.settings.Wgs84TypeDMM:
                s= 'DM.MM'
            else:
                s = 'DMS'
        elif self.settings.captureProjIsProjectCRS():
            crsID = self.canvas.mapSettings().destinationCrs().authid()
            if self.settings.otherNumberFormat == 0:  # Numerical
                if self.settings.coordOrder == CoordOrder.OrderYX:
                    s = '{} - Y,X'.format(crsID)
                else:
                    s = '{} - X,Y'.format(crsID)
            else:  # WKT
                s = 'WKT'
        elif self.settings.captureProjIsMGRS():
            s = 'MGRS'
        elif self.settings.captureProjIsUTM():
            s = 'Standard UTM'
        elif self.settings.captureProjIsUPS():
            s = 'UPS'
        elif self.settings.captureProjIsPlusCodes():
            s = 'Plus Codes'
        elif self.settings.captureProjIsGeohash():
            s = 'Geohash'
        elif self.settings.captureProjIsH3():
            s = 'H3'
        elif self.settings.captureProjIsMaidenhead():
            s = 'Maidenhead Grid Locator'
        elif self.settings.captureProjIsGEOREF():
            s = 'GEOREF'
        elif self.settings.captureProjIsCustomCRS():
            if self.settings.otherNumberFormat == 0:  # Numerical
                if self.settings.coordOrder == CoordOrder.OrderYX:
                    s = '{} - Y,X'.format(self.settings.captureCustomCRSID())
                else:
                    s = '{} - X,Y'.format(self.settings.captureCustomCRSID())
            else:  # WKT
                s = 'WKT'
        else:  # Should never happen
            s = ''
        return s

    def canvasReleaseEvent(self, event):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard. pt is QgsPointXY'''
        pt = self.snappoint(event.originalPixelPoint())
        self.removeVertexMarker()
        if settings.captureShowLocation:
            if self.marker is None:
                self.marker = QgsVertexMarker(self.canvas)
                self.marker.setIconSize(18)
                self.marker.setPenWidth(2)
                self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            self.marker.setCenter(pt)
        else:
            self.removeMarker()

        try:
            msg = self.formatCoord(pt, self.settings.delimiter)
            formatString = self.coordFormatString()
            if msg is not None:
                clipboard = QApplication.clipboard()
                clipboard.setText(msg)
                self.iface.messageBar().pushMessage("", "{} {} {} {}".format(formatString, tr('coordinate'), msg, tr('copied to the clipboard')), level=Qgis.Info, duration=3)
        except Exception as e:
            self.iface.messageBar().pushMessage("", "{} {}".format(tr('Invalid coordinate:'), e), level=Qgis.Warning, duration=3)

    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None

    def removeVertexMarker(self):
        if self.vertex is not None:
            self.canvas.scene().removeItem(self.vertex)
            self.vertex = None
