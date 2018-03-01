import logging
import math
from overpy import Overpass
from geofence import Geofences
from models import Gym, init_database
from s2sphere import LatLng, CellId

# Specify app for a database connection and log to show module name in logs.
app = None
log = logging.getLogger(__name__)
db = init_database(app)
EARTH_CIRCUMFERENCE_METERS = 400750170


def earthMetersToRadians(meters):
    return (2 * math.pi) * (float(meters) / EARTH_CIRCUMFERENCE_METERS)


def ex_query(s, w, n, e):
    # Query Overpass for known gym areas.
    api = Overpass()
    result = api.query("""
    [out:json]
    [date:"2016-07-10T00:00:00Z"]
    [timeout:620]
    [bbox:{},{},{},{}];
    (
        // Tags that are confirmed to classify gyms as 'parks' for EX Raids.
        way[leisure=park];
        way[landuse=recreation_ground];
        way[leisure=recreation_ground];
        way[leisure=pitch];
        way[leisure=garden];
        way[leisure=golf_course];
        way[leisure=playground];
        way[landuse=meadow];
        way[landuse=grass];
        way[landuse=greenfield];
        way[natural=scrub];
        way[natural=heath];
        way[natural=grassland];
        way[landuse=farmyard];
        way[landuse=vineyard];
        way[landuse=farmland];
        way[landuse=orchard];
    );
    out body;
    >;
    out skel qt;
    """.format(s, w, n, e))

    return result


def update_ex_gyms(geofence):
    # Parse geofence file.
    log.info('Finding border points from geofence.')
    geofence = Geofences.parse_geofences_file(geofence, '')
    fence = geofence[0]['polygon']

    # Figure out borders for bounding box.
    south = min(fence, key=lambda ev: ev['lat'])['lat']
    west = min(fence, key=lambda ev: ev['lon'])['lon']
    north = max(fence, key=lambda ev: ev['lat'])['lat']
    east = max(fence, key=lambda ev: ev['lon'])['lon']

    log.info('Finding parks within zone.')
    ex_gyms = ex_query(south, west, north, east)
    gyms = Gym.get_gyms(south, west, north, east)

    if not gyms:
        log.error('No gyms detected within geofence, exiting.')
        exit(1)

    log.info(
        'Checking {} gyms against {} parks.'.format(len(gyms),
                                                    len(ex_gyms.ways)))
    # Retrieve list of confirmed EX gyms to update the DB.
    confirmed_ex_gyms = filter(lambda gym: __gym_is_ex_gym(gym, ex_gyms),
                               gyms.values())

    if not confirmed_ex_gyms:
        log.info('No EX-eligible gyms found.')
        exit(1)
    Gym.set_gyms_in_park(confirmed_ex_gyms, True)


def __gym_is_ex_gym(gym, ex_gyms):
    gympoint = [float(gym['latitude']),
                float(gym['longitude'])]
    s2_center = get_s2_cell_center(gympoint[0], gympoint[1], 20)

    for way in ex_gyms.ways:
        data = [{'lat': float(e.lat), 'lon': float(e.lon)} for e in way.nodes]

        if Geofences.is_point_in_polygon_custom(s2_center, data):
            gymname = gym['name'] or gym['gym_id']
            log.info('{} is eligible for EX raids.'.format(
                gymname.encode('utf8')))
            return True
    return False


def get_s2_cell_center(lat, lng, level):
    lat_lng = LatLng.from_degrees(lat, lng)
    cell_id = CellId.from_lat_lng(lat_lng).parent(level)
    center = cell_id.to_lat_lng()
    return {'lat': float(center.lat().degrees),
            'lon': float(center.lng().degrees)}
