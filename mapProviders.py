MAP_PROVIDERS = [
    ['OSM', 'http://www.openstreetmap.org/#map={zoom}/{lat}/{lon}', 'http://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map={zoom}/{lat}/{lon}'],
    ['Google Map', 'https://www.google.com/maps/@{lat},{lon},{zoom}z', 'https://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},{zoom}z'],
    ['Google Aerial', 'https://www.google.com/maps/@{lat},{lon},{zoom}z/data=!3m1!1e3', 'https://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},{zoom}z/data=!3m1!1e3'],
    ['Bing Map', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={zoom}', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={zoom}&sp=point.{lat}_{lon}_QGIS%20Point'],
    ['Bing Aerial', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={zoom}&style=a', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={zoom}&style=a&sp=point.{lat}_{lon}_QGIS%20Point'],
    ['MapQuest Map', 'https://mapquest.com/?center={lat},{lon}&zoom={zoom}', 'https://mapquest.com/?center={lat},{lon}&zoom={zoom}'],
    ['MapQuest Aerial', 'https://mapquest.com/?center={lat},{lon}&zoom={zoom}&maptype=sat', 'https://mapquest.com/?center={lat},{lon}&zoom={zoom}&maptype=sat'],
    ['Mapillary Street', 'https://mapillary.com/app/?lat={lat}&lng={lon}&z={zoom}&mapStyle=Mapillary+streets', 'https://mapillary.com/app/?lat={lat}&lng={lon}&z={zoom}&mapStyle=Mapillary+streets'],
    ['Mapillary Aerial', 'https://www.mapillary.com/app/?lat={lat}&lng={lon}&z={zoom}&mapStyle=Mapillary+satellite', 'https://www.mapillary.com/app/?lat={lat}&lng={lon}&z={zoom}&mapStyle=Mapillary+satellite'],
    ['iD Editor ESRI World Imagery', 'https://preview.ideditor.com/master/#background=EsriWorldImagery&disable_features=boundaries&map={zoom}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features', 'https://preview.ideditor.com/master/#background=EsriWorldImagery&disable_features=boundaries&map={zoom}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features'],
    ['iD Editor OpenTopoMap', 'https://preview.ideditor.com/master/#background=OpenTopoMap&disable_features=boundaries&map={zoom}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features','https://preview.ideditor.com/master/#background=OpenTopoMap&disable_features=boundaries&map={zoom}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features']
]
