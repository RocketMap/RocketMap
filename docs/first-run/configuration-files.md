# Configuration files

Configuration files can be used to organize server/scanner deployments.  Any long-form command-line argument can be specified in a configuration file.

##  Default file

The default configuration file is *config/config.ini* underneath the project home. However, this location can be changed by setting the environment variable POGOMAP_CONFIG or using the -cf or --config flag on the command line. In the event that both the environment variable and the command line argument exists, the command line value will take precedence. Note that all relative pathnames are relative to the current working directory (often, but not necessarily where runserver.py is located).

## Setting configuration key/value pairs

  For command line values that take a single value they can be specified as:

    keyname: value
    e.g.   host: 0.0.0.0

  For parameters that may be repeated:

    keyname: [ value1, value2, ...]
    e.g.   username: [ randomjoe, bonnieclyde ]
	
	*for usernames and passwords, the first username must correspond to the first password, and so on *

  For command line arguments that take no parameters:

    keyname: True
    e.g.   fixed-location: True
	

## Example config file

```
  auth-service: ptc
  username: [ username1, username2 ]
  password: [ password1, password2 ]
  location: seattle, wa
  step-limit: 5
  gmaps-key: MyGmapsKeyGoesHereSomeLongString
  hash-kay: MyHashingKeyGoesHere
  print-status: "status"
  speed-scan: True
```

  Running this config file as:

     python runserver.py -cf myconfig.seattle

  would be the same as running with the following command line:

     python runserver.py -u randomjoe -p password1 -u bob -p password2 -l "seattle, wa" -st 5 -k MyGmapsKeyGoesHereSomeLongString -ps

## Running multiple configs

   One common way of running multiple locations is to use two configuration files each with common or default database values, but with different location specs. The first configuration running as both a scanner and a server, and in the second configuration file, use the *no-server* flag to not start the web interface for the second configuration.   In the config file, this would mean including a line like:

   no-server: True
   
### Using `-ns` and `-os`

If RocketMap is not scanning enough areas, you can add additional areas by starting a 2nd RocketMap instance with the flag `-ns`. This starts the searchers without starting another webserver. You can run as many instances with `-ns` as your server can keep up with. ***HOWEVER:*** If all your instances are running `-ns` you will also want to start an instance with `-os`. This will start only the webserver. This becomes useful if you begin to seperate your RM instances across several computers all linked to the same database. 


