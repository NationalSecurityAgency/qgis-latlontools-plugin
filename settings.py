import os
import re

from PyQt4 import QtGui, uic
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'latLonSettings.ui'))


class SettingsWidget(QtGui.QDialog, FORM_CLASS):
    def __init__(self, iface, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.loadSettings()
        
    def loadSettings(self):
        settings = QSettings()
        self.outputFormat = settings.value('/LatLonTools/OutputFormat', 'decimal')
        self.delimiter = settings.value('/LatLonTools/Delimiter', ', ')
        self.dmsPrecision =  int(settings.value('/LatLonTools/DMSPrecision', 0))
        
    def accept(self):
        settings = QSettings()
        if self.dd.isChecked():
            settings.setValue('/LatLonTools/OutputFormat', 'decimal')
        elif self.dms.isChecked():
            settings.setValue('/LatLonTools/OutputFormat', 'dms')
        elif self.ddmmss.isChecked():
            settings.setValue('/LatLonTools/OutputFormat', 'ddmmss')
        else:
            settings.setValue('/LatLonTools/OutputFormat', 'native')
            
        if self.commaDelim.isChecked():
            settings.setValue('/LatLonTools/Delimiter', ', ')
        elif self.spaceDelim.isChecked():
            settings.setValue('/LatLonTools/Delimiter', ' ')
        elif self.tabDelim.isChecked():
            settings.setValue('/LatLonTools/Delimiter', '\t')
        else:
            settings.setValue('/LatLonTools/Delimiter', self.otherTxt.text())
            
        settings.setValue('/LatLonTools/DMSPrecision', self.precisionSpinBox.value())
        self.loadSettings()
        self.close()
        
    def showEvent(self, e):
        self.loadSettings()
        if self.outputFormat == 'decimal':
            self.dd.setChecked(True)
        elif self.outputFormat == 'dms':
            self.dms.setChecked(True)
        elif self.outputFormat == 'ddmmss':
            self.ddmmss.setChecked(True)
        else:
            self.nativeFormat.setChecked(True)
        
        self.otherTxt.setText("")
        if self.delimiter == ', ':
            self.commaDelim.setChecked(True)
        elif self.delimiter == ' ':
            self.spaceDelim.setChecked(True)
        elif self.delimiter == '\t':
            self.tabDelim.setChecked(True)
        else:
            self.otherDelim.setChecked(True)
            self.otherTxt.setText(self.delimiter)
            
        self.precisionSpinBox.setValue(self.dmsPrecision)
