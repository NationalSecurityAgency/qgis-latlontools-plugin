import re
from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from .util import epsg4326

class UtmException(Exception):
    pass

def utmParse(utm_str):
    utm = utm_str.strip().upper()
    m = re.match(r'(\d+)\s*([NS])\s+(\d+\.?\d*)\s+(\d+\.?\d*)', utm).groups()
    if len(m) != 4:
        raise UtmException('Invalid UTM Coordinate')
    zone = int(m[0])
    if zone < 1 or zone > 60:
        raise UtmException('Invalid UTM Coordinate')
    hemisphere = m[1]
    if hemisphere != 'N' and hemisphere != 'S':
        raise UtmException('Invalid UTM Coordinate')
    easting = float(m[2])
    northing = float(m[3])
    return(zone, hemisphere, easting, northing)

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
        raise UtmException('Invalid longitude')
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

def latLon2Utm(lat, lon, precision):
    try:
        zone, hemisphere, utmx, utmy = latLon2UtmParameters(lat, lon)
        msg = '{}{} {:.{prec}f} {:.{prec}f}'.format(zone, hemisphere, utmx, utmy, prec=precision)
    except Exception:
        msg = ''
    return(msg)

def utmGetEpsg(hemisphere, zone):
    if hemisphere == 'N':
        code = 32600 + zone
    else:
        code = 32700 + zone
    return('EPSG:{}'.format(code))
