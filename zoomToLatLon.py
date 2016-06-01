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

    def __init__(self, iface, parent):
        super(ZoomToLatLon, self).__init__(parent)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.setupUi(self)
        self.coordTxt.returnPressed.connect(self.zoomToPressed)
        
        self.crossRb = QgsRubberBand(self.canvas, QGis.Line)
        self.crossRb.setColor(Qt.red)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
        
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False    

    def zoomToPressed(self):
        try:
            lat, lon = LatLon.parseDMSString(self.coordTxt.text())
        except:
            self.iface.messageBar().pushMessage("", "Invalid Coordinate" , level=QgsMessageBar.WARNING, duration=2)
            return
        #print "Lat ", lat, " Lon ", lon
        canvasCrs = self.canvas.mapRenderer().destinationCrs()
        epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        transform4326 = QgsCoordinateTransform(epsg4326, canvasCrs)
        x, y = transform4326.transform(float(lon), float(lat))
            
        rect = QgsRectangle(x,y,x,y)
        self.canvas.setExtent(rect)

        pt = QgsPoint(x,y)
        self.highlight(pt)
        self.canvas.refresh()
        
    def highlight(self, point):
        currExt = self.canvas.extent()
        
        leftPt = QgsPoint(currExt.xMinimum(),point.y())
        rightPt = QgsPoint(currExt.xMaximum(),point.y())
        
        topPt = QgsPoint(point.x(),currExt.yMaximum())
        bottomPt = QgsPoint(point.x(),currExt.yMinimum())
        
        horizLine = QgsGeometry.fromPolyline( [ leftPt , rightPt ] )
        vertLine = QgsGeometry.fromPolyline( [ topPt , bottomPt ] )
        
        self.crossRb.reset(QGis.Line)
        self.crossRb.addGeometry(horizLine, None)
        self.crossRb.addGeometry(vertLine, None)
        
        QTimer.singleShot(700, self.resetRubberbands)
        
    def resetRubberbands(self):
        self.crossRb.reset()


