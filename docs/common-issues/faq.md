# Common Questions and Answers

### Should I use this as a way to make money?

No, it is gross to charge people for maps when the information should be provided by Niantic! We do not endorse paid maps, which is why this platform is opensource.

### What do the spawn point colors mean?

* A **grey** dot represents a spawn point that is more than 5 minutes from spawning.
* A **light blue** dot represents a spawn point that will spawn in 5 minutes. **Light blue** changes to **dark blue** and finally into **purple** just before spawn time.
* A **green dot** represents a fresh spawn. This will transition to **yellow**, through **orange** and finally **red** (like a stop light) as it is about to despawn.

### All I see are numbers! Where are the pokemon?

You are missing the sprite files. Please consult #faq on the [RocketMap Discord](https://discord.gg/rocketmap).

### Lures are 6 hours right now! Why is it saying they have already expired?

You need to add `-ldur 360` to change the lure assumption to 6 hours (360 minutes.)

### Can I sign in with Google?

Yes you can! Pass the flag `-a google` (replacing `-a ptc`) to use Google authentication.

If you happen to have 2-step verification enabled for your Google account you will need to supply an [app password](https://support.google.com/accounts/answer/185833?hl=en) for your password instead of your normal login password.

### Which is the best scan option to use to find pokemon?

SpeedScan (`-speed`) is the most used scheduler: it's the only scheduler that currently supports finding the proper spawnpoint time and duration, and it also features a built-in speed limiter to avoid speed violations (i.e. softbans).

More information can be found here : [Speed Scheduler](http://rocketmap.readthedocs.io/en/develop/scanning-method/Speed-Scheduler.html)

### But I was happy using the default Hex or -ss...

Speed Scheduler combines both and is more efficient, -ss is not being actively maintained and doesn't work unless you already have spawnpoints and timers exported.

### All pokemon disappear after only 1 minute, the map is broken!

One of Niantic's updates removed spawn timers from Pokémon (until there's little time left until they despawn). SpeedScan does an initial scan to determine all spawn points and their timers and automatically transitions into spawn scanning once it found them all.
Seeing 1-minute timers during initial scan is perfectly normal.

### What's the simplest command to start the map scanning?

./runserver.py -speed -l LOCATION -a GOOGLE/PTC -u USER -p PASS -k GOOGLEKEY -hk HASHINGHEY
You must replace the values for GOOGLE,PTC/LOCATION/USER/PASS/GOOGLEKEY/HASHINGKEY with your information.

### Nice, what other stuff can I use in the command line?

There is a list [here](http://rocketmap.readthedocs.io/en/develop/first-run/commandline.html) or a more up to date list can be found by running ./runserver.py -h

### Woah I added a ton of cool stuff and now my command line is massive, any way to shorten it?

It is a lot simplier to use a [config file](http://rocketmap.readthedocs.io/en/develop/first-run/configuration-files.html)

### Can I scan for free or do I need to pay for a hashing key?

Using a [hashing  key](https://hashing.pogodev.org/) is mandatory at this point. The API will not function without an active hashing key from Bossland. [More Informatiion about Hashing Keys](https://rocketmap.readthedocs.io/en/develop/first-run/hashing.html)

### Is there anything I can do to lower captchas?

Yes, you can run with `-tut` to level your workers to level two (spinning a single pokéstop), this reduces captchas a lot. You may also consider scanning a smaller area, using less workers or encountering less pokemon for IV.

### How many workers do I need?

There is no simple answer to this, it all depends on your -st and more importantly how spawn dense that location is.  
For a rough guide you can use the formulas at the bottom of this page.

### example.py isn't working right!

Seb deleted it, it was the only good thing left in our lives. Seb has murdered us all.

### I have problems with my database because......

RocketMap uses SQLite which doesn't support real concurrency, so you're limited directly by the read/write speed of your drive and you're hoping that nothing happens concurrently (otherwise it breaks).

Higher threads or extra workers = increased odds of SQLite locking up. sqlite also has a very low limit of number of variables that can be used in a single query, which breaks support for medium or large sized maps.

You need [MySQL](http://rocketmap.readthedocs.io/en/develop/extras/mysql.html) if you want a proper database.

### How do I setup port forwarding?

[See this helpful guide](http://rocketmap.readthedocs.io/en/develop/extras/external.html)

### I edited my files/installed unfinished code and messed up, will you help me fix it?

No, the best course of action is to delete it all and start again, this time don't edit files unless you know what you are doing.

### I used a PR and now everything is messed up! HELP ME!

No, remove everything and start from scratch. A Pull Request is merged when it meets the standards of the project.

### “It’s acting like the location flag is missing.”

-l, never forget.

### I overridden watchdog and now all my accounts are flagged/banned.

Good Job! We recommend making new accounts. [Current Tools are Here!](https://rocketmap.readthedocs.io/en/develop/extras/Community-Tools.html)

### I'm getting this error...

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

```
InternalError(1054, u"unknown column 'cp' in 'field list'") or similar
```

Only one instance can run when the database is being modified or upgraded. Run ***ONE*** instance of RM with `-cd` to wipe your database, then run ***ONE*** instance of RM (without `-cd`) to setup your database.

```
ValueError: Exceeded maximum connections.
```

Try raising --db-max_connections, default is 5.

```
OperationalError(1040, u'Too many connections')
```

You need to raise the maximum connections allowed on your MySQL server configuration, this is typically by setting `max_connections` in my.cnf or my.ini. Please use Google to find where this file is located on your specific operating system.

```
OperationalError: too many SQL variables
```

Due to SQLite supporting only a small amount of variables in a single query, you will need to use MySQL as you are above said limit. This is typically due to the adding of more workers/area to your map.

## I have more questions!

Please read all wiki pages relating to the specific function you are questioning. If it does not answer your question, join us on the [RocketMap Discord](https://discord.gg/rocketmap). Before asking questions in #help on Discord, make sure you've read #announcements and #faq.

## Formulas?

st=step distance  
sd=scan delay [default: 10]  
w=# of workers  
t=desired scan time  

### Speed Scan

Workers for initial scan(speed scan):  
Workers = Cells / 20, Cells = (((steps * (steps - 1)) * 3) + 1)  
an example for st 19: (((19 * 18) * 3) +1 ) / 20 = 51.35 so use 52 workers.  
You will not need as many accounts once initial scan is complete.

### Hex scan
time to scan: (sd/w)*(3st^2-3st+1)  
time to scan (using default scan delay): (10/w)*(3st^2-3st+1)

workers needed: (sd/t)*(3st^2-3st+1)  
workers needed (using default scan delay): (10/t)*(3st^2-3st+1)
