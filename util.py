import math
import re
from qgis.core import QgsCoordinateReferenceSystem, QgsPoint

epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

def formatDmsString(lat, lon, isdms=False, prec=0, order=0, delimiter=', '):
    '''Return a DMS formated string.'''
    if order == 0: # Y, X or Lat, Lon
        return convertDD2DMS(lat, True, isdms, prec) + str(delimiter) + convertDD2DMS(lon, False, isdms, prec)
    else:
        return convertDD2DMS(lon, False, isdms, prec) + str(delimiter) + convertDD2DMS(lat, True, isdms, prec)

def convertDD2DMS(coord, islat, isdms, prec):
    '''Convert decimal degrees to DMS'''
    if islat:
        if coord < 0:
            unit = 'S'
        else:
            unit = 'N'
    else:
        if coord > 0:
            unit = 'E'
        else:
            unit = 'W'
    coord = math.fabs(coord)
    deg = math.floor(coord)
    dmin = (coord - deg) * 60.0
    min = math.floor(dmin)
    sec = (dmin - min) * 60.0
    if prec == 0:
        dprec = 2
    else:
        dprec = prec + 3
    if isdms:
        s = f"{deg:.0f}\xB0{min:.0f}\'{sec:.{prec}f}\""
    else:
        if islat:
            s = f"{deg:02.0f}{min:02.0f}{sec:0{dprec}.{prec}f}"
        else:
            s = f"{deg:03.0f}{min:02.0f}{sec:0{dprec}.{prec}f}"
    if isdms:
        s += " "+unit
    else:
        s += unit
    return(s)
    
def parseDMSString(str, order=0):
    '''Parses a pair of coordinates that are in the order of
    "latitude, longitude". The string can be in DMS or decimal
    degree notation. If order is 0 then then decimal coordinates are assumed to
    be in Lat Lon order otherwise they are in Lon Lat order. For DMS coordinates
    it does not matter the order.'''
    str = str.strip().upper() # Make it all upper case
    try:
        if re.search(r"[NSEW]", str) == None:
            # There were no annotated dms coordinates so assume decimal degrees
            # Remove any characters that are not digits and decimal
            str = re.sub(r"[^\d.+-]+", " ", str).strip()
            coords = re.split(r'\s+', str, 1)
            if len(coords) != 2:
                raise ValueError('Invalid Coordinates')
            if order == 0:
                lat = float(coords[0])
                lon = float(coords[1])
            else:
                lon = float(coords[0])
                lat = float(coords[1])
        else:
            # We should have a DMS coordinate
            if re.search(r'[NSEW]\s*\d+.+[NSEW]\s*\d+', str) == None:
                # We assume that the cardinal directions occur after the digits
                m = re.findall(r'(.+)\s*([NS])[\s,;:]*(.+)\s*([EW])', str)
                if len(m) != 1 or len(m[0]) != 4:
                    # This is either invalid or the coordinates are ordered by lon lat
                    m = re.findall(r'(.+)\s*([EW])[\s,;:]*(.+)\s*([NS])', str)
                    if len(m) != 1 or len(m[0]) != 4:
                        # Now we know it is invalid
                        raise ValueError('Invalid DMS Coordinate')
                    else:
                        # The coordinates were in lon, lat order
                        lon = parseDMS(m[0][0], m[0][1])
                        lat = parseDMS(m[0][2], m[0][3])
                else:
                    # The coordinates are in lat, lon order
                    lat = parseDMS(m[0][0], m[0][1])
                    lon = parseDMS(m[0][2], m[0][3])
            else:
                # The cardinal directions occur at the beginning of the digits
                m = re.findall(r'([NS])\s*(\d+.*?)[\s,;:]*([EW])(.+)', str)
                if len(m) != 1 or len(m[0]) != 4:
                    # This is either invalid or the coordinates are ordered by lon lat
                    m = re.findall(r'([EW])\s*(\d+.*?)[\s,;:]*([NS])(.+)', str)
                    if len(m) != 1 or len(m[0]) != 4:
                        # Now we know it is invalid
                        raise ValueError('Invalid DMS Coordinate')
                    else:
                        # The coordinates were in lon, lat order
                        lon = parseDMS(m[0][1], m[0][0])
                        lat = parseDMS(m[0][3], m[0][2])
                else:
                    # The coordinates are in lat, lon order
                    lat = parseDMS(m[0][1], m[0][0])
                    lon = parseDMS(m[0][3], m[0][2])
    
    except:
        raise ValueError('Invalid Coordinates')
        
    return lat, lon

def parseDMSStringSingle(str):
    '''Parse a single coordinate either DMS or decimal degrees.
    It simply returns the value but doesn't maintain any knowledge
    as to whether it is latitude or longitude'''
    str = str.strip().upper()
    try:
        if re.search(r"[NSEW]", str) == None:
            coord = float(str)
        else:
            # We should have a DMS coordinate
            if re.search(r'[NSEW]\s*\d+', str) == None:
                # We assume that the cardinal directions occur after the digits
                m = re.findall(r'(.+)\s*([NSEW])', str)
                if len(m) != 1 or len(m[0]) != 2:
                    raise ValueError('Invalid DMS Coordinate')
                coord = parseDMS(m[0][0], m[0][1])
            else:
                # The cardinal directions occur at the beginning of the digits
                m = re.findall(r'([NSEW])\s*(.+)', str)
                if len(m) != 1 or len(m[0]) != 2:
                    raise ValueError('Invalid DMS Coordinate')
                coord = parseDMS(m[0][1], m[0][0])
    except:
        raise ValueError('Invalid Coordinates')
    return coord

def parseDMS(str, hemisphere):
    '''Parse a DMS formatted string.'''
    str = re.sub(r"[^\d.]+", " ", str).strip()
    parts = re.split(r'[\s]+', str)
    dmslen = len(parts)
    if dmslen == 3:
        deg = float(parts[0]) + float(parts[1])/60.0 + float(parts[2])/3600.0
    elif dmslen == 2:
        deg = float(parts[0]) + float(parts[1])/60.0
    elif dmslen == 1:
        dms = parts[0]
        if hemisphere == 'N' or hemisphere == 'S':
            dms = '0' + dms
        # Find the length up to the first decimal
        l = dms.find('.')
        if l == -1:
            # No decimal point found so just return the length of the string
            l = len(dms)
        if l >= 7:
            deg = float(dms[0:3]) + float(dms[3:5]) / 60.0 + float(dms[5:]) / 3600.0
        elif l == 6: # A leading 0 was left off but we can still work with 6 digits
             deg = float(dms[0:2]) + float(dms[2:4]) / 60.0 + float(dms[4:]) / 3600.0
        elif l == 5:
            deg = float(dms[0:3]) + float(dms[3:]) / 60.0
        elif l == 4: # Leading 0's were left off
            deg = float(dms[0:2]) + float(dms[2:]) / 60.0
        else:
            deg = float(dms)
    else:
        raise ValueError('Invalid DMS Coordinate')
    if hemisphere == 'S' or hemisphere == 'W':
        deg = -deg
    return deg
