from qgis.core import QgsExpression, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.utils import qgsfunction
# from qgis.gui import *
from . import mgrs as mg

epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

def transform_coords(y, x, crs):
    coord_crs = QgsCoordinateReferenceSystem(crs)
    transform = QgsCoordinateTransform(coord_crs, epsg4326, QgsProject.instance())
    pt = transform.transform(x,y)
    return(pt.y(), pt.x())

def InitLatLonFunctions():
    QgsExpression.registerFunction(mgrs)
    QgsExpression.registerFunction(mgrs_gzd)
    QgsExpression.registerFunction(mgrs_100km)
    QgsExpression.registerFunction(mgrs_east)
    QgsExpression.registerFunction(mgrs_north)

def UnloadLatLonFunctions():
    QgsExpression.unregisterFunction('mgrs')
    QgsExpression.unregisterFunction('mgrs_gzd')
    QgsExpression.unregisterFunction('mgrs_100km')
    QgsExpression.unregisterFunction('mgrs_east')
    QgsExpression.unregisterFunction('mgrs_north')

@qgsfunction(-1, group='Lat Lon Tools')
def mgrs(values, feature, parent):
    """
    Calculate the MGRS coordinate from decimal latitude and longitude.

    <h4>Syntax</h4>
    <p><b>mgrs</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>
    
    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>mgrs</b>(46.2, 6.1) &rarr; 32TKS7626020357</li>
      <li><b>mgrs</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; 32TKS7626020357</li>
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
    
@qgsfunction(-1, group='Lat Lon Tools')
def mgrs_gzd(values, feature, parent):
    """
    Calculate the one or three digit Grid Zone Designator (GZD) from decimal latitude and longitude. Between and including latitudes 80&deg;S and 84&deg;N this is a three digit value with the first two characters representing the UTM zone and the third characater representing the band of latitude. In the polar regions outside of the UTM area this is a one character field with A and B used near the south pole, and Y and Z used near the north pole.

    <h4>Syntax</h4>
    <p><b>mgrs_gzd</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>
    
    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>mgrs_gzd</b>(46.2, 6.1) &rarr; 32T</li>
      <li><b>mgrs_gzd</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; 32T</li>
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
    
@qgsfunction(-1, group='Lat Lon Tools')
def mgrs_100km(values, feature, parent):
    """
    Calculate the MGRS 100,000 meter grid squares (BIGRAM)
    from decimal latitude and longitude.

    <h4>Syntax</h4>
    <p><b>mgrs_100km</b>( <i>y, x[, crs='EPSG:4326']</i> )</p>
    
    <h4>Arguments</h4>
    <p><i>y</i> &rarr; the y or latitude coordinate.</p>
    <p><i>x</i> &rarr; the x or longitude coordinate.</p>
    <p><i>crs</i> &rarr; optional coordinate reference system. Default value is 'EPSG:4326' if not specified.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>mgrs_100km</b>(46.2, 6.1) &rarr; KS</li>
      <li><b>mgrs_100km</b>(5812456.38,679048.05, 'EPSG:3857') &rarr; KS</li>
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
    
@qgsfunction(-1, group='Lat Lon Tools')
def mgrs_east(values, feature, parent):
    """
    Calculate the MGRS easting part value from decimal latitude and longitude.

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

@qgsfunction(-1, group='Lat Lon Tools')
def mgrs_north(values, feature, parent):
    """
    Calculate the MGRS northing part value from decimal latitude and longitude.

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
