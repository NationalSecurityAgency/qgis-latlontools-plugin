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

from qgis.PyQt.QtCore import QSize, QTextCodec
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog, QMenu
from qgis.PyQt.uic import loadUiType
from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsVectorDataProvider, QgsGeometry, QgsPointXY, QgsJsonUtils, QgsWkbTypes, QgsProject, QgsVectorLayerUtils, QgsSettings
from qgis.gui import QgsProjectionSelectionDialog
from .util import epsg4326, parseDMSString, tr
# import traceback

from . import mgrs
from . import olc
from .utm import utm2Point

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/digitizer.ui'))


class DigitizerWidget(QDialog, FORM_CLASS):
    inputProjection = 0
    inputXYOrder = 1

    def __init__(self, lltools, iface, parent):
        super(DigitizerWidget, self).__init__(parent)
        self.setupUi(self)
        self.lltools = lltools
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.xymenu = QMenu()
        icon = QIcon(os.path.dirname(__file__) + '/images/yx.svg')
        a = self.xymenu.addAction(icon, tr("Y, X (Lat, Lon) Order"))
        a.setData(0)
        icon = QIcon(os.path.dirname(__file__) + '/images/xy.svg')
        a = self.xymenu.addAction(icon, tr("X, Y (Lon, Lat) Order"))
        a.setData(1)
        self.xyButton.setIconSize(QSize(24, 24))
        self.xyButton.setIcon(icon)
        self.xyButton.setMenu(self.xymenu)
        self.xyButton.triggered.connect(self.xyTriggered)

        self.crsmenu = QMenu()
        icon = QIcon(os.path.dirname(__file__) + '/images/wgs84Projection.svg')
        a = self.crsmenu.addAction(icon, tr("WGS 84 (latitude & longitude)"))
        a.setData(0)
        icon = QIcon(os.path.dirname(__file__) + '/images/mgrsProjection.svg')
        a = self.crsmenu.addAction(icon, tr("MGRS"))
        a.setData(1)
        icon = QIcon(os.path.dirname(__file__) + '/images/projProjection.svg')
        a = self.crsmenu.addAction(icon, tr("Project CRS"))
        a.setData(2)
        icon = QIcon(os.path.dirname(__file__) + '/images/customProjection.svg')
        a = self.crsmenu.addAction(icon, tr("Specify CRS"))
        a.setData(3)
        icon = QIcon(os.path.dirname(__file__) + '/images/pluscodes.svg')
        a = self.crsmenu.addAction(icon, tr("Plus Codes"))
        a.setData(4)
        icon = QIcon(os.path.dirname(__file__) + '/images/utm.svg')
        a = self.crsmenu.addAction(icon, tr("UTM"))
        a.setData(5)
        self.crsButton.setIconSize(QSize(24, 24))
        self.crsButton.setIcon(icon)
        self.crsButton.setMenu(self.crsmenu)
        self.crsButton.triggered.connect(self.crsTriggered)
        self.iface.currentLayerChanged.connect(self.currentLayerChanged)

        self.addButton.clicked.connect(self.addFeature)
        self.exitButton.clicked.connect(self.exit)

        self.readSettings()
        self.configButtons()

    def currentLayerChanged(self):
        self.close()

    def showEvent(self, e):
        self.labelUpdate()

    def exit(self):
        self.close()

    def addFeature(self):
        text = self.lineEdit.text().strip()
        if text == "":
            return
        layer = self.iface.activeLayer()
        if layer is None:
            return
        try:
            if (self.inputProjection == 0) or (text[0] == '{'):
                # If this is GeoJson it does not matter what inputProjection is
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
                    lat = pt.y()
                    lon = pt.x()
                elif re.search(r'POINT\(', text) is not None:
                    m = re.findall(r'POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                    if len(m) != 1:
                        raise ValueError(tr('Invalid Coordinates'))
                    lon = float(m[0][0])
                    lat = float(m[0][1])
                else:
                    lat, lon = parseDMSString(text, self.inputXYOrder)
                srcCrs = epsg4326
            elif self.inputProjection == 1:
                # This is an MGRS coordinate
                text = re.sub(r'\s+', '', text)  # Remove all white space
                lat, lon = mgrs.toWgs(text)
                srcCrs = epsg4326
            elif self.inputProjection == 4:
                text = text.strip()
                coord = olc.decode(text)
                lat = coord.latitudeCenter
                lon = coord.longitudeCenter
                srcCrs = epsg4326
            elif self.inputProjection == 5:
                text = text.strip()
                pt = utm2Point(text, epsg4326)
                lat = pt.y()
                lon = pt.x()
                srcCrs = epsg4326
            else:  # Is either the project or custom CRS
                if re.search(r'POINT\(', text) is None:
                    coords = re.split(r'[\s,;:]+', text, 1)
                    if len(coords) < 2:
                        raise ValueError('Invalid Coordinates')
                    if self.inputXYOrder == 0:  # Y, X Order
                        lat = float(coords[0])
                        lon = float(coords[1])
                    else:
                        lon = float(coords[0])
                        lat = float(coords[1])
                else:
                    m = re.findall(r'POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                    if len(m) != 1:
                        raise ValueError(tr('Invalid Coordinates'))
                    lon = float(m[0][0])
                    lat = float(m[0][1])
                if self.inputProjection == 2:  # Project CRS
                    srcCrs = self.canvas.mapSettings().destinationCrs()
                else:
                    srcCrs = QgsCoordinateReferenceSystem(self.inputCustomCRS)
        except Exception:
            # traceback.print_exc()
            self.iface.messageBar().pushMessage("", tr("Invalid Coordinate"), level=Qgis.Warning, duration=2)
            return
        self.lineEdit.clear()
        caps = layer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.AddFeatures:
            destCRS = layer.crs()  # Get the CRS of the layer we are adding a point toWgs
            transform = QgsCoordinateTransform(srcCrs, destCRS, QgsProject.instance())
            # Transform the input coordinate projection to the layer CRS
            x, y = transform.transform(float(lon), float(lat))
            geom = QgsGeometry.fromPointXY(QgsPointXY(x, y))
            result = self.iface.vectorLayerTools().addFeature( layer, {}, geom)
            if result[0]:
                self.lltools.zoomTo(srcCrs, lat, lon)

    def labelUpdate(self):
        if self.inputProjection == 1:  # MGRS projection
            self.infoLabel.setText(tr('Input Coordinate: MGRS'))
            return
        if self.inputProjection == 4:  # Plus Codes projection
            self.infoLabel.setText(tr('Input Coordinate: Plus Codes'))
            return
        if self.inputProjection == 5:  # UTM
            self.infoLabel.setText(tr('Input Coordinate: UTM'))
            return
        if self.isWgs84():
            if self.inputXYOrder == 0:
                o = tr("Lat, Lon")
            else:
                o = tr("Lon, Lat")
            proj = "Wgs84"
        else:
            if self.inputXYOrder == 0:
                o = tr("Y, X")
            else:
                o = tr("X, Y")
            if self.inputProjection == 2:  # Project Projection
                proj = self.canvas.mapSettings().destinationCrs().authid()
            else:
                proj = self.inputCustomCRS
        s = "Input Projection: {} - {}: {}".format(proj, tr('Coordinate Order'), o)
        self.infoLabel.setText(s)

    def configButtons(self):
        self.xyButton.setDefaultAction(self.xymenu.actions()[self.inputXYOrder])
        self.crsButton.setDefaultAction(self.crsmenu.actions()[self.inputProjection])

    def readSettings(self):
        settings = QgsSettings()
        self.inputProjection = int(settings.value('/LatLonTools/DigitizerProjection', 0))
        self.inputXYOrder = int(settings.value('/LatLonTools/DigitizerXYOrder', 0))
        self.inputCustomCRS = settings.value('/LatLonTools/DigitizerCustomCRS', 'EPSG:4326')
        if self.inputProjection < 0 or self.inputProjection > 4:
            self.inputProjection = 0
        if self.inputXYOrder < 0 or self.inputXYOrder > 1:
            self.inputXYOrder = 1
        self.labelUpdate()

    def saveSettings(self):
        settings = QgsSettings()
        settings.setValue('/LatLonTools/DigitizerProjection', self.inputProjection)
        settings.setValue('/LatLonTools/DigitizerXYOrder', self.inputXYOrder)
        settings.setValue('/LatLonTools/DigitizerCustomCRS', self.inputCustomCRS)
        self.labelUpdate()

    def crsTriggered(self, action):
        self.crsButton.setDefaultAction(action)
        self.inputProjection = action.data()
        if self.inputProjection == 3:
            selector = QgsProjectionSelectionDialog()
            selector.setCrs(QgsCoordinateReferenceSystem(self.inputCustomCRS))
            if selector.exec():
                self.inputCustomCRS = selector.crs().authid()
            else:
                self.inputCustomCRS = 'EPSG:4326'
        self.saveSettings()

    def xyTriggered(self, action):
        self.xyButton.setDefaultAction(action)
        self.inputXYOrder = action.data()
        self.saveSettings()

    def isWgs84(self):
        if self.inputProjection == 0:  # WGS 84
            return True
        elif self.inputProjection == 2:  # Projection Projection
            if self.canvas.mapSettings().destinationCrs() == epsg4326:
                return True
        return False
