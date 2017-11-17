import os
import re

from PyQt4.QtCore import QSize, QSettings
from PyQt4.QtGui import QDialog, QIcon, QMenu, QToolButton
from PyQt4.uic import loadUiType
from qgis.core import QgsCoordinateReferenceSystem, QgsVectorDataProvider, QgsFeature, QgsGeometry, QgsPoint
from qgis.gui import QgsMessageBar
from LatLon import LatLon
#import traceback

import mgrs

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/digitizer.ui'))
    
    
epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')


class DigitizerWidget(QDialog, FORM_CLASS):
    inputProjection = 0
    inputXYOrder = 1
    
    def __init__(self, lltools, iface, parent):
        super(DigitizerWidget, self).__init__(parent)
        self.setupUi(self)
        self.lltools = lltools
        self.iface = iface
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
        
        self.readSettings()
        self.configButtons()
        
        
    def accept(self):
        print "accept"
        text = self.lineEdit.text().strip()
        layer = self.iface.activeLayer()
        if layer == None:
            return
        try:
            if self.inputProjection == 0:
                if re.search('POINT\(', text) == None:
                    lat, lon = LatLon.parseDMSString(text, self.inputXYOrder)
                else:
                    m = re.findall('POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                    if len(m) != 1:
                        print "Here 1"
                        raise ValueError('Invalid Coordinates')
                    lon = float(m[0][0])
                    lat = float(m[0][1])
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
                        print "Here 2"
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
                        print "Here 3"
                        raise ValueError('Invalid Coordinates')
                    lon = float(m[0][0])
                    lat = float(m[0][1])
                if self.inputProjection == 2: # Project CRS
                    srcCrs = self.canvas.mapSettings().destinationCrs()
                else:
                    srcCrs = epsg4326
        except:
            #traceback.print_exc()
            print "Here 4"
            self.iface.messageBar().pushMessage("", "Invalid Coordinate" , level=QgsMessageBar.WARNING, duration=2)
            return
        print "lat ", lat
        print "lon ", lon
        #self.lineEdit.clear()
        caps = layer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.AddFeatures:
            #lt = QgsTrackedVectorLayerTools()
            feat = QgsFeature(layer.pendingFields())
            feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(lon,lat)))
            #lt.addFeature(layer, {0:'id', 1:'name'}, QgsGeometry.fromPoint(QgsPoint(lon,lat)), feat)
            layer.addFeature(feat)
            #layer.dataProvider().addFeatures([feat])
            self.lltools.zoomTo(srcCrs, lat, lon)
        
    def configButtons(self):
        print "configButtons"
        self.xyButton.setDefaultAction(self.xymenu.actions()[self.inputXYOrder])
        self.crsButton.setDefaultAction(self.crsmenu.actions()[self.inputProjection])
        
    def readSettings(self):
        print "readSettings"
        settings = QSettings()
        self.inputProjection = int(settings.value('/LatLonTools/DigitizerProjection', 0))
        self.inputXYOrder = int(settings.value('/LatLonTools/DigitizerXYOrder', 0))
        if self.inputProjection < 0 or self.inputProjection > 3:
            self.inputProjection = 0
        if self.inputXYOrder < 0 or self.inputXYOrder > 1:
            self.inputXYOrder = 1
        print "   inputProjection ", self.inputProjection
        print "   inputXYOrder ", self.inputXYOrder
        
    def saveSettings(self):
        print "saveSettings"
        settings = QSettings()
        settings.setValue('/LatLonTools/DigitizerProjection', self.inputProjection)
        settings.setValue('/LatLonTools/DigitizerXYOrder', self.inputXYOrder)
        print "   inputProjection ", self.inputProjection
        print "   inputXYOrder ", self.inputXYOrder
        
    def crsTriggered(self, action):
        print "crsTriggered"
        self.crsButton.setDefaultAction(action)
        self.inputProjection = action.data()
        self.saveSettings()
        
    def xyTriggered(self, action):
        print "xyTriggered"
        self.xyButton.setDefaultAction(action)
        self.inputXYOrder = action.data()
        self.saveSettings()
