# Speed Scheduler

Speed Scheduler is an alternative scheduler to Hex Scan or Spawnpoint Scan with a speed limit and full support for spawnpoint discovery, exact spawnpoint spawntime and duration identification, and automatic transition from spawnpoint discovery to identification to only scanning spawnpoints.

## Features

* Limit speed according to default of 35 kph or by setting -kph
* Do an initial scan of the full area, then automatically switch to tracking down the exact spawn time (finding the TTH) and only scan for spawns (an -ss like behaviour).
* Add spawn point type identification of the three current types of spawn points -- 15, 30, and 60 minute spawns.
* Change spawn point scans to correct spawn time according to spawnpoint type
* Add scans to complete identification for partially identified spawn points
* Dynamically identify and check duration of new spawn points without requiring return to Hex scanning
* Identify spawn points that have been removed and stop scanning them

To use Speed Scheduler, always put -speed in the command line or set `speed-scan` in your config file.

## Commands and configs

What command line args should I use for Speed Scheduler?

> Here's an example: `runserver.py -speed -st 25 -w 100 -ac accounts.csv`

How big should I make my -st?

> Speed Scheduler works best with -st larger than 20. For smaller -st, more instances will be required to handle a large area, and the workers will not be able to help each other because they are walled off into separate instances.

What should I set scan delay (-sd) to?

> With the default speed limit of 35 kph, scan delay isn't needed. It takes about 12 seconds to get to a neighboring location, which is sufficient delay. If you include an -sd lower than 12 seconds, it won't have an effect. If you use a -sd higher than 12, it will decrease the amount of scans your workers can do.

Is there a different command line option to tell Speed Scheduler to do an initial scan or to do -ss (spawnpoint based scanning)?

> Speed workers are independent and look for the best scans they reach under the speed limit. The priority is initial scans, TTH, and then spawns. If a worker can not reach an initial scan under the speed limit, it will do a TTH search. If it can't do an initial scan or a TTH search, it will scan for new pokemon spawns, so all workers are always doing their best to find pokemon. Always put -speed in the command line or set `speed-scan` in your config file.

Does Speed Scheduler work with beehives (-bh argument)?

> Yes, although before using beehives, it's first recommended to use larger -st. The logic of Speed Scheduler scheduler works with the beehives, but the strength of Speed Scheduler is it's ability to have multiple workers in a single hive working together to cover the closest spawns. If the area you have to cover is so large (> -st 50?) that CPU load is becoming an issue, then using -bh in combination with -wph (--workers_per_hive) to set more workers per hive may be helpful.

Does Speed Scheduler work with no-jitter (-nj)?

> Yes. Jitter adjusts only the location sent to the API, not the location used internally, so Speed Scheduler can still recognize the location.

Does Speed Scheduler work with spawn point json lists?

> No. I'm not aware of a method to populate the Spawnpoint DB table with a JSON list. Writing and testing and publishing such a method left as an exercise for the reader.

You mean I will need to do an initial scan again? Oh, the captchas! Oh, the humanity!

> I feel your pain. At least I can tell you that Speed Scheduler will do the initial scan and find the TTHs with less scans than any other Scheduler. Hex Scheduler would take 60 scans to find spawn points and TTH, whereas Speed Scheduler will only take 5 scans per location to find the spawn points, and perhaps another 5 scans to find the TTH per spawn point, so it's about one fifth of the scans other schedulers require.

## General

How long does the initial scan take?

> With sufficient workers, the initial scan to find all the spawnpoints should be completed in a little over an hour.

I'm doing the initial scan, and the spawns have a duration under 1 minute. Why?

> Speed Scheduler doesn't make assumptions about how long the spawns are, so when it first sees a spawn, if there's no TTH, all it can say is that the spawn will be there for at least 60 seconds. After the initial scan is done, durations will be longer.

How does Speed Scheduler find the time_til_hidden or TTH?

> At the last minute or so of a Pokemon spawn, the servers include a time stamp of when the pokemon will disappear, called the time_til_hidden (TTH). Until the TTH is found, spawns are scanned twice -- once when they first spawn and again at the end of their spawn window to find the time_til_hidden and get the exact spawn time. Speed Scheduler searches for the TTH by doing a search between the last seen time and 15 minutes after. If the spawn isn't there at this time, it searches again between that last seen time and earliest unseen time. Next check is between those times again, and so on. This reduces the time where the TTH could be by about half every search, so it should find the TTH within five or so searches.

Speed Scheduler has been running for days, but the TTH found is still about 99%. Why doesn't it find 100% of the TTH?

> There appear to be some rare spawns that are not simple 15, 30, or 60 minute spawns. These spawns may have hidden times or not end with a TTH period. Also, as the possible window for where the TTH could be gets smaller, the time for a worker to scan that location also becomes smaller, so it takes longer to hit the window and find the TTH.

Does Speed Scheduler still find new spawns even if TTH complete is less than 100%?

> Yes. For the few spawns where the TTH still hasn't been found, there is usually only a few minutes when it could be, so Speed Scheduler still queues those new spawns and is probably only late to scan them by a minute or two.

How many workers will I need for the initial scan?

> Here's a rough formula for how many workers:

> Workers = Cells / 20
> Cells = (((steps * (steps - 1)) * 3) + 1)

> With -st 26, you will have 1951 cells and need about 98 workers.

> To do the initial scan in an hour so, at -kph 35, it takes about half a minute to get to a the next location to scan, and you will want to be able to scan all cells in about 10 minutes, so the workers Cells / 20. If you reduce the -kph from 35 by half, increase the workers by double.

How many workers will I need after the initial scan is done?

> This will depend on the spawn density of your area. If the Spawns Reached percentage is 100%, you should be able to reduce the number of workers.

What if I don't have enough workers?

> Speed Scheduler will work with less workers, although it will take longer than an hour for the initial scan and may take a while raise the TTH found percent.

Does this work with beehive instances?

> Unless scanning a very large area (> -st 50?), Speed Scheduler does not require beehives. Each worker independently looks for the best scan it can do closest to it, so they work well together without fencing off workers into different hives.

Can I run multiple instances with Speed Scheduler with one DB?

> Yes.

Can the instances overlap?

> Yes.

How does it find the spawn points without having data from a Hex Scan?

> Magic. This is covered in more detail in my initial [PR#1386](https://github.com/RocketMap/RocketMap/pull/1386)

What happens when it finds a new spawn point after the initial scan is done?

> If a spawn point is noticed while scanning other spawnpoints, that scan location alone is reset and fully scanned to find the spawn point duration and exact spawn time.

How does it handle spawn points disappearing?

> After a spawn point is not seen as expected over five times in a row, it stops scheduling scans for that spawnpoint. The data remains in the DB.

How does it handle web changes in the search location?

> For changing the location of the searcher, this should work, but with lots of rescanning of the initial scan. Each time you change the location of the server, Speed Scheduler will restart its initial scan. Since Speed Scheduler records data about each search location, it is sensitive to changes in the location, and has to start over with the initial scan every time it is changed. This is true even if you move back to an already scanned location, but the loc is only slightly different.

Is the speed limit also used when changing the scanner location?

> Yes. Each worker remembers it's last scan location and time, so if the scanner is moved, it will take the workers  time to get to the new location.

## Print Screen, Status Page, and Log Messages

I'm seeing a lot of "[ WARNING] Nothing on nearby_pokemons or wild. Speed violation?" in the log. What could cause this?

> Common causes:
* Not using -speed as an argument. Other schedulers ignore the -kph argument.
* If the DB worker table has been recently deleted and the script restarted, such as with -cd (clear DB) option, the old position of the workers is forgotten, so they may violate the speed limit.
* There *aren't* any pokemon nearby. In areas over water or without pokemon spawns in 200m, these messages may be common. This is just a warning, and the data for that position is recorded normally.

I'm seeing a lot of "[ WARNING] Bad scan. Parsing found 0/0/0 pokemons/pokestops/gyms"

> Common causes:
* captchas
* IP bans
* Running Pogo-map with --no-gyms (-ng) and --no-pokestops (-nk). Speed Scheduler uses visible Gyms and Pokestops to determine if a scan is valid. Try adding gyms and stops back into your scan.

I'm seeing a lot of "[ WARNING] hhhs kind spawnpoint 12341234123 has no pokemon 2 times in a row"

> Possible causes:
* Spawnpoint is one of the extremely rare double spawnpoints and was scanned during it's hidden period
* Spawnpoint has been removed by Niantic. Speed Scheduler will no longer queue for scans after missing five times.

What does this line mean? `SpeedScan Overseer: Scanning status: 27 total waiting, 0 initial bands, 0 TTH searches, and 27 new spawns`

* `Intial bands` are the scans done to find the spawn points
* `TTH searches` are looking for the time_til_hidden stamp to find the exact spawn time
* `New spawn searches` are scanning new spawns.

How about this line? `Initial scan: 100.00%, TTH found: 100.00%, Spawns reached: 100.00%, Spawns found: 100.00%, Good scans 99.59%`

* `Initial scan` is the search for spawn points and scans each location in five bands within an hour, about 12 minutes apart. This should take a little over an hour to reach 100% with sufficient workers.
* `TTH found` is the percentage of spawn points for which the exact spawn time is known. This could take up to a day to get over 90%.
* `Spawns reached` is the percentage of spawns that are scanned before their timer runs out and they disappear. Will be low during the initial scan and possibly while still finding TTHs, but should reach 100% afterwards with sufficient workers.
* `Spawns found` is the percentage of spawns that found when and where they were expected. Low percentages mean the durations or end time of the spawnpoints are incorrect.
* `Good scans` are scans that aren't 0/0/0. Should be over 99% generally. If not, see above note about 0/0/0 warnings.

On the print screen (-ps) or status page (-sn) what do the messages mean?

* `Not able to reach any scan under the speed limit` — Worker is not able to find anything to scan within range and stay under the speed limit.
* `Nothing to scan` — All initial scans, spawns, and TTHs searches have been done, and workers are waiting for next spawn. Usually a good sign that you have more than enough workers.

But my system has been saying `Nothing to scan` for several minutes, and I know there are pokemon that have spawned during that time.

> Ok, that's a bad sign. It means the Overseer thread has probably had an uncaught exception and died. Restart, and if you see an exception error in the logs, please report to @Artifice to fix.
