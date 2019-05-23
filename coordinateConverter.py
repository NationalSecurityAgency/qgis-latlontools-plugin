import os
import re
from qgis.PyQt.QtCore import QSize, QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog, QMenu, QToolButton, QApplication
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.uic import loadUiType
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPoint, QgsPointXY, QgsProject
from qgis.gui import QgsProjectionSelectionDialog
from .util import epsg4326, parseDMSString, formatDmsString
import traceback

from .settings import settings
from . import mgrs
from . import olc
from .utm import latLon2UtmString, isUtm, utmString2Crs

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/coordinateConverter.ui'))

class CoordinateConverterWidget(QDialog, FORM_CLASS):
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
        
        self.clipboard = QApplication.clipboard()

        
        # Set up a connection with the coordinate capture tool
        self.lltools.mapTool.capturesig.connect(self.capturedPoint)

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
        self.optionsButton.setIcon(QIcon(':/images/themes/default/mActionOptions.svg'))
        self.optionsButton.clicked.connect(self.showSettings)
        self.closeButton.clicked.connect(self.closeEvent)

        icon = QIcon(os.path.dirname(__file__) + "/images/check.png")
        self.wgs84CommitButton.setIcon(icon)
        self.projCommitButton.setIcon(icon)
        self.customCommitButton.setIcon(icon)
        self.dmsCommitButton.setIcon(icon)
        self.ddmmssCommitButton.setIcon(icon)
        self.utmCommitButton.setIcon(icon)
        self.mgrsCommitButton.setIcon(icon)
        self.plusCommitButton.setIcon(icon)

        self.wgs84CommitButton.clicked.connect(self.commitWgs84)
        self.wgs84LineEdit.returnPressed.connect(self.commitWgs84)
        self.projCommitButton.clicked.connect(self.commitProject)
        self.projLineEdit.returnPressed.connect(self.commitProject)
        self.customCommitButton.clicked.connect(self.commitCustom)
        self.customLineEdit.returnPressed.connect(self.commitCustom)
        self.dmsCommitButton.clicked.connect(self.commitDms)
        self.dmsLineEdit.returnPressed.connect(self.commitDms)
        self.ddmmssCommitButton.clicked.connect(self.commitDdmmss)
        self.ddmmssLineEdit.returnPressed.connect(self.commitDdmmss)
        self.utmCommitButton.clicked.connect(self.commitUtm)
        self.utmLineEdit.returnPressed.connect(self.commitUtm)
        self.mgrsCommitButton.clicked.connect(self.commitMgrs)
        self.mgrsLineEdit.returnPressed.connect(self.commitMgrs)
        self.plusCommitButton.clicked.connect(self.commitPlus)
        self.plusLineEdit.returnPressed.connect(self.commitPlus)

        icon = QIcon(':/images/themes/default/mActionEditCopy.svg')
        self.wgs84CopyButton.setIcon(icon)
        self.projCopyButton.setIcon(icon)
        self.customCopyButton.setIcon(icon)
        self.dmsCopyButton.setIcon(icon)
        self.ddmmssCopyButton.setIcon(icon)
        self.utmCopyButton.setIcon(icon)
        self.mgrsCopyButton.setIcon(icon)
        self.plusCopyButton.setIcon(icon)

        self.wgs84CopyButton.clicked.connect(self.copyWgs84)
        self.projCopyButton.clicked.connect(self.copyProject)
        self.customCopyButton.clicked.connect(self.copyCustom)
        self.dmsCopyButton.clicked.connect(self.copyDms)
        self.ddmmssCopyButton.clicked.connect(self.copyDdmmss)
        self.utmCopyButton.clicked.connect(self.copyUtm)
        self.mgrsCopyButton.clicked.connect(self.copyMgrs)
        self.plusCopyButton.clicked.connect(self.copyPlus)
        
        self.customProjectionSelectionWidget.setCrs(epsg4326)
        self.customProjectionSelectionWidget.crsChanged.connect(self.customCrsChanged)

    def showEvent(self, e):
        self.inputXYOrder = settings.converterCoordOrder
        self.xyButton.setDefaultAction(self.xymenu.actions()[settings.converterCoordOrder])
        self.updateLabel()

    def closeEvent(self, e):
        self.stopCapture()
        self.hide()
    
    def xyTriggered(self, action):
        self.xyButton.setDefaultAction(action)
        self.inputXYOrder = action.data()
        if self.origPt != None:
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
            self.ddmmssLineEdit.setText('Invalid')
        if id != 5:
            self.utmLineEdit.setText('Invalid')
        if id != 6:
            self.mgrsLineEdit.setText('Invalid')
        if id != 7:
            self.plusLineEdit.setText('Invalid')
            
    def clearForm(self):
        self.origPt = None
        self.wgs84LineEdit.setText('')
        self.projLineEdit.setText('')
        self.customLineEdit.setText('')
        self.dmsLineEdit.setText('')
        self.ddmmssLineEdit.setText('')
        self.utmLineEdit.setText('')
        self.mgrsLineEdit.setText('')
        self.plusLineEdit.setText('')
    
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
        if id != 0: # WGS 84
            if self.inputXYOrder == 0: # Y, X
                s = '{:.{prec}f}{}{:.{prec}f}'.format(pt4326.y(), settings.converterDelimiter, pt4326.x(), prec=settings.converter4326DDPrec)
            else:
                s = '{:.{prec}f}{}{:.{prec}f}'.format(pt4326.x(), settings.converterDelimiter, pt4326.y(), prec=settings.converter4326DDPrec)
            self.wgs84LineEdit.setText(s)
        if id != 1: # Project CRS
            if crs == projCRS:
                newpt = pt
            else:
                trans = QgsCoordinateTransform(crs, projCRS, QgsProject.instance())
                newpt = trans.transform(pt.x(), pt.y())
            if projCRS == epsg4326:
                precision = settings.converter4326DDPrec
            else:
                precision = settings.converterDDPrec
            if self.inputXYOrder == 0: # Y, X
                s = '{:.{prec}f}{}{:.{prec}f}'.format(newpt.y(), settings.converterDelimiter, newpt.x(), prec=precision)
            else:
                s = '{:.{prec}f}{}{:.{prec}f}'.format(newpt.x(), settings.converterDelimiter, newpt.y(), prec=precision)
            self.projLineEdit.setText(s)
        if id != 2: # Custom CRS
            if crs == customCRS:
                newpt = pt
            else:
                trans = QgsCoordinateTransform(crs, customCRS, QgsProject.instance())
                newpt = trans.transform(pt.x(), pt.y())
            if customCRS == epsg4326:
                precision = settings.converter4326DDPrec
            else:
                precision = settings.converterDDPrec
            if self.inputXYOrder == 0: # Y, X
                s = '{:.{prec}f}{}{:.{prec}f}'.format(newpt.y(), settings.converterDelimiter, newpt.x(), prec=precision)
            else:
                s = '{:.{prec}f}{}{:.{prec}f}'.format(newpt.x(), settings.converterDelimiter, newpt.y(), prec=precision)
            self.customLineEdit.setText(s)
        if id != 3: # D M' S"
            s = formatDmsString(pt4326.y(), pt4326.x(), True, settings.converterDmsPrec, self.inputXYOrder, settings.converterDelimiter)
            self.dmsLineEdit.setText(s)
        if id != 4: # DDMMSS
            s = formatDmsString(pt4326.y(), pt4326.x(), False, settings.converterDmsPrec, self.inputXYOrder, settings.converterDelimiter)
            self.ddmmssLineEdit.setText(s)
        if id != 5: # UTM
            s = latLon2UtmString(pt4326.y(), pt4326.x(), settings.converterUtmPrec)
            self.utmLineEdit.setText(s)
        if id != 6: # MGRS
            try:
                s = mgrs.toMgrs(pt4326.y(), pt4326.x())
            except:
                s = 'Invalid'
            self.mgrsLineEdit.setText(s)
        if id != 7: # Plus Codes
            try:
                s = olc.encode(pt4326.y(), pt4326.x(), settings.converterPlusCodeLength)
            except:
                s = 'Invalid'
            self.plusLineEdit.setText(s)

    def commitWgs84(self):
        text = self.wgs84LineEdit.text().strip()
        try:
            lat, lon = parseDMSString(text, self.inputXYOrder)
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(0, pt, epsg4326)
        except:
            traceback.print_exc()
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
                if self.inputXYOrder == 0: # Lat, Lon
                    lat = float(coords[0])
                    lon = float(coords[1])
                else: # Lon, Lat
                    lon = float(coords[0])
                    lat = float(coords[1])
        except:
            traceback.print_exc()
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
                if self.inputXYOrder == 0: # Lat, Lon
                    lat = float(coords[0])
                    lon = float(coords[1])
                else: # Lon, Lat
                    lon = float(coords[0])
                    lat = float(coords[1])
        except:
            traceback.print_exc()
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
        except:
            traceback.print_exc()
            self.showInvalid(3)

    def commitDdmmss(self):
        text = self.ddmmssLineEdit.text().strip()
        try:
            lat, lon = parseDMSString(text, self.inputXYOrder)
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(4, pt, epsg4326)
        except:
            traceback.print_exc()
            self.showInvalid(4)

    def commitUtm(self):
        text = self.utmLineEdit.text().strip()
        if isUtm(text):
            pt = utmString2Crs(text, epsg4326)
            self.updateCoordinates(5, QgsPoint(pt), epsg4326)
        else:
            self.showInvalid(5)

    def commitMgrs(self):
        text = self.mgrsLineEdit.text().strip()
        text = re.sub(r'\s+', '', text) # Remove all white space
        try:
            lat, lon = mgrs.toWgs(text)
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(5, pt, epsg4326)
        except:
            self.showInvalid(6)

    def commitPlus(self):
        text = self.plusLineEdit.text().strip()
        text = re.sub(r'\s+', '', text) # Remove all white space
        try:
            coord = olc.decode(text)
            srcCrs = epsg4326
            lat = coord.latitudeCenter
            lon = coord.longitudeCenter
            pt = QgsPoint(lon, lat)
            self.updateCoordinates(7, pt, epsg4326)
        except:
            self.showInvalid(7)

    def updateLabel(self):
        if self.inputXYOrder == 0: # Y, X
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
        
        label = 'WGS 84 {}'.format(latlon)
        self.wgs84Label.setText(label)
        
        crs = self.customProjectionSelectionWidget.crs()
        if crs == epsg4326:
            label = 'Custom CRS - {} {}'.format('EPSG:4326', latlon)
        else:
            label = 'Custom CRS - {} {}'.format(crs.authid(), xy)
        self.customLabel.setText(label)
        
        label = 'D° M\' S" {}'.format(latlon)
        self.dmsLabel.setText(label)
        
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
        s = self.projLineEdit.text()
        self.clipboard.setText(s)
        self.iface.statusBarIface().showMessage("'{}' copied to the clipboard".format(s), 3000)
        self.clipboard.setText(self.dmsLineEdit.text())
        
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

    def customCrsChanged(self):
        if self.origPt != None:
            self.updateCoordinates(-1, self.origPt, self.origCrs)
        self.updateLabel()
        
    @pyqtSlot(QgsPointXY)
    def capturedPoint(self, pt):
        if self.isVisible() and self.coordCaptureButton.isChecked():
            self.updateCoordinates(-1, pt, epsg4326)
        
    def startCapture(self):
        if self.coordCaptureButton.isChecked():
            self.lltools.mapTool.capture4326 = True
            self.lltools.startCapture()
        else:
            self.lltools.mapTool.capture4326 = False
        
    def stopCapture(self):
        self.lltools.mapTool.capture4326 = False
        self.coordCaptureButton.setChecked(False)

    def showSettings(self):
        self.settings.showTab(5)
