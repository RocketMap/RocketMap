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
            log.exception(repr(e))


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
            ident = message.get(ident_fields.get(whtype), None)

            # cachetools in Python2.7 isn't thread safe, but adding a Lock
            # slows down the queue immensely. Rather than being entirely
            # thread safe, we catch the rare exception and re-add to queue.
            try:
                # Only send if identifier isn't already in cache.
                if ident is None:
                    # We don't know what it is, so let's just log and send
                    # as-is.
                    log.debug(
                        'Sending webhook item of unknown type: %s.', whtype)
                    send_to_webhook(whtype, message)
                elif ident not in key_cache:
                    key_cache[ident] = message
                    log.debug('Sending %s to webhook: %s.', whtype, ident)
                    send_to_webhook(whtype, message)
                else:
                    # Make sure to call key_cache[ident] in all branches so it
                    # updates the LFU usage count.

                    # If the object has changed in an important way, send new
                    # data to webhooks.
                    if __wh_object_changed(whtype, key_cache[ident], message):
                        key_cache[ident] = message
                        send_to_webhook(whtype, message)
                        log.debug('Sending updated %s to webhook: %s.',
                                  whtype, ident)
                    else:
                        log.debug('Not resending %s to webhook: %s.',
                                  whtype, ident)
            except KeyError as ex:
                log.debug(
                    'LFUCache thread unsafe exception: %s. Requeuing.',
                    repr(ex))
                queue.put((whtype, message))

            # Webhook queue moving too slow.
            if queue.qsize() > 50:
                log.warning('Webhook queue is > 50 (@%d); ' +
                            'try increasing --wh-threads.',
                            queue.qsize())

            queue.task_done()
        except Exception as e:
            log.exception('Exception in wh_updater: %s.', repr(e))


# Helpers

def __get_key_fields(whtype):
    key_fields = {
        # lure_expiration is a UTC timestamp so it's good (Y).
        'pokestop': ['enabled', 'latitude',
                     'longitude', 'lure_expiration', 'active_fort_modifier'],
        'pokemon': ['spawnpoint_id', 'pokemon_id', 'latitude', 'longitude',
                    'disappear_time', 'move_1', 'move_2',
                    'individual_stamina', 'individual_defense',
                    'individual_attack'],
        'gym': ['team_id', 'guard_pokemon_id',
                'gym_points', 'enabled', 'latitude', 'longitude']
    }

    return key_fields.get(whtype, [])


# Determine if a webhook object has changed in any important way (and
# requires a resend).
def __wh_object_changed(whtype, old, new):
    # Only test for important fields: don't trust last_modified fields.
    fields = __get_key_fields(whtype)

    if not fields:
        log.debug('Received an object of unknown type %s.', whtype)
        return True

    return not __dict_fields_equal(fields, old, new)


# Determine if two dicts have equal values for all keys in a list.
def __dict_fields_equal(keys, a, b):
    for k in keys:
        if a.get(k) != b.get(k):
            return False

    return True
