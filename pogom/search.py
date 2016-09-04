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
   - Pushes finds to db queue and webhook queue
'''

import logging
import math
import json
import os
import random
import time
import geopy
import geopy.distance

from datetime import datetime
from operator import itemgetter
from threading import Thread
from queue import Queue, Empty

from pgoapi import PGoApi
from pgoapi.utilities import f2i
from pgoapi import utilities as util
from pgoapi.exceptions import AuthException

from .models import parse_map, Pokemon, hex_bounds, GymDetails, parse_gyms, MainWorker, WorkerStatus
from .transform import generate_location_steps
from .fakePogoApi import FakePogoApi
from .utils import now

import terminalsize

log = logging.getLogger(__name__)

TIMESTAMP = '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000'


# Apply a location jitter
def jitterLocation(location=None, maxMeters=10):
    origin = geopy.Point(location[0], location[1])
    b = random.randint(0, 360)
    d = math.sqrt(random.random()) * (float(maxMeters) / 1000)
    destination = geopy.distance.distance(kilometers=d).destination(origin, b)
    return (destination.latitude, destination.longitude, location[2])


# gets the current time past the hour
def cur_sec():
    return (60 * time.gmtime().tm_min) + time.gmtime().tm_sec


# Thread to handle user input
def switch_status_printer(display_type, current_page):
    # Get a reference to the root logger
    mainlog = logging.getLogger()
    # Disable logging of the first handler - the stream handler, and disable it's output
    mainlog.handlers[0].setLevel(logging.CRITICAL)

    while True:
        # Wait for the user to press a key
        command = raw_input()

        if command == '':
            # Switch between logging and display.
            if display_type[0] != 'logs':
                # Disable display, enable on screen logging
                mainlog.handlers[0].setLevel(logging.DEBUG)
                display_type[0] = 'logs'
                # If logs are going slowly, sometimes it's hard to tell you switched.  Make it clear.
                print 'Showing logs...'
            elif display_type[0] == 'logs':
                # Enable display, disable on screen logging (except for critical messages)
                mainlog.handlers[0].setLevel(logging.CRITICAL)
                display_type[0] = 'workers'
        elif command.isdigit():
                current_page[0] = int(command)
                mainlog.handlers[0].setLevel(logging.CRITICAL)
                display_type[0] = 'workers'
        elif command.lower() == 'f':
                mainlog.handlers[0].setLevel(logging.CRITICAL)
                display_type[0] = 'failedaccounts'


# Thread to print out the status of each worker
def status_printer(threadStatus, search_items_queue, db_updates_queue, wh_queue, account_queue, account_failures):
    display_type = ["workers"]
    current_page = [1]

    # Start another thread to get user input
    t = Thread(target=switch_status_printer,
               name='switch_status_printer',
               args=(display_type, current_page))
    t.daemon = True
    t.start()

    while True:
        time.sleep(1)

        if display_type[0] == 'logs':
            # In log display mode, we don't want to show anything
            continue

        # Create a list to hold all the status lines, so they can be printed all at once to reduce flicker
        status_text = []

        if display_type[0] == 'workers':

            # Get the terminal size
            width, height = terminalsize.get_terminal_size()
            # Queue and overseer take 2 lines.  Switch message takes up 2 lines.  Remove an extra 2 for things like screen status lines.
            usable_height = height - 6
            # Prevent people running terminals only 6 lines high from getting a divide by zero
            if usable_height < 1:
                usable_height = 1

            # Calculate total skipped items
            skip_total = 0
            for item in threadStatus:
                if 'skip' in threadStatus[item]:
                    skip_total += threadStatus[item]['skip']

            # Print the queue length
            status_text.append('Queues: {} search items, {} db updates, {} webhook.  Total skipped items: {}. Spare accounts available: {}. Accounts on hold: {}'.format(search_items_queue.qsize(), db_updates_queue.qsize(), wh_queue.qsize(), skip_total, account_queue.qsize(), len(account_failures)))

            # Print status of overseer
            status_text.append('{} Overseer: {}'.format(threadStatus['Overseer']['method'], threadStatus['Overseer']['message']))

            # Calculate the total number of pages.  Subtracting 1 for the overseer.
            total_pages = math.ceil((len(threadStatus) - 1) / float(usable_height))

            # Prevent moving outside the valid range of pages
            if current_page[0] > total_pages:
                current_page[0] = total_pages
            if current_page[0] < 1:
                current_page[0] = 1

            # Calculate which lines to print
            start_line = usable_height * (current_page[0] - 1)
            end_line = start_line + usable_height
            current_line = 1

            # Find the longest username and proxy
            userlen = 4
            proxylen = 5
            for item in threadStatus:
                if threadStatus[item]['type'] == 'Worker':
                    userlen = max(userlen, len(threadStatus[item]['user']))
                    if 'proxy_display' in threadStatus[item]:
                        proxylen = max(proxylen, len(str(threadStatus[item]['proxy_display'])))

            # How pretty
            status = '{:10} | {:5} | {:' + str(userlen) + '} | {:' + str(proxylen) + '} | {:7} | {:6} | {:5} | {:7} | {:10}'

            # Print the worker status
            status_text.append(status.format('Worker ID', 'Start', 'User', 'Proxy', 'Success', 'Failed', 'Empty', 'Skipped', 'Message'))
            for item in sorted(threadStatus):
                if(threadStatus[item]['type'] == 'Worker'):
                    current_line += 1

                    # Skip over items that don't belong on this page
                    if current_line < start_line:
                        continue
                    if current_line > end_line:
                        break

                    status_text.append(status.format(item, time.strftime('%H:%M', time.localtime(threadStatus[item]['starttime'])), threadStatus[item]['user'], threadStatus[item]['proxy_display'], threadStatus[item]['success'], threadStatus[item]['fail'], threadStatus[item]['noitems'], threadStatus[item]['skip'], threadStatus[item]['message']))

        elif display_type[0] == 'failedaccounts':
            status_text.append('-----------------------------------------')
            status_text.append('Accounts on hold:')
            status_text.append('-----------------------------------------')

            # Find the longest account name
            userlen = 4
            for account in account_failures:
                userlen = max(userlen, len(account['account']['username']))

            status = '{:' + str(userlen) + '} | {:10} | {:20}'
            status_text.append(status.format('User', 'Hold Time', 'Reason'))

            for account in account_failures:
                status_text.append(status.format(account['account']['username'], time.strftime('%H:%M:%S', time.localtime(account['last_fail_time'])), account['reason']))

        # Print the status_text for the current screen
        status_text.append('Page {}/{}. Page number to switch pages. F to show on hold accounts. <ENTER> alone to switch between status and log view'.format(current_page[0], total_pages))
        # Clear the screen
        os.system('cls' if os.name == 'nt' else 'clear')
        # Print status
        print "\n".join(status_text)


# The account recycler monitors failed accounts and places them back in the account queue 2 hours after they failed.
# This allows accounts that were soft banned to be retried after giving them a chance to cool down.
def account_recycler(accounts_queue, account_failures, args):
    while True:
        # Run once a minute
        time.sleep(60)
        log.info('Account recycler running. Checking status of {} accounts'.format(len(account_failures)))

        # Create a new copy of the failure list to search through, so we can iterate through it without it changing
        failed_temp = list(account_failures)

        # Search through the list for any item that last failed before 2 hours ago
        ok_time = now() - args.account_rest_interval
        for a in failed_temp:
            if a['last_fail_time'] <= ok_time:
                # Remove the account from the real list, and add to the account queue
                log.info('Account {} returning to active duty.'.format(a['account']['username']))
                account_failures.remove(a)
                accounts_queue.put(a['account'])
            else:
                log.info('Account {} needs to cool off for {} seconds due to {}'.format(a['account']['username'], a['last_fail_time'] - ok_time, a['reason']))


def worker_status_db_thread(threads_status, name, db_updates_queue):
    log.info("Clearing previous statuses for '%s' worker", name)
    WorkerStatus.delete().where(WorkerStatus.worker_name == name).execute()

    while True:
        workers = {}
        overseer = None
        for status in threads_status.values():
            if status['type'] == 'Overseer':
                overseer = {
                    'worker_name': name,
                    'message': status['message'],
                    'method': status['method'],
                    'last_modified': datetime.utcnow()
                }
            if status['type'] == 'Worker':
                workers[status['user']] = {
                    'username': status['user'],
                    'worker_name': name,
                    'success': status['success'],
                    'fail': status['fail'],
                    'no_items': status['noitems'],
                    'skip': status['skip'],
                    'last_modified': datetime.utcnow(),
                    'message': status['message']
                }
        if overseer is not None:
            db_updates_queue.put((MainWorker, {0: overseer}))
            db_updates_queue.put((WorkerStatus, workers))
        time.sleep(3)


# The main search loop that keeps an eye on the over all process
def search_overseer_thread(args, method, new_location_queue, pause_bit, encryption_lib_path, db_updates_queue, wh_queue):

    log.info('Search overseer starting')

    search_items_queue = Queue()
    account_queue = Queue()
    threadStatus = {}

    '''
    Create a queue of accounts for workers to pull from. When a worker has failed too many times,
    it can get a new account from the queue and reinitialize the API. Workers should return accounts
    to the queue so they can be tried again later, but must wait a bit before doing do so to
    prevent accounts from being cycled through too quickly.
    '''
    for i, account in enumerate(args.accounts):
        account_queue.put(account)

    # Create a list for failed accounts
    account_failures = []

    threadStatus['Overseer'] = {
        'message': 'Initializing',
        'type': 'Overseer',
        'method': 'Hex Grid' if method == 'hex' else 'Spawn Point'
    }

    if(args.print_status):
        log.info('Starting status printer thread')
        t = Thread(target=status_printer,
                   name='status_printer',
                   args=(threadStatus, search_items_queue, db_updates_queue, wh_queue, account_queue, account_failures))
        t.daemon = True
        t.start()

    # Create account recycler thread
    log.info('Starting account recycler thread')
    t = Thread(target=account_recycler, name='account-recycler', args=(account_queue, account_failures, args))
    t.daemon = True
    t.start()

    if args.status_name is not None:
        log.info('Starting status database thread')
        t = Thread(target=worker_status_db_thread,
                   name='status_worker_db',
                   args=(threadStatus, args.status_name, db_updates_queue))
        t.daemon = True
        t.start()

    # Create specified number of search_worker_thread
    log.info('Starting search worker threads')
    for i in range(0, args.workers):
        log.debug('Starting search worker thread %d', i)

        # Set proxy for each worker, using round robin
        proxy_display = 'No'
        proxy_url = False

        if args.proxy:
            proxy_display = proxy_url = args.proxy[i % len(args.proxy)]
            if args.proxy_display.upper() != 'FULL':
                proxy_display = i % len(args.proxy)

        workerId = 'Worker {:03}'.format(i)
        threadStatus[workerId] = {
            'type': 'Worker',
            'message': 'Creating thread...',
            'success': 0,
            'fail': 0,
            'noitems': 0,
            'skip': 0,
            'user': '',
            'proxy_display': proxy_display,
            'proxy_url': proxy_url,
        }

        t = Thread(target=search_worker_thread,
                   name='search-worker-{}'.format(i),
                   args=(args, account_queue, account_failures, search_items_queue, pause_bit,
                         encryption_lib_path, threadStatus[workerId],
                         db_updates_queue, wh_queue))
        t.daemon = True
        t.start()

    '''
    For hex scanning, we can generate the full list of scan points well
    in advance. When then can queue them all up to be searched as fast
    as the threads will allow.

    With spawn point scanning (sps) we can come up with the order early
    on, and we can populate the entire queue, but the individual threads
    will need to wait until the point is available (and ensure it is not
    to late as well).
    '''

    # A place to track the current location
    current_location = False

    # Used to tell SPS to scan for all CURRENT pokemon instead
    # of, like during a normal loop, just finding the next one
    # which will appear (since you've already scanned existing
    # locations in the prior loop)
    # Needed in a first loop and pausing/changing location.
    sps_scan_current = True

    # The real work starts here but will halt on pause_bit.set()
    while True:

        # paused; clear queue if needed, otherwise sleep and loop
        while pause_bit.is_set():
            if not search_items_queue.empty():
                try:
                    while True:
                        search_items_queue.get_nowait()
                except Empty:
                    pass
            threadStatus['Overseer']['message'] = 'Scanning is paused'
            sps_scan_current = True
            time.sleep(1)

        # If a new location has been passed to us, get the most recent one
        if not new_location_queue.empty():
            log.info('New location caught, moving search grid')
            sps_scan_current = True
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

        # If there are no search_items_queue either the loop has finished (or been
        # cleared above) -- either way, time to fill it back up
        if search_items_queue.empty():
            log.debug('Search queue empty, restarting loop')

            # locations = [((lat, lng, alt), ts_appears, ts_leaves),...]
            if method == 'hex':
                locations = get_hex_location_list(args, current_location)
            else:
                locations = get_sps_location_list(args, current_location, sps_scan_current)
                sps_scan_current = False

            if len(locations) == 0:
                log.warning('Nothing to scan!')

            threadStatus['Overseer']['message'] = 'Queuing steps'
            for step, step_location in enumerate(locations, 1):
                log.debug('Queueing step %d @ %f/%f/%f', step, step_location[0][0], step_location[0][1], step_location[0][2])
                search_args = (step, step_location[0], step_location[1], step_location[2])
                search_items_queue.put(search_args)
        else:
            nextitem = search_items_queue.queue[0]
            threadStatus['Overseer']['message'] = 'Processing search queue, next item is {:6f},{:6f}'.format(nextitem[1][0], nextitem[1][1])
            # If times are specified, print the time of the next queue item, and how many seconds ahead/behind realtime
            if nextitem[2]:
                threadStatus['Overseer']['message'] += ' @ {}'.format(time.strftime('%H:%M:%S', time.localtime(nextitem[2])))
                if nextitem[2] > now():
                    threadStatus['Overseer']['message'] += ' ({}s ahead)'.format(nextitem[2] - now())
                else:
                    threadStatus['Overseer']['message'] += ' ({}s behind)'.format(now() - nextitem[2])

        # Now we just give a little pause here
        time.sleep(1)


def get_hex_location_list(args, current_location):
    # if we are only scanning for pokestops/gyms, then increase step radius to visibility range
    if args.no_pokemon:
        step_distance = 0.900
    else:
        step_distance = 0.070

    # update our list of coords
    locations = generate_location_steps(current_location, args.step_limit, step_distance)

    # In hex "spawns only" mode, filter out scan locations with no history of pokemons
    if args.spawnpoints_only and not args.no_pokemon:
        n, e, s, w = hex_bounds(current_location, args.step_limit)
        spawnpoints = set((d['latitude'], d['longitude']) for d in Pokemon.get_spawnpoints(s, w, n, e))

        if len(spawnpoints) == 0:
            log.warning('No spawnpoints found in the specified area! (Did you forget to run a normal scan in this area first?)')

        def any_spawnpoints_in_range(coords):
            return any(geopy.distance.distance(coords, x).meters <= 70 for x in spawnpoints)

        locations = [coords for coords in locations if any_spawnpoints_in_range(coords)]

    # put into the right struture with zero'ed before/after values
    # locations = [(lat, lng, alt, ts_appears, ts_leaves),...]
    locationsZeroed = []
    for location in locations:
        locationsZeroed.append(((location[0], location[1], 0), 0, 0))

    return locationsZeroed


def get_sps_location_list(args, current_location, sps_scan_current):
    locations = []

    # Attempt to load spawns from file
    if args.spawnpoint_scanning != 'nofile':
        log.debug('Loading spawn points from json file @ %s', args.spawnpoint_scanning)
        try:
            with open(args.spawnpoint_scanning) as file:
                locations = json.load(file)
        except ValueError as e:
            log.exception(e)
            log.error('JSON error: %s; will fallback to database', e)
        except IOError as e:
            log.error('Error opening json file: %s; will fallback to database', e)

    # No locations yet? Try the database!
    if not len(locations):
        log.debug('Loading spawn points from database')
        locations = Pokemon.get_spawnpoints_in_hex(current_location, args.step_limit)

    # Well shit...
    if not len(locations):
        raise Exception('No availabe spawn points!')

    # locations[]:
    # {"lat": 37.53079079414139, "lng": -122.28811690874117, "spawnpoint_id": "808f9f1601d", "time": 511

    log.info('Total of %d spawns to track', len(locations))

    locations.sort(key=itemgetter('time'))

    if args.very_verbose:
        for i in locations:
            sec = i['time'] % 60
            minute = (i['time'] / 60) % 60
            m = 'Scan [{:02}:{:02}] ({}) @ {},{}'.format(minute, sec, i['time'], i['lat'], i['lng'])
            log.debug(m)

    # 'time' from json and db alike has been munged to appearance time as seconds after the hour
    # Here we'll convert that to a real timestamp
    for location in locations:
        # For a scan which should cover all CURRENT pokemon, we can offset
        # the comparison time by 15 minutes so that the "appears" time
        # won't be rolled over to the next hour.

        # TODO: Make it work. The original logic (commented out) was producing
        #       bogus results if your first scan was in the last 15 minute of
        #       the hour. Wrapping my head around this isn't work right now,
        #       so I'll just drop the feature for the time being. It does need
        #       to come back so that repositioning/pausing works more nicely,
        #       but we can live without it too.

        # if sps_scan_current:
        #     cursec = (location['time'] + 900) % 3600
        # else:
        cursec = location['time']

        if cursec > cur_sec():
            # hasn't spawn in the current hour
            from_now = location['time'] - cur_sec()
            appears = now() + from_now
        else:
            # won't spawn till next hour
            late_by = cur_sec() - location['time']
            appears = now() + 3600 - late_by

        location['appears'] = appears
        location['leaves'] = appears + 900

    # Put the spawn points in order of next appearance time
    locations.sort(key=itemgetter('appears'))

    # Match expected structure:
    # locations = [((lat, lng, alt), ts_appears, ts_leaves),...]
    retset = []
    for location in locations:
        retset.append(((location['lat'], location['lng'], 40.32), location['appears'], location['leaves']))

    return retset


def search_worker_thread(args, account_queue, account_failures, search_items_queue, pause_bit, encryption_lib_path, status, dbq, whq):

    log.debug('Search worker thread starting')

    # The outer forever loop restarts only when the inner one is intentionally exited - which should only be done when the worker is failing too often, and probably banned.
    # This reinitializes the API and grabs a new account from the queue.
    while True:
        try:
            status['starttime'] = now()

            # Get account
            status['message'] = 'Waiting to get new account from the queue'
            log.info(status['message'])
            account = account_queue.get()
            status['message'] = 'Switching to account {}'.format(account['username'])
            status['user'] = account['username']
            log.info(status['message'])

            stagger_thread(args, account)

            # New lease of life right here
            status['fail'] = 0
            status['success'] = 0
            status['noitems'] = 0
            status['skip'] = 0

            # Create the API instance this will use
            if args.mock != '':
                api = FakePogoApi(args.mock)
            else:
                api = PGoApi()

            if status['proxy_url']:
                log.debug("Using proxy %s", status['proxy_url'])
                api.set_proxy({'http': status['proxy_url'], 'https': status['proxy_url']})

            api.activate_signature(encryption_lib_path)

            # The forever loop for the searches
            while True:

                # If this account has been messing up too hard, let it rest
                if status['fail'] >= args.max_failures:
                    status['message'] = 'Account {} failed more than {} scans; possibly bad account. Switching accounts...'.format(account['username'], args.max_failures)
                    log.warning(status['message'])
                    account_failures.append({'account': account, 'last_fail_time': now(), 'reason': 'failures'})
                    break  # exit this loop to get a new account and have the API recreated

                # If this account has been running too long, let it rest
                if (args.account_search_interval is not None):
                    if (status['starttime'] <= (now() - args.account_search_interval)):
                        status['message'] = 'Account {} is being rotated out to rest.'.format(account['username'])
                        log.info(status['message'])
                        account_failures.append({'account': account, 'last_fail_time': now(), 'reason': 'rest interval'})
                        break

                while pause_bit.is_set():
                    status['message'] = 'Scanning paused'
                    time.sleep(2)

                # Grab the next thing to search (when available)
                status['message'] = 'Waiting for item from queue'
                step, step_location, appears, leaves = search_items_queue.get()

                # too soon?
                if appears and now() < appears + 10:  # adding a 10 second grace period
                    first_loop = True
                    paused = False
                    while now() < appears + 10:
                        if pause_bit.is_set():
                            paused = True
                            break  # why can't python just have `break 2`...
                        remain = appears - now() + 10
                        status['message'] = 'Early for {:6f},{:6f}; waiting {}s...'.format(step_location[0], step_location[1], remain)
                        if first_loop:
                            log.info(status['message'])
                            first_loop = False
                        time.sleep(1)
                    if paused:
                        search_items_queue.task_done()
                        continue

                # too late?
                if leaves and now() > (leaves - args.min_seconds_left):
                    search_items_queue.task_done()
                    status['skip'] += 1
                    # it is slightly silly to put this in status['message'] since it'll be overwritten very shortly after. Oh well.
                    status['message'] = 'Too late for location {:6f},{:6f}; skipping'.format(step_location[0], step_location[1])
                    log.info(status['message'])
                    # No sleep here; we've not done anything worth sleeping for. Plus we clearly need to catch up!
                    continue

                status['message'] = 'Searching at {:6f},{:6f}'.format(step_location[0], step_location[1])
                log.info(status['message'])

                # Let the api know where we intend to be for this loop
                api.set_position(*step_location)

                # Ok, let's get started -- check our login status
                check_login(args, account, api, step_location, status['proxy_url'])

                # Make the actual request (finally!)
                response_dict = map_request(api, step_location, args.jitter)

                # G'damnit, nothing back. Mark it up, sleep, carry on
                if not response_dict:
                    status['fail'] += 1
                    status['message'] = 'Invalid response at {:6f},{:6f}, abandoning location'.format(step_location[0], step_location[1])
                    log.error(status['message'])
                    time.sleep(args.scan_delay)
                    continue

                # Got the response, parse it out, send todo's to db/wh queues
                try:
                    parsed = parse_map(args, response_dict, step_location, dbq, whq)
                    search_items_queue.task_done()
                    status[('success' if parsed['count'] > 0 else 'noitems')] += 1
                    status['message'] = 'Search at {:6f},{:6f} completed with {} finds'.format(step_location[0], step_location[1], parsed['count'])
                    status['fail'] = 0
                    log.debug(status['message'])
                except KeyError:
                    parsed = False
                    status['fail'] += 1
                    status['message'] = 'Map parse failed at {:6f},{:6f}, abandoning location. {} may be banned.'.format(step_location[0], step_location[1], account['username'])
                    log.exception(status['message'])

                # Get detailed information about gyms
                if args.gym_info and parsed:
                    # build up a list of gyms to update
                    gyms_to_update = {}
                    for gym in parsed['gyms'].values():
                        # Can only get gym details within 1km of our position
                        distance = calc_distance(step_location, [gym['latitude'], gym['longitude']])
                        if distance < 1:
                            # check if we already have details on this gym (if not, get them)
                            try:
                                record = GymDetails.get(gym_id=gym['gym_id'])
                            except GymDetails.DoesNotExist as e:
                                gyms_to_update[gym['gym_id']] = gym
                                continue

                            # if we have a record of this gym already, check if the gym has been updated since our last update
                            if record.last_scanned < gym['last_modified']:
                                gyms_to_update[gym['gym_id']] = gym
                                continue
                            else:
                                log.debug('Skipping update of gym @ %f/%f, up to date', gym['latitude'], gym['longitude'])
                                continue
                        else:
                            log.debug('Skipping update of gym @ %f/%f, too far away from our location at %f/%f (%fkm)', gym['latitude'], gym['longitude'], step_location[0], step_location[1], distance)

                    if len(gyms_to_update):
                        gym_responses = {}
                        current_gym = 1
                        status['message'] = 'Updating {} gyms for location {},{}...'.format(len(gyms_to_update), step_location[0], step_location[1])
                        log.debug(status['message'])

                        for gym in gyms_to_update.values():
                            status['message'] = 'Getting details for gym {} of {} for location {},{}...'.format(current_gym, len(gyms_to_update), step_location[0], step_location[1])
                            time.sleep(random.random() + 2)
                            response = gym_request(api, step_location, gym)

                            # make sure the gym was in range. (sometimes the API gets cranky about gyms that are ALMOST 1km away)
                            if response['responses']['GET_GYM_DETAILS']['result'] == 2:
                                log.warning('Gym @ %f/%f is out of range (%dkm), skipping', gym['latitude'], gym['longitude'], distance)
                            else:
                                gym_responses[gym['gym_id']] = response['responses']['GET_GYM_DETAILS']

                            # increment which gym we're on (for status messages)
                            current_gym += 1

                        status['message'] = 'Processing details of {} gyms for location {},{}...'.format(len(gyms_to_update), step_location[0], step_location[1])
                        log.debug(status['message'])

                        if gym_responses:
                            parse_gyms(args, gym_responses, whq)

                # Always delay the desired amount after "scan" completion
                status['message'] += ', sleeping {}s until {}'.format(args.scan_delay, time.strftime('%H:%M:%S', time.localtime(time.time() + args.scan_delay)))
                time.sleep(args.scan_delay)

        # catch any process exceptions, log them, and continue the thread
        except Exception as e:
            status['message'] = 'Exception in search_worker using account {}. Restarting with fresh account. See logs for details.'.format(account['username'])
            time.sleep(args.scan_delay)
            log.error('Exception in search_worker under account {} Exception message: {}'.format(account['username'], e))
            account_failures.append({'account': account, 'last_fail_time': now(), 'reason': 'exception'})


def check_login(args, account, api, position, proxy_url):

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
            if proxy_url:
                api.set_authentication(provider=account['auth_service'], username=account['username'], password=account['password'], proxy_config={'http': proxy_url, 'https': proxy_url})
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
    time.sleep(args.scan_delay)


def map_request(api, position, jitter=False):
    # create scan_location to send to the api based off of position, because tuples aren't mutable
    if jitter:
        # jitter it, just a little bit.
        scan_location = jitterLocation(position)
        log.debug('Jittered to: %f/%f/%f', scan_location[0], scan_location[1], scan_location[2])
    else:
        # Just use the original coordinates
        scan_location = position

    try:
        cell_ids = util.get_cell_ids(scan_location[0], scan_location[1])
        timestamps = [0, ] * len(cell_ids)
        return api.get_map_objects(latitude=f2i(scan_location[0]),
                                   longitude=f2i(scan_location[1]),
                                   since_timestamp_ms=timestamps,
                                   cell_id=cell_ids)
    except Exception as e:
        log.warning('Exception while downloading map: %s', e)
        return False


def gym_request(api, position, gym):
    try:
        log.debug('Getting details for gym @ %f/%f (%fkm away)', gym['latitude'], gym['longitude'], calc_distance(position, [gym['latitude'], gym['longitude']]))
        x = api.get_gym_details(gym_id=gym['gym_id'],
                                player_latitude=f2i(position[0]),
                                player_longitude=f2i(position[1]),
                                gym_latitude=gym['latitude'],
                                gym_longitude=gym['longitude'])

        # print pretty(x)
        return x

    except Exception as e:
        log.warning('Exception while downloading gym details: %s', e)
        return False


def calc_distance(pos1, pos2):
    R = 6378.1  # km radius of the earth

    dLat = math.radians(pos1[0] - pos2[0])
    dLon = math.radians(pos1[1] - pos2[1])

    a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
        math.cos(math.radians(pos1[0])) * math.cos(math.radians(pos2[0])) * \
        math.sin(dLon / 2) * math.sin(dLon / 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c

    return d


# Delay each thread start time so that logins only occur ~1s
def stagger_thread(args, account):
    if args.accounts.index(account) == 0:
        return  # No need to delay the first one
    delay = args.accounts.index(account) + ((random.random() - .5) / 2)
    log.debug('Delaying thread startup for %.2f seconds', delay)
    time.sleep(delay)


class TooManyLoginAttempts(Exception):
    pass
