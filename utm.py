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

class UtmException(Exception):
    pass

def utmParse(utm_str):
    utm = utm_str.strip().upper()
    m = re.match(r'(\d+)\s*([NS])\s+(\d+\.?\d*)\s+(\d+\.?\d*)', utm)
    if m:
        m = m.groups()
        if len(m) == 4:
            zone = int(m[0])
            if zone < 1 or zone > 60:
                raise UtmException(tr('Invalid UTM Coordinate'))
            hemisphere = m[1]
            if hemisphere != 'N' and hemisphere != 'S':
                raise UtmException(tr('Invalid UTM Coordinate'))
            easting = float(m[2])
            northing = float(m[3])
            return(zone, hemisphere, easting, northing)
    m = re.match(r'(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+)\s*([NS])', utm)
    if m is None:
        m = re.match(r'(\d+\.?\d*)\s*M\s*E\s*,\s*(\d+\.?\d*)\s*M\s*N\s*,\s*(\d+)\s*([NS])', utm)
        if m is None:
            m = re.match(r'(\d+\.?\d*)\s*M\s*E\s*,\s*(\d+\.?\d*)\s*M\s*N\s*,\s*(\d+)\s*,\s*([NS])', utm)
    if m:
        m = m.groups()
        if len(m) == 4:
            zone = int(m[2])
            if zone < 1 or zone > 60:
                raise UtmException(tr('Invalid UTM Coordinate'))
            hemisphere = m[3]
            if hemisphere != 'N' and hemisphere != 'S':
                raise UtmException(tr('Invalid UTM Coordinate'))
            easting = float(m[0])
            northing = float(m[1])
            return(zone, hemisphere, easting, northing)
    
    raise UtmException('Invalid UTM Coordinate')

def utm2Point(utm, crs=epsg4326):
    zone, hemisphere, easting, northing = utmParse(utm)
    utmcrs = QgsCoordinateReferenceSystem(utmGetEpsg(hemisphere, zone))
    pt = QgsPointXY(easting, northing)
    utmtrans = QgsCoordinateTransform(utmcrs, crs, QgsProject.instance())
    return(utmtrans.transform(pt))

def isUtm(utm):
    try:
        z, h, e, n = utmParse(utm)
    except Exception:
        return(False)

    return(True)

def latLon2UtmZone(lat, lon):
    if lon < -180 or lon > 360:
        raise UtmException(tr('Invalid longitude'))
    if lat > 84.5 or lat < -80.5:
        raise UtmException(tr('Invalid latitude'))
    if lon < 180:
        zone = int(31 + (lon / 6.0))
    else:
        zone = int((lon / 6) - 29)

    if zone > 60:
        zone = 1
    # Handle UTM special cases
    if 56.0 <= lat < 64.0 and 3.0 <= lon < 12.0:
        zone = 32

    if 72.0 <= lat < 84.0:
        if 0.0 <= lon < 9.0:
            zone = 31
        elif 9.0 <= lon < 21.0:
            zone = 33
        elif 21.0 <= lon < 33.0:
            zone = 35
        elif 33.0 <= lon < 42.0:
            zone = 37

    if lat < 0:
        hemisphere = 'S'
    else:
        hemisphere = 'N'
    return(zone, hemisphere)

def latLon2UtmParameters(lat, lon):
    zone, hemisphere = latLon2UtmZone(lat, lon)
    epsg = utmGetEpsg(hemisphere, zone)
    utmcrs = QgsCoordinateReferenceSystem(epsg)
    utmtrans = QgsCoordinateTransform(epsg4326, utmcrs, QgsProject.instance())
    pt = QgsPointXY(lon, lat)
    utmpt = utmtrans.transform(pt)
    return(zone, hemisphere, utmpt.x(), utmpt.y())

def latLon2Utm(lat, lon, precision, format=0):
    try:
        zone, hemisphere, utmx, utmy = latLon2UtmParameters(lat, lon)
        if format == 0:
            msg = '{}{} {:.{prec}f} {:.{prec}f}'.format(zone, hemisphere, utmx, utmy, prec=precision)
        elif format == 1:
            msg = '{:.{prec}f},{:.{prec}f},{}{}'.format(utmx, utmy, zone, hemisphere, prec=precision)
        elif format == 2:
            msg = '{:.{prec}f}mE,{:.{prec}f}mN,{}{}'.format(utmx, utmy, zone, hemisphere, prec=precision)
        else:
            msg = '{:.{prec}f}mE,{:.{prec}f}mN,{},{}'.format(utmx, utmy, zone, hemisphere, prec=precision)
    except Exception:
        msg = ''
    return(msg)

def utmGetEpsg(hemisphere, zone):
    if hemisphere == 'N':
        code = 32600 + zone
    else:
        code = 32700 + zone
    return('EPSG:{}'.format(code))
