import math
import geopy
import geopy.distance
import random

a = 6378245.0
ee = 0.00669342162296594323
pi = 3.14159265358979324


def transform_from_wgs_to_gcj(latitude, longitude):
    if is_location_out_of_china(latitude, longitude):
        adjust_lat, adjust_lon = latitude, longitude
    else:
        adjust_lat = transform_lat(longitude - 105, latitude - 35.0)
        adjust_lon = transform_long(longitude - 105, latitude - 35.0)
        rad_lat = latitude / 180.0 * pi
        magic = math.sin(rad_lat)
        magic = 1 - ee * magic * magic
        math.sqrt_magic = math.sqrt(magic)
        adjust_lat = (adjust_lat *
                      180.0) / ((a * (1 - ee)) / (magic *
                                                  math.sqrt_magic) * pi)
        adjust_lon = (adjust_lon *
                      180.0) / (a / math.sqrt_magic * math.cos(rad_lat) * pi)
        adjust_lat += latitude
        adjust_lon += longitude
    #  Print 'transfromed from ', wgs_loc, ' to ', adjust_loc.
    return adjust_lat, adjust_lon


def is_location_out_of_china(latitude, longitude):
    if (longitude < 72.004 or longitude > 137.8347 or
            latitude < 0.8293 or latitude > 55.8271):
        return True
    return False


def transform_lat(x, y):
    lat = (-100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y +
           0.1 * x * y + 0.2 * math.sqrt(abs(x)))
    lat += (20.0 * math.sin(6.0 * x * pi) + 20.0 *
            math.sin(2.0 * x * pi)) * 2.0 / 3.0
    lat += (20.0 * math.sin(y * pi) + 40.0 *
            math.sin(y / 3.0 * pi)) * 2.0 / 3.0
    lat += (160.0 * math.sin(y / 12.0 * pi) + 320 *
            math.sin(y * pi / 30.0)) * 2.0 / 3.0
    return lat


def transform_long(x, y):
    lon = (300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y +
           0.1 * math.sqrt(abs(x)))
    lon += (20.0 * math.sin(6.0 * x * pi) + 20.0 *
            math.sin(2.0 * x * pi)) * 2.0 / 3.0
    lon += (20.0 * math.sin(x * pi) + 40.0 *
            math.sin(x / 3.0 * pi)) * 2.0 / 3.0
    lon += (150.0 * math.sin(x / 12.0 * pi) + 300.0 *
            math.sin(x / 30.0 * pi)) * 2.0 / 3.0
    return lon


# Returns destination coords given origin coords, distance (Kms) and bearing.
def get_new_coords(init_loc, distance, bearing):
    """
    Given an initial lat/lng, a distance(in kms), and a bearing (degrees),
    this will calculate the resulting lat/lng coordinates.
    """
    origin = geopy.Point(init_loc[0], init_loc[1])
    destination = geopy.distance.distance(kilometers=distance).destination(
        origin, bearing)
    return (destination.latitude, destination.longitude)


# Returns destination coords given origin coords, distance (Ms) and bearing.
# This version is less precise and almost 1 order of magnitude faster than
# using geopy.
def fast_get_new_coords(origin, distance, bearing):
    R = 6371009  # IUGG mean earth radius in kilometers.

    oLat = math.radians(origin[0])
    oLon = math.radians(origin[1])
    b = math.radians(bearing)

    Lat = math.asin(
        math.sin(oLat) * math.cos(distance / R) +
        math.cos(oLat) * math.sin(distance / R) * math.cos(b))

    Lon = oLon + math.atan2(
        math.sin(bearing) * math.sin(distance / R) * math.cos(oLat),
        math.cos(distance / R) - math.sin(oLat) * math.sin(Lat))

    return math.degrees(Lat), math.degrees(Lon)


# Apply a location jitter.
def jitter_location(location=None, maxMeters=10):
    origin = geopy.Point(location[0], location[1])
    bearing = random.randint(0, 360)
    distance = math.sqrt(random.random()) * (float(maxMeters))
    destination = fast_get_new_coords(origin, distance, bearing)
    return (destination[0], destination[1], location[2])
