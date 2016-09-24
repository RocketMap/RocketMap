# Common Questions and Answers

## Can I sign in with Google?

Yes you can! Pass the flag `-a google` (replacing `-a ptc`) to use Google authentication.

If you happen to have 2-step verification enabled for your Google account you will need to supply an [app password](https://support.google.com/accounts/answer/185833?hl=en) for your password instead of your normal login password.


## ...expected one argument.

The -dp, -dg -dl, -i, -o and -ar parameters are no longer needed. Remove them from your query.

## How do I setup port forwarding?

[See this helpful guide](external.md)

## "It's acting like the location flag is missing."

`-l`, never forget.

## example.py isn't working right

10/10 would run again

## I'm getting this error...

```
pip or python is not recognized as an internal or external command
```

[Python/pip has not been added to the environment](https://github.com/Langoor2/PokemonGo-Map-FAQ/blob/master/FAQ/Enviroment_Variables_not_correct.md) or [pip needs to be installed to retrieve all the dependencies](https://github.com/AHAAAAAAA/PokemonGo-Map/wiki/Installation-and-requirements)

```
Exception, e <- Invalid syntax.
```

This error is caused by Python 3. The project requires python 2.7

```
error: command 'gcc' failed with exit status 1

# - or -

[...]failed with error code 1 in /tmp/pip-build-k3oWzv/pycryptodomex/
```

Your OS is missing the `gcc` compiler library. For Debian, run `apt-get install build-essentials`. For Red Hat, run `yum groupinstall 'Development Tools'`

## Formulas?
Worker Count Formula: `W= 10/T * (R/5)^2`

Another:
```
A = 10 / T * (R/5)^2

A = Accounts
R = Radius (in "steps" -st)
T = 15 minutes minus the minimum remaining amount of time you want when the pokemon is spotted.   (T=15-0=15 if you are just scanning for spawn points;   T= (15 - 5 ) = 10 means you will have 5 minutes left guaranteed after spotting it, more for twitter bots)
```

