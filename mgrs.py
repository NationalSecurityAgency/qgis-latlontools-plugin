# -*- coding: utf-8 -*-
"""
***************************************************************************
    mgrs.py
    ---------------------
    Date                 : August 2016, October 2019
    Author               : Alex Bruy, Planet Federal
    Copyright            : (C) 2016 Boundless, http://boundlessgeo.com
                         : (C) 2019 Planet Inc, https://planet.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
from builtins import str
from builtins import range
__author__ = 'Planet Federal'
__date__ = 'October 2019'
__copyright__ = '(C) 2019 Planet Inc, https://planet.com'

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'


import os
import sys
import re
import math
import itertools
import logging

HAVE_OSR = False
# Force using proj for transformations by setting MGRSPY_USE_PROJ env var
if os.environ.get('MGRSPY_USE_PROJ', None) is None:
    try:
        from osgeo import osr
        HAVE_OSR = True
    except ImportError:
        pass

PYPROJ_VER = 0
if not HAVE_OSR:
    try:
        from pyproj import Transformer, CRS, __version__ as pyproj_ver
        PYPROJ_VER = 2
        if float(pyproj_ver[:3]) < 2.2:
            raise Exception('Unsupported pyproj version (need >= 2.2)')
    except ImportError:
        from pyproj import Proj, transform, __version__ as pyproj_ver
        if float(pyproj_ver[:3]) < 1.9 or int(pyproj_ver[4]) < 5:
            raise Exception('Unsupported pyproj version (need >= 1.9.5)')
        PYPROJ_VER = 1

LOG_LEVEL = os.environ.get('PYTHON_LOG_LEVEL', 'WARNING').upper()
FORMAT = "%(levelname)s [%(name)s:%(lineno)s  %(funcName)s()] %(message)s"
logging.basicConfig(level=LOG_LEVEL, format=FORMAT)
log = logging.getLogger(__name__)

BADLY_FORMED = \
    'An MGRS string error: string too long, too short, or badly formed'

# Whether to add the extra half-multiplier to UTM coords per precision,
# added in geotrans3.8
GEOTRANS_HALFMULTI = False

ALPHABET = {l: c for c, l in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}

ONEHT = 100000.0
TWOMIL = 2000000.0

MAX_PRECISION = 5         # Maximum precision of easting & northing
MIN_EAST_NORTH = 0
MAX_EAST_NORTH = 4000000

# letter,
# 2nd letter range - low,
# 2nd letter range - high,
# 3rd letter range - high (UPS),
# false easting based on 2nd letter,
# false northing based on 3rd letter
UPS_CONSTANTS = {
    0: (ALPHABET['A'], ALPHABET['J'], ALPHABET['Z'], ALPHABET['Z'],
        800000.0, 800000.0),
    1: (ALPHABET['B'], ALPHABET['A'], ALPHABET['R'], ALPHABET['Z'],
        2000000.0, 800000.0),
    2: (ALPHABET['Y'], ALPHABET['J'], ALPHABET['Z'], ALPHABET['P'],
        800000.0, 1300000.0),
    3: (ALPHABET['Z'], ALPHABET['A'], ALPHABET['J'], ALPHABET['P'],
        2000000.0, 1300000.0)
}

# letter, minimum northing, upper latitude, lower latitude, northing offset
LATITUDE_BANDS = [(ALPHABET['C'], 1100000.0, -72.0, -80.5, 0.0),
                  (ALPHABET['D'], 2000000.0, -64.0, -72.0, 2000000.0),
                  (ALPHABET['E'], 2800000.0, -56.0, -64.0, 2000000.0),
                  (ALPHABET['F'], 3700000.0, -48.0, -56.0, 2000000.0),
                  (ALPHABET['G'], 4600000.0, -40.0, -48.0, 4000000.0),
                  (ALPHABET['H'], 5500000.0, -32.0, -40.0, 4000000.0),
                  (ALPHABET['J'], 6400000.0, -24.0, -32.0, 6000000.0),
                  (ALPHABET['K'], 7300000.0, -16.0, -24.0, 6000000.0),
                  (ALPHABET['L'], 8200000.0, -8.0, -16.0, 8000000.0),
                  (ALPHABET['M'], 9100000.0, 0.0, -8.0, 8000000.0),
                  (ALPHABET['N'], 0.0, 8.0, 0.0, 0.0),
                  (ALPHABET['P'], 800000.0, 16.0, 8.0, 0.0),
                  (ALPHABET['Q'], 1700000.0, 24.0, 16.0, 0.0),
                  (ALPHABET['R'], 2600000.0, 32.0, 24.0, 2000000.0),
                  (ALPHABET['S'], 3500000.0, 40.0, 32.0, 2000000.0),
                  (ALPHABET['T'], 4400000.0, 48.0, 40.0, 4000000.0),
                  (ALPHABET['U'], 5300000.0, 56.0, 48.0, 4000000.0),
                  (ALPHABET['V'], 6200000.0, 64.0, 56.0, 6000000.0),
                  (ALPHABET['W'], 7000000.0, 72.0, 64.0, 6000000.0),
                  (ALPHABET['X'], 7900000.0, 84.5, 72.0, 6000000.0)]


class MgrsException(Exception):
    pass


def _log_proj_crs(proj_crs, proj_desc='', espg=''):
    if proj_desc:
        proj_desc = '{0} '.format(str(proj_desc))
    if espg:
        espg = 'espg:{0} '.format(str(espg))
    definition = ''
    if HAVE_OSR:
        definition = proj_crs.ExportToPrettyWkt()
    if PYPROJ_VER == 1:
        definition = proj_crs.definition_string()
    elif PYPROJ_VER == 2:
        definition = proj_crs.to_wkt(pretty=True)
    log.debug('{0}proj: {1}{2}{3}'.format(
        proj_desc, espg, os.linesep, definition))


def _transform_proj(x1, y1, epsg_src, epsg_dst, polar=False):
    if PYPROJ_VER == 1:
        proj_src = Proj(init='epsg:{0}'.format(epsg_src))
        _log_proj_crs(proj_src, proj_desc='src', espg=epsg_src)
        proj_dst = Proj(init='epsg:{0}'.format(epsg_dst))
        _log_proj_crs(proj_dst, proj_desc='dst', espg=epsg_dst)
        x2, y2 = transform(proj_src, proj_dst, x1, y1)
    elif PYPROJ_VER == 2:
        # With PROJ 6+ input axis ordering needs honored per projection, even
        #   though always_xy should fix it (doesn't seem to work for UPS)
        crs_src = CRS.from_epsg(epsg_src)
        _log_proj_crs(crs_src, proj_desc='src', espg=epsg_src)
        crs_dst = CRS.from_epsg(epsg_dst)
        _log_proj_crs(crs_dst, proj_desc='dst', espg=epsg_dst)
        ct = Transformer.from_crs(crs_src, crs_dst, always_xy=(not polar))
        if polar:
            y2, x2 = ct.transform(y1, x1)
        else:
            x2, y2 = ct.transform(x1, y1)
    else:
        raise MgrsException('pyproj version unsupported')

    return x2, y2


def _transform_osr(x1, y1, epsg_src, epsg_dst, polar=False):
    src = osr.SpatialReference()
    # Check if we are using osgeo.osr linked against PROJ 6+
    # If so, input axis ordering needs honored per projection, even though
    #   OAMS_TRADITIONAL_GIS_ORDER should fix it (doesn't seem to work for UPS)
    # See GDAL/OGR migration guide for 2.4 to 3.0
    # https://github.com/OSGeo/gdal/blob/master/gdal/MIGRATION_GUIDE.TXT and
    # https://trac.osgeo.org/gdal/wiki/rfc73_proj6_wkt2_srsbarn#Axisorderissues
    osr_proj6 = hasattr(src, 'SetAxisMappingStrategy')
    if not polar and osr_proj6:
        src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    src.ImportFromEPSG(epsg_src)
    _log_proj_crs(src, proj_desc='src', espg=epsg_src)
    dst = osr.SpatialReference()
    if not polar and osr_proj6:
        dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    dst.ImportFromEPSG(epsg_dst)
    _log_proj_crs(dst, proj_desc='dst', espg=epsg_dst)
    ct = osr.CoordinateTransformation(src, dst)
    if polar and osr_proj6:
        # only supported with osgeo.osr v3.0.0+
        y2, x2, _ = ct.TransformPoint(y1, x1)
    else:
        x2, y2, _ = ct.TransformPoint(x1, y1)

    return x2, y2


def _transform(x1, y1, epsg_src, epsg_dst, polar=False):
    if HAVE_OSR:
        return _transform_osr(x1, y1, epsg_src, epsg_dst, polar=polar)
    else:
        return _transform_proj(x1, y1, epsg_src, epsg_dst, polar=polar)


def toMgrs(latitude, longitude, precision=5):
    """ Converts geodetic (latitude and longitude) coordinates to an MGRS
    coordinate string, according to the current ellipsoid parameters.

    @param latitude - latitude value
    @param longitude - longitude value
    @param precision - precision level of MGRS string
    @returns - MGRS coordinate string
    """

    # To avoid precision issues, which appear when using more than
    # 9 decimal places
    # This may no longer be an issue for Python >= 3
    if sys.version_info.major < 3:
        latitude = round(latitude, 9)
        longitude = round(longitude, 9)

    if math.fabs(latitude) > 90:
        raise MgrsException(
            'Latitude outside of valid range (-90 to 90 degrees).')

    if (longitude < -180) or (longitude > 360):
        raise MgrsException(
            'Longitude outside of valid range (-180 to 360 degrees).')

    if (precision < 0) or (precision > MAX_PRECISION):
        raise MgrsException('The precision must be between 0 and 5 inclusive.')

    hemisphere, zone, epsg = _epsgForWgs(latitude, longitude)

    x, y = _transform(longitude, latitude, 4326, epsg, polar=(zone == 61))

    if (latitude < -80) or (latitude > 84):
        # Convert to UPS
        mgrs = _upsToMgrs(hemisphere, x, y, precision)
    else:
        # Convert to UTM
        mgrs = _utmToMgrs(
            zone, hemisphere, latitude, longitude, x, y, precision)

    return mgrs


def toWgs(mgrs):
    """ Converts an MGRS coordinate string to geodetic (latitude and longitude)
    coordinates

    @param mgrs - MGRS coordinate string
    @returns - tuple containning latitude and longitude values
    """
    mgrs = _clean_mgrs_str(mgrs)
    log.debug('in: {0}'.format(mgrs))

    utm = _checkZone(mgrs)
    if utm:
        zone, hemisphere, easting, northing = _mgrsToUtm(mgrs)
    else:
        zone, hemisphere, easting, northing = _mgrsToUps(mgrs)

    log.debug('e: {0}, n: {1}'.format(easting, northing))

    epsg = _epsgForUtm(zone, hemisphere)

    longitude, latitude = \
        _transform(easting, northing, epsg, 4326, polar=(not utm))

    # Note y, x axis order for output
    log.debug('lat: {0}, lon: {1}'.format(latitude, longitude))

    return latitude, longitude


def _upsToMgrs(hemisphere, easting, northing, precision):
    """ Converts UPS (hemisphere, easting, and northing) coordinates
    to an MGRS coordinate string.

    @param hemisphere - hemisphere either 'N' or 'S'
    @param easting - easting/X in meters
    @param northing - northing/Y in meters
    @param precision - precision level of MGRS string
    @returns - MGRS coordinate string
    """
    if hemisphere not in ['N', 'S']:
        raise MgrsException('Invalid hemisphere ("N" or "S").')

    if (easting < MIN_EAST_NORTH) or (easting > MAX_EAST_NORTH):
        raise MgrsException(
            'Easting outside of valid range (100,000 to 900,000 meters '
            'for UTM, 0 to 4,000,000 meters for UPS).')

    if (northing < MIN_EAST_NORTH) or (northing > MAX_EAST_NORTH):
        raise MgrsException(
            'Northing outside of valid range (0 to 10,000,000 meters for UTM, '
            '0 to 4,000,000 meters for UPS).')

    if (precision < 0) or (precision > MAX_PRECISION):
        raise MgrsException('The precision must be between 0 and 5 inclusive.')

    letters = [None, None, None]
    if hemisphere == 'N':
        if easting >= TWOMIL:
            letters[0] = ALPHABET['Z']
        else:
            letters[0] = ALPHABET['Y']

        idx = letters[0] - 22
        ltr2LowValue = UPS_CONSTANTS[idx][1]
        falseEasting = UPS_CONSTANTS[idx][4]
        falseNorthing = UPS_CONSTANTS[idx][5]
    else:
        if easting >= TWOMIL:
            letters[0] = ALPHABET['B']
        else:
            letters[0] = ALPHABET['A']

        ltr2LowValue = UPS_CONSTANTS[letters[0]][1]
        falseEasting = UPS_CONSTANTS[letters[0]][4]
        falseNorthing = UPS_CONSTANTS[letters[0]][5]

    gridNorthing = northing
    gridNorthing = gridNorthing - falseNorthing

    letters[2] = int(gridNorthing / ONEHT)

    if letters[2] > ALPHABET['H']:
        letters[2] = letters[2] + 1

    if letters[2] > ALPHABET['N']:
        letters[2] = letters[2] + 1

    gridEasting = easting
    gridEasting = gridEasting - falseEasting
    letters[1] = ltr2LowValue + int(gridEasting / ONEHT)

    if easting < TWOMIL:
        if letters[1] > ALPHABET['L']:
            letters[1] = letters[1] + 3

        if letters[1] > ALPHABET['U']:
            letters[1] = letters[1] + 2
    else:
        if letters[1] > ALPHABET['C']:
            letters[1] = letters[1] + 2

        if letters[1] > ALPHABET['H']:
            letters[1] = letters[1] + 1

        if letters[1] > ALPHABET['L']:
            letters[1] = letters[1] + 3

    return _mgrsString(0, letters, easting, northing, precision)


def _mgrsToUps(mgrs):
    """ Converts an MGRS coordinate string to UTM projection (zone, hemisphere,
    easting and northing) coordinates

    @param mgrs - MGRS coordinate string
    @returns - tuple containing UTM zone, hemisphere, easting and northing
    """
    zone, letters, easting, northing, precision = _breakMgrsString(mgrs)

    if zone != 0:
        raise MgrsException(BADLY_FORMED)

    if letters[0] >= ALPHABET['Y']:
        hemisphere = 'N'

        idx = letters[0] - 22
        ltr2LowValue = UPS_CONSTANTS[idx][1]
        ltr2HighValue = UPS_CONSTANTS[idx][2]
        ltr3HighValue = UPS_CONSTANTS[idx][3]
        falseEasting = UPS_CONSTANTS[idx][4]
        falseNorthing = UPS_CONSTANTS[idx][5]
    else:
        hemisphere = 'S'

        ltr2LowValue = UPS_CONSTANTS[letters[0]][1]
        ltr2HighValue = UPS_CONSTANTS[letters[0]][2]
        ltr3HighValue = UPS_CONSTANTS[letters[0]][3]
        falseEasting = UPS_CONSTANTS[letters[0]][4]
        falseNorthing = UPS_CONSTANTS[letters[0]][5]

    # Check that the second letter of the MGRS string is within the range
    # of valid second letter values. Also check that the third letter is valid
    invalid = [
        ALPHABET['D'],
        ALPHABET['E'],
        ALPHABET['M'],
        ALPHABET['N'],
        ALPHABET['V'],
        ALPHABET['W']
    ]
    if (letters[1] < ltr2LowValue) \
            or (letters[1] > ltr2HighValue) \
            or (letters[1] in [invalid]) \
            or (letters[2] > ltr3HighValue):
        raise MgrsException(BADLY_FORMED)

    gridNorthing = float(letters[2] * ONEHT + falseNorthing)
    if letters[2] > ALPHABET['I']:
        gridNorthing = gridNorthing - ONEHT

    if letters[2] > ALPHABET['O']:
        gridNorthing = gridNorthing - ONEHT

    gridEasting = float((letters[1] - ltr2LowValue) * ONEHT + falseEasting)
    if ltr2LowValue != ALPHABET['A']:
        if letters[1] > ALPHABET['L']:
            gridEasting = gridEasting - 300000.0

        if letters[1] > ALPHABET['U']:
            gridEasting = gridEasting - 200000.0
    else:
        if letters[1] > ALPHABET['C']:
            gridEasting = gridEasting - 200000.0

        if letters[1] > ALPHABET['I']:
            gridEasting = gridEasting - ONEHT

        if letters[1] > ALPHABET['L']:
            gridEasting = gridEasting - 300000.0

    easting += gridEasting
    northing += gridNorthing

    return zone, hemisphere, easting, northing


def _utmToMgrs(zone, hemisphere, latitude, longitude,
               easting, northing, precision):
    """ Calculates an MGRS coordinate string based on the UTM zone, latitude,
    easting and northing values.

    @param zone - UTM zone number
    @param hemisphere - hemisphere either 'N' or 'S'
    @param latitude - latitude value
    @param longitude - longitude value
    @param easting - easting/X in meters
    @param northing - northing/Y in meters
    @param precision - precision level of MGRS string
    @returns - MGRS coordinate string
    """
    # FIXME: do we really need this?
    # Special check for rounding to (truncated) eastern edge of zone 31V
    # if (zone == 31) \
    #         and (((latitude >= 56.0) and (latitude < 64.0))
    #              and ((longitude >= 3.0) or (easting >= 500000.0))):
    #    # Reconvert to UTM zone 32
    #    override = 32
    #    lat = int(latitude)
    #    lon = int(longitude)
    #    if zone == 1 and override == 60:
    #        zone = override
    #    elif zone == 60 and override == 1:
    #        zone = override
    #    elif (lat > 71) and (lon > -1) and (lon < 42):
    #        if (zone - 2 <= override) and (override <= zone + 2):
    #            zone = override
    #        else:
    #            raise MgrsException('Zone outside of valid range (1 to 60) '
    #                                'and within 1 of "natural" zone')
    #    elif (zone - 1 <= override) and (override <= zone + 1):
    #        zone = override
    #    else:
    #        raise MgrsException('Zone outside of valid range (1 to 60) and '
    #                            'within 1 of "natural" zone')
    #
    #    epsg = _epsgForUtm(zone, hemisphere)
    #
    #    src = osr.SpatialReference()
    #    src.ImportFromEPSG(4326)
    #    dst = osr.SpatialReference()
    #    dst.ImportFromEPSG(epsg)
    #    ct = osr.CoordinateTransformation(src, dst)
    #    x, y, z = ct.TransformPoint(longitude, latitude)

    if latitude <= 0.0 and northing == 1.0e7:
        latitude = 0
        northing = 0

    ltr2LowValue, ltr2HighValue, patternOffset = _gridValues(zone)

    letters = [_latitudeLetter(latitude), None, None]

    while northing >= TWOMIL:
        northing = northing - TWOMIL

    northing += patternOffset
    if northing >= TWOMIL:
        northing = northing - TWOMIL

    letters[2] = int(northing / ONEHT)
    if letters[2] > ALPHABET['H']:
        letters[2] += 1

    if letters[2] > ALPHABET['N']:
        letters[2] += 1

    if ((letters[0] == ALPHABET['V']) and (zone == 31)) \
            and (easting == 500000.0):
        easting = easting - 1.0  # Substract 1 meter

    letters[1] = ltr2LowValue + int((easting / ONEHT) - 1)
    if ltr2LowValue == ALPHABET['J'] and letters[1] > ALPHABET['N']:
        letters[1] += 1

    return _mgrsString(zone, letters, easting, northing, precision)


def _mgrsToUtm(mgrs):
    """ Converts an MGRS coordinate string to UTM projection (zone, hemisphere,
    easting and northing) coordinates.

    @param mgrs - MGRS coordinate string
    @returns - tuple containing UTM zone, hemisphere, easting, northing
    """
    zone, letters, easting, northing, precision = _breakMgrsString(mgrs)
    if zone == 0:
        raise MgrsException(BADLY_FORMED)

    if letters == ALPHABET['X'] and zone in [32, 34, 36]:
        raise MgrsException(BADLY_FORMED)

    if letters[0] < ALPHABET['N']:
        hemisphere = 'S'
    else:
        hemisphere = 'N'

    ltr2LowValue, ltr2HighValue, patternOffset = _gridValues(zone)

    # Check that the second letter of the MGRS string is within the range
    # of valid second letter values. Also check that the third letter is valid
    if (letters[1] < ltr2LowValue) \
            or (letters[1] > ltr2HighValue) \
            or (letters[2] > ALPHABET['V']):
        raise MgrsException(BADLY_FORMED)

    rowLetterNorthing = float(letters[2] * ONEHT)
    gridEasting = float((letters[1] - ltr2LowValue + 1) * ONEHT)
    if ltr2LowValue == ALPHABET['J'] and letters[1] > ALPHABET['O']:
        gridEasting = gridEasting - ONEHT

    if letters[2] > ALPHABET['O']:
        rowLetterNorthing = rowLetterNorthing - ONEHT

    if letters[2] > ALPHABET['I']:
        rowLetterNorthing = rowLetterNorthing - ONEHT

    if rowLetterNorthing >= TWOMIL:
        rowLetterNorthing = rowLetterNorthing - TWOMIL

    minNorthing, northingOffset = _latitudeBandMinNorthing(letters[0])

    gridNorthing = rowLetterNorthing - patternOffset
    if gridNorthing < 0:
        gridNorthing += TWOMIL

    gridNorthing += northingOffset

    if gridNorthing < minNorthing:
        gridNorthing += TWOMIL

    easting += gridEasting
    northing += gridNorthing

    return zone, hemisphere, easting, northing


def _mgrsString(zone, letters, easting, northing, precision):
    """ Constructs an MGRS string from its component parts
    @param zone - UTM zone
    @param letters - MGRS coordinate string letters
    @param easting - easting value
    @param northing - northing value
    @param precision - precision level of MGRS string
    @returns - MGRS coordinate string
    """
    if zone:
        tmp = str(zone)
        mgrs = tmp.zfill(3 - len(tmp))
    else:
        mgrs = '  '

    for i in range(3):
        mgrs += list(ALPHABET.keys())[
            list(ALPHABET.values()).index(letters[i])
        ]

    easting = math.fmod(easting + 1e-8, 100000.0)
    if easting >= 99999.5:
        easting = 99999.0
    mgrs += str(int(easting)).rjust(5, '0')[:precision]

    northing = math.fmod(northing + 1e-8, 100000.0)
    if northing >= 99999.5:
        northing = 99999.0
    mgrs += str(int(northing)).rjust(5, '0')[:precision]

    log.debug('mgrs: {0}'.format(mgrs))

    return mgrs


def _epsgForWgs(latitude, longitude):
    """ Returns corresponding UTM or UPS EPSG code from WGS84 coordinates
    @param latitude - latitude value
    @param longitude - longitude value
    @returns - tuple containing hemisphere, UTM zone and EPSG code
    """

    if math.fabs(latitude) > 90:
        raise MgrsException(
            'Latitude outside of valid range (-90 to 90 degrees).')

    if longitude < -180 or longitude > 360:
        return MgrsException(
            'Longitude outside of valid range (-180 to 360 degrees).')

    # hemisphere
    if latitude < 0:
        hemisphere = 'S'
    else:
        hemisphere = 'N'

    # UTM zone
    if latitude <= -80 or latitude >= 84:
        # Coordinates falls under UPS system
        zone = 61
    else:
        # Coordinates falls under UTM system
        if longitude < 180:
            zone = int(31 + (longitude / 6.0))
        else:
            zone = int((longitude / 6) - 29)

        if zone > 60:
            zone = 1

        # Handle UTM special cases
        if 56.0 <= latitude < 64.0 and 3.0 <= longitude < 12.0:
            zone = 32

        if 72.0 <= latitude < 84.0:
            if 0.0 <= longitude < 9.0:
                zone = 31
            elif 9.0 <= longitude < 21.0:
                zone = 33
            elif 21.0 <= longitude < 33.0:
                zone = 35
            elif 33.0 <= longitude < 42.0:
                zone = 37

    # North or South hemisphere
    if latitude >= 0:
        ns = 600
    else:
        ns = 700

    return hemisphere, zone, 32000 + ns + zone


def _epsgForUtm(zone, hemisphere):
    """ Returen EPSG code for given UTM zone and hemisphere

    @param zone - UTM zone
    @param hemisphere - hemisphere either 'N' or 'S'
    @returns - corresponding EPSG code
    """
    if hemisphere not in ['N', 'S']:
        raise MgrsException('Invalid hemisphere ("N" or "S").')

    if zone < 0 or zone > 60:
        raise MgrsException('UTM zone ouside valid range.')

    if hemisphere == 'N':
        ns = 600
    else:
        ns = 700

    if zone == 0:
        zone = 61

    return 32000 + ns + zone


def _gridValues(zone):
    """ Sets the letter range used for the 2nd letter in the MGRS coordinate
    string, based on the set number of the UTM zone. It also sets the pattern
    offset using a value of A for the second letter of the grid square, based
    on the grid pattern and set number of the UTM zone.

    @param zone - UTM zone number
    @returns - tuple containing 2nd letter low number, 2nd letter high number
    and pattern offset
    """
    setNumber = zone % 6

    if not setNumber:
        setNumber = 6

    ltr2LowValue = None
    ltr2HighValue = None

    if setNumber in [1, 4]:
        ltr2LowValue = ALPHABET['A']
        ltr2HighValue = ALPHABET['H']
    elif setNumber in [2, 5]:
        ltr2LowValue = ALPHABET['J']
        ltr2HighValue = ALPHABET['R']
    elif setNumber in [3, 6]:
        ltr2LowValue = ALPHABET['S']
        ltr2HighValue = ALPHABET['Z']

    if ltr2LowValue is None or ltr2HighValue is None:
        raise MgrsException(BADLY_FORMED)

    if setNumber % 2:
        patternOffset = 0.0
    else:
        patternOffset = 500000.0

    return ltr2LowValue, ltr2HighValue, patternOffset


def _latitudeLetter(latitude):
    """ Returns the latitude band letter for given latitude

    @param latitude - latitude value
    @returns - latitude band letter
    """
    if 72 <= latitude < 84.5:
        return ALPHABET['X']
    elif -80.5 < latitude < 72:
        idx = int(((latitude + 80.0) / 8.0) + 1.0e-12)
        return LATITUDE_BANDS[idx][0]


def _checkZone(mgrs):
    """ Checks if MGRS coordinate string contains UTM zone definition

    @param mgrs - MGRS coordinate string
    @returns - True if zone is given, False otherwise (or for UPS)
    """
    mgrs = _clean_mgrs_str(mgrs)  # should always set two zone digits, even UPS
    count = sum(1 for _ in itertools.takewhile(str.isdigit, mgrs))
    zone = int(mgrs[:count])
    if zone == 0:
        return False
    if count <= 2:
        return count > 0
    else:
        raise MgrsException(BADLY_FORMED)


def _breakMgrsString(mgrs):
    """ Breaks down an MGRS coordinate string into its component parts.

    @param mgrs - MGRS coordinate string
    @returns - tuple containing MGRS string componets: UTM zone,
    MGRS coordinate string letters, easting, northing and precision
    """
    mgrs = _clean_mgrs_str(mgrs)  # should always set two zone digits, even UPS
    # Number of zone digits
    count = sum(1 for _ in itertools.takewhile(str.isdigit, mgrs))
    if count == 2:
        zone = int(mgrs[:2])
        if zone < 0 or zone > 60:
            raise MgrsException(BADLY_FORMED)
    else:
        raise MgrsException(BADLY_FORMED)

    idx = count
    # MGRS letters
    count = sum(1 for _ in itertools.takewhile(
        str.isalpha, itertools.islice(mgrs, idx, None)))
    if count == 3:
        a = ord('A')
        invalid = [ALPHABET['I'], ALPHABET['O']]

        letters = []
        ch = ord(mgrs[idx:idx + 1].upper()) - a
        if ch in invalid:
            raise MgrsException(BADLY_FORMED)
        idx += 1
        letters.append(ch)

        ch = ord(mgrs[idx:idx + 1].upper()) - a
        if ch in invalid:
            raise MgrsException(BADLY_FORMED)
        idx += 1
        letters.append(ch)

        ch = ord(mgrs[idx:idx + 1].upper()) - a
        if ch in invalid:
            raise MgrsException(BADLY_FORMED)
        idx += 1
        letters.append(ch)
    else:
        raise MgrsException(BADLY_FORMED)

    # Easting and Northing
    count = sum(1 for _ in itertools.takewhile(
        str.isdigit, itertools.islice(mgrs, idx, None)))
    if count <= 10 and count % 2 == 0:
        precision = int(count / 2)
        if precision > 0:
            easting = float(mgrs[idx:idx + precision])
            northing = float(mgrs[idx + precision:])

            multiplier = _computeScale(precision)
            easting = easting * multiplier
            northing = northing * multiplier

            if GEOTRANS_HALFMULTI:
                half_multi = multiplier * 0.5  # added in geotrans3.8
                easting += half_multi
                northing += half_multi
        else:
            easting = 0.0
            northing = 0.0
    else:
        raise MgrsException(BADLY_FORMED)

    log.debug(
        'zone: "{0}", letters: "{1}", '
        'easting: "{2}": northing "{3}", precision: "{4}" '.format(
            zone, letters, easting, northing, precision)
    )

    return zone, letters, easting, northing, precision


def _latitudeBandMinNorthing(letter):
    """ Determines the minimum northing and northing offset
    for given latitude band letter.

    @param letter - latitude band letter
    @returns - tuple containing minimum northing and northing offset
    for that letter
    """
    if ALPHABET['C'] <= letter <= ALPHABET['H']:
        minNorthing = LATITUDE_BANDS[letter - 2][1]
        northingOffset = LATITUDE_BANDS[letter - 2][4]
    elif ALPHABET['J'] <= letter <= ALPHABET['N']:
        minNorthing = LATITUDE_BANDS[letter - 3][1]
        northingOffset = LATITUDE_BANDS[letter - 3][4]
    elif ALPHABET['P'] <= letter <= ALPHABET['X']:
        minNorthing = LATITUDE_BANDS[letter - 4][1]
        northingOffset = LATITUDE_BANDS[letter - 4][4]
    else:
        raise MgrsException(BADLY_FORMED)

    return minNorthing, northingOffset


def _computeScale(precision):
    if precision == 0:
        return 1.0e5
    elif precision == 1:
        return 1.0e4
    elif precision == 2:
        return 1.0e3
    elif precision == 3:
        return 1.0e2
    elif precision == 4:
        return 1.0e1
    elif precision == 5:
        return 1.0e0
    return 1.0e5


def _clean_mgrs_str(s):
    """
    Clean up MGRS user-input string.
    :param s: MGRS input string
    :return: Cleaned and stripped string as Unicode
    """
    log.debug('in: {0}'.format(s))
    if str(type(s)) not in ["<class 'str'>",
                            "<class 'bytes'>",
                            "<type 'str'>",
                            "<type 'unicode'>"]:
        raise MgrsException(BADLY_FORMED)

    # convert to unicode, so str.isdigit, etc work in Py2
    if str(type(s)) == "<class 'bytes'>":  # Py 3
        s = s.decode()  # <class 'str'> as UTF-8
    elif str(type(s)) == "<type 'str'>":  # Py 2
        s = unicode(s, encoding='UTF-8')  # <type 'unicode'>

    # strip whitespace
    s = re.sub(r'\s+', '', s)

    # prepend 0 to input of single-digit zone
    count = sum(1 for _ in itertools.takewhile(str.isdigit, s))
    if count == 0:
        s = u'00' + s
    elif count == 1:
        s = u'0' + s
    elif count > 2:
        raise MgrsException(BADLY_FORMED)
    log.debug('out: {0}'.format(s))
    return s
