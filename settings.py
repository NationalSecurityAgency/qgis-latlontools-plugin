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
import enum
try:
    import h3
    v = h3.versions()
    if v['python'][0] == '3':
        H3_INSTALLED = True
    else:
        H3_INSTALLED = False
except Exception:
    H3_INSTALLED = False
from . import mapProviders

from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor

from qgis.core import QgsCoordinateReferenceSystem, QgsSettings
from .util import epsg4326, tr


FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/latLonSettings.ui'))

@enum.unique
class CopyExtent(enum.IntEnum):
    WSEN = 0
    WESN = 1
    SWNE = 2
    Poly1 = 3
    Poly2 = 4
    PolyWkt = 5
    MapProxy = 6
    GeoServer = 7

@enum.unique
class CoordOrder(enum.IntEnum):
    OrderYX = 0
    OrderXY = 1


class Settings():
    userMapProviders = []

    def __init__(self):
        self.readSettings()
        self.externalBasemapCnt = len(mapProviders.MAP_PROVIDERS)

    def readSettings(self):
        '''Load the user selected settings. The settings are retained even when
        the user quits QGIS. This just loads the saved information into variables,
        but does not update the widgets. The widgets are updated with showEvent.'''
        qset = QgsSettings()

        ### CAPTURE SETTINGS ###
        self.captureShowLocation = int(qset.value('/LatLonTools/CaptureShowClickedLocation', Qt.Unchecked))
        self.captureCustomCrsAuthId = qset.value('/LatLonTools/CaptureCustomCrsId', 'EPSG:4326')
        self.captureGeohashPrecision = int(qset.value('/LatLonTools/CaptureGeohashPrecision', 12))
        self.captureDmmPrecision =  int(qset.value('/LatLonTools/CaptureDmmPrecision', 4))
        self.captureUtmPrecision =  int(qset.value('/LatLonTools/CaptureUtmPrecision', 0))
        self.captureUtmFormat = int(qset.value('/LatLonTools/CaptureUtmFormat', 0))
        self.captureUpsPrecision =  int(qset.value('/LatLonTools/CaptureUpsPrecision', 0))
        self.captureUpsFormat = int(qset.value('/LatLonTools/CaptureUpsFormat', 0))
        self.captureAddDmsSpace = int(qset.value('/LatLonTools/CaptureAddDmsSpace', Qt.Checked))
        self.capturePadZeroes = int(qset.value('/LatLonTools/CapturePadZeroes', Qt.Unchecked))
        self.captureMaidenheadPrecision = int(qset.value('/LatLonTools/CaptureMaidenheadPrecision', 3))
        self.captureGeorefPrecision = int(qset.value('/LatLonTools/CaptureGeorefPrecision', 5))
        self.captureMgrsAddSpacesCheckBox = int(qset.value('/LatLonTools/CaptureMgrsAddSpaces', Qt.Unchecked))
        self.captureMgrsPrec = int(qset.value('/LatLonTools/CaptureMgrsPrecision', 5))
        if H3_INSTALLED:
            self.captureH3Precision = int(qset.value('/LatLonTools/CaptureH3Precision', 8))
        else:
            self.captureH3Precision = 8

        ### ZOOM TO SETTINGS ###
        self.markerSize = int(qset.value('/LatLonTools/MarkerSize', 18))
        self.markerWidth = int(qset.value('/LatLonTools/MarkerWidth', 2))
        self.gridWidth = int(qset.value('/LatLonTools/GridWidth', 2))
        color = qset.value('/LatLonTools/MarkerColor', '#ff0000')
        self.markerColor = QColor(color)
        value = int(qset.value('/LatLonTools/MarkerColorOpacity', 255))
        self.markerColor.setAlpha(value)
        color = qset.value('/LatLonTools/GridColor', '#ff0000')
        self.gridColor = QColor(color)
        value = int(qset.value('/LatLonTools/GridColorOpacity', 255))
        self.gridColor.setAlpha(value)

        ### EXTERNAL MAP ###
        self.showPlacemark = int(qset.value('/LatLonTools/ShowPlacemark', Qt.Checked))
        self.mapProvider = int(qset.value('/LatLonTools/MapProvider', 0))
        self.mapProviderRight = int(qset.value('/LatLonTools/MapProviderRight', 0))
        self.mapZoom = int(qset.value('/LatLonTools/MapZoom', 13))
        self.externalMapShowLocation = int(qset.value('/LatLonTools/ExternMapShowClickedLocation', Qt.Unchecked))
        self.userMapProviders = qset.value('/LatLonTools/UserMapProviders', 0)
        if not isinstance(self.userMapProviders, list):
            self.userMapProviders = []

        ### Multi-zoom Settings ###
        self.multiZoomCustomCrsAuthId = qset.value('/LatLonTools/MultiZoomCustomCrsId', 'EPSG:4326')

        ### BBOX CAPTURE SETTINGS ###
        self.bBoxCrs = int(qset.value('/LatLonTools/BBoxCrs', 0))  # Specifies WGS 84
        self.bBoxFormat = int(qset.value('/LatLonTools/BBoxFormat', CopyExtent.WSEN))
        self.bBoxDelimiter = qset.value('/LatLonTools/BBoxDelimiter', ',')
        self.bBoxDigits = int(qset.value('/LatLonTools/BBoxDigits', 8))
        self.bBoxPrefix = qset.value('/LatLonTools/BBoxPrefix', '')
        self.bBoxSuffix = qset.value('/LatLonTools/BBoxSuffix', '')

        ### COORDINATE CONVERSION SETTINGS ###
        self.converterCustomCrsAuthId = qset.value('/LatLonTools/ConverterCustomCrsId', 'EPSG:4326')
        self.converterCoordOrder = int(qset.value('/LatLonTools/ConverterCoordOrder', CoordOrder.OrderYX))
        self.converterDDPrec = int(qset.value('/LatLonTools/ConverterDDPrecision', 2))
        self.converter4326DDPrec = int(qset.value('/LatLonTools/Converter4326DDPrecision', 8))
        self.converterDmsPrec = int(qset.value('/LatLonTools/ConverterDmsPrecision', 0))
        self.converterDmmPrec = int(qset.value('/LatLonTools/ConverterDmmPrecision', 4))
        self.converterUtmPrec = int(qset.value('/LatLonTools/ConverterUtmPrecision', 0))
        self.converterUtmFormat = int(qset.value('/LatLonTools/ConverterUtmFormat', 0))
        self.converterUpsPrec = int(qset.value('/LatLonTools/ConverterUpsPrecision', 0))
        self.converterUpsFormat = int(qset.value('/LatLonTools/ConverterUpsFormat', 0))
        self.converterPlusCodeLength = int(qset.value('/LatLonTools/ConverterPlusCodeLength', 10))
        self.converterGeohashPrecision = int(qset.value('/LatLonTools/ConverterGeohashPrecision', 12))
        self.converterMaidenheadPrecision = int(qset.value('/LatLonTools/ConverterMaidenheadPrecision', 3))
        self.converterGeorefPrecision = int(qset.value('/LatLonTools/ConverterGeorefPrecision', 5))
        self.converterDelimiter = qset.value('/LatLonTools/ConverterDelimiter', ', ')
        self.converterDdmmssDelimiter = qset.value('/LatLonTools/ConverterDdmmssDelimiter', ', ')
        self.converterAddDmsSpace = int(qset.value('/LatLonTools/ConverterAddDmsSpace', Qt.Checked))
        self.converterPadZeroes = int(qset.value('/LatLonTools/ConverterPadZeroes', Qt.Unchecked))
        self.converterNsewBeginning = int(qset.value('/LatLonTools/ConverterNsewBeginning', Qt.Unchecked))
        self.converterMgrsAddSpacesCheckBox = int(qset.value('/LatLonTools/ConverterMgrsAddSpaces', Qt.Unchecked))
        self.converterMgrsPrec = int(qset.value('/LatLonTools/ConverterMgrsPrecision', 5))

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
    ProjectionTypeUPS = 8
    ProjectionTypeGEOREF = 9
    ProjectionTypeH3 = 10
    ZoomProjectionTypeH3 = 8

    def __init__(self, lltools, iface, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.lltools = lltools
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restoreDefaults)
        if H3_INSTALLED:
            self.captureH3Label.setEnabled(True)
            self.captureH3PrecisionSpinBox.setEnabled(True)
        else:
            self.captureH3Label.setEnabled(False)
            self.captureH3PrecisionSpinBox.setEnabled(False)

        ### CAPTURE SETTINGS ###
        if H3_INSTALLED:
            self.captureProjectionComboBox.addItems([tr('WGS 84 (Latitude & Longitude)'), tr('Project CRS'), tr('Custom CRS'), tr('MGRS'), tr('Plus Codes (Open Location Code)'), tr('Standard UTM'),tr('Geohash'),tr('Maidenhead Grid Locator'),tr('UPS'),tr('GEOREF'),'H3'])
        else:
            self.captureProjectionComboBox.addItems([tr('WGS 84 (Latitude & Longitude)'), tr('Project CRS'), tr('Custom CRS'), tr('MGRS'), tr('Plus Codes (Open Location Code)'), tr('Standard UTM'),tr('Geohash'),tr('Maidenhead Grid Locator'),tr('UPS'),tr('GEOREF')])
        self.captureProjectionSelectionWidget.setCrs(epsg4326)
        self.wgs84NumberFormatComboBox.addItems([tr('Decimal Degrees'), 'D°M\'S"', 'DDMMSS', 'D°M.MM\'', 'WKT POINT', 'GeoJSON'])
        self.otherNumberFormatComboBox.addItems([tr('Normal Coordinate'), 'WKT POINT'])
        self.coordOrderComboBox.addItems([tr('Lat, Lon (Y,X) - Google Map Order'), tr('Lon, Lat (X,Y) Order')])
        self.delimComboBox.addItems([tr('Comma'), tr('Comma Space'), tr('Space'), tr('Tab'), tr('Other')])
        self.captureProjectionComboBox.activated.connect(self.setEnabled)
        self.captureUtmFormatComboBox.addItems(['15N 755631 4283168', '755631,4283168,15N','755631mE,4283168mN,15N', '755631mE,4283168mN,15,N'])
        self.captureUpsFormatComboBox.addItems(['Z 2426773mE 1530125mN', 'Z2426773E1530125N'])

        ### ZOOM TO SETTINGS ###
        if H3_INSTALLED:
            self.zoomToProjectionComboBox.addItems([tr('WGS 84 (Latitude & Longitude) / Auto Detect Format'), tr('Project CRS'), tr('Custom CRS'), tr('MGRS'), tr('Plus Codes (Open Location Code)'), tr('Standard UTM'),tr('Geohash'),tr('Maidenhead Grid'),'H3'])
        else:
            self.zoomToProjectionComboBox.addItems([tr('WGS 84 (Latitude & Longitude) / Auto Detect Format'), tr('Project CRS'), tr('Custom CRS'), tr('MGRS'), tr('Plus Codes (Open Location Code)'), tr('Standard UTM'),tr('Geohash'),tr('Maidenhead Grid')])
        self.zoomToProjectionSelectionWidget.setCrs(epsg4326)
        self.zoomToCoordOrderComboBox.addItems([tr('Lat, Lon (Y,X) - Google Map Order'), tr('Lon, Lat (X,Y) Order')])
        self.zoomToProjectionComboBox.activated.connect(self.setEnabled)

        ### EXTERNAL MAP ###
        self.addProviderButton.clicked.connect(self.addUserProvider)
        self.deleteProviderButton.clicked.connect(self.deleteUserProvider)

        ### MULTI-ZOOM ###
        self.multiZoomToProjectionComboBox.addItems([tr('WGS 84 (Latitude & Longitude)'), tr('Project CRS'), tr('Custom CRS'), tr('MGRS'), tr('Plus Codes (Open Location Code)'), tr('Standard UTM')])
        self.multiZoomToProjectionComboBox.activated.connect(self.setEnabled)
        self.multiZoomToProjectionSelectionWidget.setCrs(epsg4326)
        self.qmlBrowseButton.clicked.connect(self.qmlOpenDialog)
        self.markerStyleComboBox.addItems([tr('Default'), tr('Labeled'), tr('Custom')])
        self.multiCoordOrderComboBox.addItems([tr('Lat, Lon (Y,X) - Google Map Order'), tr('Lon, Lat (X,Y) Order')])
        self.qmlStyle = ''

        ### BBOX CAPTURE SETTINGS ###
        self.bBoxCrsComboBox.addItems([tr('WGS 84 (Latitude & Longitude)'), tr('Project CRS')])
        self.bBoxFormatComboBox.addItems([
            tr('"minX,minY,maxX,maxY (W,S,E,N)" - Using the selected delimiter'),
            tr('"minX,maxX,minY,maxY (W,E,S,N)" - Using the selected delimiter'),
            tr('"minY,minX,maxY,maxX (S,W,N,E)" - Using the selected delimiter'),
            tr('"x1 y1,x2 y2,x3 y3,x4 y4,x1 y1" - Polygon format'),
            tr('"x1,y1 x2,y2 x3,y3 x4,y4 x1,y1" - Alternate polgyon format'),
            tr('WKT Polygon'),
            tr('"bbox: [minX, minY, maxX, maxY]" - MapProxy'),
            tr('"bbox=minX,minY,maxX,maxY" - GeoServer WFS, WMS')])
        self.bBoxDelimiterComboBox.addItems([tr('Comma'), tr('Comma Space'), tr('Space'), tr('Tab'), tr('Other')])

        ### COORDINATE CONVERSION SETTINGS ###
        self.converterCoordOrderComboBox.addItems([tr('Lat, Lon (Y,X) - Google Map Order'), tr('Lon, Lat (X,Y) Order')])
        self.converterUtmFormatComboBox.addItems(['15N 755631 4283168', '755631,4283168,15N','755631mE,4283168mN,15N', '755631mE,4283168mN,15,N'])
        self.converterUpsFormatComboBox.addItems(['Z 2426773mE 1530125mN', 'Z2426773E1530125N'])
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
        self.coordOrderComboBox.setCurrentIndex(CoordOrder.OrderYX)
        self.otherTxt.setText("")
        self.delimComboBox.setCurrentIndex(1)
        self.precisionSpinBox.setValue(0)
        self.captureDmmPrecisionSpinBox.setValue(4)
        self.captureUtmPrecisionSpinBox.setValue(0)
        self.captureUtmFormatComboBox.setCurrentIndex(0)
        self.captureUpsPrecisionSpinBox.setValue(0)
        self.captureUpsFormatComboBox.setCurrentIndex(0)
        self.captureGeohashSpinBox.setValue(12)
        self.captureMaidenheadPrecisionSpinBox.setValue(3)
        self.captureGeorefPrecisionSpinBox.setValue(5)
        self.captureProjectionSelectionWidget.setCrs(epsg4326)
        self.plusCodesSpinBox.setValue(10)
        self.digitsSpinBox.setValue(8)
        self.capturePrefixLineEdit.setText('')
        self.captureSuffixLineEdit.setText('')
        self.captureMarkerCheckBox.setCheckState(Qt.Unchecked)
        self.captureAddDmsSpaceCheckBox.setCheckState(Qt.Checked)
        self.capturePadZeroesCheckBox.setCheckState(Qt.Unchecked)
        self.captureMgrsAddSpacesCheckBox.setCheckState(Qt.Unchecked)
        self.captureMgrsPrecisionSpinBox.setValue(5)
        if H3_INSTALLED:
            self.captureH3PrecisionSpinBox.setValue(8)

        ### ZOOM TO SETTINGS ###
        self.zoomToProjectionComboBox.setCurrentIndex(self.ProjectionTypeWgs84)
        self.zoomToCoordOrderComboBox.setCurrentIndex(CoordOrder.OrderYX)
        self.persistentMarkerCheckBox.setCheckState(Qt.Checked)
        self.showGridCheckBox.setCheckState(Qt.Checked)
        self.zoomToProjectionSelectionWidget.setCrs(epsg4326)
        self.markerSizeSpinBox.setValue(18)
        self.markerWidthSpinBox.setValue(2)
        self.gridWidthSpinBox.setValue(2)
        markerColor = QColor('#ff0000')
        markerColor.setAlpha(255)
        gridColor = QColor('#ff0000')
        gridColor.setAlpha(255)
        self.markerColorButton.setColor(markerColor)
        self.gridColorButton.setColor(gridColor)

        ### EXTERNAL MAP ###
        self.showPlacemarkCheckBox.setCheckState(Qt.Checked)
        self.mapProviderComboBox.setCurrentIndex(0)
        self.mapProviderRComboBox.setCurrentIndex(0)
        self.zoomSpinBox.setValue(13)
        self.showLocationCheckBox.setCheckState(Qt.Unchecked)

        ### Multi-zoom Settings ###
        self.multiZoomToProjectionComboBox.setCurrentIndex(0)  # WGS 84
        self.multiZoomToProjectionSelectionWidget.setCrs(epsg4326)
        self.multiCoordOrderComboBox.setCurrentIndex(CoordOrder.OrderYX)
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
        self.converterUtmFormatComboBox.setCurrentIndex(0)
        self.converterUpsPrecisionSpinBox.setValue(0)
        self.converterUpsFormatComboBox.setCurrentIndex(0)
        self.converterPlusCodePrecisionSpinBox.setValue(10)
        self.converterGeohashSpinBox.setValue(12)
        self.converterMaidenheadPrecisionSpinBox.setValue(3)
        self.converterGeorefPrecisionSpinBox.setValue(5)
        self.converterDelimiterLineEdit.setText(',')
        self.converterDdmmssDelimiterLineEdit.setText(',')
        self.converterAddDmsSpaceCheckBox.setCheckState(Qt.Checked)
        self.converterPadZeroesCheckBox.setCheckState(Qt.Unchecked)
        self.converterNsewBeginningCheckBox.setCheckState(Qt.Unchecked)
        self.converterMgrsAddSpacesCheckBox.setCheckState(Qt.Unchecked)
        self.converterMgrsPrecisionSpinBox.setValue(5)


    def readSettings(self):
        '''Load the user selected settings. The settings are retained even when
        the user quits QGIS. This just loads the saved information into varialbles,
        but does not update the widgets. The widgets are updated with showEvent.'''
        qset = QgsSettings()

        ### CAPTURE SETTINGS ###
        self.captureProjection = int(qset.value('/LatLonTools/CaptureProjection', self.ProjectionTypeWgs84))
        if not H3_INSTALLED and self.captureProjection == self.ProjectionTypeH3:
            self.captureProjection = 0
        self.delimiter = qset.value('/LatLonTools/Delimiter', ', ')
        self.dmsPrecision = int(qset.value('/LatLonTools/DMSPrecision', 0))
        self.coordOrder = int(qset.value('/LatLonTools/CoordOrder', CoordOrder.OrderYX))
        self.wgs84NumberFormat = int(qset.value('/LatLonTools/WGS84NumberFormat', 0))
        self.otherNumberFormat = int(qset.value('/LatLonTools/OtherNumberFormat', 0))
        self.plusCodesLength = int(qset.value('/LatLonTools/PlusCodesLength', 10))
        self.decimalDigits = int(qset.value('/LatLonTools/DecimalDigits', 8))
        self.capturePrefix = qset.value('/LatLonTools/CapturePrefix', '')
        self.captureSuffix = qset.value('/LatLonTools/CaptureSuffix', '')

        ### ZOOM TO SETTINGS ###
        self.zoomToCoordOrder = int(qset.value('/LatLonTools/ZoomToCoordOrder', CoordOrder.OrderYX))
        self.zoomToProjection = int(qset.value('/LatLonTools/ZoomToCoordType', 0))
        if not H3_INSTALLED and self.zoomToProjection == self.ZoomProjectionTypeH3:
            self.zoomToProjection = 0
        self.persistentMarker = int(qset.value('/LatLonTools/PersistentMarker', Qt.Checked))
        self.showGrid = int(qset.value('/LatLonTools/ShowGrid', Qt.Checked))
        self.zoomToCustomCrsAuthId = qset.value('/LatLonTools/ZoomToCustomCrsId', 'EPSG:4326')
        self.zoomToProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(self.zoomToCustomCrsAuthId))

        ### MULTI-ZOOM CUSTOM QML STYLE ###
        self.multiZoomToProjection = int(qset.value('/LatLonTools/MultiZoomToProjection', 0))
        self.multiCoordOrder = int(qset.value('/LatLonTools/MultiCoordOrder', CoordOrder.OrderYX))
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
        qset = QgsSettings()

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
        qset.setValue('/LatLonTools/CaptureUtmFormat', int(self.captureUtmFormatComboBox.currentIndex()))
        qset.setValue('/LatLonTools/CaptureUpsPrecision', self.captureUpsPrecisionSpinBox.value())
        qset.setValue('/LatLonTools/CaptureUpsFormat', int(self.captureUpsFormatComboBox.currentIndex()))
        qset.setValue('/LatLonTools/CaptureGeohashPrecision', self.captureGeohashSpinBox.value())
        qset.setValue('/LatLonTools/CaptureMaidenheadPrecision', self.captureMaidenheadPrecisionSpinBox.value())
        qset.setValue('/LatLonTools/CaptureGeorefPrecision', self.captureGeorefPrecisionSpinBox.value())
        qset.setValue('/LatLonTools/PlusCodesLength', self.plusCodesSpinBox.value())
        qset.setValue('/LatLonTools/DecimalDigits', self.digitsSpinBox.value())
        qset.setValue('/LatLonTools/CapturePrefix', self.capturePrefixLineEdit.text())
        qset.setValue('/LatLonTools/CaptureSuffix', self.captureSuffixLineEdit.text())
        qset.setValue('/LatLonTools/CaptureShowClickedLocation', self.captureMarkerCheckBox.checkState())
        qset.setValue('/LatLonTools/CaptureAddDmsSpace', self.captureAddDmsSpaceCheckBox.checkState())
        qset.setValue('/LatLonTools/CapturePadZeroes', self.capturePadZeroesCheckBox.checkState())
        qset.setValue('/LatLonTools/CaptureMgrsAddSpaces', self.captureMgrsAddSpacesCheckBox.checkState())
        qset.setValue('/LatLonTools/CaptureMgrsPrecision', int(self.captureMgrsPrecisionSpinBox.value()))
        if H3_INSTALLED:
            qset.setValue('/LatLonTools/CaptureH3Precision', self.captureH3PrecisionSpinBox.value())

        ### ZOOM TO SETTINGS ###
        qset.setValue('/LatLonTools/ZoomToCoordType', int(self.zoomToProjectionComboBox.currentIndex()))
        qset.setValue('/LatLonTools/ZoomToCoordOrder', int(self.zoomToCoordOrderComboBox.currentIndex()))
        qset.setValue('/LatLonTools/PersistentMarker', self.persistentMarkerCheckBox.checkState())
        qset.setValue('/LatLonTools/ShowGrid', self.showGridCheckBox.checkState())
        qset.setValue('/LatLonTools/ZoomToCustomCrsId', self.zoomToCustomCrsId())
        qset.setValue('/LatLonTools/MarkerSize', int(self.markerSizeSpinBox.value()))
        qset.setValue('/LatLonTools/MarkerWidth', int(self.markerWidthSpinBox.value()))
        qset.setValue('/LatLonTools/GridWidth', int(self.gridWidthSpinBox.value()))
        settings.markerColor = self.markerColorButton.color()
        settings.gridColor = self.gridColorButton.color()
        qset.setValue('/LatLonTools/MarkerColor', settings.markerColor.name())
        qset.setValue('/LatLonTools/MarkerColorOpacity', settings.markerColor.alpha())
        qset.setValue('/LatLonTools/GridColor', settings.gridColor.name())
        qset.setValue('/LatLonTools/GridColorOpacity', settings.gridColor.alpha())

        ### EXTERNAL MAP ###
        qset.setValue('/LatLonTools/ShowPlacemark', self.showPlacemarkCheckBox.checkState())
        qset.setValue('/LatLonTools/ExternMapShowClickedLocation', self.showLocationCheckBox.checkState())
        qset.setValue('/LatLonTools/MapProvider', int(self.mapProviderComboBox.currentIndex()))
        qset.setValue('/LatLonTools/MapProviderRight', int(self.mapProviderRComboBox.currentIndex()))
        if settings.userMapProviders:
            qset.setValue('/LatLonTools/UserMapProviders', settings.userMapProviders)
        else:
            qset.setValue('/LatLonTools/UserMapProviders', 0)
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
        qset.setValue('/LatLonTools/ConverterUtmFormat', int(self.converterUtmFormatComboBox.currentIndex()))
        qset.setValue('/LatLonTools/ConverterUpsPrecision', int(self.converterUpsPrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterUpsFormat', int(self.converterUpsFormatComboBox.currentIndex()))
        qset.setValue('/LatLonTools/ConverterPlusCodeLength', int(self.converterPlusCodePrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterGeohashPrecision', int(self.converterGeohashSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterMaidenheadPrecision', int(self.converterMaidenheadPrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterGeorefPrecision', int(self.converterGeorefPrecisionSpinBox.value()))
        qset.setValue('/LatLonTools/ConverterDelimiter', self.converterDelimiterLineEdit.text())
        qset.setValue('/LatLonTools/ConverterDdmmssDelimiter', self.converterDdmmssDelimiterLineEdit.text())
        qset.setValue('/LatLonTools/ConverterAddDmsSpace', self.converterAddDmsSpaceCheckBox.checkState())
        qset.setValue('/LatLonTools/ConverterPadZeroes', self.converterPadZeroesCheckBox.checkState())
        qset.setValue('/LatLonTools/ConverterNsewBeginning', self.converterNsewBeginningCheckBox.checkState())
        qset.setValue('/LatLonTools/ConverterMgrsAddSpaces', self.converterMgrsAddSpacesCheckBox.checkState())
        qset.setValue('/LatLonTools/ConverterMgrsPrecision', int(self.converterMgrsPrecisionSpinBox.value()))

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
            None, tr("Input QML Style File"),
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
                (zoomToProjection != self.ProjectionTypeGeohash) and (zoomToProjection != self.ProjectionTypeMaidenhead) and
                (zoomToProjection != self.ZoomProjectionTypeH3))
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
        self.captureUtmFormatComboBox.setCurrentIndex(settings.captureUtmFormat)
        self.captureUpsPrecisionSpinBox.setValue(settings.captureUpsPrecision)
        self.captureUpsFormatComboBox.setCurrentIndex(settings.captureUpsFormat)
        self.captureGeohashSpinBox.setValue(settings.captureGeohashPrecision)
        self.captureH3PrecisionSpinBox.setValue(settings.captureH3Precision)
        self.captureMaidenheadPrecisionSpinBox.setValue(settings.captureMaidenheadPrecision)
        self.captureGeorefPrecisionSpinBox.setValue(settings.captureGeorefPrecision)
        self.capturePrefixLineEdit.setText(self.capturePrefix)
        self.captureSuffixLineEdit.setText(self.captureSuffix)
        self.captureMarkerCheckBox.setCheckState(settings.captureShowLocation)
        self.captureAddDmsSpaceCheckBox.setCheckState(settings.captureAddDmsSpace)
        self.capturePadZeroesCheckBox.setCheckState(settings.capturePadZeroes)
        self.captureMgrsAddSpacesCheckBox.setCheckState(settings.captureMgrsAddSpacesCheckBox)
        self.captureMgrsPrecisionSpinBox.setValue(settings.captureMgrsPrec)

        ### ZOOM TO SETTINGS ###
        self.zoomToProjectionComboBox.setCurrentIndex(self.zoomToProjection)
        if self.zoomToCustomCrsAuthId == 'EPSG:4326':
            self.zoomToProjectionSelectionWidget.setCrs(epsg4326)
        else:
            self.zoomToProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(self.zoomToCustomCrsAuthId))
        self.zoomToCoordOrderComboBox.setCurrentIndex(self.zoomToCoordOrder)
        self.persistentMarkerCheckBox.setCheckState(self.persistentMarker)
        self.showGridCheckBox.setCheckState(self.showGrid)
        self.markerSizeSpinBox.setValue(settings.markerSize)
        self.markerWidthSpinBox.setValue(settings.markerWidth)
        self.gridWidthSpinBox.setValue(settings.gridWidth)
        self.markerColorButton.setColor(settings.markerColor)
        self.gridColorButton.setColor(settings.gridColor)

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
        self.converterUtmFormatComboBox.setCurrentIndex(settings.converterUtmFormat)
        self.converterUpsPrecisionSpinBox.setValue(settings.converterUpsPrec)
        self.converterUpsFormatComboBox.setCurrentIndex(settings.converterUpsFormat)
        self.converterPlusCodePrecisionSpinBox.setValue(settings.converterPlusCodeLength)
        self.converterGeohashSpinBox.setValue(settings.converterGeohashPrecision)
        self.converterMaidenheadPrecisionSpinBox.setValue(settings.converterMaidenheadPrecision)
        self.converterGeorefPrecisionSpinBox.setValue(settings.converterGeorefPrecision)
        self.converterDelimiterLineEdit.setText(settings.converterDelimiter)
        self.converterDdmmssDelimiterLineEdit.setText(settings.converterDdmmssDelimiter)
        self.converterAddDmsSpaceCheckBox.setCheckState(settings.converterAddDmsSpace)
        self.converterPadZeroesCheckBox.setCheckState(settings.converterPadZeroes)
        self.converterNsewBeginningCheckBox.setCheckState(settings.converterNsewBeginning)
        self.converterMgrsAddSpacesCheckBox.setCheckState(settings.converterMgrsAddSpacesCheckBox)
        self.converterMgrsPrecisionSpinBox.setValue(settings.converterMgrsPrec)

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

    def captureProjIsUPS(self):
        if self.captureProjection == self.ProjectionTypeUPS:
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

    def captureProjIsGEOREF(self):
        if self.captureProjection == self.ProjectionTypeGEOREF:
            return True
        return False

    def captureProjIsH3(self):
        if self.captureProjection == self.ProjectionTypeH3:
            return True
        return False

    def setZoomToCoordOrder(self, order):
        if order:
            self.zoomToCoordOrder = CoordOrder.OrderXY
        else:
            self.zoomToCoordOrder = CoordOrder.OrderYX
        self.zoomToCoordOrderComboBox.setCurrentIndex(self.zoomToCoordOrder)
        qset = QgsSettings()
        qset.setValue('/LatLonTools/ZoomToCoordOrder', self.zoomToCoordOrder)

    def setZoomToMode(self, mode, crs=None):
        qset = QgsSettings()
        if mode == 'wgs84':
            self.zoomToProjection = self.ProjectionTypeWgs84
        elif mode == 'project':
            self.zoomToProjection = self.ProjectionTypeProjectCRS
        elif mode == 'custom':
            self.zoomToProjection = self.ProjectionTypeCustomCRS
            if not crs:
                crs = epsg4326
            self.zoomToCustomCrsAuthId = crs.authid()
            qset.setValue('/LatLonTools/ZoomToCustomCrsId', self.zoomToCustomCrsAuthId)
            self.zoomToProjectionSelectionWidget.setCrs(crs)
        elif mode == 'mgrs':
            self.zoomToProjection = self.ProjectionTypeMGRS
        elif mode == 'pluscode':
            self.zoomToProjection = self.ProjectionTypePlusCodes
        elif mode == 'utm':
            self.zoomToProjection = self.ProjectionTypeUTM
        elif mode == 'geohash':
            self.zoomToProjection = self.ProjectionTypeGeohash
        elif mode == 'ham':
            self.zoomToProjection = self.ProjectionTypeMaidenhead
        elif mode == 'h3':
            self.zoomToProjection = self.ZoomProjectionTypeH3
        self.zoomToProjectionComboBox.setCurrentIndex(self.zoomToProjection)
        qset.setValue('/LatLonTools/ZoomToCoordType', int(self.zoomToProjectionComboBox.currentIndex()))

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

    def zoomToProjIsH3(self):
        if self.zoomToProjection == self.ZoomProjectionTypeH3:
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
            return self.epsg4326
        if self.multiZoomToProjection == 1:  # Project CRS
            return self.canvas.mapSettings().destinationCrs()
        if self.multiZoomToProjection == 2:  # Custom CRS
            return self.multiZoomToCustomCRS()
