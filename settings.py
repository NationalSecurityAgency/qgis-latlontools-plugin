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
    def __init__(self, lltools, iface, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.lltools = lltools
        self.iface = iface
        self.coordComboBox.addItems(['Decimal Degrees', 'DMS', 'DDMMSS', 'Project CRS', 'MGRS'])
        self.delimComboBox.addItems(['Comma', 'Space', 'Tab', 'Other'])
        self.coordOrderComboBox.addItems(['Lat, Lon (Y,X) - Google Map Order','Lon, Lat (X,Y) Order'])
        self.zoomToCoordTypeComboBox.addItems(['WGS 84 (Latitude & Longitude)', 'MGRS'])
        self.zoomToCoordOrderComboBox.addItems(['Lat, Lon (Y,X) - Google Map Order','Lon, Lat (X,Y) Order'])
        self.zoomToCoordTypeComboBox.activated.connect(self.comboBoxChanged)
        self.mapProviderComboBox.addItems(mapProviders.mapProviderNames())
        self.readSettings()
        
    def readSettings(self):
        '''Load the user selected settings. The settings are retained even when
        the user quits QGIS.'''
        settings = QSettings()
        self.outputFormat = settings.value('/LatLonTools/OutputFormat', 'decimal')
        self.delimiter = settings.value('/LatLonTools/Delimiter', ', ')
        self.dmsPrecision =  int(settings.value('/LatLonTools/DMSPrecision', 0))
        self.coordOrder = int(settings.value('/LatLonTools/CoordOrder', 0))
        self.zoomToCoordOrder = int(settings.value('/LatLonTools/ZoomToCoordOrder', 0))
        self.zoomToCoordType = int(settings.value('/LatLonTools/ZoomToCoordType', 0))
        self.showPlacemark = int(settings.value('/LatLonTools/ShowPlacemark', Qt.Checked))
        self.persistentMarker = int(settings.value('/LatLonTools/PersistentMarker', Qt.Checked))
        self.mapProvider = int(settings.value('/LatLonTools/MapProvider', 0))
        self.mapZoom = int(settings.value('/LatLonTools/MapZoom', 13))
        self.setEnabled()
        
    def accept(self):
        '''Accept the settings and save them for next time.'''
        settings = QSettings()
        settings.setValue('/LatLonTools/ZoomToCoordType', int(self.zoomToCoordTypeComboBox.currentIndex()))
        settings.setValue('/LatLonTools/ZoomToCoordOrder', int(self.zoomToCoordOrderComboBox.currentIndex()))
        coord = self.coordComboBox.currentIndex()
        if coord == 0:
            settings.setValue('/LatLonTools/OutputFormat', 'decimal')
        elif coord == 1:
            settings.setValue('/LatLonTools/OutputFormat', 'dms')
        elif coord == 2:
            settings.setValue('/LatLonTools/OutputFormat', 'ddmmss')
        elif coord == 3:
            settings.setValue('/LatLonTools/OutputFormat', 'native')
        else:
            settings.setValue('/LatLonTools/OutputFormat', 'mgrs')
            
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
        
        settings.setValue('/LatLonTools/CoordOrder', int(self.coordOrderComboBox.currentIndex()))
        
        settings.setValue('/LatLonTools/ShowPlacemark', self.showPlacemarkCheckBox.checkState())
        settings.setValue('/LatLonTools/PersistentMarker', self.persistentMarkerCheckBox.checkState())
        settings.setValue('/LatLonTools/MapProvider',int(self.mapProviderComboBox.currentIndex()))
        settings.setValue('/LatLonTools/MapZoom',int(self.zoomSpinBox.value()))
        
        self.readSettings()
        self.lltools.settingsChanged()
        self.close()
        
    def comboBoxChanged(self):
        self.zoomToCoordType = int(self.zoomToCoordTypeComboBox.currentIndex())
        self.setEnabled()
        
    def setEnabled(self):
        self.zoomToCoordOrderComboBox.setEnabled(self.zoomToCoordType == 0)
        
    def showEvent(self, e):
        '''The user has selected the settings dialog box so we need to
        read the settings and update the dialog box with the previously
        selected settings.'''
        self.readSettings()
        
        self.zoomToCoordTypeComboBox.setCurrentIndex(self.zoomToCoordType)
        self.zoomToCoordOrderComboBox.setCurrentIndex(self.zoomToCoordOrder)
        
        if self.outputFormat == 'decimal':
            self.coordComboBox.setCurrentIndex(0)
        elif self.outputFormat == 'dms':
            self.coordComboBox.setCurrentIndex(1)
        elif self.outputFormat == 'ddmmss':
            self.coordComboBox.setCurrentIndex(2)
        elif self.outputFormat == 'native':
            self.coordComboBox.setCurrentIndex(3)
        else:
            self.coordComboBox.setCurrentIndex(4)
        
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
        
        self.coordOrderComboBox.setCurrentIndex(self.coordOrder)
        self.showPlacemarkCheckBox.setCheckState(self.showPlacemark)
        self.persistentMarkerCheckBox.setCheckState(self.persistentMarker)
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
        