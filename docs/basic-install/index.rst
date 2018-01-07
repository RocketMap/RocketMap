Basic Installation
##################

These instructions cover an installation from the develop branch in git.

Prerequisites
*************

Follow one of the guides below to get the basic prerequisites installed:

 * :doc:`osx`
 * :doc:`windows`
 * :doc:`linux`

You will also need a MySQL server installed:

 * :doc:`mysql`

Credentials
***********

 * You'll need an active Pokemon Trainer Club account or Google account
 * Get a :doc:`google-maps`
 * Get a `Hashing Key <https://rocketmap.readthedocs.io/en/develop/first-run/hashing.html>`_

Downloading the Application
***************************

To run a copy from the latest ``develop`` branch in ``git`` you can clone the repository:

.. code-block:: bash

  git clone https://github.com/RocketMap/RocketMap.git

Installing Modules
******************

At this point you should have the following:

 * Python 2.7
 * pip
 * RocketMap application folder

First, open up your shell (``cmd.exe``/``terminal.app``) and change to the directory of RocketMap.

You can verify your installation like this:

.. code-block:: bash

  python --version
  pip --version

The output should look something like:

.. code-block:: bash

  $ python --version
  Python 2.7.12
  $ pip --version
  pip 8.1.2 from /usr/local/lib/python2.7/site-packages (python 2.7)

Now you can install all the Python dependencies, make sure you're still in the directory of RocketMap:

Windows:

.. code-block:: bash

  pip install -r requirements.txt

Linux/OSX:

.. code-block:: bash

  sudo -H pip install -r requirements.txt

Building Front-End Assets
===========================

In order to run from a git clone, you must compile the front-end assets with node. Make sure you have node installed for your platform:

 * `Windows/OSX <https://nodejs.org/en/download/>`_ (Click the Windows or Macintosh Installer respectively)
 * Linux -- refer to the `package installation <https://nodejs.org/en/download/package-manager/>`_ for your flavor of OS"

Once node/npm is installed, open a command window and validation your install:

.. code-block:: bash

  node --version
  npm --version

The output should look something like:

.. code-block:: bash

  $ node --version
  v4.7.0
  $ npm --version
  3.8.9

Once node/npm is installed, you can install the node dependencies and build the front-end assets:

.. code-block:: bash

  npm install

  # The assets should automatically build (you'd see something about "grunt build")
  # If that doesn't happen, you can directly run the build process:
  npm run build


Basic Launching
***************

Once those have run, you should be able to start using the application, make sure you're in the directory of RocketMap then:

.. code-block:: bash

  python ./runserver.py --help

Read through the available options and set all the required CLI flags to start your own server. At a minimum you will need to provide a location, account login credentials, and a :doc:`google maps key <google-maps>`.

The most basic config you could use would look something like this:

.. code-block:: bash

 python ./runserver.py -ac accounts.csv -st 10 \
 -l "a street address or lat/lng coords here" -k "MAPS_KEY_HERE" \
 -hk "HASH_KEY_HERE" -cs -ck "CAPTCHA_KEY"

Let's run through this startup command to make sure you understand what flags are being set.

* -ac accounts.csv
Load accounts from CSV (Comma Seperated Values) file containing "auth_service,username,password" lines. `More Info <http://rocketmap.readthedocs.io/en/develop/first-run/multi-account.html>`_


* -hk "HASH_KEY_HERE"
Key used to access the hash server. `More Info <http://rocketmap.readthedocs.io/en/develop/first-run/hashing.html>`_

* -cs -ck "CAPTCHA_KEY"
Enables captcha solving and 2Captcha API key. (Manual captcha available, see `Full Info <http://rocketmap.readthedocs.io/en/develop/first-run/captchas.html>`_ )

**Once your setup is running, open your browser to http://localhost:5000 and your pokemon will begin to show up! Happy hunting!**

Things to Know
**************

 * You may want to use more than one account to scan with RocketMap. `Here <https://rocketmap.readthedocs.io/en/develop/first-run/multi-account.html>`_ is how to use as many accounts as your heart desires.
 * Your accounts need to complete the tutorial before they will be any use to RocketMap! `Here <https://rocketmap.readthedocs.io/en/develop/first-run/tutorial.html>`_ is how do that with RM.
 * You might experience your accounts encountering Captchas at some point. `Here <https://rocketmap.readthedocs.io/en/develop/first-run/captchas.html>`_ is how we handle those.
 * Due to recent updates, you might experience a shaddow ban. `Here <https://rocketmap.readthedocs.io/en/develop/first-run/Blinding.html>`_ is what you need to know.
 * All of these flags can be set inside of a configuration file to avoid clutter in the command line. Go `here <http://rocketmap.readthedocs.io/en/develop/first-run/configuration-files.html>`_ to see how.
 * A full list of all commands are available `here. <https://rocketmap.readthedocs.io/en/develop/first-run/commandline.html>`_
 * A few tools to help you along the way are located `here. <https://rocketmap.readthedocs.io/en/develop/extras/Community-Tools.html>`_


Updating the Application
************************

RocketMap is a very active project and updates often. You can follow the `latest changes <https://github.com/RocketMap/RocketMap/commits/develop>`_ to see what's changing.

You can update with a few quick commands:

.. code-block:: bash

  git pull
  pip install -r requirements.txt --upgrade (Prepend sudo -H on Linux)
  npm run build

Watch the `latest changes <https://github.com/RocketMap/RocketMap/commits/develop>`_ on `Discord <https://discord.gg/RocketMap>`_ to know when updating will require commands other than above.

**IMPORTANT** Some updates will include database changes that run on first startup. You should run only **one** ``runserver.py`` command until you are certain that the DB has been updated. You will know almost immediately that your DB needs updating if **Detected database version x, updating to x** is printed in the console. This can take a while so please be patient. Once it's done, you can start all your instances like you normally would.
