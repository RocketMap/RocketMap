# Common Questions and Answers

## Critical Error "Missing sprite files"

Please consult #faq on the [RocketMap Discord](https://discord.gg/PWp2bAm).

## Can I sign in with Google?

Yes you can! Pass the flag `-a google` (replacing `-a ptc`) to use Google authentication.

If you happen to have 2-step verification enabled for your Google account you will need to supply an [app password](https://support.google.com/accounts/answer/185833?hl=en) for your password instead of your normal login password.

## Which is the best scan option to use to find pokemon?

SpeedScan (`-speed`) is the most used scheduler: it's the only scheduler that currently supports finding the proper spawnpoint time and duration, and it also features a built-in speed limiter to avoid speed violations (i.e. softbans).

More information can be found here : [Speed Scheduler](http://rocketmap.readthedocs.io/en/develop/extras/Speed-Scheduler.html)

## But I was happy using the default Hex or Spawnpoint scanning...

Speed- Scheduler combines both and is more efficient.

## Should I swap back to spawn point scanning after the speed-scheduler has done its initial scan?

No, it will automatically scan spawnpoints.

## All pokemon disappear after only 1 minute, the map is broken!

One of Niantic's updates removed spawn timers from Pokémon (until there's little time left until they despawn). SpeedScan does an initial scan to determine all spawn points and their timers and automatically transitions into spawn scanning once it found them all. 
Seeing 1-minute timers during initial scan is perfectly normal.

## What's the simplest command to start the map scanning?

./runserver.py -speed -l LOCATION -u USER -p PASS -k GOOGLEKEY
You must replace the values for LOCATION/USER/PASS/GOOGLEKEY with your information.

## Nice, what other stuff can I use in the command line?

There is a list [here](http://rocketmap.readthedocs.io/en/develop/extras/commandline.html) or a more up to date list can be found by running ./runserver.py -h 

## Woah I added a ton of cool stuff and now my command line is massive, any way to shorten it?

It is a lot simplier to use a [config file](http://rocketmap.readthedocs.io/en/develop/extras/configuration-files.html)

## Can I scan for free or do I need to pay for a hash key?

You can use the the free api but be aware that using an api that is older than the game currently uses makes it easy for Niantic to see that you are not using the game client. This can get your accounts flagged for increased captcha rate or even account bans. Using a [hash key](https://hashing.pogodev.org/) uses the latest api and reduces captchas or removes them almost completely.

## Is there anything I can do to lower captchas on either api version?

Yes, you can level your workers to level two (spin a single pokéstop manually), this reduces captchas a lot. You may also consider scanning a smaller area, using less workers or encountering less pokemon for IV.

## How many workers do I need?

There is no simple answer to this, it all depends on your -st and more importantly how spawn dense that location is.  
For a rough guide you can use the formulas at the bottom of this page.

## example.py isn't working right!

10/10 would run again

## I have problems with my database because......

RocketMap uses SQLite which doesn't support real concurrency, so you're limited directly by the read/write speed of your drive and you're hoping that nothing happens concurrently (otherwise it breaks).

Higher threads or extra workers = increased odds of SQLite locking up. sqlite also has a very low limit of number of variables that can be used in a single query, which breaks support for medium or large sized maps.

You need [MySQL](http://rocketmap.readthedocs.io/en/develop/extras/mysql.html) if you want a proper database.

## How do I setup port forwarding?

[See this helpful guide](http://rocketmap.readthedocs.io/en/develop/extras/external.html)

## I edited my files/installed unfinished code and messed up, will you help me fix it?

No, the best course of action is to delete it all and start again, this time don't edit files unless you know what you are doing.

## “It’s acting like the location flag is missing.”

-l, never forget.

## I'm getting this error...

```
pip or python is not recognized as an internal or external command
```

[Python/pip has not been added to the environment](http://rocketmap.readthedocs.io/en/develop/extras/environment-variables-fix.html)

```.md
Exception, e <- Invalid syntax.
```

This error is caused by Python 3. The project requires python 2.7

```
error: command 'gcc' failed with exit status 1

# - or -

[...]failed with error code 1 in /tmp/pip-build-k3oWzv/pycryptodomex/
```

Your OS is missing the `gcc` compiler library. For Debian, run `apt-get install build-essentials`. For Red Hat, run `yum groupinstall 'Development Tools'`

```
cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']

KeyError: 'map_cells'
```

The account is banned or hasn't completed the tutorial.


## I have more questions!

Please read the [Wiki](http://rocketmap.readthedocs.io/en/develop/extras/configuration-files.html) for information and then join us on the [RocketMap Discord](https://discord.gg/PWp2bAm). Before asking questions in #help on Discord, make sure you've read #announcements and #faq.

## Formulas?

st=step distance  
sd=scan delay [default: 10]  
w=# of workers  
t=desired scan time  

## Speed Scan

Workers for initial scan(speed scan):  
Workers = Cells / 20, Cells = (((steps * (steps - 1)) * 3) + 1)  
an example for st 19: (((19 * 18) * 3) +1 ) / 20 = 51.35 so use 52 workers.  
You will not need as many accounts once initial scan is complete.

## Hex scan
time to scan: (sd/w)*(3st^2-3st+1)  
time to scan (using default scan delay): (10/w)*(3st^2-3st+1)

workers needed: (sd/t)*(3st^2-3st+1)  
workers needed (using default scan delay): (10/t)*(3st^2-3st+1)
