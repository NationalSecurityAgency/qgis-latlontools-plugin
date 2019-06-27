import re
from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from .util import epsg4326

utm_epsg_codes = {
    '1N': 'EPSG:32601',
    '2N': 'EPSG:32602',
    '3N': 'EPSG:32603',
    '4N': 'EPSG:32604',
    '5N': 'EPSG:32605',
    '6N': 'EPSG:32606',
    '7N': 'EPSG:32607',
    '8N': 'EPSG:32608',
    '9N': 'EPSG:32609',
    '10N': 'EPSG:32610',
    '11N': 'EPSG:32611',
    '12N': 'EPSG:32612',
    '13N': 'EPSG:32613',
    '14N': 'EPSG:32614',
    '15N': 'EPSG:32615',
    '16N': 'EPSG:32616',
    '17N': 'EPSG:32617',
    '18N': 'EPSG:32618',
    '19N': 'EPSG:32619',
    '20N': 'EPSG:32620',
    '21N': 'EPSG:32621',
    '22N': 'EPSG:32622',
    '23N': 'EPSG:32623',
    '24N': 'EPSG:32624',
    '25N': 'EPSG:32625',
    '26N': 'EPSG:32626',
    '27N': 'EPSG:32627',
    '28N': 'EPSG:32628',
    '29N': 'EPSG:32629',
    '30N': 'EPSG:32630',
    '31N': 'EPSG:32631',
    '32N': 'EPSG:32632',
    '33N': 'EPSG:32633',
    '34N': 'EPSG:32634',
    '35N': 'EPSG:32635',
    '36N': 'EPSG:32636',
    '37N': 'EPSG:32637',
    '38N': 'EPSG:32638',
    '39N': 'EPSG:32639',
    '40N': 'EPSG:32640',
    '41N': 'EPSG:32641',
    '42N': 'EPSG:32642',
    '43N': 'EPSG:32643',
    '44N': 'EPSG:32644',
    '45N': 'EPSG:32645',
    '46N': 'EPSG:32646',
    '47N': 'EPSG:32647',
    '48N': 'EPSG:32648',
    '49N': 'EPSG:32649',
    '50N': 'EPSG:32650',
    '51N': 'EPSG:32651',
    '52N': 'EPSG:32652',
    '53N': 'EPSG:32653',
    '54N': 'EPSG:32654',
    '55N': 'EPSG:32655',
    '56N': 'EPSG:32656',
    '57N': 'EPSG:32657',
    '58N': 'EPSG:32658',
    '59N': 'EPSG:32659',
    '60N': 'EPSG:32660',
    '1S': 'EPSG:32701',
    '2S': 'EPSG:32702',
    '3S': 'EPSG:32703',
    '4S': 'EPSG:32704',
    '5S': 'EPSG:32705',
    '6S': 'EPSG:32706',
    '7S': 'EPSG:32707',
    '8S': 'EPSG:32708',
    '9S': 'EPSG:32709',
    '10S': 'EPSG:32710',
    '11S': 'EPSG:32711',
    '12S': 'EPSG:32712',
    '13S': 'EPSG:32713',
    '14S': 'EPSG:32714',
    '15S': 'EPSG:32715',
    '16S': 'EPSG:32716',
    '17S': 'EPSG:32717',
    '18S': 'EPSG:32718',
    '19S': 'EPSG:32719',
    '20S': 'EPSG:32720',
    '21S': 'EPSG:32721',
    '22S': 'EPSG:32722',
    '23S': 'EPSG:32723',
    '24S': 'EPSG:32724',
    '25S': 'EPSG:32725',
    '26S': 'EPSG:32726',
    '27S': 'EPSG:32727',
    '28S': 'EPSG:32728',
    '29S': 'EPSG:32729',
    '30S': 'EPSG:32730',
    '31S': 'EPSG:32731',
    '32S': 'EPSG:32732',
    '33S': 'EPSG:32733',
    '34S': 'EPSG:32734',
    '35S': 'EPSG:32735',
    '36S': 'EPSG:32736',
    '37S': 'EPSG:32737',
    '38S': 'EPSG:32738',
    '39S': 'EPSG:32739',
    '40S': 'EPSG:32740',
    '41S': 'EPSG:32741',
    '42S': 'EPSG:32742',
    '43S': 'EPSG:32743',
    '44S': 'EPSG:32744',
    '45S': 'EPSG:32745',
    '46S': 'EPSG:32746',
    '47S': 'EPSG:32747',
    '48S': 'EPSG:32748',
    '49S': 'EPSG:32749',
    '50S': 'EPSG:32750',
    '51S': 'EPSG:32751',
    '52S': 'EPSG:32752',
    '53S': 'EPSG:32753',
    '54S': 'EPSG:32754',
    '55S': 'EPSG:32755',
    '56S': 'EPSG:32756',
    '57S': 'EPSG:32757',
    '58S': 'EPSG:32758',
    '59S': 'EPSG:32759',
    '60S': 'EPSG:32760',
}

def utmString2Crs(utm, crs=epsg4326):
    parts = re.split(r'[\s]+', utm.upper())
    utmlen = len(parts)
    if utmlen == 3:
        m = re.findall(r'(\d+)([NS])', parts[0])
        if len(m) != 1 or len(m[0]) != 2:
            raise ValueError('Invalid UTM Coordinate')
        zone = int(m[0][0])
        hemisphere = m[0][1]
        easting = float(parts[1])
        northing = float(parts[2])
    elif utmlen == 4:
        if parts[1] != 'N' and parts[1] != 'S':
            raise ValueError('Invalid UTM Coordinate')
        zone = int(parts[0])
        easting = float(parts[2])
        northing = float(parts[3])
    else:
        raise ValueError('Invalid UTM Coordinate')
    if zone < 1 or zone > 60:
        raise ValueError('Invalid UTM Coordinate')

    utmcrs = QgsCoordinateReferenceSystem(utm_epsg_codes['{}{}'.format(zone, hemisphere)])
    pt = QgsPointXY(easting, northing)
    utmtrans = QgsCoordinateTransform(utmcrs, crs, QgsProject.instance())
    return(utmtrans.transform(pt))

def isUtm(utm):
    try:
        parts = re.split(r'[\s]+', utm.upper())
        utmlen = len(parts)
        if utmlen == 3:
            m = re.findall(r'(\d+)([NS])', parts[0])
            if len(m) != 1 or len(m[0]) != 2:
                return(False)
            zone = int(m[0][0])
            hemisphere = m[0][1]
            easting = float(parts[1])
            northing = float(parts[2])
        elif utmlen == 4:
            if parts[1] != 'N' and parts[1] != 'S':
                return(False)
            zone = int(parts[0])
            easting = float(parts[2])
            northing = float(parts[3])
        else:
            return(False)
        if zone < 1 or zone > 60:
            return(False)
    except Exception:
        return(False)

    return(True)

def latLon2UtmString(lat, lon, precision):
    zone = int((lon + 180) / 6) + 1
    if lon >= 0:
        zonestr = '{}N'.format(zone)
    else:
        zonestr = '{}S'.format(zone)
    try:
        utmcrs = QgsCoordinateReferenceSystem(utm_epsg_codes[zonestr])
        utmtrans = QgsCoordinateTransform(epsg4326, utmcrs, QgsProject.instance())
        pt = QgsPointXY(lon, lat)
        utmpt = utmtrans.transform(pt)
        msg = '{} {:.{prec}f} {:.{prec}f}'.format(zonestr, utmpt.x(), utmpt.y(), prec=precision)
    except Exception:
        msg = ''
    return(msg)
