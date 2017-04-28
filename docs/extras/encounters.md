# Pokémon Encounters

Since the IV update of April 21st 2017 which makes IVs the same for players of level 25 and above, the encounter system has been reworked and now includes CP/IV scanning.

Steps for using the new encounter system:

1. Make sure initial scan has finished. Enabling encounters during initial scan is a waste of requests.
2. Enable encounters on your map (`-enc`).
3. Add L30 accounts for IV/CP scanning into a CSV file (separate from your regular accounts file, e.g. 'high-level.csv'). **Warning: read the important points below if you're scanning with only L30s!** The lines should be formatted as "service,user,pass":
   ```
   ptc,randOMusername1,P4ssw0rd!
   ptc,randOMusername2,P4ssw0rd!
   ptc,randOMusername1,P4ssw0rd!
   ```
   The config item or parameter to use this separate account file is:
   ```
   --high-lvl-accounts high-level.csv
   ```
4. Create files for your IV/CP encounter whitelist and add the Pokémon IDs which you want to encounter, one per line.
   enc-whitelist.txt:
   ```
   10
   25
   38
   168
   ```
5. Enable the whitelist files in your config or cli parameters (check commandline.md for usage):
   ```
   --enc-whitelist-file enc-whitelist.txt
   ```
6. (Optional) Set a speed limit for your high level accounts. This is separate from the usual speed limit, to allow a lower speed to keep high level accounts safer:
   ```
   --hlvl-kph 25
   ```
7. (Optional) To reduce the number of times a high level account will log into the game via the API, the API objects are stored in memory to re-use them rather than recreating them. This is enabled by default to keep high level accounts *safer* but it will cause an increase in memory usage. To reduce memory usage, disable the feature with:
   ```
   --no-api-store
   ```

L30 accounts are not being recycled and are not in the usual account flow. This is intentional, to allow for future reworks to handle accounts properly. This also keeps interaction with high level accounts to a minimum. We can consider handling them more automatically when the account handlers are properly fully implemented.

Some important notes:

 * If you're only scanning with high level accounts (i.e. your regular accounts file only has L30s), the `--high-lvl-accounts` file can stay empty. The encounter code will use your regular accounts to encounter Pokémon if they're high enough level. But don't mix low level accounts with high levels, otherwise encounters will be skipped.
 * To report Unown form, Unown's Pokémon ID must be added to the IV or CP whitelist.
 * The old encounter whitelists/blacklists have been removed entirely.
 * Both the IV and CP whitelists are optional.
 * Captcha'd L30 accounts will be logged in console and disabled in the scheduler. Having `-v` enabled will show you an entry in the logs mentioning "High level account x encountered a captcha". They will not be solved automatically.
 * The encounter is a single request (1 RPM). We intentionally don't use the account for anything else besides the encounter.
 * The high level account properly uses a proxy if one is set for the scan, and properly rotates hashing keys when needed.
