Basic Installation
##################

These instructions cover an instation from a **release** as well as from a git clone.

Prerequisites
*************

Follow one of the guides below to get the basic prerequisites installed:

 * :doc:`osx`
 * :doc:`windows`
 * :doc:`linux`

Credentials
***********

 * You'll need an active Pokemon Trainer Club account or Google account
 * Get a :doc:`google-maps`

Downloading the Application
***************************

You have an important decision here, you may either download a "release" or use ``git`` to fetch the latest development version. The release versions tend to be more stable and require less technical install steps, but they will have fewer features.

Release Version
===============
If you want to run a release version, visit the `Github releases page <https://github.com/PokemonGoMap/PokemonGo-Map/releases>`_ and download and extract the release you want to run


``git`` Version
===============

If you're going to run a copy from the latest ``develop`` branch in ``git`` you can clone the repository:

.. code-block:: bash

  git clone https://github.com/PokemonGoMap/PokemonGo-Map.git

Installing Modules
******************

At this point you should have the following:

 * Python 2.7
 * pip
 * PokemonGo-Map application folder

First, open up your shell (``cmd.exe``/``terminal.app``) and change to the directory of PokemonGo-Map.

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

Now you can install all the Python dependencies, make sure you're still in the directory of PokemonGo-Map:

Windows:

.. code-block:: bash

  pip install -r requirements.txt

Linux/OSX:

.. code-block:: bash

  sudo -H pip install -r requirements.txt

``git`` Version Extra Steps
===========================

.. warning::

  This only applies if you are running from a ``git clone``. If you are using a release version, skip this section

In order to run from a git clone, you must compile the front-end assets with node. Make sure you have node installed for your platform:

 * `Windows <https://nodejs.org/dist/v4.4.7/node-v4.4.7-x64.msi>`_
 * `OSX <https://nodejs.org/dist/v4.4.7/node-v4.4.7.pkg>`_
 * Linux -- refer to the `package installation <https://nodejs.org/en/download/package-manager/>`_ for your flavor of OS

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

Once those have run, you should be able to start using the application, make sure you're in the directory of PokemonGo-Map then:

.. code-block:: bash

  python ./runserver.py --help

Read through the available options and set all the required CLI flags to start your own server. At a minimum you will need to provide a location, account login credentials, and a :doc:`google maps key <google-maps>`.

The most basic config you could use would look something like this:

.. code-block:: bash

  python ./runserver.py -a ptc -u "USERNAME_HERE" -p "PASSWORD_HERE" \
   -l "a street address or lat/lng coords here" -st 3 -k "maps key here"

Open your browser to http://localhost:5000 and your pokemon will begin to show up! Happy hunting!

Updating the Application
************************

PokemonGo-Map is a very active project and updates often. You can follow the `latest changes <https://github.com/PokemonGoMap/PokemonGo-Map/commits/develop>`_ to see what's changing.

If you are running a **release** version, you can simply start this tutorial over again with a new download.

If you are running a ``git`` version, you can update with a few quick commands:

.. code-block:: bash

  git pull
  pip install -r requirements.txt --upgrade
  npm install
  npm run build

You can now restart your ``runserver.py`` command.
