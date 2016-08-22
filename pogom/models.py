#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import calendar
import sys
import time
import geopy
from peewee import SqliteDatabase, InsertQuery, \
    IntegerField, CharField, DoubleField, BooleanField, \
    DateTimeField, CompositeKey, fn
from playhouse.flask_utils import FlaskDB
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import RetryOperationalError
from playhouse.migrate import migrate, MySQLMigrator, SqliteMigrator
from datetime import datetime, timedelta
from base64 import b64encode

from . import config
from .utils import get_pokemon_name, get_pokemon_rarity, get_pokemon_types, get_args
from .transform import transform_from_wgs_to_gcj, get_new_coords, generate_location_steps
from .customLog import printPokemon

log = logging.getLogger(__name__)

args = get_args()
flaskDb = FlaskDB()

db_schema_version = 5


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

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    @staticmethod
    def get_active(swLat, swLng, neLat, neLng):
        if swLat is None or swLng is None or neLat is None or neLng is None:
            query = (Pokemon
                     .select()
                     .where(Pokemon.disappear_time > datetime.utcnow())
                     .dicts())
        else:
            query = (Pokemon
                     .select()
                     .where((Pokemon.disappear_time > datetime.utcnow()) &
                            (Pokemon.latitude >= swLat) &
                            (Pokemon.longitude >= swLng) &
                            (Pokemon.latitude <= neLat) &
                            (Pokemon.longitude <= neLng))
                     .dicts())

        pokemons = []
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            p['pokemon_rarity'] = get_pokemon_rarity(p['pokemon_id'])
            p['pokemon_types'] = get_pokemon_types(p['pokemon_id'])
            if args.china:
                p['latitude'], p['longitude'] = \
                    transform_from_wgs_to_gcj(p['latitude'], p['longitude'])
            pokemons.append(p)

        return pokemons

    @staticmethod
    def get_active_by_id(ids, swLat, swLng, neLat, neLng):
        if swLat is None or swLng is None or neLat is None or neLng is None:
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

        pokemons = []
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            p['pokemon_rarity'] = get_pokemon_rarity(p['pokemon_id'])
            p['pokemon_types'] = get_pokemon_types(p['pokemon_id'])
            if args.china:
                p['latitude'], p['longitude'] = \
                    transform_from_wgs_to_gcj(p['latitude'], p['longitude'])
            pokemons.append(p)

        return pokemons

    @classmethod
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
                 .where(Pokemon.disappear_time == pokemon_count_query.c.lastappeared)
                 .dicts()
                 )
        pokemons = []
        total = 0
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            pokemons.append(p)
            total += p['count']

        return {'pokemon': pokemons, 'total': total}

    @classmethod
    def get_appearances(cls, pokemon_id, last_appearance):
        query = (Pokemon
                 .select()
                 .where((Pokemon.pokemon_id == pokemon_id) &
                        (Pokemon.disappear_time > datetime.utcfromtimestamp(last_appearance / 1000.0))
                        )
                 .order_by(Pokemon.disappear_time.asc())
                 .dicts()
                 )
        appearances = []
        for a in query:
            appearances.append(a)
        return appearances

    @classmethod
    def get_spawnpoints(cls, southBoundary, westBoundary, northBoundary, eastBoundary):
        query = Pokemon.select(Pokemon.latitude, Pokemon.longitude, Pokemon.spawnpoint_id)

        if None not in (northBoundary, southBoundary, westBoundary, eastBoundary):
            query = (query
                     .where((Pokemon.latitude <= northBoundary) &
                            (Pokemon.latitude >= southBoundary) &
                            (Pokemon.longitude >= westBoundary) &
                            (Pokemon.longitude <= eastBoundary)
                            ))

        # Sqlite doesn't support distinct on columns
        if args.db_type == 'mysql':
            query = query.distinct(Pokemon.spawnpoint_id)
        else:
            query = query.group_by(Pokemon.spawnpoint_id)

        return list(query.dicts())

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

        # Filter to spawns which actually fall in the hex locations
        # This loop is about as non-pythonic as you can get, I bet.
        # Oh well.
        filtered = []
        hex_locations = list(generate_location_steps(center, steps, 0.07))
        for hl in hex_locations:
            for idx, sp in enumerate(s):
                if geopy.distance.distance(hl, (sp['lat'], sp['lng'])).meters <= 70:
                    filtered.append(s.pop(idx))

        # at this point, 'time' is DISAPPEARANCE time, we're going to morph it to APPEARANCE time
        for location in filtered:
            # examples: time    shifted
            #           0       (   0 + 2700) = 2700 % 3600 = 2700 (0th minute to 45th minute, 15 minutes prior to appearance as time wraps around the hour)
            #           1800    (1800 + 2700) = 4500 % 3600 =  900 (30th minute, moved to arrive at 15th minute)
            # todo: this DOES NOT ACCOUNT for pokemons that appear sooner and live longer, but you'll _always_ have at least 15 minutes, so it works well enough
            location['time'] = (location['time'] + 2700) % 3600

        return filtered


class Pokestop(BaseModel):
    pokestop_id = CharField(primary_key=True, max_length=50)
    enabled = BooleanField()
    latitude = DoubleField()
    longitude = DoubleField()
    last_modified = DateTimeField(index=True)
    lure_expiration = DateTimeField(null=True, index=True)
    active_fort_modifier = CharField(max_length=50, null=True)

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    @staticmethod
    def get_stops(swLat, swLng, neLat, neLng):
        if swLat is None or swLng is None or neLat is None or neLng is None:
            query = (Pokestop
                     .select()
                     .dicts())
        else:
            query = (Pokestop
                     .select()
                     .where((Pokestop.latitude >= swLat) &
                            (Pokestop.longitude >= swLng) &
                            (Pokestop.latitude <= neLat) &
                            (Pokestop.longitude <= neLng))
                     .dicts())

        pokestops = []
        for p in query:
            if args.china:
                p['latitude'], p['longitude'] = \
                    transform_from_wgs_to_gcj(p['latitude'], p['longitude'])
            pokestops.append(p)

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

    class Meta:
        indexes = ((('latitude', 'longitude'), False),)

    @staticmethod
    def get_gyms(swLat, swLng, neLat, neLng):
        if swLat is None or swLng is None or neLat is None or neLng is None:
            query = (Gym
                     .select()
                     .dicts())
        else:
            query = (Gym
                     .select()
                     .where((Gym.latitude >= swLat) &
                            (Gym.longitude >= swLng) &
                            (Gym.latitude <= neLat) &
                            (Gym.longitude <= neLng))
                     .dicts())

        gyms = []
        for g in query:
            gyms.append(g)

        return gyms


class ScannedLocation(BaseModel):
    latitude = DoubleField()
    longitude = DoubleField()
    last_modified = DateTimeField(index=True)

    class Meta:
        primary_key = CompositeKey('latitude', 'longitude')

    @staticmethod
    def get_recent(swLat, swLng, neLat, neLng):
        query = (ScannedLocation
                 .select()
                 .where((ScannedLocation.last_modified >=
                        (datetime.utcnow() - timedelta(minutes=15))) &
                        (ScannedLocation.latitude >= swLat) &
                        (ScannedLocation.longitude >= swLng) &
                        (ScannedLocation.latitude <= neLat) &
                        (ScannedLocation.longitude <= neLng))
                 .dicts())

        scans = []
        for s in query:
            scans.append(s)

        return scans


class Versions(flaskDb.Model):
    key = CharField()
    val = IntegerField()

    class Meta:
        primary_key = False


def hex_bounds(center, steps):
    # Make a box that is (70m * step_limit * 2) + 70m away from the center point
    # Rationale is that you need to travel
    sp_dist = 0.07 * 2 * steps
    n = get_new_coords(center, sp_dist, 0)[0]
    e = get_new_coords(center, sp_dist, 90)[1]
    s = get_new_coords(center, sp_dist, 180)[0]
    w = get_new_coords(center, sp_dist, 270)[1]
    return (n, e, s, w)


# todo: this probably shouldn't _really_ be in "models" anymore, but w/e
def parse_map(args, map_dict, step_location, db_update_queue, wh_update_queue):
    pokemons = {}
    pokestops = {}
    gyms = {}

    cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    for cell in cells:
        if config['parse_pokemon']:
            for p in cell.get('wild_pokemons', []):
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
                pokemons[p['encounter_id']] = {
                    'encounter_id': b64encode(str(p['encounter_id'])),
                    'spawnpoint_id': p['spawn_point_id'],
                    'pokemon_id': p['pokemon_data']['pokemon_id'],
                    'latitude': p['latitude'],
                    'longitude': p['longitude'],
                    'disappear_time': d_t
                }

                if args.webhooks:
                    wh_update_queue.put(('pokemon', {
                        'encounter_id': b64encode(str(p['encounter_id'])),
                        'spawnpoint_id': p['spawn_point_id'],
                        'pokemon_id': p['pokemon_data']['pokemon_id'],
                        'latitude': p['latitude'],
                        'longitude': p['longitude'],
                        'disappear_time': calendar.timegm(d_t.timetuple()),
                        'last_modified_time': p['last_modified_timestamp_ms'],
                        'time_until_hidden_ms': p['time_till_hidden_ms']
                    }))

        for f in cell.get('forts', []):
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
                        'last_modified': calendar.timegm(pokestops[f['id']]['last_modified'].timetuple()),
                        'lure_expiration': l_e,
                        'active_fort_modifier': active_fort_modifier
                    }))

            elif config['parse_gyms'] and f.get('type') is None:  # Currently, there are only stops and gyms
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
                        'last_modified': calendar.timegm(gyms[f['id']]['last_modified'].timetuple())
                    }))

    if len(pokemons):
        db_update_queue.put((Pokemon, pokemons))
    if len(pokestops):
        db_update_queue.put((Pokestop, pokestops))
    if len(gyms):
        db_update_queue.put((Gym, gyms))

    log.info('Parsing found %d pokemons, %d pokestops, and %d gyms',
             len(pokemons),
             len(pokestops),
             len(gyms))

    db_update_queue.put((ScannedLocation, {0: {
        'latitude': step_location[0],
        'longitude': step_location[1],
        'last_modified': datetime.utcnow()
    }}))

    return len(pokemons) + len(pokestops) + len(gyms)


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

            # If desired, clear old pokemon spawns
            if args.purge_data > 0:
                query = (Pokemon
                         .delete()
                         .where((Pokemon.disappear_time <
                                (datetime.utcnow() - timedelta(hours=args.purge_data)))))

            log.info('Regular database cleaning complete')
            time.sleep(60)
        except Exception as e:
            log.exception('Exception in clean_db_loop: %s', e)


def bulk_upsert(cls, data):
    num_rows = len(data.values())
    i = 0
    step = 120

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
    db.create_tables([Pokemon, Pokestop, Gym, ScannedLocation], safe=True)
    db.close()


def drop_tables(db):
    db.connect()
    db.drop_tables([Pokemon, Pokestop, Gym, ScannedLocation, Versions], safe=True)
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
