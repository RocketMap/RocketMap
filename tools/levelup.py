#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import logging
import time

from threading import Thread
from queue import Queue, Empty
from enum import Enum

sys.path.append('.')
from pogom.schedulers import KeyScheduler  # noqa: E402
from pogom.account import (check_login, setup_api, pokestop_spinnable,
                           spin_pokestop, TooManyLoginAttempts)  # noqa: E402
from pogom.utils import get_args, gmaps_reverse_geolocate  # noqa: E402
from pogom.apiRequests import (get_map_objects as gmo,
                               AccountBannedException)  # noqa: E402
from runserver import (set_log_and_verbosity, startup_db,
                       extract_coordinates)  # noqa: E402
from pogom.proxy import initialize_proxies  # noqa: E402
from pogom.models import PlayerLocale  # noqa: E402


class FakeQueue:

    def put(self, something):
        pass


class ErrorType(Enum):
    generic = 1
    captcha = 2
    no_stops = 3
    banned = 4
    login_error = 5


def get_location_forts(api, account, location):
    response = gmo(api, account, location)
    if len(response['responses']['CHECK_CHALLENGE'].challenge_url) > 1:
        log.error('account: %s got captcha: %s', account['username'],
                  response['responses']['CHECK_CHALLENGE'].challenge_url)
        return (ErrorType.captcha, None)
    cells = response['responses']['GET_MAP_OBJECTS'].map_cells
    forts = []
    for i, cell in enumerate(cells):
        forts += cell.forts
    if not forts:
        return (ErrorType.no_stops, None)
    return (None, forts)


def level_up_account(args, location, accounts, errors):
    while True:
        try:
            # Loop the queue.
            try:
                (account, error_count) = accounts.get(False)
            except Empty:
                break

            log.info('Starting account %s', account['username'])
            status = {
                'type': 'Worker',
                'message': 'Creating thread...',
                'success': 0,
                'fail': 0,
                'noitems': 0,
                'skip': 0,
                'captcha': 0,
                'username': '',
                'proxy_display': None,
                'proxy_url': None,
            }
            api = setup_api(args, status, account)
            api.set_position(*location)
            key = key_scheduler.next()
            api.activate_hash_server(key)
            check_login(args, account, api, status['proxy_url'])
            log.info('Account %s, level %d.', account['username'],
                     account['level'])
            (error, forts) = get_location_forts(api, account, location)
            if error:
                errors[error].append(account)
                accounts.task_done()
                continue
            log.info('%d stops in range', len(forts))
            for fort in forts:
                if pokestop_spinnable(fort, location):
                    spin_pokestop(api, account, args, fort, location)
            log.info('Ended with account %s.', account['username'])
            log.info('Account %s, level %d.', account['username'],
                     account['level'])
        except TooManyLoginAttempts:
            errors[ErrorType.login_error].append(account)
        except AccountBannedException:
            errors[ErrorType.banned].append(account)
        except Exception as e:
            if error_count < 2:
                log.exception('Exception in worker: %s. retrying.', e)
                accounts.put((account, error_count+1))
            else:
                errors[ErrorType.generic].append(account)

        accounts.task_done()


log = logging.getLogger()
set_log_and_verbosity(log)


args = get_args()

# Abort if we don't have a hash key set.
if not args.hash_key:
    log.critical('Hash key is required for leveling up accounts. Exiting.')
    sys.exit(1)

fake_queue = FakeQueue()
key_scheduler = KeyScheduler(args.hash_key, fake_queue)
position = extract_coordinates(args.location)
startup_db(None, args.clear_db)
args.player_locale = PlayerLocale.get_locale(args.location)
if not args.player_locale:
    args.player_locale = gmaps_reverse_geolocate(
        args.gmaps_key,
        args.locale,
        str(position[0]) + ', ' + str(position[1]))

initialize_proxies(args)
account_queue = Queue()
errors = {}
for error in ErrorType:
    errors[error] = []

for i, account in enumerate(args.accounts):
    account_queue.put((account, 0))

for i in range(0, args.workers):
    log.debug('Starting levelup worker thread %d...', i)
    t = Thread(target=level_up_account,
               name='worker-{}'.format(i),
               args=(args, position, account_queue, errors))
    t.daemon = True
    t.start()

try:
    while True:
        if account_queue.unfinished_tasks > 0:
            time.sleep(1)
        else:
            break
except KeyboardInterrupt:
    log.info('Process killed')
    exit(1)

account_queue.join()
log.info('Process finished')
for error_type in ErrorType:
    if len(errors[error_type]) > 0:
        log.warning('Some accounts did not finish properly (%s):',
                    error_type.name)
        for account in errors[error_type]:
            log.warning('\t%s', account['username'])
