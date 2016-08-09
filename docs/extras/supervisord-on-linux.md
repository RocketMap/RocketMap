# Supervisord on Linux

## Assuming:

* You are running on Linux
* You have installed [supervisord](http://supervisord.org/)
* You have seen a shell prompt at least a few times in your life
* You have configured your stuff properly in `config.ini`
* You understand worker separation
* You can tie your own shoelaces

## The good stuff

cd into your root PokemonGO Map folder. Then:

    cd contrib/supervisord/
    ./install-reinstall.sh

When this completes, you will have all the required files. (this copies itself and the required files so that there is no conflict when doing a `git pull`. Now we are going to edit your local copy of gen-workers.sh:
    
    cd ~/supervisor
    nano gen-workers.sh


In this file, change the variables needed to suit your situation. Below is a snippet of the variables:

    # Name of coords file. SEE coords-only.sh if you dont have one!
    coords="coords.txt"

    # Webserver Location
    initloc="Dallas, TX"
    # Account name without numbers
    pre="accountname"

    # Variables
    hexnum=1   # This is the beehive number you are creating. If its the first, or you want to overwrite, dont change
    worker=0   # This is the worker number. Generally 0 unless 2+ Hives
    acct1=0    # The beginning account number for the hive is this +1
    numacct=5  # This is how many accounts you want per worker
    pass="yourpasshere" # The password you used for all the accounts
    auth="ptc" # The auth you use for all the accounts
    st=5       # Step Count per worker
    sd=5       # Scan Delay per account
    ld=1       # Login Delay per account
    directory='/path/to/your/runserver/directory/' # Path to the folder containing runserver.py **NOTICE THE TRAILING /**

As you saw above you will need to create a coords.txt (or whatever you decide to name it. I personally use city.stepcount.coords as my naming convention). We are going to use location_generator.py:
    
    cd (your Pokemon Go Map main folder here)
    python Tools/Hex-Beehive-Generator/location_generator.py -lat "yourlat" -lon "yourlon" -st 5 -lp 4 -or "~/supervisor/coords.txt"

Now run the gen-workers.sh script

    cd ~/supervisor
    ./gen-workers.sh

You should now have a bunch of .ini files in `~/supervisor/hex1/`

You can now do:

    supervisord -c ~/supervisor/supervisord.conf

And you will have a working controllable hive! You should be able to see from the web as well at `http://localhost:5001` Read up on the supervisord link at the top if you want to understand more about supervisorctl and how to control from the web.
