# Beehive

## Visual Representation

![](https://camo.githubusercontent.com/d65ac33656b410549aadfc9975f2f1a779ae437c/687474703a2f2f693330342e70686f746f6275636b65742e636f6d2f616c62756d732f6e6e3138362f736f6c6563616a756e2f426565686976652532304578706c616e6174696f6e2e706e67)

## Get Ready

The beehive script works by specifying only the parameters that are different for each worker on the command line. All other parameters are taken from [the config file](https://github.com/PokemonGoMap/PokemonGo-Map/blob/develop/config/config.ini.example).

To ensure that your beehive will run correctly, first make sure that you can run purely from the config file:

```
python runserver.py
```

If this runs ok, you should be good to go!

## Get Set

Open a Terminal or Command Window to the Tools / Hex Beehive Generator directory:

```
cd PokemonGo-Map/Tools/Hex-Beehive-Generator/
```

Now generate coordinates with `location_generator.py`:

***NOTE:*** Carefully read [these instructions](https://github.com/PokemonGoMap/PokemonGo-Map/blob/develop/docs/extras/beehive.md) for the proper arguments.

```
python location_generator.py -st stepsize -lp ringsize -lat yourstartinglathere -lon yourstartinglonghere
```

For example:

```
python location_generator.py -st 5 -lp 4 -lat 39.949157 -lon -75.165297
```

This will generate a beehive.bat (or beehive.sh for non-Windows) file in the main map directory.

## GO!

Run the .bat/.sh file to start the workers.

## Troubleshooting

If your instances start but then immediately stop, take each line from the beehive file and run them one at a time manually. This will stop the window from automatically closing so that you can see what the actual error is.
