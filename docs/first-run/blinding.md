# Account Blinding 

### As of May 21st 2017, Niantic has implemented a new kind of ban. This ban will hide rare pokemon and other features within the Pokemon Go app when using an account that is blind. 

## What do we know?

Accounts are automattically banned based on specific behaviors known to mappers and botters. While RocketMap is working on a full scale solution, this a guide of what we know. 

* New accounts work for 60 to 140 hours (depending on config).
* Blinded accounts can get unblinded after 6 to 10 days.
* Reusing unblinded accounts in any 3rd party app (including RM) will get them blinded again faster than before (sometimes in just a few hours).
* If you buy accounts to scan, do so at your own risk. These have often been getting blinded in a matter of a few hours (~4h), most likely because they had already been flagged before.
* Once flagged, the blinding is inevitable.
* All 3rd party apps/scanners are affected in the exact same manner. We've spent extra time to confirm this because some people were pretty convinced we were wrong, although it usually ended up being because they hadn't even realized their accounts were already blind.
* **There is NO recommended way to test accounts for blindness.** The current 3rd party implementations are incorrect and could get your accounts flagged if they weren't already. This is a WIP and is being added to RM itself.

## What can I do?

Right now, here are 3 approaches for your configs to maximize the scan time per account. **Results depend on a lot of things, so test and experiment for yourself until you find what works best for you:**
1. Burn through accounts: no sleep, no account rotation. For some whose accounts usually get flagged very early on, this will increase the scan time of the account.
2. Use a basic constant rotation: e.g. asi 8h (8h of scanning) for ari 4h (4 hours of sleep).
3. Use more realistic scan times: low asi and high ari (scan in bursts: short period of scanning for a realistic resting time), or low asi and low ari (what you would call "not too active players") but use enough spare accounts to fill 24 hours with realistic schedules for all accounts.

The ideal will depend on your own results, we've found that all three approaches had positive effects for at least one testing setup. A person who needs #1 will be the direct opposite of someone running #3, but both are equally valid.

### Spawnpoint Fix

If your accounts are blinded and it starts disabling spawnpoints because it considers them "missed too often", you can run this query safely to re-enable those spawnpoints:
```sql
UPDATE spawnpoint SET missed_count = 0;
```

`last updated 6/9/17`
