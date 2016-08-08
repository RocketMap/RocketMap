App Development
###############

.. note::

  This article is about contributing to the development codebase. For contributing to the wiki see :doc:`contributing`.

.. warning::

  These instructions will help you get started contributing code to the ``develop`` branch. If you just want to **use the map** you should not use ``develop``, instead follow the :doc:`/basic-install/index` instructions

Development requires several tools to get the job done. Python, obviously, needs to be installed. We also utilize NodeJS and Grunt for front-end asset compilation. The :doc:`/basic-install/index` instructions have an extra section about getting node installed. Follow that.

Node and Grunt
**************

Grunt is a tool to automatically run tasks against the code. We use grunt to transform the Javascript and CSS before it's run, and bundle it up for distribution.

If you want to change the Javascript or CSS, you must install and run Grunt to see your changes

Compiling Assets
================

After Grunt is installed successfully, you need to run it when you change Javascript or CSS.

Simply type

.. code-block:: bash

  npm run watch

on the command-line. This runs a default grunt "task" that performs a number of subtasks, like transforming JS with Babel, minifying, linting, and placing files in the right place. It will also automatically start a "watch" which will automatically rebuild files as you modify them. You can stop grunt-watch with CTRL+C.

If you'd like to just build assets once, you can run:

.. code-block:: bash

  npm run build


The "/dist" directory
*********************

Files in the "static/dist/" subdirectories should not be edited. These will be automatically overwritten by Grunt.

To make your changes you want to edit e.g. ``static/js/map.js``
