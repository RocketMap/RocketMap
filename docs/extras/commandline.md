# Command Line

    usage: runserver.py
                        [-h] [-a AUTH_SERVICE] [-u USERNAME] [-p PASSWORD]
                        [-w WORKERS] [-asi ACCOUNT_SEARCH_INTERVAL]
                        [-ari ACCOUNT_REST_INTERVAL] [-ac ACCOUNTCSV]
                        [-l LOCATION] [-j] [-st STEP_LIMIT] [-sd SCAN_DELAY]
                        [-ld LOGIN_DELAY] [-lr LOGIN_RETRIES] [-mf MAX_FAILURES]
                        [-msl MIN_SECONDS_LEFT] [-dc] [-H HOST] [-P PORT]
                        [-L LOCALE] [-c] [-m MOCK] [-ns] [-os] [-nsc] [-fl] -k
                        GMAPS_KEY [--spawnpoints-only] [-C] [-D DB] [-cd] [-np]
                        [-ng] [-nk] [-ss [SPAWNPOINT_SCANNING]]
                        [--dump-spawnpoints] [-pd PURGE_DATA] [-px PROXY]
                        [-pxt PROXY_TIMEOUT] [-pxd PROXY_DISPLAY]
                        [--db-type DB_TYPE] [--db-name DB_NAME]
                        [--db-user DB_USER] [--db-pass DB_PASS]
                        [--db-host DB_HOST] [--db-port DB_PORT]
                        [--db-max_connections DB_MAX_CONNECTIONS]
                        [--db-threads DB_THREADS] [-wh [WEBHOOKS [WEBHOOKS ...]]]
                        [-gi] [--webhook-updates-only] [--wh-threads WH_THREADS]
                        [--ssl-certificate SSL_CERTIFICATE]
                        [--ssl-privatekey SSL_PRIVATEKEY] [-ps] [-sn STATUS_NAME]
                        [-spp STATUS_PAGE_PASSWORD] [-el ENCRYPT_LIB]
                        [-v [filename.log] | -vv [filename.log] | -d]
    
    Args that start with '--' (eg. -a) can also be set in a config file
    (C:\Users\User\Desktop\Pogom\PokemonGo-map\pogom\../config/config.ini or ).
    The recognized syntax for setting (key, value) pairs is based on the INI and
    YAML formats (e.g. key=value or foo=TRUE). For full documentation of the
    differences from the standards please refer to the ConfigArgParse
    documentation. If an arg is specified in more than one place, then commandline
    values override environment variables which override config file values which
    override defaults.
    
    optional arguments:
      -h, --help            Show this help message and exit.
      -a AUTH_SERVICE, --auth-service AUTH_SERVICE
                            Auth Services, either one for all accounts or one per
                            account: ptc or google. Defaults all to ptc. 
      -u USERNAME, --username USERNAME
                            Usernames, one per account. 
      -p PASSWORD, --password PASSWORD
                            Passwords, either single one for all accounts or one
                            per account. 
      -w WORKERS, --workers WORKERS
                            Number of search worker threads to start. Defaults to
                            the number of accounts specified. 
      -asi ACCOUNT_SEARCH_INTERVAL, --account-search-interval ACCOUNT_SEARCH_INTERVAL
                            Seconds for accounts to search before switching to a
                            new account. 0 to disable.
      -ari ACCOUNT_REST_INTERVAL, --account-rest-interval ACCOUNT_REST_INTERVAL
                            Seconds for accounts to rest when they fail or are
                            switched out.
      -ac ACCOUNTCSV, --accountcsv ACCOUNTCSV
                            Load accounts from CSV file containing
                            "auth_service,username,passwd" lines.
      -l LOCATION, --location LOCATION
                            Location, can be an address or coordinates.
      -j, --jitter          Apply random -9m to +9m jitter to location.
      -st STEP_LIMIT, --step-limit STEP_LIMIT
                            Steps.
      -sd SCAN_DELAY, --scan-delay SCAN_DELAY
                            Time delay between requests in scan threads.
      -ld LOGIN_DELAY, --login-delay LOGIN_DELAY
                            Time delay between each login attempt.
      -lr LOGIN_RETRIES, --login-retries LOGIN_RETRIES
                            Number of logins attempts before refreshing a thread.
      -mf MAX_FAILURES, --max-failures MAX_FAILURES
                            Maximum number of failures to parse locations before
                            an account will go into a two hour sleep.
      -msl MIN_SECONDS_LEFT, --min-seconds-left MIN_SECONDS_LEFT
                            Time that must be left on a spawn before considering
                            it too late and skipping it. eg. 600 would skip
                            anything with < 10 minutes remaining. Default 0.
      -dc, --display-in-console
                            Display Found Pokemon in Console.
      -H HOST, --host HOST  Set web server listening host.
      -P PORT, --port PORT  Set web server listening port.
      -L LOCALE, --locale LOCALE
                            Locale for Pokemon names (default: en, check
                            static/dist/locales for more).
      -c, --china           Coordinates transformer for China.
      -m MOCK, --mock MOCK  Mock mode - point to a fpgo endpoint instead of using
                            the real PogoApi, ec: http://127.0.0.1:9090.
      -ns, --no-server      No-Server Mode. Starts the searcher but not the
                            Webserver.
      -os, --only-server    Server-Only Mode. Starts only the Webserver without
                            the searcher.
      -nsc, --no-search-control
                            Disables search control.
      -fl, --fixed-location
                            Hides the search bar for use in shared maps.
      -k GMAPS_KEY, --gmaps-key GMAPS_KEY
                            Google Maps Javascript API Key.
      --spawnpoints-only    Only scan locations with spawnpoints in them.
      -C, --cors            Enable CORS on web server.
      -D DB, --db DB        Database filename.
      -cd, --clear-db       Deletes the existing database before starting the
                            Webserver.
      -np, --no-pokemon     Disables Pokemon from the map (including parsing them
                            into local db).
      -ng, --no-gyms        Disables Gyms from the map (including parsing them
                            into local db).
      -nk, --no-pokestops   Disables PokeStops from the map (including parsing
                            them into local db).
      -ss [SPAWNPOINT_SCANNING], --spawnpoint-scanning [SPAWNPOINT_SCANNING]
                            Use spawnpoint scanning (instead of hex grid). Scans
                            in a circle based on step_limit when on DB.
      --dump-spawnpoints    dump the spawnpoints from the db to json (only for use
                            with -ss).
      -pd PURGE_DATA, --purge-data PURGE_DATA
                            Clear pokemon from database this many hours after they
                            disappear (0 to disable).
      -px PROXY, --proxy PROXY
                            Proxy url (e.g. socks5://127.0.0.1:9050).
      -pxt PROXY_TIMEOUT, --proxy-timeout PROXY_TIMEOUT
                            Timeout settings for proxy checker in seconds.
      -pxd PROXY_DISPLAY, --proxy-display PROXY_DISPLAY
                            Display info on which proxy beeing used (index or
                            full) To be used with -ps.
      --db-type DB_TYPE     Type of database to be used (default: sqlite).
      --db-name DB_NAME     Name of the database to be used.
      --db-user DB_USER     Username for the database.
      --db-pass DB_PASS     Password for the database.
      --db-host DB_HOST     IP or hostname for the database.
      --db-port DB_PORT     Port for the database.
      --db-max_connections DB_MAX_CONNECTIONS
                            Max connections (per thread) for the database.
      --db-threads DB_THREADS
                            Number of db threads; increase if the db queue falls
                            behind.
      -wh [WEBHOOKS [WEBHOOKS ...]], --webhook [WEBHOOKS [WEBHOOKS ...]]
                            Define URL(s) to POST webhook information to.
      -gi, --gym-info       Get all details about gyms (causes an additional API
                            hit for every gym).
      --webhook-updates-only
                            Only send updates (pokemon & lured pokestops).
      --wh-threads WH_THREADS
                            Number of webhook threads; increase if the webhook
                            queue falls behind.
      --ssl-certificate SSL_CERTIFICATE
                            Path to SSL certificate file.
      --ssl-privatekey SSL_PRIVATEKEY
                            Path to SSL private key file.
      -ps, --print-status   Show a status screen instead of log messages. Can
                            switch between status and logs by pressing enter.
      -sn STATUS_NAME, --status-name STATUS_NAME
                            Enable status page database update using STATUS_NAME
                            as main worker name.
      -spp STATUS_PAGE_PASSWORD, --status-page-password STATUS_PAGE_PASSWORD
                            Set the status page password.
      -el ENCRYPT_LIB, --encrypt-lib ENCRYPT_LIB
                            Path to encrypt lib to be used instead of the shipped
                            ones.
      -v [filename.log], --verbose [filename.log]
                            Show debug messages from PomemonGo-Map and pgoapi.
                            Optionally specify file to log to.
      -vv [filename.log], --very-verbose [filename.log]
                            Like verbose, but show debug messages from all modules
                            as well. Optionally specify file to log to.
      -d, --debug           Depreciated, use -v or -vv instead.
    
