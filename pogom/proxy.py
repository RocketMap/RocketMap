#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import requests
import sys
import time

from queue import Queue
from threading import Thread
from random import randint

log = logging.getLogger(__name__)

# Last used proxy for round-robin.
last_proxy = -1

# Proxy check result constants.
check_result_ok = 0
check_result_failed = 1
check_result_banned = 2
check_result_wrong = 3
check_result_timeout = 4
check_result_exception = 5
check_result_empty = 6
check_result_max = 6  # Should be equal to maximal return code.


# Simple function to do a call to Niantic's system for
# testing proxy connectivity.
def check_proxy(proxy_queue, timeout, proxies, show_warnings, check_results):

    # Url for proxy testing.
    proxy_test_url = 'https://pgorelease.nianticlabs.com/plfe/rpc'
    proxy_test_ptc_url = 'https://sso.pokemon.com/sso/oauth2.0/authorize?' \
                         'client_id=mobile-app_pokemon-go&redirect_uri=' \
                         'https%3A%2F%2Fwww.nianticlabs.com%2Fpokemongo' \
                         '%2Ferror'
    proxy = proxy_queue.get()

    check_result = check_result_ok

    if proxy and proxy[1]:

        log.debug('Checking proxy: %s', proxy[1])

        try:
            proxy_response = requests.post(proxy_test_url, '',
                                           proxies={'http': proxy[1],
                                                    'https': proxy[1]},
                                           timeout=timeout)

            proxy_response_ptc = requests.get(proxy_test_ptc_url, '',
                                              proxies={'http': proxy[1],
                                                       'https': proxy[1]},
                                              timeout=timeout,
                                              headers={'User-Agent':
                                                       'pokemongo/1 '
                                                       'CFNetwork/811.4.18 '
                                                       'Darwin/16.5.0',
                                                       'Host':
                                                       'sso.pokemon.com',
                                                       'X-Unity-Version':
                                                       '5.5.1f1'})

            niantic_status = proxy_response.status_code
            ptc_status = proxy_response_ptc.status_code

            banned_status_codes = [403, 409]

            if niantic_status == 200 and ptc_status == 200:
                log.debug('Proxy %s is ok.', proxy[1])
                proxy_queue.task_done()
                proxies.append(proxy[1])
                check_results[check_result_ok] += 1
                return True

            elif (niantic_status in banned_status_codes or
                  ptc_status in banned_status_codes):
                proxy_error = ("Proxy " + proxy[1] +
                               " is banned - got Niantic status code: " +
                               str(niantic_status) + ", PTC status code: " +
                               str(ptc_status))
                check_result = check_result_banned

            else:
                proxy_error = ("Wrong status codes - " + str(niantic_status) +
                               ", " + str(ptc_status))
                check_result = check_result_wrong

        except requests.ConnectTimeout:
            proxy_error = ("Connection timeout (" + str(timeout) +
                           " second(s) ) via proxy " + proxy[1])
            check_result = check_result_timeout

        except requests.ConnectionError:
            proxy_error = "Failed to connect to proxy " + proxy[1]
            check_result = check_result_failed

        except Exception as e:
            proxy_error = e
            check_result = check_result_exception

    else:
        proxy_error = "Empty proxy server."
        check_result = check_result_empty

    # Decrease output amount if there are lot of proxies.
    if show_warnings:
        log.warning('%s', repr(proxy_error))
    else:
        log.debug('%s', repr(proxy_error))
    proxy_queue.task_done()

    check_results[check_result] += 1
    return False


# Check all proxies and return a working list with proxies.
def check_proxies(args):

    source_proxies = []

    check_results = [0] * (check_result_max + 1)

    # Load proxies from the file. Override args.proxy if specified.
    if args.proxy_file is not None:
        log.info('Loading proxies from file.')

        with open(args.proxy_file) as f:
            for line in f:
                # Ignore blank lines and comment lines.
                if len(line.strip()) == 0 or line.startswith('#'):
                    continue
                source_proxies.append(line.strip())

        log.info('Loaded %d proxies.', len(source_proxies))

        if len(source_proxies) == 0:
            log.error('Proxy file was configured but ' +
                      'no proxies were loaded. Aborting.')
            sys.exit(1)
    else:
        source_proxies = args.proxy

    # No proxies - no cookies.
    if (source_proxies is None) or (len(source_proxies) == 0):
        log.info('No proxies are configured.')
        return None

    if args.proxy_skip_check:
        return source_proxies

    proxy_queue = Queue()
    total_proxies = len(source_proxies)

    log.info('Checking %d proxies...', total_proxies)
    if (total_proxies > 10):
        log.info('Enable "-v or -vv" to see checking details.')

    proxies = []

    for proxy in enumerate(source_proxies):
        proxy_queue.put(proxy)

        t = Thread(target=check_proxy,
                   name='check_proxy',
                   args=(proxy_queue, args.proxy_timeout, proxies,
                         total_proxies <= 10, check_results))
        t.daemon = True
        t.start()

    # This is painful but we need to wait here until proxy_queue is
    # completed so we have a working list of proxies.
    proxy_queue.join()

    working_proxies = len(proxies)

    if working_proxies == 0:
        log.error('Proxy was configured but no working ' +
                  'proxies were found. Aborting.')
        sys.exit(1)
    else:
        other_fails = (check_results[check_result_failed] +
                       check_results[check_result_wrong] +
                       check_results[check_result_exception] +
                       check_results[check_result_empty])
        log.info('Proxy check completed. Working: %d, banned: %d, ' +
                 'timeout: %d, other fails: %d of total %d configured.',
                 working_proxies, check_results[check_result_banned],
                 check_results[check_result_timeout],
                 other_fails,
                 total_proxies)
        return proxies


# Thread function for periodical proxy updating.
def proxies_refresher(args):

    while True:
        # Wait BEFORE refresh, because initial refresh is done at startup.
        time.sleep(args.proxy_refresh)

        try:
            proxies = check_proxies(args)

            if len(proxies) == 0:
                log.warning('No live proxies found. Using previous ones ' +
                            'until next round...')
                continue

            args.proxy = proxies
            log.info('Regular proxy refresh complete.')
        except Exception as e:
            log.exception('Exception while refresh proxies: %s', repr(e))


# Provide new proxy for a search thread.
def get_new_proxy(args):

    global last_proxy

    # If none/round - simply get next proxy.
    if ((args.proxy_rotation is None) or (args.proxy_rotation == 'none') or
            (args.proxy_rotation == 'round')):
        if last_proxy >= len(args.proxy) - 1:
            last_proxy = 0
        else:
            last_proxy = last_proxy + 1
        lp = last_proxy
    # If random - get random one.
    elif (args.proxy_rotation == 'random'):
        lp = randint(0, len(args.proxy) - 1)
    else:
        log.warning('Parameter -pxo/--proxy-rotation has wrong value. ' +
                    'Use only first proxy.')
        lp = 0

    return lp, args.proxy[lp]
