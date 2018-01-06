# Account leveling
RocketMap completes the tutorial steps on all accounts on first log in and sets a Pokémon as buddy if it does not have one.

Accounts with level 1 will get captchas after some time and will stop working unless you setup [catpcha handling](http://rocketmap.readthedocs.io/en/develop/first-run/captchas.html):


To avoid this, it's recommended to level accounts at least to level 2. It's as simple as spin a Pokéstop and there are two ways to do so from RM:

 * Enabling pokestop spinning during regular scanning
 * Using the level-up tool provided with RM

## Pokéstop Spinning

To enable Pokéstop spinning, add pokestop-spinning to your configuration file, or -spin to your cli parameters.

```
pokestop-spinning
```

With this setting enabled, RM's scanner instances will try to spin a Pokéstop (50% chance to spin if the account has a level greater than 1) if it's within range and the `--account-max-spins` limit hasn't been reached (default is 20 per account per hour).

This setting could be enough for some maps with a high density of Pokéstops, as the accounts will get near one soon enough to avoid the captcha, otherwise you will need to enable [catpcha handling](http://rocketmap.readthedocs.io/en/develop/first-run/captchas.html) to keep them working until until there is a Pokéstop within range.

## Level-up tool

In the tools folder there is a small python script that will go through the account list, send a map request at a location, and spin all Pokéstops in range (following `account-max-spins` limit). With this tool, you can make sure all accounts are level 2 before using them for scanning.

The tool uses the same config file and options as RM (the ones that apply) so the setup and run is pretty simple, just change the location to some coordinates that are near 1 or more Pokéstops and change the worker setting to the number of accounts you want to level up simultaneously.

In the console you will see the initial level of each account, the Pokéstop spinning and the final level. The script will end automatically when all accounts have finished the process or have failed 3 times.

To run the script, go to RM's root folder and execute:

```
python tools/levelup.py
```

All command line flags available in RM can be used here too (b(but not all of them will have an effect). So you could increase `account-max-spins` and change location and workers from the command line without needing to modify the config file with something like:

```
python tools/levelup.py -w 30 -l 40.417281,-3.683235 -ams 1000
```
