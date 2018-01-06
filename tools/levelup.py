#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import logging
import time

from threading import Thread
from queue import Queue, Empty

sys.path.append('.')
from pogom.schedulers import KeyScheduler  # noqa: E402
from pogom.account import (check_login, setup_api, pokestop_spinnable,
                           spin_pokestop)  # noqa: E402
from pogom.utils import get_args, gmaps_reverse_geolocate  # noqa: E402
from pogom.apiRequests import get_map_objects as gmo  # noqa: E402
from runserver import (set_log_and_verbosity, startup_db,
                       extract_coordinates)  # noqa: E402
from pogom.proxy import initialize_proxies  # noqa: E402
from pogom.models import PlayerLocale  # noqa: E402


class FakeQueue:

    def put(self, something):
        pass


def get_location_forts(api, account, location):
    response = gmo(api, account, location)
    cells = response['responses']['GET_MAP_OBJECTS'].map_cells
    forts = []
    for i, cell in enumerate(cells):
        forts += cell.forts
    return forts


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
            log.info('Account %s level %d', account['username'],
                     account['level'])
            forts = get_location_forts(api, account, location)
            log.info('%d stops in range', len(forts))
            for fort in forts:
                if pokestop_spinnable(fort, location):
                    spin_pokestop(api, account, args, fort, location)
            log.info('Ended with account %s', account['username'])
            log.info('Account %s level %d', account['username'],
                     account['level'])
        except Exception as e:
            if error_count < 2:
                log.exception('Exception in worker: %s retrying.', e)
                accounts.put((account, error_count+1))
            else:
                errors.append(account)

        accounts.task_done()


log = logging.getLogger()
set_log_and_verbosity(log)


args = get_args()
fake_queue = FakeQueue()
key_scheduler = KeyScheduler(args.hash_key, fake_queue)
position = extract_coordinates(args.location)
startup_db(None, args.clear_db, args.db_type, args.db)
args.player_locale = PlayerLocale.get_locale(args.location)
if not args.player_locale:
    args.player_locale = gmaps_reverse_geolocate(
        args.gmaps_key,
        args.locale,
        str(position[0]) + ', ' + str(position[1]))

initialize_proxies(args)
account_queue = Queue()
errors = []

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
if len(errors) > 0:
    log.info('Some accounts did not finish properly:')
    for account in errors:
        log.info('\t%s', account['username'])
