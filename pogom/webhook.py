#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import requests
from .utils import get_args

log = logging.getLogger(__name__)


def send_to_webhook(message_type, message):
    args = get_args()

    if not args.webhooks:
        # what are you even doing here...
        return

    data = {
        'type': message_type,
        'message': message
    }

    for w in args.webhooks:
        try:
            requests.post(w, json=data, timeout=(None, 1))
        except requests.exceptions.ReadTimeout:
            log.debug('Response timeout on webhook endpoint %s', w)
        except requests.exceptions.RequestException as e:
            log.debug(e)


def wh_updater(args, q):
    # The forever loop
    while True:
        try:
            # Loop the queue
            while True:
                whtype, message = q.get()
                send_to_webhook(whtype, message)
                if q.qsize() > 50:
                    log.warning("Webhook queue is > 50 (@%d); try increasing --wh-threads", q.qsize())
                q.task_done()
        except Exception as e:
            log.exception('Exception in wh_updater: %s', e)
