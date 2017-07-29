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

    def call(self, *args, **kwargs):
        # Retry x times on failure.
        retries_left = self.retries

        while retries_left > 0:
            try:
                log.debug('Sending API request w/ %d retries left.',
                          retries_left)
                return self.request.call(*args, **kwargs)
            except HashingQuotaExceededException:
                # Sleep a minimum to free some RPM and don't use one of our
                # retries, just retry until we have RPM left.
                time.sleep(random.uniform(0.75, 1.5))
                log.debug('Hashing quota exceeded. If this delays requests for'
                          ' too long, consider adding more RPM. Retrying...')
            except Exception as ex:
                if retries_left > 0:
                    retries_left -= 1

                    log.debug('API request failed with exception type %s.'
                              ' Retrying...', type(ex).__name__)

                    # Rotate proxy. Not necessary on
                    # HashingQuotaExceededException, because it's proof that
                    # the proxy worked.
                    if self.args.proxy:
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
