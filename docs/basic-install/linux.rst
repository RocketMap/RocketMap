Linux Install
##################

Installation will require Python 2.7 and pip.

Ubuntu
*************

You can install the required packages on Ubuntu by running the following command:

.. code-block:: bash

  sudo apt-get install -y python python-pip python-dev build-essential git
  curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
  sudo apt-get install -y nodejs
  
  
Debian 7/8
**********

Debian's sources lists are out of date and will not fetch the correct versions of Python and PIP. You must download and install these from source:

.. code-block:: bash

	sudo apt-get install -y build-essential libbz2-dev libsqlite3-dev libreadline-dev zlib1g-dev libncurses5-dev libssl-dev libgdbm-dev python-dev nodejs npm
	wget https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz
	tar xzf Python-2.7.12.tgz && cd Python-2.7.12
	./configure --prefix=/opt/python
	make
	make install
	ln -s /opt/python/bin/python2.7 /usr/local/bin/python2.7
	ln -s /opt/python/bin/python2.7 /usr/bin/python2.7
	ln -s /usr/bin/python2.7 /usr/bin/python
	ln -s /usr/local/bin/python2.7 /usr/local/bin/python
	ln -s /opt/python/bin/pip /usr/bin/pip
	ln -s /opt/python/bin/pip /usr/local/bin/pip
	ln -s /usr/bin/nodejs /usr/bin/node
	sed -e '$a\PATH="$PATH:/opt/python/bin"\' ~/.profile
	source ~/.profile
	wget https://bootstrap.pypa.io/get-pip.py
	python get-pip.py
	
After install, check that you have the correct versions in your environment variables:

.. code-block:: bash

	~$ python --version
		Python 2.7.12
	~$ pip --version
		pip 8.1.2 from /home/user/.local/lib/python2.7/site-packages (python 2.7)
		
If your output looks as above, you can proceed with installation:

.. code-block:: bash
        
	cd ~/
	sudo apt-get install git
	git clone https://github.com/RocketMap/RocketMap.git
	cd RocketMap
	sudo -H pip install -r requirements.txt
	npm install
	sudo npm install -g grunt-cli
	sudo grunt build

Troubleshooting:
****************
	
	If you have preciously installed pip packages before following this guide, you may need to remove them before installing:
	
.. code-block:: bash

	pip freeze | xargs pip uninstall -y
	
If you have other pip installed packages, the old requirements.txt and cannot uninstall all then you can use:

.. code-block:: bash
	
	pip uninstall -r "old requirements.txt"
	pip install -r "new requirements.txt"

An error resulting from not removing previous packages can be:

.. code-block:: bash
	
	016-12-29 00:50:37,560 [ search-worker-1][        search][    INFO] Searching at xxxxxxx,xxxxxxx
	2016-12-29 00:50:37,575 [ search-worker-1][        search][ WARNING] Exception while downloading map:
	2016-12-29 00:50:37,575 [ search-worker-1][        search][   ERROR] Invalid response at xxxxxxx,xxxxxxx, abandoning location
	
If you're getting the following error:

.. code-block:: bash

	root:~/RocketMap# ./runserver.py
	Traceback (most recent call last):
  		File "./runserver.py", line 10, in <module>
  		import requests
	ImportError: No module named requests
	
	You will need to completely uninstall all of your pip packages, pip, and python, then re-install from source again. Something from your previous installation is still hanging around.
	
Debian 7
********

Additional steps are required to get Debian 7 (wheezy) working. You'll need to update from ``glibc`` to ``eglibc``

Edit your ``/etc/apt/sources.list`` file and add the following line:

.. code-block:: bash

	deb http://ftp.debian.org/debian sid main
	
Then install the packages for ``eglibc``:

.. code-block:: bash

	sudo apt-get update
	apt-get -t sid install libc6-amd64 libc6-dev libc6-dbg
	reboot

Red Hat or CentOs or Fedora
***************************

You can install required packages on Red Hat by running the following command:

You may also need to install the EPEL repository to install ``python-pip`` and ``python-devel``.

.. code-block:: bash

  yum install epel-release
  yum install python python-pip python-devel
  
  Fedora Server:
  dnf install python
  dnf install redhat-rpm-config // fix for error: command 'gcc' failed with exit status 1
  

All set, head back to the basic install guide.
