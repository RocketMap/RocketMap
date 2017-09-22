# Webhooks

RocketMap can send map information such as Pokémon spawns, gym details, raid appearances and pokestop lures to other applications through webhooks.

Every time a webhook-enabled event occurs (for example a new Pokémon appearing) a web request will be sent to a provided URL containing information about that event.

## Table of Contents

- [What Do Webhooks Do?](#what-do-webhooks-do)
- [Setting Up a Webhook](#setting-up-a-webhook)
  - [Setting webhook urls](#setting-webhook-urls)
    - [Using the command line](#using-the-command-line)
    - [Using a config file](#using-a-config-file)
  - [Setting webhook types](#setting-webhook-types)
    - [Using the command line](#using-the-command-line)
    - [Using a config file](#using-a-config-file)
  - [Filtering Pokémon](#filtering-pokemon)
    - [Whitelisting Pokémon](#whitelisting-pokemon)
    - [Blacklisting Pokémon](#blacklisting-pokemon)
- [Webhook Types](#webhook-types)
  - [`pokemon`](#pokemon)
  - [`pokestop`](#pokestop)
  - [`lure`](#lure)
  - [`gym`](#gym)
  - [`gym-info`](#gym-info)
  - [`egg`](#egg)
  - [`raid`](#raid)
  - [`tth`](#tth)
  - [`captcha`](#captcha)
- [PokeAlarm](#pokealarm)
- [RocketMap Public Webhook](#rocketmap-public-webhook)

## What Do Webhooks Do?

Webhooks allow developers to send data from RocketMap to other applications.

A simple example would be an application that receives Pokémon spawn events, checks if the Pokémon that's appeared is a Dragonite, and if so plays an alarm sound.

## Setting Up a Webhook

To start sending data to a webhook:
1. set a webhook url (or list of webhook urls) to send data to
2. set the webhook types to be received
3. (optional) set up a whitelist or blacklist

**If no webhook types are set, no webhook data will be sent.**

### Setting webhook URLs

#### Using the command line

Add `-wh http://YOUR_WEBHOOK_URL` to your existing command line.

To send data to multiple URLs, add a new `-wh ...` string for each URL, for example:
```
-wh http://YOUR_FIRST_WEBHOOK_URL -wh http://YOUR_SECOND_WEBHOOK_URL
```

#### Using a config file

Add a new line to your config file:
```
webhook: http://YOUR_WEBHOOK_URL
```

To send data to multiple URLs, use an array:
```
webhook: [ http://YOUR_FIRST_WEBHOOK_URL, http://YOUR_SECOND_WEBHOOK_URL ]
```

### Setting webhook types

#### Using the command line

Add `--wh-types WEBHOOK_TYPE` to your existing command line.

To set multiple webhook types, add a new `--wh-types ...` string for each URL, for example:
```
--wh-types pokemon --wh-types raid
```

#### Using a config file

Add a new line to your config file:
```
wh-types: WEBHOOK_TYPE
```

To set multiple webhook types, use an array:
```
wh-types: [ pokemon, raid ]
```

### Filtering Pokémon

To limit the Pokémon that get sent to webhooks you can:
* whitelist specific Pokémon IDs, **or**
* blacklist specific Pokémon IDs

**If you use a whitelist you cannot also use a blacklist (and vice-versa).**

You can whitelist/blacklist Pokémon IDs using either a list or a file. You can use **either** a list **or** a file, but **not both**.

#### Whitelisting Pokémon

If you want to send webhook data for specific Pokémon (and no other Pokémon) you can use a Pokémon whitelist.

**Using a string**

You can a string of Pokémon IDs to whitelist using:
```
webhook-whitelist: [ POKEMON_ID_1, POKEMON_ID_2, POKEMON_ID_3 ]
```

**Using a file**

You can set a whitelist file using:
```
webhook-whitelist-file: WHITELIST_FILE
```

Note: each Pokémon ID must be on a new line.

**Example**

Whitelisting Dratini, Dragonair, Dragonite, Larvitar, Pupitar and Tyranitar using a whitelist array:

`config.ini`:
```
webhook-whitelist: [ 147, 148, 149, 246, 247, 248 ]
```

#### Blacklisting Pokémon

If you want to exclude specific Pokémon from being set to webhooks you can use a Pokémon blacklist.

**Using a string**

You can a string of Pokémon IDs to blacklist using:
```
webhook-blacklist: [ POKEMON_ID_1, POKEMON_ID_2, POKEMON_ID_3 ]
```

**Using a file**

You can set a blacklist file using:
```
webhook-blacklist-file: BLACKLIST_FILE
```
Note: each Pokémon ID must be on a new line.

**Example**

Blacklisting Pidgey, Spearow, Caterpie and Weedle using a blacklist file:

`config.ini`:
```
webhook-blacklist-file: pokemon-blacklist.txt
```

`pokemon-blacklist.txt`:
```
10
13
16
21
```

## Webhook Types

Data is sent to webhooks as a JSON object containing an array of webhook events.

Each webhook event has the structure:
```
{
  "type":    EVENT_TYPE,
  "message": EVENT_DATA
}
```

For example:
```
[
  {
    "type":    "pokemon",
    "message": { ... }
  },
  {
    "type":    "pokemon",
    "message": { ... }
  },
  {
    "type":    "pokemon",
    "message": { ... }
  },
  {
    "type":    "gym",
    "message": { ... }
  }
]
```

RocketMap currently provides the following webhook types: [`pokemon`](#pokemon), [`pokestop`](#pokestop), [`lure`](#lure), [`gym`](#gym), [`gym-info`](#gym-info), [`egg`](#egg), [`raid`](#raid), [`tth`](#tth), [`captcha`](#captcha). Please note that as RocketMap evolves more webhook types may be added.

If you are a developer please feel free to contribute new webhook types through the usual [RocketMap development process](https://github.com/RocketMap/RocketMap/blob/develop/CONTRIBUTING.md#contributing-code).

The sections below outline the different webhook types and the data that gets sent for each event.

### `pokemon`

A `pokemon` event is sent every time RocketMap detects that a Pokémon has spawned.

| Field                   | Details                                                               | Example   |
| ----------------------- | --------------------------------------------------------------------- | --------- |
| `spawnpoint_id`         | The spawnpoint that the Pokémon has appeared at                 | `"47d9e3e05a7"` |
| `encounter_id`          | The unique ID of this Pokémon spawn            | `"MTExMjE5MDExODAyNTczOTg4MjM="` |
| `pokemon_id`            | The Pokémon's ID                                           |                 `91` |
| `latitude`              | The Pokémon's latitude                                     |  `43.62969347887845` |
| `longitude`             | The Pokémon's longitude                                    | `5.2886973939569513` |
| `disappear_time`        | The time at which the Pokémon will disappear (in unix time)     |    `1504056600` |
| `time_until_hidden_ms`  | ???                                                             |    `-809985329` |
| `last_modified_time`    | The time at which the Pokémon was detected                      | `1504048538928` |
| `seconds_until_despawn` | The current number of seconds remaining before the Pokémon disappears |    `1772` |
| `spawn_start`           | The number of seconds past the hour at which the Pokémon appears      |     `911` |
| `spawn_end`             | The number of seconds past the hour at which the Pokémon disappears   |    `2710` |
| `gender`                | The Pokémon's gender<sup>1</sup>                                    |       `2` |
| `cp`                    | The Pokémon's CP<sup>2</sup>                                          |      `""` |
| `form`                  | The Pokémon's form<sup>2</sup>                                        |      `""` |
| `individual_attack`     | The Pokémon's attack IV<sup>2</sup>                                   |      `""` |
| `individual_defense`    | The Pokémon's defence IV<sup>2</sup>                                  |      `""` |
| `individual_stamina`    | The Pokémon's stamina IV<sup>2</sup>                                  |      `""` |
| `cp_multiplier`         | The Pokémon's CP multiplier<sup>2</sup>                               |      `""` |
| `move_1`                | The Pokémon's quick move<sup>2</sup>                                  |      `""` |
| `move_2`                | The Pokémon's charge move<sup>2</sup>                                 |      `""` |
| `weight`                | The Pokémon's weight<sup>2</sup>                                      |      `""` |
| `height`                | The Pokémon's height<sup>2</sup>                                      |      `""` |
| `player_level`          | The level of the account that found the Pokémon                       |       `2` |
| `verified`              | Whether the TTH for the spawn has been identified                     |    `true` |

1. Pokémon genders are represented by the values:

| Value   | Gender     |
| ------- | ---------- |
| `0`     | Unset      |
| `1`     | Male       |
| `2`     | Female     |
| `3`     | Genderless |

2. These fields will be empty unless the Pokémon has been [encountered](https://rocketmap.readthedocs.io/en/develop/extras/encounters.html).

### `pokestop`

A `pokestop` event is sent whenever RocketMap scans a pokestop.

| Field                  | Details                                                             | Example         |
| ---------------------- | ------------------------------------------------------------------- | --------------- |
| `pokestop_id`          | The pokestop's unique ID | `"ZmY2NjNmZGQxZTg1NDgxNG`<br>`E5MDAyNTkwM2ZkZjk2NTMuMTY="` |
| `latitude`             | The pokestop's latitude                                             |      `43.62686` |
| `longitude`            | The pokestop's longitude                                            |      `5.304069` |
| `enabled`              | Whether the pokestop can be interacted with                         |          `true` |
| `last_modified`        | The time at which the pokestop last changed                         | `1501611306167` |
| `active_fort_modifier` | ???                                                                 |             ??? |
| `lure_expiration`      | The time at which the current lure expires                          |             ??? |

### `lure`

A `lure` event is sent whenever RocketMap scans a pokestop **if that pokestop has been lured**.

**Important: while the webhook type name for `lure` events is `lure`, when this data is sent to a webhook the `type` field will be `pokestop`.**

Note: if you add `lure` events to your `wh_types` you will receive them even if you have not enabled `pokestop` events.
                                                       
Lure events contain the same fields as `pokestop` events (described above).

### `gym`

A `gym` event is sent whenever RocketMap scans a gym.

| Field                       | Details                                                    | Example             |
| --------------------------- | ---------------------------------------------------------- | ------------------- |
| `gym_id`                    | The gym's unique ID | `"YmQ5MDc4ZjJiNTNjNGE0Ym`<br>`JhOGI0YTIyYzZjOTRhYmUuMTY="` |
| `latitude`                  | The gym's latitude                                         |         `43.568213` |
| `longitude`                 | The gym's longitude                                        |          `5.296438` |
| `enabled`                   | Whether the gym can be interacted with                     |              `true` |
| `team_id`                   | The team that currently controls the gym<sup>1</sup>       |                 `1` |
| `occupied_since`            | The time at which the controlling team took the gym        |        `1504047118` |
| `last_modified`             | The time at which the gym last changed<sup>2</sup>         |     `1504047134624` |
| `guard_pokemon_id`          | The ID of the Pokémon which is displayed on top of the gym |               `149` |
| `total_cp`                  | The total of the defending Pokémons' CPs                   |              `3853` |
| `slots_available`           | The number of spaces available                             |                 `4` |
| `lowest_pokemon_motivation` | The lowest of the defending Pokémons' motivations         | `0.892739474773407` |
| `raid_active_until`         | The time at which the current raid finishes<sup>3</sup>    |                 `0` |


1. The teams are represented by the values:

| Value   | Team        |
| ------- | ----------- |
| `0`     | Uncontested |
| `1`     | Mystic      |
| `2`     | Valor       |
| `3`     | Instinct    |

2. Gym changes include: Pokémon being added, Pokémon being knocked out, gym control changing etc.
3. If there is no raid at the gym this value will be `0`.

### `gym-info`

A `gym-info` event is sent whenever RocketMap fetches a gym's details.

**Important: while the webhook type name for `gym-info` events is `gym-info`, when this data is sent to a webhook the `type` field will be `gym_details`.**

| Field         | Details                                                | Example                 |
| ------------- | ------------------------------------------------------ | ----------------------- |
| `id`          | The gym's unique ID | `"MzcwNGE0MjgyNThiNGE5NW`<br>`FkZWIwYTBmOGM1Yzc2ODcuMTE="` |
| `name`        | The gym's name                                         | `"St. Clements Church"` |
| `description` | The gym's description                                  |                    `""` |
| `url`         | A URL to the gym's image        | `"http://lh3.googleusercontent.com/image_url"` |
| `latitude`    | The gym's latitude                                     |             `43.633181` |
| `longitude`   | The gym's longitude                                    |              `5.296836` |
| `team`        | The team that currently controls the gym               |                     `1` |
| `pokemon`     | An array containing the Pokémon currently in the gym   |                    `[]` |

**Gym Pokémon:**

| Field                      | Details                                                  | Example      |
| -------------------------- | -------------------------------------------------------- | ------------ |
| `trainer_name`             | The name of the trainer that the Pokémon belongs to   | `"johndoe9876"` |
| `trainer_level`            | The trainer's level<sup>1</sup>                          |         `34` |
| `pokemon_uid`              | The Pokémon's unique ID                         | `4348002772281054056` |
| `pokemon_id`               | The Pokémon's ID                                         |        `242` |
| `cp`                       | The Pokémon's base CP                                    |       `2940` |
| `cp_decayed`               | The Pokémon's current CP                                 |        `115` |
| `stamina_max`              | The Pokémon's max stamina                                |        `500` |
| `stamina`                  | The Pokémon's current stamina                            |        `500` |
| `move_1`                   | The Pokémon's quick move                                 |        `234` |
| `move_2`                   | The Pokémon's charge move                                |        `108` |
| `height`                   | The Pokémon's height                              | `1.746612787246704` |
| `weight`                   | The Pokémon's weight                              | `51.84344482421875` |
| `form`                     | The Pokémon's form                                       |          `0` |
| `iv_attack`                | The Pokémon's attack IV                                  |         `12` |
| `iv_defense`               | The Pokémon's defense IV                                 |         `14` |
| `iv_stamina`               | The Pokémon's stamina IV                                 |         `14` |
| `cp_multiplier`            | The Pokémon's CP multiplier                      | `0.4785003960132599` |
| `additional_cp_multiplier` | The Pokémon's additional CP multiplier                   |        `0.0` |
| `num_upgrades`             | The number of times that the Pokémon has been powered up |         `31` |
| `deployment_time`          | The time at which the Pokémon was added to the gym       | `1504361277` |

1. The trainer's level at the time that they added their Pokémon to the gym.

### `egg`

An `egg` event is sent whenever RocketMap detects that an egg has appeared at a gym.

**Important: while the webhook type name for `egg` events is `egg`, when this data is sent to a webhook the `type` field will be `raid`.**

Note: `egg` events use the same event type and fields as `raid` events, but the Pokémon-specific fields such as `pokemon_id` will be `null`.

| Field        | Details                                                           | Example      |
| ------------ | ----------------------------------------------------------------- | ------------ |
| `gym_id`     | The gym's unique ID | `"NGY2ZjBjY2Y3OTUyNGQyZW`<br>`FlMjc3ODkzODM2YmI1Y2YuMTY="` |
| `latitude`   | The gym's latitude                                                |  `43.599321` |
| `longitude`  | The gym's longitude                                               |   `5.181415` |
| `spawn`      | The time at which the raid spawned                                | `1500992342` |
| `start`      | The time at which the raid starts                                 | `1501005600` |
| `end`        | The time at which the raid ends                                   | `1501007400` |
| `level`      | The raid's level                                                  |          `5` |
| `pokemon_id` | For egg events this will always be `null`                         |       `null` |
| `cp`         | For egg events this will always be `null`                         |       `null` |
| `move_1`     | For egg events this will always be `null`                         |       `null` |
| `move_2`     | For egg events this will always be `null`                         |       `null` |

### `raid`

A `raid` event is sent whenever RocketMap detects that a raid has started at a gym.

Note: `raid` events use the same event type and fields as `egg` events, but the Pokémon-specific fields such as `pokemon_id` will be populated.

| Field        | Details                                                           | Example      |
| ------------ | ----------------------------------------------------------------- | ------------ |
| `gym_id`     | The gym's unique ID | `"NGY2ZjBjY2Y3OTUyNGQyZW`<br>`FlMjc3ODkzODM2YmI1Y2YuMTY="` |
| `latitude`   | The gym's latitude                                                |  `43.599321` |
| `longitude`  | The gym's longitude                                               |   `5.181415` |
| `spawn`      | The time at which the raid spawned                                | `1500992342` |
| `start`      | The time at which the raid starts                                 | `1501005600` |
| `end`        | The time at which the raid ends                                   | `1501007400` |
| `level`      | The raid's level                                                  |          `5` |
| `pokemon_id` | The raid boss's ID                                                |        `249` |
| `cp`         | The raid boss's CP                                                |      `42753` |
| `move_1`     | The raid boss's quick move                                        |        `274` |
| `move_2`     | The raid boss's charge move                                       |        `275` |

### `tth`

A `tth` event is sent whenever a scan instance's TTH completion status changes by more than 1%.

**Important: while the webhook type name for `tth` events is `tth`, when this data is sent to a webhook the `type` field will be `scheduler`.**

Note: at present only the `speed-scan` scheduler sends `tth` events.

| Field          | Details                                                     | Example       |
| -------------- | ----------------------------------------------------------- | ------------- |
| `name`         | The type of scheduler which performed the update            | `"SpeedScan"` |
| `instance`     | The status name of scan instance which performed the update |  `"New York"` |
| `tth_found`    | The completion status of the TTH scan                       |      `0.9965` |
| `spawns_found` | The number of spawns found in this update                   |           `5` |

### `captcha`

A `captcha` event is sent whenever a scan worker encounters a captcha.

Note: at present it is not possible to disable `captcha` events: they will be sent regardless of your `wh-types` settings.

| Field         | Details                                                   | Example           |
| ------------- | --------------------------------------------------------- | ----------------- |
| `status_name` | The status name of the account which received the captcha |      '"New York"` |
| `account`     | The name of the account that received the captcha         | `"silverwind268"` |
| `status`      | The captchas status<sup>1</sup>                           |       `"success"` |
| `captcha`     | The number of captchas that the account has received      |               `1` |
| `time`        | The time taken to resolve the captcha                     |              `11` |
| `mode`        | The captcha solving method, either `manual` or `2captcha` |      `"2captcha"` |

1. Possible captcha statuses:

| Status        | Description                                |
| ------------- | ------------------------------------------ |
| `"encounter"` | A captcha has been detected                |
| `"success"`   | The captcha has been solved                |
| `"failure"`   | The captcha has not been solved            |
| `"error"`     | An error occurred while solving the captcha |

## PokeAlarm

[PokeAlarm](https://github.com/RocketMap/PokeAlarm) is an application which can be used to send alerts for various events.

PokeAlarm receives data from RocketMap through webhooks, processes and filters the data, and can then send event-specific alerts through messaging services such as Twitter and Discord.

A full list of the events PokeAlarm can provide alerts for, as well as the messaging services that can be used, can be found in the [PokeAlarm wiki](https://github.com/RocketMap/PokeAlarm/wiki).

## RocketMap Public Webhook

RocketMap is collecting data for an upcoming project. If you would like to help our efforts please fill out [this form](https://goo.gl/forms/ZCx6mQNngr0bAvRY2). You will then receive an email with a webhook url which you can add to your list of webhooks.
