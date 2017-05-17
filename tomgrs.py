import os

from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsMapLayerProxyModel, QgsVectorLayer, QgsFields, QgsField, QgsFeature, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMessageBar

from . import mgrs

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/tomgrs.ui'))


class ToMGRSWidget(QDialog, FORM_CLASS):
    '''ToMGRS Dialog box.'''
    def __init__(self, iface, parent):
        super(ToMGRSWidget, self).__init__(parent)
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
            
        # Get the field names for the input layer. The will be copied to the output layer with MGRS added
        fields = layer.pendingFields()
        fieldsout = QgsFields(fields)
        
        # We need to add the mgrs field at the end
        if fieldsout.append(QgsField(field_name, QVariant.String)) == False:
            self.iface.messageBar().pushMessage("", "MGRS Field Name must be unique", level=QgsMessageBar.WARNING, duration=4)
            return
        precision = self.precisionSpinBox.value()
        layerCRS = layer.crs()
        pointLayer = QgsVectorLayer("Point?crs={}".format(layerCRS.authid()), layer_name, "memory")
        ppoint = pointLayer.dataProvider()
        ppoint.addAttributes(fieldsout)
        pointLayer.updateFields()

        # The input to the mgrs conversions requires latitudes and longitudes
        # If the layer is not EPSG:4326 we need to convert it.
        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        if layerCRS != epsg4326:
            transform = QgsCoordinateTransform(inCRS, epsg4326)

        iter = layer.getFeatures()

        for feature in iter:
            pt = feature.geometry().asPoint()
            if layerCRS != epsg4326:
                pt = transform.transform(pt)
            try:
                msg = mgrs.toMgrs(pt.y(), pt.x(), precision)
            except:
                msg = ''
            f = QgsFeature()
            f.setGeometry(feature.geometry())
            f.setAttributes(feature.attributes()+[msg])
            ppoint.addFeatures([f])
            
        pointLayer.updateExtents()
        QgsProject.instance().addMapLayer(pointLayer)
        self.close()
        
        