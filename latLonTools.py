from qgis.PyQt.QtCore import Qt, QTimer, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QApplication
from qgis.core import Qgis, QgsCoordinateTransform, QgsVectorLayer, QgsRectangle, QgsPoint, QgsPointXY, QgsGeometry, QgsWkbTypes, QgsProject, QgsApplication
from qgis.gui import QgsRubberBand
import processing

from .zoomToLatLon import ZoomToLatLon
from .multizoom import MultiZoomWidget
from .settings import SettingsWidget, settings
from .provider import LatLonToolsProvider
from .util import epsg4326
import os


class LatLonTools:
    digitizerDialog = None
    convertCoordinateDialog = None
    mapTool = None
    showMapTool = None

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.crossRb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.crossRb.setColor(Qt.red)
        self.provider = LatLonToolsProvider()
        self.toolbar = self.iface.addToolBar('Lat Lon Tools Toolbar')
        self.toolbar.setObjectName('LatLonToolsToolbar')

    def initGui(self):
        '''Initialize Lot Lon Tools GUI.'''
        # Initialize the Settings Dialog box
        self.settingsDialog = SettingsWidget(self, self.iface, self.iface.mainWindow())

        # Add Interface for Coordinate Capturing
        icon = QIcon(os.path.dirname(__file__) + "/images/copyicon.png")
        self.copyAction = QAction(icon, "Copy/Display Coordinate", self.iface.mainWindow())
        self.copyAction.setObjectName('latLonToolsCopy')
        self.copyAction.triggered.connect(self.startCapture)
        self.copyAction.setCheckable(True)
        self.toolbar.addAction(self.copyAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.copyAction)

        # Add Interface for External Map
        icon = QIcon(os.path.dirname(__file__) + "/images/mapicon.png")
        self.externMapAction = QAction(icon, "Show in External Map", self.iface.mainWindow())
        self.externMapAction.setObjectName('latLonToolsExternalMap')
        self.externMapAction.triggered.connect(self.setShowMapTool)
        self.externMapAction.setCheckable(True)
        self.toolbar.addAction(self.externMapAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.externMapAction)

        # Add Interface for Zoom to Coordinate
        icon = QIcon(os.path.dirname(__file__) + "/images/zoomicon.png")
        self.zoomToAction = QAction(icon, "Zoom To Coordinate", self.iface.mainWindow())
        self.zoomToAction.setObjectName('latLonToolsZoom')
        self.zoomToAction.triggered.connect(self.showZoomToDialog)
        self.toolbar.addAction(self.zoomToAction)
        self.iface.addPluginToMenu('Lat Lon Tools', self.zoomToAction)

        self.zoomToDialog = ZoomToLatLon(self, self.iface, self.iface.mainWindow())
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()

        # Add Interface for Multi point zoom
        icon = QIcon(os.path.dirname(__file__) + '/images/multizoom.png')
        self.multiZoomToAction = QAction(icon, "Multi-location Zoom", self.iface.mainWindow())
        self.multiZoomToAction.setObjectName('latLonToolsMultiZoom')
        self.multiZoomToAction.triggered.connect(self.multiZoomTo)
        self.toolbar.addAction(self.multiZoomToAction)
        self.iface.addPluginToMenu('Lat Lon Tools', self.multiZoomToAction)

        self.multiZoomDialog = MultiZoomWidget(self, self.settingsDialog, self.iface.mainWindow())
        self.multiZoomDialog.hide()
        self.multiZoomDialog.setFloating(True)

        # Create the coordinate converter menu
        icon = QIcon(':/images/themes/default/mIconProjectionEnabled.svg')
        self.convertCoordinatesAction = QAction(icon, "Coordinate Conversion", self.iface.mainWindow())
        self.convertCoordinatesAction.setObjectName('latLonToolsCoordinateConversion')
        self.convertCoordinatesAction.triggered.connect(self.convertCoordinatesTool)
        self.toolbar.addAction(self.convertCoordinatesAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.convertCoordinatesAction)

        # Create the conversions menu
        menu = QMenu()
        icon = QIcon(os.path.dirname(__file__) + '/images/field2geom.png')
        action = menu.addAction(icon, "Fields to point layer", self.field2geom)
        action.setObjectName('latLonToolsField2Geom')
        icon = QIcon(os.path.dirname(__file__) + '/images/geom2field.png')
        action = menu.addAction(icon, "Point layer to fields", self.geom2Field)
        action.setObjectName('latLonToolsGeom2Field')
        icon = QIcon(os.path.dirname(__file__) + '/images/pluscodes.png')
        action = menu.addAction(icon, "Plus Codes to point layer", self.PlusCodestoLayer)
        action.setObjectName('latLonToolsPlusCodes2Geom')
        action = menu.addAction(icon, "Point layer to Plus Codes", self.toPlusCodes)
        action.setObjectName('latLonToolsGeom2PlusCodes')
        icon = QIcon(os.path.dirname(__file__) + '/images/mgrs2point.png')
        action = menu.addAction(icon, "MGRS to point layer", self.MGRStoLayer)
        action.setObjectName('latLonToolsMGRS2Geom')
        icon = QIcon(os.path.dirname(__file__) + '/images/point2mgrs.png')
        action = menu.addAction(icon, "Point layer to MGRS", self.toMGRS)
        action.setObjectName('latLonToolsGeom2MGRS')
        self.conversionsAction = QAction(icon, "Conversions", self.iface.mainWindow())
        self.conversionsAction.setMenu(menu)
        self.iface.addPluginToMenu('Lat Lon Tools', self.conversionsAction)

        # Add to Digitize Toolbar
        icon = QIcon(os.path.dirname(__file__) + '/images/latLonDigitize.png')
        self.digitizeAction = QAction(icon, "Lat Lon Digitize", self.iface.mainWindow())
        self.digitizeAction.setObjectName('latLonToolsDigitize')
        self.digitizeAction.triggered.connect(self.digitizeClicked)
        self.digitizeAction.setEnabled(False)
        self.toolbar.addAction(self.digitizeAction)
        self.iface.addPluginToMenu('Lat Lon Tools', self.digitizeAction)

        # Add Interface for copying the canvas extent
        icon = QIcon(os.path.dirname(__file__) + "/images/copycanvas.png")
        self.copyCanvasAction = QAction(icon, "Copy Canvas Bounding Box", self.iface.mainWindow())
        self.copyCanvasAction.setObjectName('latLonToolsCopyCanvas')
        self.copyCanvasAction.triggered.connect(self.copyCanvas)
        self.toolbar.addAction(self.copyCanvasAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.copyCanvasAction)

        # Initialize the Settings Dialog Box
        settingsicon = QIcon(os.path.dirname(__file__) + '/images/settings.png')
        self.settingsAction = QAction(settingsicon, "Settings", self.iface.mainWindow())
        self.settingsAction.setObjectName('latLonToolsSettings')
        self.settingsAction.triggered.connect(self.settings)
        self.iface.addPluginToMenu('Lat Lon Tools', self.settingsAction)

        # Help
        icon = QIcon(os.path.dirname(__file__) + '/images/help.png')
        self.helpAction = QAction(icon, "Help", self.iface.mainWindow())
        self.helpAction.setObjectName('latLonToolsHelp')
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('Lat Lon Tools', self.helpAction)

        self.iface.currentLayerChanged.connect(self.currentLayerChanged)
        self.canvas.mapToolSet.connect(self.resetTools)
        self.enableDigitizeTool()

        # Add the processing provider
        QgsApplication.processingRegistry().addProvider(self.provider)

    def resetTools(self, newtool, oldtool):
        '''Uncheck the Copy Lat Lon tool'''
        try:
            if self.mapTool and (oldtool is self.mapTool):
                self.copyAction.setChecked(False)
            if self.showMapTool and (oldtool is self.showMapTool):
                self.externMapAction.setChecked(False)
            if newtool is self.mapTool:
                self.copyAction.setChecked(True)
            if newtool is self.showMapTool:
                self.externMapAction.setChecked(True)
        except Exception:
            pass

    def unload(self):
        '''Unload LatLonTools from the QGIS interface'''
        self.zoomToDialog.removeMarker()
        self.multiZoomDialog.removeMarkers()
        if self.mapTool:
            self.canvas.unsetMapTool(self.mapTool)
        if self.showMapTool:
            self.canvas.unsetMapTool(self.showMapTool)
        self.iface.removePluginMenu('Lat Lon Tools', self.copyAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.copyCanvasAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.externMapAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.zoomToAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.multiZoomToAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.convertCoordinatesAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.conversionsAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.settingsAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.helpAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.digitizeAction)
        self.iface.removeDockWidget(self.zoomToDialog)
        self.iface.removeDockWidget(self.multiZoomDialog)
        # Remove Toolbar Icons
        self.iface.removeToolBarIcon(self.copyAction)
        self.iface.removeToolBarIcon(self.copyCanvasAction)
        self.iface.removeToolBarIcon(self.zoomToAction)
        self.iface.removeToolBarIcon(self.externMapAction)
        self.iface.removeToolBarIcon(self.multiZoomToAction)
        self.iface.removeToolBarIcon(self.convertCoordinatesAction)
        self.iface.removeToolBarIcon(self.digitizeAction)
        del self.toolbar

        self.zoomToDialog = None
        self.multiZoomDialog = None
        self.settingsDialog = None
        self.showMapTool = None
        self.mapTool = None
        self.digitizerDialog = None
        self.convertCoordinateDialog = None
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def startCapture(self):
        '''Set the focus of the copy coordinate tool'''
        if self.mapTool is None:
            from .copyLatLonTool import CopyLatLonTool
            self.mapTool = CopyLatLonTool(self.settingsDialog, self.iface)
        self.canvas.setMapTool(self.mapTool)

    def copyCanvas(self):
        extent = self.iface.mapCanvas().extent()
        canvasCrs = self.canvas.mapSettings().destinationCrs()
        if settings.bBoxCrs == 0 and canvasCrs != epsg4326:
            transform = QgsCoordinateTransform(canvasCrs, epsg4326, QgsProject.instance())
            p1x, p1y = transform.transform(float(extent.xMinimum()), float(extent.yMinimum()))
            p2x, p2y = transform.transform(float(extent.xMaximum()), float(extent.yMaximum()))
            extent.set(p1x, p1y, p2x, p2y)
        delim = settings.bBoxDelimiter
        prefix = settings.bBoxPrefix
        suffix = settings.bBoxSuffix
        precision = settings.bBoxDigits
        outStr = ''
        minX = extent.xMinimum()
        minY = extent.yMinimum()
        maxX = extent.xMaximum()
        maxY = extent.yMaximum()
        if settings.bBoxFormat == 0:  # minX,minY,maxX,maxY - using the delimiter
            outStr = '{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}'.format(
                minX, delim, minY, delim, maxX, delim, maxY, prec=precision)
        elif settings.bBoxFormat == 1:  # minX,maxX,minY,maxY - Using the selected delimiter'
            outStr = '{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}'.format(
                minX, delim, maxX, delim, minY, delim, maxY, prec=precision)
        elif settings.bBoxFormat == 2:  # x1 y1,x2 y2,x3 y3,x4 y4,x1 y1 - Polygon format
            outStr = '{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f}'.format(
                minX, minY, minX, maxY, maxX, maxY, maxX, minY, minX, minY, prec=precision)
        elif settings.bBoxFormat == 3:  # x1,y1 x2,y2 x3,y3 x4,y4 x1,y1 - Polygon format
            outStr = '{:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f}'.format(
                minX, minY, minX, maxY, maxX, maxY, maxX, minY, minX, minY, prec=precision)
        elif settings.bBoxFormat == 4:  # WKT Polygon
            outStr = extent.asWktPolygon()
        elif settings.bBoxFormat == 5:  # bbox: [minX, minY, maxX, maxY] - MapProxy
            outStr = 'bbox: [{}, {}, {}, {}]'.format(
                minX, minY, maxX, maxY)
        elif settings.bBoxFormat == 6:  # bbox: [minX, minY, maxX, maxY] - MapProxy
            outStr = 'bbox={},{},{},{}'.format(
                minX, minY, maxX, maxY)
        outStr = '{}{}{}'.format(prefix, outStr, suffix)
        clipboard = QApplication.clipboard()
        clipboard.setText(outStr)
        self.iface.messageBar().pushMessage("", "'{}' copied to the clipboard".format(outStr), level=Qgis.Info, duration=4)

    def setShowMapTool(self):
        '''Set the focus of the external map tool.'''
        if self.showMapTool is None:
            from .showOnMapTool import ShowOnMapTool
            self.showMapTool = ShowOnMapTool(self.iface)
        self.canvas.setMapTool(self.showMapTool)

    def showZoomToDialog(self):
        '''Show the zoom to docked widget.'''
        self.zoomToDialog.show()

    def convertCoordinatesTool(self):
        '''Display the Convert Coordinate Tool Dialog box.'''
        if self.convertCoordinateDialog is None:
            from .coordinateConverter import CoordinateConverterWidget
            self.convertCoordinateDialog = CoordinateConverterWidget(self, self.settingsDialog, self.iface, self.iface.mainWindow())
            self.convertCoordinateDialog.setFloating(True)
        self.convertCoordinateDialog.show()

    def multiZoomTo(self):
        '''Display the Multi-zoom to dialog box'''
        self.multiZoomDialog.show()

    def field2geom(self):
        '''Convert layer containing a point x & y coordinate to a new point layer'''
        processing.execAlgorithmDialog('latlontools:field2geom', {})

    def geom2Field(self):
        '''Convert layer geometry to a text string'''
        processing.execAlgorithmDialog('latlontools:geom2field', {})

    def toMGRS(self):
        '''Display the to MGRS  dialog box'''
        processing.execAlgorithmDialog('latlontools:point2mgrs', {})

    def MGRStoLayer(self):
        '''Display the to MGRS  dialog box'''
        processing.execAlgorithmDialog('latlontools:mgrs2point', {})

    def toPlusCodes(self):
        processing.execAlgorithmDialog('latlontools:point2pluscodes', {})

    def PlusCodestoLayer(self):
        processing.execAlgorithmDialog('latlontools:pluscodes2point', {})

    def settings(self):
        '''Show the settings dialog box'''
        self.settingsDialog.show()

    def help(self):
        '''Display a help page'''
        import webbrowser
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)

    def settingsChanged(self):
        # Settings may have changed so we need to make sure the zoomToDialog window is configured properly
        self.zoomToDialog.configure()
        self.multiZoomDialog.settingsChanged()

    def zoomTo(self, srcCrs, lat, lon):
        canvasCrs = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(srcCrs, canvasCrs, QgsProject.instance())
        x, y = transform.transform(float(lon), float(lat))

        rect = QgsRectangle(x, y, x, y)
        self.canvas.setExtent(rect)

        pt = QgsPointXY(x, y)
        self.highlight(pt)
        self.canvas.refresh()
        return pt

    def highlight(self, point):
        currExt = self.canvas.extent()

        leftPt = QgsPoint(currExt.xMinimum(), point.y())
        rightPt = QgsPoint(currExt.xMaximum(), point.y())

        topPt = QgsPoint(point.x(), currExt.yMaximum())
        bottomPt = QgsPoint(point.x(), currExt.yMinimum())

        horizLine = QgsGeometry.fromPolyline([leftPt, rightPt])
        vertLine = QgsGeometry.fromPolyline([topPt, bottomPt])

        self.crossRb.reset(QgsWkbTypes.LineGeometry)
        self.crossRb.addGeometry(horizLine, None)
        self.crossRb.addGeometry(vertLine, None)

        QTimer.singleShot(700, self.resetRubberbands)

    def resetRubberbands(self):
        self.crossRb.reset()

    def digitizeClicked(self):
        if self.digitizerDialog is None:
            from .digitizer import DigitizerWidget
            self.digitizerDialog = DigitizerWidget(self, self.iface, self.iface.mainWindow())
        self.digitizerDialog.show()

    def currentLayerChanged(self):
        layer = self.iface.activeLayer()
        if layer is not None:
            try:
                layer.editingStarted.disconnect(self.layerEditingChanged)
            except Exception:
                pass
            try:
                layer.editingStopped.disconnect(self.layerEditingChanged)
            except Exception:
                pass

            if isinstance(layer, QgsVectorLayer):
                layer.editingStarted.connect(self.layerEditingChanged)
                layer.editingStopped.connect(self.layerEditingChanged)

        self.enableDigitizeTool()

    def layerEditingChanged(self):
        self.enableDigitizeTool()

    def enableDigitizeTool(self):
        self.digitizeAction.setEnabled(False)
        layer = self.iface.activeLayer()

        if layer is not None and isinstance(layer, QgsVectorLayer) and (layer.geometryType() == QgsWkbTypes.PointGeometry) and layer.isEditable():
            self.digitizeAction.setEnabled(True)
        else:
            if self.digitizerDialog is not None:
                self.digitizerDialog.close()
