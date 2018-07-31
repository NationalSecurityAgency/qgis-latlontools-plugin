import os

from PyQt4.QtGui import QDialog
from PyQt4.uic import loadUiType
from PyQt4.QtCore import QVariant
from qgis.core import QgsVectorLayer, QgsFields, QgsField, QgsFeature, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsMapLayerRegistry
from qgis.gui import QgsMapLayerProxyModel, QgsMessageBar

from .util import *
import olc

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/topluscodes.ui'))


class ToPlusCodesWidget(QDialog, FORM_CLASS):
    '''ToMGRS Dialog box.'''
    def __init__(self, iface, parent):
        super(ToPlusCodesWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.mapLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
                
    def accept(self):
        field_name = self.fieldLineEdit.text()
        layer_name = self.layerLineEdit.text()
        layer = self.mapLayerComboBox.currentLayer()
        if not layer:
            self.iface.messageBar().pushMessage("", "No Valid Layer", level=QgsMessageBar.WARNING, duration=4)
            return
            
        # Get the field names for the input layer. The will be copied to the output layer with Plus Codes added
        fields = layer.pendingFields()
        fieldsout = QgsFields(fields)
        
        # We need to add the plus codes field at the end
        if fieldsout.append(QgsField(field_name, QVariant.String)) == False:
            self.iface.messageBar().pushMessage("", "Plus Codes Field Name must be unique", level=QgsMessageBar.WARNING, duration=4)
            return
        precision = self.precisionSpinBox.value()
        layerCRS = layer.crs()
        pointLayer = QgsVectorLayer("Point?crs={}".format(layerCRS.authid()), layer_name, "memory")
        ppoint = pointLayer.dataProvider()
        ppoint.addAttributes(fieldsout)
        pointLayer.updateFields()

        # The input to the plus codes conversions requires latitudes and longitudes
        # If the layer is not EPSG:4326 we need to convert it.
        if layerCRS != epsg4326:
            transform = QgsCoordinateTransform(layerCRS, epsg4326)

        iter = layer.getFeatures()

        for feature in iter:
            pt = feature.geometry().asPoint()
            if layerCRS != epsg4326:
                pt = transform.transform(pt)
            try:
                msg = olc.encode(pt.y(), pt.x(), precision)
            except:
                msg = ''
            f = QgsFeature()
            f.setGeometry(feature.geometry())
            f.setAttributes(feature.attributes()+[msg])
            ppoint.addFeatures([f])
            
        pointLayer.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayer(pointLayer)
        self.close()
        
        