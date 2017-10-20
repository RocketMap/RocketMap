# Geofences

With the help of geofences you can define your search area even better. This feature let's you line out areas you are interested in without scanning overhead. Also you can exclude areas where no scan should happen due to the sake of security or respective issues. Lastly, with Geofences you can scan geometries which were not possible to define in before.

## Speed
The included algorithm should be fast enough, but if you see your geofencing takes too long, there are some things you can do to improve geofencing times:

  * Try to make the polygon simpler removing vertexes.
  * Reduce step size to better fit your polygon.
  * Install ``matplotlib``.

## Matplotlib
The geofence calculations can be faster if the powerful ``matplotlib`` python package is installed, in that case it will use it instead of the included algorithm to check if a point is inside an area.
The real improvement varies a lot between setups but it should be faster anyway, in tests we have seen it ranging from 12% to 100%.

The install procedure is the same as any other python package:
``pip install matplotlib``

You can see in the logs if RM is using ``matplotlib`` or not for the calculations.
While this is a powerful tool, it also has its downsides that it may not be supported on certain devices, for example older Raspberry Pi.

## How to use?
1. Define areas which you like geofence or exclude, from your standard hex. Best done via an online tool like [this](https://codepen.io/jennerpalacios/full/mWWVeJ) (export using Show Coordinates at the top) or [this one](http://geo.jasparke.net/) (use the exp button on the left after creating a fence).
The resulting format needs to match the content of ``geofences/geofence.txt.example`` or ``geofences/excluded.txt.example``.
2. You may exactly use one file per instance for geofenced areas and one file for excluded areas. Put all areas into the correct file like it is done in the examples.
3. Activate geofencing by adding these file paths as flag arguments to either ``-gf`` / ``--geofence-file`` or ``-gef``/ ``--geofence-excluded-file`` in CLI. This can be done via the configuration file, as well.
4. Best, place your scan location  ``-l`` / ``--location`` on top of a valid area of your geofence file and adjust ``-st`` / ``--step-limit`` to a value which just exceeds the maximum desired scan radius by a bit.

### Optional
You can define geofences to form interesting areas like Pikachu faces or scanning along long paths with defining just a small corridor as geofence and rise ``-st`` accordingly.

### Beehive
This feature explicitly works with beehive ``-bh`` scan function just as good. Please make sure that the very center of your scan area - meaning ``-l`` is right inside a valid geofence area.
