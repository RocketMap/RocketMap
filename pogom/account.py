#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import time
import random
from threading import Lock
from timeit import default_timer

from pgoapi import PGoApi
from pgoapi.exceptions import AuthException

from .fakePogoApi import FakePogoApi
from .utils import in_radius, generate_device_info, equi_rect_distance
from .proxy import get_new_proxy

log = logging.getLogger(__name__)


class TooManyLoginAttempts(Exception):
    pass


class LoginSequenceFail(Exception):
    pass


# Create the API object that'll be used to scan.
def setup_api(args, status, account):
    # Create the API instance this will use.
    if args.mock != '':
        api = FakePogoApi(args.mock)
    else:
        identifier = account['username'] + account['password']
        device_info = generate_device_info(identifier)
        api = PGoApi(device_info=device_info)

    # New account - new proxy.
    if args.proxy:
        # If proxy is not assigned yet or if proxy-rotation is defined
        # - query for new proxy.
        if ((not status['proxy_url']) or
                ((args.proxy_rotation is not None) and
                 (args.proxy_rotation != 'none'))):

            proxy_num, status['proxy_url'] = get_new_proxy(args)
            if args.proxy_display.upper() != 'FULL':
                status['proxy_display'] = proxy_num
            else:
                status['proxy_display'] = status['proxy_url']

    if status['proxy_url']:
        log.debug('Using proxy %s', status['proxy_url'])
        api.set_proxy({
            'http': status['proxy_url'],
            'https': status['proxy_url']})

    return api


# Use API to check the login status, and retry the login if possible.
def check_login(args, account, api, position, proxy_url):
    # Logged in? Enough time left? Cool!
    if api._auth_provider and api._auth_provider._ticket_expire:
        remaining_time = api._auth_provider._ticket_expire / 1000 - time.time()

        if remaining_time > 60:
            log.debug(
                'Credentials remain valid for another %f seconds.',
                remaining_time)
            return

    # Try to login. Repeat a few times, but don't get stuck here.
    num_tries = 0

    # One initial try + login_retries.
    while num_tries < (args.login_retries + 1):
        try:
            if proxy_url:
                api.set_authentication(
                    provider=account['auth_service'],
                    username=account['username'],
                    password=account['password'],
                    proxy_config={'http': proxy_url, 'https': proxy_url})
            else:
                api.set_authentication(
                    provider=account['auth_service'],
                    username=account['username'],
                    password=account['password'])
            # Success!
            break
        except AuthException:
            num_tries += 1
            log.error(
                ('Failed to login to Pokemon Go with account %s. ' +
                 'Trying again in %g seconds.'),
                account['username'], args.login_delay)
            time.sleep(args.login_delay)

    if num_tries > args.login_retries:
        log.error(
            ('Failed to login to Pokemon Go with account %s in ' +
             '%d tries. Giving up.'),
            account['username'], num_tries)
        raise TooManyLoginAttempts('Exceeded login attempts.')

    time.sleep(random.uniform(2, 4))

    # Simulate login sequence.
    rpc_login_sequence(args, api, account)


# Simulate real app via login sequence.
def rpc_login_sequence(args, api, account):
    total_req = 0
    app_version = int(args.api_version.replace('.', '0'))

    # 1 - Make an empty request to mimick real app behavior.
    log.debug('Starting RPC login sequence...')

    try:
        request = api.create_request()
        request.call()

        total_req += 1
        time.sleep(random.uniform(.43, .97))
    except Exception as e:
        log.exception('Login for account %s failed.'
                      + ' Exception in call request: %s.',
                      account['username'],
                      e)
        raise LoginSequenceFail('Failed during empty request in login'
                                + ' sequence for account %s.',
                                account['username'])

    # 2 - Get player information.
    log.debug('Fetching player information...')

    try:
        req = api.create_request()
        req.get_player(player_locale=args.player_locale)
        req.call()

        total_req += 1
        time.sleep(random.uniform(.53, 1.1))
    except Exception as e:
        log.exception('Login for account %s failed. Exception in ' +
                      'player request: %s.',
                      account['username'],
                      e)
        raise LoginSequenceFail('Failed while retrieving player information in'
                                + ' login sequence for account %s.',
                                account['username'])

    # 3 - Get remote config version.
    log.debug('Downloading remote config version...')
    old_config = account.get('remote_config', {})

    try:
        request = api.create_request()
        request.download_remote_config_version(platform=1,
                                               app_version=app_version)
        request.check_challenge()
        request.get_hatched_eggs()
        request.get_inventory(last_timestamp_ms=0)
        request.check_awarded_badges()
        request.download_settings()
        response = request.call()

        parse_download_settings(account, response)
        parse_new_timestamp_ms(account, response)

        total_req += 1
        time.sleep(random.uniform(.53, 1.1))
    except Exception as e:
        log.exception('Error while downloading remote config: %s.', e)
        raise LoginSequenceFail('Failed while getting remote config version in'
                                + ' login sequence for account %s.',
                                account['username'])

    # 4 - Get asset digest.
    log.debug('Fetching asset digest...')
    config = account.get('remote_config', {})

    if config.get('asset_time', 0) > old_config.get('asset_time', 0):
        i = random.randint(0, 3)
        req_count = 0
        result = 2
        page_offset = 0
        page_timestamp = 0

        time.sleep(random.uniform(.7, 1.2))

        while result == 2:
            request = api.create_request()
            request.get_asset_digest(
                platform=1,
                app_version=app_version,
                paginate=True,
                page_offset=page_offset,
                page_timestamp=page_timestamp)
            request.check_challenge()
            request.get_hatched_eggs()
            request.get_inventory(last_timestamp_ms=account[
                'last_timestamp_ms'])
            request.check_awarded_badges()
            request.download_settings(hash=account[
                'remote_config']['hash'])
            response = request.call()

            parse_new_timestamp_ms(account, response)

            req_count += 1
            total_req += 1

            if i > 2:
                time.sleep(random.uniform(1.4, 1.6))
                i = 0
            else:
                i += 1
                time.sleep(random.uniform(.3, .5))

            try:
                # Re-use variable name. Also helps GC.
                response = response['responses']['GET_ASSET_DIGEST']
            except KeyError:
                break

            result = response.get('result', 0)
            page_offset = response.get('page_offset', 0)
            page_timestamp = response.get('timestamp_ms', 0)
            log.debug('Completed %d requests to get asset digest.',
                      req_count)

    # 5 - Get item templates.
    log.debug('Fetching item templates...')

    if config.get('template_time', 0) > old_config.get('template_time', 0):
        i = random.randint(0, 3)
        req_count = 0
        result = 2
        page_offset = 0
        page_timestamp = 0

        while result == 2:
            request = api.create_request()
            request.download_item_templates(
                paginate=True,
                page_offset=page_offset,
                page_timestamp=page_timestamp)
            request.check_challenge()
            request.get_hatched_eggs()
            request.get_inventory(
                last_timestamp_ms=account['last_timestamp_ms'])
            request.check_awarded_badges()
            request.download_settings(
                hash=account['remote_config']['hash'])
            response = request.call()

            parse_new_timestamp_ms(account, response)

            req_count += 1
            total_req += 1

            if i > 2:
                time.sleep(random.uniform(1.4, 1.6))
                i = 0
            else:
                i += 1
                time.sleep(random.uniform(.25, .5))

            try:
                # Re-use variable name. Also helps GC.
                response = response['responses']['DOWNLOAD_ITEM_TEMPLATES']
            except KeyError:
                break

            result = response.get('result', 0)
            page_offset = response.get('page_offset', 0)
            page_timestamp = response.get('timestamp_ms', 0)
            log.debug('Completed %d requests to download'
                      + ' item templates.', req_count)

    # 6 - Get player profile.
    log.debug('Fetching player profile...')

    try:
        request = api.create_request()
        request.get_player_profile()
        request.check_challenge()
        request.get_hatched_eggs()
        request.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        request.check_awarded_badges()
        request.download_settings(hash=account['remote_config']['hash'])
        request.get_buddy_walked()
        response = request.call()

        parse_new_timestamp_ms(account, response)

        total_req += 1
        time.sleep(random.uniform(.2, .3))
    except Exception as e:
        log.exception('Login for account %s failed. Exception occurred ' +
                      'while fetching player profile: %s.',
                      account['username'],
                      e)
        raise LoginSequenceFail('Failed while getting player profile in'
                                + ' login sequence for account %s.',
                                account['username'])

    # Needs updated PGoApi to be used.
    # log.debug('Retrieving Store Items...')
    # try:  # 7 - Make an empty request to retrieve store items.
    #    request = api.create_request()
    #    request.get_store_items()
    #    response = request.call()
    #    total_req += 1
    #    time.sleep(random.uniform(.6, 1.1))
    # except Exception as e:
    #    log.exception('Login for account %s failed. Exception in ' +
    #                  'retrieving Store Items: %s.', account['username'],
    #                  e)
    #    raise LoginSequenceFail('Failed during login sequence.')

    # 8 - Check if there are level up rewards to claim.
    log.debug('Checking if there are level up rewards to claim...')

    try:
        request = api.create_request()
        request.level_up_rewards(level=account['level'])
        request.check_challenge()
        request.get_hatched_eggs()
        request.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        request.check_awarded_badges()
        request.download_settings(hash=account['remote_config']['hash'])
        request.get_buddy_walked()
        request.get_inbox(is_history=True)
        response = request.call()

        parse_new_timestamp_ms(account, response)

        total_req += 1
        time.sleep(random.uniform(.45, .7))
    except Exception as e:
        log.exception('Login for account %s failed. Exception occurred ' +
                      'while fetching level-up rewards: %s.',
                      account['username'],
                      e)
        raise LoginSequenceFail('Failed while getting level-up rewards in'
                                + ' login sequence for account %s.',
                                account['username'])

    log.info('RPC login sequence for account %s successful with %s requests.',
             account['username'],
             total_req)
    time.sleep(random.uniform(10, 20))


# Check if all important tutorial steps have been completed.
# API argument needs to be a logged in API instance.
def get_tutorial_state(args, api, account):
    log.debug('Checking tutorial state for %s.', account['username'])
    request = api.create_request()
    request.get_player(
        player_locale=args.player_locale)
    response = request.call().get('responses', {})

    get_player = response.get('GET_PLAYER', {})
    tutorial_state = get_player.get(
        'player_data', {}).get('tutorial_state', [])
    time.sleep(random.uniform(2, 4))
    return tutorial_state


# Complete minimal tutorial steps.
# API argument needs to be a logged in API instance.
# TODO: Check if game client bundles these requests, or does them separately.
def complete_tutorial(args, api, account, tutorial_state):
    if 0 not in tutorial_state:
        time.sleep(random.uniform(1, 5))
        request = api.create_request()
        request.mark_tutorial_complete(tutorials_completed=0)
        log.debug('Sending 0 tutorials_completed for %s.', account['username'])
        request.call()

    if 1 not in tutorial_state:
        time.sleep(random.uniform(5, 12))
        request = api.create_request()
        request.set_avatar(player_avatar={
            'hair': random.randint(1, 5),
            'shirt': random.randint(1, 3),
            'pants': random.randint(1, 2),
            'shoes': random.randint(1, 6),
            'avatar': random.randint(0, 1),
            'eyes': random.randint(1, 4),
            'backpack': random.randint(1, 5)
        })
        log.debug('Sending set random player character request for %s.',
                  account['username'])
        request.call()

        time.sleep(random.uniform(0.3, 0.5))

        request = api.create_request()
        request.mark_tutorial_complete(tutorials_completed=1)
        log.debug('Sending 1 tutorials_completed for %s.', account['username'])
        request.call()

    time.sleep(random.uniform(0.5, 0.6))
    request = api.create_request()
    request.get_player_profile()
    log.debug('Fetching player profile for %s...', account['username'])
    request.call()

    starter_id = None
    if 3 not in tutorial_state:
        time.sleep(random.uniform(1, 1.5))
        request = api.create_request()
        request.get_download_urls(asset_id=[
            '1a3c2816-65fa-4b97-90eb-0b301c064b7a/1477084786906000',
            'aa8f7687-a022-4773-b900-3a8c170e9aea/1477084794890000',
            'e89109b0-9a54-40fe-8431-12f7826c8194/1477084802881000'])
        log.debug('Grabbing some game assets.')
        request.call()

        time.sleep(random.uniform(1, 1.6))
        request = api.create_request()
        request.call()

        time.sleep(random.uniform(6, 13))
        request = api.create_request()
        starter = random.choice((1, 4, 7))
        request.encounter_tutorial_complete(pokemon_id=starter)
        log.debug('Catching the starter for %s.', account['username'])
        request.call()

        time.sleep(random.uniform(0.5, 0.6))
        request = api.create_request()
        request.get_player(
            player_locale=args.player_locale)
        responses = request.call().get('responses', {})

        inventory = responses.get('GET_INVENTORY', {}).get(
            'inventory_delta', {}).get('inventory_items', [])
        for item in inventory:
            pokemon = item.get('inventory_item_data', {}).get('pokemon_data')
            if pokemon:
                starter_id = pokemon.get('id')

    if 4 not in tutorial_state:
        time.sleep(random.uniform(5, 12))
        request = api.create_request()
        request.claim_codename(codename=account['username'])
        log.debug('Claiming codename for %s.', account['username'])
        request.call()

        time.sleep(random.uniform(1, 1.3))
        request = api.create_request()
        request.mark_tutorial_complete(tutorials_completed=4)
        log.debug('Sending 4 tutorials_completed for %s.', account['username'])
        request.call()

        time.sleep(0.1)
        request = api.create_request()
        request.get_player(
            player_locale=args.player_locale)
        request.call()

    if 7 not in tutorial_state:
        time.sleep(random.uniform(4, 10))
        request = api.create_request()
        request.mark_tutorial_complete(tutorials_completed=7)
        log.debug('Sending 7 tutorials_completed for %s.', account['username'])
        request.call()

    if starter_id:
        time.sleep(random.uniform(3, 5))
        request = api.create_request()
        request.set_buddy_pokemon(pokemon_id=starter_id)
        log.debug('Setting buddy pokemon for %s.', account['username'])
        request.call()
        time.sleep(random.uniform(0.8, 1.8))

    # Sleeping before we start scanning to avoid Niantic throttling.
    log.debug('And %s is done. Wait for a second, to avoid throttle.',
              account['username'])
    time.sleep(random.uniform(2, 4))
    return True


# Complete tutorial with a level up by a Pokestop spin.
# API argument needs to be a logged in API instance.
# Called during fort parsing in models.py
def tutorial_pokestop_spin(api, player_level, forts, step_location, account):
    if player_level > 1:
        log.debug(
            'No need to spin a Pokestop. ' +
            'Account %s is already level %d.',
            account['username'], player_level)
    else:  # Account needs to spin a Pokestop for level 2.
        log.debug(
            'Spinning Pokestop for account %s.',
            account['username'])
        for fort in forts:
            if fort.get('type') == 1:
                if spin_pokestop(api, account, fort, step_location):
                    log.debug(
                        'Account %s successfully spun a Pokestop ' +
                        'after completed tutorial.',
                        account['username'])
                    return True

    return False


def get_player_level(map_dict):
    inventory_items = map_dict['responses'].get(
        'GET_INVENTORY', {}).get(
        'inventory_delta', {}).get(
        'inventory_items', [])
    player_stats = [item['inventory_item_data']['player_stats']
                    for item in inventory_items
                    if 'player_stats' in item.get(
                    'inventory_item_data', {})]
    if len(player_stats) > 0:
        player_level = player_stats[0].get('level', 1)
        return player_level

    return 0


def spin_pokestop(api, account, fort, step_location):
    spinning_radius = 0.04
    if in_radius((fort['latitude'], fort['longitude']), step_location,
                 spinning_radius):
        log.debug('Attempt to spin Pokestop (ID %s)', fort['id'])

        time.sleep(random.uniform(0.8, 1.8))
        fort_details_request(api, account, fort)
        time.sleep(random.uniform(0.8, 1.8))  # Don't let Niantic throttle
        response = spin_pokestop_request(api, account, fort, step_location)
        time.sleep(random.uniform(2, 4))  # Don't let Niantic throttle.

        # Check for reCaptcha
        captcha_url = response['responses'][
            'CHECK_CHALLENGE']['challenge_url']
        if len(captcha_url) > 1:
            log.debug('Account encountered a reCaptcha.')
            return False

        spin_result = response['responses']['FORT_SEARCH']['result']
        if spin_result is 1:
            log.debug('Successful Pokestop spin.')
            return True
        elif spin_result is 2:
            log.debug('Pokestop was not in range to spin.')
        elif spin_result is 3:
            log.debug('Failed to spin Pokestop. Has recently been spun.')
        elif spin_result is 4:
            log.debug('Failed to spin Pokestop. Inventory is full.')
        elif spin_result is 5:
            log.debug('Maximum number of Pokestops spun for this day.')
        else:
            log.debug(
                'Failed to spin a Pokestop. Unknown result %d.',
                spin_result)

    return False


def spin_pokestop_request(api, account, fort, step_location):
    try:
        req = api.create_request()
        req.fort_search(
            fort_id=fort['id'],
            fort_latitude=fort['latitude'],
            fort_longitude=fort['longitude'],
            player_latitude=step_location[0],
            player_longitude=step_location[1])
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        response = req.call()
        parse_new_timestamp_ms(account, response)
        return response

    except Exception as e:
        log.exception('Exception while spinning Pokestop: %s.', repr(e))
        return False


def fort_details_request(api, account, fort):
    try:
        req = api.create_request()
        req.fort_details(
            fort_id=fort['id'],
            latitude=fort['latitude'],
            longitude=fort['longitude'])
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        response = req.call()
        parse_new_timestamp_ms(account, response)
        return response
    except Exception as e:
        log.exception('Exception while getting Pokestop details: %s.', repr(e))
        return False


def encounter_pokemon_request(api, account, encounter_id, spawnpoint_id,
                              scan_location):
    try:
        # Setup encounter request envelope.
        req = api.create_request()
        req.encounter(
            encounter_id=encounter_id,
            spawn_point_id=spawnpoint_id,
            player_latitude=scan_location[0],
            player_longitude=scan_location[1])
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        response = req.call()
        parse_new_timestamp_ms(account, response)
        return response
    except Exception as e:
        log.exception('Exception while encountering Pokémon: %s.', repr(e))
        return False


def parse_download_settings(account, api_response):
    if 'DOWNLOAD_REMOTE_CONFIG_VERSION' in api_response['responses']:
        remote_config = (api_response['responses']
                         .get('DOWNLOAD_REMOTE_CONFIG_VERSION', 0))
        if 'asset_digest_timestamp_ms' in remote_config:
            asset_time = remote_config['asset_digest_timestamp_ms'] / 1000000
        if 'item_templates_timestamp_ms' in remote_config:
            template_time = remote_config['item_templates_timestamp_ms'] / 1000

        download_settings = {}
        download_settings['hash'] = api_response[
            'responses']['DOWNLOAD_SETTINGS']['hash']
        download_settings['asset_time'] = asset_time
        download_settings['template_time'] = template_time

        account['remote_config'] = download_settings

        log.debug('Download settings for account %s: %s.',
                  account['username'],
                  download_settings)
        return True


# Parse new timestamp from the GET_INVENTORY response.
def parse_new_timestamp_ms(account, api_response):
    if 'GET_INVENTORY' in api_response['responses']:
        account['last_timestamp_ms'] = (api_response['responses']
                                                    ['GET_INVENTORY']
                                                    ['inventory_delta']
                                        .get('new_timestamp_ms', 0))

        player_level = get_player_level(api_response)
        if player_level:
            account['level'] = player_level


# The AccountSet returns a scheduler that cycles through different
# sets of accounts (e.g. L30). Each set is defined at runtime, and is
# (currently) used to separate regular accounts from L30 accounts.
# TODO: Migrate the old account Queue to a real AccountScheduler, preferably
# handled globally via database instead of per instance.
# TODO: Accounts in the AccountSet are exempt from things like the
# account recycler thread. We could've hardcoded support into it, but that
# would have added to the amount of ugly code. Instead, we keep it as is
# until we have a proper account manager.
class AccountSet(object):

    def __init__(self, kph):
        self.sets = {}

        # Scanning limits.
        self.kph = kph

        # Thread safety.
        self.next_lock = Lock()

    # Set manipulation.
    def create_set(self, name, values=[]):
        if name in self.sets:
            raise Exception('Account set ' + name + ' is being created twice.')

        self.sets[name] = values

    # Release an account back to the pool after it was used.
    def release(self, account):
        if 'in_use' not in account:
            log.error('Released account %s back to the AccountSet,'
                      + " but it wasn't locked.",
                      account['username'])
        else:
            account['in_use'] = False

    # Get next account that is ready to be used for scanning.
    def next(self, set_name, coords_to_scan):
        # Yay for thread safety.
        with self.next_lock:
            # Readability.
            account_set = self.sets[set_name]

            # Loop all accounts for a good one.
            now = default_timer()
            max_speed_kmph = self.kph

            for i in range(len(account_set)):
                account = account_set[i]

                # Make sure it's not in use.
                if account.get('in_use', False):
                    continue

                # Make sure it's not captcha'd.
                if account.get('captcha', False):
                    continue

                # Check if we're below speed limit for account.
                last_scanned = account.get('last_scanned', False)

                if last_scanned:
                    seconds_passed = now - last_scanned
                    old_coords = account.get('last_coords', coords_to_scan)

                    distance_km = equi_rect_distance(
                        old_coords,
                        coords_to_scan)
                    cooldown_time_sec = distance_km / max_speed_kmph * 3600

                    # Not enough time has passed for this one.
                    if seconds_passed < cooldown_time_sec:
                        continue

                # We've found an account that's ready.
                account['last_scanned'] = now
                account['last_coords'] = coords_to_scan
                account['in_use'] = True

                return account

        # TODO: Instead of returning False, return the amount of min. seconds
        # the instance needs to wait until the first account becomes available,
        # so it doesn't need to keep asking if we know we need to wait.
        return False
