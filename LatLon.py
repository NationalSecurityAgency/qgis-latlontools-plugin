import sys, math, re, string
from qgis.core import *

class LatLon():
    def __init__(self):
        self.lat = 0.0
        self.lon = 0.0
        self.precision = 2
        self.valid = True
        
    def setCoord(self, lat, lon):
        try:
            self.lat = float(lat)
            if self.lat > 90.0 or self.lat < -90.0:
                self.valid = False
                return
            # Normalize the Longitude
            self.lon = LatLon.normalizeLongitude(float(lon))
            self.valid = True
        except:
            self.valid = False
            
    def isValid(self):
        return self.valid
        
    @staticmethod
    def normalizeLongitude(num):
        num += 180.0
        num = math.fmod(num, 360.0)
        if num < 0:
            num += 180
        else:
            num -= 180
        return num

    def setPrecision(self, precision):
        self.precision = precision
        
    def convertDD2DMS(self, coord, islat, isdms):
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
        if self.valid:
            return self.convertDD2DMS(self.lat, True, True) + str(delimiter) + self.convertDD2DMS(self.lon, False, True)
        else:
            return None

    def getDDMMSS(self, delimiter=', '):
        if self.valid:
            return self.convertDD2DMS(self.lat, True, False) + str(delimiter) + self.convertDD2DMS(self.lon, False, False)
        else:
            return None
         
    @staticmethod
    def parseDMS(str, hemisphere):
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
        
    @staticmethod
    def getEllipseCoords(lat, lon, sma, smi, azi):
        TPI = math.pi * 2.0
        PI_2 = math.pi / 2.0
        DG2NM = 60.0 # Degrees on the Earth's Surface to NM
    
        c = []
        cnt = 0
        # If either the semi major or minor axis are tiny,
        # create a very small ellipse instead (0.0005 NB = 3 ft).
        # Do not let sma/smi go through with Zero values!!
        if smi < 0.0005: smi = 0.0005
        if sma < 0.0005: sma = 0.0005
        center_lat = math.radians(lat)
        center_lon = math.radians(lon)
        sma = math.radians(sma / DG2NM)
        smi = math.radians(smi / DG2NM)
        azi = math.radians(azi)
        size = 512
        angle = 18.0 * smi / sma
        if angle < 1.0:
            minimum = angle
        else:
            minimum = 1.0
            
        # maxang = math.pi / 6 * min(1.0, 18.0 * smi/sma)
        maxang = math.pi / 6 * minimum
        while azi < 0:
            azi += TPI
        while azi > math.pi:
            azi -= math.pi
        slat = math.sin(center_lat)
        clat = math.cos(center_lat)
        ab = sma * smi
        a2 = sma * sma
        b2 = smi * smi
        
        delta = ab * math.pi / 30.0
        o = azi
        while True:
            sino = math.sin(o - azi)
            coso = math.cos(o - azi)
            
            if o > math.pi and o < TPI:
                sgn = -1.0
                azinc = TPI - o
            else:
                sgn = 1.0
                azinc = o
            
            rad = ab / math.sqrt(a2 * sino * sino + b2 * coso * coso)
            sinr = math.sin(rad)
            cosr = math.cos(rad)
            
            acos_val = cosr * slat + sinr * clat * math.cos(azinc)
            
            if acos_val > 1.0:
                acos_val = 1.0
            elif acos_val < -1.0:
                acos_val = -1.0
                
            tmplat = math.acos(acos_val)
            
            acos_val = (cosr - slat * math.cos(tmplat)) / (clat * math.sin(tmplat))
            
            if acos_val > 1.0:
                acos_val = 1.0
            elif acos_val < -1.0:
                acos_val = -1.0
            
            tmplon = math.acos(acos_val)
            tmplat = math.degrees(PI_2 - tmplat)
            tmplon = math.degrees(center_lon + sgn * tmplon)
            
            # Check for wrapping over north pole
            if (azinc == 0.0) and (center_lat + rad > PI_2):
                tmplat = math.degrees(math.pi - (center_lat + rad))
                tmplon = math.degrees(center_lon + math.pi)
                
            if (azinc == math.pi) and (center_lat - rad < -1.0*PI_2):
                tmplat = math.degrees(-1.0 * math.pi - (center_lat - rad))
                tmplon = math.degrees(center_lon + math.pi)
            
            # Check for wrapping over the date line
            if tmplon < -180.0:
                tmplon += 360.0
            if tmplon > 180.0:
                tmplon -= 360.0
            
            c.append( QgsPoint(tmplon, tmplat) )
            cnt += 1
            delo = delta / (rad * rad)
            if maxang < delo:
                delo = maxang
            o += delo
            
            if (o >= TPI + azi + delo / 2.0) or (cnt >= size):
                break
        
        if c[cnt-1].x() != c[0].x() or c[cnt-1].y() != c[0].y():
            c[cnt-1].set(c[0].x(), c[0].y())
        
        return c