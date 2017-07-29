#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import random
import logging

from .utils import get_args
from .proxy import get_new_proxy

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
                # Sleep a minimum to free some RPM and don't use one of our
                # retries, just retry until we have RPM left.
                time.sleep(random.uniform(0.75, 1.5))
                log.debug('Hashing quota exceeded. If this delays requests for'
                          ' too long, consider adding more RPM. Retrying...')
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
