import os
import re
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget, QMenu, QApplication
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.uic import loadUiType
from qgis.core import QgsCoordinateTransform, QgsPoint, QgsPointXY, QgsProject
from .util import epsg4326, parseDMSString, formatDmsString
# import traceback

from .captureCoordinate  import CaptureCoordinate
from .settings import settings
from . import mgrs
from . import olc
from .utm import latLon2UtmString, isUtm, utmString2Crs
from . import geohash
from . import maidenhead

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/coordinateConverter.ui'))

class CoordinateConverterWidget(QDockWidget, FORM_CLASS):
    inputProjection = 0
    origPt = None
    origCrs = epsg4326

    def __init__(self, lltools, settingsDialog, iface, parent):
        super(CoordinateConverterWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.lltools = lltools
        self.settings = settingsDialog
        self.savedMapTool = None

        self.clipboard = QApplication.clipboard()

        # Set up a connection with the coordinate capture tool
        self.captureCoordinate = CaptureCoordinate(self.canvas)
        self.captureCoordinate.capturePoint.connect(self.capturedPoint)
        self.captureCoordinate.captureStopped.connect(self.stopCapture)

        self.xymenu = QMenu()
        icon = QIcon(os.path.dirname(__file__) + '/images/yx.png')
        a = self.xymenu.addAction(icon, "Y, X (Lat, Lon) Order")
        a.setData(0)
        icon = QIcon(os.path.dirname(__file__) + '/images/xy.png')
        a = self.xymenu.addAction(icon, "X, Y (Lon, Lat) Order")
        a.setData(1)
        self.xyButton.setIconSize(QSize(16, 16))
        self.xyButton.setIcon(icon)
        self.xyButton.setMenu(self.xymenu)
        self.xyButton.triggered.connect(self.xyTriggered)
        self.inputXYOrder = settings.converterCoordOrder
        self.clearFormButton.setIcon(QIcon(':/images/themes/default/mIconClearText.svg'))
        self.clearFormButton.clicked.connect(self.clearForm)
        self.coordCaptureButton.setIcon(QIcon(os.path.dirname(__file__) + "/images/coordinate_capture.png"))
        self.coordCaptureButton.clicked.connect(self.startCapture)
        self.zoomButton.setIcon(QIcon(':/images/themes/default/mActionZoomIn.svg'))
        self.zoomButton.clicked.connect(self.zoomTo)
        self.optionsButton.setIcon(QIcon(':/images/themes/default/mActionOptions.svg'))
        self.optionsButton.clicked.connect(self.showSettings)

        icon = QIcon(os.path.dirname(__file__) + "/images/check.png")
        self.wgs84CommitButton.setIcon(icon)
        self.projCommitButton.setIcon(icon)
        self.customCommitButton.setIcon(icon)
        self.dmsCommitButton.setIcon(icon)
        self.dmCommitButton.setIcon(icon)
        self.ddmmssCommitButton.setIcon(icon)
        self.utmCommitButton.setIcon(icon)
        self.mgrsCommitButton.setIcon(icon)
        self.plusCommitButton.setIcon(icon)
        self.geohashCommitButton.setIcon(icon)
        self.maidenheadCommitButton.setIcon(icon)

        self.wgs84CommitButton.clicked.connect(self.commitWgs84)
        self.wgs84LineEdit.returnPressed.connect(self.commitWgs84)
        self.projCommitButton.clicked.connect(self.commitProject)
        self.projLineEdit.returnPressed.connect(self.commitProject)
        self.customCommitButton.clicked.connect(self.commitCustom)
        self.customLineEdit.returnPressed.connect(self.commitCustom)
        self.dmsCommitButton.clicked.connect(self.commitDms)
        self.dmsLineEdit.returnPressed.connect(self.commitDms)
        self.dmCommitButton.clicked.connect(self.commitDm)
        self.dmLineEdit.returnPressed.connect(self.commitDm)
        self.ddmmssCommitButton.clicked.connect(self.commitDdmmss)
        self.ddmmssLineEdit.returnPressed.connect(self.commitDdmmss)
        self.utmCommitButton.clicked.connect(self.commitUtm)
        self.utmLineEdit.returnPressed.connect(self.commitUtm)
        self.mgrsCommitButton.clicked.connect(self.commitMgrs)
        self.mgrsLineEdit.returnPressed.connect(self.commitMgrs)
        self.plusCommitButton.clicked.connect(self.commitPlus)
        self.plusLineEdit.returnPressed.connect(self.commitPlus)
        self.geohashCommitButton.clicked.connect(self.commitGeohash)
        self.geohashLineEdit.returnPressed.connect(self.commitGeohash)
        self.maidenheadCommitButton.clicked.connect(self.commitMaidenhead)
        self.maidenheadLineEdit.returnPressed.connect(self.commitMaidenhead)

        icon = QIcon(':/images/themes/default/mActionEditCopy.svg')
        self.wgs84CopyButton.setIcon(icon)
        self.projCopyButton.setIcon(icon)
        self.customCopyButton.setIcon(icon)
        self.dmsCopyButton.setIcon(icon)
        self.dmCopyButton.setIcon(icon)
        self.ddmmssCopyButton.setIcon(icon)
        self.utmCopyButton.setIcon(icon)
        self.mgrsCopyButton.setIcon(icon)
        self.plusCopyButton.setIcon(icon)
        self.geohashCopyButton.setIcon(icon)
        self.maidenheadCopyButton.setIcon(icon)

        self.wgs84CopyButton.clicked.connect(self.copyWgs84)
        self.projCopyButton.clicked.connect(self.copyProject)
        self.customCopyButton.clicked.connect(self.copyCustom)
        self.dmsCopyButton.clicked.connect(self.copyDms)
        self.dmCopyButton.clicked.connect(self.copyDm)
        self.ddmmssCopyButton.clicked.connect(self.copyDdmmss)
        self.utmCopyButton.clicked.connect(self.copyUtm)
        self.mgrsCopyButton.clicked.connect(self.copyMgrs)
        self.plusCopyButton.clicked.connect(self.copyPlus)
        self.geohashCopyButton.clicked.connect(self.copyGeohash)
        self.maidenheadCopyButton.clicked.connect(self.copyMaidenhead)

        self.customProjectionSelectionWidget.setCrs(epsg4326)
        self.customProjectionSelectionWidget.crsChanged.connect(self.customCrsChanged)

    def showEvent(self, e):
        self.inputXYOrder = settings.converterCoordOrder
        self.xyButton.setDefaultAction(self.xymenu.actions()[settings.converterCoordOrder])
        self.updateLabel()

    def closeEvent(self, e):
        if self.savedMapTool:
            self.canvas.setMapTool(self.savedMapTool)
            self.savedMapTool = None

    def xyTriggered(self, action):
        self.xyButton.setDefaultAction(action)
        self.inputXYOrder = action.data()
        if self.origPt is not None:
            self.updateCoordinates(-1, self.origPt, self.origCrs)
        self.updateLabel()

    def showInvalid(self, id):
        self.origPt = None
        if id != 0:
            self.wgs84LineEdit.setText('Invalid')
        if id != 1:
            self.projLineEdit.setText('Invalid')
        if id != 2:
            self.customLineEdit.setText('Invalid')
        if id != 3:
            self.dmsLineEdit.setText('Invalid')
        if id != 4:
            self.dmLineEdit.setText('Invalid')
        if id != 5:
            self.ddmmssLineEdit.setText('Invalid')
        if id != 6:
            self.utmLineEdit.setText('Invalid')
        if id != 7:
            self.mgrsLineEdit.setText('Invalid')
        if id != 8:
            self.plusLineEdit.setText('Invalid')
        if id != 9:
            self.geohashLineEdit.setText('Invalid')
        if id != 10:
            self.maidenheadLineEdit.setText('Invalid')

    def clearForm(self):
        self.origPt = None
        self.wgs84LineEdit.setText('')
        self.projLineEdit.setText('')
        self.customLineEdit.setText('')
        self.dmsLineEdit.setText('')
        self.dmLineEdit.setText('')
        self.ddmmssLineEdit.setText('')
        self.utmLineEdit.setText('')
        self.mgrsLineEdit.setText('')
        self.plusLineEdit.setText('')
        self.geohashLineEdit.setText('')
        self.maidenheadLineEdit.setText('')

    def updateCoordinates(self, id, pt, crs):
        self.origPt = pt
        self.origCrs = crs
        projCRS = self.canvas.mapSettings().destinationCrs()
        customCRS = self.customProjectionSelectionWidget.crs()
        if crs == epsg4326:
            pt4326 = pt
        else:
            trans = QgsCoordinateTransform(crs, epsg4326, QgsProject.instance())
            pt4326 = trans.transform(pt.x(), pt.y())
        if id != 0:  # WGS 84
            if self.inputXYOrder == 0:  # Y, X
                s = '{:.{prec}f}{}{:.{prec}f}'.format(pt4326.y(), settings.converterDelimiter, pt4326.x(), prec=settings.converter4326DDPrec)
            else:
                s = '{:.{prec}f}{}{:.{prec}f}'.format(pt4326.x(), settings.converterDelimiter, pt4326.y(), prec=settings.converter4326DDPrec)
            self.wgs84LineEdit.setText(s)
        if id != 1:  # Project CRS
            if crs == projCRS:
                newpt = pt
            else:
                trans = QgsCoordinateTransform(crs, projCRS, QgsProject.instance())
                newpt = trans.transform(pt.x(), pt.y())
            if projCRS == epsg4326:
                precision = settings.converter4326DDPrec
            else:
                precision = settings.converterDDPrec
            if self.inputXYOrder == 0:  # Y, X
                s = '{:.{prec}f}{}{:.{prec}f}'.format(newpt.y(), settings.converterDelimiter, newpt.x(), prec=precision)
            else:
                s = '{:.{prec}f}{}{:.{prec}f}'.format(newpt.x(), settings.converterDelimiter, newpt.y(), prec=precision)
            self.projLineEdit.setText(s)
        if id != 2:  # Custom CRS
            if crs == customCRS:
                newpt = pt
            else:
                trans = QgsCoordinateTransform(crs, customCRS, QgsProject.instance())
                newpt = trans.transform(pt.x(), pt.y())
            if customCRS == epsg4326:
                precision = settings.converter4326DDPrec
            else:
                precision = settings.converterDDPrec
            if self.inputXYOrder == 0:  # Y, X
                s = '{:.{prec}f}{}{:.{prec}f}'.format(newpt.y(), settings.converterDelimiter, newpt.x(), prec=precision)
            else:
                s = '{:.{prec}f}{}{:.{prec}f}'.format(newpt.x(), settings.converterDelimiter, newpt.y(), prec=precision)
            self.customLineEdit.setText(s)
        if id != 3:  # D M' S"
            s = formatDmsString(pt4326.y(), pt4326.x(), 0, settings.converterDmsPrec, self.inputXYOrder,
                    settings.converterDelimiter, settings.converterAddDmsSpace, settings.converterPadZeroes)
            self.dmsLineEdit.setText(s)
        if id != 4:  # D M.MM'
            s = formatDmsString(pt4326.y(), pt4326.x(), 2, settings.converterDmmPrec, self.inputXYOrder,
                    settings.converterDelimiter, settings.converterAddDmsSpace, settings.converterPadZeroes)
            self.dmLineEdit.setText(s)
        if id != 5:  # DDMMSS
            s = formatDmsString(pt4326.y(), pt4326.x(), 1, settings.converterDmsPrec, self.inputXYOrder, settings.converterDdmmssDelimiter)
            self.ddmmssLineEdit.setText(s)
        if id != 6:  # UTM
            s = latLon2UtmString(pt4326.y(), pt4326.x(), settings.converterUtmPrec)
            self.utmLineEdit.setText(s)
        if id != 7:  # MGRS
            try:
                s = mgrs.toMgrs(pt4326.y(), pt4326.x())
            except Exception:
                s = 'Invalid'
            self.mgrsLineEdit.setText(s)
        if id != 8:  # Plus Codes
            try:
                s = olc.encode(pt4326.y(), pt4326.x(), settings.converterPlusCodeLength)
            except Exception:
                s = 'Invalid'
            self.plusLineEdit.setText(s)
        if id != 9: # GEOHASH
            try:
                s = geohash.encode(pt4326.y(), pt4326.x(), settings.converterGeohashPrecision)
            except Exception:
                s = 'Invalid'
            self.geohashLineEdit.setText(s)
        if id != 10: # Maidenhead
            try:
                s = maidenhead.toMaiden(pt4326.y(), pt4326.x(), precision=settings.converterMaidenheadPrecision)
            except Exception:
                s = 'Invalid'
            self.maidenheadLineEdit.setText(s)

    def commitWgs84(self):
        text = self.wgs84LineEdit.text().strip()
        try:
            lat, lon = parseDMSString(text, self.inputXYOrder)
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(0, pt, epsg4326)
        except Exception:
            # traceback.print_exc()
            self.showInvalid(0)

    def commitProject(self):
        projCRS = self.canvas.mapSettings().destinationCrs()
        text = self.projLineEdit.text().strip()
        try:
            if projCRS == epsg4326:
                lat, lon = parseDMSString(text, self.inputXYOrder)
            else:
                coords = re.split(r'[\s,;:]+', text, 1)
                if len(coords) < 2:
                    self.showInvalid(1)
                    return
                if self.inputXYOrder == 0:  # Lat, Lon
                    lat = float(coords[0])
                    lon = float(coords[1])
                else:  # Lon, Lat
                    lon = float(coords[0])
                    lat = float(coords[1])
        except Exception:
            self.showInvalid(1)
            return

        pt = QgsPoint(lon, lat)
        self.updateCoordinates(1, pt, projCRS)

    def commitCustom(self):
        customCRS = self.customProjectionSelectionWidget.crs()
        text = self.customLineEdit.text().strip()
        try:
            if customCRS == epsg4326:
                lat, lon = parseDMSString(text, self.inputXYOrder)
            else:
                coords = re.split(r'[\s,;:]+', text, 1)
                if len(coords) < 2:
                    self.showInvalid(2)
                    return
                if self.inputXYOrder == 0:  # Lat, Lon
                    lat = float(coords[0])
                    lon = float(coords[1])
                else:  # Lon, Lat
                    lon = float(coords[0])
                    lat = float(coords[1])
        except Exception:
            self.showInvalid(2)
            return

        pt = QgsPoint(lon, lat)
        self.updateCoordinates(2, pt, customCRS)

    def commitDms(self):
        text = self.dmsLineEdit.text().strip()
        try:
            lat, lon = parseDMSString(text, self.inputXYOrder)
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(3, pt, epsg4326)
        except Exception:
            self.showInvalid(3)

    def commitDm(self):
        text = self.dmLineEdit.text().strip()
        try:
            lat, lon = parseDMSString(text, self.inputXYOrder)
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(4, pt, epsg4326)
        except Exception:
            self.showInvalid(4)

    def commitDdmmss(self):
        text = self.ddmmssLineEdit.text().strip()
        try:
            lat, lon = parseDMSString(text, self.inputXYOrder)
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(5, pt, epsg4326)
        except Exception:
            self.showInvalid(5)

    def commitUtm(self):
        text = self.utmLineEdit.text().strip()
        if isUtm(text):
            pt = utmString2Crs(text, epsg4326)
            self.updateCoordinates(6, QgsPoint(pt), epsg4326)
        else:
            self.showInvalid(6)

    def commitMgrs(self):
        text = self.mgrsLineEdit.text().strip()
        text = re.sub(r'\s+', '', text)  # Remove all white space
        try:
            lat, lon = mgrs.toWgs(text)
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(7, pt, epsg4326)
        except Exception:
            self.showInvalid(7)

    def commitPlus(self):
        text = self.plusLineEdit.text().strip()
        text = re.sub(r'\s+', '', text)  # Remove all white space
        try:
            coord = olc.decode(text)
            lat = coord.latitudeCenter
            lon = coord.longitudeCenter
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(8, pt, epsg4326)
        except Exception:
            self.showInvalid(8)

    def commitGeohash(self):
        text = self.geohashLineEdit.text().strip()
        try:
            (lat, lon) = geohash.decode(text)
            pt = QgsPoint(float(lon), float(lat))
            self.updateCoordinates(9, pt, epsg4326)
        except Exception:
            self.showInvalid(9)

    def commitMaidenhead(self):
        text = self.maidenheadLineEdit.text().strip()
        try:
            (lat, lon) = maidenhead.maidenGridCenter(text)
            pt = QgsPoint(float(lon), float(lat))
            self.updateCoordinates(10, pt, epsg4326)
        except Exception:
            self.showInvalid(10)

    def updateLabel(self):
        if self.inputXYOrder == 0:  # Y, X
            xy = '(Y, X)'
            latlon = '(latitude, longitude)'
        else:
            xy = '(X, Y)'
            latlon = '(longitude, latitude)'

        crs = self.canvas.mapSettings().destinationCrs()
        if crs == epsg4326:
            label = 'Project CRS - {} {}'.format('EPSG:4326', latlon)
        else:
            label = 'Project CRS - {} {}'.format(crs.authid(), xy)
        self.projectLabel.setText(label)

        label = 'Decimal Degrees {}'.format(latlon)
        self.wgs84Label.setText(label)

        crs = self.customProjectionSelectionWidget.crs()
        if crs == epsg4326:
            label = 'Custom CRS - {} {}'.format('EPSG:4326', latlon)
        else:
            label = 'Custom CRS - {} {}'.format(crs.authid(), xy)
        self.customLabel.setText(label)

        label = 'D° M\' S" {}'.format(latlon)
        self.dmsLabel.setText(label)

        label = 'D° M.MM\' {}'.format(latlon)
        self.dmLabel.setText(label)

        label = 'DDMMSS {}'.format(latlon)
        self.ddmmssLabel.setText(label)

    def copyWgs84(self):
        s = self.wgs84LineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)

    def copyProject(self):
        s = self.projLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)

    def copyCustom(self):
        s = self.customLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)

    def copyDms(self):
        s = self.dmsLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)
        self.clipboard.setText(self.dmsLineEdit.text())

    def copyDm(self):
        s = self.dmLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)
        self.clipboard.setText(self.dmLineEdit.text())

    def copyDdmmss(self):
        s = self.ddmmssLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)

    def copyUtm(self):
        s = self.utmLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)

    def copyMgrs(self):
        s = self.mgrsLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)

    def copyPlus(self):
        s = self.plusLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)

    def copyGeohash(self):
        s = self.geohashLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)

    def copyMaidenhead(self):
        s = self.maidenheadLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)

    def customCrsChanged(self):
        if self.origPt is not None:
            self.updateCoordinates(-1, self.origPt, self.origCrs)
        self.updateLabel()

    @pyqtSlot(QgsPointXY)
    def capturedPoint(self, pt):
        if self.isVisible() and self.coordCaptureButton.isChecked():
            self.updateCoordinates(-1, pt, epsg4326)

    def startCapture(self):
        if self.coordCaptureButton.isChecked():
            self.savedMapTool = self.canvas.mapTool()
            self.canvas.setMapTool(self.captureCoordinate)
        else:
            if self.savedMapTool:
                self.canvas.setMapTool(self.savedMapTool)
                self.savedMapTool = None
        
    @pyqtSlot()
    def stopCapture(self):
        self.coordCaptureButton.setChecked(False)

    def showSettings(self):
        self.settings.showTab(5)

    def zoomTo(self):
        text = self.wgs84LineEdit.text().strip()
        try:
            lat, lon = parseDMSString(text, self.inputXYOrder)
            pt = self.lltools.zoomTo(epsg4326, lat, lon)
        except Exception:
            pass
