# Beehive

## Visual Representation

![](../_static/img/soznlqc.png)

## Get Ready

The beehive script works by specifying only the parameters that are different for each worker on the command line. All other parameters are taken from [the config file](https://github.com/RocketMap/RocketMap/blob/develop/config/config.ini.example).

To ensure that your beehive will run correctly, first make sure that you have setup your config.ini with the appropriate settings. 

You will want the following to run optimial beehives:
MySQL
Captcha Solving (manual or 2captcha)
possibly a few proxies


## Get Set

[Go here] (https://voxx.github.io/pgm-multiloc/)

Select the areas in which you want to scan. Keep in mind the more areas you select the more workers you will need. 

Once you have the areas ready, select `Generate Launch Script`

You will select the options for your setup and decide how many workers per hive. 

After your scanning preferences are set, you will download the script. 

***Please Note:*** By default, it will look in the folder workers for accounts to use. For every hive you have you must also have have a CSV named `HIVE{number}.csv`. Please do not put a account in more than one CSV as it might cause unwanted effects.  

CSV format example:

```
ptc,username,password
```


## GO!

Run the .bat/.sh file to start the workers.

## Troubleshooting

If your instances start but then immediately stop, take each line and run the part after /MIN starting with the python path. This will stop the window from automatically closing so that you can see what the actual error is.

## Distances

![](../_static/img/ZHSo3GN.png)

 if using -st 10, these are the numbers you should know: 4.9283 km, 1.425 km, 2.468175 km, 2.85 km - you can use the distances to calculate coords here http://www.sunearthtools.com/tools/distance.php
