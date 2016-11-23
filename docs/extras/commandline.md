# Command Line

    usage: runserver.py
                        [-h] [-cf CONFIG] [-a AUTH_SERVICE] [-u USERNAME]
                        [-p PASSWORD] [-w WORKERS] [-asi ACCOUNT_SEARCH_INTERVAL]
                        [-ari ACCOUNT_REST_INTERVAL] [-ac ACCOUNTCSV]
                        [-l LOCATION] [-j] [-st STEP_LIMIT] [-sd SCAN_DELAY]
                        [-enc] [-cs] [-ck CAPTCHA-KEY] [-cds CAPTCHA-DSK] [-ed ENCOUNTER_DELAY]
                        [-ewht ENCOUNTER_WHITELIST | -eblk ENCOUNTER_BLACKLIST]
                        [-ld LOGIN_DELAY] [-lr LOGIN_RETRIES] [-mf MAX_FAILURES]
                        [-msl MIN_SECONDS_LEFT] [-dc] [-H HOST] [-P PORT]
                        [-L LOCALE] [-c] [-m MOCK] [-ns] [-os] [-nsc] [-fl] -k
                        GMAPS_KEY [--skip-empty] [-C] [-D DB] [-cd] [-np]
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
                        [-v [filename.log] | -vv [filename.log]]
    
    Args that start with '--' (eg. -a) can also be set in a config file
    (default: <PokemonGo-Map Project Root>/config/config.ini or via -cf).
    The recognized syntax for setting (key, value) pairs is based on the INI and
    YAML formats (e.g. key=value or foo=TRUE). For full documentation of the
    differences from the standards please refer to the ConfigArgParse
    documentation. If an arg is specified in more than one place, then commandline
    values override environment variables which override config file values which
    override defaults.
    
    optional arguments:
      -h, --help            show this help message and exit [env var:
                            POGOMAP_HELP]
      -cf CONFIG, --config CONFIG
                            Configuration file.  See docs/extras/configuration-files.md
      -a AUTH_SERVICE, --auth-service AUTH_SERVICE
                            Auth Services, either one for all accounts or one per
                            account: ptc or google. Defaults all to ptc. [env var:
                            POGOMAP_AUTH_SERVICE]
      -u USERNAME, --username USERNAME
                            Usernames, one per account. [env var:
                            POGOMAP_USERNAME]
      -p PASSWORD, --password PASSWORD
                            Passwords, either single one for all accounts or one
                            per account. [env var: POGOMAP_PASSWORD]
      -w WORKERS, --workers WORKERS
                            Number of search worker threads to start. Defaults to
                            the number of accounts specified. [env var:
                            POGOMAP_WORKERS]
      -asi ACCOUNT_SEARCH_INTERVAL, --account-search-interval ACCOUNT_SEARCH_INTERVAL
                            Seconds for accounts to search before switching to a
                            new account. 0 to disable. [env var:
                            POGOMAP_ACCOUNT_SEARCH_INTERVAL]
      -ari ACCOUNT_REST_INTERVAL, --account-rest-interval ACCOUNT_REST_INTERVAL
                            Seconds for accounts to rest when they fail or are
                            switched out [env var: POGOMAP_ACCOUNT_REST_INTERVAL]
      -ac ACCOUNTCSV, --accountcsv ACCOUNTCSV
                            Load accounts from CSV file containing
                            "auth_service,username,passwd" lines [env var:
                            POGOMAP_ACCOUNTCSV]
      -l LOCATION, --location LOCATION
                            Location, can be an address or coordinates [env var:
                            POGOMAP_LOCATION]
      -j, --jitter          Apply random -9m to +9m jitter to location [env var:
                            POGOMAP_JITTER]
      -st STEP_LIMIT, --step-limit STEP_LIMIT
                            Steps [env var: POGOMAP_STEP_LIMIT]
      -sd SCAN_DELAY, --scan-delay SCAN_DELAY
                            Time delay between requests in scan threads [env var:
                            POGOMAP_SCAN_DELAY]
      -enc, --encounter     Start an encounter to gather IVs and moves [env var:
                            POGOMAP_ENCOUNTER]
      -cs, --captcha-solving
                            Enables captcha solving [env var:
                            POGOMAP_CAPTCHA_SOLVING]
      -ck, --captcha-key    2Captcha API Key [env var:
                            POGOMAP_CAPTCHA_KEY]
      -cds, --captcha-dsk   PokemonGo Captcha data-sitekey [env var:
                            POGOMAP_CAPTCHA_DSK]
      -ed ENCOUNTER_DELAY, --encounter-delay ENCOUNTER_DELAY
                            Time delay between encounter pokemon in scan threads
                            [env var: POGOMAP_ENCOUNTER_DELAY]
      -ewht ENCOUNTER_WHITELIST, --encounter-whitelist ENCOUNTER_WHITELIST
                            List of pokemon to encounter for more stats [env var:
                            POGOMAP_ENCOUNTER_WHITELIST]
      -eblk ENCOUNTER_BLACKLIST, --encounter-blacklist ENCOUNTER_BLACKLIST
                            List of pokemon to NOT encounter for more stats [env
                            var: POGOMAP_ENCOUNTER_BLACKLIST]    
      -ld LOGIN_DELAY, --login-delay LOGIN_DELAY
                            Time delay between each login attempt [env var:
                            POGOMAP_LOGIN_DELAY]
      -lr LOGIN_RETRIES, --login-retries LOGIN_RETRIES
                            Number of logins attempts before refreshing a thread
                            [env var: POGOMAP_LOGIN_RETRIES]
      -mf MAX_FAILURES, --max-failures MAX_FAILURES
                            Maximum number of failures to parse locations before
                            an account will go into a two hour sleep [env var:
                            POGOMAP_MAX_FAILURES]
      -msl MIN_SECONDS_LEFT, --min-seconds-left MIN_SECONDS_LEFT
                            Time that must be left on a spawn before considering
                            it too late and skipping it. eg. 600 would skip
                            anything with < 10 minutes remaining. Default 0. [env
                            var: POGOMAP_MIN_SECONDS_LEFT]
      -dc, --display-in-console
                            Display Found Pokemon in Console [env var:
                            POGOMAP_DISPLAY_IN_CONSOLE]
      -H HOST, --host HOST  Set web server listening host [env var: POGOMAP_HOST]
      -P PORT, --port PORT  Set web server listening port [env var: POGOMAP_PORT]
      -L LOCALE, --locale LOCALE
                            Locale for Pokemon names (default: en, check
                            static/dist/locales for more) [env var:
                            POGOMAP_LOCALE]
      -c, --china           Coordinates transformer for China [env var:
                            POGOMAP_CHINA]
      -m MOCK, --mock MOCK  Mock mode - point to a fpgo endpoint instead of using
                            the real PogoApi, ec: http://127.0.0.1:9090 [env var:
                            POGOMAP_MOCK]
      -ns, --no-server      No-Server Mode. Starts the searcher but not the
                            Webserver. [env var: POGOMAP_NO_SERVER]
      -os, --only-server    Server-Only Mode. Starts only the Webserver without
                            the searcher. [env var: POGOMAP_ONLY_SERVER]
      -nsc, --no-search-control
                            Disables search control [env var:
                            POGOMAP_NO_SEARCH_CONTROL]
      -fl, --fixed-location
                            Hides the search bar for use in shared maps. [env var:
                            POGOMAP_FIXED_LOCATION]
      -k GMAPS_KEY, --gmaps-key GMAPS_KEY
                            Google Maps Javascript API Key [env var:
                            POGOMAP_GMAPS_KEY]
      --skip-empty          Enables skipping of empty cells in normal scans -
                            requires previously populated database (not to be used
                            with -ss) [env var: POGOMAP_SKIP_EMPTY]
      -C, --cors            Enable CORS on web server [env var: POGOMAP_CORS]
      -D DB, --db DB        Database filename [env var: POGOMAP_DB]
      -cd, --clear-db       Deletes the existing database before starting the
                            Webserver. [env var: POGOMAP_CLEAR_DB]
      -np, --no-pokemon     Disables Pokemon from the map (including parsing them
                            into local db) [env var: POGOMAP_NO_POKEMON]
      -ng, --no-gyms        Disables Gyms from the map (including parsing them
                            into local db) [env var: POGOMAP_NO_GYMS]
      -nk, --no-pokestops   Disables PokeStops from the map (including parsing
                            them into local db) [env var: POGOMAP_NO_POKESTOPS]
      -ss [SPAWNPOINT_SCANNING], --spawnpoint-scanning [SPAWNPOINT_SCANNING]
                            Use spawnpoint scanning (instead of hex grid). Scans
                            in a circle based on step_limit when on DB [env var:
                            POGOMAP_SPAWNPOINT_SCANNING]
      --dump-spawnpoints    dump the spawnpoints from the db to json (only for use
                            with -ss) [env var: POGOMAP_DUMP_SPAWNPOINTS]
      -pd PURGE_DATA, --purge-data PURGE_DATA
                            Clear pokemon from database this many hours after they
                            disappear (0 to disable) [env var: POGOMAP_PURGE_DATA]
      -px PROXY, --proxy PROXY
                            Proxy url (e.g. socks5://127.0.0.1:9050) [env var:
                            POGOMAP_PROXY]
      -pxsc, --proxy-skip-check
                            Disable checking of proxies before start [env var:
                            POGOMAP_PROXY_SKIP_CHECK]
      -pxt PROXY_TIMEOUT, --proxy-timeout PROXY_TIMEOUT
                            Timeout settings for proxy checker in seconds [env
                            var: POGOMAP_PROXY_TIMEOUT]
      -pxd PROXY_DISPLAY, --proxy-display PROXY_DISPLAY
                            Display info on which proxy beeing used (index or
                            full) To be used with -ps [env var:
                            POGOMAP_PROXY_DISPLAY]
      --db-type DB_TYPE     Type of database to be used (default: sqlite) [env
                            var: POGOMAP_DB_TYPE]
      --db-name DB_NAME     Name of the database to be used [env var:
                            POGOMAP_DB_NAME]
      --db-user DB_USER     Username for the database [env var: POGOMAP_DB_USER]
      --db-pass DB_PASS     Password for the database [env var: POGOMAP_DB_PASS]
      --db-host DB_HOST     IP or hostname for the database [env var:
                            POGOMAP_DB_HOST]
      --db-port DB_PORT     Port for the database [env var: POGOMAP_DB_PORT]
      --db-max_connections DB_MAX_CONNECTIONS
                            Max connections (per thread) for the database [env
                            var: POGOMAP_DB_MAX_CONNECTIONS]
      --db-threads DB_THREADS
                            Number of db threads; increase if the db queue falls
                            behind [env var: POGOMAP_DB_THREADS]
      -wh [WEBHOOKS [WEBHOOKS ...]], --webhook [WEBHOOKS [WEBHOOKS ...]]
                            Define URL(s) to POST webhook information to [env var:
                            POGOMAP_WEBHOOK]
      -gi, --gym-info       Get all details about gyms (causes an additional API
                            hit for every gym) [env var: POGOMAP_GYM_INFO]
      --disable-clean       Disable clean db loop [env var: POGOMAP_DISABLE_CLEAN]
      --webhook-updates-only
                            Only send updates (pokÃ©mon & lured pokÃ©stops) [env
                            var: POGOMAP_WEBHOOK_UPDATES_ONLY]
      --wh-threads WH_THREADS
                            Number of webhook threads; increase if the webhook
                            queue falls behind [env var: POGOMAP_WH_THREADS]
      --ssl-certificate SSL_CERTIFICATE
                            Path to SSL certificate file [env var:
                            POGOMAP_SSL_CERTIFICATE]
      --ssl-privatekey SSL_PRIVATEKEY
                            Path to SSL private key file [env var:
                            POGOMAP_SSL_PRIVATEKEY]
      -ps, --print-status   Show a status screen instead of log messages. Can
                            switch between status and logs by pressing enter. [env
                            var: POGOMAP_PRINT_STATUS]
      -sn STATUS_NAME, --status-name STATUS_NAME
                            Enable status page database update using STATUS_NAME
                            as main worker name [env var: POGOMAP_STATUS_NAME]
      -spp STATUS_PAGE_PASSWORD, --status-page-password STATUS_PAGE_PASSWORD
                            Set the status page password [env var:
                            POGOMAP_STATUS_PAGE_PASSWORD]
      -el ENCRYPT_LIB, --encrypt-lib ENCRYPT_LIB
                            Path to encrypt lib to be used instead of the shipped
                            ones [env var: POGOMAP_ENCRYPT_LIB]
      -odt ON_DEMAND_TIMEOUT, --on-demand_timeout ON_DEMAND_TIMEOUT
                            Pause searching while web UI is inactive for this
                            timeout(in seconds) [env var:
                            POGOMAP_ON_DEMAND_TIMEOUT]
      -v [filename.log], --verbose [filename.log]
                            Show debug messages from PomemonGo-Map and pgoapi.
                            Optionally specify file to log to. [env var:
                            POGOMAP_VERBOSE]
      -vv [filename.log], --very-verbose [filename.log]
                            Like verbose, but show debug messages from all modules
                            as well. Optionally specify file to log to. [env var:
                            POGOMAP_VERY_VERBOSE]
