#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from pgoapi.utilities import get_cell_ids
from pgoapi.hash_server import BadHashRequestException, HashingOfflineException

log = logging.getLogger(__name__)


class AccountBannedException(Exception):
    pass


def send_generic_request(req, account, settings=True, buddy=True, inbox=True):
    req.check_challenge()
    req.get_hatched_eggs()
    req.get_holo_inventory(last_timestamp_ms=account['last_timestamp_ms'])
    req.check_awarded_badges()

    if settings:
        if 'remote_config' in account:
            req.download_settings(hash=account['remote_config']['hash'])
        else:
            req.download_settings()

    if buddy:
        req.get_buddy_walked()

    if inbox:
        req.get_inbox(is_history=True)

    try:
        resp = req.call(False)
    except HashingOfflineException:
        log.error('Hashing server is unreachable, it might be offline.')
        raise
    except BadHashRequestException:
        log.error('Invalid or expired hashing key: %s.',
                  req.__parent__.get_hash_server_token())
        raise

    parse_inventory(account, resp)
    if settings:
        parse_remote_config(account, resp)

    # Clean all unneeded data.
    del resp['envelope'].platform_returns[:]
    if 'responses' not in resp:
        return resp
    responses = [
        'GET_HATCHED_EGGS', 'GET_HOLO_INVENTORY', 'CHECK_AWARDED_BADGES',
        'DOWNLOAD_SETTINGS', 'GET_BUDDY_WALKED', 'GET_INBOX'
    ]
    for item in responses:
        if item in resp['responses']:
            del resp['responses'][item]

    log.log(5, 'Response: \n%s', resp)
    return resp


def parse_remote_config(account, api_response):
    if 'DOWNLOAD_REMOTE_CONFIG_VERSION' not in api_response['responses']:
        return

    remote_config = api_response['responses']['DOWNLOAD_REMOTE_CONFIG_VERSION']
    if remote_config.result == 0:
        raise AccountBannedException('The account is temporarily banned')

    asset_time = remote_config.asset_digest_timestamp_ms / 1000000
    template_time = remote_config.item_templates_timestamp_ms / 1000

    download_settings = {}
    download_settings['hash'] = api_response['responses'][
        'DOWNLOAD_SETTINGS'].hash
    download_settings['asset_time'] = asset_time
    download_settings['template_time'] = template_time

    account['remote_config'] = download_settings

    log.debug('Download settings for account %s: %s.', account['username'],
              download_settings)


# Parse player stats and inventory into account.
def parse_inventory(account, api_response):
    if 'GET_HOLO_INVENTORY' not in api_response['responses']:
        return
    inventory = api_response['responses']['GET_HOLO_INVENTORY']
    parsed_items = 0
    parsed_pokemons = 0
    parsed_eggs = 0
    parsed_incubators = 0
    account['last_timestamp_ms'] = inventory.inventory_delta.new_timestamp_ms

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
        'Parsed %s player inventory: %d items, %d pokemons, %d available' +
        ' eggs and %d available incubators.', account['username'],
        parsed_items, parsed_pokemons, parsed_eggs, parsed_incubators)


def catchRequestException(task):

    def _catch(function):

        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                log.exception('Exception while %s with account %s: %s.', task,
                              kwargs.get('account', args[1])['username'], e)
                return False

        return wrapper

    return _catch


@catchRequestException('spinning Pokestop')
def fort_search(api, account, fort, step_location):
    req = api.create_request()
    req.fort_search(
        fort_id=fort.id,
        fort_latitude=fort.latitude,
        fort_longitude=fort.longitude,
        player_latitude=step_location[0],
        player_longitude=step_location[1])
    return send_generic_request(req, account)


@catchRequestException('getting Pokestop details')
def fort_details(api, account, fort):
    req = api.create_request()
    req.fort_details(
        fort_id=fort.id, latitude=fort.latitude, longitude=fort.longitude)
    return send_generic_request(req, account)


@catchRequestException('encountering Pokémon')
def encounter(api, account, encounter_id, spawnpoint_id, scan_location):
    req = api.create_request()
    req.encounter(
        encounter_id=encounter_id,
        spawn_point_id=spawnpoint_id,
        player_latitude=scan_location[0],
        player_longitude=scan_location[1])
    return send_generic_request(req, account)


@catchRequestException('clearing Inventory')
def recycle_inventory_item(api, account, item_id, drop_count):
    req = api.create_request()
    req.recycle_inventory_item(item_id=item_id, count=drop_count)
    return send_generic_request(req, account)


@catchRequestException('putting an egg in incubator')
def use_item_egg_incubator(api, account, incubator_id, egg_id):
    req = api.create_request()
    req.use_item_egg_incubator(item_id=incubator_id, pokemon_id=egg_id)
    return send_generic_request(req, account)


@catchRequestException('releasing Pokemon')
def release_pokemon(api, account, pokemon_id, release_ids=None):
    if release_ids is None:
        return False

    req = api.create_request()
    req.release_pokemon(pokemon_id=pokemon_id, pokemon_ids=release_ids)
    return send_generic_request(req, account)


@catchRequestException('getting Rewards')
def level_up_rewards(api, account):
    req = api.create_request()
    req.level_up_rewards(level=account['level'])
    return send_generic_request(req, account)


@catchRequestException('downloading map')
def get_map_objects(api, account, location):
    cell_ids = get_cell_ids(location[0], location[1])
    timestamps = [0, ]*len(cell_ids)
    req = api.create_request()
    req.get_map_objects(
        latitude=location[0],
        longitude=location[1],
        since_timestamp_ms=timestamps,
        cell_id=cell_ids)
    return send_generic_request(req, account)


@catchRequestException('getting gym details')
def gym_get_info(api, account, position, gym):
    req = api.create_request()
    req.gym_get_info(
        gym_id=gym['gym_id'],
        player_lat_degrees=position[0],
        player_lng_degrees=position[1],
        gym_lat_degrees=gym['latitude'],
        gym_lng_degrees=gym['longitude'])
    return send_generic_request(req, account)
