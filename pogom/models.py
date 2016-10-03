#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import itertools
import calendar
import sys
import gc
import time
import geopy
from peewee import SqliteDatabase, InsertQuery, \
    IntegerField, CharField, DoubleField, BooleanField, \
    DateTimeField, fn, DeleteQuery, CompositeKey, FloatField, SQL, TextField
from playhouse.flask_utils import FlaskDB
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import RetryOperationalError
from playhouse.migrate import migrate, MySQLMigrator, SqliteMigrator
from datetime import datetime, timedelta
from base64 import b64encode
from cachetools import TTLCache
from cachetools import cached

from . import config
from .utils import get_pokemon_name, get_pokemon_rarity, get_pokemon_types, get_args
from .transform import transform_from_wgs_to_gcj, get_new_coords
from .customLog import printPokemon

log = logging.getLogger(__name__)

args = get_args()
flaskDb = FlaskDB()
cache = TTLCache(maxsize=100, ttl=60 * 5)

db_schema_version = 9


class MyRetryDB(RetryOperationalError, PooledMySQLDatabase):
    pass


def init_database(app):
    if args.db_type == 'mysql':
        log.info('Connecting to MySQL database on %s:%i', args.db_host, args.db_port)
        connections = args.db_max_connections
        if hasattr(args, 'accounts'):
            connections *= len(args.accounts)
        db = MyRetryDB(
            args.db_name,
            user=args.db_user,
            password=args.db_pass,
            host=args.db_host,
            port=args.db_port,
            max_connections=connections,
            stale_timeout=300)
    else:
        log.info('Connecting to local SQLite database')
        db = SqliteDatabase(args.db)

    app.config['DATABASE'] = db
    flaskDb.init_app(app)

    return db


class BaseModel(flaskDb.Model):

    @classmethod
    def get_all(cls):
        results = [m for m in cls.select().dicts()]
        if args.china:
            for result in results:
                result['latitude'], result['longitude'] = \
                    transform_from_wgs_to_gcj(
                        result['latitude'], result['longitude'])
        return results


class Pokemon(BaseModel):
    # We are base64 encoding the ids delivered by the api
    # because they are too big for sqlite to handle
    encounter_id = CharField(primary_key=True, max_length=50)
    spawnpoint_id = CharField(index=True)
    pokemon_id = IntegerField(index=True)
    latitude = DoubleField()
    longitude = DoubleField()
    disappear_time = DateTimeField(index=True)
    individual_attack = IntegerField(null=True)
    individual_defense = IntegerField(null=True)
    individual_stamina = IntegerField(null=True)
    move_1 = IntegerField(null=True)
    move_2 = IntegerField(null=True)
    last_modified = DateTimeField(null=True, index=True, default=datetime.utcnow)

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    @staticmethod
    def get_active(swLat, swLng, neLat, neLng, timestamp=0, oSwLat=None, oSwLng=None, oNeLat=None, oNeLng=None):
        query = Pokemon.select()
        if not (swLat and swLng and neLat and neLng):
            query = (query
                     .where(Pokemon.disappear_time > datetime.utcnow())
                     .dicts())
        elif timestamp > 0:
            # If timestamp is known only load modified pokemon
            query = (query
                     .where(((Pokemon.last_modified > datetime.utcfromtimestamp(timestamp / 1000)) &
                             (Pokemon.disappear_time > datetime.utcnow())) &
                            ((Pokemon.latitude >= swLat) &
                             (Pokemon.longitude >= swLng) &
                             (Pokemon.latitude <= neLat) &
                             (Pokemon.longitude <= neLng)))
                     .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng:
            # Send Pokemon in view but exclude those within old boundaries. Only send newly uncovered Pokemon.
            query = (query
                     .where(((Pokemon.disappear_time > datetime.utcnow()) &
                            (((Pokemon.latitude >= swLat) &
                              (Pokemon.longitude >= swLng) &
                              (Pokemon.latitude <= neLat) &
                              (Pokemon.longitude <= neLng))) &
                            ~((Pokemon.disappear_time > datetime.utcnow()) &
                              (Pokemon.latitude >= oSwLat) &
                              (Pokemon.longitude >= oSwLng) &
                              (Pokemon.latitude <= oNeLat) &
                              (Pokemon.longitude <= oNeLng))))
                     .dicts())
        else:
            query = (query
                     .where((Pokemon.disappear_time > datetime.utcnow()) &
                            (((Pokemon.latitude >= swLat) &
                              (Pokemon.longitude >= swLng) &
                              (Pokemon.latitude <= neLat) &
                              (Pokemon.longitude <= neLng))))
                     .dicts())

        # Performance: Disable the garbage collector prior to creating a (potentially) large dict with append()
        gc.disable()

        pokemons = []
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            p['pokemon_rarity'] = get_pokemon_rarity(p['pokemon_id'])
            p['pokemon_types'] = get_pokemon_types(p['pokemon_id'])
            if args.china:
                p['latitude'], p['longitude'] = \
                    transform_from_wgs_to_gcj(p['latitude'], p['longitude'])
            pokemons.append(p)

        # Re-enable the GC.
        gc.enable()

        return pokemons

    @staticmethod
    def get_active_by_id(ids, swLat, swLng, neLat, neLng):
        if not (swLat and swLng and neLat and neLng):
            query = (Pokemon
                     .select()
                     .where((Pokemon.pokemon_id << ids) &
                            (Pokemon.disappear_time > datetime.utcnow()))
                     .dicts())
        else:
            query = (Pokemon
                     .select()
                     .where((Pokemon.pokemon_id << ids) &
                            (Pokemon.disappear_time > datetime.utcnow()) &
                            (Pokemon.latitude >= swLat) &
                            (Pokemon.longitude >= swLng) &
                            (Pokemon.latitude <= neLat) &
                            (Pokemon.longitude <= neLng))
                     .dicts())

        # Performance: Disable the garbage collector prior to creating a (potentially) large dict with append()
        gc.disable()

        pokemons = []
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            p['pokemon_rarity'] = get_pokemon_rarity(p['pokemon_id'])
            p['pokemon_types'] = get_pokemon_types(p['pokemon_id'])
            if args.china:
                p['latitude'], p['longitude'] = \
                    transform_from_wgs_to_gcj(p['latitude'], p['longitude'])
            pokemons.append(p)

        # Re-enable the GC.
        gc.enable()

        return pokemons

    @classmethod
    @cached(cache)
    def get_seen(cls, timediff):
        if timediff:
            timediff = datetime.utcnow() - timediff
        pokemon_count_query = (Pokemon
                               .select(Pokemon.pokemon_id,
                                       fn.COUNT(Pokemon.pokemon_id).alias('count'),
                                       fn.MAX(Pokemon.disappear_time).alias('lastappeared')
                                       )
                               .where(Pokemon.disappear_time > timediff)
                               .group_by(Pokemon.pokemon_id)
                               .alias('counttable')
                               )
        query = (Pokemon
                 .select(Pokemon.pokemon_id,
                         Pokemon.disappear_time,
                         Pokemon.latitude,
                         Pokemon.longitude,
                         pokemon_count_query.c.count)
                 .join(pokemon_count_query, on=(Pokemon.pokemon_id == pokemon_count_query.c.pokemon_id))
                 .distinct()
                 .where(Pokemon.disappear_time == pokemon_count_query.c.lastappeared)
                 .dicts()
                 )

        # Performance: Disable the garbage collector prior to creating a (potentially) large dict with append()
        gc.disable()

        pokemons = []
        total = 0
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            pokemons.append(p)
            total += p['count']

        # Re-enable the GC.
        gc.enable()

        return {'pokemon': pokemons, 'total': total}

    @classmethod
    def get_appearances(cls, pokemon_id, timediff):
        '''
        :param pokemon_id: id of pokemon that we need appearances for
        :param timediff: limiting period of the selection
        :return: list of  pokemon  appearances over a selected period
        '''
        if timediff:
            timediff = datetime.utcnow() - timediff
        query = (Pokemon
                 .select(Pokemon.latitude, Pokemon.longitude, Pokemon.pokemon_id, fn.Count(Pokemon.spawnpoint_id).alias('count'), Pokemon.spawnpoint_id)
                 .where((Pokemon.pokemon_id == pokemon_id) &
                        (Pokemon.disappear_time > timediff)
                        )
                 .group_by(Pokemon.latitude, Pokemon.longitude, Pokemon.pokemon_id, Pokemon.spawnpoint_id)
                 .dicts()
                 )

        return list(query)

    @classmethod
    def get_appearances_times_by_spawnpoint(cls, pokemon_id, spawnpoint_id, timediff):
        '''
        :param pokemon_id: id of pokemon that we need appearances times for
        :param spawnpoint_id: spawnpoing id we need appearances times for
        :param timediff: limiting period of the selection
        :return: list of time appearances over a selected period
        '''
        if timediff:
            timediff = datetime.utcnow() - timediff
        query = (Pokemon
                 .select(Pokemon.disappear_time)
                 .where((Pokemon.pokemon_id == pokemon_id) &
                        (Pokemon.spawnpoint_id == spawnpoint_id) &
                        (Pokemon.disappear_time > timediff)
                        )
                 .order_by(Pokemon.disappear_time.asc())
                 .tuples()
                 )

        return list(itertools.chain(*query))

    @classmethod
    def get_spawn_time(cls, disappear_time):
        return (disappear_time + 2700) % 3600

    @classmethod
    def get_spawnpoints(cls, swLat, swLng, neLat, neLng, timestamp=0, oSwLat=None, oSwLng=None, oNeLat=None, oNeLng=None):
        query = Pokemon.select(Pokemon.latitude, Pokemon.longitude, Pokemon.spawnpoint_id, ((Pokemon.disappear_time.minute * 60) + Pokemon.disappear_time.second).alias('time'), fn.Count(Pokemon.spawnpoint_id).alias('count'))

        if timestamp > 0:
            query = (query
                     .where(((Pokemon.last_modified > datetime.utcfromtimestamp(timestamp / 1000))) &
                            ((Pokemon.latitude >= swLat) &
                             (Pokemon.longitude >= swLng) &
                             (Pokemon.latitude <= neLat) &
                             (Pokemon.longitude <= neLng)))
                     .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng:
            # Send spawnpoints in view but exclude those within old boundaries. Only send newly uncovered spawnpoints.
            query = (query
                     .where((((Pokemon.latitude >= swLat) &
                              (Pokemon.longitude >= swLng) &
                              (Pokemon.latitude <= neLat) &
                              (Pokemon.longitude <= neLng))) &
                            ~((Pokemon.latitude >= oSwLat) &
                              (Pokemon.longitude >= oSwLng) &
                              (Pokemon.latitude <= oNeLat) &
                              (Pokemon.longitude <= oNeLng)))
                     .dicts())
        elif swLat and swLng and neLat and neLng:
            query = (query
                     .where((Pokemon.latitude <= neLat) &
                            (Pokemon.latitude >= swLat) &
                            (Pokemon.longitude >= swLng) &
                            (Pokemon.longitude <= neLng)
                            ))

        query = query.group_by(Pokemon.latitude, Pokemon.longitude, Pokemon.spawnpoint_id, SQL('time'))

        queryDict = query.dicts()
        spawnpoints = {}

        for sp in queryDict:
            key = sp['spawnpoint_id']
            disappear_time = cls.get_spawn_time(sp.pop('time'))
            count = int(sp['count'])

            if key not in spawnpoints:
                spawnpoints[key] = sp
            else:
                spawnpoints[key]['special'] = True

            if 'time' not in spawnpoints[key] or count >= spawnpoints[key]['count']:
                spawnpoints[key]['time'] = disappear_time
                spawnpoints[key]['count'] = count

        for sp in spawnpoints.values():
            del sp['count']

        return list(spawnpoints.values())

    @classmethod
    def get_spawnpoints_in_hex(cls, center, steps):
        log.info('Finding spawn points {} steps away'.format(steps))

        n, e, s, w = hex_bounds(center, steps)

        query = (Pokemon
                 .select(Pokemon.latitude.alias('lat'),
                         Pokemon.longitude.alias('lng'),
                         ((Pokemon.disappear_time.minute * 60) + Pokemon.disappear_time.second).alias('time'),
                         Pokemon.spawnpoint_id
                         ))
        query = (query.where((Pokemon.latitude <= n) &
                             (Pokemon.latitude >= s) &
                             (Pokemon.longitude >= w) &
                             (Pokemon.longitude <= e)
                             ))
        # Sqlite doesn't support distinct on columns
        if args.db_type == 'mysql':
            query = query.distinct(Pokemon.spawnpoint_id)
        else:
            query = query.group_by(Pokemon.spawnpoint_id)

        s = list(query.dicts())

        # The distance between scan circles of radius 70 in a hex is 121.2436
        # steps - 1 to account for the center circle then add 70 for the edge
        step_distance = ((steps - 1) * 121.2436) + 70
        # Compare spawnpoint list to a circle with radius steps * 120
        # Uses the direct geopy distance between the center and the spawnpoint.
        filtered = []

        for idx, sp in enumerate(s):
            if geopy.distance.distance(center, (sp['lat'], sp['lng'])).meters <= step_distance:
                filtered.append(s[idx])

        # at this point, 'time' is DISAPPEARANCE time, we're going to morph it to APPEARANCE time
        for location in filtered:
            # examples: time    shifted
            #           0       (   0 + 2700) = 2700 % 3600 = 2700 (0th minute to 45th minute, 15 minutes prior to appearance as time wraps around the hour)
            #           1800    (1800 + 2700) = 4500 % 3600 =  900 (30th minute, moved to arrive at 15th minute)
            # todo: this DOES NOT ACCOUNT for pokemons that appear sooner and live longer, but you'll _always_ have at least 15 minutes, so it works well enough
            location['time'] = cls.get_spawn_time(location['time'])

        return filtered


class Pokestop(BaseModel):
    pokestop_id = CharField(primary_key=True, max_length=50)
    enabled = BooleanField()
    latitude = DoubleField()
    longitude = DoubleField()
    last_modified = DateTimeField(index=True)
    lure_expiration = DateTimeField(null=True, index=True)
    active_fort_modifier = CharField(max_length=50, null=True)
    last_updated = DateTimeField(null=True, index=True, default=datetime.utcnow)

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    @staticmethod
    def get_stops(swLat, swLng, neLat, neLng, timestamp=0, oSwLat=None, oSwLng=None, oNeLat=None, oNeLng=None, lured=False):

        query = Pokestop.select(Pokestop.active_fort_modifier, Pokestop.enabled, Pokestop.latitude, Pokestop.longitude, Pokestop.last_modified, Pokestop.lure_expiration, Pokestop.pokestop_id)

        if not (swLat and swLng and neLat and neLng):
            query = (query
                     .dicts())
        elif timestamp > 0:
            query = (query
                     .where(((Pokestop.last_updated > datetime.utcfromtimestamp(timestamp / 1000))) &
                            (Pokestop.latitude >= swLat) &
                            (Pokestop.longitude >= swLng) &
                            (Pokestop.latitude <= neLat) &
                            (Pokestop.longitude <= neLng))
                     .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng and lured:
            query = (query
                     .where((((Pokestop.latitude >= swLat) &
                              (Pokestop.longitude >= swLng) &
                              (Pokestop.latitude <= neLat) &
                              (Pokestop.longitude <= neLng)) &
                             (Pokestop.active_fort_modifier.is_null(False))) &
                            ~((Pokestop.latitude >= oSwLat) &
                              (Pokestop.longitude >= oSwLng) &
                              (Pokestop.latitude <= oNeLat) &
                              (Pokestop.longitude <= oNeLng)) &
                             (Pokestop.active_fort_modifier.is_null(False)))
                     .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng:
            # Send stops in view but exclude those within old boundaries. Only send newly uncovered stops.
            query = (query
                     .where(((Pokestop.latitude >= swLat) &
                             (Pokestop.longitude >= swLng) &
                             (Pokestop.latitude <= neLat) &
                             (Pokestop.longitude <= neLng)) &
                            ~((Pokestop.latitude >= oSwLat) &
                              (Pokestop.longitude >= oSwLng) &
                              (Pokestop.latitude <= oNeLat) &
                              (Pokestop.longitude <= oNeLng)))
                     .dicts())
        elif lured:
            query = (query
                     .where(((Pokestop.last_updated > datetime.utcfromtimestamp(timestamp / 1000))) &
                            ((Pokestop.latitude >= swLat) &
                             (Pokestop.longitude >= swLng) &
                             (Pokestop.latitude <= neLat) &
                             (Pokestop.longitude <= neLng)) &
                            (Pokestop.active_fort_modifier.is_null(False)))
                     .dicts())

        else:
            query = (query
                     .where((Pokestop.latitude >= swLat) &
                            (Pokestop.longitude >= swLng) &
                            (Pokestop.latitude <= neLat) &
                            (Pokestop.longitude <= neLng))
                     .dicts())

        # Performance: Disable the garbage collector prior to creating a (potentially) large dict with append()
        gc.disable()

        pokestops = []
        for p in query:
            if args.china:
                p['latitude'], p['longitude'] = \
                    transform_from_wgs_to_gcj(p['latitude'], p['longitude'])
            pokestops.append(p)

        # Re-enable the GC.
        gc.enable()

        return pokestops


class Gym(BaseModel):
    UNCONTESTED = 0
    TEAM_MYSTIC = 1
    TEAM_VALOR = 2
    TEAM_INSTINCT = 3

    gym_id = CharField(primary_key=True, max_length=50)
    team_id = IntegerField()
    guard_pokemon_id = IntegerField()
    gym_points = IntegerField()
    enabled = BooleanField()
    latitude = DoubleField()
    longitude = DoubleField()
    last_modified = DateTimeField(index=True)
    last_scanned = DateTimeField(default=datetime.utcnow)

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    @staticmethod
    def get_gyms(swLat, swLng, neLat, neLng, timestamp=0, oSwLat=None, oSwLng=None, oNeLat=None, oNeLng=None):
        if not (swLat and swLng and neLat and neLng):
            results = (Gym
                       .select()
                       .dicts())
        elif timestamp > 0:
            # If timestamp is known only send last scanned Gyms.
            results = (Gym
                       .select()
                       .where(((Gym.last_scanned > datetime.utcfromtimestamp(timestamp / 1000)) &
                              (Gym.latitude >= swLat) &
                              (Gym.longitude >= swLng) &
                              (Gym.latitude <= neLat) &
                              (Gym.longitude <= neLng)))
                       .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng:
            # Send gyms in view but exclude those within old boundaries. Only send newly uncovered gyms.
            results = (Gym
                       .select()
                       .where(((Gym.latitude >= swLat) &
                               (Gym.longitude >= swLng) &
                               (Gym.latitude <= neLat) &
                               (Gym.longitude <= neLng)) &
                              ~((Gym.latitude >= oSwLat) &
                                (Gym.longitude >= oSwLng) &
                                (Gym.latitude <= oNeLat) &
                                (Gym.longitude <= oNeLng)))
                       .dicts())

        else:
            results = (Gym
                       .select()
                       .where((Gym.latitude >= swLat) &
                              (Gym.longitude >= swLng) &
                              (Gym.latitude <= neLat) &
                              (Gym.longitude <= neLng))
                       .dicts())

        # Performance: Disable the garbage collector prior to creating a (potentially) large dict with append()
        gc.disable()

        gyms = {}
        gym_ids = []
        for g in results:
            g['name'] = None
            g['pokemon'] = []
            gyms[g['gym_id']] = g
            gym_ids.append(g['gym_id'])

        if len(gym_ids) > 0:
            pokemon = (GymMember
                       .select(
                           GymMember.gym_id,
                           GymPokemon.cp.alias('pokemon_cp'),
                           GymPokemon.pokemon_id,
                           Trainer.name.alias('trainer_name'),
                           Trainer.level.alias('trainer_level'))
                       .join(Gym, on=(GymMember.gym_id == Gym.gym_id))
                       .join(GymPokemon, on=(GymMember.pokemon_uid == GymPokemon.pokemon_uid))
                       .join(Trainer, on=(GymPokemon.trainer_name == Trainer.name))
                       .where(GymMember.gym_id << gym_ids)
                       .where(GymMember.last_scanned > Gym.last_modified)
                       .order_by(GymMember.gym_id, GymPokemon.cp)
                       .dicts())

            for p in pokemon:
                p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
                gyms[p['gym_id']]['pokemon'].append(p)

            details = (GymDetails
                       .select(
                           GymDetails.gym_id,
                           GymDetails.name)
                       .where(GymDetails.gym_id << gym_ids)
                       .dicts())

            for d in details:
                gyms[d['gym_id']]['name'] = d['name']

        # Re-enable the GC.
        gc.enable()

        return gyms


class ScannedLocation(BaseModel):
    latitude = DoubleField()
    longitude = DoubleField()
    last_modified = DateTimeField(index=True, default=datetime.utcnow)

    class Meta:
        primary_key = CompositeKey('latitude', 'longitude')

    @staticmethod
    def get_recent(swLat, swLng, neLat, neLng, timestamp=0, oSwLat=None, oSwLng=None, oNeLat=None, oNeLng=None):
        activeTime = (datetime.utcnow() - timedelta(minutes=15))
        if timestamp > 0:
            query = (ScannedLocation
                     .select()
                     .where(((ScannedLocation.last_modified >= datetime.utcfromtimestamp(timestamp / 1000))) &
                            (ScannedLocation.latitude >= swLat) &
                            (ScannedLocation.longitude >= swLng) &
                            (ScannedLocation.latitude <= neLat) &
                            (ScannedLocation.longitude <= neLng))
                     .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng:
            # Send scannedlocations in view but exclude those within old boundaries. Only send newly uncovered scannedlocations.
            query = (ScannedLocation
                     .select()
                     .where((((ScannedLocation.last_modified >= activeTime)) &
                             (ScannedLocation.latitude >= swLat) &
                             (ScannedLocation.longitude >= swLng) &
                             (ScannedLocation.latitude <= neLat) &
                             (ScannedLocation.longitude <= neLng)) &
                            ~(((ScannedLocation.last_modified >= activeTime)) &
                              (ScannedLocation.latitude >= oSwLat) &
                              (ScannedLocation.longitude >= oSwLng) &
                              (ScannedLocation.latitude <= oNeLat) &
                              (ScannedLocation.longitude <= oNeLng)))
                     .dicts())
        else:
            query = (ScannedLocation
                     .select()
                     .where((ScannedLocation.last_modified >= activeTime) &
                            (ScannedLocation.latitude >= swLat) &
                            (ScannedLocation.longitude >= swLng) &
                            (ScannedLocation.latitude <= neLat) &
                            (ScannedLocation.longitude <= neLng))
                     .order_by(ScannedLocation.last_modified.asc())
                     .dicts())

        return list(query)


class MainWorker(BaseModel):
    worker_name = CharField(primary_key=True, max_length=50)
    message = CharField()
    method = CharField(max_length=50)
    last_modified = DateTimeField(index=True)


class WorkerStatus(BaseModel):
    username = CharField(primary_key=True, max_length=50)
    worker_name = CharField()
    success = IntegerField()
    fail = IntegerField()
    no_items = IntegerField()
    skip = IntegerField()
    last_modified = DateTimeField(index=True)
    message = CharField(max_length=255)

    @staticmethod
    def get_recent():
        query = (WorkerStatus
                 .select()
                 .where((WorkerStatus.last_modified >=
                        (datetime.utcnow() - timedelta(minutes=5))))
                 .order_by(WorkerStatus.username)
                 .dicts())

        status = []
        for s in query:
            status.append(s)

        return status


class Versions(flaskDb.Model):
    key = CharField()
    val = IntegerField()

    class Meta:
        primary_key = False


class GymMember(BaseModel):
    gym_id = CharField(index=True)
    pokemon_uid = CharField()
    last_scanned = DateTimeField(default=datetime.utcnow)

    class Meta:
        primary_key = False


class GymPokemon(BaseModel):
    pokemon_uid = CharField(primary_key=True, max_length=50)
    pokemon_id = IntegerField()
    cp = IntegerField()
    trainer_name = CharField()
    num_upgrades = IntegerField(null=True)
    move_1 = IntegerField(null=True)
    move_2 = IntegerField(null=True)
    height = FloatField(null=True)
    weight = FloatField(null=True)
    stamina = IntegerField(null=True)
    stamina_max = IntegerField(null=True)
    cp_multiplier = FloatField(null=True)
    additional_cp_multiplier = FloatField(null=True)
    iv_defense = IntegerField(null=True)
    iv_stamina = IntegerField(null=True)
    iv_attack = IntegerField(null=True)
    last_seen = DateTimeField(default=datetime.utcnow)


class Trainer(BaseModel):
    name = CharField(primary_key=True, max_length=50)
    team = IntegerField()
    level = IntegerField()
    last_seen = DateTimeField(default=datetime.utcnow)


class GymDetails(BaseModel):
    gym_id = CharField(primary_key=True, max_length=50)
    name = CharField()
    description = TextField(null=True, default="")
    url = CharField()
    last_scanned = DateTimeField(default=datetime.utcnow)


def hex_bounds(center, steps):
    # Make a box that is (70m * step_limit * 2) + 70m away from the center point
    # Rationale is that you need to travel
    sp_dist = 0.07 * 2 * steps
    n = get_new_coords(center, sp_dist, 0)[0]
    e = get_new_coords(center, sp_dist, 90)[1]
    s = get_new_coords(center, sp_dist, 180)[0]
    w = get_new_coords(center, sp_dist, 270)[1]
    return (n, e, s, w)


def construct_pokemon_dict(pokemons, p, encounter_result, d_t):
    pokemons[p['encounter_id']] = {
        'encounter_id': b64encode(str(p['encounter_id'])),
        'spawnpoint_id': p['spawn_point_id'],
        'pokemon_id': p['pokemon_data']['pokemon_id'],
        'latitude': p['latitude'],
        'longitude': p['longitude'],
        'disappear_time': d_t,
    }
    if encounter_result is not None and 'wild_pokemon' in encounter_result['responses']['ENCOUNTER']:
        pokemon_info = encounter_result['responses']['ENCOUNTER']['wild_pokemon']['pokemon_data']
        attack = pokemon_info.get('individual_attack', 0)
        defense = pokemon_info.get('individual_defense', 0)
        stamina = pokemon_info.get('individual_stamina', 0)
        pokemons[p['encounter_id']].update({
            'individual_attack': attack,
            'individual_defense': defense,
            'individual_stamina': stamina,
            'move_1': pokemon_info['move_1'],
            'move_2': pokemon_info['move_2'],
        })
    else:
        if encounter_result is not None and 'wild_pokemon' not in encounter_result['responses']['ENCOUNTER']:
            log.warning("Error encountering {}, status code: {}".format(p['encounter_id'], encounter_result['responses']['ENCOUNTER']['status']))
        pokemons[p['encounter_id']].update({
            'individual_attack': None,
            'individual_defense': None,
            'individual_stamina': None,
            'move_1': None,
            'move_2': None,
        })


# todo: this probably shouldn't _really_ be in "models" anymore, but w/e
def parse_map(args, map_dict, step_location, db_update_queue, wh_update_queue, api):
    pokemons = {}
    pokestops = {}
    gyms = {}
    skipped = 0
    stopsskipped = 0
    forts = None
    wild_pokemon = None
    pokesfound = False
    fortsfound = False

    cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    for cell in cells:
        if config['parse_pokemon']:
            if len(cell.get('wild_pokemons', [])) > 0:
                pokesfound = True
                if wild_pokemon is None:
                    wild_pokemon = cell.get('wild_pokemons', [])
                else:
                    wild_pokemon += cell.get('wild_pokemons', [])

        if config['parse_pokestops'] or config['parse_gyms']:
            if len(cell.get('forts', [])) > 0:
                fortsfound = True
                if forts is None:
                    forts = cell.get('forts', [])
                else:
                    forts += cell.get('forts', [])

    if pokesfound:
        encounter_ids = [b64encode(str(p['encounter_id'])) for p in wild_pokemon]
        # For all the wild pokemon we found check if an active pokemon is in the database
        query = (Pokemon
                 .select(Pokemon.encounter_id, Pokemon.spawnpoint_id)
                 .where((Pokemon.disappear_time > datetime.utcnow()) & (Pokemon.encounter_id << encounter_ids))
                 .dicts())

        # Store all encounter_ids and spawnpoint_id for the pokemon in query (all thats needed to make sure its unique)
        encountered_pokemon = [(p['encounter_id'], p['spawnpoint_id']) for p in query]

        for p in wild_pokemon:
            if (b64encode(str(p['encounter_id'])), p['spawn_point_id']) in encountered_pokemon:
                # If pokemon has been encountered before dont process it.
                skipped += 1
                continue

            # time_till_hidden_ms was overflowing causing a negative integer.
            # It was also returning a value above 3.6M ms.
            if 0 < p['time_till_hidden_ms'] < 3600000:
                d_t = datetime.utcfromtimestamp(
                    (p['last_modified_timestamp_ms'] +
                     p['time_till_hidden_ms']) / 1000.0)
            else:
                # Set a value of 15 minutes because currently its unknown but larger than 15.
                d_t = datetime.utcfromtimestamp((p['last_modified_timestamp_ms'] + 900000) / 1000.0)

            printPokemon(p['pokemon_data']['pokemon_id'], p['latitude'],
                         p['longitude'], d_t)

            # Scan for IVs and moves
            encounter_result = None
            if (args.encounter and (p['pokemon_data']['pokemon_id'] in args.encounter_whitelist or
                                    p['pokemon_data']['pokemon_id'] not in args.encounter_blacklist and not args.encounter_whitelist)):
                time.sleep(args.encounter_delay)
                encounter_result = api.encounter(encounter_id=p['encounter_id'],
                                                 spawn_point_id=p['spawn_point_id'],
                                                 player_latitude=step_location[0],
                                                 player_longitude=step_location[1])
            construct_pokemon_dict(pokemons, p, encounter_result, d_t)
            if args.webhooks:
                wh_update_queue.put(('pokemon', {
                    'encounter_id': b64encode(str(p['encounter_id'])),
                    'spawnpoint_id': p['spawn_point_id'],
                    'pokemon_id': p['pokemon_data']['pokemon_id'],
                    'latitude': p['latitude'],
                    'longitude': p['longitude'],
                    'disappear_time': calendar.timegm(d_t.timetuple()),
                    'last_modified_time': p['last_modified_timestamp_ms'],
                    'time_until_hidden_ms': p['time_till_hidden_ms'],
                    'individual_attack': pokemons[p['encounter_id']]['individual_attack'],
                    'individual_defense': pokemons[p['encounter_id']]['individual_defense'],
                    'individual_stamina': pokemons[p['encounter_id']]['individual_stamina'],
                    'move_1': pokemons[p['encounter_id']]['move_1'],
                    'move_2': pokemons[p['encounter_id']]['move_2']
                }))

    if fortsfound:
        if config['parse_pokestops']:
            stop_ids = [f['id'] for f in forts if f.get('type') == 1]
            if len(stop_ids) > 0:
                query = (Pokestop
                         .select(Pokestop.pokestop_id, Pokestop.last_modified)
                         .where((Pokestop.pokestop_id << stop_ids))
                         .dicts())
                encountered_pokestops = [(f['pokestop_id'], int((f['last_modified'] - datetime(1970, 1, 1)).total_seconds())) for f in query]

        for f in forts:
            if config['parse_pokestops'] and f.get('type') == 1:  # Pokestops
                if 'active_fort_modifier' in f:
                    lure_expiration = datetime.utcfromtimestamp(
                        f['last_modified_timestamp_ms'] / 1000.0) + timedelta(minutes=30)
                    active_fort_modifier = f['active_fort_modifier']
                    if args.webhooks and args.webhook_updates_only:
                        wh_update_queue.put(('pokestop', {
                            'pokestop_id': b64encode(str(f['id'])),
                            'enabled': f['enabled'],
                            'latitude': f['latitude'],
                            'longitude': f['longitude'],
                            'last_modified_time': f['last_modified_timestamp_ms'],
                            'lure_expiration': calendar.timegm(lure_expiration.timetuple()),
                            'active_fort_modifier': active_fort_modifier
                        }))
                else:
                    lure_expiration, active_fort_modifier = None, None

                # Send all pokéstops to webhooks
                if args.webhooks and not args.webhook_updates_only:
                    # Explicitly set 'webhook_data', in case we want to change the information pushed to webhooks,
                    # similar to above and previous commits.
                    l_e = None

                    if lure_expiration is not None:
                        l_e = calendar.timegm(lure_expiration.timetuple())

                    wh_update_queue.put(('pokestop', {
                        'pokestop_id': b64encode(str(f['id'])),
                        'enabled': f['enabled'],
                        'latitude': f['latitude'],
                        'longitude': f['longitude'],
                        'last_modified': f['last_modified_timestamp_ms'],
                        'lure_expiration': l_e,
                        'active_fort_modifier': active_fort_modifier
                    }))

                if (f['id'], int(f['last_modified_timestamp_ms'] / 1000.0)) in encountered_pokestops:
                    # If pokestop has been encountered before and hasn't changed dont process it.
                    stopsskipped += 1
                    continue

                pokestops[f['id']] = {
                    'pokestop_id': f['id'],
                    'enabled': f['enabled'],
                    'latitude': f['latitude'],
                    'longitude': f['longitude'],
                    'last_modified': datetime.utcfromtimestamp(
                        f['last_modified_timestamp_ms'] / 1000.0),
                    'lure_expiration': lure_expiration,
                    'active_fort_modifier': active_fort_modifier
                }

            elif config['parse_gyms'] and f.get('type') is None:  # Currently, there are only stops and gyms
                # Send gyms to webhooks
                if args.webhooks and not args.webhook_updates_only:
                    # Explicitly set 'webhook_data', in case we want to change the information pushed to webhooks,
                    # similar to above and previous commits.
                    wh_update_queue.put(('gym', {
                        'gym_id': b64encode(str(f['id'])),
                        'team_id': f.get('owned_by_team', 0),
                        'guard_pokemon_id': f.get('guard_pokemon_id', 0),
                        'gym_points': f.get('gym_points', 0),
                        'enabled': f['enabled'],
                        'latitude': f['latitude'],
                        'longitude': f['longitude'],
                        'last_modified': f['last_modified_timestamp_ms']
                    }))

                gyms[f['id']] = {
                    'gym_id': f['id'],
                    'team_id': f.get('owned_by_team', 0),
                    'guard_pokemon_id': f.get('guard_pokemon_id', 0),
                    'gym_points': f.get('gym_points', 0),
                    'enabled': f['enabled'],
                    'latitude': f['latitude'],
                    'longitude': f['longitude'],
                    'last_modified': datetime.utcfromtimestamp(
                        f['last_modified_timestamp_ms'] / 1000.0),
                }

    if len(pokemons):
        db_update_queue.put((Pokemon, pokemons))
    if len(pokestops):
        db_update_queue.put((Pokestop, pokestops))
    if len(gyms):
        db_update_queue.put((Gym, gyms))

    log.info('Parsing found %d pokemons, %d pokestops, and %d gyms.',
             len(pokemons) + skipped,
             len(pokestops) + stopsskipped,
             len(gyms))

    log.debug('Skipped %d Pokemons and %d pokestops.',
              skipped,
              stopsskipped)

    db_update_queue.put((ScannedLocation, {0: {
        'latitude': step_location[0],
        'longitude': step_location[1],
    }}))

    return {
        'count': skipped + stopsskipped + len(pokemons) + len(pokestops) + len(gyms),
        'gyms': gyms,
    }


def parse_gyms(args, gym_responses, wh_update_queue):
    gym_details = {}
    gym_members = {}
    gym_pokemon = {}
    trainers = {}

    i = 0
    for g in gym_responses.values():
        gym_state = g['gym_state']
        gym_id = gym_state['fort_data']['id']

        gym_details[gym_id] = {
            'gym_id': gym_id,
            'name': g['name'],
            'description': g.get('description'),
            'url': g['urls'][0],
        }

        if args.webhooks:
            webhook_data = {
                'id': gym_id,
                'latitude': gym_state['fort_data']['latitude'],
                'longitude': gym_state['fort_data']['longitude'],
                'team': gym_state['fort_data'].get('owned_by_team', 0),
                'name': g['name'],
                'description': g.get('description'),
                'url': g['urls'][0],
                'pokemon': [],
            }

        for member in gym_state.get('memberships', []):
            gym_members[i] = {
                'gym_id': gym_id,
                'pokemon_uid': member['pokemon_data']['id'],
            }

            gym_pokemon[i] = {
                'pokemon_uid': member['pokemon_data']['id'],
                'pokemon_id': member['pokemon_data']['pokemon_id'],
                'cp': member['pokemon_data']['cp'],
                'trainer_name': member['trainer_public_profile']['name'],
                'num_upgrades': member['pokemon_data'].get('num_upgrades', 0),
                'move_1': member['pokemon_data'].get('move_1'),
                'move_2': member['pokemon_data'].get('move_2'),
                'height': member['pokemon_data'].get('height_m'),
                'weight': member['pokemon_data'].get('weight_kg'),
                'stamina': member['pokemon_data'].get('stamina'),
                'stamina_max': member['pokemon_data'].get('stamina_max'),
                'cp_multiplier': member['pokemon_data'].get('cp_multiplier'),
                'additional_cp_multiplier': member['pokemon_data'].get('additional_cp_multiplier', 0),
                'iv_defense': member['pokemon_data'].get('individual_defense', 0),
                'iv_stamina': member['pokemon_data'].get('individual_stamina', 0),
                'iv_attack': member['pokemon_data'].get('individual_attack', 0),
                'last_seen': datetime.utcnow(),
            }

            trainers[i] = {
                'name': member['trainer_public_profile']['name'],
                'team': gym_state['fort_data']['owned_by_team'],
                'level': member['trainer_public_profile']['level'],
                'last_seen': datetime.utcnow(),
            }

            if args.webhooks:
                webhook_data['pokemon'].append({
                    'pokemon_uid': member['pokemon_data']['id'],
                    'pokemon_id': member['pokemon_data']['pokemon_id'],
                    'cp': member['pokemon_data']['cp'],
                    'num_upgrades': member['pokemon_data'].get('num_upgrades', 0),
                    'move_1': member['pokemon_data'].get('move_1'),
                    'move_2': member['pokemon_data'].get('move_2'),
                    'height': member['pokemon_data'].get('height_m'),
                    'weight': member['pokemon_data'].get('weight_kg'),
                    'stamina': member['pokemon_data'].get('stamina'),
                    'stamina_max': member['pokemon_data'].get('stamina_max'),
                    'cp_multiplier': member['pokemon_data'].get('cp_multiplier'),
                    'additional_cp_multiplier': member['pokemon_data'].get('additional_cp_multiplier', 0),
                    'iv_defense': member['pokemon_data'].get('individual_defense', 0),
                    'iv_stamina': member['pokemon_data'].get('individual_stamina', 0),
                    'iv_attack': member['pokemon_data'].get('individual_attack', 0),
                    'trainer_name': member['trainer_public_profile']['name'],
                    'trainer_level': member['trainer_public_profile']['level'],
                })

            i += 1
        if args.webhooks:
            wh_update_queue.put(('gym_details', webhook_data))

    # All this database stuff is synchronous (not using the upsert queue) on purpose.
    # Since the search workers load the GymDetails model from the database to determine if a gym
    # needs rescanned, we need to be sure the GymDetails get fully committed to the database before moving on.
    #
    # We _could_ synchronously upsert GymDetails, then queue the other tables for
    # upsert, but that would put that Gym's overall information in a weird non-atomic state.

    # upsert all the models
    if len(gym_details):
        bulk_upsert(GymDetails, gym_details)
    if len(gym_pokemon):
        bulk_upsert(GymPokemon, gym_pokemon)
    if len(trainers):
        bulk_upsert(Trainer, trainers)

    # This needs to be completed in a transaction, because we don't wany any other thread or process
    # to mess with the GymMembers for the gyms we're updating while we're updating the bridge table.
    with flaskDb.database.transaction():
        # get rid of all the gym members, we're going to insert new records
        if len(gym_details):
            DeleteQuery(GymMember).where(GymMember.gym_id << gym_details.keys()).execute()

        # insert new gym members
        if len(gym_members):
            bulk_upsert(GymMember, gym_members)

    log.info('Upserted %d gyms and %d gym members',
             len(gym_details),
             len(gym_members))


def db_updater(args, q):
    # The forever loop
    while True:
        try:

            while True:
                try:
                    flaskDb.connect_db()
                    break
                except Exception as e:
                    log.warning('%s... Retrying', e)

            # Loop the queue
            while True:
                model, data = q.get()
                bulk_upsert(model, data)
                q.task_done()
                log.debug('Upserted to %s, %d records (upsert queue remaining: %d)',
                          model.__name__,
                          len(data),
                          q.qsize())
                if q.qsize() > 50:
                    log.warning("DB queue is > 50 (@%d); try increasing --db-threads", q.qsize())

        except Exception as e:
            log.exception('Exception in db_updater: %s', e)


def clean_db_loop(args):
    while True:
        try:
            # Clean out old scanned locations
            query = (ScannedLocation
                     .delete()
                     .where((ScannedLocation.last_modified <
                             (datetime.utcnow() - timedelta(minutes=30)))))
            query.execute()

            query = (MainWorker
                     .delete()
                     .where((ScannedLocation.last_modified <
                             (datetime.utcnow() - timedelta(minutes=30)))))
            query.execute()

            query = (WorkerStatus
                     .delete()
                     .where((ScannedLocation.last_modified <
                             (datetime.utcnow() - timedelta(minutes=30)))))
            query.execute()

            # Remove active modifier from expired lured pokestops
            query = (Pokestop
                     .update(lure_expiration=None, active_fort_modifier=None)
                     .where(Pokestop.lure_expiration < datetime.utcnow()))
            query.execute()

            # If desired, clear old pokemon spawns
            if args.purge_data > 0:
                query = (Pokemon
                         .delete()
                         .where((Pokemon.disappear_time <
                                (datetime.utcnow() - timedelta(hours=args.purge_data)))))
                query.execute()

            log.info('Regular database cleaning complete')
            time.sleep(60)
        except Exception as e:
            log.exception('Exception in clean_db_loop: %s', e)


def bulk_upsert(cls, data):
    num_rows = len(data.values())
    i = 0

    if args.db_type == 'mysql':
        step = 120
    else:
        # SQLite has a default max number of parameters of 999,
        # so we need to limit how many rows we insert for it.
        step = 50

    while i < num_rows:
        log.debug('Inserting items %d to %d', i, min(i + step, num_rows))
        try:
            InsertQuery(cls, rows=data.values()[i:min(i + step, num_rows)]).upsert().execute()
        except Exception as e:
            log.warning('%s... Retrying', e)
            continue

        i += step


def create_tables(db):
    db.connect()
    verify_database_schema(db)
    db.create_tables([Pokemon, Pokestop, Gym, ScannedLocation, GymDetails, GymMember, GymPokemon, Trainer, MainWorker, WorkerStatus], safe=True)
    db.close()


def drop_tables(db):
    db.connect()
    db.drop_tables([Pokemon, Pokestop, Gym, ScannedLocation, Versions, GymDetails, GymMember, GymPokemon, Trainer, MainWorker, WorkerStatus, Versions], safe=True)
    db.close()


def verify_database_schema(db):
    if not Versions.table_exists():
        db.create_tables([Versions])

        if ScannedLocation.table_exists():
            # Versions table didn't exist, but there were tables. This must mean the user
            # is coming from a database that existed before we started tracking the schema
            # version. Perform a full upgrade.
            InsertQuery(Versions, {Versions.key: 'schema_version', Versions.val: 0}).execute()
            database_migrate(db, 0)
        else:
            InsertQuery(Versions, {Versions.key: 'schema_version', Versions.val: db_schema_version}).execute()

    else:
        db_ver = Versions.get(Versions.key == 'schema_version').val

        if db_ver < db_schema_version:
            database_migrate(db, db_ver)

        elif db_ver > db_schema_version:
            log.error("Your database version (%i) appears to be newer than the code supports (%i).",
                      db_ver, db_schema_version)
            log.error("Please upgrade your code base or drop all tables in your database.")
            sys.exit(1)


def database_migrate(db, old_ver):
    # Update database schema version
    Versions.update(val=db_schema_version).where(Versions.key == 'schema_version').execute()

    log.info("Detected database version %i, updating to %i", old_ver, db_schema_version)

    # Perform migrations here
    migrator = None
    if args.db_type == 'mysql':
        migrator = MySQLMigrator(db)
    else:
        migrator = SqliteMigrator(db)

#   No longer necessary, we're doing this at schema 4 as well
#    if old_ver < 1:
#        db.drop_tables([ScannedLocation])

    if old_ver < 2:
        migrate(migrator.add_column('pokestop', 'encounter_id', CharField(max_length=50, null=True)))

    if old_ver < 3:
        migrate(
            migrator.add_column('pokestop', 'active_fort_modifier', CharField(max_length=50, null=True)),
            migrator.drop_column('pokestop', 'encounter_id'),
            migrator.drop_column('pokestop', 'active_pokemon_id')
        )

    if old_ver < 4:
        db.drop_tables([ScannedLocation])

    if old_ver < 5:
        # Some pokemon were added before the 595 bug was "fixed"
        # Clean those up for a better UX
        query = (Pokemon
                 .delete()
                 .where(Pokemon.disappear_time >
                        (datetime.utcnow() - timedelta(hours=24))))
        query.execute()

    if old_ver < 6:
        migrate(
            migrator.add_column('gym', 'last_scanned', DateTimeField(null=True)),
        )

    if old_ver < 7:
        migrate(
            migrator.drop_column('gymdetails', 'description'),
            migrator.add_column('gymdetails', 'description', TextField(null=True, default=""))
        )

    if old_ver < 8:
        migrate(
            migrator.add_column('pokemon', 'individual_attack', IntegerField(null=True, default=0)),
            migrator.add_column('pokemon', 'individual_defense', IntegerField(null=True, default=0)),
            migrator.add_column('pokemon', 'individual_stamina', IntegerField(null=True, default=0)),
            migrator.add_column('pokemon', 'move_1', IntegerField(null=True, default=0)),
            migrator.add_column('pokemon', 'move_2', IntegerField(null=True, default=0))
        )

    if old_ver < 9:
        migrate(
            migrator.add_column('pokemon', 'last_modified', DateTimeField(null=True, index=True)),
            migrator.add_column('pokestop', 'last_updated', DateTimeField(null=True, index=True))
        )
