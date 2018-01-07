# Spawnpoint Scanning Scheduler

If you already have a 100% completed Initial Scan, it may be worth looking into Spawnpoint Scanning.

Spawnpoint Scanning consists of only scanning an area in which a spawn has recently happened, this saves a large number of requests and also detects all spawns soon after they appear instead of whenever the scan gets round to them again.

Spawnpoint Scanning is particularly useful in areas where spawns are spread out.

## Spawnpoint Scanning can be run in one of two different modes:

### Scans without Spawnpoint Clustering

```
python runserver.py -ss -l YOURLOCATION -st STEPS
```

Where YOURLOCATION is the location the map should be centered at and also the center of the hex to get spawn locations from, -st sets the size of the clipping hexagon (hexagon is the same size as the scan of the same -st value).

This is particularly useful for when using a beehive.

Note: When using the mode when not in a beehive, it is recommended to use an -st value one higher than the scan was done on, to avoid very edge spawns being clipped off.

### Scans with Spawnpoint Clustering

```
python runserver.py -ss -ssct YOURVALUE -l YOURLOCATION -st STEPS
```

Where YOURLOCATION is the location the map should be centered at and also the center of the hex to get spawn locations from, -st sets the size of the clipping hexagon (hexagon is the same size as the scan of the same -st value), -ssct (Spawnpoint Cluster Time) sets a Time threshold (in seconds) for spawn point clustering.
A Value around 200 seconds is recommended.
Spawnpoint Clustering can help to reduce requests and also your worker count because its compressing several Spawnpoints into a cluster. Cluster time will try to schedule scans at the same position within -ssct amount of seconds to catch multiple spawns at once.


This is particularly useful for when using a beehive.

Note: When using the mode when not in a beehive, it is recommended to use an -st value one higher than the scan was done on, to avoid very edge spawns being clipped off.


### Getting spawns

For generating the spawns to use with Spawnpoint Scanning it is recommended to scan the area with -speed until the initial scan reaches 100%.
