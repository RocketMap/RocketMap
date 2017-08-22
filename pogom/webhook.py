#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import requests
import threading
from cachetools import LFUCache
from timeit import default_timer
from .utils import get_async_requests_session

log = logging.getLogger(__name__)

wh_lock = threading.Lock()


def send_to_webhooks(args, session, message_frame):
    if not args.webhooks:
        # What are you even doing here...
        log.warning('Called send_to_webhook() without webhooks.')
        return

    req_timeout = args.wh_timeout

    for w in args.webhooks:
        try:
            # Disable keep-alive and set streaming to True, so we can skip
            # the response content.
            session.post(w, json=message_frame,
                         timeout=(None, req_timeout),
                         background_callback=__wh_completed,
                         headers={'Connection': 'close'},
                         stream=True)
        except requests.exceptions.ReadTimeout:
            log.exception('Response timeout on webhook endpoint %s.', w)
        except requests.exceptions.RequestException as e:
            log.exception(e)


def wh_updater(args, queue, key_caches):
    wh_threshold_timer = default_timer()
    wh_over_threshold = False

    # Set up one session to use for all requests.
    # Requests to the same host will reuse the underlying TCP
    # connection, giving a performance increase.
    session = get_async_requests_session(
        args.wh_retries,
        args.wh_backoff_factor,
        args.wh_concurrency)

    # Extract the proper identifier. This list also controls which message
    # types are getting cached.
    ident_fields = {
        'pokestop': 'pokestop_id',
        'pokemon': 'encounter_id',
        'gym': 'gym_id',
        'gym_details': 'id',
        'raid': 'gym_id'
    }

    # Instantiate WH LFU caches for all cached types. We separate the caches
    # by ident_field types, because different ident_field (message) types can
    # use the same name for their ident field.
    for key in ident_fields:
        key_caches[key] = LFUCache(maxsize=args.wh_lfu_size)

    # Prepare to send data per timed message frames instead of per object.
    frame_interval_sec = (args.wh_frame_interval / 1000)
    frame_first_message_time_sec = default_timer()
    frame_messages = []
    first_message = True

    # How low do we want the queue size to stay?
    wh_warning_threshold = 100
    # How long can it be over the threshold, in seconds?
    # Default: 5 seconds per 100 in threshold + frame_interval_sec.
    wh_threshold_lifetime = int(5 * (wh_warning_threshold / 100.0))
    wh_threshold_timer += frame_interval_sec

    # The forever loop.
    while True:
        try:
            # Loop the queue.
            whtype, message = queue.get()

            frame_message = {
                'type': whtype,
                'message': message
            }

            # Get the proper cache if this type has one.
            key_cache = None

            if whtype in key_caches:
                key_cache = key_caches[whtype]

            # Get the unique identifier to check our cache, if it has one.
            ident = message.get(ident_fields.get(whtype), None)

            # cachetools in Python2.7 isn't thread safe, so we add a lock.
            with wh_lock:
                # Only send if identifier isn't already in cache.
                if ident is None or key_cache is None:
                    # We don't know what it is, or it doesn't have a cache,
                    # so let's just log and send as-is.
                    log.debug(
                        'Queued webhook item of uncached type: %s.', whtype)
                    frame_messages.append(frame_message)
                elif ident not in key_cache:
                    key_cache[ident] = message
                    log.debug('Queued %s to webhook: %s.', whtype, ident)
                    frame_messages.append(frame_message)
                else:
                    # Make sure to call key_cache[ident] in all branches so it
                    # updates the LFU usage count.

                    # If the object has changed in an important way, send new
                    # data to webhooks.
                    if __wh_object_changed(whtype, key_cache[ident], message):
                        key_cache[ident] = message
                        frame_messages.append(frame_message)
                        log.debug('Queued updated %s to webhook: %s.',
                                  whtype, ident)
                    else:
                        log.debug('Not queuing %s to webhook: %s.',
                                  whtype, ident)

            # Store the time when we added the first message instead of the
            # time when we last cleared the messages, so we more accurately
            # measure time spent getting messages from our queue.
            now = default_timer()
            num_messages = len(frame_messages)

            if num_messages == 1 and first_message:
                frame_first_message_time_sec = now
                first_message = False

            # If enough time has passed, send the message frame.
            time_passed_sec = now - frame_first_message_time_sec

            if num_messages > 0 and (time_passed_sec >
                                     frame_interval_sec):
                log.debug('Sending %d items to %d webhook(s).',
                          num_messages,
                          len(args.webhooks))
                send_to_webhooks(args, session, frame_messages)

                frame_messages = []
                first_message = True

            # Webhook queue moving too slow.
            if (not wh_over_threshold) and (
                    queue.qsize() > wh_warning_threshold):
                wh_over_threshold = True
                wh_threshold_timer = default_timer()
            elif wh_over_threshold:
                if queue.qsize() < wh_warning_threshold:
                    wh_over_threshold = False
                else:
                    timediff_sec = default_timer() - wh_threshold_timer

                    if timediff_sec > wh_threshold_lifetime:
                        log.warning('Webhook queue has been > %d (@%d);'
                                    + ' for over %d seconds,'
                                    + ' try increasing --wh-concurrency'
                                    + ' or --wh-threads.',
                                    wh_warning_threshold,
                                    queue.qsize(),
                                    wh_threshold_lifetime)

            queue.task_done()
        except Exception as e:
            log.exception('Exception in wh_updater: %s.', e)


# Helpers

# Background handler for completed webhook requests.
def __wh_completed(sess, resp):
    # Instantly close the response to release the connection back to the pool.
    resp.close()


def __get_key_fields(whtype):
    key_fields = {
        # lure_expiration is a UTC timestamp so it's good (Y).
        'pokestop': [
            'enabled', 'latitude', 'longitude', 'lure_expiration',
            'active_fort_modifier'
        ],
        'pokemon': [
            'spawnpoint_id', 'pokemon_id', 'latitude', 'longitude',
            'disappear_time', 'move_1', 'move_2', 'individual_stamina',
            'individual_defense', 'individual_attack', 'form', 'cp',
            'pokemon_level'
        ],
        'gym': [
            'team_id', 'guard_pokemon_id', 'enabled', 'latitude', 'longitude',
            'raid_active_until', 'occupied_since', 'total_cp',
            'slots_available'
        ],
        'gym_details': ['latitude', 'longitude', 'team', 'pokemon'],
        'raid': [
            'spawn', 'start', 'end', 'pokemon_id', 'latitude', 'longitude'
        ]
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
