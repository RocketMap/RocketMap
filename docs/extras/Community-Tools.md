# Community Tools
Some useful tools made by the community for the community

## [PalletTown](https://github.com/novskey/PalletTown)
### Java tool for creating PTC Accounts, based on Pikaptcha.
Used to generate any desired number of PTC accounts for use with RocketMap.

## [PGM Multi Loc](https://beccasafan.github.io/pgm-multiloc/)
### Easily visualize locations on a map before scanning, and generate a customized launch script.
Add multiple scan locations on the map. Automatically convert an area to a beehive. Resize and move the location on the map. Disable individual hives to stop scanning a specific location.

Generate a customized launch script, with the ability to edit the templates used for the individual commands. Pass in a list of account information that contains usernames, passwords, proxies, etc.

## [Cor3Zer0's Map Calculator](https://github.com/Cor3Zer0/Map-Calculator)
### Calculator that helps in the creation of RocketMap
Used to calculate optimized flags for particular use cases given a set situation.
_Example: I have an ST of 7, a delay of 10, and need my scan to be around 100 seconds. How many accounts should I use?_

## [HoneySpots - Easy Multi-account-Multi-location generator](https://github.com/razorasadsid/HoneySpots)
### Saves users a ton of tedious work - allows completely customized file generation and control.
Constantly in development - but allows the generation of a multi-worker .bat file with ease, along with custom flags. Can read account and location data right off a .csv file (no need to edit the files either - just set the right columns) and allows you to customize everything from the starting parameters to the naming of each instance through an easily configurable config.ini. 
_Example: I need to search a few small areas very very quickly with accounts I've generated.
_Example: I have a list of locations and a list of accounts, but I don't want to go through the tedium of having to create the .bat myself_

## [HoneyFill - Multi-account-multi-location generator in python](https://github.com/joostsijm/HoneyFill)
### Easily parsing your accounts and coordinates.
Generate .sh file to start RocketMap with given coordinates. Use your .csv files to fill the users and coordinates. Providing Command line arguments to configure the output. Allows setting the step size of multiple coordinates, and amount of users it's using. Useful when you need to regenerate a scanner starter with new accounts.
_Example: python2 generate.py -a EXAMPLEaccounts.csv -c EXAMPLElocations.csv_
