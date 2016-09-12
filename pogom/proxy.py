#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import requests
import sys

from queue import Queue
from threading import Thread

log = logging.getLogger(__name__)


# Simple function to do a call to Niantic's system for testing proxy connectivity
def check_proxy(proxy_queue, timeout, proxies):

    # Update check url - Thanks ChipWolf #1282 and #1281
    proxy_test_url = 'https://pgorelease.nianticlabs.com/plfe/rpc'
    proxy = proxy_queue.get()

    if proxy and proxy[1]:

        log.debug('Checking proxy: %s', proxy[1])

        try:
            proxy_response = requests.post(proxy_test_url, '', proxies={'http': proxy[1], 'https': proxy[1]}, timeout=timeout)

            if proxy_response.status_code == 200:
                log.debug('Proxy %s is ok', proxy[1])
                proxy_queue.task_done()
                proxies.append(proxy[1])
                return True

            elif proxy_response.status_code == 403:
                log.error("Proxy %s is banned - got status code: %s", proxy[1], str(proxy_response.status_code))
                return False

            else:
                proxy_error = "Wrong status code - " + str(proxy_response.status_code)

        except requests.ConnectTimeout:
            proxy_error = "Connection timeout (" + str(timeout) + " second(s) ) via proxy " + proxy[1]

        except requests.ConnectionError:
            proxy_error = "Failed to connect to proxy " + proxy[1]

        except Exception as e:
            proxy_error = e

    else:
            proxy_error = "Empty proxy server"

    log.warning('%s', proxy_error)
    proxy_queue.task_done()

    return False


# Check all proxies and return a working list with proxies
def check_proxies(args):

    proxy_queue = Queue()
    total_proxies = len(args.proxy)

    log.info('Checking %d proxies...', total_proxies)

    proxies = []

    for proxy in enumerate(args.proxy):
        proxy_queue.put(proxy)

        t = Thread(target=check_proxy,
                   name='check_proxy',
                   args=(proxy_queue, args.proxy_timeout, proxies))
        t.daemon = True
        t.start()

    # This is painfull but we need to wait here untill proxy_queue is completed so we have a working list of proxies
    proxy_queue.join()

    working_proxies = len(proxies)

    if working_proxies == 0:
        log.error('Proxy was configured but no working proxies was found! We are aborting!')
        sys.exit(1)
    else:
        log.info('Proxy check completed with %d working proxies of %d configured', working_proxies, total_proxies)
        return proxies
