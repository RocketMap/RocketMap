
# PokemonGo Map ![Python 2.7](https://img.shields.io/badge/python-2.7-blue.svg) [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/PoGoMapDev) [![Build Status](https://travis-ci.org/PokemonGoMap/PokemonGo-Map.svg?branch=develop)](https://travis-ci.org/PokemonGoMap/PokemonGo-Map)


#[Twitter] (https://twitter.com/PokemapDevRE), [Website] (https://pokemongomap.github.io/PoGoMapWebsite/)#

For general support, join [our discord server](https://discord.gg/uAmEkcu).

Live visualization of all the pokemon (with option to show gyms and pokestops) in your area. This is a proof of concept that we can load all the pokemon visible nearby given a location. Currently runs on a Flask server displaying Google Maps with markers on it.

Features: 

* Shows Pokemon, Pokestops, and gyms with a clean GUI.
* Notifications 
* Lure information
* Multithreaded mode
* Filters
* Independent worker threads (many can be used simulatenously to quickly generate a livemap of a huge geographical area)
* Localization (en, fr, pt_br, de, ru, ja, zh_tw, zh_cn, zh_hk)
* DB storage (sqlite or mysql) of all found pokemon
* Incredibly fast, efficient searching algorithm (compared to everything else available)

[![Deploy](https://raw.githubusercontent.com/sych74/PokemonGo-Map-in-Cloud/master/images/deploy-to-jelastic.png)](https://jelastic.com/install-application/?manifest=https://raw.githubusercontent.com/sych74/PokemonGo-Map-in-Cloud/master/manifest.jps) [![Deploy on Scalingo](https://cdn.scalingo.com/deploy/button.svg)](https://my.scalingo.com/deploy?source=https://github.com/PokemonGoMap/PokemonGo-Map#develop)


![Map](https://camo.githubusercontent.com/61d585e7706d136694f50ed2a092661b203a0a5d/687474703a2f2f70676d2e72656164746865646f63732e696f2f656e2f6c61746573742f5f696d616765732f636f7665722e706e67)

## How to setup

For instructions on how to setup and run the tool, please refer to the project [wiki](https://github.com/PokemonGoMap/PokemonGo-Map/wiki), or the [video guide](https://www.youtube.com/watch?v=2ACJHCNZ3ow).


## Android Version

There is an [Android port](https://github.com/omkarmoghe/Pokemap) in the works. All Android related prs and issues please refer to this [repo](https://github.com/omkarmoghe/Pokemap).

## iOS Version

There is an [iOS port](https://github.com/istornz/iPokeGo) in the works. All iOS related prs and issues please refer to this [repo](https://github.com/istornz/iPokeGo).


## Contributions

Please submit all pull requests to [develop](https://github.com/PokemonGoMap/PokemonGo-Map/tree/develop) branch.

Building off [tejado's python pgoapi](https://github.com/tejado/pgoapi), [Mila432](https://github.com/Mila432/Pokemon_Go_API)'s API, [leegao's additions](https://github.com/leegao/pokemongo-api-demo/tree/simulation) and [Flask-GoogleMaps](https://github.com/rochacbruno/Flask-GoogleMaps). Current version relies primarily on the pgoapi and Google Maps JS API.
