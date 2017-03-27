import os
import re

from PyQt4 import QtGui, uic
from PyQt4.QtGui import QFileDialog, QHeaderView
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from LatLon import LatLon

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/multiZoomDialog.ui'))


class MultiZoomWidget(QtGui.QDialog, FORM_CLASS):
    '''Multizoom Dialog box.'''
    def __init__(self, lltools, settings, parent):
        super(MultiZoomWidget, self).__init__(parent)
        self.setupUi(self)
        self.settings = settings
        self.iface = lltools.iface
        self.lltools = lltools
        
        self.doneButton.clicked.connect(self.closeDialog)
        self.browseButton.clicked.connect(self.browseDialog)
        self.addButton.clicked.connect(self.addSingleCoord)
        self.removeButton.clicked.connect(self.removeTableRow)
        self.coordTxt.returnPressed.connect(self.addSingleCoord)
        self.clearAllButton.clicked.connect(self.clearAll)
        self.dirname = ''
        self.numcoord = 0;
        self.maxResults = 100
        self.resultsTable.setColumnCount(2)
        self.resultsTable.setSortingEnabled(False)
        self.resultsTable.setHorizontalHeaderLabels(['Latitude','Longitude'])
        self.resultsTable.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.resultsTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.resultsTable.cellClicked.connect(self.itemClicked)
        self.lats=[]
        self.lons=[]
        
    def closeDialog(self):
        self.hide()
        
    def clearAll(self):
        self.lats=[]
        self.lons=[]
        self.resultsTable.setRowCount(0)
        self.numcoord = 0
        
    def browseDialog(self):
        filename = QFileDialog.getOpenFileName(None, "Input Lat,Lon File", 
                self.dirname, "Lat,Lon File (*.csv *.txt)")
        if filename:
            self.dirname = os.path.dirname(filename)
            self.readFile(filename)
            
    def readFile(self, fname):
        '''Read a file of coordinates and add them to the list.'''
        try:
            with open(fname) as f:
                for line in f:
                    try:
                        lat, lon = LatLon.parseDMSString(line)
                        self.addCoord(lat, lon)
                    except:
                        pass
        except:
            pass
    
    def removeTableRow(self):
        '''Remove an entry from the coordinate table.'''
        row = int(self.resultsTable.currentRow())
        if row < 0:
            return
        self.resultsTable.removeRow(row)
        del self.lats[row]
        del self.lons[row]
        self.resultsTable.clearSelection()
        self.numcoord -= 1
        
    
    def addSingleCoord(self):
        '''Add a coordinate that was pasted into the coordinate text box.'''
        try:
            lat, lon = LatLon.parseDMSString(self.coordTxt.text())
        except:
            if self.coordTxt.text():
                self.iface.messageBar().pushMessage("", "Invalid Coordinate" , level=QgsMessageBar.WARNING, duration=2)
            return
        self.addCoord(lat, lon)
        self.coordTxt.clear()
        
    def addCoord(self, lat, lon):
        '''Add a coordinate to the list.'''
        if self.numcoord >= self.maxResults:
            return
        self.resultsTable.insertRow(self.numcoord)
        self.resultsTable.setItem(self.numcoord, 0, QtGui.QTableWidgetItem(str(lat)))
        self.resultsTable.setItem(self.numcoord, 1, QtGui.QTableWidgetItem(str(lon)))
        self.lats.append(lat)
        self.lons.append(lon)
        self.numcoord += 1
        
    def itemClicked(self, row, col):
        '''An item has been click on so zoom to it'''
        selectedRow = self.resultsTable.currentRow()
        # Call the the parent's zoom to function
        self.lltools.zoomTo(self.settings.epsg4326, self.lats[selectedRow],self.lons[selectedRow])