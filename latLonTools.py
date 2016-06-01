from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Initialize Qt resources from file resources.py
import resources

from zoomToLatLon import ZoomToLatLon
from settings import SettingsWidget
from LatLon import LatLon
import os.path


class LatLonTools:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.settingsDialog = SettingsWidget(self.iface, self.iface.mainWindow())
        self.mapTool = CopyLatLonTool(self.settingsDialog, self.iface)

        icon = QIcon(":/plugins/latlontools/copyicon.png")
        self.copyAction = QAction(icon, "Copy Latitude, Longitude",
            self.iface.mainWindow())
        self.copyAction.triggered.connect(self.setTool)
        self.copyAction.setCheckable(True)
        self.iface.addToolBarIcon(self.copyAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.copyAction)

        zoomicon = QIcon(':/plugins/latlontools/zoomicon.png')
        self.zoomToAction = QAction(zoomicon, "Zoom To Latitude, Longitude", 
                    self.iface.mainWindow())
        self.zoomToAction.triggered.connect(self.zoomTo)
        self.iface.addPluginToMenu('Lat Lon Tools', self.zoomToAction)
        
        
        self.iface.mapCanvas().mapToolSet.connect(self.unsetTool)

        
        self.dockwidget = ZoomToLatLon(self.iface,
                    self.iface.mainWindow())
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
        self.dockwidget.hide()
        
        # Initialize the Settings Dialog Box
        settingsicon = QIcon(':/plugins/latlontools/settings.png')
        self.settingsAction = QAction(settingsicon, "Settings", 
                    self.iface.mainWindow())
        self.settingsAction.triggered.connect(self.settings)
        self.iface.addPluginToMenu('Lat Lon Tools', self.settingsAction)
        
    def unsetTool(self, tool):
        try:
            if not isinstance(tool, CopyLatLonTool):
                self.copyAction.setChecked(False)
        except:
            pass
 

    def unload(self):
        self.iface.mapCanvas().unsetMapTool(self.mapTool)
        self.iface.removePluginMenu('Lat Lon Tools', self.copyAction)
        self.iface.removeToolBarIcon(self.copyAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.zoomToAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.settingsAction)
        self.iface.removeDockWidget(self.dockwidget)
        self.dockwidget = None

    def setTool(self):
        self.copyAction.setChecked(True)
        self.iface.mapCanvas().setMapTool(self.mapTool)

    def zoomTo(self):
        self.dockwidget.show()
    
    def settings(self):
        self.settingsDialog.show()
        

 
class CopyLatLonTool(QgsMapTool):
    def __init__(self, settings, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.settings = settings
        self.latlon = LatLon()
        
    def activate(self):
        self.canvas.setCursor(Qt.CrossCursor)
        
    def formatCoord(self, pt, delimiter, outputFormat):
        if outputFormat == 'native':
            msg = str(pt.y()) + delimiter + str(pt.x())
        else:
            canvasCRS = self.canvas.mapRenderer().destinationCrs()
            epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(canvasCRS, epsg4326)
            pt4326 = transform.transform(pt.x(), pt.y())
            self.latlon.setCoord(pt4326.y(), pt4326.x())
            self.latlon.setPrecision(self.settings.dmsPrecision)
            if self.latlon.isValid():
                if outputFormat == 'dms':
                    msg = self.latlon.getDMS(delimiter)
                elif outputFormat == 'ddmmss':
                    msg = self.latlon.getDDMMSS(delimiter)
                else:
                    msg = str(self.latlon.lat)+ delimiter +str(self.latlon.lon)
            else:
                msg = None
        return msg
        
    def canvasMoveEvent(self, event):
        outputFormat = self.settings.outputFormat
        pt = self.toMapCoordinates(event.pos())
        msg = self.formatCoord(pt, ', ', outputFormat)
        if outputFormat == 'native' or msg == None:
            self.iface.mainWindow().statusBar().showMessage("")
        elif outputFormat == 'dms' or outputFormat == 'ddmmss':
            self.iface.mainWindow().statusBar().showMessage("DMS: " + msg)
        else:
            self.iface.mainWindow().statusBar().showMessage("Lat Lon: " + msg)


    def canvasReleaseEvent(self, event):
        pt = self.toMapCoordinates(event.pos())
        msg = self.formatCoord(pt, self.settings.delimiter,
            self.settings.outputFormat)
        if msg != None:
            clipboard = QApplication.clipboard()
            clipboard.setText(msg)
            self.iface.messageBar().pushMessage("", "Coordinate %s copied to the clipboard" % msg, level=QgsMessageBar.INFO, duration=3)
