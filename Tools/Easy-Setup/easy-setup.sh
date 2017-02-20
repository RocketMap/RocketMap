#!/bin/sh

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Installing RocketMap Requirements."
echo "This script may ask for your sudo/root password to perform the installation."
echo ""

if [ "$(grep -Ei 'debian|buntu|mint' /etc/*release)" ]; then
    echo "Installing python development tools..."
    sudo apt-get install python python-dev build-essential -y
    echo "Adding node repo..."
    curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
    echo "Installing node..."
    sudo apt-get install nodejs -y
else
    echo "This script only supports debain based Linux distros."
    echo "Please install manually."
    exit 1
fi

echo "Installing pip..."
sudo python get-pip.py
echo "Installing required python packages..."
sudo pip install -r $scriptDir/../../requirements.txt --upgrade
echo "Installing frontend dependencies..."
npm --prefix $scriptDir/../../ install $scriptDir/../../
echo "Building frontend..."
npm run build

echo "Configuring Google Maps API..."
cp $scriptDir/../../config/config.ini.example $scriptDir/../../config/config.ini
echo -n "Enter your Google Maps API key here:"
read key
sed -i -e "s/\"\#gmaps-key\":\ \"\"/\"gmaps-key\":\ \""$key"\"/g" $scriptDir/../config/config.ini

echo "All done!"
