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
import math
import re
from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QCoreApplication

epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

def tr(string):
    return QCoreApplication.translate('@default', string)

def formatMgrsString(mgrs, add_spaces=False):
    if add_spaces:
        gzd = mgrs[0:3].strip()
        gsid = mgrs[3:5]
        ns = mgrs[5:].strip()
        if len(mgrs) > 5:
            l = int(len(ns) / 2)
            easting = ns[0:l]
            northing = ns[l:]
            s = '{} {} {} {}'.format(gzd, gsid, easting, northing)
        else:
            s = '{} {}'.format(gzd, gsid)
        return(s)
    else:
        return(mgrs.strip())

def formatDmsString(lat, lon, dms_mode=0, prec=0, order=0, delimiter=', ', useDmsSpace=True, padZeros=False, nsewInFront=False):
    '''Return a DMS formated string.'''
    if order == 0:  # Y, X or Lat, Lon
        return convertDD2DMS(lat, True, dms_mode, prec, useDmsSpace, padZeros, nsewInFront) + str(delimiter) + convertDD2DMS(lon, False, dms_mode, prec, useDmsSpace, padZeros, nsewInFront)
    else:  # X, Y or Lon, Lat
        return convertDD2DMS(lon, False, dms_mode, prec, useDmsSpace, padZeros, nsewInFront) + str(delimiter) + convertDD2DMS(lat, True, dms_mode, prec, useDmsSpace, padZeros, nsewInFront)

def convertDD2DMS(coord, islat, dms_mode, prec, useDmsSpace=True, padZeros=False, nsewInFront=False):
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
    dmsSpace = " " if useDmsSpace else ""
    zeros = 1 if padZeros else 0 #this will be used for padding
    dextra = 1 if prec else 0
    coord = math.fabs(coord)
    deg = math.floor(coord)
    dmin = (coord - deg) * 60.0
    min = math.floor(dmin)
    sec = (dmin - min) * 60.0
    if prec == 0:
        dprec = 2
    else:
        dprec = prec + 3
    s = ""
    if dms_mode==0: # D M S
        # Properly handle rounding based on the digit precision
        d = "{:.{prec}f}".format(sec, prec=prec)
        if float(d) == 60:
            min += 1
            sec = 0
            if min == 60:
                deg += 1
                min = 0
        if islat:
            s = "{:0{}.0f}\xB0{}{:0{}.0f}\'{}{:0{}.{prec}f}\"".format(deg, zeros*2, dmsSpace, min, zeros*2, dmsSpace, sec, prec+zeros*2+dextra, prec=prec)
        else:
            s = "{:0{}.0f}\xB0{}{:0{}.0f}\'{}{:0{}.{prec}f}\"".format(deg, zeros*3, dmsSpace, min, zeros*2, dmsSpace, sec, prec+zeros*2+dextra, prec=prec)
        if nsewInFront:
            s = "{}{}{}".format(unit, dmsSpace, s)
        else:
            s = "{}{}{}".format(s, dmsSpace, unit)
    elif dms_mode==1: # DDMMS
        # Properly handle rounding based on the digit precision
        d = "{:.{prec}f}".format(sec, prec=prec)
        if float(d) == 60:
            min += 1
            sec = 0
            if min == 60:
                deg += 1
                min = 0
        if islat:
            s = "{:02.0f}{:02.0f}{:0{dprec}.{prec}f}".format(deg, min, sec, dprec=dprec, prec=prec)
        else:
            s = "{:03.0f}{:02.0f}{:0{dprec}.{prec}f}".format(deg, min, sec, dprec=dprec, prec=prec)
        if nsewInFront:
            s = "{}{}".format(unit, s)
        else:
            s = "{}{}".format(s, unit)
    elif dms_mode==2: # DM.MM
        d = "{:.{prec}f}".format(dmin, prec=prec)
        if float(d) == 60:
            deg += 1
            dmin = 0
        if islat:
            s = "{:0{}.0f}\xB0{}{:0{}.0{prec}f}\'".format(deg, zeros*2, dmsSpace, dmin, prec+zeros*2+dextra, prec=prec)
        else:
            s = "{:0{}.0f}\xB0{}{:0{}.0{prec}f}\'".format(deg, zeros*3, dmsSpace, dmin, prec+zeros*2+dextra, prec=prec)
        if nsewInFront:
            s = "{}{}{}".format(unit, dmsSpace, s)
        else:
            s = "{}{}{}".format(s, dmsSpace, unit)
    return(s)

def parseDMSString(str, order=0):
    '''Parses a pair of coordinates that are in the order of
    "latitude, longitude". The string can be in DMS or decimal
    degree notation. If order is 0 then then decimal coordinates are assumed to
    be in Lat Lon order otherwise they are in Lon Lat order. For DMS coordinates
    it does not matter the order.'''
    str = str.strip().upper()  # Make it all upper case
    try:
        if re.search(r"[NSEW]", str) is None:
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
            if re.search(r'[NSEW]\s*\d+.+[NSEW]\s*\d+', str) is None:
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

    except Exception:
        raise ValueError('Invalid Coordinates')

    return lat, lon

def parseDMSStringSingle(str):
    '''Parse a single coordinate either DMS or decimal degrees.
    It simply returns the value but doesn't maintain any knowledge
    as to whether it is latitude or longitude'''
    str = str.strip().upper()
    try:
        if re.search(r"[NSEW]", str) is None:
            coord = float(str)
        else:
            # We should have a DMS coordinate
            if re.search(r'[NSEW]\s*\d+', str) is None:
                # We assume that the cardinal directions occur after the digits
                m = re.findall(r'([\d.]+)\s*([NSEW])', str)
                if len(m) != 1 or len(m[0]) != 2:
                    raise ValueError('Invalid DMS Coordinate')
                coord = parseDMS(m[0][0], m[0][1])
            else:
                # The cardinal directions occur at the beginning of the digits
                m = re.findall(r'([NSEW])\s*([\d.]+)', str)
                if len(m) != 1 or len(m[0]) != 2:
                    raise ValueError('Invalid DMS Coordinate')
                coord = parseDMS(m[0][1], m[0][0])
    except Exception:
        raise ValueError('Invalid Coordinates')
    return coord

def parseDMS(str, hemisphere):
    '''Parse a DMS formatted string.'''
    str = re.sub(r"[^\d.]+", " ", str).strip()
    parts = re.split(r'[\s]+', str)
    dmslen = len(parts)
    if dmslen == 3:
        deg = float(parts[0]) + float(parts[1]) / 60.0 + float(parts[2]) / 3600.0
    elif dmslen == 2:
        deg = float(parts[0]) + float(parts[1]) / 60.0
    elif dmslen == 1:
        dms = parts[0]
        if hemisphere == 'N' or hemisphere == 'S':
            dms = '0' + dms
        # Find the length up to the first decimal
        ll = dms.find('.')
        if ll == -1:
            # No decimal point found so just return the length of the string
            ll = len(dms)
        if ll >= 7:
            deg = float(dms[0:3]) + float(dms[3:5]) / 60.0 + float(dms[5:]) / 3600.0
        elif ll == 6:  # A leading 0 was left off but we can still work with 6 digits
            deg = float(dms[0:2]) + float(dms[2:4]) / 60.0 + float(dms[4:]) / 3600.0
        elif ll == 5:
            deg = float(dms[0:3]) + float(dms[3:]) / 60.0
        elif ll == 4:  # Leading 0's were left off
            deg = float(dms[0:2]) + float(dms[2:]) / 60.0
        else:
            deg = float(dms)
    else:
        raise ValueError('Invalid DMS Coordinate')
    if hemisphere == 'S' or hemisphere == 'W':
        deg = -deg
    return deg
