#!/bin/bash

# Name of coords file. If you do not have one use location_generator.py -or
coords="coords.txt"

# Webserver Location
initloc="Dallas, TX"
# Account name without numbers
pre="accountname"

# Variables
hexnum=1   # This is the beehive number you are creating. If its the first, or you want to overwrite, dont change
worker=0   # This is the worker number. Generally 0 unless 2+ Hives
acct1=0    # The beginning account number for the hive is this +1
numacct=5  # This is how many accounts you want per worker
pass="yourpasshere" # The password you used for all the accounts
auth="ptc" # The auth you use for all the accounts
st=5       # Step Count per worker
sd=5       # Scan Delay per account
ld=1       # Login Delay per account
directory='/path/to/your/runserver/directory/' # Path to the folder containing runserver.py **NOTICE THE TRAILING /**

# Check to see if supervisor folder/subfolder exists if not make it
if [ ! -d ~/supervisor/hex$hexnum ]; then
  mkdir -p ~/supervisor/hex$hexnum
fi

# Change Directory to ~/supervisor in script subshell
cd "$HOME/supervisor" || exit 1

# Cleaning up directory
rm -f hex$hexnum/*.ini

# Epicly complex loop
while read -r line; do
  ((worker++))
  printf -v n %02d $worker
  cp template.ini "hex$hexnum/worker_$n.ini"
  user=$(for (( i = 1; i <= numacct; i++ )) do
           echo -n "-u ACCT$i "
         done)
  sed -i "s/WRK/$n/" "hex$hexnum/worker_$n.ini"
  sed -i "s/LOC/$line/" "hex$hexnum/worker_$n.ini"
  sed -i "s/USER/$user/" "hex$hexnum/worker_$n.ini"
  sed -i "s/AUTH/$auth/" "hex$hexnum/worker_$n.ini"
  sed -i "s/PASS/$pass/" "hex$hexnum/worker_$n.ini"
  sed -i "s/ST/$st/" "hex$hexnum/worker_$n.ini"
  sed -i "s/LD/$ld/" "hex$hexnum/worker_$n.ini"
  sed -i "s/SD/$sd/" "hex$hexnum/worker_$n.ini"
  sed -i "s,DIRECTORY,$directory," "hex$hexnum/worker_$n.ini"
  for (( i = 1; i <= numacct; i++ )) do
    sed -i "s/ACCT$i/$pre$((acct1+i))/" "hex$hexnum/worker_$n.ini"
  done
  ((acct1+=numacct))
done < $coords

sed -i "s,DIRECTORY,$directory," "$HOME/supervisor/supervisord.conf"
sed -i "s/LOC/$initloc/" "$HOME/supervisor/supervisord.conf"

# Adding the folder to supervisord.conf [inclues]
if [ -z $(grep -i "hex$hexnum/\*.ini" supervisord.conf) ]; then
  echo "files = hex$hexnum/*.ini" >> supervisord.conf
fi
