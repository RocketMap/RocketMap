#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import random
import logging

from .utils import get_args
from .proxy import get_new_proxy

from pgoapi.exceptions import HashingQuotaExceededException

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

    def do_call(self, retries_left, *args, **kwargs):
        try:
            log.debug('Sending API request w/ %d retries left.', retries_left)
            return self.request.call(*args, **kwargs)
        except HashingQuotaExceededException:
            # Sleep a minimum to free some RPM.
            time.sleep(random.uniform(0.75, 1.5))
        except:
            pass

        # If we've reached here, an exception was raised and the function
        # hasn't returned yet.

        # Try again if we have retries left.
        if retries_left > 0:
            if self.args.proxy:
                # Rotate proxy.
                proxy_idx, proxy_url = get_new_proxy(get_args())

                if proxy_url:
                    log.debug('Changed to proxy: %s.', proxy_url)
                    proxy_config = {'http': proxy_url, 'https': proxy_url}
                    parent = self.request.__parent__
                    parent.set_proxy(proxy_config)
                    parent._auth_provider.set_proxy(proxy_config)

            log.debug('API request failed. Retrying...')
            return self.do_call(retries_left - 1, *args, **kwargs)
        else:
            raise

    def call(self, *args, **kwargs):
        # Retry x times on failure.
        return self.do_call(self.retries, *args, **kwargs)
