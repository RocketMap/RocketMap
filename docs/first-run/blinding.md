# Account Blinding

### As of May 21st 2017, Niantic has implemented a new kind of ban. This ban will hide some pokemon within the Pokemon Go app when using an account in that state.

## What do we know?

Currently all APIs and tools are affected, the flag they use to identify third party projects has not been found and there are some fields in the API which we are missing information for.

 * Clean accounts work for up to 3 days before blinding under regular usage.
 * There are some unknown daily limits for map requests or encounters, if an account reaches that limit it immediately gets banned.
 * Blinded accounts will get banned after 2-3 more days (even if they are removed from use).
 * Banned accounts will get unbanned and unblinded after up to 2 months.
 * If you buy accounts to scan, you do so at your own risk. Often these accounts are already blind when you purchase them or can get blinded soon if the seller does not give you accounts that have been resting for 2 months.
 * Blinding is inevitable.
 * All 3rd party apps/scanners are affected in the exact same manner. We've spent extra time to confirm this because some people were pretty convinced we were wrong, although it usually ended up being because they hadn't even realized their accounts were already blind.
 * Blinding also affects high level accounts, blinded accounts will fail to encounter the Pokémon hidden in the map, they also get banned within 24 hours if they do too many encounters.
 * Even a simple login without a map request will start the countdown that leads to blinding. Any third party API usage whatsoever on an account will flag your account.

## What can I do?

Given the current situation the best option is to burn through accounts: no sleep, no account rotation. This will allow you to use as little accounts as possible and just change the whole batch at once (including high level accounts) once you see that accounts are getting blinded.

You can identify that your accounts are getting blinded by the lower number of Pokémon in the map or the frequency with which the following message occurs in your logs:

```
[models][ WARNING] hsss kind spawnpoint XXXXX has no Pokemon Y times in a row.
```

Some errors like that are expected during regular operation but if the log is constantly spammed with this, then you are likely getting blinded accounts. Please note that this message will only appear up to 5 times per spawnpoint (and it will subsequently be hidden so your logs don't get spammed).

On high lvl accounts you can identify blinded accounts when the encounter fails with the error `3`.

### Spawnpoint Fix

If your accounts are blinded and it starts disabling spawnpoints because it considers them "missed too often", you can run this query safely to re-enable those spawnpoints:
```sql
UPDATE spawnpoint SET missed_count = 0;
```
