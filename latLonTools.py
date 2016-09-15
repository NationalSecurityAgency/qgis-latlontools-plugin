from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Initialize Qt resources from file resources.py
# import resources

from zoomToLatLon import ZoomToLatLon
from multizoom import MultiZoomWidget
from copyLatLonTool import CopyLatLonTool
from settings import SettingsWidget
import os.path
import webbrowser


class LatLonTools:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.crossRb = QgsRubberBand(self.canvas, QGis.Line)
        self.crossRb.setColor(Qt.red)

    def initGui(self):
        '''Initialize Lot Lon Tools GUI.'''
        # Initialize the Settings Dialog box
        self.settingsDialog = SettingsWidget(self, self.iface, self.iface.mainWindow())
        self.multiZoomDialog = MultiZoomWidget(self, self.settingsDialog, self.iface.mainWindow())
        self.mapTool = CopyLatLonTool(self.settingsDialog, self.iface)
        
        # Add Interface for Coordinate Capturing
        icon = QIcon(os.path.dirname(__file__) + "/images/copyicon.png")
        self.copyAction = QAction(icon, "Copy Latitude, Longitude", self.iface.mainWindow())
        self.copyAction.triggered.connect(self.setTool)
        self.copyAction.setCheckable(True)
        self.iface.addToolBarIcon(self.copyAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.copyAction)

        # Add Interface for Zoom to Coordinate
        zoomicon = QIcon(os.path.dirname(__file__) + "/images/zoomicon.png")
        self.zoomToAction = QAction(zoomicon, "Zoom To Latitude, Longitude", self.iface.mainWindow())
        self.zoomToAction.triggered.connect(self.zoomTo)
        self.iface.addPluginToMenu('Lat Lon Tools', self.zoomToAction)
        self.canvas.mapToolSet.connect(self.unsetTool)

        self.zoomToDialog = ZoomToLatLon(self, self.iface, self.iface.mainWindow())
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()
        
        # Add Interface for Multi point zoom
        zoomicon = QIcon(os.path.dirname(__file__) + '/images/multizoom.png')
        self.multiZoomToAction = QAction(zoomicon, "Multi-location Zoom", self.iface.mainWindow())
        self.multiZoomToAction.triggered.connect(self.multiZoomTo)
        self.iface.addPluginToMenu('Lat Lon Tools', self.multiZoomToAction)
        
        
        # Initialize the Settings Dialog Box
        settingsicon = QIcon(os.path.dirname(__file__) + '/images/settings.png')
        self.settingsAction = QAction(settingsicon, "Settings", self.iface.mainWindow())
        self.settingsAction.triggered.connect(self.settings)
        self.iface.addPluginToMenu('Lat Lon Tools', self.settingsAction)
        
        # Help
        helpicon = QIcon(os.path.dirname(__file__) + '/images/help.png')
        self.helpAction = QAction(helpicon, "Lat Lon Tools Help", self.iface.mainWindow())
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('Lat Lon Tools', self.helpAction)
                
    def unsetTool(self, tool):
        '''Uncheck the Copy Lat Lon tool'''
        try:
            if not isinstance(tool, CopyLatLonTool):
                self.copyAction.setChecked(False)
        except:
            pass

    def unload(self):
        '''Unload LatLonTools from the QGIS interface'''
        self.canvas.unsetMapTool(self.mapTool)
        self.iface.removePluginMenu('Lat Lon Tools', self.copyAction)
        self.iface.removeToolBarIcon(self.copyAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.zoomToAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.multiZoomToAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.settingsAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.helpAction)
        self.iface.removeDockWidget(self.zoomToDialog)
        self.zoomToDialog = None

    def setTool(self):
        '''Set the focus of the copy coordinate tool and check it'''
        self.copyAction.setChecked(True)
        self.canvas.setMapTool(self.mapTool)

    def zoomTo(self):
        '''Show the zoom to docked widget.'''
        self.zoomToDialog.show()

    def multiZoomTo(self):
        '''Display the Multi-zoom to dialog box'''
        self.multiZoomDialog.show()
    
    def settings(self):
        '''Show the settings dialog box'''
        self.settingsDialog.show()
        
    def help(self):
        '''Display a help page'''
        webbrowser.open("https://github.com/NationalSecurityAgency/qgis-latlontools-plugin/#readme")
        
    def settingsChanged(self):
        # Settings may have changed so we need to make sure the zoomToDialog window is configured properly
        self.zoomToDialog.configure()
            
 
    def zoomToLatLon(self, lat, lon):
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
        

 
