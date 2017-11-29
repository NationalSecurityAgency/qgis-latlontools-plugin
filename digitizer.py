import os
import re

from qgis.PyQt.QtCore import QSize, QSettings, QTextCodec
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog, QMenu, QToolButton
from qgis.PyQt.uic import loadUiType
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsVectorDataProvider, QgsFeature, QgsGeometry, QgsPointXY, QgsJsonUtils, QgsWkbTypes
from qgis.gui import QgsMessageBar, QgsProjectionSelectionTreeWidget
from .LatLon import LatLon
from .util import *
#import traceback

from . import mgrs

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
        icon = QIcon(os.path.dirname(__file__) + '/images/yx.png')
        a = self.xymenu.addAction(icon, "Y, X (Lat, Lon) Order")
        a.setData(0)
        icon = QIcon(os.path.dirname(__file__) + '/images/xy.png')
        a = self.xymenu.addAction(icon, "X, Y (Lon, Lat) Order")
        a.setData(1)
        self.xyButton.setIconSize(QSize(24,24))
        self.xyButton.setIcon(icon)
        self.xyButton.setMenu(self.xymenu)
        self.xyButton.triggered.connect(self.xyTriggered)
        
        self.crsmenu = QMenu()
        icon = QIcon(os.path.dirname(__file__) + '/images/wgs84Projection.png')
        a = self.crsmenu.addAction(icon, "WGS 84 (latitude & longitude)")
        a.setData(0)
        icon = QIcon(os.path.dirname(__file__) + '/images/mgrsProjection.png')
        a = self.crsmenu.addAction(icon, "MGRS")
        a.setData(1)
        icon = QIcon(os.path.dirname(__file__) + '/images/projProjection.png')
        a = self.crsmenu.addAction(icon, "Project CRS")
        a.setData(2)
        icon = QIcon(os.path.dirname(__file__) + '/images/customProjection.png')
        a = self.crsmenu.addAction(icon, "Specify CRS")
        a.setData(3)
        self.crsButton.setIconSize(QSize(24,24))
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
        if layer == None:
            return
        try:
            if (self.inputProjection == 0) or (text[0] == '{'):
                # If this is GeoJson it does not matter what inputProjection is
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
                elif re.search('POINT\(', text) != None:
                    m = re.findall('POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                    if len(m) != 1:
                        raise ValueError('Invalid Coordinates')
                    lon = float(m[0][0])
                    lat = float(m[0][1])
                else:
                    lat, lon = LatLon.parseDMSString(text, self.inputXYOrder)
                srcCrs = epsg4326
            elif self.inputProjection == 1:
                # This is an MGRS coordinate
                text = re.sub(r'\s+', '', unicode(text)) # Remove all white space
                lat, lon = mgrs.toWgs(text)
                srcCrs = epsg4326
            else: # Is either the project or custom CRS
                if re.search('POINT\(', text) == None:
                    coords = re.split('[\s,;:]+', text, 1)
                    if len(coords) < 2:
                        raise ValueError('Invalid Coordinates')
                    if self.inputXYOrder == 0: # Y, X Order
                        lat = float(coords[0])
                        lon = float(coords[1])
                    else:
                        lon = float(coords[0])
                        lat = float(coords[1])
                else:
                    m = re.findall('POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                    if len(m) != 1:
                        raise ValueError('Invalid Coordinates')
                    lon = float(m[0][0])
                    lat = float(m[0][1])
                if self.inputProjection == 2: # Project CRS
                    srcCrs = self.canvas.mapSettings().destinationCrs()
                else:
                    srcCrs = QgsCoordinateReferenceSystem().createFromString(self.inputCustomCRS)
        except:
            #traceback.print_exc()
            self.iface.messageBar().pushMessage("", "Invalid Coordinate" , level=QgsMessageBar.WARNING, duration=2)
            return
        self.lineEdit.clear()
        caps = layer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.AddFeatures:
            destCRS = layer.crs() # Get the CRS of the layer we are adding a point toWgs
            transform = QgsCoordinateTransform(srcCrs, destCRS) 
            # Transform the input coordinate projection to the layer CRS
            x, y = transform.transform(float(lon), float(lat))
            feat = QgsFeature(layer.pendingFields())
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x,y)))
            if layer.pendingFields().count() == 0:
                layer.addFeature(feat)
                self.lltools.zoomTo(srcCrs, lat, lon)
            else:
                if self.iface.openFeatureForm(layer, feat):
                    layer.addFeature(feat)
                    self.lltools.zoomTo(srcCrs, lat, lon)
        
    def labelUpdate(self):
        #print "labelUpdate"
        if self.inputProjection == 1: # MGRS projection
            self.infoLabel.setText('Input Projection: MGRS')
            return
        if self.isWgs84():
            if self.inputXYOrder == 0:
                o = "Lat, Lon"
            else:
                o = "Lon, Lat"
            proj = "Wgs84"
        else:
            if self.inputXYOrder == 0:
                o = "Y, X"
            else:
                o = "X, Y"
            if self.inputProjection == 2: # Project Projection
                proj = self.canvas.mapSettings().destinationCrs().authid()
            else:
                proj = self.inputCustomCRS
        s = "Input Projection: {} - Coordinate Order: {}".format(proj, o)
        self.infoLabel.setText(s)
        
    def configButtons(self):
        self.xyButton.setDefaultAction(self.xymenu.actions()[self.inputXYOrder])
        self.crsButton.setDefaultAction(self.crsmenu.actions()[self.inputProjection])
        
    def readSettings(self):
        settings = QSettings()
        self.inputProjection = int(settings.value('/LatLonTools/DigitizerProjection', 0))
        self.inputXYOrder = int(settings.value('/LatLonTools/DigitizerXYOrder', 0))
        self.inputCustomCRS = settings.value('/LatLonTools/DigitizerCustomCRS', 'EPSG:4326')
        if self.inputProjection < 0 or self.inputProjection > 3:
            self.inputProjection = 0
        if self.inputXYOrder < 0 or self.inputXYOrder > 1:
            self.inputXYOrder = 1
        self.labelUpdate()
        
    def saveSettings(self):
        settings = QSettings()
        settings.setValue('/LatLonTools/DigitizerProjection', self.inputProjection)
        settings.setValue('/LatLonTools/DigitizerXYOrder', self.inputXYOrder)
        settings.setValue('/LatLonTools/DigitizerCustomCRS', self.inputCustomCRS)
        self.labelUpdate()
        
    def crsTriggered(self, action):
        self.crsButton.setDefaultAction(action)
        self.inputProjection = action.data()
        if self.inputProjection == 3:
            selector = QgsProjectionSelectionTreeWidget()
            selector.setOgcWmsCrsFilter(self.inputCustomCRS)
            if selector.exec_():
                self.inputCustomCRS = selector.crs().authid()
            else:
                self.inputCustomCRS = 'EPSG:4326'
        self.saveSettings()
        
    def xyTriggered(self, action):
        self.xyButton.setDefaultAction(action)
        self.inputXYOrder = action.data()
        self.saveSettings()

    def isWgs84(self):
        if self.inputProjection == 0: # WGS 84
            return True
        elif self.inputProjection == 2: # Projection Projection
            if self.canvas.mapSettings().destinationCrs() == epsg4326:
                return True
        return False