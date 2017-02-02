#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import configargparse
import os
import math
import json
import logging
import shutil
import pprint
import random
import time
import socket
import struct
import requests
from uuid import uuid4
from s2sphere import CellId, LatLng

from . import config

log = logging.getLogger(__name__)


def parse_unicode(bytestring):
    decoded_string = bytestring.decode(sys.getfilesystemencoding())
    return decoded_string


def verify_config_file_exists(filename):
    fullpath = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.exists(fullpath):
        log.info('Could not find %s, copying default.', filename)
        shutil.copy2(fullpath + '.example', fullpath)


def memoize(function):
    memo = {}

    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper


@memoize
def get_args():
    # Pre-check to see if the -cf or --config flag is used on the command line.
    # If not, we'll use the env var or default value. This prevents layering of
    # config files as well as a missing config.ini.
    defaultconfigfiles = []
    if '-cf' not in sys.argv and '--config' not in sys.argv:
        defaultconfigfiles = [os.getenv('POGOMAP_CONFIG', os.path.join(
            os.path.dirname(__file__), '../config/config.ini'))]
    parser = configargparse.ArgParser(
        default_config_files=defaultconfigfiles,
        auto_env_var_prefix='POGOMAP_')
    parser.add_argument('-cf', '--config',
                        is_config_file=True, help='Configuration file')
    parser.add_argument('-a', '--auth-service', type=str.lower,
                        action='append', default=[],
                        help=('Auth Services, either one for all accounts ' +
                              'or one per account: ptc or google. Defaults ' +
                              'all to ptc.'))
    parser.add_argument('-u', '--username', action='append', default=[],
                        help='Usernames, one per account.')
    parser.add_argument('-p', '--password', action='append', default=[],
                        help=('Passwords, either single one for all ' +
                              'accounts or one per account.'))
    parser.add_argument('-w', '--workers', type=int,
                        help=('Number of search worker threads to start. ' +
                              'Defaults to the number of accounts specified.'))
    parser.add_argument('-asi', '--account-search-interval', type=int,
                        default=0,
                        help=('Seconds for accounts to search before ' +
                              'switching to a new account. 0 to disable.'))
    parser.add_argument('-ari', '--account-rest-interval', type=int,
                        default=7200,
                        help=('Seconds for accounts to rest when they fail ' +
                              'or are switched out.'))
    parser.add_argument('-ac', '--accountcsv',
                        help=('Load accounts from CSV file containing ' +
                              '"auth_service,username,passwd" lines.'))
    parser.add_argument('-bh', '--beehive',
                        help=('Use beehive configuration for multiple ' +
                              'accounts, one account per hex.  Make sure ' +
                              'to keep -st under 5, and -w under the total' +
                              'amount of accounts available.'),
                        action='store_true', default=False)
    parser.add_argument('-wph', '--workers-per-hive',
                        help=('Only referenced when using --beehive. Sets ' +
                              'number of workers per hive. Default value ' +
                              'is 1.'),
                        type=int, default=1)
    parser.add_argument('-l', '--location', type=parse_unicode,
                        help='Location, can be an address or coordinates.')
    # Default based on the average elevation of cities around the world.
    # Source: https://www.wikiwand.com/en/List_of_cities_by_elevation
    parser.add_argument('-alt', '--altitude',
                        help='Default altitude in meters.',
                        type=int, default=507)
    parser.add_argument('-altv', '--altitude-variance',
                        help='Variance for --altitude in meters',
                        type=int, default=1)
    parser.add_argument('-nac', '--no-altitude-cache',
                        help=('Do not cache fetched altitudes in the' +
                              'database. This implies fetching the altitude ' +
                              'only once for the running instance.'),
                        action='store_true', default=False)
    parser.add_argument('-nj', '--no-jitter',
                        help=("Don't apply random -9m to +9m jitter to " +
                              "location."),
                        action='store_true', default=False)
    parser.add_argument('-st', '--step-limit', help='Steps.', type=int,
                        default=12)
    parser.add_argument('-sd', '--scan-delay',
                        help='Time delay between requests in scan threads.',
                        type=float, default=10)
    parser.add_argument('--spawn-delay',
                        help=('Number of seconds after spawn time to wait ' +
                              'before scanning to be sure the Pokemon ' +
                              'is there.'),
                        type=float, default=10)
    parser.add_argument('-enc', '--encounter',
                        help='Start an encounter to gather IVs and moves.',
                        action='store_true', default=False)
    parser.add_argument('-cs', '--captcha-solving',
                        help='Enables captcha solving.',
                        action='store_true', default=False)
    parser.add_argument('-ck', '--captcha-key',
                        help='2Captcha API key.')
    parser.add_argument('-cds', '--captcha-dsk',
                        help='PokemonGo captcha data-sitekey.',
                        default="6LeeTScTAAAAADqvhqVMhPpr_vB9D364Ia-1dSgK")
    parser.add_argument('-mcd', '--manual-captcha-domain',
                        help='Domain to where captcha tokens will be sent.',
                        default="http://127.0.0.1:5000")
    parser.add_argument('-mcr', '--manual-captcha-refresh',
                        help='Time available before captcha page refreshes.',
                        type=int, default=30)
    parser.add_argument('-mct', '--manual-captcha-timeout',
                        help='Maximum time captchas will wait for manual ' +
                        'captcha solving. On timeout, if enabled, 2Captcha ' +
                        'will be used to solve captcha. Default is 0.',
                        type=int, default=0)
    parser.add_argument('-ed', '--encounter-delay',
                        help=('Time delay between encounter pokemon ' +
                              'in scan threads.'),
                        type=float, default=1)
    encounter_list = parser.add_mutually_exclusive_group()
    encounter_list.add_argument('-ewht', '--encounter-whitelist',
                                action='append', default=[],
                                help=('List of Pokemon to encounter for ' +
                                      'more stats.'))
    encounter_list.add_argument('-eblk', '--encounter-blacklist',
                                action='append', default=[],
                                help=('List of Pokemon to NOT encounter for ' +
                                      'more stats.'))
    encounter_list.add_argument('-ewhtf', '--encounter-whitelist-file',
                                default='', help='File containing a list of '
                                                 'Pokemon to encounter for'
                                                 ' more stats.')
    encounter_list.add_argument('-eblkf', '--encounter-blacklist-file',
                                default='', help='File containing a list of '
                                                 'Pokemon to NOT encounter for'
                                                 ' more stats.')
    parser.add_argument('-ld', '--login-delay',
                        help='Time delay between each login attempt.',
                        type=float, default=6)
    parser.add_argument('-lr', '--login-retries',
                        help=('Number of login attempts before refreshing ' +
                              'a thread.'),
                        type=int, default=3)
    parser.add_argument('-mf', '--max-failures',
                        help=('Maximum number of failures to parse ' +
                              'locations before an account will go into a ' +
                              'sleep for -ari/--account-rest-interval ' +
                              'seconds.'),
                        type=int, default=5)
    parser.add_argument('-me', '--max-empty',
                        help=('Maximum number of empty scans before an ' +
                              'account will go into a sleep for ' +
                              '-ari/--account-rest-interval seconds.' +
                              'Reasonable to use with proxies.'),
                        type=int, default=0)
    parser.add_argument('-bsr', '--bad-scan-retry',
                        help=('Number of bad scans before giving up on a ' +
                              'step. Default 2, 0 to disable.'),
                        type=int, default=2)
    parser.add_argument('-msl', '--min-seconds-left',
                        help=('Time that must be left on a spawn before ' +
                              'considering it too late and skipping it. ' +
                              'For example 600 would skip anything with ' +
                              '< 10 minutes remaining. Default 0.'),
                        type=int, default=0)
    parser.add_argument('-dc', '--display-in-console',
                        help='Display Found Pokemon in Console.',
                        action='store_true', default=False)
    parser.add_argument('-H', '--host', help='Set web server listening host.',
                        default='127.0.0.1')
    parser.add_argument('-P', '--port', type=int,
                        help='Set web server listening port.', default=5000)
    parser.add_argument('-L', '--locale',
                        help=('Locale for Pokemon names (default: {}, check ' +
                              '{} for more).').format(config['LOCALE'],
                                                      config['LOCALES_DIR']),
                        default='en')
    parser.add_argument('-c', '--china',
                        help='Coordinates transformer for China.',
                        action='store_true')
    parser.add_argument('-m', '--mock', type=str,
                        help=('Mock mode - point to a fpgo endpoint instead ' +
                              'of using the real PogoApi, ec: ' +
                              'http://127.0.0.1:9090'),
                        default='')
    parser.add_argument('-ns', '--no-server',
                        help=('No-Server Mode. Starts the searcher but not ' +
                              'the Webserver.'),
                        action='store_true', default=False)
    parser.add_argument('-os', '--only-server',
                        help=('Server-Only Mode. Starts only the Webserver ' +
                              'without the searcher.'),
                        action='store_true', default=False)
    parser.add_argument('-nsc', '--no-search-control',
                        help='Disables search control.',
                        action='store_false', dest='search_control',
                        default=True)
    parser.add_argument('-fl', '--fixed-location',
                        help='Hides the search bar for use in shared maps.',
                        action='store_true', default=False)
    parser.add_argument('-k', '--gmaps-key',
                        help='Google Maps Javascript API Key.',
                        required=True)
    parser.add_argument('--skip-empty',
                        help=('Enables skipping of empty cells in normal ' +
                              'scans - requires previously populated ' +
                              'database (not to be used with -ss)'),
                        action='store_true', default=False)
    parser.add_argument('-C', '--cors', help='Enable CORS on web server.',
                        action='store_true', default=False)
    parser.add_argument('-D', '--db', help='Database filename for SQLite.',
                        default='pogom.db')
    parser.add_argument('-cd', '--clear-db',
                        help=('Deletes the existing database before ' +
                              'starting the Webserver.'),
                        action='store_true', default=False)
    parser.add_argument('-np', '--no-pokemon',
                        help=('Disables Pokemon from the map (including ' +
                              'parsing them into local db.)'),
                        action='store_true', default=False)
    parser.add_argument('-ng', '--no-gyms',
                        help=('Disables Gyms from the map (including ' +
                              'parsing them into local db).'),
                        action='store_true', default=False)
    parser.add_argument('-nk', '--no-pokestops',
                        help=('Disables PokeStops from the map (including ' +
                              'parsing them into local db).'),
                        action='store_true', default=False)
    parser.add_argument('-ss', '--spawnpoint-scanning',
                        help=('Use spawnpoint scanning (instead of hex ' +
                              'grid). Scans in a circle based on step_limit ' +
                              'when on DB.'),
                        nargs='?', const='nofile', default=False)
    parser.add_argument('-speed', '--speed-scan',
                        help=('Use speed scanning to identify spawn points ' +
                              'and then scan closest spawns.'),
                        action='store_true', default=False)
    parser.add_argument('-kph', '--kph',
                        help=('Set a maximum speed in km/hour for scanner ' +
                              'movement.'),
                        type=int, default=35)
    parser.add_argument('--dump-spawnpoints',
                        help=('Dump the spawnpoints from the db to json ' +
                              '(only for use with -ss).'),
                        action='store_true', default=False)
    parser.add_argument('-pd', '--purge-data',
                        help=('Clear Pokemon from database this many hours ' +
                              'after they disappear (0 to disable).'),
                        type=int, default=0)
    parser.add_argument('-px', '--proxy',
                        help='Proxy url (e.g. socks5://127.0.0.1:9050)',
                        action='append')
    parser.add_argument('-pxsc', '--proxy-skip-check',
                        help='Disable checking of proxies before start.',
                        action='store_true', default=False)
    parser.add_argument('-pxt', '--proxy-timeout',
                        help='Timeout settings for proxy checker in seconds.',
                        type=int, default=5)
    parser.add_argument('-pxd', '--proxy-display',
                        help=('Display info on which proxy being used ' +
                              '(index or full). To be used with -ps.'),
                        type=str, default='index')
    parser.add_argument('-pxf', '--proxy-file',
                        help=('Load proxy list from text file (one proxy ' +
                              'per line), overrides -px/--proxy.'))
    parser.add_argument('-pxr', '--proxy-refresh',
                        help=('Period of proxy file reloading, in seconds. ' +
                              'Works only with -pxf/--proxy-file. ' +
                              '(0 to disable).'),
                        type=int, default=0)
    parser.add_argument('-pxo', '--proxy-rotation',
                        help=('Enable proxy rotation with account changing ' +
                              'for search threads (none/round/random).'),
                        type=str, default='none')
    parser.add_argument('--db-type',
                        help='Type of database to be used (default: sqlite).',
                        default='sqlite')
    parser.add_argument('--db-name', help='Name of the database to be used.')
    parser.add_argument('--db-user', help='Username for the database.')
    parser.add_argument('--db-pass', help='Password for the database.')
    parser.add_argument('--db-host', help='IP or hostname for the database.')
    parser.add_argument(
        '--db-port', help='Port for the database.', type=int, default=3306)
    parser.add_argument('--db-max_connections',
                        help='Max connections (per thread) for the database.',
                        type=int, default=5)
    parser.add_argument('--db-threads',
                        help=('Number of db threads; increase if the db ' +
                              'queue falls behind.'),
                        type=int, default=1)
    parser.add_argument('-wh', '--webhook',
                        help='Define URL(s) to POST webhook information to.',
                        default=None, dest='webhooks', action='append')
    parser.add_argument('-gi', '--gym-info',
                        help=('Get all details about gyms (causes an ' +
                              'additional API hit for every gym).'),
                        action='store_true', default=False)
    parser.add_argument('--disable-clean', help='Disable clean db loop.',
                        action='store_true', default=False)
    parser.add_argument('--webhook-updates-only',
                        help='Only send updates (Pokemon & lured pokestops).',
                        action='store_true', default=False)
    parser.add_argument('--wh-threads',
                        help=('Number of webhook threads; increase if the ' +
                              'webhook queue falls behind.'),
                        type=int, default=1)
    parser.add_argument('-whc', '--wh-concurrency',
                        help=('Async requests pool size.'), type=int,
                        default=25)
    parser.add_argument('-whr', '--wh-retries',
                        help=('Number of times to retry sending webhook ' +
                              'data on failure.'),
                        type=int, default=3)
    parser.add_argument('-wht', '--wh-timeout',
                        help='Timeout (in seconds) for webhook requests.',
                        type=float, default=1.0)
    parser.add_argument('-whbf', '--wh-backoff-factor',
                        help=('Factor (in seconds) by which the delay ' +
                              'until next retry will increase.'),
                        type=float, default=0.25)
    parser.add_argument('-whlfu', '--wh-lfu-size',
                        help='Webhook LFU cache max size.', type=int,
                        default=1000)
    parser.add_argument('-whsu', '--webhook-scheduler-updates',
                        help=('Send webhook updates with scheduler status ' +
                              '(use with -wh).'),
                        action='store_true', default=True)
    parser.add_argument('--ssl-certificate',
                        help='Path to SSL certificate file.')
    parser.add_argument('--ssl-privatekey',
                        help='Path to SSL private key file.')
    parser.add_argument('-ps', '--print-status',
                        help=('Show a status screen instead of log ' +
                              'messages. Can switch between status and ' +
                              'logs by pressing enter.  Optionally specify ' +
                              '"logs" to startup in logging mode.'),
                        nargs='?', const='status', default=False,
                        metavar='logs')
    parser.add_argument('-slt', '--stats-log-timer',
                        help='In log view, list per hr stats every X seconds',
                        type=int, default=0)
    parser.add_argument('-sn', '--status-name', default=None,
                        help=('Enable status page database update using ' +
                              'STATUS_NAME as main worker name.'))
    parser.add_argument('-spp', '--status-page-password', default=None,
                        help='Set the status page password.')
    parser.add_argument('-hk', '--hash-key', default=None, action='append',
                        help='Key for hash server')
    parser.add_argument('-tut', '--complete-tutorial', action='store_true',
                        help=("Complete ToS and tutorial steps on accounts " +
                              "if they haven't already."),
                        default=False)
    parser.add_argument('-el', '--encrypt-lib',
                        help=('Path to encrypt lib to be used instead of ' +
                              'the shipped ones.'))
    parser.add_argument('-odt', '--on-demand_timeout',
                        help=('Pause searching while web UI is inactive ' +
                              'for this timeout(in seconds).'),
                        type=int, default=0)
    parser.add_argument('--disable-blacklist',
                        help=('Disable the global anti-scraper IP blacklist.'),
                        action='store_true', default=False)
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument('-v', '--verbose',
                           help=('Show debug messages from PokemonGo-Map ' +
                                 'and pgoapi. Optionally specify file ' +
                                 'to log to.'),
                           nargs='?', const='nofile', default=False,
                           metavar='filename.log')
    verbosity.add_argument('-vv', '--very-verbose',
                           help=('Like verbose, but show debug messages ' +
                                 'from all modules as well.  Optionally ' +
                                 'specify file to log to.'),
                           nargs='?', const='nofile', default=False,
                           metavar='filename.log')
    parser.set_defaults(DEBUG=False)

    args = parser.parse_args()

    if args.only_server:
        if args.location is None:
            parser.print_usage()
            print(sys.argv[0] +
                  ": error: arguments -l/--location is required.")
            sys.exit(1)
    else:
        # If using a CSV file, add the data where needed into the username,
        # password and auth_service arguments.
        # CSV file should have lines like "ptc,username,password",
        # "username,password" or "username".
        if args.accountcsv is not None:
            # Giving num_fields something it would usually not get.
            num_fields = -1
            with open(args.accountcsv, 'r') as f:
                for num, line in enumerate(f, 1):

                    fields = []

                    # First time around populate num_fields with current field
                    # count.
                    if num_fields < 0:
                        num_fields = line.count(',') + 1

                    csv_input = []
                    csv_input.append('')
                    csv_input.append('<username>')
                    csv_input.append('<username>,<password>')
                    csv_input.append('<ptc/google>,<username>,<password>')

                    # If the number of fields is differend this is not a CSV.
                    if num_fields != line.count(',') + 1:
                        print(sys.argv[0] +
                              ": Error parsing CSV file on line " + str(num) +
                              ". Your file started with the following " +
                              "input, '" + csv_input[num_fields] +
                              "' but now you gave us '" +
                              csv_input[line.count(',') + 1] + "'.")
                        sys.exit(1)

                    field_error = ''
                    line = line.strip()

                    # Ignore blank lines and comment lines.
                    if len(line) == 0 or line.startswith('#'):
                        continue

                    # If number of fields is more than 1 split the line into
                    # fields and strip them.
                    if num_fields > 1:
                        fields = line.split(",")
                        fields = map(str.strip, fields)

                    # If the number of fields is one then assume this is
                    # "username". As requested.
                    if num_fields == 1:
                        # Empty lines are already ignored.
                        args.username.append(line)

                    # If the number of fields is two then assume this is
                    # "username,password". As requested.
                    if num_fields == 2:
                        # If field length is not longer than 0 something is
                        # wrong!
                        if len(fields[0]) > 0:
                            args.username.append(fields[0])
                        else:
                            field_error = 'username'

                        # If field length is not longer than 0 something is
                        # wrong!
                        if len(fields[1]) > 0:
                            args.password.append(fields[1])
                        else:
                            field_error = 'password'

                    # If the number of fields is three then assume this is
                    # "ptc,username,password". As requested.
                    if num_fields == 3:
                        # If field 0 is not ptc or google something is wrong!
                        if (fields[0].lower() == 'ptc' or
                                fields[0].lower() == 'google'):
                            args.auth_service.append(fields[0])
                        else:
                            field_error = 'method'

                        # If field length is not longer then 0 something is
                        # wrong!
                        if len(fields[1]) > 0:
                            args.username.append(fields[1])
                        else:
                            field_error = 'username'

                        # If field length is not longer then 0 something is
                        # wrong!
                        if len(fields[2]) > 0:
                            args.password.append(fields[2])
                        else:
                            field_error = 'password'

                    if num_fields > 3:
                        print(('Too many fields in accounts file: max ' +
                               'supported are 3 fields. ' +
                               'Found {} fields').format(num_fields))
                        sys.exit(1)

                    # If something is wrong display error.
                    if field_error != '':
                        type_error = 'empty!'
                        if field_error == 'method':
                            type_error = (
                                'not ptc or google instead we got \'' +
                                fields[0] + '\'!')
                        print(sys.argv[0] +
                              ": Error parsing CSV file on line " + str(num) +
                              ". We found " + str(num_fields) + " fields, " +
                              "so your input should have looked like '" +
                              csv_input[num_fields] + "'\nBut you gave us '" +
                              line + "', your " + field_error +
                              " was " + type_error)
                        sys.exit(1)

        errors = []

        num_auths = len(args.auth_service)
        num_usernames = 0
        num_passwords = 0

        if len(args.username) == 0:
            errors.append(
                'Missing `username` either as -u/--username, csv file ' +
                'using -ac, or in config.')
        else:
            num_usernames = len(args.username)

        if args.location is None:
            errors.append(
                'Missing `location` either as -l/--location or in config.')

        if len(args.password) == 0:
            errors.append(
                'Missing `password` either as -p/--password, csv file, ' +
                'or in config.')
        else:
            num_passwords = len(args.password)

        if args.step_limit is None:
            errors.append(
                'Missing `step_limit` either as -st/--step-limit or ' +
                'in config.')

        if num_auths == 0:
            args.auth_service = ['ptc']

        num_auths = len(args.auth_service)

        if num_usernames > 1:
            if num_passwords > 1 and num_usernames != num_passwords:
                errors.append((
                    'The number of provided passwords ({}) must match the ' +
                    'username count ({})').format(num_passwords,
                                                  num_usernames))
            if num_auths > 1 and num_usernames != num_auths:
                errors.append((
                    'The number of provided auth ({}) must match the ' +
                    'username count ({}).').format(num_auths, num_usernames))

        if len(errors) > 0:
            parser.print_usage()
            print(sys.argv[0] + ": errors: \n - " + "\n - ".join(errors))
            sys.exit(1)

        # Fill the pass/auth if set to a single value.
        if num_passwords == 1:
            args.password = [args.password[0]] * num_usernames
        if num_auths == 1:
            args.auth_service = [args.auth_service[0]] * num_usernames

        # Make the accounts list.
        args.accounts = []
        for i, username in enumerate(args.username):
            args.accounts.append({'username': username,
                                  'password': args.password[i],
                                  'auth_service': args.auth_service[i]})

        # Make max workers equal number of accounts if unspecified, and disable
        # account switching.
        if args.workers is None:
            args.workers = len(args.accounts)
            args.account_search_interval = None

        # Disable search interval if 0 specified.
        if args.account_search_interval == 0:
            args.account_search_interval = None

        # Make sure we don't have an empty account list after adding command
        # line and CSV accounts.
        if len(args.accounts) == 0:
            print(sys.argv[0] +
                  ": Error: no accounts specified. Use -a, -u, and -p or " +
                  "--accountcsv to add accounts.")
            sys.exit(1)

        if args.encounter_whitelist_file:
            with open(args.encounter_whitelist_file) as f:
                args.encounter_whitelist = [get_pokemon_id(name) for name in
                                            f.read().splitlines()]
        elif args.encounter_blacklist_file:
            with open(args.encounter_blacklist_file) as f:
                args.encounter_blacklist = [get_pokemon_id(name) for name in
                                            f.read().splitlines()]
        else:
            args.encounter_blacklist = [int(i) for i in
                                        args.encounter_blacklist]
            args.encounter_whitelist = [int(i) for i in
                                        args.encounter_whitelist]

        # Decide which scanning mode to use.
        if args.spawnpoint_scanning:
            args.scheduler = 'SpawnScan'
        elif args.skip_empty:
            args.scheduler = 'HexSearchSpawnpoint'
        elif args.speed_scan:
            args.scheduler = 'SpeedScan'
        else:
            args.scheduler = 'HexSearch'

        # Disable webhook scheduler updates if webhooks are disabled
        if args.webhooks is None:
            args.webhook_scheduler_updates = False

    return args


def now():
    # The fact that you need this helper...
    return int(time.time())


# Gets the seconds past the hour.
def cur_sec():
    return (60 * time.gmtime().tm_min) + time.gmtime().tm_sec


# Gets the total seconds past the hour for a given date.
def date_secs(d):
    return d.minute * 60 + d.second


# Checks to see if test is between start and end accounting for hour
# wraparound.
def clock_between(start, test, end):
    return ((start <= test <= end and start < end) or
            (not (end <= test <= start) and start > end))


# Return amount of seconds between two times on the clock.
def secs_between(time1, time2):
    return min((time1 - time2) % 3600, (time2 - time1) % 3600)


# Return the s2sphere cellid token from a location.
def cellid(loc):
    return CellId.from_lat_lng(LatLng.from_degrees(loc[0], loc[1])).to_token()


# Return equirectangular approximation distance in km.
def equi_rect_distance(loc1, loc2):
    R = 6371  # Radius of the earth in km.
    lat1 = math.radians(loc1[0])
    lat2 = math.radians(loc2[0])
    x = (math.radians(loc2[1]) - math.radians(loc1[1])
         ) * math.cos(0.5 * (lat2 + lat1))
    y = lat2 - lat1
    return R * math.sqrt(x * x + y * y)


# Return True if distance between two locs is less than distance in km.
def in_radius(loc1, loc2, distance):
    return equi_rect_distance(loc1, loc2) < distance


def i8ln(word):
    if config['LOCALE'] == "en":
        return word
    if not hasattr(i8ln, 'dictionary'):
        file_path = os.path.join(
            config['ROOT_PATH'],
            config['LOCALES_DIR'],
            '{}.min.json'.format(config['LOCALE']))
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                i8ln.dictionary = json.loads(f.read())
        else:
            log.warning(
                'Skipping translations - unable to find locale file: %s',
                file_path)
            return word
    if word in i8ln.dictionary:
        return i8ln.dictionary[word]
    else:
        log.debug('Unable to find translation for "%s" in locale %s!',
                  word, config['LOCALE'])
        return word


def get_pokemon_data(pokemon_id):
    if not hasattr(get_pokemon_data, 'pokemon'):
        file_path = os.path.join(
            config['ROOT_PATH'],
            config['DATA_DIR'],
            'pokemon.min.json')

        with open(file_path, 'r') as f:
            get_pokemon_data.pokemon = json.loads(f.read())
    return get_pokemon_data.pokemon[str(pokemon_id)]


def get_pokemon_id(pokemon_name):
    if not hasattr(get_pokemon_id, 'ids'):
        if not hasattr(get_pokemon_data, 'pokemon'):
            # initialize from file
            get_pokemon_data(1)

        get_pokemon_id.ids = {}
        for pokemon_id, data in get_pokemon_data.pokemon.iteritems():
            get_pokemon_id.ids[data['name']] = int(pokemon_id)

    return get_pokemon_id.ids.get(pokemon_name, -1)


def get_pokemon_name(pokemon_id):
    return i8ln(get_pokemon_data(pokemon_id)['name'])


def get_pokemon_rarity(pokemon_id):
    return i8ln(get_pokemon_data(pokemon_id)['rarity'])


def get_pokemon_types(pokemon_id):
    pokemon_types = get_pokemon_data(pokemon_id)['types']
    return map(lambda x: {"type": i8ln(x['type']), "color": x['color']},
               pokemon_types)


def get_moves_data(move_id):
    if not hasattr(get_moves_data, 'moves'):
        file_path = os.path.join(
            config['ROOT_PATH'],
            config['DATA_DIR'],
            'moves.min.json')

        with open(file_path, 'r') as f:
            get_moves_data.moves = json.loads(f.read())
    return get_moves_data.moves[str(move_id)]


def get_move_name(move_id):
    return i8ln(get_moves_data(move_id)['name'])


def get_move_damage(move_id):
    return i8ln(get_moves_data(move_id)['damage'])


def get_move_energy(move_id):
    return i8ln(get_moves_data(move_id)['energy'])


def get_move_type(move_id):
    return i8ln(get_moves_data(move_id)['type'])


class Timer():

    def __init__(self, name):
        self.times = [(name, time.time(), 0)]

    def add(self, step):
        t = time.time()
        self.times.append((step, t, round((t - self.times[-1][1]) * 1000)))

    def checkpoint(self, step):
        t = time.time()
        self.times.append(('total @ ' + step, t, t - self.times[0][1]))

    def output(self):
        self.checkpoint('end')
        pprint.pprint(self.times)


def dottedQuadToNum(ip):
    return struct.unpack("!L", socket.inet_aton(ip))[0]


def get_blacklist():
    try:
        url = 'https://blist.devkat.org/blacklist.json'
        blacklist = requests.get(url).json()
        log.debug('Entries in blacklist: %s.', len(blacklist))
        return blacklist
    except (requests.exceptions.RequestException, IndexError, KeyError):
        log.error('Unable to retrieve blacklist, setting to empty.')
        return []


# Generate random device info.
# Original by Noctem.
IPHONES = {'iPhone5,1': 'N41AP',
           'iPhone5,2': 'N42AP',
           'iPhone5,3': 'N48AP',
           'iPhone5,4': 'N49AP',
           'iPhone6,1': 'N51AP',
           'iPhone6,2': 'N53AP',
           'iPhone7,1': 'N56AP',
           'iPhone7,2': 'N61AP',
           'iPhone8,1': 'N71AP',
           'iPhone8,2': 'N66AP',
           'iPhone8,4': 'N69AP',
           'iPhone9,1': 'D10AP',
           'iPhone9,2': 'D11AP',
           'iPhone9,3': 'D101AP',
           'iPhone9,4': 'D111AP'}


def generate_device_info():
    device_info = {'device_brand': 'Apple', 'device_model': 'iPhone',
                   'hardware_manufacturer': 'Apple',
                   'firmware_brand': 'iPhone OS'}
    devices = tuple(IPHONES.keys())

    ios8 = ('8.0', '8.0.1', '8.0.2', '8.1', '8.1.1',
            '8.1.2', '8.1.3', '8.2', '8.3', '8.4', '8.4.1')
    ios9 = ('9.0', '9.0.1', '9.0.2', '9.1', '9.2', '9.2.1',
            '9.3', '9.3.1', '9.3.2', '9.3.3', '9.3.4', '9.3.5')
    ios10 = ('10.0', '10.0.1', '10.0.2', '10.0.3', '10.1', '10.1.1')

    device_info['device_model_boot'] = random.choice(devices)
    device_info['hardware_model'] = IPHONES[device_info['device_model_boot']]
    device_info['device_id'] = uuid4().hex

    if device_info['hardware_model'] in ('iPhone9,1', 'iPhone9,2',
                                         'iPhone9,3', 'iPhone9,4'):
        device_info['firmware_type'] = random.choice(ios10)
    elif device_info['hardware_model'] in ('iPhone8,1', 'iPhone8,2',
                                           'iPhone8,4'):
        device_info['firmware_type'] = random.choice(ios9 + ios10)
    else:
        device_info['firmware_type'] = random.choice(ios8 + ios9 + ios10)

    return device_info
