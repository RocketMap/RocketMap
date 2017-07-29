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
from .pgoapiwrapper import PGoApiWrapper
from .utils import (in_radius, generate_device_info, equi_rect_distance,
                    clear_dict_response)
from .proxy import get_new_proxy

log = logging.getLogger(__name__)


class TooManyLoginAttempts(Exception):
    pass


class LoginSequenceFail(Exception):
    pass


class NullTimeException(Exception):

    def __init__(self, type):
        self.type = type
        super(NullTimeException, self).__init__(NullTimeException.__name__)


# Create the API object that'll be used to scan.
def setup_api(args, status, account):
    reset_account(account)
    # Create the API instance this will use.
    if args.mock != '':
        api = FakePogoApi(args.mock)
    else:
        identifier = account['username'] + account['password']
        device_info = generate_device_info(identifier)
        api = PGoApiWrapper(PGoApi(device_info=device_info))

    # New account - new proxy.
    if args.proxy:
        # If proxy is not assigned yet or if proxy-rotation is defined
        # - query for new proxy.
        if ((not status['proxy_url']) or
                (args.proxy_rotation != 'none')):

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
        if (status['proxy_url'] not in args.proxy):
            log.warning(
                'Tried replacing proxy %s with a new proxy, but proxy ' +
                'rotation is disabled ("none"). If this isn\'t intentional, ' +
                'enable proxy rotation.',
                status['proxy_url'])

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
        req = api.create_request()
        req.call(False)

        total_req += 1
        time.sleep(random.uniform(.43, .97))
    except Exception as e:
        log.exception('Login for account %s failed.'
                      + ' Exception in call request: %s.',
                      account['username'],
                      e)
        raise LoginSequenceFail('Failed during empty request in login'
                                + ' sequence for account {}.'.format(
                                    account['username']))

    # 2 - Get player information.
    log.debug('Fetching player information...')

    try:
        req = api.create_request()
        req.get_player(player_locale=args.player_locale)
        response = req.call(False)

        parse_get_player(account, response)

        total_req += 1
        time.sleep(random.uniform(.53, 1.1))
        if account['warning']:
            log.warning('Account %s has received a warning.',
                        account['username'])
    except Exception as e:
        log.exception('Login for account %s failed. Exception in ' +
                      'player request: %s.',
                      account['username'],
                      e)
        raise LoginSequenceFail('Failed while retrieving player information in'
                                + ' login sequence for account {}.'.format(
                                    account['username']))

    # 3 - Get remote config version.
    log.debug('Downloading remote config version...')
    old_config = account.get('remote_config', {})

    try:
        req = api.create_request()
        req.download_remote_config_version(platform=1,
                                           app_version=app_version)
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=0)
        req.check_awarded_badges()
        req.download_settings()
        response = req.call(False)

        parse_download_settings(account, response)
        parse_new_timestamp_ms(account, response)
        parse_inventory(api, account, response)

        total_req += 1
        time.sleep(random.uniform(.53, 1.1))
    except Exception as e:
        log.exception('Error while downloading remote config: %s.', e)
        raise LoginSequenceFail('Failed while getting remote config version in'
                                + ' login sequence for account {}.'.format(
                                    account['username']))

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
            req = api.create_request()
            req.get_asset_digest(
                platform=1,
                app_version=app_version,
                paginate=True,
                page_offset=page_offset,
                page_timestamp=page_timestamp)
            req.check_challenge()
            req.get_hatched_eggs()
            req.get_inventory(last_timestamp_ms=account[
                'last_timestamp_ms'])
            req.check_awarded_badges()
            req.download_settings(hash=account[
                'remote_config']['hash'])
            response = req.call(False)

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

            result = response.result
            page_offset = response.page_offset
            page_timestamp = response.timestamp_ms
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
            req = api.create_request()
            req.download_item_templates(
                paginate=True,
                page_offset=page_offset,
                page_timestamp=page_timestamp)
            req.check_challenge()
            req.get_hatched_eggs()
            req.get_inventory(
                last_timestamp_ms=account['last_timestamp_ms'])
            req.check_awarded_badges()
            req.download_settings(
                hash=account['remote_config']['hash'])
            response = req.call(False)

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

            result = response.result
            page_offset = response.page_offset
            page_timestamp = response.timestamp_ms
            log.debug('Completed %d requests to download'
                      + ' item templates.', req_count)

    # Check tutorial completion.
    if not all(x in account['tutorials'] for x in (0, 1, 3, 4, 7)):
        log.info('Completing tutorial steps for %s.', account['username'])
        complete_tutorial(args, api, account)
    else:
        log.debug('Account %s already did the tutorials.', account['username'])

    # 6 - Get player profile.
    log.debug('Fetching player profile...')

    try:
        req = api.create_request()
        req.get_player_profile()
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.download_settings(hash=account['remote_config']['hash'])
        req.get_buddy_walked()
        response = req.call(False)

        parse_new_timestamp_ms(account, response)

        total_req += 1
        time.sleep(random.uniform(.2, .3))
    except Exception as e:
        log.exception('Login for account %s failed. Exception occurred ' +
                      'while fetching player profile: %s.',
                      account['username'],
                      e)
        raise LoginSequenceFail('Failed while getting player profile in'
                                + ' login sequence for account {}.'.format(
                                    account['username']))

    log.debug('Retrieving Store Items...')
    try:  # 7 - Make an empty request to retrieve store items.
        req = api.create_request()
        req.get_store_items()
        response = req.call(False)

        total_req += 1
        time.sleep(random.uniform(.6, 1.1))
    except Exception as e:
        log.exception('Login for account %s failed. Exception in ' +
                      'retrieving Store Items: %s.', account['username'],
                      e)
        raise LoginSequenceFail('Failed during login sequence.')

    # 8 - Check if there are level up rewards to claim.
    log.debug('Checking if there are level up rewards to claim...')

    try:
        req = api.create_request()
        req.level_up_rewards(level=account['level'])
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.download_settings(hash=account['remote_config']['hash'])
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        response = req.call(False)

        parse_new_timestamp_ms(account, response)

        total_req += 1
        time.sleep(random.uniform(.45, .7))
    except Exception as e:
        log.exception('Login for account %s failed. Exception occurred ' +
                      'while fetching level-up rewards: %s.',
                      account['username'],
                      e)
        raise LoginSequenceFail('Failed while getting level-up rewards in'
                                + ' login sequence for account {}.'.format(
                                    account['username']))

    log.info('RPC login sequence for account %s successful with %s requests.',
             account['username'],
             total_req)
    time.sleep(random.uniform(10, 20))


# Complete minimal tutorial steps.
# API argument needs to be a logged in API instance.
# TODO: Check if game client bundles these requests, or does them separately.
def complete_tutorial(args, api, account):
    tutorial_state = account['tutorials']
    if 0 not in tutorial_state:
        time.sleep(random.uniform(1, 5))
        req = api.create_request()
        req.mark_tutorial_complete(tutorials_completed=0)
        log.debug('Sending 0 tutorials_completed for %s.', account['username'])
        req.call(False)

    if 1 not in tutorial_state:
        time.sleep(random.uniform(5, 12))
        req = api.create_request()
        req.set_avatar(player_avatar={
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
        req.call(False)

        time.sleep(random.uniform(0.3, 0.5))

        req = api.create_request()
        req.mark_tutorial_complete(tutorials_completed=1)
        log.debug('Sending 1 tutorials_completed for %s.', account['username'])
        req.call(False)

    time.sleep(random.uniform(0.5, 0.6))
    req = api.create_request()
    req.get_player_profile()
    log.debug('Fetching player profile for %s...', account['username'])
    req.call(False)

    starter_id = None
    if 3 not in tutorial_state:
        time.sleep(random.uniform(1, 1.5))
        req = api.create_request()
        req.get_download_urls(asset_id=[
            '1a3c2816-65fa-4b97-90eb-0b301c064b7a/1477084786906000',
            'aa8f7687-a022-4773-b900-3a8c170e9aea/1477084794890000',
            'e89109b0-9a54-40fe-8431-12f7826c8194/1477084802881000'])
        log.debug('Grabbing some game assets.')
        req.call(False)

        time.sleep(random.uniform(1, 1.6))
        req = api.create_request()
        req.call(False)

        time.sleep(random.uniform(6, 13))
        req = api.create_request()
        starter = random.choice((1, 4, 7))
        req.encounter_tutorial_complete(pokemon_id=starter)
        log.debug('Catching the starter for %s.', account['username'])
        req.call(False)

        time.sleep(random.uniform(0.5, 0.6))
        req = api.create_request()
        req.get_player(
            player_locale=args.player_locale)
        responses = req.call(False).get('responses', {})

        if 'GET_INVENTORY' in responses:
            for item in (responses['GET_INVENTORY'].inventory_delta
                         .inventory_items):
                pokemon = item.inventory_item_data.pokemon_data
                if pokemon:
                    starter_id = pokemon.id

    if 4 not in tutorial_state:
        time.sleep(random.uniform(5, 12))
        req = api.create_request()
        req.claim_codename(codename=account['username'])
        log.debug('Claiming codename for %s.', account['username'])
        req.call(False)

        time.sleep(random.uniform(1, 1.3))
        req = api.create_request()
        req.mark_tutorial_complete(tutorials_completed=4)
        log.debug('Sending 4 tutorials_completed for %s.', account['username'])
        req.call(False)

        time.sleep(0.1)
        req = api.create_request()
        req.get_player(
            player_locale=args.player_locale)
        req.call(False)

    if 7 not in tutorial_state:
        time.sleep(random.uniform(4, 10))
        req = api.create_request()
        req.mark_tutorial_complete(tutorials_completed=7)
        log.debug('Sending 7 tutorials_completed for %s.', account['username'])
        req.call(False)

    if starter_id:
        time.sleep(random.uniform(3, 5))
        req = api.create_request()
        req.set_buddy_pokemon(pokemon_id=starter_id)
        log.debug('Setting buddy pokemon for %s.', account['username'])
        req.call(False)
        time.sleep(random.uniform(0.8, 1.8))

    # Sleeping before we start scanning to avoid Niantic throttling.
    log.debug('And %s is done. Wait for a second, to avoid throttle.',
              account['username'])
    time.sleep(random.uniform(2, 4))
    return True


def get_player_level(map_dict):
    if 'responses' in map_dict and 'GET_INVENTORY' in map_dict['responses']:
        for item in (map_dict['responses']['GET_INVENTORY'].inventory_delta
                     .inventory_items):
            if item.inventory_item_data.HasField("player_stats"):
                return item.inventory_item_data.player_stats.level

    return 0


def reset_account(account):
    account['start_time'] = time.time()
    account['warning'] = None
    account['tutorials'] = []
    account['items'] = {}
    account['pokemons'] = {}
    account['incubators'] = []
    account['eggs'] = []
    account['level'] = 0
    account['spins'] = 0
    account['session_spins'] = 0
    account['walked'] = 0.0


def can_spin(account, max_h_spins):
    elapsed_time = time.time() - account['start_time']

    # Just to prevent division by 0 errors, when needed
    # set elapsed to 1 millisecond.
    if elapsed_time == 0:
        elapsed_time = 1

    return (account['session_spins'] * 3600.0 / elapsed_time) > max_h_spins


# Check if Pokestop is spinnable and not on cooldown.
def pokestop_spinnable(fort, step_location):
    if not fort.enabled:
        return False

    spinning_radius = 0.038
    in_range = in_radius((fort.latitude, fort.longitude),
                         step_location, spinning_radius)
    now = time.time()
    pause_needed = fort.cooldown_complete_timestamp_ms / 1000 > now
    return in_range and not pause_needed


def spin_pokestop(api, account, args, fort, step_location):
    if can_spin(account, args.account_max_spins):
        log.warning('Account %s has reached its Pokestop spinning limits.',
                    account['username'])
        return False
    # Set 50% Chance to spin a Pokestop.
    if random.random() > 0.5 or account['level'] == 1:
        time.sleep(random.uniform(0.8, 1.8))
        fort_details_request(api, account, fort)
        time.sleep(random.uniform(0.8, 1.8))  # Don't let Niantic throttle.
        response = spin_pokestop_request(api, account, fort, step_location)
        time.sleep(random.uniform(2, 4))  # Don't let Niantic throttle.

        # Check for reCaptcha.
        captcha_url = response['responses']['CHECK_CHALLENGE'].challenge_url
        if len(captcha_url) > 1:
            log.debug('Account encountered a reCaptcha.')
            return False

        spin_result = response['responses']['FORT_SEARCH'].result
        if spin_result is 1:
            log.info('Successful Pokestop spin with %s.',
                     account['username'])
            # Update account stats and clear inventory if necessary.
            parse_level_up_rewards(api, account)
            clear_inventory(api, account)
            account['session_spins'] += 1
            incubate_eggs(api, account)
            return True
        elif spin_result is 2:
            log.debug('Pokestop was not in range to spin.')
        elif spin_result is 3:
            log.debug('Failed to spin Pokestop. Has recently been spun.')
        elif spin_result is 4:
            log.debug('Failed to spin Pokestop. Inventory is full.')
            clear_inventory(api, account)
        elif spin_result is 5:
            log.debug('Maximum number of Pokestops spun for this day.')
        else:
            log.debug(
                'Failed to spin a Pokestop. Unknown result %d.',
                spin_result)

    return False


def parse_download_settings(account, api_response):
    if 'DOWNLOAD_REMOTE_CONFIG_VERSION' in api_response['responses']:
        remote_config = (api_response['responses']
                         .get('DOWNLOAD_REMOTE_CONFIG_VERSION', 0))
        asset_time = remote_config.asset_digest_timestamp_ms / 1000000
        template_time = remote_config.item_templates_timestamp_ms / 1000

        if asset_time == 0 or asset_time is None:
            raise NullTimeException(type="asset")
        if template_time == 0 or template_time is None:
            raise NullTimeException(type="template")

        download_settings = {}
        download_settings['hash'] = api_response['responses'][
            'DOWNLOAD_SETTINGS'].hash
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
        account['last_timestamp_ms'] = api_response['responses'][
            'GET_INVENTORY'].inventory_delta.new_timestamp_ms

        player_level = get_player_level(api_response)
        if player_level:
            account['level'] = player_level


def parse_get_player(account, api_response):
    if 'GET_PLAYER' in api_response['responses']:
        player_data = api_response['responses']['GET_PLAYER'].player_data

        account['warning'] = api_response['responses']['GET_PLAYER'].warn
        account['tutorials'] = player_data.tutorial_state


# Parse player stats and inventory into account.
def parse_inventory(api, account, api_response):
    inventory = api_response['responses']['GET_INVENTORY']
    parsed_items = 0
    parsed_pokemons = 0
    parsed_eggs = 0
    parsed_incubators = 0
    for item in inventory.inventory_delta.inventory_items:
        item_data = item.inventory_item_data
        if item_data.HasField('player_stats'):
            stats = item_data.player_stats
            account['level'] = stats.level
            account['spins'] = stats.poke_stop_visits
            account['walked'] = stats.km_walked

            log.debug('Parsed %s player stats: level %d, %f km ' +
                      'walked, %d spins.', account['username'],
                      account['level'], account['walked'], account['spins'])
        elif item_data.HasField('item'):
            item_id = item_data.item.item_id
            item_count = item_data.item.count
            account['items'][item_id] = item_count
            parsed_items += item_count
        elif item_data.HasField('egg_incubators'):
            incubators = item_data.egg_incubators.egg_incubator
            for incubator in incubators:
                if incubator.pokemon_id != 0:
                    left = (incubator.target_km_walked - account['walked'])
                    log.debug('Egg kms remaining: %.2f', left)
                else:
                    account['incubators'].append({
                        'id': incubator.id,
                        'item_id': incubator.item_id,
                        'uses_remaining': incubator.uses_remaining
                    })
                    parsed_incubators += 1
        elif item_data.HasField('pokemon_data'):
            p_data = item_data.pokemon_data
            p_id = p_data.id
            if not p_data.is_egg:
                account['pokemons'][p_id] = {
                    'pokemon_id': p_data.pokemon_id,
                    'move_1': p_data.move_1,
                    'move_2': p_data.move_2,
                    'height': p_data.height_m,
                    'weight': p_data.weight_kg,
                    'gender': p_data.pokemon_display.gender,
                    'cp': p_data.cp,
                    'cp_multiplier': p_data.cp_multiplier
                }
                parsed_pokemons += 1
            else:
                if p_data.egg_incubator_id:
                    # Egg is already incubating.
                    continue
                account['eggs'].append({
                    'id': p_id,
                    'km_target': p_data.egg_km_walked_target
                })
                parsed_eggs += 1
    log.debug(
        'Parsed %s player inventory: %d items, %d pokemons, %d available ' +
        'eggs and %d available incubators.',
        account['username'], parsed_items, parsed_pokemons, parsed_eggs,
        parsed_incubators)
    log.debug('Total amount in Inventory:' +
              ' {} Items, {} pokemon, {} eggs, {} Incubator'.format(
                int(parsed_items + item_count), len(account['pokemons']),
                len(account['eggs']), len(account['incubators'])))


def clear_inventory(api, account):
    items = [(1, 'Pokeball'), (2, 'Greatball'), (3, 'Ultraball'),
             (101, 'Potion'), (102, 'Super Potion'), (103, 'Hyper Potion'),
             (104, 'Max Potion'),
             (201, 'Revive'), (202, 'Max Revive'),
             (701, 'Razz Berry'), (703, 'Nanab Berry'), (705, 'Pinap Berry'),
             (1101, 'Sun Stone'), (1102, 'Kings Rock'), (1103, 'Metal Coat'),
             (1104, 'Dragon Scale'), (1105, 'Upgrade')]

    release_ids = []
    total_pokemon = len(account['pokemons'])
    release_count = int(total_pokemon - 5)
    if total_pokemon > random.randint(5, 10):
        release_ids = random.sample(account['pokemons'].keys(), release_count)
        # Don't let Niantic throttle.
        time.sleep(random.uniform(2, 4))
        release_p_response = request_release_pokemon(api, account, 0,
                                                     release_ids)

        captcha_url = release_p_response[
            'responses']['CHECK_CHALLENGE'].challenge_url
        if len(captcha_url) > 1:
            log.info('Account encountered a reCaptcha.')
            return False

        release_response = release_p_response['responses']['RELEASE_POKEMON']
        release_result = release_response.result

        if release_result is 1:
            log.info('Sucessfully Released %s Pokemon', len(release_ids))
            for p_id in release_ids:
                account['pokemons'].pop(p_id, None)
        elif release_result != 1:
            log.error('Failed to release Pokemon.')

    for item_id, item_name in items:
        item_count = account['items'].get(item_id, 0)
        random_max = random.randint(5, 10)
        if item_count > random_max:
            drop_count = item_count - random_max

            # Don't let Niantic throttle.
            time.sleep(random.uniform(2, 4))
            clear_inventory_response = clear_inventory_request(
                api, account, item_id, drop_count)

            captcha_url = clear_inventory_response['responses'][
                'CHECK_CHALLENGE'].challenge_url
            if len(captcha_url) > 1:
                log.info('Account encountered a reCaptcha.')
                return False

            clear_response = clear_inventory_response[
                'responses']['RECYCLE_INVENTORY_ITEM']
            clear_result = clear_response.result
            if clear_result is 1:
                log.info('Clearing %s %ss succeeded.', item_count,
                         item_name)
            elif clear_result is 2:
                log.debug('Not enough items to clear, parsing failed.')
            elif clear_result is 3:
                log.debug('Tried to recycle incubator, parsing failed.')
            else:
                log.warning('Failed to clear inventory.')

            log.debug('Recycled inventory: \n\r{}'.format(clear_result))

    return


def incubate_eggs(api, account):
    account['eggs'] = sorted(account['eggs'], key=lambda k: k['km_target'])
    for incubator in account['incubators']:
        if not account['eggs']:
            log.debug('Account %s has no eggs to incubate.',
                      account['username'])
            break
        egg = account['eggs'].pop(0)
        time.sleep(random.uniform(2.0, 4.0))
        if request_use_item_egg_incubator(
           api, account, incubator['id'], egg['id']):
            log.info('Egg #%s (%.0f km) is on incubator #%s.',
                     egg['id'], egg['km_target'], incubator['id'])
            account['incubators'].remove(incubator)
        else:
            log.warning('Failed to put egg on incubator #%s.', incubator['id'])

    return


def spin_pokestop_request(api, account, fort, step_location):
    try:
        req = api.create_request()
        req.fort_search(
            fort_id=fort.id,
            fort_latitude=fort.latitude,
            fort_longitude=fort.longitude,
            player_latitude=step_location[0],
            player_longitude=step_location[1])
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        response = req.call(False)
        parse_new_timestamp_ms(account, response)
        parse_inventory(api, account, response)
        return response

    except Exception as e:
        log.exception('Exception while spinning Pokestop: %s.', e)
        return False


def fort_details_request(api, account, fort):
    try:
        req = api.create_request()
        req.fort_details(
            fort_id=fort.id,
            latitude=fort.latitude,
            longitude=fort.longitude)
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        response = req.call(False)
        parse_new_timestamp_ms(account, response)
        return response
    except Exception as e:
        log.exception('Exception while getting Pokestop details: %s.', e)
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
        response = req.call(False)
        parse_new_timestamp_ms(account, response)
        return clear_dict_response(response)
    except Exception as e:
        log.exception('Exception while encountering Pokémon: %s.', e)
        return False


def clear_inventory_request(api, account, item_id, drop_count):
    try:
        req = api.create_request()
        req.recycle_inventory_item(item_id=item_id, count=drop_count)
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        clear_inventory_response = req.call(False)

        parse_new_timestamp_ms(account, clear_inventory_response)
        parse_inventory(api, account, clear_inventory_response)

        return clear_inventory_response

    except Exception as e:
        log.exception('Exception while clearing Inventory: %s', e)
        return False


def request_use_item_egg_incubator(api, account, incubator_id, egg_id):
    try:
        req = api.create_request()
        req.use_item_egg_incubator(
            item_id=incubator_id,
            pokemon_id=egg_id
        )
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        response = req.call(False)

        parse_new_timestamp_ms(account, response)

        return True

    except Exception as e:
        log.exception('Exception while putting an egg in incubator: %s', e)
    return False


def request_release_pokemon(api, account, pokemon_id, release_ids=[]):
    try:
        req = api.create_request()
        req.release_pokemon(pokemon_id=pokemon_id,
                            pokemon_ids=release_ids)
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        release_p_response = req.call(False)

        parse_new_timestamp_ms(account, release_p_response)

        return release_p_response

    except Exception as e:
        log.exception('Exception while releasing Pokemon: %s', e)

    return False


def parse_level_up_rewards(api, account):
    try:
        req = api.create_request()
        req.level_up_rewards(level=account['level'])
        req.check_challenge()
        req.get_hatched_eggs()
        req.get_inventory(last_timestamp_ms=account['last_timestamp_ms'])
        req.check_awarded_badges()
        req.get_buddy_walked()
        req.get_inbox(is_history=True)
        response = req.call(False)

        parse_new_timestamp_ms(account, response)

        response = response['responses']['LEVEL_UP_REWARDS']
        result = response.result
        if result is 1:
            log.info('Account %s collected its level up rewards.',
                     account['username'])
        elif result != 1:
            log.debug('Account %s already collected its level up rewards.',
                      account['username'])
    except Exception as e:
        log.exception('Error during getting Level Up Rewards %s.', e)


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
        if values is None:
            values = []
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
