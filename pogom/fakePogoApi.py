#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import struct
from time import time
from .utils import get_args


class FakePogoApi:

    def __init__(self, mock):
        # Fake a 24 hour auth token
        self._auth_provider = type('', (object,), {"_ticket_expire": (time() + (3600 * 24)) * 1000})()
        self.inited = False
        self.mock = mock

    def set_proxy(self, proxy_config):
        pass

    def activate_signature(self, library):
        pass

    def set_position(self, lat, lng, alt):
        # meters radius (very, very rough approximation -- deal with it)
        if not self.inited:
            args = get_args()
            radius = 140 * args.step_limit
            requests.get('{}/login/{}/{}/{}'.format(self.mock, lat, lng, radius))
            self.inited = True

    def set_authentication(self, provider=None, oauth2_refresh_token=None, username=None, password=None):
        pass

    def i2f(self, i):
        return struct.unpack('<d', struct.pack('<Q', i))[0]

    def get_map_objects(self, latitude=None, longitude=None, since_timestamp_ms=None, cell_id=None):
        location = (self.i2f(latitude), self.i2f(longitude))
        response = requests.get('{}/scan/{}/{}'.format(self.mock, *location))
        return response.json()
