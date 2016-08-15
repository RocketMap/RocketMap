# Using Multiple Accounts

PokemonGo-Map supports using multiple accounts to run a worker with multiple threads.


## Using Command Line Arguments:

To use multiple accounts when running from the command line, you must specify multiple -u and -p values.

Example: `python runserver.py -u thunderfox01 -u thunderfox02 -p thunderfox01 -p thunderfox02`


If you have multiple accounts with the same password, you can specify one -p value. PokemonGo-Map will use the value for all specified accounts.

Example: `python runserver.py -u thunderfox01 -u thunderfox02 -p thunderfox`

## Using config.ini

To use multiple accounts with config.ini, you must surround all the accounts and passwords in brackets [] and seperate them with a comma and space.

Example: 
```
username: [thunderfox01, thunderfox02]
password: [password01, password02]
```


If you have multiple accounts with the same password, you can specify one password value similar to the command line.

Example: 
```
username: [thunderfox01, thunderfox02]
password: password
```
