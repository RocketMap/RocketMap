# Hash Keys

## What are hash keys for?
Hash keys allow your client program (in this case RocketMap) to access the latest API using the Bossland Hashing service. Accessing Niantic's servers without using a hash key is using an older API that is easier for Niantic to flag and ban.

## Where do I get a hash key?
[Check out this FAQ](https://talk.pogodev.org/d/55-api-hashing-service-f-a-q)

## How many RPMs will I use?
There is no perfect way to know. There are many variables that must be considered, including your step size, spawn spoints, encounters.

Please don't ask *"What if my step size is _x_, and I have encounters for _y_ Pokemon"*

We still don't know.  Get a key, turn on your map and see if it works.
If you are getting rate limited then either get more keys, or lower your calls (disabling/reducing encounters, disabling gym details, and decreasing step size are a few ways to reduce calls)

## What does HashingQuotaExceededException('429: Request limited, error: ',) mean?
Any variant of this means you've exceeded the Requests Per Minute that your key allows.

## How about [ WARNING] Exception while downloading map: HashingOfflineException('502 Server Error',)
Hashing server is temporarily unavailable (possibly offline).

## And this one? BadHashRequestException('400: Bad request, error: Unauthorized',)
Either your key is expired, or the hashing servers are having issues.

## This one? TempHashingBanException('Your IP was temporarily banned for sending too many requests with invalid keys',)
You are using invalid keys, or... you guessed it, the hashing servers are having issues.
