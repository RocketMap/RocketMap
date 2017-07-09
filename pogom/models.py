#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import itertools
import calendar
import sys
import traceback
import gc
import time
import geopy
import math
from peewee import (InsertQuery, Check, CompositeKey, ForeignKeyField,
                    SmallIntegerField, IntegerField, CharField, DoubleField,
                    BooleanField, DateTimeField, fn, DeleteQuery, FloatField,
                    TextField, JOIN, OperationalError)
from playhouse.flask_utils import FlaskDB
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import RetryOperationalError, case
from playhouse.migrate import migrate, MySQLMigrator, SqliteMigrator
from playhouse.sqlite_ext import SqliteExtDatabase
from datetime import datetime, timedelta
from base64 import b64encode
from cachetools import TTLCache
from cachetools import cached
from timeit import default_timer

from . import config
from .utils import (get_pokemon_name, get_pokemon_rarity, get_pokemon_types,
                    get_args, cellid, in_radius, date_secs, clock_between,
                    get_move_name, get_move_damage, get_move_energy,
                    get_move_type, clear_dict_response, calc_pokemon_level)
from .transform import transform_from_wgs_to_gcj, get_new_coords
from .customLog import printPokemon

from .account import (tutorial_pokestop_spin, check_login,
                      setup_api, encounter_pokemon_request)

log = logging.getLogger(__name__)

args = get_args()
flaskDb = FlaskDB()
cache = TTLCache(maxsize=100, ttl=60 * 5)

db_schema_version = 20


class MyRetryDB(RetryOperationalError, PooledMySQLDatabase):
    pass


# Reduction of CharField to fit max length inside 767 bytes for utf8mb4 charset
class Utf8mb4CharField(CharField):
    def __init__(self, max_length=191, *args, **kwargs):
        self.max_length = max_length
        super(CharField, self).__init__(*args, **kwargs)


def init_database(app):
    if args.db_type == 'mysql':
        log.info('Connecting to MySQL database on %s:%i...',
                 args.db_host, args.db_port)
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
            stale_timeout=300,
            charset='utf8mb4')
    else:
        log.info('Connecting to local SQLite database')
        db = SqliteExtDatabase(args.db,
                               pragmas=(
                                   ('journal_mode', 'WAL'),
                                   ('mmap_size', 1024 * 1024 * 32),
                                   ('cache_size', 10000),
                                   ('journal_size_limit', 1024 * 1024 * 4),))

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
    # because they are too big for sqlite to handle.
    encounter_id = Utf8mb4CharField(primary_key=True, max_length=50)
    spawnpoint_id = Utf8mb4CharField(index=True)
    pokemon_id = SmallIntegerField(index=True)
    latitude = DoubleField()
    longitude = DoubleField()
    disappear_time = DateTimeField(index=True)
    individual_attack = SmallIntegerField(null=True)
    individual_defense = SmallIntegerField(null=True)
    individual_stamina = SmallIntegerField(null=True)
    move_1 = SmallIntegerField(null=True)
    move_2 = SmallIntegerField(null=True)
    cp = SmallIntegerField(null=True)
    cp_multiplier = FloatField(null=True)
    weight = FloatField(null=True)
    height = FloatField(null=True)
    gender = SmallIntegerField(null=True)
    form = SmallIntegerField(null=True)
    last_modified = DateTimeField(
        null=True, index=True, default=datetime.utcnow)

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    @staticmethod
    def get_active(swLat, swLng, neLat, neLng, timestamp=0, oSwLat=None,
                   oSwLng=None, oNeLat=None, oNeLng=None):
        now_date = datetime.utcnow()
        query = Pokemon.select()
        if not (swLat and swLng and neLat and neLng):
            query = (query
                     .where(Pokemon.disappear_time > now_date)
                     .dicts())
        elif timestamp > 0:
            # If timestamp is known only load modified Pokemon.
            query = (query
                     .where(((Pokemon.last_modified >
                              datetime.utcfromtimestamp(timestamp / 1000)) &
                             (Pokemon.disappear_time > now_date)) &
                            ((Pokemon.latitude >= swLat) &
                             (Pokemon.longitude >= swLng) &
                             (Pokemon.latitude <= neLat) &
                             (Pokemon.longitude <= neLng)))
                     .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng:
            # Send Pokemon in view but exclude those within old boundaries.
            # Only send newly uncovered Pokemon.
            query = (query
                     .where(((Pokemon.disappear_time > now_date) &
                             (((Pokemon.latitude >= swLat) &
                               (Pokemon.longitude >= swLng) &
                               (Pokemon.latitude <= neLat) &
                               (Pokemon.longitude <= neLng))) &
                             ~((Pokemon.disappear_time > now_date) &
                               (Pokemon.latitude >= oSwLat) &
                               (Pokemon.longitude >= oSwLng) &
                               (Pokemon.latitude <= oNeLat) &
                               (Pokemon.longitude <= oNeLng))))
                     .dicts())
        else:
            query = (Pokemon
                     .select()
                     # Add 1 hour buffer to include spawnpoints that persist
                     # after tth, like shsh.
                     .where((Pokemon.disappear_time > now_date) &
                            (((Pokemon.latitude >= swLat) &
                              (Pokemon.longitude >= swLng) &
                              (Pokemon.latitude <= neLat) &
                              (Pokemon.longitude <= neLng))))
                     .dicts())

        # Performance:  disable the garbage collector prior to creating a
        # (potentially) large dict with append().
        gc.disable()

        pokemon = []
        for p in list(query):

            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            p['pokemon_rarity'] = get_pokemon_rarity(p['pokemon_id'])
            p['pokemon_types'] = get_pokemon_types(p['pokemon_id'])
            if args.china:
                p['latitude'], p['longitude'] = \
                    transform_from_wgs_to_gcj(p['latitude'], p['longitude'])
            pokemon.append(p)

        # Re-enable the GC.
        gc.enable()

        return pokemon

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

        # Performance:  disable the garbage collector prior to creating a
        # (potentially) large dict with append().
        gc.disable()

        pokemon = []
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            p['pokemon_rarity'] = get_pokemon_rarity(p['pokemon_id'])
            p['pokemon_types'] = get_pokemon_types(p['pokemon_id'])
            if args.china:
                p['latitude'], p['longitude'] = \
                    transform_from_wgs_to_gcj(p['latitude'], p['longitude'])
            pokemon.append(p)

        # Re-enable the GC.
        gc.enable()

        return pokemon

    @classmethod
    @cached(cache)
    def get_seen(cls, timediff):
        if timediff:
            timediff = datetime.utcnow() - timediff
        pokemon_count_query = (Pokemon
                               .select(Pokemon.pokemon_id,
                                       fn.COUNT(Pokemon.pokemon_id).alias(
                                           'count'),
                                       fn.MAX(Pokemon.disappear_time).alias(
                                           'lastappeared')
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
                 .join(pokemon_count_query,
                       on=(Pokemon.pokemon_id ==
                           pokemon_count_query.c.pokemon_id))
                 .distinct()
                 .where(Pokemon.disappear_time ==
                        pokemon_count_query.c.lastappeared)
                 .dicts()
                 )

        # Performance:  disable the garbage collector prior to creating a
        # (potentially) large dict with append().
        gc.disable()

        pokemon = []
        total = 0
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            pokemon.append(p)
            total += p['count']

        # Re-enable the GC.
        gc.enable()

        return {'pokemon': pokemon, 'total': total}

    @classmethod
    def get_appearances(cls, pokemon_id, timediff):
        '''
        :param pokemon_id: id of Pokemon that we need appearances for
        :param timediff: limiting period of the selection
        :return: list of Pokemon appearances over a selected period
        '''
        if timediff:
            timediff = datetime.utcnow() - timediff
        query = (Pokemon
                 .select(Pokemon.latitude, Pokemon.longitude,
                         Pokemon.pokemon_id,
                         fn.Count(Pokemon.spawnpoint_id).alias('count'),
                         Pokemon.spawnpoint_id)
                 .where((Pokemon.pokemon_id == pokemon_id) &
                        (Pokemon.disappear_time > timediff)
                        )
                 .group_by(Pokemon.latitude, Pokemon.longitude,
                           Pokemon.pokemon_id, Pokemon.spawnpoint_id)
                 .dicts()
                 )

        return list(query)

    @classmethod
    def get_appearances_times_by_spawnpoint(cls, pokemon_id,
                                            spawnpoint_id, timediff):
        '''
        :param pokemon_id: id of Pokemon that we need appearances times for.
        :param spawnpoint_id: spawnpoint id we need appearances times for.
        :param timediff: limiting period of the selection.
        :return: list of time appearances over a selected period.
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


class Pokestop(BaseModel):
    pokestop_id = Utf8mb4CharField(primary_key=True, max_length=50)
    enabled = BooleanField()
    latitude = DoubleField()
    longitude = DoubleField()
    last_modified = DateTimeField(index=True)
    lure_expiration = DateTimeField(null=True, index=True)
    active_fort_modifier = Utf8mb4CharField(max_length=50,
                                            null=True, index=True)
    last_updated = DateTimeField(
        null=True, index=True, default=datetime.utcnow)

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    @staticmethod
    def get_stops(swLat, swLng, neLat, neLng, timestamp=0, oSwLat=None,
                  oSwLng=None, oNeLat=None, oNeLng=None, lured=False):

        query = Pokestop.select(Pokestop.active_fort_modifier,
                                Pokestop.enabled, Pokestop.latitude,
                                Pokestop.longitude, Pokestop.last_modified,
                                Pokestop.lure_expiration, Pokestop.pokestop_id)

        if not (swLat and swLng and neLat and neLng):
            query = (query
                     .dicts())
        elif timestamp > 0:
            query = (query
                     .where(((Pokestop.last_updated >
                              datetime.utcfromtimestamp(timestamp / 1000))) &
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
            # Send stops in view but exclude those within old boundaries. Only
            # send newly uncovered stops.
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
                     .where(((Pokestop.last_updated >
                              datetime.utcfromtimestamp(timestamp / 1000))) &
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

        # Performance:  disable the garbage collector prior to creating a
        # (potentially) large dict with append().
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
    gym_id = Utf8mb4CharField(primary_key=True, max_length=50)
    team_id = SmallIntegerField()
    guard_pokemon_id = SmallIntegerField()
    slots_available = SmallIntegerField()
    enabled = BooleanField()
    latitude = DoubleField()
    longitude = DoubleField()
    total_cp = SmallIntegerField()
    last_modified = DateTimeField(index=True)
    last_scanned = DateTimeField(default=datetime.utcnow, index=True)

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    @staticmethod
    def get_gyms(swLat, swLng, neLat, neLng, timestamp=0, oSwLat=None,
                 oSwLng=None, oNeLat=None, oNeLng=None):
        if not (swLat and swLng and neLat and neLng):
            results = (Gym
                       .select()
                       .dicts())
        elif timestamp > 0:
            # If timestamp is known only send last scanned Gyms.
            results = (Gym
                       .select()
                       .where(((Gym.last_scanned >
                                datetime.utcfromtimestamp(timestamp / 1000)) &
                               (Gym.latitude >= swLat) &
                               (Gym.longitude >= swLng) &
                               (Gym.latitude <= neLat) &
                               (Gym.longitude <= neLng)))
                       .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng:
            # Send gyms in view but exclude those within old boundaries. Only
            # send newly uncovered gyms.
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

        # Performance:  disable the garbage collector prior to creating a
        # (potentially) large dict with append().
        gc.disable()

        gyms = {}
        gym_ids = []
        for g in results:
            g['name'] = None
            g['pokemon'] = []
            g['raid'] = None
            gyms[g['gym_id']] = g
            gym_ids.append(g['gym_id'])

        if len(gym_ids) > 0:
            pokemon = (GymMember
                       .select(
                           GymMember.gym_id,
                           GymPokemon.cp.alias('pokemon_cp'),
                           GymMember.cp_decayed,
                           GymMember.deployment_time,
                           GymPokemon.pokemon_id,
                           Trainer.name.alias('trainer_name'),
                           Trainer.level.alias('trainer_level'))
                       .join(Gym, on=(GymMember.gym_id == Gym.gym_id))
                       .join(GymPokemon, on=(GymMember.pokemon_uid ==
                                             GymPokemon.pokemon_uid))
                       .join(Trainer, on=(GymPokemon.trainer_name ==
                                          Trainer.name))
                       .where(GymMember.gym_id << gym_ids)
                       .where(GymMember.last_scanned > Gym.last_modified)
                       .distinct()
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

            raids = (Raid
                     .select()
                     .where(Raid.gym_id << gym_ids)
                     .dicts())

            for r in raids:
                if r['pokemon_id']:
                    r['pokemon_name'] = get_pokemon_name(r['pokemon_id'])
                    r['pokemon_types'] = get_pokemon_types(r['pokemon_id'])
                gyms[r['gym_id']]['raid'] = r

        # Re-enable the GC.
        gc.enable()

        return gyms

    @staticmethod
    def get_gym(id):

        try:
            result = (Gym
                      .select(Gym.gym_id,
                              Gym.team_id,
                              GymDetails.name,
                              GymDetails.description,
                              Gym.guard_pokemon_id,
                              Gym.slots_available,
                              Gym.latitude,
                              Gym.longitude,
                              Gym.last_modified,
                              Gym.last_scanned)
                      .join(GymDetails, JOIN.LEFT_OUTER,
                            on=(Gym.gym_id == GymDetails.gym_id))
                      .where(Gym.gym_id == id)
                      .dicts()
                      .get())
        except Gym.DoesNotExist:
            return None

        result['guard_pokemon_name'] = get_pokemon_name(
            result['guard_pokemon_id']) if result['guard_pokemon_id'] else ''
        result['pokemon'] = []

        pokemon = (GymMember
                   .select(GymPokemon.cp.alias('pokemon_cp'),
                           GymMember.cp_decayed,
                           GymMember.deployment_time,
                           GymPokemon.pokemon_id,
                           GymPokemon.pokemon_uid,
                           GymPokemon.move_1,
                           GymPokemon.move_2,
                           GymPokemon.iv_attack,
                           GymPokemon.iv_defense,
                           GymPokemon.iv_stamina,
                           Trainer.name.alias('trainer_name'),
                           Trainer.level.alias('trainer_level'))
                   .join(Gym, on=(GymMember.gym_id == Gym.gym_id))
                   .join(GymPokemon,
                         on=(GymMember.pokemon_uid == GymPokemon.pokemon_uid))
                   .join(Trainer, on=(GymPokemon.trainer_name == Trainer.name))
                   .where(GymMember.gym_id == id)
                   .where(GymMember.last_scanned > Gym.last_modified)
                   .order_by(GymMember.cp_decayed.desc())
                   .distinct()
                   .dicts())

        for p in pokemon:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])

            p['move_1_name'] = get_move_name(p['move_1'])
            p['move_1_damage'] = get_move_damage(p['move_1'])
            p['move_1_energy'] = get_move_energy(p['move_1'])
            p['move_1_type'] = get_move_type(p['move_1'])

            p['move_2_name'] = get_move_name(p['move_2'])
            p['move_2_damage'] = get_move_damage(p['move_2'])
            p['move_2_energy'] = get_move_energy(p['move_2'])
            p['move_2_type'] = get_move_type(p['move_2'])

            result['pokemon'].append(p)

        try:
            raid = Raid.select(Raid).where(Raid.gym_id == id).dicts().get()
            if raid['pokemon_id']:
                raid['pokemon_name'] = get_pokemon_name(raid['pokemon_id'])
                raid['pokemon_types'] = get_pokemon_types(raid['pokemon_id'])
            result['raid'] = raid
        except Raid.DoesNotExist:
            pass

        return result


class Raid(BaseModel):
    gym_id = Utf8mb4CharField(primary_key=True, max_length=50)
    level = IntegerField(index=True)
    spawn = DateTimeField(index=True)
    start = DateTimeField(index=True)
    end = DateTimeField(index=True)
    pokemon_id = SmallIntegerField(null=True)
    cp = IntegerField(null=True)
    move_1 = SmallIntegerField(null=True)
    move_2 = SmallIntegerField(null=True)
    last_scanned = DateTimeField(default=datetime.utcnow, index=True)


class LocationAltitude(BaseModel):
    cellid = Utf8mb4CharField(primary_key=True, max_length=50)
    latitude = DoubleField()
    longitude = DoubleField()
    last_modified = DateTimeField(index=True, default=datetime.utcnow,
                                  null=True)
    altitude = DoubleField()

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    # DB format of a new location altitude
    @staticmethod
    def new_loc(loc, altitude):
        return {'cellid': cellid(loc),
                'latitude': loc[0],
                'longitude': loc[1],
                'altitude': altitude}

    # find a nearby altitude from the db
    # looking for one within 140m
    @classmethod
    def get_nearby_altitude(cls, loc):
        n, e, s, w = hex_bounds(loc, radius=0.14)  # 140m

        # Get all location altitudes in that box.
        query = (cls
                 .select()
                 .where((cls.latitude <= n) &
                        (cls.latitude >= s) &
                        (cls.longitude >= w) &
                        (cls.longitude <= e))
                 .dicts())

        altitude = None
        if len(list(query)):
            altitude = query[0]['altitude']

        return altitude

    @classmethod
    def save_altitude(cls, loc, altitude):
        InsertQuery(cls, rows=[cls.new_loc(loc, altitude)]).upsert().execute()


class PlayerLocale(BaseModel):
    location = Utf8mb4CharField(primary_key=True, max_length=50, index=True)
    country = Utf8mb4CharField(max_length=2)
    language = Utf8mb4CharField(max_length=2)
    timezone = Utf8mb4CharField(max_length=50)

    @staticmethod
    def get_locale(location):
        locale = None
        try:
            query = PlayerLocale.get(PlayerLocale.location == location)
            locale = {
                'country': query.country,
                'language': query.language,
                'timezone': query.timezone
            }
        except PlayerLocale.DoesNotExist:
            log.debug('This location is not yet in PlayerLocale DB table.')
        finally:
            return locale


class ScannedLocation(BaseModel):
    cellid = Utf8mb4CharField(primary_key=True, max_length=50)
    latitude = DoubleField()
    longitude = DoubleField()
    last_modified = DateTimeField(
        index=True, default=datetime.utcnow, null=True)
    # Marked true when all five bands have been completed.
    done = BooleanField(default=False)

    # Five scans/hour is required to catch all spawns.
    # Each scan must be at least 12 minutes from the previous check,
    # with a 2 minute window during which the scan can be done.

    # Default of -1 is for bands not yet scanned.
    band1 = SmallIntegerField(default=-1)
    band2 = SmallIntegerField(default=-1)
    band3 = SmallIntegerField(default=-1)
    band4 = SmallIntegerField(default=-1)
    band5 = SmallIntegerField(default=-1)

    # midpoint is the center of the bands relative to band 1.
    # If band 1 is 10.4 minutes, and band 4 is 34.0 minutes, midpoint
    # is -0.2 minutes in minsec.  Extra 10 seconds in case of delay in
    # recording now time.
    midpoint = SmallIntegerField(default=0)

    # width is how wide the valid window is. Default is 0, max is 2 minutes.
    # If band 1 is 10.4 minutes, and band 4 is 34.0 minutes, midpoint
    # is 0.4 minutes in minsec.
    width = SmallIntegerField(default=0)

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)
        constraints = [Check('band1 >= -1'), Check('band1 < 3600'),
                       Check('band2 >= -1'), Check('band2 < 3600'),
                       Check('band3 >= -1'), Check('band3 < 3600'),
                       Check('band4 >= -1'), Check('band4 < 3600'),
                       Check('band5 >= -1'), Check('band5 < 3600'),
                       Check('midpoint >= -130'), Check('midpoint <= 130'),
                       Check('width >= 0'), Check('width <= 130')]

    @staticmethod
    def get_recent(swLat, swLng, neLat, neLng, timestamp=0, oSwLat=None,
                   oSwLng=None, oNeLat=None, oNeLng=None):
        activeTime = (datetime.utcnow() - timedelta(minutes=15))
        if timestamp > 0:
            query = (ScannedLocation
                     .select()
                     .where(((ScannedLocation.last_modified >=
                              datetime.utcfromtimestamp(timestamp / 1000))) &
                            (ScannedLocation.latitude >= swLat) &
                            (ScannedLocation.longitude >= swLng) &
                            (ScannedLocation.latitude <= neLat) &
                            (ScannedLocation.longitude <= neLng))
                     .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng:
            # Send scannedlocations in view but exclude those within old
            # boundaries. Only send newly uncovered scannedlocations.
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

    # DB format of a new location.
    @staticmethod
    def new_loc(loc):
        return {'cellid': cellid(loc),
                'latitude': loc[0],
                'longitude': loc[1],
                'done': False,
                'band1': -1,
                'band2': -1,
                'band3': -1,
                'band4': -1,
                'band5': -1,
                'width': 0,
                'midpoint': 0,
                'last_modified': None}

    # Used to update bands.
    @staticmethod
    def db_format(scan, band, nowms):
        scan.update({'band' + str(band): nowms})
        scan['done'] = reduce(lambda x, y: x and (
            scan['band' + str(y)] > -1), range(1, 6), True)
        return scan

    # Shorthand helper for DB dict.
    @staticmethod
    def _q_init(scan, start, end, kind, sp_id=None):
        return {'loc': scan['loc'], 'kind': kind, 'start': start, 'end': end,
                'step': scan['step'], 'sp': sp_id}

    @classmethod
    def get_by_cellids(cls, cellids):
        query = (cls
                 .select()
                 .where(cls.cellid << cellids)
                 .dicts())

        d = {}
        for sl in list(query):
            key = "{}".format(sl['cellid'])
            d[key] = sl

        return d

    @classmethod
    def find_in_locs(cls, loc, locs):
        key = "{}".format(cellid(loc))
        return locs[key] if key in locs else cls.new_loc(loc)

    # Return value of a particular scan from loc, or default dict if not found.
    @classmethod
    def get_by_loc(cls, loc):
        query = (cls
                 .select()
                 .where(cls.cellid == cellid(loc))
                 .dicts())

        return query[0] if len(list(query)) else cls.new_loc(loc)

    # Check if spawnpoints in a list are in any of the existing
    # spannedlocation records.  Otherwise, search through the spawnpoint list
    # and update scan_spawn_point dict for DB bulk upserting.
    @classmethod
    def link_spawn_points(cls, scans, initial, spawn_points, distance,
                          scan_spawn_point, force=False):
        for cell, scan in scans.iteritems():
            if initial[cell]['done'] and not force:
                continue
            # Difference in degrees at the equator for 70m is actually 0.00063
            # degrees and gets smaller the further north or south you go
            deg_at_lat = 0.0007 / math.cos(math.radians(scan['loc'][0]))
            for sp in spawn_points:
                if (abs(sp['latitude'] - scan['loc'][0]) > 0.0008 or
                        abs(sp['longitude'] - scan['loc'][1]) > deg_at_lat):
                    continue
                if in_radius((sp['latitude'], sp['longitude']),
                             scan['loc'], distance):
                    scan_spawn_point[cell + sp['id']] = {
                        'spawnpoint': sp['id'],
                        'scannedlocation': cell}

    # Return list of dicts for upcoming valid band times.
    @classmethod
    def linked_spawn_points(cls, cell):

        # Unable to use a normal join, since MySQL produces foreignkey
        # constraint errors when trying to upsert fields that are foreignkeys
        # on another table

        query = (SpawnPoint
                 .select()
                 .join(ScanSpawnPoint)
                 .join(cls)
                 .where(cls.cellid == cell).dicts())

        return list(query)

    # Return list of dicts for upcoming valid band times.
    @classmethod
    def get_cell_to_linked_spawn_points(cls, cellids, location_change_date):

        # Get all spawnpoints from the hive's cells
        sp_from_cells = (ScanSpawnPoint
                         .select(ScanSpawnPoint.spawnpoint)
                         .where(ScanSpawnPoint.scannedlocation << cellids)
                         .alias('spcells'))
        # A new SL (new ones are created when the location changes) or
        # it can be a cell from another active hive
        one_sp_scan = (ScanSpawnPoint
                       .select(ScanSpawnPoint.spawnpoint,
                               fn.MAX(ScanSpawnPoint.scannedlocation).alias(
                                   'cellid'))
                       .join(sp_from_cells, on=sp_from_cells.c.spawnpoint_id
                             == ScanSpawnPoint.spawnpoint)
                       .join(cls, on=(cls.cellid ==
                                      ScanSpawnPoint.scannedlocation))
                       .where(((cls.last_modified >= (location_change_date)) &
                               (cls.last_modified > (
                                datetime.utcnow() - timedelta(minutes=60)))) |
                              (cls.cellid << cellids))
                       .group_by(ScanSpawnPoint.spawnpoint)
                       .alias('maxscan'))
        # As scan locations overlap,spawnpoints can belong to up to 3 locations
        # This sub-query effectively assigns each SP to exactly one location.

        query = (SpawnPoint
                 .select(SpawnPoint, one_sp_scan.c.cellid)
                 .join(one_sp_scan, on=(SpawnPoint.id ==
                                        one_sp_scan.c.spawnpoint_id))
                 .where(one_sp_scan.c.cellid << cellids)
                 .dicts())
        l = list(query)
        ret = {}
        for item in l:
            if item['cellid'] not in ret:
                ret[item['cellid']] = []
            ret[item['cellid']].append(item)

        return ret

    # Return list of dicts for upcoming valid band times.
    @classmethod
    def get_times(cls, scan, now_date, scanned_locations):
        s = cls.find_in_locs(scan['loc'], scanned_locations)
        if s['done']:
            return []

        max = 3600 * 2 + 250  # Greater than maximum possible value.
        min = {'end': max}

        nowms = date_secs(now_date)
        if s['band1'] == -1:
            return [cls._q_init(scan, nowms, nowms + 3599, 'band')]

        # Find next window.
        basems = s['band1']
        for i in range(2, 6):
            ms = s['band' + str(i)]

            # Skip bands already done.
            if ms > -1:
                continue

            radius = 120 - s['width'] / 2
            end = (basems + s['midpoint'] + radius + (i - 1) * 720 - 10) % 3600
            end = end if end >= nowms else end + 3600

            if end < min['end']:
                min = cls._q_init(scan, end - radius * 2 + 10, end, 'band')

        return [min] if min['end'] < max else []

    # Checks if now falls within an unfilled band for a scanned location.
    # Returns the updated scan location dict.
    @classmethod
    def update_band(cls, scan, now_date):

        scan['last_modified'] = now_date

        if scan['done']:
            return scan

        now_secs = date_secs(now_date)
        if scan['band1'] == -1:
            return cls.db_format(scan, 1, now_secs)

        # Calculate if number falls in band with remaining points.
        basems = scan['band1']
        delta = (now_secs - basems - scan['midpoint']) % 3600
        band = int(round(delta / 12 / 60.0) % 5) + 1

        # Check if that band is already filled.
        if scan['band' + str(band)] > -1:
            return scan

        # Check if this result falls within the band's 2 minute window.
        offset = (delta + 1080) % 720 - 360
        if abs(offset) > 120 - scan['width'] / 2:
            return scan

        # Find band midpoint/width.
        scan = cls.db_format(scan, band, now_secs)
        bts = [scan['band' + str(i)] for i in range(1, 6)]
        bts = filter(lambda ms: ms > -1, bts)
        bts_delta = map(lambda ms: (ms - basems) % 3600, bts)
        bts_offsets = map(lambda ms: (ms + 1080) % 720 - 360, bts_delta)
        min_scan = min(bts_offsets)
        max_scan = max(bts_offsets)
        scan['width'] = max_scan - min_scan
        scan['midpoint'] = (max_scan + min_scan) / 2

        return scan

    @classmethod
    def get_bands_filled_by_cellids(cls, cellids):
        return int(cls
                   .select(fn.SUM(case(cls.band1, ((-1, 0),), 1)
                                  + case(cls.band2, ((-1, 0),), 1)
                                  + case(cls.band3, ((-1, 0),), 1)
                                  + case(cls.band4, ((-1, 0),), 1)
                                  + case(cls.band5, ((-1, 0),), 1))
                           .alias('band_count'))
                   .where(cls.cellid << cellids)
                   .scalar() or 0)

    @classmethod
    def reset_bands(cls, scan_loc):
        scan_loc['done'] = False
        scan_loc['last_modified'] = datetime.utcnow()
        for i in range(1, 6):
            scan_loc['band' + str(i)] = -1

    @classmethod
    def select_in_hex(cls, locs):
        # There should be a way to delegate this to SpawnPoint.select_in_hex,
        # but w/e.
        cells = []
        for i, e in enumerate(locs):
            cells.append(cellid(e[1]))

        # Get all spawns for the locations.
        sp = list(cls
                  .select()
                  .where(cls.cellid << cells)
                  .dicts())

        # For each spawn work out if it is in the hex (clipping the diagonals).
        in_hex = []
        for spawn in sp:
            in_hex.append(spawn)
        return in_hex


class MainWorker(BaseModel):
    worker_name = Utf8mb4CharField(primary_key=True, max_length=50)
    message = TextField(null=True, default="")
    method = Utf8mb4CharField(max_length=50)
    last_modified = DateTimeField(index=True)
    accounts_working = IntegerField()
    accounts_captcha = IntegerField()
    accounts_failed = IntegerField()

    @staticmethod
    def get_account_stats():
        account_stats = (MainWorker
                         .select(fn.SUM(MainWorker.accounts_working),
                                 fn.SUM(MainWorker.accounts_captcha),
                                 fn.SUM(MainWorker.accounts_failed))
                         .scalar(as_tuple=True))
        dict = {'working': 0, 'captcha': 0, 'failed': 0}
        if account_stats[0] is not None:
            dict = {'working': int(account_stats[0]),
                    'captcha': int(account_stats[1]),
                    'failed': int(account_stats[2])}

        return dict


class WorkerStatus(BaseModel):
    username = Utf8mb4CharField(primary_key=True, max_length=50)
    worker_name = Utf8mb4CharField(index=True, max_length=50)
    success = IntegerField()
    fail = IntegerField()
    no_items = IntegerField()
    skip = IntegerField()
    captcha = IntegerField()
    last_modified = DateTimeField(index=True)
    message = Utf8mb4CharField(max_length=191)
    last_scan_date = DateTimeField(index=True)
    latitude = DoubleField(null=True)
    longitude = DoubleField(null=True)

    @staticmethod
    def db_format(status, name='status_worker_db'):
        status['worker_name'] = status.get('worker_name', name)
        return {'username': status['username'],
                'worker_name': status['worker_name'],
                'success': status['success'],
                'fail': status['fail'],
                'no_items': status['noitems'],
                'skip': status['skip'],
                'captcha': status['captcha'],
                'last_modified': datetime.utcnow(),
                'message': status['message'],
                'last_scan_date': status.get('last_scan_date',
                                             datetime.utcnow()),
                'latitude': status.get('latitude', None),
                'longitude': status.get('longitude', None)}

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

    @staticmethod
    def get_worker(username, loc=False):
        query = (WorkerStatus
                 .select()
                 .where((WorkerStatus.username == username))
                 .dicts())

        # Sometimes is appears peewee is slow to load, and this produces
        # an exception.  Retry after a second to give peewee time to load.
        while True:
            try:
                result = query[0] if len(query) else {
                    'username': username,
                    'success': 0,
                    'fail': 0,
                    'no_items': 0,
                    'skip': 0,
                    'last_modified': datetime.utcnow(),
                    'message': 'New account {} loaded'.format(username),
                    'last_scan_date': datetime.utcnow(),
                    'latitude': loc[0] if loc else None,
                    'longitude': loc[1] if loc else None
                }
                break
            except Exception as e:
                log.error('Exception in get_worker under account {}.  '
                          'Exception message: {}'.format(username, repr(e)))
                traceback.print_exc(file=sys.stdout)
                time.sleep(1)

        return result


class SpawnPoint(BaseModel):
    id = Utf8mb4CharField(primary_key=True, max_length=50)
    latitude = DoubleField()
    longitude = DoubleField()
    last_scanned = DateTimeField(index=True)
    # kind gives the four quartiles of the spawn, as 's' for seen
    # or 'h' for hidden.  For example, a 30 minute spawn is 'hhss'.
    kind = Utf8mb4CharField(max_length=4, default='hhhs')

    # links shows whether a Pokemon encounter id changes between quartiles or
    # stays the same.  Both 1x45 and 1x60h3 have the kind of 'sssh', but the
    # different links shows when the encounter id changes.  Same encounter id
    # is shared between two quartiles, links shows a '+'.  A different
    # encounter id between two quartiles is a '-'.
    #
    # For the hidden times, an 'h' is used.  Until determined, '?' is used.
    # Note index is shifted by a half. links[0] is the link between
    # kind[0] and kind[1] and so on. links[3] is the link between
    # kind[3] and kind[0]
    links = Utf8mb4CharField(max_length=4, default='????')

    # Count consecutive times spawn should have been seen, but wasn't.
    # If too high, will not be scheduled for review, and treated as inactive.
    missed_count = IntegerField(default=0)

    # Next 2 fields are to narrow down on the valid TTH window.
    # Seconds after the hour of the latest Pokemon seen time within the hour.
    latest_seen = SmallIntegerField()

    # Seconds after the hour of the earliest time Pokemon wasn't seen after an
    # appearance.
    earliest_unseen = SmallIntegerField()

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)
        constraints = [Check('earliest_unseen >= 0'),
                       Check('earliest_unseen < 3600'),
                       Check('latest_seen >= 0'), Check('latest_seen < 3600')]

    # Returns the spawnpoint dict from ID, or a new dict if not found.
    @classmethod
    def get_by_id(cls, id, latitude=0, longitude=0):
        query = (cls
                 .select()
                 .where(cls.id == id)
                 .dicts())

        return query[0] if query else {
            'id': id,
            'latitude': latitude,
            'longitude': longitude,
            'last_scanned': None,  # Null value used as new flag.
            'kind': 'hhhs',
            'links': '????',
            'missed_count': 0,
            'latest_seen': None,
            'earliest_unseen': None

        }

    @staticmethod
    def get_spawnpoints(swLat, swLng, neLat, neLng, timestamp=0,
                        oSwLat=None, oSwLng=None, oNeLat=None, oNeLng=None):
        query = (SpawnPoint
                 .select(SpawnPoint.latitude, SpawnPoint.longitude,
                         SpawnPoint.id, SpawnPoint.links, SpawnPoint.kind,
                         SpawnPoint.latest_seen, SpawnPoint.earliest_unseen,
                         ScannedLocation.done)
                 .join(ScanSpawnPoint)
                 .join(ScannedLocation)
                 .dicts())

        if timestamp > 0:
            query = (query
                     .where(((SpawnPoint.last_scanned >
                              datetime.utcfromtimestamp(timestamp / 1000))) &
                            ((SpawnPoint.latitude >= swLat) &
                            (SpawnPoint.longitude >= swLng) &
                            (SpawnPoint.latitude <= neLat) &
                            (SpawnPoint.longitude <= neLng)))
                     .dicts())
        elif oSwLat and oSwLng and oNeLat and oNeLng:
            # Send spawnpoints in view but exclude those within old boundaries.
            # Only send newly uncovered spawnpoints.
            query = (query
                     .where((((SpawnPoint.latitude >= swLat) &
                              (SpawnPoint.longitude >= swLng) &
                              (SpawnPoint.latitude <= neLat) &
                              (SpawnPoint.longitude <= neLng))) &
                            ~((SpawnPoint.latitude >= oSwLat) &
                              (SpawnPoint.longitude >= oSwLng) &
                              (SpawnPoint.latitude <= oNeLat) &
                              (SpawnPoint.longitude <= oNeLng)))
                     .dicts())
        elif swLat and swLng and neLat and neLng:
            query = (query
                     .where((SpawnPoint.latitude <= neLat) &
                            (SpawnPoint.latitude >= swLat) &
                            (SpawnPoint.longitude >= swLng) &
                            (SpawnPoint.longitude <= neLng)))

        queryDict = query.dicts()
        spawnpoints = {}
        for sp in queryDict:
            key = sp['id']
            appear_time, disappear_time = SpawnPoint.start_end(sp)
            spawnpoints[key] = sp
            spawnpoints[key]['disappear_time'] = disappear_time
            spawnpoints[key]['appear_time'] = appear_time
            if not SpawnPoint.tth_found(sp) or not sp['done']:
                spawnpoints[key]['uncertain'] = True

        # Helping out the GC.
        for sp in spawnpoints.values():
            del sp['done']
            del sp['kind']
            del sp['links']
            del sp['latest_seen']
            del sp['earliest_unseen']

        return list(spawnpoints.values())

    @classmethod
    def get_spawnpoints_in_hex(cls, center, steps):

        log.info('Finding spawnpoints {} steps away.'.format(steps))

        n, e, s, w = hex_bounds(center, steps)

        query = (SpawnPoint
                 .select(SpawnPoint.latitude.alias('lat'),
                         SpawnPoint.longitude.alias('lng'),
                         SpawnPoint.id,
                         SpawnPoint.earliest_unseen,
                         SpawnPoint.latest_seen,
                         SpawnPoint.kind,
                         SpawnPoint.links,
                         ))
        query = (query.where((SpawnPoint.latitude <= n) &
                             (SpawnPoint.latitude >= s) &
                             (SpawnPoint.longitude >= w) &
                             (SpawnPoint.longitude <= e)
                             ))
        # Sqlite doesn't support distinct on columns.
        if args.db_type == 'mysql':
            query = query.distinct(SpawnPoint.id)
        else:
            query = query.group_by(SpawnPoint.id)

        s = list(query.dicts())

        # The distance between scan circles of radius 70 in a hex is 121.2436
        # steps - 1 to account for the center circle then add 70 for the edge.
        step_distance = ((steps - 1) * 121.2436) + 70
        # Compare spawnpoint list to a circle with radius steps * 120.
        # Uses the direct geopy distance between the center and the spawnpoint.
        filtered = []

        for idx, sp in enumerate(s):
            if geopy.distance.distance(
                    center, (sp['lat'], sp['lng'])).meters <= step_distance:
                filtered.append(s[idx])

        # We use 'time' as appearance time as this was how things worked
        # previously we now also include 'disappear_time' because we
        # can and it is meaningful in a list of spawn data
        # the other changes also maintain a similar file format
        for sp in filtered:
            sp['time'], sp['disappear_time'] = cls.start_end(sp)
            del sp['earliest_unseen']
            del sp['latest_seen']
            del sp['kind']
            del sp['links']
            sp['spawnpoint_id'] = sp['id']
            del sp['id']

        return filtered

    # Confirm if tth has been found.
    @staticmethod
    def tth_found(sp):
        # Fully indentified if no '?' in links and
        # latest_seen == earliest_unseen.
        return sp['latest_seen'] == sp['earliest_unseen']

    # Return [start, end] in seconds after the hour for the spawn, despawn
    # time of a spawnpoint.
    @classmethod
    def start_end(cls, sp, spawn_delay=0, links=False):
        links_arg = links
        links = links if links else str(sp['links'])

        if links == '????':  # Clean up for old data.
            links = str(sp['kind'].replace('s', '?'))

        # Make some assumptions if link not fully identified.
        if links.count('-') == 0:
            links = links[:-1] + '-'

        links = links.replace('?', '+')

        links = links[:-1] + '-'
        plus_or_minus = links.index(
            '+') if links.count('+') else links.index('-')
        start = sp['earliest_unseen'] - (4 - plus_or_minus) * 900 + spawn_delay
        no_tth_adjust = 60 if not links_arg and not cls.tth_found(sp) else 0
        end = sp['latest_seen'] - (3 - links.index('-')) * 900 + no_tth_adjust
        return [start % 3600, end % 3600]

    # Return a list of dicts with the next spawn times.
    @classmethod
    def get_times(cls, cell, scan, now_date, scan_delay,
                  cell_to_linked_spawn_points, sp_by_id):
        l = []
        now_secs = date_secs(now_date)
        linked_spawn_points = (cell_to_linked_spawn_points[cell]
                               if cell in cell_to_linked_spawn_points else [])

        for sp in linked_spawn_points:

            if sp['missed_count'] > 5:
                continue

            endpoints = SpawnPoint.start_end(sp, scan_delay)
            cls.add_if_not_scanned('spawn', l, sp, scan,
                                   endpoints[0], endpoints[1], now_date,
                                   now_secs, sp_by_id)

            # Check to see if still searching for valid TTH.
            if cls.tth_found(sp):
                continue

            # Add a spawnpoint check between latest_seen and earliest_unseen.
            start = sp['latest_seen']
            end = sp['earliest_unseen']

            # So if the gap between start and end < 89 seconds make the gap
            # 89 seconds
            if ((end > start and end - start < 89) or
                    (start > end and (end + 3600) - start < 89)):
                end = (start + 89) % 3600
            # So we move the search gap on 45 to within 45 and 89 seconds from
            # the last scan. TTH appears in the last 90 seconds of the Spawn.
            start = sp['latest_seen'] + 45

            cls.add_if_not_scanned('TTH', l, sp, scan,
                                   start, end, now_date, now_secs, sp_by_id)

        return l

    @classmethod
    def add_if_not_scanned(cls, kind, l, sp, scan, start,
                           end, now_date, now_secs, sp_by_id):
        # Make sure later than now_secs.
        while end < now_secs:
            start, end = start + 3600, end + 3600

        # Ensure start before end.
        while start > end:
            start -= 3600

        while start < 0:
            start, end = start + 3600, end + 3600

        last_scanned = sp_by_id[sp['id']]['last_scanned']
        if ((now_date - last_scanned).total_seconds() > now_secs - start):
            l.append(ScannedLocation._q_init(scan, start, end, kind, sp['id']))

    @classmethod
    def select_in_hex_by_cellids(cls, cellids, location_change_date):
        # Get all spawnpoints from the hive's cells
        sp_from_cells = (ScanSpawnPoint
                         .select(ScanSpawnPoint.spawnpoint)
                         .where(ScanSpawnPoint.scannedlocation << cellids)
                         .alias('spcells'))
        # Allocate a spawnpoint to one cell only, this can either be
        # A new SL (new ones are created when the location changes) or
        # it can be a cell from another active hive
        one_sp_scan = (ScanSpawnPoint
                       .select(ScanSpawnPoint.spawnpoint,
                               fn.MAX(ScanSpawnPoint.scannedlocation).alias(
                                   'Max_ScannedLocation_id'))
                       .join(sp_from_cells, on=sp_from_cells.c.spawnpoint_id
                             == ScanSpawnPoint.spawnpoint)
                       .join(
                           ScannedLocation,
                           on=(ScannedLocation.cellid
                               == ScanSpawnPoint.scannedlocation))
                       .where(((ScannedLocation.last_modified
                                >= (location_change_date)) & (
                           ScannedLocation.last_modified > (
                               datetime.utcnow() - timedelta(minutes=60)))) |
                              (ScannedLocation.cellid << cellids))
                       .group_by(ScanSpawnPoint.spawnpoint)
                       .alias('maxscan'))

        query = (cls
                 .select(cls)
                 .join(one_sp_scan,
                       on=(one_sp_scan.c.spawnpoint_id == cls.id))
                 .where(one_sp_scan.c.Max_ScannedLocation_id << cellids)
                 .dicts())

        in_hex = []
        for spawn in list(query):
            in_hex.append(spawn)
        return in_hex

    @classmethod
    def select_in_hex_by_location(cls, center, steps):
        R = 6378.1  # KM radius of the earth
        hdist = ((steps * 120.0) - 50.0) / 1000.0
        n, e, s, w = hex_bounds(center, steps)

        # Get all spawns in that box.
        sp = list(cls
                  .select()
                  .where((cls.latitude <= n) &
                         (cls.latitude >= s) &
                         (cls.longitude >= w) &
                         (cls.longitude <= e))
                  .dicts())

        # For each spawn work out if it is in the hex (clipping the diagonals).
        in_hex = []
        for spawn in sp:
            # Get the offset from the center of each spawn in km.
            offset = [math.radians(spawn['latitude'] - center[0]) * R,
                      math.radians(spawn['longitude'] - center[1]) *
                      (R * math.cos(math.radians(center[0])))]
            # Check against the 4 lines that make up the diagonals.
            if (offset[1] + (offset[0] * 0.5)) > hdist:  # Too far NE
                continue
            if (offset[1] - (offset[0] * 0.5)) > hdist:  # Too far SE
                continue
            if ((offset[0] * 0.5) - offset[1]) > hdist:  # Too far NW
                continue
            if ((0 - offset[1]) - (offset[0] * 0.5)) > hdist:  # Too far SW
                continue
            # If it gets to here it's a good spawn.
            in_hex.append(spawn)
        return in_hex


class ScanSpawnPoint(BaseModel):
    scannedlocation = ForeignKeyField(ScannedLocation, null=True)
    spawnpoint = ForeignKeyField(SpawnPoint, null=True)

    class Meta:
        primary_key = CompositeKey('spawnpoint', 'scannedlocation')


class SpawnpointDetectionData(BaseModel):
    id = Utf8mb4CharField(primary_key=True, max_length=54)
    # Removed ForeignKeyField since it caused MySQL issues.
    encounter_id = Utf8mb4CharField(max_length=54)
    # Removed ForeignKeyField since it caused MySQL issues.
    spawnpoint_id = Utf8mb4CharField(max_length=54, index=True)
    scan_time = DateTimeField()
    tth_secs = SmallIntegerField(null=True)

    @staticmethod
    def set_default_earliest_unseen(sp):
        sp['earliest_unseen'] = (sp['latest_seen'] + 15 * 60) % 3600

    @classmethod
    def classify(cls, sp, scan_loc, now_secs, sighting=None):

        # Get past sightings.
        query = list(cls.select()
                        .where(cls.spawnpoint_id == sp['id'])
                        .order_by(cls.scan_time.asc())
                        .dicts())

        if sighting:
            query.append(sighting)

        tth_found = False
        for s in query:
            if s['tth_secs'] is not None:
                tth_found = True
                tth_secs = (s['tth_secs'] - 1) % 3600

        # To reduce CPU usage, give an intial reading of 15 minute spawns if
        # not done with initial scan of location.
        if not scan_loc['done']:
            # We only want to reset a SP if it is new and not due the
            # location changing (which creates new Scannedlocations)
            if not tth_found:
                sp['kind'] = 'hhhs'
                if not sp['earliest_unseen']:
                    sp['latest_seen'] = now_secs
                    cls.set_default_earliest_unseen(sp)

                elif clock_between(sp['latest_seen'], now_secs,
                                   sp['earliest_unseen']):
                    sp['latest_seen'] = now_secs
            return

        # Make a record of links, so we can reset earliest_unseen
        # if it changes.
        old_kind = str(sp['kind'])
        # Make a sorted list of the seconds after the hour.
        seen_secs = sorted(map(lambda x: date_secs(x['scan_time']), query))
        # Include and entry for the TTH if it found
        if tth_found:
            seen_secs.append(tth_secs)
            seen_secs.sort()
        # Add the first seen_secs to the end as a clock wrap around.
        if seen_secs:
            seen_secs.append(seen_secs[0] + 3600)

        # Make a list of gaps between sightings.
        gap_list = [seen_secs[i + 1] - seen_secs[i]
                    for i in range(len(seen_secs) - 1)]

        max_gap = max(gap_list)

        # An hour minus the largest gap in minutes gives us the duration the
        # spawn was there.  Round up to the nearest 15 minute interval for our
        # current best guess duration.
        duration = (int((60 - max_gap / 60.0) / 15) + 1) * 15

        # If the second largest gap is larger than 15 minutes, then there are
        # two gaps greater than 15 minutes.  It must be a double spawn.
        if len(gap_list) > 4 and sorted(gap_list)[-2] > 900:
            sp['kind'] = 'hshs'
            sp['links'] = 'h?h?'

        else:
            # Convert the duration into a 'hhhs', 'hhss', 'hsss', 'ssss' string
            # accordingly.  's' is for seen, 'h' is for hidden.
            sp['kind'] = ''.join(
                ['s' if i > (3 - duration / 15) else 'h' for i in range(0, 4)])

        # Assume no hidden times.
        sp['links'] = sp['kind'].replace('s', '?')

        if sp['kind'] != 'ssss':

            if (not sp['earliest_unseen'] or
                    sp['earliest_unseen'] != sp['latest_seen'] or
                    not tth_found):

                # New latest_seen will be just before max_gap.
                sp['latest_seen'] = seen_secs[gap_list.index(max_gap)]

                # if we don't have a earliest_unseen yet or if the kind of
                # spawn has changed, reset to latest_seen + 14 minutes.
                if not sp['earliest_unseen'] or sp['kind'] != old_kind:
                    cls.set_default_earliest_unseen(sp)
            return

        # Only ssss spawns from here below.

        sp['links'] = '+++-'
        if sp['earliest_unseen'] == sp['latest_seen']:
            return

        # Make a sight_list of dicts:
        # {date: first seen time,
        # delta: duration of sighting,
        # same: whether encounter ID was same or different over that time}
        #
        # For 60 minute spawns ('ssss'), the largest gap doesn't give the
        # earliest spawnpoint because a Pokemon is always there.  Use the union
        # of all intervals where the same encounter ID was seen to find the
        # latest_seen.  If a different encounter ID was seen, then the
        # complement of that interval was the same ID, so union that
        # complement as well.

        sight_list = [{'date': query[i]['scan_time'],
                       'delta': query[i + 1]['scan_time'] -
                       query[i]['scan_time'],
                       'same': query[i + 1]['encounter_id'] ==
                       query[i]['encounter_id']
                       }
                      for i in range(len(query) - 1)
                      if query[i + 1]['scan_time'] - query[i]['scan_time'] <
                      timedelta(hours=1)
                      ]

        start_end_list = []
        for s in sight_list:
            if s['same']:
                # Get the seconds past the hour for start and end times.
                start = date_secs(s['date'])
                end = (start + int(s['delta'].total_seconds())) % 3600

            else:
                # Convert diff range to same range by taking the clock
                # complement.
                start = date_secs(s['date'] + s['delta']) % 3600
                end = date_secs(s['date'])

            start_end_list.append([start, end])

        # Take the union of all the ranges.
        while True:
            # union is list of unions of ranges with the same encounter id.
            union = []
            for start, end in start_end_list:
                if not union:
                    union.append([start, end])
                    continue
                # Cycle through all ranges in union, since it might overlap
                # with any of them.
                for u in union:
                    if clock_between(u[0], start, u[1]):
                        u[1] = end if not(clock_between(
                            u[0], end, u[1])) else u[1]
                    elif clock_between(u[0], end, u[1]):
                        u[0] = start if not(clock_between(
                            u[0], start, u[1])) else u[0]
                    elif union.count([start, end]) == 0:
                        union.append([start, end])

            # Are no more unions possible?
            if union == start_end_list:
                break

            start_end_list = union  # Make another pass looking for unions.

        # If more than one disparate union, take the largest as our starting
        # point.
        union = reduce(lambda x, y: x if (x[1] - x[0]) % 3600 >
                       (y[1] - y[0]) % 3600 else y, union, [0, 3600])
        sp['latest_seen'] = union[1]
        sp['earliest_unseen'] = union[0]
        log.info('1x60: appear %d, despawn %d, duration: %d min.',
                 union[0], union[1], ((union[1] - union[0]) % 3600) / 60)

    # Expand the seen times for 30 minute spawnpoints based on scans when spawn
    # wasn't there.  Return true if spawnpoint dict changed.
    @classmethod
    def unseen(cls, sp, now_secs):

        # Return if we already have a tth.
        if sp['latest_seen'] == sp['earliest_unseen']:
            return False

        # If now_secs is later than the latest seen return.
        if not clock_between(sp['latest_seen'], now_secs,
                             sp['earliest_unseen']):
            return False

        sp['earliest_unseen'] = now_secs

        return True


class Versions(flaskDb.Model):
    key = Utf8mb4CharField()
    val = SmallIntegerField()

    class Meta:
        primary_key = False


class GymMember(BaseModel):
    gym_id = Utf8mb4CharField(index=True)
    pokemon_uid = Utf8mb4CharField(index=True)
    last_scanned = DateTimeField(default=datetime.utcnow, index=True)
    deployment_time = DateTimeField()
    cp_decayed = SmallIntegerField()

    class Meta:
        primary_key = False


class GymPokemon(BaseModel):
    pokemon_uid = Utf8mb4CharField(primary_key=True, max_length=50)
    pokemon_id = SmallIntegerField()
    cp = SmallIntegerField()
    trainer_name = Utf8mb4CharField(index=True)
    num_upgrades = SmallIntegerField(null=True)
    move_1 = SmallIntegerField(null=True)
    move_2 = SmallIntegerField(null=True)
    height = FloatField(null=True)
    weight = FloatField(null=True)
    stamina = SmallIntegerField(null=True)
    stamina_max = SmallIntegerField(null=True)
    cp_multiplier = FloatField(null=True)
    additional_cp_multiplier = FloatField(null=True)
    iv_defense = SmallIntegerField(null=True)
    iv_stamina = SmallIntegerField(null=True)
    iv_attack = SmallIntegerField(null=True)
    last_seen = DateTimeField(default=datetime.utcnow)


class Trainer(BaseModel):
    name = Utf8mb4CharField(primary_key=True, max_length=50)
    team = SmallIntegerField()
    level = SmallIntegerField()
    last_seen = DateTimeField(default=datetime.utcnow)


class GymDetails(BaseModel):
    gym_id = Utf8mb4CharField(primary_key=True, max_length=50)
    name = Utf8mb4CharField()
    description = TextField(null=True, default="")
    url = Utf8mb4CharField()
    last_scanned = DateTimeField(default=datetime.utcnow)


class Token(flaskDb.Model):
    token = TextField()
    last_updated = DateTimeField(default=datetime.utcnow, index=True)

    @staticmethod
    def get_valid(limit=15):
        # Make sure we don't grab more than we can process
        if limit > 15:
            limit = 15
        valid_time = datetime.utcnow() - timedelta(seconds=30)
        token_ids = []
        tokens = []
        try:
            with flaskDb.database.transaction():
                query = (Token
                         .select()
                         .where(Token.last_updated > valid_time)
                         .order_by(Token.last_updated.asc())
                         .limit(limit))
                for t in query:
                    token_ids.append(t.id)
                    tokens.append(t.token)
                if tokens:
                    log.debug('Retrived Token IDs: {}'.format(token_ids))
                    result = DeleteQuery(Token).where(
                        Token.id << token_ids).execute()
                    log.debug('Deleted {} tokens.'.format(result))
        except OperationalError as e:
            log.error('Failed captcha token transactional query: {}'.format(e))

        return tokens


class HashKeys(BaseModel):
    key = Utf8mb4CharField(primary_key=True, max_length=20)
    maximum = SmallIntegerField(default=0)
    remaining = SmallIntegerField(default=0)
    peak = SmallIntegerField(default=0)
    expires = DateTimeField(null=True)
    last_updated = DateTimeField(default=datetime.utcnow)

    @staticmethod
    def get_by_key(key):
        query = (HashKeys
                 .select()
                 .where(HashKeys.key == key)
                 .dicts())

        return query[0] if query else {
            'maximum': 0,
            'remaining': 0,
            'peak': 0,
            'expires': None,
            'last_updated': None
        }

    @staticmethod
    def get_obfuscated_keys():
        # Obfuscate hashing keys before we sent them to the front-end.
        hashkeys = HashKeys.get_all()
        for i, s in enumerate(hashkeys):
            hashkeys[i]['key'] = s['key'][:-9] + '*'*9
        return hashkeys

    @staticmethod
    # Retrieve the last stored 'peak' value for each hashing key.
    def getStoredPeak(key):
        result = HashKeys.select(HashKeys.peak).where(HashKeys.key == key)
        if result:
            # only one row can be returned
            return result[0].peak
        else:
            return 0


def hex_bounds(center, steps=None, radius=None):
    # Make a box that is (70m * step_limit * 2) + 70m away from the
    # center point.  Rationale is that you need to travel.
    sp_dist = 0.07 * (2 * steps + 1) if steps else radius
    n = get_new_coords(center, sp_dist, 0)[0]
    e = get_new_coords(center, sp_dist, 90)[1]
    s = get_new_coords(center, sp_dist, 180)[0]
    w = get_new_coords(center, sp_dist, 270)[1]
    return (n, e, s, w)


# todo: this probably shouldn't _really_ be in "models" anymore, but w/e.
def parse_map(args, map_dict, step_location, db_update_queue, wh_update_queue,
              key_scheduler, api, status, now_date, account, account_sets):
    pokemon = {}
    pokestops = {}
    gyms = {}
    raids = {}
    skipped = 0
    stopsskipped = 0
    forts = []
    forts_count = 0
    wild_pokemon = []
    wild_pokemon_count = 0
    nearby_pokemon = 0
    spawn_points = {}
    scan_spawn_points = {}
    sightings = {}
    new_spawn_points = []
    sp_id_list = []
    captcha_url = ''

    # Consolidate the individual lists in each cell into two lists of Pokemon
    # and a list of forts.
    cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    # Get the level for the pokestop spin, and to send to webhook.
    level = account['level']
    # Use separate level indicator for our L30 encounters.
    encounter_level = level

    # Helping out the GC.
    if 'GET_INVENTORY' in map_dict['responses']:
        del map_dict['responses']['GET_INVENTORY']

    for i, cell in enumerate(cells):
        # If we have map responses then use the time from the request
        if i == 0:
            now_date = datetime.utcfromtimestamp(
                cell['current_timestamp_ms'] / 1000)

        nearby_pokemon += len(cell.get('nearby_pokemons', []))
        # Parse everything for stats (counts).  Future enhancement -- we don't
        # necessarily need to know *how many* forts/wild/nearby were found but
        # we'd like to know whether or not *any* were found to help determine
        # if a scan was actually bad.
        if config['parse_pokemon']:
            wild_pokemon += cell.get('wild_pokemons', [])

        if config['parse_pokestops'] or config['parse_gyms']:
            forts += cell.get('forts', [])

        # Update count regardless of Pokémon parsing or not, we need the count.
        # Length is O(1).
        wild_pokemon_count += len(cell.get('wild_pokemons', []))
        forts_count += len(cell.get('forts', []))

    now_secs = date_secs(now_date)
    if wild_pokemon:
        wild_pokemon_count = len(wild_pokemon)
    if forts:
        forts_count = len(forts)

    del map_dict['responses']['GET_MAP_OBJECTS']

    # If there are no wild or nearby Pokemon . . .
    if not wild_pokemon and not nearby_pokemon:
        # . . . and there are no gyms/pokestops then it's unusable/bad.
        if not forts:
            log.warning('Bad scan. Parsing found absolutely nothing.')
            log.info('Common causes: captchas or IP bans.')
        else:
            # No wild or nearby Pokemon but there are forts.  It's probably
            # a speed violation.
            log.warning('No nearby or wild Pokemon but there are visible gyms '
                        'or pokestops. Possible speed violation.')

    scan_loc = ScannedLocation.get_by_loc(step_location)
    done_already = scan_loc['done']
    ScannedLocation.update_band(scan_loc, now_date)
    just_completed = not done_already and scan_loc['done']

    if wild_pokemon and config['parse_pokemon']:
        encounter_ids = [b64encode(str(p['encounter_id']))
                         for p in wild_pokemon]
        # For all the wild Pokemon we found check if an active Pokemon is in
        # the database.
        query = (Pokemon
                 .select(Pokemon.encounter_id, Pokemon.spawnpoint_id)
                 .where((Pokemon.disappear_time >= now_date) &
                        (Pokemon.encounter_id << encounter_ids))
                 .dicts())

        # Store all encounter_ids and spawnpoint_ids for the Pokemon in query.
        # All of that is needed to make sure it's unique.
        encountered_pokemon = [
            (p['encounter_id'], p['spawnpoint_id']) for p in query]

        for p in wild_pokemon:

            sp = SpawnPoint.get_by_id(p['spawn_point_id'], p[
                                      'latitude'], p['longitude'])
            spawn_points[p['spawn_point_id']] = sp
            sp['missed_count'] = 0

            sighting = {
                'id': b64encode(str(p['encounter_id'])) + '_' + str(now_secs),
                'encounter_id': b64encode(str(p['encounter_id'])),
                'spawnpoint_id': p['spawn_point_id'],
                'scan_time': now_date,
                'tth_secs': None
            }

            # Keep a list of sp_ids to return.
            sp_id_list.append(p['spawn_point_id'])

            # time_till_hidden_ms was overflowing causing a negative integer.
            # It was also returning a value above 3.6M ms.
            if 0 < p['time_till_hidden_ms'] < 3600000:
                d_t_secs = date_secs(datetime.utcfromtimestamp(
                    (p['last_modified_timestamp_ms'] +
                     p['time_till_hidden_ms']) / 1000.0))
                if (sp['latest_seen'] != sp['earliest_unseen'] or
                        not sp['last_scanned']):
                    log.info('TTH found for spawnpoint %s.', sp['id'])
                    sighting['tth_secs'] = d_t_secs

                    # Only update when TTH is seen for the first time.
                    # Just before Pokemon migrations, Niantic sets all TTH
                    # to the exact time of the migration, not the normal
                    # despawn time.
                    sp['latest_seen'] = d_t_secs
                    sp['earliest_unseen'] = d_t_secs

            scan_spawn_points[scan_loc['cellid'] + sp['id']] = {
                'spawnpoint': sp['id'],
                'scannedlocation': scan_loc['cellid']}
            if not sp['last_scanned']:
                log.info('New Spawn Point found.')
                new_spawn_points.append(sp)

                # If we found a new spawnpoint after the location was already
                # fully scanned then either it's new, or we had a bad scan.
                # Either way, rescan the location.
                if scan_loc['done'] and not just_completed:
                    log.warning('Location was fully scanned, and yet a brand '
                                'new spawnpoint found.')
                    log.warning('Redoing scan of this location to identify '
                                'new spawnpoint.')
                    ScannedLocation.reset_bands(scan_loc)

            if (not SpawnPoint.tth_found(sp) or sighting['tth_secs'] or
                    not scan_loc['done'] or just_completed):
                SpawnpointDetectionData.classify(sp, scan_loc, now_secs,
                                                 sighting)
                sightings[p['encounter_id']] = sighting

            sp['last_scanned'] = datetime.utcfromtimestamp(
                p['last_modified_timestamp_ms'] / 1000.0)

            if ((b64encode(str(p['encounter_id'])), p['spawn_point_id'])
                    in encountered_pokemon):
                # If Pokemon has been encountered before don't process it.
                skipped += 1
                continue

            start_end = SpawnPoint.start_end(sp, 1)
            seconds_until_despawn = (start_end[1] - now_secs) % 3600
            disappear_time = now_date + \
                timedelta(seconds=seconds_until_despawn)

            pokemon_id = p['pokemon_data']['pokemon_id']
            printPokemon(pokemon_id, p['latitude'], p['longitude'],
                         disappear_time)

            # Scan for IVs/CP and moves.
            encounter_result = None
            if args.encounter and (pokemon_id in args.enc_whitelist):
                time.sleep(args.encounter_delay)

                hlvl_account = None
                hlvl_api = None
                using_accountset = False

                scan_location = [p['latitude'], p['longitude']]

                # If the host has L30s in the regular account pool, we
                # can just use the current account.
                if level >= 30:
                    hlvl_account = account
                    hlvl_api = api
                else:
                    # Get account to use for IV and CP scanning.
                    hlvl_account = account_sets.next('30', scan_location)

                # If we don't have an API object yet, it means we didn't re-use
                # an old one, so we're using AccountSet.
                using_accountset = not hlvl_api

                # If we didn't get an account, we can't encounter.
                if hlvl_account:
                    # Logging.
                    log.debug('Encountering Pokémon ID %s with account %s'
                              + ' at %s, %s.',
                              pokemon_id,
                              hlvl_account['username'],
                              scan_location[0],
                              scan_location[1])

                    # If not args.no_api_store is enabled, we need to
                    # re-use an old API object if it's stored and we're
                    # using an account from the AccountSet.
                    if not args.no_api_store and using_accountset:
                        hlvl_api = hlvl_account.get('api', None)

                    # Make new API for this account if we're not using an
                    # API that's already logged in.
                    if not hlvl_api:
                        hlvl_api = setup_api(args, status, account)

                        # Hashing key.
                        # TODO: all of this should be handled properly... all
                        # these useless, inefficient threads passing around all
                        # these single-use variables are making me ill.
                        if args.hash_key:
                            key = key_scheduler.next()
                            log.debug('Using hashing key %s for this'
                                      + ' encounter.', key)
                            hlvl_api.activate_hash_server(key)

                    # We have an API object now. If necessary, store it.
                    if using_accountset and not args.no_api_store:
                        hlvl_account['api'] = hlvl_api

                    # Set location.
                    hlvl_api.set_position(*scan_location)

                    # Log in.
                    check_login(args, hlvl_account, hlvl_api, scan_location,
                                status['proxy_url'])

                    # Encounter Pokémon.
                    encounter_result = encounter_pokemon_request(
                        hlvl_api,
                        account,
                        p['encounter_id'],
                        p['spawn_point_id'],
                        scan_location)

                    # Handle errors.
                    if encounter_result:
                        # Readability.
                        responses = encounter_result['responses']

                        # Check for captcha.
                        captcha_url = responses[
                            'CHECK_CHALLENGE']['challenge_url']

                        # Throw warning but finish parsing.
                        if len(captcha_url) > 1:
                            # Flag account.
                            hlvl_account['captcha'] = True
                            log.error('Account %s encountered a captcha.'
                                      + ' Account will not be used.',
                                      hlvl_account['username'])
                        else:
                            # Update level indicator before we clear the
                            # response.
                            encounter_level = hlvl_account['level']

                            # User error?
                            if encounter_level < 30:
                                raise Exception('Expected account of level 30'
                                                + ' or higher, but account '
                                                + hlvl_account['username']
                                                + ' is only level '
                                                + str(encounter_level) + '.')

                        # We're done with the encounter. If it's from an
                        # AccountSet, release account back to the pool.
                        if using_accountset:
                            account_sets.release(hlvl_account)

                        # Clear the response for memory management.
                        encounter_result = clear_dict_response(
                            encounter_result)
                    else:
                        # Something happened. Clean up.

                        # We're done with the encounter. If it's from an
                        # AccountSet, release account back to the pool.
                        if using_accountset:
                            account_sets.release(hlvl_account)
                else:
                    log.error('No L30 accounts are available, please'
                              + ' consider adding more. Skipping encounter.')

            pokemon[p['encounter_id']] = {
                'encounter_id': b64encode(str(p['encounter_id'])),
                'spawnpoint_id': p['spawn_point_id'],
                'pokemon_id': pokemon_id,
                'latitude': p['latitude'],
                'longitude': p['longitude'],
                'disappear_time': disappear_time,
                'individual_attack': None,
                'individual_defense': None,
                'individual_stamina': None,
                'move_1': None,
                'move_2': None,
                'cp': None,
                'cp_multiplier': None,
                'height': None,
                'weight': None,
                'gender': p['pokemon_data']['pokemon_display']['gender'],
                'form': None
            }

            # Check for Unown's alphabetic character.
            if pokemon_id == 201:
                pokemon[p['encounter_id']]['form'] = p['pokemon_data'][
                    'pokemon_display'].get('form', None)

            if (encounter_result is not None and 'wild_pokemon'
                    in encounter_result['responses']['ENCOUNTER']):
                pokemon_info = encounter_result['responses'][
                    'ENCOUNTER']['wild_pokemon']['pokemon_data']

                # IVs.
                individual_attack = pokemon_info.get('individual_attack', 0)
                individual_defense = pokemon_info.get('individual_defense', 0)
                individual_stamina = pokemon_info.get('individual_stamina', 0)
                cp = pokemon_info.get('cp', None)

                # Logging: let the user know we succeeded.
                log.debug('Encounter for Pokémon ID %s'
                          + ' at %s, %s successful: '
                          + ' %s/%s/%s, %s CP.',
                          pokemon_id,
                          p['latitude'],
                          p['longitude'],
                          individual_attack,
                          individual_defense,
                          individual_stamina,
                          cp)

                pokemon[p['encounter_id']].update({
                    'individual_attack': individual_attack,
                    'individual_defense': individual_defense,
                    'individual_stamina': individual_stamina,
                    'move_1': pokemon_info['move_1'],
                    'move_2': pokemon_info['move_2'],
                    'height': pokemon_info['height_m'],
                    'weight': pokemon_info['weight_kg']
                })

                # Only add CP if we're level 30+.
                if encounter_level >= 30:
                    pokemon[p['encounter_id']]['cp'] = cp
                    pokemon[p['encounter_id']][
                        'cp_multiplier'] = pokemon_info.get(
                        'cp_multiplier', None)

            if args.webhooks:
                if (pokemon_id in args.webhook_whitelist or
                    (not args.webhook_whitelist and pokemon_id
                     not in args.webhook_blacklist)):
                    wh_poke = pokemon[p['encounter_id']].copy()
                    wh_poke.update({
                        'disappear_time': calendar.timegm(
                            disappear_time.timetuple()),
                        'last_modified_time': p['last_modified_timestamp_ms'],
                        'time_until_hidden_ms': p['time_till_hidden_ms'],
                        'verified': SpawnPoint.tth_found(sp),
                        'seconds_until_despawn': seconds_until_despawn,
                        'spawn_start': start_end[0],
                        'spawn_end': start_end[1],
                        'player_level': encounter_level
                    })
                    if wh_poke['cp_multiplier'] is not None:
                        wh_poke.update({
                            'pokemon_level': calc_pokemon_level(
                                wh_poke['cp_multiplier'])
                        })
                    wh_update_queue.put(('pokemon', wh_poke))

    if forts and (config['parse_pokestops'] or config['parse_gyms']):
        if config['parse_pokestops']:
            stop_ids = [f['id'] for f in forts if f.get('type') == 1]
            if stop_ids:
                query = (Pokestop
                         .select(Pokestop.pokestop_id, Pokestop.last_modified)
                         .where((Pokestop.pokestop_id << stop_ids))
                         .dicts())
                encountered_pokestops = [(f['pokestop_id'], int(
                    (f['last_modified'] -
                     datetime(1970, 1, 1)).total_seconds())) for f in query]

        # Complete tutorial with a Pokestop spin
        if args.complete_tutorial and not (len(captcha_url) > 1):
            if config['parse_pokestops']:
                tutorial_pokestop_spin(
                    api, level, forts, step_location, account)
            else:
                log.error(
                    'Pokestop can not be spun since parsing Pokestops is ' +
                    'not active. Check if \'-nk\' flag is accidentally set.')

        for f in forts:
            if config['parse_pokestops'] and f.get('type') == 1:  # Pokestops.
                if 'active_fort_modifier' in f:
                    lure_expiration = (datetime.utcfromtimestamp(
                        f['last_modified_timestamp_ms'] / 1000.0) +
                        timedelta(minutes=args.lure_duration))
                    active_fort_modifier = f['active_fort_modifier']
                    if args.webhooks and args.webhook_updates_only:
                        wh_update_queue.put(('pokestop', {
                            'pokestop_id': b64encode(str(f['id'])),
                            'enabled': f.get('enabled', False),
                            'latitude': f['latitude'],
                            'longitude': f['longitude'],
                            'last_modified_time': f[
                                'last_modified_timestamp_ms'],
                            'lure_expiration': calendar.timegm(
                                lure_expiration.timetuple()),
                            'active_fort_modifier': active_fort_modifier
                        }))
                else:
                    lure_expiration, active_fort_modifier = None, None

                # Send all pokestops to webhooks.
                if args.webhooks and not args.webhook_updates_only:
                    # Explicitly set 'webhook_data', in case we want to change
                    # the information pushed to webhooks.  Similar to above and
                    # previous commits.
                    l_e = None

                    if lure_expiration is not None:
                        l_e = calendar.timegm(lure_expiration.timetuple())

                    wh_update_queue.put(('pokestop', {
                        'pokestop_id': b64encode(str(f['id'])),
                        'enabled': f.get('enabled', False),
                        'latitude': f['latitude'],
                        'longitude': f['longitude'],
                        'last_modified_time': f['last_modified_timestamp_ms'],
                        'lure_expiration': l_e,
                        'active_fort_modifier': active_fort_modifier
                    }))

                if ((f['id'], int(f['last_modified_timestamp_ms'] / 1000.0))
                        in encountered_pokestops):
                    # If pokestop has been encountered before and hasn't
                    # changed don't process it.
                    stopsskipped += 1
                    continue

                pokestops[f['id']] = {
                    'pokestop_id': f['id'],
                    'enabled': f.get('enabled', False),
                    'latitude': f['latitude'],
                    'longitude': f['longitude'],
                    'last_modified': datetime.utcfromtimestamp(
                        f['last_modified_timestamp_ms'] / 1000.0),
                    'lure_expiration': lure_expiration,
                    'active_fort_modifier': active_fort_modifier
                }

            # Currently, there are only stops and gyms.
            elif config['parse_gyms'] and f.get('type') is None:
                b64_gym_id = b64encode(str(f['id']))
                gym_display = f.get('gym_display', {})
                raid_info = f.get('raid_info', {})
                # Send gyms to webhooks.
                if args.webhooks and not args.webhook_updates_only:
                    raid_active_until = 0
                    raid_battle_ms = raid_info.get('raid_battle_ms', 0)
                    raid_end_ms = raid_info.get('raid_end_ms', 0)

                    if raid_battle_ms / 1000 > time.time():
                        raid_active_until = raid_end_ms / 1000

                    # Explicitly set 'webhook_data', in case we want to change
                    # the information pushed to webhooks.  Similar to above
                    # and previous commits.
                    wh_update_queue.put(('gym', {
                        'gym_id':
                            b64_gym_id,
                        'team_id':
                            f.get('owned_by_team', 0),
                        'guard_pokemon_id':
                            f.get('guard_pokemon_id', 0),
                        'slots_available':
                            gym_display.get('slots_available', 0),
                        'total_cp':
                            gym_display.get('total_gym_cp', 0),
                        'enabled':
                            f['enabled'],
                        'latitude':
                            f['latitude'],
                        'longitude':
                            f['longitude'],
                        'lowest_pokemon_motivation':
                            gym_display.get('lowest_pokemon_motivation', 0),
                        'occupied_since':
                            calendar.timegm((datetime.utcnow() - timedelta(
                                milliseconds=gym_display.get(
                                    'occupied_millis', 0))).timetuple()),
                        'last_modified':
                            f['last_modified_timestamp_ms'],
                        'raid_active_until':
                            raid_active_until
                    }))

                gyms[f['id']] = {
                    'gym_id':
                        f['id'],
                    'team_id':
                        f.get('owned_by_team', 0),
                    'guard_pokemon_id':
                        f.get('guard_pokemon_id', 0),
                    'slots_available':
                        gym_display.get('slots_available', 0),
                    'total_cp':
                        gym_display.get('total_gym_cp', 0),
                    'enabled':
                        f['enabled'],
                    'latitude':
                        f['latitude'],
                    'longitude':
                        f['longitude'],
                    'last_modified':
                        datetime.utcfromtimestamp(
                            f['last_modified_timestamp_ms'] / 1000.0),
                }

                if config['parse_raids'] and f.get('type') is None:
                    if raid_info:
                        raids[f['id']] = {
                            'gym_id': f['id'],
                            'level': raid_info['raid_level'],
                            'spawn': datetime.utcfromtimestamp(
                                raid_info['raid_spawn_ms'] / 1000.0),
                            'start': datetime.utcfromtimestamp(
                                raid_info['raid_battle_ms'] / 1000.0),
                            'end': datetime.utcfromtimestamp(
                                raid_info['raid_end_ms'] / 1000.0),
                            'pokemon_id': None,
                            'cp': None,
                            'move_1': None,
                            'move_2': None
                        }

                        raid_pokemon = raid_info.get('raid_pokemon', {})
                        if raid_pokemon:
                            raids[f['id']].update({
                                'pokemon_id': raid_pokemon['pokemon_id'],
                                'cp': raid_pokemon['cp'],
                                'move_1': raid_pokemon['move_1'],
                                'move_2': raid_pokemon['move_2']
                            })

                        if args.webhooks and not args.webhook_updates_only:
                            wh_raid = raids[f['id']].copy()
                            wh_raid.update({
                                'gym_id': b64_gym_id,
                                'spawn': raid_info['raid_spawn_ms'] / 1000,
                                'start': raid_info['raid_battle_ms'] / 1000,
                                'end': raid_info['raid_end_ms'] / 1000,
                                'latitude': f['latitude'],
                                'longitude': f['longitude']
                            })
                            wh_update_queue.put(('raid', wh_raid))

        # Helping out the GC.
        del forts

    log.info('Parsing found Pokemon: %d, nearby: %d, pokestops: %d,' +
             ' gyms: %d, raids: %d.',
             len(pokemon) + skipped,
             nearby_pokemon,
             len(pokestops) + stopsskipped,
             len(gyms),
             len(raids))

    log.debug('Skipped Pokemon: %d, pokestops: %d.', skipped, stopsskipped)

    # Look for spawnpoints within scan_loc that are not here to see if we
    # can narrow down tth window.
    for sp in ScannedLocation.linked_spawn_points(scan_loc['cellid']):
        if sp['id'] in sp_id_list:
            # Don't overwrite changes from this parse with DB version.
            sp = spawn_points[sp['id']]
        else:
            # If the cell has completed, we need to classify all
            # the SPs that were not picked up in the scan
            if just_completed:
                SpawnpointDetectionData.classify(sp, scan_loc, now_secs)
                spawn_points[sp['id']] = sp
            if SpawnpointDetectionData.unseen(sp, now_secs):
                spawn_points[sp['id']] = sp
            endpoints = SpawnPoint.start_end(sp, args.spawn_delay)
            if clock_between(endpoints[0], now_secs, endpoints[1]):
                sp['missed_count'] += 1
                spawn_points[sp['id']] = sp
                log.warning('%s kind spawnpoint %s has no Pokemon %d times'
                            ' in a row.',
                            sp['kind'], sp['id'], sp['missed_count'])
                log.info('Possible causes: Still doing initial scan, super'
                         ' rare double spawnpoint during')
                log.info('hidden period, or Niantic has removed '
                         'spawnpoint.')

        if (not SpawnPoint.tth_found(sp) and scan_loc['done'] and
                (now_secs - sp['latest_seen'] -
                 args.spawn_delay) % 3600 < 60):
            log.warning('Spawnpoint %s was unable to locate a TTH, with '
                        'only %ss after Pokemon last seen.', sp['id'],
                        (now_secs - sp['latest_seen']) % 3600)
            log.info('Restarting current 15 minute search for TTH.')
            if sp['id'] not in sp_id_list:
                SpawnpointDetectionData.classify(sp, scan_loc, now_secs)
            sp['latest_seen'] = (sp['latest_seen'] - 60) % 3600
            sp['earliest_unseen'] = (
                sp['earliest_unseen'] + 14 * 60) % 3600
            spawn_points[sp['id']] = sp

    db_update_queue.put((ScannedLocation, {0: scan_loc}))

    if pokemon:
        db_update_queue.put((Pokemon, pokemon))
    if pokestops:
        db_update_queue.put((Pokestop, pokestops))
    if gyms:
        db_update_queue.put((Gym, gyms))
    if raids:
        db_update_queue.put((Raid, raids))
    if spawn_points:
        db_update_queue.put((SpawnPoint, spawn_points))
        db_update_queue.put((ScanSpawnPoint, scan_spawn_points))
        if sightings:
            db_update_queue.put((SpawnpointDetectionData, sightings))

    if not nearby_pokemon and not wild_pokemon:
        # After parsing the forts, we'll mark this scan as bad due to
        # a possible speed violation.
        return {
            'count': wild_pokemon_count + forts_count,
            'gyms': gyms,
            'sp_id_list': sp_id_list,
            'bad_scan': True,
            'scan_secs': now_secs
        }

    return {
        'count': wild_pokemon_count + forts_count,
        'gyms': gyms,
        'sp_id_list': sp_id_list,
        'bad_scan': False,
        'scan_secs': now_secs
    }


def parse_gyms(args, gym_responses, wh_update_queue, db_update_queue):
    gym_details = {}
    gym_members = {}
    gym_pokemon = {}
    trainers = {}
    i = 0
    for g in gym_responses.values():
        gym_state = g['gym_status_and_defenders']
        gym_id = gym_state['pokemon_fort_proto']['id']

        gym_details[gym_id] = {
            'gym_id': gym_id,
            'name': g['name'],
            'description': g.get('description'),
            'url': g['url']
        }

        if args.webhooks:
            webhook_data = {
                'id': b64encode(str(gym_id)),
                'latitude': gym_state['pokemon_fort_proto']['latitude'],
                'longitude': gym_state['pokemon_fort_proto']['longitude'],
                'team': gym_state['pokemon_fort_proto'].get(
                    'owned_by_team', 0),
                'name': g['name'],
                'description': g.get('description'),
                'url': g['url'],
                'pokemon': [],
            }

        for member in gym_state.get('gym_defender', []):
            pokemon = member['motivated_pokemon']['pokemon']
            gym_members[i] = {
                'gym_id':
                    gym_id,
                'pokemon_uid':
                    pokemon['id'],
                'cp_decayed':
                    member['motivated_pokemon']['cp_now'],
                'deployment_time':
                    datetime.utcnow() -
                    timedelta(milliseconds=member['deployment_totals']
                              ['deployment_duration_ms'])
            }
            gym_pokemon[i] = {
                'pokemon_uid':
                    pokemon['id'],
                'pokemon_id':
                    pokemon['pokemon_id'],
                'cp':
                    member['motivated_pokemon']['cp_when_deployed'],
                'trainer_name':
                    pokemon['owner_name'],
                'num_upgrades':
                    pokemon.get('num_upgrades', 0),
                'move_1':
                    pokemon.get('move_1'),
                'move_2':
                    pokemon.get('move_2'),
                'height':
                    pokemon.get('height_m'),
                'weight':
                    pokemon.get('weight_kg'),
                'stamina':
                    pokemon.get('stamina'),
                'stamina_max':
                    pokemon.get('stamina_max'),
                'cp_multiplier':
                    pokemon.get('cp_multiplier'),
                'additional_cp_multiplier':
                    pokemon.get('additional_cp_multiplier', 0),
                'iv_defense':
                    pokemon.get('individual_defense', 0),
                'iv_stamina':
                    pokemon.get('individual_stamina', 0),
                'iv_attack':
                    pokemon.get('individual_attack', 0),
                'last_seen':
                    datetime.utcnow(),
            }

            trainers[i] = {
                'name': member['trainer_public_profile']['name'],
                'team': member['trainer_public_profile']['team_color'],
                'level': member['trainer_public_profile']['level'],
                'last_seen': datetime.utcnow(),
            }

            if args.webhooks:
                wh_pokemon = gym_pokemon[i].copy()
                del wh_pokemon['last_seen']
                wh_pokemon.update({
                    'cp_decayed':
                        member['motivated_pokemon']['cp_now'],
                    'trainer_level':
                        member['trainer_public_profile']['level'],
                    'deployment_time': calendar.timegm(
                        gym_members[i]['deployment_time'].timetuple())
                })
                webhook_data['pokemon'].append(wh_pokemon)

            i += 1
        if args.webhooks:
            wh_update_queue.put(('gym_details', webhook_data))

    # All this database stuff is synchronous (not using the upsert queue) on
    # purpose.  Since the search workers load the GymDetails model from the
    # database to determine if a gym needs to be rescanned, we need to be sure
    # the GymDetails get fully committed to the database before moving on.
    #
    # We _could_ synchronously upsert GymDetails, then queue the other tables
    # for upsert, but that would put that Gym's overall information in a weird
    # non-atomic state.

    # Upsert all the models.
    if gym_details:
        db_update_queue.put((GymDetails, gym_details))
    if gym_pokemon:
        db_update_queue.put((GymPokemon, gym_pokemon))
    if trainers:
        db_update_queue.put((Trainer, trainers))

    # This needs to be completed in a transaction, because we don't wany any
    # other thread or process to mess with the GymMembers for the gyms we're
    # updating while we're updating the bridge table.
    with flaskDb.database.transaction():
        # Get rid of all the gym members, we're going to insert new records.
        if gym_details:
            DeleteQuery(GymMember).where(
                GymMember.gym_id << gym_details.keys()).execute()

        # Insert new gym members.
        if gym_members:
            db_update_queue.put((GymMember, gym_members))

    log.info('Upserted gyms: %d, gym members: %d.',
             len(gym_details),
             len(gym_members))


def db_updater(args, q, db):
    # The forever loop.
    while True:
        try:

            while True:
                try:
                    flaskDb.connect_db()
                    break
                except Exception as e:
                    log.exception('%s... Retrying...', repr(e))
                    time.sleep(5)

            # Loop the queue.
            while True:
                last_upsert = default_timer()
                model, data = q.get()

                bulk_upsert(model, data, db)
                q.task_done()

                log.debug('Upserted to %s, %d records (upsert queue '
                          'remaining: %d) in %.2f seconds.',
                          model.__name__,
                          len(data),
                          q.qsize(),
                          default_timer() - last_upsert)

                # Helping out the GC.
                del model
                del data

                if q.qsize() > 50:
                    log.warning(
                        "DB queue is > 50 (@%d); try increasing --db-threads.",
                        q.qsize())

        except Exception as e:
            log.exception('Exception in db_updater: %s', repr(e))
            time.sleep(5)


def clean_db_loop(args):
    while True:
        try:
            query = (MainWorker
                     .delete()
                     .where((MainWorker.last_modified <
                             (datetime.utcnow() - timedelta(minutes=30)))))
            query.execute()

            query = (WorkerStatus
                     .delete()
                     .where((WorkerStatus.last_modified <
                             (datetime.utcnow() - timedelta(minutes=30)))))
            query.execute()

            # Remove active modifier from expired lured pokestops.
            query = (Pokestop
                     .update(lure_expiration=None, active_fort_modifier=None)
                     .where(Pokestop.lure_expiration < datetime.utcnow()))
            query.execute()

            # Remove old (unusable) captcha tokens
            query = (Token
                     .delete()
                     .where((Token.last_updated <
                             (datetime.utcnow() - timedelta(minutes=2)))))
            query.execute()

            # Remove expired HashKeys
            query = (HashKeys
                     .delete()
                     .where(HashKeys.expires <
                            (datetime.now() - timedelta(days=1))))
            query.execute()

            # If desired, clear old Pokemon spawns.
            if args.purge_data > 0:
                log.info("Beginning purge of old Pokemon spawns.")
                start = datetime.utcnow()
                query = (Pokemon
                         .delete()
                         .where((Pokemon.disappear_time <
                                 (datetime.utcnow() -
                                  timedelta(hours=args.purge_data)))))
                rows = query.execute()
                end = datetime.utcnow()
                diff = end - start
                log.info("Completed purge of old Pokemon spawns. "
                         "%i deleted in %f seconds.",
                         rows, diff.total_seconds())

            log.info('Regular database cleaning complete.')
            time.sleep(60)
        except Exception as e:
            log.exception('Exception in clean_db_loop: %s', repr(e))


def bulk_upsert(cls, data, db):
    num_rows = len(data.values())
    i = 0

    if args.db_type == 'mysql':
        step = 250
    else:
        # SQLite has a default max number of parameters of 999,
        # so we need to limit how many rows we insert for it.
        step = 50

    with db.atomic():
        while i < num_rows:
            log.debug('Inserting items %d to %d.', i, min(i + step, num_rows))
            try:
                # Turn off FOREIGN_KEY_CHECKS on MySQL, because apparently it's
                # unable to recognize strings to update unicode keys for
                # foreign key fields, thus giving lots of foreign key
                # constraint errors.
                if args.db_type == 'mysql':
                    db.execute_sql('SET FOREIGN_KEY_CHECKS=0;')

                # Use peewee's own implementation of the insert_many() method.
                InsertQuery(cls, rows=data.values()[
                            i:min(i + step, num_rows)]).upsert().execute()

                if args.db_type == 'mysql':
                    db.execute_sql('SET FOREIGN_KEY_CHECKS=1;')

            except Exception as e:
                # If there is a DB table constraint error, dump the data and
                # don't retry.
                #
                # Unrecoverable error strings:
                unrecoverable = ['constraint', 'has no attribute',
                                 'peewee.IntegerField object at']
                has_unrecoverable = filter(
                    lambda x: x in str(e), unrecoverable)
                if has_unrecoverable:
                    log.exception('%s. Data is:', repr(e))
                    log.warning(data.items())
                else:
                    log.warning('%s... Retrying...', repr(e))
                    time.sleep(1)
                    continue

            i += step


def create_tables(db):
    db.connect()
    tables = [Pokemon, Pokestop, Gym, Raid, ScannedLocation, GymDetails,
              GymMember, GymPokemon, Trainer, MainWorker, WorkerStatus,
              SpawnPoint, ScanSpawnPoint, SpawnpointDetectionData,
              Token, LocationAltitude, PlayerLocale, HashKeys]
    for table in tables:
        if not table.table_exists():
            log.info('Creating table: %s', table.__name__)
            db.create_tables([table], safe=True)
        else:
            log.debug('Skipping table %s, it already exists.', table.__name__)
    db.close()


def drop_tables(db):
    tables = [Pokemon, Pokestop, Gym, Raid, ScannedLocation, Versions,
              GymDetails, GymMember, GymPokemon, Trainer, MainWorker,
              WorkerStatus, SpawnPoint, ScanSpawnPoint,
              SpawnpointDetectionData, LocationAltitude, PlayerLocale,
              Token, HashKeys]
    db.connect()
    db.execute_sql('SET FOREIGN_KEY_CHECKS=0;')
    for table in tables:
        if table.table_exists():
            log.info('Dropping table: %s', table.__name__)
            db.drop_tables([table], safe=True)

    db.execute_sql('SET FOREIGN_KEY_CHECKS=1;')
    db.close()


def verify_table_encoding(db):
    if args.db_type == 'mysql':
        db.connect()

        cmd_sql = '''
            SELECT table_name FROM information_schema.tables WHERE
            table_collation != "utf8mb4_unicode_ci" AND table_schema = "%s";
            ''' % args.db_name
        change_tables = db.execute_sql(cmd_sql)

        cmd_sql = "SHOW tables;"
        tables = db.execute_sql(cmd_sql)

        if change_tables.rowcount > 0:
            log.info('Changing collation and charset on %s tables.',
                     change_tables.rowcount)

            if change_tables.rowcount == tables.rowcount:
                log.info('Changing whole database, this might a take while.')

            with db.atomic():
                db.execute_sql('SET FOREIGN_KEY_CHECKS=0;')
                for table in change_tables:
                    log.debug('Changing collation and charset on table %s.',
                              table[0])
                    cmd_sql = '''ALTER TABLE %s CONVERT TO CHARACTER SET utf8mb4
                                COLLATE utf8mb4_unicode_ci;''' % str(table[0])
                    db.execute_sql(cmd_sql)
                db.execute_sql('SET FOREIGN_KEY_CHECKS=1;')
        db.close()


def verify_database_schema(db):
    db.connect()
    if not Versions.table_exists():
        db.create_tables([Versions])

        if ScannedLocation.table_exists():
            # Versions table doesn't exist, but there are tables. This must
            # mean the user is coming from a database that existed before we
            # started tracking the schema version. Perform a full upgrade.
            InsertQuery(Versions, {Versions.key: 'schema_version',
                                   Versions.val: 0}).execute()
            database_migrate(db, 0)
        else:
            InsertQuery(Versions, {Versions.key: 'schema_version',
                                   Versions.val: db_schema_version}).execute()

    else:
        db_ver = Versions.get(Versions.key == 'schema_version').val

        if db_ver < db_schema_version:
            database_migrate(db, db_ver)

        elif db_ver > db_schema_version:
            log.error('Your database version (%i) appears to be newer than '
                      'the code supports (%i).', db_ver, db_schema_version)
            log.error('Please upgrade your code base or drop all tables in '
                      'your database.')
            sys.exit(1)
    db.close()


def database_migrate(db, old_ver):
    # Update database schema version.
    Versions.update(val=db_schema_version).where(
        Versions.key == 'schema_version').execute()

    log.info('Detected database version %i, updating to %i...',
             old_ver, db_schema_version)

    # Perform migrations here.
    migrator = None
    if args.db_type == 'mysql':
        migrator = MySQLMigrator(db)
    else:
        migrator = SqliteMigrator(db)

    if old_ver < 2:
        migrate(migrator.add_column('pokestop', 'encounter_id',
                                    Utf8mb4CharField(max_length=50,
                                                     null=True)))

    if old_ver < 3:
        migrate(
            migrator.add_column('pokestop', 'active_fort_modifier',
                                Utf8mb4CharField(max_length=50, null=True)),
            migrator.drop_column('pokestop', 'encounter_id'),
            migrator.drop_column('pokestop', 'active_pokemon_id')
        )

    if old_ver < 4:
        db.drop_tables([ScannedLocation])

    if old_ver < 5:
        # Some Pokemon were added before the 595 bug was "fixed".
        # Clean those up for a better UX.
        query = (Pokemon
                 .delete()
                 .where(Pokemon.disappear_time >
                        (datetime.utcnow() - timedelta(hours=24))))
        query.execute()

    if old_ver < 6:
        migrate(
            migrator.add_column('gym', 'last_scanned',
                                DateTimeField(null=True)),
        )

    if old_ver < 7:
        migrate(
            migrator.drop_column('gymdetails', 'description'),
            migrator.add_column('gymdetails', 'description',
                                TextField(null=True, default=""))
        )

    if old_ver < 8:
        migrate(
            migrator.add_column('pokemon', 'individual_attack',
                                IntegerField(null=True, default=0)),
            migrator.add_column('pokemon', 'individual_defense',
                                IntegerField(null=True, default=0)),
            migrator.add_column('pokemon', 'individual_stamina',
                                IntegerField(null=True, default=0)),
            migrator.add_column('pokemon', 'move_1',
                                IntegerField(null=True, default=0)),
            migrator.add_column('pokemon', 'move_2',
                                IntegerField(null=True, default=0))
        )

    if old_ver < 9:
        migrate(
            migrator.add_column('pokemon', 'last_modified',
                                DateTimeField(null=True, index=True)),
            migrator.add_column('pokestop', 'last_updated',
                                DateTimeField(null=True, index=True))
        )

    if old_ver < 10:
        # Information in ScannedLocation and Member Status is probably
        # out of date.  Drop and recreate with new schema.

        db.drop_tables([ScannedLocation])
        db.drop_tables([WorkerStatus])

    if old_ver < 11:

        db.drop_tables([ScanSpawnPoint])

    if old_ver < 13:

        db.drop_tables([WorkerStatus])
        db.drop_tables([MainWorker])

    if old_ver < 14:
        migrate(
            migrator.add_column('pokemon', 'weight',
                                DoubleField(null=True, default=0)),
            migrator.add_column('pokemon', 'height',
                                DoubleField(null=True, default=0)),
            migrator.add_column('pokemon', 'gender',
                                IntegerField(null=True, default=0))
        )

    if old_ver < 15:
        # we don't have to touch sqlite because it has REAL and INTEGER only
        if args.db_type == 'mysql':
            db.execute_sql('ALTER TABLE `pokemon` '
                           'MODIFY COLUMN `weight` FLOAT NULL DEFAULT NULL,'
                           'MODIFY COLUMN `height` FLOAT NULL DEFAULT NULL,'
                           'MODIFY COLUMN `gender` SMALLINT NULL DEFAULT NULL'
                           ';')

    if old_ver < 16:
        log.info('This DB schema update can take some time. '
                 'Please be patient.')

        # change some column types from INT to SMALLINT
        # we don't have to touch sqlite because it has INTEGER only
        if args.db_type == 'mysql':
            db.execute_sql(
                'ALTER TABLE `pokemon` '
                'MODIFY COLUMN `pokemon_id` SMALLINT NOT NULL,'
                'MODIFY COLUMN `individual_attack` SMALLINT '
                'NULL DEFAULT NULL,'
                'MODIFY COLUMN `individual_defense` SMALLINT '
                'NULL DEFAULT NULL,'
                'MODIFY COLUMN `individual_stamina` SMALLINT '
                'NULL DEFAULT NULL,'
                'MODIFY COLUMN `move_1` SMALLINT NULL DEFAULT NULL,'
                'MODIFY COLUMN `move_2` SMALLINT NULL DEFAULT NULL;'
            )
            db.execute_sql(
                'ALTER TABLE `gym` '
                'MODIFY COLUMN `team_id` SMALLINT NOT NULL,'
                'MODIFY COLUMN `guard_pokemon_id` SMALLINT NOT NULL;'
            )
            db.execute_sql(
                'ALTER TABLE `scannedlocation` '
                'MODIFY COLUMN `band1` SMALLINT NOT NULL,'
                'MODIFY COLUMN `band2` SMALLINT NOT NULL,'
                'MODIFY COLUMN `band3` SMALLINT NOT NULL,'
                'MODIFY COLUMN `band4` SMALLINT NOT NULL,'
                'MODIFY COLUMN `band5` SMALLINT NOT NULL,'
                'MODIFY COLUMN `midpoint` SMALLINT NOT NULL,'
                'MODIFY COLUMN `width` SMALLINT NOT NULL;'
            )
            db.execute_sql(
                'ALTER TABLE `spawnpoint` '
                'MODIFY COLUMN `latest_seen` SMALLINT NOT NULL,'
                'MODIFY COLUMN `earliest_unseen` SMALLINT NOT NULL;'
            )
            db.execute_sql(
                'ALTER TABLE `spawnpointdetectiondata` '
                'MODIFY COLUMN `tth_secs` SMALLINT NULL DEFAULT NULL;'
            )
            db.execute_sql(
                'ALTER TABLE `versions` '
                'MODIFY COLUMN `val` SMALLINT NOT NULL;'
            )
            db.execute_sql(
                'ALTER TABLE `gympokemon` '
                'MODIFY COLUMN `pokemon_id` SMALLINT NOT NULL,'
                'MODIFY COLUMN `cp` SMALLINT NOT NULL,'
                'MODIFY COLUMN `num_upgrades` SMALLINT NULL DEFAULT NULL,'
                'MODIFY COLUMN `move_1` SMALLINT NULL DEFAULT NULL,'
                'MODIFY COLUMN `move_2` SMALLINT NULL DEFAULT NULL,'
                'MODIFY COLUMN `stamina` SMALLINT NULL DEFAULT NULL,'
                'MODIFY COLUMN `stamina_max` SMALLINT NULL DEFAULT NULL,'
                'MODIFY COLUMN `iv_defense` SMALLINT NULL DEFAULT NULL,'
                'MODIFY COLUMN `iv_stamina` SMALLINT NULL DEFAULT NULL,'
                'MODIFY COLUMN `iv_attack` SMALLINT NULL DEFAULT NULL;'
            )
            db.execute_sql(
                'ALTER TABLE `trainer` '
                'MODIFY COLUMN `team` SMALLINT NOT NULL,'
                'MODIFY COLUMN `level` SMALLINT NOT NULL;'
            )

        # add some missing indexes
        migrate(
            migrator.add_index('gym', ('last_scanned',), False),
            migrator.add_index('gymmember', ('last_scanned',), False),
            migrator.add_index('gymmember', ('pokemon_uid',), False),
            migrator.add_index('gympokemon', ('trainer_name',), False),
            migrator.add_index('pokestop', ('active_fort_modifier',), False),
            migrator.add_index('spawnpointdetectiondata', ('spawnpoint_id',),
                               False),
            migrator.add_index('token', ('last_updated',), False)
        )
        # pokestop.last_updated was missing in a previous migration
        # check whether we have to add it
        has_last_updated_index = False
        for index in db.get_indexes('pokestop'):
            if index.columns[0] == 'last_updated':
                has_last_updated_index = True
                break
        if not has_last_updated_index:
            log.debug('pokestop.last_updated index is missing. Creating now.')
            migrate(
                migrator.add_index('pokestop', ('last_updated',), False)
            )

    if old_ver < 17:
        migrate(
            migrator.add_column('pokemon', 'form',
                                SmallIntegerField(null=True))
        )

    if old_ver < 18:
        migrate(
            migrator.add_column('pokemon', 'cp',
                                SmallIntegerField(null=True))
        )

    if old_ver < 19:
        migrate(
            migrator.add_column('pokemon', 'cp_multiplier',
                                FloatField(null=True))
        )

    if old_ver < 20:
        migrate(
            migrator.drop_column('gym', 'gym_points'),
            migrator.add_column('gym', 'slots_available',
                                SmallIntegerField(null=False, default=0)),
            migrator.add_column('gymmember', 'cp_decayed',
                                SmallIntegerField(null=False, default=0)),
            migrator.add_column('gymmember', 'deployment_time',
                                DateTimeField(
                                    null=False, default=datetime.utcnow())),
            migrator.add_column('gym', 'total_cp',
                                SmallIntegerField(null=False, default=0)))

    # Always log that we're done.
    log.info('Schema upgrade complete.')
