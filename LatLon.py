import sys, math, re, string
from qgis.core import *

class LatLon():
    '''LatLon is a class of useful functions to do conversions handle
    other coordinate functions.'''
    def __init__(self):
        '''Initialize the coordinates to (0,0) with a precision of 2'''
        self.lat = 0.0
        self.lon = 0.0
        self.precision = 2
        self.valid = True
        
    def setCoord(self, lat, lon):
        '''Set the coordinate to the LatLon class. It also sets a flag
        to indicate whether it was valid.'''
        try:
            self.lat = float(lat)
            if self.lat > 90.0 or self.lat < -90.0:
                self.valid = False
                return
            # Normalize the Longitude between -180 and 180 degrees
            self.lon = LatLon.normalizeLongitude(float(lon))
            self.valid = True
        except:
            self.valid = False
        return self.valid
            
    def isValid(self):
        return self.valid
        
    @staticmethod
    def normalizeLongitude(num):
        '''Normalize the Longitude between -180 and 180 degrees'''
        num += 180.0
        num = math.fmod(num, 360.0)
        if num < 0:
            num += 180
        else:
            num -= 180
        return num

    def setPrecision(self, precision):
        '''Set the precision for string representation of the coordinate.'''
        self.precision = precision
        
    def convertDD2DMS(self, coord, islat, isdms):
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
        if self.precision == 0:
            if isdms:
                s = "%d\xB0%d'%.0f\""%(deg, min, sec)
            else:
                if islat:
                    s = "%02d%02d%02.0f"%(deg, min, sec)
                else:
                    s = "%03d%02d%02.0f"%(deg, min, sec)
        else:
            if isdms:
                fmtstr = "%%d\xB0%%d'%%.%df\""%(self.precision)
            else:
                if islat:
                    fmtstr = "%%02d%%02d%%0%d.%df"%(self.precision+3, self.precision)
                else:
                    fmtstr = "%%03d%%02d%%0%d.%df"%(self.precision+3, self.precision)
            s = fmtstr%(deg, min, sec)
        if isdms:
            s += " "+unit
        else:
            s += unit
        return(s)
        
    def getDMS(self, delimiter=', '):
        '''Return a DMS formated string.'''
        if self.valid:
            return self.convertDD2DMS(self.lat, True, True) + str(delimiter) + self.convertDD2DMS(self.lon, False, True)
        else:
            return None

    def getDDMMSS(self, delimiter=', '):
        '''Return a DDMMSS formatted string.'''
        if self.valid:
            return self.convertDD2DMS(self.lat, True, False) + str(delimiter) + self.convertDD2DMS(self.lon, False, False)
        else:
            return None
         
    @staticmethod
    def parseDMS(str, hemisphere):
        '''Parse a DMS formatted string.'''
        str = re.sub("[^\d.]+", " ", str).strip()
        parts = re.split('[\s]+', str)
        dmslen = len(parts)
        if dmslen == 3:
            deg = float(parts[0]) + float(parts[1])/60.0 + float(parts[2])/3600.0
        elif dmslen == 2:
            deg = float(parts[0]) + float(parts[1])/60.0
        elif dmslen == 1:
            dms = parts[0]
            if hemisphere == 'N' or hemisphere == 'S':
                dms = '0' + dms
            if len(dms) >= 7:
                deg = float(dms[0:3]) + float(dms[3:5]) / 60.0 + float(dms[5:]) / 3600.0
            elif len(dms) == 5:
                deg = float(dms[0:3]) + float(dms[3:5]) / 60.0
            else:
                deg = float(dms[0:3])
        else:
            raise ValueError('Invalid DMS Coordinate')
        if hemisphere == 'S' or hemisphere == 'W':
            deg = -deg
        return deg
    
    @staticmethod
    def parseDMSStringSingle(str):
        '''Parse a single coordinate either DMS or decimal degrees.
        It simply returns the value but doesn't maintain any knowledge
        as to whether it is latitude or longitude'''
        str = str.strip().upper()
        try:
            if re.search("[NSEW\xb0]", str) == None:
                coord = float(str)
            else:
                m = re.findall('(.+)\s*([NSEW])', str)
                if len(m) != 1 or len(m[0]) != 2:
                    raise ValueError('Invalid DMS Coordinate')
                coord = LatLon.parseDMS(m[0][0], m[0][1])
        except:
            raise ValueError('Invalid Coordinates')
        return coord
    
    @staticmethod
    def parseDMSString(str):
        '''Parses a pair of coordinates that are in the order of
        "latitude, longitude". The string can be in DMS or decimal
        degree notation.'''
        str = str.strip().upper()
        try: 
            if re.search("[NSEW\xb0]", str) == None:
                # There were no annotated dms coordinates so assume decimal degrees
                coords = re.split('[\s,;:]+', str, 1)
                if len(coords) != 2:
                    raise ValueError('Invalid Coordinates')
                lat = float(coords[0])
                lon = float(coords[1])
            else:   
                # We should have a DMS coordinate
                m = re.findall('(.+)\s*([NS])[\s,;:]+(.+)\s*([EW])', str)
                if len(m) != 1 or len(m[0]) != 4:
                    raise ValueError('Invalid DMS Coordinate')
                lat = LatLon.parseDMS(m[0][0], m[0][1])
                lon = LatLon.parseDMS(m[0][2], m[0][3])
        except:
            raise ValueError('Invalid Coordinates')
            
        return lat, lon
