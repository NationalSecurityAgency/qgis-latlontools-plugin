import os
import re

from PyQt4 import QtGui, uic
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from LatLon import LatLon


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'zoomToLatLon.ui'))


class ZoomToLatLon(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, lltools, iface, parent):
        super(ZoomToLatLon, self).__init__(parent)
        self.setupUi(self)
        self.lltools = lltools
        self.settings = lltools.settingsDialog
        self.iface = iface
        self.coordTxt.returnPressed.connect(self.zoomToPressed)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
        
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def setLabel(self, order):
        self.coordTxt.setText("")
        if order == 0:
            self.label.setText("Enter 'Latitude, Longitude'")
        else:
            self.label.setText("Enter 'Longitude, Latitude'")

    def zoomToPressed(self):
        try:
            lat, lon = LatLon.parseDMSString(self.coordTxt.text(), self.settings.coordOrder)
        except:
            self.iface.messageBar().pushMessage("", "Invalid Coordinate" , level=QgsMessageBar.WARNING, duration=2)
            return
        self.lltools.zoomToLatLon(lat,lon)
