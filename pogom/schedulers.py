#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Schedulers determine how worker's queues get filled. They control which
locations get scanned, in what order, at what time. This allows further
optimizations to be easily added, without having to modify the existing
overseer and worker thread code.

Schedulers will recieve:

queues - A list of queues for the workers they control. For now, this is a
            list containing a single queue.
status - A list of status dicts for the workers. Schedulers can use this
            information to make more intelligent scheduling decisions.
            Useful values include:
            - last_scan_date: unix timestamp of when the last scan was
                completed
            - location: [lat,lng,alt] of the last scan
args - The configuration arguments. This may not include all of the arguments,
            just ones that are relevant to this scheduler instance (eg. if
            multiple locations become supported, the args passed to the
            scheduler will only contain the parameters for the location
            it handles)

Schedulers must fill the queues with items to search.

Queue items are a list containing:
    [step, (latitude, longitude, altitude),
     appears_seconds, disappears_seconds)]
Where:
    - step is the step number. Used only for display purposes.
    - (latitude, longitude, altitude) is the location to be scanned.
    - appears_seconds is the unix timestamp of when the pokemon next appears
    - disappears_seconds is the unix timestamp of when the
        pokemon next disappears

    appears_seconds and disappears_seconds are used to skip scans that are too
    late, and wait for scans the worker is early for.  If a scheduler doesn't
    have a specific time a location needs to be scanned, it should set
    both to 0.

If implementing a new scheduler, place it before SchedulerFactory, and
add it to __scheduler_classes
'''

import itertools
import logging
import math
import json
import time
import sys
from timeit import default_timer
from threading import Lock
from copy import deepcopy
import traceback
from collections import Counter
from queue import Empty
from operator import itemgetter
from datetime import datetime, timedelta
from .transform import get_new_coords
from .models import (hex_bounds, SpawnPoint, ScannedLocation,
                     ScanSpawnPoint, HashKeys)
from .utils import now, cur_sec, cellid, distance
from .altitude import get_altitude
from .geofence import Geofences

log = logging.getLogger(__name__)


# Simple base class that all other schedulers inherit from.
# Most of these functions should be overridden in the actual scheduler classes.
# Not all scheduler methods will need to use all of the functions.
class BaseScheduler(object):

    def __init__(self, queues, status, args):
        self.queues = queues
        self.status = status
        self.geofences = Geofences()
        self.args = args
        self.scan_location = False
        self.ready = False

    # Schedule function fills the queues with data.
    def schedule(self):
        log.warning('BaseScheduler does not schedule any items')

    # location_changed function is called whenever the location being
    # scanned changes.
    # scan_location = (lat, lng, alt)
    def location_changed(self, scan_location, dbq):
        self.scan_location = scan_location
        self.empty_queues()

    # scanning_pause function is called when scanning is paused from the UI.
    # The default function will empty all the queues.
    # Note: This function is called repeatedly while scanning is paused!
    def scanning_paused(self):
        self.empty_queues()

    def get_overseer_message(self):
        nextitem = self.queues[0].queue[0]
        message = 'Processing search queue, next item is {:6f},{:6f}'.format(
            nextitem[1][0], nextitem[1][1])
        # If times are specified, print the time of the next queue item, and
        # how many seconds ahead/behind realtime
        if nextitem[2]:
            message += ' @ {}'.format(
                time.strftime('%H:%M:%S', time.localtime(nextitem[2])))
            if nextitem[2] > now():
                message += ' ({}s ahead)'.format(nextitem[2] - now())
            else:
                message += ' ({}s behind)'.format(now() - nextitem[2])
        return message

    # check if time to refresh queue
    def time_to_refresh_queue(self):
        return self.queues[0].empty()

    def task_done(self, *args):
        return self.queues[0].task_done()

    # Return the next item in the queue
    def next_item(self, search_items_queue):
        step, step_location, appears, leaves = self.queues[0].get()
        remain = appears - now() + 10
        messages = {
            'wait': 'Waiting for item from queue.',
            'early': 'Early for {:6f},{:6f}; waiting {}s...'.format(
                step_location[0], step_location[1], remain),
            'late': 'Too late for location {:6f},{:6f}; skipping.'.format(
                step_location[0], step_location[1]),
            'search': 'Searching at {:6f},{:6f},{:6f}.'.format(
                step_location[0], step_location[1], step_location[2]),
            'invalid': ('Invalid response at {:6f},{:6f}, ' +
                        'abandoning location.').format(step_location[0],
                                                       step_location[1])
        }
        return step, step_location, appears, leaves, messages, 0

    # How long to delay since last action
    def delay(self, *args):
        return self.args.scan_delay  # always scan delay time

    # Function to empty all queues in the queues list
    def empty_queues(self):
        self.ready = False
        for queue in self.queues:
            if not queue.empty():
                try:
                    while True:
                        queue.get_nowait()
                except Empty:
                    pass


# Hex Search is the classic search method, with the pokepath modification,
# searching in a hex grid around the center location.
class HexSearch(BaseScheduler):

    # Call base initialization, set step_distance.
    def __init__(self, queues, status, args):
        BaseScheduler.__init__(self, queues, status, args)

        # If we are only scanning for pokestops/gyms, the scan radius can be
        # 450m.  Otherwise 70m.
        if self.args.no_pokemon:
            self.step_distance = 0.450
        else:
            self.step_distance = 0.070

        self.step_limit = args.step_limit
        # This will hold the list of locations to scan so it can be reused,
        # instead of recalculating on each loop.
        self.locations = False

    # On location change, empty the current queue and the locations list
    def location_changed(self, scan_location, dbq):
        self.scan_location = scan_location
        self.empty_queues()
        self.locations = False

    # Generates the list of locations to scan.
    def _generate_locations(self):
        NORTH = 0
        EAST = 90
        SOUTH = 180
        WEST = 270

        # Dist between column centers.
        xdist = math.sqrt(3) * self.step_distance
        ydist = 3 * (self.step_distance / 2)       # Dist between row centers.

        results = []

        results.append((self.scan_location[0], self.scan_location[1], 0))

        if self.step_limit > 1:
            loc = self.scan_location

            # Upper part.
            ring = 1
            while ring < self.step_limit:

                loc = get_new_coords(
                    loc, xdist, WEST if ring % 2 == 1 else EAST)
                results.append((loc[0], loc[1], 0))

                for i in range(ring):
                    loc = get_new_coords(loc, ydist, NORTH)
                    loc = get_new_coords(
                        loc, xdist / 2, EAST if ring % 2 == 1 else WEST)
                    results.append((loc[0], loc[1], 0))

                for i in range(ring):
                    loc = get_new_coords(
                        loc, xdist, EAST if ring % 2 == 1 else WEST)
                    results.append((loc[0], loc[1], 0))

                for i in range(ring):
                    loc = get_new_coords(loc, ydist, SOUTH)
                    loc = get_new_coords(
                        loc, xdist / 2, EAST if ring % 2 == 1 else WEST)
                    results.append((loc[0], loc[1], 0))

                ring += 1

            # Lower part.
            ring = self.step_limit - 1

            loc = get_new_coords(loc, ydist, SOUTH)
            loc = get_new_coords(
                loc, xdist / 2, WEST if ring % 2 == 1 else EAST)
            results.append((loc[0], loc[1], 0))

            while ring > 0:

                if ring == 1:
                    loc = get_new_coords(loc, xdist, WEST)
                    results.append((loc[0], loc[1], 0))

                else:
                    for i in range(ring - 1):
                        loc = get_new_coords(loc, ydist, SOUTH)
                        loc = get_new_coords(
                            loc, xdist / 2, WEST if ring % 2 == 1 else EAST)
                        results.append((loc[0], loc[1], 0))

                    for i in range(ring):
                        loc = get_new_coords(
                            loc, xdist, WEST if ring % 2 == 1 else EAST)
                        results.append((loc[0], loc[1], 0))

                    for i in range(ring - 1):
                        loc = get_new_coords(loc, ydist, NORTH)
                        loc = get_new_coords(
                            loc, xdist / 2, WEST if ring % 2 == 1 else EAST)
                        results.append((loc[0], loc[1], 0))

                    loc = get_new_coords(
                        loc, xdist, EAST if ring % 2 == 1 else WEST)
                    results.append((loc[0], loc[1], 0))

                ring -= 1

        # This will pull the last few steps back to the front of the list,
        # so you get a "center nugget" at the beginning of the scan, instead
        # of the entire nothern area before the scan spots 70m to the south.
        if self.step_limit >= 3:
            if self.step_limit == 3:
                results = results[-2:] + results[:-2]
            else:
                results = results[-7:] + results[:-7]

        # Geofence results.
        if self.geofences.is_enabled():
            results = self.geofences.get_geofenced_coordinates(results)
            if not results:
                log.error('No cells regarded as valid for desired scan area. '
                          'Check your provided geofences. Aborting.')
                sys.exit()

        # Add the required appear and disappear times.
        locationsZeroed = []
        for step, location in enumerate(results, 1):
            altitude = get_altitude(self.args, location)
            locationsZeroed.append(
                (step, (location[0], location[1], altitude), 0, 0))
        return locationsZeroed

    # Schedule the work to be done.
    def schedule(self):
        if not self.scan_location:
            log.warning(
                'Cannot schedule work until scan location has been set')
            return

        # Only generate the list of locations if we don't have it already
        # calculated.
        if not self.locations:
            self.locations = self._generate_locations()

        for location in self.locations:
            # FUTURE IMPROVEMENT - For now, queues is assumed to have a single
            # queue.
            self.queues[0].put(location)
            log.debug("Added location {}".format(location))
        self.ready = True


# Spawn Only Hex Search works like Hex Search, but skips locations that
# have no known spawnpoints.
class HexSearchSpawnpoint(HexSearch):

    def _any_spawnpoints_in_range(self, coords, spawnpoints):
        return any(
            distance(coords, x) <= 70
            for x in spawnpoints)

    # Extend the generate_locations function to remove locations with no
    # spawnpoints.
    def _generate_locations(self):
        n, e, s, w = hex_bounds(self.scan_location, self.step_limit)
        spawnpoints = set((d['latitude'], d['longitude'])
                          for d in SpawnPoint.get_spawnpoints(s, w, n, e))

        if len(spawnpoints) == 0:
            log.warning('No spawnpoints found in the specified area!  (Did ' +
                        'you forget to run a normal scan in this area first?)')

        # Call the original _generate_locations.
        locations = super(HexSearchSpawnpoint, self)._generate_locations()

        # Remove items with no spawnpoints in range.
        locations = [
            coords for coords in locations
            if self._any_spawnpoints_in_range(coords[1], spawnpoints)]
        return locations


# Spawn Scan searches known spawnpoints at the specific time they spawn.
class SpawnScan(BaseScheduler):

    def __init__(self, queues, status, args):
        BaseScheduler.__init__(self, queues, status, args)

        # If we are only scanning for pokestops/gyms, the scan radius can be
        # 450m.  Otherwise 70m.
        if self.args.no_pokemon:
            self.step_distance = 0.450
        else:
            self.step_distance = 0.070

        self.step_limit = args.step_limit
        self.locations = False

    # Generate locations is called when the locations list is cleared - the
    # first time it scans or after a location change.
    def _generate_locations(self):
        # Attempt to load spawns from file.
        if self.args.spawnpoint_scanning != 'nofile':
            log.debug('Loading spawn points from json file @ %s',
                      self.args.spawnpoint_scanning)
            try:
                with open(self.args.spawnpoint_scanning) as file:
                    self.locations = json.load(file)
            except ValueError as e:
                log.error('JSON error: %s; will fallback to database', repr(e))
            except IOError as e:
                log.error(
                    'Error opening json file: %s; will fallback to database',
                    repr(e))

        # No locations yet? Try the database!
        if not self.locations:
            log.debug('Loading spawn points from database')
            self.locations = SpawnPoint.get_spawnpoints_in_hex(
                self.scan_location, self.args.step_limit)

        # Geofence spawnpoints.
        if self.geofences.is_enabled():
            self.locations = self.geofences.get_geofenced_coordinates(
                self.locations)
            if not self.locations:
                log.error('No cells regarded as valid for desired scan area. '
                          'Check your provided geofences. Aborting.')
                sys.exit()

        # Well shit...
        # if not self.locations:
        #    raise Exception('No availabe spawn points!')

        # locations[]:
        # {"lat": 37.53079079414139, "lng": -122.28811690874117,
        #  "spawnpoint_id": "808f9f1601d", "time": 511

        log.info('Total of %d spawns to track', len(self.locations))

        # locations.sort(key=itemgetter('time'))

        if self.args.verbose:
            for i in self.locations:
                sec = i['time'] % 60
                minute = (i['time'] / 60) % 60
                m = 'Scan [{:02}:{:02}] ({}) @ {},{}'.format(
                    minute, sec, i['time'], i['lat'], i['lng'])
                log.debug(m)

        # 'time' from json and db alike has been munged to appearance time as
        # seconds after the hour.
        # Here we'll convert that to a real timestamp.
        for location in self.locations:
            # For a scan which should cover all CURRENT pokemon, we can offset
            # the comparison time by 15 minutes so that the "appears" time
            # won't be rolled over to the next hour.

            # TODO: Make it work. The original logic (commented out) was
            #       producing bogus results if your first scan was in the last
            #       15 minute of the hour. Wrapping my head around this isn't
            #       work right now, so I'll just drop the feature for the time
            #       being. It does need to come back so that
            #       repositioning/pausing works more nicely, but we can live
            #       without it too.

            # if sps_scan_current:
            #     cursec = (location['time'] + 900) % 3600
            # else:
            cursec = location['time']

            if cursec > cur_sec():
                # Hasn't spawn in the current hour.
                from_now = location['time'] - cur_sec()
                appears = now() + from_now
            else:
                # Won't spawn till next hour.
                late_by = cur_sec() - location['time']
                appears = now() + 3600 - late_by

            location['appears'] = appears
            location['leaves'] = appears + 900

        # Put the spawn points in order of next appearance time.
        self.locations.sort(key=itemgetter('appears'))

        # Match expected structure:
        # locations = [((lat, lng, alt), ts_appears, ts_leaves),...]
        retset = []
        for step, location in enumerate(self.locations, 1):
            altitude = get_altitude(self.args, [location['lat'],
                                                location['lng']])
            retset.append((step, (location['lat'], location['lng'], altitude),
                           location['appears'], location['leaves']))

        return retset

    # Schedule the work to be done.
    def schedule(self):
        if not self.scan_location:
            log.warning(
                'Cannot schedule work until scan location has been set')
            return

        # SpawnScan needs to calculate the list every time, since the times
        # will change.
        self.locations = self._generate_locations()

        for location in self.locations:
            # FUTURE IMPROVEMENT - For now, queues is assumed to have a single
            # queue.
            self.queues[0].put(location)
            log.debug("Added location {}".format(location))

        # Clear the locations list so it gets regenerated next cycle.
        self.locations = None
        self.ready = True


# SpeedScan is a complete search method that initially does a spawnpoint
# search in each scan location by scanning five two-minute bands within
# an hour and ten minute intervals between bands.

# After finishing the spawnpoint search or if timing isn't right for any of
# the remaining search bands, workers will search the nearest scan location
# that has a new spawn.
class SpeedScan(HexSearch):

    # Call base initialization, set step_distance
    def __init__(self, queues, status, args):
        super(SpeedScan, self).__init__(queues, status, args)
        self.refresh_date = datetime.utcnow() - timedelta(days=1)
        self.next_band_date = self.refresh_date
        self.location_change_date = datetime.utcnow()
        self.queues = [[]]
        self.queue_version = 0
        self.ready = False
        self.empty_hive = False
        self.spawns_found = 0
        self.spawns_missed_delay = {}
        self.scans_done = 0
        self.scans_missed_list = []
        # Minutes between queue refreshes. Should be less than 10 to allow for
        # new bands during Initial scan
        self.minutes = 5
        self.found_percent = []
        self.scan_percent = []
        self.spawn_percent = []
        self.status_message = []
        self.tth_found = 0
        # Initiate special types.
        self._stat_init()
        self._locks_init()

    def _stat_init(self):
        self.spawns_found = 0
        self.spawns_missed_delay = {}
        self.scans_done = 0
        self.scans_missed_list = []

    def _locks_init(self):
        self.lock_next_item = Lock()

    # On location change, empty the current queue and the locations list
    def location_changed(self, scan_location, db_update_queue):
        super(SpeedScan, self).location_changed(scan_location, db_update_queue)
        self.location_change_date = datetime.utcnow()
        self.locations = self._generate_locations()
        scans = {}
        initial = {}
        all_scans = {}
        for sl in ScannedLocation.select_in_hex(self.locations):
            all_scans[cellid((sl['latitude'], sl['longitude']))] = sl

        for i, e in enumerate(self.locations):
            cell = cellid(e[1])
            scans[cell] = {'loc': e[1],  # Lat/long pair
                           'step': e[0]}

            initial[cell] = all_scans[cell] if cell in all_scans.keys(
            ) else ScannedLocation.new_loc(e[1])

        self.scans = scans
        db_update_queue.put((ScannedLocation, initial))
        log.info('%d steps created', len(scans))
        self.band_spacing = int(10 * 60 / len(scans))
        self.band_status()
        spawnpoints = SpawnPoint.select_in_hex_by_location(
            self.scan_location, self.args.step_limit)
        if not spawnpoints:
            log.info('No spawnpoints in hex found in SpawnPoint table. ' +
                     'Doing initial scan.')
        log.info('Found %d spawn points within hex', len(spawnpoints))

        log.info('Doing %s distance calcs to assign spawn points to scans',
                 "{:,}".format(len(spawnpoints) * len(scans)))
        scan_spawn_point = {}
        ScannedLocation.link_spawn_points(scans, initial, spawnpoints,
                                          self.step_distance, scan_spawn_point,
                                          force=True)
        if len(scan_spawn_point):
            log.info('%d relations found between the spawn points and steps',
                     len(scan_spawn_point))
            db_update_queue.put((ScanSpawnPoint, scan_spawn_point))
        else:
            log.info('Spawn points assigned')

    # Generates the list of locations to scan
    # Created a new function, because speed scan requires fixed locations,
    # even when increasing -st. With HexSearch locations, the location of
    # inner rings would change if -st was increased requiring rescanning
    # since it didn't recognize the location in the ScannedLocation table
    def _generate_locations(self):

        # dist between column centers
        xdist = math.sqrt(3) * self.step_distance

        results = []
        loc = self.scan_location
        results.append((loc[0], loc[1], 0))
        # This will loop thorugh all the rings in the hex from the centre
        # moving outwards
        for ring in range(1, self.step_limit):
            for i in range(0, 6):
                # Star_locs will contain the locations of the 6 vertices of
                # the current ring (90,150,210,270,330 and 30 degrees from
                # origin) to form a star
                star_loc = get_new_coords(self.scan_location, xdist * ring,
                                          90 + 60 * i)
                for j in range(0, ring):
                    # Then from each point on the star, create locations
                    # towards the next point of star along the edge of the
                    # current ring
                    loc = get_new_coords(star_loc, xdist * (j), 210 + 60 * i)
                    results.append((loc[0], loc[1], 0))

        # Geofence results.
        if self.geofences.is_enabled():
            results = self.geofences.get_geofenced_coordinates(results)
            if not results:
                log.error('No cells regarded as valid for desired scan area. '
                          'Check your provided geofences. Aborting.')
                sys.exit()

        generated_locations = []
        for step, location in enumerate(results):
            altitude = get_altitude(self.args, location)
            generated_locations.append(
                (step, (location[0], location[1], altitude), 0, 0))
        return generated_locations

    def get_overseer_message(self):
        n = 0
        ms = (datetime.utcnow() - self.refresh_date).total_seconds() + \
            self.refresh_ms
        counter = {
            'TTH': 0,
            'spawn': 0,
            'band': 0,
        }
        for item in self.queues[0]:
            if item.get('done', False):
                continue

            if ms > item['end']:
                continue

            if ms < item['start']:
                break

            n += 1
            counter[item['kind']] += 1

        message = ('Scanning status: {} total waiting, {} initial bands, ' +
                   '{} TTH searches, and {} new spawns').format(
                       n, counter['band'], counter['TTH'], counter['spawn'])
        if self.status_message:
            message += '\n' + self.status_message

        return message

    # Refresh queue every 5 minutes
    # the first band of a scan is done
    def time_to_refresh_queue(self):
        return ((datetime.utcnow() - self.refresh_date).total_seconds() >
                self.minutes * 60 or
                (self.queues == [[]] and not self.empty_hive))

    # Function to empty all queues in the queues list
    def empty_queues(self):
        self.queues = [[]]

    # How long to delay since last action
    def delay(self, last_scan_date):
        return max(
            ((last_scan_date - datetime.utcnow()).total_seconds() +
             self.args.scan_delay),
            2)

    def band_status(self):
        try:
            bands_total = len(self.locations) * 5
            bands_filled = ScannedLocation.get_bands_filled_by_cellids(
                self.scans.keys())
            percent = bands_filled * 100.0 / bands_total
            if bands_total == bands_filled:
                log.info('Initial spawnpoint scan is complete')
            else:
                log.info('Initial spawnpoint scan, %d of %d bands are done ' +
                         'or %.1f%% complete', bands_filled, bands_total,
                         percent)
            return percent

        except Exception as e:
            log.error(
                'Exception in band_status: Exception message: {}'.format(
                    repr(e)))

    # Update the queue, and provide a report on performance of last minutes
    def schedule(self):
        log.info('Refreshing queue')
        self.ready = False
        now_date = datetime.utcnow()
        self.refresh_date = now_date
        self.refresh_ms = now_date.minute * 60 + now_date.second
        self.queue_version += 1
        old_q = deepcopy(self.queues[0])
        queue = []

        # Measure the time it takes to refresh the queue
        start = time.time()

        # prefetch all scanned locations
        scanned_locations = ScannedLocation.get_by_cellids(self.scans.keys())

        # extract all spawnpoints into a dict with spawnpoint
        # id -> spawnpoint for easy access later
        cell_to_linked_spawn_points = (
            ScannedLocation.get_cell_to_linked_spawn_points(
                self.scans.keys(), self.location_change_date))
        sp_by_id = {}
        for sps in cell_to_linked_spawn_points.itervalues():
            for sp in sps:
                sp_by_id[sp['id']] = sp

        for cell, scan in self.scans.iteritems():
            queue += ScannedLocation.get_times(scan, now_date,
                                               scanned_locations)
            queue += SpawnPoint.get_times(cell, scan, now_date,
                                          self.args.spawn_delay,
                                          cell_to_linked_spawn_points,
                                          sp_by_id)
        end = time.time()

        queue.sort(key=itemgetter('start'))
        self.queues[0] = queue
        self.ready = True
        log.info('New queue created with %d entries in %f seconds', len(queue),
                 (end - start))
        # Avoiding refreshing the Queue when the initial scan is complete, and
        # there are no spawnpoints in the hive.
        if len(queue) == 0:
            self.empty_hive = True
        if old_q:
            # Enclosing in try: to avoid divide by zero exceptions from
            # killing overseer
            try:

                # Possible 'done' values are 'Missed', 'Scanned', None, or
                # number
                Not_none_list = filter(lambda e: e.get(
                    'done', None) is not None, old_q)
                Missed_list = filter(lambda e: e.get(
                    'done', None) == 'Missed', Not_none_list)
                Scanned_list = filter(lambda e: e.get(
                    'done', None) == 'Scanned', Not_none_list)
                Timed_list = filter(lambda e: type(
                    e['done']) is not str, Not_none_list)
                spawns_timed_list = filter(
                    lambda e: e['kind'] == 'spawn', Timed_list)
                spawns_timed = len(spawns_timed_list)
                bands_timed = len(
                    filter(lambda e: e['kind'] == 'band', Timed_list))
                spawns_all = spawns_timed + \
                    len(filter(lambda e: e['kind'] == 'spawn', Scanned_list))
                spawns_missed = len(
                    filter(lambda e: e['kind'] == 'spawn', Missed_list))
                band_percent = self.band_status()
                kinds = {}
                tth_ranges = {}
                self.tth_found = 0
                self.active_sp = 0
                found_percent = 100.0
                spawns_reached = 100.0
                spawnpoints = SpawnPoint.select_in_hex_by_cellids(
                    self.scans.keys(), self.location_change_date)
                for sp in spawnpoints:
                    if sp['missed_count'] > 5:
                        continue
                    self.active_sp += 1
                    self.tth_found += (sp['earliest_unseen'] ==
                                       sp['latest_seen'])
                    kind = sp['kind']
                    kinds[kind] = kinds.get(kind, 0) + 1
                    tth_range = str(int(round(
                        ((sp['earliest_unseen'] - sp['latest_seen']) % 3600) /
                        60.0)))
                    tth_ranges[tth_range] = tth_ranges.get(tth_range, 0) + 1

                tth_ranges['0'] = tth_ranges.get('0', 0) - self.tth_found
                len_spawnpoints = len(spawnpoints) + (not len(spawnpoints))
                log.info('Total Spawn Points found in hex: %d',
                         len(spawnpoints))
                log.info('Inactive Spawn Points found in hex: %d or %.1f%%',
                         len(spawnpoints) - self.active_sp,
                         (len(spawnpoints) -
                          self.active_sp) * 100.0 / len_spawnpoints)
                log.info('Active Spawn Points found in hex: %d or %.1f%%',
                         self.active_sp,
                         self.active_sp * 100.0 / len_spawnpoints)
                self.active_sp += self.active_sp == 0
                for k in sorted(kinds.keys()):
                    log.info('%s kind spawns: %d or %.1f%%', k,
                             kinds[k], kinds[k] * 100.0 / self.active_sp)
                log.info('Spawns with found TTH: %d or %.1f%% [%d missing]',
                         self.tth_found,
                         self.tth_found * 100.0 / self.active_sp,
                         self.active_sp - self.tth_found)
                for k in sorted(tth_ranges.keys(), key=int):
                    log.info('Spawnpoints with a %sm range to find TTH: %d', k,
                             tth_ranges[k])
                log.info('Over last %d minutes: %d new bands, %d Pokemon ' +
                         'found', self.minutes, bands_timed, spawns_all)
                log.info('Of the %d total spawns, %d were targeted, and %d ' +
                         'found scanning for others', spawns_all, spawns_timed,
                         spawns_all - spawns_timed)
                scan_total = spawns_timed + bands_timed
                spm = scan_total / self.minutes
                seconds_per_scan = self.minutes * 60 * \
                    self.args.workers / scan_total if scan_total else 0
                log.info('%d scans over %d minutes, %d scans per minute, %d ' +
                         'secs per scan per worker', scan_total, self.minutes,
                         spm, seconds_per_scan)

                sum = spawns_all + spawns_missed
                if sum:
                    spawns_reached = spawns_all * 100.0 / \
                        (spawns_all + spawns_missed)
                    log.info('%d Pokemon found, and %d were not reached in ' +
                             'time for %.1f%% found', spawns_all,
                             spawns_missed, spawns_reached)

                if spawns_timed:
                    average = reduce(
                        lambda x, y: x + y['done'],
                        spawns_timed_list,
                        0) / spawns_timed
                    log.info('%d Pokemon found, %d were targeted, with an ' +
                             'average delay of %d sec', spawns_all,
                             spawns_timed, average)

                    spawns_missed = reduce(
                        lambda x, y: x + len(y),
                        self.spawns_missed_delay.values(), 0)
                    sum = spawns_missed + self.spawns_found
                    found_percent = (
                        self.spawns_found * 100.0 / sum if sum else 0)
                    log.info('%d spawns scanned and %d spawns were not ' +
                             'there when expected for %.1f%%',
                             self.spawns_found, spawns_missed, found_percent)
                    self.spawn_percent.append(round(found_percent, 1))
                    if self.spawns_missed_delay:
                        log.warning('Missed spawn IDs with times after spawn:')
                        log.warning(self.spawns_missed_delay)
                    log.info('History: %s', str(
                        self.spawn_percent).strip('[]'))

                sum = self.scans_done + len(self.scans_missed_list)
                good_percent = self.scans_done * 100.0 / sum if sum else 0
                log.info(
                    '%d scans successful and %d scans missed for %.1f%% found',
                    self.scans_done, len(self.scans_missed_list), good_percent)
                self.scan_percent.append(round(good_percent, 1))
                if self.scans_missed_list:
                    log.warning('Missed scans: %s', Counter(
                        self.scans_missed_list).most_common(3))
                    log.info('History: %s', str(self.scan_percent).strip('[]'))
                self.status_message = ('Initial scan: {:.2f}%, TTH found: ' +
                                       '{:.2f}% [{} missing], ').format(
                    band_percent, self.tth_found * 100.0 / self.active_sp,
                    self.active_sp - self.tth_found)
                self.status_message += ('Spawns reached: {:.2f}%, Spawns ' +
                                        'found: {:.2f}%, Good scans ' +
                                        '{:.2f}%').format(spawns_reached,
                                                          found_percent,
                                                          good_percent)
                self._stat_init()

            except Exception as e:
                log.error(
                    'Performance statistics had an Exception: {}'.format(
                        repr(e)))
                traceback.print_exc(file=sys.stdout)

    # Find the best item to scan next
    def next_item(self, status):
        # Thread safety: don't let multiple threads get the same "best item".
        with self.lock_next_item:
            # Score each item in the queue by # of due spawns or scan time
            # bands can be filled.

            while not self.ready:
                time.sleep(1)

            now_date = datetime.utcnow()
            q = self.queues[0]
            ms = ((now_date - self.refresh_date).total_seconds() +
                  self.refresh_ms)
            best = {}
            worker_loc = [status['latitude'], status['longitude']]
            last_action = status['last_scan_date']

            # Logging.
            log.debug('Enumerating %s scan locations in queue.',
                      len(q))

            # Keep some stats for logging purposes. If something goes wrong,
            # we can track what happened.
            count_claimed = 0
            count_parked = 0
            count_missed = 0
            count_fresh_band = 0
            count_early = 0
            count_late = 0
            min_parked_time_remaining = 0
            min_fresh_band_time_remaining = 0

            # Check all scan locations possible in the queue.
            for i, item in enumerate(q):
                # If already claimed by another worker or done, pass.
                if item.get('done', False):
                    count_claimed += 1
                    continue

                # If the item is parked by a different thread (or by a
                # different account, which should be on that one thread),
                # pass.
                our_parked_name = status['username']
                if 'parked_name' in item:
                    # We use 'parked_last_update' to determine when the
                    # last time was since the thread passed the item with the
                    # same thread name & username. If it's been too long, unset
                    # the park so another worker can pick it up.
                    now = default_timer()
                    max_parking_idle_seconds = 3 * 60
                    time_passed = now - item.get('parked_last_update', now)
                    time_remaining = (max_parking_idle_seconds - time_passed)

                    # Update logging stats.
                    if not min_parked_time_remaining:
                        min_parked_time_remaining = time_remaining
                    elif time_remaining < min_parked_time_remaining:
                        min_parked_time_remaining = time_remaining

                    # Check parked status.
                    if (time_passed > max_parking_idle_seconds):
                        # Unpark & don't skip it.
                        item.pop('parked_name', None)
                        item.pop('parked_last_update', None)
                    else:
                        # Still parked and not our item. Skip it.
                        if item.get('parked_name') != our_parked_name:
                            count_parked += 1
                            continue

                # If already timed out, mark it as Missed and check next.
                if ms > item['end']:
                    count_missed += 1
                    item['done'] = 'Missed' if not item.get(
                        'done', False) else item['done']
                    continue

                # If we just did a fresh band recently, wait a few seconds to
                # space out the band scans.
                if now_date < self.next_band_date:
                    count_fresh_band += 1

                    # Update logging stats.
                    band_time_remaining = (self.next_band_date - now_date)
                    if not min_fresh_band_time_remaining:
                        min_fresh_band_time_remaining = band_time_remaining
                    elif band_time_remaining < min_fresh_band_time_remaining:
                        min_fresh_band_time_remaining = band_time_remaining

                    continue

                # If we are going to get there before it starts then ignore.
                loc = item['loc']
                meters = distance(loc, worker_loc)
                secs_to_arrival = meters / self.args.kph * 3.6
                secs_waited = (now_date - last_action).total_seconds()
                secs_to_arrival = max(secs_to_arrival - secs_waited, 0)
                if ms + secs_to_arrival < item['start']:
                    count_early += 1
                    continue

                # If we can't make it there before it disappears, don't bother
                # trying.
                if ms + secs_to_arrival > item['end']:
                    count_late += 1
                    continue

                # Bands are top priority to find new spawns first
                score = 1e12 if item['kind'] == 'band' else (
                    1e6 if item['kind'] == 'TTH' else 1)

                # For spawns, score is purely based on how close they are to
                # last worker position
                score = score / (meters + 10)

                if score > best.get('score', 0):
                    best = {'score': score, 'i': i,
                            'secs_to_arrival': secs_to_arrival}
                    best.update(item)

            # If we didn't find one, log it.
            if not best:
                log.debug('Enumerating queue found no best location, with'
                          + ' %s claimed, %s parked, %s missed, %s fresh band'
                          + " skips, %s missed because we're early, %s because"
                          + " we're too late. Minimum %s time remaining on"
                          + ' parked item, and %s time remaining for next'
                          + ' fresh band.',
                          count_claimed,
                          count_parked,
                          count_missed,
                          count_fresh_band,
                          count_early,
                          count_late,
                          min_parked_time_remaining,
                          min_fresh_band_time_remaining)
            else:
                log.debug('Enumerating queue found best location: %s.',
                          repr(best))

            loc = best.get('loc', [])
            step = best.get('step', 0)
            secs_to_arrival = best.get('secs_to_arrival', 0)
            i = best.get('i', 0)
            st = best.get('start', 0)
            end = best.get('end', 0)

            log.debug('step {} start {} end {} secs to arrival {}'.format(
                step, st, end, secs_to_arrival))

            messages = {
                'wait': 'Nothing to scan.',
                'early': 'Early for step {}; waiting a few seconds...'.format(
                    step),
                'late': ('API response on step {} delayed by {} seconds. ' +
                         'Possible causes: slow proxies, internet, or ' +
                         'Niantic servers.').format(
                             step,
                             int((now_date - last_action).total_seconds())),
                'search': 'Searching at step {}.'.format(step),
                'invalid': ('Invalid response at step {}, abandoning ' +
                            'location.').format(step)
            }
            try:
                item = q[i]
            except IndexError:
                messages['wait'] = ('Search aborting.'
                                    + ' Overseer refreshing queue.')
                return -1, 0, 0, 0, messages, 0

            if best.get('score', 0) == 0:
                if count_late > 0:
                    messages['wait'] = ('Not able to reach any scan'
                                        + ' under the speed limit.')
                return -1, 0, 0, 0, messages, 0

            meters = distance(loc, worker_loc)
            if (meters > (now_date - last_action).total_seconds() *
                    self.args.kph / 3.6):
                # Flag item as "parked" by a specific thread, because
                # we're waiting for it. This will avoid all threads "walking"
                # to the same item.
                our_parked_name = status['username']
                item['parked_name'] = our_parked_name

                # CTRL+F 'parked_last_update' in this file for more info.
                item['parked_last_update'] = default_timer()

                messages['wait'] = 'Moving {}m to step {} for a {}.'.format(
                    int(meters), step, best['kind'])
                # So we wait while the worker arrives at the destination
                # But we don't want to sleep too long or the item might get
                # taken by another worker
                if secs_to_arrival > 179 - self.args.scan_delay:
                    secs_to_arrival = 179 - self.args.scan_delay
                return -1, 0, 0, 0, messages, max(secs_to_arrival, 0)

            # Check again if another worker heading there.
            # TODO: Check if this is still necessary. I believe this was
            # originally a failed attempt at thread safety, which still
            # resulted in a race condition (multiple workers heading to the
            # same spot). A thread Lock has since been added.
            if item.get('done', False):
                messages['wait'] = ('Skipping step {}. Other worker already ' +
                                    'scanned.').format(step)
                return -1, 0, 0, 0, messages, 0

            if not self.ready:
                messages['wait'] = ('Search aborting.'
                                    + ' Overseer refreshing queue.')
                return -1, 0, 0, 0, messages, 0

            # If a new band, set the date to wait until for the next band.
            if best['kind'] == 'band' and best['end'] - best['start'] > 5 * 60:
                self.next_band_date = datetime.utcnow() + timedelta(
                    seconds=self.band_spacing)

            # Mark scanned
            item['done'] = 'Scanned'
            status['index_of_queue_item'] = i
            status['queue_version'] = self.queue_version

            messages['search'] = 'Scanning step {} for a {}.'.format(
                best['step'], best['kind'])
            return best['step'], best['loc'], 0, 0, messages, 0

    def task_done(self, status, parsed=False):
        if parsed:
            # Record delay between spawn time and scanning for statistics
            # This now holds the actual time of scan in seconds
            scan_secs = parsed['scan_secs']

            # It seems that the best solution is not to interfere with the
            # item if the queue has been refreshed since scanning
            if status['queue_version'] != self.queue_version:
                log.info('Step item has changed since queue refresh')
                return
            item = self.queues[0][status['index_of_queue_item']]
            start_secs = item['start']
            if item['kind'] == 'spawn':
                start_secs -= self.args.spawn_delay
            start_delay = (scan_secs - start_secs) % 3600
            safety_buffer = item['end'] - scan_secs
            if safety_buffer < 0:
                log.warning('Too late by %d sec for a %s at step %d', -
                            safety_buffer, item['kind'], item['step'])

            # If we had a 0/0/0 scan, then unmark as done so we can retry, and
            # save for Statistics
            elif parsed['bad_scan']:
                self.scans_missed_list.append(cellid(item['loc']))
                # Only try for a set amount of times (BAD_SCAN_RETRY)
                if self.args.bad_scan_retry > 0 and (
                        self.scans_missed_list.count(cellid(item['loc'])) >
                        self.args.bad_scan_retry):
                    log.info('Step %d failed scan for %d times! Giving up...',
                             item['step'], self.args.bad_scan_retry + 1)
                else:
                    item['done'] = None
                    log.info('Putting back step %d in queue', item['step'])
            else:
                # Scan returned data
                self.scans_done += 1
                item['done'] = start_delay

                # Were we looking for spawn?
                if item['kind'] == 'spawn':

                    sp_id = item['sp']
                    # Did we find the spawn?
                    if sp_id in parsed['sp_id_list']:
                        self.spawns_found += 1
                    elif start_delay > 0:
                        # Not sure why this could be negative,
                        # but sometimes it is.

                        # If not, record ID and put back in queue.
                        self.spawns_missed_delay[
                            sp_id] = self.spawns_missed_delay.get(sp_id, [])
                        self.spawns_missed_delay[sp_id].append(start_delay)
                        item['done'] = 'Scanned'

                # For existing spawn points, if in any other queue items, mark
                # 'scanned'
                for sp_id in parsed['sp_id_list']:
                    for item in self.queues[0]:
                        if (sp_id == item.get('sp', None) and
                                item.get('done', None) is None and
                                scan_secs > item['start'] and
                                scan_secs < item['end']):
                            item['done'] = 'Scanned'


# The SchedulerFactory returns an instance of the correct type of scheduler.
class SchedulerFactory():
    __schedule_classes = {
        "hexsearch": HexSearch,
        "hexsearchspawnpoint": HexSearchSpawnpoint,
        "spawnscan": SpawnScan,
        "speedscan": SpeedScan,
    }

    @staticmethod
    def get_scheduler(name, *args, **kwargs):
        scheduler_class = SchedulerFactory.__schedule_classes.get(
            name.lower(), None)

        if scheduler_class:
            return scheduler_class(*args, **kwargs)

        raise NotImplementedError(
            "The requested scheduler has not been implemented")


# The KeyScheduler returns a scheduler that cycles through the given hash
# server keys.
class KeyScheduler(object):

    def __init__(self, keys, db_updates_queue):
        self.keys = {}
        for key in keys:
            self.keys[key] = {
                'remaining': 0,
                'maximum': 0,
                'peak': 0,
                'expires': None
            }

        self.key_cycle = itertools.cycle(keys)
        self.curr_key = ''

        hashkeys = self.keys
        for key in hashkeys:
            hashkeys[key]['key'] = key
        db_updates_queue.put((HashKeys, hashkeys))

    def keys(self):
        return self.keys

    def current(self):
        return self.curr_key

    def next(self):
        self.curr_key = self.key_cycle.next()
        return self.curr_key
