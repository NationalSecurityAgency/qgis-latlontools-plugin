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
from qgis.core import QgsPointXY, QgsGeometry, QgsExpression, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.utils import qgsfunction
# from qgis.gui import *
from . import mgrs as mg
from .utm import latLon2Utm, utm2Point, latLon2UtmZone, utmGetEpsg, latLon2UtmParameters
from . import olc
from .util import formatDmsString
# import traceback

group_name = 'Lat Lon Tools'
epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

def transform_coords(y, x, crs):
    coord_crs = QgsCoordinateReferenceSystem(crs)
    transform = QgsCoordinateTransform(coord_crs, epsg4326, QgsProject.instance())
    pt = transform.transform(x, y)
    return(pt.y(), pt.x())

def InitLatLonFunctions():
    QgsExpression.registerFunction(dm)
    QgsExpression.registerFunction(dms)
    QgsExpression.registerFunction(ddmmss)
    QgsExpression.registerFunction(llt_dd)
    QgsExpression.registerFunction(llt_yx)
    QgsExpression.registerFunction(mgrs)
    QgsExpression.registerFunction(mgrs_100km)
    QgsExpression.registerFunction(mgrs_east)
    QgsExpression.registerFunction(mgrs_gzd)
    QgsExpression.registerFunction(mgrs_north)
    QgsExpression.registerFunction(mgrs_to_point)
    QgsExpression.registerFunction(to_pluscode)
    QgsExpression.registerFunction(from_pluscode)
    QgsExpression.registerFunction(utm)
    QgsExpression.registerFunction(utm_east)
    QgsExpression.registerFunction(utm_epsg)
    QgsExpression.registerFunction(utm_hemisphere)
    QgsExpression.registerFunction(utm_north)
    QgsExpression.registerFunction(utm_to_point)
    QgsExpression.registerFunction(utm_zone)
    

def UnloadLatLonFunctions():
    QgsExpression.unregisterFunction('dm')
    QgsExpression.unregisterFunction('dms')
    QgsExpression.unregisterFunction('ddmmss')
    QgsExpression.unregisterFunction('llt_dd')
    QgsExpression.unregisterFunction('llt_yx')
    QgsExpression.unregisterFunction('mgrs')
    QgsExpression.unregisterFunction('mgrs_100km')
    QgsExpression.unregisterFunction('mgrs_east')
    QgsExpression.unregisterFunction('mgrs_gzd')
    QgsExpression.unregisterFunction('mgrs_north')
    QgsExpression.unregisterFunction('mgrs_to_point')
    QgsExpression.unregisterFunction('to_pluscode')
    QgsExpression.unregisterFunction('from_pluscode')
    QgsExpression.unregisterFunction('utm')
    QgsExpression.unregisterFunction('utm_east')
    QgsExpression.unregisterFunction('utm_epsg')
    QgsExpression.unregisterFunction('utm_hemisphere')
    QgsExpression.unregisterFunction('utm_north')
    QgsExpression.unregisterFunction('utm_to_point')
    QgsExpression.unregisterFunction('utm_zone')

@qgsfunction(args='auto', group=group_name)
def mgrs_to_point(mgrs, feature, parent):
    """
    Convert an MGRS string into a WGS 84 (EPSG:4326) point geometry feature.

    <h4>Syntax</h4>
    <p><b>mgrs_to_point</b>( <i>mgrs_str</i> )</p>

    <h4>Arguments</h4>
    <p><i>mgrs_str</i> &rarr; an MGRS formatted string.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>mgrs_to_point</b>('32TKS7626020357') &rarr; returns a point geometry</li>
      <li><b>geom_to_wkt</b>(<b>mgrs_to_point</b>('32TKS7626020357')) &rarr; 'Point (6.09999238 46.19999307)'</li>
    </ul>
    """
    try:
        mgrs = re.sub(r'\s+', '', str(mgrs))  # Remove all white space
        lat, lon = mg.toWgs(mgrs)
        pt = QgsPointXY(lon, lat)
        return(QgsGeometry.fromPointXY(pt))
    except Exception:
        parent.setEvalErrorString("Error: invalid MGRS coordinate")
        return

@qgsfunction(-1, group=group_name)
def mgrs(values, feature, parent):
    """
    Calculate the MGRS coordinate from y, x (latitude, longitude) coordinates.

    <h4>Syntax</h4>
    <p><b>mgrs</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>mgrs</b>(46.2, 6.1) &rarr; '32TKS7626020357'</li>
      <li><b>mgrs</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; '32TKS7626020357'</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = values[0]
        x = values[1]
        if len(values) == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        full_mgrs = mg.toMgrs(y, x).strip()
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return full_mgrs

@qgsfunction(-1, group=group_name)
def mgrs_gzd(values, feature, parent):
    """
    Calculate the one or three digit Grid Zone Designator (GZD) from y, x (latitude, longitude) coordinates. Between and including latitudes 80&deg;S and 84&deg;N this is a three digit value with the first two characters representing the UTM zone and the third characater representing the band of latitude. In the polar regions outside of the UTM area this is a one character field with A and B used near the south pole, and Y and Z used near the north pole.

    <h4>Syntax</h4>
    <p><b>mgrs_gzd</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>mgrs_gzd</b>(46.2, 6.1) &rarr; '32T'</li>
      <li><b>mgrs_gzd</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; '32T'</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = values[0]
        x = values[1]
        if len(values) == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        mgrs = mg.toMgrs(y, x).strip()
        if y > 84 or y < -80:
            gzd = mgrs[0]
        else:
            gzd = mgrs[:3]
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return gzd

@qgsfunction(-1, group=group_name)
def mgrs_100km(values, feature, parent):
    """
    Calculate the MGRS 100,000 meter grid squares (BIGRAM)
    from y, x (latitude, longitude) coordinates.

    <h4>Syntax</h4>
    <p><b>mgrs_100km</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>mgrs_100km</b>(46.2, 6.1) &rarr; 'KS'</li>
      <li><b>mgrs_100km</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; 'KS'</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = values[0]
        x = values[1]
        if len(values) == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        mgrs = mg.toMgrs(y, x).strip()
        if y > 84 or y < -80:
            ups = mgrs[1:3]
        else:
            ups = mgrs[3:5]
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return ups

@qgsfunction(-1, group=group_name)
def mgrs_east(values, feature, parent):
    """
    Calculate the MGRS easting part value from y, x (latitude, longitude) coordinates.

    <h4>Syntax</h4>
    <p><b>mgrs_east</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>mgrs_east</b>(46.2, 6.1) &rarr; 76260</li>
      <li><b>mgrs_east</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; 76260</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = values[0]
        x = values[1]
        if len(values) == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        mgrs = mg.toMgrs(y, x).strip()
        if y > 84 or y < -80:
            east = mgrs[3:8]
        else:
            east = mgrs[5:10]
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return east

@qgsfunction(-1, group=group_name)
def mgrs_north(values, feature, parent):
    """
    Calculate the MGRS northing part value from y, x (latitude, longitude) coordinates.

    <h4>Syntax</h4>
    <p><b>mgrs_north</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>mgrs_north</b>(46.2, 6.1) &rarr; 20357</li>
      <li><b>mgrs_north</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; 20357</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = values[0]
        x = values[1]
        if len(values) == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        mgrs = mg.toMgrs(y, x).strip()
        if y > 84 or y < -80:
            north = mgrs[8:13]
        else:
            north = mgrs[10:15]
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return north

@qgsfunction(-1, group=group_name)
def to_pluscode(values, feature, parent):
    """
    Calculate the Plus Code coordinate from latitude and longitude (EPSG:4326) coordinates.

    <h4>Syntax</h4>
    <p><b>to_pluscode</b>( <i>latitude, longitude[, precision=11]</i> )</p>

    <h4>Arguments</h4>
    <p><i>latitude</i> &rarr; the latitude coordinate.</p>
    <p><i>longitude</i> &rarr; the longitude coordinate.</p>
    <p><i>precision</i> &rarr; optional coordinate precision. Default value is 11 and must be between 10 and 15.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>to_pluscode</b>(46.2, 6.1) &rarr; '8FR86422+222'</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        if len(values) == 3:
            precision = int(values[2])
        else:
            precision = 11
        if precision < 10 or precision > 15:
            parent.setEvalErrorString("Error: precision must be between 10 and 15")
            return
        
        lat = values[0]
        lon = values[1]
        msg = olc.encode(lat, lon, precision)
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude, longitude, or precision parameters")
        return
    return msg

@qgsfunction(args='auto', group=group_name)
def from_pluscode(pluscode, feature, parent):
    """
    Calculate an EPSG:4326 point geometry from a plus code coordinate string.

    <h4>Syntax</h4>
    <p><b>from_pluscode</b>( <i>pluscode_string</i> )</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>from_pluscode</b>('8FR86422+222') &rarr; returns a point geometry</li>
      <li><b>geom_to_wkt(from_pluscode</b>('8FR86422+222')) &rarr; 'Point(6.10001562 46.2000125)'</li>
    </ul>
    """
    try:
        coord = olc.decode(pluscode.strip())
        lat = coord.latitudeCenter
        lon = coord.longitudeCenter
        pt = QgsPointXY(lon, lat)
        return(QgsGeometry.fromPointXY(pt))
    except Exception:
        parent.setEvalErrorString("Error: invalid pluscode coordinate")
        return

@qgsfunction(args='auto', group=group_name)
def utm_to_point(utm_str, feature, parent):
    """
    Convert a UTM string into a WGS 84 (EPSG:4326) point geometry feature.

    <h4>Syntax</h4>
    <p><b>utm_to_point</b>( <i>utm_str</i> )</p>

    <h4>Arguments</h4>
    <p><i>utm_str</i> &rarr; a UTM formatted string.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>utm_to_point</b>('13N 278501 4486692') &rarr; returns a point geometry</li>
      <li><b>geom_to_wkt</b>(<b>utm_to_point</b>('13N 278501 4486692')) &rarr; 'Point (-107.61396588 40.50139194)'</li>
    </ul>
    """
    try:
        pt = utm2Point(utm_str)
        return(QgsGeometry.fromPointXY(pt))
    except Exception:
        parent.setEvalErrorString("Error: invalid MGRS coordinate")
        return

@qgsfunction(-1, group=group_name)
def utm(values, feature, parent):
    """
    Calculate the Standard UTM coordinate from y, x (latitude, longitude) coordinates.

    <h4>Syntax</h4>
    <p><b>utm</b>( <i>y, x[, precision=0, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>precision</i> &rarr; number of decimal digits. Unless more precision is needed 0 is a good starting point.
    <p><i>crs</i> &rarr; optional coordinate reference system of the y, x coordinates. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>utm</b>(46.2, 6.1) &rarr; '32N 276261 512035'</li>
      <li><b>utm</b>(46.2, 6.1, 2) &rarr; '32N 276260.62 5120357.75'</li>
      <li><b>utm</b>(5812456.38,679048.05, 0, 'EPSG:3857') &rarr; '32N 276260 5120357'</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 4:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        num_args = len(values)
        y = values[0]
        x = values[1]
        if num_args >= 3:
            precision = int(values[2])
            if precision < 0:
                parent.setEvalErrorString("Error: invalid precision")
                return
        else:
            precision = 0
        if num_args == 4:
            crs = values[3]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        utm_str = latLon2Utm(y, x, precision)
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return utm_str

@qgsfunction(-1, group=group_name)
def utm_zone(values, feature, parent):
    """
    Calculate the Standard UTM zone from y, x (latitude, longitude) coordinates.

    <h4>Syntax</h4>
    <p><b>utm_zone</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>utm_zone</b>(46.2, 6.1) &rarr; 32</li>
      <li><b>utm_zone</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; 32</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = values[0]
        x = values[1]
        if len(values) == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        zone, hemisphere = latLon2UtmZone(y, x)
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return zone

@qgsfunction(-1, group=group_name)
def utm_hemisphere(values, feature, parent):
    """
    Calculate the Standard UTM hemisphere ('N' or 'S') from y, x (latitude, longitude) coordinates.

    <h4>Syntax</h4>
    <p><b>utm_hemisphere</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>utm_hemisphere</b>(46.2, 6.1) &rarr; 'N'</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = values[0]
        x = values[1]
        if len(values) == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        zone, hemisphere = latLon2UtmZone(y, x)
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return hemisphere

@qgsfunction(-1, group=group_name)
def utm_epsg(values, feature, parent):
    """
    Returns the UTM EPSG code which the y, x (latitude, longitude) coordinates are in.

    <h4>Syntax</h4>
    <p><b>utm_epsg</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>utm_epsg</b>(46.2, 6.1) &rarr; 'EPSG:32632'</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = values[0]
        x = values[1]
        if len(values) == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        zone, hemisphere = latLon2UtmZone(y, x)
        epsg_code = utmGetEpsg(hemisphere, zone)
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return epsg_code

@qgsfunction(-1, group=group_name)
def utm_east(values, feature, parent):
    """
    Calculate the UTM easting value from y, x (latitude, longitude) coordinates.

    <h4>Syntax</h4>
    <p><b>utm_east</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system of the y, x coordinates. Default value is 'EPSG:4326'.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>utm_east</b>(46.2, 6.1) &rarr; '276260.6162769337'</li>
      <li><b>utm_east</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; 276260.00339285017</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        num_args = len(values)
        y = values[0]
        x = values[1]
        if num_args == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        zone, hemisphere, east, north = latLon2UtmParameters(y, x)
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return east

@qgsfunction(-1, group=group_name)
def utm_north(values, feature, parent):
    """
    Calculate the UTM northing value from y, x (latitude, longitude) coordinates.

    <h4>Syntax</h4>
    <p><b>utm_north</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system of the y, x coordinates. Default value is 'EPSG:4326'.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>utm_north</b>(46.2, 6.1) &rarr; 5120357.748034837</li>
      <li><b>utm_north</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; 5120357.001692174</li>
    </ul>
    """
    if len(values) < 2 or len(values) > 3:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        num_args = len(values)
        y = values[0]
        x = values[1]
        if num_args == 3:
            crs = values[2]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        zone, hemisphere, east, north = latLon2UtmParameters(y, x)
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude/longitude parameters")
        return
    return north

@qgsfunction(-1, group=group_name)
def dm(values, feature, parent):
    """
    Convert a coordinate to a Degree, Minute (DM) string.

    <h4>Syntax</h4>
    <p><b>dm</b>( <i>y, x, order, precision[,add_space=False, pad_zero=False, delimiter=', ', crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>order</i> &rarr; specify either 'yx' or 'xy' for latitude, longitude or longitude, latitude.
    <p><i>precision</i> &rarr; specifies the number of digits after the minutes decimal point.</p>
    <p><i>add_space</i> &rarr; when True a space will be added between D M values. Default value is False.
    <p><i>pad_zero</i> &rarr; pad values with leading zeros. Default value is False.
    <p><i>delimiter</i> &rarr; specifies the delimiter between the dm latitude, longitude pairs. The default value is ', '.
    <p><i>crs</i> &rarr; optional coordinate reference system of the y, x coordinates. Default value is 'EPSG:4326'.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>dm</b>(28.41870950, -81.58118645, 'yx', 0) &rarr; 28°25'N, 81°35'W'</li>
      <li><b>dm</b>(28.41870950, -81.58118645, 'xy', 0) &rarr; 81°35'W, 28°25'N</li>
      <li><b>dm</b>(28.41870950, -81.58118645, 'yx', 0, True) &rarr; '28° 25' N, 81° 35' W'</li>
      <li><b>dm</b>(28.41870950, -81.58118645, 'yx', 2, False, True) &rarr; 28°25.12'N, 081°34.87'W</li>
      <li><b>dm</b>(28.41870950, -81.58118645, 'yx', 0, False, True, ' : ') &rarr; 28°25'N : 081°35'W</li>
      <li><b>dm</b>(3301866.78, -9081576.13, 'yx', 0,False,False,', ', 'EPSG:3857') &rarr;  '28°25'N, 81°35'W'</li>
    </ul>
    """
    num_args = len(values)
    if num_args < 4 or num_args > 8:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = float(values[0])
        x = float(values[1])
        order = 0 if values[2] == 'yx' else 1
        precision = int(values[3])
        addspace = values[4] if num_args > 4 else False
        pad_zero = values[5] if num_args > 5 else False
        delimiter = values[6] if num_args > 6 else ', '
        if num_args == 8:
            crs = values[7]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)

        dms_str = formatDmsString(y, x, 2, precision, order, delimiter, addspace, pad_zero)
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude, longitude, or parameters")
        return
    return dms_str


@qgsfunction(-1, group=group_name)
def dms(values, feature, parent):
    """
    Convert a coordinate to a Degree, Minute, Second (DMS) string.

    <h4>Syntax</h4>
    <p><b>dms</b>( <i>y, x, order, precision[,add_space=False, pad_zero=False, delimiter=', ', crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>order</i> &rarr; specify either 'yx' or 'xy' for latitude, longitude or longitude, latitude.
    <p><i>precision</i> &rarr; specifies the number of digits after the seconds decimal point.</p>
    <p><i>add_space</i> &rarr; when True a space will be added between D M S values. Default value is False.
    <p><i>pad_zero</i> &rarr; pad values with leading zeros. Default value is False.
    <p><i>delimiter</i> &rarr; specifies the delimiter between the dms latitude, longitude pairs. The default value is ', '.
    <p><i>crs</i> &rarr; optional coordinate reference system of the y, x coordinates. Default value is 'EPSG:4326'.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>dms</b>(28.41870950, -81.58118645, 'yx', 0) &rarr; 28°25'7"N, 81°34'52"W</li>
      <li><b>dms</b>(28.41870950, -81.58118645, 'xy', 0) &rarr; 81°34'52"W, 28°25'7"N</li>
      <li><b>dms</b>(28.41870950, -81.58118645, 'yx', 0, True) &rarr; 28° 25' 7" N, 81° 34' 52" W</li>
      <li><b>dms</b>(28.41870950, -81.58118645, 'yx', 2, False, True) &rarr; 28°25'07.35"N, 081°34'52.27"W</li>
      <li><b>dms</b>(28.41870950, -81.58118645, 'yx', 0, False, True, ' : ') &rarr; 28°25'07"N : 081°34'52"W</li>
      <li><b>dms</b>(3301866.78, -9081576.13, 'yx', 0,False,True,', ', 'EPSG:3857') &rarr; '28°25'07"N, 081°34'52"W'</li>
    </ul>
    """
    num_args = len(values)
    if num_args < 4 or num_args > 8:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = float(values[0])
        x = float(values[1])
        order = 0 if values[2] == 'yx' else 1
        precision = int(values[3])
        addspace = values[4] if num_args > 4 else False
        pad_zero = values[5] if num_args > 5 else False
        delimiter = values[6] if num_args > 6 else ', '
        if num_args == 8:
            crs = values[7]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)

        dms_str = formatDmsString(y, x, 0, precision, order, delimiter, addspace, pad_zero)
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude, longitude, or parameters")
        return
    return dms_str

@qgsfunction(-1, group=group_name)
def ddmmss(values, feature, parent):
    """
    Convert a coordinate to a DDMMSS string.

    <h4>Syntax</h4>
    <p><b>ddmmss</b>( <i>y, x, order, precision[, delimiter=', ', crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>order</i> &rarr; specify either 'yx' or 'xy' for latitude, longitude or longitude, latitude.
    <p><i>precision</i> &rarr; specifies the number of digits after the seconds decimal point.</p>
    <p><i>delimiter</i> &rarr; specifies the delimiter between the ddmmss latitude, longitude pairs. The default value is ', '.
    <p><i>crs</i> &rarr; optional coordinate reference system of the y, x coordinates. Default value is 'EPSG:4326'.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>ddmmss</b>(28.41870950, -81.58118645, 'yx', 0) &rarr; 282507N, 0813452W</li>
      <li><b>ddmmss</b>(28.41870950, -81.58118645, 'xy', 0) &rarr; 0813452W, 282507N</li>
      <li><b>ddmmss</b>(28.41870950, -81.58118645, 'yx', 2) &rarr; 282507.35N, 0813452.27W</li>
      <li><b>ddmmss</b>(28.41870950, -81.58118645, 'yx', 0, ':') &rarr; 282507N:0813452W</li>
      <li><b>ddmmss</b>(3301866.78, -9081576.13, 'yx', 0,', ', 'EPSG:3857') &rarr; '282507N, 0813452W'</li>
    </ul>
    """
    num_args = len(values)
    if num_args < 4 or num_args > 6:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = float(values[0])
        x = float(values[1])
        order = 0 if values[2] == 'yx' else 1
        precision = int(values[3])
        delimiter = values[4] if num_args > 4 else ', '
        if num_args == 6:
            crs = values[5]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        dms_str = formatDmsString(y, x, 1, precision, order, delimiter, False, False)
    except Exception:
        parent.setEvalErrorString("Error: invalid parameters")
        return
    return dms_str


@qgsfunction(-1, group=group_name)
def llt_dd(values, feature, parent):
    """
    Convert a coordinate pair to a decimal degree string. Trailing decimal zeros are removed. If the CRS of the input coordinate is not EPSG:4326, the CRS needs to be specified and will be converted to decimal degrees.

    <h4>Syntax</h4>
    <p><b>llt_dd</b>( <i>y, x, [order='yx', precision=8, delimiter=', ', crs='EPSG:4326']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y (lat)</i> &rarr; the y or latitude coordinate either as a floating point number or a string.</p>
    <p><i>x (lon)</i> &rarr; the x or longitude coordinate either as a floating point number or a string.</p>
    <p><i>order</i> &rarr; specify either 'yx' or 'xy' for latitude, longitude or longitude, latitude. The default is 'yx'.
    <p><i>precision</i> &rarr; specifies the number of decimal point digits.</p>
    <p><i>delimiter</i> &rarr; specifies the delimiter between the latitude and longitude pairs. The default value is ', '.
    <p><i>crs</i> &rarr; optional coordinate reference system of the y, x coordinates. Default value is 'EPSG:4326'.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>llt_dd</b>(28.41870950, -81.58118645) &rarr; '28.4187095, -81.58118645'</li>
      <li><b>llt_dd</b>(28.41870950, -81.58118645, 'xy', 4) &rarr; '-81.5812, 28.4187'</li>
      <li><b>llt_dd</b>(28.41870950, -81.58118645, 'yx', 0) &rarr; '28, -82'</li>
      <li><b>llt_dd</b>(3301866.78, -9081576.13, 'yx', 5, ' : ', 'EPSG:3857') &rarr; '28.41871 : -81.58119'</li>
    </ul>
    """
    num_args = len(values)
    if num_args < 2 or num_args > 6:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = float(values[0])
        x = float(values[1])
        if num_args > 2:
            order = 0 if values[2] == 'yx' else 1
        else:
            order = 0
        
        precision = int(values[3]) if num_args > 3 else 8
        if precision < 0:
            parent.setEvalErrorString("Error: You cannot use a negative precision")
            return
        delimiter = values[4] if num_args > 4 else ', '
        if num_args == 6:
            crs = values[5]
            if crs and crs != 'EPSG:4326':
                y, x = transform_coords(y, x, crs)
        if precision == 0:
            if order:  # xy order
                dd_str = '{:.0f}{}{:.0f}'.format(x, delimiter, y)
            else:
                dd_str = '{:.0f}{}{:.0f}'.format(y, delimiter, x)
        else:
            x_str = '{:.{prec}f}'.format(x, prec=precision).rstrip('0').rstrip('.')
            y_str = '{:.{prec}f}'.format(y, prec=precision).rstrip('0').rstrip('.')
            if order:  # xy order
                dd_str = x_str + delimiter + y_str
            else:
                dd_str = y_str + delimiter + x_str
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude, longitude, or parameters")
        return
    return dd_str

@qgsfunction(-1, group=group_name)
def llt_yx(values, feature, parent):
    """
    Convert a coordinate pair to an appropriate string. Trailing decmial zeros are removed. There is no coordinate trasformation made with this expression.

    <h4>Syntax</h4>
    <p><b>llt_yx</b>( <i>y, x, [order='yx', precision=8, delimiter=', ']</i> )</p>

    <h4>Arguments</h4>
    <p><i>y (lat)</i> &rarr; the y coordinate either as a floating point number or a string.</p>
    <p><i>x (lon)</i> &rarr; the x coordinate either as a floating point number or a string.</p>
    <p><i>order</i> &rarr; specify either 'yx' or 'xy' for the coodinate display order. The default is 'yx'.
    <p><i>precision</i> &rarr; specifies the number of decimal point digits.</p>
    <p><i>delimiter</i> &rarr; specifies the delimiter between the y and x pairs. The default value is ', '.

    <h4>Example usage</h4>
    <ul>
      <li><b>llt_yx</b>(28.41870950, -81.58118645) &rarr; '28.4187095, -81.58118645'</li>
      <li><b>llt_yx</b>(28.41870950, -81.58118645, 'xy', 4) &rarr; '-81.5812, 28.4187'</li>
      <li><b>llt_yx</b>(28.41870950, -81.58118645, 'yx', 0) &rarr; '28, -82'</li>
      <li><b>llt_yx</b>(3301866.787, -9081576.101, 'yx', 2, ' : ') &rarr; '3301866.79 : -9081576.1'</li>
    </ul>
    """
    num_args = len(values)
    if num_args < 2 or num_args > 5:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    try:
        y = float(values[0])
        x = float(values[1])
        if num_args > 2:
            order = 0 if values[2] == 'yx' else 1
        else:
            order = 0
        
        precision = int(values[3]) if num_args > 3 else 8
        if precision < 0:
            parent.setEvalErrorString("Error: You cannot use a negative precision")
            return
        delimiter = values[4] if num_args > 4 else ', '
        if precision == 0:
            if order:  # xy order
                dd_str = '{:.0f}{}{:.0f}'.format(x, delimiter, y)
            else:
                dd_str = '{:.0f}{}{:.0f}'.format(y, delimiter, x)
        else:
            x_str = '{:.{prec}f}'.format(x, prec=precision).rstrip('0').rstrip('.')
            y_str = '{:.{prec}f}'.format(y, prec=precision).rstrip('0').rstrip('.')
            if order:  # xy order
                dd_str = x_str + delimiter + y_str
            else:
                dd_str = y_str + delimiter + x_str
    except Exception:
        parent.setEvalErrorString("Error: invalid latitude, longitude, or parameters")
        return
    return dd_str
