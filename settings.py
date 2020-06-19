import os
from . import mapProviders

from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.core import QgsCoordinateReferenceSystem
from .util import epsg4326


FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/latLonSettings.ui'))


class Settings():
    OrderYX = 0
    OrderXY = 1
    userMapProviders = []

    def __init__(self):
        self.readSettings()
        self.externalBasemapCnt = len(mapProviders.MAP_PROVIDERS)

    def readSettings(self):
        '''Load the user selected settings. The settings are retained even when
        the user quits QGIS. This just loads the saved information into variables,
        but does not update the widgets. The widgets are updated with showEvent.'''
        qset = QSettings()

        ### CAPTURE SETTINGS ###
        self.captureShowLocation = int(qset.value('/LatLonTools/CaptureShowClickedLocation', Qt.Unchecked))
        self.captureCustomCrsAuthId = qset.value('/LatLonTools/CaptureCustomCrsId', 'EPSG:4326')
        self.captureGeohashPrecision = int(qset.value('/LatLonTools/CaptureGeohashPrecision', 12))
        self.captureDmmPrecision =  int(qset.value('/LatLonTools/CaptureDmmPrecision', 4))
        self.captureUtmPrecision =  int(qset.value('/LatLonTools/CaptureUtmPrecision', 0))
        self.captureAddDmsSpace = int(qset.value('/LatLonTools/CaptureAddDmsSpace', Qt.Checked))
        self.capturePadZeroes = int(qset.value('/LatLonTools/CapturePadZeroes', Qt.Unchecked))
        self.captureMaidenheadPrecision = int(qset.value('/LatLonTools/CaptureMaidenheadPrecision', 3))

        ### EXTERNAL MAP ###
        self.showPlacemark = int(qset.value('/LatLonTools/ShowPlacemark', Qt.Checked))
        self.mapProvider = int(qset.value('/LatLonTools/MapProvider', 0))
        self.mapProviderRight = int(qset.value('/LatLonTools/MapProviderRight', 0))
        self.mapZoom = int(qset.value('/LatLonTools/MapZoom', 13))
        self.externalMapShowLocation = int(qset.value('/LatLonTools/ExternMapShowClickedLocation', Qt.Unchecked))
        self.userMapProviders = qset.value('/LatLonTools/UserMapProviders', [])

        ### Multi-zoom Settings ###
        self.multiZoomCustomCrsAuthId = qset.value('/LatLonTools/MultiZoomCustomCrsId', 'EPSG:4326')

        ### BBOX CAPTURE SETTINGS ###
        self.bBoxCrs = int(qset.value('/LatLonTools/BBoxCrs', 0))  # Specifies WGS 84
        self.bBoxFormat = int(qset.value('/LatLonTools/BBoxFormat', 0))
        self.bBoxDelimiter = qset.value('/LatLonTools/BBoxDelimiter', ',')
        self.bBoxDigits = int(qset.value('/LatLonTools/BBoxDigits', 8))
        self.bBoxPrefix = qset.value('/LatLonTools/BBoxPrefix', '')
        self.bBoxSuffix = qset.value('/LatLonTools/BBoxSuffix', '')

        ### COORDINATE CONVERSION SETTINGS ###
        self.converterCustomCrsAuthId = qset.value('/LatLonTools/ConverterCustomCrsId', 'EPSG:4326')
        self.converterCoordOrder = int(qset.value('/LatLonTools/ConverterCoordOrder', self.OrderYX))
        self.converterDDPrec = int(qset.value('/LatLonTools/ConverterDDPrecision', 2))
        self.converter4326DDPrec = int(qset.value('/LatLonTools/Converter4326DDPrecision', 8))
        self.converterDmsPrec = int(qset.value('/LatLonTools/ConverterDmsPrecision', 0))
        self.converterDmmPrec = int(qset.value('/LatLonTools/ConverterDmmPrecision', 4))
        self.converterUtmPrec = int(qset.value('/LatLonTools/ConverterUtmPrecision', 0))
        self.converterPlusCodeLength = int(qset.value('/LatLonTools/ConverterPlusCodeLength', 10))
        self.converterGeohashPrecision = int(qset.value('/LatLonTools/ConverterGeohashPrecision', 12))
        self.converterMaidenheadPrecision = int(qset.value('/LatLonTools/ConverterMaidenheadPrecision', 3))
        self.converterDelimiter = qset.value('/LatLonTools/ConverterDelimiter', ', ')
        self.converterDdmmssDelimiter = qset.value('/LatLonTools/ConverterDdmmssDelimiter', ', ')
        self.converterAddDmsSpace = int(qset.value('/LatLonTools/ConverterAddDmsSpace', Qt.Checked))
        self.converterPadZeroes = int(qset.value('/LatLonTools/ConverterPadZeroes', Qt.Unchecked))

    def mapProviderNames(self):
        plist = []
        for x in mapProviders.MAP_PROVIDERS:
            plist.append(x[0])
        plist.append('Google Earth (If Installed)')
        for entry in self.userMapProviders:
            plist.append(entry[0])
        return plist

    def googleEarthMapProvider(self, button=0):
        if button == 2:
            if self.mapProviderRight == self.externalBasemapCnt:
                return True
        else:
            if self.mapProvider == self.externalBasemapCnt:
                return True
        return False

    def getMapProviderString(self, lat, lon, button=0):
        if button == 2:
            if self.mapProviderRight > self.externalBasemapCnt:
                # These are the optional user basemaps
                ms = self.userMapProviders[self.mapProviderRight - self.externalBasemapCnt - 1][1]
            else:
                if self.showPlacemark:
                    ms = mapProviders.MAP_PROVIDERS[self.mapProviderRight][2]
                else:
                    ms = mapProviders.MAP_PROVIDERS[self.mapProviderRight][1]
        else:
            if self.mapProvider > self.externalBasemapCnt:
                # These are the optional user basemaps
                ms = self.userMapProviders[self.mapProvider - self.externalBasemapCnt - 1][1]
            else:
                if self.showPlacemark:
                    ms = mapProviders.MAP_PROVIDERS[self.mapProvider][2]
                else:
                    ms = mapProviders.MAP_PROVIDERS[self.mapProvider][1]
        ms = ms.replace('{lat}', str(lat))
        ms = ms.replace('{lon}', str(lon))
        ms = ms.replace('{zoom}', str(self.mapZoom))
        return ms

settings = Settings()


class SettingsWidget(QDialog, FORM_CLASS):
    '''Settings Dialog box.'''
    Wgs84TypeDecimal = 0
    Wgs84TypeDMS = 1
    Wgs84TypeDDMMSS = 2
    Wgs84TypeDMM = 3
    Wgs84TypeWKT = 4
    Wgs84TypeGeoJSON = 5
    ProjectionTypeWgs84 = 0
    ProjectionTypeProjectCRS = 1
    ProjectionTypeCustomCRS = 2
    ProjectionTypeMGRS = 3
    ProjectionTypePlusCodes = 4
    ProjectionTypeUTM = 5
    ProjectionTypeGeohash = 6
    ProjectionTypeMaidenhead = 7
    OrderYX = 0
    OrderXY = 1

    def __init__(self, lltools, iface, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.lltools = lltools
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restoreDefaults)

        ### CAPTURE SETTINGS ###
        self.captureProjectionComboBox.addItems(['WGS 84 (Latitude & Longitude)', 'Project CRS', 'Custom CRS', 'MGRS', 'Plus Codes', 'Standard UTM','Geohash','Maidenhead Grid Locator'])
        self.captureProjectionSelectionWidget.setCrs(epsg4326)
        self.wgs84NumberFormatComboBox.addItems(['Decimal Degrees', 'D°M\'S"', 'DDMMSS', 'D°M.MM\'', 'WKT POINT', 'GeoJSON'])
        self.otherNumberFormatComboBox.addItems(['Normal Coordinate', 'WKT POINT'])
        self.coordOrderComboBox.addItems(['Lat, Lon (Y,X) - Google Map Order', 'Lon, Lat (X,Y) Order'])
        self.delimComboBox.addItems(['Comma', 'Comma Space', 'Space', 'Tab', 'Other'])
        self.captureProjectionComboBox.activated.connect(self.setEnabled)

        ### ZOOM TO SETTINGS ###
        self.zoomToProjectionComboBox.addItems(['WGS 84 (Latitude & Longitude) / Auto Detect Format', 'Project CRS', 'Custom CRS', 'MGRS', 'Plus Codes', 'Standard UTM','Geohash','Maidenhead Grid'])
        self.zoomToProjectionSelectionWidget.setCrs(epsg4326)
        self.zoomToCoordOrderComboBox.addItems(['Lat, Lon (Y,X) - Google Map Order', 'Lon, Lat (X,Y) Order'])
        self.zoomToProjectionComboBox.activated.connect(self.setEnabled)

        ### EXTERNAL MAP ###
        self.addProviderButton.clicked.connect(self.addUserProvider)
        self.deleteProviderButton.clicked.connect(self.deleteUserProvider)

        ### MULTI-ZOOM ###
        self.multiZoomToProjectionComboBox.addItems(['WGS 84 (Latitude & Longitude)', 'Project CRS', 'Custom CRS', 'MGRS', 'Plus Codes', 'Standard UTM'])
        self.multiZoomToProjectionComboBox.activated.connect(self.setEnabled)
        self.multiZoomToProjectionSelectionWidget.setCrs(epsg4326)
        self.qmlBrowseButton.clicked.connect(self.qmlOpenDialog)
        self.markerStyleComboBox.addItems(['Default', 'Labeled', 'Custom'])
        self.multiCoordOrderComboBox.addItems(['Lat, Lon (Y,X) - Google Map Order', 'Lon, Lat (X,Y) Order'])
        self.qmlStyle = ''

        ### BBOX CAPTURE SETTINGS ###
        self.bBoxCrsComboBox.addItems(['WGS 84 (Latitude & Longitude)', 'Project CRS'])
        self.bBoxFormatComboBox.addItems([
            '"xmin,ymin,xmax,ymax" - Using the selected delimiter',
            '"xmin,xmax,ymin,ymax" - Using the selected delimiter',
            '"x1 y1,x2 y2,x3 y3,x4 y4,x1 y1" - Polygon format',
            '"x1,y1 x2,y2 x3,y3 x4,y4 x1,y1" - Alternate polgyon format',
            'WKT Polygon',
            '"bbox: [xmin, ymin, xmax, ymax]" - MapProxy',
            '"bbox=xmin,ymin,xmax,ymax" - GeoServer WFS, WMS'])
        self.bBoxDelimiterComboBox.addItems(['Comma', 'Comma Space', 'Space', 'Tab', 'Other'])

        ### COORDINATE CONVERSION SETTINGS ###
        self.converterCoordOrderComboBox.addItems(['Lat, Lon (Y,X) - Google Map Order', 'Lon, Lat (X,Y) Order'])
        self.converterProjectionSelectionWidget.setCrs(epsg4326)

        self.readSettings()
        # This has been added because the coordinate capture uses it
        self.captureProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(settings.captureCustomCrsAuthId))

    def captureCustomCRS(self):
        return self.captureProjectionSelectionWidget.crs()

    def captureCustomCRSID(self):
        return self.captureProjectionSelectionWidget.crs().authid()

    def zoomToCustomCRS(self):
        return self.zoomToProjectionSelectionWidget.crs()

    def multiZoomToCustomCRS(self):
        return self.multiZoomToProjectionSelectionWidget.crs()

    def zoomToCustomCrsId(self):
        return self.zoomToProjectionSelectionWidget.crs().authid()

    def restoreDefaults(self):
        '''Restore all settings to their default state.'''
        ### CAPTURE SETTINGS ###
        self.captureProjectionComboBox.setCurrentIndex(self.ProjectionTypeWgs84)
        self.wgs84NumberFormatComboBox.setCurrentIndex(0)
        self.otherNumberFormatComboBox.setCurrentIndex(0)
        self.coordOrderComboBox.setCurrentIndex(self.OrderYX)
        self.otherTxt.setText("")
        self.delimComboBox.setCurrentIndex(1)
        self.precisionSpinBox.setValue(0)
        self.captureDmmPrecisionSpinBox.setValue(4)
        self.captureUtmPrecisionSpinBox.setValue(0)
        self.captureGeohashSpinBox.setValue(12)
        self.captureMaidenheadPrecisionSpinBox.setValue(3)
        self.captureProjectionSelectionWidget.setCrs(epsg4326)
        self.plusCodesSpinBox.setValue(10)
        self.digitsSpinBox.setValue(8)
        self.capturePrefixLineEdit.setText('')
        self.captureSuffixLineEdit.setText('')
        self.captureMarkerCheckBox.setCheckState(Qt.Unchecked)
        self.captureAddDmsSpaceCheckBox.setCheckState(Qt.Checked)
        self.capturePadZeroesCheckBox.setCheckState(Qt.Unchecked)

        ### ZOOM TO SETTINGS ###
        self.zoomToProjectionComboBox.setCurrentIndex(self.ProjectionTypeWgs84)
        self.zoomToCoordOrderComboBox.setCurrentIndex(self.OrderYX)
        self.persistentMarkerCheckBox.setCheckState(Qt.Checked)
        self.zoomToProjectionSelectionWidget.setCrs(epsg4326)

        ### EXTERNAL MAP ###
        self.showPlacemarkCheckBox.setCheckState(Qt.Checked)
        self.mapProviderComboBox.setCurrentIndex(0)
        self.mapProviderRComboBox.setCurrentIndex(0)
        self.zoomSpinBox.setValue(13)
        self.showLocationCheckBox.setCheckState(Qt.Unchecked)

        ### Multi-zoom Settings ###
        self.multiZoomToProjectionComboBox.setCurrentIndex(0)  # WGS 84
        self.multiZoomToProjectionSelectionWidget.setCrs(epsg4326)
        self.multiCoordOrderComboBox.setCurrentIndex(self.OrderYX)
        self.qmlLineEdit.setText('')
        self.markerStyleComboBox.setCurrentIndex(0)
        self.extraDataSpinBox.setValue(0)

        ### BBOX CAPTURE SETTINGS ###
        self.bBoxCrsComboBox.setCurrentIndex(0)  # WGS 84
        self.bBoxFormatComboBox.setCurrentIndex(0)  # MapProxy format
        self.bBoxDelimiterComboBox.setCurrentIndex(0)  # Comma
        self.bBoxDelimiterLineEdit.setText('')
        self.bBoxPrefixLineEdit.setText('')
        self.bBoxSuffixLineEdit.setText('')
        self.bBoxDigitsSpinBox.setValue(8)

        ### COORDINATE CONVERSION SETTINGS ###
        self.converterCoordOrderComboBox.setCurrentIndex(0)  # WGS 84
        self.converterProjectionSelectionWidget.setCrs(epsg4326)
        self.converter4326DDPrecisionSpinBox.setValue(8)
        self.converterDDPrecisionSpinBox.setValue(2)
        self.converterDmsPrecisionSpinBox.setValue(0)
        self.converterDmmPrecisionSpinBox.setValue(4)
        self.converterUtmPrecisionSpinBox.setValue(0)
        self.converterPlusCodePrecisionSpinBox.setValue(10)
        self.converterGeohashSpinBox.setValue(12)
        self.converterMaidenheadPrecisionSpinBox.setValue(3)
        self.converterDelimiterLineEdit.setText(',')
        self.converterDdmmssDelimiterLineEdit.setText(',')
        self.converterAddDmsSpaceCheckBox.setCheckState(Qt.Checked)
        self.converterPadZeroesCheckBox.setCheckState(Qt.Unchecked)



    def readSettings(self):
        '''Load the user selected settings. The settings are retained even when
        the user quits QGIS. This just loads the saved information into varialbles,
        but does not update the widgets. The widgets are updated with showEvent.'''
        qset = QSettings()

        ### CAPTURE SETTINGS ###
        self.captureProjection = int(qset.value('/LatLonTools/CaptureProjection', self.ProjectionTypeWgs84))
        self.delimiter = qset.value('/LatLonTools/Delimiter', ', ')
        self.dmsPrecision = int(qset.value('/LatLonTools/DMSPrecision', 0))
        self.coordOrder = int(qset.value('/LatLonTools/CoordOrder', self.OrderYX))
        self.wgs84NumberFormat = int(qset.value('/LatLonTools/WGS84NumberFormat', 0))
        self.otherNumberFormat = int(qset.value('/LatLonTools/OtherNumberFormat', 0))
        self.plusCodesLength = int(qset.value('/LatLonTools/PlusCodesLength', 10))
        self.decimalDigits = int(qset.value('/LatLonTools/DecimalDigits', 8))
        self.capturePrefix = qset.value('/LatLonTools/CapturePrefix', '')
        self.captureSuffix = qset.value('/LatLonTools/CaptureSuffix', '')

        ### ZOOM TO SETTINGS ###
        self.zoomToCoordOrder = int(qset.value('/LatLonTools/ZoomToCoordOrder', self.OrderYX))
        self.zoomToProjection = int(qset.value('/LatLonTools/ZoomToCoordType', 0))
        self.persistentMarker = int(qset.value('/LatLonTools/PersistentMarker', Qt.Checked))
        self.zoomToCustomCrsAuthId = qset.value('/LatLonTools/ZoomToCustomCrsId', 'EPSG:4326')
        self.zoomToProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(self.zoomToCustomCrsAuthId))

        ### MULTI-ZOOM CUSTOM QML STYLE ###
        self.multiZoomToProjection = int(qset.value('/LatLonTools/MultiZoomToProjection', 0))
        self.multiCoordOrder = int(qset.value('/LatLonTools/MultiCoordOrder', self.OrderYX))
        self.multiZoomNumCol = int(qset.value('/LatLonTools/MultiZoomExtraData', 0))
        self.multiZoomStyleID = int(qset.value('/LatLonTools/MultiZoomStyleID', 0))
        self.qmlStyle = qset.value('/LatLonTools/QmlStyle', '')
        if (self.multiZoomStyleID == 2) and (self.qmlStyle == '' or self.qmlStyle is None or not os.path.isfile(self.qmlStyle)):
            # If the file is invalid then set to an emply string
            qset.setValue('/LatLonTools/QmlStyle', '')
            qset.setValue('/LatLonTools/MultiZoomStyleID', 0)
            self.qmlStyle = ''
            self.multiZoomStyleID = 0

        ### BBOX & EXTERNAL MAP SETTINGS ###
        settings.readSettings()

        self.setEnabled()

    def accept(self):
        '''Accept the settings and save them for next time.'''
        qset = QSettings()

        ### CAPTURE SETTINGS ###
        qset.setValue('/LatLonTools/CaptureCustomCrsId', self.captureProjectionSelectionWidget.crs().authid())
        qset.setValue('/LatLonTools/CaptureProjection', int(self.captureProjectionComboBox.currentIndex()))

        qset.setValue('/LatLonTools/WGS84NumberFormat', int(self.wgs84NumberFormatComboBox.currentIndex()))
        qset.setValue('/LatLonTools/OtherNumberFormat', int(self.otherNumberFormatComboBox.currentIndex()))
        qset.setValue('/LatLonTools/CoordOrder', int(self.coordOrderComboBox.currentIndex()))
        delim = self.delimComboBox.currentIndex()
        if delim == 0:
            qset.setValue('/LatLonTools/Delimiter', ',')
        elif delim == 1:
            qset.setValue('/LatLonTools/Delimiter', ', ')
        elif delim == 2:
            qset.setValue('/LatLonTools/Delimiter', ' ')
        elif delim == 3:
            qset.setValue('/LatLonTools/Delimiter', '\t')
        else:
            qset.setValue('/LatLonTools/Delimiter', self.otherTxt.text())

        qset.setValue('/LatLonTools/DMSPrecision', self.precisionSpinBox.value())
        qset.setValue('/LatLonTools/CaptureDmmPrecision', self.captureDmmPrecisionSpinBox.value())
        qset.setValue('/LatLonTools/CaptureUtmPrecision', self.captureUtmPrecisionSpinBox.value())
        qset.setValue('/LatLonTools/CaptureGeohashPrecision', self.captureGeohashSpinBox.value())
        qset.setValue('/LatLonTools/CaptureMaidenheadPrecision', self.captureMaidenheadPrecisionSpinBox.value())
        qset.setValue('/LatLonTools/PlusCodesLength', self.plusCodesSpinBox.value())
        qset.setValue('/LatLonTools/DecimalDigits', self.digitsSpinBox.value())
        qset.setValue('/LatLonTools/CapturePrefix', self.capturePrefixLineEdit.text())
        qset.setValue('/LatLonTools/CaptureSuffix', self.captureSuffixLineEdit.text())
        qset.setValue('/LatLonTools/CaptureShowClickedLocation', self.captureMarkerCheckBox.checkState())
        qset.setValue('/LatLonTools/CaptureAddDmsSpace', self.captureAddDmsSpaceCheckBox.checkState())
        qset.setValue('/LatLonTools/CapturePadZeroes', self.capturePadZeroesCheckBox.checkState())

        ### ZOOM TO SETTINGS ###
        qset.setValue('/LatLonTools/ZoomToCoordType', int(self.zoomToProjectionComboBox.currentIndex()))
        qset.setValue('/LatLonTools/ZoomToCoordOrder', int(self.zoomToCoordOrderComboBox.currentIndex()))
        qset.setValue('/LatLonTools/PersistentMarker', self.persistentMarkerCheckBox.checkState())
        qset.setValue('/LatLonTools/ZoomToCustomCrsId', self.zoomToCustomCrsId())

        ### EXTERNAL MAP ###
        qset.setValue('/LatLonTools/ShowPlacemark', self.showPlacemarkCheckBox.checkState())
        qset.setValue('/LatLonTools/ExternMapShowClickedLocation', self.showLocationCheckBox.checkState())
        qset.setValue('/LatLonTools/MapProvider', int(self.mapProviderComboBox.currentIndex()))
        qset.setValue('/LatLonTools/MapProviderRight', int(self.mapProviderRComboBox.currentIndex()))
        qset.setValue('/LatLonTools/UserMapProviders',settings.userMapProviders)
        qset.setValue('/LatLonTools/MapZoom', int(self.zoomSpinBox.value()))

        ### MULTI-ZOOM TO SETTINGS ###
        qset.setValue('/LatLonTools/MultiZoomCustomCrsId', self.multiZoomToProjectionSelectionWidget.crs().authid())
        qset.setValue('/LatLonTools/MultiZoomToProjection', int(self.multiZoomToProjectionComboBox.currentIndex()))
        qset.setValue('/LatLonTools/MultiCoordOrder', int(self.multiCoordOrderComboBox.currentIndex()))
        qset.setValue('/LatLonTools/MultiZoomExtraData', int(self.extraDataSpinBox.value()))
        qset.setValue('/LatLonTools/MultiZoomStyleID', int(self.markerStyleComboBox.currentIndex()))
        qset.setValue('/LatLonTools/QmlStyle', self.qmlLineEdit.text())

        ### BBOX CAPTURE SETTINGS ###
        qset.setValue('/LatLonTools/BBoxCrs', int(self.bBoxCrsComboBox.currentIndex()))
        qset.setValue('/LatLonTools/BBoxFormat', int(self.bBoxFormatComboBox.currentIndex()))
        delim = self.bBoxDelimiterComboBox.currentIndex()
        if delim == 0:
            qset.setValue('/LatLonTools/BBoxDelimiter', ',')
        elif delim == 1:
            qset.setValue('/LatLonTools/BBoxDelimiter', ', ')
        elif delim == 2:
            qset.setValue('/LatLonTools/BBoxDelimiter', ' ')
        elif delim == 3:
            qset.setValue('/LatLonTools/BBoxDelimiter', '\t')
        else:
            qset.setValue('/LatLonTools/BBoxDelimiter', self.bBoxDelimiterLineEdit.text())
        qset.setValue('/LatLonTools/BBoxPrefix', self.bBoxPrefixLineEdit.text())
        qset.setValue('/LatLonTools/BBoxSuffix', self.bBoxSuffixLineEdit.text())
        qset.setValue('/LatLonTools/BBoxDigits', self.bBoxDigitsSpinBox.value())

        ### COORDINATE CONVERSION SETTINGS ###
        qset.setValue('/LatLonTools/ConverterCustomCrsId', self.converterProjectionSelectionWidget.crs().authid())
        qset.setValue('/LatLonTools/ConverterCoordOrder', int(self.converterCoordOrderComboBox.currentIndex()))
        qset.setValue('/LatLonTools/ConverterDDPrecision', int(self.converterDDPrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/Converter4326DDPrecision', int(self.converter4326DDPrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterDmsPrecision', int(self.converterDmsPrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterDmmPrecision', int(self.converterDmmPrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterUtmPrecision', int(self.converterUtmPrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterPlusCodeLength', int(self.converterPlusCodePrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterGeohashPrecision', int(self.converterGeohashSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterMaidenheadPrecision', int(self.converterMaidenheadPrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterDelimiter', self.converterDelimiterLineEdit.text())
        qset.setValue('/LatLonTools/ConverterDdmmssDelimiter', self.converterDdmmssDelimiterLineEdit.text())
        qset.setValue('/LatLonTools/ConverterAddDmsSpace', self.converterAddDmsSpaceCheckBox.checkState())
        qset.setValue('/LatLonTools/ConverterPadZeroes', self.converterPadZeroesCheckBox.checkState())

        # The values have been read from the widgets and saved to the registry.
        # Now we will read them back to the variables.
        self.readSettings()
        self.lltools.settingsChanged()
        self.close()
        
    def updateMapProviderComboBoxes(self):
            # Update the selected map provider lists
            curindex = settings.mapProvider
            self.mapProviderComboBox.clear()
            self.mapProviderComboBox.addItems(settings.mapProviderNames())
            if curindex >= len(settings.mapProviderNames()):
                curindex = 0
            self.mapProviderComboBox.setCurrentIndex(curindex)

            curindex = settings.mapProviderRight
            self.mapProviderRComboBox.clear()
            self.mapProviderRComboBox.addItems(settings.mapProviderNames())
            if curindex >= len(settings.mapProviderNames()):
                curindex = 0
            self.mapProviderRComboBox.setCurrentIndex(curindex)

    def addUserProvider(self):
        name = self.userProviderNameLineEdit.text().strip()
        url = self.userProviderUrlLineEdit.text().strip()
        if name and url:
            settings.userMapProviders.append([name, url])
            names = []
            for item in settings.userMapProviders:
                names.append(item[0])
            self.userMapProviderComboBox.clear()
            self.userMapProviderComboBox.addItems(names)
            self.updateMapProviderComboBoxes()

    def deleteUserProvider(self):
        if self.userMapProviderComboBox.count() > 0:
            index = self.userMapProviderComboBox.currentIndex()
            if index >= 0:
                del settings.userMapProviders[index]
            names = []
            for item in settings.userMapProviders:
                names.append(item[0])
            self.userMapProviderComboBox.clear()
            self.userMapProviderComboBox.addItems(names)
            # Since we deleted an entry just reset the selected map to
            # be the first one - Open Street Map
            settings.mapProvider = 0
            settings.mapProviderRight = 0
            self.updateMapProviderComboBoxes()

    def qmlOpenDialog(self):
        filename = QFileDialog.getOpenFileName(
            None, "Input QML Style File",
            self.qmlLineEdit.text(), "QGIS Layer Style File (*.qml)")[0]
        if filename:
            self.qmlStyle = filename
            self.qmlLineEdit.setText(filename)
            self.markerStyleComboBox.setCurrentIndex(2)

    def customQMLFile(self):
        return self.qmlStyle

    def setEnabled(self):
        captureProjection = int(self.captureProjectionComboBox.currentIndex())
        self.captureProjectionSelectionWidget.setEnabled(captureProjection == self.ProjectionTypeCustomCRS)

        # Simple Zoom to Enables
        zoomToProjection = int(self.zoomToProjectionComboBox.currentIndex())
        self.zoomToCoordOrderComboBox.setEnabled((zoomToProjection != self.ProjectionTypeMGRS) and
                (zoomToProjection != self.ProjectionTypePlusCodes) and (zoomToProjection != self.ProjectionTypeUTM) and
                (zoomToProjection != self.ProjectionTypeGeohash) and (zoomToProjection != self.ProjectionTypeMaidenhead))
        self.zoomToProjectionSelectionWidget.setEnabled(zoomToProjection == self.ProjectionTypeCustomCRS)

        # MULTI Zoom
        zoomToProjection = int(self.multiZoomToProjectionComboBox.currentIndex())
        self.multiZoomToProjectionSelectionWidget.setEnabled(zoomToProjection == 2)

    def showTab(self, tab):
        self.tabWidget.setCurrentIndex(tab)
        self.show()

    def showEvent(self, e):
        '''The user has selected the settings dialog box so we need to
        read the settings and update the dialog box with the previously
        selected settings.'''
        self.readSettings()

        ### CAPTURE SETTINGS ###
        self.captureProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(settings.captureCustomCrsAuthId))
        self.captureProjectionComboBox.setCurrentIndex(self.captureProjection)
        self.wgs84NumberFormatComboBox.setCurrentIndex(self.wgs84NumberFormat)
        self.otherNumberFormatComboBox.setCurrentIndex(self.otherNumberFormat)
        self.coordOrderComboBox.setCurrentIndex(self.coordOrder)

        self.otherTxt.setText("")
        if self.delimiter == ',':
            self.delimComboBox.setCurrentIndex(0)
        elif self.delimiter == ', ':
            self.delimComboBox.setCurrentIndex(1)
        elif self.delimiter == ' ':
            self.delimComboBox.setCurrentIndex(2)
        elif self.delimiter == '\t':
            self.delimComboBox.setCurrentIndex(3)
        else:
            self.delimComboBox.setCurrentIndex(4)
            self.otherTxt.setText(self.delimiter)

        self.digitsSpinBox.setValue(self.decimalDigits)
        self.precisionSpinBox.setValue(self.dmsPrecision)
        self.captureDmmPrecisionSpinBox.setValue(settings.captureDmmPrecision)
        self.captureUtmPrecisionSpinBox.setValue(settings.captureUtmPrecision)
        self.captureGeohashSpinBox.setValue(settings.captureGeohashPrecision)
        self.captureMaidenheadPrecisionSpinBox.setValue(settings.captureMaidenheadPrecision)
        self.capturePrefixLineEdit.setText(self.capturePrefix)
        self.captureSuffixLineEdit.setText(self.captureSuffix)
        self.captureMarkerCheckBox.setCheckState(settings.captureShowLocation)
        self.captureAddDmsSpaceCheckBox.setCheckState(settings.captureAddDmsSpace)
        self.capturePadZeroesCheckBox.setCheckState(settings.capturePadZeroes)

        ### ZOOM TO SETTINGS ###
        self.zoomToProjectionComboBox.setCurrentIndex(self.zoomToProjection)
        if self.zoomToCustomCrsAuthId == 'EPSG:4326':
            self.zoomToProjectionSelectionWidget.setCrs(epsg4326)
        else:
            self.zoomToProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(self.zoomToCustomCrsAuthId))
        self.zoomToCoordOrderComboBox.setCurrentIndex(self.zoomToCoordOrder)
        self.persistentMarkerCheckBox.setCheckState(self.persistentMarker)

        ### EXTERNAL MAP ###
        self.showPlacemarkCheckBox.setCheckState(settings.showPlacemark)
        self.showLocationCheckBox.setCheckState(settings.externalMapShowLocation)
        self.zoomSpinBox.setValue(settings.mapZoom)
        # self.mapProviderComboBox.setCurrentIndex(settings.mapProvider)
        # self.mapProviderRComboBox.setCurrentIndex(settings.mapProviderRight)
        names = []
        for item in settings.userMapProviders:
            names.append(item[0])
        self.userMapProviderComboBox.clear()
        self.userMapProviderComboBox.addItems(names)
        self.updateMapProviderComboBoxes()

        ### MULTI-ZOOM CUSTOM QML STYLE ###
        self.multiZoomToProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(settings.multiZoomCustomCrsAuthId))
        self.multiZoomToProjectionComboBox.setCurrentIndex(self.multiZoomToProjection)
        self.multiCoordOrderComboBox.setCurrentIndex(self.multiCoordOrder)
        self.extraDataSpinBox.setValue(self.multiZoomNumCol)
        self.markerStyleComboBox.setCurrentIndex(self.multiZoomStyleID)
        self.qmlLineEdit.setText(self.qmlStyle)

        ### BBOX CAPTURE SETTINGS ###
        self.bBoxCrsComboBox.setCurrentIndex(settings.bBoxCrs)
        self.bBoxFormatComboBox.setCurrentIndex(settings.bBoxFormat)
        self.bBoxDelimiterLineEdit.setText('')
        if settings.bBoxDelimiter == ',':
            self.bBoxDelimiterComboBox.setCurrentIndex(0)
        elif settings.bBoxDelimiter == ', ':
            self.bBoxDelimiterComboBox.setCurrentIndex(1)
        elif settings.bBoxDelimiter == ' ':
            self.bBoxDelimiterComboBox.setCurrentIndex(2)
        elif settings.bBoxDelimiter == '\t':
            self.bBoxDelimiterComboBox.setCurrentIndex(3)
        else:
            self.bBoxDelimiterComboBox.setCurrentIndex(4)
            self.bBoxDelimiterLineEdit.setText(settings.bBoxDelimiter)
        self.bBoxPrefixLineEdit.setText(settings.bBoxPrefix)
        self.bBoxSuffixLineEdit.setText(settings.bBoxSuffix)
        self.bBoxDigitsSpinBox.setValue(settings.bBoxDigits)

        ### COORDINATE CONVERSION SETTINGS ###
        self.converterProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(settings.converterCustomCrsAuthId))
        self.converterCoordOrderComboBox.setCurrentIndex(settings.converterCoordOrder)
        self.converterDDPrecisionSpinBox.setValue(settings.converterDDPrec)
        self.converter4326DDPrecisionSpinBox.setValue(settings.converter4326DDPrec)
        self.converterDmsPrecisionSpinBox.setValue(settings.converterDmsPrec)
        self.converterDmmPrecisionSpinBox.setValue(settings.converterDmmPrec)
        self.converterUtmPrecisionSpinBox.setValue(settings.converterUtmPrec)
        self.converterPlusCodePrecisionSpinBox.setValue(settings.converterPlusCodeLength)
        self.converterGeohashSpinBox.setValue(settings.converterGeohashPrecision)
        self.converterMaidenheadPrecisionSpinBox.setValue(settings.converterMaidenheadPrecision)
        self.converterDelimiterLineEdit.setText(settings.converterDelimiter)
        self.converterDdmmssDelimiterLineEdit.setText(settings.converterDdmmssDelimiter)
        self.converterAddDmsSpaceCheckBox.setCheckState(settings.converterAddDmsSpace)
        self.converterPadZeroesCheckBox.setCheckState(settings.converterPadZeroes)

        self.setEnabled()

    def captureProjIsWgs84(self):
        if self.captureProjection == self.ProjectionTypeWgs84:
            return True
        elif self.captureProjection == self.ProjectionTypeProjectCRS:
            if self.canvas.mapSettings().destinationCrs() == epsg4326:
                return True
        elif self.captureProjection == self.ProjectionTypeCustomCRS:
            if self.captureCustomCRS() == epsg4326:
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

    def captureProjIsPlusCodes(self):
        if self.captureProjection == self.ProjectionTypePlusCodes:
            return True
        return False

    def captureProjIsUTM(self):
        if self.captureProjection == self.ProjectionTypeUTM:
            return True
        return False

    def captureProjIsGeohash(self):
        if self.captureProjection == self.ProjectionTypeGeohash:
            return True
        return False

    def captureProjIsMaidenhead(self):
        if self.captureProjection == self.ProjectionTypeMaidenhead:
            return True
        return False

    def zoomToProjIsWgs84(self):
        if self.zoomToProjection == self.ProjectionTypeWgs84:
            return True
        if self.zoomToProjection == self.ProjectionTypeProjectCRS:
            if self.canvas.mapSettings().destinationCrs() == epsg4326:
                return True
        if self.zoomToProjection == self.ProjectionTypeCustomCRS:
            if self.zoomToCustomCRS() == epsg4326:
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

    def zoomToProjIsPlusCodes(self):
        if self.zoomToProjection == self.ProjectionTypePlusCodes:
            return True
        return False

    def zoomToProjIsStandardUtm(self):
        if self.zoomToProjection == self.ProjectionTypeUTM:
            return True
        return False

    def zoomToProjIsGeohash(self):
        if self.zoomToProjection == self.ProjectionTypeGeohash:
            return True
        return False

    def zoomToProjIsMaidenhead(self):
        if self.zoomToProjection == self.ProjectionTypeMaidenhead:
            return True
        return False

    def multiZoomToProjIsMGRS(self):
        if self.multiZoomToProjection == 3:  # MGRS
            return True
        return False

    def multiZoomToProjIsPlusCodes(self):
        if self.multiZoomToProjection == 4:  # Plus Codes
            return True
        return False

    def multiZoomToProjIsUtm(self):
        if self.multiZoomToProjection == 5:  # Standard UTM
            return True
        return False

    def multiZoomToProjIsWgs84(self):
        if self.multiZoomToProjection == 0:  # Wgs84
            return True
        if self.multiZoomToProjection == 1:  # Project CRS
            if self.canvas.mapSettings().destinationCrs() == epsg4326:
                return True
        if self.multiZoomToProjection == 2:  # Custom CRS
            if self.multiZoomToCustomCRS() == epsg4326:
                return True
        return False

    def multiZoomToCRS(self):
        if self.multiZoomToProjection == 0:  # Wgs84
            return self.epse4326
        if self.multiZoomToProjection == 1:  # Project CRS
            return self.canvas.mapSettings().destinationCrs()
        if self.multiZoomToProjection == 2:  # Custom CRS
            return self.multiZoomToCustomCRS()
