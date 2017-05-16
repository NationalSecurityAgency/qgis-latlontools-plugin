import os
import re

from PyQt4.uic import loadUiType
from PyQt4.QtGui import QDockWidget, QIcon
from qgis.gui import QgsMessageBar, QgsVertexMarker
from LatLon import LatLon

import mgrs
#import traceback

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/zoomToLatLon.ui'))


class ZoomToLatLon(QDockWidget, FORM_CLASS):

    def __init__(self, lltools, iface, parent):
        super(ZoomToLatLon, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()
        self.marker = None
        self.zoomToolButton.setIcon(QIcon(':/images/themes/default/mActionZoomIn.svg'))
        self.clearToolButton.setIcon(QIcon(':/images/themes/default/mIconClearText.svg'))
        self.zoomToolButton.clicked.connect(self.zoomToPressed)
        self.clearToolButton.clicked.connect(self.removeMarker)
        self.lltools = lltools
        self.settings = lltools.settingsDialog
        self.iface = iface
        self.coordTxt.returnPressed.connect(self.zoomToPressed)
        self.configure()

    def closeEvent(self, event):
        self.removeMarker()
        event.accept()
        
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def configure(self):
        self.coordTxt.setText("")
        
        if self.settings.zoomToProjIsMGRS():
            # This is an MGRS coordinate
            self.label.setText("Enter MGRS Coordinate")
        elif self.settings.zoomToProjIsWgs84():
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("Enter 'Latitude, Longitude'")
            else:
                self.label.setText("Enter 'Longitude, Latitude'")
        elif self.settings.zoomToProjIsProjectCRS():
            crsID = self.canvas.mapSettings().destinationCrs().authid()
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("Enter {} Y,X".format(crsID))
            else:
                self.label.setText("Enter {} X,Y".format(crsID))
        else: # Default to custom CRS
            crsID = self.settings.zoomToCustomCRSID()
            if self.settings.zoomToCoordOrder == 0:
                self.label.setText("Enter {} Y,X".format(crsID))
            else:
                self.label.setText("Enter {} X,Y".format(crsID))

    def zoomToPressed(self):
        try:
            text = self.coordTxt.text()
            if self.settings.zoomToProjIsWgs84():
                if re.search('POINT\(', text) == None:
                    lat, lon = LatLon.parseDMSString(text, self.settings.coordOrder)
                else:
                    m = re.findall('POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                    if len(m) != 1:
                        raise ValueError('Invalid Coordinates')
                    lon = float(m[0][0])
                    lat = float(m[0][1])
                srcCrs = self.settings.epsg4326
            elif self.settings.zoomToProjIsMGRS():
                # This is an MGRS coordinate
                text = re.sub(r'\s+', '', unicode(text)) # Remove all white space
                lat, lon = mgrs.toWgs(text)
                srcCrs = self.settings.epsg4326
            else: # Is either the project or custom CRS
                if re.search('POINT\(', text) == None:
                    coords = re.split('[\s,;:]+', text, 1)
                    if len(coords) < 2:
                        raise ValueError('Invalid Coordinates')
                    if self.settings.coordOrder == self.settings.OrderYX:
                        lat = float(coords[0])
                        lon = float(coords[1])
                    else:
                        lon = float(coords[0])
                        lat = float(coords[1])
                else:
                    m = re.findall('POINT\(\s*([+-]?\d*\.?\d*)\s+([+-]?\d*\.?\d*)', text)
                    if len(m) != 1:
                        raise ValueError('Invalid Coordinates')
                    lon = float(m[0][0])
                    lat = float(m[0][1])
                if self.settings.zoomToProjIsProjectCRS():
                    srcCrs = self.canvas.mapSettings().destinationCrs()
                else:
                    srcCrs = self.settings.zoomToCustomCRS()    
        except:
            #traceback.print_exc()
            self.iface.messageBar().pushMessage("", "Invalid Coordinate" , level=QgsMessageBar.WARNING, duration=2)
            return
        pt = self.lltools.zoomTo(srcCrs, lat, lon)
        if self.settings.persistentMarker:
            if self.marker is None:
                self.marker = QgsVertexMarker(self.canvas)
            self.marker.setCenter(pt)
            self.marker.setIconSize(18)
            self.marker.setPenWidth(2)
            self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
        elif self.marker is not None:
            self.removeMarker();


    def removeMarker(self):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None
            self.coordTxt.clear()
