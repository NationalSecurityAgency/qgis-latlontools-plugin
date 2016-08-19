# Lat Lon Tools Plugin

When working with **Google Earth**, **Google Maps** or other on-line mapping tools, coordinates are specified in the order of 'Latitude, Longitude', but the similar existing QGIS plugins specify the coordinates in the reverse order or require separate fields for latitude and longitude. This makes it so that you have to copy and paste each piece of the coordinate between QGIS and Google Maps which is time consuming. This plugin fixes this problem and adds some additional functionality. By default ***Lat Lon Tools*** snapshots coordinates and parses them in the order of "Latitude, Longitude." As of version 0.4.2, the user can configure this in Settings to reverse to the order to "Longitude, Latitude." ***Lat Lon Tools*** has three tools.

![Lat Lon Tools Plugin](doc/menu.jpg)

* ***Copy Latitude, Longitude*** - This captures coordinates onto the clipboard when the user clicks on the map using the standard Google Map format or a format specified in ***`Settings`***. If the user specifies a **`Tab`** separator, then the coordinate can be pasted into a spreadsheet in separate columns. While this tool is selected, the coordinate the mouse is over is shown in the lower left-hand corner either in decimal degrees or DMS depending on the **Settings**.
* **Zoom to Latitude, Longitude** - With this tool, type or paste a coordinate into the text area and hit **Enter**. QGIS will then center the map on the coordinate and highlight the location. The format can either be **DMS** or **decimal degrees**. The ***`Coordinate Order`*** in ***`Settings`*** dictates whether the order is latitude followed by longitude or longitude followed by latitude. By default the order is "Latitude, Longitude", the format used by Google Maps.

![Zoom to Latitude, Longitude](doc/zoomto.jpg)

* **Multi-location Zoom** - With this tool the user can read in a set of coordinates that are in either **decimal degrees** or **DMS** notation. The one requirement is that each pair of coordinates are on separate lines and in the order is latitude followed by longitude. The user can also paste or type in a coordinate in the ***`Add Single Coordinate`*** box and add it to the list. When the user clicks on one of the coordinates in the list, the QGIS map will center itself and highlight the coordinate.

![Multi-location Zoom](doc/multizoom.jpg)

Because ***Lat Lon Tools*** follows the **Google Map** convention, it makes it possible to copy and paste between QGIS, Google Map, Google Earth, and other on-line maps without breaking the coordinates into pieces. All tools work with latitude and longitude coordinates regardless of the QGIS project coordinate reference system. In ***`Settings`*** the user can choose the ***`Coordinate Capture Delimiter`*** used between coordinates with presets for **`Comma`**, **`Space`**, and **`Tab`**. **`Other`** allows the user to specify a delimited string which can be more than one character. The user can also choose whether the output format is in **`Decimal Degrees`**, **`DMS coordinates`** or in the **`Native CRS`**.

## Settings
This shows the settings dialog box.

![Settings](doc/settings.jpg)

There are 4 capture formats that can be selected from the drop down menu. The formats of each are as follows.

* **Decimal Degrees** - "42.20391297, -86.023854202"
* **DMS** - "36&deg; 47' 24.27" N, 99&deg; 22' 9.39" W"
* **DDMMSS** - "400210.53N, 1050824.96 W"
* **Native CRS** - This captures the coordinates in the Native CRS

Note that in the DMS formats, the number of digits after the decimal is set by ***`DMS Second Precision`***. The **Delimiter** is what separates the two coordinates. In the drop down menu you can specify a **`Comma`** which is really a comma followed by a space. Additional delimiters are a **`Tab`**, **`Space`**, and **`Other`**. If **`Other`** is selected, then the contents of ***`Other Delimiter`*** will be used.

The order in which the coordinates are parsed in the ***`Zoom to Latitude, Longitude`*** tool and captured in the ***`Copy Latitude, Longitude`*** tool is dictated by ***`Coordinate Order`***. The two options are **`Lat, Lon (Y,X) - Google Map Order`** and **`Lon, Lat (X,Y) Order`**. Google Map order is used by default when ***Lat, Lon Tools*** is first used. 
