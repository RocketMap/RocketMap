import math
import geopy

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
        adjust_lat = (adjust_lat * 180.0) / ((a * (1 - ee)) / (magic * math.sqrt_magic) * pi)
        adjust_lon = (adjust_lon * 180.0) / (a / math.sqrt_magic * math.cos(rad_lat) * pi)
        adjust_lat += latitude
        adjust_lon += longitude
    #  print 'transfromed from ', wgs_loc, ' to ', adjust_loc
    return adjust_lat, adjust_lon


def is_location_out_of_china(latitude, longitude):
    if longitude < 72.004 or longitude > 137.8347 or latitude < 0.8293 or latitude > 55.8271:
        return True
    return False


def transform_lat(x, y):
    lat = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    lat += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
    lat += (20.0 * math.sin(y * pi) + 40.0 * math.sin(y / 3.0 * pi)) * 2.0 / 3.0
    lat += (160.0 * math.sin(y / 12.0 * pi) + 320 * math.sin(y * pi / 30.0)) * 2.0 / 3.0
    return lat


def transform_long(x, y):
    lon = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    lon += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
    lon += (20.0 * math.sin(x * pi) + 40.0 * math.sin(x / 3.0 * pi)) * 2.0 / 3.0
    lon += (150.0 * math.sin(x / 12.0 * pi) + 300.0 * math.sin(x / 30.0 * pi)) * 2.0 / 3.0
    return lon


def get_new_coords(init_loc, distance, bearing):
    """
    Given an initial lat/lng, a distance(in kms), and a bearing (degrees),
    this will calculate the resulting lat/lng coordinates.
    """
    origin = geopy.Point(init_loc[0], init_loc[1])
    destination = geopy.distance.distance(kilometers=distance).destination(origin, bearing)
    return (destination.latitude, destination.longitude)


def generate_location_steps(initial_loc, step_count, step_distance):
    # Bearing (degrees)
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270

    pulse_radius = step_distance         # km - radius of players heartbeat is 70m
    xdist = math.sqrt(3) * pulse_radius  # dist between column centers
    ydist = 3 * (pulse_radius / 2)       # dist between row centers

    results = []

    results.append((initial_loc[0], initial_loc[1], 0))

    if step_count > 1:
        loc = initial_loc

        # upper part
        ring = 1
        while ring < step_count:

            loc = get_new_coords(loc, xdist, WEST if ring % 2 == 1 else EAST)
            results.append((loc[0], loc[1], 0))

            for i in range(ring):
                loc = get_new_coords(loc, ydist, NORTH)
                loc = get_new_coords(loc, xdist / 2, EAST if ring % 2 == 1 else WEST)
                results.append((loc[0], loc[1], 0))

            for i in range(ring):
                loc = get_new_coords(loc, xdist, EAST if ring % 2 == 1 else WEST)
                results.append((loc[0], loc[1], 0))

            for i in range(ring):
                loc = get_new_coords(loc, ydist, SOUTH)
                loc = get_new_coords(loc, xdist / 2, EAST if ring % 2 == 1 else WEST)
                results.append((loc[0], loc[1], 0))

            ring += 1

        # lower part
        ring = step_count - 1

        loc = get_new_coords(loc, ydist, SOUTH)
        loc = get_new_coords(loc, xdist / 2, WEST if ring % 2 == 1 else EAST)
        results.append((loc[0], loc[1], 0))

        while ring > 0:

            if ring == 1:
                loc = get_new_coords(loc, xdist, WEST)
                results.append((loc[0], loc[1], 0))

            else:
                for i in range(ring - 1):
                    loc = get_new_coords(loc, ydist, SOUTH)
                    loc = get_new_coords(loc, xdist / 2, WEST if ring % 2 == 1 else EAST)
                    results.append((loc[0], loc[1], 0))

                for i in range(ring):
                    loc = get_new_coords(loc, xdist, WEST if ring % 2 == 1 else EAST)
                    results.append((loc[0], loc[1], 0))

                for i in range(ring - 1):
                    loc = get_new_coords(loc, ydist, NORTH)
                    loc = get_new_coords(loc, xdist / 2, WEST if ring % 2 == 1 else EAST)
                    results.append((loc[0], loc[1], 0))

                loc = get_new_coords(loc, xdist, EAST if ring % 2 == 1 else WEST)
                results.append((loc[0], loc[1], 0))

            ring -= 1

    # This will pull the last few steps back to the front of the list
    # so you get a "center nugget" at the beginning of the scan, instead
    # of the entire nothern area before the scan spots 70m to the south.
    if step_count >= 3:
        if step_count == 3:
            results = results[-2:] + results[:-2]
        else:
            results = results[-7:] + results[:-7]

    return results
