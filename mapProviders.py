
MAP_PROVIDERS = [
['OSM', 'http://www.openstreetmap.org/#map=@Z@/@LAT@/@LON@','http://www.openstreetmap.org/?mlat=@LAT@&mlon=@LON@#map=@Z@/@LAT@/@LON@'],
['Google Map', 'https://www.google.com/maps/@@LAT@,@LON@,@Z@z', 'https://www.google.com/maps/place/@LAT@,@LON@/@@LAT@,@LON@,@Z@z'],
['Google Aerial', 'https://www.google.com/maps/@@LAT@,@LON@,@Z@z/data=!3m1!1e3', 'https://www.google.com/maps/place/@LAT@,@LON@/@@LAT@,@LON@,@Z@z/data=!3m1!1e3'],
['Bing Map', 'https://www.bing.com/maps?cp=@LAT@~@LON@&lvl=@Z@', 'https://www.bing.com/maps?cp=@LAT@~@LON@&lvl=@Z@&sp=point.@LAT@_@LON@_QGIS%20Point'],
['Bing Aerial', 'https://www.bing.com/maps?cp=@LAT@~@LON@&lvl=@Z@&style=a', 'https://www.bing.com/maps?cp=@LAT@~@LON@&lvl=@Z@&style=a&sp=point.@LAT@_@LON@_QGIS%20Point'],
['MapQuest Map', 'https://www.mapquest.com/latlng/@LAT@,@LON@?centerOnResults=1&zoom=@Z@', 'https://www.mapquest.com/latlng/@LAT@,@LON@?centerOnResults=1&zoom=@Z@'],
['MapQuest Aerial', 'https://www.mapquest.com/latlng/@LAT@,@LON@?centerOnResults=1&maptyp=sat&zoom=@Z@', 'https://www.mapquest.com/latlng/@LAT@,@LON@?centerOnResults=1&maptyp=sat&zoom=@Z@']
]

def mapProviderNames():
    plist =[]
    for x in MAP_PROVIDERS:
        plist.append(x[0])
    return plist