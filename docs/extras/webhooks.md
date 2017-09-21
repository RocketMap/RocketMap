# Webhooks

Webhooks have been implemented into RocketMap. Using these webhooks are simple, and opens up a new realm of possibilities for over almost anything related to RocketMap.

## How Do RocketMap Webhooks Work?

Every time an event occurs (e.g. a Pokemon spawns) a POST request will be sent to a provided URL containing information about that event. A developer may create a listener in whatever language they feel most comfortable in (it just has to handle incoming connections, after all) and do certain things when information from the webhook is received. For example, a developer would be able to wait for a Dragonite to spawn, then play a loud alarm throughout the house and flash the lights in order to get their attention. All of this could be done without even the slightest touch to the internal RocketMap code, so there's no risk to break anything.

## Types of Webhooks

Pokemon Spawn webhooks are available. 
If you're a developer, feel free to contribute by creating some more webhooks.

* `pokemon` - Emitted every time a Pokemon spawns.
* `gym` - Emitted when finding a gym.
* `pokestop` - Emitted when finding a pokestop.
* `pokestop_lured` - Emitted every time a Pokestop is lured.
* `gym_defeated` -  Emitted every time a Gym is defeated (prestige changes)
* `gym_conquered` -  Emitted every time the owner of a Gym is changed

## Configuring Webhooks
Add `-wh http://my-webhook/location` argument when starting RocketMap (runserver.py) to define the location of your webhook. You can add multiple webhook locations to a single -wh argument to define multiple webhooks.


### To use this, RocketMap would be run with the following parameters:

```
python runserver.py -a ptc -u [username] -p [password] -l "Location or lat/lon" -st 15 -k [google maps api key] -wh http://localhost:9876
```

## Configuring Webhook filter types
Use `wh-types` to configure webhook types that should get sent.

The list of valid types are:
* `pokemon`
* `gym`
* `raid`
* `egg`
* `tth`
* `gym-info`
* `pokestop`
* `lure`

Example to send the webhook messages pokemon, gym, raid and gym-info:

```
wh-types: [pokemon, gym, raid, gym-info]
```

## Filtering Pokémon
To filter what Pokémon get sent to the webhooks, you can configure a whitelist of Pokémon IDs (one per line).

For example, if we only want to sent data on dratini, dragonair, dragonite, larvitar, pupitar and tyranitar, add this to your configuration:

```
webhook-whitelist-file: pokemon-whitelist.txt
```

And add the Pokémon IDs to the pokemon-whitelist.txt file:

```
147
148
149
246
247
248
```

## RocketMap Public Webhook

RM is collecting data for an upcoming project. If you would like to donate your data, please fill out [this form](https://goo.gl/forms/ZCx6mQNngr0bAvRY2) and add `-wh [your webhook URL here]` to your command line. 

## PokeAlarm

PokeAlarm is an example of a script you can run to accept webhook data and send it elsewhere. In PokeAlarm's usage it is publishing that information on Facebook, Twitter, Discord, etc. 

[Learn More Here](https://github.com/RocketMap/PokeAlarm)


## Webhook Data

The POST request made by RocketMap will contain the following data for pokemon type webhooks:

```json
{
   "message":{
      "disappear_time":1493734519,
      "form":null,
      "seconds_until_despawn":1748,
      "spawnpoint_id":"0d24fec01e7",
      "cp_multiplier":null,
      "move_2":null,
      "height":null,
      "time_until_hidden_ms":915847883,
      "last_modified_time":1493732771124,
      "cp":null,
      "encounter_id":"AzMxMjYyNjhWeDI4ODgwNjI1Mg==",
      "spawn_end":919,
      "move_1":null,
      "individual_defense":null,
      "verified":true,
      "weight":null,
      "pokemon_id":187,
      "player_level":6,
      "individual_stamina":null,
      "longitude":0,
      "spawn_start":0,
      "pokemon_level":null,
      "gender":null,
      "latitude":0,
      "individual_attack":null
   },
   "type":"pokemon"
}
```
