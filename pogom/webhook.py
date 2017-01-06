#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import requests
from .utils import get_args
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

log = logging.getLogger(__name__)


def send_to_webhook(message_type, message):
    args = get_args()

    if not args.webhooks:
        # What are you even doing here...
        log.warning('Called send_to_webhook() without webhooks.')
        return

    # Config / arg parser
    num_retries = args.wh_retries
    req_timeout = args.wh_timeout
    backoff_factor = args.wh_backoff_factor

    # Use requests & urllib3 to auto-retry.
    # If the backoff_factor is 0.1, then sleep() will sleep for [0.1s, 0.2s,
    # 0.4s, ...] between retries. It will also force a retry if the status
    # code returned is 500, 502, 503 or 504.
    session = requests.Session()

    # If any regular response is generated, no retry is done. Without using
    # the status_forcelist, even a response with status 500 will not be
    # retried.
    retries = Retry(total=num_retries, backoff_factor=backoff_factor,
                    status_forcelist=[500, 502, 503, 504])

    # Mount handler on both HTTP & HTTPS.
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    data = {
        'type': message_type,
        'message': message
    }

    for w in args.webhooks:
        try:
            session.post(w, json=data, timeout=(None, req_timeout))
        except requests.exceptions.ReadTimeout:
            log.exception('Response timeout on webhook endpoint %s.', w)
        except requests.exceptions.RequestException as e:
            log.exception(e)


def wh_updater(args, queue, key_cache):
    # The forever loop.
    while True:
        try:
            # Loop the queue.
            whtype, message = queue.get()

            # Extract the proper identifier.
            ident_fields = {
                'pokestop': 'pokestop_id',
                'pokemon': 'encounter_id',
                'gym': 'gym_id'
            }
            ident = message.get(ident_fields.get(whtype))

            # Only send if identifier isn't already in cache.
            if ident is None:
                log.warning(
                    'Trying to send webhook item of invalid type: %s.', whtype)
            elif ident not in key_cache:
                key_cache[ident] = 1
                log.debug('Sending %s to webhook: %s.', whtype, ident)
                send_to_webhook(whtype, message)
            else:
                # Make sure to call key_cache[ident] so it updates the LFU
                # usage count. We just use it as a count for now, can come in
                # useful for stats/debugging later.
                key_cache[ident] = key_cache[ident] + 1
                log.debug('Not resending %s to webhook: %s.', whtype, ident)

            # Webhook queue moving too slow.
            if queue.qsize() > 50:
                log.warning(
                    'Webhook queue is > 50 (@%d); try increasing --wh-threads.', queue.qsize())

            queue.task_done()
        except Exception as e:
            log.exception('Exception in wh_updater: %s.', e)
