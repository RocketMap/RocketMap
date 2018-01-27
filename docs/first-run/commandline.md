# Command Line

    usage: runserver.py [-h] [-cf CONFIG] [-scf SHARED_CONFIG] [-a AUTH_SERVICE]
                    [-u USERNAME] [-p PASSWORD] [-w WORKERS]
                    [-asi ACCOUNT_SEARCH_INTERVAL]
                    [-ari ACCOUNT_REST_INTERVAL] [-ac ACCOUNTCSV]
                    [-hlvl HIGH_LVL_ACCOUNTS] [-bh] [-wph WORKERS_PER_HIVE]
                    [-l LOCATION] [-alt ALTITUDE] [-altv ALTITUDE_VARIANCE]
                    [-uac] [-j] [-al] [-st STEP_LIMIT] [-gf GEOFENCE_FILE]
                    [-gef GEOFENCE_EXCLUDED_FILE] [-sd SCAN_DELAY]
                    [--spawn-delay SPAWN_DELAY] [-enc] [-cs] [-ck CAPTCHA_KEY]
                    [-cds CAPTCHA_DSK] [-mcd MANUAL_CAPTCHA_DOMAIN]
                    [-mcr MANUAL_CAPTCHA_REFRESH]
                    [-mct MANUAL_CAPTCHA_TIMEOUT] [-ed ENCOUNTER_DELAY]
                    [-ignf IGNORELIST_FILE] [-encwf ENC_WHITELIST_FILE]
                    [-nostore] [-apir API_RETRIES]
                    [-wwht WEBHOOK_WHITELIST | -wblk WEBHOOK_BLACKLIST | -wwhtf WEBHOOK_WHITELIST_FILE | -wblkf WEBHOOK_BLACKLIST_FILE]
                    [-ld LOGIN_DELAY] [-lr LOGIN_RETRIES] [-mf MAX_FAILURES]
                    [-me MAX_EMPTY] [-bsr BAD_SCAN_RETRY]
                    [-msl MIN_SECONDS_LEFT] [-dc] [-H HOST] [-P PORT]
                    [-L LOCALE] [-c] [-m MOCK] [-ns] [-os] [-sc] [-nfl] -k
                    GMAPS_KEY [--skip-empty] [-C] [-cd] [-np] [-ng] [-nr]
                    [-nk] [-ss] [-ssct SS_CLUSTER_TIME] [-speed] [-spin]
                    [-ams ACCOUNT_MAX_SPINS] [-kph KPH] [-hkph HLVL_KPH]
                    [-ldur LURE_DURATION] [-pd PURGE_DATA] [-px PROXY] [-pxsc]
                    [-pxt PROXY_TEST_TIMEOUT] [-pxre PROXY_TEST_RETRIES]
                    [-pxbf PROXY_TEST_BACKOFF_FACTOR]
                    [-pxc PROXY_TEST_CONCURRENCY] [-pxd PROXY_DISPLAY]
                    [-pxf PROXY_FILE] [-pxr PROXY_REFRESH]
                    [-pxo PROXY_ROTATION] --db-name DB_NAME --db-user DB_USER
                    --db-pass DB_PASS [--db-host DB_HOST] [--db-port DB_PORT]
                    [--db-threads DB_THREADS] [-wh WEBHOOKS] [-gi] [-DC]
                    [--wh-types {pokemon,gym,raid,egg,tth,gym-info,pokestop,lure,captcha}]
                    [--wh-threads WH_THREADS] [-whc WH_CONCURRENCY]
                    [-whr WH_RETRIES] [-whct WH_CONNECT_TIMEOUT]
                    [-whrt WH_READ_TIMEOUT] [-whbf WH_BACKOFF_FACTOR]
                    [-whlfu WH_LFU_SIZE] [-whfi WH_FRAME_INTERVAL]
                    [--ssl-certificate SSL_CERTIFICATE]
                    [--ssl-privatekey SSL_PRIVATEKEY] [-ps [logs]]
                    [-slt STATS_LOG_TIMER] [-sn STATUS_NAME]
                    [-spp STATUS_PAGE_PASSWORD] [-hk HASH_KEY] [-novc]
                    [-vci VERSION_CHECK_INTERVAL] [-odt ON_DEMAND_TIMEOUT]
                    [--disable-blacklist] [-tp TRUSTED_PROXIES]
                    [--api-version API_VERSION] [--no-file-logs]
                    [--log-path LOG_PATH] [--dump] [-v | --verbosity VERBOSE]
                    [-Rh RARITY_HOURS] [-Rf RARITY_UPDATE_FREQUENCY]

Args that start with '--' (eg. -a) can also be set in a config file
(config/config.ini or specified via -cf or -scf). The recognized syntax
for setting (key, value) pairs is based on the INI and YAML formats
(e.g. key=value or foo=TRUE). For full documentation of the differences
from the standards please refer to the ConfigArgParse documentation. If an
arg is specified in more than one place, then commandline values override
environment variables which override config file values which override defaults.

    optional arguments:
      -h, --help            show this help message and exit [env var:
                            POGOMAP_HELP]
      -cf CONFIG, --config CONFIG
                            Set configuration file
      -scf SHARED_CONFIG, --shared-config SHARED_CONFIG
                            Set a shared config
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
                            switched out. [env var: POGOMAP_ACCOUNT_REST_INTERVAL]
      -ac ACCOUNTCSV, --accountcsv ACCOUNTCSV
                            Load accounts from CSV file containing
                            "auth_service,username,password" lines. [env var:
                            POGOMAP_ACCOUNTCSV]
      -hlvl HIGH_LVL_ACCOUNTS, --high-lvl-accounts HIGH_LVL_ACCOUNTS
                            Load high level accounts from CSV file containing
                            "auth_service,username,password" lines. [env var:
                            POGOMAP_HIGH_LVL_ACCOUNTS]
      -bh, --beehive        Use beehive configuration for multiple accounts, one
                            account per hex. Make sure to keep -st under 5, and -w
                            under the total amount of accounts available. [env
                            var: POGOMAP_BEEHIVE]
      -wph WORKERS_PER_HIVE, --workers-per-hive WORKERS_PER_HIVE
                            Only referenced when using --beehive. Sets number of
                            workers per hive. Default value is 1. [env var:
                            POGOMAP_WORKERS_PER_HIVE]
      -l LOCATION, --location LOCATION
                            Location, can be an address or coordinates. [env var:
                            POGOMAP_LOCATION]
      -alt ALTITUDE, --altitude ALTITUDE
                            Default altitude in meters. [env var:
                            POGOMAP_ALTITUDE]
      -altv ALTITUDE_VARIANCE, --altitude-variance ALTITUDE_VARIANCE
                            Variance for --altitude in meters [env var:
                            POGOMAP_ALTITUDE_VARIANCE]
      -uac, --use-altitude-cache
                            Query the Elevation API for each step, rather than
                            only once, and store results in the database. [env
                            var: POGOMAP_USE_ALTITUDE_CACHE]
      -j, --jitter          Apply random -5m to +5m jitter to location. [env var:
                            POGOMAP_JITTER]
      -al, --access-logs    Write web logs to access.log. [env var:
                            POGOMAP_ACCESS_LOGS]
      -st STEP_LIMIT, --step-limit STEP_LIMIT
                            Steps. [env var: POGOMAP_STEP_LIMIT]
      -gf GEOFENCE_FILE, --geofence-file GEOFENCE_FILE
                            Geofence file to define outer borders of the scan
                            area. [env var: POGOMAP_GEOFENCE_FILE]
      -gef GEOFENCE_EXCLUDED_FILE, --geofence-excluded-file GEOFENCE_EXCLUDED_FILE
                            File to define excluded areas inside scan area.
                            Regarded this as inverted geofence. Can be combined
                            with geofence-file. [env var:
                            POGOMAP_GEOFENCE_EXCLUDED_FILE]
      -sd SCAN_DELAY, --scan-delay SCAN_DELAY
                            Time delay between requests in scan threads. [env var:
                            POGOMAP_SCAN_DELAY]
      --spawn-delay SPAWN_DELAY
                            Number of seconds after spawn time to wait before
                            scanning to be sure the Pokemon is there. [env var:
                            POGOMAP_SPAWN_DELAY]
      -enc, --encounter     Start an encounter to gather IVs and moves. [env var:
                            POGOMAP_ENCOUNTER]
      -cs, --captcha-solving
                            Enables captcha solving. [env var:
                            POGOMAP_CAPTCHA_SOLVING]
      -ck CAPTCHA_KEY, --captcha-key CAPTCHA_KEY
                            2Captcha API key. [env var: POGOMAP_CAPTCHA_KEY]
      -cds CAPTCHA_DSK, --captcha-dsk CAPTCHA_DSK
                            Pokemon Go captcha data-sitekey. [env var:
                            POGOMAP_CAPTCHA_DSK]
      -mcd MANUAL_CAPTCHA_DOMAIN, --manual-captcha-domain MANUAL_CAPTCHA_DOMAIN
                            Domain to where captcha tokens will be sent. [env var:
                            POGOMAP_MANUAL_CAPTCHA_DOMAIN]
      -mcr MANUAL_CAPTCHA_REFRESH, --manual-captcha-refresh MANUAL_CAPTCHA_REFRESH
                            Time available before captcha page refreshes. [env
                            var: POGOMAP_MANUAL_CAPTCHA_REFRESH]
      -mct MANUAL_CAPTCHA_TIMEOUT, --manual-captcha-timeout MANUAL_CAPTCHA_TIMEOUT
                            Maximum time captchas will wait for manual captcha
                            solving. On timeout, if enabled, 2Captcha will be used
                            to solve captcha. Default is 0. [env var:
                            POGOMAP_MANUAL_CAPTCHA_TIMEOUT]
      -ed ENCOUNTER_DELAY, --encounter-delay ENCOUNTER_DELAY
                            Time delay between encounter pokemon in scan threads.
                            [env var: POGOMAP_ENCOUNTER_DELAY]
      -ignf IGNORELIST_FILE, --ignorelist-file IGNORELIST_FILE
                            File containing a list of Pokemon IDs to ignore, one
                            line per ID. Spawnpoints will be saved, but ignored
                            Pokemon won't be encountered, sent to webhooks or
                            saved to the DB. [env var: POGOMAP_IGNORELIST_FILE]
      -encwf ENC_WHITELIST_FILE, --enc-whitelist-file ENC_WHITELIST_FILE
                            File containing a list of Pokemon IDs to encounter for
                            IV/CP scanning. One line per ID. [env var:
                            POGOMAP_ENC_WHITELIST_FILE]
      -nostore, --no-api-store
                            Don't store the API objects used by the high level
                            accounts in memory. This will increase the number of
                            logins per account, but decreases memory usage. [env
                            var: POGOMAP_NO_API_STORE]
      -apir API_RETRIES, --api-retries API_RETRIES
                            Number of times to retry an API request. [env var:
                            POGOMAP_API_RETRIES]
      -wwht WEBHOOK_WHITELIST, --webhook-whitelist WEBHOOK_WHITELIST
                            List of Pokemon to send to webhooks. Specified as
                            Pokemon ID. [env var: POGOMAP_WEBHOOK_WHITELIST]
      -wblk WEBHOOK_BLACKLIST, --webhook-blacklist WEBHOOK_BLACKLIST
                            List of Pokemon NOT to send to webhooks. Specified as
                            Pokemon ID. [env var: POGOMAP_WEBHOOK_BLACKLIST]
      -wwhtf WEBHOOK_WHITELIST_FILE, --webhook-whitelist-file WEBHOOK_WHITELIST_FILE
                            File containing a list of Pokemon IDs to be sent to
                            webhooks. [env var: POGOMAP_WEBHOOK_WHITELIST_FILE]
      -wblkf WEBHOOK_BLACKLIST_FILE, --webhook-blacklist-file WEBHOOK_BLACKLIST_FILE
                            File containing a list of Pokemon IDs NOT to be sent
                            towebhooks. [env var: POGOMAP_WEBHOOK_BLACKLIST_FILE]
      -ld LOGIN_DELAY, --login-delay LOGIN_DELAY
                            Time delay between each login attempt. [env var:
                            POGOMAP_LOGIN_DELAY]
      -lr LOGIN_RETRIES, --login-retries LOGIN_RETRIES
                            Number of times to retry the login before refreshing a
                            thread. [env var: POGOMAP_LOGIN_RETRIES]
      -mf MAX_FAILURES, --max-failures MAX_FAILURES
                            Maximum number of failures to parse locations before
                            an account will go into a sleep for -ari/--account-
                            rest-interval seconds. [env var: POGOMAP_MAX_FAILURES]
      -me MAX_EMPTY, --max-empty MAX_EMPTY
                            Maximum number of empty scans before an account will
                            go into a sleep for -ari/--account-rest-interval
                            seconds.Reasonable to use with proxies. [env var:
                            POGOMAP_MAX_EMPTY]
      -bsr BAD_SCAN_RETRY, --bad-scan-retry BAD_SCAN_RETRY
                            Number of bad scans before giving up on a step.
                            Default 2, 0 to disable. [env var:
                            POGOMAP_BAD_SCAN_RETRY]
      -msl MIN_SECONDS_LEFT, --min-seconds-left MIN_SECONDS_LEFT
                            Time that must be left on a spawn before considering
                            it too late and skipping it. For example 600 would
                            skip anything with < 10 minutes remaining. Default 0.
                            [env var: POGOMAP_MIN_SECONDS_LEFT]
      -dc, --display-in-console
                            Display Found Pokemon in Console. [env var:
                            POGOMAP_DISPLAY_IN_CONSOLE]
      -H HOST, --host HOST  Set web server listening host. [env var: POGOMAP_HOST]
      -P PORT, --port PORT  Set web server listening port. [env var: POGOMAP_PORT]
      -L LOCALE, --locale LOCALE
                            Locale for Pokemon names (check static/dist/locales
                            for more). [env var: POGOMAP_LOCALE]
      -c, --china           Coordinates transformer for China. [env var:
                            POGOMAP_CHINA]
      -m MOCK, --mock MOCK  Mock mode - point to a fpgo endpoint instead of using
                            the real PogoApi, ec: http://127.0.0.1:9090 [env var:
                            POGOMAP_MOCK]
      -ns, --no-server      No-Server Mode. Starts the searcher but not the
                            Webserver. [env var: POGOMAP_NO_SERVER]
      -os, --only-server    Server-Only Mode. Starts only the Webserver without
                            the searcher. [env var: POGOMAP_ONLY_SERVER]
      -sc, --search-control
                            Enables search control. [env var:
                            POGOMAP_SEARCH_CONTROL]
      -nfl, --no-fixed-location
                            Disables a fixed map location and shows the search bar
                            for use in shared maps. [env var:
                            POGOMAP_NO_FIXED_LOCATION]
      -k GMAPS_KEY, --gmaps-key GMAPS_KEY
                            Google Maps Javascript API Key. [env var:
                            POGOMAP_GMAPS_KEY]
      --skip-empty          Enables skipping of empty cells in normal scans -
                            requires previously populated database (not to be used
                            with -ss) [env var: POGOMAP_SKIP_EMPTY]
      -C, --cors            Enable CORS on web server. [env var: POGOMAP_CORS]
      -cd, --clear-db       Deletes the existing database before starting the
                            Webserver. [env var: POGOMAP_CLEAR_DB]
      -np, --no-pokemon     Disables Pokemon from the map (including parsing them
                            into local db.) [env var: POGOMAP_NO_POKEMON]
      -ng, --no-gyms        Disables Gyms from the map (including parsing them
                            into local db). [env var: POGOMAP_NO_GYMS]
      -nr, --no-raids       Disables Raids from the map (including parsing them
                            into local db). [env var: POGOMAP_NO_RAIDS]
      -nk, --no-pokestops   Disables PokeStops from the map (including parsing
                            them into local db). [env var: POGOMAP_NO_POKESTOPS]
      -ss, --spawnpoint-scanning
                            Use spawnpoint scanning (instead of hex grid). Scans
                            in a circle based on step_limit when on DB. [env var:
                            POGOMAP_SPAWNPOINT_SCANNING]
      -ssct SS_CLUSTER_TIME, --ss-cluster-time SS_CLUSTER_TIME
                            Time threshold in seconds for spawn point clustering
                            (0 to disable). [env var: POGOMAP_SS_CLUSTER_TIME]
      -speed, --speed-scan  Use speed scanning to identify spawn points and then
                            scan closest spawns. [env var: POGOMAP_SPEED_SCAN]
      -spin, --pokestop-spinning
                            Spin Pokestops with 50% probability. [env var:
                            POGOMAP_POKESTOP_SPINNING]
      -ams ACCOUNT_MAX_SPINS, --account-max-spins ACCOUNT_MAX_SPINS
                            Maximum number of Pokestop spins per hour. [env var:
                            POGOMAP_ACCOUNT_MAX_SPINS]
      -kph KPH, --kph KPH   Set a maximum speed in km/hour for scanner movement. 0
                            to disable. Default: 35. [env var: POGOMAP_KPH]
      -hkph HLVL_KPH, --hlvl-kph HLVL_KPH
                            Set a maximum speed in km/hour for scanner movement,
                            for high-level (L30) accounts. 0 to disable. Default:
                            25. [env var: POGOMAP_HLVL_KPH]
      -ldur LURE_DURATION, --lure-duration LURE_DURATION
                            Change duration for lures set on pokestops. This is
                            useful for events that extend lure duration. [env var:
                            POGOMAP_LURE_DURATION]
      -pd PURGE_DATA, --purge-data PURGE_DATA
                            Clear Pokemon from database this many hours after they
                            disappear (0 to disable). [env var:
                            POGOMAP_PURGE_DATA]
      -px PROXY, --proxy PROXY
                            Proxy url (e.g. socks5://127.0.0.1:9050) [env var:
                            POGOMAP_PROXY]
      -pxsc, --proxy-skip-check
                            Disable checking of proxies before start. [env var:
                            POGOMAP_PROXY_SKIP_CHECK]
      -pxt PROXY_TEST_TIMEOUT, --proxy-test-timeout PROXY_TEST_TIMEOUT
                            Timeout settings for proxy checker in seconds. [env
                            var: POGOMAP_PROXY_TEST_TIMEOUT]
      -pxre PROXY_TEST_RETRIES, --proxy-test-retries PROXY_TEST_RETRIES
                            Number of times to retry sending proxy test requests
                            on failure. [env var: POGOMAP_PROXY_TEST_RETRIES]
      -pxbf PROXY_TEST_BACKOFF_FACTOR, --proxy-test-backoff-factor PROXY_TEST_BACKOFF_FACTOR
                            Factor (in seconds) by which the delay until next
                            retry will increase. [env var:
                            POGOMAP_PROXY_TEST_BACKOFF_FACTOR]
      -pxc PROXY_TEST_CONCURRENCY, --proxy-test-concurrency PROXY_TEST_CONCURRENCY
                            Async requests pool size. [env var:
                            POGOMAP_PROXY_TEST_CONCURRENCY]
      -pxd PROXY_DISPLAY, --proxy-display PROXY_DISPLAY
                            Display info on which proxy being used (index or
                            full). To be used with -ps. [env var:
                            POGOMAP_PROXY_DISPLAY]
      -pxf PROXY_FILE, --proxy-file PROXY_FILE
                            Load proxy list from text file (one proxy per line),
                            overrides -px/--proxy. [env var: POGOMAP_PROXY_FILE]
      -pxr PROXY_REFRESH, --proxy-refresh PROXY_REFRESH
                            Period of proxy file reloading, in seconds. Works only
                            with -pxf/--proxy-file. (0 to disable). [env var:
                            POGOMAP_PROXY_REFRESH]
      -pxo PROXY_ROTATION, --proxy-rotation PROXY_ROTATION
                            Enable proxy rotation with account changing for search
                            threads (none/round/random). [env var:
                            POGOMAP_PROXY_ROTATION]
      -wh WEBHOOKS, --webhook WEBHOOKS
                            Define URL(s) to POST webhook information to. [env
                            var: POGOMAP_WEBHOOK]
      -gi, --gym-info       Get all details about gyms (causes an additional API
                            hit for every gym). [env var: POGOMAP_GYM_INFO]
      -DC, --enable-clean   Enable DB cleaner. [env var: POGOMAP_ENABLE_CLEAN]
      --wh-types {pokemon,gym,raid,egg,tth,gym-info,pokestop,lure,captcha}
                            Defines the type of messages to send to webhooks. [env
                            var: POGOMAP_WH_TYPES]
      --wh-threads WH_THREADS
                            Number of webhook threads; increase if the webhook
                            queue falls behind. [env var: POGOMAP_WH_THREADS]
      -whc WH_CONCURRENCY, --wh-concurrency WH_CONCURRENCY
                            Async requests pool size. [env var:
                            POGOMAP_WH_CONCURRENCY]
      -whr WH_RETRIES, --wh-retries WH_RETRIES
                            Number of times to retry sending webhook data on
                            failure. [env var: POGOMAP_WH_RETRIES]
      -whct WH_CONNECT_TIMEOUT, --wh-connect-timeout WH_CONNECT_TIMEOUT
                            Connect timeout (in seconds) for webhook requests.
                            [env var: POGOMAP_WH_CONNECT_TIMEOUT]
      -whrt WH_READ_TIMEOUT, --wh-read-timeout WH_READ_TIMEOUT
                            Read timeout (in seconds) for webhookrequests. [env
                            var: POGOMAP_WH_READ_TIMEOUT]
      -whbf WH_BACKOFF_FACTOR, --wh-backoff-factor WH_BACKOFF_FACTOR
                            Factor (in seconds) by which the delay until next
                            retry will increase. [env var:
                            POGOMAP_WH_BACKOFF_FACTOR]
      -whlfu WH_LFU_SIZE, --wh-lfu-size WH_LFU_SIZE
                            Webhook LFU cache max size. [env var:
                            POGOMAP_WH_LFU_SIZE]
      -whfi WH_FRAME_INTERVAL, --wh-frame-interval WH_FRAME_INTERVAL
                            Minimum time (in ms) to wait before sending the next
                            webhook data frame. [env var:
                            POGOMAP_WH_FRAME_INTERVAL]
      --ssl-certificate SSL_CERTIFICATE
                            Path to SSL certificate file. [env var:
                            POGOMAP_SSL_CERTIFICATE]
      --ssl-privatekey SSL_PRIVATEKEY
                            Path to SSL private key file. [env var:
                            POGOMAP_SSL_PRIVATEKEY]
      -ps [logs], --print-status [logs]
                            Show a status screen instead of log messages. Can
                            switch between status and logs by pressing enter.
                            Optionally specify "logs" to startup in logging mode.
                            [env var: POGOMAP_PRINT_STATUS]
      -slt STATS_LOG_TIMER, --stats-log-timer STATS_LOG_TIMER
                            In log view, list per hr stats every X seconds [env
                            var: POGOMAP_STATS_LOG_TIMER]
      -sn STATUS_NAME, --status-name STATUS_NAME
                            Enable status page database update using STATUS_NAME
                            as main worker name. [env var: POGOMAP_STATUS_NAME]
      -spp STATUS_PAGE_PASSWORD, --status-page-password STATUS_PAGE_PASSWORD
                            Set the status page password. [env var:
                            POGOMAP_STATUS_PAGE_PASSWORD]
      -hk HASH_KEY, --hash-key HASH_KEY
                            Key for hash server [env var: POGOMAP_HASH_KEY]
      -novc, --no-version-check
                            Disable API version check. [env var:
                            POGOMAP_NO_VERSION_CHECK]
      -vci VERSION_CHECK_INTERVAL, --version-check-interval VERSION_CHECK_INTERVAL
                            Interval to check API version in seconds (Default: in
                            [60, 300]). [env var: POGOMAP_VERSION_CHECK_INTERVAL]
      -odt ON_DEMAND_TIMEOUT, --on-demand_timeout ON_DEMAND_TIMEOUT
                            Pause searching while web UI is inactive for this
                            timeout (in seconds). [env var:
                            POGOMAP_ON_DEMAND_TIMEOUT]
      --disable-blacklist   Disable the global anti-scraper IP blacklist. [env
                            var: POGOMAP_DISABLE_BLACKLIST]
      -tp TRUSTED_PROXIES, --trusted-proxies TRUSTED_PROXIES
                            Enables the use of X-FORWARDED-FOR headers to identify
                            the IP of clients connecting through these trusted
                            proxies. [env var: POGOMAP_TRUSTED_PROXIES]
      --api-version API_VERSION
                            API version currently in use. [env var:
                            POGOMAP_API_VERSION]
      --no-file-logs        Disable logging to files. Does not disable --access-
                            logs. [env var: POGOMAP_NO_FILE_LOGS]
      --log-path LOG_PATH   Defines directory to save log files to. [env var:
                            POGOMAP_LOG_PATH]
      --dump                Dump censored debug info about the environment and
                            auto-upload to hastebin.com. [env var: POGOMAP_DUMP]
      -v                    Show debug messages from RocketMap and pgoapi. Can be
                            repeated up to 3 times.
      --verbosity VERBOSE   Show debug messages from RocketMap and pgoapi. [env
                            var: POGOMAP_VERBOSITY]

    Database:
      --db-name DB_NAME     Name of the database to be used. [env var:
                            POGOMAP_DB_NAME]
      --db-user DB_USER     Username for the database. [env var: POGOMAP_DB_USER]
      --db-pass DB_PASS     Password for the database. [env var: POGOMAP_DB_PASS]
      --db-host DB_HOST     IP or hostname for the database. [env var:
                            POGOMAP_DB_HOST]
      --db-port DB_PORT     Port for the database. [env var: POGOMAP_DB_PORT]
      --db-threads DB_THREADS
                            Number of db threads; increase if the db queue falls
                            behind. [env var: POGOMAP_DB_THREADS]

    Dynamic Rarity:
      -Rh RARITY_HOURS, --rarity-hours RARITY_HOURS
                            Number of hours of Pokemon data to use to calculate
                            dynamic rarity. Decimals allowed. Default: 48. 0 to
                            use all data. [env var: POGOMAP_RARITY_HOURS]
      -Rf RARITY_UPDATE_FREQUENCY, --rarity-update-frequency RARITY_UPDATE_FREQUENCY
                            How often (in minutes) the dynamic rarity should be
                            updated. Decimals allowed. Default: 0. 0 to disable.
                            [env var: POGOMAP_RARITY_UPDATE_FREQUENCY]
