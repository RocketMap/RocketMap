# Common Questions and Answers

## Critical Error "Missing sprite files"
If you're unaware of what sprites are, the friendly users on our Discord are more than willing to explain. [RocketMap Discord](https://discord.gg/PWp2bAm).

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
```
st=step distance

sd=scan delay [default: 10]

w=# of workers

t=desired scan time
```
time to scan:
`(sd/w)*(3st^2-3st+1)`

workers needed:
`(sd/t)*(3st^2-3st+1)`

time to scan (using default scan delay):
`(10/w)*(3st^2-3st+1)`

workers needed (using default scan delay):
`(10/t)*(3st^2-3st+1)`

