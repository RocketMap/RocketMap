#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import logging
import time
import re
import requests
import ssl
import json

from distutils.version import StrictVersion

from threading import Thread, Event
from queue import Queue
from flask_cors import CORS
from flask_cache_bust import init_cache_busting

from pogom import config
from pogom.app import Pogom
from pogom.utils import get_args, get_encryption_lib_path, now

from pogom.search import search_overseer_thread
from pogom.models import init_database, create_tables, drop_tables, Pokemon, db_updater, clean_db_loop
from pogom.webhook import wh_updater

from pogom.proxy import check_proxies

# Currently supported pgoapi
pgoapi_version = "1.1.7"

# Moved here so logger is configured at load time
logging.basicConfig(format='%(asctime)s [%(threadName)16s][%(module)14s][%(levelname)8s] %(message)s')
log = logging.getLogger()

# Make sure pogom/pgoapi is actually removed if it is an empty directory
# This is a leftover directory from the time pgoapi was embedded in PokemonGo-Map
# The empty directory will cause problems with `import pgoapi` so it needs to go
oldpgoapiPath = os.path.join(os.path.dirname(__file__), "pogom/pgoapi")
if os.path.isdir(oldpgoapiPath):
    log.info("I found %s, but its no longer used. Going to remove it...", oldpgoapiPath)
    shutil.rmtree(oldpgoapiPath)
    log.info("Done!")

# Assert pgoapi is installed
try:
    import pgoapi
    from pgoapi import utilities as util
except ImportError:
    log.critical("It seems `pgoapi` is not installed. You must run pip install -r requirements.txt again")
    sys.exit(1)

# Assert pgoapi >= pgoapi_version
if not hasattr(pgoapi, "__version__") or StrictVersion(pgoapi.__version__) < StrictVersion(pgoapi_version):
    log.critical("It seems `pgoapi` is not up-to-date. You must run pip install -r requirements.txt again")
    sys.exit(1)


# Patch to make exceptions in threads cause an exception.
def install_thread_excepthook():
    """
    Workaround for sys.excepthook thread bug
    (https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470).
    Call once from __main__ before creating any threads.
    If using psyco, call psycho.cannotcompile(threading.Thread.run)
    since this replaces a new-style class method.
    """
    import sys
    run_old = Thread.run

    def run(*args, **kwargs):
        try:
            run_old(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            sys.excepthook(*sys.exc_info())
    Thread.run = run


# Exception handler will log unhandled exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def main():
    # Patch threading to make exceptions catchable
    install_thread_excepthook()

    # Make sure exceptions get logged
    sys.excepthook = handle_exception

    args = get_args()

    # Add file logging if enabled
    if args.verbose and args.verbose != 'nofile':
        filelog = logging.FileHandler(args.verbose)
        filelog.setFormatter(logging.Formatter('%(asctime)s [%(threadName)16s][%(module)14s][%(levelname)8s] %(message)s'))
        logging.getLogger('').addHandler(filelog)
    if args.very_verbose and args.very_verbose != 'nofile':
        filelog = logging.FileHandler(args.very_verbose)
        filelog.setFormatter(logging.Formatter('%(asctime)s [%(threadName)16s][%(module)14s][%(levelname)8s] %(message)s'))
        logging.getLogger('').addHandler(filelog)

    # Check if we have the proper encryption library file and get its path
    encryption_lib_path = get_encryption_lib_path(args)
    if encryption_lib_path is "":
        sys.exit(1)

    if args.verbose or args.very_verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    # Let's not forget to run Grunt / Only needed when running with webserver
    if not args.no_server:
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'static/dist')):
            log.critical('Missing front-end assets (static/dist) -- please run "npm install && npm run build" before starting the server')
            sys.exit()

    # These are very noisey, let's shush them up a bit
    logging.getLogger('peewee').setLevel(logging.INFO)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('pgoapi.pgoapi').setLevel(logging.WARNING)
    logging.getLogger('pgoapi.rpc_api').setLevel(logging.INFO)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    config['parse_pokemon'] = not args.no_pokemon
    config['parse_pokestops'] = not args.no_pokestops
    config['parse_gyms'] = not args.no_gyms

    # Turn these back up if debugging
    if args.verbose or args.very_verbose:
        logging.getLogger('pgoapi').setLevel(logging.DEBUG)
    if args.very_verbose:
        logging.getLogger('peewee').setLevel(logging.DEBUG)
        logging.getLogger('requests').setLevel(logging.DEBUG)
        logging.getLogger('pgoapi.pgoapi').setLevel(logging.DEBUG)
        logging.getLogger('pgoapi.rpc_api').setLevel(logging.DEBUG)
        logging.getLogger('rpc_api').setLevel(logging.DEBUG)
        logging.getLogger('werkzeug').setLevel(logging.DEBUG)

    # use lat/lng directly if matches such a pattern
    prog = re.compile("^(\-?\d+\.\d+),?\s?(\-?\d+\.\d+)$")
    res = prog.match(args.location)
    if res:
        log.debug('Using coordinates from CLI directly')
        position = (float(res.group(1)), float(res.group(2)), 0)
    else:
        log.debug('Looking up coordinates in API')
        position = util.get_pos_by_name(args.location)

    # Use the latitude and longitude to get the local altitude from Google
    try:
        url = 'https://maps.googleapis.com/maps/api/elevation/json?locations={},{}'.format(
            str(position[0]), str(position[1]))
        altitude = requests.get(url).json()[u'results'][0][u'elevation']
        log.debug('Local altitude is: %sm', altitude)
        position = (position[0], position[1], altitude)
    except (requests.exceptions.RequestException, IndexError, KeyError):
        log.error('Unable to retrieve altitude from Google APIs; setting to 0')

    if not any(position):
        log.error('Could not get a position by name, aborting')
        sys.exit()

    log.info('Parsed location is: %.4f/%.4f/%.4f (lat/lng/alt)',
             position[0], position[1], position[2])

    if args.no_pokemon:
        log.info('Parsing of Pokemon disabled')
    if args.no_pokestops:
        log.info('Parsing of Pokestops disabled')
    if args.no_gyms:
        log.info('Parsing of Gyms disabled')
    if args.encounter:
        log.info('Encountering pokemon enabled')

    config['LOCALE'] = args.locale
    config['CHINA'] = args.china

    app = Pogom(__name__)
    db = init_database(app)
    if args.clear_db:
        log.info('Clearing database')
        if args.db_type == 'mysql':
            drop_tables(db)
        elif os.path.isfile(args.db):
            os.remove(args.db)
    create_tables(db)

    app.set_current_location(position)

    # Control the search status (running or not) across threads
    pause_bit = Event()
    pause_bit.clear()
    if args.on_demand_timeout > 0:
        pause_bit.set()

    heartbeat = [now()]

    # Setup the location tracking queue and push the first location on
    new_location_queue = Queue()
    new_location_queue.put(position)

    # DB Updates
    db_updates_queue = Queue()

    # Thread(s) to process database updates
    for i in range(args.db_threads):
        log.debug('Starting db-updater worker thread %d', i)
        t = Thread(target=db_updater, name='db-updater-{}'.format(i), args=(args, db_updates_queue))
        t.daemon = True
        t.start()

    # db clearner; really only need one ever
    if not args.disable_clean:
        t = Thread(target=clean_db_loop, name='db-cleaner', args=(args,))
        t.daemon = True
        t.start()

    # WH Updates
    wh_updates_queue = Queue()

    # Thread to process webhook updates
    for i in range(args.wh_threads):
        log.debug('Starting wh-updater worker thread %d', i)
        t = Thread(target=wh_updater, name='wh-updater-{}'.format(i), args=(args, wh_updates_queue))
        t.daemon = True
        t.start()

    if not args.only_server:

        # Check all proxies before continue so we know they are good
        if args.proxy and not args.proxy_skip_check:

            # Overwrite old args.proxy with new working list
            args.proxy = check_proxies(args)

        # Gather the pokemons!

        # attempt to dump the spawn points (do this before starting threads of endure the woe)
        if args.spawnpoint_scanning and args.spawnpoint_scanning != 'nofile' and args.dump_spawnpoints:
            with open(args.spawnpoint_scanning, 'w+') as file:
                log.info('Saving spawn points to %s', args.spawnpoint_scanning)
                spawns = Pokemon.get_spawnpoints_in_hex(position, args.step_limit)
                file.write(json.dumps(spawns))
                log.info('Finished exporting spawn points')

        argset = (args, new_location_queue, pause_bit, heartbeat, encryption_lib_path, db_updates_queue, wh_updates_queue)

        log.debug('Starting a %s search thread', args.scheduler)
        search_thread = Thread(target=search_overseer_thread, name='search-overseer', args=argset)
        search_thread.daemon = True
        search_thread.start()

    if args.cors:
        CORS(app)

    # No more stale JS
    init_cache_busting(app)

    app.set_search_control(pause_bit)
    app.set_heartbeat_control(heartbeat)
    app.set_location_queue(new_location_queue)

    config['ROOT_PATH'] = app.root_path
    config['GMAPS_KEY'] = args.gmaps_key

    if args.no_server:
        # This loop allows for ctrl-c interupts to work since flask won't be holding the program open
        while search_thread.is_alive():
            time.sleep(60)
    else:
        ssl_context = None
        if args.ssl_certificate and args.ssl_privatekey \
                and os.path.exists(args.ssl_certificate) and os.path.exists(args.ssl_privatekey):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            ssl_context.load_cert_chain(args.ssl_certificate, args.ssl_privatekey)
            log.info('Web server in SSL mode.')
        if args.verbose or args.very_verbose:
            app.run(threaded=True, use_reloader=False, debug=True, host=args.host, port=args.port, ssl_context=ssl_context)
        else:
            app.run(threaded=True, use_reloader=False, debug=False, host=args.host, port=args.port, ssl_context=ssl_context)

if __name__ == '__main__':
    main()
