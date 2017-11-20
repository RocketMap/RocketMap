#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import configargparse
import os
import json
import logging
import random
import time
import socket
import struct
import hashlib
import psutil
import subprocess
import requests

from s2sphere import CellId, LatLng
from geopy.geocoders import GoogleV3
from requests_futures.sessions import FuturesSession
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from cHaversine import haversine
from pprint import pformat

log = logging.getLogger(__name__)


def parse_unicode(bytestring):
    decoded_string = bytestring.decode(sys.getfilesystemencoding())
    return decoded_string


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
                        is_config_file=True, help='Set configuration file')
    parser.add_argument('-scf', '--shared-config',
                        is_config_file=True, help='Set a shared config')
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
    parser.add_argument('-hlvl', '--high-lvl-accounts',
                        help=('Load high level accounts from CSV file '
                              + ' containing '
                              + '"auth_service,username,passwd"'
                              + ' lines.'))
    parser.add_argument('-bh', '--beehive',
                        help=('Use beehive configuration for multiple ' +
                              'accounts, one account per hex.  Make sure ' +
                              'to keep -st under 5, and -w under the total ' +
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
    parser.add_argument('-uac', '--use-altitude-cache',
                        help=('Query the Elevation API for each step,' +
                              ' rather than only once, and store results in' +
                              ' the database.'),
                        action='store_true', default=False)
    parser.add_argument('-nj', '--no-jitter',
                        help=("Don't apply random -9m to +9m jitter to " +
                              "location."),
                        action='store_true', default=False)
    parser.add_argument('-al', '--access-logs',
                        help=("Write web logs to access.log."),
                        action='store_true', default=False)
    parser.add_argument('-st', '--step-limit', help='Steps.', type=int,
                        default=12)
    parser.add_argument('-gf', '--geofence-file',
                        help=('Geofence file to define outer borders of the ' +
                              'scan area.'),
                        default='')
    parser.add_argument('-gef', '--geofence-excluded-file',
                        help=('File to define excluded areas inside scan ' +
                              'area. Regarded this as inverted geofence. ' +
                              'Can be combined with geofence-file.'),
                        default='')
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
                        help='Pokemon Go captcha data-sitekey.',
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
    parser.add_argument('-ignf', '--ignorelist-file',
                        default='', help='File containing a list of ' +
                        'Pokemon IDs to ignore, one line per ID. ' +
                        'Spawnpoints will be saved, but ignored ' +
                        'Pokemon won\'t be encountered, sent to ' +
                        'webhooks or saved to the DB.')
    parser.add_argument('-encwf', '--enc-whitelist-file',
                        default='', help='File containing a list of '
                        'Pokemon IDs to encounter for'
                        ' IV/CP scanning. One line per ID.')
    parser.add_argument('-nostore', '--no-api-store',
                        help=("Don't store the API objects used by the high"
                              + ' level accounts in memory. This will increase'
                              + ' the number of logins per account, but '
                              + ' decreases memory usage.'),
                        action='store_true', default=False)
    parser.add_argument('-apir', '--api-retries',
                        help=('Number of times to retry an API request.'),
                        type=int, default=3)
    webhook_list = parser.add_mutually_exclusive_group()
    webhook_list.add_argument('-wwht', '--webhook-whitelist',
                              action='append', default=[],
                              help=('List of Pokemon to send to '
                                    'webhooks. Specified as Pokemon ID.'))
    webhook_list.add_argument('-wblk', '--webhook-blacklist',
                              action='append', default=[],
                              help=('List of Pokemon NOT to send to '
                                    'webhooks. Specified as Pokemon ID.'))
    webhook_list.add_argument('-wwhtf', '--webhook-whitelist-file',
                              default='', help='File containing a list of '
                                               'Pokemon IDs to be sent to '
                                               'webhooks.')
    webhook_list.add_argument('-wblkf', '--webhook-blacklist-file',
                              default='', help='File containing a list of '
                                               'Pokemon IDs NOT to be sent to'
                                               'webhooks.')
    parser.add_argument('-ld', '--login-delay',
                        help='Time delay between each login attempt.',
                        type=float, default=6)
    parser.add_argument('-lr', '--login-retries',
                        help=('Number of times to retry the login before ' +
                              'refreshing a thread.'),
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
                        help=('Locale for Pokemon names (check' +
                              ' static/dist/locales for more).'),
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
    parser.add_argument('-sc', '--search-control',
                        help='Enables search control.',
                        action='store_true', dest='search_control',
                        default=False)
    parser.add_argument('-nfl', '--no-fixed-location',
                        help='Disables a fixed map location and shows the ' +
                        'search bar for use in shared maps.',
                        action='store_false', dest='fixed_location',
                        default=True)
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
    parser.add_argument('-nr', '--no-raids',
                        help=('Disables Raids from the map (including ' +
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
    parser.add_argument('-spin', '--pokestop-spinning',
                        help=('Spin Pokestops with 50%% probability.'),
                        action='store_true', default=False)
    parser.add_argument('-ams', '--account-max-spins',
                        help='Maximum number of Pokestop spins per hour.',
                        type=int, default=20)
    parser.add_argument('-kph', '--kph',
                        help=('Set a maximum speed in km/hour for scanner ' +
                              'movement.'),
                        type=int, default=35)
    parser.add_argument('-hkph', '--hlvl-kph',
                        help=('Set a maximum speed in km/hour for scanner ' +
                              'movement, for high-level (L30) accounts.'),
                        type=int, default=25)
    parser.add_argument('-ldur', '--lure-duration',
                        help=('Change duration for lures set on pokestops. ' +
                              'This is useful for events that extend lure ' +
                              'duration.'), type=int, default=30)
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
    parser.add_argument('-pxt', '--proxy-test-timeout',
                        help='Timeout settings for proxy checker in seconds.',
                        type=int, default=5)
    parser.add_argument('-pxre', '--proxy-test-retries',
                        help=('Number of times to retry sending proxy ' +
                              'test requests on failure.'),
                        type=int, default=0)
    parser.add_argument('-pxbf', '--proxy-test-backoff-factor',
                        help=('Factor (in seconds) by which the delay ' +
                              'until next retry will increase.'),
                        type=float, default=0.25)
    parser.add_argument('-pxc', '--proxy-test-concurrency',
                        help=('Async requests pool size.'), type=int,
                        default=0)
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
                        type=str, default='round')
    parser.add_argument('--db-type',
                        help='Type of database to be used (default: sqlite).',
                        default='sqlite')
    parser.add_argument('--db-name', help='Name of the database to be used.')
    parser.add_argument('--db-user', help='Username for the database.')
    parser.add_argument('--db-pass', help='Password for the database.')
    parser.add_argument('--db-host', help='IP or hostname for the database.')
    parser.add_argument(
        '--db-port', help='Port for the database.', type=int, default=3306)
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
    parser.add_argument('-DC', '--enable-clean', help='Enable DB cleaner.',
                        action='store_true', default=False)
    parser.add_argument(
        '--wh-types',
        help=('Defines the type of messages to send to webhooks.'),
        choices=[
            'pokemon', 'gym', 'raid', 'egg', 'tth', 'gym-info',
            'pokestop', 'lure', 'captcha'
        ],
        action='append',
        default=[])
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
                        default=2500)
    parser.add_argument('-whfi', '--wh-frame-interval',
                        help=('Minimum time (in ms) to wait before sending the'
                              + ' next webhook data frame.'), type=int,
                        default=500)
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
    parser.add_argument('-sn', '--status-name', default=str(os.getpid()),
                        help=('Enable status page database update using ' +
                              'STATUS_NAME as main worker name.'))
    parser.add_argument('-spp', '--status-page-password', default=None,
                        help='Set the status page password.')
    parser.add_argument('-hk', '--hash-key', default=None, action='append',
                        help='Key for hash server')
    parser.add_argument('-novc', '--no-version-check', action='store_true',
                        help='Disable API version check.',
                        default=False)
    parser.add_argument('-vci', '--version-check-interval', type=int,
                        help='Interval to check API version in seconds ' +
                        '(Default: in [60, 300]).',
                        default=random.randint(60, 300))
    parser.add_argument('-el', '--encrypt-lib',
                        help=('Path to encrypt lib to be used instead of ' +
                              'the shipped ones.'))
    parser.add_argument('-odt', '--on-demand_timeout',
                        help=('Pause searching while web UI is inactive ' +
                              'for this timeout (in seconds).'),
                        type=int, default=0)
    parser.add_argument('--disable-blacklist',
                        help=('Disable the global anti-scraper IP blacklist.'),
                        action='store_true', default=False)
    parser.add_argument('-tp', '--trusted-proxies', default=[],
                        action='append',
                        help=('Enables the use of X-FORWARDED-FOR headers ' +
                              'to identify the IP of clients connecting ' +
                              'through these trusted proxies.'))
    parser.add_argument('--api-version', default='0.79.4',
                        help=('API version currently in use.'))
    parser.add_argument('--no-file-logs',
                        help=('Disable logging to files. ' +
                              'Does not disable --access-logs.'),
                        action='store_true', default=False)
    parser.add_argument('--log-path',
                        help=('Defines directory to save log files to.'),
                        default='logs/')
    parser.add_argument('--dump',
                        help=('Dump censored debug info about the ' +
                              'environment and auto-upload to ' +
                              'hastebin.com.'),
                        action='store_true', default=False)
    verbose = parser.add_mutually_exclusive_group()
    verbose.add_argument('-v',
                         help=('Show debug messages from RocketMap ' +
                               'and pgoapi. Can be repeated up to 3 times.'),
                         action='count', default=0, dest='verbose')
    verbose.add_argument('--verbosity',
                         help=('Show debug messages from RocketMap ' +
                               'and pgoapi.'),
                         type=int, dest='verbose')
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

        # Prepare the L30 accounts for the account sets.
        args.accounts_L30 = []

        if args.high_lvl_accounts:
            # Context processor.
            with open(args.high_lvl_accounts, 'r') as accs:
                for line in accs:
                    # Make sure it's not an empty line.
                    if not line.strip():
                        continue

                    line = line.split(',')

                    # We need "service, user, pass".
                    if len(line) < 3:
                        raise Exception('L30 account is missing a'
                                        + ' field. Each line requires: '
                                        + '"service,user,pass".')

                    # Let's remove trailing whitespace.
                    service = line[0].strip()
                    username = line[1].strip()
                    password = line[2].strip()

                    hlvl_account = {
                        'auth_service': service,
                        'username': username,
                        'password': password,
                        'captcha': False
                    }

                    args.accounts_L30.append(hlvl_account)

        # Prepare the IV/CP scanning filters.
        args.enc_whitelist = []

        # IV/CP scanning.
        if args.enc_whitelist_file:
            with open(args.enc_whitelist_file) as f:
                args.enc_whitelist = frozenset([int(l.strip()) for l in f])

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

        if args.webhook_whitelist_file:
            with open(args.webhook_whitelist_file) as f:
                args.webhook_whitelist = frozenset(
                    [int(p_id.strip()) for p_id in f])
        elif args.webhook_blacklist_file:
            with open(args.webhook_blacklist_file) as f:
                args.webhook_blacklist = frozenset(
                    [int(p_id.strip()) for p_id in f])
        else:
            args.webhook_blacklist = frozenset(
                [int(i) for i in args.webhook_blacklist])
            args.webhook_whitelist = frozenset(
                [int(i) for i in args.webhook_whitelist])

        # create an empty set
        args.ignorelist = []
        if args.ignorelist_file:
            with open(args.ignorelist_file) as f:
                args.ignorelist = frozenset([int(l.strip()) for l in f])

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
            args.wh_types = frozenset()
        else:
            args.wh_types = frozenset([i for i in args.wh_types])

    args.locales_dir = 'static/dist/locales'
    args.data_dir = 'static/dist/data'
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


# Return the s2sphere cellid token from a location.
def cellid(loc):
    return CellId.from_lat_lng(LatLng.from_degrees(loc[0], loc[1])).to_token()


# Return approximate distance in meters.
def distance(pos1, pos2):
    return haversine((tuple(pos1))[0:2], (tuple(pos2))[0:2])


# Return True if distance between two locs is less than distance in meters.
def in_radius(loc1, loc2, radius):
    return distance(loc1, loc2) < radius


def i8ln(word):
    if not hasattr(i8ln, 'dictionary'):
        args = get_args()
        file_path = os.path.join(
            args.root_path,
            args.locales_dir,
            '{}.min.json'.format(args.locale))
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                i8ln.dictionary = json.loads(f.read())
        else:
            # If locale file is not found we set an empty dict to avoid
            # checking the file every time, we skip the warning for English as
            # it is not expected to exist.
            if not args.locale == 'en':
                log.warning(
                    'Skipping translations - unable to find locale file: %s',
                    file_path)
            i8ln.dictionary = {}
    if word in i8ln.dictionary:
        return i8ln.dictionary[word]
    else:
        return word


def get_pokemon_data(pokemon_id):
    if not hasattr(get_pokemon_data, 'pokemon'):
        args = get_args()
        file_path = os.path.join(
            args.root_path,
            args.data_dir,
            'pokemon.min.json')

        with open(file_path, 'r') as f:
            get_pokemon_data.pokemon = json.loads(f.read())
    return get_pokemon_data.pokemon[str(pokemon_id)]


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
        args = get_args()
        file_path = os.path.join(
            args.root_path,
            args.data_dir,
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
    move_type = get_moves_data(move_id)['type']
    return {'type': i8ln(move_type), 'type_en': move_type}


def dottedQuadToNum(ip):
    return struct.unpack("!L", socket.inet_aton(ip))[0]


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
           'iPhone9,4': 'D111AP',
           'iPhone10,1': 'D20AP',
           'iPhone10,2': 'D21AP',
           'iPhone10,3': 'D22AP',
           'iPhone10,4': 'D201AP',
           'iPhone10,5': 'D211AP',
           'iPhone10,6': 'D221AP'}


def generate_device_info(identifier):
    md5 = hashlib.md5()
    md5.update(identifier)
    pick_hash = int(md5.hexdigest(), 16)

    device_info = {'device_brand': 'Apple', 'device_model': 'iPhone',
                   'hardware_manufacturer': 'Apple',
                   'firmware_brand': 'iPhone OS'}
    devices = tuple(IPHONES.keys())

    ios9 = ('9.0', '9.0.1', '9.0.2', '9.1', '9.2', '9.2.1', '9.3', '9.3.1',
            '9.3.2', '9.3.3', '9.3.4', '9.3.5')
    # 10.0 was only for iPhone 7 and 7 Plus, and is rare.
    ios10 = ('10.0.1', '10.0.2', '10.0.3', '10.1', '10.1.1', '10.2', '10.2.1',
             '10.3', '10.3.1', '10.3.2', '10.3.3')
    ios11 = ('11.0.1', '11.0.2', '11.0.3', '11.1', '11.1.1', '11.1.2')

    device_pick = devices[pick_hash % len(devices)]
    device_info['device_model_boot'] = device_pick
    device_info['hardware_model'] = IPHONES[device_pick]
    device_info['device_id'] = md5.hexdigest()

    if device_pick in ('iPhone10,1', 'iPhone10,2', 'iPhone10,3',
                       'iPhone10,4', 'iPhone10,5', 'iPhone10,6'):
        # iPhone 8/8+ and X started on 11.
        ios_pool = ios11
    elif device_pick in ('iPhone9,1', 'iPhone9,2', 'iPhone9,3', 'iPhone9,4'):
        # iPhone 7/7+ started on 10.
        ios_pool = ios10 + ios11
    elif device_pick == 'iPhone8,4':
        # iPhone SE started on 9.3.
        ios_pool = ('9.3', '9.3.1', '9.3.2', '9.3.3', '9.3.4', '9.3.5') \
                   + ios10 + ios11
    elif device_pick in ('iPhone5,1', 'iPhone5,2', 'iPhone5,3', 'iPhone5,4'):
        # iPhone 5/5c doesn't support iOS 11.
        ios_pool = ios9 + ios10
    else:
        ios_pool = ios9 + ios10 + ios11

    device_info['firmware_type'] = ios_pool[pick_hash % len(ios_pool)]
    return device_info


def calc_pokemon_level(cp_multiplier):
    if cp_multiplier < 0.734:
        pokemon_level = (58.35178527 * cp_multiplier * cp_multiplier -
                         2.838007664 * cp_multiplier + 0.8539209906)
    else:
        pokemon_level = 171.0112688 * cp_multiplier - 95.20425243
    pokemon_level = int((round(pokemon_level) * 2) / 2)
    return pokemon_level


@memoize
def gmaps_reverse_geolocate(gmaps_key, locale, location):
    # Find the reverse geolocation
    geolocator = GoogleV3(api_key=gmaps_key)

    player_locale = {
        'country': 'US',
        'language': locale,
        'timezone': 'America/Denver'
    }

    try:
        reverse = geolocator.reverse(location)
        address = reverse[-1].raw['address_components']
        country_code = 'US'

        # Find country component.
        for component in address:
            # Look for country.
            component_is_country = any([t == 'country'
                                        for t in component.get('types', [])])

            if component_is_country:
                country_code = component['short_name']
                break

        try:
            timezone = geolocator.timezone(location)
            player_locale.update({
                'country': country_code,
                'timezone': str(timezone)
            })
        except Exception as e:
            log.exception('Exception on Google Timezone API. '
                          + 'Please check that you have Google Timezone API'
                          + ' enabled for your API key'
                          + ' (https://developers.google.com/maps/'
                          + 'documentation/timezone/intro): %s.', e)
    except Exception as e:
        log.exception('Exception while obtaining player locale: %s.'
                      + ' Using default locale.', e)

    return player_locale


# Get a future_requests FuturesSession that supports asynchronous workers
# and retrying requests on failure.
# Setting up a persistent session that is re-used by multiple requests can
# speed up requests to the same host, as it'll re-use the underlying TCP
# connection.
def get_async_requests_session(num_retries, backoff_factor, pool_size,
                               status_forcelist=None):
    # Use requests & urllib3 to auto-retry.
    # If the backoff_factor is 0.1, then sleep() will sleep for [0.1s, 0.2s,
    # 0.4s, ...] between retries. It will also force a retry if the status
    # code returned is in status_forcelist.
    if status_forcelist is None:
        status_forcelist = [500, 502, 503, 504]
    session = FuturesSession(max_workers=pool_size)

    # If any regular response is generated, no retry is done. Without using
    # the status_forcelist, even a response with status 500 will not be
    # retried.
    retries = Retry(total=num_retries, backoff_factor=backoff_factor,
                    status_forcelist=status_forcelist)

    # Mount handler on both HTTP & HTTPS.
    session.mount('http://', HTTPAdapter(max_retries=retries,
                                         pool_connections=pool_size,
                                         pool_maxsize=pool_size))
    session.mount('https://', HTTPAdapter(max_retries=retries,
                                          pool_connections=pool_size,
                                          pool_maxsize=pool_size))

    return session


# Get common usage stats.
def resource_usage():
    platform = sys.platform
    proc = psutil.Process()

    with proc.oneshot():
        cpu_usage = psutil.cpu_times_percent()
        mem_usage = psutil.virtual_memory()
        net_usage = psutil.net_io_counters()

        usage = {
            'platform': platform,
            'PID': proc.pid,
            'MEM': {
                'total': mem_usage.total,
                'available': mem_usage.available,
                'used': mem_usage.used,
                'free': mem_usage.free,
                'percent_used': mem_usage.percent,
                'process_percent_used': proc.memory_percent()
            },
            'CPU': {
                'user': cpu_usage.user,
                'system': cpu_usage.system,
                'idle': cpu_usage.idle,
                'process_percent_used': proc.cpu_percent(interval=1)
            },
            'NET': {
                'bytes_sent': net_usage.bytes_sent,
                'bytes_recv': net_usage.bytes_recv,
                'packets_sent': net_usage.packets_sent,
                'packets_recv': net_usage.packets_recv,
                'errin': net_usage.errin,
                'errout': net_usage.errout,
                'dropin': net_usage.dropin,
                'dropout': net_usage.dropout
            },
            'connections': {
                'ipv4': len(proc.connections('inet4')),
                'ipv6': len(proc.connections('inet6'))
            },
            'thread_count': proc.num_threads(),
            'process_count': len(psutil.pids())
        }

        # Linux only.
        if platform == 'linux' or platform == 'linux2':
            usage['sensors'] = {
                'temperatures': psutil.sensors_temperatures(),
                'fans': psutil.sensors_fans()
            }
            usage['connections']['unix'] = len(proc.connections('unix'))
            usage['num_handles'] = proc.num_fds()
        elif platform == 'win32':
            usage['num_handles'] = proc.num_handles()

    return usage


# Log resource usage to any logger.
def log_resource_usage(log_method):
    usage = resource_usage()
    log_method('Resource usage: %s.', usage)


# Generic method to support periodic background tasks. Thread sleep could be
# replaced by a tiny sleep, and time measuring, but we're using sleep() for
# now to keep resource overhead to an absolute minimum.
def periodic_loop(f, loop_delay_ms):
    while True:
        # Do the thing.
        f()
        # zZz :bed:
        time.sleep(loop_delay_ms / 1000)


# Periodically log resource usage every 'loop_delay_ms' ms.
def log_resource_usage_loop(loop_delay_ms=60000):
    # Helper method to log to specific log level.
    def log_resource_usage_to_debug():
        log_resource_usage(log.debug)

    periodic_loop(log_resource_usage_to_debug, loop_delay_ms)


# Return shell call output as string, replacing any errors with the
# error's string representation.
def check_output_catch(command):
    try:
        result = subprocess.check_output(command,
                                         stderr=subprocess.STDOUT,
                                         shell=True)
    except Exception as ex:
        result = 'ERROR: ' + ex.output.replace(os.linesep, ' ')
    finally:
        return result.strip()


# Automatically censor all necessary fields. Lists will return
# their length, all other items will return 'censored_tag'.
def _censor_args_namespace(args, censored_tag):
    fields_to_censor = [
        'accounts',
        'accounts_L30',
        'username',
        'password',
        'auth_service',
        'proxy',
        'webhooks',
        'webhook_blacklist',
        'webhook_whitelist',
        'config',
        'accountcsv',
        'high_lvl_accounts',
        'geofence_file',
        'geofence_excluded_file',
        'ignorelist_file',
        'enc_whitelist_file',
        'webhook_whitelist_file',
        'webhook_blacklist_file',
        'db',
        'proxy_file',
        'log_path',
        'encrypt_lib',
        'ssl_certificate',
        'ssl_privatekey',
        'location',
        'captcha_key',
        'captcha_dsk',
        'manual_captcha_domain',
        'host',
        'port',
        'gmaps_key',
        'db_name',
        'db_user',
        'db_pass',
        'db_host',
        'db_port',
        'status_name',
        'status_page_password',
        'hash_key',
        'trusted_proxies'
    ]

    for field in fields_to_censor:
        # Do we have the field?
        if field in args:
            value = args[field]

            # Replace with length of list or censored tag.
            if isinstance(value, list):
                args[field] = len(value)
            else:
                args[field] = censored_tag

    return args


# Get censored debug info about the environment we're running in.
def get_censored_debug_info():
    CENSORED_TAG = '<censored>'
    args = _censor_args_namespace(vars(get_args()), CENSORED_TAG)

    # Get git status.
    status = check_output_catch('git status')
    log = check_output_catch('git log -1')
    remotes = check_output_catch('git remote -v')

    # Python, pip, node, npm.
    python = sys.version.replace(os.linesep, ' ').strip()
    pip = check_output_catch('pip -V')
    node = check_output_catch('node -v')
    npm = check_output_catch('npm -v')

    return {
        'args': args,
        'git': {
            'status': status,
            'log': log,
            'remotes': remotes
        },
        'versions': {
            'python': python,
            'pip': pip,
            'node': node,
            'npm': npm
        }
    }


# Post a string of text to a hasteb.in and retrieve the URL.
def upload_to_hastebin(text):
    log.info('Uploading info to hastebin.com...')
    response = requests.post('https://hastebin.com/documents', data=text)
    return response.json()['key']


# Get censored debug info & auto-upload to hasteb.in.
def get_debug_dump_link():
    debug = get_censored_debug_info()
    args = debug['args']
    git = debug['git']
    versions = debug['versions']

    # Format debug info for text upload.
    result = '''#######################
### RocketMap debug ###
#######################

## Versions:
'''

    # Versions first, for readability.
    result += '- Python: ' + versions['python'] + '\n'
    result += '- pip: ' + versions['pip'] + '\n'
    result += '- Node.js: ' + versions['node'] + '\n'
    result += '- npm: ' + versions['npm'] + '\n'

    # Next up is git.
    result += '\n\n' + '## Git:' + '\n'
    result += git['status'] + '\n'
    result += '\n\n' + git['remotes'] + '\n'
    result += '\n\n' + git['log'] + '\n'

    # And finally, our censored args.
    result += '\n\n' + '## Settings:' + '\n'
    result += pformat(args, width=1)

    # Upload to hasteb.in.
    return upload_to_hastebin(result)
