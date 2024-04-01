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
from .util import tr

MAP_PROVIDERS = [
    [tr('OSM'), 'http://www.openstreetmap.org/#map={zoom}/{lat}/{lon}', 'http://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map={zoom}/{lat}/{lon}'],
    [tr('Google Map'), 'https://www.google.com/maps/@{lat},{lon},{zoom}z', 'https://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},{zoom}z'],
    [tr('Google Aerial'), 'https://www.google.com/maps/@{lat},{lon},{zoom}z/data=!3m1!1e3', 'https://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},{zoom}z/data=!3m1!1e3'],
    [tr('Bing Map'), 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={zoom}', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={zoom}&sp=point.{lat}_{lon}_QGIS%20Point'],
    [tr('Bing Aerial'), 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={zoom}&style=a', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={zoom}&style=a&sp=point.{lat}_{lon}_QGIS%20Point'],
    [tr('MapQuest Map'), 'https://mapquest.com/?center={lat},{lon}&zoom={zoom}', 'https://mapquest.com/?center={lat},{lon}&zoom={zoom}'],
    [tr('MapQuest Aerial'), 'https://mapquest.com/?center={lat},{lon}&zoom={zoom}&maptype=sat', 'https://mapquest.com/?center={lat},{lon}&zoom={zoom}&maptype=sat'],
    [tr('Mapillary Street'), 'https://mapillary.com/app/?lat={lat}&lng={lon}&z={zoom}&mapStyle=Mapillary+streets', 'https://mapillary.com/app/?lat={lat}&lng={lon}&z={zoom}&mapStyle=Mapillary+streets'],
    [tr('Mapillary Aerial'), 'https://www.mapillary.com/app/?lat={lat}&lng={lon}&z={zoom}&mapStyle=Mapillary+satellite', 'https://www.mapillary.com/app/?lat={lat}&lng={lon}&z={zoom}&mapStyle=Mapillary+satellite'],
    [tr('iD Editor ESRI World Imagery'), 'https://preview.ideditor.com/master/#background=EsriWorldImagery&disable_features=boundaries&map={zoom}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features', 'https://preview.ideditor.com/master/#background=EsriWorldImagery&disable_features=boundaries&map={zoom}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features'],
    [tr('iD Editor OpenTopoMap'), 'https://preview.ideditor.com/master/#background=OpenTopoMap&disable_features=boundaries&map={zoom}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features','https://preview.ideditor.com/master/#background=OpenTopoMap&disable_features=boundaries&map={zoom}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features'],
    [tr('Google Earth Web'), 'https://earth.google.com/web/search/{lat},{lon}/', 'https://earth.google.com/web/search/{lat},{lon}/'],
    [tr('Panoramax'), 'https://api.panoramax.xyz/#focus=map&map={zoom}/{lat}/{lon}', 'https://api.panoramax.xyz/#focus=map&map={zoom}/{lat}/{lon}']
]
