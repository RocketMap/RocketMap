# Tutorial Completion
## RocketMap's tutorial completion for new accounts
RocketMap now completes the tutorial steps on all accounts on first log in, there is no more `-tut` argument to complete the tutorial.

It's recommended to enable pokestop spinning in the config to get your accounts to level 2.

To enable Pokéstop spinning, add pokestop-spinning to your configuration file, or -spin to your cli parameters.

```
pokestop-spinning
```

To set the maximum number of Pokéstop spins per account per hour (default: 80), add -ams 30 to your cli parameters or edit your configuration file:

```
account-max-spins: 30
```
