import sys, math, re, string
from qgis.core import QgsPoint

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
        
    def getDMSLonLatOrder(self, delimiter=', '):
        '''Return a DMS formated string.'''
        if self.valid:
            return self.convertDD2DMS(self.lon, False, True) + str(delimiter) + self.convertDD2DMS(self.lat, True, True)
        else:
            return None

    def getDDMMSS(self, delimiter=', '):
        '''Return a DDMMSS formatted string.'''
        if self.valid:
            return self.convertDD2DMS(self.lat, True, False) + str(delimiter) + self.convertDD2DMS(self.lon, False, False)
        else:
            return None

    def getDDMMSSLonLatOrder(self, delimiter=', '):
        '''Return a DDMMSS formatted string.'''
        if self.valid:
            return self.convertDD2DMS(self.lon, False, False) + str(delimiter) + self.convertDD2DMS(self.lat, True, False)
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
            # Find the length up to the first decimal
            l = dms.find('.')
            if l == -1:
                # No decimal point found so just return the length of the string
                l = len(dms)
            if l >= 7:
                deg = float(dms[0:3]) + float(dms[3:5]) / 60.0 + float(dms[5:]) / 3600.0
            elif l == 5:
                deg = float(dms[0:3]) + float(dms[3:]) / 60.0
            else:
                deg = float(dms)
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
            if re.search("[NSEW]", str) == None:
                coord = float(str)
            else:
                # We should have a DMS coordinate
                if re.search('[NSEW]\s*\d+', str) == None:
                    # We assume that the cardinal directions occur after the digits
                    m = re.findall('(.+)\s*([NSEW])', str)
                    if len(m) != 1 or len(m[0]) != 2:
                        raise ValueError('Invalid DMS Coordinate')
                    coord = LatLon.parseDMS(m[0][0], m[0][1])
                else:
                    # The cardinal directions occur at the beginning of the digits
                    m = re.findall('([NSEW])\s*(.+)', str)
                    if len(m) != 1 or len(m[0]) != 2:
                        raise ValueError('Invalid DMS Coordinate')
                    coord = LatLon.parseDMS(m[0][1], m[0][0])
        except:
            raise ValueError('Invalid Coordinates')
        return coord
    
    @staticmethod
    def parseDMSString(str, order=0):
        '''Parses a pair of coordinates that are in the order of
        "latitude, longitude". The string can be in DMS or decimal
        degree notation. If order is 0 then then decimal coordinates are assumed to
        be in Lat Lon order otherwise they are in Lon Lat order. For DMS coordinates
        it does not matter the order.'''
        str = str.strip().upper() # Make it all upper case 
        try: 
            if re.search("[NSEW]", str) == None:
                # There were no annotated dms coordinates so assume decimal degrees
                # Remove any characters that are not digits and decimal
                str = re.sub("[^\d.+-]+", " ", str).strip()
                coords = re.split('\s+', str, 1)
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
                if re.search('[NSEW]\s*\d+.+[NSEW]\s*\d+', str) == None:
                    # We assume that the cardinal directions occur after the digits
                    m = re.findall('(.+)\s*([NS])[\s,;:]*(.+)\s*([EW])', str)
                    if len(m) != 1 or len(m[0]) != 4:
                        # This is either invalid or the coordinates are ordered by lon lat
                        m = re.findall('(.+)\s*([EW])[\s,;:]*(.+)\s*([NS])', str)
                        if len(m) != 1 or len(m[0]) != 4:
                            # Now we know it is invalid
                            raise ValueError('Invalid DMS Coordinate')
                        else:
                            # The coordinates were in lon, lat order
                            lon = LatLon.parseDMS(m[0][0], m[0][1])
                            lat = LatLon.parseDMS(m[0][2], m[0][3])
                    else:
                        # The coordinates are in lat, lon order
                        lat = LatLon.parseDMS(m[0][0], m[0][1])
                        lon = LatLon.parseDMS(m[0][2], m[0][3])
                else:
                    # The cardinal directions occur at the beginning of the digits
                    m = re.findall('([NS])\s*(\d+.*?)[\s,;:]*([EW])(.+)', str)
                    if len(m) != 1 or len(m[0]) != 4:
                        # This is either invalid or the coordinates are ordered by lon lat
                        m = re.findall('([EW])\s*(\d+.*?)[\s,;:]*([NS])(.+)', str)
                        if len(m) != 1 or len(m[0]) != 4:
                            # Now we know it is invalid
                            raise ValueError('Invalid DMS Coordinate')
                        else:
                            # The coordinates were in lon, lat order
                            lon = LatLon.parseDMS(m[0][1], m[0][0])
                            lat = LatLon.parseDMS(m[0][3], m[0][2])
                    else:
                        # The coordinates are in lat, lon order
                        lat = LatLon.parseDMS(m[0][1], m[0][0])
                        lon = LatLon.parseDMS(m[0][3], m[0][2])
        
        except:
            raise ValueError('Invalid Coordinates')
            
        return lat, lon
    
    @staticmethod
    def distanceTo(lat1, lon1, lat2, lon2, R=6371000.0):
        '''Compute the distance between two points. The average earth
           radius is 6371000 meters. The returned distance is in the same
           units as R which by default is meters'''
        phi1 = math.radians(lat1)
        lambda1 = math.radians(lon1)
        phi2 = math.radians(lat2)
        lambda2 = math.radians(lon2)
        deltaphi = phi2 - phi1
        deltalambda = lambda2 - lambda1
        a = (math.sin(deltaphi/2.0) * math.sin(deltaphi/2.0)
              + math.cos(phi1) * math.cos(phi2)
              * math.sin(deltalambda/2.0) * math.sin(deltalambda/2.0))
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))
        d = R * c
        return d
    
    @staticmethod
    def intermediatePointTo(lat1, lon1, lat2, lon2, fraction):
        '''Return the fractional point between [lat1, lon1] and [lat2, lon2]
           Coordinates are in degrees and fraction is between 0 and 1'''
        phi1 = math.radians(lat1)
        lambda1 = math.radians(lon1)
        phi2 = math.radians(lat2)
        lambda2 = math.radians(lon2)
        sinphi1 = math.sin(phi1)
        cosphi1 = math.cos(phi1)
        sinlambda1 = math.sin(lambda1)
        coslambda1 = math.cos(lambda1)
        sinphi2 = math.sin(phi2)
        cosphi2 = math.cos(phi2)
        sinlambda2 = math.sin(lambda2)
        coslambda2 = math.cos(lambda2)

        # distance between points
        deltaphi = phi2 - phi1
        deltalambda = lambda2 - lambda1
        a = math.sin(deltaphi/2.0) * math.sin(deltaphi/2.0) + math.cos(phi1) * math.cos(phi2) * math.sin(deltalambda/2.0) * math.sin(deltalambda/2.0)
        delta = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))

        A = math.sin((1.0-fraction)*delta) / math.sin(delta)
        B = math.sin(fraction*delta) / math.sin(delta)

        x = A * cosphi1 * coslambda1 + B * cosphi2 * coslambda2
        y = A * cosphi1 * sinlambda1 + B * cosphi2 * sinlambda2
        z = A * sinphi1 + B * sinphi2

        phi3 = math.atan2(z, math.sqrt(x*x + y*y))
        lambda3 = math.atan2(y, x)

        # Returns lat, lon and normalize lon from -180 to 180 degrees
        return math.degrees(phi3), ((math.degrees(lambda3)+540.0)%360.0 - 180.0)
    
    @staticmethod
    def getPointsOnLine(lat1, lon1, lat2, lon2, minSegLength=1000.0, maxNodes=500):
        '''Get points along a great circle line between the two coordinates.
           minSegLength is the minimum segment length in meters before a new
           node point is created. maxNodes is the maximum number of points on
           the line to create.'''
        dist = LatLon.distanceTo(lat1, lon1, lat2, lon2)
        numPoints = int(dist / minSegLength)
        if numPoints > maxNodes:
            numPoints = maxNodes
        pts = [QgsPoint(lon1, lat1)]
        f = 1.0 / (numPoints - 1.0)
        i = 1
        while i < numPoints-1:
            newlat, newlon = LatLon.intermediatePointTo(lat1, lon1, lat2, lon2, f * i)
            pts.append(QgsPoint(newlon, newlat))
            i += 1
        pts.append(QgsPoint(lon2, lat2))
        return pts
        

    # distance s is in meters
    @staticmethod
    def destinationPointVincenty(lat, lon, brng, s):
        a = 6378137.0
        b = 6356752.3142
        f = 1.0/298.257223563
        alpha1 = math.radians(brng)
        sinAlpha1 = math.sin(alpha1)
        cosAlpha1 = math.cos(alpha1)
        tanU1 = (1.0 - f) * math.tan(math.radians(lat))
        cosU1 = 1.0 / math.sqrt(1.0 + tanU1*tanU1)
        sinU1 = tanU1 * cosU1
        sigma1 = math.atan2(tanU1, cosAlpha1)
        sinAlpha = cosU1 * sinAlpha1
        cosSqAlpha = 1.0 - sinAlpha*sinAlpha
        uSq = cosSqAlpha * (a*a - b*b) / (b*b)
        A = 1.0 + uSq / 16384.0 * (4096.0+uSq*(-768.0+uSq*(320.0-175.0*uSq)))
        B = uSq / 1024.0 * (256.0+uSq*(-128.0+uSq*(74.0-47.0*uSq)))
        
        sigma = s / (b*A)
        sigmaP = 2.0 * math.pi
        
        while math.fabs(sigma-sigmaP) > 1e-12:
            cos2SigmaM = math.cos(2.0 * sigma1 + sigma)
            sinSigma = math.sin(sigma)
            cosSigma = math.cos(sigma)
            deltaSigma = B * sinSigma * (cos2SigmaM+B/4.0*(cosSigma*(-1.0+2.0*cos2SigmaM*cos2SigmaM) - B/6.0*cos2SigmaM*(-3.0+4.0*sinSigma*sinSigma)*(-3.0+4.0*cos2SigmaM*cos2SigmaM)))
            sigmaP = sigma
            sigma = s / (b*A) + deltaSigma
        
        tmp = sinU1 * sinSigma - cosU1*cosSigma*cosAlpha1
        lat2 = math.atan2(sinU1*cosSigma + cosU1*sinSigma*cosAlpha1,
            (1.0 - f)*math.sqrt(sinAlpha*sinAlpha + tmp*tmp))
        
        lambdav = math.atan2(sinSigma*sinAlpha1, cosU1*cosSigma - sinU1*sinSigma*cosAlpha1)
        C = f / 16.0 * cosSqAlpha*(4.0+f*(4.0-3.0*cosSqAlpha))
        L = lambdav - (1.0-C) * f * sinAlpha * (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1.0+2.0*cos2SigmaM*cos2SigmaM)))
        
        return math.degrees(lat2), lon + math.degrees(L)
    
    # bearing is in degrees and distances are in meters
    @staticmethod
    def getLineCoords(lat, lon, bearing, distance, maxSegments, minLength):
        pts = []
        seglen = distance / maxSegments
        if seglen < minLength:
            seglen = minLength
        pts.append(QgsPoint(lon, lat))
        pdist = seglen
        while pdist < distance:
            newlat, newlon = LatLon.destinationPointVincenty(lat, lon, bearing, pdist)
            pts.append(QgsPoint(newlon, newlat))
            pdist += seglen
            
        newlat, newlon = LatLon.destinationPointVincenty(lat, lon, bearing, distance)
        pts.append(QgsPoint(newlon, newlat))
        return pts
    
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
            '''if (azinc == 0.0) and (center_lat + rad > PI_2):
                tmplat = math.degrees(math.pi - (center_lat + rad))
                tmplon = math.degrees(center_lon + math.pi)
                
            if (azinc == math.pi) and (center_lat - rad < -1.0*PI_2):
                tmplat = math.degrees(-1.0 * math.pi - (center_lat - rad))
                tmplon = math.degrees(center_lon + math.pi)'''
                       
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
