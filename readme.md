# Lat Lon Tools Plugin

***Lat Lon Tools*** is a suite of tools that makes it easy to interact with other on-line mapping tools. When working with **Google Earth**, **Google Maps** or other on-line mapping tools, coordinates are specified in the order of 'Latitude, Longitude'. By default ***Lat Lon Tools*** uses the standard Google Map format, but is very flexible and can use virtually any projection and coordinate format for input and output. The following tools are available in ***Lat Lon Tools***.

<div style="text-align:center"><img src="doc/menu.jpg" alt="Lat Lon Tools Plugin"></div>

* <img src="images/copyicon.png" alt="Copy coordinate"> ***Copy Latitude, Longitude*** - This captures coordinates onto the clipboard when the user clicks on the map using the standard Google Map format or a format specified in ***Settings***. If the user specifies a **Tab** separator, then the coordinate can be pasted into a spreadsheet in separate columns. While this tool is selected, the coordinate the mouse is over is shown in the lower left-hand corner either in **decimal degrees**, **DMS**, **MGRS**, or **WKT POINT** notation depending on the **Settings**. By default it uses the Geographic Latitude and Longitude to snapshot the coordinate, but this can be configured in **Settings** to use the project CRS or any other projection desired.
  
* <img src="images/zoomicon.png" alt="Copy coordinate"> ***Zoom to Latitude, Longitude*** - With this tool, type or paste a coordinate into the text area and hit **Enter**. QGIS will center the map on the coordinate, highlight the location and create a temporary marker at the location. The marker can be removed with the <img src="doc/cleartool.jpg" alt="Clear marker"> button. If the default WGS 84 (EPSG:4326 - latitude/longitude) coordinate system is specified, "Zoom to Latitude, Longitude" will interpret **decimal degrees**, **DMS**, or **WKT POINT** coordinates. If configure in **Settings** it can zoom to **MGRS** coordinates or coordinates formatted in the project CRS or any other projection. The ***Coordinate Order*** in ***Settings*** dictates whether the order is latitude followed by longitude (Y,X) or longitude followed by latitude (X,Y). By default the order is "Latitude, Longitude", the format used by Google Maps. Pressing the <img src="doc/zoomtool.jpg" alt="Zoom button"> also causes QGIS to zoom to that location.<br /><div style="text-align:center"><img src="doc/zoomto.jpg" alt="Zoom to Latitude, Longitude"></div><br />The following are acceptable coordinate formats when the ***Settings*** **Zoom to Coordinate Type** is set to ***WGS 84 (Latitude & Longitude)***. When the letters "N, S, E, W" are used, then the coordinate order is not important. These letters can be used before or after the coordinates. As long as the coordinate is understandable, punctuation, spaces, and &deg; ' " are optional. In these examples "d" represents degree digits, "m" minutes, and "s" seconds. Here are some examples:

    * Decimal Degree: 38.959390&deg;, -95.265483&deg; / 38.959390, -95.265483 / 38.959390N, 95.265483 W (d.dddd, d.dddd)
    * Degree, Minute: 38&deg; 57.5634'N 95&deg; 15.92890'W (d m.mmmm, d m.mmmm)
    * Degree, Minute: 3857.5634N 09515.92890W (ddmm.mmmm, ddmm.mmmm) - there must be 2 digits for latitude degrees, and 3 digits for longitude degrees.
    * Degree, Minute, Second: 38&deg;57'33.804"N, 95&deg;15'55.739"W (d m s.ssss, d m s.ssss)
    * Degree, Minute, Second: 385733.804N 0951555.739W (ddmmss.ssss, dddmmss.ssss)
    * WKT: POINT(-95.265483 38.959390)
    * Example MGRS coordinate when **Zoom to Coordinate Type** is set to ***MGRS***: 15S UD 03704 14710

* <img src="images/mapicon.png" alt="Copy coordinate"> ***Show in External Map*** - With this tool, the user can click on the QGIS map which launches an external browser and displays the location on an external map. Currently Open Street Map, Google Maps, and Bing Maps are supported. The desired map can be configured in **Settings**.
* <img src="images/multizoom.png" alt="Multi-location Zoom"> ***Multi-location Zoom*** - With this tool the user can read in a set of coordinates that are in either **decimal degrees** or **DMS** notation. The one requirement is that each pair of coordinates are on separate lines and in the order is latitude followed by longitude. The user can also paste or type in a coordinate in the ***Add Single Coordinate*** box and add it to the list. When the user clicks on one of the coordinates in the list, the QGIS map will center itself and highlight the coordinate.

<div style="text-align:center"><img src="doc/multizoom.jpg" alt="Multi-location Zoom"></div>

* ***MGRS Conversions***
    * <img src="images/mgrs2point.png" alt="MGRS to Geometry"> ***MGRS to Geometry*** - This takes a table or vector layer and if there is a field that contains MGRS coordinates, it will convert the layer to a new point vector layer where each record is converted to WGS84 (EPSG:4326) geometry.
    
    <div style="text-align:center"><img src="doc/mgrs2geom.jpg" alt="MGRS to Geometry"></div>

    * <img src="images/point2mgrs.png" alt="Geometry to MGRS"> ***Geometry to MGRS*** - Convert a point vector layer into a point memory layer, but add an MGRS column, containing coordinates based on the vector layer's geometry. MGRS supports measuring precisions of 1m, 10m, 100m, 1km, 10km, and 100km. **MGRS Precision** of 5 is 1m and an **MGRS Precision** of 0 represents a point accuracy of 100km.
    
    <div style="text-align:center"><img src="doc/geom2mgrs.jpg" alt="MGRS to Geometry"></div>

* <img src="images/settings.png" alt="Settings"> ***Settings*** - Displays the settings dialog box (see below).
* <img src="images/help.png" alt="Help"> ***Help*** - Displays this help page.

By default ***Lat Lon Tools*** follows the **Google Map** convention making it possible to copy and paste between QGIS, Google Map, Google Earth, and other on-line maps without breaking the coordinates into pieces. All tools work with latitude and longitude coordinates regardless of the QGIS project coordinate reference system. In ***Settings*** the user can choose the ***Coordinate Capture Delimiter*** used between coordinates with presets for **Comma**, **Space**, and **Tab**. **Other** allows the user to specify a delimited string which can be more than one character.

## Settings

### Capture & Display Settings

![Capture and Display Settings](doc/settings.jpg)

There are 4 capture projections that can be selected from the ***Coordinate Capture Projection*** drop down menu. They are as follows.

* **WGS 84 (Latitude & Longitude)** - This captures the coordinates as a latitude and longitude regardless of what the project CRS is set to. This is the default setting.
* **MGRS** - This captures the coordinates in the [MGRS](https://en.wikipedia.org/wiki/Military_grid_reference_system) format,
* **Project CRS** - This captures the coordinates using the project's specified CRS.
* **Custom CRS** - The captures the coordinate in any coordinate reference system regardless of what the project CRS is set to. When this is selected, then the ***Custom CRS*** dialog box is activated allowing selection of any projection.

Additional coordinate formatting can be specified with ***WGS 84 (Latitude & Longitude) Number Format***.

* **Decimal Degrees** - "42.20391297, -86.023854202"
* **DMS** - "36&deg; 47' 24.27" N, 99&deg; 22' 9.39" W"
* **DDMMSS** - "400210.53N, 1050824.96 W"
* **WKT POINT** - POINT(-86.023854202 42.20391297)

For ***Other CRS Number Format*** such as **Project CRS** or **Custom CRS** the coordinate formatting options are:

* **Normal Coordinate** - Decimal coordinate notation.
* **WKT POINT**

The order in which the coordinates are captured are determined by ***Coordinate Capture Order*** (not applicable to MGRS coordinates or WKT formatted coordinates) and are one of the following:

* **Lat, Lon (Y,X) - Google Map Order**
* **Lon, Lat (X,Y) Order**.

* ***Coordinate Capture Delimiter (Not applicable to MGRS and WKT)*** - Specifies the delimiter that separates the two coordinates. The options are:
    * **Comma** - This is really a comma followed by a space. 
    * **Tab** - This useful if you are pasting the coordinates into two columns of a spreadsheet.
    * **Space**
    * **Other** - With this selected, the contents of ***Other Delimiter*** will be used.
* ***DMS Second Precision*** - Used when fomatting DMS coordinates and specifies the number of digits after the decimal. 

### Zoom to Settings

![Zoom to Settings](doc/settings2.jpg)

The ***Zoom to Latitude, Longitude*** tool accepts the following input coordinates as specified by ***Zoom to Coordinate Type***:

* **WGS 84 (Latitude & Longitude)** - Input coordinates can be either in decimal, DMS or WKT degrees. The order of the coordinates are determined by ***Zoom to Coordinate Order***.
* **MGRS** - This accepts [MGRS](https://en.wikipedia.org/wiki/Military_grid_reference_system) coordinates as input.
* **Project CRS** - This accepts coordinates formatted in the CRS of the QGIS project. The numbers can be formatted in decimal or WKT notation.
* **Custom CRS** - You can specify any CRS for the input coordinates and QGIS will zoom to that coordinate regardless of the project CRS. The numbers can be formatted in decimal or WKT notation.

The order in which the coordinates are parsed in the ***Zoom to Latitude, Longitude*** tool is specified by ***Zoom to Coordinate Type*** and has the following two options: This is not applicable for **MGRS** coordinates or **WKT** formatted coordinates.

* **Lat, Lon (Y,X) - Google Map Order**
* **Lon, Lat (X,Y) Order**

**Use Persistent Marker** - If this is checked, then when you zoom to a coordinate a persistent marker will be displayed until you exit, zoom to another location, or click on the <img src="doc/cleartool.jpg" alt="Clear marker"> button.

### External Map Settings

![External Map Settings](doc/settings3.jpg)

Here you can ***Select an External Map Provider***. The options are:

* **OSM** - Open Street Map
* **Google Map**
* **Google Aerial**
* **Bing Map**
* **Bing Aerial**

***Map Hints*** are desired attributes you would like to see in the resulting map. 

* **Show placemark** - When checked the external map will show a placemark at the location clicked on in the QGIS map. If this is not checked then the external map will center itself around clicked location, but will not display the placemark.
* **Map Zoom Level** - This is the desired default zoom level in the external map when it is launched.
