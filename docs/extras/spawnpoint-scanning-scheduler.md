# Spawnpoint Scanning Scheduler

If you already have a large number of known spawnpoints it may be worth looking into Spawnpoint Scanning

Spawnpoint Scanning consists of only scanning an area in which a spawn has recently happened, this saves a large number of requests and also detects all spawns soon after they appear instead of whenever the scan gets round to them again

Spawnpoint Scanning is particularly useful in areas where spawns are spread out

## Spawnpoint Scanning can be run in one of three different modes:

### Scans based on database

```
python runserver.py -ss -l YOURLOCATION -st STEPS
```

Where YOURLOCATION is the location the map should be centered at and also the center of the hex to get spawn locations from, -st sets the size of the clipping hexagon (hexagon is the same size as the scan of the same -st value)

This is particularly useful for when using a beehive

Note: when using the mode when not in a beehive, it is recommended to use an -st value one higher than the scan was done on, to avoid very edge spawns being clipped off

### Dump scans from database then use the created file

```
python runserver.py -ss YOURFILE.json -l YOURLOCATION -st STEPS --dump-spawnpoints
```

Where YOURFILE.json is the file containing all the spawns, YOURLOCATION is the location the map should be centered at and also the center of the hex to get spawn locations from and -st sets the size of the clipping hexagon (hexagon is the same size as the scan of the same -st value)

This mode is mainly used for switching from database mode to spawnFile mode, and can also be used simply for dumping all spawns to file (use a very large -st and close the program once it has created the file)

### Scans based on file

```
python runserver.py -ss YOURFILE.json -l YOURLOCATION
```

Where YOURFILE.json is the file containing all the spawns, and YOURLOCATION is the location the map should be centered at (YOURLOCATION is not used for anything else in this mode)

Note: in this mode -st does nothing

### Getting spawns

for generating the spawns to use with Spawnpoint Scanning it is recommended to scan the area with a scan that completes in 10 minutes for at least 1 hour, this should guarantee that all spawns are found

spawn files can also be generated with an external tool such as spawnScan
