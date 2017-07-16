# Geofences

With the help of geofences you can define your search area even better. This feature let's you line out areas you are interested in without scanning overhead. Also you can exclude areas where no scan should happen due to the sake of security or respective issues. Lastly, with Geofences you can scan geometries which were not possible to define in before.

## Requirements
No exclusive requirement is needed in general, but we try to rely on the powerful ``matplotlib`` python package which is installed via the standard procedure of ``pip install -r requirements.txt``. While this is a powerful tool, it also has its downsides that it may not be supported on certain devices, for example older Raspberry Pi. If you know that you let your setup run on such a machine, make sure to remove the ``matplotlib`` line from ``requirements.txt`` before you install them. Also enable the ``-nmpl`` / ``--no-matplotlib`` flag via CLI or by uncommenting the ``no-matplotlib`` line in the configuration file, referring to ``config/config.ini.example`` to look-up any changes to your current setup.

## How to use?
1. Define areas which you like geofence or exclude, from your standard hex. Best done via an online tool. The resulting format needs to match the content of ``geofences/geofence.txt.example`` or ``geofences/excluded.txt.example``.
2. You may exactly use one file per instance for geofenced areas and one file for excluded areas. Put all areas into the correct file like it is done in the examples.
3. Activate geofencing by adding these file paths as flag arguments to either ``-gf`` / ``--geofence-file`` or ``-gef``/ ``--geofence-excluded-file`` in CLI. This can be done via the configuration file, as well.
4. Best, place your scan location  ``-l`` / ``--location`` on top of a valid area of your geofence file and adjust ``-st`` / ``--step-limit`` to a value which just exceeds the maximum desired scan radius by a bit.

### Optional
You can define geofences to form interesting areas like Pikachu faces or scanning along long paths with defining just a small corridor as geofence and rise ``-st`` accordingly.

### Beehive
This feature explicitly works with beehive ``-bh`` scan function just as good. Please make sure that the very center of your scan area - meaning ``-l`` is right inside a valid geofence area.
