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
import re
import math
from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from .util import epsg4326, tr

epsg32661 = QgsCoordinateReferenceSystem("EPSG:32661")
epsg32761 = QgsCoordinateReferenceSystem("EPSG:32761")

class UpsException(Exception):
    pass

def upsParse(ups_str):
    ups = ups_str.strip().upper()
    m = re.match(r'^([ABYZ])\s+(\d+\.?\d*)\s*M\s*E\s+(\d+\.?\d*)\s*M\s*N', ups)
    if m is None:
        m = re.match(r'^([ABYZ])\s+(\d+\.?\d*)\s+(\d+\.?\d*)', ups)
        if m is None:
            m = re.match(r'^([ABYZ])(\d+\.?\d*)E(\d+\.?\d*)N', ups)
    if m:
        m = m.groups()
        if len(m) == 3:
            letter = m[0]
            easting = float(m[1])
            northing = float(m[2])
            return(letter, easting, northing)
    
    raise UpsException(tr('Invalid UPS Coordinate'))

def ups2Point(ups, crs=epsg4326):
    letter, easting, northing = upsParse(ups)
    if letter == 'A' or letter == 'B':
        epsg = epsg32761
    else:
        epsg = epsg32661
    pt = QgsPointXY(easting, northing)
    upstrans = QgsCoordinateTransform(epsg, crs, QgsProject.instance())
    return(upstrans.transform(pt))

def isUps(ups):
    try:
        l, e, n = upsParse(ups)
    except Exception:
        return(False)

    return(True)


def latLon2Ups(lat, lon, precision=0, format=0):
    if lon < -180 or lon > 360:
        return("")
    if lat < 83.5 and lat > -79.5:
        return("")
    if lat > 90 or lat < -90:
        return("")
    if lon > 180:
        lon -= 360
    if lat >= 83.5:
        epsg = epsg32661
        if lon < 0:
            letter = 'Y'
        else:
            letter = 'Z'
    else:
        epsg = epsg32761
        if lon < 0:
            letter = 'A'
        else:
            letter = 'B'
    upstrans = QgsCoordinateTransform(epsg4326, epsg, QgsProject.instance())
    pt = QgsPointXY(lon, lat)
    upspt = upstrans.transform(pt)
    if format == 0:
        msg = '{} {:.{prec}f}mE {:.{prec}f}mN'.format(letter, upspt.x(), upspt.y(), prec=precision)
    else:
        msg = '{}{:.{prec}f}E{:.{prec}f}N'.format(letter, upspt.x(), upspt.y(), prec=precision)

    return(msg)
