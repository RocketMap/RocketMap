# Hashing Keys

## What are hashing keys for?
Hashing keys allow your client program (in this case RocketMap) to access the latest API using the Bossland Hashing service. It is no longer possible to access the API without a hashing key.

## Where do I get a hashing key?
[Check out this FAQ](https://talk.pogodev.org/d/55-api-hashing-service-f-a-q)

## How many RPMs will I use?
There is no perfect way to know. There are many variables that must be considered, including your step size, spawn spoints, encounters.

Please don't ask *"What if my step size is _x_, and I have encounters for _y_ Pokemon"*
We still don't know.  Get a key, turn on your map and see if it works.

If you are getting rate limited then either get more keys, or lower your calls (disabling/reducing encounters, disabling gym details, and decreasing step size are a few ways to reduce calls)

You can get a more detailed view of how many Hashing key calls are being used by enabling the status view `-ps` / `--print-status` and typing `h` followed by the enter key *OR* go to `<YourMapUrl>/status` and enter the password you defined. The status of each of your workers and hashing keys will be displayed and continually updated. [More information about the status page](https://rocketmap.readthedocs.io/en/develop/extras/status-page.html)  

## Common Questions

### Where do I enter my hashing key?
Use `-hk YourHashKeyHere` / `--hash-key YourHashKeyHere`.  
If you use a configuration file, add the line `hash-key: YourHashKeyHere` to that file.

### What if I have more than one hashing key?
Specify `-hk YourHashKeyHere -hk YourSecondHashKeyHere ...`.  
If you use a configuration file, use `hash-key: [YourHashKeyHere, YourSecondHashKeyHere, ...]` in the file.

### If you have multiple keys, how does RM decide which one to use?
RM will load balance the keys until a key is full. For example, if you had a 150 rpm key and 500 rpm key, both would be used equally until the 150 rpm key is full then only the 500 rpm key would be utilized.

### What does `HashingQuotaExceededException('429: Request limited, error: ',)` mean?
Any variant of this means you've exceeded the Requests Per Minute that your key allows. Currently, this is not being tracked accurately by Bossland, therefore, you will get more hashing requests than what you are paying for.

### How about `Hashing server is unreachable, it might be offline.`
Hashing server is temporarily unavailable (possibly offline). This could be due to maintenance or server failure. Please checkout discord for more information is you start getting this error.

### And this one? `Invalid or expired hashing key: %s. + api._hash_server_token`
Either your key is expired, the hashing servers are having issues, or you have mistyped your key.

### This one? `TempHashingBanException('Your IP was temporarily banned for sending too many requests with invalid keys',)`
You are using invalid keys, or... you guessed it, the hashing servers are having issues. This ban will last for 3 minutes. 
