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

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget, QHeaderView, QAbstractItemView, QFileDialog, QTableWidgetItem, QMessageBox
from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtCore import Qt, QVariant, pyqtSlot
from qgis.core import (
    QgsCoordinateTransform, QgsVectorLayer,
    QgsField, QgsFeature, QgsGeometry, QgsPointXY,
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsProject, Qgis)
from qgis.gui import QgsVertexMarker
from .captureCoordinate  import CaptureCoordinate
from .util import epsg4326, parseDMSStringSingle, parseDMSString, tr
from .utm import utm2Point
from .settings import CoordOrder, settings
from . import mgrs
from . import olc

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/multiZoomDialog.ui'))

LABELS = [
    'Latitude', 'Longitude', 'Label', 'Data1', 'Data2', 'Data3',
    'Data4', 'Data5', 'Data6', 'Data7', 'Data8', 'Data9', 'Data10']

MAXDATA = 10


class MultiZoomWidget(QDockWidget, FORM_CLASS):
    '''Multizoom Dialog box.'''
    def __init__(self, lltools, settings, parent):
        super(MultiZoomWidget, self).__init__(parent)
        self.setupUi(self)
        self.settings = settings
        self.iface = lltools.iface
        self.canvas = self.iface.mapCanvas()
        self.lltools = lltools
        self.savedMapTool = None

        # Set up a connection with the coordinate capture tool
        self.captureCoordinate = CaptureCoordinate(self.canvas)
        self.captureCoordinate.capturePoint.connect(self.capturedPoint)
        self.captureCoordinate.captureStopped.connect(self.stopCapture)

        self.addButton.setIcon(QIcon(':/images/themes/default/algorithms/mAlgorithmCheckGeometry.svg'))
        self.coordCaptureButton.setIcon(QIcon(os.path.dirname(__file__) + "/images/coordCapture.svg"))
        self.coordCaptureButton.clicked.connect(self.startCapture)
        self.openButton.setIcon(QIcon(':/images/themes/default/mActionFileOpen.svg'))
        self.saveButton.setIcon(QIcon(':/images/themes/default/mActionFileSave.svg'))
        self.removeButton.setIcon(QIcon(':/images/themes/default/mActionDeleteSelected.svg'))
        self.clearAllButton.setIcon(QIcon(':/images/themes/default/mActionDeselectAll.svg'))
        self.createLayerButton.setIcon(QIcon(':/images/themes/default/mActionNewVectorLayer.svg'))
        self.optionsButton.setIcon(QIcon(':/images/themes/default/mActionOptions.svg'))

        self.openButton.clicked.connect(self.openDialog)
        self.saveButton.clicked.connect(self.saveDialog)
        self.addButton.clicked.connect(self.addSingleCoord)
        self.removeButton.clicked.connect(self.removeTableRows)
        self.addLineEdit.returnPressed.connect(self.addSingleCoord)
        self.clearAllButton.clicked.connect(self.clearAll)
        self.createLayerButton.clicked.connect(self.createLayer)
        self.optionsButton.clicked.connect(self.showSettings)
        self.showAllCheckBox.stateChanged.connect(self.updateDisplayedMarkers)
        self.dirname = ''
        self.maxResults = 5000
        self.numCol = 3 + self.settings.multiZoomNumCol
        self.resultsTable.setColumnCount(self.numCol)
        self.resultsTable.setSortingEnabled(False)
        self.resultsTable.setHorizontalHeaderLabels(LABELS[0:self.numCol])
        self.resultsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.resultsTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.resultsTable.cellClicked.connect(self.itemClicked)
        self.resultsTable.cellChanged.connect(self.cellChanged)
        self.resultsTable.itemSelectionChanged.connect(self.selectionChanged)
        self.resultsTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.resultsTable.horizontalHeader().geometriesChanged.connect(self.geomChanged)
        self.canvas.destinationCrsChanged.connect(self.crsChanged)
        self.initLabel()

    def crsChanged(self):
        if self.isVisible():
            self.initLabel()

    def initLabel(self):
        if self.settings.multiZoomToProjIsWgs84():
            if self.settings.multiCoordOrder == CoordOrder.OrderYX:
                self.label.setText(tr("Enter coordinate ('lat,lon,...)"))
            else:
                self.label.setText(tr("Enter coordinate ('lon,lat,...)"))
        elif self.settings.multiZoomToProjIsMGRS():
            self.label.setText(tr("Enter coordinate ('mgrs,...)"))
        elif self.settings.multiZoomToProjIsPlusCodes():
            self.label.setText(tr("Enter coordinate ('Plus code,...)"))
        elif self.settings.multiZoomToProjIsUtm():
            self.label.setText(tr("Enter coordinate ('Standard UTM,...)"))
        else:
            if self.settings.multiCoordOrder == CoordOrder.OrderYX:
                self.label.setText("{} ({} Y,X,...)".format(tr('Enter coordinate'), self.settings.multiZoomToCRS().authid()))
            else:
                self.label.setText("{} ({} X,Y,...)".format(tr('Enter coordinate'), self.settings.multiZoomToCRS().authid()))

    def settingsChanged(self):
        self.initLabel()
        if self.numCol != self.settings.multiZoomNumCol + 3:
            # The number of columns have changed
            self.numCol = 3 + self.settings.multiZoomNumCol
            self.resultsTable.blockSignals(True)
            self.resultsTable.setColumnCount(self.numCol)
            self.resultsTable.setHorizontalHeaderLabels(LABELS[0:self.numCol])
            rowcnt = self.resultsTable.rowCount()
            for i in range(rowcnt):
                item = self.resultsTable.item(i, 0).data(Qt.UserRole)
                if self.numCol > 3:
                    for j in range(3, self.numCol):
                        self.resultsTable.setItem(i, j, QTableWidgetItem(item.data[j - 3]))

            self.resultsTable.clearSelection()
            self.resultsTable.blockSignals(False)
            self.geomChanged()
            self.updateDisplayedMarkers()

    def closeEvent(self, e):
        '''Called when the dialog box is being closed. We want to clear selected features and remove
           all the markers.'''
        if self.savedMapTool:
            self.canvas.setMapTool(self.savedMapTool)
            self.savedMapTool = None
        self.resultsTable.clearSelection()
        self.removeMarkers()
        self.hide()

    def showEvent(self, e):
        '''The dialog box is going to be displayed so we need to check to
           see if markers need to be displayed.'''
        self.updateDisplayedMarkers()
        self.resultsTable.horizontalHeader().resizeSections(QHeaderView.Stretch)
        self.initLabel()
        self.setEnabled(True)

    def geomChanged(self):
        '''This will force the columns to be stretched to the full width
           when the dialog geometry changes, but will then set it so that the user
           can adjust them.'''
        self.resultsTable.horizontalHeader().resizeSections(QHeaderView.Stretch)

    @pyqtSlot(QgsPointXY)
    def capturedPoint(self, pt):
        if self.isVisible() and self.coordCaptureButton.isChecked():
            newrow = self.addCoord(pt.y(), pt.x())
            self.resultsTable.selectRow(newrow)

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

    def clearAll(self):
        reply = QMessageBox.question(
            self, 'Message',
            tr('Are your sure you want to delete all locations?'),
            QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.resultsTable.blockSignals(True)
            self.removeMarkers()
            self.resultsTable.setRowCount(0)
            self.resultsTable.blockSignals(False)

    def showSettings(self):
        self.settings.showTab(3)

    def updateDisplayedMarkers(self):
        rowcnt = self.resultsTable.rowCount()

        if self.showAllCheckBox.checkState():
            for id in range(rowcnt):
                item = self.resultsTable.item(id, 0).data(Qt.UserRole)
                if item.marker is None:
                    item.marker = QgsVertexMarker(self.canvas)
                    item.marker.setColor(settings.markerColor)
                    pt = self.canvasPointXY(item.lat, item.lon)
                    item.marker.setCenter(pt)
                    item.marker.setIconSize(settings.markerSize)
                    item.marker.setPenWidth(settings.markerWidth)
                    item.marker.setIconType(QgsVertexMarker.ICON_CROSS)
        else:  # Only selected rows will be displayed
            indices = [x.row() for x in self.resultsTable.selectionModel().selectedRows()]
            for id in range(rowcnt):
                item = self.resultsTable.item(id, 0).data(Qt.UserRole)
                if id in indices:
                    if item.marker is None:
                        item.marker = QgsVertexMarker(self.canvas)
                        item.marker.setColor(settings.markerColor)
                        pt = self.canvasPointXY(item.lat, item.lon)
                        item.marker.setCenter(pt)
                        item.marker.setIconSize(settings.markerSize)
                        item.marker.setPenWidth(settings.markerWidth)
                        item.marker.setIconType(QgsVertexMarker.ICON_CROSS)
                elif item.marker is not None:
                    self.canvas.scene().removeItem(item.marker)
                    item.marker = None

    def removeMarkers(self):
        rowcnt = self.resultsTable.rowCount()
        if rowcnt == 0:
            return
        for id in range(rowcnt):
            item = self.resultsTable.item(id, 0).data(Qt.UserRole)
            if item.marker is not None:
                self.canvas.scene().removeItem(item.marker)
                item.marker = None

    def openDialog(self):
        filename = QFileDialog.getOpenFileName(
            None, "Input File", self.dirname,
            "Text, CSV (*.txt *.csv);;All files (*.*)")[0]
        if filename:
            self.dirname = os.path.dirname(filename)
            self.readFile(filename)

    def saveDialog(self):
        filename = QFileDialog.getSaveFileName(None, "Save File", self.dirname, "Text CSV (*.csv)")[0]
        if filename:
            self.dirname = os.path.dirname(filename)
            self.saveFile(filename)

    def readFile(self, fname):
        '''Read a file of coordinates and add them to the list.'''
        try:
            with open(fname) as f:
                for line in f:
                    try:
                        parts = [x.strip() for x in line.split(',')]
                        if len(parts) >= 2:
                            lat = parseDMSStringSingle(parts[0])
                            lon = parseDMSStringSingle(parts[1])
                            label = ''
                            data = []
                            if len(parts) >= 3:
                                label = parts[2]
                            if len(parts) >= 4:
                                data = parts[3:]
                            self.addCoord(lat, lon, label, data)
                    except Exception:
                        pass
        except Exception:
            pass
        self.updateDisplayedMarkers()

    def saveFile(self, fname):
        '''Save the zoom locations'''
        rowcnt = self.resultsTable.rowCount()
        if rowcnt == 0:
            return
        with open(fname, 'w') as f:
            for id in range(rowcnt):
                item = self.resultsTable.item(id, 0).data(Qt.UserRole)
                s = "{},{},{}".format(item.lat, item.lon, item.label)
                f.write(s)
                if self.numCol >= 4:
                    for i in range(self.numCol - 3):
                        s = ",{}".format(item.data[i])
                        f.write(s)
                f.write('\n')
        f.close()

    def removeTableRows(self):
        '''Remove selected entries from the coordinate table.'''
        indices = [x.row() for x in self.resultsTable.selectionModel().selectedRows()]
        if len(indices) == 0:
            return
        # We need to remove the rows from the bottom to the top so that the indices
        # don't change.
        reply = QMessageBox.question(
            self, 'Message',
            tr('Are your sure you want to delete the selected locations?'),
            QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Blocking the signals is necessary to prevent the signals replacing
            # the marker before it is completely removed.
            self.resultsTable.blockSignals(True)
            for row in sorted(indices, reverse=True):
                # Remove the marker from the map
                item = self.resultsTable.item(row, 0).data(Qt.UserRole)
                if item.marker is not None:
                    self.canvas.scene().removeItem(item.marker)
                    item.marker = None
                # Then remove the location from the table
                self.resultsTable.removeRow(row)

            self.resultsTable.blockSignals(False)
            self.resultsTable.clearSelection()

    def addSingleCoord(self):
        '''Add a coordinate from the coordinate text box.'''
        parts = [x.strip() for x in self.addLineEdit.text().split(',')]
        label = ''
        data = []
        numFields = len(parts)
        try:
            if self.settings.multiZoomToProjIsMGRS():
                '''Check to see if we have an MGRS coordinate for entry'''
                lat, lon = mgrs.toWgs(re.sub(r'\s+', '', parts[0]))
                if numFields >= 2:
                    label = parts[1]
                if numFields >= 3:
                    data = parts[2:]
            elif self.settings.multiZoomToProjIsPlusCodes():
                coord = olc.decode(parts[0])
                lat = coord.latitudeCenter
                lon = coord.longitudeCenter
                if numFields >= 2:
                    label = parts[1]
                if numFields >= 3:
                    data = parts[2:]
            elif self.settings.multiZoomToProjIsUtm():
                pt = utm2Point(parts[0])
                lat = pt.y()
                lon = pt.x()
                if numFields >= 2:
                    label = parts[1]
                if numFields >= 3:
                    data = parts[2:]
            elif numFields == 1:
                '''Perhaps the user forgot to add the comma separator. Check to see
                   if there are two coordinates anyway.'''
                if self.settings.multiZoomToProjIsWgs84():
                    lat, lon = parseDMSString(parts[0], self.settings.multiCoordOrder)
                else:
                    parts = re.split(r'[\s;:]+', parts[0], 1)
                    if len(parts) < 2:
                        self.iface.messageBar().pushMessage("", tr("Invalid Coordinate."), level=Qgis.Warning, duration=3)
                        return
                    srcCrs = self.settings.multiZoomToCRS()
                    transform = QgsCoordinateTransform(srcCrs, epsg4326, QgsProject.instance())
                    if self.settings.multiCoordOrder == CoordOrder.OrderYX:
                        lon, lat = transform.transform(float(parts[1]), float(parts[0]))
                    else:
                        lon, lat = transform.transform(float(parts[0]), float(parts[1]))
            elif numFields >= 2:
                if self.settings.multiZoomToProjIsWgs84():
                    '''Combine the coordinates back together and use parseDMSString
                       as it is more robust than parseDMSStringSingle.'''
                    str = "{}, {}".format(parts[0], parts[1])
                    lat, lon = parseDMSString(str, self.settings.multiCoordOrder)
                else:
                    srcCrs = self.settings.multiZoomToCRS()
                    transform = QgsCoordinateTransform(srcCrs, epsg4326, QgsProject.instance())
                    if self.settings.multiCoordOrder == CoordOrder.OrderYX:
                        lon, lat = transform.transform(float(parts[1]), float(parts[0]))
                    else:
                        lon, lat = transform.transform(float(parts[0]), float(parts[1]))
                if numFields >= 3:
                    label = parts[2]
                if numFields >= 4:
                    data = parts[3:]
            else:
                self.iface.messageBar().pushMessage("", tr("Invalid Coordinate."), level=Qgis.Warning, duration=3)
                return
        except Exception:
            if self.addLineEdit.text():
                self.iface.messageBar().pushMessage("", tr("Invalid Coordinate. Perhaps comma separators between fields were not used."), level=Qgis.Warning, duration=3)
            return
        newrow = self.addCoord(lat, lon, label, data)
        self.addLineEdit.clear()
        self.resultsTable.selectRow(newrow)
        self.itemClicked(newrow, 0)

    def addCoord(self, lat, lon, label='', data=[]):
        '''Add a coordinate to the list.'''
        rowcnt = self.resultsTable.rowCount()
        if rowcnt >= self.maxResults:
            return
        self.resultsTable.blockSignals(True)
        self.resultsTable.insertRow(rowcnt)
        item = QTableWidgetItem(str(lat))
        item.setData(Qt.UserRole, LatLonItem(lat, lon, label, data))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.resultsTable.setItem(rowcnt, 0, item)
        item = QTableWidgetItem(str(lon))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.resultsTable.setItem(rowcnt, 1, item)
        self.resultsTable.setItem(rowcnt, 2, QTableWidgetItem(label))
        if self.numCol > 3 and len(data) > 0:
            for i in range(min(self.numCol - 3, len(data))):
                self.resultsTable.setItem(rowcnt, i + 3, QTableWidgetItem(data[i]))

        self.resultsTable.blockSignals(False)
        return(rowcnt)

    def selectionChanged(self):
        '''There had been a change in what rows are selected in
        the coordinate table. We need to update the displayed markers.'''
        self.updateDisplayedMarkers()

    def itemClicked(self, row, col):
        '''An item has been click on so zoom to it. The selectionChanged event will update
        the displayed markers.'''
        selectedRow = self.resultsTable.currentRow()
        item = self.resultsTable.item(selectedRow, 0).data(Qt.UserRole)
        # Call the the parent's zoom to function
        self.lltools.zoomTo(epsg4326, item.lat, item.lon)

    def canvasPointXY(self, lat, lon):
        canvasCrs = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(epsg4326, canvasCrs, QgsProject.instance())
        x, y = transform.transform(float(lon), float(lat))
        pt = QgsPointXY(x, y)
        return pt

    def cellChanged(self, row, col):
        '''The label or one of the data cell strings have changed.
        We need to update the LatLonItem data.'''
        item = self.resultsTable.item(row, 0).data(Qt.UserRole)
        if col == 2:
            item.label = self.resultsTable.item(row, col).text()
        elif col >= 3:
            item.data[col - 3] = self.resultsTable.item(row, col).text()

    def createLayer(self):
        '''Create a memory layer from the zoom to locations'''
        rowcnt = self.resultsTable.rowCount()
        if rowcnt == 0:
            return
        attr = []
        for item, label in enumerate(LABELS[0:self.numCol]):
            label = label.lower()
            if item <= 1:
                attr.append(QgsField(label, QVariant.Double))
            else:
                attr.append(QgsField(label, QVariant.String))
        ptLayer = QgsVectorLayer("Point?crs=epsg:4326", u"Lat Lon Locations", "memory")
        provider = ptLayer.dataProvider()
        provider.addAttributes(attr)
        ptLayer.updateFields()

        for id in range(rowcnt):
            item = self.resultsTable.item(id, 0).data(Qt.UserRole)
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(item.lon, item.lat)))
            attr = [item.lat, item.lon, item.label]
            for i in range(3, self.numCol):
                attr.append(item.data[i - 3])
            feature.setAttributes(attr)
            provider.addFeatures([feature])

        ptLayer.updateExtents()
        if self.settings.multiZoomStyleID == 1:
            settings = QgsPalLayerSettings()
            settings.fieldName = 'label'
            settings.placement = QgsPalLayerSettings.AroundPoint
            labeling = QgsVectorLayerSimpleLabeling(settings)
            ptLayer.setLabeling(labeling)
            ptLayer.setLabelsEnabled(True)
        elif self.settings.multiZoomStyleID == 2 and os.path.isfile(self.settings.customQMLFile()):
            ptLayer.loadNamedStyle(self.settings.customQMLFile())

        QgsProject.instance().addMapLayer(ptLayer)


class LatLonItem():
    def __init__(self, lat, lon, label='', data=[]):
        self.lat = lat
        self.lon = lon
        self.label = label
        self.data = [''] * MAXDATA
        for i, d in enumerate(data):
            if i < MAXDATA:
                self.data[i] = d
        self.marker = None
