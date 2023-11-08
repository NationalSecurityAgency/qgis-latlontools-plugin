"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import Qgis, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject
from qgis.gui import QgsMapToolExtent
# import traceback
from .util import epsg4326, tr
from .settings import settings, CopyExtent

def getExtentString(bbox, src_crs, dst_crs):
    if src_crs != dst_crs:
        transform = QgsCoordinateTransform(src_crs, dst_crs, QgsProject.instance())
        bbox = transform.transformBoundingBox(bbox)
    delim = settings.bBoxDelimiter
    prefix = settings.bBoxPrefix
    suffix = settings.bBoxSuffix
    precision = settings.bBoxDigits
    outStr = ''
    minX = bbox.xMinimum()
    minY = bbox.yMinimum()
    maxX = bbox.xMaximum()
    maxY = bbox.yMaximum()
    if settings.bBoxFormat == CopyExtent.WSEN:  # minX,minY,maxX,maxY (W,S,E,N)
        outStr = '{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}'.format(
            minX, delim, minY, delim, maxX, delim, maxY, prec=precision)
    elif settings.bBoxFormat == CopyExtent.WESN:  # minX,maxX,minY,maxY (W,E,S,N)
        outStr = '{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}'.format(
            minX, delim, maxX, delim, minY, delim, maxY, prec=precision)
    elif settings.bBoxFormat == CopyExtent.SWNE:  # minY,minX,maxY,maxX (S,W,N,E)
        outStr = '{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}{}{:.{prec}f}'.format(
            minY, delim, minX, delim, maxY, delim, maxX, prec=precision)
    elif settings.bBoxFormat == CopyExtent.Poly1:  # x1 y1,x2 y2,x3 y3,x4 y4,x1 y1 - Polygon format
        outStr = '{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f}'.format(
            minX, minY, minX, maxY, maxX, maxY, maxX, minY, minX, minY, prec=precision)
    elif settings.bBoxFormat == CopyExtent.Poly2:  # x1,y1 x2,y2 x3,y3 x4,y4 x1,y1 - Polygon format
        outStr = '{:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f} {:.{prec}f},{:.{prec}f}'.format(
            minX, minY, minX, maxY, maxX, maxY, maxX, minY, minX, minY, prec=precision)
    elif settings.bBoxFormat == CopyExtent.PolyWkt:  # WKT Polygon
        outStr = bbox.asWktPolygon()
    elif settings.bBoxFormat == CopyExtent.MapProxy:  # bbox: [minX, minY, maxX, maxY] - MapProxy
        outStr = 'bbox: [{}, {}, {}, {}]'.format(
            minX, minY, maxX, maxY)
    elif settings.bBoxFormat == CopyExtent.GeoServer:  # bbox=minX,minY,maxX,maxY - GeoServer
        outStr = 'bbox={},{},{},{}'.format(
            minX, minY, maxX, maxY)
    outStr = '{}{}{}'.format(prefix, outStr, suffix)
    return(outStr)

class CaptureExtentTool(QgsMapToolExtent):
    def __init__(self, iface, parent):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        QgsMapToolExtent.__init__(self, self.canvas)
        self.extentChanged.connect(self.getExtent)

    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)

    def deactivate(self):
        QgsMapToolExtent.deactivate(self)
        action = self.action()
        if action:
            action.setChecked(False)
        
    def getExtent(self, bbox):
        if bbox.isNull():
            return
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        if settings.bBoxCrs == 0:
            dstCRS = epsg4326
        else:
            dstCRS = canvasCRS

        outStr = getExtentString(bbox, canvasCRS, dstCRS)

        clipboard = QApplication.clipboard()
        clipboard.setText(outStr)
        self.iface.messageBar().pushMessage("", "'{}'".format(outStr) + tr("copied to the clipboard"), level=Qgis.Info, duration=4)
