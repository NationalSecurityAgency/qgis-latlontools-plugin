import os
import re

from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsMapLayerProxyModel, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint, QgsProject
from qgis.gui import QgsMessageBar
#import traceback

from . import mgrs

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/mgrstolayer.ui'))


class MGRStoLayerWidget(QDialog, FORM_CLASS):
    '''Convert an MGRS field to a point geometry layer.'''
    def __init__(self, iface, parent):
        super(MGRStoLayerWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer | QgsMapLayerProxyModel.NoGeometry)
        self.mMapLayerComboBox.layerChanged.connect(self.layerChanged)
        
    def accept(self):
        layer = self.mMapLayerComboBox.currentLayer()
        if not layer:
            self.iface.messageBar().pushMessage("", "No Valid Layer to Process", level=QgsMessageBar.WARNING, duration=4)
            return
        layer_name = self.nameLineEdit.text()
        
        selectedField = self.mFieldComboBox.currentField()
        fieldIndex = layer.fields().lookupField(selectedField)
        if fieldIndex == -1:
            self.iface.messageBar().pushMessage("", "Invalid MGRS Field", level=QgsMessageBar.WARNING, duration=4)
            return
        
        fields = layer.pendingFields()
        # Check to see if the field is of the right type
        f = fields.at(fieldIndex)
        if f.type() != QVariant.String:
            self.iface.messageBar().pushMessage("", "Selected MGRS Field is not a valid data type", level=QgsMessageBar.WARNING, duration=4)
            return
            
        
        pointLayer = QgsVectorLayer("Point?crs=epsg:4326", layer_name, "memory")
        ppoint = pointLayer.dataProvider()
        ppoint.addAttributes(fields)
        pointLayer.updateFields()

        iter = layer.getFeatures()

        num_features = 0
        num_bad = 0
        for feature in iter:
            num_features += 1
            m = feature[fieldIndex]
            try:
                m = re.sub(r'\s+', '', str(m)) # Remove all white space
                lat, lon = mgrs.toWgs(m)
            except:
                #traceback.print_exc()
                num_bad += 1
                continue
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPoint(QgsPoint(lon,lat)))
            f.setAttributes(feature.attributes())
            ppoint.addFeatures([f])
            
        pointLayer.updateExtents()
        QgsProject.instance().addMapLayer(pointLayer)
        
        if num_bad != 0:
            self.iface.messageBar().pushMessage("", "{} out of {} features failed".format(num_bad, num_features), level=QgsMessageBar.WARNING, duration=4)
        
        self.close()
        
    def layerChanged(self):
        if not self.isVisible():
            return
        layer = self.mMapLayerComboBox.currentLayer()
        self.mFieldComboBox.setLayer(layer)
        
    def showEvent(self, event):
        self.layerChanged()