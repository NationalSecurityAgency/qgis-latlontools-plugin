
def maidenGridCenter(maiden):
    """
        maiden is a string the is even and between 2 to 8 characters
        It returns the center point of a maiden grid and throws an exception
        on error
    """
    if not isinstance(maiden, str):
        raise TypeError('Maidenhead locator must be a string')

    maiden = maiden.strip().upper()

    N = len(maiden)
    if not 8 >= N >= 2 and N % 2 == 0:
        raise ValueError('Maidenhead locator requires 2-8 characters, even number of characters')

    Oa = ord('A')
    lon = -180.
    lat = -90.
# %% first pair
    isValid(maiden[0], 0)
    isValid(maiden[1], 0)
    lon += (ord(maiden[0])-Oa)*20
    lat += (ord(maiden[1])-Oa)*10
    if N == 2:
        lon += 10
        lat += 5
# %% second pair
    if N >= 4:
        isValid(maiden[2], 1)
        isValid(maiden[3], 1)
        lon += int(maiden[2])*2
        lat += int(maiden[3])*1
    if N == 4:
        lon += 1
        lat += 0.5
# %%
    if N >= 6:
        isValid(maiden[4], 2)
        isValid(maiden[5], 2)
        lon += (ord(maiden[4])-Oa) * 5./60
        lat += (ord(maiden[5])-Oa) * 2.5/60
    if N == 6:
        lon += 5./120
        lat += 2.5/120
# %%
    if N == 8:
        lon += int(maiden[6]) * 5./600
        lat += int(maiden[7]) * 2.5/600
        lon += 5./1200
        lat += 2.5/1200

    return lat, lon

def maidenGrid(maiden):
    """
        maiden is a string the is even and between 2 to 8 characters
        It returns the center point of a maiden grid and throws an exception
        on error
    """
    if not isinstance(maiden, str):
        raise TypeError('Maidenhead locator must be a string')

    maiden = maiden.strip().upper()

    N = len(maiden)
    if not 8 >= N >= 2 and N % 2 == 0:
        raise ValueError('Maidenhead locator requires 2-8 characters, even number of characters')

    Oa = ord('A')
    lon = -180.
    lat = -90.
# %% first pair
    isValid(maiden[0], 0)
    isValid(maiden[1], 0)
    lon += (ord(maiden[0])-Oa)*20
    lat += (ord(maiden[1])-Oa)*10
    if N == 2:
        lon1 = lon
        lat1 = lat
        lon2 = lon + 20
        lat2 = lat + 10
        lon += 10
        lat += 5
# %% second pair
    if N >= 4:
        isValid(maiden[2], 1)
        isValid(maiden[3], 1)
        lon += int(maiden[2])*2
        lat += int(maiden[3])*1
    if N == 4:
        lon1 = lon
        lat1 = lat
        lon2 = lon + 2
        lat2 = lat + 1
        lon += 1
        lat += 0.5
# %%
    if N >= 6:
        isValid(maiden[4], 2)
        isValid(maiden[5], 2)
        lon += (ord(maiden[4])-Oa) * 5./60
        lat += (ord(maiden[5])-Oa) * 2.5/60
    if N == 6:
        lon1 = lon
        lat1 = lat
        lon2 = lon + 5./60
        lat2 = lat + 2.5/60
        lon += 5./120
        lat += 2.5/120
# %%
    if N == 8:
        lon += int(maiden[6]) * 5./600
        lat += int(maiden[7]) * 2.5/600
        lon1 = lon
        lat1 = lat
        lon2 = lon + 5./600
        lat2 = lat + 2.5/600
        lon += 5./1200
        lat += 2.5/1200

    return lat, lon, lat1, lon1, lat2, lon2

def isValid(c, level):
    if level == 0:
        if not 'R' >= c >= 'A':
            raise ValueError('Invalid maidenhead encoding')
    if level == 1 or level == 3:
        if not '9' >= c >= '0':
            raise ValueError('Invalid maidenhead encoding')
    if level == 2:
        if not 'X' >= c >= 'A':
            raise ValueError('Invalid maidenhead encoding')
    return(True)

def toMaiden(lat, lon=None,precision = 3):
    """
    Returns a maidenhead string for latitude, longitude at specified level.

    Parameters
    ----------

    lat : float or tuple of float
        latitude or tuple of latitude, longitude
    lon : float, optional
        longitude (if not given tuple)
    precision : int, optional
        level of precision (length of maidenhead grid string output)

    Returns
    -------

    maiden : str
        Maidenhead grid string of specified precision
    """

    if lon < -180.0 or lon > 180.0 or lat < -90.0 or lat > 90.0:
        raise ValueError('Maidenhead: invalid latitude and longitude')
    A = ord('A')
    a = divmod(lon+180, 20)
    b = divmod(lat+90, 10)
    maiden = chr(A+int(a[0])) + chr(A+int(b[0]))
    lon = a[1] / 2.
    lat = b[1]
    i = 1
    while i < precision:
        i += 1
        a = divmod(lon, 1)
        b = divmod(lat, 1)
        if not (i % 2):
            maiden += str(int(a[0])) + str(int(b[0]))
            lon = 24 * a[1]
            lat = 24 * b[1]
        else:
            maiden += chr(A+int(a[0])) + chr(A+int(b[0]))
            lon = 10 * a[1]
            lat = 10 * b[1]

    if len(maiden) >= 6:
        maiden = maiden[:4] + maiden[4:6].lower() + maiden[6:]

    return maiden

