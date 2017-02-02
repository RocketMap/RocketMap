#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import requests
import random
from .models import LocationAltitude

log = logging.getLogger(__name__)

# Altitude used when no_altitude_cache is enabled
fallback_altitude = None


def get_gmaps_altitude(lat, lng, gmaps_key):
    try:
        r_session = requests.Session()
        response = r_session.get((
            'https://maps.googleapis.com/maps/api/elevation/json?' +
            'locations={},{}&key={}').format(lat, lng, gmaps_key))
        response = response.json()
        status = response['status']
        results = response.get('results', [])
        result = results[0] if results else {}
        altitude = result.get('elevation', None)
    except:
        log.error('Unable to retrieve altitude from Google APIs.')
        status = 'UNKNOWN_ERROR'
        altitude = None

    return (altitude, status)


def randomize_altitude(altitude, altitude_variance):
    if altitude_variance > 0:
        altitude = (altitude +
                    random.randrange(-1 * altitude_variance,
                                     altitude_variance) +
                    float(format(random.random(), '.13f')))
    else:
        altitude = altitude + float(format(random.random(), '.13f'))

    return altitude


# Only once fetched altitude
def get_fallback_altitude(args, loc):
    global fallback_altitude

    if fallback_altitude is None:
        (fallback_altitude, status) = get_gmaps_altitude(loc[0], loc[1],
                                                         args.gmaps_key)

    return fallback_altitude


# Get altitude from the db or try to fetch from gmaps api,
# otherwise, default altitude
def cached_get_altitude(args, loc):
    altitude = LocationAltitude.get_nearby_altitude(loc)

    if altitude is None:
        (altitude, status) = get_gmaps_altitude(loc[0], loc[1], args.gmaps_key)
        if altitude is not None:
            LocationAltitude.save_altitude(loc, altitude)

    return altitude


# Get altitude main method
def get_altitude(args, loc):
    if args.no_altitude_cache:
        altitude = get_fallback_altitude(args, loc)
    else:
        altitude = cached_get_altitude(args, loc)

    if altitude is None:
        altitude = args.altitude

    return randomize_altitude(altitude, args.altitude_variance)
