import os
import re

from PyQt4 import QtGui, uic
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'latLonSettings.ui'))


class SettingsWidget(QtGui.QDialog, FORM_CLASS):
    '''Settings Dialog box.'''
    def __init__(self, iface, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.coordComboBox.addItems(['Decimal Degrees', 'DMS', 'DDMMSS', 'Native CRS'])
        self.delimComboBox.addItems(['Comma', 'Tab', 'Space', 'Other'])
        self.readSettings()
        
    def readSettings(self):
        '''Load the user selected settings. The settings are retained even when
        the user quits QGIS.'''
        settings = QSettings()
        self.outputFormat = settings.value('/LatLonTools/OutputFormat', 'decimal')
        self.delimiter = settings.value('/LatLonTools/Delimiter', ', ')
        self.dmsPrecision =  int(settings.value('/LatLonTools/DMSPrecision', 0))
        
    def accept(self):
        '''Accept the settings and save them for next time.'''
        settings = QSettings()
        coord = self.coordComboBox.currentIndex()
        if coord == 0:
            settings.setValue('/LatLonTools/OutputFormat', 'decimal')
        elif coord == 1:
            settings.setValue('/LatLonTools/OutputFormat', 'dms')
        elif coord ==2:
            settings.setValue('/LatLonTools/OutputFormat', 'ddmmss')
        else:
            settings.setValue('/LatLonTools/OutputFormat', 'native')
            
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
        self.readSettings()
        self.close()
        
    def showEvent(self, e):
        '''The user has selected the settings dialog box so we need to
        read the settings and update the dialog box with the previously
        selected settings.'''
        self.readSettings()
        if self.outputFormat == 'decimal':
            self.coordComboBox.setCurrentIndex(0)
        elif self.outputFormat == 'dms':
            self.coordComboBox.setCurrentIndex(1)
        elif self.outputFormat == 'ddmmss':
            self.coordComboBox.setCurrentIndex(2)
        else:
            self.coordComboBox.setCurrentIndex(3)
        
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
