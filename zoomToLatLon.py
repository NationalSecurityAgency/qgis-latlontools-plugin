import os
import re

from PyQt4 import uic
from PyQt4.QtGui import QDockWidget, QIcon
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from LatLon import LatLon

import mgrs

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/zoomToLatLon.ui'))


class ZoomToLatLon(QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, lltools, iface, parent):
        super(ZoomToLatLon, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()
        self.marker = None
        self.zoomToolButton.setIcon(QIcon(':/images/themes/default/mActionZoomIn.svg'))
        self.clearToolButton.setIcon(QIcon(':/images/themes/default/mIconClear.svg'))
        self.zoomToolButton.clicked.connect(self.zoomToPressed)
        self.clearToolButton.clicked.connect(self.removeMarker)
        self.lltools = lltools
        self.settings = lltools.settingsDialog
        self.iface = iface
        self.coordTxt.returnPressed.connect(self.zoomToPressed)
        self.configure()

    def closeEvent(self, event):
        self.removeMarker()
        self.closingPlugin.emit()
        event.accept()
        
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def configure(self):
        self.coordTxt.setText("")
        
        if self.settings.zoomToCoordType == 1:
            # This is an MGRS coordinate
            self.label.setText("Enter MGRS Coordinate")
        else:
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("Enter 'Latitude, Longitude'")
            else:
                self.label.setText("Enter 'Longitude, Latitude'")

    def zoomToPressed(self):
        try:
            if self.settings.zoomToCoordType == 1:
                # This is an MGRS coordinate
                lat, lon = mgrs.toWgs(unicode(self.coordTxt.text()))
            else:
                lat, lon = LatLon.parseDMSString(self.coordTxt.text(), self.settings.coordOrder)
        except:
            self.iface.messageBar().pushMessage("", "Invalid Coordinate" , level=QgsMessageBar.WARNING, duration=2)
            return
        pt = self.lltools.zoomToLatLon(lat,lon)
        if self.marker is None:
            self.marker = QgsVertexMarker(self.canvas)
        self.marker.setCenter(pt)
        self.marker.setIconSize(18)
        self.marker.setPenWidth(2)
        self.marker.setIconType(QgsVertexMarker.ICON_CROSS)


    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None
