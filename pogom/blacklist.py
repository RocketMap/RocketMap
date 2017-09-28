#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import requests

log = logging.getLogger(__name__)


# Global IP blacklist.
def get_ip_blacklist():
    try:
        url = 'https://blist.devkat.org/blacklist.json'
        blacklist = requests.get(url, timeout=5).json()
        log.debug('Entries in blacklist: %s.', len(blacklist))
        return blacklist
    except (requests.exceptions.RequestException, IndexError, KeyError):
        log.error('Unable to retrieve blacklist, setting to empty.')
        return []


# Fingerprinting methods. They receive Flask's request object as
# argument and return True when a blacklisted fingerprint
# matches.


# No referrer = request w/o being on a website.
def _no_referrer(request):
    return not request.referrer


# iPokeGo.
def _iPokeGo(request):
    user_agent = request.headers.get('User-Agent', False)

    if not user_agent:
        return False

    return 'ipokego' in user_agent.lower()


# Fingerprints dict for easy scoping on imports.
fingerprints = {
    'no_referrer': _no_referrer,
    'iPokeGo': _iPokeGo
}
