#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Search Architecture:
 - Have a list of accounts
 - Create an "overseer" thread
 - Search Overseer:
   - Tracks incoming new location values
   - Tracks "paused state"
   - During pause or new location will clears current search queue
   - Starts search_worker threads
 - Search Worker Threads each:
   - Have a unique API login
   - Listens to the same Queue for areas to scan
   - Can re-login as needed
   - Shares a global lock for map parsing
'''

import logging
import math
import json
import os
import random
import time
import geopy.distance as geopy_distance

from operator import itemgetter
from threading import Thread, Lock
from queue import Queue, Empty

from pgoapi import PGoApi
from pgoapi.utilities import f2i
from pgoapi import utilities as util
from pgoapi.exceptions import AuthException

from .models import parse_map, Pokemon

log = logging.getLogger(__name__)

TIMESTAMP = '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000'


def get_new_coords(init_loc, distance, bearing):
    """ Given an initial lat/lng, a distance(in kms), and a bearing (degrees),
    this will calculate the resulting lat/lng coordinates.
    """
    R = 6378.1  # km radius of the earth
    bearing = math.radians(bearing)

    init_coords = [math.radians(init_loc[0]), math.radians(init_loc[1])]  # convert lat/lng to radians

    new_lat = math.asin(math.sin(init_coords[0]) * math.cos(distance / R) +
                        math.cos(init_coords[0]) * math.sin(distance / R) * math.cos(bearing)
                        )

    new_lon = init_coords[1] + math.atan2(math.sin(bearing) * math.sin(distance / R) * math.cos(init_coords[0]),
                                          math.cos(distance / R) - math.sin(init_coords[0]) * math.sin(new_lat)
                                          )

    return [math.degrees(new_lat), math.degrees(new_lon)]


def generate_location_steps(initial_loc, step_count):
    # Bearing (degrees)
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270

    pulse_radius = 0.07                 # km - radius of players heartbeat is 70m
    xdist = math.sqrt(3) * pulse_radius   # dist between column centers
    ydist = 3 * (pulse_radius / 2)          # dist between row centers

    yield (initial_loc[0], initial_loc[1], 0)  # insert initial location

    ring = 1
    loc = initial_loc
    while ring < step_count:
        # Set loc to start at top left
        loc = get_new_coords(loc, ydist, NORTH)
        loc = get_new_coords(loc, xdist / 2, WEST)
        for direction in range(6):
            for i in range(ring):
                if direction == 0:  # RIGHT
                    loc = get_new_coords(loc, xdist, EAST)
                if direction == 1:  # DOWN + RIGHT
                    loc = get_new_coords(loc, ydist, SOUTH)
                    loc = get_new_coords(loc, xdist / 2, EAST)
                if direction == 2:  # DOWN + LEFT
                    loc = get_new_coords(loc, ydist, SOUTH)
                    loc = get_new_coords(loc, xdist / 2, WEST)
                if direction == 3:  # LEFT
                    loc = get_new_coords(loc, xdist, WEST)
                if direction == 4:  # UP + LEFT
                    loc = get_new_coords(loc, ydist, NORTH)
                    loc = get_new_coords(loc, xdist / 2, WEST)
                if direction == 5:  # UP + RIGHT
                    loc = get_new_coords(loc, ydist, NORTH)
                    loc = get_new_coords(loc, xdist / 2, EAST)
                yield (loc[0], loc[1], 0)
        ring += 1


#
# A fake search loop which does....nothing!
#
def fake_search_loop():
    while True:
        log.info('Fake search loop running')
        time.sleep(10)


# gets the current time past the hour
def curSec():
    return (60 * time.gmtime().tm_min) + time.gmtime().tm_sec


# gets the diference between two times past the hour (in a range from -1800 to 1800)
def timeDif(a, b):
    dif = a - b
    if (dif < -1800):
        dif += 3600
    if (dif > 1800):
        dif -= 3600
    return dif


# binary search to get the lowest index of the item in Slist that has atleast time T
def SbSearch(Slist, T):
    first = 0
    last = len(Slist) - 1
    while first < last:
        mp = (first + last) // 2
        if Slist[mp]['time'] < T:
            first = mp + 1
        else:
            last = mp
    return first


# The main search loop that keeps an eye on the over all process
def search_overseer_thread(args, new_location_queue, pause_bit, encryption_lib_path):

    log.info('Search overseer starting')

    search_items_queue = Queue()
    parse_lock = Lock()

    # Create a search_worker_thread per account
    log.info('Starting search worker threads')
    for i, account in enumerate(args.accounts):
        log.debug('Starting search worker thread %d for user %s', i, account['username'])
        t = Thread(target=search_worker_thread,
                   name='search_worker_{}'.format(i),
                   args=(args, account, search_items_queue, parse_lock,
                         encryption_lib_path))
        t.daemon = True
        t.start()

    # A place to track the current location
    current_location = False
    locations = []
    spawnpoints = set()

    # The real work starts here but will halt on pause_bit.set()
    while True:

        # paused; clear queue if needed, otherwise sleep and loop
        if pause_bit.is_set():
            if not search_items_queue.empty():
                try:
                    while True:
                        search_items_queue.get_nowait()
                except Empty:
                    pass
            time.sleep(1)
            continue

        # If a new location has been passed to us, get the most recent one
        if not new_location_queue.empty():
            log.info('New location caught, moving search grid')
            try:
                while True:
                    current_location = new_location_queue.get_nowait()
            except Empty:
                pass

            # We (may) need to clear the search_items_queue
            if not search_items_queue.empty():
                try:
                    while True:
                        search_items_queue.get_nowait()
                except Empty:
                    pass

            # update our list of coords
            locations = list(generate_location_steps(current_location, args.step_limit))

            # repopulate our spawn points
            if args.spawnpoints_only:
                # We need to get all spawnpoints in range. This is a square 70m * step_limit * 2
                sp_dist = 0.07 * 2 * args.step_limit
                log.debug('Spawnpoint search radius: %f', sp_dist)
                # generate coords of the midpoints of each edge of the square
                south, west = get_new_coords(current_location, sp_dist, 180), get_new_coords(current_location, sp_dist, 270)
                north, east = get_new_coords(current_location, sp_dist, 0), get_new_coords(current_location, sp_dist, 90)
                # Use the midpoints to arrive at the corners
                log.debug('Searching for spawnpoints between %f, %f and %f, %f', south[0], west[1], north[0], east[1])
                spawnpoints = set((d['latitude'], d['longitude']) for d in Pokemon.get_spawnpoints(south[0], west[1], north[0], east[1]))
                if len(spawnpoints) == 0:
                    log.warning('No spawnpoints found in the specified area! (Did you forget to run a normal scan in this area first?)')

                def any_spawnpoints_in_range(coords):
                    return any(geopy_distance.distance(coords, x).meters <= 70 for x in spawnpoints)

                locations = [coords for coords in locations if any_spawnpoints_in_range(coords)]

            if len(locations) == 0:
                log.warning('Nothing to scan!')

        # If there are no search_items_queue either the loop has finished (or been
        # cleared above) -- either way, time to fill it back up
        if search_items_queue.empty():
            log.debug('Search queue empty, restarting loop')
            for step, step_location in enumerate(locations, 1):
                log.debug('Queueing step %d @ %f/%f/%f', step, step_location[0], step_location[1], step_location[2])
                search_args = (step, step_location)
                search_items_queue.put(search_args)
        # else:
        #     log.info('Search queue processing, %d items left', search_items_queue.qsize())

        # Now we just give a little pause here
        time.sleep(1)


def search_overseer_thread_ss(args, new_location_queue, pause_bit, encryption_lib_path):
    log.info('Search ss overseer starting')
    search_items_queue = Queue()
    parse_lock = Lock()
    spawns = []

    # Create a search_worker_thread per account
    log.info('Starting search worker threads')
    for i, account in enumerate(args.accounts):
        log.debug('Starting search worker thread %d for user %s', i, account['username'])
        t = Thread(target=search_worker_thread_ss,
                   name='ss_search_worker_{}'.format(i),
                   args=(args, account, search_items_queue, parse_lock, encryption_lib_path))
        t.daemon = True
        t.start()

    if os.path.isfile(args.spawnpoint_scanning):  # if the spawns file exists use it
        try:
            with open(args.spawnpoint_scanning) as file:
                try:
                    spawns = json.load(file)
                except ValueError:
                    log.error(args.spawnpoint_scanning + " is not valid")
                    return
                file.close()
        except IOError:
            log.error("Error opening " + args.spawnpoint_scanning)
            return
    else:  # if spawns file dose not exist use the db
        loc = new_location_queue.get()
        spawns = Pokemon.get_spawnpoints_in_hex(loc, args.step_limit)
    spawns.sort(key=itemgetter('time'))
    log.info('Total of %d spawns to track', len(spawns))
    # find the inital location (spawn thats 60sec old)
    pos = SbSearch(spawns, (curSec() + 3540) % 3600)
    while True:
        while timeDif(curSec(), spawns[pos]['time']) < 60:
            time.sleep(1)
        # make location with a dummy height (seems to be more reliable than 0 height)
        location = [spawns[pos]['lat'], spawns[pos]['lng'], 40.32]
        search_args = (pos, location, spawns[pos]['time'])
        search_items_queue.put(search_args)
        pos = (pos + 1) % len(spawns)


def search_worker_thread(args, account, search_items_queue, parse_lock, encryption_lib_path):

    stagger_thread(args, account)

    log.debug('Search worker thread starting')

    # The forever loop for the thread
    while True:
        try:
            log.debug('Entering search loop')

            # Create the API instance this will use
            api = PGoApi()
            if args.proxy:
                api.set_proxy({'http': args.proxy, 'https': args.proxy})

            # Get current time
            loop_start_time = int(round(time.time() * 1000))

            # The forever loop for the searches
            while True:

                # Grab the next thing to search (when available)
                step, step_location = search_items_queue.get()

                log.info('Search step %d beginning (queue size is %d)', step, search_items_queue.qsize())

                # Let the api know where we intend to be for this loop
                api.set_position(*step_location)

                # The loop to try very hard to scan this step
                failed_total = 0
                while True:

                    # After so many attempts, let's get out of here
                    if failed_total >= args.scan_retries:
                        # I am choosing to NOT place this item back in the queue
                        # otherwise we could get a "bad scan" area and be stuck
                        # on this overall loop forever. Better to lose one cell
                        # than have the scanner, essentially, halt.
                        log.error('Search step %d went over max scan_retires; abandoning', step)
                        break

                    # Increase sleep delay between each failed scan
                    # By default scan_dela=5, scan_retries=5 so
                    # We'd see timeouts of 5, 10, 15, 20, 25
                    sleep_time = args.scan_delay * (1 + failed_total)

                    # Ok, let's get started -- check our login status
                    check_login(args, account, api, step_location)

                    api.activate_signature(encryption_lib_path)

                    # Make the actual request (finally!)
                    response_dict = map_request(api, step_location)

                    # G'damnit, nothing back. Mark it up, sleep, carry on
                    if not response_dict:
                        log.error('Search step %d area download failed, retrying request in %g seconds', step, sleep_time)
                        failed_total += 1
                        time.sleep(sleep_time)
                        continue

                    # Got the response, lock for parsing and do so (or fail, whatever)
                    with parse_lock:
                        try:
                            parse_map(response_dict, step_location)
                            log.debug('Search step %s completed', step)
                            search_items_queue.task_done()
                            break  # All done, get out of the request-retry loop
                        except KeyError:
                            log.exception('Search step %s map parsing failed, retrying request in %g seconds. Username: %s', step, sleep_time, account['username'])
                            failed_total += 1
                    time.sleep(sleep_time)

                # If there's any time left between the start time and the time when we should be kicking off the next
                # loop, hang out until its up.
                sleep_delay_remaining = loop_start_time + (args.scan_delay * 1000) - int(round(time.time() * 1000))
                if sleep_delay_remaining > 0:
                    time.sleep(sleep_delay_remaining / 1000)

                loop_start_time += args.scan_delay * 1000

        # catch any process exceptions, log them, and continue the thread
        except Exception as e:
            log.exception('Exception in search_worker: %s. Username: %s', e, account['username'])


def search_worker_thread_ss(args, account, search_items_queue, parse_lock, encryption_lib_path):
    stagger_thread(args, account)
    log.debug('Search worker ss thread starting')
    # forever loop (for catching when the other forever loop fails)
    while True:
        try:
            log.debug('Entering search loop')
            # create api instance
            api = PGoApi()
            if args.proxy:
                api.set_proxy({'http': args.proxy, 'https': args.proxy})
            api.activate_signature(encryption_lib_path)
            # search forever loop
            while True:
                # Grab the next thing to search (when available)
                step, step_location, spawntime = search_items_queue.get()
                log.info('Searching step %d, remaining %d', step, search_items_queue.qsize())
                if timeDif(curSec(), spawntime) < 840:  # if we arnt 14mins too late
                    # set position
                    api.set_position(*step_location)
                    # try scan (with retries)
                    failed_total = 0
                    while True:
                        if failed_total >= args.scan_retries:
                            log.error('Search step %d went over max scan_retires; abandoning', step)
                            break
                        sleep_time = args.scan_delay * (1 + failed_total)
                        check_login(args, account, api, step_location)
                        # make the map request
                        response_dict = map_request(api, step_location)
                        # check if got anything back
                        if not response_dict:
                            log.error('Search step %d area download failed, retyring request in %g seconds', step, sleep_time)
                            failed_total += 1
                            time.sleep(sleep_time)
                            continue
                        # got responce try and parse it
                        with parse_lock:
                            try:
                                parse_map(response_dict, step_location)
                                log.debug('Search step %s completed', step)
                                search_items_queue.task_done()
                                break
                            except KeyError:
                                log.exception('Search step %s map parsing failed, retrying request in %g seconds. Username: %s', step, sleep_time, account['username'])
                                failed_total += 1
                        time.sleep(sleep_time)
                    time.sleep(sleep_time)
                else:
                    search_items_queue.task_done()
                    log.info('Cant keep up. Skipping')
        except Exception as e:
            log.exception('Exception in search_worker: %s', e)


def check_login(args, account, api, position):

    # Logged in? Enough time left? Cool!
    if api._auth_provider and api._auth_provider._ticket_expire:
        remaining_time = api._auth_provider._ticket_expire / 1000 - time.time()
        if remaining_time > 60:
            log.debug('Credentials remain valid for another %f seconds', remaining_time)
            return

    # Try to login (a few times, but don't get stuck here)
    i = 0
    api.set_position(position[0], position[1], position[2])
    while i < args.login_retries:
        try:
            if args.proxy:
                api.set_authentication(provider=account['auth_service'], username=account['username'], password=account['password'], proxy_config={'http': args.proxy, 'https': args.proxy})
            else:
                api.set_authentication(provider=account['auth_service'], username=account['username'], password=account['password'])
            break
        except AuthException:
            if i >= args.login_retries:
                raise TooManyLoginAttempts('Exceeded login attempts')
            else:
                i += 1
                log.error('Failed to login to Pokemon Go with account %s. Trying again in %g seconds', account['username'], args.login_delay)
                time.sleep(args.login_delay)

    log.debug('Login for account %s successful', account['username'])


def map_request(api, position):
    try:
        cell_ids = util.get_cell_ids(position[0], position[1])
        timestamps = [0, ] * len(cell_ids)
        return api.get_map_objects(latitude=f2i(position[0]),
                                   longitude=f2i(position[1]),
                                   since_timestamp_ms=timestamps,
                                   cell_id=cell_ids)
    except Exception as e:
        log.warning('Exception while downloading map: %s', e)
        return False


def stagger_thread(args, account):
    # If we have more than one account, stagger the logins such that they occur evenly over scan_delay
    if len(args.accounts) > 1:
        if len(args.accounts) > args.scan_delay:  # force ~1 second delay between threads if you have many accounts
            delay = args.accounts.index(account) + ((random.random() - .5) / 2) if args.accounts.index(account) > 0 else 0
        else:
            delay = (args.scan_delay / len(args.accounts)) * args.accounts.index(account)
            log.debug('Delaying thread startup for %.2f seconds', delay)
        time.sleep(delay)


class TooManyLoginAttempts(Exception):
    pass
