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


def wh_updater(args, q):
    # The forever loop.
    while True:
        try:
            # Loop the queue.
            while True:
                whtype, message = q.get()
                send_to_webhook(whtype, message)

                if q.qsize() > 50:
                    log.warning(
                        'Webhook queue is > 50 (@%d); try increasing --wh-threads.', q.qsize())

                q.task_done()
        except Exception as e:
            log.exception('Exception in wh_updater: %s.', e)
