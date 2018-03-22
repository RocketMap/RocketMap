#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import random
import logging

from .utils import get_args
from .proxy import get_new_proxy

from pgoapi.hash_server import HashServer
from pgoapi.exceptions import (HashingQuotaExceededException,
                               ServerSideRequestThrottlingException,
                               NianticThrottlingException,
                               HashingOfflineException,
                               HashingTimeoutException)

log = logging.getLogger(__name__)


class PGoRequestWrapper:

    def __init__(self, request):
        log.debug('Wrapped PGoApiRequest.')
        self.args = get_args()

        self.request = request
        self.retries = self.args.api_retries

    def __getattr__(self, attr):
        orig_attr = getattr(self.request, attr)

        if callable(orig_attr):
            def hooked(*args, **kwargs):
                result = orig_attr(*args, **kwargs)
                # Prevent wrapped class from becoming unwrapped.
                if result == self.request:
                    return self
                return result
            return hooked
        else:
            return orig_attr

    def call(self, *args, **kwargs):
        # Retry x times on failure.
        retries_left = self.retries

        while retries_left > 0:
            # If reduce_retries = True, we expect exception_name to be set.
            reduce_retries = False
            rotate_proxy = False
            exception_name = ''

            try:
                log.debug('Sending wrapped API request.')
                return self.request.call(*args, **kwargs)
            except HashingQuotaExceededException:
                # Default = sleep for a little bit, then retry.
                random_sleep_secs = random.uniform(0.75, 1.5)
                secs_to_sleep = random_sleep_secs

                # Sleep until the RPM reset to free some RPM and don't use
                # one of our retries, just retry until we have RPM left.
                # If RPM reset was in the past, we'll still sleep for a
                # little bit to introduce variation.
                if self.args.hash_header_sleep:
                    now = int(time.time())
                    rpm_reset = HashServer.status.get('period', now)
                    secs_till_reset = rpm_reset - now

                    # Could be outdated key header, or already passed.
                    if secs_till_reset > 0:
                        secs_to_sleep = secs_till_reset + random_sleep_secs

                # Don't be too enthusiastic about sleeping. Failsafe against a
                # bugged header, timezone problems, ...
                secs_to_sleep = min(secs_to_sleep, 60)

                # Shhhhhh. Only happy dreams now.
                log.debug('Hashing quota exceeded. If this delays requests for'
                          ' too long, consider adding more RPM. Sleeping for'
                          ' %ss before retrying...', secs_to_sleep)
                time.sleep(secs_to_sleep)
            except (ServerSideRequestThrottlingException,
                    NianticThrottlingException) as ex:
                # Raised when too many requests were made in a short period.
                # Sleep a bit.
                reduce_retries = True
                rotate_proxy = True
                exception_name = type(ex).__name__
                time.sleep(random.uniform(0.75, 1.5))
            except (HashingOfflineException, HashingTimeoutException) as ex:
                # Hashing server issues. Make sure we sleep a minimum.
                reduce_retries = True
                rotate_proxy = True
                exception_name = type(ex).__name__
                time.sleep(random.uniform(0.75, 1.5))
            except Exception as ex:
                reduce_retries = True
                rotate_proxy = True
                exception_name = type(ex).__name__

            if reduce_retries and retries_left > 0:
                plural = 'retries' if retries_left > 1 else 'retry'
                log.debug('API request failed with exception type %s.'
                          ' Retrying w/ %s %s left...',
                          exception_name,
                          retries_left,
                          plural)
                retries_left -= 1

            # Rotate proxy. Not necessary on
            # HashingQuotaExceededException, because it's proof that
            # the proxy worked. The variable "rotate_proxy" may seem
            # unnecessary, but it's here for readability and avoiding problems
            # in the future.
            if rotate_proxy and self.args.proxy:
                proxy_idx, proxy_url = get_new_proxy(get_args())

                if proxy_url:
                    log.debug('Changed to proxy: %s.', proxy_url)
                    proxy_config = {
                        'http': proxy_url,
                        'https': proxy_url
                    }
                    parent = self.request.__parent__
                    parent.set_proxy(proxy_config)
                    parent._auth_provider.set_proxy(proxy_config)

        # If we've reached here, we have no retries left and an exception
        # still occurred.
        raise
