import os
import re
import mapProviders

from PyQt4 import QtGui, uic
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *



FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/latLonSettings.ui'))


class SettingsWidget(QtGui.QDialog, FORM_CLASS):
    '''Settings Dialog box.'''
    Wgs84TypeDecimal = 0
    Wgs84TypeDMS = 1
    Wgs84TypeDDMMSS = 2
    Wgs84TypeWKT = 3
    ProjectionTypeWgs84 = 0
    ProjectionTypeMGRS = 1
    ProjectionTypeProjectCRS = 2
    ProjectionTypeCustomCRS = 3
    OrderYX = 0
    OrderXY = 1
    def __init__(self, lltools, iface, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.lltools = lltools
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        
        self.buttonBox.button(QtGui.QDialogButtonBox.RestoreDefaults).clicked.connect(self.restoreDefaults)
        
        ### CAPTURE SETTINGS ###
        self.captureProjectionComboBox.addItems(['WGS 84 (Latitude & Longitude)','MGRS', 'Project CRS', 'Custom CRS'])
        self.captureProjectionSelectionWidget.setCrs(self.epsg4326)
        self.wgs84NumberFormatComboBox.addItems(['Decimal Degrees', 'DMS', 'DDMMSS','WKT POINT'])
        self.otherNumberFormatComboBox.addItems(['Normal Coordinate','WKT POINT'])
        self.coordOrderComboBox.addItems(['Lat, Lon (Y,X) - Google Map Order','Lon, Lat (X,Y) Order'])
        self.delimComboBox.addItems(['Comma', 'Space', 'Tab', 'Other'])
        self.captureProjectionComboBox.activated.connect(self.setEnabled)
        
        ### ZOOM TO SETTINGS ###
        self.zoomToProjectionComboBox.addItems(['WGS 84 (Latitude & Longitude)', 'MGRS', 'Project CRS','Custom CRS'])
        self.zoomToProjectionSelectionWidget.setCrs(self.epsg4326)
        self.zoomToCoordOrderComboBox.addItems(['Lat, Lon (Y,X) - Google Map Order','Lon, Lat (X,Y) Order'])
        self.zoomToProjectionComboBox.activated.connect(self.setEnabled)
        
        ### EXTERNAL MAP ###
        self.mapProviderComboBox.addItems(mapProviders.mapProviderNames())
        
        self.readSettings()

        
    def captureCustomCRS(self):
        return self.captureProjectionSelectionWidget.crs()
        
    def captureCustomCRSID(self):
        return self.captureProjectionSelectionWidget.crs().authid()
    
    def zoomToCustomCRS(self):
        return self.zoomToProjectionSelectionWidget.crs()
        
    def zoomToCustomCRSID(self):
        return self.zoomToProjectionSelectionWidget.crs().authid()
    
    def restoreDefaults(self):
        '''Restore all settings to their default state.'''
        ### CAPTURE SETTINGS ###
        self.captureProjectionComboBox.setCurrentIndex(self.ProjectionTypeWgs84)
        self.wgs84NumberFormatComboBox.setCurrentIndex(0)
        self.otherNumberFormatComboBox.setCurrentIndex(0)
        self.coordOrderComboBox.setCurrentIndex(self.OrderYX)
        self.otherTxt.setText("")
        self.delimComboBox.setCurrentIndex(0)
        self.precisionSpinBox.setValue(0)
        self.captureProjectionSelectionWidget.setCrs(self.epsg4326)
        
        ### ZOOM TO SETTINGS ###
        self.zoomToProjectionComboBox.setCurrentIndex(self.ProjectionTypeWgs84)
        self.zoomToCoordOrderComboBox.setCurrentIndex(self.OrderYX)
        self.persistentMarkerCheckBox.setCheckState(Qt.Checked)
        self.zoomToProjectionSelectionWidget.setCrs(self.epsg4326)
        
        ### EXTERNAL MAP ###
        self.showPlacemarkCheckBox.setCheckState(Qt.Checked)
        self.mapProviderComboBox.setCurrentIndex(0)
        self.zoomSpinBox.setValue(13)
        
    def readSettings(self):
        '''Load the user selected settings. The settings are retained even when
        the user quits QGIS.'''
        settings = QSettings()
        
        ### CAPTURE SETTINGS ###
        self.captureProjection = int(settings.value('/LatLonTools/CaptureProjection', self.ProjectionTypeWgs84))
        self.delimiter = settings.value('/LatLonTools/Delimiter', ', ')
        self.dmsPrecision =  int(settings.value('/LatLonTools/DMSPrecision', 0))
        self.coordOrder = int(settings.value('/LatLonTools/CoordOrder', self.OrderYX))
        self.wgs84NumberFormat = int(settings.value('/LatLonTools/WGS84NumberFormat', 0))
        self.otherNumberFormat = int(settings.value('/LatLonTools/OtherNumberFormat', 0))
        
        ### ZOOM TO SETTINGS ###
        self.zoomToCoordOrder = int(settings.value('/LatLonTools/ZoomToCoordOrder', self.OrderYX))
        self.zoomToProjection = int(settings.value('/LatLonTools/ZoomToCoordType', 0))
        self.persistentMarker = int(settings.value('/LatLonTools/PersistentMarker', Qt.Checked))
        
        ### EXTERNAL MAP ###
        self.showPlacemark = int(settings.value('/LatLonTools/ShowPlacemark', Qt.Checked))
        self.mapProvider = int(settings.value('/LatLonTools/MapProvider', 0))
        self.mapZoom = int(settings.value('/LatLonTools/MapZoom', 13))
        
        self.setEnabled()
        
    def accept(self):
        '''Accept the settings and save them for next time.'''
        settings = QSettings()
        
        ### CAPTURE SETTINGS ###
        settings.setValue('/LatLonTools/CaptureProjection', int(self.captureProjectionComboBox.currentIndex()))
            
        settings.setValue('/LatLonTools/WGS84NumberFormat', int(self.wgs84NumberFormatComboBox.currentIndex()))
        settings.setValue('/LatLonTools/OtherNumberFormat', int(self.otherNumberFormatComboBox.currentIndex()))
        settings.setValue('/LatLonTools/CoordOrder', int(self.coordOrderComboBox.currentIndex()))
        delim = self.delimComboBox.currentIndex()
        if delim == 0:
            settings.setValue('/LatLonTools/Delimiter', ', ')
        elif delim == 1:
            settings.setValue('/LatLonTools/Delimiter', ' ')
        elif delim == 2:
            settings.setValue('/LatLonTools/Delimiter', '\t')
        else:
            settings.setValue('/LatLonTools/Delimiter', self.otherTxt.text())
            
        settings.setValue('/LatLonTools/DMSPrecision', self.precisionSpinBox.value())
        
        ### ZOOM TO SETTINGS ###
        settings.setValue('/LatLonTools/ZoomToCoordType', int(self.zoomToProjectionComboBox.currentIndex()))
        settings.setValue('/LatLonTools/ZoomToCoordOrder', int(self.zoomToCoordOrderComboBox.currentIndex()))
        settings.setValue('/LatLonTools/PersistentMarker', self.persistentMarkerCheckBox.checkState())
        
        ### EXTERNAL MAP ###
        settings.setValue('/LatLonTools/ShowPlacemark', self.showPlacemarkCheckBox.checkState())
        settings.setValue('/LatLonTools/MapProvider',int(self.mapProviderComboBox.currentIndex()))
        settings.setValue('/LatLonTools/MapZoom',int(self.zoomSpinBox.value()))
        
        self.readSettings()
        self.lltools.settingsChanged()
        self.close()
        
    def setEnabled(self):
        captureProjection = int(self.captureProjectionComboBox.currentIndex())
        self.captureProjectionSelectionWidget.setEnabled(captureProjection == self.ProjectionTypeCustomCRS)
        
        zoomToProjection = int(self.zoomToProjectionComboBox.currentIndex())
        self.zoomToCoordOrderComboBox.setEnabled(zoomToProjection != self.ProjectionTypeMGRS)
        self.zoomToProjectionSelectionWidget.setEnabled(zoomToProjection == self.ProjectionTypeCustomCRS)
        
    def showEvent(self, e):
        '''The user has selected the settings dialog box so we need to
        read the settings and update the dialog box with the previously
        selected settings.'''
        self.readSettings()
        
        ### CAPTURE SETTINGS ###
        self.captureProjectionComboBox.setCurrentIndex(self.captureProjection)
        self.wgs84NumberFormatComboBox.setCurrentIndex(self.wgs84NumberFormat)
        self.otherNumberFormatComboBox.setCurrentIndex(self.otherNumberFormat)
        self.coordOrderComboBox.setCurrentIndex(self.coordOrder)
        
        self.otherTxt.setText("")
        if self.delimiter == ', ':
            self.delimComboBox.setCurrentIndex(0)
        elif self.delimiter == ' ':
            self.delimComboBox.setCurrentIndex(1)
        elif self.delimiter == '\t':
            self.delimComboBox.setCurrentIndex(2)
        else:
            self.delimComboBox.setCurrentIndex(3)
            self.otherTxt.setText(self.delimiter)
            
        self.precisionSpinBox.setValue(self.dmsPrecision)
        
        ### ZOOM TO SETTINGS ###
        self.zoomToProjectionComboBox.setCurrentIndex(self.zoomToProjection)
        self.zoomToCoordOrderComboBox.setCurrentIndex(self.zoomToCoordOrder)
        self.persistentMarkerCheckBox.setCheckState(self.persistentMarker)
        
        ### EXTERNAL MAP ###
        self.showPlacemarkCheckBox.setCheckState(self.showPlacemark)
        self.mapProviderComboBox.setCurrentIndex(self.mapProvider)
        self.zoomSpinBox.setValue(self.mapZoom)
        
        self.setEnabled()

    def getMapProviderString(self, lat, lon):
        if self.showPlacemark:
            ms = mapProviders.MAP_PROVIDERS[self.mapProvider][2]
        else:
            ms = mapProviders.MAP_PROVIDERS[self.mapProvider][1]
        ms = ms.replace('@LAT@', str(lat))
        ms = ms.replace('@LON@', str(lon))
        ms = ms.replace('@Z@', str(self.mapZoom))
        return ms
        
    def captureProjIsWgs84(self):
        if self.captureProjection == self.ProjectionTypeWgs84:
            return True
        elif self.captureProjection == self.ProjectionTypeProjectCRS:
            if self.canvas.mapSettings().destinationCrs() == self.epsg4326:
                return True
        elif self.captureProjection == self.ProjectionTypeCustomCRS:
            if self.captureCustomCRS() == self.epsg4326:
                return True
        return False

    def captureProjIsProjectCRS(self):
        if self.captureProjection == self.ProjectionTypeProjectCRS:
            return True
        return False
        
    def captureProjIsMGRS(self):
        if self.captureProjection == self.ProjectionTypeMGRS:
            return True
        return False
        
    def captureProjIsCustomCRS(self):
        if self.captureProjection == self.ProjectionTypeCustomCRS:
            return True
        return False

    def zoomToProjIsWgs84(self):
        if self.zoomToProjection == self.ProjectionTypeWgs84:
            return True
        if self.zoomToProjection == self.ProjectionTypeProjectCRS:
            if self.canvas.mapSettings().destinationCrs() == self.epsg4326:
                return True
        return False
        
    def zoomToProjIsMGRS(self):
        if self.zoomToProjection == self.ProjectionTypeMGRS:
            return True
        return False

    def zoomToProjIsProjectCRS(self):
        if self.zoomToProjection == self.ProjectionTypeProjectCRS:
            return True
        return False
