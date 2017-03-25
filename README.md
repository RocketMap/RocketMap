
# RocketMap

![Python 2.7](https://img.shields.io/badge/python-2.7-blue.svg) ![License](https://img.shields.io/github/license/RocketMap/RocketMap.svg) [![Build Status](https://travis-ci.org/RocketMap/RocketMap.svg?branch=develop)](https://travis-ci.org/RocketMap/RocketMap)

Live visualization of all the pokemon (with option to show gyms and pokestops) in your area. This is a proof of concept that we can load all the pokemon visible nearby given a location. Currently runs on a Flask server displaying Google Maps with markers on it.

![Map](https://camo.githubusercontent.com/61d585e7706d136694f50ed2a092661b203a0a5d/687474703a2f2f70676d2e72656164746865646f63732e696f2f656e2f6c61746573742f5f696d616765732f636f7665722e706e67)

## Features:

* Shows Pokemon, Pokestops, and gyms with a clean GUI.
* Notifications
* Lure information
* Multithreaded mode
* Filters
* Independent worker threads (many can be used simulatenously to quickly generate a livemap of a huge geographical area)
* Localization (en, fr, pt_br, de, ru, ko, ja, zh_tw, zh_cn, zh_hk)
* DB storage (sqlite or mysql) of all found pokemon
* Incredibly fast, efficient searching algorithm (compared to everything else available)

## Information
* [Discord](https://discord.gg/rocketmap) for general support
* [Documentation](https://rocketmap.readthedocs.io/) for installation and usage docs
* [vote.devkat.org](http://vote.devkat.org) to request new features
* [Github Issues](https://github.com/RocketMap/RocketMap/issues) for reporting bugs (not for support!)

## Installation

For instructions on how to setup and run the tool, please refer to the project [documentation](https://rocketmap.readthedocs.io).

## Deployment

**Please note, deployments are not supported officially. You are using these deployment links at your own risk.**
[![Deploy](https://raw.githubusercontent.com/RocketMap/PokemonGo-Map-in-Cloud/master/images/deploy-to-jelastic.png)](https://jelastic.com/install-application/?manifest=https://raw.githubusercontent.com/RocketMap/PokemonGo-Map-in-Cloud/master/manifest.jps) [![Deploy on Scalingo](https://cdn.scalingo.com/deploy/button.svg)](https://my.scalingo.com/deploy?source=https://github.com/RocketMap/RocketMap#develop)

## Contributions

Please submit all pull requests to [develop](https://github.com/RocketMap/RocketMap/tree/develop) branch.

Building off [tejado's python pgoapi](https://github.com/tejado/pgoapi), [Mila432](https://github.com/Mila432/Pokemon_Go_API)'s API, [leegao's additions](https://github.com/leegao/pokemongo-api-demo/tree/simulation) and [Flask-GoogleMaps](https://github.com/rochacbruno/Flask-GoogleMaps). Current version relies primarily on the pgoapi and Google Maps JS API.

Discord icon: "Rocket" by Flat Icons (flaticon.com)
