#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Fake PokemonGo API

This is a simplistic flask app to emulate what a pokemon go api returns.

It *does not* speak protobuff, and uses a hacky internal re-routing. That said,
it does the trick well enough in my testing.

When first "logged into" it will create a static map of evenly distributed
gyms and poke stops. As each "scan" is run, it will gerenate a set of pokemon
for that scan area. "New" pokemon will be found every 10 minutes.

You can run this as is, and then just add `-m http://127.0.0.1:9090` to your
runserver.py call to start using it.
'''

import logging
import configargparse
import math

from flask import Flask, jsonify
from random import randint, getrandbits, seed, random
from uuid import uuid4
from time import time
from s2sphere import CellId, LatLng
import geopy
from geopy.distance import VincentyDistance
from geopy.distance import vincenty

logging.basicConfig(format='%(asctime)s [%(threadName)16s][%(module)14s][%(levelname)8s] %(message)s')
log = logging.getLogger()

# Configish
parser = configargparse.ArgParser()
parser.add_argument('-H', '--host', help='Server Host', default='127.0.0.1')
parser.add_argument('-p', '--port', help='Server Port', default=9090, type=int)
parser.add_argument('-d', '--debug', help='Debug Mode', action='store_true')
parser.set_defaults(DEBUG=False)
args = parser.parse_args()

if args.debug:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)


# A holder of gyms/pokestops
forts = []


def getRandomPoint(location=None, maxMeters=70):
    origin = geopy.Point(location[0], location[1])
    b = randint(0, 360)
    d = math.sqrt(random()) * (float(maxMeters) / 1000)
    destination = VincentyDistance(kilometers=d).destination(origin, b)
    return (destination.latitude, destination.longitude)


# TODO: This method is suuuuper inefficient.
#       Namely, it loops over EVERY POSSIBLE fort and does a distance calc
#       Not a time-cheap operation to do at all. It would be way more efficient
#       if we had all the forts setup with s2 locations and could more quickly
#       query for 'within XYZ cells'. Or something like that :/
def getForts(location):
    global forts

    lforts = []
    for i in forts:
        f = (i['latitude'], i['longitude'])
        d = vincenty(location, f).meters
        if d < 900:
            lforts.append(i)

    return lforts


def makeWildPokemon(location):
    # Cause the randomness to only shift every N minutes (thus new pokes every N minutes)
    offset = int(time() % 3600) / 10
    seedid = str(location[0]) + str(location[1]) + str(offset)
    seed(seedid)

    # Now, collect the pokes for this can point
    pokes = []
    for i in range(randint(0, 2)):
        coords = getRandomPoint(location)
        ll = LatLng.from_degrees(coords[0], coords[1])
        cellId = CellId.from_lat_lng(ll).parent(20).to_token()
        pokes.append({
            'encounter_id': 'pkm' + seedid + str(i),
            'last_modified_timestamp_ms': int((time() - 10) * 1000),
            'latitude': coords[0],
            'longitude': coords[1],
            'pokemon_data': {'pokemon_id': randint(1, 140)},
            'spawn_point_id': cellId,
            'time_till_hidden_ms': randint(60, 600) * 1000
        })
    return pokes

# Fancy app time
app = Flask(__name__)


@app.route('/')
def api_root():
    return 'This here be a Fake PokemonGo API Endpoint Server'


@app.route('/login/<lat>/<lng>/<r>')
def api_login(lat, lng, r):
    global forts

    if len(forts):
        # already generated
        return jsonify(forts)

    # coerce types
    r = int(r)  # radius in meters
    lat = float(lat)
    lng = float(lng)

    forts = []
    area = 3.14 * (r * r)

    # One gym every N sq.m
    gymCount = int(math.ceil(area / 25000))

    # One pks every N sq.m
    pksCount = int(math.ceil(area / 15000))

    # Gyms
    for i in range(gymCount):
        coords = getRandomPoint(location=(lat, lng), maxMeters=r)
        forts.append({
            'enabled': True,
            'guard_pokemon_id': randint(1, 140),
            'gym_points': randint(1, 30000),
            'id': 'gym-{}'.format(i),
            'is_in_battle': not getrandbits(1),
            'last_modified_timestamp_ms': int((time() - 10) * 1000),
            'latitude': coords[0],
            'longitude': coords[1],
            'owned_by_team': randint(0, 3)
        })

    # Pokestops
    for i in range(pksCount):
        coords = getRandomPoint(location=(lat, lng), maxMeters=r)
        forts.append({
            'enabled': True,
            'id': 'pks-{}'.format(i),
            'last_modified_timestamp_ms': int((time() - 10) * 1000),
            'latitude': coords[0],
            'longitude': coords[1],
            'type': 1
        })

    log.info('Login for location %f,%f generated %d gyms, %d pokestop', lat, lng, gymCount, pksCount)
    return jsonify(forts)


@app.route('/scan/<lat>/<lng>')
def api_scan(lat, lng):
    location = (float(lat), float(lng))
    cells = []
    # for i in range(randint(60,70)):
    for i in range(3):
        cells.append({
            'current_timestamp_ms': int(time() * 1000),
            'forts': getForts(location),
            's2_cell_id': uuid4(),  # wrong, but also unused so it doesn't matter
            'wild_pokemons': makeWildPokemon(location),
            'catchable_pokemons': [],  # unused
            'nearby_pokemons': []  # unused
        })
    return jsonify({'responses': {'GET_MAP_OBJECTS': {'map_cells': cells}}})

if __name__ == '__main__':
    app.run(threaded=True, debug=args.debug, host=args.host, port=args.port)
