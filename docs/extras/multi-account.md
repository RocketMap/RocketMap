# Using Multiple Accounts

RocketMap supports using multiple accounts to run a worker with multiple threads.


## Using Command Line Arguments:

To use multiple accounts when running from the command line, you must specify multiple -u and -p values.

Example: `python runserver.py -a ptc -u thunderfox01 -u thunderfox02 -p thunderfox01 -p thunderfox02`


If you have multiple accounts with the same password, you can specify one -p value. RocketMap will use the value for all specified accounts.

Example: `python runserver.py -a ptc -u thunderfox01 -u thunderfox02 -p thunderfox`


If you have multiple accounts with different auth services, you can specify multiple -a values.

Example: `python runserver.py -a ptc -a ptc -a google -u thunderfox01 -u thunderfox02 -u thunderfox03@gmail.com -p thunderfox01 -p thunderfox02 -p thunderfox03`

## Using config.ini

To use multiple accounts with config.ini, you must surround all the accounts and passwords in brackets [] and seperate them with a comma and space.

Example: 
```
auth-service: ptc
username: [thunderfox01, thunderfox02]
password: [password01, password02]
```


If you have multiple accounts with the same password, you can specify one password value similar to the command line.

Example: 
```
auth-service: ptc
username: [thunderfox01, thunderfox02]
password: password
```

If you have multiple accounts using Google and PTC, you can specify auth-service for each account.

Example:
```
auth-service: [ptc, ptc, google]
username: [thunderfox01, thunderfox02, thunderfox03@gmail.com]
password: [password01, password02, password03]
```

## Using CSV file:

To use multiple accounts from a CSV file, you create a CSV file with the auth method, username and password on each line. Shorten to 3 fields only, more than 3 fields will error out.

CSV File Example:
```
ptc,thunderfox01,password01
google,thunderfox02@gmail.com,password02
```

Example: `python runserver.py -ac accounts.csv`
