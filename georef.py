'''
This is adapted from a C++ version of GeographicLib's GEOREF code with
the following license.

Copyright (c) Charles Karney (2015-2020) <charles@karney.com> and licensed
under the MIT/X11 License.  For more information, see
https://geographiclib.sourceforge.io/
'''

import math
import sys

digits_ = "0123456789"
lontile_ = "ABCDEFGHJKLMNPQRSTUVWXYZ"
lattile_ = "ABCDEFGHJKLMM" # Repeat the last M for 90 degrees which rounds up - Prevents extra checks in the code
degrees_ = "ABCDEFGHJKLMNPQ"
tile_ = 15
lonorig_ = -180
latorig_ = -90
base_ = 10
baselen_ = 4
maxprec_ = 11
maxlen_ = baselen_ + 2 * maxprec_

class GeorefException(Exception):
    pass

def find_first_not_of(s, s_set):
    for i, c in enumerate(s):
        if c not in s_set:
            return i
    return(-1)

def lookup(s, c):
    r = s.find(c)
    if r < 0:
        return( -1 )
    return(r)

def encode(lat, lon, prec):
    if lat > 90 or lat < -90:
        raise GeorefException('Latitude not in -90 to 90 range')
    if lon < -180 or lon > 360:
        raise GeorefException('Longitude is out of range')
    if lon >= 180: # make longitude in the range -180, 180
        lon = lon - 360


    if lat == 90:
        lat = lat - sys.float_info.epsilon
    prec = max(-1, min(int(maxprec_), prec))
    if prec == 1:
        prec = prec + 1  # Disallow prec = 1
    m = 60000000000
    x = int(math.floor(lon * m) - lonorig_ * m)
    y = int(math.floor(lat * m) - latorig_ * m)
    ilon = int(x / m)
    ilat = int(y / m)
    georef1 = [""] * maxlen_
    georef1[0] = lontile_[int(ilon / tile_)]
    georef1[1] = lattile_[int(ilat / tile_)]
    if prec >= 0:
        georef1[2] = degrees_[ilon % tile_]
        georef1[3] = degrees_[ilat % tile_]
        if prec > 0:
            x = int(x - m * ilon)
            y = int(y - m * ilat)
            d = math.pow(base_, maxprec_ - prec)
            x = int(x / d)
            y = int(y / d)
            c = prec
            while c:
                georef1[baselen_ + c] = digits_[x % base_]
                x = int(x / base_)
                georef1[baselen_ + c + prec] = digits_[y % base_]
                y = int(y / base_)
                c = c - 1
    return(''.join(georef1))

def decode(georef, centerp=False):
    if georef is None:
        raise GeorefException('Invalid Georef string: None')
    georef = georef.upper()
    leng = len(georef)
    if leng >= 3 and georef[0] == 'I' and georef[1] == 'N' and georef[2] == 'V':
        raise GeorefException('Invalid Georef string')
    if leng < baselen_ - 2 :
        raise GeorefException('Georef must start with at least 2 letters: {}'.format(georef))
    prec1 = int((2 + leng - baselen_) / 2 - 1)
    k = lookup(lontile_, georef[0])
    if k < 0:
        raise GeorefException('Bad longitude tile letter in georef: {}'.format(georef))
    lon1 = k + lonorig_ / tile_
    k = lookup(lattile_, georef[1])
    if k < 0:
        raise GeorefException('Bad latitude tile letter in georef: {}'.format(georef))
    lat1 = k + latorig_ / tile_
    unit = 1
    if leng > 2:
        unit = unit * tile_
        k = lookup(degrees_, georef[2])
        if k < 0:
            raise GeorefException('Bad longitude degree letter in georef: {}'.format(georef))
        lon1 = lon1 * tile_ + k
        if leng < 4:
            raise GeorefException('Missing latitude degree letter in georef: {}'.format(georef))
        k = lookup(degrees_, georef[3])
        if k < 0:
            raise GeorefException('Bad latitude degree letter in georef: {}'.format(georef))
        lat1 = lat1 * tile_ + k
        if prec1 > 0:
            if find_first_not_of(georef[baselen_:], digits_) != -1:
                raise GeorefException('Non digits in trailing portion of georef: {}'.format(georef[baselen_:]))
            if leng % 2:
                raise GeorefException('Georef must end with an even number of digits: {}'.format(georef[baselen_:]))
            if prec1 == 1:
                raise GeorefException('Georef needs at least 4 digits for minutes: {}'.format(georef[baselen_:]))
            if prec1 > maxprec_:
                raise GeorefException('More than {} digits in georef: {}'.format(2*maxprec_, georef[baselen_:]))
            i = 0
            while i < prec1:
                if i:
                    m = base_
                else:
                    m = 6
                unit = unit * m
                x = lookup(digits_, georef[baselen_ + i])
                y = lookup(digits_, georef[baselen_ + i + prec1])                
                if not (i or (x < m and y < m)):
                    raise GeorefException('Minutes terms in georef must be less than 60: {}'.format(georef[baselen_:]))
                lon1 = m * lon1 + x
                lat1 = m * lat1 + y
                i = i + 1
    if centerp:
        unit = unit * 2
        lat1 = 2 * lat1 + 1
        lon1 = 2 * lon1 + 1
    lat = (tile_ * lat1) / unit
    lon = (tile_ * lon1) / unit
    prec = prec1
    return(lat, lon, prec)
