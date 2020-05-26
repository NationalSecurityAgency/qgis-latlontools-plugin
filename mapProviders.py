MAP_PROVIDERS = [
    ['OSM', 'http://www.openstreetmap.org/#map={z}/{lat}/{lon}', 'http://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map={z}/{lat}/{lon}'],
    ['Google Map', 'https://www.google.com/maps/@{lat},{lon},{z}z', 'https://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},{z}z'],
    ['Google Aerial', 'https://www.google.com/maps/@{lat},{lon},{z}z/data=!3m1!1e3', 'https://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},{z}z/data=!3m1!1e3'],
    ['Bing Map', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={z}', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={z}&sp=point.{lat}_{lon}_QGIS%20Point'],
    ['Bing Aerial', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={z}&style=a', 'https://www.bing.com/maps?cp={lat}~{lon}&lvl={z}&style=a&sp=point.{lat}_{lon}_QGIS%20Point'],
    ['MapQuest Map', 'https://mapquest.com/?center={lat},{lon}&zoom={z}', 'https://mapquest.com/?center={lat},{lon}&zoom={z}'],
    ['MapQuest Aerial', 'https://mapquest.com/?center={lat},{lon}&zoom={z}&maptype=sat', 'https://mapquest.com/?center={lat},{lon}&zoom={z}&maptype=sat'],
    ['Mapillary Street', 'https://mapillary.com/app/?lat={lat}&lng={lon}&z={z}&mapStyle=Mapillary+streets', 'https://mapillary.com/app/?lat={lat}&lng={lon}&z={z}&mapStyle=Mapillary+streets'],
    ['Mapillary Aerial', 'https://www.mapillary.com/app/?lat={lat}&lng={lon}&z={z}&mapStyle=Mapillary+satellite', 'https://www.mapillary.com/app/?lat={lat}&lng={lon}&z={z}&mapStyle=Mapillary+satellite'],
    ['iD Editor ESRI World Imagery', 'https://preview.ideditor.com/master/#background=EsriWorldImagery&disable_features=boundaries&map={z}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features', 'https://preview.ideditor.com/master/#background=EsriWorldImagery&disable_features=boundaries&map={z}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features'],
    ['iD Editor OpenTopoMap', 'https://preview.ideditor.com/master/#background=OpenTopoMap&disable_features=boundaries&map={z}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features','https://preview.ideditor.com/master/#background=OpenTopoMap&disable_features=boundaries&map={z}/{lat}/{lon}&overlays=BANO&photo_overlay=mapillary-map-features']
]


def mapProviderNames():
    plist = []
    for x in MAP_PROVIDERS:
        plist.append(x[0])
    plist.append('Google Earth (If Installed)')
    return plist
