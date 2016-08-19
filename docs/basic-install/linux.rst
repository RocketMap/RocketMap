Linux Install
##################

Installation will require Python 2.7 and Pip.

Ubuntu
*************

You can install the required packages on Ubuntu by running the following command:

.. code-block:: bash

  sudo apt-get install python python-pip python-dev
  
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

	pip install -r requirements.txt
	npm install
	npm install -g grunt-cli
	grunt build

troubleshooting:
	
	If you have preciously installed pip packages before following this guide, you may need to remove them before installing:
	
.. code-block:: bash

	pip freeze | xargs pip uninstall -y
	

Red Hat or CentOs or Fedora
***************************

You can install required packages on Red Hat by running the following command:

You may also need to install the EPEL repository to install python-pip and python-devel.

.. code-block:: bash

  yum install epel-release
  yum install python python-pip python-devel

All set, head back to the basic install guide.
